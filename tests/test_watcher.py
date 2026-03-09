"""Tests for codetrellis.watcher — thread-safety and batching."""

import time
import threading
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from codetrellis.watcher import MatrixSyncHandler, HAS_WATCHDOG

pytestmark = pytest.mark.skipif(not HAS_WATCHDOG, reason="watchdog not installed")


@pytest.fixture
def handler(tmp_path):
    """Create a handler with a temporary project root."""
    ct_dir = tmp_path / ".codetrellis"
    ct_dir.mkdir()
    h = MatrixSyncHandler(tmp_path, ct_dir, on_change=None)
    return h


class TestProcessPendingThreadSafety:
    """Verify process_pending does not crash under concurrent mutations."""

    def test_empty_pending_is_noop(self, handler):
        handler.process_pending()
        assert len(handler.pending_updates) == 0

    def test_snapshot_clears_pending(self, handler):
        handler.pending_updates.add(Path("/a.ts"))
        handler.last_update = time.time() - 10  # past debounce
        results = []
        handler.on_change = lambda batch: results.append(batch)

        handler.process_pending()

        assert len(handler.pending_updates) == 0
        assert len(results) == 1

    def test_batch_callback_receives_sorted_list(self, handler):
        handler.pending_updates.update([Path("/c.ts"), Path("/a.ts"), Path("/b.ts")])
        handler.last_update = time.time() - 10
        results = []
        handler.on_change = lambda batch: results.append(batch)

        handler.process_pending()

        assert results[0] == [Path("/a.ts"), Path("/b.ts"), Path("/c.ts")]

    def test_full_resync_sends_none(self, handler):
        handler.pending_updates.add(Path("__full_resync__"))
        handler.last_update = time.time() - 10
        results = []
        handler.on_change = lambda batch: results.append(batch)

        handler.process_pending()

        assert results == [None]

    def test_debounce_delays_processing(self, handler):
        handler.pending_updates.add(Path("/a.ts"))
        handler.last_update = time.time()  # just now
        handler.on_change = MagicMock()

        handler.process_pending()

        handler.on_change.assert_not_called()
        assert len(handler.pending_updates) == 1

    def test_concurrent_add_during_process(self, handler):
        """Simulate watchdog thread adding to set while process_pending runs."""
        handler.debounce_seconds = 0
        handler.last_update = time.time() - 10

        # Pre-populate
        for i in range(100):
            handler.pending_updates.add(Path(f"/file{i}.ts"))

        results = []
        barrier = threading.Barrier(2, timeout=5)

        def slow_callback(batch):
            results.append(batch)
            barrier.wait()  # Wait for concurrent writer to finish

        handler.on_change = slow_callback

        def concurrent_writer():
            """Simulates watchdog adding events while process_pending runs."""
            barrier.wait()  # Wait until callback is processing
            for i in range(100, 200):
                with handler._lock:
                    handler.pending_updates.add(Path(f"/file{i}.ts"))
                    handler.last_update = time.time()

        writer = threading.Thread(target=concurrent_writer)
        writer.start()

        # This should NOT raise RuntimeError
        handler.process_pending()

        writer.join(timeout=5)

        # First batch should have processed 100 files
        assert len(results) == 1
        assert len(results[0]) == 100

        # Second batch should be pending (from concurrent writer)
        assert len(handler.pending_updates) == 100

    def test_no_crash_rapid_fire_events(self, handler):
        """Stress test: many threads adding while process_pending runs repeatedly."""
        handler.debounce_seconds = 0
        errors = []
        stop = threading.Event()

        def writer(start_idx):
            for i in range(50):
                with handler._lock:
                    handler.pending_updates.add(Path(f"/file{start_idx + i}.ts"))
                    handler.last_update = time.time() - 10
                time.sleep(0.001)

        def processor():
            while not stop.is_set():
                try:
                    handler.process_pending()
                except RuntimeError as e:
                    errors.append(e)
                time.sleep(0.005)

        handler.on_change = lambda batch: None

        threads = [threading.Thread(target=writer, args=(i * 50,)) for i in range(4)]
        proc = threading.Thread(target=processor)

        proc.start()
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        stop.set()
        proc.join(timeout=5)

        assert errors == [], f"Got RuntimeErrors: {errors}"


class TestShouldWatch:
    """Verify file filtering logic."""

    def test_watches_ts_files(self, handler):
        assert handler._should_watch("/src/app.ts") is True

    def test_watches_py_files(self, handler):
        assert handler._should_watch("/src/main.py") is True

    def test_ignores_node_modules(self, handler):
        assert handler._should_watch("/node_modules/foo/bar.ts") is False

    def test_ignores_spec_files(self, handler):
        assert handler._should_watch("/src/app.spec.ts") is False

    def test_ignores_test_files(self, handler):
        assert handler._should_watch("/src/app.test.ts") is False

    def test_ignores_txt_files(self, handler):
        assert handler._should_watch("/src/readme.txt") is False

    def test_ignores_git_dir(self, handler):
        assert handler._should_watch("/.git/config") is False

    def test_ignores_codetrellis_dir(self, handler):
        assert handler._should_watch("/.codetrellis/cache/matrix.prompt") is False
