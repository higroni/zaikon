@echo off
setlocal

set "BACKEND_PORT=8100"
set "FRONTEND_PORT=5173"

echo Stopping zAIkon servers...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ports = @(%BACKEND_PORT%, %FRONTEND_PORT%); foreach ($port in $ports) { $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -gt 0 }; if (-not $connections) { Write-Host \"No server listening on port ${port}.\"; continue }; $processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique; foreach ($processId in $processIds) { try { $process = Get-Process -Id $processId -ErrorAction Stop; Write-Host \"Stopping $($process.ProcessName) pid ${processId} on port ${port}.\"; Stop-Process -Id $processId -Force -ErrorAction Stop } catch { Write-Host \"Could not stop pid ${processId} on port ${port}: $($_.Exception.Message)\" } } }"

echo Done.

endlocal
