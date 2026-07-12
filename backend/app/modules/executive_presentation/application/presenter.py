from __future__ import annotations

from dataclasses import dataclass
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

        short_name = str(meta.get("short_name", "Indicador"))
        display_name = str(meta.get("display_name", short_name))
        description = str(meta.get("description", ""))
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
        kpi_id = str(item.get("kpi_id") or "")
        rule_id = str(item.get("rule_id") or "")

        alerts_catalog = self.catalog.get("alerts", {})
        by_rule = alerts_catalog.get("by_rule", {})
        by_kpi = alerts_catalog.get("by_kpi", {})

        meta = dict(by_rule.get(rule_id, by_kpi.get(kpi_id, alerts_catalog.get("default", {}))))
        kpi_meta = self.catalog.get("kpis", {}).get(kpi_id, self.catalog.get("kpis", {}).get("default", {}))
        kpi_name = str(kpi_meta.get("display_name", kpi_id or "Indicador"))

        metric_raw = item.get("metric_value")
        metric_value = float(metric_raw) if metric_raw is not None else None

        kpi_value = kpis.get(kpi_id, {}).get("value")
        if kpi_value is None and metric_value is not None:
            kpi_value = metric_value
        if kpi_value is None:
            kpi_display = ""
        else:
            kpi_display = self.money_formatter.format(float(kpi_value), "BRL")

        impact: dict[str, Any] | None = None
        if metric_value is not None and abs(metric_value) > 0:
            impact = {
                "label": str(self.catalog.get("strings", {}).get("impact_label", "Impacto estimado")),
                "display_value": self.money_formatter.format(abs(metric_value), "BRL"),
                "description": f"Impacto financeiro estimado sobre {kpi_name.lower()}.",
            }

        title_template = str(meta.get("title_template", "{kpi_name} com desvio relevante"))
        message_template = str(
            meta.get("message_template", "O indicador {kpi_name} apresentou variacao fora do esperado para este periodo.")
        )
        title_value = str(meta.get("title") or title_template.format(kpi_name=kpi_name))
        message_value = str(meta.get("message") or message_template.format(kpi_name=kpi_name))

        return {
            "alert_id": str(item.get("alert_id") or ""),
            "severity": self.severity_formatter.format(str(item.get("severity") or "INFO")),
            "priority": str(item.get("priority") or "").upper(),
            "category": str(meta.get("category", kpi_meta.get("category", "Operacional"))),
            "title": title_value,
            "subtitle": self.date_formatter.period_subtitle(period_ref),
            "message": message_value,
            "impact": impact,
            "kpi": {
                "name": kpi_name,
                "display_value": kpi_display,
                "description": str(kpi_meta.get("description", "")),
            },
            "recommended_action": str(self.catalog.get("strings", {}).get("recommended_action", "Ver recomendacoes")),
            "details_available": True,
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
            "summary": statement,
            "importance": str(meta.get("importance", "medium")),
            "icon": str(meta.get("icon", "lightbulb")),
            "category": str(meta.get("category", "Executivo")),
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
            impact_display = "Nao informado"
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
            "estimated_effort": str(defaults.get("estimated_effort", "media")),
            "estimated_time": str(defaults.get("estimated_time", "7 dias")),
            "category": category,
            "icon": str(defaults.get("icon", "task_alt")),
            "color": str(defaults.get("color", "primary")),
            "action_button": str(defaults.get("action_button", "Ver plano de acao")),
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

        raw_timeline_points = list(technical_payload.get("timeline", {}).get("points", []))
        timeline_points = [
            self._present_timeline_point(point, idx, technical_payload.get("timeline", {}).get("points", []))
            for idx, point in enumerate(raw_timeline_points)
        ]

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
            "kpis": presented_kpis,
            "alerts": alerts,
            "insights": insights,
            "recommendations": recommendations,
            "trends": trends_payload,
            "next_risks": [self._present_risk(item) for item in technical_payload.get("next_risks", [])],
            "timeline": {"points": timeline_points},
        }
        return payload

    def _present_hero(self, executive_score: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        score = float(executive_score.get("overall", 0.0))
        max_score = 100
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
        }

    def _present_highlights(
        self,
        kpis: list[dict[str, Any]],
        alerts: list[dict[str, Any]],
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
        alerts_template = alerts_card.get("singular_template") if alerts_count == 1 else alerts_card.get("plural_template")

        trend_card = dict(highlights_catalog.get("trend", {}))
        monthly = trends.get("monthly", {})
        trend_direction = str(monthly.get("direction", "stable"))
        trend_value = str(monthly.get("display", "0%"))
        trend_template = str(trend_card.get(f"{trend_direction}_template", trend_card.get("stable_template", "")))

        score_card = dict(highlights_catalog.get("executive_score", {}))

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
                "value": trend_template.format(value=trend_value),
                "subtitle": self.date_formatter.period_subtitle(period_ref),
                "color": str(trend_card.get(f"color_{trend_direction}", trend_card.get("color_stable", "info"))),
                "trend": trend_direction,
            },
            {
                "icon": str(score_card.get("icon", "workspace_premium")),
                "title": "Executive Score",
                "value": str(score_card.get("template", "Executive Score {value}")).format(
                    value=executive_score.get("display", "0")
                ),
                "subtitle": self.date_formatter.period_subtitle(period_ref),
                "color": str(score_card.get("color", "primary")),
                "trend": "stable",
            },
        ]

    def _present_sections(self, *, counts: dict[str, int]) -> list[dict[str, Any]]:
        sections = []
        for item in self.catalog.get("sections", []):
            section_type = str(item.get("type", ""))
            count = int(counts.get(section_type, 0))
            sections.append(
                {
                    "type": section_type,
                    "title": str(item.get("title", section_type.title())),
                    "visible": True if section_type in {"hero", "highlights"} else count > 0,
                    "count": count,
                    "empty_message": str(item.get("empty_message", "Sem dados para esta secao.")),
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
        if index + 1 < len(all_points):
            previous = float(all_points[index + 1].get("overall_score", 0.0))
            trend = self.trend_formatter.direction(score - previous)

        description = self.catalog.get("strings", {}).get(
            "timeline_current_description" if index == 0 else "timeline_previous_description",
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

    def _present_risk(self, item: dict[str, Any]) -> dict[str, Any]:
        probability = float(item.get("probability", 0.0))
        return {
            "title": str(item.get("title") or "Risco monitorado"),
            "summary": str(item.get("description") or "Risco identificado para acompanhamento."),
            "probability": self.percent_formatter.format(probability * 100.0, decimals=0, include_sign=False),
        }
