@echo off
chcp 65001 > nul
title 5 MILLION 3 TA VIRTUAL AGENT ISHCHI KLASTERI

echo ============================================================
echo   🚀 5 MILLION 3 TA VIRTUAL AGENT ISHGA TUSHMOQDA...
echo   1-Agent, 2-Agent va 3-Agent alohida oqimlarda parallel ishlaydi.
echo ============================================================

set MASTER_URL=http://127.0.0.1:8080

start "5 MILLION AGENT 1" cmd /k "set AGENT_ID=Agent_1&& python cluster_agent.py"
timeout /t 2 /nobreak > nul

start "5 MILLION AGENT 2" cmd /k "set AGENT_ID=Agent_2&& python cluster_agent.py"
timeout /t 2 /nobreak > nul

start "5 MILLION AGENT 3" cmd /k "set AGENT_ID=Agent_3&& python cluster_agent.py"

echo.
echo ✅ Barcha 3 ta Virtual Agent muvaffaqiyatli ishga tushirildi!
echo Boshqaruv Master Server orqali amalga oshiriladi.
echo.
pause
