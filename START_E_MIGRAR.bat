@echo off
echo ========================================
echo  SUBINDO AMBIENTE E EXECUTANDO MIGRATION
echo ========================================
echo.

cd d:\Projetos\business-intelligence

echo [1/4] Verificando Docker...
docker --version
if %ERRORLEVEL% NEQ 0 (
    echo ERRO: Docker não encontrado!
    pause
    exit /b 1
)
echo ✓ Docker encontrado
echo.

echo [2/4] Subindo containers...
docker-compose up -d
echo ✓ Containers iniciados
echo.

echo [3/4] Aguardando API ficar pronta (30 segundos)...
timeout /t 30 /nobreak > nul
echo ✓ API pronta
echo.

echo [4/4] Executando migration de sincronizacao...
curl -X POST http://localhost:8000/api/v1/admin/run-sync-migration
echo.
echo.

echo ========================================
echo  VERIFICANDO RESULTADO
echo ========================================
echo.

echo Testando endpoint de health...
curl http://localhost:8000/api/v1/synchronization/health
echo.
echo.

echo ========================================
echo  CONCLUIDO!
echo ========================================
echo.
echo API: http://localhost:8000
echo Docs: http://localhost:8000/docs
echo.
echo Para ver logs: docker logs bi_api -f
echo Para parar: docker-compose down
echo.

pause
