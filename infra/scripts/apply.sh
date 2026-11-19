#!/usr/bin/env bash
# Applies the WeLinc setup as code (VRMS spec 0008). Run from anywhere, logged in with `az login`.
#
#   apply.sh shared                         the registry (rg-welinc-shared), AcrPush for every login
#   apply.sh budget                         the subscription budget alerts (AC-12)
#   apply.sh <staging|prod>                 pass 1: everything on the default Azure host names
#   apply.sh <staging|prod> --domains       pass 2: bind the custom domains (after dns-records.sh)
#   ... --what-if                           preview only, changes nothing (WHATIF_ARGS="--result-format
#                                           ResourceIdOnly" lists only what changes, no values)
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
    # shellcheck disable=SC2086  # WHATIF_ARGS is a list of az options
    az deployment "$scope" what-if -n "$name" ${WHATIF_ARGS:-} "$@"
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

# {name: image}: what each app and job runs now, keyed by its name with the environment ending.
# The list is the base names (the core ones, plus any group app the last apply had, its ending
# removed) with this environment's ending, never the last outputs as they are: before task 18a
# they hold the old bare names. Per name:
#   1. the image the app or job runs now;
#   2. not there yet (the first apply under the new names): what the old bare named one runs, so
#      a renamed app starts on the image staging runs today, never the placeholder;
#   3. it runs the placeholder: the newest image pushed for it (its first deploy pushed one);
#   4. neither exists (a brand new environment's pass 1): nothing, so Bicep uses the placeholder.
current_images() {
  local env="$1" rg acr suffix last names n img repo tag out='{}'
  rg="$(env_rg "$env")"
  acr="$(registry_name)"
  suffix="$(name_suffix "$env")"
  last="$(az deployment group show -g "$rg" -n welinc-env \
    --query 'properties.outputs.[appNames.value, jobNames.value]' -o json 2>/dev/null || true)"
  names="$( {
    printf '%s\n' api-gateway auth-service vrms-backend auth-migrate auth-seed vrms-migrate vrms-seed
    jq -r 'flatten | .[]' <<<"${last:-[]}"
  } | while read -r n; do echo "$(base_name "$n")$suffix"; done | sort -u)"
  for n in $names; do
    img="$(running_image "$rg" "$n")"
    [ -n "$img" ] || img="$(running_image "$rg" "$(base_name "$n")")"
    if [ "$img" = "$PLACEHOLDER_IMAGE" ]; then
      repo="$(image_repo "$n")"
      tag="$(az acr repository show-tags -n "$acr" --repository "$repo" --orderby time_desc --top 1 -o tsv 2>/dev/null || true)"
      img="${tag:+$acr.azurecr.io/$repo:$tag}"
    fi
    [ -n "$img" ] && out="$(jq --arg n "$n" --arg i "$img" '. + {($n): $i}' <<<"$out")"
  done
  echo "$out"
}

# The image an app or job runs now, or nothing if it doesn't exist
running_image() {
  az containerapp show -g "$1" -n "$2" --query 'properties.template.containers[0].image' -o tsv 2>/dev/null ||
    az containerapp job show -g "$1" -n "$2" --query 'properties.template.containers[0].image' -o tsv 2>/dev/null || true
}

case "$target" in
  shared)
    register_providers
    az group create -n "$SHARED_RG" -l "$LOCATION" -o none
    jq '[.staging, .prod | .[] | .principalId | select(. != "")]' "$INFRA/env/logins.json" >"$TMP/push.json"
    deploy group welinc-shared -g "$SHARED_RG" -f "$INFRA/shared.bicep" \
      -p location="$LOCATION" -p pushPrincipalIds=@"$TMP/push.json" -p purgeTask="${PURGE_TASK:-true}" \
      -p purgePrincipalId="$(jq -r '.purge.principalId // ""' "$INFRA/env/logins.json")"
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
    suffix="$(name_suffix "$env")"
    # Production runs in staging's Container Apps environment (AC-23), so it must exist first
    if [ "$env" = prod ] && ! az containerapp env show -g "$CAE_RG" -n "$CAE_NAME" -o none 2>/dev/null; then
      die "$CAE_NAME in $CAE_RG doesn't exist. Production runs in staging's Container Apps environment: run apply.sh staging first."
    fi
    location="$(env_location "$env")"
    if [ "$env" = prod ] && [ "$location" != "$LOCATION" ]; then
      die "PROD_LOCATION ($location) must be staging's region ($LOCATION): production's apps join $CAE_NAME there"
    fi
    az group create -n "$rg" -l "$location" -o none

    current_images "$env" >"$TMP/images.json"
    note "images kept: $(jq -c . "$TMP/images.json")"
    jq --arg e "$env" '.[$e] | map_values(.principalId)' "$INFRA/env/logins.json" >"$TMP/logins.json"

    certExists=false
    # Each environment's gateway certificate sits on the shared environment as cert-api<ending>
    if $domains && [ -n "$(az containerapp env certificate list -g "$CAE_RG" -n "$CAE_NAME" \
      --managed-certificates-only --query "[?name=='cert-api$suffix'].name" -o tsv 2>/dev/null || true)" ]; then
      certExists=true
    fi

    deploy group welinc-env -g "$rg" -f "$INFRA/env.bicep" \
      -p @"$INFRA/env/$env.parameters.json" \
      -p location="$location" postgresLocation="$(env_postgres_location "$env")" registryName="$acr" \
      -p environmentName="$CAE_NAME" environmentResourceGroup="$CAE_RG" \
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
