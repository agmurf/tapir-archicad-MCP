# =============================================================================
#  Architech ArchiCAD MCP - Diagnostic
#  Checks why Claude Desktop can't see ArchiCAD and writes a plain-English
#  report to the Desktop that you can email back for help.
#
#  Run by double-clicking Diagnose-ArchitechMCP.bat, or from PowerShell:
#     irm https://raw.githubusercontent.com/agmurf/tapir-archicad-MCP/master/diagnose.ps1 | iex
#  No admin rights needed. It only reads things and briefly test-launches the
#  server - it changes nothing on the PC.
# =============================================================================
$ErrorActionPreference = 'Continue'

$InstallDir = 'C:\ArchitechMCP'
$Server     = Join-Path $InstallDir '.venv\Scripts\archicad-server.exe'
$CfgDir     = Join-Path $env:APPDATA 'Claude'
$Cfg        = Join-Path $CfgDir 'claude_desktop_config.json'
$LogsDir    = Join-Path $CfgDir 'logs'

$report = New-Object System.Collections.Generic.List[string]
$fails  = New-Object System.Collections.Generic.List[string]

function Out2($msg, $color = 'Gray') { Write-Host $msg -ForegroundColor $color; $report.Add($msg) | Out-Null }
function Head($msg) { Out2 ''; Out2 ('==================================================') 'Cyan'; Out2 ("  $msg") 'Cyan'; Out2 ('==================================================') 'Cyan' }
function Pass($msg) { Out2 ("  [ OK ]   $msg") 'Green' }
function Fail($msg) { Out2 ("  [PROBLEM] $msg") 'Red'; $fails.Add($msg) | Out-Null }
function Info($msg) { Out2 ("           $msg") 'DarkGray' }

Head 'Architech ArchiCAD MCP - Diagnostic'
Out2 ("  Date:     " + (Get-Date))
Out2 ("  Computer: " + $env:COMPUTERNAME)
Out2 ("  User:     " + $env:USERNAME)

# ---------------------------------------------------------------------------
Head '1. Is the MCP installed on this PC?'
$installOk = $true
if (Test-Path $InstallDir) { Pass "Install folder found:  $InstallDir" }
else { Fail "Install folder is MISSING:  $InstallDir"; $installOk = $false }

if (Test-Path $Server) {
    Pass "Server program found:  $Server"
} else {
    Fail "Server program is MISSING:  $Server"
    Info "This usually means the installer did not finish (the dependency step failed)."
    $installOk = $false
}

if (Get-Command uv -ErrorAction SilentlyContinue) { Pass "Python toolchain (uv) is installed." }
else { Info "uv not on PATH (not always a problem if the server program exists)." }

# ---------------------------------------------------------------------------
Head '2. Is Claude Desktop pointed at the server?'
$cfgOk = $true
if (Test-Path $Cfg) {
    Pass "Claude Desktop config found:  $Cfg"
    try {
        $j = Get-Content $Cfg -Raw | ConvertFrom-Json
        $entry = $null
        if ($j.PSObject.Properties.Name -contains 'mcpServers') {
            $entry = $j.mcpServers.PSObject.Properties | Where-Object { $_.Name -eq 'ArchicadTapir' }
        }
        if ($entry) {
            Pass "Found the 'ArchicadTapir' entry in the config."
            $cmd = $entry.Value.command
            Info "It launches:  $cmd"
            if ($cmd -and (Test-Path $cmd)) { Pass "That program path exists." }
            else { Fail "The program the config points to does NOT exist: $cmd"; $cfgOk = $false }
        } else {
            Fail "The config has NO 'ArchicadTapir' entry - Claude Desktop has nothing to launch."
            Info "This is why Claude falls back to its built-in Linux sandbox."
            $cfgOk = $false
        }
    } catch {
        Fail "The config file exists but is not valid JSON (it may be corrupted)."
        Info $_.Exception.Message
        $cfgOk = $false
    }
} else {
    Fail "Claude Desktop config is MISSING:  $Cfg"
    Info "The installer did not write it, or Claude Desktop has never been run."
    $cfgOk = $false
}

