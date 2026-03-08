# CodeTrellis v4.1.0 - Testing Checklist

**Version:** 1.0.0
**Created:** 2 February 2026
**Based on:** Report 2 (CodeTrellis Deep Analysis Report) Section 7 Recommendations

---

## 🧪 Testing Overview

This checklist covers all testing requirements identified in the deep analysis report.
Use this to validate v4.1.0 improvements and ensure production readiness.

### Testing Pyramid

```
                    ┌─────────────┐
                    │    E2E      │  10% - Full workflow tests
                    │  (~5 tests) │
                    ├─────────────┤
                    │ Integration │  20% - Component interaction tests
                    │ (~20 tests) │
                    ├─────────────┤
                    │    Unit     │  70% - Individual function tests
                    │ (~100 tests)│
                    └─────────────┘
```

---

## ✅ Unit Tests Checklist

### 1. Error Handling Module (`test_errors.py`) - NEW v4.1.0

#### CodeTrellisErrorCode Tests

- [ ] **T1.1** All error codes have unique values
- [ ] **T1.2** Error codes follow naming convention (EXXX)
- [ ] **T1.3** Error categories are correctly grouped

#### CodeTrellisError Tests

- [ ] **T1.4** Error message formatting is correct

  ```python
  error = CodeTrellisError(CodeTrellisErrorCode.FILE_NOT_FOUND, "File missing", {"path": "/test.ts"})
  assert "[E100]" in str(error)
  assert "path: /test.ts" in str(error)
  ```

- [ ] **T1.5** Error to_dict() serialization works
- [ ] **T1.6** Error timestamp is set correctly
- [ ] **T1.7** Cause exception is preserved

#### ExtractorResult Tests

- [ ] **T1.8** success() factory method works
- [ ] **T1.9** failure() factory method works
- [ ] **T1.10** partial() factory method works
- [ ] **T1.11** Result data is correctly stored

#### ErrorCollector Tests

- [ ] **T1.12** add_error() collects errors
- [ ] **T1.13** add_warning() collects warnings
- [ ] **T1.14** has_errors property works
- [ ] **T1.15** summary() generates correct output
- [ ] **T1.16** to_dict() serialization works

#### resilient_extract Decorator Tests

- [ ] **T1.17** Normal extraction returns success result
- [ ] **T1.18** Exception is caught and returns failure result
- [ ] **T1.19** ExtractorResult passthrough works

---

### 2. Compressor Module (`test_compressor.py`)

#### Deduplication Tests - NEW v4.1.0

- [ ] **T2.1** \_deduplicate_interfaces removes exact duplicates

  ```python
  interfaces = [
      {"name": "Position", "file_path": "/types.ts"},
      {"name": "Position", "file_path": "/types.ts"},  # Duplicate
  ]
  result = compressor._deduplicate_interfaces(interfaces)
  assert len(result) == 1
  ```

- [ ] **T2.2** \_deduplicate_interfaces keeps different paths

  ```python
  interfaces = [
      {"name": "Position", "file_path": "/types.ts"},
      {"name": "Position", "file_path": "/models.ts"},  # Different file
  ]
  result = compressor._deduplicate_interfaces(interfaces)
  assert len(result) == 2
  ```

- [ ] **T2.3** \_deduplicate_by_name works correctly
- [ ] **T2.4** Empty list returns empty list

#### Compression Tier Tests

- [ ] **T2.5** COMPACT tier applies truncation limits
- [ ] **T2.6** PROMPT tier has no truncation
- [ ] **T2.7** FULL tier includes all details
- [ ] **T2.8** JSON tier returns valid JSON
- [ ] **T2.9** LOGIC tier includes function bodies

#### Interface Compression Tests

- [ ] **T2.10** Simple interface compression
- [ ] **T2.11** Interface with generics
- [ ] **T2.12** Interface with extends
- [ ] **T2.13** Interface with nested types

---

### 3. Interface Extractor (`test_interface_extractor.py`)

#### Basic Extraction

- [ ] **T3.1** Extract simple interface
- [ ] **T3.2** Extract interface with optional properties
- [ ] **T3.3** Extract interface with readonly properties
- [ ] **T3.4** Extract interface extending another

#### Complex Extraction

