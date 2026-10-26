# 7. Data structures

## What & why

There are no mutable arrays or hash tables in Bend, so familiar data structures take a different shape: **persistent** structures where "inserting" returns a new structure that shares most of the old one. This lesson builds the ones you'll reach for most — stack, queue, binary search tree, sorted list and set — and shows how to choose between them and the built-in `List`, `Map` and `Tree`.

## Stack

A list already *is* a stack: pushing and popping at the front are O(1).

<!-- expect: Result: (3, 2) -->
```bend
def push(stack, x):
  return List/Cons(x, stack)

def pop(stack):
  match stack:
    case List/Cons:
      return Maybe/Some((stack.head, stack.tail))
    case List/Nil:
      return Maybe/None

def top_or(stack, default):
  match stack:
    case List/Cons:
      return stack.head
    case List/Nil:
      return default

def main():
  s = push(push(push([], 1), 2), 3)
  match popped = pop(s):
    case Maybe/Some:
      (*, rest) = popped.value
      return (top_or(s, 0), top_or(rest, 0))
    case Maybe/None:
      return (0, 0)
```

`pop` returns a `Maybe` of a pair `(top, rest)` because popping an empty stack must be representable. The original `s` is untouched: that's persistence, and it makes "undo" free — just keep the old stack.

## Queue

A queue needs fast access to both ends. The classic functional queue uses **two lists**: items are added to `back` and taken from `front`; when `front` runs out, `back` is reversed into it.

<!-- expect: Result: [1, 2, 3, 4] -->
```bend
object Queue { front, back }

def empty():
  return Queue { front: [], back: [] }

def enqueue(q, x):
  open Queue: q
  return Queue { front: q.front, back: List/Cons(x, q.back) }

def dequeue(q):
  open Queue: q
  match q.front:
    case List/Cons:
      return Maybe/Some((q.front.head, Queue { front: q.front.tail, back: q.back }))
    case List/Nil:
      rev = List/reverse(q.back)
      match rev:
        case List/Cons:
          return Maybe/Some((rev.head, Queue { front: rev.tail, back: [] }))
        case List/Nil:
          return Maybe/None

# Take everything out, in order.
def drain(q):
  match r = dequeue(q):
    case Maybe/Some:
      (item, rest) = r.value
      return List/Cons(item, drain(rest))
    case Maybe/None:
      return List/Nil

def main():
  q = enqueue(enqueue(enqueue(enqueue(empty, 1), 2), 3), 4)
  return drain(q)
```

Each item is reversed at most once, so enqueue and dequeue are O(1) *amortised*.

## Binary search tree

A binary search tree keeps keys ordered: everything on the left of a node is smaller, everything on the right larger. Lookups and inserts take time proportional to the depth.

<!-- expect: Result: ([1, 2, 3, 5, 8, 9], (1, 0)) -->
```bend
type Bst:
  Node { key, ~left, ~right }
  Empty

def insert(t, x):
  match t:
    case Bst/Empty:
      return Bst/Node(x, Bst/Empty, Bst/Empty)
    case Bst/Node:
      if x < t.key:
        return Bst/Node(t.key, insert(t.left, x), t.right)
      elif x > t.key:
        return Bst/Node(t.key, t.left, insert(t.right, x))
      else:
        return t

def contains(t, x):
  match t:
    case Bst/Empty:
      return 0
    case Bst/Node:
      if x < t.key:
        return contains(t.left, x)
      elif x > t.key:
        return contains(t.right, x)
      else:
        return 1

# In-order traversal gives the keys sorted.
def to_list(t):
  fold t:
    case Bst/Node:
      return List/concat(t.left, List/Cons(t.key, t.right))
    case Bst/Empty:
      return List/Nil

def from_list(xs):
  fold xs:
    case List/Cons:
      return insert(xs.tail, xs.head)
    case List/Nil:
      return Bst/Empty

def main():
  t = from_list([5, 2, 8, 1, 9, 3])
  return (to_list(t), (contains(t, 5), contains(t, 7)))
```

Notes:

