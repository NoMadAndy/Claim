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
# Unix timestamp for cache busting
CACHE_BUST=$(date +%s)

echo "[info] Injecting version: $SHORT_HASH"
echo "[info] Timestamp: $TIMESTAMP"
echo "[info] Cache bust: $CACHE_BUST"

# Update the toggle-debug button element with both commit and timestamp attributes
# Also update cache busting for CSS and JS files
# IMPORTANT: remove any existing data-commit/data-timestamp attributes first to avoid duplicates.
awk -v commit="$SHORT_HASH" -v timestamp="$TIMESTAMP" -v cachebust="$CACHE_BUST" '
  /id="toggle-debug"/ {
    line = $0
    gsub(/ data-commit="[^"]*"/, "", line)
    gsub(/ data-timestamp="[^"]*"/, "", line)
    sub(/id="toggle-debug"/, "id=\"toggle-debug\" data-commit=\"" commit "\" data-timestamp=\"" timestamp "\"", line)
    print line
    next
  }
  /href="styles\.css"/ {
    # Ensure cache busting even if no ?v= is present
    if ($0 ~ /styles\.css\?v=/) {
      gsub(/styles\.css\?v=[0-9]+/, "styles.css?v=" cachebust)
    } else {
      gsub(/href="styles\.css"/, "href=\"styles.css?v=" cachebust "\"")
    }
  }
  /src="app\.js"/ {
    # Ensure cache busting even if no ?v= is present
    if ($0 ~ /app\.js\?v=/) {
      gsub(/app\.js\?v=[0-9]+/, "app.js?v=" cachebust)
    } else {
      gsub(/src="app\.js"/, "src=\"app.js?v=" cachebust "\"")
    }
  }
  /styles\.css\?v=/ {
    gsub(/styles\.css\?v=[0-9]+/, "styles.css?v=" cachebust)
  }
  /app\.js\?v=/ {
    gsub(/app\.js\?v=[0-9]+/, "app.js?v=" cachebust)
  }
  { print }
' "$INDEX_FILE" > "${INDEX_FILE}.tmp"

mv "${INDEX_FILE}.tmp" "$INDEX_FILE"

echo "[success] Version injected successfully!"
echo "[info] Hash: $SHORT_HASH"
echo "[info] Time: $TIMESTAMP"
echo "[info] Cache: $CACHE_BUST"
