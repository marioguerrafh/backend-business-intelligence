# Casos de Uso - Executive Intelligence v1.0

Date: 2026-07-10
Status: Proposed

## 1. UC-BIZ-01 - Ver saúde geral da empresa

1. Ator: CEO
2. Entrada: abre dashboard executivo.
3. Saída: score geral + eixos + alertas críticos.
4. Regra: deve refletir último ciclo válido do tenant.

## 2. UC-BIZ-02 - Priorizar ação semanal

1. Ator: Diretor Comercial
2. Entrada: lista de recomendações ordenada por impacto.
3. Saída: top 3 ações com owner_role e SLA.
4. Regra: deduplicação por causa raiz.

## 3. UC-BIZ-03 - Justificar decisão em reunião

1. Ator: CFO
2. Entrada: insight + evidências + variação temporal.
3. Saída: narrativa objetiva com causa e consequência.
4. Regra: insight sem evidência não deve ser publicado.

## 4. UC-BIZ-04 - Monitorar risco emergente

1. Ator: COO
2. Entrada: painel de riscos e probabilidade.
3. Saída: riscos p0/p1 com impacto potencial.
4. Regra: risco crítico sempre aparece no summary.

## 5. UC-TEC-01 - Reprocessar ciclo por falha parcial

1. Ator: Operação da Plataforma
2. Entrada: orchestrator_run com status failed/partial.
3. Saída: execução idempotente do estágio pendente.
4. Regra: não duplicar resultados já confirmados.

## 6. UC-TEC-02 - Atualizar regra sem deploy

1. Ator: BI Engineer
2. Entrada: nova versão da Rule DSL.
3. Saída: próxima execução usa catálogo atualizado.
4. Regra: manter trilha de versão por execução.

## 7. UC-TEC-03 - Auditar recomendação publicada

1. Ator: Auditor Interno
2. Entrada: recommendation_id + period_ref.
3. Saída: regra origem, risco associado, impacto esperado, versão de DSL.
4. Regra: cadeia de rastreabilidade fim a fim obrigatória.
