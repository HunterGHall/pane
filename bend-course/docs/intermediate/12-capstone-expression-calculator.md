# 12. Capstone: expression calculator

## What you're building

A calculator that reads arithmetic from the keyboard, parses it properly (precedence, parentheses, unary minus) and evaluates it, reporting errors instead of crashing:

```text
$ bend run-c main.bend
2 + 3 * (4 - 1)
= 11
-7 % 3
= -1
10 / (5 - 5)
error: division by zero
(1 + 2
error: missing )
quit
```

It brings together the whole Intermediate level: algebraic data types, pattern matching, recursion, the `Result`-style monad with `with`, modules and imports, IO, and tests.

## Design

The pipeline has three pure stages and a thin IO shell:

1. **Tokenize** the string into a `List(Token)`. `Token` is an ADT: numbers, the operators, and parentheses. Unknown characters are errors.
2. **Parse** the tokens into an `Expr` tree by *recursive descent*: one function per precedence level (`expr` → `term` → `unary` → `primary`), each consuming tokens and returning what's left.
3. **Evaluate** the `Expr` to a signed 24-bit number, failing on division by zero.
4. **REPL** (in `main.bend`) reads lines, calls `evaluate`, prints `show_result`.

Everything fallible returns an `Outcome` (our own `Result`, see below) and chains with `with Outcome:`, so each stage reads as a straight line.

The code is split across three files, exactly as the Modules and Testing lessons suggested:

| File | Role |
| --- | --- |
| `calc.bend` | tokenizer, parser, evaluator, result formatting (all pure) |
| `main.bend` | the interactive loop |
| `tests.bend` | a test suite for `calc.bend` |

## The core: `calc.bend`

