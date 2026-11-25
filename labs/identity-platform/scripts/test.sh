#!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$LAB_ROOT/tests/run_tests.py"
python3 "$LAB_ROOT/tests/check_reference.py"
