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
10. Imports > Import Cashflow CSV
11. Imports > Import Balance Sheet CSV
12. Imports > Import Income Statement CSV
13. Imports > Import Accounts Receivable CSV
14. Imports > Import Accounts Payable CSV
15. Imports > Import Inventory CSV
16. Imports > Import HR CSV
17. Internal Pipeline > KPI Orchestrator Ingest Completed
18. Internal Pipeline > Rule Execute
19. Internal Pipeline > Recommendation Generate
20. Internal Pipeline > Insight Generate
21. Internal Pipeline > Executive Score Calculate
22. Summary > Get Summary
23. KPI > Evaluate Formula
24. Auth > Logout

Observacoes:

- Requests protegidos usam Authorization: Bearer {{accessToken}}.
- Login e Refresh atualizam accessToken e refreshToken automaticamente no environment.
- Os imports salvam automaticamente job_id e ingest_event_id no environment para encadear a pipeline.
- O request de importacao CSV exige selecionar manualmente o arquivo no campo file.
- Exemplos de arquivo para importacao:
	- backend/data/demo/nova_distribuidora/customers.csv
	- backend/data/demo/nova_distribuidora/products.csv
	- backend/demo/sales.csv
	- backend/demo/cashflow.csv
	- backend/demo/balance_sheet.csv
	- backend/demo/income_statement.csv
	- backend/demo/accounts_receivable.csv
	- backend/demo/accounts_payable.csv
	- backend/demo/inventory.csv
	- backend/demo/hr.csv
- A pipeline interna usa por padrao o import de sales (variaveis importJobIdSales e ingestEventIdSales); se preferir, troque para cashflow ou outro template canonico no body do request de KPI Orchestrator.
