@echo off
setlocal

REM Launch Weighbridge System + Cloudflare Tunnel for phone access

REM Start the main app minimized
start "" /MIN "%~dp0WeighbridgeSystem.exe"

REM Give it a few seconds to start
timeout /t 5 /nobreak >nul

REM Start cloudflared tunnel (shows URL in this window)
if exist "%~dp0cloudflared.exe" (
    "%~dp0cloudflared.exe" tunnel --url http://127.0.0.1:8000
) else (
    echo cloudflared.exe not found next to this bat!
    echo Copy cloudflared.exe to the same folder as this bat.
    pause
)

endlocal
