# PowerShell Automated GitHub Push & Fork Sync Utility
# Profiles:
# 1. Main Profile: https://github.com/lokanathvenkateshsarakanam/bank-transaction-anomaly-flagger-1
# 2. Fork Profile: https://github.com/saitejaavala946-jpg (Sai Teja Avala)

Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "  BANK TRANSACTION ANOMALY FLAGGER - GITHUB PUSH & FORK SYNC UTILITY       " -ForegroundColor Cyan
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "  Main Repo Profile : https://github.com/lokanathvenkateshsarakanam/bank-transaction-anomaly-flagger-1" -ForegroundColor Yellow
Write-Host "  Fork Repo Profile : https://github.com/saitejaavala946-jpg" -ForegroundColor Magenta
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host ""

# Ensure git remotes are properly configured
git remote remove origin 2>$null
git remote add origin https://github.com/lokanathvenkateshsarakanam/bank-transaction-anomaly-flagger-1.git
git remote remove fork 2>$null
git remote add fork https://github.com/saitejaavala946-jpg/bank-transaction-anomaly-flagger-1.git

Write-Host "Git Remotes Configured:" -ForegroundColor Green
git remote -v
Write-Host ""

Write-Host "Select an action to perform:" -ForegroundColor White
Write-Host "  [1] Interactive Web Login via GitHub CLI (gh auth login) & Push" -ForegroundColor Green
Write-Host "  [2] Push using GitHub Personal Access Token (PAT)" -ForegroundColor Yellow
Write-Host "  [3] Push using Standard Windows Git Credential Manager (Browser popup)" -ForegroundColor Cyan
Write-Host "  [4] Push directly to 'saitejaavala946-jpg' profile (Current Browser Account)" -ForegroundColor Magenta
Write-Host "  [5] Push to BOTH accounts (lokanathvenkateshsarakanam & saitejaavala946-jpg)" -ForegroundColor Blue
Write-Host "  [6] Open 1-Click Fork page in default browser" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter option number (1-6)"

switch ($choice) {
    "1" {
        Write-Host "`nLaunching GitHub interactive login..." -ForegroundColor Yellow
        gh auth login -h github.com -p https -w
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Pushing to origin (lokanathvenkateshsarakanam)..." -ForegroundColor Green
            git push -u origin main
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
        }
    }

    "3" {
        Write-Host "`nPushing to origin main via Git Credential Manager..." -ForegroundColor Yellow
        git push -u origin main
    }

    "4" {
        Write-Host "`nChecking if repository exists on saitejaavala946-jpg..." -ForegroundColor Yellow
        gh auth status 2>$null
        if ($LASTEXITCODE -eq 0) {
            gh repo create saitejaavala946-jpg/bank-transaction-anomaly-flagger-1 --public --source=. --remote=fork --push
        } else {
            Write-Host "Pushing to fork remote (saitejaavala946-jpg)..." -ForegroundColor Yellow
            git push -u fork main
        }
    }

    "5" {
        Write-Host "`nPushing to Origin (lokanathvenkateshsarakanam)..." -ForegroundColor Yellow
        git push -u origin main
        Write-Host "`nPushing to Fork (saitejaavala946-jpg)..." -ForegroundColor Magenta
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

Write-Host "`nDone." -ForegroundColor Cyan
