# 6. Scopeless lambdas

## What & why

A normal lambda's variable can only be used inside its body. A **scopeless lambda** binds a variable that can be used *anywhere* in the same definition — before, after or far away from the lambda. It sounds like a recipe for chaos, and it is a sharp tool, but it's also one of HVM's most distinctive features: it gives you things like continuations, difference-list-style queues and "write into a hole later" with nothing but lambdas. You will rarely need it. Knowing it exists explains parts of the standard library (`DiffList` uses a related idea) and teaches how HVM treats variables as wires.

Scopeless lambdas live in the lambda-calculus layer of Bend, so the examples here use the Fun syntax (and a few Imp equivalents).

## The `$` sigil

Prefix a lambda's variable with `$`. That variable is now a global wire for the current definition:

<!-- expect: Result: (1, 2) -->
```bend
main = (((λ$x 1) 2), $x)
```

Walk through it:

1. `(λ$x 1)` is a lambda that ignores its argument and returns `1`, but its variable is `$x`.
2. It's applied to `2`, so `$x` becomes `2`.
3. The expression `$x` *outside the lambda* now refers to that value `2`.

The tuple is `(1, 2)`: the result of the application, and the value that was captured. The lambda "returned" two things by one going out the normal way and the other through the wire `$x`.

In Imp syntax it's written `lambda $x: ...`:

<!-- expect: Result: (1, 2) -->
```bend
def main():
  f = lambda $x: 1
  return (f(2), $x)
```

## Rules

- A `$x` must be **used exactly once** in a definition (as the binder), and exactly once as the use. Use a scopeless variable zero times or twice and the compiler rejects the program.
- Scopeless variables are **local to one top-level definition**: a `$x` in `main` and a `$x` in `helper` are unrelated.
- They are *not* transformed or linearised like normal variables: they stay raw wires.
- **Type-checked functions can't contain them.** Leave the function un-annotated (or `unchecked`).

## What if the lambda is never called?

If the lambda is erased, so is the wire it would have filled. The reader of `$x` gets the eraser:

<!-- expect: Result: (2, *) -->
```bend
main =
  let _ = λ$x 1
  (2, $x)
```

## What if it's called twice?

If a lambda is duplicated and then called twice, the single wire receives *both* arguments — as a superposition (Advanced 2):

<!-- expect: Result: (1, (1, {2 3})) -->
```bend
main =
  let f = λ$x 1
  ((f 2), ((f 3), $x))
```

The first two components are the results `1` and `1`. `$x` was filled by both calls, so it holds `{2 3}`. (Which argument comes first in the superposition is the compiler's choice, so don't rely on the order.)

## Example: call/cc

A **continuation** captures "the rest of the computation". With scopeless lambdas, `call/cc` is a handful of lines. The idea: `callcc` runs a callback with an escape function `k`; calling `k v` makes the whole `callcc(...)` expression evaluate to `v`, discarding whatever else the callback was doing.

<!-- expect: Result: 52 -->
```bend
Seq a b = a

CC.lang = λprogram
  let callcc  = λcallback (λ$garbage($hole) (callback λ$hole(0)))
  let result  = (program callcc)
  (Seq result $garbage)

Main = (CC.lang λcallcc
  (+ 10 (callcc λk (+ (k 42) 1729)))
)
```

The program computes `10 + callcc(...)`. Inside, `(k 42)` fires the escape: `callcc` returns `42`, so the answer is `10 + 42 = 52`. The `+ 1729` branch is garbage that never contributes; `$garbage` collects it. The `$hole` is the wire that carries the escaped value to the point where `callcc` returns.

You don't need to follow every wire to see the point: with scopeless lambdas the language gets *non-local control flow* — exceptions, generators, coroutines — without any special runtime support.

## Example: a queue with O(1) enqueue and dequeue

The Bend repository ships a queue built from lambdas and one scopeless variable:

<!-- expect: Result: [1, 2, 3] -->
```bend
# Constant-time queues with just lambdas.
Qnew = λx x
Qadd = λx λq λk (q λc (c x k))
Qrem = λq (q $k λx λxs λp (p x λ$k xs))

main: (List u24) =
  let q = Qnew
  let q = (Qadd 1 q)
  let q = (Qadd 2 q)
  let q = (Qadd 3 q)
  ((Qrem q) λv0 λq
  ((Qrem q) λv1 λq
  ((Qrem q) λv2 λq
  [v0, v1, v2])))
```

A queue is a function that, given a continuation `k`, produces `(c x k)` — the first element and "the rest, still waiting for `k`". Adding an element writes it into the *end* of the queue through the hole `$k`, instead of walking to the end. That is how both ends are O(1).

Interesting, but it's also a good example of why you'd normally reach for `DiffList` or the two-list queue from Intermediate 7: they're far easier to read.

## Dangers

- **Surprising erasure.** A forgotten lambda silently turns the other end of the wire into `*`.
- **Superpositions.** Calling the lambda more than once is a legitimate way to build one — and an easy way to build one by accident.
- **Unreadable code.** A wire can connect two places that are far apart in the source. Use sparingly and comment heavily.
- **No type checking.** All the compiler's help is gone.

## Common mistakes

- **Using `$x` twice** or **not at all**: it must have exactly one binder and one use.
- **Expecting `$x` to be visible in another `def`.** It's local to one definition.
- **Annotating a function that uses scopeless variables.** The checker refuses; drop the annotation.
- **Using them where a normal lambda would do.** They add confusion with no benefit.
- **Relying on the order of a superposition** produced by a doubly-called scopeless lambda.

## Exercises

1. Run `main = (((λ$x 1) 2), $x)` and change `2` to another value; predict the result.
2. Write a function `put_get(v)` that returns `(1, $x)` after applying `λ$x 1` to `v`.
3. Duplicate a scopeless lambda without calling it and see what `$x` becomes.
4. Modify the call/cc example so `k` is never called; what is the result?
5. Use call/cc to implement an early-exit `find_first(pred, xs)` over a Church-style list.
6. Rewrite the queue example in Imp syntax (`lambda $k: ...`).
7. Compare `Qadd` ten thousand times with a two-list queue in `ITRS`.
8. Explain, in your own words, why scopeless variables can't be type-checked.

## Recap

- `λ$x ...` binds a variable usable anywhere in the same definition: a raw wire, filled when the lambda is called.
- Erase the lambda and the wire is `*`; call it twice and the wire is a superposition.
- They enable continuations, O(1) queues and "fill later" holes using only lambdas.
- They are untypable, local to one definition, and hard to read: use them sparingly.

Next: [Fusion →](07-fusion.md)
