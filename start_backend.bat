@echo off
REM Restart backend server after migration
echo.
echo ================================================
echo Starting FastAPI Backend Server
echo ================================================
echo.

cd /d "C:\Users\santh\Downloads\physioclinic-backend (2) (1)\physioclinic-backend (2)\physioclinic-backend\physioclinic-backend"

echo Starting server on port 8000...
echo.

"C:\Users\santh\AppData\Local\Programs\Python\Python311\python.exe" main.py

pause
