from datetime import datetime, timezone

from app.modules.auth.application.ports.clock import Clock


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
