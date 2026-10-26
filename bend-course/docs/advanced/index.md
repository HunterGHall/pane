# Advanced

Start here when you can build and test a program in Bend and want to know **why** it behaves as it does — why a function returns `<Invalid>`, why a recursion hangs, why one tree folds in parallel and a list doesn't. This level opens the box: the interaction-net runtime, duplications and superpositions, lambda encodings, laziness, performance, and the tool chain, ending with a parallel benchmark lab.

## Lessons

| # | Lesson | You'll learn |
| --- | --- | --- |
| 1 | [How Bend runs: interaction nets & HVM](01-how-bend-runs.md) | graphs, interactions, `desugar`/`gen-hvm`, readback, the three backends |
| 2 | [Duplications & superpositions](02-dups-and-sups.md) | dups, sups, labels, and the "don't duplicate a duplicating lambda" rule |
| 3 | [Parallelism in practice](03-parallelism-in-practice.md) | what runs in parallel, granularity, balance, measuring scaling with `taskset` |
| 4 | [Performance & profiling](04-performance.md) | interactions as a cost model, quadratic traps, `Nat` vs native numbers, `-O` flags |
| 5 | [Lambda encodings](05-lambda-encodings.md) | Church and Scott encodings, how `type` and `match` compile |
| 6 | [Scopeless lambdas](06-scopeless-lambdas.md) | `$x` wires, call/cc, O(1) queues |
| 7 | [Fusion](07-fusion.md) | why `not` grows and `fusing_not` doesn't; linear lambdas up, duplicating lambdas down |
| 8 | [Laziness & recursion](08-laziness-and-recursion.md) | lazy definitions, guarded recursion, infinite structures, closed handlers |
| 9 | [Custom monads](09-custom-monads.md) | `bind`/`wrap`/`undefer`, state, parser and writer monads, the closure caveat |
| 10 | [FFI & dynamic libraries](10-ffi.md) | calling C from Bend with `IO/DyLib`, building and loading a library |
| 11 | [The compiler & HVM](11-compiler-and-hvm.md) | stages, `-O` passes, warnings, hand-written nets, debugging recipes |
| 12 | [Capstone: parallel lab](12-capstone-parallel-lab.md) | N-Queens and bitonic sort with a benchmark harness and honest measurements |

## How to work through it

- Read in order: lessons 1, 2 and 8 explain most of the "weird" behaviour you'll meet; the rest build on them.
- Run every command in the lessons. Many of the best insights are in `bend desugar`, `bend gen-hvm` and `-s` output.
- Measure before you believe: use `ITRS` for work and `taskset` for scaling.
- Keep a timeout (`timeout 10 bend run-c ...`) around experiments with recursion.
- Expect the unexpected — Bend is a research language. The lessons call out every sharp edge verified against 0.2.38.

## When you're done

You should be able to explain, for any program, which parts can run in parallel and why, diagnose a duplication or laziness problem from `desugar` output, and make a Bend program faster by changing its algorithm and data shape.
