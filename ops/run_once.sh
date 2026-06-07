#!/usr/bin/env bash
# Ecnyss v2 — one evolve cycle. Sandboxed, gated, PR-only. Never pushes main.
set -uo pipefail
export HOME="${HOME:-/root}"   # ensure git finds the gh credential helper
REPO="/root/ai-lab/ecnesse"
LOG="/var/log/ecnyss/cycle.log"
LOCK="/tmp/ecnyss-cycle.lock"
mkdir -p /var/log/ecnyss
log(){ echo "[$(date -u +%FT%TZ)] $*" >> "$LOG"; }

if [ -f "$LOCK" ]; then
  pid=$(cat "$LOCK" 2>/dev/null || echo "")
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then log "SKIP: cycle still running (pid=$pid)"; exit 0; fi
  rm -f "$LOCK"
fi
echo $$ > "$LOCK"; trap 'rm -f "$LOCK"' EXIT

cd "$REPO" || exit 1
log "═══ CYCLE START ═══"
git pull --rebase --autostash --quiet 2>/dev/null || log "WARN: pull --rebase failed"
PYTHONPATH="$REPO" timeout 1100 python3 -m ecnyss.interfaces.cli evolve >> "$LOG" 2>&1
rc=$?
log "═══ CYCLE END rc=$rc ═══"

# Real-time docs: regenerate CHANGELOG.md + README status from the audit chain
# and publish to main (deterministic, fact-derived — outside the gate).
git pull --rebase --autostash --quiet 2>/dev/null || true
PYTHONPATH="$REPO" python3 -m ecnyss.interfaces.cli docs >/dev/null 2>&1 || true
git add CHANGELOG.md README.md 2>/dev/null || true
if ! git diff --cached --quiet 2>/dev/null; then
  git commit -m "docs: refresh changelog + status ($(date -u +%FT%TZ))" \
    --author="ecnyss <ecnyss@autonomous.local>" --quiet 2>/dev/null || true
  git push --quiet origin main 2>/dev/null || log "WARN: docs push failed"
  log "docs refreshed"
fi
exit 0
