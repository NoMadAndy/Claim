#!/bin/bash

# Claim - Automatic Repository Sync Script
# This script automatically commits and pushes changes to the repository
# with a compressed changelog entry

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Claim Auto-Sync ===${NC}"

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo -e "${RED}Error: Not a git repository${NC}"
    exit 1
fi

# Get current date
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)

# Check for changes
if git diff-index --quiet HEAD --; then
    echo -e "${GREEN}No changes to commit${NC}"
    exit 0
fi

# Show changed files
echo -e "${BLUE}Changed files:${NC}"
git status --short

# Prompt for changelog message
echo -e "\n${BLUE}Enter a brief changelog message (one line):${NC}"
read -r CHANGELOG_MSG

if [ -z "$CHANGELOG_MSG" ]; then
    echo -e "${RED}Error: Changelog message cannot be empty${NC}"
    exit 1
fi

# Update CHANGELOG.md
if [ ! -f CHANGELOG.md ]; then
    echo "# Changelog" > CHANGELOG.md
    echo "" >> CHANGELOG.md
fi

# Add new entry to changelog
sed -i "3i\\${DATE} ${TIME}\n${CHANGELOG_MSG}\n" CHANGELOG.md

# Stage all changes
git add -A

# Commit with changelog message
COMMIT_MSG="${DATE}: ${CHANGELOG_MSG}"
git commit -m "$COMMIT_MSG"

echo -e "${GREEN}Committed: ${COMMIT_MSG}${NC}"

# Push to remote
echo -e "${BLUE}Pushing to remote...${NC}"
git push origin $(git branch --show-current)

echo -e "${GREEN}=== Sync Complete ===${NC}"
echo -e "${GREEN}Changelog updated and pushed to repository${NC}"
