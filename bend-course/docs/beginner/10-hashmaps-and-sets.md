# 10. Maps & trees

## What & why

Lists are linear: to reach the millionth element you walk a million cells, and a walk is inherently sequential. Bend's other two built-in collections are **trees**, and trees are the secret of the language. A balanced binary tree has depth *log n*, lookups are fast, and — crucially — its two halves are independent, so they can be processed on different cores at the same time.

This lesson covers `Map` (keys to values, backed by a binary trie) and `Tree` (a binary tree of values), then shows the pattern that makes Bend fast: **build a tree, fold a tree.**

## Maps

A `Map` associates `u24` keys with values. Keys are numbers, characters or symbols; values can be anything.

<!-- expect: Result: ("one", "uno") -->
```bend
def main():
  m = {1: "one", 2: "two"}
  m[3] = "three"          # insert a new key
  first = m[1]            # look up
  m[1] = "uno"            # replace
  return (first, m[1])
```

- `{ }` is an empty map; `{k: v, ...}` a literal.
- `m[k]` reads, `m[k] = v` writes, `m[k] @= f` applies `f` to the existing value.
- Characters and symbols work as keys because they're numbers: `{'a': 1, 'b': 2}` and `` `hi` `` (a "symbol": up to four base-64 characters packed into a `u24`).

<!-- expect: Result: 7 -->
```bend
def main():
  m = {'a': 1, 'b': 2}
  m['a'] @= lambda n: n + 4
  return m['a'] + m['b']
```

!!! note
    Maps are immutable like everything else. `m[k] = v` doesn't change the old map; it binds the name `m` to a *new* map from that line on. Under the hood a read is `(value, m) = Map/get(m, k)` — it hands the map back — and the `m[k]` syntax does that threading for you.

### Missing keys

Looking up a key that isn't there is an error you must prevent. Use `Map/contains` or `Map/get_check`. Both return a pair — the answer *and* the map, like `List/length`:

<!-- expect: Result: (1, 0) -->
```bend
def main():
  m = {5: 50, 6: 60}
  (has5, m) = Map/contains(m, 5)
  (has9, m) = Map/contains(m, 9)
  return (has5, has9)
```

`Map/get_check(m, k)` returns `(Maybe/Some(v) or Maybe/None, m)`; lesson 11 shows how to consume a `Maybe`.

### Counting with a map

Count how often each character appears in a word:

<!-- expect: Result: (2, 1) -->
```bend
def bump(counts, c):
  (seen, counts) = Map/contains(counts, c)
  if seen:
    counts[c] @= lambda n: n + 1
    return counts
  else:
    counts[c] = 1
    return counts

def count_chars(s):
  counts = {}
  fold s with counts:
    case String/Cons:
      return s.tail(bump(counts, s.head))
    case String/Nil:
      return counts

def main():
  counts = count_chars("banana")
  return (counts['n'], counts['b'])
```

(`banana` has 2 `n`s and 1 `b`.)

### Sets

There is no separate set type. Use a map whose values are `1` (or anything) and test with `Map/contains`:

<!-- expect: Result: (1, 0) -->
```bend
def main():
  seen = {}
  seen[10] = 1
  seen[20] = 1
  (a, seen) = Map/contains(seen, 10)
  (b, seen) = Map/contains(seen, 30)
  return (a, b)
```

## Trees

`Tree(T)` is a binary tree that stores values **at the leaves**. There are special literals:

<!-- expect: Result: [1, 2, 3, 4] -->
```bend
def main():
  tree = ![![!1, !2], ![!3, !4]]
  return Tree/to_list(tree)
```

- `!x` is `Tree/Leaf(x)`.
- `![a, b]` is `Tree/Node(a, b)`.
- `Tree/to_list` flattens left to right; `Tree/reverse` mirrors the tree.

You can define your own tree shapes with `type` (Intermediate 1); the builtin one is the quickest start.

## The pattern: build a tree, fold a tree

Suppose you need the sum of the numbers 0 … 2ⁿ−1. You could cons up a list and sum it — sequential from start to finish. Or you can **generate a tree** whose leaves are the numbers, then **fold** it:

<!-- expect: Result: 120 -->
```bend
def gen(depth):
  bend d = 0, i = 0:
    when d < depth:
      t = ![fork(d + 1, i * 2), fork(d + 1, i * 2 + 1)]
    else:
      t = !i
  return t

def sum(t):
  fold t:
    case Tree/Node:
      return t.left + t.right
    case Tree/Leaf:
      return t.value

def main():
  return sum(gen(4))
```

`gen(4)` makes a tree of depth 4 with 16 leaves. Each step down doubles the number `i` (left child) or doubles it and adds one (right child), so the leaves are numbered `0, 1, 2, … 15` in order; their sum is 120.

Both halves matter:

- **`bend` with two `fork`s** builds the two subtrees independently — they can be created on different cores.
- **`fold` with `t.left + t.right`** reduces the two subtrees independently — they can be summed on different cores — and then combines the answers.

Compare with a list sum, where each step needs the previous one. The tree version has *depth log n* of dependent steps instead of *n*. This is the whole trick of Bend: **shape your data like a tree and your folds parallelise by themselves.**

!!! tip
    You never mention threads. The only decision you make is the *shape* of the data. A balanced tree is ideal; a lopsided tree (basically a list) gets no speedup.

## Choosing a collection

| You need | Use |
| --- | --- |
| Small sequence, walk front to back | `List` |
| Lookup by number / character key | `Map` |
| Big dataset to process in parallel | `Tree` (build with `bend`, reduce with `fold`) |
| A sorted structure | a tree you build yourself (Intermediate 7) |

## Common mistakes

- **Reading a key that isn't there.** It's an unrecoverable error; test with `Map/contains` first.
- **Using a string as a map key.** Keys must be `u24`. Hash the string yourself or use a different structure.
- **Using `m` after a write as if it were the old map.** After `m[k] = v`, the name `m` means the new map.
- **Expecting `Map` iteration.** There's no `keys()`/`items()` built in. Keep the keys in a list alongside, or traverse your own tree type.
- **Building a degenerate tree.** A tree where every `fork` goes to one side is a list in disguise: no parallelism.
- **Thinking `Tree` values live in the nodes.** In the builtin `Tree`, values are in the leaves only.

## Exercises

1. Build a map from `1, 2, 3` to their squares and look up `2`.
2. Write `has_duplicates(list)` using a map as a set.
3. Change `gen` to produce leaves numbered from 1 instead of 0 and predict the new sum before running it.
4. Write `depth(tree)` returning the depth of a `Tree` (leaf = 0).
5. Write `tree_map(tree, f)` applying `f` to every leaf.
6. Build a tree of depth 10 with `bend` whose leaves are `1`; fold it to count the leaves (1024).
7. Use `Tree/reverse` and `Tree/to_list` to reverse a tree of the numbers 1–8.
8. Count the words in a list of strings by using their first characters as map keys.

## Recap

- `Map` is a persistent number-keyed map: `{k: v}`, `m[k]`, `m[k] = v`, `m[k] @= f`; check keys with `Map/contains`; there is no separate set type.
- `Tree` stores values at leaves: `!x` and `![a, b]`.
- Trees are the unit of parallelism: build with a two-`fork` `bend`, reduce with `fold`; the independent halves run concurrently.
- Lists are sequential; trees are what make Bend scale.

Next: [Maybe, Result & IO →](11-option-result-and-files.md)
