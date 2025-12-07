#!/usr/bin/env bash
# Continuous Git Sync Watcher
# Fetches new commits from remote and syncs changes automatically
# Works on any branch (main, feature/*, etc.)

set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SYNC_SCRIPT="$PROJECT_ROOT/tools/auto_sync.sh"
LOG_FILE="$PROJECT_ROOT/.git-watch.log"
INTERVAL="${1:=10}"  # Default: check every 10 seconds

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
log_msg "INFO" "Sync script: $SYNC_SCRIPT"

cd "$PROJECT_ROOT"

# Track last known commits
local_commit=$(git rev-parse HEAD 2>/dev/null || echo "")
remote_commit=$local_commit

while true; do
  # Get current branch dynamically
  current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
  
  # Fetch latest from remote for current branch
  if git fetch origin "$current_branch" >/dev/null 2>&1; then
    new_local=$(git rev-parse HEAD 2>/dev/null || echo "")
    new_remote=$(git rev-parse "origin/$current_branch" 2>/dev/null || echo "")
    
    # Check for remote changes on current branch
    if [[ "$new_remote" != "$remote_commit" ]]; then
      log_msg "INFO" "🌐 Remote changes detected on branch '$current_branch'!"
      log_msg "INFO" "   Old: ${remote_commit:0:8}"
      log_msg "INFO" "   New: ${new_remote:0:8}"
      
      # Check if we need to pull (if remote is ahead of local)
      # If origin/main is NOT an ancestor of HEAD, we're behind and should pull
      if ! git merge-base --is-ancestor origin/main HEAD 2>/dev/null; then
        log_msg "INFO" "⬇️  Local is behind remote, pulling..."
        if git pull origin main >/dev/null 2>&1; then
          log_msg "SUCCESS" "✓ Remote changes pulled successfully"
          local_commit=$(git rev-parse HEAD)
        else
          log_msg "WARN" "⚠️  Pull failed (may have conflicts)"
        fi
      else
        log_msg "INFO" "✓ Local is up-to-date or ahead of remote"
      fi
      remote_commit=$new_remote
    fi
    
    # Check for local changes (uncommitted modifications)
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
      log_msg "INFO" "💾 Local changes detected on branch '$current_branch'"
      log_msg "INFO" "🔄 Running auto_sync..."
      if bash "$SYNC_SCRIPT" >> "$LOG_FILE" 2>&1; then
        log_msg "SUCCESS" "✓ Local sync completed"
        local_commit=$(git rev-parse HEAD)
      else
        log_msg "ERROR" "✗ Sync failed"
      fi
    fi
  else
    log_msg "WARN" "⚠️  Fetch from origin/$current_branch failed"
  fi
  
  sleep "$INTERVAL"
done
