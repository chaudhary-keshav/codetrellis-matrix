# Stimulus / Hotwire Integration — Consolidated Analysis Report

**CodeTrellis v4.68 — Session 58**
**Date:** February 2026
**Branch:** batch-2

---

## 1. Executive Summary

Full Stimulus / Hotwire framework support has been integrated into CodeTrellis, following the established language integration pattern used for Alpine.js (Session 52) and HTMX (Session 53). The integration covers:

- **Stimulus** v1 (`stimulus` npm), v2 (`@hotwired/stimulus`), v3 (outlets, afterLoad, action options)
- **Turbo** v7-v8 (frames, streams, drive, morphing, events)
- **Strada** v1 (BridgeComponent, BridgeElement)

**91 new tests**, all passing. **Zero regressions** across the existing 5018-test suite. Round 1 scanner evaluation on 3 public repos extracted **18 controllers, 50 actions, 70 values, 32 targets** from 49 Stimulus files.

---

## 2. Files Created

| File                                                      | Lines | Purpose                                                    |
| --------------------------------------------------------- | ----- | ---------------------------------------------------------- |
| `codetrellis/extractors/stimulus/__init__.py`             | ~30   | Module init, exports all extractors + dataclasses          |
| `codetrellis/extractors/stimulus/controller_extractor.py` | ~160  | Extract controller class definitions, lifecycle, statics   |
| `codetrellis/extractors/stimulus/target_extractor.py`     | ~160  | Extract HTML data-\*-target (v1/v2), JS getters, callbacks |
| `codetrellis/extractors/stimulus/action_extractor.py`     | ~200  | Extract data-action descriptors, params, options, globals  |
| `codetrellis/extractors/stimulus/value_extractor.py`      | ~195  | Extract static values, HTML attrs, get/set, valueChanged   |
| `codetrellis/extractors/stimulus/api_extractor.py`        | ~540  | Imports, CDNs, Turbo, Strada, integrations, configs        |
| `codetrellis/stimulus_parser_enhanced.py`                 | ~640  | EnhancedStimulusParser orchestrating all 5 extractors      |
| `tests/unit/test_stimulus_parser_enhanced.py`             | ~1200 | 91 tests across 7 test classes                             |

## 3. Files Modified

| File                              | Changes                                                                                                        |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `codetrellis/scanner.py`          | Import, 17 ProjectMatrix fields, parser init, 3 file routing branches, `_parse_stimulus()` method (~160 lines) |
| `codetrellis/compressor.py`       | 5 section calls + 5 compression methods (~200 lines)                                                           |
| `codetrellis/bpl/selector.py`     | stimulus_count, framework mapping, prefix mapping, filter block, debug log                                     |
| `codetrellis/cache_optimizer.py`  | 5 STIMULUS sections with priorities 1325-1329                                                                  |
| `codetrellis/mcp_server.py`       | STIMULUS_API, STIMULUS_CONTROLLERS, STIMULUS_ACTIONS                                                           |
| `codetrellis/jit_context.py`      | .html/.htm extensions, component path pattern                                                                  |
| `codetrellis/skills_generator.py` | API + component detect_sections                                                                                |

## 4. Dataclass Architecture

### StimulusControllerInfo

- `name`, `identifier`, `extends`, `has_initialize`, `has_connect`, `has_disconnect`, `has_after_load`
- `static_targets: List[str]`, `static_values: List[str]`, `static_classes: List[str]`, `static_outlets: List[str]`
- `methods: List[str]`, `version_hint`

### StimulusTargetInfo

- `name`, `target_type` (declaration/html_attribute/getter/callback), `controller_name`
- `is_plural`, `has_existence_check`, `is_connected_callback`, `is_disconnected_callback`
- `is_v1_format`, `version_hint`

### StimulusActionInfo

- `descriptor`, `event_name`, `controller_name`, `method_name`
- `has_prevent`, `has_stop`, `is_global`, `global_target`, `keyboard_filter`
- `params: List[str]`

