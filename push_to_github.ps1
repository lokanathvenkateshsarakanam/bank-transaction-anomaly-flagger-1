# PowerShell Automated GitHub Push & Fork Sync Utility
# Profiles:
# 1. Main Profile: https://github.com/lokanathvenkateshsarakanam/bank-transaction-anomaly-flagger-1
# 2. Fork Profile: https://github.com/saitejaavala946-jpg (Sai Teja Avala)

Clear-Host
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "  BANK TRANSACTION ANOMALY FLAGGER - GITHUB PUSH & FORK UTILITY           " -ForegroundColor Cyan
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "  Main Account  : https://github.com/lokanathvenkateshsarakanam" -ForegroundColor Yellow
Write-Host "  Target Repo   : bank-transaction-anomaly-flagger-1" -ForegroundColor Yellow
Write-Host "  Browser Login : https://github.com/saitejaavala946-jpg (Sai Teja Avala)" -ForegroundColor Magenta
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host ""

# Ensure git remotes are properly configured
git remote remove origin 2>$null
git remote add origin https://github.com/lokanathvenkateshsarakanam/bank-transaction-anomaly-flagger-1.git
git remote remove fork 2>$null
git remote add fork https://github.com/saitejaavala946-jpg/bank-transaction-anomaly-flagger-1.git

Write-Host "Choose how you want to push to GitHub:" -ForegroundColor White
Write-Host ""
Write-Host "  [1] Push to 'lokanathvenkateshsarakanam' via Interactive Browser Login (Recommended)" -ForegroundColor Green
Write-Host "      -> Logs in as lokanathvenkateshsarakanam in browser, then pushes to main repo." -ForegroundColor Gray
Write-Host ""
Write-Host "  [2] Push to 'lokanathvenkateshsarakanam' using Personal Access Token (PAT)" -ForegroundColor Yellow
Write-Host "      -> Paste your token from https://github.com/settings/tokens" -ForegroundColor Gray
Write-Host ""
Write-Host "  [3] Push directly to 'saitejaavala946-jpg' (Your Current Logged-In Account)" -ForegroundColor Magenta
Write-Host "      -> Creates and pushes to https://github.com/saitejaavala946-jpg/bank-transaction-anomaly-flagger-1" -ForegroundColor Gray
Write-Host ""
Write-Host "  [4] Standard Git Push via Windows Credential Manager" -ForegroundColor Cyan
Write-Host "      -> Prompts Windows Git Credential Manager popup." -ForegroundColor Gray
Write-Host ""
Write-Host "  [5] Push to BOTH accounts" -ForegroundColor Blue
Write-Host ""
Write-Host "  [6] Open 1-Click Fork page in default browser" -ForegroundColor White
Write-Host "      -> https://github.com/lokanathvenkateshsarakanam/bank-transaction-anomaly-flagger-1/fork" -ForegroundColor Gray
Write-Host ""

$choice = Read-Host "Enter option number (1-6)"

switch ($choice) {
    "1" {
        Write-Host "`n[1/2] Authenticating with GitHub..." -ForegroundColor Yellow
        gh auth login -h github.com -p https -w
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n[2/2] Pushing to https://github.com/lokanathvenkateshsarakanam/bank-transaction-anomaly-flagger-1..." -ForegroundColor Green
            git push -u origin main
            if ($LASTEXITCODE -eq 0) {
                Write-Host "`nSUCCESS: Code pushed to main repository!" -ForegroundColor Green
                Write-Host "Opening Fork URL so you can fork into saitejaavala946-jpg in 1 click..." -ForegroundColor Cyan
                Start-Process "https://github.com/lokanathvenkateshsarakanam/bank-transaction-anomaly-flagger-1/fork"
            }
        }
    }

    "2" {
        $username = Read-Host "`nEnter GitHub Username (default: lokanathvenkateshsarakanam)"
        if ([string]::IsNullOrWhiteSpace($username)) { $username = "lokanathvenkateshsarakanam" }
        
        $token = Read-Host "Paste GitHub Personal Access Token (PAT)" -AsSecureString
        $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($token)
        $plainToken = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
        
        $pushUrl = "https://$($username):$($plainToken)@github.com/$($username)/bank-transaction-anomaly-flagger-1.git"
        Write-Host "Pushing to https://github.com/$username/bank-transaction-anomaly-flagger-1..." -ForegroundColor Yellow
        git push -u $pushUrl main
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`nSUCCESS: Code pushed to https://github.com/$username/bank-transaction-anomaly-flagger-1" -ForegroundColor Green
            Write-Host "Opening Fork URL in browser..." -ForegroundColor Cyan
            Start-Process "https://github.com/lokanathvenkateshsarakanam/bank-transaction-anomaly-flagger-1/fork"
        }
    }

    "3" {
        Write-Host "`nPushing to saitejaavala946-jpg repository..." -ForegroundColor Magenta
        # Check if repo exists via gh or push
        gh auth status 2>$null
        if ($LASTEXITCODE -eq 0) {
            gh repo create saitejaavala946-jpg/bank-transaction-anomaly-flagger-1 --public --source=. --remote=fork --push
        } else {
            git push -u fork main
        }
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`nSUCCESS: Repository live at https://github.com/saitejaavala946-jpg/bank-transaction-anomaly-flagger-1" -ForegroundColor Green
        }
    }

    "4" {
        Write-Host "`nPushing to origin main via Git Credential Manager..." -ForegroundColor Yellow
        git push -u origin main
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`nSUCCESS! Opening Fork URL..." -ForegroundColor Green
            Start-Process "https://github.com/lokanathvenkateshsarakanam/bank-transaction-anomaly-flagger-1/fork"
        }
    }

    "5" {
        Write-Host "`n[1/2] Pushing to Origin (lokanathvenkateshsarakanam)..." -ForegroundColor Yellow
        git push -u origin main
        Write-Host "`n[2/2] Pushing to Fork (saitejaavala946-jpg)..." -ForegroundColor Magenta
        git push -u fork main
    }

    "6" {
        $forkUrl = "https://github.com/lokanathvenkateshsarakanam/bank-transaction-anomaly-flagger-1/fork"
        Write-Host "`nOpening Fork URL: $forkUrl" -ForegroundColor Cyan
        Start-Process $forkUrl
    }

    default {
        Write-Host "Invalid option selected." -ForegroundColor Red
    }
}

Write-Host "`nPress any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
