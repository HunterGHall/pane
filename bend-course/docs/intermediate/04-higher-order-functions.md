# 4. Higher-order functions & a list library

## What & why

Bend's standard library is tiny: there's no `map`, no `zip`, no `sum`. That's not a flaw you work around; it's the language telling you to build your own small library of **higher-order functions** — functions that take or return functions — and reuse it everywhere. This lesson builds that library, with attention to the one rule that keeps it correct: duplication safety.

## The core trio

<!-- expect: Result: ([2, 4, 6], ([2, 4], 10)) -->
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

def reduce(xs, f, z):
  fold xs with f, z:
    case List/Cons:
      return f(xs.head, xs.tail(f, z))
    case List/Nil:
      return z

def main():
  evens = filter([1, 2, 3, 4, 5, 6], lambda x: x % 2 == 0)
  return (map([1, 2, 3], lambda x: x * 2), (filter([1, 2, 3, 4], lambda x: x % 2 == 0), reduce([1, 2, 3, 4], lambda a, b: a + b, 0)))
```

`reduce(xs, f, z)` folds from the right: `f(1, f(2, f(3, f(4, z))))`. The state clause `with f, z` lists *both* values that the recursive calls need.

## More building blocks

<!-- expect: Result: ([(1, 4), (2, 5)], ([1, 2], (1, 0))) -->
```bend
def zip(xs, ys):
  match xs:
    case List/Cons:
      match ys:
        case List/Cons:
          return List/Cons((xs.head, ys.head), zip(xs.tail, ys.tail))
        case List/Nil:
          return List/Nil
    case List/Nil:
      return List/Nil

def take(xs, n):
  match xs:
    case List/Cons:
      if n == 0:
        return List/Nil
      else:
        return List/Cons(xs.head, take(xs.tail, n - 1))
    case List/Nil:
      return List/Nil

def any(xs, pred):
  fold xs with pred:
    case List/Cons:
      return pred(xs.head) | xs.tail(pred)
    case List/Nil:
      return 0

def main():
  return (zip([1, 2, 3], [4, 5]), (take([1, 2, 3, 4], 2), (any([1, 2, 3], lambda x: x == 2), any([1, 2, 3], lambda x: x == 9))))
```

`zip` uses nested `match` because Imp can't match two lists at once.

## Functions that return functions

Currying and composition are one-liners, and partial application lets you build specialised helpers:

<!-- expect: Result: ([11, 12, 13], [3, 5, 7]) -->
```bend
def map(xs, f):
  fold xs with f:
    case List/Cons:
      return List/Cons(f(xs.head), xs.tail(f))
    case List/Nil:
      return List/Nil

def add(a, b):
  return a + b

def compose(f, g):
  return lambda x: f(g(x))

def main():
  add10 = add(10)                       # partial application
  inc = add(1)
  double = lambda x: x * 2
  step = compose(inc, double)           # inc(double(x))
  return (map([1, 2, 3], add10), map([1, 2, 3], step))
```

## The duplication rule

Lesson 7 of the Beginner level warned that a lambda which duplicates a variable must not itself be duplicated. `map` duplicates `f` once per element, so the function you pass must use its parameter **at most once** — or the whole thing may silently give wrong answers:

```text
map([1, 2, 3], lambda x: x + x)     # x used twice: UNSAFE
map([1, 2, 3], lambda x: x * 2)     # x used once: safe
```

Running the unsafe version in Bend 0.2.38 gives something like `[3, 4, *]` instead of `[2, 4, 6]`. No error — just a wrong list.

`x * x` is just as unsafe as `x + x`: any lambda that mentions its parameter twice qualifies. Naming it with a top-level `def` doesn't help either — passing `twice` to `map` fails the same way.

Rules of thumb:

1. **Pass linear lambdas** to higher-order functions: use each parameter once (`x * 2`, `x + 1`, `f(x)`).
2. **When the logic needs its argument twice, don't pass it as a value.** Call it directly, where the fold is written. A list comprehension does exactly this — its expression is inlined into the fold, not passed as a function:

<!-- expect: Result: ([2, 4, 6], [1, 4, 9]) -->
```bend
def twice(x):
  return x + x

def main():
  return ([twice(x) for x in [1, 2, 3]], [x * x for x in [1, 2, 3]])
```

3. **Or specialise the fold:** write `double_all` / `square_all` as their own small folds instead of reusing a generic `map`. Repetitive, but always correct.

Advanced 2 explains exactly why. For now, when a higher-order call returns something strange (a `*` in a list is the telltale sign), look for a lambda that uses its argument twice.

## Building lists efficiently: `DiffList`

Appending to the end of a list is O(n). A **difference list** represents a list as a function, so appending is just composition:

<!-- expect: Result: [1, 2, 3] -->
```bend
def main():
  d = DiffList/new
  d = DiffList/append(d, 1)
  d = DiffList/append(d, 2)
  d = DiffList/append(d, 3)
  return DiffList/to_list(d)
```

`DiffList/cons` adds to the front, `DiffList/concat` joins two difference lists, `DiffList/wrap(x)` makes a single-element one. You can't `match` on a difference list; convert with `to_list` when you're done building.

## List comprehensions

For simple map/filter combinations:

<!-- expect: Result: [4, 16] -->
```bend
def main():
  return [x * x for x in [1, 2, 3, 4] if x % 2 == 0]
```

(Comprehensions are sugar for a fold, so the same duplication caution applies to the expression.)

## A tiny library in one file

Collect these in `list.bend` and `import` them (Intermediate 9). That is how real Bend programs work: a few dozen lines of helpers, defined once.

## Common mistakes

- **Passing a lambda that uses its parameter twice** to `map`/`filter`/`reduce`.
- **Forgetting `with f`** — then the recursive call can't see the function.
- **Calling `xs.tail` without the state** inside a `fold ... with`: it must be `xs.tail(f)`.
- **Looking for built-in `sum`/`len`/`zip`/`take`.** Write them once, reuse them.
- **Appending in a loop.** Quadratic; use `DiffList`.
- **Assuming `reduce` goes left to right.** The fold is a right fold.

## Exercises

1. Write `length(xs)`, `sum(xs)`, `product(xs)` using `reduce`.
2. Write `all(xs, pred)` (the mirror of `any`) and `count(xs, pred)`.
3. Write `drop(xs, n)` and `split_at(xs, n)` returning a tuple.
4. Write `flat_map(xs, f)` where `f` returns a list; test with `lambda x: [x, x]` — and notice why `[x, x]` duplicates `x`!
5. Write `iterate(f, x, n)` returning `[x, f(x), f(f(x)), ...]` (n items) with `bend`.
6. Write `enumerate(xs)` giving `(index, item)` pairs.
7. Write `group_by_parity(xs)` returning `(evens, odds)` with one `fold`.
8. Rebuild `reverse` with `reduce` and a `DiffList`.

## Recap

- `map`, `filter`, `reduce`, `zip`, `take`, `any` are all short folds; put them in a library file.
- Pass the state a fold needs with `with a, b`; recurse with `xs.tail(a, b)`.
- Partial application and `compose` build specialised functions from general ones.
- A function passed to a duplicating higher-order function must use its parameter at most once.
- `DiffList` gives O(1) appends.

Next: [Generics & the type checker →](05-generics-and-type-checking.md)
