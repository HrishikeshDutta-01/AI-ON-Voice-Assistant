@echo off
echo Starting AI-ON Project...

echo Starting Backend...
start cmd /k "cd backend && python server.py"

timeout /t 3 >nul

echo Opening Frontend...
start http://127.0.0.1:5500

echo Done!