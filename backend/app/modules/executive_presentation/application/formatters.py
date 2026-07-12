from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


def _format_pt_number(value: float, decimals: int = 2) -> str:
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


@dataclass(slots=True)
class MoneyFormatter:
    def format(self, value: float, currency: str = "BRL") -> str:
        symbol = "R$" if currency.upper() == "BRL" else currency.upper()
        abs_value = abs(value)

        if abs_value >= 1_000_000:
            short = _format_pt_number(value / 1_000_000, decimals=2)
            return f"{symbol} {short} mi"
        if abs_value >= 1_000:
            short = _format_pt_number(value / 1_000, decimals=0)
            return f"{symbol} {short} mil"
        return f"{symbol} {_format_pt_number(value, decimals=2)}"


@dataclass(slots=True)
class PercentFormatter:
    def format(self, value: float, decimals: int = 1, *, include_sign: bool = True) -> str:
        sign = ""
        if include_sign:
            sign = "+" if value > 0 else "-" if value < 0 else ""
        magnitude = abs(value)
        return f"{sign}{_format_pt_number(magnitude, decimals)}%"


@dataclass(slots=True)
class QuantityFormatter:
    def format(self, value: float, decimals: int = 0) -> str:
        return _format_pt_number(value, decimals)


@dataclass(slots=True)
class DateFormatter:
    catalog: dict[str, Any]

    def period_subtitle(self, period_ref: str) -> str:
        if "-" not in period_ref:
            return period_ref
        year, month = period_ref.split("-", 1)
        month_name = str(self.catalog.get("locale", {}).get("months", {}).get(month, month))
        return f"{month_name} de {year}"

    def format_date(self, iso_date: str) -> str:
        try:
            parsed = datetime.fromisoformat(iso_date)
        except ValueError:
            return iso_date
        return parsed.strftime("%d/%m/%Y")

    def format_datetime(self, iso_date: str) -> str:
        try:
            parsed = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        except ValueError:
            return iso_date
        return parsed.strftime("%d/%m/%Y %H:%M")

    def timeline_label(self, iso_date: str) -> tuple[str, int, str]:
        try:
            parsed = datetime.fromisoformat(iso_date)
        except ValueError:
            return iso_date, 0, iso_date
        month = parsed.strftime("%m")
        year = parsed.year
        short = str(self.catalog.get("locale", {}).get("months_short", {}).get(month, month))
        return short, year, f"{short}/{str(year)[-2:]}"


@dataclass(slots=True)
class TrendFormatter:
    catalog: dict[str, Any]
    percent_formatter: PercentFormatter

    def direction(self, value: float | None) -> str:
        if value is None:
            return "stable"
        if value > 0:
            return "up"
        if value < 0:
            return "down"
        return "stable"

    def color(self, direction: str) -> str:
        return str(self.catalog.get("trends", {}).get(direction, {}).get("color", "info"))

    def icon(self, direction: str) -> str:
        return str(self.catalog.get("trends", {}).get(direction, {}).get("icon", "trending_flat"))

    def description(self, direction: str) -> str:
        return str(self.catalog.get("trends", {}).get(direction, {}).get("description", ""))

    def label(self, value: float | None) -> str:
        if value is None:
            return "0,0%"
        return self.percent_formatter.format(value, decimals=1)


@dataclass(slots=True)
class SeverityFormatter:
    catalog: dict[str, Any]

    def format(self, code: str) -> dict[str, str]:
        normalized = code.upper()
        mapping = self.catalog.get("severity", {})
        data = mapping.get(normalized, mapping.get("INFO", {}))
        return {
            "code": normalized,
            "label": str(data.get("label", normalized.title())),
            "color": str(data.get("color", "info")),
            "icon": str(data.get("icon", "info")),
        }


@dataclass(slots=True)
class ScoreFormatter:
    catalog: dict[str, Any]

    def format(self, score: float) -> dict[str, str]:
        thresholds = list(self.catalog.get("score", {}).get("thresholds", []))
        for item in thresholds:
            if score >= float(item.get("min", 0)):
                return {
                    "display": str(round(score)),
                    "status": str(item.get("status", "Boa")),
                    "status_description": str(item.get("description", "")),
                    "status_color": str(item.get("color", "success")),
                    "status_icon": str(item.get("icon", "insights")),
                    "description": str(item.get("description", "Resumo executivo disponivel.")),
                }
        return {
            "display": str(round(score)),
            "status": "Boa",
            "status_description": "",
            "status_color": "success",
            "status_icon": "insights",
            "description": "Resumo executivo disponivel.",
        }

    def grade(self, score: float) -> str:
        if score >= 95:
            return "A+"
        if score >= 80:
            return "B"
        if score >= 65:
            return "C"
        if score >= 50:
            return "D"
        if score >= 35:
            return "E"
        return "F"


@dataclass(slots=True)
class HealthMapper:
    catalog: dict[str, Any]

    def map(self, raw: str | None) -> dict[str, str]:
        status = str(raw or "attention").lower()
        table = self.catalog.get("health", {})
        mapped = table.get(status, table.get("attention", {}))
        return {
            "status": status,
            "label": str(mapped.get("label", "Atencao")),
            "color": str(mapped.get("color", "warning")),
            "icon": str(mapped.get("icon", "warning")),
            "description": str(mapped.get("description", "Indicador requer acompanhamento.")),
        }
