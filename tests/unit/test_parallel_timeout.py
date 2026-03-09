"""Tests for parallel extraction timeout enforcement."""

import time
import pytest
from pathlib import Path

from codetrellis.parallel import ParallelConfig, ParallelExtractor
from codetrellis.errors import ExtractorResult, CodeTrellisError


def _slow_extractor(content: str, file_path: str) -> dict:
    """Simulate a slow extraction that takes longer than any reasonable timeout."""
    time.sleep(60)
    return {"result": "should not reach here"}


class TestTimeoutPerFile:
    """Verify that timeout_per_file in ParallelConfig is enforced."""

    def test_timeout_produces_failure_result(self, tmp_path):
        """A file that takes >timeout_per_file should result in a timeout failure,
        not hang indefinitely."""
        test_file = tmp_path / "slow_file.py"
        test_file.write_text("x = 1")

        config = ParallelConfig(
            max_workers=1,
            timeout_per_file=2.0,
            use_processes=True,  # Processes can be killed on shutdown
        )
        extractor = ParallelExtractor(config)

        start = time.time()
        result = extractor.extract_all(
            files=[test_file],
            extract_func=_slow_extractor,
            extractor_name="test_slow",
        )
        elapsed = time.time() - start

        # Should complete well before the 60s sleep
        assert elapsed < 30, f"Timeout not enforced: took {elapsed:.1f}s"

        # The result should record a timeout failure
        assert result.total_files == 1
        assert result.failed >= 1
        assert any(
            not r.success and "imeout" in " ".join(r.errors)
            for r in result.results
        ), f"Expected timeout failure in results: {[r.errors for r in result.results]}"
