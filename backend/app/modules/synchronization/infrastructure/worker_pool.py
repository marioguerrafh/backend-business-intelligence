"""Worker pool for concurrent job execution."""
from __future__ import annotations

import logging
import queue
import threading
from dataclasses import dataclass, field
from typing import Callable


@dataclass(slots=True)
class WorkerPool:
    """Thread pool for executing synchronization jobs."""

    max_workers: int = 4
    _workers: list[threading.Thread] = field(default_factory=list, init=False, repr=False)
    _queue: queue.Queue = field(default_factory=queue.Queue, init=False, repr=False)
    _shutdown: bool = field(default=False, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _logger: logging.Logger = field(
        default_factory=lambda: logging.getLogger("app.synchronization.worker_pool"),
        init=False,
        repr=False,
    )

    def start(self) -> None:
        """Start worker threads."""
        with self._lock:
            if self._workers:
                return  # Already started

            self._shutdown = False
            for i in range(self.max_workers):
                worker = threading.Thread(
                    target=self._worker_loop,
                    name=f"sync-worker-{i}",
                    daemon=True,
                )
                worker.start()
                self._workers.append(worker)

            self._logger.info(f"Worker pool started with {self.max_workers} workers")

    def submit(self, fn: Callable[[], None]) -> None:
        """Submit a job to the worker pool."""
        if self._shutdown:
            raise RuntimeError("Worker pool is shut down")
        self._queue.put(fn)

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the worker pool."""
        with self._lock:
            if self._shutdown:
                return

            self._shutdown = True

            # Send sentinel values to wake up workers
            for _ in range(len(self._workers)):
                self._queue.put(None)

            if wait:
                for worker in self._workers:
                    worker.join(timeout=5.0)

            self._workers.clear()
            self._logger.info("Worker pool shut down")

    def _worker_loop(self) -> None:
        """Main worker loop."""
        while not self._shutdown:
            try:
                fn = self._queue.get(timeout=1.0)
                if fn is None:  # Sentinel value
                    break

                try:
                    fn()
                except Exception as exc:
                    self._logger.error(f"Worker error: {exc}", exc_info=True)
                finally:
                    self._queue.task_done()

            except queue.Empty:
                continue

    def queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    def is_running(self) -> bool:
        """Check if worker pool is running."""
        with self._lock:
            return not self._shutdown and len(self._workers) > 0
