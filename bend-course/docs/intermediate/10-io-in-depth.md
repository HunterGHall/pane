# 10. IO in depth

## What & why

Beginner 11 introduced `with IO:`. This lesson fills in the rest: how IO values work, the full file API, reading input safely, timing, writing helpers that return IO, and the limits you'll hit. IO is the one place where Bend is *sequential on purpose*: effects must happen in order, even though pure code around them can be reordered and parallelised freely.

## IO values are descriptions

A function like `IO/print("hi")` doesn't print anything when it's *called*. It returns an `IO` value — a description of the action. The runtime performs the actions when it executes `main`'s result. That's why every action must be threaded through a `with IO:` block: the block builds one big description, step by step, that the runtime then runs in order.

Consequences:

- A function that returns `IO(...)` is just a function; you can pass it around and build bigger actions out of smaller ones.
- Pure computations inside the block (`n = parse(line)`) are ordinary expressions and can be evaluated whenever convenient.
- Forgetting to bind an action with `<-` means it **never runs**: it's a description you dropped on the floor.

<!-- expect: Hello -->
```bend
def greet(name):
  return IO/print(name)

def main() -> IO(u24):
  with IO:
    * <- greet("Hello\n")
    return wrap(0)
```

## Helper actions

Make small actions and compose them:

<!-- expect: Total: 42 -->
```bend
def concat(a, b):
  fold a with b:
    case String/Cons:
      return String/Cons(a.head, a.tail(b))
    case String/Nil:
      return b

def say(text):
  return IO/print(concat(text, "\n"))

def say_number(label, n):
  return say(concat(label, u24/to_string(n)))

def main() -> IO(u24):
  with IO:
    * <- say_number("Total: ", 40 + 2)
    return wrap(0)
```

## Branching and recursion in IO

`if`, `match` and recursion all work inside a block; a recursive call returns an IO action you bind like any other. Read lines until a blank one:

<!-- stdin: a\nb\nc\n\n -->
<!-- expect: 3 lines -->
```bend
def concat(a, b):
  fold a with b:
    case String/Cons:
      return String/Cons(a.head, a.tail(b))
    case String/Nil:
      return b

def read_lines(acc):
  with IO:
    r <- IO/input()
    match r:
      case Result/Err:
        return wrap(List/reverse(acc))
      case Result/Ok:
        match r.val:
          case String/Nil:
            return wrap(List/reverse(acc))
          case String/Cons:
            rest <- read_lines(List/Cons(r.val, acc))
            return wrap(rest)

def main() -> IO(u24):
  with IO:
    lines <- read_lines([])
    (n, lines) = List/length(lines)
    * <- IO/print(concat(u24/to_string(n), " lines\n"))
    return wrap(0)
```

!!! warning
    `IO/input()` never returns once standard input is exhausted (Bend 0.2.38), so always end interactive input with a sentinel: a blank line, a `quit` command, or a fixed count.

## Files: open, read, write, close

For whole-file work use `IO/FS/read_file(path)` and `IO/FS/write_file(path, bytes)` (Beginner 11). For streaming, open a file and get a *file descriptor*:

<!-- expect: alpha -->
```bend
def main() -> IO(u24):
  with IO:
    w <- IO/FS/open("log.txt", "w")
    fd = Result/unwrap(w)
    * <- IO/FS/write(fd, String/encode_utf8("alpha\nbeta\n"))
    * <- IO/FS/close(fd)

    a <- IO/FS/open("log.txt", "a")
    fa = Result/unwrap(a)
    * <- IO/FS/write(fa, String/encode_utf8("gamma\n"))
    * <- IO/FS/close(fa)

    r <- IO/FS/open("log.txt", "r")
    fr = Result/unwrap(r)
    first <- IO/FS/read_line(fr)
    second <- IO/FS/read_line(fr)
    * <- IO/FS/close(fr)

    * <- IO/print(String/decode_utf8(Result/unwrap(first)))
    * <- IO/print("\n")
    * <- IO/print(String/decode_utf8(Result/unwrap(second)))
    * <- IO/print("\n")
    return wrap(0)
```

The API:

| Function | Does |
| --- | --- |
| `IO/FS/open(path, mode)` | open a file; `mode` is `"r"`, `"w"`, `"a"`, `"r+"`, `"w+"` or `"a+"`; returns a descriptor |
| `IO/FS/close(fd)` | close it |
| `IO/FS/read(fd, n)` | read up to `n` bytes |
| `IO/FS/read_line(fd)` | read one line (without the newline) |
| `IO/FS/read_to_end(fd)` | read everything that's left |
| `IO/FS/write(fd, bytes)` | write bytes |
| `IO/FS/flush(fd)`, `IO/FS/seek(fd, offset, mode)` | flush; move within the file |
| `IO/FS/read_file(path)`, `IO/FS/write_file(path, bytes)` | whole-file helpers |

