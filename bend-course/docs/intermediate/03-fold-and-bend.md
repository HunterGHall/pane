# 3. Recursion schemes: `fold` and `bend`

## What & why

Almost every recursive function you write falls into one of two molds:

- **Consuming** a recursive structure — sum a tree, count a list, evaluate an expression. This is `fold`.
- **Producing** a recursive structure from a seed — build a list from a range, a tree from a depth. This is `bend`.

Bend gives both a dedicated statement. They look like loops, but they're recursion with the plumbing hidden, and they are the forms the compiler is best at parallelising. In real Bend code you'll write far more `fold` and `bend` than hand-rolled recursion.

(We use `BTree` below because the prelude already owns the name `Tree`.)

## `fold`: consume a structure

`fold` is a `match` that automatically recurses into every field marked `~`. In each case, the `~` fields hold **the already-computed results** for the substructures:

<!-- expect: Result: (10, 3) -->
```bend
type BTree:
  Node { val, ~left, ~right }
  Leaf

def sum(t):
  fold t:
    case BTree/Node:
      return t.val + t.left + t.right
    case BTree/Leaf:
      return 0

def depth(t):
  fold t:
    case BTree/Node:
      return 1 + max(t.left, t.right)
    case BTree/Leaf:
      return 0

def max(a, b):
  if a > b:
    return a
  else:
    return b

def main():
  deep = BTree/Node(5, BTree/Node(0, BTree/Leaf, BTree/Leaf), BTree/Leaf)
  t = BTree/Node(4, BTree/Node(1, BTree/Leaf, BTree/Leaf), deep)
  return (sum(t), depth(t))
```

Read `t.left + t.right` as "the sum of the left subtree plus the sum of the right subtree", because `left` and `right` are marked `~` in the type. The two recursive results are independent, so a parallel runtime can compute them at the same time.

### `fold` vs `match`

| | `match` | `fold` |
| --- | --- | --- |
| `~` fields are | the **raw** substructures | the **results** of recursing |
| You recurse by | calling the function yourself | not at all — it's automatic |
| Use when | you need to look at the structure itself | you're reducing it to an answer |

The same sum with `match`:

<!-- expect: Result: 10 -->
```bend
type BTree:
  Node { val, ~left, ~right }
  Leaf

def sum(t):
  match t:
    case BTree/Node:
      return t.val + sum(t.left) + sum(t.right)
    case BTree/Leaf:
      return 0

def main():
  return sum(BTree/Node(4, BTree/Node(1, BTree/Leaf, BTree/Leaf), BTree/Node(5, BTree/Leaf, BTree/Leaf)))
```

Prefer `fold` when it fits. If a `fold` needs the original substructure (say, to compare it to something), use `match`.

## `fold` with state

To pass information *down* while you consume, add `with`. Every recursive call then takes the new state as an argument. This labels each node of a tree with its depth:

<!-- expect: Result: 10 -->
```bend
type BTree:
  Node { val, ~left, ~right }
  Leaf

def label_depths(t):
  depth = 0
  fold t with depth:
    case BTree/Node:
      return BTree/Node(depth, t.left(depth + 1), t.right(depth + 1))
    case BTree/Leaf:
      return BTree/Leaf

def sum(t):
  fold t:
    case BTree/Node:
      return t.val + t.left + t.right
    case BTree/Leaf:
      return 0

def full(h):
  bend d = 0:
    when d < h:
      t = BTree/Node(0, fork(d + 1), fork(d + 1))
    else:
      t = BTree/Leaf
  return t

def main():
  return sum(label_depths(full(3)))
```

`fold t with depth:` declares the state; the recursive calls are written `t.left(new_state)`. (The sum 0 + 2·1 + 4·2 = 10 is the depths of a full tree of height 3.)

State is duplicated for each recursive call, so pass small things (numbers, short lists), not huge structures.

Folds work on lists exactly the same way, and you've already used them: `fold xs with k:` in the Beginner lessons carried a function or a number down the list.

## `fold` on lists, a reminder

<!-- expect: Result: (15, [2, 4, 6]) -->
```bend
def sum(xs):
  fold xs:
    case List/Cons:
      return xs.head + xs.tail
    case List/Nil:
      return 0

def double_all(xs):
  fold xs:
    case List/Cons:
      return List/Cons(xs.head * 2, xs.tail)
    case List/Nil:
      return List/Nil

def main():
  return (sum([1, 2, 3, 4, 5]), double_all([1, 2, 3]))
```

## `bend`: produce a structure

`bend` creates a structure from seed values. It's a recursive function written inline:

```text
bend state = initial ...:
  when condition(state):
    result = ...fork(next_state)...
  else:
    result = ...base case...
```

`fork(...)` inside the `when` branch is the recursive call. It takes one argument per state variable.

