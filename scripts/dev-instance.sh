#!/usr/bin/env bash
# Runs a disposable, local Home Assistant instance with this repo's
# custom_components bind-mounted in, for fast dev iteration.
# See docs/DEVELOPMENT.md — never develop directly against the real
# Home Assistant Green instance.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p "$REPO_ROOT/dev-config"

docker run -it --rm \
  --name ha-tibber-vehicle-dev \
  -v "$REPO_ROOT/custom_components:/config/custom_components" \
  -v "$REPO_ROOT/dev-config:/config" \
  -p 8123:8123 \
  ghcr.io/home-assistant/home-assistant:stable
