#!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$LAB_ROOT/tests/test_promotion.sh"
python3 "$LAB_ROOT/tests/check_workflows.py"