<!-- sync: capstones/expression-calculator/calc.bend -->
```bend
# calc.bend: tokenizer, parser and evaluator for arithmetic expressions.
#
#   evaluate("2 + 3 * (4 - 1)")  =>  Outcome/Ok(+11)
#
# Grammar (lowest to highest precedence):
#   expr    := term   (("+" | "-") term)*
#   term    := unary  (("*" | "/" | "%") unary)*
#   unary   := "-" unary | primary
#   primary := NUMBER | "(" expr ")"
#
# All arithmetic is on signed 24-bit integers (i24).

# ---------- the Outcome monad ----------
# Like the built-in Result, but defined here: `with` blocks look up
# `Type/bind`, and a module's own definitions are only found under their own
# type name when the type is defined in the same file.

type Outcome:
  Ok { val }
  Err { val }

def Outcome/bind(res, nxt):
  match res:
    case Outcome/Ok:
      nxt = undefer(nxt)
      return nxt(res.val)
    case Outcome/Err:
      return res

def Outcome/wrap(x):
  return Outcome/Ok(x)

# ---------- types ----------

type Token:
  Num { v }
  Plus
  Minus
  Star
  Slash
  Percent
  LParen
  RParen

# op codes: 1 = +, 2 = -, 3 = *, 4 = /, 5 = %
type Expr:
  Lit { v }
  Neg { ~e }
  Bin { op, ~l, ~r }

# ---------- tokenizer ----------

def is_digit(c):
  return (c >= '0') & (c <= '9')

# Read digits from the front of `s`; returns (number, rest of s).
def read_number(s, acc):
  match s:
    case String/Nil:
      return (acc, s)
    case String/Cons:
      if is_digit(s.head):
        return read_number(s.tail, acc * 10 + (s.head - '0'))
      else:
        return (acc, s)

# Put `tok` in front of a tokenizer result.
def push(tok, r):
  match r:
    case Outcome/Ok:
      return Outcome/Ok(List/Cons(tok, r.val))
    case Outcome/Err:
      return r

def tokenize(s):
  match s:
    case String/Nil:
      return Outcome/Ok(List/Nil)
    case String/Cons:
      c = s.head
      if c == ' ':
        return tokenize(s.tail)
      elif is_digit(c):
        (n, rest) = read_number(s, 0)
        return push(Token/Num(n), tokenize(rest))
      elif c == '+':
        return push(Token/Plus, tokenize(s.tail))
      elif c == '-':
        return push(Token/Minus, tokenize(s.tail))
      elif c == '*':
        return push(Token/Star, tokenize(s.tail))
      elif c == '/':
        return push(Token/Slash, tokenize(s.tail))
      elif c == '%':
        return push(Token/Percent, tokenize(s.tail))
      elif c == '(':
        return push(Token/LParen, tokenize(s.tail))
      elif c == ')':
        return push(Token/RParen, tokenize(s.tail))
      else:
        return Outcome/Err("unexpected character")

# ---------- parser ----------
# Each parse function takes the remaining tokens and returns
# Outcome((Expr, remaining tokens), String).

def add_op(t):
  match t:
    case Token/Plus:
      return 1
    case Token/Minus:
      return 2
    case _:
      return 0

def mul_op(t):
  match t:
    case Token/Star:
      return 3
    case Token/Slash:
      return 4
    case Token/Percent:
      return 5
    case _:
      return 0

def parse_expr(ts):
  with Outcome:
    first <- parse_term(ts)
    (left, rest) = first
    all <- expr_rest(left, rest)
    return wrap(all)

def expr_rest(left, ts):
  match ts:
    case List/Nil:
      return Outcome/Ok((left, ts))
    case List/Cons:
      op = add_op(ts.head)
      if op == 0:
        return Outcome/Ok((left, ts))
      else:
        with Outcome:
          next <- parse_term(ts.tail)
          (right, rest) = next
          all <- expr_rest(Expr/Bin(op, left, right), rest)
          return wrap(all)

def parse_term(ts):
  with Outcome:
    first <- parse_unary(ts)
    (left, rest) = first
    all <- term_rest(left, rest)
    return wrap(all)

def term_rest(left, ts):
  match ts:
    case List/Nil:
      return Outcome/Ok((left, ts))
    case List/Cons:
      op = mul_op(ts.head)
      if op == 0:
        return Outcome/Ok((left, ts))
      else:
        with Outcome:
          next <- parse_unary(ts.tail)
          (right, rest) = next
          all <- term_rest(Expr/Bin(op, left, right), rest)
          return wrap(all)

def parse_unary(ts):
  match ts:
    case List/Nil:
      return Outcome/Err("unexpected end of input")
    case List/Cons:
      match ts.head:
        case Token/Minus:
          with Outcome:
            inner <- parse_unary(ts.tail)
            (e, rest) = inner
            return wrap((Expr/Neg(e), rest))
        case _:
          return parse_primary(ts)

def parse_primary(ts):
  match ts:
    case List/Nil:
      return Outcome/Err("unexpected end of input")
    case List/Cons:
      match ts.head:
        case Token/Num:
          return Outcome/Ok((Expr/Lit(u24/to_i24(ts.head.v)), ts.tail))
        case Token/LParen:
          with Outcome:
            inner <- parse_expr(ts.tail)
            (e, rest) = inner
            closed <- expect_rparen(rest)
            return wrap((e, closed))
        case _:
          return Outcome/Err("unexpected token")

def expect_rparen(ts):
  match ts:
    case List/Nil:
      return Outcome/Err("missing )")
    case List/Cons:
      match ts.head:
        case Token/RParen:
          return Outcome/Ok(ts.tail)
        case _:
          return Outcome/Err("missing )")

# Parse a whole string; every token must be used.
def parse(s):
  with Outcome:
    tokens <- tokenize(s)
    parsed <- parse_expr(tokens)
    (e, rest) = parsed
    match rest:
      case List/Nil:
        return wrap(e)
      case List/Cons:
        return Outcome/Err("unexpected token")

# ---------- evaluator ----------

def apply(op, a, b):
  if op == 1:
    return Outcome/Ok(a + b)
  elif op == 2:
    return Outcome/Ok(a - b)
  elif op == 3:
    return Outcome/Ok(a * b)
  elif b == +0:
    return Outcome/Err("division by zero")
  elif op == 4:
    return Outcome/Ok(a / b)
  else:
    return Outcome/Ok(a % b)

def eval(e):
  match e:
    case Expr/Lit:
      return Outcome/Ok(e.v)
    case Expr/Neg:
      with Outcome:
        v <- eval(e.e)
        return wrap(+0 - v)
    case Expr/Bin:
      with Outcome:
        a <- eval(e.l)
        b <- eval(e.r)
        r <- apply(e.op, a, b)
        return wrap(r)

def evaluate(s):
  with Outcome:
    e <- parse(s)
    v <- eval(e)
    return wrap(v)

# ---------- showing results ----------

def concat(a, b):
  fold a with b:
    case String/Cons:
      return String/Cons(a.head, a.tail(b))
    case String/Nil:
      return b

def show_i24(n):
  if n < +0:
    return concat("-", u24/to_string(i24/to_u24(+0 - n)))
  else:
    return u24/to_string(i24/to_u24(n))

# "= 11" or "error: division by zero"
def show_result(r):
  match r:
    case Outcome/Ok:
      return concat("= ", show_i24(r.val))
    case Outcome/Err:
      return concat("error: ", r.val)
```
<!-- /sync -->

