from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Service healthcheck")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
