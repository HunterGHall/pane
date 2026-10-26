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
