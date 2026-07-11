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
7. Imports > Import Customers CSV
8. Imports > Import Products CSV
9. Imports > Import Sales CSV
10. Imports > Import Financial CSV
11. Internal Pipeline > KPI Orchestrator Ingest Completed
12. Internal Pipeline > Rule Execute
13. Internal Pipeline > Recommendation Generate
14. Internal Pipeline > Insight Generate
15. Internal Pipeline > Executive Score Calculate
16. Summary > Get Summary
17. KPI > Evaluate Formula
18. Auth > Logout

Observacoes:

- Requests protegidos usam Authorization: Bearer {{accessToken}}.
- Login e Refresh atualizam accessToken e refreshToken automaticamente no environment.
- Os imports salvam automaticamente job_id e ingest_event_id no environment para encadear a pipeline.
- O request de importacao CSV exige selecionar manualmente o arquivo no campo file.
- Exemplos de arquivo para importacao:
	- backend/data/demo/nova_distribuidora/customers.csv
	- backend/data/demo/nova_distribuidora/products.csv
	- backend/data/demo/nova_distribuidora/sales.csv
	- backend/data/demo/nova_distribuidora/financial.csv
- A pipeline interna usa por padrao o import de sales (variaveis importJobIdSales e ingestEventIdSales); se preferir, troque para financial no body do request de KPI Orchestrator.
