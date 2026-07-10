# Business Rules Catalog v1.0

Date: 2026-07-10
Author: Chief Business Intelligence Office + Controller + CFO + Principal Software Architect
Status: Approved
References:
- Catalogo Oficial de KPIs v1.0
- RFC KPI Engine v1.0

## 1. Objetivo

Padronizar as regras de negocio que governam saude, alertas, automacoes e explicacoes por IA para todos os KPIs oficiais da plataforma.

## 2. Politica Global das Regras

1. Toda regra e avaliada por company_id.
2. Toda regra usa periodo de referencia explicito (dia, semana, mes).
3. Toda regra deve registrar versao, timestamp e fonte de dados.
4. Toda regra deve produzir: status de saude, severidade, prioridade e narrativa para gestor.
5. Toda recomendacao deve ser acionavel e orientada por impacto.

## 3. Estrutura Padrao por KPI

Cada KPI possui um pacote padrao de regras:

1. Regra de saude (verde/amarelo/vermelho).
2. Regra de gatilho (evento de atencao).
3. Regra de agravamento (escalonamento de severidade).
4. Regra de acao automatica (quando aplicavel).
5. Template oficial de explicacao por IA.

---

## 4. Financeiro

### BR-FIN-01 - Receita Liquida (KPI FIN-01)
- Regras de saude: Verde >= meta mensal; Amarelo entre 90% e 99%; Vermelho < 90%.
- Gatilhos: Queda > 10% em 7 dias; desvio > 5% entre faturamento e fiscal.
- Condicoes: Receita liquida calculada com impostos, devolucoes e descontos conciliados.
- Severidade: Medio (amarelo), Alto (vermelho), Critico (vermelho + queda consecutiva 3 periodos).
- Dependencias: Faturamento, fiscal, devolucoes, descontos, calendario mensal.
- Acoes automaticas: Abrir incidente financeiro; notificar dono comercial e controladoria; gerar analise por canal.
- Alertas: Painel executivo, email para CFO, notificacao em centro de alertas.
- Recomendacoes: Revisar descontos, devolucoes e mix; priorizar produtos de maior margem.
- Impacto esperado: Recuperacao de receita e previsibilidade de caixa.
- Prioridade: P1.
- Template IA: "Receita liquida em {valor_atual}, {variacao}% vs periodo anterior e {gap_meta}% vs meta. Principais causas: {causa_1}, {causa_2}, {causa_3}. Acoes prioritarias em 7 dias: {acao_1}, {acao_2}, {acao_3}."

### BR-FIN-02 - Margem EBITDA (KPI FIN-02)
- Regras de saude: Verde >= benchmark; Amarelo entre 80% e 99% do benchmark; Vermelho < 80%.
- Gatilhos: Queda de margem em 2 periodos; aumento de OPEX > 8% sem crescimento de receita.
- Condicoes: DRE gerencial fechada no periodo e classificacao de OPEX valida.
- Severidade: Medio, Alto, Critico quando margem cai e caixa operacional tambem cai.
- Dependencias: DRE, centro de custos, classificacao contabilidade gerencial.
- Acoes automaticas: Abrir plano de eficiencia; emitir ranking de centros de custo com maior desvio.
- Alertas: CFO, Controller e lideres de area impactada.
- Recomendacoes: Renegociar contratos e reduzir despesas de baixo retorno.
- Impacto esperado: Melhor alocacao de custo e recuperacao de rentabilidade.
- Prioridade: P1.
- Template IA: "Margem EBITDA atual de {margem}% ({variacao_pp} pp). Pressao principal em {centro_custo_1}, {centro_custo_2}. Para recuperar {objetivo_pp} pp, execute: {acao_1}, {acao_2}, {acao_3}."

