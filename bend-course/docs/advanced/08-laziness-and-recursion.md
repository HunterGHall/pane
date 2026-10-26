# 8. Laziness & recursion

## What & why

Bend evaluates function arguments **eagerly**, and yet recursion works, infinite structures sometimes work, and sometimes a perfectly reasonable recursive function hangs forever. The difference is a single mechanism: **top-level definitions are lazy references**. A recursive call that goes through a top-level definition is only unfolded when something actually needs it. A recursive call that doesn't is unfolded *immediately and endlessly*.

This lesson teaches you to see which is which, so you can write recursive code that terminates — and so you aren't baffled when a program hangs without an error.

## Eager arguments, lazy definitions

Strict (eager) means: before a function runs, its arguments are fully reduced. So `f(g(x))` computes `g(x)` first. That holds for every call in Bend.

Lazy definitions means: a name like `fib` is a **reference** (`@fib` in the net). Nothing is unfolded until something interacts with it. Each unfold copies the body of the definition into the running graph, one layer at a time.

An `if`/`match`/`switch`/`fold` statement compiles to a function with a branch: the branch bodies become **their own top-level definitions**. So when you write

```text
def count(n):
  if n == 0:
    return 0
  else:
    return 1 + count(n - 1)
```

the recursive `count(n - 1)` sits inside the "else" branch's definition. Until the test `n == 0` is decided, that definition is just a reference: it isn't unfolded. When `n` is `0` the `else` branch is thrown away unopened, so recursion stops. This is why *guarded* recursion — a recursive call inside a branch of a `match`/`if`/`switch`/`fold` — terminates.

<!-- expect: Result: 1000000 -->
```bend
def count(n):
  if n == 0:
    return 0
  else:
    return 1 + count(n - 1)

def main():
  return count(1000000)
```

(A million deep, no stack overflow — recursion depth is a memory question, not a stack question.)

## Unguarded recursion never stops

If a recursive call isn't inside a branch, it unfolds forever:

<!-- check: skip -->
```bend
def f(x):
  return f(x + 1)       # unconditional: loops forever

def main():
  return f(0)
```

There's nothing to stop it. This program runs until you interrupt it. It's the same bug as an unconditional infinite loop in any language, just with no output and no error.

## Infinite structures, carefully

A top-level definition with **no arguments** is a lazy constant: referenced, not unfolded, until used. That makes this infinite list work:

<!-- expect: Result: [1, 1, 1] -->
```bend
def ones():
  return List/Cons(1, ones)

def take(n, xs):
  match xs:
    case List/Cons:
      if n == 0:
        return List/Nil
      else:
        return List/Cons(xs.head, take(n - 1, xs.tail))
    case List/Nil:
      return List/Nil

def main():
  return take(3, ones)
```

`ones` refers to itself. `take` only unfolds as many cells as it needs.

But a definition **with arguments** is applied *eagerly*, so the same trick with a parameter hangs:

<!-- check: skip -->
```bend
def nats_from(n):
  return List/Cons(n, nats_from(n + 1))   # builds forever

def main():
  return take(5, nats_from(0))            # hangs
```

The call `nats_from(n + 1)` is an argument of `List/Cons`, so it is evaluated *before* the `Cons` is returned — and it makes another call, and so on. (`ones` had no arguments, so `ones` inside `Cons` was just a reference.)

To generate an infinite or very long structure with parameters, use **`bend`**, which structures the recursion as a guarded `when` branch, with an explicit stop:

<!-- expect: Result: [0, 1, 2, 3, 4] -->
```bend
def nats(limit):
  bend n = 0:
    when n < limit:
      xs = List/Cons(n, fork(n + 1))
    else:
      xs = List/Nil
  return xs

def main():
  return nats(5)
```

## Hand-written lambda recursion

The hanging bugs get nastier when you write recursion with raw lambdas (Church/Scott encodings, Advanced 5). A `map` over a Scott list written the obvious way:

<!-- check: skip -->
```bend
Cons = λx λxs λcons λnil (cons x xs)
Nil  = λcons λnil nil

Map = λf λlist
  let cons = λx λxs (Cons (f x) (Map f xs))
  let nil = Nil
  (list cons nil)

Main = (Map λx (+ x 1) (Cons 1 Nil))      # never finishes
```

