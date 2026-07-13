from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class KpiExplorerItemResponse(BaseModel):
    id: str
    name: str
    short_name: str
    description: str
    category: str
    value: float
    formatted_value: str
    unit: str
    trend: str
    trend_label: str
    trend_icon: str
    trend_color: str
    health: str
    status: str
    icon: str
    display_order: int


class KpiExplorerCategoryResponse(BaseModel):
    id: str
    label: str
    icon: str
    items: list[KpiExplorerItemResponse]


class KpiExplorerListResponse(BaseModel):
    company_id: str
    period_ref: str
    categories: list[KpiExplorerCategoryResponse]


class KpiCatalogItemResponse(BaseModel):
    id: str
    name: str
    short_name: str
    description: str
    category: str
    unit: str
    icon: str
    display_order: int
    formula_id: str


class KpiCatalogCategoryResponse(BaseModel):
    id: str
    label: str
    icon: str
    items: list[KpiCatalogItemResponse]


class KpiCatalogResponse(BaseModel):
    total: int
    categories: list[KpiCatalogCategoryResponse]


class KpiCurrentValueResponse(BaseModel):
    value: float
    formatted_value: str
    unit: str
    period_ref: str
    trend: str
    health: str
    status: str


class KpiFormulaResponse(BaseModel):
    formula_id: str
    expression: str
    unit: str


class KpiHistoryItemResponse(BaseModel):
    period_ref: str
    value: float
    formatted_value: str
    trend: str
    health: str
    calculated_at: str


class KpiDetailResponse(BaseModel):
    id: str
    name: str
    short_name: str
    description: str
    category: str
    formula: KpiFormulaResponse
    current_value: KpiCurrentValueResponse
    history: list[KpiHistoryItemResponse]
    related_rules: list[dict[str, Any]]
    related_insights: list[dict[str, Any]]
    related_recommendations: list[dict[str, Any]]
    timeline: list[dict[str, Any]]