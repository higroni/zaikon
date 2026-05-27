@echo off
setlocal

set "ROOT=%~dp0"
set "BACKEND_PORT=8100"
set "FRONTEND_PORT=5173"

echo Starting zAIkon servers...
echo Project root: %ROOT%

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$backend = Get-NetTCPConnection -LocalPort %BACKEND_PORT% -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -gt 0 }; if ($backend) { Write-Host 'Backend already listening on port %BACKEND_PORT%.' } else { $env:PYTHONPATH = '%ROOT%backend'; Start-Process -FilePath 'python' -ArgumentList @('-m','uvicorn','zaikon.main:app','--host','127.0.0.1','--port','%BACKEND_PORT%') -WorkingDirectory '%ROOT%' -WindowStyle Hidden -RedirectStandardOutput '%ROOT%backend-dev.log' -RedirectStandardError '%ROOT%backend-dev.err.log'; Write-Host 'Backend starting on http://127.0.0.1:%BACKEND_PORT%'; }"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$frontend = Get-NetTCPConnection -LocalPort %FRONTEND_PORT% -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -gt 0 }; if ($frontend) { Write-Host 'Frontend already listening on port %FRONTEND_PORT%.' } else { Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c','npm run dev -- --port %FRONTEND_PORT%') -WorkingDirectory '%ROOT%frontend' -WindowStyle Hidden -RedirectStandardOutput '%ROOT%frontend\vite-dev.log' -RedirectStandardError '%ROOT%frontend\vite-dev.err.log'; Write-Host 'Frontend starting on http://127.0.0.1:%FRONTEND_PORT%'; }"

echo.
echo zAIkon UI: http://127.0.0.1:%FRONTEND_PORT%/
echo Backend health: http://127.0.0.1:%BACKEND_PORT%/health
echo.
echo Logs:
echo   %ROOT%backend-dev.log
echo   %ROOT%backend-dev.err.log
echo   %ROOT%frontend\vite-dev.log
echo   %ROOT%frontend\vite-dev.err.log

endlocal
