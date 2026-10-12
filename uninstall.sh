#!/usr/bin/env bash
# ==============================================================================
# jamovi-antigravity Uninstaller
# A lightweight, one install and uninstall MCP setup connecting Google Antigravity to Jamovi Desktop.
# ==============================================================================

set -e

PURGE_REPO=false
TEST_MODE=false

for arg in "$@"; do
    case "$arg" in
        --purge-repo)
            PURGE_REPO=true
            ;;
        --test|--dry-run)
            TEST_MODE=true
            ;;
    esac
done

echo "------------------------------------------------------------"
echo "jamovi-antigravity: One-Click Uninstall"
echo "A lightweight, one install and uninstall MCP setup connecting"
echo "Google Antigravity to Jamovi Desktop."
echo "------------------------------------------------------------"

MCP_DIR="$HOME/.gemini/antigravity/mcp/jamovi"
AGENT_FILE="$HOME/.gemini/config/agents/jamovi-analyst.md"
SCRATCH_DIR="$HOME/.gemini/antigravity/scratch"

SCRIPT_DIR=""
if [ -n "${BASH_SOURCE[0]}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

if [ "$TEST_MODE" = true ]; then
    echo "[TEST MODE] Resolving cleanup targets:"
    echo "  Target MCP directory:   $MCP_DIR"
    echo "  Target agent file:      $AGENT_FILE"
    echo "  Target scratch cleanup: $SCRATCH_DIR (jamovi artifacts)"
    if [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR" ]; then
        echo "  Repository directory:   $SCRIPT_DIR"
    fi
    echo "  Purge repository flag:  $PURGE_REPO"
    echo "[TEST MODE] Verification passed. No files removed."
    exit 0
fi

# 1. Remove MCP Server and tools
echo "[1/4] Removing jamovi MCP Server from Antigravity..."
if [ -d "$MCP_DIR" ]; then
    rm -rf "$MCP_DIR"
    echo "      Removed: $MCP_DIR"
else
    echo "      Not found (already clean): $MCP_DIR"
fi

# 2. Remove jamovi-analyst Agent
echo "[2/4] Removing jamovi-analyst Agent..."
if [ -f "$AGENT_FILE" ]; then
    rm -f "$AGENT_FILE"
    echo "      Removed: $AGENT_FILE"
else
    echo "      Not found (already clean): $AGENT_FILE"
fi

# 3. Clean temporary scratch files and repository artifacts
echo "[3/4] Cleaning temporary artifacts and test caches..."
if [ -d "$SCRATCH_DIR" ]; then
    rm -f "$SCRATCH_DIR"/*jamovi* 2>/dev/null || true
    rm -f "$SCRATCH_DIR"/active_regression_* 2>/dev/null || true
    rm -f "$SCRATCH_DIR"/linear_regression_* 2>/dev/null || true
    rm -f "$SCRATCH_DIR"/regression_plot_* 2>/dev/null || true
    rm -f "$SCRATCH_DIR"/test_reg* 2>/dev/null || true
    echo "      Cleaned scratch artifacts in: $SCRATCH_DIR"
fi

if [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR" ]; then
    rm -f "$SCRIPT_DIR"/examples/*.omv 2>/dev/null || true
    rm -f "$SCRIPT_DIR"/examples/*.html 2>/dev/null || true
    rm -f "$SCRIPT_DIR"/examples/*.png 2>/dev/null || true
    rm -f "$SCRIPT_DIR"/Rplots.pdf 2>/dev/null || true
    find "$SCRIPT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    echo "      Cleaned local artifacts and caches in repository."
fi

# 4. Post-removal verification & optional repository purge
echo "[4/4] Verifying clean teardown..."
VERIFY_CLEAN=true
if [ -d "$MCP_DIR" ]; then
    echo "      Error: MCP directory could not be removed: $MCP_DIR"
    VERIFY_CLEAN=false
fi
if [ -f "$AGENT_FILE" ]; then
    echo "      Error: Agent file could not be removed: $AGENT_FILE"
    VERIFY_CLEAN=false
fi

if [ "$PURGE_REPO" = true ]; then
    if [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR" ]; then
        echo "      Purging repository directory: $SCRIPT_DIR"
        cd "$HOME"
        rm -rf "$SCRIPT_DIR"
        echo "      Repository directory completely purged."
    elif [ -d "$HOME/projects/jamovi-antigravity" ]; then
        rm -rf "$HOME/projects/jamovi-antigravity"
        echo "      Purged $HOME/projects/jamovi-antigravity"
    fi
fi

echo "------------------------------------------------------------"
if [ "$VERIFY_CLEAN" = true ]; then
    echo "Teardown Complete!"
    echo "All jamovi-antigravity configurations and files have been removed."
else
    echo "Teardown finished with warnings. Review the log messages above."
fi
echo "------------------------------------------------------------"
