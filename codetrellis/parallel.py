"""
CodeTrellis Parallel Processing Module
================================

Implements parallel file extraction for improved performance.
Addresses Report 2 Section 3.2 (HIGH: No Parallel Processing).

Key Features:
- ProcessPoolExecutor for CPU-bound extraction tasks
- Async file scanning with concurrent.futures
- Configurable worker count
- Graceful error handling per file

Version: 4.1.0
Created: 2 February 2026
"""

import asyncio
import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import logging
from datetime import datetime

from .errors import ErrorCollector, ExtractorResult, CodeTrellisError, CodeTrellisErrorCode


# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class ParallelConfig:
    """Configuration for parallel processing."""
    max_workers: Optional[int] = None  # None = use cpu_count()
    chunk_size: int = 10  # Files to process per batch
    timeout_per_file: float = 30.0  # Seconds
    use_processes: bool = True  # True = ProcessPoolExecutor, False = ThreadPoolExecutor


@dataclass
class ParallelResult:
    """Result from parallel extraction."""
    total_files: int
    successful: int
    failed: int
    duration_seconds: float
    results: List[ExtractorResult]
    errors: ErrorCollector


def _get_worker_count(config: ParallelConfig) -> int:
    """Determine the number of workers to use."""
    if config.max_workers is not None:
        return config.max_workers

    cpu_count = os.cpu_count() or 4
    # Leave one core free for the main process
    return max(1, cpu_count - 1)


def _extract_single_file(args: tuple) -> ExtractorResult:
    """
    Process a single file. This function runs in a worker process/thread.

    Args:
        args: Tuple of (file_path, extractor_func, extractor_name)

    Returns:
        ExtractorResult with extraction outcome
    """
    file_path, extractor_func, extractor_name = args

    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        # Run the extractor
        result = extractor_func(content, str(file_path))

        if isinstance(result, ExtractorResult):
            return result

        # Wrap dict results in ExtractorResult
        return ExtractorResult.success(
            extractor_name=extractor_name,
            file_path=str(file_path),
            data=result if isinstance(result, dict) else {"result": result}
        )

    except FileNotFoundError:
        return ExtractorResult.failure(
            extractor_name=extractor_name,
            file_path=str(file_path),
            error=f"File not found: {file_path}"
        )
    except UnicodeDecodeError as e:
        return ExtractorResult.failure(
            extractor_name=extractor_name,
            file_path=str(file_path),
            error=f"Encoding error: {e}"
        )
    except Exception as e:
        return ExtractorResult.failure(
            extractor_name=extractor_name,
            file_path=str(file_path),
            error=str(e)
        )


class ParallelExtractor:
    """
    Parallel file extraction manager.

    Uses ProcessPoolExecutor for CPU-bound extraction tasks across multiple files.
    Implements Report 2 Section 3.2 recommendation.

    Example:
        >>> extractor = ParallelExtractor(config=ParallelConfig(max_workers=4))
        >>> result = extractor.extract_all(
        ...     files=["/path/to/file1.ts", "/path/to/file2.ts"],
        ...     extract_func=my_extractor_function,
        ...     extractor_name="InterfaceExtractor"
        ... )
        >>> print(f"Processed {result.total_files} files in {result.duration_seconds:.2f}s")
    """

    def __init__(self, config: Optional[ParallelConfig] = None):
        self.config = config or ParallelConfig()
        self.worker_count = _get_worker_count(self.config)
        logger.info(f"ParallelExtractor initialized with {self.worker_count} workers")

    def extract_all(
        self,
        files: List[Path],
        extract_func: Callable[[str, str], Any],
        extractor_name: str
    ) -> ParallelResult:
        """
        Extract from multiple files in parallel.

        Args:
            files: List of file paths to process
            extract_func: Function that takes (content, file_path) and returns extraction result
            extractor_name: Name of the extractor for logging

        Returns:
            ParallelResult with all extraction outcomes
        """
        start_time = datetime.now()
        results: List[ExtractorResult] = []
        error_collector = ErrorCollector()

        if not files:
            return ParallelResult(
                total_files=0,
                successful=0,
                failed=0,
                duration_seconds=0.0,
                results=[],
                errors=error_collector
            )

        # Prepare arguments for workers
        work_items = [(f, extract_func, extractor_name) for f in files]

        # Choose executor type
        executor_class = ProcessPoolExecutor if self.config.use_processes else ThreadPoolExecutor

        logger.info(f"Starting parallel extraction of {len(files)} files with {self.worker_count} workers")

        executor = executor_class(max_workers=self.worker_count)
        timed_out = False
        try:
            # Submit all tasks
            future_to_file = {
                executor.submit(_extract_single_file, item): item[0]
                for item in work_items
            }

            # Collect results as they complete
            try:
                for future in as_completed(future_to_file, timeout=self.config.timeout_per_file * len(files)):
                    file_path = future_to_file[future]
                    try:
                        result = future.result(timeout=self.config.timeout_per_file)
                        results.append(result)

                        if not result.success:
                            error_collector.add_error(
                                str(file_path),
                                extractor_name,
                                Exception(result.errors[0] if result.errors else "Unknown error")
                            )

                        if result.warnings:
                            for warning in result.warnings:
                                error_collector.add_warning(str(file_path), warning)

                    except TimeoutError:
                        error_collector.add_error(
                            str(file_path),
                            extractor_name,
                            Exception(f"Timeout after {self.config.timeout_per_file}s")
                        )
                        results.append(ExtractorResult.failure(
                            extractor_name=extractor_name,
                            file_path=str(file_path),
                            error=f"Timeout after {self.config.timeout_per_file}s"
                        ))
                    except Exception as e:
                        error_collector.add_error(str(file_path), extractor_name, e)
                        results.append(ExtractorResult.failure(
                            extractor_name=extractor_name,
                            file_path=str(file_path),
                            error=str(e)
                        ))
            except TimeoutError:
                timed_out = True
                # as_completed() timed out — record remaining futures as failures
                for future, file_path in future_to_file.items():
                    if not future.done():
                        future.cancel()
                        error_collector.add_error(
                            str(file_path),
                            extractor_name,
                            Exception(f"Timeout after {self.config.timeout_per_file}s")
                        )
                        results.append(ExtractorResult.failure(
                            extractor_name=extractor_name,
                            file_path=str(file_path),
                            error=f"Timeout after {self.config.timeout_per_file}s"
                        ))
                logger.warning("Parallel extraction timed out for some files")

        except Exception as e:
            logger.error(f"Parallel extraction failed: {e}")
            raise CodeTrellisError(
                code=CodeTrellisErrorCode.EXTRACTION_FAILED,
                message="Parallel extraction failed",
                context={"error": str(e)},
                cause=e
            )
        finally:
            # On timeout, shut down without waiting for stuck workers
            executor.shutdown(wait=not timed_out, cancel_futures=timed_out)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        logger.info(
            f"Parallel extraction complete: {successful}/{len(files)} successful, "
            f"{failed} failed, {duration:.2f}s"
        )

        return ParallelResult(
            total_files=len(files),
            successful=successful,
            failed=failed,
            duration_seconds=duration,
            results=results,
            errors=error_collector
        )