### BR-FIN-03 - Fluxo de Caixa Operacional (KPI FIN-03)
- Regras de saude: Verde positivo e acima da meta; Amarelo positivo abaixo da meta; Vermelho negativo.
- Gatilhos: 3 dias seguidos negativos; projecao de caixa < cobertura minima de 30 dias.
- Condicoes: Conciliacao bancaria diaria concluida e movimentos classificados.
- Severidade: Alto para 3 dias negativos; Critico quando cobertura < 15 dias.
- Dependencias: Bancos, contas a receber, contas a pagar, previsao de desembolso.
- Acoes automaticas: Simulacao de caixa 30/60 dias; bloqueio de despesas discricionarias conforme politica.
- Alertas: Tesouraria, CFO, Controller.
- Recomendacoes: Antecipar recebiveis, renegociar prazos e priorizar pagamentos criticos.
- Impacto esperado: Reducao de risco de liquidez e continuidade operacional.
- Prioridade: P0.
- Template IA: "Caixa operacional em {saldo}, tendencia {tendencia}. Risco de cobertura em {dias_cobertura} dias. Para proteger caixa, priorize: {acao_1}, {acao_2}, {acao_3}."

---

## 5. Comercial

### BR-COM-01 - Taxa de Conversao (KPI COM-01)
- Regras de saude: Verde >= meta; Amarelo entre 85% e 99%; Vermelho < 85%.
- Gatilhos: Queda por canal em 2 semanas; backlog de leads sem follow-up > SLA.
- Condicoes: Estagios de funil padronizados e oportunidades qualificadas validadas.
- Severidade: Medio, Alto por canal estrategico.
- Dependencias: CRM, funil, leads qualificados, vendas fechadas.
- Acoes automaticas: Gerar ranking por canal e vendedor; abrir tarefa de coaching para time.
- Alertas: Gestor comercial e diretoria.
- Recomendacoes: Melhorar qualificacao e script de abordagem.
- Impacto esperado: Aumento de eficiencia comercial e previsibilidade de pipeline.
- Prioridade: P1.
- Template IA: "Conversao em {conversao}% ({variacao_pp} pp). Maior queda em {canal_critico}. Principais alavancas: {acao_1}, {acao_2}, {acao_3}."

### BR-COM-02 - Ticket Medio (KPI COM-02)
- Regras de saude: Verde >= meta; Amarelo 90% a 99%; Vermelho < 90%.
- Gatilhos: Queda > 8% no mes; desconto medio acima da politica.
- Condicoes: Receita liquida e pedidos validos no mesmo periodo.
- Severidade: Medio; Alto quando queda combina com margem em baixa.
- Dependencias: ERP vendas, politica de descontos, mix de produtos.
- Acoes automaticas: Sinalizar pedidos fora da politica; recomendar campanha de upsell.
- Alertas: Comercial, pricing e financeiro.
- Recomendacoes: Ajustar bundles e limitar descontos fora de regra.
- Impacto esperado: Melhora de receita por pedido e margem.
- Prioridade: P1.
- Template IA: "Ticket medio em {ticket}, {variacao}% no periodo. Queda explicada por {fator_1} e {fator_2}. Acoes sugeridas: {acao_1}, {acao_2}, {acao_3}."

### BR-COM-03 - CAC (KPI COM-03)
- Regras de saude: Verde <= meta; Amarelo 101% a 115%; Vermelho > 115%.
- Gatilhos: CAC acima do limite por 2 ciclos; gasto de marketing cresce sem ganho de conversao.
- Condicoes: Custos comerciais e marketing alocados por canal e periodo.
- Severidade: Alto; Critico se CAC > LTV minimo aceitavel.
- Dependencias: Financeiro, CRM, marketing, base de novos clientes.
- Acoes automaticas: Pausar campanhas de baixa eficiencia; recalcular distribuicao de verba.
- Alertas: Marketing, vendas, CFO.
- Recomendacoes: Rebalancear canais e segmentacoes.
- Impacto esperado: Reducao de custo de aquisicao e crescimento sustentavel.
- Prioridade: P1.
- Template IA: "CAC atual de {cac}, relacao CAC/LTV em {ratio}. Canal mais ineficiente: {canal}. Redirecione investimento para {canal_eficiente}."

---

## 6. Contabil

### BR-CON-01 - Prazo de Fechamento Contabil (KPI CON-01)
- Regras de saude: Verde <= 5 dias uteis; Amarelo 6 a 8; Vermelho > 8.
- Gatilhos: Etapa critica atrasada; reabertura de fechamento.
- Condicoes: Checklist de fechamento completo com status por etapa.
- Severidade: Medio, Alto, Critico se atraso compromete reporte externo.
- Dependencias: Fiscal, financeiro, conciliacoes, contabilidade.
- Acoes automaticas: Escalar etapa atrasada para dono funcional; replanejar cronograma.
- Alertas: Controller e diretoria financeira.
- Recomendacoes: Automatizar conciliacoes e eliminar retrabalhos recorrentes.
- Impacto esperado: Fechamento mais rapido e confiavel.
- Prioridade: P1.
- Template IA: "Fechamento em {dias} dias uteis, {desvio} vs meta. Gargalos: {etapa_1}, {etapa_2}. Plano de aceleracao: {acao_1}, {acao_2}."

