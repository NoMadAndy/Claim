#!/bin/bash

# Claim - Automatic Repository Sync Script
# This script automatically commits and pushes changes to the repository
# with automatic commit messages based on changed files
#
# Usage:
#   ./auto_sync.sh              # Single sync
#   ./auto_sync.sh 10           # Watch mode: sync every 10 seconds
#   ./auto_sync.sh 0            # Watch mode: sync as fast as possible

set -e

# Parse arguments
WATCH_MODE=false
INTERVAL=0

if [ $# -gt 0 ]; then
    INTERVAL=$1
    WATCH_MODE=true
fi

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to perform single sync
do_sync() {
    echo -e "${BLUE}=== Claim Auto-Sync ===  $(date '+%Y-%m-%d %H:%M:%S') ===${NC}"
    
    # Check if we're in a git repository
    if [ ! -d .git ]; then
        echo -e "${RED}Error: Not a git repository${NC}"
        return 1
    fi

    # Get current date and time
    DATE=$(date +%Y-%m-%d)
    TIME=$(date +%H:%M:%S)
    DATETIME="${DATE} ${TIME}"

    # Check for changes
    if git diff-index --quiet HEAD --; then
        echo -e "${GREEN}✓ No changes to commit${NC}"
        return 0
    fi

    # Show changed files
    echo -e "${BLUE}Changed files:${NC}"
    git status --short

    # Get list of modified files
    CHANGED_FILES=$(git diff-index --name-only HEAD --)
    FILE_COUNT=$(echo "$CHANGED_FILES" | wc -l)

    echo -e "\n${YELLOW}Files changed: ${FILE_COUNT}${NC}"

    # Get a summary of changes (added/modified/deleted)
    SUMMARY=$(git diff --stat HEAD -- | tail -1 | tr -d ' ')

    # Auto-generate commit message based on changed files
    # Extract the most significant changes
    MAIN_FILES=$(echo "$CHANGED_FILES" | grep -E '\.(js|py|html|css)$' | head -3)

    if [ -z "$MAIN_FILES" ]; then
        MAIN_FILES=$(echo "$CHANGED_FILES" | head -3)
    fi

    # Build commit message from file changes
    COMMIT_MSG="${DATE} ${TIME}:"
    FILE_LIST=""
    while IFS= read -r file; do
        if [ ! -z "$file" ]; then
            # Get just the filename without path
            FILENAME=$(basename "$file")
            if [ -z "$FILE_LIST" ]; then
                FILE_LIST=" ${FILENAME}"
            else
                FILE_LIST="${FILE_LIST}, ${FILENAME}"
            fi
        fi
    done <<< "$MAIN_FILES"

    COMMIT_MSG="${COMMIT_MSG}${FILE_LIST}"

    # Create detailed changelog entry with timestamp and file list
    ENTRY="## ${DATETIME}"
    ENTRY="${ENTRY}\n**Files:** ${SUMMARY}"
    ENTRY="${ENTRY}\n**Modified:**"

    while IFS= read -r file; do
        if [ ! -z "$file" ]; then
            ENTRY="${ENTRY}\n- \`${file}\`"
        fi
    done <<< "$CHANGED_FILES"

    ENTRY="${ENTRY}\n"

    # Update CHANGELOG.md
    if [ ! -f CHANGELOG.md ]; then
        echo "# Changelog" > CHANGELOG.md
        echo "" >> CHANGELOG.md
    fi

    # Add new entry to changelog (insert after the header)
    sed -i "3i\\${ENTRY}" CHANGELOG.md

    # Stage all changes
    git add -A

    # Commit with auto-generated message
    git commit -m "$COMMIT_MSG"

    echo -e "${GREEN}✓ Committed: ${COMMIT_MSG}${NC}"
    echo -e "${GREEN}✓ Changelog updated${NC}"

    # Push to remote
    echo -e "${BLUE}Pushing to remote...${NC}"
    git push origin $(git branch --show-current)

    echo -e "${GREEN}=== Sync Complete ===${NC}"
    echo -e "${GREEN}✓ All changes synced to repository${NC}"
    return 0
}

# If watch mode is enabled
if [ "$WATCH_MODE" = true ]; then
    echo -e "${BLUE}Starting watch mode (interval: ${INTERVAL}s)${NC}"
    while true; do
        do_sync || true
        if [ "$INTERVAL" -gt 0 ]; then
            sleep "$INTERVAL"
        fi
    done
else
    # Single sync
    do_sync
fi
