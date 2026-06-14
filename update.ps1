# =============================================================================
#  Architech ArchiCAD MCP - update to the latest version from GitHub
#  Double-click Update.bat, or run this from PowerShell.
#  Pulls the newest server + add-on Adam has published, keeps your settings.
# =============================================================================
$ErrorActionPreference = 'Stop'

$GitHubUser = 'agmurf'
$RepoName   = 'tapir-archicad-MCP'
$Branch     = 'master'
$InstallDir = 'C:\ArchitechMCP'
$RepoZip = "https://github.com/$GitHubUser/$RepoName/archive/refs/heads/$Branch.zip"

function Say($m, $c = 'White') { Write-Host $m -ForegroundColor $c }
Say "`n==== Architech ArchiCAD MCP - Update ====`n" Cyan

if (-not (Test-Path $InstallDir)) {
    Say "Not installed yet. Run the installer first (Setup-Windows.bat)." Red
    return
}

# The add-on file is locked while ArchiCAD is open - ask to close it.
if (Get-Process Archicad -ErrorAction SilentlyContinue) {
    Say "Please CLOSE ArchiCAD first (so the add-on can be updated), then run Update again." Red
    return
}

Say "Downloading the latest version..." Yellow
$zip = Join-Path $env:TEMP 'architech_mcp_update.zip'
Invoke-WebRequest $RepoZip -OutFile $zip -UseBasicParsing
$ext = Join-Path $env:TEMP 'architech_update_extract'
if (Test-Path $ext) { Remove-Item $ext -Recurse -Force }
Expand-Archive $zip $ext -Force
$src = (Get-ChildItem $ext -Directory | Select-Object -First 1).FullName

Say "Applying the update (your settings and environment are kept)..." Yellow
robocopy $src $InstallDir /E /XD '.venv' '.git' /NFL /NDL /NJH /NJS /NC /NS /NP | Out-Null

$uv = (Get-Command uv -ErrorAction SilentlyContinue).Source
if (-not $uv) { $uv = "$env:USERPROFILE\.local\bin\uv.exe" }
Say "Refreshing dependencies..." Yellow
Push-Location $InstallDir
try { & $uv sync } finally { Pop-Location }

Say "`n==== Update complete ====`n" Green
Say "If the add-on changed, it will be used the next time you open ArchiCAD." White
Say "Restart Claude Desktop (fully quit and reopen) to load any new tools." White
Say ""
