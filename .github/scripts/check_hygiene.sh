#!/usr/bin/env bash
# Guard against the things that make merges painful or leak data.
#
#     .github/scripts/check_hygiene.sh
#
# Runs against tracked files only, so it is fast and says nothing about a
# contributor's untracked scratch files.

set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1

status=0

fail() { echo "[ FAIL ] $*"; status=1; }
ok()   { echo "[  ok  ] $*"; }

echo "== unresolved conflict markers =="
# A conflict marker committed to a branch is a merge someone abandoned
# halfway. Exclude this script, which necessarily contains the pattern.
markers=$(git grep -lE '^(<<<<<<< |>>>>>>> )' -- . ':(exclude).github/scripts/check_hygiene.sh' || true)
if [ -n "$markers" ]; then
  fail "conflict markers still present in:"
  echo "$markers" | sed 's/^/           /'
else
  ok "no files contain conflict markers"
fi

echo
echo "== OS and editor junk =="
junk=$(git ls-files | grep -E '(^|/)(\.DS_Store|Thumbs\.db|desktop\.ini)$' || true)
if [ -n "$junk" ]; then
  fail "OS junk is tracked (it conflicts on every merge):"
  echo "$junk" | sed 's/^/           /'
else
  ok "no .DS_Store or Thumbs.db tracked"
fi

echo
echo "== secrets =="
secrets=$(git ls-files | grep -E '(^|/)(\.env|serviceAccountKey\.json|.*\.SECRET\..*)$' || true)
if [ -n "$secrets" ]; then
  fail "files that must never be committed are tracked:"
  echo "$secrets" | sed 's/^/           /'
else
  ok "no .env, service account key, or SECRET file tracked"
fi

echo
echo "== build output =="
dist=$(git ls-files | grep -E '^medico-app/dist/' || true)
if [ -n "$dist" ]; then
  fail "medico-app/dist is tracked — it is generated, and it conflicts constantly"
else
  ok "no build output tracked"
fi

echo
if [ "$status" -ne 0 ]; then
  echo "Repo hygiene check failed."
else
  echo "Repo hygiene check passed."
fi
exit "$status"
