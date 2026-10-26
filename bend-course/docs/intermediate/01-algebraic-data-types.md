# 1. Algebraic data types

## What & why

So far your data has been numbers, strings, tuples and lists. Real programs need to say *what kind of thing* a value is: a shape is a circle **or** a rectangle; an expression is a number **or** a sum **or** a product. An **algebraic data type** (ADT) names that choice. Defining your own types is the most important skill in the Intermediate level; almost every Bend program is "define the shape of the data, then write functions that take it apart".

## `type`: one of several variants

A `type` lists its **constructors** (variants), each with its own fields:

<!-- expect: Result: (12, 78) -->
```bend
type Shape:
  Circle { r }
  Rect { w, h }

def area(s):
  match s:
    case Shape/Circle:
      return 3 * s.r * s.r
    case Shape/Rect:
      return s.w * s.h

def main():
  return (area(Shape/Rect(3, 4)), area(Shape/Circle(5)) + 3)
```

- `type Shape:` introduces the type; each indented line is a constructor with a field list in braces.
- The constructors become functions named `Type/Constructor`: `Shape/Circle` and `Shape/Rect`.
- To use a value you `match` it; inside a `case`, the fields are `s.r`, `s.w`, `s.h`.

(`3 * r * r` is a toy circle area — Bend has floats, but integers keep the examples short.)

## Constructing values

Three equivalent spellings; use whichever reads best:

<!-- expect: Result: (12, (12, 12)) -->
```bend
type Shape:
  Circle { r }
  Rect { w, h }

def area(s):
  match s:
    case Shape/Circle:
      return 3 * s.r * s.r
    case Shape/Rect:
      return s.w * s.h

def main():
  a = Shape/Rect(3, 4)                  # positional
  b = Shape/Rect { w: 3, h: 4 }         # braces, all field names
  c = Shape/Rect(h = 4, w = 3)          # named arguments
  return (area(a), (area(b), area(c)))
```

## Variants without fields: enums

A constructor with no fields is just a tag. An all-tags type is an enum:

<!-- expect: Result: (5, 1) -->
```bend
type Op:
  Plus
  Minus

def apply(op, a, b):
  match op:
    case Op/Plus:
      return a + b
    case Op/Minus:
      return a - b

def main():
  return (apply(Op/Plus, 3, 2), apply(Op/Minus, 3, 2))
```

There is no built-in boolean (lesson 4), but nothing stops you defining a readable one when you want a type-checked yes/no:

<!-- check: check -->
```bend
type Answer:
  Yes
  No
```

## `object`: exactly one variant

When a type has a single constructor — a record, a struct — use `object`. The constructor has the same name as the type:

<!-- expect: Result: ("Ann", 31) -->
```bend
object Person { name, age }

def birthday(p):
  open Person: p
  return Person { name: p.name, age: p.age + 1 }

def main():
  q = birthday(Person { name: "Ann", age: 30 })
  open Person: q
  return (q.name, q.age)
```

`open Person: p` brings the fields into scope as `p.name`, `p.age` — the equivalent of a `match` with only one case. After `open`, the original name still works, but using fields through it duplicates them.

## Recursive types

A type can contain itself. Mark each self-referencing field with `~` (the *recursive* marker):

<!-- expect: Result: 7 -->
```bend
type Expr:
  Num { v }
  Add { ~l, ~r }
  Mul { ~l, ~r }

def eval(e):
  fold e:
    case Expr/Num:
      return e.v
    case Expr/Add:
      return e.l + e.r
    case Expr/Mul:
      return e.l * e.r

def main():
  # 1 + 2 * 3
  e = Expr/Add(Expr/Num(1), Expr/Mul(Expr/Num(2), Expr/Num(3)))
  return eval(e)
```

The `~` does two jobs: it tells `fold` which fields to recurse into (next lesson), and it lets the compiler treat the type as a proper inductive structure. Always put `~` on fields that hold the same type.

Linked lists are the simplest recursive type, and you could define your own:

<!-- expect: Result: 6 -->
```bend
type Stack:
  Push { top, ~rest }
  Empty

def sum(s):
  fold s:
    case Stack/Push:
      return s.top + s.rest
    case Stack/Empty:
      return 0

def main():
  return sum(Stack/Push(1, Stack/Push(2, Stack/Push(3, Stack/Empty))))
```

## Parameterised types

A type can be generic over what it holds. Declare the type variables in parentheses:

