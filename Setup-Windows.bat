@echo off
title Architech ArchiCAD MCP - Setup
echo Starting setup. This downloads and configures everything - please wait.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
echo.
echo Setup finished. You can close this window.
pause
