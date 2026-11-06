@echo off
chcp 65001 > nul
title 5 MILLION PROMPTER - CHROME BILAN ISHLATISH
cd /d D:\5millionbot
color 0B
echo =====================================================================
echo    5 MILLION PROMPTER - NOUTBUKDA BRAUZER BILAN ISHGA TUSHIRISH
echo =====================================================================
python process_5million_excel.py
echo.
pause
