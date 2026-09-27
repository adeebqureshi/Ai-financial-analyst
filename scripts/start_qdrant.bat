@echo off
REM Starts a local Qdrant server for local development on Windows (no Docker required).
REM Serves the REST API on http://localhost:6333 and gRPC on 6334.
REM Storage is persistent and lives in QDRANT_HOME\storage.

setlocal

if "%QDRANT_HOME%"=="" set "QDRANT_HOME=%USERPROFILE%\qdrant-server"

set "QDRANT_EXE=%QDRANT_HOME%\qdrant.exe"

if not exist "%QDRANT_EXE%" (
    echo [ERROR] qdrant.exe not found at "%QDRANT_EXE%".
    echo.
    echo Install the official Windows release once:
    echo   set QDRANT_HOME=%%USERPROFILE%%\qdrant-server
    echo   curl -L -o qdrant.zip https://github.com/qdrant/qdrant/releases/download/v1.19.1/qdrant-x86_64-pc-windows-msvc.zip
    echo   tar -xf qdrant.zip -C "%%QDRANT_HOME%%"
    exit /b 1
)

REM Wait for an already-running instance instead of failing on a port conflict.
REM A second instance cannot bind the WAL lock and would panic, so detect first.
set "QDRANT_UP=0"
if exist "%SystemRoot%\System32\curl.exe" (
    "%SystemRoot%\System32\curl.exe" -s -o NUL -m 3 "http://localhost:6333/" 2>nul
    if not errorlevel 1 set "QDRANT_UP=1"
) else (
    "%SystemRoot%\System32\netstat.exe" -ano 2>nul | findstr /r /c:"0.0.0.0:6333" /c:"[::]:6333" | findstr /c:"LISTENING" >nul
    if not errorlevel 1 set "QDRANT_UP=1"
)
if "%QDRANT_UP%"=="1" (
    echo [OK] Qdrant is already running at http://localhost:6333
    exit /b 0
)

echo [INFO] Starting Qdrant from "%QDRANT_HOME%"
echo [INFO] REST API : http://localhost:6333
echo [INFO] Dashboard : http://localhost:6333/dashboard
echo [INFO] Storage   : "%QDRANT_HOME%\storage"
echo [INFO] Press Ctrl+C to stop.
echo.

pushd "%QDRANT_HOME%"
"%QDRANT_EXE%"
set "EXITCODE=%ERRORLEVEL%"
popd

exit /b %EXITCODE%
