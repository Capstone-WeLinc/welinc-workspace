#!/usr/bin/env sh
# Starts the shared stack, then your group's, and waits until they answer through the gateway.
# Safe to run any time; containers already running are left alone.
#
# Usage (from the workspace root, in Git Bash on Windows or a terminal on Mac):
#   sh scripts/start.sh vrms            shared stack plus VRMS
#   sh scripts/start.sh vrms --build    the same, rebuilding images (after a Dockerfile or package change)
#   sh scripts/start.sh                 the shared stack only
set -e
cd "$(dirname "$0")/.."

usage() {
  echo "Usage: sh scripts/start.sh [vrms|vmms|bms] [--build]" >&2
  exit 1
}

group=""
build=""
for arg in "$@"; do
  case "$arg" in
    vrms | vmms | bms) group=$arg ;;
    --build) build="--build" ;;
    *) usage ;;
  esac
done

if ! docker info >/dev/null 2>&1; then
  echo "Docker isn't running. Start Docker Desktop, wait for it to say it's running, then try again." >&2
  exit 1
fi

echo "Starting the shared stack (auth, gateway, portal)..."
docker compose -f docker-compose.shared.yml up -d $build

if [ -n "$group" ]; then
  if [ -f "docker-compose.$group.yml" ]; then
    echo "Starting $group..."
    docker compose -f "docker-compose.$group.yml" up -d $build
  else
    echo "note  docker-compose.$group.yml doesn't exist yet, so only the shared stack runs (see docs/integration/move-$group.md)"
  fi
fi

failed=0
# wait_for <name> <url> <container>: up to 3 minutes for a 2xx answer
wait_for() {
  printf 'Waiting for %s ' "$1"
  tries=0
  while [ $tries -lt 60 ]; do
    if curl -fs -o /dev/null "$2"; then
      echo " ok"
      return 0
    fi
    printf '.'
    sleep 3
    tries=$((tries + 1))
  done
  echo " no answer after 3 minutes. Read its log: docker logs --tail 50 $3"
  failed=1
}

wait_for gateway http://localhost:3000/health welinc_api_gateway
wait_for auth http://localhost:3000/auth/health welinc_auth_service
# Each system's health routes through the gateway (suite spec 0014, AC-16); VMMS and BMS only once
# they have moved (their compose file exists). Container names are the ones the move guides fix.
case "$group" in
  vrms) wait_for vrms http://localhost:3000/vrms/health welinc_vrms_backend ;;
  vmms)
    if [ -f docker-compose.vmms.yml ]; then
      wait_for vmms http://localhost:3000/vmms/health welinc_vmms_backend
      wait_for "vmms analytics" http://localhost:3000/vmms/analytics/health welinc_vmms_analytics
    fi
    ;;
  bms)
    [ -f docker-compose.bms.yml ] && wait_for bms http://localhost:3000/bms/health welinc_bms_gateway
    ;;
esac

echo
echo "  Portal (sign in here)   http://localhost:8000"
echo "  Gateway                 http://localhost:3000"
case "$group" in
  vrms) echo "  VRMS                    http://localhost:8001" ;;
  vmms) echo "  VMMS                    http://localhost:8002" ;;
  bms) echo "  BMS                     http://localhost:8003" ;;
esac
echo
echo "  Seed logins: docs/integration/seed-accounts.md (for example vrms.admin@welinc.com, admin1234)"
echo "  Stop everything: sh scripts/stop.sh"

exit $failed
