# 11. The compiler & HVM

## What & why

You now know what Bend programs become (graphs of interaction nodes) and why some shapes are fast. This lesson is a tour of the tool chain itself: what each compiler pass does, which command shows which stage, how to read the options and warnings, and how to run HVM code directly. When something behaves strangely — a hang, a surprising `ITRS` count, an `<Invalid>` result — these are the tools for finding out why.

## The commands

```text
bend [OPTIONS] <COMMAND> file.bend [ARGS]

check      parse + type-check only
run-rs     compile and run with the Rust HVM
run-c      compile and run with the C HVM
run-cu     compile and run with the CUDA HVM
gen-hvm    print the compiled HVM net
gen-c      print a standalone C program
gen-cu     print a standalone CUDA program
desugar    print the program after the desugaring passes
```

Useful run flags: `-s` (statistics), `-p` (pretty-print the result), `-l` (linear readback), and `-O...` / `-W...` / `-D...` / `-A...` for optimisations and warnings. Program arguments come after the file name.

The separate `hvm` binary runs raw nets:

```text
hvm run     file.hvm      Rust interpreter
hvm run-c   file.hvm      C (add --io for IO programs)
hvm run-cu  file.hvm      CUDA
hvm gen-c   file.hvm      standalone C
```

## Stages, with real output

Take one tiny program:

```text
def double(x):
  return x * 2

def main():
  return double(21)
```

**`bend desugar`** — the program after types, `match`, `fold` and friends have become lambda-calculus-style core terms:

```text
unchecked double: (Any -> Any)
(double) = λa (* a 2)

unchecked main: Any
(main) = (double 21)
```

**`bend gen-hvm`** — the HVM net the runtime loads:

```text
@double = ($([*0x0000002] a) a)

@main = a
  & @double ~ (21 a)
```

**`hvm run-c`** — run that net directly, skipping Bend:

<!-- check: skip -->
```bash
bend gen-hvm double.bend > double.hvm
hvm run-c double.hvm
```

```text
Result: 42
- ITRS: 4
- TIME: 0.00s
- MIPS: 0.00
```

The net syntax is the same you saw in Advanced 1: `@name` references, `(a b)` constructor nodes, `{a b}` duplicators, `*` erasers, numbers, operator nodes, and `& A ~ B` for an active pair. You can write a net by hand using the generated ones as a model — the file below is accepted by `hvm run-c` as written:

```text
@double = ($([*0x0000002] a) a)

@main = a
  & @double ~ (21 a)
```

## What the compiler does, in order

1. **Parse** the file (Imp or Fun syntax), resolve **imports**.
2. **Desugar**: expand `with` blocks, `use`, list/string/map literals, comprehensions, `fold`, `bend`, `match`/`switch`, local `def`s; give types their encodings (`adt-num-scott` by default).
3. **Type-check** (unless disabled), reporting `Can't unify`, non-exhaustive matches, and so on.
4. **Linearise** variables (insert dups/erasers; Beginner 7).
5. **Optimise** (the `-O` passes below).
6. **Lower to an HVM net** and hand it to the chosen backend.

## The optimisation flags

Set with `-O<name>` and cancel with `-Ono-<name>`:

| Pass | Default | What it does |
| --- | --- | --- |
| `linearize-matches` | on | moves the arms of `match`/`switch` into their own definitions so unused arms are never unfolded (Advanced 8) |
| `float-combinators` | on | lifts closed lambdas to lazy top-level definitions (Advanced 8) |
| `type-check` | on | runs the type checker |
| `adt-num-scott` / `adt-scott` | `adt-num-scott` | how data types are encoded (Advanced 5) |
| `eta` | off | eta-reduces: `λx (f x)` becomes `f` |
| `prune` | off | removes unused definitions |
| `merge` | off | merges identical definitions |
| `inline` | off | inlines definitions that compile to numbers, erasers or references |
| `check-net-size` | off | fails if a definition is too big for the CUDA runtime (64 nodes) |
| `all` / `no-all` | — | turn every pass on or off |

Examples from the compiler documentation:

```text
# -Oeta
id_id = λx (id x)      ⇒      id_id = id

# -Oinline  (foo = 2)
main = (id foo)        ⇒      main = (id 2)
```

Rules of thumb:

