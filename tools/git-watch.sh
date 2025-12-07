#!/usr/bin/env bash
# Continuous Git Sync Watcher
# Fetches new commits from remote and syncs changes automatically

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

cd "$PROJECT_ROOT"

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")

log_msg "INFO" "Git Watch started (interval: ${INTERVAL}s)"
log_msg "INFO" "Log file: $LOG_FILE"
log_msg "INFO" "Sync script: $SYNC_SCRIPT"
log_msg "INFO" "Project root: $PROJECT_ROOT"
log_msg "INFO" "Current branch: $CURRENT_BRANCH"

# Track last known commits
local_commit=$(git rev-parse HEAD 2>/dev/null || echo "")
remote_commit="none"

log_msg "INFO" "Initial local commit: ${local_commit:0:8}"

while true; do
  # Fetch latest from remote for current branch
  if git fetch origin "$CURRENT_BRANCH" >/dev/null 2>&1; then
    new_local=$(git rev-parse HEAD 2>/dev/null || echo "")
    new_remote=$(git rev-parse "origin/$CURRENT_BRANCH" 2>/dev/null || echo "")
    
    # Debug output
    log_msg "DEBUG" "Local: ${new_local:0:8}, Remote: ${new_remote:0:8}, Last remote: ${remote_commit:0:8}"
    
    # Check for remote changes (new commits on origin/branch)
    if [[ "$new_remote" != "$remote_commit" ]]; then
      log_msg "INFO" "🌐 Remote changes detected!"
      log_msg "INFO" "   Old: ${remote_commit:0:8}"
      log_msg "INFO" "   New: ${new_remote:0:8}"
      
      # Check merge base to determine if we're behind
      # If origin/branch is an ancestor of HEAD, we're ahead or equal
      # If origin/branch is NOT an ancestor of HEAD, we're behind and need to pull
      if git merge-base --is-ancestor "origin/$CURRENT_BRANCH" HEAD 2>/dev/null; then
        # origin/branch IS an ancestor of HEAD = we're ahead
        log_msg "INFO" "✓ Local is ahead of or equal to remote (no pull needed)"
      else
        # origin/branch is NOT an ancestor of HEAD = we're behind
        log_msg "INFO" "⬇️  Local is behind remote, pulling..."
        if git pull origin "$CURRENT_BRANCH" 2>&1 | tee -a "$LOG_FILE"; then
          log_msg "SUCCESS" "✓ Remote changes pulled successfully"
          local_commit=$(git rev-parse HEAD)
        else
          log_msg "WARN" "⚠️  Pull failed (may have conflicts)"
        fi
      fi
      
      remote_commit=$new_remote
    fi
    
    # Check for local changes (uncommitted modifications)
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
      log_msg "INFO" "💾 Local changes detected"
      log_msg "INFO" "🔄 Running auto_sync..."
      if bash "$SYNC_SCRIPT" >> "$LOG_FILE" 2>&1; then
        log_msg "SUCCESS" "✓ Local sync completed"
        local_commit=$(git rev-parse HEAD)
      else
        log_msg "ERROR" "✗ Sync failed"
      fi
    fi
  else
    log_msg "WARN" "⚠️  Fetch from origin/$CURRENT_BRANCH failed"
  fi
  
  sleep "$INTERVAL"
done
