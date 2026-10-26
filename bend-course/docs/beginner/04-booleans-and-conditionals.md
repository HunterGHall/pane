# 4. Conditionals

## What & why

Programs make decisions. Bend has `if`/`elif`/`else`, `switch` for numbers, and `match` for data types (lesson 9 and Intermediate 2). The first thing to know: **there is no boolean type.** A "true" value is any non-zero `u24`, "false" is `0`, and comparisons return `1` or `0`.

## `if` / `elif` / `else`

<!-- expect: Result: "teen" -->
```bend
def describe(age):
  if age < 13:
    return "child"
  elif age < 20:
    return "teen"
  else:
    return "adult"

def main():
  return describe(15)
```

Two rules differ from Python:

1. **`else` is mandatory.** Every `if` must have an `else`.
2. **Every branch must `return`** (or assign — see below). A function can't "fall off the end".

The condition must be a `u24`: `0` takes the `else` branch, anything else takes the `if` branch.

<!-- expect: Result: ("yes", "no") -->
```bend
def truthy(n):
  if n:
    return "yes"
  else:
    return "no"

def main():
  return (truthy(7), truthy(0))
```

## Branches that compute a value

You don't have to `return` inside every branch if you're picking a value and carrying on — assign in each branch, then continue:

<!-- expect: Result: 25 -->
```bend
def main():
  n = 5
  if n % 2 == 0:
    half = n / 2
  else:
    half = n * n
  return half
```

Both branches must define the same names. But note the restriction from lesson 1: **no early `return` in the middle of a function** — a `return` ends the function only at the very end of a block, or in a branch where every branch returns.

## Combining conditions

There's no `and`, `or`, or `not`. Because comparisons are `1`/`0`, use the bitwise operators on comparisons (parenthesise them for readability):

<!-- expect: Result: (1, (0, (1, 0))) -->
```bend
def main():
  x = 7
  both = (x > 5) & (x < 10)        # and
  both2 = (x > 5) & (x > 100)
  either = (x > 100) | (x == 7)    # or
  negated = (x > 5) ^ 1            # not (flips 1 and 0)
  return (both, both2, either, negated)
```

!!! warning
    `&`, `|` and `^` evaluate **both** sides. There is no short-circuiting — fine for numbers, but both sides of a condition always run. Also keep results to `0`/`1`: `^ 1` as "not" only works if the value is exactly `0` or `1`. (`(x > 5)` always is.)

For decisions that depend on one another, nest `if`s instead:

<!-- expect: Result: "safe" -->
```bend
def check(a, b):
  if b == 0:
    return "undefined"
  else:
    if a / b > 2:
      return "big"
    else:
      return "safe"

def main():
  return check(6, 3)
```

## `switch` on numbers

When you're choosing among small numbers, `switch` reads better than an `if` chain. Cases must be `0`, `1`, `2`, … in order, and the last case must be `_`:

<!-- expect: Result: ("Mon", ("Wed", "?")) -->
```bend
def day(n):
  switch n:
    case 0:
      return "Mon"
    case 1:
      return "Tue"
    case 2:
      return "Wed"
    case _:
      return "?"

def main():
  return (day(0), day(2), day(40))
```

In the `_` case, the original number minus the cases you've covered is bound as `n-3` (here, since cases `0`, `1`, `2` came first):

<!-- expect: Result: 4 -->
```bend
def main():
  switch n = 7:
    case 0:
      return 100
    case 1:
      return 101
    case 2:
      return 102
    case _:
      return n-3
```

(`7 - 3 = 4`.) That odd-looking `n-3` name is how Bend gives you the predecessor without a subtraction; you'll use it for counting down in lesson 5.

## `match` is for data

`match` chooses on the *constructor* of a data value (a list, a `Maybe`, your own types). A preview:

<!-- expect: Result: "empty" -->
```bend
def kind(xs):
  match xs:
    case List/Nil:
      return "empty"
    case List/Cons:
      return "non-empty"

def main():
  return kind([])
```

You'll use `match` constantly from lesson 9 onward.

## Common mistakes

- **Writing `if x:` with no `else`.** It won't compile; always include one.
- **Using `and`/`or`/`not`.** They don't exist. Use `&`, `|`, `^ 1` on parenthesised comparisons.
- **Dropping the parentheses when it matters.** Comparisons bind tighter than `&` and `|`, so `x > 5 & x < 10` happens to work — but `^ 1` for "not" needs parentheses around what it flips, and parenthesised conditions are easier to read.
- **Early `return`.** Not allowed mid-function; restructure with `if`/`else` where both branches return.
- **Switch cases out of order** or without the final `_`.
- **Comparing strings or lists with `==`.** `==` is only for numbers. Use `String/equals(a, b)` for strings (lesson 8).

## Exercises

1. Write `sign(n)` using `i24` numbers (`+5`, `-3`, `+0`) that returns `-1`, `0` or `1`.
2. Write `max(a, b)` and `min(a, b)`.
3. Write `in_range(x, lo, hi)` returning `1` when `lo <= x <= hi`.
4. Write `fizzbuzz(n)` returning `"FizzBuzz"`, `"Fizz"`, `"Buzz"` or `"other"`.
5. Use `switch` to turn a month number (0–11) into a number of days (ignore leap years; 3 for Apr/Jun/Sep/Nov style months is the fun part).
6. Write `is_leap(year)` using `%` and your boolean operators.
7. Rewrite `describe` from the top of this lesson using `switch` on `age / 10` instead.
8. Explain why `(a > 0) & (b / a > 1)` can still divide by zero.

## Recap

- No boolean type: `0` is false, any other `u24` is true; comparisons return `1`/`0`.
- `if`/`elif`/`else` always needs an `else`, and every branch must `return` or assign the same names.
- Combine conditions with `&`, `|`, `^ 1` — on parenthesised conditions, with no short-circuiting.
- `switch` is for numbers (cases `0, 1, 2, …, _`); `match` is for data.

Next: [Recursion instead of loops →](05-loops.md)
