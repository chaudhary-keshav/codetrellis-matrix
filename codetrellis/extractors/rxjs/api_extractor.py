"""
RxJS API Extractor — Imports, framework integrations, TypeScript types, version.

Extracts:
- ESM imports (rxjs, rxjs/operators, rxjs/ajax, rxjs/webSocket, etc.)
- CommonJS require
- Dynamic imports
- Framework integrations (Angular, NestJS, Nx, React/redux-observable, etc.)
- TypeScript types (Observable, Observer, Subscription, etc.)
- Version detection (v5 operator chaining vs v6 pipeable vs v7 tree-shakable)
- rxjs-compat usage (migration)
- Deprecated API detection

Supports RxJS v5, v6, v7.
v4.77: Full RxJS API support.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class RxjsImportInfo:
    """An RxJS import statement."""
    source: str = ""                  # Package path
    file: str = ""
    line_number: int = 0
    named_imports: List[str] = field(default_factory=list)
    default_import: str = ""
    import_type: str = ""             # 'esm', 'cjs', 'dynamic'
    is_type_import: bool = False
    subpath: str = ""                 # 'operators', 'ajax', 'webSocket', 'testing', 'fetch', etc.


@dataclass
class RxjsIntegrationInfo:
    """A framework integration with RxJS."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    integration_type: str = ""        # 'angular', 'nestjs', 'redux-observable', 'ngrx', 'ngxs', 'react', 'vue', 'nx'
    details: str = ""


@dataclass
class RxjsTypeInfo:
    """An RxJS TypeScript type reference."""
    type_name: str = ""
    file: str = ""
    line_number: int = 0
    source: str = ""


