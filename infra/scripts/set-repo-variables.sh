#!/usr/bin/env bash
# Writes the GitHub repo variables our deploy workflows read, from the last apply's outputs and
# env/logins.json (VRMS spec 0008, Value sourcing: deploy steps). Variables, never secrets: none of
# these values is secret. VMMS and BMS set their own from docs/integration/hosting.md.
#
#   set-repo-variables.sh <staging|prod>

. "$(dirname "$0")/lib.sh"
need az
need jq
need gh

env="${1:-}"
check_env "$env"
ENV="$(echo "$env" | tr '[:lower:]' '[:upper:]')"
out="$(env_outputs "$env")"
client="$(login_id "$env" ours clientId)"
[ -n "$client" ] || die "fill $env.ours.clientId in infra/env/logins.json first"

host() { jq -r --arg w "$1" '.hosts.value[$w]' <<<"$out"; }
web() { jq -r --arg w "$1" '.webNames.value[$w]' <<<"$out"; }

set_var() {
  # set_var <repo> <name> <value>
  gh variable set "$2" -R "$GITHUB_ORG/$1" --body "$3" >/dev/null
  echo "  $1  $2"
}

common() {
  set_var "$1" AZURE_TENANT_ID "$(az account show --query tenantId -o tsv)"
  set_var "$1" AZURE_SUBSCRIPTION_ID "$(az account show --query id -o tsv)"
  set_var "$1" "AZURE_CLIENT_ID_$ENV" "$client"
  set_var "$1" ACR_NAME "$(registry_name)"
  set_var "$1" "RESOURCE_GROUP_$ENV" "$(env_rg "$env")"
  # Every deploy's smoke test calls all three (spec 0008 AC-9); the web builds read the first two
  set_var "$1" "${ENV}_API_URL" "https://$(host api)"
  set_var "$1" "${ENV}_PORTAL_URL" "https://$(host portal)"
  set_var "$1" "${ENV}_VRMS_URL" "https://$(host vrms)"
}

# Both environments share one Container Apps environment, so every app and job name carries its
# ending (spec 0008 AC-23). IMAGE_REPO is the base name, the same for both: production reuses the
# image staging built. The old CONTAINER_APP and MIGRATE_JOB are never written again; delete them
# once every workflow reads these (task 18a step 6).
suffix="$(name_suffix "$env")"

note "writing $env variables"
for pair in welinc-auth:auth-service:auth-migrate welinc-backend-vrms:vrms-backend:vrms-migrate; do
  IFS=: read -r repo app job <<<"$pair"
  common "$repo"
  set_var "$repo" IMAGE_REPO "$app"
  set_var "$repo" "CONTAINER_APP_$ENV" "$app$suffix"
  set_var "$repo" "MIGRATE_JOB_$ENV" "$job$suffix"
done

for pair in welinc-web-portal:portal welinc-web-vrms:vrms; do
  repo="${pair%%:*}"
  w="${pair##*:}"
  common "$repo"
  set_var "$repo" "STATIC_WEB_APP_$ENV" "$(web "$w")"
done

common welinc-workspace
set_var welinc-workspace IMAGE_REPO api-gateway
set_var welinc-workspace "CONTAINER_APP_$ENV" "api-gateway$suffix"
# The weekly image cleanup (.github/workflows/purge-images.yml); one login for both environments
purge="$(jq -r '.purge.clientId // ""' "$INFRA/env/logins.json")"
[ -z "$purge" ] || set_var welinc-workspace AZURE_CLIENT_ID_PURGE "$purge"
note "done"