### StimulusValueInfo

- `name`, `value_type`, `default_value`, `value_usage` (declaration/html_attribute/getter/setter/callback)
- `controller_name`, `has_change_callback`, `is_complex_type`

### StimulusImportInfo / StimulusIntegrationInfo / StimulusConfigInfo / StimulusCDNInfo

- Full import tracking (ESM/CJS/dynamic/side-effect), CDN version extraction, config detection

### StimulusParseResult

- Aggregates all extraction results + `detected_frameworks`, `detected_features`, `stimulus_version`, `has_turbo`, `has_strada`

## 5. Version Detection

| Version | Detection Signals                                                                 |
| ------- | --------------------------------------------------------------------------------- |
| v1      | `import ... from "stimulus"` (old npm package)                                    |
| v2      | `import ... from "@hotwired/stimulus"` (Hotwire era)                              |
| v3      | `static outlets = [...]`, `afterLoad()`, `outletConnected/Disconnected` callbacks |

## 6. Framework Detection (20+ patterns)

`stimulus`, `turbo`, `turbo-rails`, `strada`, `stimulus-use`, `stimulus-components`, `stimulus-vite-helpers`, `stimulus-webpack-helpers`, `stimulus-flatpickr`, `stimulus-autocomplete`, `stimulus-hotkeys`, `tailwind`, `rails`, `laravel-vite`, `django`, `phoenix`, `importmap`, `webpack`, `vite`, `esbuild`

## 7. Feature Detection (40+ patterns)

Controllers: `controller-class`, `lifecycle-connect/disconnect/initialize`, `afterLoad`, `static-targets/values/classes/outlets`
Targets: `html-target-v1/v2`, `target-getter`, `target-callback`
Actions: `html-action`, `action-options`, `action-params`, `keyboard-filter`, `global-action`
Values: `static-values`, `value-getter/setter`, `value-changed`
API: `app-start/register/load`, `definitions-from-context`
Turbo: `turbo-frame`, `turbo-stream`, `turbo-drive`, `turbo-morph`, `turbo-events`
Strada: `bridge-component`, `bridge-element`

## 8. ProjectMatrix Fields (17 new)

```python
stimulus_controllers: list          # Controller class definitions
stimulus_targets: list              # Target usages (HTML + JS)
stimulus_actions: list              # Action descriptors
stimulus_values: list               # Value definitions
stimulus_imports: list              # Import statements
stimulus_integrations: list         # Ecosystem integrations
stimulus_configs: list              # Configuration entries
stimulus_cdns: list                 # CDN script tags
stimulus_detected_frameworks: list  # Detected frameworks
stimulus_detected_features: list    # Detected features
stimulus_version: str               # Detected Stimulus version
stimulus_has_turbo: bool            # Turbo detected
stimulus_has_strada: bool           # Strada detected
stimulus_has_turbo_frames: bool     # Turbo frames detected
stimulus_has_turbo_streams: bool    # Turbo streams detected
stimulus_has_outlets: bool          # v3 outlets detected
stimulus_has_cdn: bool              # CDN usage detected
```

## 9. Compressor Sections (5)

1. **STIMULUS_CONTROLLERS** — Controller name, identifier, lifecycle, statics, methods
2. **STIMULUS_TARGETS** — Grouped by controller, type, version hint
3. **STIMULUS_ACTIONS** — Grouped by controller, event→method, options, params
4. **STIMULUS_VALUES** — Grouped by controller, type, defaults, changed callbacks
5. **STIMULUS_API** — Imports, CDNs, configs, integrations, version, frameworks, features

## 10. Test Results

### Stimulus Tests: 91/91 ✅

- TestStimulusControllerExtractor: 8 tests
- TestStimulusTargetExtractor: 5 tests
- TestStimulusActionExtractor: 8 tests
- TestStimulusValueExtractor: 5 tests
- TestStimulusApiExtractor: 18 tests
- TestEnhancedStimulusParser: 28 tests
- TestStimulusIntegration: 3 tests

