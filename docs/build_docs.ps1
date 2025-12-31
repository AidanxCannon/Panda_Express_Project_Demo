# Build and view Sphinx documentation for PandaPOS Team52

Write-Host "Building HTML documentation..." -ForegroundColor Cyan

Set-Location $PSScriptRoot
& .\make.bat html

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Documentation built successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    $docPath = Join-Path $PSScriptRoot "_build\html\index.html"
    Write-Host "Opening documentation in browser..." -ForegroundColor Cyan
    Start-Process $docPath
    
    Write-Host ""
    Write-Host "Documentation location:" -ForegroundColor Yellow
    Write-Host $docPath
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Build failed! Check the errors above." -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
}