Data are **lists of bytes** (`List(u24)`): convert strings with `String/encode_utf8` and `String/decode_utf8`. The standard descriptors are `IO/FS/STDIN` (0), `IO/FS/STDOUT` (1) and `IO/FS/STDERR` (2), so you can write to stderr like any file:

<!-- expect: oops -->
```bend
def main() -> IO(u24):
  with IO:
    * <- IO/FS/write(IO/FS/STDERR, String/encode_utf8("oops\n"))
    return wrap(0)
```

## Handling IO errors

Every file function returns a `Result`. `Result/unwrap` is fine in a script; a robust program matches:

<!-- expect: open failed -->
```bend
def main() -> IO(u24):
  with IO:
    r <- IO/FS/open("/nonexistent/dir/file.txt", "r")
    match r:
      case Result/Ok:
        * <- IO/print("opened\n")
      case Result/Err:
        * <- IO/print("open failed\n")
    return wrap(0)
```

The `Err` value is a numeric error code.

## Time and sleeping

<!-- check: check -->
```bend
def main() -> IO(u24):
  with IO:
    start <- IO/get_time()
    * <- IO/sleep(0.25)
    return wrap(0)
```

- `IO/get_time()` returns the time as a pair of numbers (high and low parts of a nanosecond count); the low half is enough for coarse timing.
- `IO/sleep(seconds)` takes a float; `IO/nanosleep` takes a nanosecond pair.

For *measuring a computation*, the simplest method is not in the program at all: `bend run-c -s` prints the run time (Advanced 4).

## Command-line arguments

Arguments are applied to `main` (Beginner 11). Use plain `main(a, b)` — annotating the return type of `main` as `IO(...)` together with parameters fails type checking in 0.2.38, so leave the annotation off:

<!-- args: 6 7 -->
<!-- expect: product = 42 -->
```bend
def concat(a, b):
  fold a with b:
    case String/Cons:
      return String/Cons(a.head, a.tail(b))
    case String/Nil:
      return b

def main(a, b):
  with IO:
    * <- IO/print(concat("product = ", concat(u24/to_string(a * b), "\n")))
    return wrap(0)
```

## Keeping IO at the edges

The best Bend programs are a **pure core with a thin IO shell**:

1. Read everything you need.
2. Call pure functions to compute the answer (this part parallelises).
3. Write the results.

The task tracker is built this way: `handle` and `repl` do IO, but `mark_done`, `remove`, `render`, `serialize` are pure and could be tested without any IO (next lesson).

## What IO can't do (yet)

- **No end-of-input signal** from `IO/input()` (it hangs).
- **No network, no processes, no environment variables, no directory listing** in the prelude. (Dynamic libraries can add them: Advanced 10.)
- **No IO on `run-rs`** — use `run-c` (or `run-cu`).
- The `Result: λa (a IO/Done/tag ...)` line at the end of an IO program is the runtime printing the final value; it's harmless.

## Common mistakes

- **Forgetting `<-`** so the action is never executed.
- **Using `x = IO/...` instead of `x <- IO/...`.** `=` binds the description, `<-` runs it.
- **Reading until EOF** — it hangs; use a sentinel.
- **Treating file data as strings.** They're byte lists; encode/decode.
- **Not closing file descriptors** you opened (the program still ends, but it's sloppy).
- **Mixing `Result/unwrap` into production code** where a missing file is an expected case.
- **Putting effects inside pure functions.** A function can only perform IO by returning an `IO` value that its caller runs.

## Exercises

1. Write `cat(path)` that prints a file, or "cannot read" on failure.
2. Write `copy(src, dst)` using `read_file` and `write_file`.
3. Write a program that appends a line typed by the user to `notes.txt`.
4. Write `count_lines(path)` using `read_line` in a loop (recursive IO) until the first error.
5. Print to stderr when something goes wrong and to stdout otherwise.
6. Read numbers until a blank line and print their sum, minimum and maximum.
7. Take a file name from the command line, read it, and print how many bytes it has.
8. Refactor the task tracker so `handle` only does IO and all list logic is in pure functions you can call from a test.

## Recap

- IO values are descriptions executed in order by `with IO:`; bind with `<-`, finish with `wrap`.
- Recursion and branching work inside IO blocks; helper functions return IO actions.
- Files are byte lists opened with a mode and read/written through descriptors; every operation returns a `Result`.
- `IO/input()` has no EOF signal; use sentinels. Use `run-c` for IO.
- Keep a pure core and a thin IO shell.

Next: [Testing →](11-testing.md)
