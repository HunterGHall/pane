# 8. Error handling & monads

## What & why

Bend has no exceptions. A function that can fail returns a `Result` (success with a value, or failure with a reason) or a `Maybe` (a value or nothing), and the caller has to look. That keeps failures visible in the types — but nesting a `match` after every call gets ugly fast:

```text
match a:
  case Result/Ok:
    match b:
      case Result/Ok:
        ...
```

Bend's answer is the **`with` block**: a small piece of syntax that lets you write the happy path in a straight line while the error plumbing happens behind the scenes. This is the same idea as Haskell's `do` or Rust's `?`, and it's how `IO` works too. This lesson shows how to use it for `Result` and `Maybe` and what's really going on.

## `Result` and `Maybe`, a reminder

<!-- expect: Result: ((1, 5), (0, 0)) -->
```bend
def divide(a, b):
  if b == 0:
    return Result/Err("divide by zero")
  else:
    return Result/Ok(a / b)

def summarise(r):
  match r:
    case Result/Ok:
      return (1, r.val)
    case Result/Err:
      return (0, 0)

def main():
  return (summarise(divide(10, 2)), summarise(divide(1, 0)))
```

Both `Ok` and `Err` hold their payload in `.val`. `Result(O, E)` is generic: `O` is the success type, `E` the error type (here `String`).

## Chaining by hand

Parse two digits, then divide — three fallible steps. Written with plain `match`:

<!-- expect: Result: (1, 21) -->
```bend
def digit(c):
  if (c >= '0') & (c <= '9'):
    return Result/Ok(c - '0')
  else:
    return Result/Err("not a digit")

def parse2_then_halve(a, b):
  match x = digit(a):
    case Result/Ok:
      match y = digit(b):
        case Result/Ok:
          return Result/Ok((x.val * 10 + y.val) / 2)
        case Result/Err:
          return y
    case Result/Err:
      return x

def main():
  match r = parse2_then_halve('4', '2'):
    case Result/Ok:
      return (1, r.val)
    case Result/Err:
      return (0, 0)
```

It works, but every extra step adds a level of nesting. Let's flatten it.

## The `with` block

A `with Type:` block rewrites each line of the form `name <- expr` into "if `expr` is a success, continue with `name` bound; otherwise stop and return the failure". For this to work the type must supply two functions, conventionally named `Type/bind` and `Type/wrap`. **The prelude defines `Result` but not these**, so you define them once:

<!-- expect: Result: ((1, 42), ((0, 0), (0, 0))) -->
```bend
def Result/bind(res, nxt):
  match res:
    case Result/Ok:
      nxt = undefer(nxt)
      return nxt(res.val)
    case Result/Err:
      return res

def Result/wrap(x):
  return Result/Ok(x)

def digit(c):
  if (c >= '0') & (c <= '9'):
    return Result/Ok(c - '0')
  else:
    return Result/Err("not a digit")

def div(a, b):
  if b == 0:
    return Result/Err("divide by zero")
  else:
    return Result/Ok(a / b)

def two_digits(a, b):
  with Result:
    x <- digit(a)
    y <- digit(b)
    return wrap(x * 10 + y)

def calc(a, b, c):
  with Result:
    n <- two_digits(a, b)
    q <- div(n, c - '0')
    return wrap(q)

def show(r):
  match r:
    case Result/Ok:
      return (1, r.val)
    case Result/Err:
      return (0, 0)

def main():
  return (show(calc('8', '4', '2')), (show(calc('8', 'x', '2')), show(calc('8', '4', '0'))))
```

Read `calc` top to bottom: get the number from two digits (any failure stops here and propagates), divide it, and wrap the answer. The first failing line decides the result; later lines never run.

How it works:

- `x <- expr` calls `Result/bind(expr, continuation)`. If `expr` is `Ok(v)`, `bind` calls the continuation with `v`; if `Err`, it returns the `Err` unchanged and the rest of the block is skipped.
- `return wrap(v)` calls `Result/wrap(v)`, i.e. `Result/Ok(v)`. Inside a `with` block the name `wrap` is shorthand for `Type/wrap`.
- `undefer(nxt)` is required in `bind`. The continuation arrives *deferred* so that recursive monadic functions stay lazy; `undefer` forces it just before it's called. Always include that line (Advanced 8 and 9 explain why).

