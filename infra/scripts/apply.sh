#!/usr/bin/env bash
# Applies the WeLinc setup as code (VRMS spec 0008). Run from anywhere, logged in with `az login`.
#
#   apply.sh shared                         the registry (rg-welinc-shared), AcrPush for every login
#   apply.sh budget                         the subscription budget alerts (AC-12)
#   apply.sh <staging|prod>                 pass 1: everything on the default Azure host names
#   apply.sh <staging|prod> --domains       pass 2: bind the custom domains (after dns-records.sh)
#   ... --what-if                           preview only, changes nothing
#   ... --skip-db                           skip infra/db/init.sql (it needs psql)
#
# An environment apply always passes the image each app and job runs now, so it never rolls an
# app back, and the private file's secrets, because Container Apps replaces the whole secret list.
# Run it again any time: it changes only what differs.

. "$(dirname "$0")/lib.sh"
need az
need jq

target="${1:-}"
shift || true
domains=false
whatif=false
skipdb=false
for a in "$@"; do
  case "$a" in
    --domains) domains=true ;;
    --what-if) whatif=true ;;
    --skip-db) skipdb=true ;;
    *) die "unknown option $a" ;;
  esac
done

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

deploy() {
  # deploy <group|sub> <name> args...: create, or what-if with --what-if
  local scope="$1" name="$2"
  shift 2
  if $whatif; then
    az deployment "$scope" what-if -n "$name" "$@"
  else
    az deployment "$scope" create -n "$name" "$@" -o none
    note "applied $name"
  fi
}

register_providers() {
  for p in Microsoft.App Microsoft.OperationalInsights Microsoft.ContainerRegistry \
    Microsoft.DBforPostgreSQL Microsoft.Web Microsoft.Storage Microsoft.ManagedIdentity \
    Microsoft.Consumption; do
    state="$(az provider show -n "$p" --query registrationState -o tsv 2>/dev/null || true)"
    if [ "$state" != Registered ]; then
      note "registering $p (once per subscription)"
      az provider register -n "$p" --wait -o none
    fi
  done
}

# The repository an app or job's image comes from: runners are <app>, jobs run <app>-seed
image_repo() {
  case "$1" in
    auth-migrate | auth-seed) echo auth-service-seed ;;
    vrms-migrate | vrms-seed) echo vrms-backend-seed ;;
    vmms-migrate) echo vmms-backend-seed ;;
    *-migrate) echo "${1%-migrate}-seed" ;;
    *) echo "$1" ;;
  esac
}

# {name: image}: what each app and job runs now; for one still on the placeholder, the newest
# image pushed for it (its first deploy pushed one); else nothing, and Bicep uses the placeholder.
current_images() {
  local env="$1" rg acr names out='{}'
  rg="$(env_rg "$env")"
  acr="$(registry_name)"
  names="$(az deployment group show -g "$rg" -n welinc-env \
    --query 'properties.outputs.[appNames.value, jobNames.value]' -o json 2>/dev/null |
    jq -r 'flatten | .[]' || true)"
  [ -n "$names" ] || names="api-gateway auth-service vrms-backend auth-migrate auth-seed vrms-migrate vrms-seed"
  for n in $names; do
    img="$(az containerapp show -g "$rg" -n "$n" --query 'properties.template.containers[0].image' -o tsv 2>/dev/null ||
      az containerapp job show -g "$rg" -n "$n" --query 'properties.template.containers[0].image' -o tsv 2>/dev/null || true)"
    if [ -z "$img" ] || [ "$img" = "$PLACEHOLDER_IMAGE" ]; then
      repo="$(image_repo "$n")"
      tag="$(az acr repository show-tags -n "$acr" --repository "$repo" --orderby time_desc --top 1 -o tsv 2>/dev/null || true)"
      img="${tag:+$acr.azurecr.io/$repo:$tag}"
    fi
    [ -n "$img" ] && out="$(jq --arg n "$n" --arg i "$img" '. + {($n): $i}' <<<"$out")"
  done
  echo "$out"
}

case "$target" in
  shared)
    register_providers
    az group create -n "$SHARED_RG" -l "$LOCATION" -o none
    jq '[.staging, .prod | .[] | .principalId | select(. != "")]' "$INFRA/env/logins.json" >"$TMP/push.json"
    deploy group welinc-shared -g "$SHARED_RG" -f "$INFRA/shared.bicep" \
      -p location="$LOCATION" -p pushPrincipalIds=@"$TMP/push.json" -p purgeTask="${PURGE_TASK:-true}"
    ;;

  budget)
    email="$(jq -r '.alertEmail // ""' "$(private_file staging)")"
    [ -n "$email" ] || die "set alertEmail in infra/private/staging.json"
    deploy sub welinc-budget -l "$LOCATION" -f "$INFRA/subscription.bicep" -p alertEmail="$email"
    ;;

  staging | prod)
    env="$target"
    rg="$(env_rg "$env")"
    secrets="$(private_file "$env")"
    register_providers
    acr="$(registry_name)"
    az group create -n "$rg" -l "$LOCATION" -o none

    current_images "$env" >"$TMP/images.json"
    note "images kept: $(jq -c . "$TMP/images.json")"
    jq --arg e "$env" '.[$e] | map_values(.principalId)' "$INFRA/env/logins.json" >"$TMP/logins.json"

    certExists=false
    if $domains && [ -n "$(az containerapp env certificate list -g "$rg" -n "cae-welinc-$env" \
      --managed-certificates-only --query "[?name=='cert-api'].name" -o tsv 2>/dev/null || true)" ]; then
      certExists=true
    fi

    deploy group welinc-env -g "$rg" -f "$INFRA/env.bicep" \
      -p @"$INFRA/env/$env.parameters.json" \
      -p location="$LOCATION" postgresLocation="$POSTGRES_LOCATION" registryName="$acr" \
      -p bindDomains="$domains" gatewayCertExists="$certExists" \
      -p images=@"$TMP/images.json" -p logins=@"$TMP/logins.json" -p secrets=@"$secrets"

    if ! $whatif && ! $skipdb; then
      "$(dirname "$0")/db-init.sh" "$env"
    fi
    $whatif || $domains || note "next: infra/scripts/dns-records.sh $env, add the records, then apply.sh $env --domains"
    ;;

  *)
    sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
    ;;
esac
