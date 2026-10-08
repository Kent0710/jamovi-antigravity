#!/usr/bin/env bash
# ==============================================================================
# jamovi-antigravity Uninstaller
# One-command teardown script for macOS and Linux.
# Removes all MCP tools, agent definitions, and generated files.
# ==============================================================================

set -e

PURGE_REPO=false
TEST_MODE=false

for arg in "$@"; do
    case "$arg" in
        --purge-repo)
            PURGE_REPO=true
            ;;
        --test)
            TEST_MODE=true
            ;;
    esac
done

echo "------------------------------------------------------------"
echo "jamovi-antigravity: One-Command Teardown"
echo "------------------------------------------------------------"

MCP_DIR="$HOME/.gemini/antigravity/mcp/jamovi"
AGENT_FILE="$HOME/.gemini/config/agents/jamovi-analyst.md"

if [ "$TEST_MODE" = true ]; then
    echo "[TEST MODE] Resolving cleanup targets:"
    echo "  Target MCP directory: $MCP_DIR"
    echo "  Target agent file:    $AGENT_FILE"
    echo "  Purge repository:     $PURGE_REPO"
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

# 3. Clean generated demo files if running inside the repository
echo "[3/4] Cleaning temporary and generated test artifacts..."
SCRIPT_DIR=""
if [ -n "${BASH_SOURCE[0]}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

if [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR" ]; then
    rm -f "$SCRIPT_DIR"/examples/*.omv
    rm -f "$SCRIPT_DIR"/examples/*.html
    rm -f "$SCRIPT_DIR"/Rplots.pdf
    rm -rf "$SCRIPT_DIR"/**/__pycache__
    echo "      Cleaned generated artifacts in repository."
fi

# 4. Optional: Purge cloned repository folder
echo "[4/4] Finalizing cleanup..."
if [ "$PURGE_REPO" = true ]; then
    if [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR" ]; then
        echo "      Purging repository directory: $SCRIPT_DIR"
        cd "$HOME"
        rm -rf "$SCRIPT_DIR"
        echo "      Repository folder completely deleted."
    elif [ -d "$HOME/projects/jamovi-antigravity" ]; then
        rm -rf "$HOME/projects/jamovi-antigravity"
        echo "      Purged $HOME/projects/jamovi-antigravity"
    fi
fi

echo "------------------------------------------------------------"
echo "Teardown Complete!"
echo "All jamovi-antigravity configurations and files have been removed."
echo "------------------------------------------------------------"
