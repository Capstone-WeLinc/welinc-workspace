#!/usr/bin/env bash
# Starts an unattended overnight run of Claude Code with the overnight guards.
#   bash agents/vrms/overnight/start.sh                 picks the queue from queue.md and the scope
#   bash agents/vrms/overnight/start.sh 69 65 58        only these features
#   bash agents/vrms/overnight/start.sh --until 07:00   stop starting new items after this time
#   bash agents/vrms/overnight/start.sh --plan          writes the queue and stops (a dry run)
#   bash agents/vrms/overnight/start.sh --watch         one long session you can follow from the Claude app
# By default every item runs in its own fresh session, on its own model (Opus to build, Sonnet for the
# rest, or the [model effort] tag on its queue.md line), and the run waits when your 5 hour usage
# reaches 95% (OVERNIGHT_LIMIT=90 to change it). Nothing here pushes, opens PRs or touches Azure.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

# 1. Find Claude Code: the CLI on PATH first, else the newest copy bundled in an editor extension.
CLAUDE_BIN="${CLAUDE_BIN:-$(command -v claude || true)}"
if [ -z "$CLAUDE_BIN" ]; then
  CLAUDE_BIN="$(ls -d "$HOME"/.antigravity-ide/extensions/anthropic.claude-code-*/resources/native-binary/claude* \
    "$HOME"/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude* 2>/dev/null | sort -V | tail -1 || true)"
fi
if [ -z "$CLAUDE_BIN" ]; then
  echo "Claude Code CLI not found. Install it (https://code.claude.com/docs/en/setup) and run this again." >&2
  exit 1
fi

# 2. The guard must pass its own tests before anything runs unattended.
if ! node --test agents/vrms/overnight/guard.test.mjs >/dev/null 2>&1; then
  echo "The overnight guard tests fail. Run: node --test agents/vrms/overnight/guard.test.mjs" >&2
  exit 1
fi

# 3. Docker has to be up for verify and test.
if ! docker info >/dev/null 2>&1; then
  echo "Docker is not running. Start Docker Desktop, then run this again." >&2
  exit 1
fi

# 4. Keep the machine awake while this shell (and Claude Code, its child) runs.
case "$(uname -s)" in
  Darwin)
    caffeinate -dimsu -w $$ &
    echo "Keeping the Mac awake (caffeinate). Keep it plugged in."
    ;;
  MINGW*|MSYS*|CYGWIN*)
    echo "Windows: make sure Sleep is set to Never while plugged in (Settings > System > Power), or run: powercfg /change standby-timeout-ac 0"
    ;;
esac

DIR=docs/_private/vrms/overnight
mkdir -p "$DIR"
export OVERNIGHT_RUN=1
SETTINGS="$ROOT/agents/vrms/overnight/settings.json"

RUNNER="$ROOT/agents/vrms/overnight/runner.mjs"
LIMIT="${OVERNIGHT_LIMIT:-95}"
export CLAUDE_BIN

# Fresh mode is the default: one headless session per step, so each item starts with a clean, cheap
# context. --watch keeps the old single session you can follow and message from your phone.
WATCH=0
PLAN=0
ARGS=()
for a in "$@"; do
  case "$a" in
    --watch) WATCH=1 ;;
    --fresh) ;; # the default now; still accepted
    --plan) PLAN=1; ARGS+=("$a") ;;
    *) ARGS+=("$a") ;;
  esac
done

# 5. The shared .claude/settings.json "asks" before git commit and git switch -c, and an ask rule
# beats every allow rule, so lift those routine rules for the run and put them back when it ends
# (after the report, on Ctrl+C, or at the next start if the machine died mid run).
# The process id the lift belongs to (Git Bash gives a Windows id through /proc), so a normal session
# opened mid run leaves the lift alone and one opened after a dead run puts the settings back.
OWNER="$(cat /proc/$$/winpid 2>/dev/null || echo $$)"
node agents/vrms/overnight/lift-settings.mjs lift "$OWNER"
trap 'node agents/vrms/overnight/lift-settings.mjs restore' EXIT
trap 'exit 130' INT TERM HUP

