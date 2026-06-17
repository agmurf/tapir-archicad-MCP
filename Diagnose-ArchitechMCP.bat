@echo off
title Architech ArchiCAD MCP - Diagnostic
echo.
echo  ============================================================
echo    Architech ArchiCAD MCP - Diagnostic
echo  ============================================================
echo.
echo  This will check why Claude can't see ArchiCAD and save a
echo  report to your Desktop. It changes nothing on your PC.
echo.
echo  Please wait about 15 seconds...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { irm https://raw.githubusercontent.com/agmurf/tapir-archicad-MCP/master/diagnose.ps1 ^| iex } catch { Write-Host ('Could not download the diagnostic. Check the internet connection. ' + $_.Exception.Message) -ForegroundColor Red }"
echo.
echo  ------------------------------------------------------------
echo  Done. A file called 'Architech-Diagnostic-Report.txt' should
echo  now be on your Desktop. Please email that file back.
echo  ------------------------------------------------------------
echo.
pause
