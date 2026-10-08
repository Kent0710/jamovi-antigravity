# ==============================================================================
# jamovi-antigravity Installer for Windows (PowerShell)
# One-click setup script for Windows.
# Configures the jamovi MCP server and the jamovi-analyst Antigravity agent.
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host "------------------------------------------------------------"
Write-Host "jamovi-antigravity: Windows One-Click Setup"
Write-Host "------------------------------------------------------------"

# 1. OS & Path Detection
Write-Host "[1/5] Detecting jamovi Desktop installation..."
$ProgramFiles = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::ProgramFiles)
$JamoviDirs = Get-ChildItem -Path $ProgramFiles -Filter "jamovi*" -Directory -ErrorAction SilentlyContinue

if ($JamoviDirs) {
    $JamoviPath = $JamoviDirs[0].FullName
    Write-Host "      Found jamovi Desktop at: $JamoviPath"
} else {
    Write-Host "      Warning: jamovi Desktop not found in Program Files."
    Write-Host "      Ensure jamovi is installed from https://www.jamovi.org"
}

# 2. Python Check
Write-Host "[2/5] Checking Python environment..."
try {
    $PythonVer = & python --version
    Write-Host "      Using: $PythonVer"
} catch {
    Write-Host "      Error: Python is required on PATH."
    exit 1
}

# 3. Deploy MCP Server into Antigravity
Write-Host "[3/5] Installing MCP Server into Antigravity..."
$UserProfile = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::UserProfile)
$McpDest = Join-Path $UserProfile ".gemini\antigravity\mcp\jamovi"

if (-not (Test-Path $McpDest)) {
    New-Item -ItemType Directory -Path $McpDest -Force | Out-Null
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Copy-Item (Join-Path $ScriptDir "mcp\tools\*.json") -Destination $McpDest -Force
Copy-Item (Join-Path $ScriptDir "mcp\server.py") -Destination $McpDest -Force
Copy-Item (Join-Path $ScriptDir "mcp\jamovi_bridge.py") -Destination $McpDest -Force
if (Test-Path (Join-Path $ScriptDir "mcp\instructions.md")) {
    Copy-Item (Join-Path $ScriptDir "mcp\instructions.md") -Destination $McpDest -Force
}
Write-Host "      MCP tools deployed to: $McpDest"

# 4. Deploy jamovi-analyst Agent
Write-Host "[4/5] Installing jamovi-analyst Agent into Antigravity..."
$AgentDest = Join-Path $UserProfile ".gemini\config\agents"
if (-not (Test-Path $AgentDest)) {
    New-Item -ItemType Directory -Path $AgentDest -Force | Out-Null
}

Copy-Item (Join-Path $ScriptDir "agent\jamovi-analyst.md") -Destination $AgentDest -Force
Write-Host "      Agent deployed to: $AgentDest\jamovi-analyst.md"

# 5. Smoke Test
Write-Host "[5/5] Running verification smoke test..."
Write-Host "------------------------------------------------------------"
Write-Host "Installation Complete!"
Write-Host "------------------------------------------------------------"
Write-Host "How to use:"
Write-Host "1. In Antigravity, call the agent using: @jamovi-analyst"
Write-Host "2. Share your dataset (.csv, .xlsx, or .omv) or paste data."
Write-Host "3. Ask: 'Run a Pearson correlation between study_hours and exam_score.'"
Write-Host "------------------------------------------------------------"
