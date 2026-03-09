"""
CodeTrellis Streaming Extractor - Memory-efficient extraction for large projects
=========================================================================

This module provides streaming/chunked extraction to handle large projects
without loading everything into memory at once.

Version: 4.1.1
Created: 2 February 2026

Features:
- Chunked file processing
- Memory-limited extraction
- Progress callbacks
- Incremental result yielding
- Configurable batch sizes
"""

import os
import gc
import sys
import mmap
import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    List, Dict, Any, Optional, Iterator, AsyncIterator,
    Callable, TypeVar, Generic, Union, Set
)
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from contextlib import contextmanager
import logging
import time
import hashlib

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class StreamingConfig:
    """Configuration for streaming extraction."""

    # Batch processing
    batch_size: int = 100  # Files per batch
    max_file_size_mb: float = 10.0  # Skip files larger than this

    # Memory management
    memory_limit_mb: float = 512.0  # Target memory usage limit
    gc_after_batch: bool = True  # Run garbage collection after each batch

    # Parallelism
    max_workers: int = 4
    use_multiprocessing: bool = False  # Use threads by default (shared state)

    # Progress
    progress_callback: Optional[Callable[[int, int, str], None]] = None

    # Caching
    use_cache: bool = True
    cache_dir: Optional[Path] = None

    # File filtering
    include_extensions: Set[str] = field(default_factory=lambda: {
        '.py', '.ts', '.tsx', '.js', '.jsx', '.java', '.cs', '.go', '.rs'
    })
    exclude_patterns: Set[str] = field(default_factory=lambda: {
        'node_modules', '__pycache__', '.git', 'dist', 'build', '.venv', 'venv'
    })


@dataclass
class StreamingResult:
    """Result from streaming extraction."""
    file_path: str
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    file_size: int = 0
    processing_time_ms: float = 0.0
    from_cache: bool = False


@dataclass
class StreamingStats:
    """Statistics from streaming extraction."""
    total_files: int = 0
    processed_files: int = 0
    skipped_files: int = 0
    failed_files: int = 0
    cached_files: int = 0
    total_bytes: int = 0
    processing_time_ms: float = 0.0
    peak_memory_mb: float = 0.0
    batches_processed: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_files == 0:
            return 100.0
        return (self.processed_files / self.total_files) * 100


class FileChunker:
    """
    Reads large files in chunks to avoid loading entire file into memory.
    """

    def __init__(self, chunk_size: int = 64 * 1024):  # 64KB chunks
        self.chunk_size = chunk_size

    def read_chunks(self, file_path: Path) -> Iterator[bytes]:
        """Read file in chunks."""
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(self.chunk_size)
                if not chunk:
                    break
                yield chunk

    def read_lines_chunked(self, file_path: Path, encoding: str = 'utf-8') -> Iterator[str]:
        """Read file line by line (memory efficient for text files)."""
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            for line in f:
                yield line

    @contextmanager
    def mmap_file(self, file_path: Path):
        """
        Memory-map a file for efficient random access.
        Useful for large files where you need to search/parse specific sections.
        """
        with open(file_path, 'rb') as f:
            # Memory-map the file (read-only)
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            try:
                yield mm
            finally:
                mm.close()

    def get_file_hash(self, file_path: Path) -> str:
        """Calculate file hash without loading entire file into memory."""
        hasher = hashlib.md5()
        for chunk in self.read_chunks(file_path):
            hasher.update(chunk)
        return hasher.hexdigest()[:12]


class MemoryMonitor:
    """Monitor memory usage during extraction."""

    def __init__(self, limit_mb: float = 512.0):
        self.limit_mb = limit_mb
        self.peak_mb = 0.0
        self._start_mb = self._get_current_mb()

    def _get_current_mb(self) -> float:
        """Get peak memory usage in MB (via ru_maxrss).

        Note: ru_maxrss reports peak RSS, not current. Sufficient for
        limit checks since peak only grows, but should not be used for
        precise current-memory decisions.
        """
        import resource
        # Get memory usage in bytes
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On macOS, ru_maxrss is in bytes; on Linux, it's in KB
        if sys.platform == 'darwin':
            return usage / (1024 * 1024)
        else:
            return usage / 1024

    def check_memory(self) -> Dict[str, float]:
        """Check current memory status."""
        current = self._get_current_mb()
        self.peak_mb = max(self.peak_mb, current)

        return {
            'current_mb': current,
            'peak_mb': self.peak_mb,
            'start_mb': self._start_mb,
            'delta_mb': current - self._start_mb,
            'limit_mb': self.limit_mb,
            'within_limit': current < self.limit_mb
        }

    def should_gc(self) -> bool:
        """Check if garbage collection is recommended."""
        status = self.check_memory()
        return status['current_mb'] > self.limit_mb * 0.8

    def force_gc(self):
        """Force garbage collection."""
        gc.collect()


