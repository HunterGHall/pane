# 7. Linearity & duplication

## What & why

Other languages make you think about memory: Rust has ownership and borrowing, C has `malloc`/`free`, Python has a garbage collector. Bend does none of that — and it never needs a GC — because of one design decision: **every value is used at most once, and when you use a value more than once, the runtime copies it for you.** The technical word is that Bend is *linear* (strictly, *affine*).

You don't have to think about this to write Bend. But a few consequences are worth knowing now, because they explain performance, parallelism, and a couple of sharp edges you'll meet in the advanced lessons.

## Use a variable twice: it's duplicated

<!-- expect: Result: ([1, 2, 3], [1, 2, 3]) -->
```bend
def main():
  xs = [1, 2, 3]
  return (xs, xs)       # xs is used twice
```

You wrote nothing special, yet both halves of the tuple are full copies. Behind the scenes the compiler turned `xs` into an explicit **duplication node** (`dup`) that hands out two copies. Duplication is *lazy and shared*: HVM doesn't copy the whole list up front; it copies a piece only when something actually needs to look at it. In practice, duplicating even huge data is cheap.

## Don't use a variable: it's erased

A value you never use is freed immediately:

<!-- expect: Result: 1 -->
```bend
def main():
  unused = [1, 2, 3, 4, 5]
  return 1
```

Memory is reclaimed the instant a value is dropped (the runtime keeps reference counts implicitly through its graph rewrites). That's why there's no garbage collector and no GC pauses, and why you also never see a "use after free" or a data race: values are immutable, and sharing is by logical copy.

## Where the cost shows up

Duplication of *data* is lazy and cheap. What costs is the **work** you do. Bend evaluates a bound value once and shares the result:

<!-- expect: Result: 13530 -->
```bend
def fib(n):
  if n < 2:
    return n
  else:
    return fib(n - 1) + fib(n - 2)

def main():
  x = fib(20)      # computed once
  return x + x
```

Running this with `bend run-c -s` reports about **306,000** interactions (the unit of work; more in Advanced 1).

## `use`: inline instead of share

The `use` statement does the opposite of sharing: it pastes a *copy of the expression* wherever the name appears.

<!-- expect: Result: 13530 -->
```bend
def fib(n):
  if n < 2:
    return n
  else:
    return fib(n - 1) + fib(n - 2)

def main():
  use x = fib(20)      # pasted twice: fib(20) + fib(20)
  return x + x
```

That version reports about **613,000** interactions — exactly double, because `fib(20)` ran twice. So:

- Plain `x = expr` — evaluate once, share the result. This is what you want almost always.
- `use x = expr` — substitute the expression. Good for *cheap* things (a constant, a variable, a small tuple), where it avoids creating a duplication node.

<!-- expect: Result: (7, 7) -->
```bend
def main():
  use pair = (3, 4)
  (a, b) = pair
  (c, d) = pair
  return (a + b, c + d)
```

## Linearity gives you parallelism

Because two uses of one value are independent copies, and nothing can mutate either, HVM is free to evaluate *anything that doesn't depend on something else at the same time*. Look at this:

<!-- expect: Result: 8 -->
```bend
def slow(n):
  if n == 0:
    return 1
  else:
    return slow(n - 1) + slow(n - 1)   # two independent calls

def main():
  return slow(3)
```

The two recursive calls share no variables with each other, so HVM can run them on different cores. That's the entire "programming model" for parallelism: write independent subproblems, and they run in parallel. Lesson 10 and Advanced 3 explore exactly which shapes parallelise.

## Lambdas and duplication: a sharp edge

Lambdas can be duplicated too (a function used twice is two functions). That works fine — with one exception that is easy to hit as you get comfortable:

> A lambda that itself duplicates one of its variables must not be duplicated.

For example, `lambda x: x + x` duplicates `x`. If a higher-order function such as a hand-written `map` uses that lambda twice (it does: once per list element), you can get wrong results or a runtime error. The rule of thumb for now: **write either your higher-order function or the function you pass to it so that it doesn't duplicate, not both.** Advanced lesson 2 explains why (superpositions colliding) and gives safe patterns. Everything in the Beginner and Intermediate levels stays on the safe side.

## Comparison for the curious

| Concern | Rust | Python | Bend |
| --- | --- | --- | --- |
| Who frees memory? | the borrow checker's ownership rules | the garbage collector | erasure when a value is unused |
| Using a value twice | `.clone()` or borrow | free (shared reference) | automatic lazy duplication |
| Mutation | `mut` | everywhere | none |
| Data races | prevented by `Send`/`Sync` | possible | impossible — nothing is shared mutably |

## Common mistakes

- **Reaching for mutation.** There is none. Return a new value instead.
- **Using `use` on an expensive expression.** It does the work once per occurrence. Use a plain binding to share a result.
- **Worrying about copying lists.** Duplication is lazy; copy freely, but measure with `-s` when performance matters.
- **Passing a duplicating lambda to a higher-order function that duplicates it.** See the sharp edge above and Advanced 2.
- **Being surprised by unused parameters.** An argument you never use is simply erased, silently.

## Exercises

1. Return `(xs, xs)` for a list of five numbers and check you get two copies.
2. Write `square(x)` as `x * x` — `x` is used twice. Does it work? (It does: numbers duplicate trivially.)
3. Run the two `fib(20)` programs above with `bend run-c -s` and compare their `ITRS` counts yourself.
4. Write a function that ignores its second argument; call it with an expensive expression such as `fib(25)` and see how fast it is. Why?
5. Write `pair_up(x)` returning `(x, x)` and call it with a tuple argument.
6. Use `use` for a cheap constant in a function that uses it three times.
7. Explain in your own words why Bend has no data races.
8. Write `slow(n)` as above for `n = 20` and run it with `-s`. (It does `2^20` leaf calls.)

## Recap

- Every value is used once; extra uses create lazy, shared duplicates automatically; unused values are erased immediately.
- That is Bend's whole memory model: no GC, no borrow checker, no mutation, no data races.
- A plain binding shares a computed result; `use` re-evaluates the pasted expression each time.
- Independent expressions run in parallel — the foundation of everything in lesson 10.
- Don't duplicate a lambda that itself duplicates (Advanced 2).

Next: [Strings & characters →](08-strings.md)
