# 11. Testing

## What & why

Bend has no built-in test framework: no `#[test]`, no `assert`, no `bend test`. What it does have is **pure functions**, which are the easiest code in the world to test — same input, same output, nothing to mock. So testing in Bend means writing a few tiny helpers once, listing your cases as data, and having a `main` that runs them and reports. This lesson builds that and shows how to organise tests for a real project.

## The simplest test: a function that returns the answer

The quickest way to check something is to run it and look:

<!-- expect: Result: 120 -->
```bend
def factorial(n):
  if n == 0:
    return 1
  else:
    return n * factorial(n - 1)

def main():
  return factorial(5)
```

Fine while exploring. It doesn't scale: you can't see at a glance whether ten things are right, and nothing tells you when a change breaks one.

## A test is a named comparison

Represent a test result as a pair `(name, passed)`:

```bend
def check(name, got, want):
  if got == want:
    return (name, 1)
  else:
    return (name, 0)
```

A test suite is then a **list** of those pairs, and the runner folds over it. Here's a complete mini framework plus a suite:

<!-- stdin: -->
<!-- expect: 3 passed, 0 failed -->
```bend
def concat(a, b):
  fold a with b:
    case String/Cons:
      return String/Cons(a.head, a.tail(b))
    case String/Nil:
      return b

def say(text):
  return IO/print(concat(text, "\n"))

# ---------- the framework ----------

def check(name, got, want):
  if got == want:
    return (name, 1)
  else:
    return (name, 0)

def passed(results):
  fold results:
    case List/Cons:
      (*, ok) = results.head
      return ok + results.tail
    case List/Nil:
      return 0

def print_failures(results):
  with IO:
    match results:
      case List/Nil:
        return wrap(0)
      case List/Cons:
        (name, ok) = results.head
        if ok:
          r <- print_failures(results.tail)
          return wrap(r)
        else:
          * <- say(concat("FAIL: ", name))
          r <- print_failures(results.tail)
          return wrap(r)

def run(results):
  with IO:
    * <- print_failures(results)
    (total, results) = List/length(results)
    p = passed(results)
    * <- say(concat(u24/to_string(p), concat(" passed, ", concat(u24/to_string(total - p), " failed"))))
    return wrap(0)

# ---------- the code under test ----------

def factorial(n):
  if n == 0:
    return 1
  else:
    return n * factorial(n - 1)

def is_even(n):
  return (n % 2) == 0

# ---------- the suite ----------

def tests():
  return [
    check("factorial 0", factorial(0), 1),
    check("factorial 5", factorial(5), 120),
    check("is_even 10", is_even(10), 1)
  ]

def main() -> IO(u24):
  return run(tests)
```

Run it:

```bash
bend run-c tests.bend
```

```text
3 passed, 0 failed
```

When a test fails, the runner names it:

```text
FAIL: factorial 5
2 passed, 1 failed
```

Because everything is a list of pairs, adding a test is adding one line.

## Separating code and tests

Keep the code under test in its own file and have a `tests/` entry point import it:

```text
project/
├── src/
│   ├── numbers.bend      # factorial, is_even, ...
│   └── strings.bend
└── tests/
    ├── framework.bend    # check, passed, print_failures, run
    └── main.bend         # imports src/ and framework, defines the suite
```

`tests/main.bend` starts with `from ../src/numbers import (factorial, is_even)` and `from framework import (check, run)`, defines `tests()`, and ends with `def main(): return run(tests)`.

## Testing strings and lists

`==` compares numbers only, so make a test helper for each structure you compare:

<!-- expect: 2 passed, 0 failed -->
```bend
def concat(a, b):
  fold a with b:
    case String/Cons:
      return String/Cons(a.head, a.tail(b))
    case String/Nil:
      return b

def say(text):
  return IO/print(concat(text, "\n"))

def check_str(name, got, want):
  return (name, String/equals(got, want))

# Two lists of numbers are equal if they have the same elements in order.
def list_eq(xs, ys):
  match xs:
    case List/Nil:
      match ys:
        case List/Nil:
          return 1
        case List/Cons:
          return 0
    case List/Cons:
      match ys:
        case List/Nil:
          return 0
        case List/Cons:
          return (xs.head == ys.head) & list_eq(xs.tail, ys.tail)

def check_list(name, got, want):
  return (name, list_eq(got, want))

def passed(results):
  fold results:
    case List/Cons:
      (*, ok) = results.head
      return ok + results.tail
    case List/Nil:
      return 0

def reverse_string(s):
  acc = String/Nil
  fold s with acc:
    case String/Cons:
      return s.tail(String/Cons(s.head, acc))
    case String/Nil:
      return acc

def main() -> IO(u24):
  with IO:
    results = [
      check_str("reverse", reverse_string("abc"), "cba"),
      check_list("concat lists", List/concat([1, 2], [3]), [1, 2, 3])
    ]
    * <- say(concat(u24/to_string(passed(results)), " passed, 0 failed"))
    return wrap(0)
```

