# 1. Setup & your first program

## What & why

Bend is a high-level, Python-looking language that runs on **HVM2**, a runtime that executes programs as graphs of tiny rewrite steps. The pitch: write ordinary-looking code — no threads, no locks, no `async` — and anything that *can* run in parallel *will*, on every CPU core (or on a GPU).

That pitch comes with a different mental model from Python or Rust. Bend is **purely functional**: no mutation, no loops, no objects with state. Data flows through functions. Once that clicks, the language is tiny and the parallelism is free. This first lesson just gets you installed and running.

## Installing

Bend currently supports **Linux and macOS** (on Windows, use WSL). You need:

- the **Rust toolchain** (to install Bend itself) — get it from [rustup.rs](https://rustup.rs)
- a **C compiler** (`gcc` or `clang`) — the fast, parallel backend compiles your program to C. On Debian/Ubuntu: `sudo apt install build-essential`; on macOS: `xcode-select --install`
- *(optional)* an NVIDIA GPU and the CUDA toolkit, for the GPU backend

Then install the runtime (`hvm`) and the compiler (`bend-lang`):

```bash
cargo install hvm
cargo install bend-lang
bend --version
```

This course was written and tested against **Bend 0.2.38** with HVM 2.0.22. Bend is young and still changing; if something behaves differently for you, check your version first.

## Your first program

Create `hello.bend`:

```bend
def main():
  return 42
```

Run it:

```bash
bend run-c hello.bend
```

```text
Result: 42
```

Every Bend program starts at a function called `main`. There is no `print` here: the program's **return value** is the result, and the tool prints it after `Result:`. Indentation (two spaces by convention) defines blocks, like Python.

## The three ways to run

Bend has a *compiler* and three *backends*. You pick one with the subcommand:

| Command | Backend | Good for |
| --- | --- | --- |
| `bend run-rs file.bend` | Rust interpreter | Quick experiments. Slow, but nothing extra to install. **No IO.** |
| `bend run-c file.bend` | C, all CPU cores | **The one you'll use.** Fast, parallel, supports IO. |
| `bend run-cu file.bend` | CUDA, GPU | Massive parallelism on an NVIDIA GPU. |

And two commands that don't run anything:

| Command | What it does |
| --- | --- |
| `bend check file.bend` | Parse and type-check only. Fast. Run it before running. |
| `bend gen-c file.bend` | Print the generated C instead of running it. |

!!! note
    Older tutorials say `bend run`. In current releases you choose the backend explicitly with `run-rs`, `run-c` or `run-cu`. Throughout this course, "run it" means `bend run-c`.

## Printing: the IO type

To print text you need *IO*. Bend keeps the outside world explicit: a function that talks to it returns an `IO` value, and you sequence the steps inside a `with IO:` block.

<!-- expect: Hello, world! -->
```bend
def main() -> IO(u24):
  with IO:
    * <- IO/print("Hello, world!\n")
    return wrap(0)
```

```text
Hello, world!
Result: λa (a IO/Done/tag IO/MAGIC 0)
```

Read it line by line:

- `-> IO(u24)` says `main` produces an IO action that finishes with a `u24` (a number — more in lesson 2).
- `with IO:` opens a block where each `x <- action` runs an action and names its result.
- `* <- ...` means "run this and throw the result away" (`*` is the *eraser*, Bend's "ignore" pattern).
- `wrap(0)` finishes the block with the value `0`.
- The odd `Result: λa (...)` line is just the runtime showing you the raw IO value it ended with. Ignore it; lesson 11 explains where it comes from.

You'll learn the machinery properly in lessons 11 and Intermediate 10. For now, treat this as a template: **return a value to see it, or use the IO template to print text.**

## Printing numbers

`IO/print` takes a `String`. To print a number, convert it first with `u24/to_string`:

<!-- expect: 6 * 7 = 42 -->
```bend
def main() -> IO(u24):
  with IO:
    * <- IO/print("6 * 7 = ")
    * <- IO/print(u24/to_string(6 * 7))
    * <- IO/print("\n")
    return wrap(0)
```

## Reading the compiler

Bend's error messages are short and point at the definition that's wrong. Try a typo on purpose:

<!-- check: fail -->
```bend
def main():
  return fortytwo
```

```text
Errors:
In definition 'main':
  Unbound variable 'fortytwo'.
```

Use `bend check` to see errors without running anything — it's instant, and it also prints warnings (unused definitions and the like).

## Comments

```bend
# A single-line comment

#{
  A multi-line comment,
  usually used to document a function.
#}
def main():
  return 1  # trailing comments work too
```

## Common mistakes

- **`bend: command not found`** after `cargo install`. Add `~/.cargo/bin` to your `PATH`.
- **Using `bend run-rs` for a program that prints.** The Rust backend has no IO; the output will be a wall of `λa (a IO/Call/tag ...)`. Use `run-c`.
- **Forgetting that `main` must `return`.** Every function ends in `return` (or a branch statement whose every branch returns). There's no implicit last-expression value.
- **Mixing tabs and spaces.** Use spaces, consistently.
- **Expecting `print`.** There is no `print`; see the IO template above.

## Exercises

1. Install Bend and run `bend --version`. Write down the version.
2. Make `main` return `2 + 3 * 4`. Predict the result before running it.
3. Make `main` return a tuple: `(1, 2, 3)`. What does the output look like?
4. Write the "Hello, world!" program and change the message. Then print two lines.
5. Print `The answer is 42` using `u24/to_string`.
6. Introduce a deliberate typo and read the error. Fix it using only the message.
7. Run the same trivial program with `run-rs` and `run-c`. Same answer?
8. Run `bend gen-c hello.bend | head -50` and just skim what the compiler produces.

## Recap

- Bend is a purely functional, Python-flavoured language that runs on HVM2 and parallelises automatically.
- Install with `cargo install hvm bend-lang`; you need a C compiler for the fast backend.
- `bend run-c file.bend` runs a program; `bend check` only checks it.
- `main` returns the result; printing text goes through `IO` inside a `with IO:` block.

Next: [Values, variables & types →](02-variables-and-types.md)
