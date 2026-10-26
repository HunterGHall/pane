# 6. Divide and conquer

## What & why

This is the lesson where Bend's reason for existing shows up. A **divide-and-conquer** algorithm splits a problem into independent subproblems, solves them, and combines the answers. Independent subproblems are exactly what a parallel machine wants, and in Bend you get the parallelism by writing the recursion naturally — no threads, no pools, no synchronisation.

The skill to learn is recognising which shapes give you independent work, and which accidentally serialise it.

## The shape of a parallel algorithm

<!-- expect: Result: 75025 -->
```bend
def fib(n):
  if n < 2:
    return n
  else:
    return fib(n - 1) + fib(n - 2)

def main():
  return fib(25)
```

`fib(n - 1)` and `fib(n - 2)` don't depend on each other. HVM can evaluate both at once, then add. (The algorithm itself is exponential — a poor way to compute Fibonacci numbers — but it's a clear example of two independent calls.)

Contrast a sequential shape:

<!-- expect: Result: 500500 -->
```bend
def sum_to(n, acc):
  if n == 0:
    return acc
  else:
    return sum_to(n - 1, acc + n)

def main():
  return sum_to(1000, 0)
```

Each step of `sum_to` needs the previous step's `acc`: a chain, with nothing to run alongside.

The test is simple: **draw the dependency graph.** Wide and shallow runs fast; a single long chain doesn't, whatever language you write it in.

## Merge sort

Sort by splitting, sorting each half, and merging:

<!-- expect: Result: [0, 1, 2, 3, 5, 5, 6, 9] -->
```bend
def split(xs):
  match xs:
    case List/Nil:
      return ([], [])
    case List/Cons:
      (a, b) = split(xs.tail)
      return (List/Cons(xs.head, b), a)

def merge(xs, ys):
  match xs:
    case List/Nil:
      return ys
    case List/Cons:
      match ys:
        case List/Nil:
          return xs
        case List/Cons:
          if xs.head <= ys.head:
            return List/Cons(xs.head, merge(xs.tail, ys))
          else:
            return List/Cons(ys.head, merge(xs, ys.tail))

def msort(xs):
  match xs:
    case List/Nil:
      return List/Nil
    case List/Cons:
      match xs.tail:
        case List/Nil:
          return xs
        case List/Cons:
          (a, b) = split(xs)
          return merge(msort(a), msort(b))

def main():
  return msort([5, 2, 9, 1, 5, 6, 0, 3])
```

The two recursive calls `msort(a)` and `msort(b)` are independent. But there's a catch: `split` and `merge` walk lists one cell at a time, so those parts are sequential chains. Merge sort on *lists* gets some parallelism from the recursion tree, but not a lot.

## Quicksort

<!-- expect: Result: [0, 1, 2, 3, 5, 5, 6, 9] -->
```bend
def qsort(xs):
  match xs:
    case List/Nil:
      return List/Nil
    case List/Cons:
      pivot = xs.head
      small = List/filter(xs.tail, lambda x: x < pivot)
      big = List/filter(xs.tail, lambda x: x >= pivot)
      return List/concat(qsort(small), List/Cons(pivot, qsort(big)))

def main():
  return qsort([5, 2, 9, 1, 5, 6, 0, 3])
```

Same story: the two recursive calls are parallel, the partitioning isn't.

## Data shaped as a tree

The big gains come when the **data itself** is a tree, so even the combine step has independent parts. Summing a tree of numbers is the cleanest example: both halves are summed independently, and the combine is one addition.

<!-- expect: Result: 2096128 -->
```bend
type Num:
  Node { ~l, ~r }
  Leaf { v }

# Build a tree of depth d whose leaves are numbered 0, 1, 2, ...
def gen(depth):
  bend d = 0, i = 0:
    when d < depth:
      t = Num/Node(fork(d + 1, i * 2), fork(d + 1, i * 2 + 1))
    else:
      t = Num/Leaf(i)
  return t

def sum(t):
  fold t:
    case Num/Node:
      return t.l + t.r
    case Num/Leaf:
      return t.v

def main():
  return sum(gen(11))
```

