"""
CodeTrellis - Project Self-Awareness System
=====================================

A tool that scans your codebase, compresses it to minimal tokens,
and injects complete project awareness into every AI prompt.

Created: 31 January 2026
Author: Keshav Chaudhary
"""

try:
    from importlib.metadata import version as _pkg_version
    __version__ = _pkg_version("codetrellis")
except Exception:
    __version__ = "unknown"
__author__ = "Keshav Chaudhary"

# Lazy imports to avoid dependency issues
def __getattr__(name):
    if name == "ProjectScanner":
        from .scanner import ProjectScanner
        return ProjectScanner
    elif name == "MatrixCompressor":
        from .compressor import MatrixCompressor
        return MatrixCompressor
    elif name == "FileWatcher":
        from .watcher import FileWatcher
        return FileWatcher
    elif name == "CodeTrellisError":
        from .errors import CodeTrellisError
        return CodeTrellisError
    elif name == "CodeTrellisErrorCode":
        from .errors import CodeTrellisErrorCode
        return CodeTrellisErrorCode
    elif name == "ExtractorResult":
        from .errors import ExtractorResult
        return ExtractorResult
    elif name == "ErrorCollector":
        from .errors import ErrorCollector
        return ErrorCollector
    elif name == "ParallelExtractor":
        from .parallel import ParallelExtractor
        return ParallelExtractor
    elif name == "AsyncParallelExtractor":
        from .parallel import AsyncParallelExtractor
        return AsyncParallelExtractor
    elif name == "ParallelConfig":
        from .parallel import ParallelConfig
        return ParallelConfig
    elif name == "ParallelResult":
        from .parallel import ParallelResult
        return ParallelResult
    elif name == "MatrixBuilder":
        from .builder import MatrixBuilder
        return MatrixBuilder
    elif name == "BuildConfig":
        from .builder import BuildConfig
        return BuildConfig
    elif name == "CacheManager":
        from .cache import CacheManager
        return CacheManager
    elif name == "LockfileManager":
        from .cache import LockfileManager
        return LockfileManager
    elif name == "InputHashCalculator":
        from .cache import InputHashCalculator
        return InputHashCalculator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "ProjectScanner",
    "MatrixCompressor",
    "FileWatcher",
    "CodeTrellisError",
    "CodeTrellisErrorCode",
    "ExtractorResult",
    "ErrorCollector",
    "ParallelExtractor",
    "AsyncParallelExtractor",
    "ParallelConfig",
    "ParallelResult",
    "MatrixBuilder",
    "BuildConfig",
    "CacheManager",
    "LockfileManager",
    "InputHashCalculator",
]
