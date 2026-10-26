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
