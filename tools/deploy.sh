#!/usr/bin/env bash
# Auto-Deployment Script: Pulls changes and redeploys Docker containers
# Run this on the production server (as root or with docker/systemctl permissions)

set -uo pipefail

# This script lives in tools/, but must operate from the repository root.
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$PROJECT_ROOT/.deploy.log"
LOCK_FILE="$PROJECT_ROOT/.deploy.lock"

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
BRANCH="${BRANCH:-main}"
RESTART_TIMEOUT=30

log_msg() {
  local level="$1"
  shift
  local msg="$*"
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[$timestamp] [$level] $msg" | tee -a "$LOG_FILE"
}

# Prevent concurrent deployments
if [[ -f "$LOCK_FILE" ]]; then
  LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null || echo "unknown")
  log_msg "WARN" "Deployment already in progress (PID: $LOCK_PID). Skipping."
  exit 0
fi

trap 'rm -f "$LOCK_FILE"' EXIT
echo $$ > "$LOCK_FILE"

log_msg "INFO" "========== DEPLOYMENT STARTED =========="
log_msg "INFO" "Project: $PROJECT_ROOT"
log_msg "INFO" "Compose file: $COMPOSE_FILE"
log_msg "INFO" "Branch: $BRANCH"

cd "$PROJECT_ROOT"

# Get current state before pull
LOCAL_COMMIT=$(git rev-parse HEAD 2>/dev/null | cut -c1-8)
log_msg "INFO" "Current commit: $LOCAL_COMMIT"

# Fetch latest changes
log_msg "INFO" "Fetching from remote..."
if ! git fetch origin "$BRANCH"; then
  log_msg "ERROR" "Failed to fetch from remote"
  exit 1
fi

# Check if there are new commits
REMOTE_COMMIT=$(git rev-parse "origin/$BRANCH" 2>/dev/null | cut -c1-8)
log_msg "INFO" "Remote commit: $REMOTE_COMMIT"

if [[ "$LOCAL_COMMIT" == "$REMOTE_COMMIT" ]]; then
  log_msg "INFO" "✓ Already up-to-date, no deployment needed"
  exit 0
fi

# Pull changes
log_msg "INFO" "⬇️ Pulling changes from origin/$BRANCH..."
if ! git pull origin "$BRANCH"; then
  log_msg "ERROR" "Failed to pull from remote"
  exit 1
fi

NEW_COMMIT=$(git rev-parse HEAD 2>/dev/null | cut -c1-8)
log_msg "SUCCESS" "✓ Pulled successfully (now at $NEW_COMMIT)"

# Check if docker-compose file exists
if [[ ! -f "$COMPOSE_FILE" ]]; then
  log_msg "ERROR" "Compose file not found: $COMPOSE_FILE"
  exit 1
fi

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
  log_msg "ERROR" "Docker daemon not running"
  exit 1
fi

log_msg "INFO" "Building Docker images..."
if ! docker-compose -f "$COMPOSE_FILE" build --no-cache; then
  log_msg "ERROR" "Docker build failed"
  exit 1
fi

log_msg "INFO" "⬆️ Stopping old containers..."
if ! docker-compose -f "$COMPOSE_FILE" down; then
  log_msg "WARN" "Failed to stop containers gracefully, continuing..."
fi

log_msg "INFO" "🚀 Starting new containers..."
if ! docker-compose -f "$COMPOSE_FILE" up -d; then
  log_msg "ERROR" "Failed to start containers"
  exit 1
fi

# Wait for services to be healthy
log_msg "INFO" "Waiting for services to be healthy..."
WAIT_COUNT=0
while [[ $WAIT_COUNT -lt $RESTART_TIMEOUT ]]; do
  if docker-compose -f "$COMPOSE_FILE" exec -T api curl -f http://localhost:8000/api/health >/dev/null 2>&1; then
    log_msg "SUCCESS" "✓ API is healthy"
    break
  fi
  sleep 1
  ((WAIT_COUNT++))
done

if [[ $WAIT_COUNT -ge $RESTART_TIMEOUT ]]; then
  log_msg "ERROR" "API failed to become healthy within ${RESTART_TIMEOUT}s"
  exit 1
fi

log_msg "SUCCESS" "========== DEPLOYMENT SUCCESSFUL =========="
log_msg "INFO" "Containers running:"
docker-compose -f "$COMPOSE_FILE" ps | tee -a "$LOG_FILE"

# Clean up old images
log_msg "INFO" "Cleaning up old images..."
docker image prune -f --filter "dangling=true" >/dev/null 2>&1 || true

exit 0
