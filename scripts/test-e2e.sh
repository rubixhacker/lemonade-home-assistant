#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Unique project names isolate concurrent runs and cleanup from developer stacks.
project="lemonade-e2e-${GITHUB_RUN_ID:-local}-$$"
compose=(docker compose -p "$project" -f tests/e2e/compose.yaml)
artifacts="${E2E_ARTIFACTS:-dist/e2e}"
mkdir -p "$artifacts"
cleanup() {
  result=$?
  trap - EXIT
  "${compose[@]}" logs --no-color > "$artifacts/containers.log" 2>&1 || true
  "${compose[@]}" down --volumes --remove-orphans || true
  exit "$result"
}
trap cleanup EXIT
"${compose[@]}" config > "$artifacts/compose.yaml"
"${compose[@]}" pull
for image in "${HA_IMAGE:-ghcr.io/home-assistant/home-assistant:stable}" "${LEMONADE_IMAGE:-ghcr.io/lemonade-sdk/lemonade-server:latest}"; do
  docker image inspect "$image" --format '{{json .RepoDigests}}'
done > "$artifacts/images.jsonl"
"${compose[@]}" up --abort-on-container-exit --exit-code-from homeassistant
