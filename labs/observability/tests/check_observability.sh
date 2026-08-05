#\!/usr/bin/env bash
set -euo pipefail

LAB_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RULES_FILE="$LAB_ROOT/solution/prometheus/rules.yaml"

grep -q 'HighErrorRate' "$RULES_FILE"
grep -q 'HighLatencyP95' "$RULES_FILE"
grep -q 'severity:' "$RULES_FILE"

if command -v promtool >/dev/null 2>&1; then
  promtool check rules "$RULES_FILE" >/dev/null
fi

echo "observability solution checks passed"
