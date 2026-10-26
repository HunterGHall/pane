# Beginner

Start here if you've never written Bend — or never written functional code. By the end you'll be comfortable with immutable values, recursion in place of loops, lists, strings and maps, error values, and `IO`, and you'll have built a command-line app that saves its data to disk.

## Lessons

| # | Lesson | You'll learn |
| --- | --- | --- |
| 1 | [Setup & your first program](01-setup-and-first-program.md) | installing Bend and HVM, `bend run-c`, `main`, the `IO` template, compiler errors |
| 2 | [Values, variables & types](02-variables-and-types.md) | immutable bindings, rebinding, `u24`/`i24`/`f24`, tuples, optional type annotations |
| 3 | [Numbers & math](03-numbers-and-math.md) | 24-bit wrap-around, signs and decimal points, conversions, `Math/`, bit operations |
| 4 | [Conditionals](04-booleans-and-conditionals.md) | no booleans, `if`/`elif`/`else`, `&` `\|` as and/or, `switch`, a taste of `match` |
| 5 | [Recursion instead of loops](05-loops.md) | base cases, accumulators, `switch` counting, the `bend` statement |
| 6 | [Functions](06-functions.md) | `def`, lambdas, closures, partial application, named arguments |
| 7 | [Linearity & duplication](07-linearity-and-duplication.md) | automatic duplication, erasure, `use`, why there is no GC and no data race |
| 8 | [Strings & characters](08-strings.md) | strings as lists, `fold`, writing `concat`/`reverse`/`parse` |
| 9 | [Lists](09-lists.md) | `match` vs `fold`, `map`/`filter`/`reduce`, comprehensions, cost of operations |
| 10 | [Maps & trees](10-hashmaps-and-sets.md) | `Map`, `Tree`, build-a-tree/fold-a-tree, why trees run in parallel |
| 11 | [Maybe, Result & IO](11-option-result-and-files.md) | `Maybe`, `Result`, `with IO`, input, files, arguments, how results print |
| 12 | [Capstone: task tracker](12-capstone-task-tracker.md) | put it all together in a real command-line app |

## How to work through it

- One lesson per sitting. Type every example. Do the exercises.
- Don't move on until the "Recap" makes sense — especially lessons 5, 7 and 9.
- When the compiler rejects your code, read the message slowly: Bend's errors are short and name the definition at fault.
- Unexpected output? Check the lesson's "Common mistakes" first — most Bend surprises (24-bit wrap-around, missing `else`, `n-1` as a name, number kinds that don't mix) are listed there.
- Bend is young. If something differs from the lessons, check `bend --version` against 0.2.38.

## When you're done

You should be able to explain every line of the capstone and add a new feature to it unaided. Then go to [Intermediate](../intermediate/index.md).
