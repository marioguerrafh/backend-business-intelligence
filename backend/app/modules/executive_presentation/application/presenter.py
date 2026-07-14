from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.modules.executive_presentation.application.catalog import PresentationCatalog
from app.modules.executive_presentation.application.formatters import (
    DateFormatter,
    HealthMapper,
    MoneyFormatter,
    PercentFormatter,
    QuantityFormatter,
    ScoreFormatter,
    SeverityFormatter,
    TrendFormatter,
)


@dataclass(slots=True)
class KpiPresenter:
    catalog: dict[str, Any]
    date_formatter: DateFormatter
    money_formatter: MoneyFormatter
    percent_formatter: PercentFormatter
    quantity_formatter: QuantityFormatter

    def present(self, item: dict[str, Any], *, period_ref: str, display_order: int) -> dict[str, Any]:
        kpi_id = str(item.get("kpi_id") or "")
        kpi_catalog = self.catalog.get("kpis", {})
        meta = dict(kpi_catalog.get(kpi_id, kpi_catalog.get("default", {})))

        short_name = str(meta.get("short_name", "")) or kpi_id or "Indicador"
        if short_name.strip().lower() == "indicador":
            short_name = (kpi_id or "Indicador").replace("_", " ").strip()
        display_name = str(meta.get("display_name", short_name))
        if display_name.strip().lower() == "indicador":
            display_name = short_name
        description = str(meta.get("description") or f"Indicador {display_name} consolidado para acompanhamento executivo.")
        currency_mode = str(meta.get("currency", "NUMBER")).upper()
        value = float(item.get("value", 0.0))

        if currency_mode == "BRL":
            formatted_value = self.money_formatter.format(value, "BRL")
            currency = "BRL"
        elif currency_mode == "PERCENT" or str(item.get("unit", "")).lower() in {"%", "percent"}:
            formatted_value = self.percent_formatter.format(value, decimals=1, include_sign=False)
            currency = "PERCENT"
        else:
            formatted_value = self.quantity_formatter.format(value, decimals=0)
            currency = "NUMBER"

        trend = str(item.get("trend") or "stable").lower()
        health_map = dict(meta.get("health", {}))
        health_raw = str(item.get("health") or "green").lower()
        normalized_health = str(health_map.get(health_raw, "attention"))

        trend_label = str(item.get("trend_label") or "")
        if not trend_label:
            trend_label = {
                "up": "+0,0%",
                "down": "-0,0%",
            }.get(trend, "0,0%")

        return {
            "id": kpi_id,
            "title": display_name,
            "short_name": short_name,
            "display_name": display_name,
            "description": description,
            "subtitle": self.date_formatter.period_subtitle(period_ref),
            "value": value,
            "display_value": formatted_value,
            "formatted_value": formatted_value,
            "currency": currency,
            "icon": str(meta.get("icon", "insights")),
            "category": str(meta.get("category", "Executivo")),
            "trend": trend,
            "trend_label": trend_label,
            "trend_icon": "trending_up" if trend == "up" else "trending_down" if trend == "down" else "trending_flat",
            "trend_color": "success" if trend == "up" else "error" if trend == "down" else "info",
            "comparison": str(meta.get("comparison", self.catalog.get("strings", {}).get("comparison_last_month", ""))),
            "health": normalized_health,
            "display_order": int(meta.get("display_order", display_order)),
        }