- [ ] **T3.5** Extract nested interface
- [ ] **T3.6** Extract interface with array types
- [ ] **T3.7** Extract interface with generic types
- [ ] **T3.8** Extract interface with Record types
- [ ] **T3.9** Extract interface with function types
- [ ] **T3.10** Extract multiple interfaces in same file

---

### 4. Type Extractor (`test_type_extractor.py`)

- [ ] **T4.1** Extract simple type alias
- [ ] **T4.2** Extract union type
- [ ] **T4.3** Extract intersection type
- [ ] **T4.4** Extract literal type
- [ ] **T4.5** Extract generic type alias
- [ ] **T4.6** Extract conditional type
- [ ] **T4.7** Extract mapped type
- [ ] **T4.8** Extract tuple type

---

### 5. Component Parser (`test_component_parser.py`)

- [ ] **T5.1** Parse component name and selector
- [ ] **T5.2** Parse standalone component
- [ ] **T5.3** Parse OnPush change detection
- [ ] **T5.4** Parse @Input decorator
- [ ] **T5.5** Parse input() signal
- [ ] **T5.6** Parse required input
- [ ] **T5.7** Parse @Output decorator
- [ ] **T5.8** Parse output() signal
- [ ] **T5.9** Parse signal with initial value
- [ ] **T5.10** Parse computed signal

---

### 6. Store Parser (`test_store_parser.py`)

- [ ] **T6.1** Parse withState interface
- [ ] **T6.2** Parse inline state
- [ ] **T6.3** Parse withComputed selectors
- [ ] **T6.4** Parse withMethods
- [ ] **T6.5** Parse patchState usage

---

### 7. Route Parser (`test_route_parser.py`)

- [ ] **T7.1** Parse simple route
- [ ] **T7.2** Parse route with redirect
- [ ] **T7.3** Parse route with parameters
- [ ] **T7.4** Parse child routes
- [ ] **T7.5** Parse lazy-loaded routes
- [ ] **T7.6** Parse route guards

---

### 8. Logic Extractor (`test_logic_extractor.py`)

- [ ] **T8.1** Extract TypeScript function body
- [ ] **T8.2** Extract Python function body
- [ ] **T8.3** Extract control flow (if/else/for)
- [ ] **T8.4** Extract API calls
- [ ] **T8.5** Extract data transformations
- [ ] **T8.6** Calculate complexity indicator

---

### 9. Python Extractors (`test_python_extractors.py`)

#### Dataclass Extractor

- [ ] **T9.1** Extract basic dataclass
- [ ] **T9.2** Extract frozen dataclass
- [ ] **T9.3** Extract dataclass with defaults
- [ ] **T9.4** Extract dataclass with field()

#### Pydantic Extractor

- [ ] **T9.5** Extract Pydantic model
- [ ] **T9.6** Extract model validators
- [ ] **T9.7** Extract computed fields
- [ ] **T9.8** Extract model config

#### FastAPI Extractor

- [ ] **T9.9** Extract GET endpoint
- [ ] **T9.10** Extract POST endpoint
- [ ] **T9.11** Extract path parameters
- [ ] **T9.12** Extract query parameters
- [ ] **T9.13** Extract request body

---

## ✅ Integration Tests Checklist

### 10. Scanner Integration (`test_scanner_integration.py`)

- [ ] **T10.1** Scan folder with multiple component files
- [ ] **T10.2** Scan folder with component + service + store
- [ ] **T10.3** Scan folder and extract all dependencies
- [ ] **T10.4** Scan folder and link interfaces to components
- [ ] **T10.5** Handle circular dependencies gracefully
- [ ] **T10.6** Skip ignored files/folders correctly
- [ ] **T10.7** Generate correct file structure

### 11. Formatter Integration (`test_formatter_integration.py`)

- [ ] **T11.1** Format component with all sections
- [ ] **T11.2** Format store with state/computed/methods
- [ ] **T11.3** Format service with API/events/deps
- [ ] **T11.4** Format routes file
- [ ] **T11.5** v2.0 format is valid and parseable

### 12. Error Handling Integration (`test_error_integration.py`) - NEW v4.1.0

- [ ] **T12.1** Extraction continues after single file error
- [ ] **T12.2** ErrorCollector aggregates all errors
- [ ] **T12.3** Partial results are returned on failure
- [ ] **T12.4** Error context includes file path and line

---

## ✅ End-to-End Tests Checklist

### 13. CLI E2E (`test_cli_e2e.py`)

