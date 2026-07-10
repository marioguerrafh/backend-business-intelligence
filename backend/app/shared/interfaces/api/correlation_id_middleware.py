from collections.abc import Awaitable, Callable

from fastapi import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from app.shared.domain.primitives.correlation_id import CorrelationId


class CorrelationIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        incoming = request.headers.get("X-Correlation-ID")
        correlation = CorrelationId.from_header(incoming)
        scope.setdefault("state", {})
        scope["state"]["correlation_id"] = correlation.value

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                headers.append((b"x-correlation-id", correlation.value.encode("utf-8")))
            await send(message)

        await self.app(scope, receive, send_wrapper)
