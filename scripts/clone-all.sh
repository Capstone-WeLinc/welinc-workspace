#!/usr/bin/env sh
# Clones every WeLinc service repo next to this workspace repo.
# Each repo is checked out on `development` when it has one, otherwise on its default branch.
# Usage: sh scripts/clone-all.sh   (run from the workspace root)
set -e

ORG="https://github.com/Capstone-WeLinc"
REPOS="
welinc-auth
welinc-web-portal
welinc-web-vrms
welinc-backend-vrms
welinc-web-vmms
welinc-backend-vmms
welinc-web-bms
welinc-backend-bms
"

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
