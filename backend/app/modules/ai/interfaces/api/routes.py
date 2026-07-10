from fastapi import APIRouter

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/health")
def module_health() -> dict[str, str]:
    return {"module": "ai", "status": "ok"}
