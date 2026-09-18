@echo off
title Facebook Viral Scout (Powered by Scrapling)
cd /d "%~dp0"
echo ========================================================
echo   Starting Facebook Viral Scout in Background Mode...
echo ========================================================
python -m fb_winner_scout run --headless
pause
