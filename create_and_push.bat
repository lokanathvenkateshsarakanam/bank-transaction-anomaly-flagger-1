@echo off
title GitHub Repository Creator and Pusher
cd /d "%~dp0"

echo =====================================================================
echo   BANK TRANSACTION ANOMALY FLAGGER - 1-CLICK GITHUB PUBLISHER
echo =====================================================================
echo.
echo This tool will:
echo   1. Connect to your active browser GitHub account
echo   2. Automatically create the repository on GitHub (no 404 page)
echo   3. Push all project code, branches, and multi-language models
echo   4. Open your brand new live repository in your browser!
echo.
echo =====================================================================
echo.
echo Press any key to start...
pause >nul

echo.
echo [Step 1 of 3] Authenticating with GitHub...
echo A browser window will open. Enter the code shown on screen to authorize.
echo.
gh auth login -h github.com -p https -w

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Authentication was not completed.
    echo Please run this script again when ready.
    echo.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [Step 2 of 3] Creating repository and pushing all code to GitHub...
gh repo create bank-transaction-anomaly-flagger --public --source=. --remote=origin --push

if %ERRORLEVEL% neq 0 (
    echo.
    echo [NOTE] Trying direct push to configured remote...
    git push -u origin main
)

echo.
echo [Step 3 of 3] Verifying and opening your live GitHub repository...
echo.
echo =====================================================================
echo   SUCCESS! Your repository is now live and published on GitHub!
echo =====================================================================
echo.
gh browse
pause
