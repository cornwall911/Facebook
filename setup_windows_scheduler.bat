@echo off
chcp 65001 >nul
title إعداد الجدولة التلقائية كل 12 ساعة
echo ====================================================
echo   تثبيت مهمة التشغيل التلقائي كل 12 ساعة في الويندوز
echo ====================================================
echo.
echo جاري جدولة تشغيل fb_winner_scout كل 12 ساعة في الخلفية...

schtasks /create /tn "FacebookViralScout" /tr "\"%~dp0run_scout.bat\"" /sc hourly /mo 12 /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [✓] تم تفعيل الجدولة بنجاح!
    echo سيعمل البرنامج تلقائياً كل 12 ساعة ويسحب البوستات ويحدث الداش بورد وشيت الإكسيل.
) else (
    echo.
    echo [!] يرجى تشغيل هذا الملف كمسؤول (Run as Administrator) لتثبيت المهمة المجدولة.
)

echo.
pause
