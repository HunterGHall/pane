# 10. FFI & dynamic libraries

## What & why

Bend's prelude can print, read and write files, and sleep. It cannot open a socket, list a directory, run a program, call a GPU kernel or use any of the vast C ecosystem. The escape hatch is the **dynamic-library FFI**: you write a function in C (or CUDA), compile it into a shared library (`.so`/`.dylib`), and call it from Bend with `IO/DyLib/open` and `IO/DyLib/call`. This lesson builds one, end to end.

Everything here is IO, so it runs with `bend run-c` (the Rust backend has no IO), and the library must match the backend: C libraries for `run-c`, CUDA libraries for `run-cu`.

## The Bend side

Three functions in the prelude:

| Function | Does |
| --- | --- |
| `IO/DyLib/open(path, lazy)` | load a library; `lazy` is `0` to resolve all symbols now, `1` to resolve on first use; returns an id |
| `IO/DyLib/call(lib, name, arg)` | call the function `name` in the library with one argument |
| `IO/DyLib/close(lib)` | unload it |

All three return `Result`s inside `IO`. A call takes **one** argument (pass a tuple or list for several) and returns **one** value, whose shape depends on the C function.

## The C side

A function callable from Bend has exactly this signature:

```c
Port function_name(Net* net, Book* book, Port arg);
```

- `Net`, `Book` and `Port` come from HVM's header, **`hvm.h`** (it's in the HVM source: `~/.cargo/registry/src/*/hvm-2.0.22/src/hvm.h` if you installed with `cargo`).
- `arg` points at the argument in the runtime's graph; you convert it to a C value with helpers.
- You return a `Port` for the result, built with another helper.

Helpers used in this lesson:

| Helper | Direction | Meaning |
| --- | --- | --- |
| `get_u24(get_val(arg))` | Bend → C | a `u24` argument as a C integer |
| `new_port(NUM, new_u24(n))` | C → Bend | return a `u24` |
| `readback_str(net, book, arg)` | Bend → C | a Bend `String` as a C buffer (`Str`: `.buf`, `.len`) |
| `inject_bytes(net, &bytes)` | C → Bend | return a `List(u24)` of bytes (`Bytes`: `.buf`, `.len`) |
| `new_port(ERA, 0)` | C → Bend | return "nothing" (`*`) |

A tiny library with two functions: one takes a number, one takes a string:

<!-- file: libdemo.c -->
```c
#include "hvm.h"
#include <stdlib.h>

// u24 -> u24 : n * n + 1
Port square_plus_one(Net* net, Book* book, Port arg) {
  u32 n = get_u24(get_val(arg));
  return new_port(NUM, new_u24(n * n + 1));
}

// String -> bytes : upper-cases ASCII letters
Port shout(Net* net, Book* book, Port arg) {
  Str s = readback_str(net, book, arg);
  Bytes out = { .buf = malloc(s.len + 1), .len = s.len };
  for (u32 i = 0; i < s.len; i++) {
    char c = s.buf[i];
    out.buf[i] = (c >= 'a' && c <= 'z') ? c - 32 : c;
  }
  free(s.buf);
  Port result = inject_bytes(net, &out);
  free(out.buf);
  return result;
}
```

## Building the library

The library is compiled *without* HVM's runtime (the symbols it calls are provided by the running Bend program), so unresolved symbols must be allowed:

```bash
# Linux
gcc -shared -o libdemo.so -I /path/to/hvm/src libdemo.c \
    -Wl,--unresolved-symbols=ignore-all -fPIC

# macOS
gcc -shared -o libdemo.so -I /path/to/hvm/src libdemo.c \
    -undefined dynamic_lookup -fPIC
```

(`/path/to/hvm/src` is the directory containing `hvm.h`.)

## Calling it

<!-- setup: if [ "$(uname)" = Darwin ]; then gcc -shared -o libdemo.so -I "$HVM_SRC" libdemo.c -undefined dynamic_lookup -fPIC; else gcc -shared -o libdemo.so -I "$HVM_SRC" libdemo.c -Wl,--unresolved-symbols=ignore-all -fPIC; fi -->
<!-- expect: HELLO FFI -->
```bend
def main() -> IO(u24):
  with IO:
    dl <- IO/DyLib/open("./libdemo.so", 0)
    lib = Result/unwrap(dl)

    n <- IO/DyLib/call(lib, "square_plus_one", 12)
    * <- IO/print(u24/to_string(Result/unwrap(n)))
    * <- IO/print("\n")

    bytes <- IO/DyLib/call(lib, "shout", "hello ffi")
    * <- IO/print(String/decode_utf8(Result/unwrap(bytes)))
    * <- IO/print("\n")

    * <- IO/DyLib/close(lib)
    return wrap(0)
```

