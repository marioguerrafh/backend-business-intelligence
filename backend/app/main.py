from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.settings import settings
from app.shared.interfaces.api.correlation_id_middleware import CorrelationIdMiddleware
from app.shared.interfaces.api.health import router as health_router
from app.shared.interfaces.api.v1_router import api_v1_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Place startup hooks (db checks, messaging wiring) here.
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    lifespan=lifespan,
)
app.add_middleware(CorrelationIdMiddleware)

app.include_router(health_router)
app.include_router(api_v1_router, prefix=settings.api_v1_prefix)
