# 3. Parallelism in practice

## What & why

"Bend parallelises automatically" is true and incomplete. The runtime runs independent work in parallel; **you** decide how much independent work exists, by how you shape your data and recursion. This lesson is a practical guide: which shapes parallelise, which don't, how much work each piece needs to be worth running on its own core, and how to measure.

All timings below were measured on a 4-vCPU cloud sandbox with Bend 0.2.38. Your numbers will differ; the *patterns* won't.

## The rule

> Work can run in parallel when neither piece needs the other's result.

HVM finds those pieces on its own: whenever two rewrites don't depend on each other, they can be handed to different threads. Your job is to make sure the algorithm has such pieces.

## Shapes that parallelise

**1. Independent recursive calls.**

<!-- expect: Result: 4880 -->
```bend
def fib(n):
  if n < 2:
    return n
  else:
    return fib(n - 1) + fib(n - 2)

type Work:
  Node { ~l, ~r }
  Leaf { n }

def gen(depth):
  bend d = 0:
    when d < depth:
      t = Work/Node(fork(d + 1), fork(d + 1))
    else:
      t = Work/Leaf(15)
  return t

def run(t):
  fold t:
    case Work/Node:
      return t.l + t.r
    case Work/Leaf:
      return fib(t.n)

def main():
  return run(gen(3))
```

Eight leaves each compute `fib(15)` (610), and the fold adds them: 8 × 610 = 4880. The leaves share nothing, so they can all run at once. Raise the depth to 5 and the leaf number to 24 and you get the benchmark below.

**2. Tree folds.** Both children of a node reduce independently; only the combine step is serial.

**3. Divide-and-conquer.** `msort(left)` and `msort(right)`; `count(solutions)` over different columns.

**4. Pure maps over trees.** Applying a function to every leaf has no dependency between leaves.

## Shapes that don't

**1. Chains.** A fold over a list, or a loop with an accumulator: step *k* needs step *k−1*.

<!-- expect: Result: 500500 -->
```bend
def sum_to(n, total):
  if n == 0:
    return total
  else:
    return sum_to(n - 1, total + n)

def main():
  return sum_to(1000, 0)
```

**2. A long serial step inside a parallel algorithm.** Merge sort's `merge` walks lists one cell at a time. Past the recursion, the algorithm is as sequential as the longest chain.

**3. Lopsided trees.** If the left subtree is a million nodes and the right is three, one thread does the work.

**4. State threaded through everything.** A `Map` passed along (`m[k] = v; m[k2] = v2`) is a dependency chain; each write needs the previous map.

**5. IO.** Effects are strictly ordered. Do IO at the edges and compute in between.

## Measuring: does it scale?

Use `bend run-c -s`. To control how many cores HVM sees, pin the process (Linux):

```bash
taskset -c 0     bend run-c -s prog.bend     # 1 core
taskset -c 0,1   bend run-c -s prog.bend     # 2 cores
taskset -c 0-3   bend run-c -s prog.bend     # 4 cores
```

Here are three programs on 1 / 2 / 4 cores:

| Program | 1 core | 2 cores | 4 cores | Verdict |
| --- | --- | --- | --- | --- |
| 32 leaves, each `fib(24)`, folded by a tree | 6.8 s | 3.9 s | 3.1 s | scales |
| sum of a 1,000,000-element **list** (`bend` + `fold`) | 2.1 s | — | 5.6 s | **slower** with more cores |
| sum of a depth-20 **tree** (about 1,000,000 leaves, trivial work per node) | 4.5 s | — | 4.6 s | no gain |

The first row is the pattern you want: coarse, independent leaves that each do real work. The other two are instructive failures:

- The **list** has no independent work at all. Extra threads only add coordination cost.
- The **tree sum** has plenty of independent *nodes*, but each node does a single addition. The cost of creating, moving and synchronising tiny tasks swamps the arithmetic, and the whole thing is limited by memory allocation rather than computation.

## Granularity

Parallelism needs **enough work per independent piece** to pay for itself. Rules of thumb:

- A leaf that does a few interactions isn't worth a core. Make each leaf do real work (a search, a numeric kernel, a sort of a chunk).
- Stop splitting early: instead of a tree down to single elements, stop at chunks of, say, a few hundred and process each chunk sequentially.
- There's no benefit in having far more independent tasks than cores *and* each of them tiny. Depth 8–12 is often plenty.