### BR-CON-02 - Indice de Conciliacao (KPI CON-02)
- Regras de saude: Verde >= 98%; Amarelo 95% a 97.9%; Vermelho < 95%.
- Gatilhos: Conta critica sem conciliacao por 2 ciclos.
- Condicoes: Lista de contas criticas ativa e materialidade definida.
- Severidade: Alto para conta critica; Critico se impacto potencial relevante.
- Dependencias: Balancete, conciliacoes, trilha de ajustes.
- Acoes automaticas: Abrir pendencia por conta; travar fechamento se regra critica violada.
- Alertas: Controladoria, contabilidade e auditoria interna.
- Recomendacoes: Corrigir origem do lancamento e reforcar governanca.
- Impacto esperado: Reducao de risco de distorcao contabil.
- Prioridade: P0.
- Template IA: "Indice de conciliacao em {indice}%. Contas criticas pendentes: {conta_1}, {conta_2}. Risco: {risco}. Acoes imediatas: {acao_1}, {acao_2}."

### BR-CON-03 - Taxa de Reclassificacao (KPI CON-03)
- Regras de saude: Verde <= 2%; Amarelo 2.1% a 5%; Vermelho > 5%.
- Gatilhos: Crescimento por 3 meses consecutivos.
- Condicoes: Historico de ajustes com motivo padronizado.
- Severidade: Medio, Alto quando associado a atraso de fechamento.
- Dependencias: Razao contabil, ajustes e mapeamento de contas.
- Acoes automaticas: Classificar causas de reclassificacao; criar backlog de correcoes de origem.
- Alertas: Controller e lider contabil.
- Recomendacoes: Revisar matriz de contas e regras de integracao.
- Impacto esperado: Menos retrabalho e mais confiabilidade.
- Prioridade: P2.
- Template IA: "Reclassificacao em {taxa}%, tendencia {tendencia}. Principal causa: {causa}. Corrija origem em {processo_1} e {processo_2}."

---

## 7. Estoque

### BR-EST-01 - Giro de Estoque (KPI EST-01)
- Regras de saude: Verde no intervalo alvo por categoria; Amarelo fora ate 15%; Vermelho fora acima de 15%.
- Gatilhos: Queda abrupta de giro; cobertura acima do limite.
- Condicoes: CPV e estoque medio validados por categoria.
- Severidade: Medio; Alto para itens de alto valor parado.
- Dependencias: Estoque, custos, cadastro de categoria, demanda.
- Acoes automaticas: Marcar itens com excesso e recomendar reposicionamento comercial.
- Alertas: Operacoes, compras e financeiro.
- Recomendacoes: Ajustar politica de reposicao e mix.
- Impacto esperado: Menor capital parado e melhor caixa.
- Prioridade: P1.
- Template IA: "Giro em {giro} vs alvo {alvo}. Itens com maior excesso: {item_1}, {item_2}. Acoes: {acao_1}, {acao_2}, {acao_3}."

### BR-EST-02 - Taxa de Ruptura (KPI EST-02)
- Regras de saude: Verde <= 2%; Amarelo 2.1% a 5%; Vermelho > 5%.
- Gatilhos: SKU critico em ruptura > 24h; ruptura em item de alta margem.
- Condicoes: Demanda real e disponibilidade sincronizadas.
- Severidade: Alto; Critico para item estrategico com perda de receita.
- Dependencias: Pedidos, estoque em tempo real, classificacao de criticidade.
- Acoes automaticas: Priorizar reposicao de SKU critico; sugerir transferencia entre unidades.
- Alertas: Operacoes, comercial e suprimentos.
- Recomendacoes: Revisar ponto de pedido e previsao de demanda.
- Impacto esperado: Reducao de perda de vendas e aumento de satisfacao.
- Prioridade: P0.
- Template IA: "Ruptura em {ruptura}% com perda estimada de {perda_receita}. SKUs criticos: {sku_1}, {sku_2}. Priorize reposicao imediata."

