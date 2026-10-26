# The Bend Course

A complete, self-paced Bend curriculum in Markdown, from your first `return 42` to algebraic data types, `fold` and `bend`, monads, interaction nets, duplications and superpositions, FFI and parallel performance tuning. Work through it top to bottom, or jump to the level that matches your experience.

**What is Bend?** A high-level language that looks like Python and behaves like Haskell, compiled to the HVM2 runtime. Programs are pure functions over immutable data; whatever doesn't depend on something else runs in parallel, automatically, on all your cores (or your GPU). You never write a thread.

## How this course is organized

| Folder | For you if... | Outcome |
| --- | --- | --- |
| [Beginner](beginner/index.md) | You have never written Bend (or never written functional code) | Write and run real programs, think in recursion and immutable data, build a command-line app that saves data |
| [Intermediate](intermediate/index.md) | You know the syntax but data types, `fold`/`bend`, monads and the type checker still feel shaky | Model data with your own types, write generic code, error handling, modules, IO, tests, a real project |
| [Advanced](advanced/index.md) | You want to know *why* it's fast and how to make it faster | How HVM2 works, duplications and superpositions, writing parallel-friendly code, performance tuning, lambda encodings, fusion, FFI, a parallel capstone |

Each lesson is one file and follows the same shape:

1. **What & why** – the idea in plain language
2. **Examples** – code you should type out yourself
3. **Common mistakes** – the traps everyone hits
4. **Exercises** – do these; reading is not learning
5. **Recap**

Each level ends with a **capstone** project. The complete, buildable source for all three lives in the [`capstones/`](https://github.com/HunterGHall/bend-course/tree/main/capstones) folder of the repository, and CI runs them. CI also **compiles and runs every Bend code block in the lessons**, and checks the output the lesson claims, so the examples are known to work on the version this course targets.

## Setup (do this first)

This course targets **Bend 0.2.38** on **Linux or macOS** (Windows users: WSL). You need the Rust toolchain, a C compiler, and then:

```bash
cargo install hvm
cargo install bend-lang
bend --version
```

Lesson 1 walks through it in detail. The commands you'll use constantly:

```bash
bend check file.bend     # parse and type-check only
bend run-c file.bend     # compile to C, run on all cores (supports IO)
bend run-rs file.bend    # Rust interpreter: no extra tooling, but no IO
bend run-c -s file.bend  # also print the interaction count and speed
```

A good editor helps: install the Bend language server with `cargo install bend-language-server` and use any editor with LSP support.

## How to study

- **Type every example.** Copy-paste teaches you nothing.
- **Predict, then run.** Guess the output; if you're wrong, work out why.
- **Break things on purpose.** Change a line, predict the result, run it.
- **Do the exercises before looking anything up.**
- **Think in shapes, not steps.** Ask "what does this data look like?" before "what order do things happen in?" — in Bend the shape of your data decides how parallel your program is.
- **One lesson per sitting** is plenty. Consistency beats marathons.

## A note on Bend's maturity

Bend is a young research language. It is wonderfully expressive and genuinely parallel, but it has rough edges: 24-bit numbers, a small standard library, raw-lambda printing of user types, a handful of prelude bugs (this course points them out where it hits them), and no way yet to run IO on the Rust backend. Every limitation the lessons mention was verified against 0.2.38. Where the language changes, the lesson examples are re-run by CI so the course can be updated quickly.

## Curriculum at a glance

### Beginner
1. [Setup & your first program](beginner/01-setup-and-first-program.md)
2. [Values, variables & types](beginner/02-variables-and-types.md)
3. [Numbers & math](beginner/03-numbers-and-math.md)
4. [Conditionals](beginner/04-booleans-and-conditionals.md)
5. [Recursion instead of loops](beginner/05-loops.md)
6. [Functions](beginner/06-functions.md)
7. [Linearity & duplication](beginner/07-linearity-and-duplication.md)
8. [Strings & characters](beginner/08-strings.md)
9. [Lists](beginner/09-lists.md)
10. [Maps & trees](beginner/10-hashmaps-and-sets.md)
11. [Maybe, Result & IO](beginner/11-option-result-and-files.md)
12. [Capstone: task tracker](beginner/12-capstone-task-tracker.md)

### Intermediate
1. [Algebraic data types](intermediate/01-algebraic-data-types.md)
2. [Pattern matching](intermediate/02-pattern-matching.md)
3. [Recursion schemes: `fold` and `bend`](intermediate/03-fold-and-bend.md)
4. [Higher-order functions & a list library](intermediate/04-higher-order-functions.md)
5. [Generics & the type checker](intermediate/05-generics-and-type-checking.md)
6. [Divide and conquer](intermediate/06-divide-and-conquer.md)
7. [Data structures](intermediate/07-data-structures.md)
8. [Error handling & monads](intermediate/08-error-handling.md)
9. [Modules & imports](intermediate/09-modules-and-imports.md)
10. [IO in depth](intermediate/10-io-in-depth.md)
11. [Testing](intermediate/11-testing.md)
12. [Capstone: expression calculator](intermediate/12-capstone-expression-calculator.md)

### Advanced
1. [How Bend runs: interaction nets & HVM](advanced/01-how-bend-runs.md)
2. [Duplications & superpositions](advanced/02-dups-and-sups.md)
3. [Parallelism in practice](advanced/03-parallelism-in-practice.md)
4. [Performance & profiling](advanced/04-performance.md)
5. [Lambda encodings](advanced/05-lambda-encodings.md)
6. [Scopeless lambdas](advanced/06-scopeless-lambdas.md)
7. [Fusion](advanced/07-fusion.md)
8. [Laziness & recursion](advanced/08-laziness-and-recursion.md)
9. [Custom monads](advanced/09-custom-monads.md)
10. [FFI & dynamic libraries](advanced/10-ffi.md)
11. [The compiler & HVM](advanced/11-compiler-and-hvm.md)
12. [Capstone: parallel lab](advanced/12-capstone-parallel-lab.md)

## License

Use freely for learning and teaching.