<!-- check: check -->
```bend
type Pair(A, B):
  Both { first: A, second: B }

type Option(T):
  Has { value: T }
  Lacks
```

Intermediate 5 covers generics and the type checker properly.

## Names you can't use

Bend's prelude already defines `List`, `String`, `Tree`, `Map`, `Maybe`, `Result`, `IO`, `Nat` and friends. Redefining a built-in is an error:

<!-- check: fail -->
```bend
type Maybe:
  Some { value }
  None
```

Pick another name (`Option`, `Opt`, `MyTree`, `BTree`). Also avoid a one-letter type name such as `T` — the prelude uses `T` as a type variable and the clash produces a baffling error inside `builtins.bend`.

## Printing user types

Return a user type directly from `main` and you get its raw lambda encoding (lesson 11). To see a value, turn it into numbers or a string:

<!-- expect: Result: "rectangle 3x4" -->
```bend
type Shape:
  Circle { r }
  Rect { w, h }

def concat(a, b):
  fold a with b:
    case String/Cons:
      return String/Cons(a.head, a.tail(b))
    case String/Nil:
      return b

def describe(s):
  match s:
    case Shape/Circle:
      return concat("circle r=", u24/to_string(s.r))
    case Shape/Rect:
      return concat("rectangle ", concat(u24/to_string(s.w), concat("x", u24/to_string(s.h))))

def main():
  return describe(Shape/Rect(3, 4))
```

A `describe`/`show` function per type is the Bend equivalent of `Debug`/`toString`.

## Constructors are functions

Because a constructor is a function, you can pass it around and partially apply it:

<!-- expect: Result: 25 -->
```bend
type Shape:
  Circle { r }
  Rect { w, h }

def area(s):
  match s:
    case Shape/Circle:
      return 3 * s.r * s.r
    case Shape/Rect:
      return s.w * s.h

def main():
  square = Shape/Rect(5)    # still waiting for h
  return area(square(5))
```

## Modelling with types

A few patterns you'll reuse:

| Need | Model |
| --- | --- |
| "one of several things" | a `type` with a constructor per case |
| "a record" | an `object` |
| "might be absent" | the built-in `Maybe` |
| "might fail with a reason" | the built-in `Result` |
| "tree-shaped data" | a recursive `type` with `~` fields |
| "a state machine" | an enum of states plus a function `state -> input -> state` |

Make illegal states unrepresentable: if a shape *must* have a radius, no `Circle` should exist without one — the constructor takes it, so it can't.

## Common mistakes

- **Forgetting the `~`** on a recursive field. Without it `fold` won't recurse into that field.
- **Reading a field without matching first.** `s.r` only exists inside `case Shape/Circle:` (or after `open`).
- **Constructors by bare name.** It's `Shape/Circle(...)`, never `Circle(...)`.
- **Redefining a built-in type** (`Maybe`, `Tree`, `List`, ...), or naming a type `T`.
- **Missing a case** in a `match`: the compiler reports `Non-exhaustive 'match' expression ... Case 'Shape/Rect' not covered`.
- **Expecting equality `==` on user types.** `==` is numeric only; write an `equals` function with `match`.

## Exercises

1. Define `type Weekday` as an enum and write `is_weekend(d)`.
2. Add a `Triangle { base, height }` variant to `Shape`; the compiler should flag every `match` that now misses it.
3. Define `object Point { x, y }` and write `add(p, q)` and `distance_squared(p, q)`.
4. Define `type Token` with `Number { v }`, `Plus`, `Minus`, `LParen`, `RParen` — you'll use it in the capstone.
5. Define a recursive `type Path` with `Step { dir, ~next }` and `End`, and write `length(path)`.
6. Define `type Json` with `Null`, `Num { v }`, `Str { s }`, `Arr { items }` and a function counting the values in an array.
7. Model a traffic light as an enum and write `next(light)`.
8. Write `show_expr(e)` that renders the `Expr` of this lesson back to text with parentheses.

## Recap

- `type` lists constructors, each with fields; `object` is the single-constructor case.
- Construct with `Type/Ctor(...)`, `Type/Ctor { field: ... }` or named arguments; constructors are functions.
- Fields are available only after `match` (or `open`); mark self-referencing fields `~`.
- User types print as raw encodings; write your own `show`.
- Don't reuse built-in type names or `T`.

Next: [Pattern matching →](02-pattern-matching.md)
