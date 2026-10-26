#!/usr/bin/env python3
"""Checks every ```bend block in docs/ against the real Bend compiler, so the lessons never contain code that doesn't work.

By default a block is compiled AND run with `bend run-c`, and must succeed. A block with no `def main`
(only helper definitions) gets `def main(): return 0` appended.

Comments directly above the fence (one per line) change how a block is checked:

  <!-- check: check -->    only `bend check` it (type/syntax check, no run)
  <!-- check: fail -->     must be REJECTED by the compiler (to show an error message)
  <!-- check: skip -->     not checked (needs several files, hardware, a nightly feature, ...)
  <!-- expect: TEXT -->    the program's output must contain TEXT (after "Result: " for plain returns)
  <!-- stdin: TEXT -->     feed TEXT (with \\n escapes) to the program on standard input
  <!-- args: ARGS -->      pass ARGS on the command line (`bend run-c file ARGS`)
  <!-- runner: rs -->      run with `bend run-rs` instead of run-c (default is run-c, needed for IO)
  <!-- file: lib/x.bend --> this block is an extra source file (for import lessons): it is written next to
                        the main program of every other block in the same lesson, and not run itself

Usage: python tools/check_examples.py [--check-only] [files...]
"""
import concurrent.futures
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FENCE = re.compile(r"^(`{3,})bend\s*$")
MARK = re.compile(r"^<!--\s*(check|expect|stdin|args|runner|file):\s*(.*?)\s*-->\s*$")
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def extract(path):
    blocks = []
    lines = path.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        m = FENCE.match(lines[i])
        if m:
            marks = {}
            k = i - 1
            if k >= 0 and lines[k].startswith("<!-- sync:"):
                marks["check"] = "skip"
            while k >= 0 and MARK.match(lines[k]):
                kind, val = MARK.match(lines[k]).groups()
                marks[kind] = val
                k -= 1
            start = i + 1
            j = start
            while j < len(lines) and not lines[j].startswith(m.group(1)):
                j += 1
            blocks.append((start + 1, marks, "\n".join(lines[start:j]) + "\n"))
            i = j
        i += 1
    return blocks


def check(job):
    path, line, marks, code, check_only, aux = job
    mode = marks.get("check", "run")
    where = f"{path.relative_to(ROOT)}:{line}"
    if mode == "skip" or "file" in marks:
        return None
    if not re.search(r"^(def|main|Main)\b", code, re.M) or not re.search(r"^def main|^main|^Main", code, re.M):
        code += "\ndef main():\n  return 0\n"
    with tempfile.TemporaryDirectory() as tmp:
        for name, text in aux.items():
            target = Path(tmp) / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        src = Path(tmp) / "example.bend"
        src.write_text(code, encoding="utf-8")
        if mode == "fail":
            p = subprocess.run(["bend", "check", str(src)], capture_output=True, text=True, timeout=120)
            return f"{where}: expected a compile error, but it was accepted" if p.returncode == 0 else None
        if mode == "check" or check_only:
            cmd = ["bend", "check", str(src)]
        else:
            runner = "run-" + marks.get("runner", "c")
            cmd = ["bend", runner, str(src)] + marks.get("args", "").split()
        stdin = marks.get("stdin", "").encode().decode("unicode_escape") if "stdin" in marks else ""
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, input=stdin, timeout=120, cwd=tmp)
        except subprocess.TimeoutExpired:
            return f"{where}: timed out"
        out = ANSI.sub("", p.stdout + p.stderr)
        if p.returncode != 0 or "Errors:" in out:
            return f"{where}: failed\n" + "\n".join(out.splitlines()[:20])
        if "expect" in marks and marks["expect"] not in out:
            return f"{where}: expected output to contain {marks['expect']!r}, got:\n" + "\n".join(out.splitlines()[:12])
    return None


def main():
    args = sys.argv[1:]
    check_only = "--check-only" in args
    files = [Path(a).resolve() for a in args if not a.startswith("--")]
    if not files:
        files = sorted((ROOT / "docs").rglob("*.md"))
    jobs = []
    for f in files:
        blocks = extract(f)
        aux = {m["file"]: code for (_, m, code) in blocks if "file" in m}
        jobs += [(f, line, marks, code, check_only, aux) for (line, marks, code) in blocks]
    print(f"Checking {len(jobs)} code blocks from {len(files)} files...")
    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
        for result in pool.map(check, jobs):
            if result:
                failures.append(result)
    for f in failures:
        print("FAIL", f, "\n")
    print(f"{len(jobs) - len(failures)} OK, {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
