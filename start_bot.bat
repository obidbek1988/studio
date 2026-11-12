@echo off
chcp 65001 > nul
title 5 MILLION TELEGRAM BOT (@Beshmillionagentbot)
cd /d D:\5millionbot
color 0A
echo =====================================================================
echo    5 MILLION PROMPTER - TELEGRAM BOTNI ISHGA TUSHIRISH
echo =====================================================================
:loop
echo [%date% %time%] Telegram bot ishga tushmoqda...
python telegram_bot.py
echo.
echo [AVTO-RESTART] Bot to'xtadi yoki uzildi. 5 soniyadan so'ng avtomatik qayta yondi...
timeout /t 5 /nobreak > nul
goto loop
