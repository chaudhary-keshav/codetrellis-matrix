"""
Enhanced MobX Parser v1.0

Provides comprehensive MobX state management parsing for JavaScript/TypeScript files.

Detects and extracts:
- Observables (makeObservable, makeAutoObservable, observable(), @observable)
- Computed properties (computed(), @computed, getter annotations)
- Actions (action(), @action, runInAction(), flow(), @flow)
- Reactions (autorun, reaction, when, observe, intercept)
- API patterns (imports, configure(), observer(), TypeScript types, ecosystem)
- Framework patterns (16 patterns for file detection)
- Feature patterns (20 patterns for feature detection)
- Version detection (MobX v1-v6+)

Architecture:
- 5 specialized extractors (observable, computed, action, reaction, api)
- Regex-based AST (no tree-sitter dependency)
- Runs as supplementary layer on JS/TS files
- File detection via is_mobx_file() before full parse

Part of CodeTrellis v4.51 - MobX Framework Support
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from codetrellis.extractors.mobx import (
    MobXObservableExtractor,
    MobXComputedExtractor,
    MobXActionExtractor,
    MobXReactionExtractor,
    MobXApiExtractor,
)


@dataclass
class MobXParseResult:
    """Result of parsing a file for MobX state management patterns."""
    # Observable-related
    observables: List[Dict] = field(default_factory=list)
    auto_observables: List[Dict] = field(default_factory=list)
    decorator_observables: List[Dict] = field(default_factory=list)

    # Computed-related
    computeds: List[Dict] = field(default_factory=list)

    # Action-related
    actions: List[Dict] = field(default_factory=list)
    flows: List[Dict] = field(default_factory=list)

    # Reaction-related
    reactions: List[Dict] = field(default_factory=list)

    # API-related
    imports: List[Dict] = field(default_factory=list)
    configures: List[Dict] = field(default_factory=list)
    types: List[Dict] = field(default_factory=list)
    integrations: List[Dict] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    mobx_version: str = ""


class EnhancedMobXParser:
    """Enhanced parser for MobX state management framework."""

    # Framework detection patterns — if ANY match, file might use MobX
    FRAMEWORK_PATTERNS = [
        re.compile(r'''from\s+['"]mobx['"]'''),
        re.compile(r'''from\s+['"]mobx-react['"]'''),
        re.compile(r'''from\s+['"]mobx-react-lite['"]'''),
        re.compile(r'''from\s+['"]mobx-state-tree['"]'''),
        re.compile(r'''from\s+['"]mobx-keystone['"]'''),
        re.compile(r'''from\s+['"]mobx-utils['"]'''),
        re.compile(r'''require\s*\(\s*['"]mobx['"]\s*\)'''),
        re.compile(r'''require\s*\(\s*['"]mobx-react(?:-lite)?['"]\s*\)'''),
        re.compile(r'\bmakeObservable\s*\('),
        re.compile(r'\bmakeAutoObservable\s*\('),
        re.compile(r'\bobservable\s*\('),
        re.compile(r'@observable'),
        re.compile(r'@computed'),
        re.compile(r'@action'),
        re.compile(r'\bobserver\s*\('),
        re.compile(r'\brunInAction\s*\('),
    ]

    # Feature detection patterns
    FEATURE_PATTERNS = {
        'makeObservable': re.compile(r'\bmakeObservable\s*\('),
        'makeAutoObservable': re.compile(r'\bmakeAutoObservable\s*\('),
        'observable': re.compile(r'\bobservable\s*[.(]'),
        'observable.ref': re.compile(r'\bobservable\.ref\b'),
        'observable.shallow': re.compile(r'\bobservable\.shallow\b'),
        'observable.deep': re.compile(r'\bobservable\.deep\b'),
        'observable.struct': re.compile(r'\bobservable\.struct\b'),
        'computed': re.compile(r'\bcomputed\s*\('),
        'computed.struct': re.compile(r'\bcomputed\.struct\b'),
        'action': re.compile(r'\baction\s*[.(]'),
        'action.bound': re.compile(r'\baction\.bound\b'),
        'runInAction': re.compile(r'\brunInAction\s*\('),
        'flow': re.compile(r'\bflow\s*\('),
        'flow.bound': re.compile(r'\bflow\.bound\b'),
        'autorun': re.compile(r'\bautorun\s*\('),
        'reaction': re.compile(r'\breaction\s*\('),
        'when': re.compile(r'\bwhen\s*\('),
        'observer': re.compile(r'\bobserver\s*\('),
        'useLocalObservable': re.compile(r'\buseLocalObservable\s*\('),
        'configure': re.compile(r'\bconfigure\s*\('),
    }

    def __init__(self):
        """Initialize the MobX parser with all extractors."""
        self.observable_extractor = MobXObservableExtractor()
        self.computed_extractor = MobXComputedExtractor()
        self.action_extractor = MobXActionExtractor()
        self.reaction_extractor = MobXReactionExtractor()
        self.api_extractor = MobXApiExtractor()

    def is_mobx_file(self, content: str, file_path: str = "") -> bool:
        """Check if a file contains MobX patterns.

        Uses fast pattern matching to avoid full parsing of non-MobX files.

        Args:
            content: File content to check
            file_path: Path to the file (for extension-based checks)

        Returns:
            True if the file likely uses MobX
        """
        # Quick check: any framework pattern matches?
        for pattern in self.FRAMEWORK_PATTERNS:
            if pattern.search(content):
                return True
        return False

    def parse(self, content: str, file_path: str = "") -> MobXParseResult:
        """Parse a file for MobX patterns.

        Calls all 5 extractors and aggregates results into MobXParseResult.

        Args:
            content: File content to parse
            file_path: Path to the file

        Returns:
            MobXParseResult with all extracted information
        """
        result = MobXParseResult()

        # Run observable extractor
        try:
            obs_result = self.observable_extractor.extract(content, file_path)
            result.observables = [self._dataclass_to_dict(o) for o in obs_result.get('observables', [])]
            result.auto_observables = [self._dataclass_to_dict(o) for o in obs_result.get('auto_observables', [])]
            result.decorator_observables = [self._dataclass_to_dict(o) for o in obs_result.get('decorator_observables', [])]
        except Exception:
            pass

        # Run computed extractor
        try:
            comp_result = self.computed_extractor.extract(content, file_path)
            result.computeds = [self._dataclass_to_dict(c) for c in comp_result.get('computeds', [])]
        except Exception:
            pass

        # Run action extractor
        try:
            act_result = self.action_extractor.extract(content, file_path)
            result.actions = [self._dataclass_to_dict(a) for a in act_result.get('actions', [])]
            result.flows = [self._dataclass_to_dict(f) for f in act_result.get('flows', [])]
        except Exception:
            pass

        # Run reaction extractor
        try:
            rxn_result = self.reaction_extractor.extract(content, file_path)
            result.reactions = [self._dataclass_to_dict(r) for r in rxn_result.get('reactions', [])]
        except Exception:
            pass

        # Run API extractor
        try:
            api_result = self.api_extractor.extract(content, file_path)
            result.imports = [self._dataclass_to_dict(i) for i in api_result.get('imports', [])]
            result.configures = [self._dataclass_to_dict(c) for c in api_result.get('configures', [])]
            result.types = [self._dataclass_to_dict(t) for t in api_result.get('types', [])]
            result.integrations = [self._dataclass_to_dict(i) for i in api_result.get('integrations', [])]
            result.detected_frameworks = api_result.get('detected_ecosystems', [])
        except Exception:
            pass

        # Detect features
        result.detected_features = self._detect_features(content)

        # Detect MobX version
        result.mobx_version = self._detect_version(content)

        return result

    def _detect_features(self, content: str) -> List[str]:
        """Detect which MobX features are used in the file."""
        features = []
        for name, pattern in self.FEATURE_PATTERNS.items():
            if pattern.search(content):
                features.append(name)
        return features

    def _detect_version(self, content: str) -> str:
        """Detect MobX version from content patterns.

        Version detection heuristics:
        - v6: makeObservable, makeAutoObservable (introduced in v6)
        - v5: Proxy-based (useProxies config, no decorators by default)
        - v4: Legacy decorators (@observable, @action, @computed required)
        - v3 and below: Very old patterns (observable.shallowMap, etc.)
        """
        has_make_observable = bool(re.search(r'\bmakeObservable\s*\(', content))
        has_make_auto_observable = bool(re.search(r'\bmakeAutoObservable\s*\(', content))
        has_configure = bool(re.search(r'\bconfigure\s*\(', content))
        has_decorators = bool(re.search(r'@observable|@action|@computed', content))
        has_legacy_observable = bool(re.search(r'observable\.shallowMap|observable\.shallowArray', content))
        has_use_proxies = bool(re.search(r'useProxies', content))

        # v6: makeObservable / makeAutoObservable are the definitive markers
        if has_make_observable or has_make_auto_observable:
            return 'v6'

        # v5: Proxy-based with configure({ useProxies: ... })
        if has_use_proxies or (has_configure and not has_make_observable):
            return 'v5'

        # v4: Legacy decorators but no makeObservable
        if has_decorators and not has_make_observable:
            return 'v4'

        # v3 and below: very old API
        if has_legacy_observable:
            return 'v3'

        # Default: unknown but MobX is present
        return 'v6'  # Assume latest

    def _dataclass_to_dict(self, obj: Any) -> Dict[str, Any]:
        """Convert a dataclass instance to a dictionary."""
        if hasattr(obj, '__dataclass_fields__'):
            result = {}
            for field_name in obj.__dataclass_fields__:
                value = getattr(obj, field_name)
                if isinstance(value, list):
                    result[field_name] = [
                        self._dataclass_to_dict(v) if hasattr(v, '__dataclass_fields__') else v
                        for v in value
                    ]
                elif hasattr(value, '__dataclass_fields__'):
                    result[field_name] = self._dataclass_to_dict(value)
                else:
                    result[field_name] = value
            return result
        return obj

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings. Returns >0 if v1 > v2, <0 if v1 < v2, 0 if equal."""
        version_order = {'': 0, 'v3': 3, 'v4': 4, 'v5': 5, 'v6': 6}
        return version_order.get(v1, 0) - version_order.get(v2, 0)
