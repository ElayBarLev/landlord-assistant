#!/usr/bin/env bash
# Publish a change: ./release.sh "what changed"
# Checks everything, raises the version, commits, tags and pushes. Pushes nothing if a check fails.
set -euo pipefail
cd "$(dirname "$0")"
msg=${1:?usage: ./release.sh \"what changed\"}
[ "$(git branch --show-current)" = main ] || { echo "Switch to main first"; exit 1; }
git fetch -q origin
git merge-base --is-ancestor origin/main HEAD || { echo "Run git pull first"; exit 1; }
claude plugin validate . 
claude plugin validate plugins/landlord
python3 tests/test_ledger.py
m=plugins/landlord/.claude-plugin/plugin.json
v=$(python3 - "$m" <<'P'
import json, sys
p = sys.argv[1]; d = json.load(open(p))
a, b, c = map(int, d["version"].split("."))
d["version"] = f"{a}.{b}.{c + 1}"
open(p, "w").write(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
print(d["version"])
P
)
git add -A
git commit -qm "$msg (v$v)"
git tag "v$v"
git push -q --atomic origin main "v$v"
echo "Published v$v"
