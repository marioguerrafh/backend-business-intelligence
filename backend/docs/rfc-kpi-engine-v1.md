# RFC - KPI Engine v1.0

Date: 2026-07-10
Author: Chief Business Intelligence Office + CFO + Controller + Principal Software Architect
Status: Proposed
Reference: Catálogo Oficial de KPIs da Plataforma v1.0

## 1. Objetivo

Definir o motor oficial de KPIs da plataforma para cálculo, interpretação, alertas e explicações por IA, com governança multiempresa e sem ambiguidade semântica.

## 2. Escopo

Inclui:

1. Governança do catálogo oficial de KPIs por domínio.
2. Regras de cálculo, frequência e dependências.
3. Motor de faixas de saúde, alertas e recomendações.
4. Camada de explicação por IA para gestores não técnicos.
5. Observabilidade e rastreabilidade completa de cada valor calculado.

Não inclui:

1. Construção de novos módulos de negócio.
2. Alteração de contratos públicos existentes fora do KPI Engine.
3. Modelagem de indicadores fora do catálogo oficial sem aprovação.

## 3. Princípios de Arquitetura

1. Single Source of Truth para definição de KPI.
2. Multi-tenant obrigatório por company_id.
3. Cálculo determinístico e reproduzível por período.
4. Separação estrita entre cálculo, interpretação e apresentação.
5. Explicabilidade nativa orientada a decisão executiva.

## 4. Componentes Lógicos do KPI Engine

### 4.1 KPI Catalog Service
Responsável por armazenar e versionar:

1. Nome do KPI.
2. Objetivo.
3. Fórmula oficial.
4. Fontes e dependências.
5. Frequência.
6. Faixas de saúde.
7. Regras de alerta.
8. Templates de explicação por IA.

### 4.2 KPI Calculation Service
Responsável por:

1. Resolver dependências de dados.
2. Executar fórmulas por período e empresa.
3. Garantir consistência temporal e idempotência de cálculo.
4. Publicar trilha de auditoria do cálculo.

### 4.3 KPI Health & Alert Service
Responsável por:

1. Classificar valor em verde, amarelo, vermelho.
2. Detectar quebra de tendência e desvio de meta.
3. Emitir alertas com severidade e prioridade.

### 4.4 KPI Recommendation Service
Responsável por:

1. Associar alertas a ações recomendadas.
2. Priorizar ações por impacto financeiro e operacional.
3. Sugerir responsável e prazo.

### 4.5 KPI Explanation AI Service
Responsável por:

1. Gerar resumo executivo sem jargão.
2. Explicar causa raiz com linguagem simples.
3. Transformar variação percentual em impacto de negócio.
4. Gerar narrativa para gestor não técnico.

## 5. Domínios do Catálogo Suportados

1. Financeiro
2. Comercial
3. Contábil
4. Estoque
5. Compras
6. RH
7. Atendimento
8. Produção
9. Executivo

## 6. Fluxo Funcional do KPI Engine

1. Ingestão e consolidação de dados por domínio.
2. Validação de qualidade e disponibilidade de dependências.
3. Cálculo do KPI conforme fórmula oficial.
4. Classificação em faixa de saúde.
5. Avaliação de regras de alerta.
6. Geração de recomendações.
7. Geração de explicação por IA.
8. Publicação para dashboards, alert center e reports executivos.

## 7. Governança do Catálogo

### 7.1 Papéis

1. Dono de negócio do KPI: aprova objetivo e utilidade.
2. Dono financeiro/controladoria: valida fórmula e consistência.
3. Dono de dados: valida fonte, qualidade e frequência.
4. Arquitetura: valida aderência técnica e rastreabilidade.

### 7.2 Processo de mudança

1. Proposta de novo KPI ou alteração em KPI existente.
2. Revisão técnica e de negócio.
3. Aprovação formal em comitê.
4. Versionamento com histórico de mudanças.
5. Comunicação para usuários e IA explanation templates.

## 8. Política de Qualidade de Dados

1. KPI não deve ser publicado sem dependências mínimas válidas.
2. Toda execução deve registrar timestamp, período e fonte.
3. Divergências críticas geram status de confiança baixo.
4. Todo KPI deve exibir nível de confiabilidade do dado.

## 9. Política de Explicação para Gestores

A IA deve seguir roteiro obrigatório:

1. O que aconteceu: valor atual, meta e tendência.
2. Por que aconteceu: até 3 causas principais.
3. O que fazer agora: 3 recomendações priorizadas.

A IA deve evitar:

1. Linguagem técnica sem tradução.
2. Conclusão sem evidência de dado.
3. Recomendação genérica sem ação prática.

## 10. Modelo de Alertas

### 10.1 Tipos

1. Desvio de meta.
2. Mudança abrupta de tendência.
3. Inconsistência de dados.
4. Risco composto executivo.

### 10.2 Severidade

1. Crítico: risco imediato de caixa, margem ou operação.
2. Alto: impacto relevante no ciclo corrente.
3. Médio: tendência adversa com tempo de reação.
4. Baixo: monitoramento preventivo.

## 11. Segurança e Multi-Tenant

1. Isolamento de dados por company_id em todas as camadas.
2. Controle de acesso por perfil e unidade organizacional.
3. Logs de acesso e explicação para auditoria.
4. Nenhuma explicação por IA deve expor dados de outra empresa.

## 12. Observabilidade e Auditoria

1. Rastrear linhagem de cálculo por KPI e período.
2. Rastrear regras aplicadas de saúde e alerta.
3. Rastrear versão do catálogo utilizada em cada execução.
4. Rastrear prompts e respostas da explicação por IA para auditoria.

## 13. Critérios de Aceite

1. 100% dos KPIs do catálogo oficial cadastrados no engine.
2. 100% dos KPIs com fórmula, fonte, dependências e frequência validadas.
3. 100% dos KPIs com faixas de saúde e regras de alerta configuradas.
4. 100% dos KPIs com explicação em linguagem simples e template para IA.
5. Rastreabilidade completa de cálculo e interpretação.
6. Isolamento multi-tenant validado ponta a ponta.

## 14. Roadmap de Evolução

### Fase 1 - Foundation

1. Cadastro e versionamento do catálogo oficial.
2. Cálculo determinístico dos KPIs principais por categoria.
3. Faixas de saúde e alertas básicos.

### Fase 2 - Intelligence

1. Explicação por IA com narrativa executiva.
2. Recomendações prescritivas por contexto.
3. Priorização por impacto financeiro.

### Fase 3 - Predictive

1. Forecast de KPIs críticos.
2. Detecção proativa de risco.
3. Simulação de cenários para decisão.

## 15. Riscos e Mitigações

1. Risco: divergência de fórmula entre áreas.
- Mitigação: governança central com aprovação formal.

2. Risco: baixa qualidade de dados em origem.
- Mitigação: score de confiabilidade e bloqueio de publicação crítica.

3. Risco: explicação de IA genérica.
- Mitigação: templates por KPI com contexto de meta, tendência e impacto.

## 16. Conclusão

O KPI Engine v1.0 formaliza o cérebro analítico da plataforma, conectando cálculo confiável, interpretação executiva e recomendação acionável. O catálogo oficial passa a ser a referência única de performance empresarial, com governança robusta e explicabilidade orientada a decisão.
