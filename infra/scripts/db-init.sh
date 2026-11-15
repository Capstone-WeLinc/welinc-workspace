#!/usr/bin/env bash
# Runs infra/db/init.sql for all seven databases of one environment (VRMS spec 0008, Database
# roles). apply.sh calls it after each environment apply; safe to run again.
#
#   db-init.sh <staging|prod>

. "$(dirname "$0")/lib.sh"
need az
need jq
need psql

env="${1:-}"
check_env "$env"
secrets="$(private_file "$env")"
host="psql-welinc-$env.postgres.database.azure.com"
admin_pw="$(jq -r .postgresAdminPassword "$secrets")"

open_firewall "$env"

for db in auth vrms vmms bms_booking bms_dispatch bms_completion bms_analytics; do
  owner_pw="$(jq -r --arg d "$db" '.roles[$d].owner // ""' "$secrets")"
  app_pw="$(jq -r --arg d "$db" '.roles[$d].app // ""' "$secrets")"
  [ -n "$owner_pw" ] && [ -n "$app_pw" ] || die "roles.$db needs owner and app passwords in $secrets"
  ext=""
  [ "$db" = vrms ] && ext="vector,pg_trgm"
  note "roles for $db"
  # The password goes in through the environment, never on the command line
  PGPASSWORD="$admin_pw" psql "host=$host port=5432 dbname=postgres user=welincadmin sslmode=require" \
    -q -v db="$db" -v owner_pw="$owner_pw" -v app_pw="$app_pw" -v extensions="$ext" \
    -f "$INFRA/db/init.sql" >/dev/null
done
note "database roles ready on $host"