class StreamingFileScanner:
    """
    Scans project files in a streaming manner, yielding files in batches.
    """

    def __init__(self, config: StreamingConfig):
        self.config = config
        self.chunker = FileChunker()

    def scan_files(self, root: Path) -> Iterator[List[Path]]:
        """
        Scan and yield files in batches.

        Yields:
            List of Path objects, batch_size at a time
        """
        batch = []

        for file_path in self._walk_files(root):
            batch.append(file_path)

            if len(batch) >= self.config.batch_size:
                yield batch
                batch = []

        # Yield remaining files
        if batch:
            yield batch

    def _walk_files(self, root: Path) -> Iterator[Path]:
        """Walk through files, respecting configuration."""
        for dirpath, dirnames, filenames in os.walk(root):
            # Filter out excluded directories
            dirnames[:] = [
                d for d in dirnames
                if d not in self.config.exclude_patterns
            ]

            for filename in filenames:
                file_path = Path(dirpath) / filename

                # Check extension
                if file_path.suffix.lower() not in self.config.include_extensions:
                    continue

                # Check file size
                try:
                    size = file_path.stat().st_size
                    if size > self.config.max_file_size_mb * 1024 * 1024:
                        logger.debug(f"Skipping large file: {file_path} ({size / 1024 / 1024:.1f}MB)")
                        continue
                except OSError:
                    continue

                yield file_path

    def count_files(self, root: Path) -> int:
        """Count total files (for progress reporting)."""
        return sum(1 for _ in self._walk_files(root))