@dataclass(slots=True)
class AlertPresenter:
    catalog: dict[str, Any]
    date_formatter: DateFormatter
    severity_formatter: SeverityFormatter
    money_formatter: MoneyFormatter

    def present(self, item: dict[str, Any], *, period_ref: str, kpis: dict[str, dict[str, Any]]) -> dict[str, Any]:
        kpi_id = str(item.get("kpi_id") or "").strip()
        rule_id = str(item.get("rule_id") or "").strip()

        alerts_catalog = self.catalog.get("alerts", {})
        by_rule = alerts_catalog.get("by_rule", {})
        by_kpi = alerts_catalog.get("by_kpi", {})

        if not kpi_id and kpis:
            kpi_id = next(iter(kpis.keys()))
        if not kpi_id:
            kpi_id = "unknown_kpi"

        if not rule_id:
            rule_id = str(item.get("alert_id") or "").strip()
        if not rule_id:
            rule_id = f"rule.{kpi_id}.monitor"

        meta = dict(by_rule.get(rule_id, by_kpi.get(kpi_id, alerts_catalog.get("default", {}))))
        kpi_meta = self.catalog.get("kpis", {}).get(kpi_id, self.catalog.get("kpis", {}).get("default", {}))
        kpi_name = str(kpi_meta.get("display_name") or kpis.get(kpi_id, {}).get("title") or kpi_id)
        if kpi_name.strip().lower() == "indicador":
            kpi_name = kpi_id or "Indicador"
        if not kpi_name.strip():
            kpi_name = kpi_id

        metric_raw = item.get("metric_value")
        metric_value = float(metric_raw) if metric_raw is not None else None

        kpi_value = kpis.get(kpi_id, {}).get("value")
        if kpi_value is None and metric_value is not None:
            kpi_value = metric_value
        if kpi_value is None:
            kpi_display = "Sem valor consolidado"
        else:
            kpi_display = self.money_formatter.format(float(kpi_value), "BRL")

        impact_display = self.money_formatter.format(0.0, "BRL")
        if metric_value is not None and abs(metric_value) > 0:
            impact_display = self.money_formatter.format(abs(metric_value), "BRL")

        title_template = str(meta.get("title_template", "{kpi_name} com desvio relevante"))
        message_template = str(
            meta.get("message_template", "O indicador {kpi_name} apresentou variacao fora do esperado para este periodo.")
        )
        title_value = str(meta.get("title") or title_template.format(kpi_name=kpi_name))
        message_value = str(meta.get("message") or message_template.format(kpi_name=kpi_name))
        if title_value.strip().lower() in {"kpi", "indicador", "indicador com desvio"}:
            title_value = f"{kpi_name} fora da faixa esperada"
        if message_value.strip().lower() in {"kpi", "indicador", "indicador com desvio"}:
            message_value = f"{kpi_name} apresentou desvio relevante no periodo analisado."

        severity = str(item.get("severity") or "INFO").upper()
        status = "critical" if severity in {"CRITICAL", "HIGH"} else "warning" if severity == "MEDIUM" else "active"
        probability_raw = item.get("probability")
        if isinstance(probability_raw, (int, float)):
            probability = f"{int(round(float(probability_raw) * 100))}%"
        else:
            probability = "85%" if severity in {"CRITICAL", "HIGH"} else "65%" if severity == "MEDIUM" else "40%"

        rule_name = str(item.get("rule_name") or item.get("title") or rule_id)
        if not rule_name:
            rule_name = "Regra de monitoramento"

        return {
            "alert_id": str(item.get("alert_id") or ""),
            "severity": severity,
            "severity_meta": self.severity_formatter.format(severity),
            "priority": str(item.get("priority") or "").upper(),
            "category": str(item.get("category") or meta.get("category", kpi_meta.get("category", "Operacional"))),
            "status": status,
            "probability": probability,
            "title": title_value,
            "subtitle": self.date_formatter.period_subtitle(period_ref),
            "message": message_value,
            "impact": impact_display,
            "kpi": {
                "name": kpi_name,
                "display_value": kpi_display,
                "description": str(kpi_meta.get("description", "")),
            },
            "kpi_id": kpi_id,
            "kpi_name": kpi_name,
            "rule_id": rule_id,
            "rule_name": rule_name,
            "recommended_action": str(self.catalog.get("strings", {}).get("recommended_action", "Ver recomendacoes")),
            "details": str(item.get("description") or message_value),
            "details_available": True,
            "related_recommendation_ids": sorted({str(x) for x in (item.get("related_recommendation_ids") or []) if str(x)}),
            "icon": str(meta.get("icon", "warning")),
            "color": str(meta.get("color", "warning")),
        }


@dataclass(slots=True)
class InsightPresenter:
    catalog: dict[str, Any]

    def present(self, item: dict[str, Any], *, index: int = 0) -> dict[str, Any]:
        insight_type = str(item.get("type") or "default").lower()
        statement = str(item.get("statement") or "")

        inferred = insight_type
        lower = statement.lower()
        if "marg" in lower:
            inferred = "margin_attention"
        elif "caixa" in lower:
            inferred = "healthy_cashflow"
        elif "venda" in lower and ("acima" in lower or "cres" in lower):
            inferred = "sales_above_average"
        elif "convers" in lower or "baixa" in lower:
            inferred = "low_conversion"
        elif "receita" in lower:
            inferred = "trend"

        meta = dict(self.catalog.get("insights", {}).get(inferred, self.catalog.get("insights", {}).get("default", {})))
        title = str(meta.get("title", "Oportunidade de melhoria detectada"))
        if index > 0:
            title = f"{title} {index + 1}"

        return {
            "title": title,
            "summary": statement or "Insight executivo identificado para apoio a decisao.",
            "importance": str(meta.get("importance", "medium")),
            "icon": str(meta.get("icon", "lightbulb")),
            "category": str(meta.get("category", "Executivo")),
            "related_kpis": list(item.get("related_kpis") or []),
            "related_rules": list(item.get("related_rules") or []),
            "related_recommendations": list(item.get("related_recommendations") or []),
            "display_order": int(meta.get("display_order", 99)),
        }


