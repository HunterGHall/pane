# 11. Maybe, Result & IO

## What & why

Things go wrong: a key is missing, a file doesn't exist, a division has a zero divisor. Bend has no exceptions and no `null`. A function that might fail returns a value that says so — `Maybe` for "there might be nothing", `Result` for "success or an error" — and you `match` on it. This lesson also covers the last piece of the beginner toolkit: input, files and command-line arguments, all of which live in the `IO` type.

## `Maybe`

```text
type Maybe(T):
  Some { value }
  None
```

<!-- expect: Result: (5, 999) -->
```bend
def safe_div(a, b):
  if b == 0:
    return Maybe/None
  else:
    return Maybe/Some(a / b)

def or_default(m, default):
  match m:
    case Maybe/Some:
      return m.value
    case Maybe/None:
      return default

def main():
  return (or_default(safe_div(10, 2), 999), or_default(safe_div(1, 0), 999))
```

You must handle both constructors; the compiler won't let you forget `None`. `Maybe/unwrap(m)` extracts the value but hits an "unreachable" error on `None`, so reserve it for cases that truly can't fail.

`Map/get_check(m, k)` is the standard way to look up a key safely:

<!-- expect: Result: (10, 0) -->
```bend
def lookup(m, k):
  (found, m) = Map/get_check(m, k)
  match found:
    case Maybe/Some:
      return found.value
    case Maybe/None:
      return 0

def main():
  m = {1: 10}
  return (lookup(m, 1), lookup(m, 2))
```

## `Result`

```text
type Result(O, E):
  Ok { val }
  Err { val }
```

`Result` carries either a value (`Ok`) or an error (`Err`), and **both fields are called `val`**:

<!-- expect: Result: ("ok: 5", "error: division by zero") -->
```bend
def divide(a, b):
  if b == 0:
    return Result/Err("division by zero")
  else:
    return Result/Ok(a / b)

def concat(a, b):
  fold a with b:
    case String/Cons:
      return String/Cons(a.head, a.tail(b))
    case String/Nil:
      return b

def describe(r):
  match r:
    case Result/Ok:
      return concat("ok: ", u24/to_string(r.val))
    case Result/Err:
      return concat("error: ", r.val)

def main():
  return (describe(divide(10, 2)), describe(divide(1, 0)))
```

Intermediate 8 shows how to chain several fallible steps with `with Result:` instead of nesting matches.

## Why results of your own types print strangely

Try returning a `Maybe` directly from `main`:

<!-- expect: Result: λa (a Maybe/Some/tag 3) -->
```bend
def main():
  return Maybe/Some(3)
```

You get a lambda, not `Some(3)`. That isn't a bug. Bend compiles every user-defined data type into lambda terms (a "Scott encoding"); numbers, tuples, lists and strings are special-cased by the printer, but your own types and the standard `Maybe`/`Result`/`Tree` are not. Reading `λa (a Maybe/Some/tag 3)` as "a function that takes a handler `a` and calls it with the tag `Some` and the field `3`" tells you what's inside.

Two ways to deal with it:

1. **Return something printable** — convert to a number or string with a `match`, like `describe` above.
2. **Know the shape.** An empty list prints as `λa (a List/Nil/tag)` for the same reason.

This will matter again in Advanced 1, where you see how the encoding works.

## `IO`: the outside world

Anything that touches the outside world — printing, reading input, files, the clock — returns an `IO` value. An `IO` value is a *description* of work; the `with IO:` block sequences those descriptions.

- `x <- action` runs `action` and binds its result to `x`.
- `* <- action` runs it and ignores the result.
- `return wrap(value)` ends the block, producing `value`.
- Steps run **strictly in order**, even though the rest of Bend is free to reorder or parallelise.

<!-- expect: Hello, Bend -->
```bend
def main() -> IO(u24):
  with IO:
    * <- IO/print("Hello, ")
    * <- IO/print("Bend\n")
    return wrap(0)
```

At the end of every `bend run-c` of an IO program you'll also see something like `Result: λa (a IO/Done/tag IO/MAGIC 0)`. That's the final `IO/Done` wrapper around the value you passed to `wrap` — the runtime prints whatever is left after executing your steps. It's noise; ignore it.

### Reading input

`IO/input()` reads one line from standard input. It returns a `Result(String, u24)`: `Ok` with the text (without the newline), or `Err`:

<!-- stdin: Ada\n -->
<!-- expect: Hello, Ada! -->
```bend
def concat(a, b):
  fold a with b:
    case String/Cons:
      return String/Cons(a.head, a.tail(b))
    case String/Nil:
      return b

def main() -> IO(u24):
  with IO:
    * <- IO/print("What is your name? ")
    line <- IO/input()
    match line:
      case Result/Ok:
        * <- IO/print(concat("Hello, ", concat(line.val, "!\n")))
      case Result/Err:
        * <- IO/print("could not read input\n")
    return wrap(0)
```

!!! warning
    In Bend 0.2.38, `IO/input()` does **not** return when standard input has reached end-of-file — the program hangs (and is silently stopped by a timeout if you use one). Always give an interactive or piped program an explicit end marker: a `quit` command or a blank line, as the loop below does.

