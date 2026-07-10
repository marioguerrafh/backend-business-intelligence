# Catálogo Oficial de KPIs da Plataforma v1.0

Date: 2026-07-10
Author: Chief Business Intelligence Office + CFO + Controller + Principal Software Architect
Status: Approved

## 1. Diretrizes do Catálogo

1. Todo KPI deve ser calculado por company_id.
2. Toda fórmula deve ter rastreabilidade para origem de dados e período.
3. Toda faixa de saúde deve ser configurável por empresa e setor.
4. Toda explicação por IA deve ser clara, sem jargão técnico, com foco em decisão.

---

## 2. Financeiro

### KPI FIN-01 - Receita Líquida
- Nome: Receita Líquida
- Objetivo: Medir quanto realmente entrou de receita após deduções.
- Fórmula: Receita Bruta - Impostos sobre vendas - Devoluções - Descontos concedidos.
- Fonte dos dados: ERP faturamento, notas fiscais, módulo fiscal.
- Dependências: Plano de contas, classificação de impostos, calendário fiscal.
- Frequência de atualização: Diário com fechamento mensal.
- Interpretação: Crescente e consistente indica expansão saudável.
- Faixas de saúde: Verde >= meta mensal; Amarelo entre 90% e 99% da meta; Vermelho < 90% da meta.
- Alertas: Queda > 10% em 7 dias; divergência entre faturamento e fiscal.
- Recomendações: Revisar mix de produtos, política de descontos e causas de devolução.
- Explicação em linguagem simples: É o dinheiro que sobrou das vendas depois de tirar impostos e perdas comerciais.
- Como a IA deve explicar para gestor sem conhecimento técnico: Mostrar valor atual, comparação com meta e explicar em três frases o que mais ajudou e o que mais prejudicou a receita.

### KPI FIN-02 - Margem EBITDA
- Nome: Margem EBITDA
- Objetivo: Avaliar eficiência operacional antes de juros, impostos, depreciação e amortização.
- Fórmula: EBITDA / Receita Líquida * 100.
- Fonte dos dados: DRE gerencial, plano de contas, centro de custos.
- Dependências: Mapeamento contábil correto de despesas operacionais.
- Frequência de atualização: Diário estimado e fechamento mensal oficial.
- Interpretação: Margem maior indica melhor geração operacional de resultado.
- Faixas de saúde: Verde >= benchmark setorial; Amarelo entre 80% e 99% do benchmark; Vermelho < 80%.
- Alertas: Queda de margem por 2 períodos consecutivos; aumento abrupto de OPEX.
- Recomendações: Cortar desperdícios, renegociar contratos e revisar estrutura de custos.
- Explicação em linguagem simples: Mostra quanto sobra da operação para cada 100 de receita, antes de despesas financeiras e contábeis.
- Como a IA deve explicar para gestor sem conhecimento técnico: Traduzir a margem para valor por 100 de venda e apontar as 3 maiores despesas que pressionaram o resultado.

### KPI FIN-03 - Fluxo de Caixa Operacional
- Nome: Fluxo de Caixa Operacional
- Objetivo: Medir a capacidade da operação de gerar caixa real.
- Fórmula: Entradas operacionais de caixa - Saídas operacionais de caixa.
- Fonte dos dados: Contas a receber, contas a pagar, bancos, conciliação financeira.
- Dependências: Conciliação bancária diária, classificação correta de movimentos.
- Frequência de atualização: Diário.
- Interpretação: Positivo recorrente indica sustentabilidade financeira.
- Faixas de saúde: Verde positivo e acima da meta de caixa; Amarelo positivo porém abaixo da meta; Vermelho negativo.
- Alertas: 3 dias seguidos negativos; projeção de caixa insuficiente para 30 dias.
- Recomendações: Acelerar recebimentos, postergar pagamentos não críticos, rever capital de giro.
- Explicação em linguagem simples: Mostra se a operação está gerando dinheiro ou consumindo dinheiro.
- Como a IA deve explicar para gestor sem conhecimento técnico: Indicar saldo atual, tendência para os próximos 30 dias e ações práticas para evitar falta de caixa.

---

## 3. Comercial

