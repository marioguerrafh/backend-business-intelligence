"""Unit tests for synchronization domain entities."""
import pytest
from datetime import date, datetime, timedelta

from app.modules.synchronization.domain.entities import SyncBatch, SyncCheckpoint, SyncJob, TimeWindow
from app.modules.synchronization.domain.value_objects import (
    CheckpointStatus,
    JobPriority,
    JobStatus,
    SyncDomain,
)


class TestTimeWindow:
    """Tests for TimeWindow entity."""

    def test_create_valid_window(self):
        """Test creating a valid time window."""
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)
        window = TimeWindow(start_date=start, end_date=end)

        assert window.start_date == start
        assert window.end_date == end
        assert window.days == 31
        assert window.window_id is not None

    def test_invalid_window_raises_error(self):
        """Test that invalid window raises error."""
        start = date(2024, 1, 31)
        end = date(2024, 1, 1)

        with pytest.raises(ValueError, match="start_date must be before"):
            TimeWindow(start_date=start, end_date=end)

    def test_single_day_window(self):
        """Test window with single day."""
        day = date(2024, 1, 1)
        window = TimeWindow(start_date=day, end_date=day)

        assert window.days == 1

    def test_to_dict(self):
        """Test window to dictionary conversion."""
        window = TimeWindow(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        result = window.to_dict()

        assert result["start_date"] == "2024-01-01"
        assert result["end_date"] == "2024-01-31"
        assert result["days"] == 31
        assert "window_id" in result


class TestSyncJob:
    """Tests for SyncJob entity."""

    def test_create_job(self):
        """Test creating a sync job."""
        job = SyncJob.create(
            company_id="company-1",
            provider="omie",
            domain=SyncDomain.SALES,
            priority=JobPriority.HIGH,
        )

        assert job.company_id == "company-1"
        assert job.provider == "omie"
        assert job.domain == SyncDomain.SALES
        assert job.priority == JobPriority.HIGH
        assert job.status == JobStatus.PENDING
        assert job.job_id is not None

    def test_start_job(self):
        """Test starting a job."""
        job = SyncJob.create(
            company_id="company-1",
            provider="omie",
            domain=SyncDomain.SALES,
        )

        job.start()

        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None

    def test_complete_job(self):
        """Test completing a job."""
        job = SyncJob.create(
            company_id="company-1",
            provider="omie",
            domain=SyncDomain.SALES,
        )
        job.start()

        job.complete(
            records_read=1000,
            records_imported=950,
            records_failed=50,
            pages_processed=10,
        )

        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        assert job.records_read == 1000
        assert job.records_imported == 950
        assert job.records_failed == 50
        assert job.pages_processed == 10

    def test_fail_job(self):
        """Test failing a job."""
        job = SyncJob.create(
            company_id="company-1",
            provider="omie",
            domain=SyncDomain.SALES,
        )
        job.start()

        job.fail("Connection timeout")

        assert job.status == JobStatus.FAILED
        assert job.failed_at is not None
        assert job.error_message == "Connection timeout"
        assert job.retry_count == 1

    def test_pause_and_resume_job(self):
        """Test pausing and resuming a job."""
        job = SyncJob.create(
            company_id="company-1",
            provider="omie",
            domain=SyncDomain.SALES,
        )
        job.start()

        job.pause()
        assert job.status == JobStatus.PAUSED

        job.resume()
        assert job.status == JobStatus.PENDING

    def test_cancel_job(self):
        """Test cancelling a job."""
        job = SyncJob.create(
            company_id="company-1",
            provider="omie",
            domain=SyncDomain.SALES,
        )

        job.cancel()
        assert job.status == JobStatus.CANCELLED

    def test_can_retry(self):
        """Test retry logic."""
        job = SyncJob.create(
            company_id="company-1",
            provider="omie",
            domain=SyncDomain.SALES,
        )
        job.max_retries = 3

        assert job.can_retry() is True

        job.retry_count = 3
        assert job.can_retry() is False

    def test_duration_calculation(self):
        """Test job duration calculation."""
        job = SyncJob.create(
            company_id="company-1",
            provider="omie",
            domain=SyncDomain.SALES,
        )

        # Not started yet
        assert job.duration_seconds is None

        job.start()
        job.complete(records_read=100, records_imported=100, records_failed=0, pages_processed=1)

        assert job.duration_seconds is not None
        assert job.duration_seconds >= 0


class TestSyncCheckpoint:
    """Tests for SyncCheckpoint entity."""

    def test_create_checkpoint(self):
        """Test creating a checkpoint."""
        checkpoint = SyncCheckpoint(
            checkpoint_id="cp-1",
            company_id="company-1",
            provider="omie",
            domain=SyncDomain.SALES,
            status=CheckpointStatus.ACTIVE,
        )

        assert checkpoint.checkpoint_id == "cp-1"
        assert checkpoint.status == CheckpointStatus.ACTIVE

    def test_update_progress(self):
        """Test updating checkpoint progress."""
        checkpoint = SyncCheckpoint(
            checkpoint_id="cp-1",
            company_id="company-1",
            provider="omie",
            domain=SyncDomain.SALES,
            status=CheckpointStatus.ACTIVE,
        )

        checkpoint.update_progress(page=5, cursor="cursor-123", processed_record="rec-100")

        assert checkpoint.last_page == 5
        assert checkpoint.last_cursor == "cursor-123"
        assert checkpoint.last_processed_record == "rec-100"

    def test_mark_completed(self):
        """Test marking checkpoint as completed."""
        checkpoint = SyncCheckpoint(
            checkpoint_id="cp-1",
            company_id="company-1",
            provider="omie",
            domain=SyncDomain.SALES,
            status=CheckpointStatus.ACTIVE,
        )

        checkpoint.mark_completed()

        assert checkpoint.status == CheckpointStatus.COMPLETED

    def test_mark_failed(self):
        """Test marking checkpoint as failed."""
        checkpoint = SyncCheckpoint(
            checkpoint_id="cp-1",
            company_id="company-1",
            provider="omie",
            domain=SyncDomain.SALES,
            status=CheckpointStatus.ACTIVE,
        )

        checkpoint.mark_failed()

        assert checkpoint.status == CheckpointStatus.FAILED


class TestSyncBatch:
    """Tests for SyncBatch entity."""

    def test_create_batch(self):
        """Test creating a batch."""
        batch = SyncBatch.create(company_id="company-1", provider="omie")

        assert batch.company_id == "company-1"
        assert batch.provider == "omie"
        assert batch.batch_id is not None
        assert len(batch.jobs) == 0

    def test_add_job_to_batch(self):
        """Test adding job to batch."""
        batch = SyncBatch.create(company_id="company-1", provider="omie")
        job = SyncJob.create(
            company_id="company-1",
            provider="omie",
            domain=SyncDomain.SALES,
        )

        batch.add_job(job)

        assert len(batch.jobs) == 1
        assert batch.jobs[0] == job

    def test_add_job_wrong_company_raises_error(self):
        """Test that adding job with wrong company raises error."""
        batch = SyncBatch.create(company_id="company-1", provider="omie")
        job = SyncJob.create(
            company_id="company-2",
            provider="omie",
            domain=SyncDomain.SALES,
        )

        with pytest.raises(ValueError, match="company_id does not match"):
            batch.add_job(job)

    def test_all_completed(self):
        """Test checking if all jobs are completed."""
        batch = SyncBatch.create(company_id="company-1", provider="omie")
        job1 = SyncJob.create(company_id="company-1", provider="omie", domain=SyncDomain.SALES)
        job2 = SyncJob.create(company_id="company-1", provider="omie", domain=SyncDomain.CUSTOMERS)

        batch.add_job(job1)
        batch.add_job(job2)

        assert batch.all_completed() is False

        job1.start()
        job1.complete(records_read=100, records_imported=100, records_failed=0, pages_processed=1)
        job2.start()
        job2.complete(records_read=100, records_imported=100, records_failed=0, pages_processed=1)

        assert batch.all_completed() is True

    def test_has_failures(self):
        """Test checking if batch has failures."""
        batch = SyncBatch.create(company_id="company-1", provider="omie")
        job1 = SyncJob.create(company_id="company-1", provider="omie", domain=SyncDomain.SALES)
        job2 = SyncJob.create(company_id="company-1", provider="omie", domain=SyncDomain.CUSTOMERS)

        batch.add_job(job1)
        batch.add_job(job2)

        assert batch.has_failures() is False

        job1.start()
        job1.fail("Test error")

        assert batch.has_failures() is True

    def test_total_records_imported(self):
        """Test calculating total records imported."""
        batch = SyncBatch.create(company_id="company-1", provider="omie")
        job1 = SyncJob.create(company_id="company-1", provider="omie", domain=SyncDomain.SALES)
        job2 = SyncJob.create(company_id="company-1", provider="omie", domain=SyncDomain.CUSTOMERS)

        batch.add_job(job1)
        batch.add_job(job2)

        job1.start()
        job1.complete(records_read=100, records_imported=95, records_failed=5, pages_processed=1)
        job2.start()
        job2.complete(records_read=200, records_imported=190, records_failed=10, pages_processed=2)

        assert batch.total_records_imported() == 285