### Command-line arguments

Arguments come after the file name, as Bend expressions, and are applied to `main`:

<!-- args: 6 7 -->
<!-- expect: Result: 42 -->
```bend
def main(a, b):
  return a * b
```

Run with `bend run-c prog.bend 6 7`. Strings need shell quoting: `bend run-c prog.bend '"hello"'`.

### Files

File operations return `Result`s inside `IO`. Writing and reading a file:

<!-- expect: first line -->
```bend
def main() -> IO(u24):
  with IO:
    saved <- IO/FS/write_file("notes.txt", String/encode_utf8("first line\nsecond line\n"))
    data <- IO/FS/read_file("notes.txt")
    match data:
      case Result/Ok:
        * <- IO/print(String/decode_utf8(data.val))
      case Result/Err:
        * <- IO/print("could not read the file\n")
    return wrap(0)
```

- Files are read and written as **lists of bytes** (`List(u24)`); convert with `String/encode_utf8` and `String/decode_utf8`.
- `IO/FS/read_file(path)` reads everything; `IO/FS/write_file(path, bytes)` replaces a file's contents.
- For streaming there are `IO/FS/open(path, mode)`, `IO/FS/read`, `IO/FS/read_line`, `IO/FS/write`, `IO/FS/close` with modes `"r"`, `"w"`, `"a"`, `"r+"`, ...

Reading a file that doesn't exist is an ordinary `Err`, not a crash:

<!-- expect: no such file -->
```bend
def main() -> IO(u24):
  with IO:
    data <- IO/FS/read_file("this-file-does-not-exist.txt")
    match data:
      case Result/Ok:
        * <- IO/print("found it\n")
      case Result/Err:
        * <- IO/print("no such file\n")
    return wrap(0)
```

### A loop in IO

There are no loops, so a read-until-done loop is recursion that returns an IO action. This program adds up numbers typed one per line until a blank line:

<!-- stdin: 10\n20\n12\n\n -->
<!-- expect: sum = 42 -->
```bend
def concat(a, b):
  fold a with b:
    case String/Cons:
      return String/Cons(a.head, a.tail(b))
    case String/Nil:
      return b

def parse(s):
  acc = 0
  fold s with acc:
    case String/Cons:
      return s.tail(acc * 10 + (s.head - '0'))
    case String/Nil:
      return acc

def sum_lines(total):
  with IO:
    line <- IO/input()
    match line:
      case Result/Err:
        return wrap(total)
      case Result/Ok:
        match line.val:
          case String/Nil:
            return wrap(total)
          case String/Cons:
            rest <- sum_lines(total + parse(line.val))
            return wrap(rest)

def main() -> IO(u24):
  with IO:
    total <- sum_lines(0)
    * <- IO/print(concat("sum = ", concat(u24/to_string(total), "\n")))
    return wrap(0)
```

`sum_lines` calls itself with `<-`, which sequences the recursive call after the current read. Recursion depth is not a problem in Bend.

## Common mistakes

- **Treating `Maybe`/`Result` as if they were their contents.** You must `match` first.
- **Using `Maybe/unwrap` or `Result/unwrap` on a `None`/`Err`.** It fails. `match` instead.
- **Forgetting that `Ok` and `Err` both use `.val`** (while `Maybe/Some` uses `.value`).
- **Running IO with `run-rs`.** No IO there; use `run-c`.
- **Passing a number where `IO/print` wants a string.** Convert with `u24/to_string`.
- **Doing IO outside a `with IO:` block.** `<-` only works inside one.
- **Expecting `IO/input()` to strip nothing.** It returns the line without its newline; blank lines come back as an empty string.

## Exercises

1. Write `first(xs)` returning a `Maybe` of the first element of a list.
2. Write `parse_digit(c)` returning `Maybe/Some(n)` for `'0'..'9'` and `Maybe/None` otherwise.
3. Write `safe_sqrt(x)` for floats returning `Result/Err("negative")` when `x < 0.0`.
4. Make a program that takes two numbers as command-line arguments and prints their quotient, or "division by zero".
5. Write a program that reads a name and a year of birth from input and prints the age in 2025.
6. Write a file `numbers.txt` containing `1 2 3` on separate lines, then read it back and print the count of lines.
7. Handle a missing config file by falling back to a default string.
8. Write a loop that reads lines and echoes each one until the user types `quit`.

## Recap

- No exceptions, no `null`: use `Maybe` (`Some`/`None`) or `Result` (`Ok`/`Err`, both `.val`) and `match`.
- User-defined types print as lambda encodings; return numbers or strings from `main` when you want readable output.
- IO lives in `with IO:` blocks: `x <- action`, `* <- action`, `return wrap(x)`; steps run in order.
- Input, files and arguments: `IO/input`, `IO/FS/read_file`/`write_file` (bytes), and arguments applied to `main`.
- Use `run-c` for anything with IO.

Next: [Capstone: task tracker →](12-capstone-task-tracker.md)
