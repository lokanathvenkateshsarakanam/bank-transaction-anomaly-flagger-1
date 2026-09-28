@echo off
title Push to GitHub - Bank Transaction Anomaly Flagger
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0push_to_github.ps1"
pause
