#!/usr/bin/env bash
# Complete Production Deployment Setup
# Run this ONCE on a fresh Ubuntu/Debian server to set up auto-deployment

set -eo pipefail

CLAIM_DIR="${CLAIM_DIR:-/opt/claim}"
GITHUB_REPO="${GITHUB_REPO:-https://github.com/NoMadAndy/Claim.git}"
BRANCH="${BRANCH:-main}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_step() {
  echo -e "${GREEN}➜${NC} $*"
}

log_error() {
  echo -e "${RED}✗${NC} $*"
}

log_warn() {
  echo -e "${YELLOW}⚠${NC} $*"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
  log_error "This script must be run as root"
  exit 1
fi

log_step "Starting Claim Production Setup..."

# 1. Install dependencies
log_step "Installing system dependencies..."
apt-get update
apt-get install -y \
  git \
  curl \
  wget \
  docker.io \
  docker-compose \
  postgresql-client

# Enable Docker service
systemctl enable docker
systemctl start docker

# 2. Clone or update repository
if [[ -d "$CLAIM_DIR" ]]; then
  log_step "Updating existing repository at $CLAIM_DIR..."
  cd "$CLAIM_DIR"
  git fetch origin
  git reset --hard "origin/$BRANCH"
else
  log_step "Cloning repository to $CLAIM_DIR..."
  git clone --branch "$BRANCH" "$GITHUB_REPO" "$CLAIM_DIR"
  cd "$CLAIM_DIR"
fi

# 3. Set up environment file
if [[ ! -f "$CLAIM_DIR/.env" ]]; then
  log_step "Creating .env file..."
  cp "$CLAIM_DIR/.env.example" "$CLAIM_DIR/.env"
  log_warn "Please edit $CLAIM_DIR/.env with your configuration"
  log_warn "Especially: DB_PASSWORD, CORS_ORIGINS, DOMAIN"
fi

# 4. Make scripts executable
log_step "Making scripts executable..."
chmod +x "$CLAIM_DIR/tools/deploy.sh"
chmod +x "$CLAIM_DIR/tools/deploy-watcher.sh"

# 5. Set up systemd service
log_step "Installing systemd service..."
cp "$CLAIM_DIR/claim-watcher.service" /etc/systemd/system/
sed -i "s|/opt/claim|$CLAIM_DIR|g" /etc/systemd/system/claim-watcher.service

systemctl daemon-reload
systemctl enable claim-watcher.service

# 6. Run initial deployment
log_step "Running initial deployment..."
cd "$CLAIM_DIR"
bash "$CLAIM_DIR/tools/deploy.sh" || {
  log_error "Initial deployment failed"
  exit 1
}

# 7. Start the watcher service
log_step "Starting auto-deployment watcher..."
systemctl start claim-watcher.service

log_step ""
log_step "✓ Claim production setup complete!"
log_step ""
log_step "Next steps:"
log_step "1. Configure $CLAIM_DIR/.env"
log_step "2. Check service status: systemctl status claim-watcher"
log_step "3. Watch logs: journalctl -u claim-watcher -f"
log_step "4. Push changes to GitHub to trigger auto-deployment"
log_step ""

# Show deployment info
log_step "Current deployment status:"
systemctl status claim-watcher.service --no-pager || true

exit 0
