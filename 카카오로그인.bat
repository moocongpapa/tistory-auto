@echo off
title Kakao Tistory Login Setup
cd /d "C:\Users\kws911004\.gemini\antigravity\scratch\tistory-auto"
echo ========================================================
echo   Kakao and Tistory Login Setup
echo ========================================================
echo   1. The browser window will open shortly.
echo   2. Please login with your Kakao Account on Tistory.
echo   3. After login is completed, return here and press [Enter].
echo ========================================================
echo.
"C:\Users\kws911004\.gemini\antigravity\scratch\tistory-auto\.venv\Scripts\python.exe" "scripts\setup_login.py"
echo.
echo ========================================================
echo   Session saved successfully! You can close this window.
echo ========================================================
pause
