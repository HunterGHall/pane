# 1. How Bend runs: interaction nets & HVM

## What & why

Up to now Bend has been a language you write. This lesson opens the box and shows what actually executes, because every performance and correctness quirk in the Advanced level (duplication errors, lambda encodings, laziness, why trees are fast) falls out of how the runtime works.

The short version: **Bend compiles your program to a graph, and HVM2 runs it by repeatedly rewriting small local pieces of that graph.** Each rewrite is independent of the others, which is why running them on thousands of cores is possible at all.

## The pipeline

```text
your.bend
   │  parse + desugar     (match → switch/lambdas, types → encodings, folds → recursion)
   │  type check          (optional, Hindley–Milner)
   │  optimise            (float combinators, linearise matches, ...)
   ▼
HVM net (text)            ← `bend gen-hvm`
   │  hvm run-rs / run-c / run-cu
   ▼
reduced graph → read back as a term → printed as  Result: ...
```

You can look at every stage:

| Command | Shows |
| --- | --- |
| `bend desugar file.bend` | the program after desugaring, in the lambda-calculus-like core syntax |
| `bend gen-hvm file.bend` | the HVM net text the runtime loads |
| `bend gen-c file.bend` | a standalone C program (the C backend's output) |
| `bend run-c -s file.bend` | run it and print interactions, time and speed |

## Graphs and interactions

HVM2 represents a program as a graph of **nodes** connected by wires. There are only a handful of node kinds:

- **Constructor nodes** `(a b)` with two ports: lambdas, pairs and (via encodings) all your data.
- **Duplicator nodes** `{a b}`: copy a value (and its dual, the superposition — Advanced 2).
- **Eraser** `*`: discards a value.
- **References** `@name`: a pointer to a top-level definition, expanded only when needed.
- **Numbers** and **operators** for the native 24-bit arithmetic.
- **Switches**: branch on a number.

Computation happens where two nodes meet **face to face** — an *active pair*. Each kind of meeting has a fixed rewrite rule:

| When this meets this | It does |
| --- | --- |
| lambda ↔ argument | substitutes (β-reduction) |
| duplicator ↔ constructor | copies the constructor, duplicating its children |
| duplicator ↔ eraser | the erased copy disappears and the other keeps the value |
| operator ↔ numbers | does the arithmetic |
| reference ↔ anything | unfolds the definition |

Each application of a rule is one **interaction**. The number of interactions is the unit of work Bend reports, the `ITRS` figure in `bend run-c -s`.

Two properties make this model special:

1. **Locality.** A rewrite only touches the two nodes involved and their immediate neighbours. There is no global state, no shared heap to lock.
2. **Strong confluence.** Rewrites can be done in any order — or all at once — and you get the same answer. Independent redexes can therefore be reduced by independent threads with no coordination.

Parallelism isn't bolted on; it is a consequence of the evaluation model.

## Reading some real output

Here is the identity function and its net:

```bash
printf 'main = λx x\n' > id.bend && bend gen-hvm id.bend
```

```text
@main = (a a)
```

A constructor node `(a a)` whose two ports are wired to the *same* variable: take an argument, hand it straight back.

A tiny numeric program:

<!-- expect: Result: 42 -->
```bend
def double(x):
  return x * 2

def main():
  return double(21)
```

`bend gen-hvm` prints:

```text
@double = ($([*0x0000002] a) a)

@main = a
  & @double ~ (21 a)
```

- `@double` and `@main` are definitions, referenced by name.
- `$([*0x2] a)` is an operator node: multiply by the constant 2. Its result wire is the second port of the outer pair, so `double` takes an argument and returns that argument times 2.
- `& @double ~ (21 a)` is an **active pair**: the reference `@double` meets the constructor `(21 a)` (argument `21`, result wire `a`). That is the redex that starts the computation, and `a` is `main`'s result.

Running it counts 4 interactions:

```bash
bend run-c -s double.bend
```

```text
Result: 42
- ITRS: 4
- TIME: 0.00s
- MIPS: 0.00
```

Unfold `@double`, apply it to `21`, multiply, return. Four rewrites for a four-step idea. You will see the same notation in the HVM docs.

You can also feed a net straight to the HVM runtime, skipping Bend entirely:

```bash
bend gen-hvm double.bend > double.hvm
hvm run-c double.hvm
```

```text
Result: 42
- ITRS: 4
- TIME: 0.00s
- MIPS: 0.00
```

## What your code becomes

The compiler rewrites your `match`es, types and loops into a few primitive forms. `bend desugar` shows it. For

<!-- expect: Result: 5 -->
```bend
type Color:
  Red
  Green { n }

def f(c):
  match c:
    case Color/Red:
      return 0
    case Color/Green:
      return c.n

def main():
  return f(Color/Green(5))
```

the desugared program is (trimmed):

```text
(Color/Red/tag)   = 0
(Color/Red)       = λa (a Color/Red/tag)
(Color/Green/tag) = 1
(Color/Green)     = λa λb (b Color/Green/tag a)

(f) = λa (a f__C0)
(f__C0) = λa switch a { 0: 0; _: λ* λb b; }
```

There is no `Color` type at runtime. `Green(5)` is a function waiting for a "handler" `b`, to which it hands its tag (`1`) and field (`5`) — a *Scott encoding*. `match` becomes "call the value with the continuation", and `f__C0` is the generated switch on the tag. Lesson 5 explores encodings in depth. For now: **data is functions**, and "matching" is function application.

## Readback

When the program finishes, HVM has a graph, not text. Bend *reads it back* into a term by following the wires. That reconstruction is why:

- numbers, strings, lists and tuples print nicely — the readback knows those shapes;
- your own types print as `λa (a Color/Green/tag 5)` — it only sees lambdas and cannot know you meant `Color`;
- an unreduced function prints as a lambda with its body.

It is also why a result like `{10 14}` (a superposition) can show up in output.

## Lazy definitions, strict evaluation

HVM2 evaluates function arguments eagerly (strict), but **top-level definitions are lazy**: `@name` stays a reference until something interacts with it. This is what stops recursion from unfolding forever, and it is why where you place a recursive call matters (Advanced 8).

## Memory

All memory is the graph. There is no garbage collector: when a node is erased (an unused value, a finished interaction), its memory is immediately available. Duplicating a value does not copy it eagerly; it adds a duplicator node that copies *lazily*, only as far as someone looks. That is why the data you "copy" is cheap and why Bend can run with a few gigabytes of RAM on programs that touch hundreds of millions of nodes.

## The three backends

| Backend | How it runs | Strengths | Limits |
| --- | --- | --- | --- |
| `run-rs` | Rust interpreter | zero setup; good for correctness checks | slower; **no IO** |
| `run-c` | compiled C, one worker thread per core | the practical default; IO | one machine's cores |
| `run-cu` | CUDA on an NVIDIA GPU | thousands of lightweight threads for huge, uniform workloads | needs a GPU; each thread is slower; limited memory; IO unsupported in places |

On a typical CPU, `run-c` scales across all cores. The GPU backend shines on programs with a lot of independent work, such as a tree of tens of millions of leaves, and not at all on a sequential chain.

## Why numbers are 24 bits

HVM2 packs each value into a single machine word together with a few tag bits. In the 32-bit build that Bend 0.2.x uses, that leaves 24 bits for a native number — hence `u24`, `i24` and `f24`. It's an engineering trade-off for speed, not a law of the language; a wider runtime would change it. Until then, bigger numbers are structures you build (lists of digits, trees of limbs).

## Common mistakes

- **Thinking of Bend as an interpreter of an AST.** It's a graph reducer; the AST is gone after compilation.
- **Reading `Result: λa (a Foo/Bar/tag 1)` as an error.** It's a correct but un-prettified value.
- **Assuming parallelism is automatic for any code.** It's automatic for *independent* work; a chain of dependent steps stays a chain.
- **Assuming the GPU is always faster.** It wins only on enormous, uniform parallelism.
- **Assuming lazy evaluation everywhere.** Arguments are strict; only top-level references are lazy.

## Exercises

1. Run `bend gen-hvm` on `main = λx λy x` and describe the net you get.
2. Run `bend desugar` on a function with a `fold` and find the generated recursive function.
3. Count interactions for `fib(10)`, `fib(15)`, `fib(20)` with `-s`. How does the count grow per step?
4. Run the same program with `run-rs` and `run-c -s`. Compare MIPS.
5. Write an HVM net by hand for "add 1 to the argument" (using `bend gen-hvm` output as a model) and run it with `hvm run-c`.
6. Return an unreduced function from `main` and read the printed lambda.
7. Write `main = λf λx (f (f x))` and look at its net. Where is the duplicator?
8. Use `-Oadt-scott` with `bend desugar` on a type with fields and compare the encoding with the default.

## Recap

- Bend compiles to a graph of constructor/duplicator/eraser/operator nodes; HVM2 runs it by local rewrites called interactions.
- Locality and confluence mean independent rewrites can run on any number of threads — parallelism is inherent.
- Your data types become lambda encodings, `match` becomes application, and readback explains the raw `λ...` output.
- Top-level definitions are lazy references; there is no GC; duplication is lazy.
- `run-rs` for setup-free checks, `run-c` for real work, `run-cu` for massive uniform parallelism.

Next: [Duplications & superpositions →](02-dups-and-sups.md)
