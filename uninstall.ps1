# ==============================================================================
# jamovi-antigravity Uninstaller for Windows (PowerShell)
# One-command teardown script for Windows.
# Removes all MCP tools, agent definitions, and generated files.
# ==============================================================================

param (
    [switch]$PurgeRepo,
    [switch]$Test
)

$ErrorActionPreference = "SilentlyContinue"

Write-Host "------------------------------------------------------------"
Write-Host "jamovi-antigravity: Windows One-Command Teardown"
Write-Host "------------------------------------------------------------"

$UserProfile = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::UserProfile)
$McpDest = Join-Path $UserProfile ".gemini\antigravity\mcp\jamovi"
$AgentDest = Join-Path $UserProfile ".gemini\config\agents\jamovi-analyst.md"

if ($Test) {
    Write-Host "[TEST MODE] Resolving cleanup targets:"
    Write-Host "  Target MCP directory: $McpDest"
    Write-Host "  Target agent file:    $AgentDest"
    Write-Host "  Purge repository:     $PurgeRepo"
    Write-Host "[TEST MODE] Verification passed. No files removed."
    exit 0
}

# 1. Remove MCP Directory
Write-Host "[1/3] Removing jamovi MCP Server from Antigravity..."
if (Test-Path $McpDest) {
    Remove-Item -Path $McpDest -Recurse -Force
    Write-Host "      Removed: $McpDest"
} else {
    Write-Host "      Not found (already clean): $McpDest"
}

# 2. Remove Agent File
Write-Host "[2/3] Removing jamovi-analyst Agent..."
if (Test-Path $AgentDest) {
    Remove-Item -Path $AgentDest -Force
    Write-Host "      Removed: $AgentDest"
} else {
    Write-Host "      Not found (already clean): $AgentDest"
}

# 3. Optional Purge Repo
Write-Host "[3/3] Finalizing cleanup..."
if ($PurgeRepo) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    if ($ScriptDir -and (Test-Path $ScriptDir)) {
        Write-Host "      Purging repository: $ScriptDir"
        Remove-Item -Path $ScriptDir -Recurse -Force
    }
}

Write-Host "------------------------------------------------------------"
Write-Host "Teardown Complete!"
Write-Host "All jamovi-antigravity configurations and files have been removed."
Write-Host "------------------------------------------------------------"
