# 5. Generics & the type checker

## What & why

Bend is dynamically flexible but comes with an **optional, Hindley–Milner-style type checker**. Where you write annotations, it verifies them; where you don't, values are `Any` and nothing is checked. Types matter more as programs grow: they catch the classic "passed a string where a number belongs" bug *before* the program runs, and — since mixing `u24`/`i24`/`f24` produces silent garbage — they are the only guard you have against it.

## What gets checked

Annotations are checked at compile time (`bend check`, `bend run-c`, ...):

<!-- check: fail -->
```bend
def add(x: u24, y: u24) -> u24:
  return x + y

def main() -> u24:
  return add(1, "two")
```

An unannotated function has the type `Any -> Any` and accepts anything:

<!-- expect: Result: 3 -->
```bend
def add(x, y):
  return x + y

def main():
  return add(1, 2)
```

Mixing annotated and unannotated code is fine: the checker verifies the annotated functions, trusting the unannotated ones.

## The built-in types

| Type | Meaning |
| --- | --- |
| `u24`, `i24`, `f24` | the three number kinds |
| `(A, B)`, `(A, B, C)` | tuples |
| `List(T)`, `String`, `Tree(T)`, `Map(T)` | the standard containers |
| `Maybe(T)`, `Result(O, E)` | optional values and results |
| `IO(T)` | an IO action producing a `T` |
| `A -> B` | a function from `A` to `B` |
| `Any` | untyped; accepted everywhere |
| `_` | "work this one out for me" |
| `None` | the eraser `*` |

Function types chain: `u24 -> u24 -> u24` takes two numbers and returns one.

## Catching the mix-ups Bend can't otherwise see

The big payoff is number kinds:

<!-- check: fail -->
```bend
def bad(x: u24, y: f24) -> f24:
  return x + y

def main():
  return 0
```

The error shows that `+` needs both sides to be the same kind. Without the annotations, `bad(1, 2.0)` would compile and return nonsense.

Collections are checked element-wise:

<!-- check: fail -->
```bend
def main() -> List(u24):
  return [1, "two"]
```

## Generic functions

