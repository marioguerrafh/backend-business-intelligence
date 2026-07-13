from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.modules.executive_presentation.application.catalog import PresentationCatalog
from app.modules.executive_presentation.application.formatters import MoneyFormatter, PercentFormatter, QuantityFormatter
from app.modules.kpi.application.kpi_catalog_service import KpiCatalogService
from app.modules.kpi.infrastructure.kpi_catalog_yaml import YamlKpiCatalogReader
from app.modules.recommendation.infrastructure.models import RecommendationAuditLogModel
from app.modules.rule.infrastructure.models import RuleResultModel
from app.modules.summary.infrastructure.models import InsightResultModel, KPIResultModel, RecommendationResultModel, TimelineSnapshotModel


@dataclass(slots=True)
class KpiExplorerService:
    session: Session
    catalog_service: KpiCatalogService = field(init=False)
    presentation_catalog: dict[str, Any] = field(init=False)
    money: MoneyFormatter = field(init=False)
    percent: PercentFormatter = field(init=False)
    quantity: QuantityFormatter = field(init=False)

    def __post_init__(self) -> None:
        self.catalog_service = KpiCatalogService(reader=YamlKpiCatalogReader())
        self.presentation_catalog = PresentationCatalog().load()
        self.money = MoneyFormatter()
        self.percent = PercentFormatter()
        self.quantity = QuantityFormatter()

    def list_kpis(self, *, company_id: str, period_ref: str | None) -> dict[str, object]:
        all_kpis = self.catalog_service.list_all()
        effective_period = self._effective_period(company_id=company_id, period_ref=period_ref)
        results_by_kpi = self._latest_kpi_results(company_id=company_id, period_ref=effective_period)

        groups: dict[str, dict[str, object]] = {}
        for kpi in sorted(all_kpis, key=lambda item: int(item.get("display_order") or 999)):
            category_id, category_label, category_icon = self._category_meta(str(kpi.get("category") or ""))
            group = groups.setdefault(
                category_id,
                {
                    "id": category_id,
                    "label": category_label,
                    "icon": category_icon,
                    "items": [],
                },
            )

            row = results_by_kpi.get(str(kpi.get("id") or ""))
            item = self._present_kpi_item(kpi=kpi, row=row)
            group["items"].append(item)

        categories = list(groups.values())
        categories.sort(key=lambda item: str(item["label"]))
        return {
            "company_id": company_id,
            "period_ref": effective_period,
            "categories": categories,
        }

    def get_kpi_detail(self, *, company_id: str, kpi_id: str, period_ref: str | None) -> dict[str, object] | None:
        kpi = self.catalog_service.get_by_id(kpi_id)
        if kpi is None:
            return None

        effective_period = self._effective_period(company_id=company_id, period_ref=period_ref)
        current_row = self._latest_kpi_results(company_id=company_id, period_ref=effective_period).get(kpi_id)
        history_rows = self.session.execute(
            select(KPIResultModel)
            .where(
                KPIResultModel.company_id == company_id,
                KPIResultModel.kpi_id == kpi_id,
            )
            .order_by(desc(KPIResultModel.calculated_at))
            .limit(24)
        ).scalars().all()

        rule_rows = self.session.execute(
            select(RuleResultModel)
            .where(
                RuleResultModel.company_id == company_id,
                RuleResultModel.period_ref == effective_period,
                RuleResultModel.kpi_id == kpi_id,
            )
            .order_by(desc(RuleResultModel.fired_at))
            .limit(10)
        ).scalars().all()

        recommendation_rows = self.session.execute(
            select(RecommendationResultModel)
            .where(
                RecommendationResultModel.company_id == company_id,
                RecommendationResultModel.period_ref == effective_period,
            )
            .order_by(desc(RecommendationResultModel.rank_score))
        ).scalars().all()
        recommendation_map = {row.recommendation_id: row for row in recommendation_rows}

        related_recommendations: list[dict[str, object]] = []
        for rule in rule_rows:
            audits = self.session.execute(
                select(RecommendationAuditLogModel)
                .where(
                    RecommendationAuditLogModel.company_id == company_id,
                    RecommendationAuditLogModel.period_ref == effective_period,
                    RecommendationAuditLogModel.trigger_rule_id == rule.rule_id,
                )
                .order_by(desc(RecommendationAuditLogModel.created_at))
                .limit(3)
            ).scalars().all()
            for audit in audits:
                result_row = recommendation_map.get(audit.recommendation_id)
                if result_row is None:
                    continue
                related_recommendations.append(
                    {
                        "recommendation_id": result_row.recommendation_id,
                        "title": result_row.title,
                        "owner": result_row.owner_role or "time_executivo",
                        "estimated_gain": self._format_impact(result_row.expected_impact_json),
                    }
                )

        insights = self.session.execute(
            select(InsightResultModel)
            .where(
                InsightResultModel.company_id == company_id,
                InsightResultModel.period_ref == effective_period,
            )
            .order_by(desc(InsightResultModel.generated_at))
            .limit(10)
        ).scalars().all()

        related_insights = [
            {
                "insight_id": row.insight_result_id,
                "title": row.insight_type.replace("_", " ").title(),
                "summary": row.statement,
            }
            for row in insights
            if self._is_related_insight(kpi=kpi, statement=row.statement)
        ]

        timeline_rows = self.session.execute(
            select(TimelineSnapshotModel)
            .where(TimelineSnapshotModel.company_id == company_id)
            .order_by(desc(TimelineSnapshotModel.snapshot_date))
            .limit(12)
        ).scalars().all()

        current_value = float(current_row.value) if current_row is not None else 0.0
        current_unit = str((current_row.unit if current_row is not None else kpi.get("unit")) or "NUMBER")
        current_status = self._normalize_health(current_row.health if current_row is not None else None)

        return {
            "id": str(kpi.get("id") or kpi_id),
            "name": str(kpi.get("name") or "KPI"),
            "short_name": str(kpi.get("short_name") or kpi.get("name") or "KPI"),
            "description": str(kpi.get("description") or "Indicador executivo para acompanhamento."),
            "category": str(kpi.get("category") or "Executivo"),
            "formula": {
                "formula_id": str(kpi.get("formula_id") or ""),
                "expression": str(kpi.get("formula") or "Formula definida no catalogo oficial."),
                "unit": str(kpi.get("unit") or "NUMBER"),
            },
            "current_value": {
                "value": current_value,
                "formatted_value": self._format_value(current_value, current_unit),
                "unit": current_unit,
                "period_ref": effective_period,
                "trend": str((current_row.trend if current_row is not None else "stable") or "stable"),
                "health": current_status,
                "status": current_status,
            },
            "history": [
                {
                    "period_ref": row.period_ref,
                    "value": float(row.value),
                    "formatted_value": self._format_value(float(row.value), str(row.unit or kpi.get("unit") or "NUMBER")),
                    "trend": str(row.trend or "stable"),
                    "health": self._normalize_health(row.health),
                    "calculated_at": row.calculated_at.isoformat(),
                }
                for row in history_rows
            ],
            "related_rules": [
                {
                    "rule_id": row.rule_id,
                    "severity": row.severity,
                    "priority": row.priority,
                    "title": row.alert_title,
                    "description": row.alert_description,
                }
                for row in rule_rows
            ],
            "related_insights": related_insights,
            "related_recommendations": related_recommendations,
            "timeline": [
                {
                    "snapshot_date": row.snapshot_date.isoformat(),
                    "overall_score": float(row.overall_score),
                }
                for row in timeline_rows
            ],
        }

    def catalog(self) -> dict[str, object]:
        all_kpis = self.catalog_service.list_all()
        groups: dict[str, dict[str, object]] = {}

        for kpi in sorted(all_kpis, key=lambda item: int(item.get("display_order") or 999)):
            category_id, category_label, category_icon = self._category_meta(str(kpi.get("category") or ""))
            group = groups.setdefault(
                category_id,
                {
                    "id": category_id,
                    "label": category_label,
                    "icon": category_icon,
                    "items": [],
                },
            )
            group["items"].append(
                {
                    "id": str(kpi.get("id") or ""),
                    "name": str(kpi.get("name") or "KPI"),
                    "short_name": str(kpi.get("short_name") or kpi.get("name") or "KPI"),
                    "description": str(kpi.get("description") or "Indicador executivo para acompanhamento."),
                    "category": str(kpi.get("category") or "Executivo"),
                    "unit": str(kpi.get("unit") or "NUMBER"),
                    "icon": str(kpi.get("icon") or "insights"),
                    "display_order": int(kpi.get("display_order") or 999),
                    "formula_id": str(kpi.get("formula_id") or ""),
                }
            )

        categories = list(groups.values())
        categories.sort(key=lambda item: str(item["label"]))
        return {
            "total": len(all_kpis),
            "categories": categories,
        }

    def _effective_period(self, *, company_id: str, period_ref: str | None) -> str:
        if period_ref:
            return period_ref
        latest = self.session.execute(
            select(KPIResultModel)
            .where(KPIResultModel.company_id == company_id)
            .order_by(desc(KPIResultModel.calculated_at))
            .limit(1)
        ).scalar_one_or_none()
        if latest is not None:
            return latest.period_ref
        return ""

    def _latest_kpi_results(self, *, company_id: str, period_ref: str) -> dict[str, KPIResultModel]:
        if not period_ref:
            return {}
        rows = self.session.execute(
            select(KPIResultModel).where(
                KPIResultModel.company_id == company_id,
                KPIResultModel.period_ref == period_ref,
            )
        ).scalars().all()
        return {row.kpi_id: row for row in rows}

    def _present_kpi_item(self, *, kpi: dict[str, Any], row: KPIResultModel | None) -> dict[str, object]:
        unit = str((row.unit if row is not None else kpi.get("unit")) or "NUMBER")
        value = float(row.value) if row is not None else 0.0
        trend = str((row.trend if row is not None else "stable") or "stable").lower()
        health = self._normalize_health(row.health if row is not None else None)
        trend_label = self._trend_label(trend)

        return {
            "id": str(kpi.get("id") or ""),
            "name": str(kpi.get("name") or "KPI"),
            "short_name": str(kpi.get("short_name") or kpi.get("name") or "KPI"),
            "description": str(kpi.get("description") or "Indicador executivo para acompanhamento."),
            "category": str(kpi.get("category") or "Executivo"),
            "value": value,
            "formatted_value": self._format_value(value, unit),
            "unit": unit,
            "trend": trend,
            "trend_label": trend_label,
            "trend_icon": "trending_up" if trend == "up" else "trending_down" if trend == "down" else "trending_flat",
            "trend_color": "success" if trend == "up" else "error" if trend == "down" else "info",
            "health": health,
            "status": health,
            "icon": str(kpi.get("icon") or "insights"),
            "display_order": int(kpi.get("display_order") or 999),
        }

    def _format_value(self, value: float, unit: str) -> str:
        normalized = unit.upper()
        if normalized in {"BRL", "CURRENCY"}:
            return self.money.format(value, "BRL")
        if normalized in {"PERCENT", "%"}:
            return self.percent.format(value, decimals=1, include_sign=False)
        return self.quantity.format(value, decimals=0)

    @staticmethod
    def _trend_label(trend: str) -> str:
        if trend == "up":
            return "Crescimento"
        if trend == "down":
            return "Queda"
        return "Tendencia estavel"

    @staticmethod
    def _normalize_health(health: str | None) -> str:
        raw = str(health or "warning").lower()
        if raw in {"green", "good", "healthy"}:
            return "healthy"
        if raw in {"red", "critical", "error"}:
            return "critical"
        return "warning"

    @staticmethod
    def _category_meta(category: str) -> tuple[str, str, str]:
        normalized = category.strip().lower()
        if normalized in {"financeiro", "economico", "econômico", "fiscal"}:
            return "financial", "Financeiro", "payments"
        if normalized in {"comercial", "clientes"}:
            return "commercial", "Comercial", "storefront"
        if normalized in {"estoque"}:
            return "inventory", "Estoque", "inventory"
        if normalized in {"rh"}:
            return "hr", "RH", "badge"
        return "operational", "Operacional", "precision_manufacturing"

    @staticmethod
    def _format_impact(payload: dict[str, Any] | None) -> str:
        if not isinstance(payload, dict):
            return "Ganho estimado nao disponivel"
        value = payload.get("value")
        if value is None:
            return "Ganho estimado nao disponivel"
        unit = str(payload.get("unit") or "BRL").upper()
        if unit == "BRL":
            return f"R$ {float(value):.2f}".replace(".", ",")
        return f"{value} {unit}"

    @staticmethod
    def _is_related_insight(*, kpi: dict[str, Any], statement: str) -> bool:
        text = statement.lower()
        name = str(kpi.get("name") or "").lower()
        short = str(kpi.get("short_name") or "").lower()
        code = str(kpi.get("code") or "").lower()
        return any(part and part in text for part in {name, short, code})