class StreamingCache:
    """
    File-based cache for extraction results.
    """

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.chunker = FileChunker()

    def _get_cache_path(self, file_path: Path, file_hash: str) -> Path:
        """Get cache file path for a source file."""
        # Use hash to avoid cache collisions
        cache_name = f"{file_path.stem}_{file_hash}.cache"
        return self.cache_dir / cache_name

    def get(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Get cached result if available and valid."""
        try:
            file_hash = self.chunker.get_file_hash(file_path)
            cache_path = self._get_cache_path(file_path, file_hash)

            if cache_path.exists():
                import json
                with open(cache_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Cache miss for {file_path}: {e}")

        return None

    def set(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Cache extraction result."""
        try:
            file_hash = self.chunker.get_file_hash(file_path)
            cache_path = self._get_cache_path(file_path, file_hash)

            import json
            with open(cache_path, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.debug(f"Failed to cache {file_path}: {e}")

    def clear(self) -> int:
        """Clear all cache files. Returns count of files removed."""
        count = 0
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                cache_file.unlink()
                count += 1
            except Exception:
                pass
        return count


class StreamingExtractor:
    """
    Main streaming extractor that processes files in memory-efficient batches.

    Usage:
        config = StreamingConfig(batch_size=50, memory_limit_mb=256)
        extractor = StreamingExtractor(config)

        for result in extractor.extract_stream(project_path):
            process_result(result)
    """

    def __init__(self, config: Optional[StreamingConfig] = None):
        self.config = config or StreamingConfig()
        self.scanner = StreamingFileScanner(self.config)
        self.memory_monitor = MemoryMonitor(self.config.memory_limit_mb)
        self.cache = None

        if self.config.use_cache and self.config.cache_dir:
            self.cache = StreamingCache(self.config.cache_dir)

        # Stats
        self.stats = StreamingStats()

    def extract_stream(self, root: Path) -> Iterator[StreamingResult]:
        """
        Stream extraction results one at a time.

        This is the most memory-efficient mode - processes files one by one
        and yields results immediately.

        Args:
            root: Project root path

        Yields:
            StreamingResult for each processed file
        """
        start_time = time.perf_counter()
        self.stats = StreamingStats()

        # Count total files for progress
        self.stats.total_files = self.scanner.count_files(root)

        batch_num = 0
        for batch in self.scanner.scan_files(root):
            batch_num += 1

            for file_path in batch:
                result = self._process_file(file_path)
                yield result

                # Update stats
                if result.success:
                    self.stats.processed_files += 1
                elif result.error:
                    self.stats.failed_files += 1
                else:
                    self.stats.skipped_files += 1

                if result.from_cache:
                    self.stats.cached_files += 1

                self.stats.total_bytes += result.file_size

                # Report progress
                if self.config.progress_callback:
                    current = self.stats.processed_files + self.stats.failed_files + self.stats.skipped_files
                    try:
                        self.config.progress_callback(
                            current,
                            self.stats.total_files,
                            str(file_path)
                        )
                    except Exception:
                        pass  # Never let callback errors crash the pipeline

            # Memory management after batch
            if self.config.gc_after_batch or self.memory_monitor.should_gc():
                self.memory_monitor.force_gc()

            self.stats.batches_processed = batch_num

        self.stats.processing_time_ms = (time.perf_counter() - start_time) * 1000
        self.stats.peak_memory_mb = self.memory_monitor.peak_mb

    def extract_batch(self, root: Path) -> Iterator[List[StreamingResult]]:
        """
        Yield results in batches (useful for bulk processing).

        Args:
            root: Project root path

        Yields:
            List of StreamingResult for each batch
        """
        start_time = time.perf_counter()
        self.stats = StreamingStats()
        self.stats.total_files = self.scanner.count_files(root)

        for batch in self.scanner.scan_files(root):
            results = []

            # Process batch in parallel
            if self.config.max_workers > 1:
                results = self._process_batch_parallel(batch)
            else:
                results = [self._process_file(f) for f in batch]

            # Update stats
            for result in results:
                if result.success:
                    self.stats.processed_files += 1
                elif result.error:
                    self.stats.failed_files += 1
                else:
                    self.stats.skipped_files += 1

                if result.from_cache:
                    self.stats.cached_files += 1

                self.stats.total_bytes += result.file_size

            yield results

            # Memory management
            if self.config.gc_after_batch or self.memory_monitor.should_gc():
                self.memory_monitor.force_gc()

            self.stats.batches_processed += 1

        self.stats.processing_time_ms = (time.perf_counter() - start_time) * 1000
        self.stats.peak_memory_mb = self.memory_monitor.peak_mb

    def _process_file(self, file_path: Path) -> StreamingResult:
        """Process a single file."""
        start_time = time.perf_counter()

        try:
            file_size = file_path.stat().st_size

            # Check cache first
            if self.cache:
                cached = self.cache.get(file_path)
                if cached:
                    return StreamingResult(
                        file_path=str(file_path),
                        success=True,
                        data=cached,
                        file_size=file_size,
                        processing_time_ms=(time.perf_counter() - start_time) * 1000,
                        from_cache=True
                    )

            # Extract
            data = self._extract_file_data(file_path)

            # Cache result
            if self.cache and data:
                self.cache.set(file_path, data)

            return StreamingResult(
                file_path=str(file_path),
                success=True,
                data=data,
                file_size=file_size,
                processing_time_ms=(time.perf_counter() - start_time) * 1000
            )

        except Exception as e:
            return StreamingResult(
                file_path=str(file_path),
                success=False,
                error=str(e),
                processing_time_ms=(time.perf_counter() - start_time) * 1000
            )

    def _extract_file_data(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract data from a file.
        Override this method to customize extraction logic.
        """
        # Default implementation: use AST parser if available
        try:
            from codetrellis.ast_parser import parse_file, TREE_SITTER_AVAILABLE

            if TREE_SITTER_AVAILABLE and file_path.suffix in ('.py', '.ts', '.tsx', '.js', '.jsx'):
                result = parse_file(file_path)
                return result.to_dict()
        except ImportError:
            pass

        # Fallback: basic file info
        content = file_path.read_text(encoding='utf-8', errors='replace')

        return {
            'file_path': str(file_path),
            'extension': file_path.suffix,
            'lines': content.count('\n') + 1,
            'size': len(content),
        }

    def _process_batch_parallel(self, batch: List[Path]) -> List[StreamingResult]:
        """Process a batch of files in parallel."""
        executor_class = ProcessPoolExecutor if self.config.use_multiprocessing else ThreadPoolExecutor

        with executor_class(max_workers=self.config.max_workers) as executor:
            results = list(executor.map(self._process_file, batch))

        return results


class AsyncStreamingExtractor:
    """
    Async version of the streaming extractor for better I/O performance.
    """

    def __init__(self, config: Optional[StreamingConfig] = None):
        self.config = config or StreamingConfig()
        self.scanner = StreamingFileScanner(self.config)
        self.memory_monitor = MemoryMonitor(self.config.memory_limit_mb)
        self.stats = StreamingStats()

    async def extract_stream(self, root: Path) -> AsyncIterator[StreamingResult]:
        """
        Async stream extraction results.

        Args:
            root: Project root path

        Yields:
            StreamingResult for each processed file
        """
        start_time = time.perf_counter()
        self.stats = StreamingStats()
        self.stats.total_files = self.scanner.count_files(root)

        for batch in self.scanner.scan_files(root):
            # Process batch concurrently
            tasks = [self._process_file_async(f) for f in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    yield StreamingResult(
                        file_path="unknown",
                        success=False,
                        error=str(result)
                    )
                    self.stats.failed_files += 1
                else:
                    yield result
                    if result.success:
                        self.stats.processed_files += 1
                    else:
                        self.stats.failed_files += 1

            # Memory management
            if self.config.gc_after_batch:
                self.memory_monitor.force_gc()

            self.stats.batches_processed += 1

        self.stats.processing_time_ms = (time.perf_counter() - start_time) * 1000
        self.stats.peak_memory_mb = self.memory_monitor.peak_mb

    async def _process_file_async(self, file_path: Path) -> StreamingResult:
        """Process a file asynchronously."""
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()

        def _sync_process():
            try:
                content = file_path.read_text(encoding='utf-8', errors='replace')

                # Use AST parser if available
                try:
                    from codetrellis.ast_parser import parse_content, TREE_SITTER_AVAILABLE
                    if TREE_SITTER_AVAILABLE:
                        result = parse_content(content, str(file_path))
                        return StreamingResult(
                            file_path=str(file_path),
                            success=True,
                            data=result.to_dict(),
                            file_size=len(content)
                        )
                except ImportError:
                    pass

                return StreamingResult(
                    file_path=str(file_path),
                    success=True,
                    data={'lines': content.count('\n') + 1},
                    file_size=len(content)
                )

            except Exception as e:
                return StreamingResult(
                    file_path=str(file_path),
                    success=False,
                    error=str(e)
                )

        return await loop.run_in_executor(None, _sync_process)


# Convenience functions

def extract_project_streaming(
    project_path: Union[str, Path],
    batch_size: int = 100,
    memory_limit_mb: float = 512.0,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> Iterator[StreamingResult]:
    """
    Extract project data using streaming (memory-efficient).

    Args:
        project_path: Path to project root
        batch_size: Files per batch
        memory_limit_mb: Memory limit in MB
        progress_callback: Optional progress callback (current, total, file)

    Yields:
        StreamingResult for each file
    """
    config = StreamingConfig(
        batch_size=batch_size,
        memory_limit_mb=memory_limit_mb,
        progress_callback=progress_callback
    )

    extractor = StreamingExtractor(config)
    yield from extractor.extract_stream(Path(project_path))


async def extract_project_async(
    project_path: Union[str, Path],
    batch_size: int = 100
) -> AsyncIterator[StreamingResult]:
    """
    Extract project data using async streaming.

    Args:
        project_path: Path to project root
        batch_size: Files per batch

    Yields:
        StreamingResult for each file
    """
    config = StreamingConfig(batch_size=batch_size)
    extractor = AsyncStreamingExtractor(config)

    async for result in extractor.extract_stream(Path(project_path)):
        yield result
