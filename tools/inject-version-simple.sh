#!/bin/bash
# Simple version injection - set data attributes on toggle-debug button
# This script is meant to be run on deployment servers, not in git hooks

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INDEX_FILE="$PROJECT_ROOT/frontend/index.html"

if [[ ! -f "$INDEX_FILE" ]]; then
  echo "[error] index.html not found at $INDEX_FILE"
  exit 1
fi

# Get current git info
COMMIT_HASH=$(cd "$PROJECT_ROOT" && git rev-parse HEAD 2>/dev/null || echo "unknown")
if [[ "$COMMIT_HASH" == "unknown" ]]; then
  # If not in git repo, use current date
  COMMIT_HASH="deployed"
fi

SHORT_HASH="${COMMIT_HASH:0:8}"

# Use German timezone (Europe/Berlin) for timestamp
TIMESTAMP=$(TZ='Europe/Berlin' date '+%d.%m.%Y %H:%M:%S')

echo "[info] Injecting version: $SHORT_HASH"
echo "[info] Timestamp: $TIMESTAMP"

# Update the toggle-debug button with data attributes (idempotent)
# 1) Remove any existing data-commit/data-timestamp
# 2) Inject exactly one set right after id="toggle-debug"
sed -i \
  -e 's/ data-commit="[^"]*"//g' \
  -e 's/ data-timestamp="[^"]*"//g' \
  -e "s|id=\"toggle-debug\"|id=\"toggle-debug\" data-commit=\"$SHORT_HASH\" data-timestamp=\"$TIMESTAMP\"|" \
  "$INDEX_FILE"

echo "[success] Version injected successfully!"
