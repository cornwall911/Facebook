@echo off
chcp 65001 >nul
title Facebook Viral Scout (Powered by Scrapling)
cd /d "%~dp0"
echo ========================================================
echo   Starting Facebook Viral Scout with Scrapling Engine...
echo ========================================================

python -m fb_winner_scout run --headless --groups groups.txt

echo.
echo ========================================================
echo   Syncing new products to Cloudflare / GitHub Pages...
echo ========================================================
git add public/index.html index.html public/source_posts.json public/run_status.json data/reports/
git commit -m "chore(auto): harvest fresh viral products and update dashboard"
git push origin main

echo.
echo [✓] Done! Dashboard updated and pushed to live website.