# ---------------------------------------------------------------------------
Head '3. Does the server actually start? (8-second test launch)'
if (Test-Path $Server) {
    $errFile = Join-Path $env:TEMP 'architech_diag_err.txt'
    $outFile = Join-Path $env:TEMP 'architech_diag_out.txt'
    Remove-Item $errFile, $outFile -ErrorAction SilentlyContinue
    try {
        $p = Start-Process $Server -PassThru -WindowStyle Hidden -RedirectStandardError $errFile -RedirectStandardOutput $outFile
        for ($i = 0; $i -lt 8 -and -not $p.HasExited; $i++) { Start-Sleep -Seconds 1 }
        if ($p.HasExited) {
            Fail "The server started but then crashed (exit code $($p.ExitCode))."
            $err = (Get-Content $errFile -ErrorAction SilentlyContinue -Tail 25) -join "`r`n"
            if ($err) { Info "Last error output:"; foreach ($l in ($err -split "`r`n")) { Out2 ("             > " + $l) 'DarkGray' } }
        } else {
            Pass "The server launched and kept running - it starts correctly."
            Stop-Process $p -Force -ErrorAction SilentlyContinue
        }
    } catch {
        Fail "Could not start the server program at all."
        Info $_.Exception.Message
    }
} else {
    Info "Skipped - the server program isn't installed (see section 1)."
}

# ---------------------------------------------------------------------------
Head '4. What does Claude Desktop''s own log say?'
$log = $null
if (Test-Path $LogsDir) {
    $log = Get-ChildItem $LogsDir -Filter '*ArchicadTapir*' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
}
if ($log) {
    Info ("Reading: " + $log.FullName)
    $tail = Get-Content $log.FullName -Tail 25 -ErrorAction SilentlyContinue
    if ($tail) { foreach ($l in $tail) { Out2 ("             | " + $l) 'DarkGray' } }
    else { Info "Log is empty." }
} else {
    Info "No ArchicadTapir log found yet (normal if Claude Desktop hasn't tried to start it)."
}

# ---------------------------------------------------------------------------
Head '5. Is ArchiCAD running right now?'
$ac = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.Name -like '*ARCHICAD*' -or $_.Name -like '*ArchiCAD*' }
if ($ac) { Pass ("ArchiCAD is running (" + (($ac | Select-Object -Expand Name -Unique) -join ', ') + ").") }
else { Info "ArchiCAD is not running. That's fine for this test, but it must be open (with a project) for Claude to actually control it." }

# ---------------------------------------------------------------------------
Head 'SUMMARY'
if ($fails.Count -eq 0) {
    Out2 "  Everything checks out on this PC." 'Green'
    Out2 "  If Claude still gives the 'Linux container' message, the most likely" 'Green'
    Out2 "  cause is simply that Claude Desktop wasn't FULLY restarted after install:" 'Green'
    Out2 "    - Right-click the Claude icon in the system tray (bottom-right) -> Quit." 'White'
    Out2 "    - Reopen Claude Desktop, then ask: 'What MCP tools do you have?'" 'White'
} else {
    Out2 "  Found $($fails.Count) problem(s):" 'Red'
    foreach ($f in $fails) { Out2 ("    - " + $f) 'Red' }
    Out2 '' 'White'
    if (-not $installOk) {
        Out2 "  MOST LIKELY FIX: the installer didn't finish. Re-run the installer and" 'Yellow'
        Out2 "  watch for a red error near the 'Installing dependencies' step." 'Yellow'
    } elseif (-not $cfgOk) {
        Out2 "  MOST LIKELY FIX: re-run the installer so it writes the Claude config," 'Yellow'
        Out2 "  then fully Quit and reopen Claude Desktop." 'Yellow'
    }
}

# ---------------------------------------------------------------------------
$reportPath = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Architech-Diagnostic-Report.txt'
try {
    ($report -join "`r`n") | Set-Content $reportPath -Encoding UTF8
    Out2 '' 'White'
    Out2 ('==================================================') 'Cyan'
    Out2 ("  A report was saved to your Desktop:") 'Cyan'
    Out2 ("    " + $reportPath) 'White'
    Out2 ("  Please EMAIL THAT FILE back so we can help.") 'Cyan'
    Out2 ('==================================================') 'Cyan'
} catch {
    Out2 ("Could not save the report file: " + $_.Exception.Message) 'Red'
}
