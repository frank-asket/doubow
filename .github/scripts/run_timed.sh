#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -lt 3 ]]; then
  echo "usage: $0 <label> <timeout_window> <command...>"
  exit 2
fi

label="$1"
timeout_window="$2"
shift 2

step_start="$(date +%s)"
before_file="$(mktemp)"
after_file="$(mktemp)"

ps -eo pid,ppid,etime,cmd | rg -i "python|pytest|alembic|postgres" > "${before_file}" || true
echo "[timing] ${label} process snapshot BEFORE:"
awk '{print}' "${before_file}" || true
echo "[timing] ${label} start: $(date -u +'%Y-%m-%dT%H:%M:%SZ')"

set +e
timeout --foreground --kill-after=30s "${timeout_window}" "$@"
exit_code="$?"
set -e

ps -eo pid,ppid,etime,cmd | rg -i "python|pytest|alembic|postgres" > "${after_file}" || true
echo "[timing] ${label} process snapshot AFTER:"
awk '{print}' "${after_file}" || true

before_pids="$(awk '{print $1}' "${before_file}" | sort -u | tr '\n' ' ')"
after_pids="$(awk '{print $1}' "${after_file}" | sort -u | tr '\n' ' ')"
lingering_pids="$(comm -13 <(awk '{print $1}' "${before_file}" | sort -u) <(awk '{print $1}' "${after_file}" | sort -u) | tr '\n' ' ')"

echo "[timing] ${label} pid set BEFORE: ${before_pids:-<none>}"
echo "[timing] ${label} pid set AFTER: ${after_pids:-<none>}"
echo "[timing] ${label} new pids AFTER command: ${lingering_pids:-<none>}"

if [[ -n "${lingering_pids// }" ]]; then
  echo "[timing] ${label} attempting targeted cleanup for lingering pids"
  for pid in ${lingering_pids}; do
    ps -p "${pid}" -o pid,ppid,etime,cmd || true
  done
  kill -TERM ${lingering_pids} 2>/dev/null || true
  sleep 2
  kill -KILL ${lingering_pids} 2>/dev/null || true
fi

# Safety-net cleanup for command signatures known to hang in this job.
pkill -f "python -m pytest" || true
pkill -f "python -m alembic" || true

step_end="$(date +%s)"
echo "[timing] ${label} end: $(date -u +'%Y-%m-%dT%H:%M:%SZ') (elapsed=$((step_end-step_start))s)"
if [[ "${exit_code}" -eq 124 ]]; then
  echo "[timing] ${label} command timed out after ${timeout_window}"
fi

rm -f "${before_file}" "${after_file}"
exit "${exit_code}"
