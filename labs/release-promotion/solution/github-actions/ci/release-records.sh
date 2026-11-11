#!/usr/bin/env bash
# Release records kept in the platform, not in a workflow's memory.
#
# Every deployment of a release is recorded through the GitHub Deployments API with
# task=release (or task=acceptance), ref=<release commit> and a payload holding the
# image digest and the promotion workflow's blob hash. Jobs that use `environment:`
# also get automatic deployment records, but those carry github.sha (the head of the
# default branch for workflow_run and workflow_dispatch), not the release commit.
# Filtering on task keeps the two apart.
#
# usage:
#   release-records.sh start   ENV SHA DIGEST [TASK]   -> prints deployment id
#   release-records.sh finish  ID STATE                (success | failure)
#   release-records.sh last    ENV [TASK]              -> prints "sha digest workflow_blob" of the latest success
#   release-records.sh get     ENV SHA [TASK]          -> same, for the latest success of this release
#   release-records.sh find    ENV SHA DIGEST [TASK]   -> exit 0 if this exact release succeeded there
set -euo pipefail

REPO="${GITHUB_REPOSITORY:?}"
WORKFLOW_BLOB="${WORKFLOW_BLOB:-}"

start() {
  local env="$1" sha="$2" digest="$3" task="${4:-release}"
  jq -n --arg ref "$sha" --arg env "$env" --arg task "$task" --arg digest "$digest" \
        --arg blob "$WORKFLOW_BLOB" --arg run "${GITHUB_RUN_ID:-}" --arg actor "${GITHUB_ACTOR:-}" \
     '{ref: $ref, environment: $env, task: $task, auto_merge: false, required_contexts: [],
       transient_environment: false, production_environment: ($env == "prod"),
       payload: {digest: $digest, workflow_blob: $blob, run_id: $run, actor: $actor}}' \
    | gh api "repos/$REPO/deployments" --input - --jq '.id'
}

finish() {
  gh api "repos/$REPO/deployments/$1/statuses" -f state="$2" \
     -f log_url="${GITHUB_SERVER_URL:-https://github.com}/$REPO/actions/runs/${GITHUB_RUN_ID:-}" >/dev/null
}

# Newest-first scan; prints the first successful record matching SHA (or any, if SHA is empty)
# and stops, so no early-closed pipe can fail the script under pipefail.
first_success() {
  local env="$1" want_sha="${2:-}" task="${3:-release}" id sha digest blob state
  while IFS=$'\t' read -r id sha digest blob; do
    [[ -n "$want_sha" && "$sha" != "$want_sha" ]] && continue
    state="$(gh api "repos/$REPO/deployments/$id/statuses?per_page=1" --jq '.[0].state // ""')"
    if [[ "$state" == "success" ]]; then
      printf '%s %s %s\n' "$sha" "$digest" "$blob"
      return 0
    fi
  done < <(gh api --paginate "repos/$REPO/deployments?environment=$env&task=$task&per_page=100" \
             --jq '.[] | [.id, .sha, .payload.digest, .payload.workflow_blob] | @tsv')
  return 0
}

case "${1:-}" in
  start)  shift; start "$@" ;;
  finish) shift; finish "$@" ;;
  last)   shift; first_success "$1" "" "${2:-release}" ;;
  get)    shift; first_success "$1" "$2" "${3:-release}" ;;
  find)   shift; [[ "$(first_success "$1" "$2" "${4:-release}" | cut -d' ' -f2)" == "$3" ]] ;;
  *) echo "usage: $0 start|finish|last|get|find ..." >&2; exit 2 ;;
esac
