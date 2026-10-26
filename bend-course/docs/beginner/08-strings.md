# 8. Strings & characters

## What & why

A `String` in Bend is just a **list of characters**, and a character is just a `u24` Unicode code point. That makes strings simple and fully Unicode-aware from the start, and it means everything you learn about lists in the next lesson applies to strings too. It also means the standard library for strings is small; you'll write several helpers yourself in this lesson, which is a good way to learn `fold`.

## Literals

<!-- expect: Result: ("hello", (104, "héllo ✓")) -->
```bend
def main():
  return ("hello", 'h', "héllo ✓")
```

- `"..."` is a string; `'...'` is a character, which is the number of its code point.
- Escapes work: `"\n"`, `"\t"`, `"\""`, `"\\"` and `'\u{1F30E}'`.
- Strings aren't limited to ASCII: `"🌎"` is one character.

## Strings are `Cons` lists

A string is built from two constructors, `String/Cons(head, tail)` and `String/Nil`:

<!-- expect: Result: "hi" -->
```bend
def main():
  return String/Cons('h', String/Cons('i', String/Nil))
```

The literal `"hi"` is exactly that. Everything you do to a string is either building one with `Cons`/`Nil`, or taking one apart with `match` or `fold`.

## `fold`: walking a string

`fold` is a recursive `match`. In the `Cons` case, `s.head` is the character and `s.tail` is the result of folding the rest, already computed:

<!-- expect: Result: 5 -->
```bend
def length(s):
  fold s:
    case String/Cons:
      return 1 + s.tail
    case String/Nil:
      return 0

def main():
  return length("hello")
```

