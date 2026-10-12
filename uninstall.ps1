# ==============================================================================
# jamovi-antigravity Uninstaller for Windows (PowerShell)
# A lightweight, one install and uninstall MCP setup connecting Google Antigravity to Jamovi Desktop.
# ==============================================================================

param (
    [switch]$PurgeRepo,
    [switch]$Test,
    [switch]$DryRun
)

$ErrorActionPreference = "SilentlyContinue"

Write-Host "------------------------------------------------------------"
Write-Host "jamovi-antigravity: Windows One-Click Uninstall"
Write-Host "A lightweight, one install and uninstall MCP setup connecting"
Write-Host "Google Antigravity to Jamovi Desktop."
Write-Host "------------------------------------------------------------"

$UserProfile = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::UserProfile)
$McpDest = Join-Path $UserProfile ".gemini\antigravity\mcp\jamovi"
$AgentDest = Join-Path $UserProfile ".gemini\config\agents\jamovi-analyst.md"
$ScratchDest = Join-Path $UserProfile ".gemini\antigravity\scratch"

$ScriptDir = ""
if ($MyInvocation.MyCommand.Path) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

if ($Test -or $DryRun) {
    Write-Host "[TEST MODE] Resolving cleanup targets:"
    Write-Host "  Target MCP directory:   $McpDest"
    Write-Host "  Target agent file:      $AgentDest"
    Write-Host "  Target scratch cleanup: $ScratchDest"
    if ($ScriptDir -and (Test-Path $ScriptDir)) {
        Write-Host "  Repository directory:   $ScriptDir"
    }
    Write-Host "  Purge repository:       $PurgeRepo"
    Write-Host "[TEST MODE] Verification passed. No files removed."
    exit 0
}

# 1. Remove MCP Directory
Write-Host "[1/4] Removing jamovi MCP Server from Antigravity..."
if (Test-Path $McpDest) {
    Remove-Item -Path $McpDest -Recurse -Force
    Write-Host "      Removed: $McpDest"
} else {
    Write-Host "      Not found (already clean): $McpDest"
}

# 2. Remove Agent File
Write-Host "[2/4] Removing jamovi-analyst Agent..."
if (Test-Path $AgentDest) {
    Remove-Item -Path $AgentDest -Force
    Write-Host "      Removed: $AgentDest"
} else {
    Write-Host "      Not found (already clean): $AgentDest"
}

# 3. Clean temporary scratch files and repository artifacts
Write-Host "[3/4] Cleaning temporary artifacts and test caches..."
if (Test-Path $ScratchDest) {
    Get-ChildItem -Path $ScratchDest -Filter "*jamovi*" | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $ScratchDest -Filter "active_regression_*" | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $ScratchDest -Filter "linear_regression_*" | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $ScratchDest -Filter "regression_plot_*" | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $ScratchDest -Filter "test_reg*" | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "      Cleaned scratch artifacts in: $ScratchDest"
}

if ($ScriptDir -and (Test-Path $ScriptDir)) {
    $ExamplesDir = Join-Path $ScriptDir "examples"
    if (Test-Path $ExamplesDir) {
        Get-ChildItem -Path $ExamplesDir -Include "*.omv", "*.html", "*.png" -Recurse | Remove-Item -Force -ErrorAction SilentlyContinue
    }
    Get-ChildItem -Path $ScriptDir -Filter "Rplots.pdf" | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $ScriptDir -Filter "__pycache__" -Recurse -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "      Cleaned local artifacts and caches in repository."
}

# 4. Post-removal verification & optional repository purge
Write-Host "[4/4] Verifying clean teardown..."
$VerifyClean = $true
if (Test-Path $McpDest) {
    Write-Host "      Error: MCP directory could not be removed: $McpDest"
    $VerifyClean = $false
}
if (Test-Path $AgentDest) {
    Write-Host "      Error: Agent file could not be removed: $AgentDest"
    $VerifyClean = $false
}

if ($PurgeRepo) {
    if ($ScriptDir -and (Test-Path $ScriptDir)) {
        Write-Host "      Purging repository: $ScriptDir"
        Remove-Item -Path $ScriptDir -Recurse -Force
        Write-Host "      Repository folder completely purged."
    }
}

Write-Host "------------------------------------------------------------"
if ($VerifyClean) {
    Write-Host "Teardown Complete!"
    Write-Host "All jamovi-antigravity configurations and files have been removed."
} else {
    Write-Host "Teardown finished with warnings. Review the log messages above."
}
Write-Host "------------------------------------------------------------"
