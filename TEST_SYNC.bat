@echo off
echo ========================================
echo  TESTANDO ENDPOINTS DE SINCRONIZACAO
echo ========================================
echo.

echo [1] Health do Orchestrator:
curl -s http://localhost:8000/v1/synchronization/health
echo.
echo.

echo [2] Status do Scheduler:
curl -s http://localhost:8000/v1/synchronization/scheduler/status
echo.
echo.

echo [3] Lista de Jobs:
curl -s http://localhost:8000/v1/synchronization/jobs
echo.
echo.

echo [4] Metricas de Runtime:
curl -s http://localhost:8000/v1/synchronization/runtime
echo.
echo.

echo ========================================
echo  CONCLUIDO!
echo ========================================
echo.
echo Abra no navegador:
echo   - http://localhost:8000/docs
echo   - http://localhost:8000/v1/synchronization/health
echo.

pause
