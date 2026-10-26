# bitonic.bend: parallel bitonic sort on a tree of pairs.
#
#   bend run-c -s bitonic.bend 10       sorts 2^10 = 1024 numbers
#
# Adapted from the bitonic_sort.bend example shipped with Bend
# (https://github.com/HigherOrderCO/Bend, Apache-2.0).
#
# A "tree of pairs of depth d" holds 2^d numbers: depth 0 is a number, depth d
# is a pair of two trees of depth d-1. Because a bare pair can't be told apart
# from a number at runtime, the depth is passed to every function.

# A reverse-sorted tree of depth d: the numbers 2^d - 1 ... 0.
def gen(d):
  bend d, x = 0:
    when d:
      return (fork(d - 1, x * 2 + 1), fork(d - 1, x * 2))
    else:
      return x

# Swap a pair if `s` says so.
def swap(s, a, b):
  if s:
    return (b, a)
  else:
    return (a, b)

# Compare-and-swap the matching elements of two trees of depth d.
def warp(d, s, a, b):
  switch d:
    case 0:
      return swap(s + (a > b), a, b)
    case _:
      (a.a, a.b) = a
      (b.a, b.b) = b
      (A.a, A.b) = warp(d-1, s, a.a, b.a)
      (B.a, B.b) = warp(d-1, s, a.b, b.b)
      return ((A.a, B.a), (A.b, B.b))

# Merge a bitonic sequence into sorted order (direction chosen by s).
def flow(d, s, t):
  switch d:
    case 0:
      return t
    case _:
      (t.a, t.b) = t
      return down(d, s, warp(d-1, s, t.a, t.b))

def down(d, s, t):
  switch d:
    case 0:
      return t
    case _:
      (t.a, t.b) = t
      return (flow(d-1, s, t.a), flow(d-1, s, t.b))

# The sort: sort the halves in opposite directions, then merge.
def sort(d, s, t):
  switch d:
    case 0:
      return t
    case _:
      (t.a, t.b) = t
      return flow(d, s, (sort(d-1, 0, t.a), sort(d-1, 1, t.b)))

# ---------- checking the result ----------

# Flatten a tree of depth d into a list, left to right.
def to_list(d, t):
  switch d:
    case 0:
      return [t]
    case _:
      (t.a, t.b) = t
      return List/concat(to_list(d-1, t.a), to_list(d-1, t.b))

def is_sorted(xs):
  match xs:
    case List/Nil:
      return 1
    case List/Cons:
      match xs.tail:
        case List/Nil:
          return 1
        case List/Cons:
          return (xs.head <= xs.tail.head) & is_sorted(xs.tail)

# 1 if sorting a reverse-sorted tree of depth d gives an ascending list.
def main(d):
  return is_sorted(to_list(d, sort(d, 0, gen(d))))
