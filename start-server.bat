@echo off
cd /d "%~dp0"
echo Starting local web server for Abbasi Auto Machinery...
echo Open http://localhost:8000 in your browser.
start http://localhost:8000/
python -m http.server 8000
pause