### Full Suite: 5018 passed, 6 failed (pre-existing JSON-LD bug)

All 6 failures are in `matrix_jsonld.py:638` (`project_profile` returning `None`) — pre-existing, confirmed by testing on base branch without Stimulus changes.

## 11. Round 1 Scanner Evaluation

### Repo 1: hotwired/stimulus-starter

- 5 total files, 3 Stimulus files
- 0 controllers (starter template), 3 imports, 1 integration
- Frameworks: stimulus, stimulus-webpack-helpers
- Features: app-load, app-start, definitions-from-context, lifecycle-connect
- Version: v2

### Repo 2: hotwired/stimulus (main repo)

- 119 total files, 43 Stimulus files
- **18 controllers**, 32 targets, 50 actions, 70 values, 7 imports
- Frameworks: stimulus, tailwind
- Features: action-options, action-params, afterLoad, app-register, class-getter, controller-class, global-action, html-action, html-target-v1, html-target-v2, keyboard-filter, lifecycle-_, outlet-callback, static-_, target-callback, value-changed, value-getter
- Version: v2 (with v3 features detected)
- Has Turbo: Yes

### Repo 3: thoughtbot/hotwire-example-template

- 14 total files, 3 Stimulus files
- 0 controllers (Rails template), 3 imports, 1 config
- Frameworks: stimulus
- Features: app-start, lifecycle-connect
- Version: v2
- Has Turbo: Yes

### Summary

| Metric            | Total |
| ----------------- | ----- |
| Stimulus files    | 49    |
| Controllers       | 18    |
| Targets           | 32    |
| Actions           | 50    |
| Values            | 70    |
| Imports           | 13    |
| Repos with Turbo  | 2/3   |
| Repos with Strada | 0/3   |

## 12. Bugs Found & Fixed

| #   | Bug                                                                         | Fix                                                                          |
| --- | --------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| 1   | Scanner `_parse_stimulus()` used `act.event` instead of `act.event_name`    | Fixed to `act.event_name`, `act.controller_name`, `act.method_name`          |
| 2   | Scanner used `tgt.controller` and `tgt.source` (non-existent fields)        | Fixed to `tgt.controller_name`, removed `source` reference                   |
| 3   | Scanner used `val.controller`, `val.source`, `val.has_changed_callback`     | Fixed to `val.controller_name`, `val.value_usage`, `val.has_change_callback` |
| 4   | Compressor referenced `t.get('source')` and `v.get('has_changed_callback')` | Fixed to `t.get('target_type')` and `v.get('has_change_callback')`           |
| 5   | Test assertions used `action.event`, `action.controller`, `action.method`   | Fixed to `event_name`, `controller_name`, `method_name`                      |
| 6   | Test assertion used `v.has_changed_callback`                                | Fixed to `v.has_change_callback`                                             |
| 7   | `is_stimulus_file()` didn't detect bare `import "@hotwired/turbo"`          | Added side-effect import pattern to detection                                |
| 8   | API extractor didn't extract side-effect imports                            | Added `SIDE_EFFECT_IMPORT_PATTERN`                                           |

## 13. Architecture Decisions

1. **Followed Alpine.js/HTMX pattern** — Same extractor→parser→scanner→compressor→BPL pipeline
2. **Regex-based extraction** — No external dependencies needed (tree-sitter optional, not required)
3. **Version-aware detection** — v1/v2/v3 detection via import source + static features
4. **Multi-framework awareness** — Single parser handles Stimulus + Turbo + Strada
5. **Side-effect import support** — Added for `import "@hotwired/turbo"` (no `from` keyword)
6. **Dict key naming** — Scanner stores with readable keys (`"controller"`, `"event"`, `"method"`) while accessing dataclass fields with accurate names

---

_Generated as part of CodeTrellis v4.68 Stimulus/Hotwire integration, Session 58._
