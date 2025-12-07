#!/bin/bash
# Inject git commit hash into version badge
# Run this before pushing to automatically update version info

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
INDEX_FILE="$FRONTEND_DIR/index.html"

if [[ ! -f "$INDEX_FILE" ]]; then
  echo "[error] index.html not found at $INDEX_FILE"
  exit 1
fi

# Get current git commit hash
COMMIT_HASH=$(cd "$PROJECT_ROOT" && git rev-parse HEAD 2>/dev/null)
if [[ -z "$COMMIT_HASH" ]]; then
  echo "[error] Failed to get git commit hash"
  exit 1
fi

SHORT_HASH="${COMMIT_HASH:0:8}"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[info] Injecting version: $SHORT_HASH (from $COMMIT_HASH)"
echo "[info] Timestamp: $TIMESTAMP"

# Update the version-hash element with data attribute
sed -i "s/id=\"version-hash\" title=\"Click to copy version\"/id=\"version-hash\" data-commit=\"$COMMIT_HASH\" title=\"Click to copy version\"/g" "$INDEX_FILE"

echo "[success] Version injected successfully!"
echo "[info] Updated: $INDEX_FILE"