<!-- expect: Result: 2096128 -->
```bend
# sum 0 .. 2047 by splitting into 1024 chunks of two numbers, each chunk summed sequentially
type Chunks:
  Node { ~l, ~r }
  Chunk { lo }

# a sequential loop over one chunk of n numbers starting at lo
def sum_chunk(lo, n, total):
  if n == 0:
    return total
  else:
    return sum_chunk(lo + 1, n - 1, total + lo)

def gen(depth):
  bend d = 0, i = 0:
    when d < depth:
      t = Chunks/Node(fork(d + 1, i * 2), fork(d + 1, i * 2 + 1))
    else:
      t = Chunks/Chunk(i * 2)
  return t

def run(t):
  fold t:
    case Chunks/Node:
      return t.l + t.r
    case Chunks/Chunk:
      return sum_chunk(t.lo, 2, 0)

def main():
  return run(gen(10))
```

(The chunks here are only two numbers wide to keep the example tiny and its result checkable; in a real program use chunks of hundreds or thousands of items, so each leaf is real work.)

## Balance

A perfectly balanced tree uses every core evenly. Generate trees from **ranges you split in half**, not by peeling one element at a time:

<!-- expect: Result: 36 -->
```bend
# sum of lo .. hi-1 by recursive halving
def range_sum(lo, hi):
  if hi - lo < 2:
    if hi == lo:
      return 0
    else:
      return lo
  else:
    mid = (lo + hi) / 2
    return range_sum(lo, mid) + range_sum(mid, hi)

def main():
  return range_sum(0, 9)
```

`range_sum(lo, mid)` and `range_sum(mid, hi)` are independent; the recursion depth is log₂ n instead of n. This "split the range" pattern is the parallel replacement for a loop. Always compare it to the accumulator loop: same answer, but the loop is a chain.

## Memory and the number of workers

Every active task is graph in memory. A huge fan-out means a huge graph; with enough cores that's fine, with too little RAM it's not. If a program is memory-hungry, reduce how much you *materialise* (chunk, stream) rather than how much you parallelise.

## CPU vs GPU

`bend run-cu` runs the same program on an NVIDIA GPU with thousands of threads. It pays off when the independent work is **enormous and uniform** (millions of similar leaves), because each GPU thread is slow and the data must fit in GPU memory. For small or irregular work, CPU `run-c` is faster. The code doesn't change; you just pick the command.

## A checklist

Before blaming Bend for being slow:

1. Is there independent work at all, or is it a chain? (Draw the dependency graph.)
2. Is each independent piece big enough? (Chunk it.)
3. Is the tree balanced? (Split ranges in half.)
4. Are you threading a `Map` or an accumulator through everything? (Replace with fold-and-combine.)
5. Is it doing needless work? (Check `ITRS` — a better algorithm beats more cores.)
6. Are you measuring something big enough to matter? (Aim for seconds, not milliseconds.)

## Common mistakes

- **Parallelising the wrong thing.** The expensive part is often sequential.
- **Tiny leaves.** Overhead dominates; chunk.
- **Building the data sequentially, then folding in parallel.** The `bend` that builds a tree should also fork.
- **Using a list as the unit of parallel work.**
- **Measuring with a stopwatch on tiny runs.** Use `-s` and big enough inputs.
- **Expecting linear speedup.** Memory bandwidth and allocation limit scaling long before you run out of cores.

## Exercises

1. Run the 32-leaf `fib(24)` program at 1, 2 and 4 cores (`taskset`) and plot the speedup.
2. Make the leaves cheaper (`fib(10)`); watch the speedup vanish.
3. Write the list sum and the `range_sum` for 0 … 100,000 and compare `ITRS` and time.
4. Parallelise "count primes below N" by splitting the range into chunks.
5. Write a lopsided tree on purpose and observe that cores don't help.
6. Turn the N-Queens counter into a version that splits at depth 2 and runs the rest sequentially.
7. Use `run-rs` and `run-c` on the 32-leaf program; compare.
8. If you have an NVIDIA GPU, try `run-cu` on a tree with a million leaves doing real work.

## Recap

- Independent subproblems run in parallel automatically; chains, accumulators, `Map` threading and IO are sequential.
- Parallelism needs coarse leaves (real work per piece) and balanced trees (split ranges in half).
- Measure with `bend run-c -s` and `taskset`; expect scaling only when the work is independent *and* big enough.
- Trivial work per node, lists, and lopsided trees don't speed up — and may slow down.
- GPU for enormous uniform workloads; CPU for most things.

Next: [Performance & profiling →](04-performance.md)