### BR-EST-03 - Acuracia de Inventario (KPI EST-03)
- Regras de saude: Verde >= 98%; Amarelo 95% a 97.9%; Vermelho < 95%.
- Gatilhos: Divergencia recorrente por endereco, turno ou operador.
- Condicoes: Inventario ciclico e contagem fisica registrados no periodo.
- Severidade: Medio; Alto quando divergencia afeta itens criticos.
- Dependencias: WMS/ERP, inventario, trilha de movimentacao.
- Acoes automaticas: Abrir auditoria de endereco; bloquear movimentacao de item divergente critico.
- Alertas: Estoque, auditoria interna e operacoes.
- Recomendacoes: Ajustar processo de contagem e separacao.
- Impacto esperado: Menos perdas e melhor confianca no plano de compras.
- Prioridade: P1.
- Template IA: "Acuracia em {acuracia}%. Divergencias concentradas em {local_1}. Impacto estimado: {impacto}. Corrija com {acao_1}, {acao_2}."

---

## 8. Compras

### BR-CPR-01 - Saving de Compras (KPI CPR-01)
- Regras de saude: Verde >= meta; Amarelo 85% a 99%; Vermelho < 85%.
- Gatilhos: Queda de saving em categoria critica.
- Condicoes: Preco de referencia aprovado e historico de cotacao completo.
- Severidade: Medio; Alto para categorias de maior peso de custo.
- Dependencias: Compras, contratos, cotacoes e classificacao de categoria.
- Acoes automaticas: Sugerir rodada de renegociacao; destacar fornecedores com menor competitividade.
- Alertas: Compras estrategicas e controladoria.
- Recomendacoes: Consolidar volume e revisar contratos.
- Impacto esperado: Reducao de custo e ganho de margem.
- Prioridade: P1.
- Template IA: "Saving acumulado em {saving} ({atingimento}% da meta). Gap principal em {categoria}. Acoes: {acao_1}, {acao_2}."

### BR-CPR-02 - Lead Time de Suprimento (KPI CPR-02)
- Regras de saude: Verde <= SLA; Amarelo ate 15% acima; Vermelho > 15%.
- Gatilhos: Atrasos recorrentes por fornecedor.
- Condicoes: Pedido e recebimento com data valida e SLA definido.
- Severidade: Medio; Alto quando afeta producao ou ruptura.
- Dependencias: Compras, recebimento, fornecedor, SLA.
- Acoes automaticas: Reclassificar risco de fornecedor; sugerir fornecedor alternativo.
- Alertas: Suprimentos, producao e planejamento.
- Recomendacoes: Revisar carteira e clausulas de entrega.
- Impacto esperado: Maior previsibilidade e menor ruptura.
- Prioridade: P1.
- Template IA: "Lead time medio em {lead_time} dias vs SLA {sla}. Fornecedor com maior desvio: {fornecedor}. Mitigue com {acao_1}, {acao_2}."

### BR-CPR-03 - OTD Fornecedor (KPI CPR-03)
- Regras de saude: Verde >= 95%; Amarelo 90% a 94.9%; Vermelho < 90%.
- Gatilhos: Fornecedor estrategico abaixo da meta por 2 meses.
- Condicoes: Calendario de entrega e tolerancia de atraso definidos.
- Severidade: Alto; Critico para fornecedor unico de item critico.
- Dependencias: Ordens de compra, recebimento, criticidade de fornecedor.
- Acoes automaticas: Abrir plano de performance do fornecedor; recomendar contingencia.
- Alertas: Compras, risco operacional e diretoria.
- Recomendacoes: Diversificar base e renegociar SLA.
- Impacto esperado: Menor risco de interrupcao operacional.
- Prioridade: P0.
- Template IA: "OTD em {otd}% com desvio de {desvio_pp} pp. Fornecedor critico: {fornecedor}. Acoes emergenciais: {acao_1}, {acao_2}."

---

## 9. RH

