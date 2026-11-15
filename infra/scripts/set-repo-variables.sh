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
  set_var "$1" "${ENV}_API_URL" "https://$(host api)"
}

note "writing $env variables"
for repo in welinc-auth welinc-backend-vrms; do
  common "$repo"
done
set_var welinc-auth CONTAINER_APP auth-service
set_var welinc-auth MIGRATE_JOB auth-migrate
set_var welinc-backend-vrms CONTAINER_APP vrms-backend
set_var welinc-backend-vrms MIGRATE_JOB vrms-migrate

for pair in welinc-web-portal:portal welinc-web-vrms:vrms; do
  repo="${pair%%:*}"
  w="${pair##*:}"
  common "$repo"
  set_var "$repo" "STATIC_WEB_APP_$ENV" "$(web "$w")"
  set_var "$repo" "${ENV}_PORTAL_URL" "https://$(host portal)"
  set_var "$repo" "${ENV}_WEB_URL" "https://$(host "$w")"
done

common welinc-workspace
set_var welinc-workspace CONTAINER_APP api-gateway
note "done"