- Leave `linearize-matches` and `float-combinators` **on**. Turning them off makes recursive programs loop forever.
- `check-net-size` matters only for `run-cu`: the CUDA runtime limits how large one function's net can be.
- The off-by-default passes did not change interaction counts on the benchmarks in Advanced 4, so reach for them only when profiling shows a reason.

## Warnings

The compiler emits warnings you can show, forbid or silence:

| Warning | Meaning |
| --- | --- |
| `unused-definition` | a definition nothing uses |
| `irrefutable-match` | a `match` whose first pattern catches everything |
| `redundant-match`, `unreachable-match` | cases that can never run |
| `repeated-bind` | the same name bound twice in a pattern |
| `recursion-cycle` | a cycle of definitions that might unfold forever |
| `import-shadow` | an import hides another name |
| `missing-main` | no `main` found |

```bash
bend check -W all prog.bend      # show every warning
bend run-c -D all prog.bend      # treat warnings as errors
bend run-c -A unused-definition prog.bend   # silence one
```

Run `bend check` regularly, and turn warnings into errors in CI: an `unused-definition` is often a forgotten function, and a `recursion-cycle` is a flag for the laziness problems of Advanced 8.

## Entry points

By default the program starts at `main` (or `Main`). The `-e` flag names another entry point, but in 0.2.38 the file must not also define `main`:

```bash
bend run-c -e other_entry prog.bend
```

Arguments after the file name are applied to the entry point (Beginner 11).

## Inspecting a problem

When a result looks wrong:

1. `bend desugar` — look at what your function became. Find the `let {a b} = ...` dups (Advanced 2).
2. `bend run-c -l` — linear readback, which shows the explicit duplications.
3. Try `run-rs` and `run-c` — a discrepancy points to a backend or dup bug.
4. `-Ono-type-check` — see if the checker is *rejecting* correct code.
5. Shrink the program until the problem is a few lines; this is almost always possible.

When a program doesn't terminate:

1. Run under `timeout` and add `-s` to see if interactions keep climbing (a loop) or it stalls.
2. Look for an unguarded recursion (Advanced 8).
3. Check you haven't disabled `float-combinators` or `linearize-matches`.

## Other backends

- **`run-c`** compiles the net to C with your C compiler; it's multi-threaded.
- **`run-cu`** compiles to CUDA for NVIDIA GPUs. Not available without a GPU and the CUDA toolkit; IO support is limited.
- **`gen-c` / `gen-cu`** print the program for you to compile yourself (Advanced 4 and 10).

## Where the code lives

Bend is two projects: the compiler (`bend-lang`, Rust) and the runtime (`hvm`, Rust plus a C and a CUDA implementation). Both are on GitHub (HigherOrderCO/Bend and HigherOrderCO/HVM). Reading `src/fun/builtins.bend` in the compiler source shows the whole prelude, written in Bend itself — a handy reference for the exact semantics of `IO/...`, `Map/...` and `List/...`.

## Common mistakes

- **Reading `bend desugar` output as the final program.** It's the intermediate stage; `gen-hvm` is the net.
- **Turning off default passes** to "speed things up".
- **Ignoring warnings.** `recursion-cycle` and `unused-definition` are free bug reports.
- **Using `-e` with a file that also defines `main`.**
- **Comparing timings without `-s`** and on tiny inputs.
- **Assuming `run-cu` works wherever `run-c` does.**

## Exercises

1. Run `bend desugar` and `bend gen-hvm` on a program with a `fold` and match the generated recursive function.
2. Hand-write the net for "add 1 to the argument" by copying `double`'s shape, and run it with `hvm run-c`.
3. Run `bend check -W all` on one of your programs and fix every warning.
4. Make `bend run-c -D all` fail on a program with an unused definition.
5. Compare `-Oeta` and `-Ono-eta` output of `bend desugar` on `id_id = λx (id x)`.
6. Read `src/fun/builtins.bend` and find the definition of `List/reverse`.
7. Write a program with the entry point named `start` and run it with `-e start`.
8. Disable `float-combinators` on a program of yours and confirm it hangs; re-enable it.

## Recap

- `desugar` → `gen-hvm` → `gen-c`/`hvm run` are successive views of the same program; use them to see what the compiler did.
- Keep `linearize-matches` and `float-combinators` on; other `-O` passes rarely change anything.
- Warnings (`-W`, `-D`, `-A`) are cheap bug reports.
- Debug by shrinking, desugaring and trying another backend.

Next: [Capstone: parallel lab →](12-capstone-parallel-lab.md)
