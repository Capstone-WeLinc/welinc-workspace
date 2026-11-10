#!/usr/bin/env sh
# Stops every WeLinc stack this workspace has a compose file for. Your data stays in the volumes.
# Usage (from the workspace root): sh scripts/stop.sh
set -e
cd "$(dirname "$0")/.."

# Each system's stack first, the shared stack last (it owns the network the others join)
for file in docker-compose.*.yml; do
  [ "$file" = docker-compose.shared.yml ] && continue
  name=${file#docker-compose.}
  echo "Stopping ${name%.yml}..."
  docker compose -f "$file" stop
done
echo "Stopping the shared stack..."
docker compose -f docker-compose.shared.yml stop