@dataclass(slots=True)
class RecommendationPresenter:
    catalog: dict[str, Any]
    money_formatter: MoneyFormatter

    def present(self, item: dict[str, Any]) -> dict[str, Any]:
        defaults = dict(self.catalog.get("recommendations", {}).get("default", {}))
        category = str(defaults.get("category", "Operacional"))
        by_category = dict(self.catalog.get("recommendations", {}).get("by_category", {}).get(category, {}))
        impact_raw = item.get("expected_impact") or {}

        impact_value = impact_raw.get("value") if isinstance(impact_raw, dict) else None
        impact_unit = str((impact_raw.get("unit") if isinstance(impact_raw, dict) else "") or "BRL").upper()
        if impact_value is None:
            impact_display = "Sem ganho estimado disponivel"
        elif impact_unit == "BRL":
            impact_display = self.money_formatter.format(float(impact_value), "BRL")
        else:
            impact_display = f"{impact_value} {impact_unit}".strip()

        rank = float(item.get("rank", 0.0))
        if rank >= 0.85:
            priority_label = "Alta"
        elif rank >= 0.6:
            priority_label = "Media"
        else:
            priority_label = "Baixa"

        return {
            "recommendation_id": str(item.get("recommendation_id") or ""),
            "title": str(item.get("title") or "Recomendacao executiva"),
            "description": str(by_category.get("description", defaults.get("description", ""))),
            "expected_benefit": str(
                by_category.get("expected_benefit_template", defaults.get("expected_benefit_template", "{value}"))
            ).format(value=impact_display),
            "priority_label": priority_label,
            "estimated_impact": impact_display,
            "estimated_gain": impact_display,
            "estimated_effort": str(defaults.get("estimated_effort", "media")),
            "estimated_time": str(defaults.get("estimated_time", "7 dias")),
            "owner": str(item.get("owner_role") or "time_executivo"),
            "related_kpis": list(item.get("related_kpis") or []),
            "related_rules": list(item.get("related_rules") or []),
            "category": category,
            "icon": str(defaults.get("icon", "task_alt")),
            "color": str(defaults.get("color", "primary")),
            "action_button": str(defaults.get("action_button", "Ver plano de acao")),
            "priority_score": round(rank, 4),
        }


@dataclass(slots=True)
class ExecutiveScorePresenter:
    catalog: dict[str, Any]
    score_formatter: ScoreFormatter
    percent_formatter: PercentFormatter

    def present(self, scores: dict[str, Any], trends: dict[str, Any]) -> dict[str, Any]:
        overall = float(scores.get("overall", 0.0))
        score_meta = self.score_formatter.format(overall)
        monthly_value = float(trends.get("today_vs_last_month") or 0.0)

        return {
            "overall": overall,
            "display": score_meta["display"],
            "status": score_meta["status"],
            "status_description": score_meta["status_description"],
            "color": score_meta["status_color"],
            "icon": score_meta["status_icon"],
            "status_color": score_meta["status_color"],
            "status_icon": score_meta["status_icon"],
            "variation": self.percent_formatter.format(monthly_value, decimals=0),
            "comparison": str(self.catalog.get("strings", {}).get("comparison_last_month", "")),
            "description": score_meta["description"],
        }