(In a plain `match`, `s.tail` would be the unprocessed remainder; in `fold` it's the recursive answer. More in lesson 9.)

## Building strings

Concatenation isn't built in (there is no `String/concat`), but it takes four lines. Use `fold ... with` to carry the second string along:

<!-- expect: Result: "foobar" -->
```bend
def concat(a, b):
  fold a with b:
    case String/Cons:
      return String/Cons(a.head, a.tail(b))
    case String/Nil:
      return b

def main():
  return concat("foo", "bar")
```

The `with b` clause passes `b` as extra state; recursive calls are written `a.tail(b)`. Put this in a file of helpers and reuse it — Intermediate 9 shows how to `import`.

## Transforming strings

Rebuild the string with a changed character:

<!-- expect: Result: "SHOUT" -->
```bend
def to_upper(s):
  fold s:
    case String/Cons:
      if (s.head >= 'a') & (s.head <= 'z'):
        return String/Cons(s.head - 32, s.tail)
      else:
        return String/Cons(s.head, s.tail)
    case String/Nil:
      return String/Nil

def main():
  return to_upper("shout")
```

Uppercase letters sit exactly 32 below lowercase in ASCII, so subtracting 32 converts.

Reversal uses an accumulator:

<!-- expect: Result: "dcba" -->
```bend
def reverse(s):
  acc = String/Nil
  fold s with acc:
    case String/Cons:
      return s.tail(String/Cons(s.head, acc))
    case String/Nil:
      return acc

def main():
  return reverse("abcd")
```

## Standard-library helpers

Bend does ship a few string functions:

<!-- expect: Result: (1, 0) -->
```bend
def main():
  return (String/equals("hi", "hi"), String/equals("hi", "ho"))
```

- `String/equals(a, b)` — `1` if equal, else `0` (don't use `==` on strings).
- `String/split(s, delimiter_char)` — a list of strings. **Careful:** in Bend 0.2.38 each piece comes back *reversed* (`String/split("ab,cd", ',')` gives `["ba", "dc"]`; single-character pieces hide the bug). This is a bug in the prelude, not intended behaviour, so write your own until it is fixed:

<!-- expect: Result: ["ab", "cd", "e"] -->
```bend
def split(s, delim):
  match s:
    case String/Nil:
      return [""]
    case String/Cons:
      rest = split(s.tail, delim)
      match rest:
        case List/Nil:
          return rest
        case List/Cons:
          if s.head == delim:
            return List/Cons("", rest)
          else:
            return List/Cons(String/Cons(s.head, rest.head), rest.tail)

def main():
  return split("ab,cd,e", ',')
```

(It splits from the right: each recursive call returns the list of pieces for the rest of the string, and the current character either starts a new piece or joins the front one. This is the `match`-then-recurse style from lesson 9.)

- `u24/to_string(n)` — decimal digits of a number.
- `String/encode_utf8(s)` / `String/decode_utf8(bytes)` — convert to and from a list of bytes (needed for files, lesson 11).

## Numbers ↔ strings

Number to text:

<!-- expect: Result: "12345" -->
```bend
def main():
  return u24/to_string(12345)
```

Text to number is not built in; write it with a state-carrying `fold`. Each digit shifts the accumulator by one decimal place:

<!-- expect: Result: 4096 -->
```bend
def parse(s):
  acc = 0
  fold s with acc:
    case String/Cons:
      return s.tail(acc * 10 + (s.head - '0'))
    case String/Nil:
      return acc

def main():
  return parse("4096")
```

This trusts the input to be all digits. A robust version would return a `Maybe`/`Result` for bad input (lesson 11).

## Comparing and searching

A character test is just number comparison:

<!-- expect: Result: (1, 0) -->
```bend
def is_digit(c):
  return (c >= '0') & (c <= '9')

def main():
  return (is_digit('7'), is_digit('x'))
```

Count the vowels in a word by folding:

<!-- expect: Result: 3 -->
```bend
def is_vowel(c):
  return (c == 'a') | (c == 'e') | (c == 'i') | (c == 'o') | (c == 'u')

def count_vowels(s):
  fold s:
    case String/Cons:
      return is_vowel(s.head) + s.tail
    case String/Nil:
      return 0

def main():
  return count_vowels("education") - 2
```

(`education` has 5 vowels, so `5 - 2 = 3`.)

## Printing strings

`IO/print` takes a `String`, so build the message with `concat` and print:

<!-- expect: Name: Ada, age 36 -->
```bend
def concat(a, b):
  fold a with b:
    case String/Cons:
      return String/Cons(a.head, a.tail(b))
    case String/Nil:
      return b

def main() -> IO(u24):
  with IO:
    msg = concat("Name: Ada, age ", u24/to_string(36))
    * <- IO/print(concat(msg, "\n"))
    return wrap(0)
```

## Common mistakes

- **Using `==` on strings.** It only compares numbers; use `String/equals`.
- **Looking for `length`, `concat`, `substring`, `trim`.** They don't exist in the prelude; write them (they're all small folds).
- **Quoting characters with `"`.** `'a'` is a character (a number), `"a"` is a one-element string — different types.
- **Indexing like `s[0]`.** Square brackets on a name are *map* access (lesson 10); strings are walked with `match`/`fold`.
- **Assuming strings are cheap to index.** They are linked lists: O(n) to reach the nth character. For heavy text work, convert to a `List` of bytes or use a structure like `Tree`.
- **Forgetting `with` state in a fold.** Without it, the extra argument isn't carried along.

## Exercises

1. Write `starts_with(s, prefix)` using `match` on both strings.
2. Write `repeat(s, n)` that concatenates `s` with itself `n` times.
3. Write `is_palindrome(s)` using `reverse` and `String/equals`.
4. Write `to_lower` mirroring `to_upper`.
5. Write `join(parts, sep)` taking a `List(String)` and a separator, e.g. `join(["a","b","c"], ", ")`.
6. Write `count_char(s, c)` returning how many times `c` occurs.
7. Write `parse_signed(s)` handling an optional leading `-`, returning an `i24`.
8. Split `"10,20,30"` with your `split`, parse each piece and add them up.

## Recap

- A `String` is a list of `u24` code points built from `String/Cons` and `String/Nil`; characters are numbers.
- `fold` walks a string; `fold ... with state` carries extra arguments for concat, reverse and parsing.
- The prelude has `String/equals`, `u24/to_string` and UTF-8 encode/decode (its `String/split` is buggy in 0.2.38 — write your own); the rest you write.
- Don't compare strings with `==`.

Next: [Lists →](09-lists.md)
