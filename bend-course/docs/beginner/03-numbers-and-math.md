# 3. Numbers & math

## What & why

Numbers are the one place where Bend gives you real hardware speed: arithmetic on native numbers is a single operation, not a tree of lambdas. But the numbers are small (24 bits) and come in three flavours that don't mix. This lesson is about getting that right.

## The three kinds

<!-- expect: Result: (7, (-1, 3.500)) -->
```bend
def main():
  return (3 + 4, -3 + +2, 1.5 + 2.0)
```

Wait — `-3 + +2` adds two `i24`s (written with signs), so the answer is `-1`. The rules:

| Written | Kind | Range |
| --- | --- | --- |
| `7`, `0xFF`, `0b101`, `1_000` | `u24` | 0 … 16,777,215 |
| `+7`, `-7` | `i24` | −8,388,608 … 8,388,607 |
| `7.0`, `-0.5` | `f24` | 24-bit float |

All the usual operators work on all three kinds:

| Operator | Meaning |
| --- | --- |
| `+ - * / %` | add, subtract, multiply, divide, remainder |
| `**` | power (floats only) |
| `== != < > <= >=` | comparisons (result is `1` or `0`) |
| `& \| ^` | bitwise and, or, xor (integers) |
| `<< >>` | bit shifts (unsigned) |

## Integer division

Dividing integers truncates, like Python's `//` for positive numbers:

<!-- expect: Result: (3, 1) -->
```bend
def main():
  return (7 / 2, 7 % 2)
```

For fractions use floats:

<!-- expect: Result: 3.500 -->
```bend
def main():
  return 7.0 / 2.0
```

Division by zero does not crash; it quietly returns 0 for integers. Guard it yourself (lesson 11 shows how with `Result`).

## 24 bits wrap around

This is the big gotcha. There is no overflow error and no promotion to a bigger type — values just wrap:

<!-- expect: Result: (0, 16777215) -->
```bend
def main():
  biggest = 16777215       # 2^24 - 1
  return (biggest + 1, 0 - 1)
```

Subtracting below zero on a `u24` wraps to the top. So: **subtract carefully on unsigned numbers**, and compare before you subtract.

If your problem needs bigger numbers, you represent them yourself (for example a list of digits) or use `i24`/`f24` where the range suits.

## No implicit conversion

Mixing kinds compiles — and gives nonsense, because the bits of one kind get interpreted as another. Convert explicitly:

| Function | Converts |
| --- | --- |
| `u24/to_i24`, `u24/to_f24` | from unsigned |
| `i24/to_u24`, `i24/to_f24` | from signed |
| `f24/to_u24`, `f24/to_i24` | from float (truncates) |

<!-- expect: Result: (3.000, (3, -2)) -->
```bend
def main():
  a = u24/to_f24(3)
  b = f24/to_u24(3.9)
  c = u24/to_i24(5) - +7
  return (a, b, c)
```

A typed function won't let the mistake through:

<!-- check: fail -->
```bend
def bad(x: u24, y: f24) -> f24:
  return x + y

def main():
  return bad(1, 2.0)
```

## Floats and the math library

`f24` has about 6–7 significant digits. The standard library has the usual functions under `Math/`:

<!-- expect: Result: (1.414, (2.000, (3.000, 1.000))) -->
```bend
def main():
  return (Math/sqrt(2.0), Math/floor(2.7), Math/ceil(2.1), Math/sin(Math/PI() / 2.0))
```

Others: `Math/cos`, `Math/tan`, `Math/log(x, base)`, `Math/atan2`, `Math/round`, `Math/asin`, `Math/E()`, `Math/radians`, and more. Constants such as `Math/PI()` are called with parentheses.

## Bitwise tricks

Because numbers are plain 24-bit words, bit operations are cheap:

<!-- expect: Result: (4, (7, (3, (40, 5)))) -->
```bend
def main():
  return (6 & 5, 6 | 5, 6 ^ 5, 5 << 3, 40 >> 3)
```

A common idiom: test evenness with `n & 1`, or halve with `n >> 1`.

## Operator precedence

Standard rules apply (`*` binds tighter than `+`, and so on), left to right; parenthesise anything you aren't sure about.

<!-- expect: Result: (14, (20, 5)) -->
```bend
def main():
  return (2 + 3 * 4, (2 + 3) * 4, 10 - 2 - 3)
```

## Characters are numbers

`'a'` is just `97`. That means arithmetic on characters works, which is handy:

<!-- expect: Result: (98, (25, 90)) -->
```bend
def main():
  return ('a' + 1, 'z' - 'a', 'A' + 25)
```

## Common mistakes

- **Subtracting below zero on `u24`.** `3 - 5` is 16777214, not −2. Use `i24` (`+3 - +5`) or check first.
- **Forgetting the sign** — `5` and `+5` are different kinds. The compiler won't warn unless you annotate types.
- **Using `**` on integers.** It's for floats. For integer powers write a recursive function (lesson 5).
- **Assuming big numbers work.** `factorial(20)` overflows 24 bits long before you see it; results silently wrap.
- **Comparing floats with `==`.** `0.1 + 0.2` isn't exactly `0.3`. Compare within a tolerance.
- **Expecting division by zero to fail loudly.** It doesn't.

## Exercises

1. Compute `17 / 5` and `17 % 5`. Check that `(17 / 5) * 5 + 17 % 5 == 17`.
2. Make `main` return `0 - 1`. Explain the output in terms of 24 bits.
3. Compute `+10 - +25` and `10 - 25` side by side. What's different?
4. Convert `7` to a float, divide by `2.0`, and convert back to `u24`.
5. Use `Math/sqrt` to compute the hypotenuse of a 3–4 right triangle (it's 5.0).
6. Use `&` to test whether `42` is even (`42 & 1` is `0`) and whether `43` is.
7. Multiply `4096 * 4096`. What do you get, and why?
8. Compute the character that comes 3 after `'x'` and return it. (It's `'{'`, code 123.)

## Recap

- Three native kinds: `u24` (bare), `i24` (explicit `+`/`-`), `f24` (with a `.`); all 24 bits wide, all wrapping.
- Convert explicitly with `a/to_b` functions; mixing kinds silently gives garbage unless you annotate types.
- Integer `/` truncates; `**` is for floats; comparisons give `1` or `0`.
- Characters are code points, so character arithmetic is ordinary integer arithmetic.

Next: [Conditionals →](04-booleans-and-conditionals.md)
