# RFC - Rule Engine v1.0

Date: 2026-07-10
Author: Chief Business Intelligence Office + Controller + CFO + Principal Software Architect
Status: Proposed
Reference: Business Rules Catalog v1.0

## 1. Objetivo

Definir o Rule Engine oficial da plataforma para avaliar regras de negocio dos KPIs, classificar saude, disparar alertas, executar acoes automaticas e gerar explicacoes por IA orientadas a decisao.

## 2. Escopo

Inclui:

1. Execucao de regras por dominio e KPI.
2. Classificacao de saude e severidade.
3. Disparo de gatilhos e escalonamento.
4. Orquestracao de acoes automaticas e recomendacoes.
5. Integracao com KPI Engine e camada de explicacao por IA.

Nao inclui:

1. Definicao de novos KPIs fora do catalogo oficial.
2. Alteracao de formulas do KPI Engine sem governanca.
3. Automacoes operacionais fora de regras aprovadas.

## 3. Principios

1. Governanca central das regras com versionamento.
2. Determinismo e auditabilidade de toda avaliacao.
3. Multi-tenant estrito por company_id.
4. Separacao de avaliacao, acao e comunicacao.
5. Explicabilidade para usuario de negocio por padrao.

## 4. Modelo Conceitual do Rule Engine

### 4.1 Rule Catalog
Camada de definicao das regras por KPI contendo:

1. Regra de saude.
2. Gatilhos e condicoes.
3. Severidade e prioridade.
4. Dependencias.
5. Acoes automaticas permitidas.
6. Alertas e recomendacoes.
7. Template de explicacao por IA.

### 4.2 Rule Evaluator
Responsavel por:

1. Consumir valor de KPI e contexto do periodo.
2. Avaliar condicoes e status de saude.
3. Determinar severidade e prioridade final.
4. Produzir evento de avaliacao.

### 4.3 Trigger & Escalation Service
Responsavel por:

1. Detectar gatilhos simples e compostos.
2. Aplicar politicas de escalonamento (critico, alto, medio, baixo).
3. Abrir incidentes e tarefas conforme SLA.

### 4.4 Action Orchestrator
Responsavel por:

1. Executar acoes automaticas aprovadas.
2. Registrar sucesso/falha e impacto esperado.
3. Evitar repeticao indevida por idempotencia de regra-periodo.

### 4.5 Alert & Recommendation Service
Responsavel por:

1. Publicar alertas por canal e perfil.
2. Priorizar recomendacoes por impacto.
3. Vincular recomendacao a dono e prazo.

### 4.6 AI Explanation Service
Responsavel por:

1. Aplicar template oficial por KPI.
2. Gerar narrativa simples para gestor.
3. Explicar causa, risco e proxima acao.

## 5. Fluxo Funcional

1. KPI Engine publica valor e contexto do KPI.
2. Rule Engine carrega regras ativas para company_id e KPI.
3. Evaluator aplica regras de saude e gatilhos.
4. Trigger Service determina severidade e escalonamento.
5. Action Orchestrator executa automacoes permitidas.
6. Alert Service emite notificacoes e recomendacoes.
7. AI Explanation Service gera explicacao para gestor.
8. Auditoria registra trilha completa da avaliacao.

## 6. Dominios Cobertos

1. Financeiro
2. Comercial
3. Contabil
4. Estoque
5. Compras
6. RH
7. Atendimento
8. Producao
9. Executivo

## 7. Regras de Prioridade

1. Prioridade P0:
- Liquidez e continuidade (caixa, margem liquida, CCC, ruptura critica, OEE gargalo, OTD fornecedor estrategico).

2. Prioridade P1:
- Crescimento e eficiencia economica (receita, EBITDA, CAC, conversao, NPS, giro).

3. Prioridade P2:
- Eficiencia incremental e estabilidade operacional.

## 8. Politica de Escalonamento

