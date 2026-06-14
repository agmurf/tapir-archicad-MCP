# =============================================================================
#  Architech ArchiCAD MCP - one-time Windows setup
#  Run from PowerShell:
#     irm https://raw.githubusercontent.com/agmurf/tapir-archicad-MCP/master/install.ps1 | iex
#  (or download the repo ZIP, extract it, and double-click Setup-Windows.bat)
#
#  Installs: uv (Python toolchain) -> the MCP server -> its dependencies ->
#  writes the Claude Desktop config -> pre-builds the AI search index.
#  Does NOT need admin rights. Safe to re-run (it updates in place).
# =============================================================================
$ErrorActionPreference = 'Stop'

# --- EDIT THESE IF YOU FORK/RENAME THE REPO -----------------------------------
$GitHubUser = 'agmurf'
$RepoName   = 'tapir-archicad-MCP'
$Branch     = 'master'
$InstallDir = 'C:\ArchitechMCP'
# -----------------------------------------------------------------------------
$RepoZip = "https://github.com/$GitHubUser/$RepoName/archive/refs/heads/$Branch.zip"

function Say($m, $c = 'White') { Write-Host $m -ForegroundColor $c }

Say "`n==============================================" Cyan
Say "  Architech ArchiCAD MCP - Setup" Cyan
Say "==============================================`n" Cyan

# 1) uv (installs & manages Python and the environment, no admin needed)
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Say "Installing the Python toolchain (uv)..." Yellow
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    $env:Path = "$env:USERPROFILE\.local\bin;" + $env:Path
}
$uv = (Get-Command uv -ErrorAction SilentlyContinue).Source
if (-not $uv) { throw "uv did not install correctly. Close this window and run the installer again." }

# 2) download the MCP server from GitHub
Say "Downloading the MCP server from GitHub..." Yellow
$zip = Join-Path $env:TEMP 'architech_mcp.zip'
Invoke-WebRequest $RepoZip -OutFile $zip -UseBasicParsing
$ext = Join-Path $env:TEMP 'architech_extract'
if (Test-Path $ext) { Remove-Item $ext -Recurse -Force }
Expand-Archive $zip $ext -Force
$src = (Get-ChildItem $ext -Directory | Select-Object -First 1).FullName

# 3) copy into place (keep any existing virtual environment if re-running)
New-Item -ItemType Directory -Force $InstallDir | Out-Null
robocopy $src $InstallDir /E /XD '.venv' '.git' /NFL /NDL /NJH /NJS /NC /NS /NP | Out-Null

# 4) install dependencies into a local environment
Say "Installing dependencies. First time can take 3-10 minutes - please wait..." Yellow
Push-Location $InstallDir
try { & $uv sync } finally { Pop-Location }
$server = Join-Path $InstallDir '.venv\Scripts\archicad-server.exe'
if (-not (Test-Path $server)) { throw "Setup failed: the server was not built at $server" }

# 5) point Claude Desktop at the server (merges in, keeps your other settings)
Say "Configuring Claude Desktop..." Yellow
$cfgDir = Join-Path $env:APPDATA 'Claude'
$cfg = Join-Path $cfgDir 'claude_desktop_config.json'
New-Item -ItemType Directory -Force $cfgDir | Out-Null
try {
    if (Test-Path $cfg) {
        Copy-Item $cfg "$cfg.bak" -Force
        $j = Get-Content $cfg -Raw | ConvertFrom-Json
    } else {
        $j = [pscustomobject]@{}
    }
    if (-not ($j.PSObject.Properties.Name -contains 'mcpServers')) {
        $j | Add-Member -NotePropertyName mcpServers -NotePropertyValue ([pscustomobject]@{})
    }
    $j.mcpServers | Add-Member -NotePropertyName 'ArchicadTapir' `
        -NotePropertyValue ([pscustomobject]@{ command = $server }) -Force
    $j | ConvertTo-Json -Depth 50 | Set-Content $cfg -Encoding UTF8
    Say "  Claude config updated (backup saved as claude_desktop_config.json.bak)." DarkGray
} catch {
    Say "  Could not auto-edit the Claude config. Add this to mcpServers manually:" Red
    Say "    `"ArchicadTapir`": { `"command`": `"$server`" }" Red
}

# 6) pre-build the AI search index so the first real use is fast (best effort).
#    The server builds + saves the index during startup; we just let it run a
#    couple of minutes, then stop it. If this is interrupted, the index simply
#    builds on first use instead (slower first reply, but it still works).
Say "Preparing the AI search index (one-time, ~2 minutes)..." Yellow
try {
    $pw = Start-Process $server -PassThru -WindowStyle Hidden
    for ($i = 0; $i -lt 200 -and -not $pw.HasExited; $i++) { Start-Sleep -Seconds 1 }
    if (-not $pw.HasExited) { Stop-Process $pw -Force -ErrorAction SilentlyContinue }
} catch { }

$apx = Join-Path $InstallDir 'addon\TapirAddOn_AC29_Win.apx'
Say "`n==============================================" Green
Say "  Setup complete!" Green
Say "==============================================`n" Green
Say "Now finish the 3 manual steps in SETUP-GUIDE.md (in $InstallDir):" White
Say "  1. In ArchiCAD: Options -> Add-On Manager -> Add this file:" White
Say "       $apx" Cyan
Say "  2. In ArchiCAD: File -> Libraries and Objects -> Library Manager -> add the standard ArchiCAD 29 library." White
Say "  3. Fully quit and reopen Claude Desktop, then ask: 'List my running ArchiCAD instances'." White
Say ""
