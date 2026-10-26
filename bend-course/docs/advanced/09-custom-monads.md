# 9. Custom monads

## What & why

In Intermediate 8 you used `with Result:` and `with Maybe:`; `with IO:` has been everywhere. All of them are one idea: a `with Type:` block turns a sequence of `x <- action` lines into calls of two functions you (or the prelude) define, `Type/bind` and `Type/wrap`. Define your own pair and you get your own sequencing syntax: **state** threaded through a computation, a **parser** that consumes input, a **logger** that accumulates output. This lesson builds two of them, a state monad and a parser monad, and — because these monads hold *functions* — teaches the one rule that keeps them correct.

## The contract

For a type `M`, `with M:` needs:

- **`M/wrap(x)`**: put a plain value into the monad ("return"). Inside the block it's available as `wrap(x)`.
- **`M/bind(m, nxt)`**: run `m`, take its result, and pass it to the continuation `nxt`, which returns the next `M` value.

and `bind` must start by calling `undefer(nxt)` — the continuation arrives *deferred* so that recursive monadic functions don't unfold forever (Advanced 8):

```text
def M/bind(m, nxt):
  ...
  nxt = undefer(nxt)
  next_m = nxt(result)
  ...
```

Every `x <- e` line becomes `M/bind(e, lambda x: <rest of the block>)`; every bare `e` line followed by more lines uses a discarded result (`* <- e`).

## A state monad

Threading state through a program normally means passing it as an argument to every function and returning the new state from each one. A **state monad** hides that plumbing. A computation is a function from the current state to `(result, new state)`:

<!-- expect: Result: ((4, 50), 50) -->
```bend
object State { run }

def State/wrap(x):
  return State { run: lambda s: (x, s) }

def State/bind(m, nxt):
  return State { run: lambda s: State/step(m, nxt, s) }

def State/step(m, nxt, s):
  open State: m
  (a, s2) = m.run(s)
  nxt = undefer(nxt)
  k = nxt(a)
  open State: k
  return k.run(s2)

def get():
  return State { run: lambda s: (s, s) }

def put(v):
  return State { run: lambda s: (0, v) }

def run(m, s):
  open State: m
  return m.run(s)

def counter():
  with State:
    a <- get
    * <- put(a + 1)
    b <- get
    * <- put(b * 10)
    c <- get
    return wrap((a, c))

def main():
  return run(counter, 4)
```

- `get` returns the current state without changing it; `put(v)` replaces it.
- `counter` reads the state (4), stores 5, reads it back (5), stores 50, reads 50 — and returns `(4, 50)` as its result, with 50 as the final state: `((4, 50), 50)`.
- `State/bind` builds a new `State` whose `run` threads `s` through `m`, then through the rest of the block.

The block reads like imperative code with a mutable variable, yet nothing is mutated: the state is passed along by `bind`.

## A parser monad

A parser consumes some of a string and either produces a value plus the remaining input or fails. Represent it as a function `String -> Maybe((value, rest))`:

