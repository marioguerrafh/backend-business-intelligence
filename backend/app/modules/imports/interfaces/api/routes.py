from fastapi import APIRouter

router = APIRouter(prefix="/imports", tags=["imports"])


@router.get("/health")
def module_health() -> dict[str, str]:
    return {"module": "imports", "status": "ok"}
