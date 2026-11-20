#!/usr/bin/env bash
# One step of welinc-auth's signing key rotation on a hosted environment, applied end to end
# (suite spec 0002 AC-24; the steps and their waits are in welinc-auth docs/keys.md):
#
#   rotate-signing-keys.sh <staging|prod> <add|promote|remove> [--now] [<kid>]
#
# keys:rotate edits an env style file, while the hosted key set lives in infra/private/<env>.json
# (auth.signingKeys, a JSON string). This copies it into a temporary env file, runs the step there
# (a step that is too early is refused and nothing changes), writes the result back, then sets it
# on every resource env.bicep gives AUTH_SIGNING_KEYS: the auth app (restarted by rotate-secret.sh)
# and both auth jobs. Prints key ids and statuses only, never a key.
#
# Afterwards, update the password manager copy of infra/private/<env>.json.

. "$(dirname "$0")/lib.sh"
need jq
need npm
need az

env="${1:-}"
check_env "$env"
shift
case "${1:-}" in add|promote|remove) ;; *) die "usage: rotate-signing-keys.sh <staging|prod> <add|promote|remove> [--now] [<kid>]" ;; esac

priv="$(private_file "$env")"
auth_repo="$INFRA/../welinc-auth"
[ -d "$auth_repo/node_modules" ] || die "run npm ci in welinc-auth first (keys:rotate runs there)"

# A copy to go back to; infra/private/ is git ignored, like the file itself
cp "$priv" "$priv.bak"

umask 077
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
printf "AUTH_SIGNING_KEYS='%s'\n" "$(jq -c '.auth.signingKeys | fromjson' "$priv")" > "$tmp"

(cd "$auth_repo" && npm run -s keys:rotate -- "$tmp" "$@")

keys="$(sed -n "s/^AUTH_SIGNING_KEYS='\(.*\)'$/\1/p" "$tmp")"
[ -n "$keys" ] || die "no AUTH_SIGNING_KEYS after the step; nothing applied"

jq --arg k "$keys" '.auth.signingKeys = $k' "$priv" > "$priv.tmp" && mv "$priv.tmp" "$priv"
note "written to infra/private/$env.json (the previous version is $env.json.bak)"

# The app first, then the jobs (their next run reads it). rotate-secret.sh reads the value from
# stdin without echo.
suffix="$(name_suffix "$env")"
for name in "auth-service$suffix" "auth-migrate$suffix" "auth-seed$suffix"; do
  printf '%s\n' "$keys" | bash "$(dirname "$0")/rotate-secret.sh" "$env" "$name" AUTH_SIGNING_KEYS
done

jq -r '.auth.signingKeys | fromjson | .keys[] | "\(.kid)  \(.status)  added \(.addedAt // "-")  retired \(.retiredAt // "-")"' "$priv" >&2
note "now update the password manager copy of infra/private/$env.json"
