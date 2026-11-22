#!/usr/bin/env bash
# Starts an unattended overnight run of Claude Code with the overnight guards and Remote Control.
#   bash agents/vrms/overnight/start.sh                 picks the queue from the scope
#   bash agents/vrms/overnight/start.sh 69 65 58        only these features
#   bash agents/vrms/overnight/start.sh --until 07:00   stop starting new items after this time
#   bash agents/vrms/overnight/start.sh --plan          writes the queue and stops (a dry run)
# Run from Git Bash on Windows or a terminal on the Mac. Nothing here pushes, opens PRs or touches Azure.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

# 1. Find Claude Code: the CLI on PATH first, else the newest copy bundled in an editor extension.
CLAUDE_BIN="$(command -v claude || true)"
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

# --fresh: one headless session per step, so every item starts with a clean context.
FRESH=0
ARGS=()
for a in "$@"; do
  if [ "$a" = "--fresh" ]; then FRESH=1; else ARGS+=("$a"); fi
done

# 5. The shared .claude/settings.json "asks" before git commit and git switch -c, and an ask rule
# beats every allow rule, so lift those routine rules for the run and put them back when it ends
# (after the report, on Ctrl+C, or at the next start if the machine died mid run).
node agents/vrms/overnight/lift-settings.mjs lift
trap 'node agents/vrms/overnight/lift-settings.mjs restore' EXIT
trap 'exit 130' INT TERM

if [ "$FRESH" = 0 ]; then
  echo "Starting the overnight run. Open the Claude app on your phone to watch it (Remote Control)."
  "$CLAUDE_BIN" \
    --settings "$SETTINGS" \
    --permission-mode auto \
    --remote-control "overnight $(date +%Y-%m-%d)" \
    "/overnight ${ARGS[*]:-}" || true
  exit 0
fi

LOG="$DIR/runner-$(date +%Y-%m-%d).log"
echo "Fresh mode: one clean session per item. Progress goes to $LOG (no Remote Control in this mode)."

# Runs one headless step. A failed exit (usually a usage limit) waits 15 minutes and tries again, up to 8 times.
step() {
  local mode="$1" prompt="$2" tries=0
  while true; do
    echo "[$(date +%H:%M)] $mode: $prompt" >>"$LOG"
    if OVERNIGHT_MODE="$mode" "$CLAUDE_BIN" -p "$prompt" --settings "$SETTINGS" --permission-mode auto --max-turns 300 >>"$LOG" 2>&1; then
      return 0
    fi
    tries=$((tries + 1))
    if [ "$tries" -ge 8 ]; then
      echo "[$(date +%H:%M)] $mode failed 8 times; giving up on this step." >>"$LOG"
      return 1
    fi
    echo "[$(date +%H:%M)] $mode exited with an error (usage limit?); waiting 15 minutes." >>"$LOG"
    sleep 900
  done
}

has_next() { node agents/vrms/overnight/guard.mjs next </dev/null >/dev/null 2>&1; }

step prepare "/overnight --prepare ${ARGS[*]:-}" || exit 1
rounds=0
while has_next && [ "$rounds" -lt 50 ]; do
  step one "/overnight --one" || break
  rounds=$((rounds + 1))
done
step close "/overnight --close"
echo "Overnight run finished. Report: $DIR/$(date +%Y-%m-%d).md"
