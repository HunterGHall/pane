# 9. Lists

## What & why

The list is Bend's everyday collection. It is a **singly linked list**: either empty (`List/Nil`) or a head element followed by another list (`List/Cons(head, tail)`). There are no mutable arrays; "changing" a list means building a new one. Because most data processing in Bend is "walk a list, build a result", this lesson is also where `match` and `fold` become second nature.

## Building lists

<!-- expect: Result: ([1, 2, 3], ["a", "b"]) -->
```bend
def main():
  nums = [1, 2, 3]
  words = ["a", "b"]
  return (nums, words)
```

!!! note
    An *empty* list has no elements to tell the printer it is a list, so `return []` prints as the raw encoding `λa (a List/Nil/tag)`. It is still the empty list; only the display is plain. Lesson 11 explains why.

The literal `[1, 2, 3]` is shorthand for `List/Cons(1, List/Cons(2, List/Cons(3, List/Nil)))`. You can build with the constructors directly, which is what recursive functions do:

<!-- expect: Result: [0, 1, 2] -->
```bend
def main():
  return List/Cons(0, [1, 2])
```

Elements may be anything — numbers, strings, tuples, other lists — but a *typed* list holds one kind of thing. Mixing kinds compiles untyped and misbehaves later; keep lists uniform.

## Taking a list apart: `match`

A `match` statement picks a branch by constructor. In the `Cons` branch the fields are `xs.head` and `xs.tail`:

<!-- expect: Result: (1, [2, 3]) -->
```bend
def main():
  xs = [1, 2, 3]
  match xs:
    case List/Cons:
      return (xs.head, xs.tail)
    case List/Nil:
      return (0, [])
```

You must handle every constructor, and `match xs:` binds the same name, so the fields appear as `xs.head` / `xs.tail`. You can also bind a different name: `match l = expr:` gives `l.head`, `l.tail`.

A plain `match` doesn't recurse by itself. To process the whole list you call your function on `xs.tail`:

<!-- expect: Result: 10 -->
```bend
def sum(xs):
  match xs:
    case List/Cons:
      return xs.head + sum(xs.tail)
    case List/Nil:
      return 0

def main():
  return sum([1, 2, 3, 4])
```

## `fold`: match plus automatic recursion

`fold` is the same shape but the recursive call is built in: in the `Cons` case, `xs.tail` is *already the answer for the rest of the list*:

<!-- expect: Result: 10 -->
```bend
def sum(xs):
  fold xs:
    case List/Cons:
      return xs.head + xs.tail
    case List/Nil:
      return 0

def main():
  return sum([1, 2, 3, 4])
```

Rule of thumb: whenever you'd write `f(x.tail)` on a recursive field, use `fold` and just write `x.tail`. Why does Bend have both? `fold` marks the recursion structurally, which lets the compiler optimise and parallelise it. For anything that is a straightforward walk, prefer `fold`.

To pass extra arguments down the recursion, add `with`:

<!-- expect: Result: [10, 20, 30] -->
```bend
def scale(xs, k):
  fold xs with k:
    case List/Cons:
      return List/Cons(xs.head * k, xs.tail(k))
    case List/Nil:
      return List/Nil

def main():
  return scale([1, 2, 3], 10)
```

The state `k` appears after `with`, and the recursive call is `xs.tail(k)`.

## The classic trio

`map`, `filter` and `reduce` aren't built in, but each is a three-line fold:

<!-- expect: Result: ([2, 4, 6], ([2, 4], 12)) -->
```bend
def map(xs, f):
  fold xs with f:
    case List/Cons:
      return List/Cons(f(xs.head), xs.tail(f))
    case List/Nil:
      return List/Nil

def filter(xs, keep):
  fold xs with keep:
    case List/Cons:
      if keep(xs.head):
        return List/Cons(xs.head, xs.tail(keep))
      else:
        return xs.tail(keep)
    case List/Nil:
      return List/Nil

def sum(xs):
  fold xs:
    case List/Cons:
      return xs.head + xs.tail
    case List/Nil:
      return 0

def main():
  doubled = map([1, 2, 3], lambda x: x * 2)
  evens = filter([1, 2, 3, 4, 5], lambda x: x % 2 == 0)
  return (doubled, (evens, sum(doubled)))
```

Careful what you pass to `map`: `f` is used once per element, so it gets duplicated. A lambda like `lambda x: x * 2` is fine; one that uses `x` twice (`lambda x: x + x`) is the sharp edge from lesson 7 and gives *wrong results*. Until Advanced 2, use `x * 2` rather than `x + x` here. (Intermediate 4 builds a safe, reusable list library.)

