# 4. Performance & profiling

## What & why

Parallel hardware makes a good algorithm faster; it does not rescue a bad one. In Bend the first question about speed is not "how many cores?" but **"how many interactions?"** — the number of graph rewrites the runtime performs. This lesson gives you the cost model, the tools to measure it, and the handful of habits that account for most real speedups.

## The cost model: interactions

Every step the runtime takes is an interaction (Advanced 1). `bend run-c -s` reports them:

```bash
bend run-c -s fib.bend
```

```text
Result: 832040
- ITRS: 37695515
- TIME: 1.85s
- MIPS: 20.39
```

- **ITRS** — total interactions: the amount of *work*, independent of how many cores run it.
- **TIME** — wall-clock seconds.
- **MIPS** — millions of interactions per second: the *speed* of the machine on this program.

Two ways to go faster: reduce `ITRS` (better algorithm, better data representation) or raise `MIPS` (more parallelism, a faster backend). Always try the first first: it's portable and compounds.

Use `ITRS` as your profiler. It's deterministic: the same program gives the same count on every run and every machine, so you can compare two versions of a function exactly even when timing is noisy.

## Habit 1: native numbers, not data-structure numbers

Bend's `Nat` (`Nat/Zero`, `Nat/Succ`) is a unary number made of nodes. Native `u24` arithmetic is one operation. Adding 2000 and 3000:

<!-- expect: Result: 5000 -->
```bend
def to_nat(n):
  if n == 0:
    return Nat/Zero
  else:
    return Nat/Succ(to_nat(n - 1))

def add(a, b):
  match a:
    case Nat/Zero:
      return b
    case Nat/Succ:
      return Nat/Succ(add(a.pred, b))

def to_num(a):
  fold a:
    case Nat/Zero:
      return 0
    case Nat/Succ:
      return 1 + a.pred

def main():
  return to_num(add(to_nat(2000), to_nat(3000)))
```

That costs about **189,000** interactions. The native version:

<!-- expect: Result: 5000 -->
```bend
def main():
  return 2000 + 3000
```

costs **2**. Use `Nat` only when you need unary structure; use `u24`/`i24`/`f24` for arithmetic.

## Habit 2: don't append in a loop

`List/concat(acc, [x])` walks the whole `acc` each time, so building a list of *n* items this way costs ~*n²*. Cons and reverse once:

<!-- expect: Result: 200 -->
```bend
def build(n, acc):
  if n == 0:
    return List/reverse(acc)
  else:
    return build(n - 1, List/Cons(n, acc))

def length(xs):
  fold xs:
    case List/Cons:
      return 1 + xs.tail
    case List/Nil:
      return 0

def main():
  return length(build(200, []))
```

Measured interactions, appending vs cons-and-reverse:

| n | append in a loop | cons + reverse |
| --- | --- | --- |
| 2,000 | 38,077,024 | 102,037 |
| 4,000 | 152,154,024 | 204,037 |

Doubling *n* quadruples the first column and doubles the second. A `DiffList` also gives constant-time append when order matters.

## Habit 3: strings are lists too

Every string operation walks a linked list, and concatenating inside loops is the same quadratic trap. Build output pieces in a list and join once, or print as you go (`IO/print` each piece) instead of assembling one giant string. Use `String/equals` and `fold`, not repeated indexing.

## Habit 4: choose the right container

| Operation | `List` | `Map` | tree / BST |
| --- | --- | --- | --- |
| prepend | O(1) | — | — |
| append | O(n) | — | — |
| index / lookup | O(n) | O(log n) | O(depth) |
| parallel-friendly | no | partly | yes |

If you index a list by position in a loop, you've written an O(n²) program.

## Habit 5: share work, don't repeat it

A plain binding is evaluated once and shared; `use` pastes the expression (Beginner 7). A computation used in two branches should be named once:

<!-- expect: Result: 13530 -->
```bend
def fib(n):
  if n < 2:
    return n
  else:
    return fib(n - 1) + fib(n - 2)

def main():
  x = fib(20)
  return x + x
```

Also avoid `fib`-style double recursion when a loop with two accumulators computes the same thing in *O(n)* interactions:

