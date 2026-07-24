"""Window manager for time-based synchronization partitioning."""
from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterator

from app.modules.synchronization.domain.entities import TimeWindow


@dataclass(slots=True)
class WindowManager:
    """Manages time windows for synchronization."""

    def generate_monthly_windows(
        self,
        start_date: date,
        end_date: date,
    ) -> Iterator[TimeWindow]:
        """Generate monthly windows between start and end dates."""
        current = start_date.replace(day=1)
        final = end_date

        while current <= final:
            # Calculate last day of current month
            last_day = monthrange(current.year, current.month)[1]
            window_end = min(
                date(current.year, current.month, last_day),
                final,
            )

            yield TimeWindow(start_date=current, end_date=window_end)

            # Move to first day of next month
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)

    def generate_daily_windows(
        self,
        start_date: date,
        end_date: date,
        days_per_window: int = 7,
    ) -> Iterator[TimeWindow]:
        """Generate daily windows with specified number of days per window."""
        if days_per_window < 1:
            raise ValueError("days_per_window must be at least 1")

        current = start_date
        final = end_date

        while current <= final:
            window_end = min(
                current + timedelta(days=days_per_window - 1),
                final,
            )

            yield TimeWindow(start_date=current, end_date=window_end)

            # Move to next window
            current = window_end + timedelta(days=1)

    def generate_single_window(
        self,
        start_date: date,
        end_date: date,
    ) -> TimeWindow:
        """Generate a single window for the entire period."""
        return TimeWindow(start_date=start_date, end_date=end_date)

    def calculate_windows_for_domain(
        self,
        *,
        domain: str,
        window_days: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[TimeWindow]:
        """Calculate appropriate windows for a domain based on configuration."""
        if end_date is None:
            end_date = date.today()

        if start_date is None:
            # Default to last window_days if no start date specified
            start_date = end_date - timedelta(days=window_days - 1)

        if window_days <= 0:
            # Single window for entire period
            return [self.generate_single_window(start_date, end_date)]

        if window_days >= 30:
            # Use monthly windows for large periods
            return list(self.generate_monthly_windows(start_date, end_date))

        # Use daily windows
        return list(self.generate_daily_windows(start_date, end_date, window_days))

    def get_next_window_after_checkpoint(
        self,
        *,
        checkpoint_window_end: date,
        final_end_date: date,
        days_per_window: int,
    ) -> TimeWindow | None:
        """Get the next window after a checkpoint's last window."""
        next_start = checkpoint_window_end + timedelta(days=1)

        if next_start > final_end_date:
            return None

        next_end = min(
            next_start + timedelta(days=days_per_window - 1),
            final_end_date,
        )

        return TimeWindow(start_date=next_start, end_date=next_end)