## List comprehensions

For the very common map-and-filter case Bend has Python-style comprehensions:

<!-- expect: Result: [4, 9, 16] -->
```bend
def main():
  return [x * x for x in [1, 2, 3, 4] if x > 1]
```

## Standard-library list functions

Only a handful exist in 0.2.38:

<!-- expect: Result: (3, ([5, 6, 7], ([7, 6, 5], ([1, 2, 3, 4], [2, 4])))) -->
```bend
def main():
  (n, xs) = List/length([5, 6, 7])
  rev = List/reverse(xs)
  joined = List/concat([1, 2], [3, 4])
  evens = List/filter([1, 2, 3, 4], lambda x: (x % 2) == 0)
  return (n, (xs, (rev, (joined, evens))))
```

- `List/length(xs)` returns **a tuple** `(length, list)`: because using the list to count it consumes it, the function hands it back to you. This idiom — "use a thing and get it back" — appears whenever a built-in needs to look inside something (`Map/get` does the same).
- `List/reverse`, `List/concat(xs, ys)`, `List/flatten(xss)`, `List/filter(xs, pred)`, `List/split_once`.

## Common patterns

**Build with an accumulator, then reverse.** Cons-ing onto the front is the cheap end of a list, so a loop that conses ends up with the items in reverse order:

<!-- expect: Result: [1, 2, 3] -->
```bend
def count_up(n, acc):
  if n == 0:
    return acc
  else:
    return count_up(n - 1, List/Cons(n, acc))

def main():
  return count_up(3, [])
```

(Counting *down* from `n` and consing each number onto the front produces `[1, 2, 3]` — so here no reverse is needed.) When the order comes out backwards, finish with `List/reverse`.

**Append to the end** is expensive: it must walk the whole list.

<!-- expect: Result: [1, 2, 3, 4] -->
```bend
def main():
  return List/concat([1, 2, 3], [4])
```

If you append inside a loop you get quadratic time. Build in reverse and reverse once, or use a difference list (`DiffList/new`, `DiffList/append`, `DiffList/to_list`), which supports constant-time appends.

**Indexing** means walking:

<!-- expect: Result: 30 -->
```bend
def nth(xs, i):
  match xs:
    case List/Nil:
      return 0
    case List/Cons:
      if i == 0:
        return xs.head
      else:
        return nth(xs.tail, i - 1)

def main():
  return nth([10, 20, 30, 40], 2)
```

That's O(n). If you need fast random access, use a `Map` or a `Tree` (next lesson).

## Common mistakes

- **Forgetting a case.** `match` and `fold` need `List/Nil` *and* `List/Cons`.
- **Using `xs.tail` in a `fold` as if it were a list.** In a `fold`, it is the *result* of the recursive call; if you need the raw tail, use `match`.
- **Looking for `xs[0]`, `len(xs)`, `xs.append(x)`.** None exist. Use `match`, `List/length`, `List/concat`.
- **Passing a duplicating lambda to a hand-written `map`.** `lambda x: x + x` duplicates `x`; use `x * 2`. (Advanced 2 explains.)
- **Appending in a loop.** Quadratic; accumulate in reverse instead.
- **Mixed element types.** The type checker will object if you annotate; untyped code just misbehaves.

## Exercises

1. Write `length(xs)` with `fold`, and `product(xs)`.
2. Write `last(xs)` returning the last element (assume non-empty).
3. Write `take(xs, n)` returning the first `n` elements, and `drop(xs, n)`.
4. Write `zip(xs, ys)` returning a list of pairs, stopping at the shorter list.
5. Write `range(lo, hi)` with `bend` returning `[lo, lo+1, ..., hi-1]`.
6. Write `max_of(xs)` for a non-empty list of numbers.
7. Using comprehensions, write the list of squares of the odd numbers below 20.
8. Write `contains(xs, x)` returning `1` or `0`; then `count(xs, x)`.

## Recap

- A list is `List/Nil` or `List/Cons(head, tail)`; `[1, 2, 3]` is sugar.
- Take a list apart with `match` (raw `head`/`tail`) or `fold` (the tail is already the recursive answer); `fold ... with state` carries arguments down.
- `map`, `filter`, `reduce` are three-line folds; comprehensions cover the common cases.
- Lists are linked: cons at the front is cheap, appending and indexing are O(n). `List/length` returns `(length, list)`.

Next: [Maps & trees →](10-hashmaps-and-sets.md)