<!-- expect: Result: 6765 -->
```bend
def fib(n, a, b):
  if n == 0:
    return a
  else:
    return fib(n - 1, b, a + b)

def main():
  return fib(20, 0, 1)
```

Memoisation is hard in a purely functional language without mutation; restructure the algorithm (dynamic programming over a list or tree) rather than caching.

## Habit 6: keep data flat

A deeply nested tuple or a function-valued field adds dup nodes and indirection. Use `object`/`type` with named fields for records you pass around a lot, and keep inner loops on plain numbers.

## Compiler flags

You can ask the compiler for optimisations with `-O`:

| Flag | Effect (0.2.38) |
| --- | --- |
| `-Oall` | enable all passes |
| `-Oeta`, `-Oinline`, `-Omerge`, `-Oprune` | eta-reduction, inlining, merging identical definitions, dropping unused ones |
| `-Olinearize-matches`, `-Ofloat-combinators` | **on by default**; they keep recursion lazy (Advanced 8) |
| `-Ono-type-check` | skip type checking |
| `-Ocheck-net-size` | warn if a definition's net is too big for the runtime |

On the benchmarks tried while writing this course, `-Oall`, `-Oinline`, `-Omerge`, `-Oeta` and `-Oprune` left the interaction count of `fib(30)` **unchanged** (37,695,515); wall-clock differences were within the machine's noise. The flags rarely matter for ordinary programs; algorithm and data representation matter much more.

!!! danger
    Do not turn off `float-combinators` (or use `-Ono-all`) on recursive code. Those passes are what stop recursive definitions unfolding forever; without them even `fib(30)` never finishes. Advanced 8 explains why.

## Compile once, run many times

`bend run-c` generates C and compiles it with your C compiler **every time**, which costs a second or two. For repeated runs, build a standalone executable:

```bash
bend gen-c prog.bend > prog.c
gcc -O2 prog.c -o prog -lm       # link libm *after* the source file
./prog
```

The binary prints the result and the interaction/time summary itself. Programs with IO work the same way (the generated C includes the IO support).

## Benchmarking checklist

1. Start with `bend check`; fix warnings.
2. Run `bend run-c -s` and note `ITRS`.
3. Change one thing; compare `ITRS` first, `TIME` second.
4. Scale the input 2×; if `ITRS` grows 4× you have a quadratic step — find it.
5. Check scaling with cores (Advanced 3).
6. Only then consider flags, `run-cu` or restructuring for parallelism.

## Common mistakes

- **Optimising time instead of interactions.** Time is noisy; interactions are exact.
- **Benchmarking tiny inputs.** Sub-millisecond runs measure startup, not your code.
- **Appending to the end of lists and strings in loops.**
- **Using `Nat` or Church numerals for arithmetic.**
- **Using `use` on an expensive expression** (it recomputes it).
- **Disabling the default optimisations.**
- **Judging parallel speed on a program with no independent work.**

## Exercises

1. Measure `ITRS` for `fib(20)`, `fib(25)`, `fib(30)` and the ratio between steps.
2. Reproduce the append-vs-reverse table and add n = 8,000.
3. Rewrite a string-building loop with `DiffList` and compare `ITRS`.
4. Find the quadratic step in a program that "indexes into a list inside a loop" and replace it with a fold.
5. Compare `Nat`-based and `u24`-based factorial for 10.
6. Build `prog` with `gen-c` + `gcc -O2` and compare end-to-end time with `bend run-c`.
7. Take any program of yours and find its most expensive function by running it with different inputs removed.
8. Run `bend run-rs -s` and `bend run-c -s` on the same program and compare MIPS.

## Recap

- The unit of cost is the **interaction**; `bend run-c -s` reports `ITRS`, `TIME` and `MIPS`. `ITRS` is deterministic — use it to compare versions.
- Biggest wins: native numbers over `Nat`, cons-and-reverse over append, the right container, sharing work.
- Compiler flags rarely change interaction counts; never disable the defaults on recursive code.
- Build with `gen-c` + `gcc -O2` when you run something repeatedly.
- Algorithm first, then parallelism, then micro-tuning.

Next: [Lambda encodings →](05-lambda-encodings.md)