- [ ] **T13.1** `codetrellis scan <path>` generates matrix.prompt
- [ ] **T13.2** `codetrellis scan <path> --tier compact` uses COMPACT tier
- [ ] **T13.3** `codetrellis scan <path> --tier logic` uses LOGIC tier
- [ ] **T13.4** `codetrellis scan <path> --deep` enables LSP mode
- [ ] **T13.5** `codetrellis show` displays compressed output
- [ ] **T13.6** .codetrellis validate <path>` reports validation errors
- [ ] **T13.7** `codetrellis watch` starts file watcher

### 14. Full Project E2E (`test_project_e2e.py`)

- [ ] **T14.1** Scan Angular project successfully
- [ ] **T14.2** Scan Python FastAPI project successfully
- [ ] **T14.3** Scan monorepo with multiple apps
- [ ] **T14.4** Compare output with expected baseline
- [ ] **T14.5** No duplicate interfaces in output

---

## ✅ Regression Tests Checklist

### 15. Version Compatibility (`test_version_compatibility.py`)

- [ ] **T15.1** Version matches in pyproject.toml
- [ ] **T15.2** Version matches in **init**.py
- [ ] **T15.3** Version matches in README.md
- [ ] **T15.4** Cache version matches code version

---

## 📊 Test Coverage Requirements

| Module                   | Current  | Target  | Priority |
| ------------------------ | -------- | ------- | -------- |
| `errors.py`              | 0%       | 90%     | HIGH     |
| `compressor.py`          | ~20%     | 80%     | HIGH     |
| `scanner.py`             | ~20%     | 80%     | HIGH     |
| `interface_extractor.py` | ~30%     | 80%     | MEDIUM   |
| `logic_extractor.py`     | 0%       | 80%     | HIGH     |
| `cli.py`                 | ~10%     | 60%     | MEDIUM   |
| **Overall**              | **~15%** | **75%** | -        |

---

## 📁 Test Fixtures Required

```
tests/fixtures/
├── projects/
│   ├── angular-sample/        # Sample Angular project
│   │   ├── src/
│   │   │   ├── app/
│   │   │   │   ├── components/
│   │   │   │   ├── services/
│   │   │   │   └── stores/
│   │   │   └── app.routes.ts
│   │   └── package.json
│   ├── python-fastapi/        # Sample FastAPI project
│   │   ├── app/
│   │   │   ├── models/
│   │   │   ├── routes/
│   │   │   └── main.py
│   │   └── requirements.txt
│   └── mixed-monorepo/        # Multi-language project
├── snapshots/
│   ├── compact_output.txt     # Expected COMPACT output
│   ├── prompt_output.txt      # Expected PROMPT output
│   └── logic_output.txt       # Expected LOGIC output
└── error_cases/
    ├── invalid_typescript.ts  # Syntax error file
    ├── circular_import.py     # Circular import case
    └── malformed_json.json    # Invalid JSON
```

---

## 🔄 Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov.codetrellis --cov-report=html

# Run specific test file
pytest tests/unit/test_errors.py

# Run specific test
pytest tests/unit/test_errors.py::TestCodeTrellisError::test_error_formatting

# Run with verbose output
pytest tests/ -v

# Run only v4.1.0 new tests
pytest tests/ -m "v410"
```

---

## ✏️ Test Implementation Status

| Test File                     | Tests Written | Tests Passing | Coverage |
| ----------------------------- | ------------- | ------------- | -------- |
| `test_errors.py`              | ⬜ 0/19       | -             | 0%       |
| `test_compressor.py`          | ⬜ Partial    | -             | ~20%     |
| `test_interface_extractor.py` | ⬜ Partial    | -             | ~30%     |
| `test_logic_extractor.py`     | ⬜ 0/6        | -             | 0%       |
| `test_scanner_integration.py` | ⬜ Partial    | -             | ~20%     |
| `test_cli_e2e.py`             | ⬜ 0/7        | -             | 0%       |

---

## Sign-off

| Phase               | Status | Verified By | Date |
| ------------------- | ------ | ----------- | ---- |
| Unit Tests          | ⬜     |             |      |
| Integration Tests   | ⬜     |             |      |
| E2E Tests           | ⬜     |             |      |
| Coverage Target Met | ⬜     |             |      |

---

_Checklist Version: 1.0.0_
_Based on Report 2 recommendations_