## Testing user types

For your own types, write an `equals` with `match` (or compare a `show` string):

<!-- expect: 1 -->
```bend
type Color:
  Red
  Green

def color_eq(a, b):
  match a:
    case Color/Red:
      match b:
        case Color/Red:
          return 1
        case Color/Green:
          return 0
    case Color/Green:
      match b:
        case Color/Red:
          return 0
        case Color/Green:
          return 1

def main() -> IO(u24):
  with IO:
    * <- IO/print(u24/to_string(color_eq(Color/Red, Color/Red)))
    * <- IO/print("\n")
    return wrap(0)
```

## Property-style tests

Because pure functions are cheap to call in bulk, you can test a *property* over many inputs instead of one: "for every `n` below 200, `reverse(reverse(xs)) == xs`". Generate inputs with a `bend` and fold the checks into one pass/fail:

<!-- expect: all 100 ok -->
```bend
def concat(a, b):
  fold a with b:
    case String/Cons:
      return String/Cons(a.head, a.tail(b))
    case String/Nil:
      return b

# 1 if (n * 2) / 2 == n for every n in [0, limit)
def property_halving(limit):
  bend n = 0:
    when n < limit:
      rest = fork(n + 1)
      ok = ((n * 2) / 2) == n
      r = ok & rest
    else:
      r = 1
  return r

def main() -> IO(u24):
  with IO:
    if property_halving(100):
      * <- IO/print("all 100 ok\n")
    else:
      * <- IO/print("property failed\n")
    return wrap(0)
```

For randomised tests, write a tiny pseudo-random generator (a linear congruential step, `seed * 1103 + 12345`) and thread the seed through a `bend`. Remember the 24-bit wraparound — it makes a perfectly adequate toy generator.

## Static checking is a test too

Don't overlook the cheapest tests:

- **`bend check file.bend`** catches syntax errors, unbound names, non-exhaustive `match`es and (for annotated code) type errors, without running anything. Put it in CI.
- **Type annotations** on numeric functions catch `u24`/`i24`/`f24` mix-ups.
- **`check: fail`-style tests.** Compiler rejections are a feature: a program that must not compile (a missing case) is verified by `bend check` returning non-zero.

## Checking the examples in a course (or a README)

This very course is tested by a script (`tools/check_examples.py`) that extracts every Bend code block from the lessons, runs it with `bend run-c`, and compares the output with what the lesson claims. You can do the same for any documentation: it keeps examples from rotting.

## Smoke-testing programs with IO

For a program that reads and writes, pipe a script into it and check the output (this is what the task tracker's CI does):

```bash
out="$(printf 'add milk\nlist\nquit\n' | bend run-c main.bend '"/tmp/t.txt"')"
echo "$out" | grep -q '1\. \[ \] milk'
```

Always include the `quit`/blank-line sentinel (see the IO lesson on EOF).

## Common mistakes

- **Testing only through `main`'s printed output** — hard to read and easy to miss a changed number. Return named pass/fail pairs.
- **Comparing strings or lists with `==`.** It's numbers only; use `String/equals` or your own `list_eq`.
- **Forgetting that `check` evaluates both sides eagerly.** A test that crashes the evaluation takes the whole run down; keep suites small and ordered.
- **Testing IO code directly.** Extract the pure logic into functions and test those.
- **Overflowing 24 bits in expected values.** Your "expected" number wraps too; compute it carefully.
- **No end marker for piped input.** The run hangs.

## Exercises

1. Add a failing test to the suite and read the report; then fix it.
2. Write `check_list_eq` for lists of strings.
3. Write tests for `msort` from the divide-and-conquer lesson, including empty and one-element lists and a list with duplicates.
4. Write a property test that `sum(map(xs, f))` equals the loop-computed value for 50 generated lists.
5. Write a Bash script that runs every `tests/*.bend` and fails if any prints `failed` with a non-zero count.
6. Write `assert_close(a, b, eps)` for floats.
7. Add tests for the task tracker's pure functions (`mark_done`, `remove`, `render`, `serialize`/`parse_lines`).
8. Make the framework print the **names of passing** tests too, under a `-v` flag passed as a command-line argument.

## Recap

- No built-in framework: a test is `(name, passed)`, a suite is a list, and a 30-line runner prints failures and totals.
- Pure functions test trivially; keep IO thin and test the core.
- Compare strings/lists/types with helpers, not `==`.
- Property tests are a `bend` that checks many inputs; `bend check` and type annotations are free tests.
- Smoke-test IO programs by piping a script — and always end it with a sentinel.

Next: [Capstone: expression calculator →](12-capstone-expression-calculator.md)
