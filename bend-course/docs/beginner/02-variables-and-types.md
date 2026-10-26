# 2. Values, variables & types

## What & why

In Bend, a **variable** is a name for a value. Names are *not* boxes you can change: there is no mutation anywhere in the language. When you "update" something you create a new value and (usually) reuse the name. This feels odd for a few days and then feels like a relief — nothing can change under you, which is exactly why Bend can run things in parallel safely.

## Binding names

```bend
def main():
  x = 10
  y = x * 2
  z = y + x
  return z
```

<!-- expect: Result: 30 -->
```bend
def main():
  x = 10
  y = x * 2
  return y + x
```

Each line creates a new binding. Names can contain letters, digits, `_`, `.` and `/` (the `/` is by convention for namespaces like `List/length`).

## "Reassignment" is rebinding

You can use the same name again, but it creates a *new* variable that shadows the old one:

<!-- expect: Result: 4 -->
```bend
def main():
  x = 1
  x = x + 1   # a new x, built from the old x
  x = x * 2
  return x
```

Nothing was mutated; each `x` is a fresh value. Python's `x += 1` works in Bend too, but it's sugar for exactly this rebinding:

<!-- expect: Result: 11 -->
```bend
def main():
  x = 10
  x += 1
  return x
```

## The basic types

Bend's built-in values are small and few:

<!-- expect: Result: (1, (-2, (3.500, (97, "hi")))) -->
```bend
def main():
  return (1, -2, 3.5, 'a', "hi")
```

| Value | Type | Notes |
| --- | --- | --- |
| `42` | `u24` | unsigned 24-bit integer: 0 to 16,777,215 |
| `+42`, `-42` | `i24` | signed 24-bit integer: the **sign is required** |
| `3.14`, `+0.5` | `f24` | 24-bit float: the **decimal point is required** |
| `'a'` | `u24` | a character is just its Unicode code point (97) |
| `"hi"` | `String` | a list of characters |
| `(1, 2)` | tuple | two or more values |
| `[1, 2, 3]` | `List(u24)` | linked list |
| `*` | `None` | the "nothing" / eraser value |

Surprising, but important: **there are no 64-bit integers.** Every number is 24 bits wide (that's what lets HVM pack a number into a single machine word along with its tag). Lesson 3 covers the consequences.

!!! warning
    `5`, `+5` and `5.0` are three *different* kinds of number. Bend will not stop you from mixing them (unless you add type annotations — see below), but the result is garbage. Always keep the kinds apart.

## Tuples and destructuring

A tuple bundles values. You take it apart by assigning to a pattern:

<!-- expect: Result: (7, 3) -->
```bend
def main():
  pair = (3, 7)
  (a, b) = pair
  return (b, a)
```

You can write the pattern directly, and use `*` to ignore parts:

<!-- expect: Result: 30 -->
```bend
def main():
  (first, *, third) = (10, 99, 20)
  return first + third
```

Tuples nest, and there are no "tuple fields" — you always destructure.

!!! note
    A tuple with more than two elements is really a pair whose second element is another tuple, and the printer shows it that way: `(1, 2, 3)` prints as `(1, (2, 3))`. Only the display is nested; you can still destructure all three at once with `(a, b, c) = ...`.

## Type annotations (optional)

You don't have to write any types. But you can, and Bend will check them:

<!-- expect: Result: 7 -->
```bend
def add(x: u24, y: u24) -> u24:
  return x + y

def main() -> u24:
  return add(3, 4)
```

The annotation after `:` is the parameter's type; `->` gives the return type. Now Bend catches mistakes:

<!-- check: fail -->
```bend
def add(x: u24, y: u24) -> u24:
  return x + y

def main() -> u24:
  return add(3, "four")
```

Annotate the functions you care about, especially anything that takes lists or your own data types — the type checker (Hindley–Milner style) then catches many bugs before you run anything. Un-annotated parameters have the type `Any`, which the checker accepts everywhere. Intermediate lesson 5 goes deeper.

A `_` in a type means "infer this for me":

<!-- check: check -->
```bend
def double(x: _) -> _:
  return x + x
```

## Constants

A top-level definition with no parameters is a constant. Call it by name — no parentheses:

<!-- expect: Result: 3141 -->
```bend
def pi_times_1000():
  return 3141

def main():
  return pi_times_1000
```

(Under the hood *everything* is a function — a "constant" is just a function of no arguments.)

## Common mistakes

- **Expecting `x = x + 1` to change `x` elsewhere.** It only creates a new `x` from this line onward; anything that already captured the old `x` still sees the old value.
- **Writing `5.` or `.5` for floats.** You need digits on both sides: `5.0`, `0.5`.
- **Writing a negative integer without a sign type in mind.** `-5` is an `i24`; `5 - 6` on `u24` *wraps around* to 16777215 (lesson 3).
- **Forgetting the `+` on positive signed numbers.** `+5` is signed; `5` is unsigned. They are not interchangeable.
- **Mixing number kinds** — `1 + 1.5` or `5 + +3`. No error, wrong answer.
- **Using a variable before defining it.** Names must be bound *above* where you use them within a function.

## Exercises

1. Bind `a = 5`, `b = 7`, and return their product plus their sum.
2. Rebind a variable three times to compute `((2 + 3) * 4) - 1` one step at a time.
3. Return a tuple containing a `u24`, an `i24`, an `f24`, a character and a string.
4. Destructure `(1, (2, 3))` and return only the `3`.
5. Annotate `add` with `u24` types, then call it with a string and read the error.
6. Write a constant `seconds_per_day` and return it.
7. What does `main` return for `return 'A' + 1`? Why?
8. Try `return 1 + 1.5`. What do you get? Why shouldn't you trust it?

## Recap

- Variables are immutable names; "updating" means rebinding a new value to the name.
- The basic numbers are `u24`, `i24` (`+`/`-` sign required) and `f24` (decimal point required) — all 24 bits wide.
- Characters are `u24` code points, strings are lists of characters, tuples are destructured by pattern.
- Type annotations are optional but checked; `_` asks Bend to infer.

Next: [Numbers & math →](03-numbers-and-math.md)
