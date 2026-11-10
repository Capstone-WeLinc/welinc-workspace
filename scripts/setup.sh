#!/usr/bin/env sh
# First time setup for one group: clones the repos, makes the .env files and signing keys, installs
# packages, starts the stack, creates the database tables and seeds them. Safe to run again: it
# skips whatever is already done, and never reseeds a database that already holds data.
#
# Usage (from the workspace root, in Git Bash on Windows or a terminal on Mac):
#   sh scripts/setup.sh vrms      (or vmms, bms)
set -e
cd "$(dirname "$0")/.."

case "${1:-}" in
  vrms | vmms | bms) group=$1 ;;
  *)
    echo "Usage: sh scripts/setup.sh <vrms|vmms|bms>" >&2
    exit 1
    ;;
esac

step() {
  printf '\n== %s\n' "$1"
}

step "Checking your tools"
for tool in git docker node npm curl; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Missing: $tool. Install it (see Prerequisites in README.md), then run this again." >&2
    exit 1
  fi
done
node_major=$(node -p "process.versions.node.split('.')[0]")
if [ "$node_major" != 24 ]; then
  echo "note  you have Node $node_major; the repos expect 24 (nvm install 24, then nvm use 24)"
fi
if ! docker info >/dev/null 2>&1; then
  echo "Docker isn't running. Start Docker Desktop, then run this again." >&2
  exit 1
fi
echo "ok"

step "Cloning the shared repos and the $group repos"
sh scripts/clone-all.sh "$group"

case "$group" in
  vrms) repos="welinc-auth welinc-web-portal welinc-web-vrms welinc-backend-vrms" ;;
  vmms) repos="welinc-auth welinc-web-portal welinc-web-vmms welinc-backend-vmms welinc-backend-vmms-analytics-ai welinc-mobile-vrms_vmms" ;;
  bms) repos="welinc-auth welinc-web-portal welinc-web-bms welinc-backend-bms welinc-backend-bms-analytics-ai" ;;
esac

step "Environment files"
# make_env <repo>: copy .env.example to .env once; an existing .env is never touched
make_env() {
  if [ -f "$1/.env" ]; then
    echo "keep  $1/.env"
  elif [ -f "$1/.env.example" ]; then
    cp "$1/.env.example" "$1/.env"
    echo "made  $1/.env from .env.example"
  fi
}
make_env welinc-auth
[ "$group" = vrms ] && make_env welinc-backend-vrms
# An older .env gets the names its .env.example gained since (spec 0010); names only are printed
node scripts/sync-env.mjs

step "Installing packages (a few minutes the first time)"
for repo in $repos; do
  if [ -f "$repo/package.json" ]; then
    echo "npm install in $repo"
    (cd "$repo" && npm install --no-audit --no-fund --loglevel=error)
  fi
done

step "Prisma clients"
# The Dockerfiles generate the client for the containers; the database steps below run on this
# machine, so each repo with a schema needs its own generated client here too
for repo in $repos; do
  if [ -f "$repo/prisma/schema.prisma" ]; then
    echo "prisma generate in $repo"
    (cd "$repo" && npx prisma generate >/dev/null)
  fi
done

step "Signing keys"
# has_value <file> <NAME>: true when NAME has a value in the file. Never prints the value.
# .env.example ships these names empty, so a present name alone is not enough. keys:dev writes the
# value single quoted, so a quote followed by real content counts, and '' or "" does not.
has_value() {
  grep -Eq "^$2=([^[:space:]\"']|[\"'][^\"'[:space:]])" "$1"
}
if has_value welinc-auth/.env AUTH_SIGNING_KEYS; then
  echo "keep  the keys already in welinc-auth/.env"
  if [ "$group" = vrms ] && ! has_value welinc-backend-vrms/.env AUTH_CLIENT_PRIVATE_KEY; then
    echo "note  welinc-backend-vrms/.env has no client key. Run: cd welinc-auth && npm run keys:dev -- --force"
  fi
elif [ -d welinc-backend-vrms ]; then
  (cd welinc-auth && npm run keys:dev --silent)
else
  # keys:dev also writes a VRMS client key; without VRMS cloned, it goes to a file that is then removed
  (cd welinc-auth && npm run keys:dev --silent -- --vrms-env .env.vrms-client.local && rm -f .env.vrms-client.local)
fi

step "Starting the shared stack"
docker compose -f docker-compose.shared.yml up -d --build

step "Auth database: tables, role catalog and seed people"
(cd welinc-auth && npm run db:deploy --silent && npm run seed --silent)
docker restart welinc_auth_service >/dev/null

case "$group" in
  vrms)
    step "VRMS: stack, tables and seed data"
    docker compose -f docker-compose.vrms.yml up -d --build
    (cd welinc-backend-vrms && npx prisma migrate deploy)
    tickets=$(docker exec welinc_vrms_db psql -U welinc_vrms_user -d welinc_vrms_db -tAc "select count(*) from repair_tickets" 2>/dev/null || echo 0)
    if [ "$tickets" = 0 ]; then
      (cd welinc-backend-vrms && npm run seed --silent)
    else
      echo "keep  the VRMS data already there (the VRMS seed wipes tickets, so it only runs on an empty database)"
    fi
    docker restart welinc_vrms_backend >/dev/null
    ;;
  *)
    step "$group"
    echo "The $group stack isn't in this workspace yet (it moves onto the shared services in suite row S11)."
    echo "Start your own system the way your group's README says until then."
    ;;
esac

step "Waiting for everything to answer"
sh scripts/start.sh "$group"

echo
echo "Setup finished. From now on, start your day with: sh scripts/start.sh $group"
echo "If you use an AI coding tool, turn on your group's setup once: node scripts/use-agents.mjs $group"
[ "$group" = vrms ] && echo "Optional: add GEMINI_API_KEY to welinc-backend-vrms/.env for the AI features (README, Environment files)."
exit 0
