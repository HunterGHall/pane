# 5. Lambda encodings

## What & why

In Advanced 1 you saw that Bend has no `Color` type at runtime: a value of your type is a *function*. This lesson shows how that works. Understanding **Church** and **Scott** encodings explains why user types print as lambdas, how `match` and `fold` compile, why `unchecked` exists, and it lets you write your own data types from nothing but `λ` — which the HVM can run very fast.

This is the most theoretical lesson in the course; every idea is small and every example runs.

## Data as functions

A lambda can *be* a data structure if you let the consumer choose what to do with it. The classic example is the boolean:

```text
true  = λt λf t        # "given two options, pick the first"
false = λt λf f        # "given two options, pick the second"
```

To use a boolean you pass it the two outcomes — no `if` required:

<!-- expect: Result: (1, 2) -->
```bend
true = λt λf t
false = λt λf f
and = λa λb (a b false)
or = λa λb (a true b)
not = λa (a false true)
cond = λc λt λe (c t e)

main = ((cond (and true (not false)) 1 2), (cond (or false false) 1 2))
```

`and` says: "if `a` is true give me `b`, otherwise give me `false`" — written as `(a b false)`. This is a **Church encoding**: a value is a function that takes one argument per constructor and calls the right one.

(The syntax here is Fun: `(f a b)` is application and `λx body` a lambda. Types can't describe these terms, so there are no annotations.)

## Church numerals

A number *n* is "apply `f` *n* times":

<!-- expect: Result: (5, 6) -->
```bend
zero = λf λx x
succ = λn λf λx (f (n f x))
add = λa λb λf λx (a f (b f x))
mul = λa λb λf (a (b f))

two = (succ (succ zero))
three = (succ two)

to_num = λn (n λx (+ x 1) 0)

main = ((to_num (add two three)), (to_num (mul two three)))
```

`to_num` converts to a native number by counting applications. Addition and multiplication are just function composition. Church numerals are beautiful and *very* slow for arithmetic — use them to learn, not to compute.

## Scott encodings: data you can take apart

Church encodings make folding easy but pattern matching awkward (the predecessor of a Church numeral is famously hard). A **Scott encoding** stores the *fields* instead of pre-applying the recursion, so `match` is trivial:

```text
Nil  = λc λn n                 # no fields: call the "nil" handler
Cons = λh λt λc λn (c h t)     # call the "cons" handler with head and tail
```

To consume a list, pass one handler per constructor:

<!-- expect: Result: 6 -->
```bend
Nil = λc λn n
Cons = λh λt λc λn (c h t)

Sum = λxs (xs λh λt (+ h (Sum t)) 0)

main = (Sum (Cons 1 (Cons 2 (Cons 3 Nil))))
```

`(xs cons_handler nil_handler)` *is* the match: the list calls whichever handler fits, passing the fields. That is precisely what `match xs:` compiles to. The recursion is explicit (`Sum t`) because Scott encodings carry data, not recursion.

## What Bend does with your types

Bend compiles `type`/`object` declarations to **tagged Scott encodings**. For

<!-- expect: Result: 0 -->
```bend
type Opt:
  Some { v }
  None

def main():
  return 0
```

`bend desugar` shows (trimmed):

```text
(Opt/Some/tag) = 0
(Opt/Some)     = λa λb (b Opt/Some/tag a)

(Opt/None/tag) = 1
(Opt/None)     = λa (a Opt/None/tag)
```

Each constructor takes its fields, then a continuation `b`, and calls it with its **tag number first** and then the fields. A `match` becomes a native `switch` on the tag, with each case a lambda over the fields (`f__C0` in the earlier example). Using a numeric tag lets the runtime select the branch with one `switch` interaction instead of walking a chain of handlers. This is the compiler's default, called `adt-num-scott`.

You can ask for the pure form:

```bash
bend desugar -Oadt-scott types.bend
```

```text
(Opt/Some) = λa λb λ* (b a)
(Opt/None) = λ* λa a
```

Here there are no tags at all: a constructor takes one handler per constructor of the type, ignores the ones it doesn't want (`λ*`) and calls its own with the fields. It is the textbook Scott encoding. `-Oadt-num-scott` (the default) is typically better with large matches because of the `switch`; `-Oadt-scott` can be more compact for types with few constructors.

## Why user types print as lambdas

Now the output from Beginner 11 makes sense:

```text
Result: λa (a Maybe/Some/tag 3)
```

`Maybe/Some(3)` *is* `λa λb (b Maybe/Some/tag a)` applied to `3`: a lambda waiting for a continuation `a`, which it calls with the tag and the field. The printer can't know that shape means "Maybe" — only the shape of numbers, strings, lists and tuples is special-cased in readback.

## Fields, recursion and `fold`

Why does Bend ask you to mark recursive fields with `~`? Because `fold` needs to know which fields to recurse into when it rewrites a `match`. For a `~` field, `fold` replaces `x.field` by a call to the fold function on it. The generated function is an ordinary recursive definition; the `~` is how the compiler finds the recursion in an otherwise untyped lambda soup.

## Encodings and the type checker

Hand-written encodings can't be given Hindley–Milner types (the terms are self-referential in ways HM forbids), and you can't use type annotations on functions that rely on them. Either leave the functions un-annotated, or mark them `unchecked`:

<!-- check: check -->
```bend
def unchecked pair_sum(p: (u24, u24)) -> u24:
  (a, b) = p
  return a + b
```

(`unchecked` makes the *annotation* be trusted without verification. The checker's limits are in Intermediate 5.)

## Writing your own type with lambdas

You can define a whole type this way and mix it with ordinary Bend. A pair that can be taken apart by a continuation:

<!-- expect: Result: 7 -->
```bend
pair = λa λb λk (k a b)
fst = λp (p λa λb a)
snd = λp (p λa λb b)

main = (+ (fst (pair 3 4)) (snd (pair 3 4)))
```

Nothing special is needed: constructors are lambdas, selectors apply the value to a handler.

## When to use hand encodings

- **Almost never** in application code: `type` gives the same thing with names, `match` and exhaustiveness checking.
- **For learning** how the language works.
- **For performance experiments** where you want to control exactly what graph is built.
- **For tricks that need no tags**, like the queue in the next lesson.

## Common mistakes

- **Recursing inside a Church/Scott encoding without care for laziness.** If the recursive call is not inside a lambda that can be floated to its own definition, evaluation may unroll forever. Put the recursion under a handler lambda as above (Advanced 8).
- **Mixing encodings.** A Church numeral is not a Scott `Nat`; don't pass one where the other is expected.
- **Using `==` on encoded data.** Only native numbers compare.
- **Annotating encoded functions** with types. Remove the annotation or add `unchecked`.
- **Expecting readable output.** Convert to a number or string.

## Exercises

1. Write a Church `is_zero` (hint: `n (λx false) true`) and test it on `zero` and `three`.
2. Write Church `exp` (`a` to the power `b` is `b a`) and compute 2³.
3. Implement a Scott `Maybe` (`Some`, `None`) and a `map_maybe`.
4. Implement `Length` and `Map` for the Scott list.
5. Run `bend desugar` on a type with three constructors and explain each constructor's lambda.
6. Compare `-Oadt-scott` and `-Oadt-num-scott` desugaring of the same `match`.
7. Encode a binary tree with Scott encoding and write `Sum`.
8. Show that a Church boolean `xor` can be built from `and`, `or`, `not`.

## Recap

- Data can be functions: a value takes one handler per constructor and calls the right one (Church/Scott encodings).
- Bend compiles `type`/`object` to tagged Scott encodings (`adt-num-scott`), `match` to a `switch` on the tag, `fold` to a recursive function over `~` fields.
- That is why user types read back as lambdas; only numbers, strings, lists and tuples print nicely.
- Encoded terms can't be typed, so leave them un-annotated or `unchecked`.

Next: [Scopeless lambdas →](06-scopeless-lambdas.md)
