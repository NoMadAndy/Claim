#!/bin/bash
# Setup git hooks for automatic version injection

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK_DIR="$PROJECT_ROOT/.git/hooks"

echo "Setting up git hooks..."

# Create pre-commit hook
cat > "$HOOK_DIR/pre-commit" << 'EOF'
#!/bin/bash
# Pre-commit hook: Auto-inject version before every commit

PROJECT_ROOT="$(git rev-parse --show-toplevel)"

# Run inject-version.sh
bash "$PROJECT_ROOT/tools/inject-version.sh"

# Stage the updated index.html if it was modified
git add "$PROJECT_ROOT/frontend/index.html" 2>/dev/null || true

exit 0
EOF

chmod +x "$HOOK_DIR/pre-commit"

echo "✓ Pre-commit hook installed"
echo "Version will now be automatically injected before every commit!"
