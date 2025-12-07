#!/bin/bash
# Inject git commit hash into version badge
# Run this before pushing to automatically update version info

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
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[info] Injecting version: $SHORT_HASH (from $COMMIT_HASH)"
echo "[info] Timestamp: $TIMESTAMP"

# Use Python for more reliable HTML manipulation
python3 << 'PYTHON_SCRIPT'
import sys
import re

index_file = sys.argv[1] if len(sys.argv) > 1 else ""
commit_hash = sys.argv[2] if len(sys.argv) > 2 else ""

try:
    with open(index_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the version-hash element with data-commit attribute
    pattern = r'id="version-hash"[^>]*title="Click to copy version"'
    replacement = f'id="version-hash" data-commit="{commit_hash}" title="Click to copy version"'
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"[success] Version injected successfully!")
        print(f"[info] Commit: {commit_hash[:8]}")
    else:
        print("[warn] No changes made (pattern not found)")
except Exception as e:
    print(f"[error] {e}")
    sys.exit(1)
PYTHON_SCRIPT

# Run Python script
python3 -c "
import sys
import re

index_file = '$INDEX_FILE'
commit_hash = '$COMMIT_HASH'

try:
    with open(index_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the version-hash element with data-commit attribute
    pattern = r'id=\"version-hash\"[^>]*title=\"Click to copy version\"'
    replacement = f'id=\"version-hash\" data-commit=\"{commit_hash}\" title=\"Click to copy version\"'
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'[success] Version injected!')
    else:
        print('[warn] Pattern not found in HTML')
except Exception as e:
    print(f'[error] {e}')
    exit(1)
"
