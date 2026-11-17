@echo off
cd /d "%~dp0"
echo ==========================================================
echo Starting local web server for Abbasi Auto Machinery...
echo Website:     http://localhost:8000/
echo Admin Panel: http://localhost:8000/admin.html
echo ==========================================================
start http://localhost:8000/admin.html
start http://localhost:8000/
if exist server.py (
    python server.py 8000
) else (
    python -m http.server 8000
)
pause