<!-- expect: Result: ([1, 2, 3], (7, 5)) -->
```bend
object Parser { run }

def Parser/wrap(x):
  return Parser { run: lambda s: Maybe/Some((x, s)) }

def Parser/bind(p, nxt):
  return Parser { run: lambda s: Parser/step(p, nxt, s) }

def Parser/step(p, nxt, s):
  open Parser: p
  match r = p.run(s):
    case Maybe/Some:
      (a, rest) = r.value
      nxt = undefer(nxt)
      k = nxt(a)
      open Parser: k
      return k.run(rest)
    case Maybe/None:
      return Maybe/None

def run_parser(p, s):
  open Parser: p
  return p.run(s)

# ---------- primitive parsers ----------

def fail():
  return Parser { run: lambda s: Maybe/None }

def item():
  return Parser { run: lambda s: item_go(s) }

def item_go(s):
  match s:
    case String/Cons:
      return Maybe/Some((s.head, s.tail))
    case String/Nil:
      return Maybe/None

# ---------- combinators ----------

def digit_of(c):
  if (c >= '0') & (c <= '9'):
    return Parser/wrap(c - '0')
  else:
    return fail

def digit():
  with Parser:
    c <- item
    return digit_of(c)

def two_digits():
  with Parser:
    a <- digit
    b <- digit
    return wrap(a * 10 + b)

# try p; if it fails, try q on the same input
def alt(p, q):
  return Parser { run: lambda s: alt_go(p, q, s) }

def alt_go(p, q, s):
  match r = run_parser(p, s):
    case Maybe/Some:
      return Maybe/Some(r.value)
    case Maybe/None:
      return run_parser(q, s)

def digit_or_seven():
  return alt(digit, Parser/wrap(7))

# apply `digit` as many times as it succeeds
def digits_go(s):
  match r = run_parser(digit, s):
    case Maybe/Some:
      (v, rest) = r.value
      (vs, rest2) = digits_go(rest)
      return (List/Cons(v, vs), rest2)
    case Maybe/None:
      return ([], s)

# result of a parser, or 9999 if it fails
def parse(p, s):
  match r = run_parser(p, s):
    case Maybe/Some:
      (v, rest) = r.value
      return v
    case Maybe/None:
      return 9999

def main():
  (ds, rest) = digits_go("123abc")
  return (ds, (parse(digit_or_seven, "x"), parse(digit_or_seven, "5")))
```

`two_digits` reads like a grammar rule: a digit, then a digit, then combine. If any step fails, the whole parse fails, and `bind` doesn't even call the rest. `alt` adds choice: `digit_or_seven` succeeds with a digit if there is one, otherwise with `7` without consuming input.

## The rule for monads that hold functions

State and Parser values are *closures* (a `lambda s: ...` inside an object). Closures that were built from duplicating code can't safely be duplicated themselves (Advanced 2). Two consequences you can see in the code above:

1. **Refer to monadic values by definition name, not through a variable used twice.** `digit_or_seven` is a zero-argument `def`; each *mention* of the name makes a fresh copy of the parser. Contrast:

<!-- expect: Result: (7, 7) -->
```bend
object Parser { run }

def Parser/wrap(x):
  return Parser { run: lambda s: Maybe/Some((x, s)) }

def Parser/bind(p, nxt):
  return Parser { run: lambda s: Parser/step(p, nxt, s) }

def Parser/step(p, nxt, s):
  open Parser: p
  match r = p.run(s):
    case Maybe/Some:
      (a, rest) = r.value
      nxt = undefer(nxt)
      k = nxt(a)
      open Parser: k
      return k.run(rest)
    case Maybe/None:
      return Maybe/None

def run_parser(p, s):
  open Parser: p
  return p.run(s)

def fail():
  return Parser { run: lambda s: Maybe/None }

def item():
  return Parser { run: lambda s: item_go(s) }

def item_go(s):
  match s:
    case String/Cons:
      return Maybe/Some((s.head, s.tail))
    case String/Nil:
      return Maybe/None

def digit_of(c):
  if (c >= '0') & (c <= '9'):
    return Parser/wrap(c - '0')
  else:
    return fail

def digit():
  with Parser:
    c <- item
    return digit_of(c)

def alt(p, q):
  return Parser { run: lambda s: alt_go(p, q, s) }

def alt_go(p, q, s):
  match r = run_parser(p, s):
    case Maybe/Some:
      return Maybe/Some(r.value)
    case Maybe/None:
      return run_parser(q, s)

def parse(p, s):
  match r = run_parser(p, s):
    case Maybe/Some:
      (v, rest) = r.value
      return v
    case Maybe/None:
      return 9999

def main():
  p = alt(digit, Parser/wrap(7))
  return (parse(p, "x"), parse(p, "5"))      # p is used twice (duplicated)
```

   The second answer should be `5`; because the *variable* `p` was duplicated, we get `(7, 7)`. Using the named `digit_or_seven` for each call gives the right `(7, 5)`.

