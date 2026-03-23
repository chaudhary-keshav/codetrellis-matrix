"""
CodeTrellis Unified File Classifier
====================================

Single source of truth for file/directory classification.

Replaces per-extractor EXAMPLE_DIRS, VENDOR_DIRS, etc. with a unified
classification layer inspired by GitHub Linguist's vendor.yml / generated.yml.

Every extractor calls `FileClassifier.classify(path)` instead of maintaining
its own exclusion set. This eliminates the Category 2 root cause
(example/vendor/generated contamination) identified in the Systemic
Improvement Plan.

Part of CodeTrellis v5.0 — Systemic Improvement Phase 1
"""

import fnmatch
import os
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import List, Optional, Set


class FileType(Enum):
    """Classification of a file/directory in a project."""
    APP_CODE = "app_code"       # Production application code
    EXAMPLE = "example"         # Example, sample, tutorial, demo code
    VENDOR = "vendor"           # Third-party vendored code
    GENERATED = "generated"     # Auto-generated code (protobuf, codegen, etc.)
    TEST = "test"               # Test files and fixtures
    BUILD = "build"             # Build output directories
    DOCUMENTATION = "documentation"  # Documentation files (not code)


class FileClassifier:
    """
    Unified file classification.  Single import replaces 4+ EXAMPLE_DIRS
    definitions scattered across extractors.

    Bootstrapped with patterns from GitHub Linguist's vendor.yml,
    generated.yml, and documentation.yml — battle-tested at GitHub's
    200M+ repo scale.

    Usage::

        from codetrellis.file_classifier import FileClassifier

        # Classify a relative path
        ft = FileClassifier.classify("examples/demo-app/main.py")
        if ft != FileType.APP_CODE:
            continue  # skip non-app code

        # Quick boolean checks
        if FileClassifier.is_example_path("docs_src/tutorial/main.py"):
            continue

        if FileClassifier.is_app_code("src/models/user.py"):
            process(file)
    """

    # ── EXAMPLE / SAMPLE / TUTORIAL DIRECTORIES ──────────────────────────
    # Any path segment matching these (case-insensitive) marks the file as
    # example/demo code.  Superset of the old per-extractor EXAMPLE_DIRS.
    EXAMPLE_DIRS: Set[str] = {
        'examples', 'example', 'samples', 'sample',
        'demos', 'demo', 'tutorials', 'tutorial',
        'docs_src', 'doc_src',
        'fixtures', 'test_data', 'testdata',
        '_examples', '_samples',
        'sandbox', 'playground',
        'quickstart', 'getting-started',
        'cookbooks', 'cookbook',
        'recipes',
    }

    # ── VENDOR / THIRD-PARTY DIRECTORIES ─────────────────────────────────
    # Patterns from Linguist vendor.yml (subset relevant to us).
    VENDOR_DIRS: Set[str] = {
        'vendor', 'node_modules', 'third_party', 'third-party',
        'external', 'deps', 'lib/vendor',
        'bower_components',
        'jspm_packages',
        'web_modules',
        'godeps',
    }

    # ── GENERATED FILE EXTENSIONS / SUFFIXES ─────────────────────────────
    # A file whose name ends with any of these is auto-generated.
    # Patterns from Linguist generated.yml.
    GENERATED_SUFFIXES: Set[str] = {
        # Protocol Buffers
        '_pb.ts', '_pb.js', '_pb.d.ts',
        '.pb.go', '_pb2.py', '_pb2_grpc.py',
        '.pb.cc', '.pb.h',
        # Code generation markers
        '.generated.ts', '.generated.js', '.generated.go',
        '.gen.go', '.gen.ts', '.gen.js',
        '_gen.go', '_gen.ts', '_gen.py',
        # OpenAPI / Swagger codegen
        '.swagger.json', '.swagger.yaml',
        # GraphQL codegen
        '.graphql.ts', '.graphql.js',
        # gRPC
        '_grpc.pb.go',
        # Thrift
        '_thrift.go',
        # Other common patterns
        '.min.js', '.min.css',
        '.bundle.js', '.chunk.js',
        # Dart code generation
        '.g.dart', '.freezed.dart', '.gr.dart', '.mocks.dart',
    }

    # ── GENERATED DIRECTORY NAMES ────────────────────────────────────────
    GENERATED_DIRS: Set[str] = {
        'generated', 'gen', 'auto-generated', 'autogen',
        '__generated__',
    }

    # ── BUILD OUTPUT DIRECTORIES ─────────────────────────────────────────
    BUILD_DIRS: Set[str] = {
        'dist', 'build', 'out', 'output',
        '.next', '.nuxt', '.svelte-kit', '.astro',
        'target',   # Rust/Java
        'bin',      # Go
        '__pycache__',
        'coverage', 'htmlcov',
        '.tox', '.mypy_cache', '.ruff_cache', '.pytest_cache',
        '.eggs', '*.egg-info',
    }

    # ── TEST DIRECTORIES ─────────────────────────────────────────────────
    TEST_DIRS: Set[str] = {
        'tests', 'test', '__tests__', '__test__',
        'spec', 'specs',
        'e2e', 'integration', 'unit',
        'test-utils', 'testing',
    }

    # ── DOCUMENTATION DIRECTORIES ────────────────────────────────────────
    DOC_DIRS: Set[str] = {
        'docs', 'doc', 'documentation',
        'wiki', 'guides', 'guide',
        'man', 'manpages',
    }

    @classmethod
    def classify(cls, relative_path: str) -> FileType:
        """
        Classify a file by its relative path within the project.

        Args:
            relative_path: Path relative to project root (e.g. "examples/demo/main.py")

        Returns:
            FileType classification
        """
        parts = PurePosixPath(relative_path).parts
        lower_parts = [p.lower() for p in parts]
        filename_lower = parts[-1].lower() if parts else ""

        # 1. Check generated files by suffix first (most specific)
        for suffix in cls.GENERATED_SUFFIXES:
            if filename_lower.endswith(suffix):
                return FileType.GENERATED

        # 2. Detect Java/Kotlin source tree — path segments under src/main/java,
        #    src/test/java, src/main/kotlin, or src/test/kotlin are package names,
        #    NOT directory classifications.
        #    e.g. "src/main/java/org/springframework/samples/petclinic/Vet.java"
        #    has "samples" in the path but it's a package name, not an example dir.
        #    e.g. "src/main/kotlin/com/example/Application.kt"
        #    has "example" in the path but it's a package name, not an example dir.
        in_java_source_tree = False
        for i, part in enumerate(lower_parts):
            if part in ('java', 'kotlin') and i >= 2:
                prev = lower_parts[i - 1] if i > 0 else ''
                prev2 = lower_parts[i - 2] if i > 1 else ''
                if prev in ('main', 'test') and prev2 == 'src':
                    in_java_source_tree = True
                    break

        # 3. Walk path segments for directory classification
        #    For Java/Kotlin source trees, only check segments BEFORE the java/kotlin package root
        java_package_start = None
        if in_java_source_tree:
            for i, part in enumerate(lower_parts):
                if part in ('java', 'kotlin') and i >= 2 and lower_parts[i - 1] in ('main', 'test') and lower_parts[i - 2] == 'src':
                    java_package_start = i + 1  # segments after java/kotlin are package names
                    break

        for idx, part in enumerate(lower_parts):
            # Skip Java package path segments — they are NOT directory classifications
            if java_package_start is not None and idx >= java_package_start:
                continue
            if part in cls.EXAMPLE_DIRS:
                return FileType.EXAMPLE
            if part in cls.VENDOR_DIRS:
                return FileType.VENDOR
            if part in cls.GENERATED_DIRS:
                return FileType.GENERATED
            if part in cls.BUILD_DIRS:
                return FileType.BUILD
            # Note: TEST_DIRS and DOC_DIRS are NOT excluded from scanning
            # by default — they are informational classifications.

        return FileType.APP_CODE

    @classmethod
    def classify_detailed(cls, relative_path: str) -> FileType:
        """
        Like classify() but also tags TEST and DOCUMENTATION paths.
        Use this when you need to know ALL classifications, not just
        the ones that should be excluded.
        """
        basic = cls.classify(relative_path)
        if basic != FileType.APP_CODE:
            return basic

        parts = PurePosixPath(relative_path).parts
        lower_parts = [p.lower() for p in parts]

        for part in lower_parts:
            if part in cls.TEST_DIRS:
                return FileType.TEST
            if part in cls.DOC_DIRS:
                return FileType.DOCUMENTATION

        return FileType.APP_CODE

    @classmethod
    def is_app_code(cls, relative_path: str) -> bool:
        """Return True if the path is production application code."""
        return cls.classify(relative_path) == FileType.APP_CODE

    @classmethod
    def is_example_path(cls, relative_path: str) -> bool:
        """Return True if the path is inside an example/sample/tutorial directory."""
        return cls.classify(relative_path) == FileType.EXAMPLE

    @classmethod
    def is_vendor_path(cls, relative_path: str) -> bool:
        """Return True if the path is vendored third-party code."""
        return cls.classify(relative_path) == FileType.VENDOR

    @classmethod
    def is_generated_file(cls, relative_path: str) -> bool:
        """Return True if the file is auto-generated."""
        return cls.classify(relative_path) == FileType.GENERATED

    @classmethod
    def should_skip_for_detection(cls, relative_path: str) -> bool:
        """
        Return True if this path should be skipped for framework/DB/ORM
        detection. Skips EXAMPLE, VENDOR, GENERATED, and BUILD paths.
        App code and test code are kept.
        """
        ft = cls.classify(relative_path)
        return ft in (FileType.EXAMPLE, FileType.VENDOR, FileType.GENERATED, FileType.BUILD)

    @classmethod
    def is_example_or_vendor(cls, relative_path: str) -> bool:
        """Return True if the path is example or vendor code."""
        ft = cls.classify(relative_path)
        return ft in (FileType.EXAMPLE, FileType.VENDOR)


