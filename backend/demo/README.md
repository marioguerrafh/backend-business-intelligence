# DEMO ENTERPRISE DATASET

## Empresa
- company_id: cmp_enterprise_demo
- Razao social: Enterprise Foods Brasil S/A
- Segmento: Industria + Distribuicao
- Funcionarios base: 100
- Filiais: 2
- Centros de distribuicao: 5
- Clientes ativos: 1200
- Produtos: 850
- Fornecedores: 420

## Periodo coberto
- Jan/2024 a Dez/2026 (36 meses)
- Todos os CSVs possuem dados em todos os meses

## Arquivos gerados
- sales.csv: 15000
- cashflow.csv: 5000
- balance_sheet.csv: 36
- income_statement.csv: 36
- accounts_receivable.csv: 8000
- accounts_payable.csv: 6000
- inventory.csv: 10000
- hr.csv: 36

## Consistencia aplicada
- Receita do DRE alinhada com agregacao de Sales por periodo
- COGS e margem variam conforme eventos operacionais
- Caixa operacional acompanha resultado + capital de giro
- Estoque responde a sazonalidade e evento de agosto (estoque alto)
- RH acompanha produtividade e recuperacao operacional

## Eventos simulados por mes (padrao anual)
- Marco: queda de vendas e aumento de pressao de caixa
- Junho: recuperacao comercial
- Agosto: excesso de estoque e aumento de dias em inventario
- Outubro: compressao de margem
- Novembro: melhora operacional
- Dezembro: recorde de vendas

## KPIs esperados
- Cobertura integral para KPI Catalog com dados de vendas, caixa, DRE, balanco, AR/AP, estoque e RH
- Oscilacao de liquidez, rentabilidade, eficiencia operacional e capital de giro

## Rules esperadas (principais)
- Receita abaixo da meta (meses de estresse)
- Fluxo de caixa operacional negativo/pressionado
- Estoque excessivo e dias em inventario elevados
- Prazo medio de recebimento alto
- Prazo medio de pagamento baixo
- Cobertura de juros fraca em meses de compressao
- ROA/ROE abaixo do alvo em janelas de estresse

## Recommendations esperadas (principais)
- Comercial: recuperacao de conversao e mix de produtos
- Financeiro: reforco de caixa, alongamento de passivos, renegociacao de custo financeiro
- Operacional: ganho de eficiencia e reducao de despesas
- Estoque: ajuste de reposicao e giro
- RH: equilibrio entre produtividade e custo de folha

## Insights esperados
- Insights variando por periodo com sinais de queda, recuperacao, excesso de estoque, pressao de margem e retomada

## Executive Score esperado por periodo
- 2024-01: 74
- 2024-02: 75
- 2024-03: 66
- 2024-04: 75
- 2024-05: 75
- 2024-06: 75
- 2024-07: 75
- 2024-08: 66
- 2024-09: 75
- 2024-10: 66
- 2024-11: 80
- 2024-12: 85
- 2025-01: 78
- 2025-02: 79
- 2025-03: 70
- 2025-04: 79
- 2025-05: 79
- 2025-06: 79
- 2025-07: 79
- 2025-08: 70
- 2025-09: 79
- 2025-10: 70
- 2025-11: 84
- 2025-12: 89
- 2026-01: 82
- 2026-02: 83
- 2026-03: 74
- 2026-04: 83
- 2026-05: 83
- 2026-06: 83
- 2026-07: 83
- 2026-08: 74
- 2026-09: 83
- 2026-10: 74
- 2026-11: 88
- 2026-12: 93

## Faturamento total (net_revenue em Sales)
- 93,830,031.95
