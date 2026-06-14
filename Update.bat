@echo off
title Architech ArchiCAD MCP - Update
echo Please make sure ArchiCAD is CLOSED before updating.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0update.ps1"
echo.
pause
