# 2. Duplications & superpositions

## What & why

Bend is *linear*: every value is meant to be used once. When you use a variable twice, the compiler inserts a **duplication** (`dup`) that hands out two copies. The mirror image of a duplication is a **superposition** (`sup`): one value that is *two values at once*. Together they are the machinery behind copying in HVM, and they explain the single most confusing failure mode in Bend — wrong answers or `<Invalid>` results when a lambda that duplicates something gets itself duplicated.

You rarely write a `dup` or a `sup` by hand. This lesson shows what they are so you can recognise the symptoms and the fixes.

## Where dups come from

Use a variable twice and the compiler makes a dup. `bend desugar` shows it:

<!-- expect: Result: (2, 3) -->
```bend
def main():
  f = lambda x: x + 1
  return (f(1), f(2))
```

```text
(main) = let {b c} = λa (+ a 1); ((b 1), (c 2))
```

`f` was used twice, so `let {b c} = ...` splits it into `b` and `c`. In the Fun syntax you can write a dup yourself — `let {x y} = value; ...` — which is how the core language expresses sharing.

Duplicating **numbers** is trivial:

<!-- expect: Result: (5, 5) -->
```bend
main =
  let {a b} = 5
  (a, b)
```

Duplicating a **lambda** or a **data structure** is lazy: HVM adds a duplicator node and copies the value one layer at a time, only when someone looks at it. A thousand-element list "copied" twice costs almost nothing until each copy is consumed.

## Superpositions

A superposition `{a b}` holds two values *simultaneously*. Write one in Fun syntax with braces:

<!-- expect: Result: ({11 12}, {11 22}) -->
```bend
add = λa λb (+ a b)

main = ((add {1 2} 10), (add {1 2} {10 20}))
```

Anything that interacts with a superposition is applied to **both** possibilities, and the result is a superposition of the results: `add {1 2} 10` is `{11 12}`. Two superpositions with the *same label* are matched up element by element: `add {1 2} {10 20}` is `{11 22}` — first with first, second with second — not all four combinations.

