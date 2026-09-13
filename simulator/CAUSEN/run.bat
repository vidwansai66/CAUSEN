@echo off
setlocal
set "PATH=C:\Users\ADMIN\AppData\Local\Programs\Python\Python312;C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\Scripts;%PATH%"

if not exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    python "%~dp0causen_ai_simulation\main.py" %*
) else (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "%~dp0causen_ai_simulation\main.py" %*
)
