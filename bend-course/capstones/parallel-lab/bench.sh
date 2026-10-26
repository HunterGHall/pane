#!/usr/bin/env bash
# Runs the lab benchmarks on 1, 2 and all cores and prints interactions, time and speed.
# Usage: bash bench.sh [queens-size] [bitonic-depth]
# Linux only for the core pinning (needs `taskset`); elsewhere it just runs once.
set -euo pipefail
cd "$(dirname "$0")"
N="${1:-9}"
D="${2:-14}"
CORES="$(nproc 2>/dev/null || sysctl -n hw.ncpu)"

run() { # name file arg cpus
  local label="$1" file="$2" arg="$3" cpus="$4"
  local out
  if command -v taskset >/dev/null 2>&1 && [ -n "$cpus" ]; then
    out="$(taskset -c "$cpus" bend run-c -s "$file" "$arg" 2>&1)"
  else
    out="$(bend run-c -s "$file" "$arg" 2>&1)"
  fi
  printf '%-22s %-24s %s\n' "$label" "$(echo "$out" | grep Result)" \
    "$(echo "$out" | grep -E 'ITRS|TIME|MIPS' | tr '\n' ' ' | sed 's/- //g')"
}

for cpus in "0" "0-1" "0-$((CORES - 1))"; do
  echo "== cores: $cpus =="
  run "queens($N)"  queens.bend  "$N" "$cpus"
  run "bitonic($D)" bitonic.bend "$D" "$cpus"
done
