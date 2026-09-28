# PowerShell Automated GitHub Push Helper
# Repository: https://github.com/lokanathvenkateshsarakanam/bank-transaction-anomaly-flagger

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  BANK TRANSACTION ANOMALY FLAGGER - GITHUB SYNC UTILITY        " -ForegroundColor Cyan
Write-Host "  Profile: https://github.com/lokanathvenkateshsarakanam       " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if gh CLI is authenticated
$ghStatus = gh auth status 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[1/2] GitHub CLI is authenticated!" -ForegroundColor Green
    Write-Host "[2/2] Creating remote repository and pushing..." -ForegroundColor Yellow
    gh repo create bank-transaction-anomaly-flagger --public --source=. --remote=origin --push
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "SUCCESS: Repository pushed to https://github.com/lokanathvenkateshsarakanam/bank-transaction-anomaly-flagger" -ForegroundColor Green
        exit 0
    }
}

Write-Host "Choose authentication method to push to GitHub:" -ForegroundColor Yellow
Write-Host "1. Interactive Browser Login via GitHub CLI (Recommended)"
Write-Host "2. Enter GitHub Personal Access Token (PAT)"
Write-Host "3. Standard Git Push (uses Windows browser prompt)"
$choice = Read-Host "Select option (1, 2, or 3)"

if ($choice -eq "1") {
    gh auth login -h github.com -p https -w
    gh repo create bank-transaction-anomaly-flagger --public --source=. --remote=origin --push
} elseif ($choice -eq "2") {
    $token = Read-Host "Paste your GitHub Personal Access Token (PAT)" -AsSecureString
    $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($token)
    $plainToken = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
    
    # Create repo via GitHub API
    $headers = @{
        "Authorization" = "token $plainToken"
        "Accept" = "application/vnd.github.v3+json"
        "User-Agent" = "BankAnomalyFlagger"
    }
    $body = @{
        "name" = "bank-transaction-anomaly-flagger"
        "description" = "Bank Transaction Anomaly Flagger with DMGT U1/U2, AI U1, ADSA U2, OOPJ, Bottle, Snowflake, Java, COBOL, Fortran, SQL, and High Security Suite"
        "private" = $false
    } | ConvertTo-Json

    try {
        Invoke-RestMethod -Uri "https://api.github.com/user/repos" -Method Post -Headers $headers -Body $body -ContentType "application/json" | Out-Null
        Write-Host "Remote repository created on GitHub!" -ForegroundColor Green
    } catch {
        Write-Host "Note: Repository might already exist on GitHub." -ForegroundColor Gray
    }

    # Push with token
    $pushUrl = "https://lokanathvenkateshsarakanam:$plainToken@github.com/lokanathvenkateshsarakanam/bank-transaction-anomaly-flagger.git"
    git push -u $pushUrl main
    git remote set-url origin "https://github.com/lokanathvenkateshsarakanam/bank-transaction-anomaly-flagger.git"
    Write-Host "Pushed successfully to https://github.com/lokanathvenkateshsarakanam/bank-transaction-anomaly-flagger" -ForegroundColor Green
} else {
    git push -u origin main
}