### BR-RH-01 - Turnover (KPI RH-01)
- Regras de saude: Verde <= benchmark interno; Amarelo ate 20% acima; Vermelho > 20% acima.
- Gatilhos: Aumento de desligamentos em area critica.
- Condicoes: Movimentacoes de pessoal consolidadas e headcount medio valido.
- Severidade: Medio; Alto para funcoes criticas.
- Dependencias: Folha, cadastro RH, desligamentos e admissioes.
- Acoes automaticas: Abrir analise de causa de desligamento por area.
- Alertas: RH, lideranca da area e diretoria.
- Recomendacoes: Plano de retencao e revisao de lideranca.
- Impacto esperado: Reducao de custo de reposicao e estabilidade de equipe.
- Prioridade: P1.
- Template IA: "Turnover em {turnover}% ({variacao_pp} pp). Area mais critica: {area}. Custo estimado da rotatividade: {custo}."

### BR-RH-02 - Absenteismo (KPI RH-02)
- Regras de saude: Verde <= 2%; Amarelo 2.1% a 4%; Vermelho > 4%.
- Gatilhos: Pico por turno/unidade por 2 semanas.
- Condicoes: Registro de ponto e escala sem pendencias.
- Severidade: Medio; Alto quando afeta capacidade operacional.
- Dependencias: Ponto, escalas, justificativas e jornada planejada.
- Acoes automaticas: Sinalizar escala critica; recomendar redistribuicao de equipe.
- Alertas: RH e operacoes.
- Recomendacoes: Acoes de saude ocupacional e ajuste de escala.
- Impacto esperado: Ganho de produtividade e menor hora extra.
- Prioridade: P2.
- Template IA: "Absenteismo em {taxa}% com impacto de {horas_perdidas} horas. Unidades criticas: {unidade_1}, {unidade_2}."

### BR-RH-03 - Custo de Pessoal / Receita (KPI RH-03)
- Regras de saude: Verde dentro da meta; Amarelo ate 10% acima; Vermelho > 10%.
- Gatilhos: Crescimento do indicador sem ganho proporcional de receita.
- Condicoes: Folha e receita fechadas no mesmo periodo.
- Severidade: Alto quando tendencia de alta por 3 meses.
- Dependencias: Folha, encargos, financeiro, receita liquida.
- Acoes automaticas: Gerar mapa de produtividade por area.
- Alertas: RH, CFO e controladoria.
- Recomendacoes: Ajuste de capacidade e melhoria de produtividade.
- Impacto esperado: Estrutura de custos mais sustentavel.
- Prioridade: P1.
- Template IA: "Custo de pessoal em {indice}% da receita. Pressao maior em {area}. Alavancas de recuperacao: {acao_1}, {acao_2}."

---

## 10. Atendimento

### BR-ATD-01 - Tempo Medio de Primeira Resposta (KPI ATD-01)
- Regras de saude: Verde <= SLA; Amarelo ate 20% acima; Vermelho > 20%.
- Gatilhos: Fila acima do limite por canal.
- Condicoes: Chamado com abertura e primeira resposta registradas.
- Severidade: Medio; Alto em canal critico de receita.
- Dependencias: Help desk, chat, CRM atendimento.
- Acoes automaticas: Rebalancear fila por skill; acionar bot para triagem.
- Alertas: Lider de atendimento e operacoes.
- Recomendacoes: Ajustar escala e automacoes de primeiro contato.
- Impacto esperado: Melhor experiencia e menor abandono.
- Prioridade: P2.
- Template IA: "Primeira resposta em {tmr} min vs SLA {sla}. Canal critico: {canal}. Acoes imediatas: {acao_1}, {acao_2}."

### BR-ATD-02 - FCR (KPI ATD-02)
- Regras de saude: Verde >= 80%; Amarelo 65% a 79.9%; Vermelho < 65%.
- Gatilhos: Queda por produto, canal ou agente.
- Condicoes: Reabertura de chamados corretamente classificada.
- Severidade: Medio; Alto quando custo por chamado sobe em paralelo.
- Dependencias: Sistema de tickets, base de conhecimento, equipe.
- Acoes automaticas: Identificar top motivos de reabertura; recomendar treinamento.
- Alertas: Atendimento e qualidade.
- Recomendacoes: Atualizar base de conhecimento e scripts.
- Impacto esperado: Reducao de retrabalho e custo operacional.
- Prioridade: P2.
- Template IA: "FCR em {fcr}%. Reaberturas concentradas em {tema_1}, {tema_2}. Plano de melhoria: {acao_1}, {acao_2}, {acao_3}."

