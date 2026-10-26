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
