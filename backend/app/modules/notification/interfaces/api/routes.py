from fastapi import APIRouter

router = APIRouter(prefix="/notification", tags=["notification"])


@router.get("/health")
def module_health() -> dict[str, str]:
    return {"module": "notification", "status": "ok"}
