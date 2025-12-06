#!/usr/bin/env bash
# Continuous Git Sync Watcher
# Fetches new commits and syncs changes periodically

set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYNC_SCRIPT="$PROJECT_ROOT/auto_sync.sh"
LOG_FILE="$PROJECT_ROOT/.git-watch.log"
INTERVAL="${1:=30}"  # Default: check every 30 seconds

if [[ ! -f "$SYNC_SCRIPT" ]]; then
  echo "[error] auto_sync.sh not found at $SYNC_SCRIPT"
  exit 1
fi

log_msg() {
  local level="$1"
  shift
  local msg="$*"
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[$timestamp] [$level] $msg" | tee -a "$LOG_FILE"
}

log_msg "INFO" "Git Watch started (interval: ${INTERVAL}s)"
log_msg "INFO" "Log file: $LOG_FILE"

cd "$PROJECT_ROOT"

# Track last known commit
last_commit=$(git rev-parse HEAD 2>/dev/null || echo "")

while true; do
  # Fetch latest
  if git fetch origin main >/dev/null 2>&1; then
    current_commit=$(git rev-parse HEAD)
    upstream_commit=$(git rev-parse origin/main 2>/dev/null || echo "")
    
    # Check for new commits
    if [[ "$current_commit" != "$last_commit" ]] || [[ "$current_commit" != "$upstream_commit" ]]; then
      log_msg "INFO" "New commits detected"
      log_msg "INFO" "Local:  $current_commit"
      log_msg "INFO" "Remote: $upstream_commit"
      
      # Check for uncommitted changes
      if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        log_msg "INFO" "Running auto_sync..."
        if bash "$SYNC_SCRIPT" >> "$LOG_FILE" 2>&1; then
          log_msg "SUCCESS" "Sync completed"
          last_commit=$(git rev-parse HEAD)
        else
          log_msg "ERROR" "Sync failed (exit code: $?)"
        fi
      else
        log_msg "INFO" "No local changes to sync"
      fi
    fi
  else
    log_msg "WARN" "Fetch failed"
  fi
  
  sleep "$INTERVAL"
done
