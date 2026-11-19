#!/usr/bin/env bash
# Changes one secret on one app or job without a full apply (VRMS spec 0008), then restarts the
# app's revision, because a running revision keeps the old value until it restarts.
#
#   rotate-secret.sh <staging|prod> <app or job> <SETTING_NAME>
#
# The name has its environment ending, as in Azure: auth-service-prod, vrms-migrate-staging.
#
# The value is read without echo, so it never lands in the shell history. Put the same value in
# infra/private/<env>.json too, or the next apply.sh sets the old one back.

. "$(dirname "$0")/lib.sh"
need az

env="${1:-}"
name="${2:-}"
setting="${3:-}"
check_env "$env"
[ -n "$name" ] && [ -n "$setting" ] || die "usage: rotate-secret.sh <staging|prod> <app or job> <SETTING_NAME>"
rg="$(env_rg "$env")"
# The same naming container-app.bicep and job.bicep use
secret="$(echo "$setting" | tr '[:upper:]_' '[:lower:]-')"

printf 'New value for %s on %s (%s): ' "$setting" "$name" "$env" >&2
IFS= read -rs value
echo >&2
[ -n "$value" ] || die "empty value, nothing changed"

if az containerapp show -g "$rg" -n "$name" -o none 2>/dev/null; then
  az containerapp secret set -g "$rg" -n "$name" --secrets "$secret=$value" -o none
  revision="$(az containerapp show -g "$rg" -n "$name" --query properties.latestReadyRevisionName -o tsv)"
  az containerapp revision restart -g "$rg" -n "$name" --revision "$revision" -o none
  note "$setting changed on $name, revision $revision restarted"
elif az containerapp job show -g "$rg" -n "$name" -o none 2>/dev/null; then
  az containerapp job secret set -g "$rg" -n "$name" --secrets "$secret=$value" -o none
  note "$setting changed on job $name (its next run uses it)"
else
  die "no app or job named $name in $rg"
fi
echo "Now put the same value in infra/private/$env.json." >&2