Use a **type variable** (any capitalised name you haven't defined: `A`, `B`, `T`) to say "any type, but the same everywhere":

<!-- expect: Result: [2, 3, 4] -->
```bend
def map(xs: List(A), f: A -> B) -> List(B):
  fold xs with f:
    case List/Cons:
      return List/Cons(f(xs.head), xs.tail(f))
    case List/Nil:
      return List/Nil

def main() -> List(u24):
  return map([1, 2, 3], lambda x: x + 1)
```

`map` works for any `A` and `B`: numbers to numbers, strings to lengths, anything. The annotation also *guarantees* the shape: a `List(A)` in gives a `List(B)` out, and `f` must turn an `A` into a `B`.

If your implementation can't live up to the signature, the checker says so:

<!-- check: fail -->
```bend
def first(xs: List(A)) -> A:
  match xs:
    case List/Cons:
      return xs.head
    case List/Nil:
      return 0
```

(The `Nil` branch returns a number, but the signature promises an `A` — which could be a string.)

## Generic data types

Declare the type variables after the type name, then use them in the field types:

<!-- expect: Result: (5, (7, ("a", 1))) -->
```bend
type Option(T):
  Has { value: T }
  Lacks

type Pair(A, B):
  Both { first: A, second: B }

def or_else(o: Option(T), default: T) -> T:
  match o:
    case Option/Has:
      return o.value
    case Option/Lacks:
      return default

def swap(p: Pair(A, B)) -> Pair(B, A):
  match p:
    case Pair/Both:
      return Pair/Both(p.second, p.first)

def first(p: Pair(A, B)) -> A:
  match p:
    case Pair/Both:
      return p.first

def main():
  swapped = swap(Pair/Both(1, "a"))
  return (or_else(Option/Has(5), 0), (or_else(Option/Lacks, 7), (first(swapped), 1)))
```

All constructors of `Option(T)` share the same `T`: an `Option(u24)` can't hold a string.

Recursive generic types:

<!-- expect: Result: 4 -->
```bend
type Bin(T):
  Node { value: T, ~left: Bin(T), ~right: Bin(T) }
  Empty

def size(t: Bin(T)) -> u24:
  fold t:
    case Bin/Node:
      return 1 + t.left + t.right
    case Bin/Empty:
      return 0

def main() -> u24:
  leaf = lambda v: Bin/Node(v, Bin/Empty, Bin/Empty)
  return size(Bin/Node(1, leaf(2), Bin/Node(3, leaf(4), Bin/Empty)))
```

## Inferred types: `_`

Put `_` where you want the checker to fill in the answer — handy when the real type is long:

<!-- check: check -->
```bend
def add(x: _, y: _) -> _:
  return x + y
```

Behind the scenes arithmetic gets special types `Number` and `Integer` meaning "some numeric kind, the same on both sides". You never write those yourself.

## Turning the checker off — and on

- **Per function:** put `unchecked` before the name to skip checking a function whose annotations you trust (or that uses features the checker can't express). `checked` forces a check on an un-annotated function.
- **Whole program:** `bend run-c -Ono-type-check file.bend`.

<!-- check: check -->
```bend
def unchecked pun(x: u24) -> f24:
  return x
```

Reach for `unchecked` as a last resort; you're promising the compiler something it can't verify.

## What the checker can't do

It doesn't understand:

- **superpositions** (`{a b}`, Advanced 2),
- **scopeless lambdas** (`$x`, Advanced 6),
- terms outside Hindley–Milner (e.g. self-application `lambda x: x(x)`).

Functions that use those must be unannotated or `unchecked`.

## A practical policy

1. Annotate the **public** functions and data constructors; leave tiny local helpers bare.
2. Always annotate **numeric** functions — it's the only protection from kind mix-ups.
3. Run `bend check` constantly; it's near-instant.
4. Annotate `main` with `-> u24` / `-> IO(u24)` if you like, but not when `main` takes arguments (the annotation then fails to unify in 0.2.38).

## Common mistakes

- **Forgetting that unannotated means unchecked.** A bug hiding in `Any` code won't be flagged.
- **Using a type variable that's secretly a real type** (e.g. naming your type `T`; it collides with the prelude's own `T`).
- **Annotating a constructor field as `u24` and then storing a float.** The checker rejects it — a good thing.
- **Annotating `main(args)` with an IO return type** — drop the return annotation.
- **Over-constraining generics:** if your function does arithmetic on `A`, it isn't generic; use `u24` or `_`.
- **Treating checker errors as noise.** `Can't unify` messages name the two types that clash; read both.

## Exercises

1. Annotate the `sum`, `filter` and `reduce` functions from lesson 4 with generic types.
2. Define `type Either(L, R)` with `Left` and `Right` and write `map_right`.
3. Write `fst(p: (A, B)) -> A` using tuple destructuring.
4. Cause a `Can't unify` error on purpose and explain it in your own words.
5. Define a generic `Stack(T)` with `push`, `pop` returning `Maybe`, and `size`.
6. Write `length(xs: List(A)) -> u24` and call it on both a list of numbers and a list of strings.
7. Mark a function `unchecked` that stores a number where a string was declared, and watch it run anyway.
8. Annotate your task tracker from the Beginner capstone and fix whatever the checker finds.

## Recap

- Types are optional and checked where written; un-annotated code is `Any`.
- Annotate numeric functions especially: it's the only protection from `u24`/`i24`/`f24` mix-ups.
- Type variables (`A`, `B`, `T`) make functions and types generic; all uses of one variable must agree.
- `_` asks for inference; `unchecked`/`checked` and `-Ono-type-check` override the checker.
- Superpositions and scopeless lambdas are beyond the checker.

Next: [Divide and conquer →](06-divide-and-conquer.md)
