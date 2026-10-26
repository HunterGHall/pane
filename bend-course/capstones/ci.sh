#!/usr/bin/env bash
# Runs every capstone: compile-checks them and smoke-tests them with scripted input.
# Used by CI; handy locally too. Needs `bend` and `hvm` on the PATH and a C compiler.
set -euo pipefail
cd "$(dirname "$0")"

bend --version

echo "== task-tracker =="
(
  cd task-tracker
  bend check main.bend
  tasks="$(mktemp -u)"
  trap 'rm -f "$tasks"' EXIT
  out="$(printf 'add Buy milk\nadd Learn Bend\ndone 2\nlist\nremove 9\nremove 1\nlist\nquit\n' \
    | bend run-c main.bend "\"$tasks\"")"
  echo "$out"
  echo "$out" | grep -q '^1\. \[ \] Buy milk$'
  echo "$out" | grep -q '^2\. \[x\] Learn Bend$'
  echo "$out" | grep -q '^no such task$'
  echo "$out" | grep -q '^removed$'
  # a second run must find the saved list again
  out="$(printf 'list\nquit\n' | bend run-c main.bend "\"$tasks\"")"
  echo "$out" | grep -q '^1\. \[x\] Learn Bend$'
)

echo "== expression-calculator =="
(
  cd expression-calculator
  bend check main.bend
  out="$(bend run-c tests.bend)"
  echo "$out"
  echo "$out" | grep -q '^16 passed, 0 failed$'
  out="$(printf '2 + 3 * (4 - 1)\n10 / (5 - 5)\nquit\n' | bend run-c main.bend)"
  echo "$out"
  echo "$out" | grep -q '^= 11$'
  echo "$out" | grep -q '^error: division by zero$'
)

echo "== parallel-lab =="
(
  cd parallel-lab
  bend check queens.bend
  bend check bitonic.bend
  bend run-c queens.bend 6 | grep -q '^Result: 4$'
  bend run-c queens.bend 8 | grep -q '^Result: 92$'
  bend run-c bitonic.bend 8 | grep -q '^Result: 1$'
)

echo "All capstones OK"
