from fastapi import APIRouter

router = APIRouter(prefix="/insight", tags=["insight"])


@router.get("/health")
def module_health() -> dict[str, str]:
    return {"module": "insight", "status": "ok"}