### KPI COM-01 - Taxa de Conversão de Vendas
- Nome: Taxa de Conversão
- Objetivo: Medir eficiência do funil comercial.
- Fórmula: Número de vendas fechadas / Número de oportunidades qualificadas * 100.
- Fonte dos dados: CRM, pipeline comercial, pedidos faturados.
- Dependências: Definição padronizada de lead qualificado e estágio de funil.
- Frequência de atualização: Diário.
- Interpretação: Quanto maior, melhor o aproveitamento das oportunidades.
- Faixas de saúde: Verde >= meta; Amarelo entre 85% e 99% da meta; Vermelho < 85%.
- Alertas: Queda de conversão por canal por 2 semanas; aumento de leads sem follow-up.
- Recomendações: Treinar time, ajustar script comercial e qualificação de leads.
- Explicação em linguagem simples: Mostra quantas oportunidades viram vendas de fato.
- Como a IA deve explicar para gestor sem conhecimento técnico: Comparar por canal e vendedor, destacando onde a conversão está melhor e onde está vazando.

### KPI COM-02 - Ticket Médio
- Nome: Ticket Médio
- Objetivo: Acompanhar valor médio por venda.
- Fórmula: Receita líquida de vendas / Número de pedidos.
- Fonte dos dados: ERP vendas, faturamento, pedidos.
- Dependências: Cadastro de pedidos e faturamento íntegros.
- Frequência de atualização: Diário.
- Interpretação: Crescimento indica maior valor capturado por transação.
- Faixas de saúde: Verde >= meta; Amarelo entre 90% e 99% da meta; Vermelho < 90%.
- Alertas: Queda > 8% no mês; aumento de descontos acima da política.
- Recomendações: Upsell, cross-sell, revisão de política comercial e bundles.
- Explicação em linguagem simples: É quanto cada venda rende em média.
- Como a IA deve explicar para gestor sem conhecimento técnico: Mostrar evolução mensal e quais linhas de produto puxaram para cima ou para baixo.

### KPI COM-03 - Custo de Aquisição de Cliente (CAC)
- Nome: CAC
- Objetivo: Medir quanto custa conquistar cada novo cliente.
- Fórmula: Investimento comercial e marketing / Número de novos clientes no período.
- Fonte dos dados: Financeiro, marketing, CRM.
- Dependências: Regra clara de atribuição de despesas por canal e período.
- Frequência de atualização: Semanal com consolidação mensal.
- Interpretação: CAC menor com qualidade de cliente estável indica eficiência.
- Faixas de saúde: Verde <= meta; Amarelo entre 101% e 115% da meta; Vermelho > 115%.
- Alertas: CAC acima do LTV aceitável; aumento de mídia sem ganho de conversão.
- Recomendações: Otimizar canais, segmentação e campanhas com baixo retorno.
- Explicação em linguagem simples: Quanto a empresa gasta para trazer cada cliente novo.
- Como a IA deve explicar para gestor sem conhecimento técnico: Relacionar CAC com retorno esperado do cliente e indicar se crescer nesse ritmo é sustentável.

---

## 4. Contábil

### KPI CON-01 - Prazo Médio de Fechamento Contábil
- Nome: Fechamento Contábil (dias)
- Objetivo: Medir velocidade e maturidade do fechamento mensal.
- Fórmula: Data final de fechamento - Último dia do mês de competência.
- Fonte dos dados: Sistema contábil, workflow de fechamento.
- Dependências: Integrações fiscais, financeiras e conciliações finalizadas.
- Frequência de atualização: Mensal.
- Interpretação: Menor prazo com qualidade indica processo maduro.
- Faixas de saúde: Verde <= 5 dias úteis; Amarelo entre 6 e 8; Vermelho > 8.
- Alertas: Atraso em etapas críticas; reabertura de fechamento.
- Recomendações: Automatizar conciliações e padronizar checklist.
- Explicação em linguagem simples: Mostra em quantos dias a contabilidade fecha o mês.
- Como a IA deve explicar para gestor sem conhecimento técnico: Informar atraso, gargalos principais e impacto na tomada de decisão.