1. Critico:
- Notificacao imediata para C-level.
- Plano de resposta em ate 24h.

2. Alto:
- Dono funcional e financeiro notificados.
- Plano em ate 48h.

3. Medio:
- Acao tatico-operacional em ate 5 dias uteis.

4. Baixo:
- Monitoramento no ciclo semanal.

## 9. Contratos Logicos de Entrada e Saida

### 9.1 Entrada de avaliacao

1. company_id
2. kpi_id
3. periodo
4. valor_kpi
5. meta
6. tendencia
7. contexto (segmento, unidade, canal, categoria)
8. score de confianca dos dados

### 9.2 Saida de avaliacao

1. status_saude
2. severidade
3. prioridade
4. gatilhos_ativados
5. alertas_emitidos
6. acoes_automaticas_executadas
7. recomendacoes
8. impacto_esperado
9. explicacao_ia
10. trilha_auditoria

## 10. Governanca e Mudanca de Regras

1. Toda regra nova ou alterada deve passar por comite BI + Controladoria + Arquitetura.
2. Toda alteracao deve ser versionada com justificativa.
3. Toda alteracao deve ter data de vigencia e rollback definido.
4. Toda regra deve ter owner de negocio e owner tecnico.

## 11. Seguranca e Compliance

1. Isolamento estrito por company_id em leitura e avaliacao de regra.
2. Controle de acesso por perfil para criacao/edicao/aprovacao de regras.
3. Trilha de auditoria imutavel para toda avaliacao.
4. Explicacoes de IA nao podem expor dados de outras empresas.

## 12. Observabilidade

1. Tempo medio de avaliacao por regra.
2. Taxa de gatilhos ativados por KPI.
3. Taxa de falso positivo por tipo de alerta.
4. Percentual de recomendacoes executadas.
5. Impacto realizado versus impacto esperado.

## 13. Criticos de Qualidade

1. Nenhuma regra executa sem dependencias minimas validas.
2. Nenhuma acao automatica executa fora de politica aprovada.
3. Nenhum alerta critico pode ficar sem dono.
4. Toda explicacao de IA deve ter base nos dados da avaliacao.

## 14. Criterios de Aceite

1. 100% dos KPIs oficiais com regras cadastradas no Rule Catalog.
2. 100% das regras com severidade, prioridade e escalonamento definidos.
3. 100% das regras com template de explicacao por IA.
4. 100% das avaliacoes com trilha de auditoria completa.
5. Validacao multi-tenant ponta a ponta aprovada.

## 15. Riscos e Mitigacoes

1. Risco: excesso de alertas (alert fatigue).
- Mitigacao: limiares adaptativos, deduplicacao e priorizacao por impacto.

2. Risco: recomendacoes genericas.
- Mitigacao: templates por KPI e contexto de negocio.

3. Risco: baixa confianca em dados de origem.
- Mitigacao: score de confianca e bloqueio de alertas criticos sem qualidade minima.

4. Risco: conflito entre regras antigas e novas.
- Mitigacao: versionamento, vigencia explicita e validacao de regressao.

## 16. Roadmap

### Fase 1 - Foundation

1. Cadastro das regras oficiais por KPI.
2. Avaliacao de saude e severidade.
3. Alertas basicos por dominio.

### Fase 2 - Automation

1. Acoes automaticas por prioridade.
2. Escalonamento inteligente.
3. Medicao de efetividade das recomendacoes.

### Fase 3 - Adaptive Intelligence

1. Ajuste dinamico de limiares por sazonalidade.
2. Recomendacoes prescritivas orientadas por impacto.
3. Simulacao de cenarios de decisao.

## 17. Conclusao

O Rule Engine v1.0 institucionaliza a disciplina de gestao por excecao, conectando KPI, regras de negocio, automacao e explicacao executiva. Com isso, a plataforma evolui de monitoramento para decisao assistida com governanca, prioridade e impacto mensuravel.
