#!/bin/bash
# Simple remote sync script - just pull the latest from current branch
# Run this on the production/remote server to pull latest changes

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$PROJECT_ROOT/.remote-sync.log"

log_msg() {
  local level="$1"
  shift
  local msg="$*"
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[$timestamp] [$level] $msg" | tee -a "$LOG_FILE"
}

cd "$PROJECT_ROOT"

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
CURRENT_COMMIT=$(git rev-parse HEAD | cut -c1-8)

log_msg "INFO" "=== Remote Sync Started ==="
log_msg "INFO" "Branch: $CURRENT_BRANCH"
log_msg "INFO" "Current commit: $CURRENT_COMMIT"

# Fetch from remote
log_msg "INFO" "Fetching from remote..."
git fetch origin

# Get latest remote commit for current branch
REMOTE_COMMIT=$(git rev-parse "origin/$CURRENT_BRANCH" 2>/dev/null | cut -c1-8 || echo "unknown")
log_msg "INFO" "Remote commit: $REMOTE_COMMIT"

# Check if we need to pull
if git merge-base --is-ancestor "origin/$CURRENT_BRANCH" HEAD 2>/dev/null; then
  log_msg "INFO" "✓ Local is up-to-date or ahead (no pull needed)"
else
  log_msg "INFO" "⬇️  Pulling from origin/$CURRENT_BRANCH..."
  if git pull origin "$CURRENT_BRANCH"; then
    NEW_COMMIT=$(git rev-parse HEAD | cut -c1-8)
    log_msg "SUCCESS" "✓ Pulled successfully (now at $NEW_COMMIT)"
  else
    log_msg "ERROR" "✗ Pull failed"
    exit 1
  fi
fi

log_msg "INFO" "=== Remote Sync Complete ==="
