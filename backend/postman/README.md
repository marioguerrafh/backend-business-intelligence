# Postman Pack - BI Platform

Arquivos deste pacote:

1. BI-Platform-APIs.postman_collection.json
2. BI-Platform-Local.postman_environment.json

Como importar no Postman:

1. Clique em Import.
2. Selecione os dois arquivos JSON.
3. Escolha o environment BI Platform Local.

Fluxo recomendado para validar tudo:

1. Auth > Login
2. Health > rodar todos
3. Business > Create Customer
4. Business > Get Customer
5. Business > Create Product
6. Business > Get Product
7. Imports > Import Financial CSV
8. Summary > Get Summary
9. KPI > Evaluate Formula
10. Auth > Logout

Observacoes:

- Requests protegidos usam Authorization: Bearer {{accessToken}}.
- Login e Refresh atualizam accessToken e refreshToken automaticamente no environment.
- O request de importacao CSV exige selecionar manualmente o arquivo no campo file.
- Exemplo de arquivo para importacao: backend/data/demo/nova_distribuidora/financial.csv