Run it from the folder containing `libdemo.so`:

```bash
bend run-c main.bend
```

```text
145
HELLO FFI
```

- The first call passes a Bend number and gets one back (`12² + 1 = 145`).
- The second passes a Bend string and receives a **list of bytes**, which `String/decode_utf8` turns back into text.
- The path `"./libdemo.so"` is relative to where you run the command. Use an absolute path in real programs.

## A standalone binary

If you compile the program with `gen-c` instead of `run-c`, link with `-rdynamic` so the library can see the runtime's symbols:

```bash
bend gen-c main.bend > main.c
gcc -rdynamic main.c -o main -lm
./main
```

(Put `-lm` after the source file, or the math functions won't link.)

## Wrapping the foreign calls

Don't scatter `DyLib/call` over your program. Wrap each foreign function in a Bend function with a proper type, so callers don't need to know about the library:

<!-- check: check -->
```bend
def square_plus_one(lib: u24, n: u24) -> IO(u24):
  with IO:
    r <- IO/DyLib/call(lib, "square_plus_one", n)
    return wrap(Result/unwrap(r))
```

Return `Result`s from the C side for failure cases instead of `ERA`: a foreign function that returns `*` and whose result is then used produces garbage.

## What you can build

With this one mechanism you can add, as a C library:

- directory listing, file metadata, environment variables, the clock;
- sockets and HTTP (a single `fetch` function);
- calls into any C library (compression, crypto, image decoding);
- GPU kernels with CUDA for `run-cu`.

The conversions between graph and C are the only subtle part: strings and byte lists use `readback_str`/`inject_bytes`; numbers use `get_u24`/`new_u24`; more complex data (tuples, lists of numbers) takes a little graph code. The HVM source (`hvm.h`, `hvm.c`) is the reference.

## Safety

- **The library runs inside the Bend process.** A crash in C crashes Bend; a memory bug corrupts the graph.
- **Free what you allocate.** `readback_str` allocates a buffer you must `free`; `inject_bytes` copies, so free your own buffer afterwards.
- **Signature mismatches fail silently.** The call passes one `Port`; if your C function expects a different shape you get garbage.
- **Side effects are ordered by IO.** Only call foreign functions inside `with IO:`.
- **Portability.** `.so` vs `.dylib`, compile flags, and CUDA vs C make libraries platform-specific.

## Common mistakes

- **Running with `run-rs`.** No IO, no FFI.
- **Forgetting `-fPIC` or `-shared`.**
- **Linking against the runtime** (`-lhvm`): there is none; leave symbols unresolved.
- **Wrong relative path to the library.**
- **Returning `NULL`/uninitialised ports.** Return `new_port(ERA, 0)` for "nothing".
- **Passing several arguments.** One argument only: bundle them.
- **Leaking the buffer from `readback_str`.**

## Exercises

1. Add `cube(n)` to the library and call it.
2. Add a function that takes a string and returns its length as a `u24`.
3. Add `reverse_bytes` that takes a string and returns the reversed bytes.
4. Wrap each foreign function in a typed Bend function and call those from `main`.
5. Write a library function that returns the current process ID (a `u24`).
6. Write a C function that lists a directory (see Bend's own `ls` example) and use `String/split`-style logic to turn the result into a list of names (remember to write your own `split`).
7. Build the program as a standalone binary with `gen-c` and run it.
8. Make a C function that returns a `Result`-shaped value for failure and handle it in Bend.

## Recap

- `IO/DyLib/open`/`call`/`close` call C (or CUDA) functions of the form `Port f(Net*, Book*, Port)` from a shared library.
- `hvm.h` provides the conversions: `get_u24`/`new_u24`, `readback_str`, `inject_bytes`, `new_port`.
- Build with `-shared -fPIC` and allow unresolved symbols; run with `bend run-c`; standalone builds need `-rdynamic`.
- Wrap foreign calls in typed Bend functions, and treat the library as trusted, in-process code.

Next: [The compiler & HVM →](11-compiler-and-hvm.md)
