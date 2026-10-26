# 9. Modules & imports

## What & why

A real program doesn't live in one file. Bend's **import system** lets you split code into files and directories and pull names from one into another. There are no packages or registry yet (nothing like `cargo`), so a Bend "project" is just a folder of `.bend` files, and the structure of that folder *is* the module structure.

## A project layout

```text
my_project/
├── main.bend
└── lib/
    ├── math.bend
    └── shapes.bend
```

Run it from the folder containing `main.bend`:

```bash
bend run-c main.bend
```

Every import path is **relative to the folder of the main file** (the one you pass to `bend`), unless it starts with `./` or `../`. Paths are case-sensitive.

## Two files to import

`lib/math.bend` — plain functions:

<!-- file: lib/math.bend -->
```bend
def square(x):
  return x * x

def cube(x):
  return x * square(x)
```

`lib/shapes.bend` — a type and a function over it:

<!-- file: lib/shapes.bend -->
```bend
type Shape:
  Circle { r }
  Square { s }

def area(s):
  match s:
    case Shape/Circle:
      return 3 * s.r * s.r
    case Shape/Square:
      return s.s * s.s
```

## Importing names

`main.bend` can import in several ways:

<!-- expect: Result: (16, (27, 25)) -->
```bend
from lib/math import (square, cube)
from lib/shapes import Shape
import lib/shapes

def main():
  return (square(4), (cube(3), shapes/area(Shape/Square(5))))
```

What each line does:

| Line | Binds |
| --- | --- |
| `from lib/math import (square, cube)` | `square` and `cube` |
| `from lib/shapes import Shape` | the type `Shape` **and** its constructors `Shape/Circle`, `Shape/Square` |
| `import lib/shapes` | every name in `shapes.bend`, prefixed by the file name: `shapes/area` |

Parentheses are optional for a single name. Always put imports at the top of the file.

## The import forms

```text
from path import name               # one name
from path import (a, b, c)          # several names
from path import *                  # every name in that file, unprefixed
from path import name as other      # rename
import path/name                    # same as 'from path import name'
import path                         # whole file, names prefixed by the file name
import path as alias                # whole file, prefixed by the alias
from folder import *                # every .bend file in a folder, each prefixed by its file name
```

For example:

<!-- expect: Result: (9, 8) -->
```bend
import lib/math as m
from lib import *

def main():
  return (m/square(3), math/cube(2))
```

Here `m/square` comes from the aliased import, and `from lib import *` brings in both files with their file-name prefixes (`math/cube`, `shapes/area`).

Importing a **type** brings its constructors with it; importing a **function** brings just that function (plus anything it needs internally — you don't import dependencies by hand).

## Relative imports

Paths that start with `./` or `../` are resolved relative to the *importing file*, not the main file. Inside `lib/shapes.bend` you could write `from ./math import square`.

## A caveat: `with` blocks across modules

Monad blocks look up `Type/bind` and `Type/wrap` by name. For the prelude's own types (`Result`, `Maybe`) this breaks when the `with` block lives in an *imported* file: Bend 0.2.38 reports `Could not find definition Result/bind`. Define the monad's type in the same file as the code that uses it and the lookup works. The expression-calculator capstone does this with its own `Outcome` type.

## Naming conventions that work well

Because there are no namespaces beyond file names, Bend code follows a convention:

- **`Type/function`** for functions that belong to a type: `Stack/push`, `Bst/insert`, `Result/bind`. They're ordinary names containing a `/`, so they import like any other.
- **One concern per file,** and the file named after it (`list.bend`, `string.bend`).
- A file that defines a type `List` and a folder `List/` of one function per file is a pattern the importer understands: `from types/List import (List, concat)`.

<!-- check: skip -->
```bend
# a conventional "standard library" you write once and import everywhere
from std/list import (map, filter, reduce)
from std/string import (concat, split, parse_number)
```

## No cycles, no re-exports

- Two files can't import each other in a cycle.
- There's no `export` list: every top-level definition in a file can be imported.
- A name defined in your file and one you import must not clash; rename with `as`.

## Splitting the Beginner capstone

The task tracker would split naturally into `strings.bend` (`concat`, `split`, `parse_number`), `tasks.bend` (the list operations), and `main.bend` (the commands and the loop). This is a good exercise.

## Common mistakes

- **Running from the wrong folder.** Import paths are relative to the main file, so run `bend run-c path/to/main.bend`, and keep the layout consistent.
- **Wrong case** in file or directory names: `Math` is not `math`.
- **Forgetting the prefix** after `import lib/shapes` — you must write `shapes/area`, not `area`.
- **Importing a type's constructors by name** only; import the *type* (`from lib/shapes import Shape`) to bring them in.
- **Name clashes** between two imported files; alias one of them.
- **Cyclic imports.**
- **Expecting a package manager.** There isn't one; vendor files into your project or copy them.

## Exercises

1. Move `concat`, `split` and `parse_number` from the task tracker into `strings.bend` and import them.
2. Create `std/list.bend` with `map`, `filter`, `reduce`, `zip`, and use them from `main.bend` with an alias.
3. Make two files that each define `helper`, and import both with aliases.
4. Put a `type` in one file and the functions over it in another; import both.
5. Use `from ./name import ...` inside a nested directory.
6. Import everything from a folder with `from folder import *` and call one function from each file.
7. Create a `tests/` folder with a `main.bend` that imports your library files, using `../` paths.
8. Predict which names exist after `import lib/shapes as s` and check with `bend check`.

## Recap

- A project is a folder of `.bend` files; imports resolve relative to the main file (or to the importing file with `./` and `../`).
- `from path import name`, `import path`, `from path import *`, and `as` for renaming.
- Importing a type brings its constructors; `import path` prefixes names with the file name.
- There are no packages, exports, or cycles — keep one concern per file and use `Type/function` names.

Next: [IO in depth →](10-io-in-depth.md)
