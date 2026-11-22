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
START_USAGE="$(node "$RUNNER" probe start)"
echo "$START_USAGE" | tee -a "$LOG"
case "$START_USAGE" in
  *'?%'*) echo "WARNING: could not read your usage, so the run will NOT wait at ${LIMIT}%. Check /usage yourself before you leave it." | tee -a "$LOG" ;;
esac

finish() {
  # A run still marked running here ended early (the week filled up, close out failed): mark it halted so
  # the next run starts fresh instead of resuming this one.
  node "$RUNNER" halt "the run ended before close out finished" >>"$LOG" 2>&1 || true
  if [ -f "$REPORT" ]; then
    echo "**Usage at the end:** $(node "$RUNNER" probe end | sed 's/^Usage: //')" >>"$REPORT" || true
  fi
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

# Runs one headless step on its model, and records its turns and usage. A step that failed because of the
# usage limit waits for the reset and runs again (up to 3 times); any other failure returns 1 at once, so
# one bad item costs one session, not three. Returns 2 when the week is full.
step() {
  local mode="$1" prompt="$2" model="$3" effort="$4" label="$5" probe="${6:-0}" tries=0
  while true; do
    # The usage check runs once per queue line (probe=1), not once per milestone session. Between checks
    # every step records the usage its own session saw, and wait_for_room reads that, so it costs nothing.
    [ "$probe" = 1 ] && node "$RUNNER" probe "before $label" >>"$LOG" 2>&1 || true
    wait_for_room || return 2
    echo "[$(date +%H:%M)] $label on $model $effort: $prompt" >>"$LOG"
    if OVERNIGHT_MODE="$mode" "$CLAUDE_BIN" -p "$prompt" --settings "$SETTINGS" --permission-mode auto \
      --max-turns 300 --model "$model" --effort "$effort" --output-format stream-json --verbose </dev/null 2>>"$LOG" |
      node "$RUNNER" log "$label" "$model" "$effort" >>"$LOG"; then
      return 0
    fi
    tries=$((tries + 1))
    if [ "$tries" -ge 3 ]; then
      echo "[$(date +%H:%M)] $label failed 3 times; giving up on this step." >>"$LOG"
      return 1
    fi
    if node "$RUNNER" room "$LIMIT" >/dev/null; then
      echo "[$(date +%H:%M)] $label exited with an error (not the usage limit); not trying again." >>"$LOG"
      return 1
    fi
    echo "[$(date +%H:%M)] $label hit the usage limit; it runs again after the reset." >>"$LOG"
  done
}

if [ "$PLAN" = 1 ]; then
  step plan "/overnight ${ARGS[*]}" sonnet medium plan || true
  finish
  exit 0
fi

if ! step prepare "/overnight --prepare ${ARGS[*]:-}" sonnet medium prepare || [ ! -f "$DIR/state.json" ]; then
  echo "[$(date +%H:%M)] Preflight did not finish; no items run." >>"$LOG"
  finish
  exit 1
fi
rounds=0
last_group=""
while [ "$rounds" -lt 50 ]; do
  NEXT="$(node agents/vrms/overnight/guard.mjs next </dev/null 2>/dev/null)" || break
  read -r _left model effort item <<<"$NEXT"
  code=0
  group="${item%-m[0-9]*}" # S19-m1, S19-m2 and so on are one queue line: S19
  probe=0
  [ "$group" != "$last_group" ] && probe=1
  last_group="$group"
  step one "/overnight --one" "$model" "$effort" "$item" "$probe" || code=$?
  [ "$code" = 2 ] && break # the week is full
  # The session ended but the item is still open (it crashed, ran out of turns, or never saved): fail it,
  # so the loop moves on instead of starting it again.
  case "$(node "$RUNNER" status "$item")" in
    pending | running) node "$RUNNER" fail "$item" "the session ended without finishing it (exit $code); see runs/$OVERNIGHT_RUN_ID/runner.log" >>"$LOG" ;;
  esac
  rounds=$((rounds + 1))
done
[ -f "$DIR/state.json" ] && step close "/overnight --close" sonnet medium close || true
finish
