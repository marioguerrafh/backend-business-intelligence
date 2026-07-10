from fastapi import APIRouter

router = APIRouter(prefix="/omie", tags=["omie"])


@router.get("/health")
def module_health() -> dict[str, str]:
    return {"module": "omie", "status": "ok"}
