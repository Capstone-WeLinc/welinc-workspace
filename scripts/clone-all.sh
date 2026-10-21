#!/usr/bin/env sh
# Clones every WeLinc service repo next to this workspace repo.
# Usage: sh scripts/clone-all.sh   (run from the workspace root)
set -e

ORG="https://github.com/Capstone-WeLinc"
REPOS="
welinc-auth
welinc-web-portal
welinc-web-vrms
welinc-backend-vrms
welinc-backend-vrms-analytics-ai
welinc-web-vmms
welinc-backend-vmms
welinc-web-bms
welinc-backend-bms
"

for repo in $REPOS; do
  if [ -d "$repo" ]; then
    echo "skip  $repo (already exists)"
  else
    git clone "$ORG/$repo.git" "$repo"
  fi
done
