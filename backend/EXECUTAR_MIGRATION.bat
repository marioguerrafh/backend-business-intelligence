@echo off
echo ========================================
echo  EXECUTANDO MIGRATION DE SINCRONIZACAO
echo ========================================
echo.

cd d:\Projetos\business-intelligence\backend

echo Executando script Python...
python EXECUTAR_MIGRATION.py

echo.
echo Testando endpoint de health...
curl http://localhost:8000/api/v1/synchronization/health

echo.
echo ========================================
echo  MIGRATION CONCLUIDA
echo ========================================
echo.

pause
