# queens.bend: count the solutions of the N-Queens puzzle.
#
#   bend run-c -s queens.bend 8         92 solutions
#
# Each row places one queen. `qs` holds the columns chosen so far (most recent
# first); `safe` checks the new queen against them. Different columns for the
# same row are independent searches, so the work spreads across all cores.

# Is a queen in column q (placed d rows below the rest) safe from every queen in qs?
def safe(q, qs, d):
  match qs:
    case List/Nil:
      return 1
    case List/Cons:
      ok = (q != qs.head) & (q != qs.head + d) & (q + d != qs.head)
      return ok & safe(q, qs.tail, d + 1)

# Try every column from `col` upward in row `row`; return the solution count.
def place(n, row, qs, col):
  if col == n:
    return 0
  else:
    if safe(col, qs, 1):
      here = count(n, row + 1, List/Cons(col, qs))
    else:
      here = 0
    return here + place(n, row, qs, col + 1)

def count(n, row, qs):
  if row == n:
    return 1
  else:
    return place(n, row, qs, 0)

def main(n):
  return count(n, 0, [])
