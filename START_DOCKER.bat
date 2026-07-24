@echo off
echo ========================================
echo  INICIANDO AMBIENTE DOCKER
echo ========================================
echo.

cd d:\Projetos\business-intelligence

echo Verificando Docker...
docker --version
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERRO: Docker nao esta instalado ou nao esta em execucao.
    echo.
    echo Por favor:
    echo 1. Instale Docker Desktop: https://www.docker.com/products/docker-desktop
    echo 2. Inicie Docker Desktop
    echo 3. Execute este script novamente
    pause
    exit /b 1
)

echo.
echo Docker encontrado!
echo.

echo Parando containers existentes...
docker-compose down
echo.

echo Construindo e iniciando containers...
docker-compose up -d --build
echo.

echo Aguardando containers ficarem prontos...
timeout /t 10 /nobreak > nul
echo.

echo Status dos containers:
docker-compose ps
echo.

echo Logs da API:
docker-compose logs --tail=50 api
echo.

echo ========================================
echo  AMBIENTE INICIADO!
echo ========================================
echo.
echo API: http://localhost:8000
echo Docs: http://localhost:8000/docs
echo PostgreSQL: localhost:5432
echo.
echo Para ver logs em tempo real:
echo   docker-compose logs -f api
echo.
echo Para parar tudo:
echo   docker-compose down
echo.

pause
