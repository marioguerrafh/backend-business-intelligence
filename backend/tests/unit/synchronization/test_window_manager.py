"""Unit tests for WindowManager."""
import pytest
from datetime import date

from app.modules.synchronization.infrastructure.window_manager import WindowManager


class TestWindowManager:
    """Tests for WindowManager."""

    def test_generate_monthly_windows_single_month(self):
        """Test generating monthly windows for a single month."""
        manager = WindowManager()
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)

        windows = list(manager.generate_monthly_windows(start, end))

        assert len(windows) == 1
        assert windows[0].start_date == date(2024, 1, 1)
        assert windows[0].end_date == date(2024, 1, 31)
        assert windows[0].days == 31

    def test_generate_monthly_windows_multiple_months(self):
        """Test generating monthly windows for multiple months."""
        manager = WindowManager()
        start = date(2024, 1, 1)
        end = date(2024, 3, 31)

        windows = list(manager.generate_monthly_windows(start, end))

        assert len(windows) == 3
        # January
        assert windows[0].start_date == date(2024, 1, 1)
        assert windows[0].end_date == date(2024, 1, 31)
        # February
        assert windows[1].start_date == date(2024, 2, 1)
        assert windows[1].end_date == date(2024, 2, 29)  # 2024 is leap year
        # March
        assert windows[2].start_date == date(2024, 3, 1)
        assert windows[2].end_date == date(2024, 3, 31)

    def test_generate_monthly_windows_partial_month(self):
        """Test generating monthly windows with partial month."""
        manager = WindowManager()
        start = date(2024, 1, 15)
        end = date(2024, 2, 10)

        windows = list(manager.generate_monthly_windows(start, end))

        assert len(windows) == 2
        # January (partial)
        assert windows[0].start_date == date(2024, 1, 1)
        assert windows[0].end_date == date(2024, 1, 31)
        # February (partial)
        assert windows[1].start_date == date(2024, 2, 1)
        assert windows[1].end_date == date(2024, 2, 10)

    def test_generate_daily_windows_7_days(self):
        """Test generating weekly windows."""
        manager = WindowManager()
        start = date(2024, 1, 1)
        end = date(2024, 1, 21)

        windows = list(manager.generate_daily_windows(start, end, days_per_window=7))

        assert len(windows) == 3
        # Week 1
        assert windows[0].start_date == date(2024, 1, 1)
        assert windows[0].end_date == date(2024, 1, 7)
        # Week 2
        assert windows[1].start_date == date(2024, 1, 8)
        assert windows[1].end_date == date(2024, 1, 14)
        # Week 3
        assert windows[2].start_date == date(2024, 1, 15)
        assert windows[2].end_date == date(2024, 1, 21)

    def test_generate_daily_windows_30_days(self):
        """Test generating monthly windows (30 days)."""
        manager = WindowManager()
        start = date(2024, 1, 1)
        end = date(2024, 3, 1)

        windows = list(manager.generate_daily_windows(start, end, days_per_window=30))

        assert len(windows) == 3
        assert windows[0].days == 30
        assert windows[1].days == 30

    def test_generate_daily_windows_invalid_days(self):
        """Test that invalid days_per_window raises error."""
        manager = WindowManager()

        with pytest.raises(ValueError, match="days_per_window must be at least 1"):
            list(manager.generate_daily_windows(date(2024, 1, 1), date(2024, 1, 10), days_per_window=0))

    def test_generate_single_window(self):
        """Test generating a single window."""
        manager = WindowManager()
        start = date(2024, 1, 1)
        end = date(2024, 12, 31)

        window = manager.generate_single_window(start, end)

        assert window.start_date == start
        assert window.end_date == end
        assert window.days == 366  # 2024 is a leap year

    def test_calculate_windows_for_domain_small_window(self):
        """Test calculating windows for domain with small window."""
        manager = WindowManager()

        windows = manager.calculate_windows_for_domain(
            domain="sales",
            window_days=7,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 21),
        )

        assert len(windows) == 3

    def test_calculate_windows_for_domain_large_window(self):
        """Test calculating windows for domain with large window (monthly)."""
        manager = WindowManager()

        windows = manager.calculate_windows_for_domain(
            domain="customers",
            window_days=30,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
        )

        assert len(windows) == 3  # January, February, March

    def test_calculate_windows_for_domain_default_dates(self):
        """Test calculating windows with default dates."""
        manager = WindowManager()

        windows = manager.calculate_windows_for_domain(
            domain="sales",
            window_days=7,
        )

        assert len(windows) >= 1
        assert windows[-1].end_date == date.today()

    def test_get_next_window_after_checkpoint(self):
        """Test getting next window after checkpoint."""
        manager = WindowManager()
        checkpoint_end = date(2024, 1, 7)
        final_end = date(2024, 1, 21)

        window = manager.get_next_window_after_checkpoint(
            checkpoint_window_end=checkpoint_end,
            final_end_date=final_end,
            days_per_window=7,
        )

        assert window is not None
        assert window.start_date == date(2024, 1, 8)
        assert window.end_date == date(2024, 1, 14)

    def test_get_next_window_no_more_windows(self):
        """Test getting next window when no more windows available."""
        manager = WindowManager()
        checkpoint_end = date(2024, 1, 21)
        final_end = date(2024, 1, 21)

        window = manager.get_next_window_after_checkpoint(
            checkpoint_window_end=checkpoint_end,
            final_end_date=final_end,
            days_per_window=7,
        )

        assert window is None