Every level of both the building and the folding doubles the available parallelism. With 2¹¹ = 2048 leaves there's plenty to spread over any number of cores. (The result is 0 + 1 + … + 2047 = 2,096,128.)

This is why Bend has `Tree` and `bend`/`fold` as first-class ideas, and why the tutorials always start with "generate a tree, then fold it". When you design a Bend algorithm, ask: *what is the tree?*

## Counting search problems: N-Queens

Backtracking search is naturally a tree (choose a column for this row, recurse for the next). Each branch is independent, so "count all solutions" is divide and conquer:

<!-- expect: Result: 4 -->
```bend
def safe(q, qs, d):
  match qs:
    case List/Nil:
      return 1
    case List/Cons:
      ok = (q != qs.head) & (q != qs.head + d) & (q + d != qs.head)
      return ok & safe(q, qs.tail, d + 1)

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

def main():
  return count(6, 0, [])
```

`count` places one queen per row; `qs` holds the columns chosen so far; `safe` checks diagonals (`d` is the row distance). Different columns for the same row are independent subtrees, so more cores means more speed — and N-Queens is a classic Bend benchmark: n = 12 has 14,200 solutions.

## Measuring: `-s`

To see whether a program is actually doing parallel work, run it with statistics:

```bash
bend run-c -s program.bend
```

```text
Result: 75025
- ITRS: 3398987
- TIME: 0.59s
- MIPS: 5.76
```

`ITRS` is the total number of interactions (the unit of work), `TIME` the wall-clock time, `MIPS` millions of interactions per second. If your program is truly parallel, MIPS should rise with core count. Advanced 3 and 4 dig into this properly.

## When not to expect speedup

- **Small inputs.** Splitting costs something; tiny problems finish before parallelism pays.
- **Long dependent chains.** A fold over a list; an accumulator loop.
- **Lopsided trees.** If one branch is a thousand times bigger than the other, one core does all the work.
- **One big sequential step** (say `merge` on a million-element list) inside an otherwise parallel algorithm.

## Common mistakes

- **Assuming "recursion" means "parallel".** It's *independent* recursion that parallelises.
- **Using a list where a tree would do.** Lists are chains by construction.
- **Benchmarking tiny inputs** and concluding Bend is slow. Start measuring at a million interactions or more.
- **Combining results sequentially** when a tree-shaped combine is possible.
- **Forgetting the 24-bit limit** while scaling inputs up; sums wrap around.

## Exercises

1. Count the leaves of a tree built by `gen(d)` with a `fold` and confirm it's `2^d`.
2. Write `max_tree(t)` returning the largest leaf.
3. Write `count_solutions` for N-Queens with `n = 8` (92) and watch the interaction count with `-s`.
4. Make the tree-sum program compute the sum of squares of the leaves. What's the largest depth before the answer wraps?
5. Write a parallel `count_primes(lo, hi)` that splits the range in half recursively (`bend` + `fold`), testing each leaf number for primality.
6. Convert a list to a balanced tree (`list_to_tree`) so you can fold it in parallel.
7. Write `tree_to_sorted_list` (in-order traversal) for a binary search tree built from random numbers.
8. Compare the time of `msort` on 1,000 numbers with `-s` against `qsort`.

## Recap

- Parallelism in Bend = independent subproblems. Draw the dependency graph: wide is good, a chain is bad.
- Recursive calls with no shared dependencies (`fib`, `msort`, `qsort`, N-Queens) are parallel for free.
- The biggest wins come from **tree-shaped data**: build with `bend`/two `fork`s, reduce with `fold`.
- Use `bend run-c -s` to see interactions, time and speed.

Next: [Data structures →](07-data-structures.md)