<!-- expect: Result: [1, 4, 9, 16, 25] -->
```bend
def squares(n):
  bend i = 1:
    when i <= n:
      xs = List/Cons(i * i, fork(i + 1))
    else:
      xs = List/Nil
  return xs

def main():
  return squares(5)
```

### Forking twice builds a tree

Call `fork` twice and you get a binary tree. The two branches share nothing, so they are built in parallel:

<!-- expect: Result: 92 -->
```bend
type BTree:
  Node { ~left, ~right }
  Leaf { v }

def build(depth):
  bend d = 0, v = 1:
    when d < depth:
      t = BTree/Node(fork(d + 1, v * 2), fork(d + 1, v * 2 + 1))
    else:
      t = BTree/Leaf(v)
  return t

def total(t):
  fold t:
    case BTree/Node:
      return t.left + t.right
    case BTree/Leaf:
      return t.v

def main():
  return total(build(3))
```

`v` is a heap-style index: the root is 1 and the children of `v` are `2v` and `2v + 1`. At depth 3 the leaves are 8 … 15, and their sum is 92.

## `bend` then `fold`: the Bend way to compute

The pair above is the most characteristic shape in the language:

1. `bend` builds a tree from a seed (embarrassingly parallel: each branch is independent).
2. `fold` reduces it to an answer (each subtree reduces independently, then the results combine).

You rarely need the tree to exist as a thing you care about; it's the *shape of the computation*. Computing "the number of ways to ..." or "sum over all inputs of ..." as a `bend` + `fold` lets the runtime spread the work across every core. Lesson 6 and Advanced 3 use it in earnest.

## More than one state variable

`bend` and `fold ... with` take any number of state variables, comma-separated. A `bend` that counts the steps of the Collatz sequence:

<!-- expect: Result: 111 -->
```bend
def collatz_steps(start):
  bend n = start, steps = 0:
    when n != 1:
      if n % 2 == 0:
        r = fork(n / 2, steps + 1)
      else:
        r = fork(3 * n + 1, steps + 1)
    else:
      r = steps
  return r

def main():
  return collatz_steps(27)
```

Here `bend` is acting as a plain loop: one `fork` per iteration, and the `else` branch returns the answer. It doesn't *have* to build a data structure.

## Choosing the right tool

| You want to... | Use |
| --- | --- |
| Reduce a list, tree or expression to one value | `fold` |
| Transform a structure into a same-shaped one | `fold` that rebuilds it |
| Generate a structure from a number or seed | `bend` |
| Loop with several state variables, no data | `bend` (one `fork`) |
| Look at a structure without recursing into it | `match` |
| Recurse in a way `fold`/`bend` can't express | a plain recursive function |

## Common mistakes

- **No `~` on the type's recursive fields.** `fold` only recurses into `~` fields; without the mark, `t.left` is the raw subtree and your arithmetic is garbage.
- **Using the result of a `fold` field as if it were the structure.** In `fold`, `t.left` is *the answer for the left subtree*, not the left subtree.
- **Forgetting `with`.** To pass state into the recursive calls you must declare it: `fold t with depth:`.
- **Calling `fork` outside the `when` branch,** or with the wrong number of arguments (one per state variable).
- **Writing a `bend` with no stop condition.** If `when` is always true, the structure never ends.
- **Sequential-looking folds on lists.** A fold over a list is a chain; only trees give the runtime independent work.
- **Early `return` inside a `bend`.** Assign the result (`r = ...`) in every branch and `return` after.

## Exercises

1. Write `count_leaves(t)` and `count_nodes(t)` for the `BTree` of this lesson using `fold`.
2. Write `mirror(t)` that swaps left and right subtrees (`fold` that rebuilds).
3. Write `map_tree(t, f)` applying `f` to every `val`; use `fold ... with f`.
4. Use `bend` to build a list of the first `n` powers of two.
5. Use `bend` + `fold` to compute the sum of all numbers `0 .. 2^k - 1` for `k = 10`.
6. Write `insert_all(xs)` that folds a list into a binary search tree (insertion in Intermediate 7).
7. Write a `bend` with two state variables that generates the first `n` Fibonacci numbers as a list.
8. Write `depth_of(t)` with `fold`, then a `match`-based version, and check they agree.

## Recap

- `fold` consumes a recursive structure: in each case the `~` fields are the already-computed sub-results; add `with` to pass state down.
- `bend` produces one from seed state: `fork(...)` in the `when` branch is the recursive call; `else` is the base case; use two `fork`s to build a tree.
- `bend` then `fold` is the signature shape of parallel Bend programs.
- Mark recursive fields with `~` or `fold` has nothing to recurse into.

Next: [Higher-order functions →](04-higher-order-functions.md)
