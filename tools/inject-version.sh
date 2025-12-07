#!/bin/bash
# Inject git commit hash and timestamp into version badge

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
# Use German timezone (Europe/Berlin) for timestamp
TIMESTAMP=$(TZ='Europe/Berlin' date '+%d.%m.%Y %H:%M:%S')

echo "[info] Injecting version: $SHORT_HASH"
echo "[info] Timestamp: $TIMESTAMP"

# Update the toggle-debug button element with both commit and timestamp attributes
# Use awk to find and replace the button line
awk -v commit="$SHORT_HASH" -v timestamp="$TIMESTAMP" '
    /id="toggle-debug"/ {
        gsub(/data-commit="[^"]*"/, "data-commit=\"" commit "\"")
        gsub(/data-timestamp="[^"]*"/, "")
        sub(/id="toggle-debug"/, "id=\"toggle-debug\" data-commit=\"" commit "\" data-timestamp=\"" timestamp "\"")
    }
    { print }
' "$INDEX_FILE" > "${INDEX_FILE}.tmp"

mv "${INDEX_FILE}.tmp" "$INDEX_FILE"

echo "[success] Version injected successfully!"
echo "[info] Hash: $SHORT_HASH"
echo "[info] Time: $TIMESTAMP"
