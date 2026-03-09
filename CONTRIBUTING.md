# Contributing to CodeTrellis

Thank you for your interest in contributing to CodeTrellis! This guide covers
the development workflow, architecture, and conventions you'll need to get
started.

## Quick Start

```bash
# Clone and install
git clone <repo-url>
cd codetrellis
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pip install -r requirements-test.txt

# Run tests
pytest tests/ -x -q

# Run a scan
codetrellis scan . --optimal
```

## Architecture Overview

CodeTrellis processes source code through a well-defined pipeline:

```
Extractors → Parser → Scanner → Compressor → BPL → Matrix Output
```

| Stage          | Purpose                                                 | Location                                |
| -------------- | ------------------------------------------------------- | --------------------------------------- |
| **Extractors** | Framework-specific extraction (routes, models, configs) | `codetrellis/extractors/<framework>/`   |
| **Parser**     | Language-level AST/regex parsing (classes, functions)   | `codetrellis/<lang>_parser_enhanced.py` |
| **Scanner**    | Orchestrates parsers, dispatches by file type           | `codetrellis/scanner.py`                |
| **Compressor** | Deduplicates and compresses parsed data                 | `codetrellis/compressor.py`             |
| **BPL**        | Best Practices Library — context-aware guidance         | `codetrellis/bpl/`                      |
| **Output**     | matrix.json + matrix.prompt (AI-ready context)          | `.codetrellis/cache/`                   |

## Adding a New Language Parser

### 1. Create Extractors (if framework-specific)

```
codetrellis/extractors/myframework/
├── __init__.py
├── controller_extractor.py
├── model_extractor.py
└── route_extractor.py
```

Each extractor is a class with an `extract(content, file_path)` method returning
a dataclass with extracted elements.

### 2. Create the Enhanced Parser

Create `codetrellis/mylang_parser_enhanced.py`:

```python
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class MyLangParseResult:
    """Complete parse result for a MyLang file."""
    file_path: str
    file_type: str = "mylang"
    classes: List[MyLangClassInfo] = field(default_factory=list)
    functions: List[MyLangFunctionInfo] = field(default_factory=list)
    imports: List[MyLangImportInfo] = field(default_factory=list)
    detected_frameworks: List[str] = field(default_factory=list)

class EnhancedMyLangParser:
    """Extracts types, functions, and framework elements from MyLang files."""

    def parse(self, content: str, file_path: str = "") -> MyLangParseResult:
        result = MyLangParseResult(file_path=file_path)
        if not content or not content.strip():
            return result
        result.classes = self._extract_classes(content, file_path)
        result.functions = self._extract_functions(content, file_path)
        result.detected_frameworks = self._detect_frameworks(content)
        return result
```

### 3. Register in Scanner

In `codetrellis/scanner.py`:

1. Import: `from codetrellis.mylang_parser_enhanced import EnhancedMyLangParser`
2. Instantiate in `__init__`: `self.mylang_parser = EnhancedMyLangParser()`
3. Add dispatch method: `def _parse_mylang(self, content, path): ...`
4. Add file type check in the scan dispatcher

### 4. Add Compression

In `codetrellis/compressor.py`, add `_compress_mylang_*` methods that transform
the parsed data into the compressed matrix format.

### 5. Write Tests

Create `tests/unit/test_mylang_parser_enhanced.py`:

```python
from codetrellis.mylang_parser_enhanced import EnhancedMyLangParser

class TestEnhancedMyLangParser:
    def setup_method(self):
        self.parser = EnhancedMyLangParser()

    def test_extracts_classes(self):
        code = '...'  # Realistic fixture
        result = self.parser.parse(code, "test.ml")
        assert len(result.classes) >= 1
        assert result.classes[0].name == "ExpectedName"

    def test_empty_input(self):
        result = self.parser.parse("", "test.ml")
        assert len(result.classes) == 0
```

Run: `pytest tests/unit/test_mylang_parser_enhanced.py -v`

## Project Conventions

### Code Style

- **Python 3.9+** — use type hints, dataclasses, and f-strings
- **Formatting**: `black` (line length 88)
- **Linting**: `ruff`
- **Type checking**: `mypy`

### Parser Conventions

- All parsers use regex-based extraction (no external AST dependencies required)
- Parse results are `@dataclass` types with `field(default_factory=list)`
- Every parser has `parse(content: str, file_path: str) -> ParseResult`
- Framework detection goes in `_detect_frameworks(content) -> List[str]`

### Test Conventions

- Unit tests: `tests/unit/test_<component>.py`
- Integration tests: `tests/integration/`
- Fixtures: inline strings in test files (keep tests self-contained)
- Use `pytest` with `-x` flag (fail fast)
- Minimum: test `parse()` on realistic input + test empty input

### Quality Gates

- Full test suite must pass: `pytest tests/ -x -q`
- Parser changes gated by matrixbench: `python scripts/run_matrixbench.py`
- Baseline score: 90.0% (20/22 tasks)

## Running Tests

```bash
# Full suite
pip install -e ".[dev]" -r requirements-test.txt
pytest tests/ -x -q

# Specific parser
pytest tests/unit/test_python_parser_enhanced.py -v

# Integration tests
pytest tests/integration/ -v

# With coverage
pytest tests/ --cov=codetrellis --cov-report=term-missing
```

## Common Tasks

### Re-scan the project

```bash
codetrellis scan . --optimal        # Full scan
codetrellis scan . --incremental    # Changed files only
```

### Validate extraction completeness

```bash
codetrellis validate .
```

### Run matrixbench (quality gate)

```bash
python scripts/run_matrixbench.py
```

### Start MCP server for AI integration

```bash
codetrellis mcp .
```

## Directory Structure

```
codetrellis/
├── cli.py                          # CLI entry point (argparse)
├── scanner.py                      # File scanning orchestrator (~26K LOC)
├── compressor.py                   # Matrix compression (~28K LOC)
├── *_parser_enhanced.py            # 90+ language/framework parsers
├── extractors/                     # Framework-specific extractors
│   ├── aspnetcore/
│   ├── nestjs_enhanced/
│   ├── stimulus/
│   └── ...
├── bpl/                            # Best Practices Library
├── mcp_server.py                   # MCP protocol server
├── streaming.py                    # Streaming extraction pipeline
├── parallel.py                     # Parallel file processing
├── jit_context.py                  # Just-in-time file context
└── matrixbench_scorer.py           # Quality benchmark suite
tests/
├── unit/                           # ~180 unit test files
├── integration/                    # End-to-end tests
└── benchmarks/                     # Performance benchmarks
```