# =============================================================================
# Gitignore Filter
# =============================================================================

class GitignoreFilter:
    """
    Lightweight .gitignore / .git/info/exclude parser that provides
    directory/file filtering.

    Loads ignore rules from a project root (both ``.gitignore`` and
    ``.git/info/exclude``) and provides a ``should_ignore`` method that
    extractors can use during their os.walk traversals.

    Supports:
    - Simple names (match anywhere): ``node_modules``, ``dist``
    - Directory-only patterns (trailing /): ``build/``
    - Rooted patterns (leading /): ``/vendor``
    - Path patterns: ``tests/repos``, ``docs/output``
    - Glob wildcards: ``*.pyc``, ``*.egg-info``
    - Negation (``!pattern``) to un-ignore
    - Comments (``#``) and blank lines

    Does NOT support ``**`` (double-star) globbing — not needed for typical
    .gitignore files and avoids complexity.

    Usage::

        gf = GitignoreFilter.from_root(Path("/my/project"))
        for root, dirs, files in os.walk(project_root):
            rel = os.path.relpath(root, project_root)
            dirs[:] = [d for d in dirs if not gf.should_ignore(
                os.path.join(rel, d) if rel != '.' else d, is_dir=True)]
    """

    def __init__(self, patterns: Optional[List['_GitignoreRule']] = None):
        self._rules: List['_GitignoreRule'] = patterns or []

    @classmethod
    def from_root(cls, root: Path) -> 'GitignoreFilter':
        """
        Parse ignore rules from project root.

        Loads rules from both ``.gitignore`` and ``.git/info/exclude``
        (the per-repo exclude file that Git also respects).

        Returns an empty filter (matches nothing) if neither file exists.
        """
        combined_text = ''

        # 1. .gitignore (project-level, committed to repo)
        gitignore_path = root / '.gitignore'
        if gitignore_path.is_file():
            try:
                combined_text += gitignore_path.read_text(
                    encoding='utf-8', errors='replace') + '\n'
            except OSError:
                pass

        # 2. .git/info/exclude (per-repo, NOT committed — personal excludes)
        exclude_path = root / '.git' / 'info' / 'exclude'
        if exclude_path.is_file():
            try:
                combined_text += exclude_path.read_text(
                    encoding='utf-8', errors='replace') + '\n'
            except OSError:
                pass

        if not combined_text.strip():
            return cls()

        return cls._parse(combined_text)

    @classmethod
    def _parse(cls, text: str) -> 'GitignoreFilter':
        """Parse .gitignore content into filter rules."""
        rules: List[_GitignoreRule] = []
        for line in text.splitlines():
            line = line.rstrip()
            # Skip blanks and comments
            if not line or line.startswith('#'):
                continue
            # Negation
            negate = False
            if line.startswith('!'):
                negate = True
                line = line[1:]
            if not line:
                continue

            # Directory-only flag (trailing /)
            dir_only = line.endswith('/')
            if dir_only:
                line = line.rstrip('/')

            # Rooted pattern (starts with / or contains / in the middle)
            # "tests/repos" is rooted because it has a / in it
            # "node_modules" is unrooted — matches anywhere
            rooted = line.startswith('/') or '/' in line
            line = line.lstrip('/')

            rules.append(_GitignoreRule(
                pattern=line,
                negate=negate,
                dir_only=dir_only,
                rooted=rooted,
            ))
        return cls(rules)

    def should_ignore(self, rel_path: str, is_dir: bool = False) -> bool:
        """
        Check whether a relative path should be ignored.

        Args:
            rel_path: Path relative to the project root, forward-slash
                      separated (e.g. "tests/repos" or "src/main.py").
            is_dir:   True if the path is a directory.

        Returns:
            True if the path matches an ignore rule (and is not negated).
        """
        # Normalise separators
        rel_path = rel_path.replace('\\', '/')
        # Remove leading ./
        if rel_path.startswith('./'):
            rel_path = rel_path[2:]

        matched = False
        for rule in self._rules:
            if rule.dir_only and not is_dir:
                continue
            if rule.matches(rel_path, is_dir):
                matched = not rule.negate
        return matched

    @property
    def is_empty(self) -> bool:
        """True when no rules were loaded (no .gitignore or empty file)."""
        return len(self._rules) == 0


