from fastapi import APIRouter

router = APIRouter(prefix="/alert", tags=["alert"])


@router.get("/health")
def module_health() -> dict[str, str]:
    return {"module": "alert", "status": "ok"}
