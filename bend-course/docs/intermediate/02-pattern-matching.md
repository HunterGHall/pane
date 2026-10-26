# 2. Pattern matching

## What & why

You define data with `type`; you consume it with **pattern matching**. A `match` looks at which constructor a value was built with and runs the corresponding branch, giving you its fields. It replaces `if`-chains full of type tests and null checks, and — because the compiler knows every constructor — it tells you when you forgot one.

Bend has two syntaxes (the Python-like *Imp* you've been using and the Haskell-like *Fun*) and they match differently. This lesson covers both.

## `match` in Imp

<!-- expect: Result: "mid" -->
```bend
type Size:
  Small
  Medium
  Large

def label(s):
  match s:
    case Size/Small:
      return "low"
    case Size/Medium:
      return "mid"
    case Size/Large:
      return "high"

def main():
  return label(Size/Medium)
```

Rules:

- One `case` per constructor, written `case Type/Ctor:`.
- Every branch ends the function (`return`) or assigns the same names (see below).
- Matching on a *variable* binds fields as `name.field`. To match an expression and name it at the same time: `match v = expr:` gives `v.field`.

<!-- expect: Result: 11 -->
```bend
type Shape:
  Circle { r }
  Rect { w, h }

def main():
  match s = Shape/Rect(2, 5):
    case Shape/Circle:
      return s.r
    case Shape/Rect:
      return s.w + s.h + 4
```

## Exhaustiveness: the compiler checks you

Leave a constructor out and Bend refuses to compile:

<!-- check: fail -->
```bend
type Shape:
  Circle { r }
  Rect { w, h }

def f(s):
  match s:
    case Shape/Circle:
      return 1

def main():
  return f(Shape/Rect(1, 1))
```

```text
Non-exhaustive 'match' expression of type 'Shape'. Case 'Shape/Rect' not covered.
```

This is the biggest practical benefit of ADTs: when you add a variant, the compiler lists every function that needs updating.

## The default case

Use `case _:` for "everything else":

<!-- expect: Result: (1, 2) -->
```bend
type Shape:
  Circle { r }
  Rect { w, h }

def is_circle(s):
  match s:
    case Shape/Circle:
      return 1
    case _:
      return 0

def main():
  return (is_circle(Shape/Circle(1)) + is_circle(Shape/Rect(1, 1)), 2)
```

Use it sparingly: a `_` silences the exhaustiveness check for future variants.

## Binding results instead of returning

A `match` can compute a value and continue, if every branch assigns the same names:

<!-- expect: Result: 14 -->
```bend
type Op:
  Plus
  Times

def main():
  op = Op/Times
  match op:
    case Op/Plus:
      result = 3 + 4
    case Op/Times:
      result = 7 * 2
  return result
```

## Nested patterns: match inside match

Imp's `match` examines one constructor at a time. To look deeper, match again on the field:

<!-- expect: Result: (3, (5, 0)) -->
```bend
def first_two(xs):
  match xs:
    case List/Cons:
      match xs.tail:
        case List/Cons:
          return xs.head + xs.tail.head
        case List/Nil:
          return xs.head
    case List/Nil:
      return 0

def main():
  return (first_two([1, 2, 3]), (first_two([5]), first_two([])))
```

Fields of fields are reachable: `xs.tail.head` is the second element once you've matched `xs.tail`.

## Matching numbers: `switch`

Numbers aren't constructors; use `switch` (lesson 4). Remember the ordered `0, 1, 2, ..., _` and the `n-k` predecessor name in the last case:

<!-- expect: Result: (100, (101, 5)) -->
```bend
def f(n):
  switch n:
    case 0:
      return 100
    case 1:
      return 101
    case _:
      return n-2

def main():
  return (f(0), (f(1), f(7)))
```

In the last case, `n-2` is a variable holding the original number minus the two cases already ruled out (here `7 - 2 = 5`). With one explicit case it would be `n-1`; with three, `n-3`.

## Destructuring tuples

A tuple is matched by assigning to a pattern. This is irrefutable (it can't fail), so there's no `match`:

<!-- expect: Result: 30 -->
```bend
def sum_pairs(ps):
  fold ps:
    case List/Cons:
      (a, b) = ps.head
      return a + b + ps.tail
    case List/Nil:
      return 0

def main():
  return sum_pairs([(1, 2), (3, 4), (5, 15)])
```

## Fun syntax: patterns in the function head

The functional (*Fun*) syntax puts patterns in the function definition itself, with one equation per case, and — unlike Imp — those patterns can be **nested and multi-argument**:

<!-- expect: Result: (12, [(1, 4), (2, 5)]) -->
```bend
type Shape:
  Circle { r }
  Rect { w, h }

area (Shape/Circle r) = (* 3 (* r r))
area (Shape/Rect w h) = (* w h)

zip (List/Cons x xs) (List/Cons y ys) = (List/Cons (x, y) (zip xs ys))
zip * * = List/Nil

main = ((area (Shape/Rect 3 4)), (zip [1, 2, 3] [4, 5]))
```

- A function call is `(f a b)` — Lisp-style parentheses, no commas.
- Operators are prefix: `(* a b)`, `(+ a b)`.
- `*` as a pattern means "anything" (a wildcard).
- Equations are tried top to bottom; the second `zip` equation catches every other combination.

You can mix the two syntaxes in one file as long as each *function* uses only one. A reasonable rule: Imp for most code, Fun when you want to match two arguments at once (like `zip`) or deeply nested constructors.

## Matching strings and characters

Strings are lists of characters, so match the list and compare the character:

<!-- expect: Result: (1, 0) -->
```bend
def starts_with_a(s):
  match s:
    case String/Cons:
      return s.head == 'a'
    case String/Nil:
      return 0

def main():
  return (starts_with_a("apple"), starts_with_a("pear"))
```

For a whole word, `String/equals(a, b)`.

## Common mistakes

- **Using `case 0:` in `match`.** Numbers need `switch`.
- **Reading fields outside their case.** `s.r` is only valid under `case Shape/Circle:`.
- **Missing constructors.** Add them, or use `case _:` deliberately.
- **Different names assigned in different branches** when you are binding instead of returning.
- **Expecting nested patterns in Imp.** Nest `match`es, or write the function in Fun syntax.
- **Writing `(f a, b)` in Fun syntax.** Application has no commas: `(f a b)`.
- **Early `return` before a `match`.** Return only at the end of a branch.

## Exercises

1. Define `type Coin { Penny Nickel Dime Quarter }` and write `cents(c)`.
2. Write `second(xs)` returning the second element of a list, or `0` if it has fewer than two.
3. Write `swap_pairs(xs)` turning `[a, b, c, d]` into `[b, a, d, c]` (nested `match`).
4. Write `is_sorted(xs)` for a list of numbers.
5. Rewrite `zip` in Imp, using nested `match`es.
6. Write `merge(xs, ys)` of two sorted lists in Fun syntax with patterns on both lists.
7. Add a `Triangle` variant to `Shape` and let the compiler tell you which functions break.
8. Write `eq_op(a, b)` that compares two `Op` values with nested `match` (the manual `==`).

## Recap

- `match v:` + `case Type/Ctor:` takes a value apart; fields are `v.field`; the compiler enforces exhaustiveness.
- `case _:` is the catch-all; `switch` is for numbers; tuple patterns go in assignments.
- Imp matches one level at a time; nest `match`es. Fun syntax matches nested, multi-argument patterns in the function head.
- Strings are lists, so match on `String/Cons` and compare characters.

Next: [Recursion schemes: fold & bend →](03-fold-and-bend.md)