### Walkthrough

**`Outcome`.** The prelude's `Result` has no `bind`/`wrap`, and (see Error handling and Modules) a `with Result:` block can't find them from an imported file. So `calc.bend` defines its own two-constructor `Outcome` type, `Outcome/bind` and `Outcome/wrap`, and uses `with Outcome:`. `main.bend` only ever calls `show_result` on it.

**Tokens and expressions.** `Token` has `Num { v }` and one constructor per symbol. `Expr` is recursive — `Lit`, `Neg { ~e }`, `Bin { op, ~l, ~r }` — and operator kinds are small integer codes (1 `+`, 2 `-`, 3 `*`, 4 `/`, 5 `%`).

**Tokenizer.** `tokenize` walks the string with `match`, skipping spaces, using `read_number` to gather digits (a `(number, rest)` pair, like a tiny parser), and consing each token onto the result of tokenizing the rest with `push`. An unknown character yields `Outcome/Err`.

**Parser.** `parse_expr` parses one `term`, then `expr_rest` keeps absorbing `+ term` / `- term` pairs, building `Bin` nodes **left-associatively** (`10 - 4 - 3` is `(10 - 4) - 3`). `parse_term`/`term_rest` do the same at the `*`/`/`/`%` level, which is why `*` binds tighter than `+`. `parse_unary` handles a leading `-`, and `parse_primary` handles numbers and parenthesised sub-expressions, checking for the closing `)`. Each function returns `(Expr, remaining tokens)` inside an `Outcome`. The `with Outcome:` blocks destructure with `(left, rest) = first` after binding.

**Evaluator.** `eval` matches on the expression: a literal is itself, `Neg` negates (`+0 - v`), and `Bin` evaluates both sides then calls `apply`. `apply` turns the op code into arithmetic and returns `Err("division by zero")` when the divisor is `+0` for `/` and `%`. Numbers are `i24`, so negatives work; literals are converted with `u24/to_i24`.

**Showing results.** `show_i24` formats a signed number (negating below zero before converting) and `show_result` produces `= 11` or `error: ...`.

## The shell: `main.bend`

<!-- sync: capstones/expression-calculator/main.bend -->
```bend
# main.bend: a read-evaluate-print loop for the calculator.
#
#   bend run-c main.bend
#
# Type an expression per line; `quit` exits.

from calc import (evaluate, show_result, concat)

def repl():
  with IO:
    line <- IO/input()
    match line:
      case Result/Err:
        return wrap(1)
      case Result/Ok:
        if String/equals(line.val, "quit"):
          return wrap(0)
        else:
          * <- IO/print(concat(show_result(evaluate(line.val)), "\n"))
          status <- repl
          return wrap(status)

def main() -> IO(u24):
  return repl
```
<!-- /sync -->

