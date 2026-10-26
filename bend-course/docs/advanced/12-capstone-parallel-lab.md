# 12. Capstone: parallel lab

## What you're building

A small lab of two classic parallel workloads, written the Bend way, plus a benchmark script that measures them on 1, 2 and all of your cores:

- **N-Queens** — count the solutions of the puzzle by exhaustive search.
- **Bitonic sort** — sort 2ᵈ numbers with a sorting *network* on a tree, verified by an independent check.

Unlike the other capstones this one has no user interface. Its job is to make you practise the whole Advanced toolkit: design for independent work, measure with interactions and time, and reason about *why* the numbers come out as they do.

```text
$ bend run-c -s queens.bend 8
Result: 92
- ITRS: 7180732
- TIME: 0.57s
- MIPS: ...

$ bend run-c -s bitonic.bend 12
Result: 1
- ITRS: 8810290
- TIME: 0.76s
```

## Design

**N-Queens** (`queens.bend`). The state is the list of columns already chosen, one per row. `place` tries each column `col` for the current row; a column is allowed if `safe` finds no clash on column or diagonal; an allowed column recurses to the next row. Every column choice in a row is an independent subtree of the search, and the counts add. Dependency graph: a wide, bushy tree — good for parallelism — but with tiny work per node (a handful of comparisons), which matters when you measure.

**Bitonic sort** (`bitonic.bend`). A sorting network compares fixed pairs of positions regardless of the data, so *which comparisons happen is known in advance and independent of the values*. The numbers live in a **tree of pairs** whose shape mirrors the network: `warp` compares and swaps matching elements of two subtrees, `flow` and `down` merge, `sort` sorts the two halves in opposite directions and merges. Each recursive call on a subtree is independent. The depth `d` is passed explicitly because a bare pair can't be told from a number at runtime. The algorithm is adapted from the example shipped with Bend; `to_list` and `is_sorted` are the course's own, so the program checks its own answer: `main` returns `1` only if the output is ascending.

**The lab report** (`bench.sh`). Runs both programs on 1 core, 2 cores and all cores (with `taskset` on Linux) and prints interactions, time and speed.

## N-Queens

<!-- sync: capstones/parallel-lab/queens.bend -->
```bend
# queens.bend: count the solutions of the N-Queens puzzle.
#
#   bend run-c -s queens.bend 8         92 solutions
#
# Each row places one queen. `qs` holds the columns chosen so far (most recent
# first); `safe` checks the new queen against them. Different columns for the
# same row are independent searches, so the work spreads across all cores.

# Is a queen in column q (placed d rows below the rest) safe from every queen in qs?
def safe(q, qs, d):
  match qs:
    case List/Nil:
      return 1
    case List/Cons:
      ok = (q != qs.head) & (q != qs.head + d) & (q + d != qs.head)
      return ok & safe(q, qs.tail, d + 1)

# Try every column from `col` upward in row `row`; return the solution count.
def place(n, row, qs, col):
  if col == n:
    return 0
  else:
    if safe(col, qs, 1):
      here = count(n, row + 1, List/Cons(col, qs))
    else:
      here = 0
    return here + place(n, row, qs, col + 1)

def count(n, row, qs):
  if row == n:
    return 1
  else:
    return place(n, row, qs, 0)

def main(n):
  return count(n, 0, [])
```
<!-- /sync -->

Notes:

- `safe(q, qs, d)` compares `q` with the queen `d` rows up. Three conditions: not the same column, not the same `/` diagonal, not the same `\` diagonal. `&` combines them without short-circuiting, which is fine for cheap checks.
- `place` is a loop over columns written as recursion with the count accumulated by `+`. The call `count(...)` for this column and the recursive `place(..., col + 1)` for the next are independent additions' operands, so both may run at once.
- `main(n)` takes the board size on the command line: `bend run-c queens.bend 8`.
- Known counts: 4×4 → 2, 6×6 → 4, 8×8 → 92, 9×9 → 352, 10×10 → 724, 12×12 → 14,200.

## Bitonic sort

<!-- sync: capstones/parallel-lab/bitonic.bend -->
```bend
# bitonic.bend: parallel bitonic sort on a tree of pairs.
#
#   bend run-c -s bitonic.bend 10       sorts 2^10 = 1024 numbers
#
# Adapted from the bitonic_sort.bend example shipped with Bend
# (https://github.com/HigherOrderCO/Bend, Apache-2.0).
#
# A "tree of pairs of depth d" holds 2^d numbers: depth 0 is a number, depth d
# is a pair of two trees of depth d-1. Because a bare pair can't be told apart
# from a number at runtime, the depth is passed to every function.