(In Bend's Imp syntax, `{1, 2}` clashes with map literals, so sups are written in Fun syntax.)

## Dup meets sup

A duplication that meets a superposition of the same label simply *unpacks* it — one copy gets each half:

<!-- expect: Result: ((1, 2), (10, 20)) -->
```bend
main =
  let {a b} = {1 2}
  let {c d} = {10 20}
  ((a, b), (c, d))
```

Sups nest, and an unconsumed sup just prints as itself:

<!-- expect: Result: {1 {2 3}} -->
```bend
main = {1 {2 3}}
```

You normally never see a sup in a result. When you do, it usually means two copies of something were never separated by the dups that should have claimed them — a sign that a duplication went wrong somewhere.

## Labels

Every dup and sup carries a **label** (a small number the compiler assigns). The interaction rules depend on it:

- A dup meeting a sup with the **same** label *annihilates*: each dup variable receives one half of the sup. This is "unpacking".
- A dup meeting a sup with a **different** label *commutes*: they pass through each other, producing copies of each.

Labels are what let nested duplications stay separate. The compiler makes sure that, in an ordinary linear program, every dup has its own label.

## The sharp edge

The model has one rule you have to respect as a programmer:

> A variable that duplicates another variable must not itself be duplicated.

Concretely: a function that uses its argument twice (so it contains a dup) must not be passed to something that uses *the function* twice (which dups it). The two dups come from the same source, carry the same label, and **destructively interfere**: the result is wrong, or `<Invalid>`, or a `*` where a value should be.

The smallest reproduction:

<!-- expect: Result: <Invalid> -->
```bend
dbl = λx (+ x x)           # uses x twice  -> contains a dup
twice = λf λy (f (f y))    # uses f twice  -> dups f

main = (twice dbl 3)       # should be 12
```

`bend desugar` makes the problem visible:

```text
(dbl)   = λa let {b c} = a; (+ b c)
(twice) = λa let {b c} = a; λd (b (c d))
```

`twice` duplicates `f` into `b` and `c`. But `f` is `dbl`, which contains its own dup. Duplicating `dbl` duplicates *that* dup too — and now two dups with the same label live in the same neighbourhood, so instead of commuting they cancel.

The same thing happens through `map`:

```text
map([1, 2, 3], lambda x: x + x)   # prints [3, 4, *] — wrong
```

`map` duplicates `f` for each element; `lambda x: x + x` duplicates `x`.

When it works: if the function is *linear* (uses its argument at most once) there's no dup inside it, so duplicating it is harmless:

<!-- expect: Result: 12 -->
```bend
dbl = λx (* x 2)           # x used once
twice = λf λy (f (f y))

main = (twice dbl 3)
```

## What to do about it

Choose **one** of the two sides to be dup-free:

1. **Make the function linear.** `x * 2` instead of `x + x`; `x + 1`; `f(x)`. Restructure so each parameter is used once, using helper arguments if needed.
2. **Don't pass the function; inline it.** A list comprehension `[x + x for x in xs]` or a hand-written fold has the doubling logic *in* the loop body, not in a duplicated closure.
3. **Duplicate data, not functions.** Pass numbers or lists into a fold's state (`fold xs with k:`) rather than lambdas that capture and reuse them.
4. **Make the consumer linear.** A higher-order function that uses `f` exactly once (applying it to a single value) never dups it. Folds over lists apply `f` once per element, which is the dup — that is why `map` is the typical victim.

The runtime sometimes detects the clash and reports an error; sometimes it silently returns `<Invalid>`, a `*`, or a wrong number. Treat any of those, especially a stray `*` inside a data structure, as a symptom of this rule.

## Dups in your own tests

Add a test with a *duplicating* function in every higher-order helper you write. If `map` returns `[2, 4, 6]` for `lambda x: x * 2` and garbage for `lambda x: x + x`, you've found out cheaply. Better, document it in the helper's comment — Bend programmers often write `# f must be linear` above `map`.

## Superpositions as a feature

Superposition isn't only a hazard; it's a computational primitive. A function applied to `{a b}` computes both results in one pass, sharing work wherever the two branches agree. Researchers use this for program search and "optimal" evaluation (evaluating many candidate programs at once). In everyday Bend you will not need it, but it is the reason HVM can promise that no work is ever duplicated unnecessarily: shared structure stays shared inside a sup.

## Common mistakes

- **Passing `lambda x: x + x` (or `x * x`) to `map`/`filter`/`reduce`.** The classic. Use `x * 2`, or a comprehension.
- **Treating a stray `*` in output as a bug in your logic.** It is almost always a dup/sup clash.
- **Writing sups in Imp syntax.** `{1, 2}` in Imp is a map literal; use Fun syntax for sups.
- **Assuming the compiler will always warn.** It does not; the failure can be silent.
- **Over-using `use`.** `use` avoids a dup node by inlining an expression, which re-does the work (Beginner 7). It's not a fix for this problem.

## Exercises

1. Reproduce `<Invalid>` with `twice dbl 3`, then fix it two ways.
2. Predict `((add {1 2} {10 20}), (add {1 2} 0))` before running it.
3. Use `bend desugar` on a function that uses its parameter three times and find the dups.
4. Write a `map` that takes a *list of numbers to add* instead of a function, avoiding closures entirely.
5. Show that `map(xs, lambda x: x * 2)` is safe but `map(xs, lambda x: (x, x))` is not.
6. Write a `compose` that is safe for linear functions and test it with `x + 1` and `x * 2`.
7. Find a stray `*` in output by writing `reduce` with a duplicating combiner.
8. Explain, in two sentences, why `[x + x for x in xs]` works when `map(xs, lambda x: x + x)` does not.

## Recap

- Using a variable twice creates a **dup**; a **sup** `{a b}` is one value that is two values at once.
- Same-label dup/sup pairs annihilate; different labels commute. Labels keep nested copies separate.
- A function containing a dup must not itself be duplicated — the two dups share a label and cancel wrongly, giving wrong results, `*`, or `<Invalid>`.
- Fix it by making the function linear, inlining the logic, or passing data instead of closures.

Next: [Parallelism in practice →](03-parallelism-in-practice.md)
