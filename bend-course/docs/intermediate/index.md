# Intermediate

Start here once the Beginner level feels comfortable: you can write recursive functions, work with lists and strings, and use `IO`. This level is about **modelling**: defining your own data types, consuming and producing them with `fold` and `bend`, handling failure with monads, organising code into modules, and testing it.

## Lessons

| # | Lesson | You'll learn |
| --- | --- | --- |
| 1 | [Algebraic data types](01-algebraic-data-types.md) | `type`, `object`, constructors, recursive types with `~`, generics preview |
| 2 | [Pattern matching](02-pattern-matching.md) | `match`, exhaustiveness, `case _`, nested matches, Fun-syntax patterns |
| 3 | [Recursion schemes: fold & bend](03-fold-and-bend.md) | `fold` with state, `bend` with `fork`, build-then-reduce |
| 4 | [Higher-order functions](04-higher-order-functions.md) | `map`/`filter`/`reduce`/`zip`, partial application, `DiffList`, the duplication rule |
| 5 | [Generics & the type checker](05-generics-and-type-checking.md) | annotations, type variables, `_`, `unchecked`, reading `Can't unify` |
| 6 | [Divide and conquer](06-divide-and-conquer.md) | independent subproblems, sorting, N-Queens, tree-shaped data, `-s` |
| 7 | [Data structures](07-data-structures.md) | stack, queue, BST, sorted list, sets, association lists |
| 8 | [Error handling & monads](08-error-handling.md) | `Result`/`Maybe`, `with`, `bind`/`wrap`/`undefer`, error types |
| 9 | [Modules & imports](09-modules-and-imports.md) | project layout, `from`/`import`/`as`/`*`, naming conventions |
| 10 | [IO in depth](10-io-in-depth.md) | IO as descriptions, recursion in IO, file handles, time, stderr, limits |
| 11 | [Testing](11-testing.md) | a 30-line test framework, property tests, smoke tests |
| 12 | [Capstone: expression calculator](12-capstone-expression-calculator.md) | tokenizer, recursive-descent parser, evaluator, REPL, tests |

## How to work through it

- Model first: sketch the `type` before writing any function.
- Let the compiler find missing cases: add a variant and fix every `Non-exhaustive 'match'`.
- Annotate numeric functions; run `bend check` often.
- When a higher-order function returns something odd (a `*` in a list), look for a lambda using its argument twice.
- Do the capstone's extension exercises — they're the real test.

## When you're done

You should be able to design a small program from its types, explain how its data flow could run in parallel, and test it. Then go to [Advanced](../advanced/index.md).