@dataclass
class RxjsDeprecationInfo:
    """A deprecated RxJS API usage."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    deprecated_in: str = ""           # 'v6', 'v7'
    replacement: str = ""


# Framework integration patterns
FRAMEWORK_INTEGRATIONS = {
    'angular': re.compile(
        r"(?:from\s+['\"]@angular|HttpClient|@Injectable|@Component|@Pipe)"
    ),
    'nestjs': re.compile(
        r"(?:from\s+['\"]@nestjs|@Injectable|@Controller|@Module)"
    ),
    'ngrx': re.compile(
        r"(?:from\s+['\"]@ngrx|createEffect|createAction|createReducer|Store\b)"
    ),
    'ngxs': re.compile(
        r"(?:from\s+['\"]@ngxs|@State|@Action|@Selector)"
    ),
    'redux-observable': re.compile(
        r"(?:from\s+['\"]redux-observable|ofType|createEpicMiddleware)"
    ),
    'nx': re.compile(
        r"(?:from\s+['\"]@nrwl|@nx/)"
    ),
    'vue-rx': re.compile(
        r"(?:from\s+['\"]vue-rx|useObservable)"
    ),
}

# Known RxJS TypeScript types
RXJS_TYPES = [
    'Observable', 'Observer', 'Subscription', 'Subject', 'BehaviorSubject',
    'ReplaySubject', 'AsyncSubject', 'Subscriber', 'Operator',
    'OperatorFunction', 'MonoTypeOperatorFunction', 'UnaryFunction',
    'SchedulerLike', 'SchedulerAction', 'ObservableInput', 'ObservedValueOf',
    'Notification', 'NextNotification', 'ErrorNotification', 'CompleteNotification',
    'TeardownLogic', 'Unsubscribable', 'SubjectLike',
    'InteropObservable', 'GroupedObservable', 'ConnectableObservable',
]

# Deprecated APIs
DEPRECATED_V6 = {
    'Observable.create': 'new Observable()',
    'ErrorObservable': 'throwError()',
    'EmptyObservable': 'EMPTY',
    'NeverObservable': 'NEVER',
    'ArrayObservable': 'from([])',
    'ForkJoinObservable': 'forkJoin()',
}

DEPRECATED_V7 = {
    'toPromise': 'firstValueFrom/lastValueFrom',
    'pluck': 'map',
    'multicast': 'connectable/share',
    'publish': 'connectable/share',
    'publishReplay': 'shareReplay',
    'publishBehavior': 'connectable',
    'publishLast': 'connectable',
    'refCount': 'share',
}


class RxjsAPIExtractor:
    """
    Extracts RxJS API patterns: imports, integrations, types, version.
    """

    # ESM import
    ESM_IMPORT = re.compile(
        r"import\s+(?:(?:type\s+)?\{([^}]*)\}|(\w+))\s+from\s+['\"]([^'\"]*rxjs[^'\"]*)['\"]",
        re.MULTILINE
    )

    # CommonJS require
    CJS_REQUIRE = re.compile(
        r"(?:const|let|var)\s+(?:\{([^}]*)\}|(\w+))\s*=\s*require\s*\(\s*['\"]([^'\"]*rxjs[^'\"]*)['\"]",
        re.MULTILINE
    )

    # Dynamic import
    DYNAMIC_IMPORT = re.compile(
        r"import\s*\(\s*['\"]([^'\"]*rxjs[^'\"]*)['\"]",
    )

    # TypeScript type import
    TYPE_IMPORT = re.compile(
        r'import\s+type\s+\{([^}]*)\}\s+from\s+["\']([^"\']*rxjs[^"\']*)["\']',
        re.MULTILINE
    )

    # rxjs-compat (migration)
    COMPAT_IMPORT = re.compile(
        r"from\s+['\"]rxjs-compat['\"]",
    )

    # v5 deep imports
    V5_DEEP_IMPORT = re.compile(
        r"from\s+['\"]rxjs/(?:Observable|Subject|BehaviorSubject|ReplaySubject|Subscription|operator)/",
    )

    # Subpath detection
    SUBPATH_PATTERN = re.compile(
        r"from\s+['\"]rxjs/(\w+)['\"]",
    )

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract all RxJS API constructs."""
        imports = []
        integrations = []
        types = []
        deprecations = []
        version_info = {}

        # ── ESM imports ─────────────────────────────────────────
        for match in self.ESM_IMPORT.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            named = match.group(1)
            default = match.group(2)
            source = match.group(3)

            named_list = [n.strip().split(' as ')[0].strip()
                          for n in (named or '').split(',') if n.strip()]

            is_type = 'import type' in content[max(0, match.start()-20):match.start()+20]

            # Determine subpath
            subpath = ''
            sp = self.SUBPATH_PATTERN.search(source)
            if sp:
                subpath = sp.group(1)

            imports.append(RxjsImportInfo(
                source=source,
                file=file_path,
                line_number=line_num,
                named_imports=named_list,
                default_import=default or '',
                import_type='esm',
                is_type_import=is_type,
                subpath=subpath,
            ))

        # ── CJS require ─────────────────────────────────────────
        for match in self.CJS_REQUIRE.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            named = match.group(1)
            default = match.group(2)
            source = match.group(3)

            named_list = [n.strip() for n in (named or '').split(',') if n.strip()]

            imports.append(RxjsImportInfo(
                source=source,
                file=file_path,
                line_number=line_num,
                named_imports=named_list,
                default_import=default or '',
                import_type='cjs',
            ))

        # ── Dynamic imports ─────────────────────────────────────
        for match in self.DYNAMIC_IMPORT.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            imports.append(RxjsImportInfo(
                source=match.group(1),
                file=file_path,
                line_number=line_num,
                import_type='dynamic',
            ))

        # ── Type imports ────────────────────────────────────────
        for match in self.TYPE_IMPORT.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            names = [n.strip() for n in match.group(1).split(',') if n.strip()]
            source = match.group(2)
            for name in names:
                types.append(RxjsTypeInfo(
                    type_name=name,
                    file=file_path,
                    line_number=line_num,
                    source=source,
                ))

        # ── Framework integrations ──────────────────────────────
        for fw_name, pattern in FRAMEWORK_INTEGRATIONS.items():
            if pattern.search(content):
                m = pattern.search(content)
                line_num = content[:m.start()].count('\n') + 1
                integrations.append(RxjsIntegrationInfo(
                    name=fw_name,
                    file=file_path,
                    line_number=line_num,
                    integration_type=fw_name,
                ))

        # ── Version detection ───────────────────────────────────
        # rxjs-compat → v6 migration
        if self.COMPAT_IMPORT.search(content):
            version_info['compat'] = True
            version_info['package'] = 'rxjs-v6-compat'

        # v5 deep imports
        if self.V5_DEEP_IMPORT.search(content):
            version_info['package'] = 'rxjs-v5'

        # v6 pipeable (from 'rxjs/operators')
        if re.search(r"from\s+['\"]rxjs/operators['\"]", content):
            version_info.setdefault('package', 'rxjs-v6')

        # v7 tree-shakable (operators imported from 'rxjs' directly)
        has_rxjs_import = re.search(r"from\s+['\"]rxjs['\"]", content)
        has_pipe_operators = re.search(r"\bpipe\s*\(\s*(?:map|filter|switchMap|mergeMap|catchError|tap)\s*\(", content)
        if has_rxjs_import and has_pipe_operators and not re.search(r"from\s+['\"]rxjs/operators['\"]", content):
            version_info['package'] = 'rxjs-v7'

        # firstValueFrom/lastValueFrom → v7+
        if re.search(r'\b(?:firstValueFrom|lastValueFrom)\s*\(', content):
            version_info['package'] = 'rxjs-v7'

        # Default
        if not version_info.get('package') and has_rxjs_import:
            version_info['package'] = 'rxjs'

        # ── Deprecation detection ───────────────────────────────
        for deprecated, replacement in DEPRECATED_V7.items():
            pattern = re.compile(r'\b' + re.escape(deprecated) + r'\s*[\(.]')
            m = pattern.search(content)
            if m:
                line_num = content[:m.start()].count('\n') + 1
                deprecations.append(RxjsDeprecationInfo(
                    name=deprecated,
                    file=file_path,
                    line_number=line_num,
                    deprecated_in='v7',
                    replacement=replacement,
                ))

        return {
            'imports': imports[:50],
            'integrations': integrations[:20],
            'types': types[:30],
            'deprecations': deprecations[:20],
            'version_info': version_info,
        }
