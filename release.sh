#!/usr/bin/env bash
# Publish a change: ./release.sh "what changed"
# Checks everything, raises the version, commits, tags and pushes. Pushes nothing if a check fails.
set -euo pipefail
cd "$(dirname "$0")"
msg=${1:?usage: ./release.sh \"what changed\"}
[ "$(git branch --show-current)" = main ] || { echo "Switch to main first"; exit 1; }
git fetch -q --tags origin
git merge-base --is-ancestor origin/main HEAD || { echo "Run git pull first"; exit 1; }
claude plugin validate .
claude plugin validate plugins/landlord
python3 tests/test_ledger.py
python3 tests/test_catalog.py
m=plugins/landlord/.claude-plugin/plugin.json
v=$(python3 - "$m" <<'P'
import json, subprocess, sys
p = sys.argv[1]; d = json.load(open(p))
# Count from the highest published version, so undoing a change still moves forward.
tags = subprocess.run(["git", "tag", "-l", "v*"], capture_output=True, text=True, check=True).stdout.split()
a, b, c = max([tuple(map(int, v.lstrip("v").split("."))) for v in [d["version"], *tags]])
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
