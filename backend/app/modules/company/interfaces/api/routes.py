from fastapi import APIRouter

router = APIRouter(prefix="/company", tags=["company"])


@router.get("/health")
def module_health() -> dict[str, str]:
    return {"module": "company", "status": "ok"}