!!! warning
    **`with` and imports.** In Bend 0.2.38 a `with Result:` block inside a file that is *imported* from another file fails with `Could not find definition Result/bind`, because the imported file's `Result/bind` gets a module-prefixed name that the block can't see. If you split code across files, define your own monad type in the module that uses it (the capstone's `Outcome` does exactly this) — `with Outcome:` then finds `Outcome/bind` correctly.

## Other statements inside `with`

Normal assignments, `if`, `match` and so on are allowed between the `<-` lines:

<!-- expect: Result: (70, (80, 0)) -->
```bend
def Result/bind(res, nxt):
  match res:
    case Result/Ok:
      nxt = undefer(nxt)
      return nxt(res.val)
    case Result/Err:
      return res

def Result/wrap(x):
  return Result/Ok(x)

def check(n):
  if n > 100:
    return Result/Err("too big")
  else:
    return Result/Ok(n)

def f(n):
  with Result:
    a <- check(n)
    if a > 50:
      b = a - 50
    else:
      b = a
    c <- check(b + 60)
    return wrap(c)

def show(r):
  match r:
    case Result/Ok:
      return r.val
    case Result/Err:
      return 0

def main():
  return (show(f(10)), (show(f(70)), show(f(200))))
```

## The same trick for `Maybe`

Define `bind` and `wrap` for `Maybe` and you get "stop at the first `None`":

<!-- expect: Result: (5, 9999) -->
```bend
def Maybe/bind(m, nxt):
  match m:
    case Maybe/Some:
      nxt = undefer(nxt)
      return nxt(m.value)
    case Maybe/None:
      return Maybe/None

def Maybe/wrap(x):
  return Maybe/Some(x)

def half(n):
  if n % 2 == 0:
    return Maybe/Some(n / 2)
  else:
    return Maybe/None

def quarter(n):
  with Maybe:
    a <- half(n)
    b <- half(a)
    return wrap(b)

def or_default(m, d):
  match m:
    case Maybe/Some:
      return m.value
    case Maybe/None:
      return d

def main():
  return (or_default(quarter(20), 9999), or_default(quarter(6), 9999))
```

`Maybe` carries no reason for failure; use `Result` when the caller needs to know *why*.

## Designing error types

A string error is fine for demos; real code uses a type so callers can react:

<!-- expect: Result: (1, (2, 0)) -->
```bend
type Problem:
  DivByZero
  NotDigit { got }

def code(p):
  match p:
    case Problem/DivByZero:
      return 1
    case Problem/NotDigit:
      return 2

def risky(n):
  if n == 0:
    return Result/Err(Problem/DivByZero)
  elif n == 1:
    return Result/Err(Problem/NotDigit('x'))
  else:
    return Result/Ok(n)

def classify(r):
  match r:
    case Result/Err:
      return code(r.val)
    case Result/Ok:
      return 0

def main():
  return (classify(risky(0)), (classify(risky(1)), classify(risky(5))))
```

Convert between error types with `Result/map_err(result, f)`:

<!-- expect: Result: 11 -->
```bend
def main():
  r = Result/map_err(Result/Err(1), lambda e: e + 10)
  match r:
    case Result/Err:
      return r.val
    case Result/Ok:
      return 0
```

## Unwrapping

`Result/unwrap(r)` and `Maybe/unwrap(m)` pull the value out *without checking*. If it was a failure you get an `unreachable` error at runtime. Use them only when failure is truly impossible (for instance after a `contains` check) — not as a shortcut.

## `IO` is the same pattern

`with IO:` is exactly this machinery with `IO/bind` and `IO/wrap` supplied by the prelude: each `x <- action` waits for the action, then continues. The *errors* of IO operations are separate: most `IO/...` functions return a `Result` as their value, which you `match` on (or `Result/unwrap`) inside the block — the IO lesson shows both. Advanced 9 shows how to write your own monads (state, parser, logger) once you understand `bind` and `wrap`.

## Common mistakes

- **Forgetting to define `Result/bind` and `Result/wrap`** — the compiler complains that they're unbound when you write `with Result:`.
- **Leaving out `undefer(nxt)`** in `bind`. Recursive monadic functions can loop forever without it.
- **Using `<-` with a non-monadic value,** or mixing monads in one block (`Maybe` lines in a `with Result:`).
- **Returning a bare value** from a `with` block instead of `wrap(value)`.
- **Using `unwrap` as error handling.** It's an assertion, not a handler.
- **Throwing away the reason.** Prefer `Result` with an error type over `Maybe` when the caller must tell failures apart.

## Exercises

1. Write `parse_number(s)` returning `Result` (error on empty or non-digit strings).
2. Use `with Result:` to write `add_strings(a, b)`: parse both, then add.
3. Write `lookup(pairs, key)` returning `Maybe`, then `lookup2(a, b, k)` that looks `k` up in `a` and then looks the *result* up in `b`.
4. Define `type ParseError` with at least three variants and a `describe(e)` function.
5. Write `sequence(results)` turning a `List(Result)` into a `Result(List)` (first error wins).
6. Write `Result/and_then(r, f)` and re-express `calc` with it instead of `with`.
7. Define `Maybe/map(m, f)` and `Result/map(r, f)`.
8. Write a `validate_age(n)` that rejects numbers above 150, and combine it with a `validate_name(s)` in one `with` block.

## Recap

- No exceptions: failure is a value (`Result`, `Maybe`) you `match` on.
- `with Type:` + `x <- expr` flattens a chain of fallible steps; the first failure short-circuits the block.
- You supply `Type/bind` (with `undefer`) and `Type/wrap`; the prelude defines neither for `Result`/`Maybe`.
- Use an error `type` for programs that need to react to failure kinds; `Result/map_err` converts between them.
- `IO` uses the very same mechanism.

Next: [Modules & imports →](09-modules-and-imports.md)
