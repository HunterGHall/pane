# 12. Capstone: command-line task tracker

## What you're building

A small to-do list you drive by typing commands, that remembers your tasks between runs:

```text
$ bend run-c main.bend '"tasks.txt"'
add Buy milk
added
add Learn Bend
added
done 2
done
list
1. [ ] Buy milk
2. [x] Learn Bend
remove 1
removed
quit
```

It uses everything from the Beginner level: functions and recursion, strings, lists and tuples, `match`/`fold`, `Maybe`-style checking of input, `IO` and files, and a command-line argument.

## Design

1. **Data.** A task is a tuple `(done, text)` where `done` is `0` or `1`. The program keeps a `List` of tasks. Lists are immutable, so each command computes a *new* list from the old one.
2. **Commands.** A line like `done 2` is split into the first word and the rest (`split_word`); the word selects what happens.
3. **State.** Because there are no mutable variables, the state (the task list) is an argument to the loop: `repl(path, tasks)` reads a command, computes the new list, and calls itself with it. That is the beginner-friendly version of "a game loop".
4. **Persistence.** After every change the list is written to the file given on the command line, one task per line as `0|text` or `1|text`. On startup `load` reads that file; a missing file is simply an empty list.
5. **Validation.** `done` and `remove` check that their argument is a number in range before using it, instead of crashing.

## The program

The code below is the complete source, kept in sync with `capstones/task-tracker/main.bend` and exercised by CI.

<!-- sync: capstones/task-tracker/main.bend -->
```bend
# Task tracker: a tiny command-line to-do list.
#
# Run it with the path of the file to keep your tasks in:
#   bend run-c main.bend '"tasks.txt"'
#
# Then type one command per line:
#   add <text>    done <n>    remove <n>    list    quit
#
# A task is a tuple (done, text): done is 0 or 1.

# ---------- strings ----------

def concat(a, b):
  fold a with b:
    case String/Cons:
      return String/Cons(a.head, a.tail(b))
    case String/Nil:
      return b

def is_number(s):
  match s:
    case String/Nil:
      return 0
    case String/Cons:
      return all_digits(s)

def all_digits(s):
  fold s:
    case String/Cons:
      return ((s.head >= '0') & (s.head <= '9')) & s.tail
    case String/Nil:
      return 1

def parse_number(s):
  acc = 0
  fold s with acc:
    case String/Cons:
      return s.tail(acc * 10 + (s.head - '0'))
    case String/Nil:
      return acc

# Split "word rest of line" into ("word", "rest of line").
def split_word(s):
  match s:
    case String/Nil:
      return ("", "")
    case String/Cons:
      if s.head == ' ':
        return ("", s.tail)
      else:
        (word, rest) = split_word(s.tail)
        return (String/Cons(s.head, word), rest)

# Split a string at every `delim` character: split("a,b", ',') is ["a", "b"].
# (The built-in String/split of Bend 0.2.38 returns each piece reversed,
# so we write our own.)
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

# ---------- tasks ----------

def count(tasks):
  fold tasks:
    case List/Cons:
      return 1 + tasks.tail
    case List/Nil:
      return 0

def append(tasks, task):
  return List/concat(tasks, [task])

def mark_done(tasks, n):
  match tasks:
    case List/Nil:
      return List/Nil
    case List/Cons:
      if n == 1:
        (*, text) = tasks.head
        return List/Cons((1, text), tasks.tail)
      else:
        return List/Cons(tasks.head, mark_done(tasks.tail, n - 1))

def remove(tasks, n):
  match tasks:
    case List/Nil:
      return List/Nil
    case List/Cons:
      if n == 1:
        return tasks.tail
      else:
        return List/Cons(tasks.head, remove(tasks.tail, n - 1))

# "1. [x] text\n" for every task.
def render(tasks, i):
  match tasks:
    case List/Nil:
      return ""
    case List/Cons:
      (done, text) = tasks.head
      if done:
        box = "[x] "
      else:
        box = "[ ] "
      line = concat(u24/to_string(i), concat(". ", concat(box, concat(text, "\n"))))
      return concat(line, render(tasks.tail, i + 1))

# ---------- saving and loading ----------
# One task per line: "0|text" or "1|text".

def serialize(tasks):
  match tasks:
    case List/Nil:
      return ""
    case List/Cons:
      (done, text) = tasks.head
      if done:
        flag = "1|"
      else:
        flag = "0|"
      return concat(flag, concat(text, concat("\n", serialize(tasks.tail))))

def parse_line(line):
  match line:
    case String/Nil:
      return List/Nil
    case String/Cons:
      match line.tail:
        case String/Nil:
          return List/Nil
        case String/Cons:
          return [(line.head == '1', line.tail.tail)]

def parse_lines(lines):
  match lines:
    case List/Nil:
      return List/Nil
    case List/Cons:
      return List/concat(parse_line(lines.head), parse_lines(lines.tail))

def load(path):
  with IO:
    data <- IO/FS/read_file(path)
    match data:
      case Result/Ok:
        text = String/decode_utf8(data.val)
        return wrap(parse_lines(split(text, '\n')))
      case Result/Err:
        return wrap(List/Nil)

def save(path, tasks):
  with IO:
    out <- IO/FS/write_file(path, String/encode_utf8(serialize(tasks)))
    return wrap(0)

# ---------- commands ----------

def say(text):
  return IO/print(concat(text, "\n"))

def check_index(tasks, arg):
  if is_number(arg):
    n = parse_number(arg)
    return (n >= 1) & (n <= count(tasks))
  else:
    return 0

def handle(path, tasks, cmd, arg):
  with IO:
    if String/equals(cmd, "add"):
      tasks = append(tasks, (0, arg))
      * <- say("added")
      * <- save(path, tasks)
      return wrap(tasks)
    elif String/equals(cmd, "list"):
      * <- IO/print(render(tasks, 1))
      return wrap(tasks)
    elif String/equals(cmd, "done"):
      if check_index(tasks, arg):
        tasks = mark_done(tasks, parse_number(arg))
        * <- say("done")
        * <- save(path, tasks)
        return wrap(tasks)
      else:
        * <- say("no such task")
        return wrap(tasks)
    elif String/equals(cmd, "remove"):
      if check_index(tasks, arg):
        tasks = remove(tasks, parse_number(arg))
        * <- say("removed")
        * <- save(path, tasks)
        return wrap(tasks)
      else:
        * <- say("no such task")
        return wrap(tasks)
    else:
      * <- say("commands: add <text>, done <n>, remove <n>, list, quit")
      return wrap(tasks)

def repl(path, tasks):
  with IO:
    input <- IO/input()
    match input:
      case Result/Err:
        return wrap(1)
      case Result/Ok:
        (cmd, arg) = split_word(input.val)
        if String/equals(cmd, "quit"):
          return wrap(0)
        else:
          tasks <- handle(path, tasks, cmd, arg)
          status <- repl(path, tasks)
          return wrap(status)

def main(path):
  with IO:
    tasks <- load(path)
    status <- repl(path, tasks)
    return wrap(status)
```
<!-- /sync -->