### KPI CON-02 - Índice de Conciliação Contábil
- Nome: Índice de Conciliação
- Objetivo: Medir qualidade das reconciliações entre submódulos e razão contábil.
- Fórmula: Número de contas conciliadas / Número total de contas críticas * 100.
- Fonte dos dados: Balancete, conciliações de contas, relatórios de auditoria.
- Dependências: Plano de contas, regras de materialidade.
- Frequência de atualização: Semanal no fechamento.
- Interpretação: Quanto maior, menor risco de distorção contábil.
- Faixas de saúde: Verde >= 98%; Amarelo entre 95% e 97,9%; Vermelho < 95%.
- Alertas: Conta crítica não conciliada por mais de 2 ciclos.
- Recomendações: Revisar lançamentos automáticos e responsáveis por conta.
- Explicação em linguagem simples: Mostra quanto da contabilidade está conferida e sem divergência.
- Como a IA deve explicar para gestor sem conhecimento técnico: Dizer quantas contas ainda têm problema e quais riscos isso traz para o resultado reportado.

### KPI CON-03 - Taxa de Lançamentos Reclassificados
- Nome: Taxa de Reclassificação
- Objetivo: Medir qualidade inicial dos lançamentos contábeis.
- Fórmula: Lançamentos reclassificados / Lançamentos totais * 100.
- Fonte dos dados: Livro razão, histórico de ajustes contábeis.
- Dependências: Regras de classificação, treinamento da equipe.
- Frequência de atualização: Mensal.
- Interpretação: Taxa alta indica problema de classificação na origem.
- Faixas de saúde: Verde <= 2%; Amarelo entre 2,1% e 5%; Vermelho > 5%.
- Alertas: Crescimento contínuo por 3 meses.
- Recomendações: Ajustar regras automáticas e revisar matriz de contas.
- Explicação em linguagem simples: Mostra quantos lançamentos precisaram ser corrigidos depois.
- Como a IA deve explicar para gestor sem conhecimento técnico: Explicar que retrabalho alto aumenta risco de erro e atrasa fechamento.

---

## 5. Estoque

### KPI EST-01 - Giro de Estoque
- Nome: Giro de Estoque
- Objetivo: Medir velocidade de renovação do estoque.
- Fórmula: Custo dos produtos vendidos / Estoque médio no período.
- Fonte dos dados: ERP estoque, custos, movimentações.
- Dependências: Valoração de estoque correta e inventário confiável.
- Frequência de atualização: Diário com visão mensal.
- Interpretação: Giro adequado reduz capital parado e ruptura.
- Faixas de saúde: Verde no intervalo alvo por categoria; Amarelo fora do alvo em até 15%; Vermelho fora acima de 15%.
- Alertas: Queda brusca de giro ou excesso de dias de cobertura.
- Recomendações: Ajustar compras, revisar mix e políticas de reposição.
- Explicação em linguagem simples: Mostra quantas vezes o estoque foi vendido e reposto no período.
- Como a IA deve explicar para gestor sem conhecimento técnico: Traduzir em dias de estoque parado e impacto em caixa.

### KPI EST-02 - Ruptura de Estoque
- Nome: Taxa de Ruptura
- Objetivo: Medir perda de venda por falta de item.
- Fórmula: SKUs com falta / SKUs demandados * 100.
- Fonte dos dados: Pedidos, estoque disponível, histórico de backorder.
- Dependências: Registro de demanda real e disponibilidade em tempo real.
- Frequência de atualização: Diário.
- Interpretação: Taxa alta representa perda direta de receita e satisfação.
- Faixas de saúde: Verde <= 2%; Amarelo entre 2,1% e 5%; Vermelho > 5%.
- Alertas: SKU crítico em ruptura > 24h; ruptura em itens de alta margem.
- Recomendações: Priorizar reposição de itens críticos e revisar ponto de pedido.
- Explicação em linguagem simples: Mostra quantas vezes o cliente quis comprar e não havia produto.
- Como a IA deve explicar para gestor sem conhecimento técnico: Quantificar perda estimada de receita e indicar os 10 itens mais críticos.

### KPI EST-03 - Acurácia de Inventário
- Nome: Acurácia de Inventário
- Objetivo: Medir confiabilidade entre estoque físico e sistema.
- Fórmula: Itens sem divergência / Itens inventariados * 100.
- Fonte dos dados: Inventário físico, WMS/ERP.
- Dependências: Procedimentos de contagem cíclica e movimentação disciplinada.
- Frequência de atualização: Semanal e inventários oficiais mensais.
- Interpretação: Alta acurácia reduz perdas, rupturas e compras erradas.
- Faixas de saúde: Verde >= 98%; Amarelo entre 95% e 97,9%; Vermelho < 95%.
- Alertas: Divergência recorrente por endereço, turno ou operador.
- Recomendações: Auditoria de processos, bloqueios de operação e treinamento.
- Explicação em linguagem simples: Mostra se o estoque no sistema bate com o que existe fisicamente.
- Como a IA deve explicar para gestor sem conhecimento técnico: Apontar onde as divergências se concentram e o impacto financeiro estimado.

