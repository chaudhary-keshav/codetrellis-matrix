"""
Enhanced RxJS reactive programming parser for CodeTrellis.

Parses JavaScript/TypeScript files containing RxJS
reactive code. Delegates to 5 specialized extractors for comprehensive
reactive programming analysis.

Supports:
- RxJS v5 (operator chaining, deep imports)
- RxJS v6 (pipeable operators, rxjs/operators)
- RxJS v7 (tree-shakable, firstValueFrom, top-level import)
- Operators: creation, transformation, filtering, combination, error, multicasting, utility
- Subjects: Subject, BehaviorSubject, ReplaySubject, AsyncSubject
- Schedulers: async, asap, queue, animationFrame, TestScheduler
- Testing: marble diagrams, hot/cold observables
- Framework integrations: Angular, NestJS, NgRx, NGXS, redux-observable, Vue-Rx
- TypeScript types: Observable, Observer, Subscription, etc.
- Deprecated API detection

AST via regex + optional tree-sitter-javascript / tsserver LSP.
v4.77: Full RxJS support.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from codetrellis.extractors.rxjs import (
    RxjsOperatorExtractor,
    RxjsObservableExtractor,
    RxjsSubjectExtractor,
    RxjsSchedulerExtractor,
    RxjsAPIExtractor,
    RxjsOperatorInfo,
    RxjsCustomOperatorInfo,
    RxjsPipeInfo,
    RxjsObservableInfo,
    RxjsSubscriptionInfo,
    RxjsConversionInfo,
    RxjsSubscriptionMgmtInfo,
    RxjsSubjectInfo,
    RxjsSubjectEmissionInfo,
    RxjsSchedulerInfo,
    RxjsTestingInfo,
    RxjsMarbleInfo,
    RxjsImportInfo,
    RxjsIntegrationInfo,
    RxjsTypeInfo,
    RxjsDeprecationInfo,
)


@dataclass
class RxjsParseResult:
    """Complete result of parsing an RxJS file."""
    file_path: str = ""
    file_type: str = ""              # 'js', 'jsx', 'ts', 'tsx'

    # Operator constructs (from operator_extractor)
    operators: List[RxjsOperatorInfo] = field(default_factory=list)
    custom_operators: List[RxjsCustomOperatorInfo] = field(default_factory=list)
    pipes: List[RxjsPipeInfo] = field(default_factory=list)

    # Observable constructs (from observable_extractor)
    observables: List[RxjsObservableInfo] = field(default_factory=list)
    subscriptions: List[RxjsSubscriptionInfo] = field(default_factory=list)
    conversions: List[RxjsConversionInfo] = field(default_factory=list)
    subscription_mgmt: List[RxjsSubscriptionMgmtInfo] = field(default_factory=list)

    # Subject constructs (from subject_extractor)
    subjects: List[RxjsSubjectInfo] = field(default_factory=list)
    emissions: List[RxjsSubjectEmissionInfo] = field(default_factory=list)

    # Scheduler constructs (from scheduler_extractor)
    schedulers: List[RxjsSchedulerInfo] = field(default_factory=list)
    testing: List[RxjsTestingInfo] = field(default_factory=list)
    marbles: List[RxjsMarbleInfo] = field(default_factory=list)

    # API constructs (from api_extractor)
    imports: List[RxjsImportInfo] = field(default_factory=list)
    integrations: List[RxjsIntegrationInfo] = field(default_factory=list)
    types: List[RxjsTypeInfo] = field(default_factory=list)
    deprecations: List[RxjsDeprecationInfo] = field(default_factory=list)
    version_info: Dict = field(default_factory=dict)

    # Detected metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    rxjs_version: str = ""
    has_typescript: bool = False
    has_operators: bool = False
    has_subjects: bool = False
    has_observables: bool = False
    has_subscriptions: bool = False
    has_pipes: bool = False
    has_schedulers: bool = False
    has_testing: bool = False
    has_higher_order: bool = False
    has_error_handling: bool = False
    has_multicasting: bool = False
    has_deprecations: bool = False


class EnhancedRxjsParser:
    """
    Full-featured RxJS reactive programming parser.

    Coordinates 5 specialized extractors to provide comprehensive
    reactive programming analysis.
    """

    # Framework/library detection patterns
    FRAMEWORK_PATTERNS = {
        'rxjs': re.compile(r"""(?:from\s+['"]rxjs['"]|require\s*\(\s*['"]rxjs['"])"""),
        'rxjs-operators': re.compile(r"""(?:from\s+['"]rxjs/operators['"])"""),
        'rxjs-ajax': re.compile(r"""(?:from\s+['"]rxjs/ajax['"])"""),
        'rxjs-webSocket': re.compile(r"""(?:from\s+['"]rxjs/webSocket['"])"""),
        'rxjs-testing': re.compile(r"""(?:from\s+['"]rxjs/testing['"])"""),
        'rxjs-fetch': re.compile(r"""(?:from\s+['"]rxjs/fetch['"])"""),
        'rxjs-compat': re.compile(r"""(?:from\s+['"]rxjs-compat['"])"""),
        'rxjs-v5-deep': re.compile(r"""(?:from\s+['"]rxjs/(?:Observable|Subject|BehaviorSubject|Subscription)/['"])"""),
        'angular-rxjs': re.compile(r"""(?:from\s+['"]@angular[^'"]*['"].*(?:Observable|Subject|pipe|subscribe))"""),
        'ngrx': re.compile(r"""(?:from\s+['"]@ngrx/['"])"""),
        'ngxs': re.compile(r"""(?:from\s+['"]@ngxs/['"])"""),
        'redux-observable': re.compile(r"""(?:from\s+['"]redux-observable['"])"""),
        'vue-rx': re.compile(r"""(?:from\s+['"]vue-rx['"])"""),
        'nestjs-rxjs': re.compile(r"""(?:from\s+['"]@nestjs[^'"]*['"].*(?:Observable|pipe))"""),
    }

    def __init__(self):
        """Initialize all 5 extractors."""
        self.operator_extractor = RxjsOperatorExtractor()
        self.observable_extractor = RxjsObservableExtractor()
        self.subject_extractor = RxjsSubjectExtractor()
        self.scheduler_extractor = RxjsSchedulerExtractor()
        self.api_extractor = RxjsAPIExtractor()

    def parse(self, content: str, file_path: str = "") -> RxjsParseResult:
        """
        Parse a file for RxJS reactive constructs.

        Args:
            content: Source code content
            file_path: Path to the source file

        Returns:
            RxjsParseResult with all extracted data
        """
        result = RxjsParseResult()
        result.file_path = file_path

        # Detect file type
        if file_path.endswith('.tsx'):
            result.file_type = 'tsx'
            result.has_typescript = True
        elif file_path.endswith('.ts'):
            result.file_type = 'ts'
            result.has_typescript = True
        elif file_path.endswith('.jsx'):
            result.file_type = 'jsx'
        else:
            result.file_type = 'js'

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Extract operator constructs ───────────────────────────
        op_result = self.operator_extractor.extract(content, file_path)
        result.operators = op_result.get('operators', [])
        result.custom_operators = op_result.get('custom_operators', [])
        result.pipes = op_result.get('pipes', [])

        # ── Extract observable constructs ─────────────────────────
        obs_result = self.observable_extractor.extract(content, file_path)
        result.observables = obs_result.get('observables', [])
        result.subscriptions = obs_result.get('subscriptions', [])
        result.conversions = obs_result.get('conversions', [])
        result.subscription_mgmt = obs_result.get('subscription_mgmt', [])

        # ── Extract subject constructs ────────────────────────────
        sub_result = self.subject_extractor.extract(content, file_path)
        result.subjects = sub_result.get('subjects', [])
        result.emissions = sub_result.get('emissions', [])

        # ── Extract scheduler constructs ──────────────────────────
        sched_result = self.scheduler_extractor.extract(content, file_path)
        result.schedulers = sched_result.get('schedulers', [])
        result.testing = sched_result.get('testing', [])
        result.marbles = sched_result.get('marbles', [])

        # ── Extract API constructs ────────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.imports = api_result.get('imports', [])
        result.integrations = api_result.get('integrations', [])
        result.types = api_result.get('types', [])
        result.deprecations = api_result.get('deprecations', [])
        result.version_info = api_result.get('version_info', {})

        # Derive version hint
        pkg = result.version_info.get('package', 'unknown')
        if pkg == 'rxjs-v7':
            result.rxjs_version = 'v7'
        elif pkg == 'rxjs-v6' or pkg == 'rxjs-v6-compat':
            result.rxjs_version = 'v6'
        elif pkg == 'rxjs-v5':
            result.rxjs_version = 'v5'
        elif pkg == 'rxjs':
            result.rxjs_version = 'v6+'

        # Derive boolean features
        result.has_operators = bool(result.operators)
        result.has_subjects = bool(result.subjects)
        result.has_observables = bool(result.observables)
        result.has_subscriptions = bool(result.subscriptions)
        result.has_pipes = bool(result.pipes)
        result.has_schedulers = bool(result.schedulers)
        result.has_testing = bool(result.testing or result.marbles)
        result.has_higher_order = any(
            op.category == 'higher_order' for op in result.operators
        )
        result.has_error_handling = any(
            op.category == 'error' for op in result.operators
        )
        result.has_multicasting = any(
            op.category == 'multicasting' for op in result.operators
        )
        result.has_deprecations = bool(result.deprecations)

        # Build detected_features list
        if result.has_operators:
            result.detected_features.append('operators')
        if result.has_subjects:
            result.detected_features.append('subjects')
        if result.has_observables:
            result.detected_features.append('observables')
        if result.has_subscriptions:
            result.detected_features.append('subscriptions')
        if result.has_pipes:
            result.detected_features.append('pipes')
        if result.has_schedulers:
            result.detected_features.append('schedulers')
        if result.has_testing:
            result.detected_features.append('testing')
        if result.has_higher_order:
            result.detected_features.append('higher_order_mapping')
        if result.has_error_handling:
            result.detected_features.append('error_handling')
        if result.has_multicasting:
            result.detected_features.append('multicasting')
        if result.custom_operators:
            result.detected_features.append('custom_operators')
        if result.conversions:
            result.detected_features.append('promise_conversion')
        if result.subscription_mgmt:
            result.detected_features.append('subscription_management')
        if result.has_deprecations:
            result.detected_features.append('deprecated_apis')
        if result.integrations:
            result.detected_features.append('integrations')

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which RxJS ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def is_rxjs_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file contains RxJS code worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file likely contains RxJS reactive code
        """
        # Check for rxjs imports
        if re.search(r"from\s+['\"]rxjs['\"]", content):
            return True
        if re.search(r"from\s+['\"]rxjs/[^'\"]+['\"]", content):
            return True
        if re.search(r"require\s*\(\s*['\"]rxjs['\"]\s*\)", content):
            return True

        # Check for rxjs-compat
        if re.search(r"from\s+['\"]rxjs-compat['\"]", content):
            return True

        # Check for Observable usage with pipe
        if re.search(r'\.pipe\s*\(', content) and re.search(r'\b(?:map|filter|switchMap|mergeMap|tap|catchError)\s*\(', content):
            # Check it's RxJS pipe, not some other pipe
            if re.search(r"from\s+['\"]rxjs", content):
                return True

        # Check for Subject types
        if re.search(r'\bnew\s+(?:Subject|BehaviorSubject|ReplaySubject|AsyncSubject)\s*[<(]', content):
            return True

        # Check for Observable constructor
        if re.search(r'\bnew\s+Observable\s*[<(]', content):
            return True

        # Check for subscribe
        if re.search(r'\.subscribe\s*\(', content) and re.search(r"from\s+['\"]rxjs", content):
            return True

        # Check for RxJS v5 deep imports
        if re.search(r"from\s+['\"]rxjs/(?:Observable|Subject|BehaviorSubject|Subscription)/", content):
            return True

        # Check for TestScheduler
        if re.search(r'\bnew\s+TestScheduler\s*\(', content):
            return True

        # Check for marble testing
        if re.search(r'(?:hot|cold|expectObservable|expectSubscriptions)\s*\(', content) and re.search(r"rxjs", content):
            return True

        # Check for redux-observable
        if re.search(r"from\s+['\"]redux-observable['\"]", content):
            return True

        # Check for NgRx effects
        if re.search(r"from\s+['\"]@ngrx/effects['\"]", content):
            return True

        # Check for dynamic import
        if re.search(r"import\s*\(\s*['\"]rxjs", content):
            return True

        # Check for firstValueFrom/lastValueFrom
        if re.search(r'\b(?:firstValueFrom|lastValueFrom)\s*\(', content):
            return True

        return False