# A reverse-sorted tree of depth d: the numbers 2^d - 1 ... 0.
def gen(d):
  bend d, x = 0:
    when d:
      return (fork(d - 1, x * 2 + 1), fork(d - 1, x * 2))
    else:
      return x

# Swap a pair if `s` says so.
def swap(s, a, b):
  if s:
    return (b, a)
  else:
    return (a, b)

# Compare-and-swap the matching elements of two trees of depth d.
def warp(d, s, a, b):
  switch d:
    case 0:
      return swap(s + (a > b), a, b)
    case _:
      (a.a, a.b) = a
      (b.a, b.b) = b
      (A.a, A.b) = warp(d-1, s, a.a, b.a)
      (B.a, B.b) = warp(d-1, s, a.b, b.b)
      return ((A.a, B.a), (A.b, B.b))

# Merge a bitonic sequence into sorted order (direction chosen by s).
def flow(d, s, t):
  switch d:
    case 0:
      return t
    case _:
      (t.a, t.b) = t
      return down(d, s, warp(d-1, s, t.a, t.b))

def down(d, s, t):
  switch d:
    case 0:
      return t
    case _:
      (t.a, t.b) = t
      return (flow(d-1, s, t.a), flow(d-1, s, t.b))

# The sort: sort the halves in opposite directions, then merge.
def sort(d, s, t):
  switch d:
    case 0:
      return t
    case _:
      (t.a, t.b) = t
      return flow(d, s, (sort(d-1, 0, t.a), sort(d-1, 1, t.b)))

# ---------- checking the result ----------

# Flatten a tree of depth d into a list, left to right.
def to_list(d, t):
  switch d:
    case 0:
      return [t]
    case _:
      (t.a, t.b) = t
      return List/concat(to_list(d-1, t.a), to_list(d-1, t.b))

def is_sorted(xs):
  match xs:
    case List/Nil:
      return 1
    case List/Cons:
      match xs.tail:
        case List/Nil:
          return 1
        case List/Cons:
          return (xs.head <= xs.tail.head) & is_sorted(xs.tail)

# 1 if sorting a reverse-sorted tree of depth d gives an ascending list.
def main(d):
  return is_sorted(to_list(d, sort(d, 0, gen(d))))
```
<!-- /sync -->

Notes:

- `gen(d)` builds the *worst-case* input, a reverse-sorted tree, with a `bend`: itself a parallel build.
- The `(a.a, a.b) = a` lines destructure a pair of subtrees; `switch d: case 0:` is the base case (a single number), and `d-1` is the predecessor of `d` in the `_` branch.
- `main(d)` sorts 2ᵈ numbers. `d = 14` is 16,384 numbers; `d = 18` (about 262,000 numbers) is on the order of a billion interactions and takes tens of seconds.
- The check `is_sorted(to_list(...))` walks a list: a sequential chain, deliberately — it's a verifier, not part of the parallel work.

## The lab report

<!-- sync: capstones/parallel-lab/bench.sh -->
```bash
#!/usr/bin/env bash
# Runs the lab benchmarks on 1, 2 and all cores and prints interactions, time and speed.
# Usage: bash bench.sh [queens-size] [bitonic-depth]
# Linux only for the core pinning (needs `taskset`); elsewhere it just runs once.
set -euo pipefail
cd "$(dirname "$0")"
N="${1:-9}"
D="${2:-14}"
CORES="$(nproc 2>/dev/null || sysctl -n hw.ncpu)"

