#!/usr/bin/env bash
# ==============================================================================
# jamovi-antigravity Installer
# One-click setup script for macOS and Linux.
# Configures the jamovi MCP server and the jamovi-analyst Antigravity agent.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_MODE=false

for arg in "$@"; do
    if [ "$arg" == "--test" ]; then
        TEST_MODE=true
    fi
done

echo "------------------------------------------------------------"
echo "jamovi-antigravity: One-Click Setup"
echo "------------------------------------------------------------"

# 1. OS Detection
OS_TYPE="$(uname -s)"
echo "[1/5] Detecting Operating System: $OS_TYPE"

JAMOVI_FOUND=false
JAMOVI_PATH=""

if [ "$OS_TYPE" == "Darwin" ]; then
    if [ -d "/Applications/jamovi.app" ]; then
        JAMOVI_PATH="/Applications/jamovi.app"
        JAMOVI_FOUND=true
    elif [ -d "$HOME/Applications/jamovi.app" ]; then
        JAMOVI_PATH="$HOME/Applications/jamovi.app"
        JAMOVI_FOUND=true
    fi
elif [ "$OS_TYPE" == "Linux" ]; then
    if [ -d "/usr/lib/jamovi" ]; then
        JAMOVI_PATH="/usr/lib/jamovi"
        JAMOVI_FOUND=true
    elif [ -d "/opt/jamovi" ]; then
        JAMOVI_PATH="/opt/jamovi"
        JAMOVI_FOUND=true
    elif command -v flatpak >/dev/null 2>&1 && flatpak info org.jamovi.jamovi >/dev/null 2>&1; then
        JAMOVI_PATH="flatpak:org.jamovi.jamovi"
        JAMOVI_FOUND=true
    fi
fi

if [ "$JAMOVI_FOUND" = true ]; then
    echo "      Found jamovi Desktop at: $JAMOVI_PATH"
else
    echo "      Warning: jamovi Desktop was not found at standard locations."
    echo "      Please ensure jamovi is installed from https://www.jamovi.org"
fi

# 2. Python Environment Check
echo "[2/5] Checking Python environment..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "      Error: Python 3 is required but not found on PATH."
    exit 1
fi
PYTHON_VER="$(python3 --version)"
echo "      Using: $PYTHON_VER"

# 3. Deploy MCP Server into Antigravity
echo "[3/5] Installing MCP Server into Antigravity..."
MCP_DEST="$HOME/.gemini/antigravity/mcp/jamovi"
mkdir -p "$MCP_DEST"

cp -r "$SCRIPT_DIR/mcp/tools/"*.json "$MCP_DEST/"
cp "$SCRIPT_DIR/mcp/server.py" "$MCP_DEST/"
cp "$SCRIPT_DIR/mcp/jamovi_bridge.py" "$MCP_DEST/"
if [ -f "$SCRIPT_DIR/mcp/instructions.md" ]; then
    cp "$SCRIPT_DIR/mcp/instructions.md" "$MCP_DEST/"
fi
chmod +x "$MCP_DEST/server.py"
echo "      MCP tools deployed to: $MCP_DEST"

# 4. Deploy jamovi-analyst Agent
echo "[4/5] Installing jamovi-analyst Agent into Antigravity..."
AGENT_DEST="$HOME/.gemini/config/agents"
mkdir -p "$AGENT_DEST"

cp "$SCRIPT_DIR/agent/jamovi-analyst.md" "$AGENT_DEST/"
echo "      Agent deployed to: $AGENT_DEST/jamovi-analyst.md"

# 5. Verification Smoke Test
echo "[5/5] Running verification smoke test..."
SMOKE_TEST="$(python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR/mcp')
from jamovi_bridge import JamoviBridge
b = JamoviBridge()
print('FOUND' if b.is_available() else 'NOT_FOUND')
" 2>/dev/null || echo "ERROR")"

if [ "$SMOKE_TEST" == "FOUND" ]; then
    echo "      Success: jamovi statistical engine detected and operational."
else
    echo "      Note: jamovi engine test returned ($SMOKE_TEST). Ensure jamovi Desktop is installed."
fi

echo "------------------------------------------------------------"
echo "Installation Complete!"
echo "------------------------------------------------------------"
echo "How to use:"
echo "1. In Antigravity, call the agent using: @jamovi-analyst"
echo "2. Share your dataset (.csv, .xlsx, or .omv) or paste data."
echo "3. Ask: 'Run a Pearson correlation between study_hours and exam_score.'"
echo "4. The agent will output official APA tables, generate downloadable .omv and HTML files, and launch jamovi Desktop."
echo "------------------------------------------------------------"
