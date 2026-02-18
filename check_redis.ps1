# Check if Redis is installed and accessible

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Redis Installation Checker" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if redis-server is in PATH
$redisInPath = Get-Command redis-server -ErrorAction SilentlyContinue

if ($redisInPath) {
    Write-Host "✓ Redis found in PATH" -ForegroundColor Green
    Write-Host "  Location: $($redisInPath.Source)" -ForegroundColor Gray
} else {
    Write-Host "✗ Redis not found in PATH" -ForegroundColor Red
    
    # Check common installation locations
    $commonPaths = @(
        "C:\Redis\redis-server.exe",
        "C:\Program Files\Redis\redis-server.exe",
        "C:\ProgramData\chocolatey\lib\redis-64\tools\redis-server.exe"
    )
    
    $found = $false
    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            Write-Host "✓ Redis found at: $path" -ForegroundColor Yellow
            Write-Host "  You need to add this to your PATH" -ForegroundColor Yellow
            $found = $true
            break
        }
    }
    
    if (-not $found) {
        Write-Host "`nRedis is not installed. Please:" -ForegroundColor Red
        Write-Host "1. Download from: https://github.com/microsoftarchive/redis/releases" -ForegroundColor White
        Write-Host "2. Install Redis-x64-3.0.504.msi" -ForegroundColor White
        Write-Host "3. Run this script again" -ForegroundColor White
    }
}

Write-Host "`n========================================`n" -ForegroundColor Cyan