---

## 6. Compras

### KPI CPR-01 - Saving de Compras
- Nome: Saving de Compras
- Objetivo: Medir ganho obtido em negociações.
- Fórmula: (Preço referência - Preço negociado) * Quantidade comprada.
- Fonte dos dados: Pedidos de compra, cotações, contratos.
- Dependências: Definição de preço referência válida por categoria.
- Frequência de atualização: Semanal com consolidação mensal.
- Interpretação: Saving consistente indica eficiência estratégica de compras.
- Faixas de saúde: Verde >= meta; Amarelo entre 85% e 99%; Vermelho < 85%.
- Alertas: Queda de saving por categoria crítica.
- Recomendações: Reabrir negociação, consolidar volume e rever fornecedores.
- Explicação em linguagem simples: Mostra quanto dinheiro foi economizado ao negociar melhor.
- Como a IA deve explicar para gestor sem conhecimento técnico: Mostrar economia total no período e quais categorias mais contribuíram.

### KPI CPR-02 - Lead Time de Suprimento
- Nome: Lead Time de Suprimento
- Objetivo: Medir tempo entre pedido de compra e recebimento.
- Fórmula: Data de recebimento - Data de emissão do pedido.
- Fonte dos dados: Compras, recebimento, logística.
- Dependências: Processo de recebimento atualizado e rastreabilidade do pedido.
- Frequência de atualização: Diário.
- Interpretação: Menor lead time, com estabilidade, aumenta previsibilidade operacional.
- Faixas de saúde: Verde <= SLA; Amarelo até 15% acima do SLA; Vermelho > 15%.
- Alertas: Atrasos recorrentes por fornecedor.
- Recomendações: Revisar carteira de fornecedores e cláusulas contratuais.
- Explicação em linguagem simples: É o tempo que a compra demora para chegar.
- Como a IA deve explicar para gestor sem conhecimento técnico: Relacionar atrasos com impacto em produção e ruptura de estoque.

### KPI CPR-03 - Índice de Entrega no Prazo (OTD Fornecedor)
- Nome: OTD de Fornecedores
- Objetivo: Medir confiabilidade de entrega dos fornecedores.
- Fórmula: Entregas no prazo / Entregas totais * 100.
- Fonte dos dados: Ordens de compra, recebimento, calendário de entrega.
- Dependências: SLA por fornecedor e regra de tolerância de atraso.
- Frequência de atualização: Semanal.
- Interpretação: Índice baixo aumenta risco de parada e custos emergenciais.
- Faixas de saúde: Verde >= 95%; Amarelo entre 90% e 94,9%; Vermelho < 90%.
- Alertas: Fornecedor estratégico abaixo da meta por 2 meses.
- Recomendações: Plano de performance com fornecedor ou substituição parcial.
- Explicação em linguagem simples: Mostra se os fornecedores entregam no dia combinado.
- Como a IA deve explicar para gestor sem conhecimento técnico: Apresentar ranking de fornecedores e impacto de atrasos no negócio.

---

## 7. RH

### KPI RH-01 - Turnover
- Nome: Taxa de Turnover
- Objetivo: Medir rotatividade de pessoas.
- Fórmula: (Admissões + Desligamentos) / 2 / Headcount médio * 100.
- Fonte dos dados: Folha, cadastro de colaboradores, desligamentos.
- Dependências: Cadastro de movimentações de pessoal atualizado.
- Frequência de atualização: Mensal.
- Interpretação: Alta rotatividade aumenta custo e reduz produtividade.
- Faixas de saúde: Verde <= benchmark interno; Amarelo até 20% acima; Vermelho > 20%.
- Alertas: Aumento de desligamentos em área crítica.
- Recomendações: Diagnóstico de clima, revisão de liderança e pacote de retenção.
- Explicação em linguagem simples: Mostra o quanto a empresa está trocando de pessoas.
- Como a IA deve explicar para gestor sem conhecimento técnico: Quantificar custo estimado da rotatividade e onde concentrar ação de retenção.