2. **Write recursion over input in an ordinary function** (`digits_go` above), calling the parser by *name*, rather than passing a parser to a generic recursive `many(p)` that duplicates `p`. When I wrote the generic `many` for parsers built with `bind`, the result was `<Invalid>`. A closure-free design — parsers as plain top-level functions of the input string — avoids the whole issue, at the cost of some boilerplate. Use the monad for sequencing and choice; use plain functions for loops.

The same care applies to the state monad: build a computation with a named `def` and run it, don't stash it in a variable and run it twice.

## Other useful monads

The recipe is always the same: choose a representation, define `wrap` and `bind`, add primitives.

| Monad | Representation | Primitives |
| --- | --- | --- |
| Reader | `lambda env: value` | `ask` |
| Writer / Logger | `(value, log)` | `tell(msg)` |
| State | `lambda s: (value, s)` | `get`, `put` |
| Parser | `lambda input: Maybe((value, rest))` | `item`, `fail`, `alt` |
| Result / Maybe | the type itself | `Err`, `None` |
| IO | provided by the prelude | `IO/print`, `IO/input`, ... |

A **Writer** has no function inside, so it doesn't suffer from the duplication caveat; it's the easiest one to get right:

<!-- expect: Result: (6, "ab") -->
```bend
object Writer { value, log }

def concat(a, b):
  fold a with b:
    case String/Cons:
      return String/Cons(a.head, a.tail(b))
    case String/Nil:
      return b

def Writer/wrap(x):
  return Writer { value: x, log: "" }

def Writer/bind(m, nxt):
  open Writer: m
  nxt = undefer(nxt)
  k = nxt(m.value)
  open Writer: k
  return Writer { value: k.value, log: concat(m.log, k.log) }

def tell(msg):
  return Writer { value: 0, log: msg }

def compute():
  with Writer:
    * <- tell("a")
    x = 2 * 3
    * <- tell("b")
    return wrap(x)

def main():
  r = compute
  open Writer: r
  return (r.value, r.log)
```

## Laws (and why you should care)

A well-behaved monad satisfies three equations: `wrap(x)` followed by `f` is just `f(x)`; `m` followed by `wrap` is `m`; and chaining is associative. They guarantee that refactoring a block (extracting two lines into a helper) doesn't change its meaning. You don't need to prove them; test a few instances.

## Common mistakes

- **Forgetting `undefer(nxt)`** in `bind`.
- **Not defining `M/wrap`** and then writing `return wrap(x)`.
- **Binding a monadic value to a variable and using it twice.** Name it with a zero-argument `def` instead.
- **Passing monadic values into generic recursive combinators** (`many`, `repeat`) that duplicate them.
- **Mixing monads in one block.** Every `<-` in a `with M:` block must produce an `M`.
- **Returning a bare value** where `wrap(value)` is needed.

## Exercises

1. Add `modify(f)` to the State monad and use it to write `tick` (increment the state).
2. Write a state computation that labels the nodes of a tree with consecutive numbers (threading a counter).
3. Add a `char(c)` parser that succeeds only if the next character is `c`, and a parser for `"ab"`.
4. Write `number` as a recursive function that reads a maximal run of digits and returns the value.
5. Write a Reader monad (`ask`, `bind`, `wrap`) and use it to read a configuration number.
6. Extend the Writer with `tell` of a number (convert with `u24/to_string`).
7. Rewrite the expression calculator's tokenizer using the parser monad.
8. Check the monad laws on `State` for one concrete example each.

## Recap

- `with M:` needs `M/bind` (starting with `undefer`) and `M/wrap`; each `x <- e` becomes a call to `bind`.
- State, parser and writer monads are a page of code each, and make threading state, input and logs invisible.
- Monads that hold closures (State, Parser) must not be duplicated: refer to them by definition name, and put loops in ordinary functions.
- A Writer holds data only, so it has no such caveat.

Next: [FFI & dynamic libraries →](10-ffi.md)
