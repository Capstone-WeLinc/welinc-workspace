#!/bin/sh
# Spec 0008, AC-13: refuse to start on a missing or malformed setting, naming it, before nginx
# reads a template. Also writes the CORS origin map from ALLOWED_ORIGINS.
set -eu

fail() {
  echo "gateway: $1" >&2
  exit 1
}

# True when the whole value (one line, no newline) matches the extended regex
matches() {
  [ "$(printf '%s' "$2" | wc -l)" -eq 0 ] && printf '%s' "$2" | grep -Eqx "$1"
}

require() {
  eval "value=\${$1-}"
  [ -n "$value" ] || fail "$1 is required and is not set"
}

for name in AUTH_UPSTREAM VRMS_UPSTREAM VMMS_UPSTREAM VMMS_ANALYTICS_UPSTREAM BMS_UPSTREAM; do
  require "$name"
  eval "value=\$$name"
  matches 'https?://[A-Za-z0-9.-]+(:[0-9]{1,5})?' "$value" \
    || fail "$name must be scheme://host[:port], with no path or trailing slash (got '$value')"
done

require TRUST_EDGE_PROXY
matches '[01]' "$TRUST_EDGE_PROXY" || fail "TRUST_EDGE_PROXY must be 0 or 1 (got '$TRUST_EDGE_PROXY')"

for name in GATEWAY_RATE_PER_SECOND GATEWAY_RATE_BURST; do
  require "$name"
  eval "value=\$$name"
  matches '[1-9][0-9]*' "$value" || fail "$name must be a positive whole number (got '$value')"
done

[ -n "${GATEWAY_HSTS+x}" ] || fail "GATEWAY_HSTS must be set (it may be empty)"

require ALLOWED_ORIGINS
map_file=/etc/nginx/generated/cors-origins.map
mkdir -p "$(dirname "$map_file")"
tmp_file="$map_file.tmp"
: > "$tmp_file"
seen=" "

# The extra comma makes a trailing empty entry visible to the loop (field splitting drops one
# trailing empty field); set -f stops a * from globbing
origins="$ALLOWED_ORIGINS,"
set -f
old_ifs=$IFS
IFS=,
for raw in $origins; do
  IFS=$old_ifs
  origin=$(printf '%s' "$raw" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
  [ -n "$origin" ] || fail "ALLOWED_ORIGINS has an empty entry"
  case "$origin" in
    *[A-Z]*) fail "ALLOWED_ORIGINS entry '$origin' has an uppercase letter" ;;
  esac
  matches 'https?://[a-z0-9.-]+(:[0-9]{1,5})?' "$origin" \
    || fail "ALLOWED_ORIGINS entry '$origin' isn't a plain http:// or https:// origin (no *, path or trailing slash)"
  case "$seen" in
    *" $origin "*) fail "ALLOWED_ORIGINS lists '$origin' twice" ;;
  esac
  seen="$seen$origin "
  printf '"%s" "%s";\n' "$origin" "$origin" >> "$tmp_file"
  IFS=,
done
IFS=$old_ifs
set +f

mv "$tmp_file" "$map_file"
echo "gateway: settings checked, $(wc -l < "$map_file" | tr -d ' ') CORS origins"
