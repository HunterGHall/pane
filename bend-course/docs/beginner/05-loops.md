# 5. Recursion instead of loops

## What & why

Bend has no `for` and no `while`. A loop needs a variable that changes on every pass, and in Bend nothing changes. Instead you repeat work the functional way: a function **calls itself** with new arguments. Every loop you know can be written this way, and — here's the payoff — recursion is exactly the shape HVM can split across cores.

Bend also has two special statements built for *structured* recursion over data, `fold` and `bend`. This lesson covers plain recursion and `bend`; `fold` arrives with lists in lesson 9.

## Recursion with an `if`

Every recursive function has a **base case** (stop) and a **recursive case** (smaller problem):

<!-- expect: Result: 3628800 -->
```bend
def factorial(n):
  if n == 0:
    return 1
  else:
    return n * factorial(n - 1)

def main():
  return factorial(10)
```

!!! warning
    Always write `n - 1` with spaces. `n-1` (no spaces) is a *single name* — hyphens are legal in identifiers — and the compiler will say `Unbound variable 'n-1'`.

There is no call-stack limit to blow: Bend's recursion depth is bounded by memory, not by a stack. (Contrast with Python's recursion limit.)

## Counting with `switch`

For counting down from a number, `switch` is the idiomatic tool, and the `n-1` name from lesson 4 is the predecessor:

<!-- expect: Result: 55 -->
```bend
def sum_to(n):
  switch n:
    case 0:
      return 0
    case _:
      return n + sum_to(n-1)

def main():
  return sum_to(10)
```

Here `n-1` *is* the intended identifier: in the `_` case after `case 0`, it is bound to `n - 1`. It's the one place the hyphenated name is on purpose.

## Accumulators

A function that does `n + sum_to(n-1)` has to wait for the recursive call before adding. Passing a running total as an argument avoids that:

<!-- expect: Result: 5050 -->
```bend
def sum_to(n, total):
  if n == 0:
    return total
  else:
    return sum_to(n - 1, total + n)

def main():
  return sum_to(100, 0)
```

This is the functional answer to `total += n` in a loop: the "loop variable" and the "accumulator" are just parameters.

Remember the 24-bit limit: `sum_to(100000, 0)` is 5,000,050,000, which wraps. Keep your answers under 16,777,215.

## Several state variables

Loops with more than one moving part simply take more parameters. Fibonacci in a loop shape:

<!-- expect: Result: 6765 -->
```bend
def fib(n, a, b):
  if n == 0:
    return a
  else:
    return fib(n - 1, b, a + b)

def main():
  return fib(20, 0, 1)
```

Contrast with the naive `fib(n - 1) + fib(n - 2)`: that version is fine for small `n`, and *can* run in parallel (the two calls are independent), but it does exponential work. Algorithm choice still matters.

## `bend`: a loop that builds data

`bend` is a statement that behaves like a recursive function written inline. You give it state variables and a stop condition; `fork(...)` is the "next iteration":

<!-- expect: Result: [1, 2, 3, 4, 5] -->
```bend
def main():
  bend i = 1:
    when i <= 5:
      result = List/Cons(i, fork(i + 1))
    else:
      result = List/Nil
  return result
```

Read it as a loop: *start with `i = 1`; while `i <= 5`, produce a `Cons` cell and continue with `i + 1`; otherwise stop with `Nil`.* It can carry several state variables:

<!-- expect: Result: [1, 2, 4, 8, 16] -->
```bend
def main():
  bend i = 0, value = 1:
    when i < 5:
      result = List/Cons(value, fork(i + 1, value * 2))
    else:
      result = List/Nil
  return result
```

The real power appears when `fork` is used *twice* — that builds a tree, and the two branches are independent, so they run in parallel. We'll do that in lesson 10; it's the single most important pattern in Bend.

## Accumulating without building: sum over a range

Sometimes you just want a number out of a loop. `bend` returns whatever the `else` branch returns, so thread an accumulator:

<!-- expect: Result: 285 -->
```bend
def main():
  bend i = 0, total = 0:
    when i < 10:
      result = fork(i + 1, total + i * i)
    else:
      result = total
  return result
```

(The sum of the squares 0² … 9².)

## Common mistakes

- **Missing base case.** The function never stops; the program runs until you interrupt it. Every recursive function needs a branch that doesn't recurse.
- **`n-1` instead of `n - 1`.** A hyphen inside a name is part of the name.
- **Not making progress.** `f(n)` calling `f(n)`, or recursing on a number that never reaches the base case (`sum_to(-1)` with unsigned wrap-around eventually does, after 16 million steps!).
- **Looking for `for`.** Reach for a recursive function, `bend`, or (soon) `fold`.
- **Putting `fork` outside `when`.** `fork` is only available in the `when` branch.
- **Forgetting `else` in `bend`.** Like `if`, it's required: that's the base case.

## Exercises

1. Write `power(base, exp)` recursively and compute `3 ** 8` (6561) with it.
2. Write `count_down(n)` using `bend` that returns the list `[n, n-1, ..., 1]`.
3. Write `sum_digits(n)` using `n % 10` and `n / 10` (stop when `n` is `0`).
4. Write `gcd(a, b)` with Euclid's algorithm (`gcd(a, b) = gcd(b, a % b)`; stop when `b` is `0`).
5. Use `bend` to build the list of the first ten odd numbers.
6. Write `collatz_steps(n)` counting how many steps it takes to reach `1` (even: `n / 2`, odd: `3 * n + 1`). `collatz_steps(27)` is `111`.
7. Use `bend` with an accumulator to compute the sum of all multiples of 3 below 100.
8. Write `is_prime(n)` with a helper that tries divisors from 2 upward.

## Recap

- No loops: repeat work by recursion with a base case, or with the `bend` statement.
- Pass accumulators and extra state as parameters.
- `switch` counts down neatly; `n-1` there is the predecessor name — but in expressions, always write `n - 1` with spaces.
- `bend` + `fork` is a loop that builds data; using `fork` twice builds trees that run in parallel.

Next: [Functions →](06-functions.md)
