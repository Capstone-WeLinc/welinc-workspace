#!/usr/bin/env sh
# Clones the WeLinc service repos next to this workspace repo (spec 0008, AC-25).
# Each repo is checked out on `development` when it has one, otherwise on its default branch.
#
# Usage (from the workspace root):
#   sh scripts/clone-all.sh          every repo (the shared services owner)
#   sh scripts/clone-all.sh vrms     the shared repos plus one group's repos (vrms, vmms or bms)
set -e

ORG="https://github.com/Capstone-WeLinc"
SHARED="welinc-auth welinc-web-portal"
VRMS="welinc-web-vrms welinc-backend-vrms"
VMMS="welinc-web-vmms welinc-backend-vmms welinc-backend-vmms-analytics-ai welinc-mobile-vrms_vmms"
BMS="welinc-web-bms welinc-backend-bms welinc-backend-bms-analytics-ai"

usage() {
  echo "Usage: sh scripts/clone-all.sh [vrms|vmms|bms]" >&2
  echo "  With no group it clones every repo; with one it clones the shared repos plus that group's." >&2
  exit 1
}

[ $# -le 1 ] || usage
case "${1:-}" in
  "") REPOS="$SHARED $VRMS $VMMS $BMS" ;;
  vrms) REPOS="$SHARED $VRMS" ;;
  vmms) REPOS="$SHARED $VMMS" ;;
  bms) REPOS="$SHARED $BMS" ;;
  *) usage ;;
esac

for repo in $REPOS; do
  if [ -d "$repo" ]; then
    echo "skip  $repo (already exists)"
    continue
  fi
  git clone "$ORG/$repo.git" "$repo"
  if git -C "$repo" ls-remote --exit-code --heads origin development >/dev/null 2>&1; then
    git -C "$repo" switch development
  else
    echo "note  $repo has no development branch, staying on $(git -C "$repo" branch --show-current)"
  fi
done