### BR-ATD-03 - NPS (KPI ATD-03)
- Regras de saude: Verde >= 50; Amarelo 20 a 49; Vermelho < 20.
- Gatilhos: Queda acentuada apos mudanca de processo ou produto.
- Condicoes: Volume minimo de respostas e amostra representativa.
- Severidade: Alto quando queda persistente por 2 ciclos.
- Dependencias: Pesquisas, jornada de cliente, tags de feedback.
- Acoes automaticas: Classificar detratores por causa; abrir plano de recuperacao.
- Alertas: CX, produto e diretoria.
- Recomendacoes: Atuar nas causas raiz de insatisfacao.
- Impacto esperado: Retencao e crescimento organico.
- Prioridade: P1.
- Template IA: "NPS em {nps}, variacao de {variacao}. Detratores citam {causa_1} e {causa_2}. Acoes de choque: {acao_1}, {acao_2}."

---

## 11. Producao

### BR-PRD-01 - OEE (KPI PRD-01)
- Regras de saude: Verde >= 85%; Amarelo 70% a 84.9%; Vermelho < 70%.
- Gatilhos: Queda por linha/turno/equipamento.
- Condicoes: Disponibilidade, performance e qualidade com apontamento valido.
- Severidade: Alto; Critico em linha gargalo.
- Dependencias: MES, apontamento de paradas, qualidade.
- Acoes automaticas: Abrir analise de perdas OEE por fator.
- Alertas: Producao, manutencao e engenharia.
- Recomendacoes: Reduzir microparadas, ajustar setup e atacar defeitos.
- Impacto esperado: Maior capacidade produtiva efetiva.
- Prioridade: P0.
- Template IA: "OEE em {oee}%. Perdas: disponibilidade {disp}%, performance {perf}%, qualidade {qual}%. Foque em {acao_1} e {acao_2}."

### BR-PRD-02 - Taxa de Refugo (KPI PRD-02)
- Regras de saude: Verde <= meta; Amarelo ate 20% acima; Vermelho > 20%.
- Gatilhos: Pico de refugo por lote, maquina ou materia-prima.
- Condicoes: Registro de causa e lote obrigatorios.
- Severidade: Alto; Critico quando custo de refugo excede limite mensal.
- Dependencias: Qualidade, producao, lotes e insumos.
- Acoes automaticas: Bloquear lote suspeito e abrir RCA (analise de causa raiz).
- Alertas: Qualidade, producao e suprimentos.
- Recomendacoes: Ajustar parametros de processo e qualidade de insumo.
- Impacto esperado: Reducao de desperdicio e custo industrial.
- Prioridade: P1.
- Template IA: "Refugo em {refugo}% com custo estimado de {custo_refugo}. Causa dominante: {causa}. Medidas imediatas: {acao_1}, {acao_2}."

### BR-PRD-03 - Aderencia ao Plano (KPI PRD-03)
- Regras de saude: Verde >= 95%; Amarelo 85% a 94.9%; Vermelho < 85%.
- Gatilhos: Desvio diario em item critico.
- Condicoes: Plano congelado por periodo e producao apontada.
- Severidade: Medio; Alto para pedido com prazo comprometido.
- Dependencias: PCP, ordens de producao, carteira de pedidos.
- Acoes automaticas: Repriorizar ordens e recalcular sequenciamento.
- Alertas: PCP, producao e comercial.
- Recomendacoes: Rebalancear capacidade e reduzir paradas.
- Impacto esperado: Melhor nivel de servico e menor atraso.
- Prioridade: P1.
- Template IA: "Aderencia em {aderencia}%. Gap de {gap} unidades no item {item}. Replaneje com {acao_1}, {acao_2}."

---

## 12. Executivo

### BR-EXE-01 - Crescimento de Receita (KPI EXE-01)
- Regras de saude: Verde >= meta estrategica; Amarelo ate 10% abaixo; Vermelho > 10% abaixo.
- Gatilhos: Crescimento desacelera por 2 ciclos.
- Condicoes: Receita comparavel com ajuste de sazonalidade.
- Severidade: Alto quando combinado com queda de margem.
- Dependencias: Financeiro, comercial, calendario comparativo.
- Acoes automaticas: Gerar decomposicao por canal, produto e regiao.
- Alertas: C-level executivo.
- Recomendacoes: Reforcar canais mais rentaveis e corrigir perdas.
- Impacto esperado: Crescimento com qualidade de receita.
- Prioridade: P1.
- Template IA: "Crescimento em {crescimento}% vs meta {meta}%. Motores positivos: {motor_1}. Riscos: {risco_1}. Acoes: {acao_1}, {acao_2}."

