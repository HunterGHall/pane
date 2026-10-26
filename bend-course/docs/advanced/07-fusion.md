# 7. Fusion

## What & why

Optimal evaluation means HVM never does the same reduction twice: shared work stays shared. A striking consequence is **fusion**: composing a function with itself *many* times can cost almost nothing, because the composed function reduces to a tiny term before it is ever applied to data. Whether you get that depends on how you *write* the function, and the rule is simple enough to learn in one lesson.

This is an expert topic. You will not need it to write ordinary Bend. But it explains why HVM can run some "impossible" programs, and it gives you a mental model for writing efficient lambda-heavy code.

## Setting the stage: Church booleans and `not`

(Everything here is Fun syntax and is not type-checked.)

```text
true  = λt λf t
false = λt λf f
not   = λboolean (boolean false true)
```

`not` is exactly "swap the two outcomes". What does `not (not x)` reduce to? It should behave like the identity function. And `not` applied many times?

## Self-composing `not` grows

Church numerals let us say "apply `f` *n* times":

```text
to_church n = switch n {
  0: λf λx x
  _: λf λx (f (to_church n-1 f x))
}
```

Apply `not` 16, 32, 64 and 128 times and look at the *size* of the result:

<!-- expect: Result: λa (a false true false true -->
```bend
true = λt λf t
false = λt λf f
not = λboolean (boolean false true)

to_church n = switch n {
  0: λf λx x
  _: λf λx (f (to_church n-1 f x))
}

main = ((to_church 16) not)
```

The result is a long term — `λa (a false true false true ...)` — whose length grows **in proportion to *n***: roughly 190, 370, 720 and 1,420 characters for 16, 32, 64 and 128 applications. Of course: each `not` wraps the previous one in another layer of `(boolean false true)`, and nothing ever collapses. Compose it 2²⁴ times and you'd need gigabytes just to hold the answer.

## Fusing: write it so the layers cancel

Rewrite `not` so its two lambda arguments are **lifted to the top**, shared between both branches:

```text
not        = λboolean (boolean false true)
fusing_not = λboolean λt λf (boolean f t)
```

Both versions mean the same thing, but they have different *shapes*. Compose the second one a few thousand times:

<!-- expect: Result: λa λb λc (a c b) -->
```bend
fusing_not = λboolean λt λf (boolean f t)

to_church n = switch n {
  0: λf λx x
  _: λf λx (f (to_church n-1 f x))
}

main = ((to_church 0xFFF) fusing_not)
```

The answer is a tiny, **constant-size** term, `λa λb λc (a c b)`, no matter how many times you compose — 4,095 here. (Because 4,095 is odd, the result swaps; 4,096 would give `λa λb λc (a b c)`, the identity-like shape.) Interactions are about 17 per application (69,621 total), the cost of building the numeral, with no growth in the result.

Why does it work? Reduce `(fusing_not (fusing_not x))` by hand:

```text
(fusing_not (fusing_not x))
 = (fusing_not λtλf (x f t))          ; inner call
 = λt1 λf1 (λtλf (x f t) f1 t1)       ; outer call
 = λt1 λf1 (x t1 f1)                  ; substitute f1, t1 for f, t
```

Each application of `fusing_not` *absorbs* its argument into the lambda that was already open, so the term never gets bigger: swapped twice, back to `x`. In the non-fusing version, `boolean` is applied *inside* an expression that stays closed until the end, so layers pile up.

## The rule of thumb

> **Push linear lambdas to the top, and duplicating lambdas to the bottom.**

- A *linear* lambda uses its variable exactly once. Lifting it above a `match`/branch point means the branches share it without duplicating anything. (Like `t` and `f` in `fusing_not`.)
- A *duplicating* lambda uses its variable more than once. Pushing it **down** into the branch that actually needs it avoids duplicating the variable for the branch that doesn't.

## Example: Scott naturals and `add`

A natural number as a Scott encoding:

```text
zero = λs λz z
succ = λpred λs λz (s pred)
```

A straightforward `add`:

```text
add = λa λb
  let case_succ = λa_pred (succ (add a_pred b))
  let case_zero = b
  (a case_succ case_zero)
```

Here `b` is used in *both* `case_succ` and `case_zero`, so the compiler must duplicate it — even though only one branch will ever run. That is a wasted dup on every step. The fusing form pushes `b` down into the branches as a lambda parameter:

```text
fusing_add = λa
  let case_succ = λa_pred λb (succ (fusing_add a_pred b))
  let case_zero = λb b
  (a case_succ case_zero)
```

Now `b` is bound separately in each branch, used once in each: no duplication. `fusing_add` also fuses on its first argument: `λx (fusing_add two x)` normalises to a small term, whereas `λx (fusing_add x two)` does not, because `a` is the thing being matched on.

## How does this show up in Bend programs?

You rarely hand-write `λ` terms in Bend. Fusion matters when:

- you write **higher-order combinators** that are composed many times (parsers, pipelines, transformers);
- you build a **library of Church/Scott-encoded data** and want it to stay cheap;
- you read the compiler's output (`bend desugar`) and wonder why some definition is expensive.

For ordinary `def` code, the same principle appears in two simple habits:

- **Don't duplicate a value you only need in one branch.** Match first, *then* use it in the branch that needs it:

<!-- expect: Result: 7 -->
```bend
def pick(flag, big):
  # `big` is used in one branch only: no need to duplicate it before the `if`
  if flag:
    return big + 1
  else:
    return 0

def main():
  return pick(1, 6)
```

- **Keep linear data linear.** Thread a value through a function once rather than reading it in several places, so the compiler never inserts a dup (Beginner 7).

## Common mistakes

- **Assuming equivalent definitions have equivalent cost.** `not` and `fusing_not` are the same function with wildly different behaviour under repeated composition.
- **Duplicating a variable above a branch** when only one branch needs it.
- **Expecting fusion to happen for you.** The compiler does not restructure your lambdas this way; you write the fusing form.
- **Looking for fusion in data-heavy code.** It applies to *composing functions*, not to walking big structures.

## Exercises

1. Run the non-fusing `not` composition for n = 16, 32, 64 and measure the output length yourself.
2. Show that `fusing_not` composed 4,096 times gives `λa λb λc (a b c)`.
3. Write a fusing `and` and compose it with itself.
4. Write the Church successor in fusing style and compose it 1,000 times.
5. Reduce `(fusing_not (fusing_not (fusing_not x)))` by hand and check it against `bend run-c`.
6. Write `fusing_add` and test `λx (fusing_add two x)` vs `λx (fusing_add x two)` with `bend run-c -s`.
7. Rewrite a function of yours that duplicates an argument above an `if` so it doesn't.
8. Write a pipeline combinator `compose_n(f, n)` that stays small for a linear `f`.

## Recap

- HVM shares work, so composing functions can be nearly free — if they **fuse**.
- A fusing definition has its linear lambdas lifted to the top and shared by the branches; duplicating lambdas live in the branch that uses them.
- `not` grows linearly when composed; `fusing_not` stays constant size.
- In ordinary code: don't duplicate what only one branch needs, and keep linear data linear.

Next: [Laziness & recursion →](08-laziness-and-recursion.md)
