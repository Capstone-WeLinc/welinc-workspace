#!/usr/bin/env bash
# Keeps the newest 15 tags of every image in the shared registry and deletes the rest: the same
# rule as the weekly purge task in shared.bicep. Only needed when the subscription refuses ACR
# Tasks (apply.sh shared with PURGE_TASK=false); .github/workflows/purge-images.yml then runs it
# every Sunday. It deletes by tag, not untagged manifests: deploys never overwrite a tag.
#
#   purge-images.sh [--dry-run]

. "$(dirname "$0")/lib.sh"
need az

dry=false
[ "${1:-}" = --dry-run ] && dry=true
acr="$(registry_name)"
keep=15

for repo in $(az acr repository list -n "$acr" -o tsv); do
  old="$(az acr repository show-tags -n "$acr" --repository "$repo" --orderby time_desc -o tsv | tail -n +$((keep + 1)))"
  for tag in $old; do
    if $dry; then
      echo "would delete $repo:$tag"
    else
      az acr repository delete -n "$acr" --image "$repo:$tag" --yes -o none
      echo "deleted $repo:$tag"
    fi
  done
done