The recursive `Map f xs` appears inside `cons`, a lambda that *captures `f`*. A lambda with a free variable can't be turned into a separate definition, so `Map` unfolds its own body inside itself, over and over, before it ever looks at the list.

The fix is to make `cons` and `nil` **closed** lambdas — no free variables — by passing `f` in as an argument:

<!-- expect: Result: 5 -->
```bend
Cons = λx λxs λcons λnil (cons x xs)
Nil  = λcons λnil nil

Map = λf λlist
  let cons = λx λxs λf (Cons (f x) (Map f xs))
  let nil = λf Nil
  (list cons nil f)

Sum = λxs (xs λh λt (+ h (Sum t)) 0)

Main = (Sum (Map λx (+ x 1) (Cons 1 (Cons 2 Nil))))
```

Now `cons` has no free variables, so the compiler can float it out into its own top-level (lazy) definition; the recursion only unfolds when the list is actually a `Cons`.

## Why it works: combinator floating

Two optimisation passes are **on by default** for exactly this reason:

- `float-combinators` lifts every lambda that has no free variables out into a new top-level definition, so it becomes a lazy reference instead of an eagerly unfolded body.
- `linearize-matches` moves the branches of a `match`/`switch` into separate definitions with their free variables passed as arguments, so only the selected branch is ever touched.

Turn them off and recursive programs stop terminating. Try it on `fib`:

```bash
bend run-c -Ono-float-combinators fib.bend      # never finishes
```

Everything in this lesson is a consequence of those passes. When Bend works you're benefiting from them; when you write raw lambdas, you must write them so the passes can do their job.

## How to write terminating recursion

1. **Guard every recursive call** with a branch (`if`, `match`, `switch`, `fold`).
2. **Prefer `fold` and `bend`.** Their recursion is built in and always guarded.
3. **For raw lambdas**, make the recursive part live inside a *closed* lambda: pass any needed variables as parameters (`λf` above) rather than capturing them.
4. **For infinite data**, use an argument-less constant (`ones`) or a `bend`; never a function with parameters that calls itself in a constructor argument.
5. **Test with a timeout** (`timeout 10 bend run-c ...`) while developing recursive code.

## Mutual recursion

If two functions call each other, only one of them has to be "lazy-protected" — the cycle is broken wherever there is a guard:

<!-- expect: Result: (1, 0) -->
```bend
def is_even(n):
  if n == 0:
    return 1
  else:
    return is_odd(n - 1)

def is_odd(n):
  if n == 0:
    return 0
  else:
    return is_even(n - 1)

def main():
  return (is_even(10), is_odd(10))
```

Both are guarded here. Remember, a guard doesn't prove the program terminates (`is_even(-1)` on unsigned numbers runs 16 million steps); it just prevents *runaway unfolding*.

## Common mistakes

- **Unconditional recursion.** `def f(x): return f(x + 1)` loops forever with no message.
- **Infinite data from a function with parameters** (`nats_from(n)`). Use `bend` with a limit, or a constant.
- **Hand-written lambda recursion with captured variables.** Make the handlers closed.
- **Turning off default optimisations** (`-Ono-all`, `-Ono-float-combinators`).
- **Expecting a hanging program to print an error.** It doesn't; add timeouts.
- **Confusing laziness with non-strictness everywhere.** Arguments are strict; only definitions are lazy.

## Exercises

1. Write `ones` and `twos` as constants and take 4 from each.
2. Make `nats_from` work by turning it into a `bend` with a limit.
3. Write a `repeat(x)`-style infinite list as a constant and a function that takes `n` elements from it.
4. Write the Scott-list `Map` and `Filter` in the closed-handler style and test them.
5. Run a deliberately unconditional recursion under `timeout 5` to see it hang.
6. Demonstrate that `-Ono-float-combinators` makes `fib(10)` hang.
7. Take `is_even`/`is_odd` and remove the guard from one; what happens?
8. Write a Church-style `add` that fuses and terminates (Advanced 7).

## Recap

- Arguments are evaluated eagerly; top-level definitions are lazy references, unfolded only when needed.
- `if`/`match`/`switch`/`fold`/`bend` put recursive calls inside lazy branch definitions, so guarded recursion terminates.
- An unconditional recursive call, or a parameterised definition that builds data by recursing in a constructor argument, unfolds forever.
- Raw-lambda recursion must use closed handlers; the default `float-combinators` and `linearize-matches` passes do the rest.

Next: [Custom monads →](09-custom-monads.md)