# 6. Each run gets its own id, folder and report, so a second run never writes over the first.
node "$RUNNER" archive
OVERNIGHT_RUN_ID="$(node "$RUNNER" runid)"
export OVERNIGHT_RUN_ID
RUN_DIR="$DIR/runs/$OVERNIGHT_RUN_ID"
REPORT="$DIR/$OVERNIGHT_RUN_ID.md"
LOG="$RUN_DIR/runner.log"
mkdir -p "$RUN_DIR"
node "$RUNNER" refs
node "$RUNNER" probe start | tee -a "$LOG"

finish() {
  echo "**Usage at the end:** $(node "$RUNNER" probe end | sed 's/^Usage: //')" >>"$REPORT" 2>/dev/null || true
  echo "Overnight run finished. Report: $REPORT"
}

if [ "$WATCH" = 1 ]; then
  echo "Starting the overnight run in one session. Open the Claude app on your phone to watch it (Remote Control)."
  "$CLAUDE_BIN" \
    --settings "$SETTINGS" \
    --permission-mode auto \
    --remote-control "overnight $OVERNIGHT_RUN_ID" \
    "/overnight ${ARGS[*]:-}" || true
  finish
  exit 0
fi

echo "Run $OVERNIGHT_RUN_ID: one fresh session per item. Follow along with: tail -f $LOG"

# Waits while the 5 hour window is at LIMIT% or more, until it resets. Returns 1 when the week is full.
wait_for_room() {
  local secs code=0
  secs="$(node "$RUNNER" room "$LIMIT")" || code=$?
  [ "$code" = 0 ] && return 0
  if [ "$code" = 3 ]; then
    echo "[$(date +%H:%M)] Weekly usage is at ${LIMIT}% or more; no new steps tonight." >>"$LOG"
    return 1
  fi
  echo "[$(date +%H:%M)] 5 hour usage is at ${LIMIT}% or more; waiting $((secs / 60)) minutes for it to reset." >>"$LOG"
  sleep "$secs"
  node "$RUNNER" probe after-wait >>"$LOG" 2>&1 || true
}

# Runs one headless step on its model, and records its turns and usage. A failed step tries again up to
# 3 times: after the reset when usage was the cause, else after 5 minutes.
step() {
  local mode="$1" prompt="$2" model="$3" effort="$4" label="$5" tries=0
  while true; do
    node "$RUNNER" probe "before $label" >>"$LOG" 2>&1 || true
    wait_for_room || return 2
    echo "[$(date +%H:%M)] $label on $model $effort: $prompt" >>"$LOG"
    if OVERNIGHT_MODE="$mode" "$CLAUDE_BIN" -p "$prompt" --settings "$SETTINGS" --permission-mode auto \
      --max-turns 300 --model "$model" --effort "$effort" --output-format stream-json --verbose 2>>"$LOG" |
      node "$RUNNER" log "$label" "$model" "$effort" >>"$LOG"; then
      return 0
    fi
    tries=$((tries + 1))
    if [ "$tries" -ge 3 ]; then
      echo "[$(date +%H:%M)] $label failed 3 times; giving up on this step." >>"$LOG"
      return 1
    fi
    if node "$RUNNER" room "$LIMIT" >/dev/null; then
      echo "[$(date +%H:%M)] $label exited with an error; trying again in 5 minutes." >>"$LOG"
      sleep 300
    fi
  done
}

if [ "$PLAN" = 1 ]; then
  step plan "/overnight ${ARGS[*]}" sonnet medium plan || true
  finish
  exit 0
fi

step prepare "/overnight --prepare ${ARGS[*]:-}" sonnet medium prepare || exit 1
rounds=0
while [ "$rounds" -lt 50 ]; do
  NEXT="$(node agents/vrms/overnight/guard.mjs next </dev/null 2>/dev/null)" || break
  read -r _left model effort <<<"$NEXT"
  step one "/overnight --one" "$model" "$effort" "item $((rounds + 1))" || break
  rounds=$((rounds + 1))
done
step close "/overnight --close" sonnet medium close || true
finish