- `insert` returns a new tree; the unchanged subtrees are shared with the old one, not copied.
- This tree is **not self-balancing**. Inserting already-sorted keys produces a degenerate, list-like tree with no parallel structure and O(n) lookups. For balanced behaviour, insert in a shuffled order or implement a balancing scheme (AVL or red–black).
- `to_list` is a `fold`: `t.left` and `t.right` are the *lists* for the subtrees.

A BST is also a **set** (keys only) and, by storing a value next to each key, a **map with arbitrary keys** — useful when `Map`'s `u24` keys aren't enough.

## Sorted list as a priority queue

For small collections, a sorted list is the simplest priority queue: insert in order, the smallest is at the front.

<!-- expect: Result: [1, 3, 4, 7, 9] -->
```bend
def insert_sorted(xs, x):
  match xs:
    case List/Nil:
      return List/Cons(x, List/Nil)
    case List/Cons:
      if x <= xs.head:
        return List/Cons(x, xs)
      else:
        return List/Cons(xs.head, insert_sorted(xs.tail, x))

def main():
  q = insert_sorted(insert_sorted(insert_sorted(insert_sorted(insert_sorted([], 7), 3), 9), 1), 4)
  return q
```

Insert is O(n), taking the minimum O(1). For larger queues use a heap (a tree with the heap property), which you can build the same way as the BST.

## Sets and dictionaries

You already have two options for **sets of numbers and characters**:

- the built-in `Map`, used as `{x: 1}` with `Map/contains`;
- the `Bst` above.

And for key-to-value lookups, `Map` (number keys) or a `Bst` of `(key, value)` pairs compared on the key.

## Association lists

The cheapest dictionary of all is a list of pairs:

<!-- expect: Result: (2, 0) -->
```bend
def lookup(pairs, key, default):
  match pairs:
    case List/Nil:
      return default
    case List/Cons:
      (k, v) = pairs.head
      if k == key:
        return v
      else:
        return lookup(pairs.tail, key, default)

def main():
  table = [(1, 10), (2, 2), (3, 30)]
  return (lookup(table, 2, 0), lookup(table, 9, 0))
```

Fine for a handful of entries; O(n) per lookup.

## Choosing

| Need | Use | Why |
| --- | --- | --- |
| LIFO | `List` | push/pop at the front are O(1) |
| FIFO | two-list `Queue` | amortised O(1) at both ends |
| Ordered keys of any comparable type | `Bst` | O(depth) lookup, in-order traversal |
| Number/character keys, many updates | `Map` | built-in binary trie, O(log n) |
| Tiny dictionary | association list | simplest |
| Data to process in parallel | `Tree` / your own tree | independent halves |
| Priority queue | sorted list (small) or a heap | min at the front |

## Common mistakes

- **Expecting `insert` to modify the tree.** It returns a new one; use the result.
- **Inserting sorted data into an unbalanced BST,** creating a chain.
- **Using a list as a queue** and appending at the end every time (quadratic).
- **Forgetting that `Maybe`-returning operations need handling:** `dequeue` of an empty queue is `None`.
- **Storing keys that aren't numbers in a `Map`.** `Map` keys must be `u24`.
- **Comparing keys with `==` that aren't numbers.** Strings need `String/equals`.

## Exercises

1. Add `size(q)` and `peek(q)` to the queue.
2. Write `bst_min(t)` and `bst_max(t)` returning `Maybe`.
3. Write `delete(t, x)` for the BST (the tricky case is a node with two children).
4. Write `height(t)` for the BST with `fold`.
5. Build a balanced BST from a *sorted* list by always choosing the middle element as the root.
6. Implement a set of numbers as a BST with `union` (insert every element of one into the other).
7. Write `word_count(words)` using a BST of `(word, count)` pairs, with a string comparison of your own.
8. Implement a leftist heap (`Node { rank, key, ~left, ~right }`) with `merge`, `insert` and `pop_min`.

## Recap

- Data structures are persistent: operations return new versions, sharing what didn't change.
- Stack = list; queue = two lists; BST = recursive type with `insert`/`contains`/in-order `fold`.
- A BST is also a set and a map for any comparable keys, but it only balances if you make it.
- Match the structure to the access pattern, and prefer trees when you want parallel work.

Next: [Error handling & monads →](08-error-handling.md)
