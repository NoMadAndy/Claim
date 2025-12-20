#!/usr/bin/env bash
# Auto-Deployment Watcher: Continuously monitors git and redeploys on changes
# Install as: sudo systemctl enable --now claim-watcher.service

set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOY_SCRIPT="$PROJECT_ROOT/tools/deploy.sh"
LOG_FILE="$PROJECT_ROOT/.watcher.log"
INTERVAL="${1:-60}"  # Check every 60 seconds by default
BRANCH="${BRANCH:-main}"

if [[ ! -f "$DEPLOY_SCRIPT" ]]; then
  echo "[ERROR] Deploy script not found: $DEPLOY_SCRIPT"
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

log_msg "INFO" "=== Deployment Watcher Started ==="
log_msg "INFO" "Project: $PROJECT_ROOT"
log_msg "INFO" "Check interval: ${INTERVAL}s"
log_msg "INFO" "Branch: $BRANCH"
log_msg "INFO" "Log: $LOG_FILE"

# Track last known commit
LAST_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "")
if [[ -z "$LAST_COMMIT" ]]; then
  log_msg "WARN" "Could not determine initial commit (detached HEAD or git error)"
else
  log_msg "INFO" "Initial commit: ${LAST_COMMIT:0:8}"
fi

while true; do
  sleep "$INTERVAL"
  
  # Fetch latest from remote (capture error output for debugging)
  FETCH_OUTPUT=$(git fetch origin "$BRANCH" 2>&1)
  FETCH_EXIT=$?
  
  if [[ $FETCH_EXIT -ne 0 ]]; then
    log_msg "WARN" "Failed to fetch from remote (exit code: $FETCH_EXIT)"
    log_msg "DEBUG" "Git fetch error: $FETCH_OUTPUT"
    
    # Additional diagnostics
    if ! git remote get-url origin >/dev/null 2>&1; then
      log_msg "ERROR" "Git remote 'origin' not configured"
    fi
    
    continue
  fi
  
  # Get remote commit
  REMOTE_COMMIT=$(git rev-parse "origin/$BRANCH" 2>/dev/null || echo "")
  
  if [[ -z "$REMOTE_COMMIT" ]]; then
    log_msg "WARN" "Could not determine remote commit"
    continue
  fi
  
  # Check if commit changed
  if [[ "$LAST_COMMIT" != "$REMOTE_COMMIT" ]]; then
    log_msg "INFO" "New commits detected! (${LAST_COMMIT:0:8} → ${REMOTE_COMMIT:0:8})"
    log_msg "INFO" "Running deployment..."
    
    # Run deployment script
    if bash "$DEPLOY_SCRIPT" 2>&1 | tee -a "$LOG_FILE"; then
      LAST_COMMIT="$REMOTE_COMMIT"
      log_msg "SUCCESS" "Deployment completed successfully"
    else
      log_msg "ERROR" "Deployment failed!"
    fi
  else
    log_msg "DEBUG" "No changes (${REMOTE_COMMIT:0:8})"
  fi
done
