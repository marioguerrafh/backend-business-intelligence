from fastapi import APIRouter

from app.modules.ai.interfaces.api.routes import router as ai_router
from app.modules.alert.interfaces.api.routes import router as alert_router
from app.modules.auth.interfaces.api.routes import router as auth_router
from app.modules.business.interfaces.api.routes import router as business_customer_router
from app.modules.business.interfaces.api.product_routes import router as business_product_router
from app.modules.company.interfaces.api.routes import router as company_router
from app.modules.executive_score.interfaces.api.routes import router as executive_score_router
from app.modules.imports.interfaces.api.routes import router as imports_router
from app.modules.insight.interfaces.api.routes import router as insight_router
from app.modules.kpi.interfaces.api.routes import router as kpi_router
from app.modules.kpi.interfaces.api.explorer_routes import router as kpi_explorer_router
from app.modules.notification.interfaces.api.routes import router as notification_router
from app.modules.omie.interfaces.api.routes import router as omie_router
from app.modules.pipeline.interfaces.api.routes import router as pipeline_router
from app.modules.recommendation.interfaces.api.routes import router as recommendation_router
from app.modules.rule.interfaces.api.routes import router as rule_router
from app.modules.summary.interfaces.api.routes import router as summary_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(business_customer_router)
api_v1_router.include_router(business_product_router)
api_v1_router.include_router(company_router)
api_v1_router.include_router(executive_score_router)
api_v1_router.include_router(imports_router)
api_v1_router.include_router(pipeline_router)
api_v1_router.include_router(omie_router)
api_v1_router.include_router(kpi_router)
api_v1_router.include_router(kpi_explorer_router)
api_v1_router.include_router(insight_router)
api_v1_router.include_router(alert_router)
api_v1_router.include_router(recommendation_router)
api_v1_router.include_router(ai_router)
api_v1_router.include_router(notification_router)
api_v1_router.include_router(rule_router)
api_v1_router.include_router(summary_router)
