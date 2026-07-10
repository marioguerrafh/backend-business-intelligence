from fastapi import APIRouter

router = APIRouter(prefix="/kpi", tags=["kpi"])


@router.get("/health")
def module_health() -> dict[str, str]:
    return {"module": "kpi", "status": "ok"}