### BR-EXE-02 - Margem Liquida (KPI EXE-02)
- Regras de saude: Verde >= meta; Amarelo 80% a 99% da meta; Vermelho < 80%.
- Gatilhos: Queda de margem por 3 meses; lucro negativo.
- Condicoes: DRE final validada e conciliada.
- Severidade: Alto; Critico em lucro negativo recorrente.
- Dependencias: Receita, custos, despesas, impostos.
- Acoes automaticas: Acionar comite de margem com plano de recuperacao.
- Alertas: CEO, CFO, Controller.
- Recomendacoes: Revisar preco, custo e eficiencia tributaria.
- Impacto esperado: Recuperacao do lucro final.
- Prioridade: P0.
- Template IA: "Margem liquida em {margem}% ({variacao_pp} pp). Maiores impactos: {impacto_1}, {impacto_2}. Plano de recuperacao: {acao_1}, {acao_2}, {acao_3}."

### BR-EXE-03 - Ciclo de Conversao de Caixa (KPI EXE-03)
- Regras de saude: Verde <= meta; Amarelo ate 15% acima; Vermelho > 15% acima.
- Gatilhos: Aumento simultaneo de prazo de estoque e recebimento.
- Condicoes: PMR, PME e PMP atualizados e consistentes.
- Severidade: Alto; Critico com risco de liquidez.
- Dependencias: Estoque, contas a receber, contas a pagar.
- Acoes automaticas: Simulacao de alavancas de giro por componente.
- Alertas: Tesouraria, CFO e operacoes.
- Recomendacoes: Melhorar cobranca, giro e negociacao de prazo.
- Impacto esperado: Liberacao de capital de giro.
- Prioridade: P0.
- Template IA: "CCC em {ccc} dias. Caixa travado em {componente_critico}. Reducao potencial com {acao_1}: {ganho_estimado}."

### BR-EXE-04 - Business Health Index (KPI EXE-04)
- Regras de saude: Verde >= 80; Amarelo 60 a 79; Vermelho < 60.
- Gatilhos: Queda > 10 pontos em 14 dias; divergencia com lucro ou caixa.
- Condicoes: KPIs componentes atualizados com confiabilidade minima.
- Severidade: Medio, Alto, Critico conforme velocidade de deterioracao.
- Dependencias: KPIs de todos os dominios, pesos oficiais e score de confianca.
- Acoes automaticas: Gerar diagnostico multi-area e plano tatico priorizado.
- Alertas: Comite executivo completo.
- Recomendacoes: Atacar os 3 fatores com maior contribuicao negativa.
- Impacto esperado: Reacao rapida e alinhamento interareas.
- Prioridade: P0.
- Template IA: "Health Index em {score} com tendencia {tendencia}. Fatores negativos principais: {fator_1}, {fator_2}, {fator_3}. Plano em 30 dias: {acao_1}, {acao_2}, {acao_3}."

---

## 13. Matriz de Prioridade e Escalonamento

1. P0: Caixa, margem liquida, ruptura critica, OEE em linha gargalo, OTD fornecedor estrategico.
2. P1: Receita, EBITDA, conversao, CAC, giro e NPS.
3. P2: Itens de eficiencia incremental sem risco imediato de continuidade.

Escalonamento minimo:

1. Critico: notificacao imediata + comite em ate 24h.
2. Alto: plano de acao em ate 48h.
3. Medio: plano de acao em ate 5 dias uteis.
4. Baixo: monitoramento e revisao no ciclo semanal.

## 14. Politica de Explicacao da IA para Gestores

A IA deve sempre responder com:

1. Resumo executivo: situacao atual, meta e tendencia.
2. Causas: ate 3 fatores com evidencia de dados.
3. Acoes: ate 3 recomendacoes priorizadas por impacto e prazo.

Padrao de linguagem:

1. Simples, direta, sem jargao.
2. Sempre traduzir percentual em impacto de negocio.
3. Sempre explicar risco de nao agir.
