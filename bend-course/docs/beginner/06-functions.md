# 6. Functions

## What & why

Functions are the center of Bend: your whole program is a set of `def`s, and the runtime is essentially a function-application machine. Functions are also *values* — you can pass them around, return them and store them in data. This lesson covers definitions, calling conventions, lambdas, closures and partial application.

## Defining and calling

<!-- expect: Result: 14 -->
```bend
def square(x):
  return x * x

def sum_of_squares(a, b):
  return square(a) + square(b)

def main():
  return sum_of_squares(2, 3) + 1
```

- Parameters are listed in parentheses; the body is an indented block ending in `return`.
- Order of definitions doesn't matter: `main` can call a function defined later.
- There is no overloading; a name refers to exactly one function.

A function can take no parameters. Such a definition is a **constant**, and you refer to it by name without `()`:

<!-- expect: Result: 100 -->
```bend
def limit():
  return 100

def main():
  return limit
```

## Annotated functions

You may annotate parameters and results; the compiler then checks every call:

<!-- expect: Result: 2.500 -->
```bend
def half(x: f24) -> f24:
  return x / 2.0

def main() -> f24:
  return half(5.0)
```

(Annotations are optional everywhere. We'll use them where they help the reader.)

## Named arguments

When you call a function by name you can label arguments, in any order after the positional ones:

<!-- expect: Result: (12, 7) -->
```bend
def rect(w, h):
  return w * h

def main():
  return (rect(h = 3, w = 4), rect(7, h = 1))
```

## Lambdas

A **lambda** is an anonymous function. Write it with `lambda` (or the symbol `λ`):

<!-- expect: Result: (10, 7) -->
```bend
def main():
  double = lambda x: x * 2
  add = lambda a, b: a + b
  return (double(5), add(3, 4))
```

A lambda with several parameters is really a chain of one-parameter lambdas, which makes **partial application** work: supply some arguments and get a function back.

<!-- expect: Result: 15 -->
```bend
def main():
  add = lambda a, b: a + b
  add10 = add(10)       # a function still waiting for b
  return add10(5)
```

Top-level `def` functions can be partially applied too:

<!-- expect: Result: 21 -->
```bend
def volume(l, w, h):
  return l * w * h

def main():
  slab = volume(7, 3)   # waiting for h
  return slab(1)
```

!!! note
    Bend does not let you chain calls like `f(a)(b)`. Bind the intermediate result to a name first (`g = f(a)`, then `g(b)`), as above.

## Closures

A lambda remembers the variables around it:

<!-- expect: Result: (13, 25) -->
```bend
def make_adder(n):
  return lambda x: x + n

def main():
  add3 = make_adder(3)
  add15 = make_adder(15)
  return (add3(10), add15(10))
```

`make_adder` returns a *new function* each time, each carrying its own `n`.

## Functions as arguments

Because functions are values, higher-order code is everyday code:

<!-- expect: Result: (16, 11) -->
```bend
def twice(f, x):
  return f(f(x))

def main():
  double = lambda x: x * 2
  inc = lambda x: x + 1
  return (twice(double, 4), twice(inc, 9))
```

And composition:

<!-- expect: Result: 23 -->
```bend
def compose(f, g):
  return lambda x: f(g(x))

def main():
  double = lambda x: x * 2
  inc = lambda x: x + 1
  double_then_inc = compose(inc, double)   # inc(double(x))
  return double_then_inc(11)
```

Lesson 9 and Intermediate 4 put this to work with `map`, `filter` and `reduce` on lists.

## Local functions

You can define a function inside another; it captures the surrounding variables:

<!-- expect: Result: 106 -->
```bend
def main():
  offset = 100
  def shift(x):
    return x + offset
  return shift(6)
```

## Tuples in, tuples out

To return several values, return a tuple and destructure it:

<!-- expect: Result: (3, 1) -->
```bend
def divmod(a, b):
  return (a / b, a % b)

def main():
  (q, r) = divmod(10, 3)
  return (q, r)
```

## Statements vs. the final `return`

A function body is a sequence of bindings followed by exactly one result: the final `return`, or an `if`/`switch`/`match` whose branches all return (lesson 4). There is no early exit. When you want one, structure the function so the early case is an `if` branch and the rest is its `else`:

<!-- expect: Result: "negative" -->
```bend
def classify(n: i24):
  if n < +0:
    return "negative"
  else:
    if n == +0:
      return "zero"
    else:
      return "positive"

def main():
  return classify(-5)
```

## Functions are names too

Functions use the same namespace as variables, and `/` in a name is just a character. The convention `Type/function` (like `List/length`) groups functions by the type they work on; you'll write your own such names from lesson 9.

## Common mistakes

- **Calling a constant with parentheses.** `limit()` vs `limit`: a zero-parameter `def` is used bare.
- **Chaining calls** like `make_adder(3)(10)`. Name the intermediate value.
- **Forgetting `return`.** A function whose last line is a bare expression won't compile.
- **Wrong argument count.** With a *named* function you must supply all arguments or none of the named style; partial application only works positionally.
- **Writing `lambda x -> ...`.** The syntax is `lambda x: expression`.
- **Capturing and re-using a lambda many times without thinking about cost.** A variable used twice is duplicated (lesson 7); duplicating a lambda that itself duplicates variables has a sharp edge — see Advanced 2.

## Exercises

1. Write `cube(x)` and use it to compute `cube(4) + cube(3)`.
2. Write `average(a, b)` using integer division and test it on `(7, 10)`.
3. Write `apply_n(f, n, x)` that applies `f` to `x` exactly `n` times (use recursion).
4. Use `apply_n` to compute `2 ** 10` by doubling `1` ten times.
5. Write `flip(f)` that returns a function swapping the arguments of a two-argument `f`.
6. Make `adder3 = make_adder(3)` and compute `adder3(adder3(adder3(0)))`.
7. Write `curry3` turning `f(a, b, c)` into a function you can call as `g(a)`, then `h(b)`, then `h2(c)`.
8. Write `sum_range(lo, hi)` recursively, with a local helper function that carries the accumulator.

## Recap

- `def name(params): ... return` defines a function; zero-parameter definitions are constants used without `()`.
- Lambdas (`lambda x, y: ...`) are values; multi-parameter lambdas and `def`s support partial application.
- Closures capture surrounding variables; functions can be passed, returned and composed.
- No early return and no chained calls: restructure with `if`/`else` and intermediate names.

Next: [Linearity & duplication →](07-linearity-and-duplication.md)