class AsyncParallelExtractor:
    """
    Async-compatible parallel extractor using asyncio.

    Useful for integration with async codebases.

    Example:
        >>> extractor = AsyncParallelExtractor()
        >>> result = await extractor.extract_all_async(files, extract_func, "MyExtractor")
    """

    def __init__(self, config: Optional[ParallelConfig] = None):
        self.config = config or ParallelConfig()
        self.worker_count = _get_worker_count(self.config)

    async def extract_all_async(
        self,
        files: List[Path],
        extract_func: Callable[[str, str], Any],
        extractor_name: str
    ) -> ParallelResult:
        """
        Extract from multiple files asynchronously.

        Args:
            files: List of file paths to process
            extract_func: Function that takes (content, file_path) and returns extraction result
            extractor_name: Name of the extractor for logging

        Returns:
            ParallelResult with all extraction outcomes
        """
        loop = asyncio.get_event_loop()
        start_time = datetime.now()
        results: List[ExtractorResult] = []
        error_collector = ErrorCollector()

        if not files:
            return ParallelResult(
                total_files=0,
                successful=0,
                failed=0,
                duration_seconds=0.0,
                results=[],
                errors=error_collector
            )

        # Prepare work items
        work_items = [(f, extract_func, extractor_name) for f in files]

        # Use ProcessPoolExecutor with asyncio
        executor_class = ProcessPoolExecutor if self.config.use_processes else ThreadPoolExecutor

        with executor_class(max_workers=self.worker_count) as executor:
            # Create async tasks
            tasks = [
                loop.run_in_executor(executor, _extract_single_file, item)
                for item in work_items
            ]

            # Wait for all tasks to complete
            completed_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(completed_results):
                file_path = files[i]

                if isinstance(result, Exception):
                    error_collector.add_error(str(file_path), extractor_name, result)
                    results.append(ExtractorResult.failure(
                        extractor_name=extractor_name,
                        file_path=str(file_path),
                        error=str(result)
                    ))
                else:
                    results.append(result)
                    if not result.success:
                        error_collector.add_error(
                            str(file_path),
                            extractor_name,
                            Exception(result.errors[0] if result.errors else "Unknown error")
                        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        return ParallelResult(
            total_files=len(files),
            successful=successful,
            failed=failed,
            duration_seconds=duration,
            results=results,
            errors=error_collector
        )


def merge_extraction_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge multiple extraction results into a unified dictionary.

    Args:
        results: List of extraction result dictionaries

    Returns:
        Merged dictionary with combined data
    """
    merged: Dict[str, Any] = {
        "interfaces": [],
        "types": [],
        "components": [],
        "services": [],
        "stores": [],
        "routes": [],
        "functions": [],
        "classes": [],
        "errors": [],
    }

    for result in results:
        for key in merged:
            if key in result and isinstance(result[key], list):
                merged[key].extend(result[key])

    return merged
