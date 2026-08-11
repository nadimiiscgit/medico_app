#!/usr/bin/env bash
# Lint ratchet: tolerate the existing errors, refuse new ones.
#
#     .github/scripts/check_lint.sh
#
# main has a standing eslint debt. Making lint a blocking check outright would
# fail every pull request for faults it did not introduce; leaving it purely
# advisory paints a permanent red X on every pull request, which teaches
# everyone to ignore red. So this compares the error count against a committed
# baseline: existing debt passes, new errors fail, and paying debt down forces
# the baseline lower so it can never silently regress.

set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1

BASELINE_FILE=".github/lint-baseline.txt"
REPORT=$(mktemp)
trap 'rm -f "$REPORT"' EXIT

baseline=$(tr -dc '0-9' < "$BASELINE_FILE")
: "${baseline:=0}"

cd medico-app || exit 1
# eslint exits non-zero when it finds errors; the JSON report is what we read,
# so its exit code is not the signal here.
npx eslint . -f json -o "$REPORT" > /dev/null 2>&1

if [ ! -s "$REPORT" ]; then
  echo "[ FAIL ] eslint produced no report — it likely failed to run at all"
  exit 1
fi

read -r errors warnings < <(python3 -c "
import json
report = json.load(open('$REPORT'))
print(sum(f['errorCount'] for f in report), sum(f['warningCount'] for f in report))
")

echo "eslint: $errors error(s), $warnings warning(s) — baseline is $baseline"

summary() { [ -n "${GITHUB_STEP_SUMMARY:-}" ] && echo "$*" >> "$GITHUB_STEP_SUMMARY"; return 0; }

if [ "$errors" -gt "$baseline" ]; then
  echo
  echo "[ FAIL ] this branch adds $((errors - baseline)) eslint error(s)."
  echo
  echo "All $errors current errors are listed below — $baseline of them predate"
  echo "this branch. Run 'npm run lint' on main to see which those are."
  echo
  python3 -c "
import json
for f in json.load(open('$REPORT')):
    for m in f['messages']:
        if m.get('severity') == 2:
            print(f\"  {f['filePath']}:{m['line']}:{m['column']}  {m['message']} ({m.get('ruleId')})\")
"
  summary "### Lint ❌"
  summary "This branch adds **$((errors - baseline))** eslint error(s) — $errors against a baseline of $baseline."
  exit 1
fi

if [ "$errors" -lt "$baseline" ]; then
  # Passing, not failing: a branch that reduces the debt must never be blocked
  # for it. The baseline is only a ceiling.
  echo
  echo "[  ok  ] $((baseline - errors)) error(s) fixed. Lower the baseline so it sticks:"
  echo "           echo $errors > $BASELINE_FILE"
  summary "### Lint ✅"
  summary "**$((baseline - errors))** error(s) fixed. Set \`$BASELINE_FILE\` to \`$errors\` to lock the gain in."
  exit 0
fi

echo "[  ok  ] no new eslint errors"
summary "### Lint ✅"
summary "No new eslint errors ($errors known, unchanged). $warnings warning(s)."
exit 0
