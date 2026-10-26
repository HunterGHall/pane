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