### KPI RH-02 - Absenteísmo
- Nome: Taxa de Absenteísmo
- Objetivo: Medir ausências não planejadas.
- Fórmula: Horas de ausência / Horas previstas de trabalho * 100.
- Fonte dos dados: Ponto eletrônico, escalas, folha.
- Dependências: Registro de jornadas e justificativas de ausência.
- Frequência de atualização: Semanal.
- Interpretação: Taxa elevada afeta produtividade e qualidade.
- Faixas de saúde: Verde <= 2%; Amarelo entre 2,1% e 4%; Vermelho > 4%.
- Alertas: Picos por turno, unidade ou função.
- Recomendações: Ações de saúde ocupacional e gestão de escala.
- Explicação em linguagem simples: Mostra quanto tempo de trabalho foi perdido por faltas.
- Como a IA deve explicar para gestor sem conhecimento técnico: Relacionar faltas com queda de produtividade e horas extras adicionais.

### KPI RH-03 - Custo de Pessoal sobre Receita
- Nome: Custo de Pessoal / Receita
- Objetivo: Medir peso da folha na geração de receita.
- Fórmula: Custo total de pessoal / Receita líquida * 100.
- Fonte dos dados: Folha, encargos, financeiro, receita líquida.
- Dependências: Rateio de custos de pessoal e receita por período.
- Frequência de atualização: Mensal.
- Interpretação: Deve estar alinhado à produtividade e ao modelo de negócio.
- Faixas de saúde: Verde dentro da meta; Amarelo até 10% acima; Vermelho > 10% acima.
- Alertas: Crescimento do indicador sem aumento proporcional de receita.
- Recomendações: Redesenhar capacidade, produtividade e estrutura organizacional.
- Explicação em linguagem simples: Mostra quanto da receita é consumido pelo custo de pessoas.
- Como a IA deve explicar para gestor sem conhecimento técnico: Traduzir em valor por 100 de receita e indicar áreas com maior pressão.

---

## 8. Atendimento

### KPI ATD-01 - Tempo Médio de Primeira Resposta
- Nome: TMR (Primeira Resposta)
- Objetivo: Medir agilidade inicial no atendimento.
- Fórmula: Soma do tempo até primeira resposta / Número de chamados.
- Fonte dos dados: Help desk, chat, CRM de atendimento.
- Dependências: Registro de abertura e primeira interação por canal.
- Frequência de atualização: Horária e diária.
- Interpretação: Menor tempo melhora percepção de qualidade.
- Faixas de saúde: Verde <= SLA; Amarelo até 20% acima do SLA; Vermelho > 20%.
- Alertas: Canal com fila acima do limite; aumento repentino de backlog.
- Recomendações: Rebalancear equipe, automação de triagem e bot assistido.
- Explicação em linguagem simples: É quanto tempo o cliente espera para ser atendido pela primeira vez.
- Como a IA deve explicar para gestor sem conhecimento técnico: Mostrar o tempo médio por canal e o impacto em satisfação e perda de clientes.

### KPI ATD-02 - Taxa de Resolução no Primeiro Contato
- Nome: FCR
- Objetivo: Medir efetividade do atendimento sem retrabalho.
- Fórmula: Chamados resolvidos no primeiro contato / Chamados totais * 100.
- Fonte dos dados: Sistema de tickets e status de resolução.
- Dependências: Classificação correta de reabertura de chamados.
- Frequência de atualização: Diário.
- Interpretação: FCR alto reduz custos e aumenta satisfação.
- Faixas de saúde: Verde >= 80%; Amarelo entre 65% e 79,9%; Vermelho < 65%.
- Alertas: Queda por produto, canal ou agente.
- Recomendações: Base de conhecimento, treinamento e scripts guiados.
- Explicação em linguagem simples: Mostra quantos problemas são resolvidos de primeira.
- Como a IA deve explicar para gestor sem conhecimento técnico: Destacar temas que mais voltam e ações para reduzir retrabalho.