## Walkthrough

**Strings first.** `concat`, `all_digits`, `parse_number` and `split_word` are small `fold`/`match` helpers straight out of lesson 8. `split` is our own because `String/split` in Bend 0.2.38 returns reversed pieces. Notice how `is_number` checks that the string is non-empty *and* all digits before `parse_number` trusts it.

**Tasks are plain list functions.** `mark_done` and `remove` walk the list with a `match`, counting down `n` until they reach the right element. They never mutate: they rebuild the list, sharing the tail that didn't change. `render` produces the whole listing as one string by recursion.

**Saving and loading.** `serialize` and `parse_lines` are inverses. `String/encode_utf8` and `decode_utf8` convert between text and the bytes the file functions work with. In `load`, an `Err` from `read_file` becomes an empty task list instead of an error — a missing file on first run is normal.

**Commands.** `handle` is one big `with IO:` block with an `if`/`elif` chain on the command word. Each branch computes the new task list, optionally prints, saves, and `return wrap(tasks)`. The result flows back into `repl`, which calls itself with it.

**The loop and the exit.** `repl` reads a line with `IO/input()`; `quit` ends the recursion (there is no end-of-input handling: in Bend 0.2.38 `IO/input()` hangs at end-of-file, so always finish a scripted session with `quit`), otherwise it recurses with the updated list. Recursion in `IO` costs no stack, so a session can be arbitrarily long.

**Entry point.** `main(path)` receives the file name from the command line (`'"tasks.txt"'` — the quotes make it a Bend string), loads the tasks and starts the loop.

## Running and testing it

From `capstones/task-tracker`:

```bash
bend run-c main.bend '"tasks.txt"'
```

To test without typing, pipe a script into it:

```bash
printf 'add Buy milk\nadd Learn Bend\ndone 2\nlist\nquit\n' | bend run-c main.bend '"/tmp/tasks.txt"'
```

CI runs exactly this kind of scripted session and checks the output. The full project lives in [`capstones/task-tracker`](https://github.com/HunterGHall/bend-course/tree/main/capstones/task-tracker).

## Extending it

You should now be able to add features unaided:

1. **`undo`**: keep the previous task list around as an extra argument to `repl` and swap back.
2. **`edit <n> <text>`**: replace a task's text.
3. **`clear`**: remove all finished tasks (`filter` on the done flag).
4. **Priorities**: make tasks `(priority, done, text)` and sort `list` by priority (write an insertion sort).
5. **`count`**: print "3 tasks, 1 done" using a fold that counts both.
6. **Escape `|` and newlines** in task text so any text round-trips safely through the file.
7. **Search**: `find <word>` lists tasks whose text contains the word (write `contains(haystack, needle)`).
8. **A second storage format**: save as one line per task `done<TAB>text` and load either format.

## When you're done

You should be able to explain every line of the program, and see that nothing in it is mutable — state is always passed along. Then go to [Intermediate](../intermediate/index.md), where you'll model data with your own types instead of tuples and strings.
