[CmdletBinding()]
param(
    [ValidateRange(1025, 65535)][int]$Port = 8000,
    [switch]$Install,
    [switch]$SkipBuild,
    [switch]$Rebuild,
    [switch]$PrepareOnly,
    [switch]$Verify,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$taskRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "A project command failed ($LASTEXITCODE): $Executable" }
}
function Test-PythonDependencies {
    param([string]$Executable)
    $taskErrorPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $Executable -c 'import fastapi, uvicorn, pydantic, httpx, multipart, PIL, numpy, pandas, sklearn, shapely, pyproj, networkx' *> $null
        return $LASTEXITCODE -eq 0
    } catch { return $false } finally { $ErrorActionPreference = $taskErrorPreference }
}
function Find-ProjectPython {
    $taskCandidates = @()
    $taskVenv = Join-Path $taskRoot '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $taskVenv) {
        $taskCandidates += @{ Executable = $taskVenv; Arguments = @() }
    }
    $taskPy = Get-Command 'py.exe' -ErrorAction SilentlyContinue
    if ($taskPy) {
        $taskCandidates += @{ Executable = $taskPy.Source; Arguments = @('-3.12') }
        $taskCandidates += @{ Executable = $taskPy.Source; Arguments = @('-3') }
    }
    $taskSystemPython = Get-Command 'python.exe' -ErrorAction SilentlyContinue
    if ($taskSystemPython) {
        $taskCandidates += @{ Executable = $taskSystemPython.Source; Arguments = @() }
    }
    foreach ($taskCandidate in $taskCandidates) {
        $taskProbeArguments = $taskCandidate.Arguments + @('-c', 'import sys; sys.exit(1) if sys.version_info < (3, 12) else print(sys.executable)')
        $taskErrorPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            $taskResult = & $taskCandidate.Executable @taskProbeArguments 2>$null
            if ($LASTEXITCODE -eq 0 -and $taskResult -and (Test-Path -LiteralPath "$taskResult")) {
                return "$taskResult"
            }
        } catch { } finally { $ErrorActionPreference = $taskErrorPreference }
    }
    throw 'Python 3.12 or newer was not found. Install Python from https://www.python.org/downloads/windows/ with the Python launcher or Add to PATH option, then run start.bat again.'
}
function Test-AvailablePort {
    param([int]$Candidate)
    $taskListener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Candidate)
    $taskListener.Server.ExclusiveAddressUse = $true
    try {
        $taskListener.Start()
        return $true
    } catch [System.Net.Sockets.SocketException] { return $false } finally { $taskListener.Stop() }
}
$taskExit = 0
$taskLog = $null
$taskTranscript = $false
$taskBrowserJob = $null
Push-Location -LiteralPath $taskRoot
try {
    $taskLogs = Join-Path $taskRoot '.runtime\launcher-logs'
    New-Item -ItemType Directory -Path $taskLogs -Force | Out-Null
    $taskLog = Join-Path $taskLogs ('start-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '-' + $PID + '.log')
    Start-Transcript -LiteralPath $taskLog | Out-Null
    $taskTranscript = $true
    Write-Host 'Starting Floodline (synthetic CAA pilot).'
    if ($SkipBuild -and $Rebuild) { throw 'Use either -SkipBuild or -Rebuild, not both.' }
    if ($SkipBuild -and -not (Test-Path -LiteralPath (Join-Path $taskRoot 'frontend\dist\index.html'))) {
        throw 'The bundled interface is missing. Run start.bat -Rebuild with Node 22.12 or newer installed.'
    }
    $settingsFile = Join-Path $taskRoot '.env'
    $allowedSettings = @('APP_MODE', 'ADMIN_USERNAME', 'ADMIN_PASSWORD', 'DATABASE_URL', 'FLOODLINE_RUNTIME')
    if (Test-Path -LiteralPath $settingsFile) {
        foreach ($line in Get-Content -LiteralPath $settingsFile -Encoding UTF8) {
            if ($line.Trim().Length -eq 0 -or $line.TrimStart().StartsWith('#')) { continue }
            if ($line -notmatch '^([A-Z_]+)=(.*)$' -or $allowedSettings -notcontains $Matches[1]) {
                throw 'The .env file contains an unsupported setting. Use .env.example as the template.'
            }
            [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2].Trim().Trim('"').Trim("'"), 'Process')
        }
    }
    if (-not $PrepareOnly -and -not (Test-AvailablePort $Port)) {
        if ($PSBoundParameters.ContainsKey('Port')) {
            throw "Port $Port is already in use. Close that server or run start.bat -Port with an unused port, for example: start.bat -Port 8002."
        }
        $taskRequestedPort = $Port
        while ($Port -le 8020 -and -not (Test-AvailablePort $Port)) { $Port++ }
        if ($Port -gt 8020) { throw 'Ports 8000 through 8020 are in use. Run start.bat -Port with another unused port.' }
        Write-Host "Port $taskRequestedPort is in use; using port $Port."
    }
    $taskPython = Find-ProjectPython
    Write-Host "Python: $taskPython"
    if ($Install -or -not (Test-PythonDependencies $taskPython)) {
        Write-Host 'Installing pinned Python dependencies. The first setup needs internet access.'
        $taskVenvPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
        if (-not (Test-Path -LiteralPath $taskVenvPython) -or $taskPython -ne $taskVenvPython) {
            Invoke-Checked $taskPython @('-m', 'venv', '.venv')
        }
        $taskPython = $taskVenvPython
        try {
            Invoke-Checked $taskPython @('-m', 'ensurepip', '--upgrade')
            Invoke-Checked $taskPython @('-m', 'pip', 'install', '--disable-pip-version-check', '-r', 'backend/requirements.txt')
        } catch {
            throw 'Python dependency installation failed. Check your internet connection and the pip error above, then run start.bat -Install to retry.'
        }
        if (-not (Test-PythonDependencies $taskPython)) { throw 'Installed Python dependencies could not be loaded. See the startup log and retry start.bat -Install.' }
    }
    if ($Rebuild -or -not (Test-Path -LiteralPath 'frontend\dist\index.html')) {
        if ($SkipBuild) { throw 'The bundled interface is missing. Run start.bat -Rebuild with Node 22.12 or newer installed.' }
        if (-not (Get-Command 'npm.cmd' -ErrorAction SilentlyContinue)) {
            throw 'The interface needs a build. Install Node 22.12 or newer from https://nodejs.org/ and run start.bat -Rebuild, or use the release ZIP with its bundled interface.'
        }
        Push-Location -LiteralPath (Join-Path $taskRoot 'frontend')
        try {
            if ($Install -or -not (Test-Path -LiteralPath 'node_modules')) { Invoke-Checked 'npm.cmd' @('ci', '--no-fund') }
            Invoke-Checked 'npm.cmd' @('run', 'build')
        } finally { Pop-Location }
    } else {
        Write-Host 'Using the bundled interface. Node and npm are not needed.'
    }
    if (-not (Test-Path -LiteralPath 'frontend\dist\index.html')) { throw 'The interface build did not produce frontend/dist/index.html.' }
    $taskRuntime = if ($env:FLOODLINE_RUNTIME) { [System.IO.Path]::GetFullPath($env:FLOODLINE_RUNTIME) } else { Join-Path $taskRoot '.runtime' }
    if (-not $env:DATABASE_URL -and (Test-Path -LiteralPath (Join-Path $taskRuntime 'floodline.db'))) {
        $taskBackup = Join-Path $taskRuntime ('backups\before-launch-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.db')
        Invoke-Checked $taskPython @('-m', 'backend.floodline', 'backup', $taskBackup)
    }
    Invoke-Checked $taskPython @('-m', 'backend.floodline', 'migrate')
    Invoke-Checked $taskPython @('-m', 'backend.floodline', 'evaluate')
    if ($Verify) { Invoke-Checked $taskPython @('-m', 'unittest', 'discover', '-s', 'backend/tests', '-v') }
    if (-not $PrepareOnly) {
        Write-Host "Floodline synthetic pilot: http://127.0.0.1:$Port"
        Write-Host 'Press Ctrl+C to stop. Demo reports and subscriptions are retained.'
        if (-not $NoBrowser) {
            $taskBrowserJob = Start-Job -ArgumentList $Port -ScriptBlock {
                param([int]$BrowserPort)
                $taskAddress = "http://127.0.0.1:$BrowserPort"
                for ($taskAttempt = 0; $taskAttempt -lt 180; $taskAttempt++) {
                    try {
                        $taskHealth = Invoke-RestMethod -Uri "$taskAddress/api/health" -TimeoutSec 1
                        if ($taskHealth.status -eq 'ok' -and $taskHealth.mode -eq 'synthetic') {
                            Start-Process $taskAddress
                            return
                        }
                    } catch { }
                    Start-Sleep -Milliseconds 250
                }
            }
        }
        Invoke-Checked $taskPython @('-m', 'backend.floodline', 'serve', '--port', "$Port")
    } else {
        Write-Host 'Preparation complete. Run start.bat to open the dashboard.'
    }
} catch {
    $taskExit = 1
    Write-Host ''
    Write-Host 'Floodline could not start.' -ForegroundColor Red
    Write-Host $_.Exception.Message
    if ($taskLog) { Write-Host "Startup log: $taskLog" }
} finally {
    if ($taskBrowserJob) {
        Stop-Job -Job $taskBrowserJob -ErrorAction SilentlyContinue
        Remove-Job -Job $taskBrowserJob -Force -ErrorAction SilentlyContinue
    }
    if ($taskTranscript) { Stop-Transcript | Out-Null }
    Pop-Location
}
exit $taskExit
