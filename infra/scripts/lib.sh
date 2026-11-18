# shellcheck shell=bash disable=SC2034  # its variables are used by the scripts that source it
# Shared by infra/scripts/*.sh (VRMS spec 0008). Sourced, never run.
# Needs: az (logged in to the WeLinc subscription), jq; psql for db-init.sh.

set -euo pipefail

INFRA="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../env/region.env
. "$INFRA/env/region.env"

SHARED_RG=rg-welinc-shared
PLACEHOLDER_IMAGE=mcr.microsoft.com/k8se/quickstart:latest
GITHUB_ORG=Capstone-WeLinc

die() { echo "error: $*" >&2; exit 1; }
note() { echo "==> $*" >&2; }

need() { command -v "$1" >/dev/null 2>&1 || die "$1 is not installed"; }

env_rg() { echo "rg-welinc-$1"; }

# The region of one environment's resources (region.env): production has its own.
env_location() { if [ "$1" = prod ]; then echo "$PROD_LOCATION"; else echo "$LOCATION"; fi; }
env_postgres_location() { if [ "$1" = prod ]; then echo "$PROD_POSTGRES_LOCATION"; else echo "$POSTGRES_LOCATION"; fi; }

check_env() {
  case "${1:-}" in staging|prod) ;; *) die "environment must be staging or prod" ;; esac
}

private_file() {
  local f="$INFRA/private/$1.json"
  [ -f "$f" ] || die "missing $f (copy infra/private.example.json and fill it)"
  echo "$f"
}

# The shared registry's name (created by `apply.sh shared`)
registry_name() {
  az acr list -g "$SHARED_RG" --query '[0].name' -o tsv 2>/dev/null | grep . \
    || die "no registry in $SHARED_RG yet: run apply.sh shared first"
}

# A deploy login's id from env/logins.json: login_id <env> <ours|vmms|bms> <clientId|principalId>
login_id() { jq -r --arg e "$1" --arg w "$2" --arg k "$3" '.[$e][$w][$k] // ""' "$INFRA/env/logins.json"; }

# Outputs of the last environment deployment
env_outputs() {
  az deployment group show -g "$(env_rg "$1")" -n welinc-env --query properties.outputs -o json 2>/dev/null \
    || die "no deployment welinc-env in $(env_rg "$1") yet: run apply.sh $1 first"
}

# A temporary firewall rule for this machine's address, removed on exit (spec 0008, Network)
open_firewall() {
  local env="$1" ip
  ip="$(curl -fsS https://api.ipify.org)" || die "could not find this machine's public address"
  FIREWALL_ENV="$env"
  note "opening psql-welinc-$env to $ip for this run"
  az postgres flexible-server firewall-rule create -g "$(env_rg "$env")" --server-name "psql-welinc-$env" \
    --name laptop-temporary --start-ip-address "$ip" --end-ip-address "$ip" -o none
  trap close_firewall EXIT
}

close_firewall() {
  [ -n "${FIREWALL_ENV:-}" ] || return 0
  note "closing the temporary firewall rule"
  az postgres flexible-server firewall-rule delete -g "$(env_rg "$FIREWALL_ENV")" --server-name "psql-welinc-$FIREWALL_ENV" \
    --name laptop-temporary --yes -o none || echo "warning: remove rule laptop-temporary by hand" >&2
}
