#!/usr/bin/env bash
# Prints the DNS records an environment needs at the registrar, from the last apply's outputs
# (VRMS spec 0008, Custom domains in two passes). Add them, wait, then run apply.sh <env> --domains.
#
#   dns-records.sh <staging|prod>            print the records
#   dns-records.sh <staging|prod> --check    check each one with dig

. "$(dirname "$0")/lib.sh"
need az
need jq

env="${1:-}"
check_env "$env"
check=false
[ "${2:-}" = --check ] && check=true

out="$(env_outputs "$env")"
domain="$(jq -r '.parameters.domain.value' "$INFRA/env/$env.parameters.json")"

# type, full name, value
records="$(jq -r --arg d "$domain" '
  [ ["CNAME", .hosts.value.api, .gatewayFqdn.value],
    ["TXT", "asuid." + .hosts.value.api, .customDomainVerificationId.value] ]
  + [ .webDefaultHostnames.value[] as $w | ["CNAME", .hosts.value[$w.web], $w.defaultHostname] ]
  | .[] | @tsv' <<<"$out")"

if ! $check; then
  echo "Add these at the registrar for $domain (host is the part before .$domain):"
  echo
  printf '%-6s %-28s %s\n' TYPE HOST VALUE
  while IFS=$'\t' read -r type name value; do
    printf '%-6s %-28s %s\n' "$type" "${name%."$domain"}" "$value"
  done <<<"$records"
  echo
  echo "A Static Web App may ask for one more TXT record when its domain is bound; pass 2 prints it if so."
  exit 0
fi

need dig
missing=0
while IFS=$'\t' read -r type name value; do
  got="$(dig +short "$type" "$name" | tr -d '"' | sed 's/\.$//' | head -1)"
  if [ "$got" = "$value" ]; then
    echo "ok       $type $name"
  else
    echo "missing  $type $name (wants $value, has ${got:-nothing})"
    missing=1
  fi
done <<<"$records"
exit "$missing"