class ExecutivePresentationMapper:
    def __init__(self, catalog_reader: PresentationCatalog) -> None:
        self.catalog_reader = catalog_reader
        catalog = self.catalog_reader.load()

        self.catalog = catalog
        self.money_formatter = MoneyFormatter()
        self.percent_formatter = PercentFormatter()
        self.quantity_formatter = QuantityFormatter()
        self.date_formatter = DateFormatter(catalog)
        self.trend_formatter = TrendFormatter(catalog, self.percent_formatter)
        self.severity_formatter = SeverityFormatter(catalog)
        self.score_formatter = ScoreFormatter(catalog)
        self.health_mapper = HealthMapper(catalog)

        self.kpi_presenter = KpiPresenter(
            catalog=catalog,
            date_formatter=self.date_formatter,
            money_formatter=self.money_formatter,
            percent_formatter=self.percent_formatter,
            quantity_formatter=self.quantity_formatter,
        )
        self.alert_presenter = AlertPresenter(
            catalog=catalog,
            date_formatter=self.date_formatter,
            severity_formatter=self.severity_formatter,
            money_formatter=self.money_formatter,
        )
        self.insight_presenter = InsightPresenter(catalog=catalog)
        self.recommendation_presenter = RecommendationPresenter(catalog=catalog, money_formatter=self.money_formatter)
        self.executive_score_presenter = ExecutiveScorePresenter(
            catalog=catalog,
            score_formatter=self.score_formatter,
            percent_formatter=self.percent_formatter,
        )

    def present(self, technical_payload: dict[str, Any]) -> dict[str, Any]:
        period_ref = str(technical_payload.get("period_ref") or "")

        presented_kpis = [
            self.kpi_presenter.present(item, period_ref=period_ref, display_order=idx + 1)
            for idx, item in enumerate(technical_payload.get("kpis", []))
        ]
        for item in presented_kpis:
            item["health"] = self.health_mapper.map(str(item.get("health") or "attention"))
        presented_kpis.sort(key=lambda item: int(item.get("display_order", 999)))

        kpi_lookup: dict[str, dict[str, Any]] = {
            str(item.get("id")): {"value": item.get("value"), "title": item.get("title")} for item in presented_kpis
        }

        trends_payload = self._present_trends(dict(technical_payload.get("trends") or {}))
        executive_score = self.executive_score_presenter.present(
            dict(technical_payload.get("scores") or {}),
            dict(technical_payload.get("trends") or {}),
        )

        alerts = [
            self.alert_presenter.present(item, period_ref=period_ref, kpis=kpi_lookup)
            for item in technical_payload.get("alerts", [])
        ]

        insights = [
            self.insight_presenter.present(item, index=idx)
            for idx, item in enumerate(technical_payload.get("insights", []))
        ]
        insights.sort(key=lambda item: int(item.get("display_order", 99)))

        recommendations = [
            self.recommendation_presenter.present(item) for item in technical_payload.get("recommendations", [])
        ]

        recommendations_by_id = {str(item.get("recommendation_id")): item for item in recommendations}
        for alert in alerts:
            rec_ids = [rid for rid in alert.get("related_recommendation_ids", []) if rid in recommendations_by_id]
            alert["related_recommendation_ids"] = rec_ids

        all_kpi_ids = [str(item.get("id")) for item in presented_kpis if str(item.get("id"))]
        all_rule_ids = [str(item.get("rule_id")) for item in alerts if str(item.get("rule_id"))]
        all_rec_ids = [str(item.get("recommendation_id")) for item in recommendations if str(item.get("recommendation_id"))]

        for insight in insights:
            if not insight.get("related_kpis"):
                insight["related_kpis"] = all_kpi_ids[:3]
            if not insight.get("related_rules"):
                insight["related_rules"] = all_rule_ids[:3]
            if not insight.get("related_recommendations"):
                insight["related_recommendations"] = all_rec_ids[:3]

        for rec in recommendations:
            if not rec.get("related_kpis"):
                rec["related_kpis"] = all_kpi_ids[:3]
            if not rec.get("related_rules"):
                rec["related_rules"] = all_rule_ids[:3]

        raw_timeline_points = self._normalize_timeline_points(list(technical_payload.get("timeline", {}).get("points", [])))
        timeline_points = [
            self._present_timeline_point(point, idx, raw_timeline_points)
            for idx, point in enumerate(raw_timeline_points)
        ]

        top_kpis = presented_kpis[:8]
        kpi_overview = self._build_kpi_overview(presented_kpis)

        sections = self._present_sections(
            counts={
                "hero": 1,
                "highlights": 4,
                "kpis": len(presented_kpis),
                "alerts": len(alerts),
                "recommendations": len(recommendations),
                "insights": len(insights),
                "timeline": len(timeline_points),
            }
        )

        payload = {
            "summary_id": str(technical_payload.get("summary_id") or ""),
            "company_id": str(technical_payload.get("company_id") or ""),
            "period_ref": period_ref,
            "generated_at": str(technical_payload.get("generated_at") or ""),
            "hero": self._present_hero(executive_score, technical_payload),
            "highlights": self._present_highlights(
                presented_kpis,
                alerts,
                recommendations,
                executive_score,
                trends_payload,
                period_ref=period_ref,
            ),
            "sections": sections,
            "dashboard": self._present_dashboard(technical_payload),
            "scores": {
                "executive_score": executive_score,
                "financial": self._present_dimension_score("Financeiro", technical_payload, "financial"),
                "commercial": self._present_dimension_score("Comercial", technical_payload, "commercial"),
                "operational": self._present_dimension_score("Operacional", technical_payload, "operational"),
            },
            "top_kpis": top_kpis,
            # Deprecated alias kept only for Flutter backward compatibility.
            "kpis": top_kpis,
            "kpi_overview": kpi_overview,
            "alerts": alerts,
            "insights": insights,
            "recommendations": recommendations,
            "trends": trends_payload,
            "next_risks": [self._present_risk(item) for item in technical_payload.get("next_risks", [])],
            "timeline": {"points": timeline_points},
        }
        return self._prune_payload(payload)

    def _present_hero(self, executive_score: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        score = float(executive_score.get("overall", 0.0))
        max_score = 100
        monthly_value = float((payload.get("trends") or {}).get("today_vs_last_month") or 0.0)
        previous = max(0.0, score - monthly_value)
        dashboard = dict(payload.get("dashboard") or {})
        pipeline_status = str((dashboard.get("last_pipeline") or "unknown")).lower()
        data_quality = str(dashboard.get("data_quality") or "good")
        confidence_score = {"excellent": 0.98, "good": 0.9, "attention": 0.72, "critical": 0.45}.get(data_quality, 0.7)
        alerts = list(payload.get("alerts") or [])
        recommendations = list(payload.get("recommendations") or [])
        insights = list(payload.get("insights") or [])
        kpis = list(payload.get("kpis") or [])
        return {
            "title": str(self.catalog.get("strings", {}).get("summary_title", "Saude da Empresa")),
            "score": round(score),
            "max_score": max_score,
            "progress": round(score / max_score, 4) if max_score else 0.0,
            "grade": self.score_formatter.grade(score),
            "status": str(executive_score.get("status", "")),
            "status_color": str(executive_score.get("status_color", "info")),
            "status_icon": str(executive_score.get("status_icon", "insights")),
            "variation": str(executive_score.get("variation", "0%")),
            "comparison": str(executive_score.get("comparison", "")),
            "description": str(executive_score.get("description", "")),
            "last_updated": self.date_formatter.format_datetime(str(payload.get("generated_at") or "")),
            "score_trend": "up" if monthly_value > 0 else "down" if monthly_value < 0 else "stable",
            "previous_score": round(previous, 2),
            "confidence": self._confidence_label(str(((payload.get("dashboard") or {}).get("data_quality") or "good"))),
            "confidence_score": confidence_score,
            "pipeline_execution": pipeline_status,
            "alerts_active": len(alerts),
            "recommendations_active": len(recommendations),
            "insights_generated": len(insights),
            "kpis_calculated": len(kpis),
            "rules_triggered": len(alerts),
            "pipeline_status": pipeline_status,
            "pipeline_duration_ms": int(dashboard.get("pipeline_duration_ms") or 0),
            "data_quality": data_quality,
        }

    def _present_highlights(
        self,
        kpis: list[dict[str, Any]],
        alerts: list[dict[str, Any]],
        recommendations: list[dict[str, Any]],
        executive_score: dict[str, Any],
        trends: dict[str, Any],
        *,
        period_ref: str,
    ) -> list[dict[str, Any]]:
        highlights_catalog = self.catalog.get("highlights", {})

        revenue_card = dict(highlights_catalog.get("revenue", {}))
        revenue_value = kpis[0].get("formatted_value") if kpis else self.money_formatter.format(0.0)

        alerts_card = dict(highlights_catalog.get("alerts", {}))
        alerts_count = len(alerts)
        alerts_template = "{count} alerta ativo" if alerts_count == 1 else "{count} alertas ativos"

        recommendation_card = dict(highlights_catalog.get("recommendations", {}))
        recommendations_count = len(recommendations)
        recommendations_template = (
            "{count} recomendacao ativa" if recommendations_count == 1 else "{count} recomendacoes ativas"
        )

        trend_card = dict(highlights_catalog.get("trend", {}))
        monthly = trends.get("monthly", {})
        trend_direction = str(monthly.get("direction", "stable"))
        trend_value = str(monthly.get("display", "0%"))
        trend_template = str(trend_card.get(f"{trend_direction}_template", trend_card.get("stable_template", "Tendencia estavel")))
        if not trend_template:
            trend_template = "Tendencia estavel"

        executive_score_card = dict(highlights_catalog.get("executive_score", {}))
        executive_score_value = str(executive_score.get("display") or f"{int(round(float(executive_score.get('overall', 0.0))))} / 100")

        return [
            {
                "icon": str(revenue_card.get("icon", "payments")),
                "title": "Receita",
                "value": str(revenue_value),
                "subtitle": self.date_formatter.period_subtitle(period_ref),
                "color": str(revenue_card.get("color", "success")),
                "trend": "stable",
            },
            {
                "icon": str(alerts_card.get("icon", "warning")),
                "title": "Alertas ativos",
                "value": str(alerts_template or "{count} alertas ativos").format(count=alerts_count),
                "subtitle": self.date_formatter.period_subtitle(period_ref),
                "color": str(alerts_card.get("color", "warning")),
                "trend": "stable",
            },
            {
                "icon": str(trend_card.get("icon", "trending_up")),
                "title": "Tendencia de receita",
                "value": trend_template.format(value=trend_value) if "{value}" in trend_template else trend_template,
                "subtitle": self.date_formatter.period_subtitle(period_ref),
                "color": str(trend_card.get(f"color_{trend_direction}", trend_card.get("color_stable", "info"))),
                "trend": trend_direction,
            },
            {
                "icon": str(executive_score_card.get("icon", "workspace_premium")),
                "title": "Executive Score",
                "value": str(executive_score_card.get("template", "Executive Score {value}")).format(value=executive_score_value),
                "subtitle": self.date_formatter.period_subtitle(period_ref),
                "color": str(executive_score_card.get("color", "primary")),
                "trend": "stable",
            },
        ]

    def _present_sections(self, *, counts: dict[str, int]) -> list[dict[str, Any]]:
        sections = []
        for item in self.catalog.get("sections", []):
            section_type = str(item.get("type", ""))
            count = int(counts.get(section_type, 0))
            title = str(item.get("title", section_type.title()))
            empty_message = str(item.get("empty_message", "Sem dados para esta secao."))
            if section_type == "kpis":
                title = "Metricas prioritarias"
                empty_message = "Nenhuma metrica disponivel para este periodo."
            sections.append(
                {
                    "type": section_type,
                    "title": title,
                    "visible": True if section_type in {"hero", "highlights"} else count > 0,
                    "count": count,
                    "empty_message": empty_message,
                }
            )
        return sections

    def _present_dashboard(self, payload: dict[str, Any]) -> dict[str, Any]:
        technical = dict(payload.get("dashboard") or {})
        defaults = dict(self.catalog.get("dashboard", {}))
        return {
            "last_import": technical.get("last_import"),
            "last_pipeline": technical.get("last_pipeline", "unknown"),
            "pipeline_duration_ms": technical.get("pipeline_duration_ms"),
            "summary_version": str(technical.get("summary_version") or defaults.get("summary_version", "3.1")),
            "formula_dsl_version": str(technical.get("formula_dsl_version") or self.catalog.get("official_formula_dsl_version") or "2.0.0"),
            "kpi_catalog_version": str(technical.get("kpi_catalog_version") or self.catalog.get("official_kpi_catalog_version") or "1.0.0"),
            "canonical_model_version": str(technical.get("canonical_model_version") or self.catalog.get("official_canonical_model_version") or "2.0.0"),
            "pipeline_version": str(technical.get("pipeline_version") or "1.0.0"),
            "refresh_interval_seconds": int(
                technical.get("refresh_interval_seconds") or defaults.get("refresh_interval_seconds", 300)
            ),
            "data_quality": str(technical.get("data_quality") or "good"),
        }

    def _present_dimension_score(self, label: str, payload: dict[str, Any], key: str) -> dict[str, Any]:
        raw_value = float((payload.get("scores") or {}).get(key, 0.0))
        meta = self.score_formatter.format(raw_value)
        return {
            "label": label,
            "value": raw_value,
            "display": str(round(raw_value)),
            "health": meta["status"],
            "health_color": meta["status_color"],
            "health_icon": meta["status_icon"],
            "description": meta["description"],
            "status": meta["status"],
            "status_color": meta["status_color"],
        }

    def _present_trends(self, trends: dict[str, Any]) -> dict[str, Any]:
        monthly = self._normalize_trend_value(trends.get("today_vs_last_month"))
        yearly = self._normalize_trend_value(trends.get("today_vs_last_year"))

        monthly_direction = self.trend_formatter.direction(monthly)
        yearly_direction = self.trend_formatter.direction(yearly)

        return {
            "monthly": {
                "value": monthly,
                "display": self.trend_formatter.label(monthly),
                "direction": monthly_direction,
                "trend_icon": self.trend_formatter.icon(monthly_direction),
                "trend_color": self.trend_formatter.color(monthly_direction),
                "trend_description": self.trend_formatter.description(monthly_direction),
                "icon": self.trend_formatter.icon(monthly_direction),
                "color": self.trend_formatter.color(monthly_direction),
                "description": self.trend_formatter.description(monthly_direction),
            },
            "yearly": {
                "value": yearly,
                "display": self.trend_formatter.label(yearly),
                "direction": yearly_direction,
                "trend_icon": self.trend_formatter.icon(yearly_direction),
                "trend_color": self.trend_formatter.color(yearly_direction),
                "trend_description": self.trend_formatter.description(yearly_direction),
                "icon": self.trend_formatter.icon(yearly_direction),
                "color": self.trend_formatter.color(yearly_direction),
                "description": self.trend_formatter.description(yearly_direction),
            },
        }

    def _normalize_trend_value(self, value: Any) -> float:
        numeric = float(value or 0.0)
        if abs(numeric) <= 1.0:
            return numeric * 100.0
        return numeric

    def _present_timeline_point(self, point: dict[str, Any], index: int, all_points: list[dict[str, Any]]) -> dict[str, Any]:
        score = float(point.get("overall_score", 0.0))
        score_meta = self.score_formatter.format(score)
        raw_date = str(point.get("snapshot_date") or "")
        month, year, formatted_label = self.date_formatter.timeline_label(raw_date)

        trend = "stable"
        if index > 0:
            previous = float(all_points[index - 1].get("overall_score", 0.0))
            trend = self.trend_formatter.direction(score - previous)

        description = self.catalog.get("strings", {}).get(
            "timeline_current_description" if index == len(all_points) - 1 else "timeline_previous_description",
            "",
        )

        return {
            "label": formatted_label,
            "month": month,
            "year": year,
            "formatted_label": formatted_label,
            "formatted_date": self.date_formatter.format_date(raw_date),
            "overall_score": score,
            "status": score_meta["status"],
            "status_color": score_meta["status_color"],
            "trend": trend,
            "description": str(description),
            "trend_description": self.trend_formatter.description(trend),
        }

    def _normalize_timeline_points(self, points: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not points:
            return points
        unique_by_date: dict[str, dict[str, Any]] = {}
        for item in points:
            snapshot_date = str(item.get("snapshot_date") or "")
            if snapshot_date and snapshot_date not in unique_by_date:
                unique_by_date[snapshot_date] = dict(item)

        def _date_key(value: str) -> datetime:
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return datetime.min

        return [
            unique_by_date[key]
            for key in sorted(unique_by_date.keys(), key=_date_key)
        ]

    def _build_kpi_overview(self, kpis: list[dict[str, Any]]) -> dict[str, Any]:
        def _health_status(item: dict[str, Any]) -> str:
            status = str((item.get("health") or {}).get("status") or "attention")
            if status in {"good", "healthy"}:
                return "healthy"
            if status in {"critical", "error"}:
                return "critical"
            return "warning"

        def _category_label(category: str) -> str:
            lowered = category.strip().lower()
            if lowered in {"financeiro", "econômico", "economico"}:
                return "Financeiro"
            if lowered in {"comercial"}:
                return "Comercial"
            if lowered in {"operacional", "operations"}:
                return "Operacional"
            if lowered in {"estoque", "inventory"}:
                return "Estoque"
            if lowered in {"clientes", "customer", "customers"}:
                return "Clientes"
            if lowered in {"rh", "people", "recursos humanos"}:
                return "RH"
            if lowered in {"fiscal", "tax"}:
                return "Fiscal"
            if lowered in {"executivo", "executive"}:
                return "Executivo"
            return (category or "Operacional").strip().title() or "Operacional"

        def _category_id(label: str) -> str:
            mapping = {
                "Financeiro": "financial",
                "Comercial": "commercial",
                "Operacional": "operational",
                "Estoque": "inventory",
                "Clientes": "customers",
                "RH": "hr",
                "Fiscal": "fiscal",
                "Executivo": "executive",
            }
            return mapping.get(label, label.lower().replace(" ", "_"))

        status_weights = {"healthy": 100.0, "warning": 60.0, "critical": 20.0}
        healthy = 0
        warning = 0
        critical = 0
        grouped: dict[str, list[dict[str, Any]]] = {}
        for item in kpis:
            status = _health_status(item)
            if status == "healthy":
                healthy += 1
            elif status == "critical":
                critical += 1
            else:
                warning += 1

            cat_label = _category_label(str(item.get("category") or "Operacional"))
            grouped.setdefault(cat_label, []).append(item)

        catalog_kpis = self.catalog.get("kpis", {}) if isinstance(self.catalog.get("kpis"), dict) else {}
        total_catalog = len(
            [
                key
                for key, meta in catalog_kpis.items()
                if key != "default" and isinstance(meta, dict)
            ]
        )

        catalog_category_labels = {
            _category_label(str(meta.get("category") or "Operacional"))
            for key, meta in catalog_kpis.items()
            if key != "default" and isinstance(meta, dict)
        }

        preferred_order = [
            "Financeiro",
            "Comercial",
            "Operacional",
            "Estoque",
            "Clientes",
            "RH",
            "Fiscal",
            "Executivo",
        ]
        for label in preferred_order:
            grouped.setdefault(label, [])
        for label in catalog_category_labels:
            grouped.setdefault(label, [])

        ordered_labels = preferred_order + sorted(
            [label for label in grouped.keys() if label not in set(preferred_order)]
        )

        categories: list[dict[str, Any]] = []
        for cat_label in ordered_labels:
            items = grouped.get(cat_label, [])
            cat_healthy = sum(1 for item in items if _health_status(item) == "healthy")
            cat_warning = sum(1 for item in items if _health_status(item) == "warning")
            cat_critical = sum(1 for item in items if _health_status(item) == "critical")
            weighted = [status_weights[_health_status(item)] for item in items]
            average_score = round(sum(weighted) / len(weighted), 2) if weighted else 0.0

            top_kpi = max(items, key=lambda item: status_weights[_health_status(item)]) if items else None
            worst_kpi = min(items, key=lambda item: status_weights[_health_status(item)]) if items else None

            categories.append(
                {
                    "id": _category_id(cat_label),
                    "label": cat_label,
                    "average_score": average_score,
                    "healthy": cat_healthy,
                    "warning": cat_warning,
                    "critical": cat_critical,
                    "top_kpi": {
                        "id": str(top_kpi.get("id") or ""),
                        "name": str(top_kpi.get("title") or ""),
                        "score": status_weights[_health_status(top_kpi)] if top_kpi else 0.0,
                    }
                    if top_kpi
                    else None,
                    "worst_kpi": {
                        "id": str(worst_kpi.get("id") or ""),
                        "name": str(worst_kpi.get("title") or ""),
                        "score": status_weights[_health_status(worst_kpi)] if worst_kpi else 0.0,
                    }
                    if worst_kpi
                    else None,
                }
            )

        return {
            "total": total_catalog,
            "healthy": healthy,
            "warning": warning,
            "critical": critical,
            "categories": categories,
        }

    @staticmethod
    def _confidence_label(data_quality: str) -> str:
        if data_quality in {"excellent", "good"}:
            return "Alta"
        if data_quality in {"attention"}:
            return "Media"
        return "Baixa"

    def _present_risk(self, item: dict[str, Any]) -> dict[str, Any]:
        probability = float(item.get("probability", 0.0))
        return {
            "title": str(item.get("title") or "Risco monitorado"),
            "summary": str(item.get("description") or "Risco identificado para acompanhamento."),
            "probability": self.percent_formatter.format(probability * 100.0, decimals=0, include_sign=False),
        }

    def _prune_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        def _clean(value: Any) -> Any:
            if isinstance(value, dict):
                cleaned = {k: _clean(v) for k, 
                           v in value.items()}
                return {k: v for k, v in cleaned.items() if v is not None and v != ""}
            if isinstance(value, list):
                cleaned_list = [_clean(v) for v in value]
                return [v for v in cleaned_list if v is not None and v != ""]
            if isinstance(value, str):
                normalized = value.strip()
                if normalized in {"", "Nao informado"}:
                    return None
                return normalized
            return value

        cleaned_payload = _clean(payload)
        if isinstance(cleaned_payload, dict):
            return cleaned_payload
        return payload
