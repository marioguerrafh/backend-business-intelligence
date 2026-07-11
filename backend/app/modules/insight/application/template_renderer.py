from __future__ import annotations

from dataclasses import dataclass

from app.modules.insight.domain.entities import PromptTemplateDefinition


@dataclass(slots=True)
class InsightTemplateRenderer:
    def render(
        self,
        *,
        template: PromptTemplateDefinition,
        kpi_context: dict[str, float],
        fired_rule_ids: tuple[str, ...],
        selected_recommendation_ids: tuple[str, ...],
    ) -> tuple[str, dict[str, object]]:
        revenue = kpi_context.get("FIN_01")
        margin = kpi_context.get("FIN_02")
        cashflow = kpi_context.get("FIN_03")
        health = kpi_context.get("EXE_04")

        if template.intent == "executive_summary":
            statement = self._render_executive_summary(
                revenue=revenue,
                margin=margin,
                cashflow=cashflow,
                health=health,
                fired_rule_ids=fired_rule_ids,
                selected_recommendation_ids=selected_recommendation_ids,
            )
            return statement, {
                "intent": template.intent,
                "schema": template.output_schema,
                "fired_rule_ids": list(fired_rule_ids),
                "selected_recommendation_ids": list(selected_recommendation_ids),
                "kpis": {
                    "FIN_01": revenue,
                    "FIN_02": margin,
                    "FIN_03": cashflow,
                    "EXE_04": health,
                },
            }

        if template.intent == "explain_kpi":
            statement = self._render_kpi_explainer(cashflow=cashflow, margin=margin)
            return statement, {
                "intent": template.intent,
                "schema": template.output_schema,
                "fired_rule_ids": list(fired_rule_ids),
            }

        # Fallback generic summary, still constrained to known evidence.
        statement = (
            "O periodo apresentou sinais mistos entre crescimento e risco operacional. "
            "As recomendacoes priorizadas devem ser executadas para estabilizar os indicadores."
        )
        return statement, {
            "intent": template.intent,
            "schema": template.output_schema,
            "fired_rule_ids": list(fired_rule_ids),
            "selected_recommendation_ids": list(selected_recommendation_ids),
        }

    def _render_executive_summary(
        self,
        *,
        revenue: float | None,
        margin: float | None,
        cashflow: float | None,
        health: float | None,
        fired_rule_ids: tuple[str, ...],
        selected_recommendation_ids: tuple[str, ...],
    ) -> str:
        revenue_part = "faturamento sem variacao relevante"
        if revenue is not None:
            revenue_part = f"faturamento em {revenue:.2f}"

        margin_part = "margem sem deterioracao relevante"
        if margin is not None:
            margin_part = f"margem em {margin:.2f}"

        cash_part = "caixa em nivel estavel"
        if cashflow is not None:
            if cashflow < 0:
                cash_part = f"fluxo de caixa negativo em {cashflow:.2f}"
            else:
                cash_part = f"fluxo de caixa positivo em {cashflow:.2f}"

        health_part = "indice de saude em faixa neutra"
        if health is not None:
            health_part = f"indice de saude executiva em {health:.2f}"

        rule_part = "sem alertas criticos ativos"
        if fired_rule_ids:
            rule_part = f"alertas ativos: {', '.join(fired_rule_ids[:3])}"

        rec_part = "sem plano de acao priorizado"
        if selected_recommendation_ids:
            rec_part = f"acoes priorizadas: {', '.join(selected_recommendation_ids[:3])}"

        return (
            f"{revenue_part}, porem {margin_part}. "
            f"No consolidado, {cash_part} e {health_part}; {rule_part}; {rec_part}."
        )

    def _render_kpi_explainer(self, *, cashflow: float | None, margin: float | None) -> str:
        cash_part = "fluxo de caixa neutro"
        if cashflow is not None:
            cash_part = f"fluxo de caixa em {cashflow:.2f}"

        margin_part = "margem estavel"
        if margin is not None:
            margin_part = f"margem em {margin:.2f}"

        return f"{cash_part}; {margin_part}; priorizar acoes de recuperacao de margem e liquidez."