`repl` is a recursive IO action: read a line, stop on `quit`, otherwise print the formatted result and recurse. It imports exactly the functions it needs from `calc`. As always, there's no end-of-input handling, so a scripted session must end in `quit`.

## The tests: `tests.bend`

<!-- sync: capstones/expression-calculator/tests.bend -->
```bend
# tests.bend: pure tests for the calculator.
#
#   bend run-c tests.bend
#
# Each test compares the text the REPL would print with what we expect.

from calc import (evaluate, show_result, concat)

def say(text):
  return IO/print(concat(text, "\n"))

def check(input, want):
  got = show_result(evaluate(input))
  return (input, String/equals(got, want))

def passed(results):
  fold results:
    case List/Cons:
      (*, ok) = results.head
      return ok + results.tail
    case List/Nil:
      return 0

def print_failures(results):
  with IO:
    match results:
      case List/Nil:
        return wrap(0)
      case List/Cons:
        (input, ok) = results.head
        if ok:
          r <- print_failures(results.tail)
          return wrap(r)
        else:
          * <- say(concat("FAIL: ", input))
          r <- print_failures(results.tail)
          return wrap(r)

def tests():
  return [
    check("1", "= 1"),
    check("1 + 2", "= 3"),
    check("2 + 3 * 4", "= 14"),
    check("(2 + 3) * 4", "= 20"),
    check("10 - 4 - 3", "= 3"),
    check("100 / 5 / 2", "= 10"),
    check("17 % 5", "= 2"),
    check("-3 + 5", "= 2"),
    check("--4", "= 4"),
    check("2 * -3", "= -6"),
    check("  7  ", "= 7"),
    check("1 / 0", "error: division by zero"),
    check("1 +", "error: unexpected end of input"),
    check("(1 + 2", "error: missing )"),
    check("1 2", "error: unexpected token"),
    check("2 $ 3", "error: unexpected character")
  ]

def main() -> IO(u24):
  with IO:
    results = tests
    * <- print_failures(results)
    (total, results) = List/length(results)
    p = passed(results)
    * <- say(concat(u24/to_string(p), concat(" passed, ", concat(u24/to_string(total - p), " failed"))))
    return wrap(0)
```
<!-- /sync -->

Each test is `(input, passed)` where `passed` compares the REPL's output text with the expectation. The suite covers precedence, associativity, unary minus, whitespace and every error. Run it with `bend run-c tests.bend`; CI expects `16 passed, 0 failed`.

## Running it

From `capstones/expression-calculator`:

```bash
bend run-c main.bend                  # interactive
bend run-c tests.bend                 # the test suite
printf '1 + 2\nquit\n' | bend run-c main.bend
```

The project lives in [`capstones/expression-calculator`](https://github.com/HunterGHall/bend-course/tree/main/capstones/expression-calculator), and CI runs the tests plus a scripted REPL session.

## Extending it

1. **Variables:** add `Ident` tokens and `let x = 3` / `x * 2` using a `Map` from a character to a value (single-letter names) kept in the REPL loop's state.
2. **Exponentiation `^`** with right associativity and higher precedence than `*`.
3. **Floats:** switch to `f24` and a decimal point in the tokenizer.
4. **Better errors:** carry a position in each `Token` and report *where* the error is.
5. **Functions:** `abs(x)`, `max(a, b)` (needs a comma token and argument-list parsing).
6. **Constant folding:** write `simplify(expr)` with `fold` that evaluates literal-only subtrees and removes `+ 0` and `* 1`.
7. **Pretty printer:** `show_expr` that prints the parsed tree back with minimal parentheses.
8. **Overflow detection:** detect results that don't fit 24 bits and report an error instead of wrapping.

## When you're done

You can model a problem with ADTs, write recursive-descent parsers, chain failures with a monad, split a project into modules, and test it. Next is [Advanced](../advanced/index.md): how Bend actually runs your program, and how to make it fast.