### KPI ATD-03 - NPS
- Nome: NPS (Net Promoter Score)
- Objetivo: Medir lealdade e recomendação dos clientes.
- Fórmula: Percentual de promotores - Percentual de detratores.
- Fonte dos dados: Pesquisas pós-atendimento e pós-compra.
- Dependências: Base de clientes válida e taxa mínima de resposta.
- Frequência de atualização: Semanal com leitura mensal.
- Interpretação: NPS alto indica maior propensão de crescimento orgânico.
- Faixas de saúde: Verde >= 50; Amarelo entre 20 e 49; Vermelho < 20.
- Alertas: Queda acentuada após mudanças de produto/processo.
- Recomendações: Atuar em causas raiz de detratores e melhorar jornada.
- Explicação em linguagem simples: Mostra o quanto os clientes recomendariam a empresa.
- Como a IA deve explicar para gestor sem conhecimento técnico: Separar elogios e reclamações mais recorrentes e indicar plano de ação prioritário.

---

## 9. Produção

### KPI PRD-01 - OEE
- Nome: OEE (Eficiência Global do Equipamento)
- Objetivo: Medir performance real da produção combinando disponibilidade, performance e qualidade.
- Fórmula: Disponibilidade * Performance * Qualidade.
- Fonte dos dados: MES, apontamentos de produção, qualidade.
- Dependências: Paradas registradas, peças produzidas, sucata e refugos.
- Frequência de atualização: Horária com consolidação diária.
- Interpretação: OEE alto indica operação eficiente com pouca perda.
- Faixas de saúde: Verde >= 85%; Amarelo entre 70% e 84,9%; Vermelho < 70%.
- Alertas: Queda por linha, turno ou equipamento.
- Recomendações: Atuar em gargalos de setup, microparadas e qualidade.
- Explicação em linguagem simples: Mostra quanto da capacidade produtiva virou produção boa.
- Como a IA deve explicar para gestor sem conhecimento técnico: Explicar perdas em três blocos: paradas, velocidade e defeitos.

### KPI PRD-02 - Taxa de Refugo
- Nome: Taxa de Refugo
- Objetivo: Medir perdas de produção por defeitos irrecuperáveis.
- Fórmula: Quantidade refugada / Quantidade produzida * 100.
- Fonte dos dados: Qualidade, produção, inspeções.
- Dependências: Registro de causa de defeito e lote.
- Frequência de atualização: Diário.
- Interpretação: Taxa alta indica desperdício e custo industrial maior.
- Faixas de saúde: Verde <= meta; Amarelo até 20% acima; Vermelho > 20% acima.
- Alertas: Aumento em lote, máquina ou matéria-prima específica.
- Recomendações: Ajuste de processo, manutenção e qualidade de insumo.
- Explicação em linguagem simples: Mostra quanto foi produzido e precisou ser descartado.
- Como a IA deve explicar para gestor sem conhecimento técnico: Quantificar custo do refugo e indicar as causas principais para atacar primeiro.

### KPI PRD-03 - Cumprimento do Plano de Produção
- Nome: Aderência ao Plano
- Objetivo: Medir quanto do planejado foi entregue no período.
- Fórmula: Quantidade produzida conforme plano / Quantidade planejada * 100.
- Fonte dos dados: PCP, produção realizada, ordens de produção.
- Dependências: Plano congelado por período e registro de replanejamento.
- Frequência de atualização: Diário.
- Interpretação: Baixa aderência indica risco de atraso e ruptura.
- Faixas de saúde: Verde >= 95%; Amarelo entre 85% e 94,9%; Vermelho < 85%.
- Alertas: Desvio diário em itens críticos.
- Recomendações: Rebalancear capacidade, priorização e manutenção.
- Explicação em linguagem simples: Mostra se a fábrica entregou o que estava programado.
- Como a IA deve explicar para gestor sem conhecimento técnico: Mostrar o que faltou produzir, impacto em pedidos e ações corretivas imediatas.

---

## 10. Executivo

### KPI EXE-01 - Crescimento de Receita
- Nome: Crescimento de Receita
- Objetivo: Medir evolução do topo de linha.
- Fórmula: (Receita líquida atual - Receita líquida período anterior) / Receita líquida período anterior * 100.
- Fonte dos dados: Financeiro, DRE gerencial.
- Dependências: Calendário comparável e ajustes de sazonalidade.
- Frequência de atualização: Mensal com leitura acumulada no ano.
- Interpretação: Crescimento sustentável exige margem e caixa compatíveis.
- Faixas de saúde: Verde >= meta estratégica; Amarelo até 10% abaixo da meta; Vermelho > 10% abaixo.
- Alertas: Crescimento sem lucro ou com queda de caixa.
- Recomendações: Revisar preço, mix, canais e eficiência operacional.
- Explicação em linguagem simples: Mostra se a empresa está vendendo mais ou menos do que antes.
- Como a IA deve explicar para gestor sem conhecimento técnico: Relacionar crescimento com rentabilidade e risco de caixa, não apenas volume de vendas.

