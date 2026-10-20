# Install MoneyPrinterTurbo (official PyPI package "mpt") into a dedicated venv and create a launcher (Windows).
# Pin mpt==1.3.8 for Codex integration. Install dir defaults to C:\mpt; override with $env:MPT_DIR.
# Keep this file ASCII-only: Windows PowerShell 5.1 reads BOM-less scripts in the ANSI code page.
# Run: powershell -ExecutionPolicy Bypass -File scripts\install.ps1

function Fail($msg) {
    Write-Host $msg -ForegroundColor Red
    exit 1
}

$MptDir = if ($env:MPT_DIR) { $env:MPT_DIR } else { 'C:\mpt' }

# Non-ASCII characters or spaces in the path break MoneyPrinterTurbo on Windows
if ($MptDir -cnotmatch '^[A-Za-z0-9:\\._-]+$') {
    Fail "Install path must be ASCII only (letters, digits, . _ -), no spaces: $MptDir"
}

function Find-Python {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($v in '3.11', '3.12', '3.13') {
            $exe = & py "-$v" -c "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $exe) { return $exe.Trim() }
        }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $exe = & python -c "import sys; print(sys.executable if sys.version_info >= (3, 11) else '')" 2>$null
        if ($LASTEXITCODE -eq 0 -and $exe) { return $exe.Trim() }
    }
    return $null
}

$Py = Find-Python
if (-not $Py) {
    Fail 'Python 3.11+ not found. Install it from https://www.python.org/downloads/ (check "Add python.exe to PATH").'
}

New-Item -ItemType Directory -Force -Path $MptDir | Out-Null
$VenvPy = Join-Path $MptDir '.venv\Scripts\python.exe'
if (-not (Test-Path $VenvPy)) {
    Write-Host "Creating venv: $MptDir\.venv ($Py)"
    & $Py -m venv (Join-Path $MptDir '.venv')
    if ($LASTEXITCODE -ne 0) { Fail 'venv creation failed.' }
}
& $VenvPy -m pip install --upgrade pip 'mpt==1.3.8'
if ($LASTEXITCODE -ne 0) { Fail 'pip install mpt failed.' }
& (Join-Path $MptDir '.venv\Scripts\mpt.exe') --version
& $VenvPy (Join-Path $PSScriptRoot 'install-locale.py')
if ($LASTEXITCODE -ne 0) { Fail 'Japanese UI installation failed.' }

$Overlay = Join-Path $MptDir 'codex_overlay'
New-Item -ItemType Directory -Force -Path $Overlay | Out-Null
Copy-Item -Path (Join-Path $PSScriptRoot '..\codex_overlay\*') -Destination $Overlay -Recurse -Force
& $VenvPy (Join-Path $PSScriptRoot 'patch-webui.py')
if ($LASTEXITCODE -ne 0) { Fail 'WebUI setup checklist installation failed.' }
$env:MPT_HOME = Join-Path $MptDir 'home'
$env:PYTHONPATH = $Overlay
$env:MPT_CODEX_APP_SERVER = '1'
& $VenvPy -c 'from app.config import config; config.app["llm_provider"] = "codex_app_server"; config.ui["language"] = "ja"; config.save_config()'
if ($LASTEXITCODE -ne 0) { Fail 'Codex provider configuration failed.' }

# Works without a system ffmpeg as long as the imageio-ffmpeg binary bundled with mpt runs
& $VenvPy -c 'import imageio_ffmpeg, subprocess; subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-version"], check=True, capture_output=True)'
if ($LASTEXITCODE -ne 0) { Fail 'Bundled ffmpeg check failed. Install ffmpeg and set [app] ffmpeg_path in config.toml.' }

# Generate the launcher here so it carries no Mark-of-the-Web from a downloaded zip
$Bat = Join-Path $MptDir 'MoneyPrinterTurbo.bat'
@'
@echo off
rem Start MoneyPrinterTurbo, or just open the browser if it is already running. Closing this window stops it.
cd /d "%~dp0"
set "MPT_HOME=%~dp0home"
set PYTHONUTF8=1
set "PYTHONPATH=%~dp0codex_overlay;%PYTHONPATH%"
set "MPT_CODEX_APP_SERVER=1"
where codex >nul 2>&1
if not %errorlevel%==0 (
  echo Codex CLI not found. Install Codex CLI and run codex login.
  exit /b 1
)
curl -fsS http://127.0.0.1:8501/_stcore/health >nul 2>&1
if %errorlevel%==0 (
  start "" http://127.0.0.1:8501
  exit /b 0
)
".venv\Scripts\mpt.exe" webui --host 127.0.0.1 --port 8501
'@ | Set-Content -Path $Bat -Encoding ASCII
Write-Host "Launcher: $Bat"

$Desktop = [Environment]::GetFolderPath('Desktop')
$Shell = New-Object -ComObject WScript.Shell
$Lnk = $Shell.CreateShortcut((Join-Path $Desktop 'MoneyPrinterTurbo.lnk'))
# Target cmd.exe rather than the .bat itself; Windows refuses to pin shortcuts to .bat files
$Lnk.TargetPath = Join-Path $env:WINDIR 'System32\cmd.exe'
$Lnk.Arguments = "/c `"$Bat`""
$Lnk.WorkingDirectory = $MptDir
$Lnk.Save()
Write-Host "Desktop shortcut: $(Join-Path $Desktop 'MoneyPrinterTurbo.lnk') (right-click > Pin to taskbar / Start)"
Write-Host "Data (MPT_HOME): $MptDir\home  Videos: $MptDir\home\storage\tasks\<task-id>\"
