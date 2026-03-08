#!/bin/bash
# ============================================================
# CodeTrellis Global Install Script
# ============================================================
# This script creates a global 'codetrellis' command that works
# from any directory without needing to activate the virtualenv.
#
# Usage:
#   chmod +x scripts/install-global.sh
#   ./scripts/install-global.sh
#
# After running, you can use from anywhere:
#   codetrellis scan /path/to/any/project
#   codetrellis scan /path/to/project --optimal
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="${PROJECT_DIR}/../.venv"

# Resolve absolute path
VENV_DIR="$(cd "$VENV_DIR" 2>/dev/null && pwd)" || true

echo "╔══════════════════════════════════════════════════╗"
echo "║       CodeTrellis Global Install                 ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Step 1: Find or create virtualenv
if [ ! -d "$VENV_DIR" ]; then
    VENV_DIR="${PROJECT_DIR}/.venv"
    if [ ! -d "$VENV_DIR" ]; then
        echo "[1/3] Creating virtualenv at ${VENV_DIR}..."
        python3 -m venv "$VENV_DIR"
    fi
fi

echo "[1/3] Using virtualenv: ${VENV_DIR}"

# Step 2: Install codetrellis in editable mode
echo "[2/3] Installing codetrellis in editable mode..."
"${VENV_DIR}/bin/pip" install -e "$PROJECT_DIR" --quiet

# Step 3: Create global symlink
INSTALL_DIR="/usr/local/bin"
SYMLINK_PATH="${INSTALL_DIR}/codetrellis"
CODETRELLIS_BIN="${VENV_DIR}/bin/codetrellis"

if [ ! -f "$CODETRELLIS_BIN" ]; then
    echo "ERROR: codetrellis binary not found at ${CODETRELLIS_BIN}"
    exit 1
fi

echo "[3/3] Creating global command..."

# Try /usr/local/bin first, fall back to ~/bin
if [ -w "$INSTALL_DIR" ] || sudo -n true 2>/dev/null; then
    if [ -w "$INSTALL_DIR" ]; then
        ln -sf "$CODETRELLIS_BIN" "$SYMLINK_PATH"
    else
        sudo ln -sf "$CODETRELLIS_BIN" "$SYMLINK_PATH"
    fi
    echo ""
    echo "✅ Installed! 'codetrellis' is now available globally."
    echo ""
else
    # Fallback: install to ~/bin
    INSTALL_DIR="$HOME/bin"
    SYMLINK_PATH="${INSTALL_DIR}/codetrellis"
    mkdir -p "$INSTALL_DIR"
    ln -sf "$CODETRELLIS_BIN" "$SYMLINK_PATH"

    echo ""
    echo "✅ Installed to ~/bin/codetrellis"
    echo ""

    # Check if ~/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
        echo "⚠️  Add ~/bin to your PATH by adding this to your ~/.zshrc:"
        echo ""
        echo "    export PATH=\"\$HOME/bin:\$PATH\""
        echo ""
        echo "Then run: source ~/.zshrc"
    fi
fi

echo "Usage:"
echo "  codetrellis scan /path/to/any/project"
echo "  codetrellis scan /path/to/project --optimal"
echo "  codetrellis scan . --tier full"
echo ""

# Verify
"$CODETRELLIS_BIN" --version