run() { # name file arg cpus
  local label="$1" file="$2" arg="$3" cpus="$4"
  local out
  if command -v taskset >/dev/null 2>&1 && [ -n "$cpus" ]; then
    out="$(taskset -c "$cpus" bend run-c -s "$file" "$arg" 2>&1)"
  else
    out="$(bend run-c -s "$file" "$arg" 2>&1)"
  fi
  printf '%-22s %-24s %s\n' "$label" "$(echo "$out" | grep Result)" \
    "$(echo "$out" | grep -E 'ITRS|TIME|MIPS' | tr '\n' ' ' | sed 's/- //g')"
}

for cpus in "0" "0-1" "0-$((CORES - 1))"; do
  echo "== cores: $cpus =="
  run "queens($N)"  queens.bend  "$N" "$cpus"
  run "bitonic($D)" bitonic.bend "$D" "$cpus"
done
```
<!-- /sync -->

Run it:

```bash
cd capstones/parallel-lab
bash bench.sh            # queens(9) and bitonic(14)
bash bench.sh 10 16      # bigger
```

## What the numbers say

On the 4-vCPU cloud sandbox used to test this course (Bend 0.2.38):

| Run | 1 core | 2 cores | 4 cores | Interactions |
| --- | --- | --- | --- | --- |
| `queens(9)` | 2.0 s | 2.5 s | 2.3 s | 37,372,310 |
| `bitonic(14)` | 2.8 s | 3.1 s | 3.1 s | 45,666,098 |

**Neither benchmark sped up with more cores here.** That is not a bug in the lab; it is the lesson of Advanced 3 made concrete. Both programs have independent work in abundance — the dependency graph is wide — but each node does a tiny amount of arithmetic, so the time goes into allocating, linking and scheduling graph nodes, not into computing. Throwing cores at that gains nothing on a small machine. The interaction counts are identical in every column: the *work* is constant; only the *schedule* changes.

Your machine may behave differently. Many cores with more memory bandwidth, or the GPU backend (`bend run-cu`) on much bigger inputs, is where these workloads are expected to shine. What you should expect on every machine:

- `ITRS` identical across runs.
- `Result` identical across core counts (confluence: the schedule can't change the answer).
- Time that depends on the machine, the input size and how coarse the independent pieces are.

## Experiments

This is where the learning is. For each, predict the effect, run it, and explain what you see.

1. **Scale the input.** Double `n` for queens and `d` for bitonic until a run takes about 10 seconds. How does `ITRS` grow? Is it what the algorithm's complexity predicts (for bitonic: about *n* log² *n*)?
2. **Make the leaves heavier.** Change queens so that, below row 3, each subtree is searched with a sequential helper that does the rest of the work *inside one leaf* (chunking, Advanced 3). Does the speedup improve? Does `ITRS` change?
3. **Break the balance.** Replace the bitonic tree by a lopsided one. What happens to the time?
4. **Compare backends.** Run both with `run-rs` and `run-c`. Compare MIPS.
5. **Build standalone binaries** with `gen-c` + `gcc -O2` and compare with `bend run-c`.
6. **Break the sort on purpose** (change `>` to `<` in `warp`) and watch the checker return `0`.
7. **Add a third workload**, such as the count of primes below *n* by splitting the range recursively, and extend `bench.sh` to include it.
8. **GPU (if you have one).** Run `bend run-cu` on `bitonic(18)` or larger.

## Extending the lab

- Print a nicely aligned table with speedup ratios from `bench.sh`.
- Add `bend check` and the correctness checks (`92`, `1`) into the script so a wrong build fails loudly.
- Write the parallel **merge sort on trees**: build a balanced tree from a list, sort leaves-up with a `fold` whose combine step merges two sorted lists, and compare with bitonic sort.
- Implement **parallel map-reduce word counting**: split the input into chunks, count each chunk into a `Map`, and merge maps pairwise up a tree.
- Try **Mandelbrot**: a `u24`/`f24` pixel grid as a tree of rows, each pixel an independent iteration — plenty of arithmetic per leaf, the shape the GPU loves.

## When you're done

You can design an algorithm so its work is independent, build and consume trees with `bend`/`fold`, measure with interactions and time, verify results independently, and explain why a given workload does or doesn't scale. That is the whole course. From here, read the HVM and Bend repositories, contribute fixes (the prelude bugs found while writing this course are a good start), and build something that needs a thousand cores.
