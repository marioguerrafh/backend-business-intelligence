from fastapi import APIRouter

router = APIRouter(prefix="/recommendation", tags=["recommendation"])


@router.get("/health")
def module_health() -> dict[str, str]:
    return {"module": "recommendation", "status": "ok"}