### KPI EXE-02 - Rentabilidade Líquida
- Nome: Margem Líquida
- Objetivo: Medir retorno final sobre a receita.
- Fórmula: Lucro líquido / Receita líquida * 100.
- Fonte dos dados: DRE contábil e gerencial.
- Dependências: Fechamento contábil e fiscal concluídos.
- Frequência de atualização: Mensal.
- Interpretação: Representa eficiência total do negócio após todos os custos.
- Faixas de saúde: Verde >= meta; Amarelo entre 80% e 99% da meta; Vermelho < 80%.
- Alertas: Queda de margem por três meses; lucro negativo.
- Recomendações: Revisar custos fixos, preço e eficiência tributária.
- Explicação em linguagem simples: Mostra quanto sobra de lucro para cada 100 de receita.
- Como a IA deve explicar para gestor sem conhecimento técnico: Apontar os maiores componentes que consumiram margem e o potencial de recuperação.

### KPI EXE-03 - Ciclo de Conversão de Caixa
- Nome: CCC (Cash Conversion Cycle)
- Objetivo: Medir quanto tempo o caixa fica preso na operação.
- Fórmula: Prazo médio de estoque + Prazo médio de recebimento - Prazo médio de pagamento.
- Fonte dos dados: Estoque, contas a receber, contas a pagar.
- Dependências: Datas corretas de compra, venda, recebimento e pagamento.
- Frequência de atualização: Semanal com leitura mensal.
- Interpretação: Quanto menor o ciclo, menor necessidade de capital de giro.
- Faixas de saúde: Verde <= meta; Amarelo até 15% acima; Vermelho > 15% acima.
- Alertas: Aumento simultâneo de estoque e recebimento.
- Recomendações: Melhorar giro, cobrança e negociação com fornecedores.
- Explicação em linguagem simples: Mostra em quantos dias o dinheiro investido volta para o caixa.
- Como a IA deve explicar para gestor sem conhecimento técnico: Explicar onde o dinheiro está travado e qual alavanca libera caixa mais rápido.

### KPI EXE-04 - Índice de Saúde Empresarial Composto
- Nome: Business Health Index
- Objetivo: Fornecer visão executiva única de desempenho global.
- Fórmula: Soma ponderada de KPIs críticos (financeiro, comercial, operação, pessoas e cliente).
- Fonte dos dados: Todos os módulos da plataforma.
- Dependências: Catálogo oficial de pesos e regras por segmento.
- Frequência de atualização: Diário.
- Interpretação: Permite leitura rápida do status geral e tendência.
- Faixas de saúde: Verde >= 80; Amarelo entre 60 e 79; Vermelho < 60.
- Alertas: Queda > 10 pontos em 14 dias; divergência entre índice e lucro/caixa.
- Recomendações: Ativar plano tático interáreas com foco em causa raiz dominante.
- Explicação em linguagem simples: É uma nota geral da empresa baseada nos indicadores mais importantes.
- Como a IA deve explicar para gestor sem conhecimento técnico: Mostrar a nota, a tendência e os três fatores que mais puxaram para cima ou para baixo.

---

## 11. Política de Explicação por IA (Padrão Global)

1. Sempre responder em três níveis:
- Resumo executivo em 1 parágrafo.
- Causas principais em até 3 pontos.
- Ações recomendadas priorizadas por impacto.

2. Sempre comparar:
- Período atual versus anterior.
- Atual versus meta.
- Atual versus benchmark, quando existir.

3. Sempre traduzir:
- Percentuais em impacto financeiro estimado.
- Tendências em risco de decisão.

4. Nunca usar jargão sem tradução:
- Todo termo técnico deve vir acompanhado de explicação simples.

5. Toda recomendação deve ter:
- Responsável sugerido.
- Prazo sugerido.
- Resultado esperado.
