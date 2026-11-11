@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*
set "floodlineExit=%ERRORLEVEL%"
if "%floodlineExit%"=="0" exit /b 0
powershell.exe -NoLogo -NoProfile -Command "if (-not [Console]::IsInputRedirected) { [void](Read-Host 'Press Enter to close this window') }"
exit /b %floodlineExit%