class _GitignoreRule:
    """A single .gitignore rule."""

    __slots__ = ('pattern', 'negate', 'dir_only', 'rooted')

    def __init__(self, pattern: str, negate: bool, dir_only: bool, rooted: bool):
        self.pattern = pattern
        self.negate = negate
        self.dir_only = dir_only
        self.rooted = rooted

    def matches(self, rel_path: str, is_dir: bool) -> bool:
        """
        Check if a relative path matches this rule.

        - Rooted patterns are matched against the full relative path.
        - Unrooted patterns are matched against every suffix of the path
          (i.e. any segment can match).
        """
        if self.rooted:
            # Match against full relative path
            return fnmatch.fnmatch(rel_path, self.pattern)
        else:
            # Unrooted: match against the path itself and also the basename
            # "node_modules" should match "a/b/node_modules" and "node_modules"
            if fnmatch.fnmatch(rel_path, self.pattern):
                return True
            # Also try matching just the last component (basename)
            basename = rel_path.rsplit('/', 1)[-1]
            if fnmatch.fnmatch(basename, self.pattern):
                return True
            # And match against every suffix path
            # e.g. pattern "vendor" should match "services/api/vendor"
            parts = rel_path.split('/')
            for i in range(len(parts)):
                suffix = '/'.join(parts[i:])
                if fnmatch.fnmatch(suffix, self.pattern):
                    return True
            return False
