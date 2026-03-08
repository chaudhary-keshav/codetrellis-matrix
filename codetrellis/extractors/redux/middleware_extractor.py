"""
Redux Middleware Extractor for CodeTrellis

Extracts Redux middleware patterns across all paradigms:
- createAsyncThunk (RTK) with lifecycle states (pending/fulfilled/rejected)
- createListenerMiddleware (RTK 1.8+) with effect, condition, startListening
- redux-saga generator effects (takeEvery, takeLatest, takeLeading, call, put,
    select, fork, spawn, all, race, delay, throttle, debounce)
- redux-observable Epics (ofType, mergeMap, switchMap, exhaustMap, catchError,
    pipe operators)
- Custom middleware (store => next => action pattern)
- redux-thunk (function-returning action creators)
- RTK matcher utilities (isAllOf, isAnyOf, isRejected, isPending, isFulfilled,
    isRejectedWithValue, isAsyncThunkAction)

Supports:
- Redux Toolkit 1.0+ (createAsyncThunk)
- Redux Toolkit 1.8+ (createListenerMiddleware)
- Redux Toolkit 2.0+ (autoBatchEnhancer, Tuple)
- redux-saga 0.x-1.x
- redux-observable 1.x-2.x
- Custom middleware patterns

Part of CodeTrellis v4.47 - Redux / Redux Toolkit Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ReduxAsyncThunkInfo:
    """Information about a createAsyncThunk definition."""
    name: str
    file: str = ""
    line_number: int = 0
    type_prefix: str = ""  # Action type prefix string
    return_type: str = ""  # TypeScript return type
    arg_type: str = ""  # TypeScript argument type
    has_condition: bool = False  # condition option
    has_dispatch_access: bool = False  # Uses thunkAPI.dispatch
    has_get_state: bool = False  # Uses thunkAPI.getState
    has_reject_with_value: bool = False  # Uses rejectWithValue
    has_extra: bool = False  # Uses thunkAPI.extra
    is_exported: bool = False
    api_endpoint: str = ""  # Detected API call endpoint


@dataclass
class ReduxSagaInfo:
    """Information about a redux-saga generator function."""
    name: str
    file: str = ""
    line_number: int = 0
    saga_type: str = ""  # watcher, worker, root
    effects_used: List[str] = field(default_factory=list)
    watched_action: str = ""  # Action type being watched
    watch_mode: str = ""  # takeEvery, takeLatest, takeLeading, throttle, debounce
    calls: List[str] = field(default_factory=list)  # API calls (call(fn))
    puts: List[str] = field(default_factory=list)  # Dispatched actions (put(action))
    selects: List[str] = field(default_factory=list)  # State selectors (select(fn))
    is_exported: bool = False


@dataclass
class ReduxObservableInfo:
    """Information about a redux-observable Epic."""
    name: str
    file: str = ""
    line_number: int = 0
    action_types: List[str] = field(default_factory=list)
    operators: List[str] = field(default_factory=list)  # RxJS operators used
    has_error_handling: bool = False  # catchError usage
    has_state_access: bool = False  # state$ parameter used
    is_exported: bool = False


@dataclass
class ReduxListenerInfo:
    """Information about a RTK listener middleware."""
    name: str
    file: str = ""
    line_number: int = 0
    action_creator: str = ""  # Watched action creator
    matcher: str = ""  # isAnyOf/isAllOf matcher
    has_condition: bool = False
    has_cancel: bool = False
    effect_type: str = ""  # effect, effectFn
    is_exported: bool = False


@dataclass
class ReduxCustomMiddlewareInfo:
    """Information about a custom Redux middleware."""
    name: str
    file: str = ""
    line_number: int = 0
    pattern: str = ""  # curried, function, arrow
    has_next_call: bool = True
    dispatches_actions: bool = False
    accesses_state: bool = False
    is_exported: bool = False


class ReduxMiddlewareExtractor:
    """
    Extracts Redux middleware patterns from source code.

    Detects:
    - createAsyncThunk with lifecycle analysis
    - createListenerMiddleware with effect patterns
    - redux-saga generators with effect extraction
    - redux-observable epics with operator detection
    - Custom middleware patterns
    """

    # createAsyncThunk
    ASYNC_THUNK_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createAsyncThunk\s*(?:<([^>]*)>)?\s*\(\s*'
        r'[\'"]([^\'"]+)[\'"]',
        re.MULTILINE
    )

    # createListenerMiddleware
    LISTENER_MW_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createListenerMiddleware\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # startListening (on listener middleware)
    START_LISTENING_PATTERN = re.compile(
        r'(\w+)\.startListening\s*\(\s*\{',
        re.MULTILINE
    )

    # addListener (dispatch-based)
    ADD_LISTENER_PATTERN = re.compile(
        r'addListener\s*\(\s*\{',
        re.MULTILINE
    )

    # redux-saga root/watcher/worker detection
    SAGA_FUNCTION_PATTERN = re.compile(
        r'(?:export\s+)?function\s*\*\s*(\w+)\s*\(',
        re.MULTILINE
    )

    # saga watcher effects
    SAGA_WATCHER_PATTERN = re.compile(
        r'(takeEvery|takeLatest|takeLeading|throttle|debounce)\s*\(\s*'
        r'(?:[\'"]([^\'"]+)[\'"]|(\w+(?:\.\w+)?))',
        re.MULTILINE
    )

    # saga call effect
    SAGA_CALL_PATTERN = re.compile(
        r'(?:yield\s+)?call\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # saga put effect
    SAGA_PUT_PATTERN = re.compile(
        r'(?:yield\s+)?put\s*\(\s*(\w+(?:\.\w+)?)\s*\(',
        re.MULTILINE
    )

    # saga select effect
    SAGA_SELECT_PATTERN = re.compile(
        r'(?:yield\s+)?select\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # redux-observable Epic
    EPIC_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+(?:Epic)?)\s*'
        r'(?::\s*Epic\s*(?:<[^>]*>)?\s*)?=\s*'
        r'(?:\([^)]*action\$[^)]*\)\s*(?::\s*\w+)?\s*=>|'
        r'combineEpics\s*\()',
        re.MULTILINE
    )

    # ofType (redux-observable)
    OF_TYPE_PATTERN = re.compile(
        r'ofType\s*\(\s*(?:[\'"]([^\'"]+)[\'"]|(\w+(?:\.\w+)?))',
        re.MULTILINE
    )

    # Custom middleware: (store|storeAPI) => (next) => (action) => ...
    CUSTOM_MW_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*'
        r'(?::\s*Middleware\s*(?:<[^>]*>)?\s*)?=\s*'
        r'(?:\(\s*(?:store|storeAPI|api)\s*\)\s*=>\s*\(\s*next\s*\)\s*=>\s*\(\s*action\s*\)\s*=>|'
        r'function\s*\(\s*(?:store|storeAPI|api)\s*\)\s*\{\s*return\s+function)',
        re.MULTILINE
    )

    # RTK matcher utilities
    MATCHER_PATTERN = re.compile(
        r'(isAllOf|isAnyOf|isRejected|isPending|isFulfilled|'
        r'isRejectedWithValue|isAsyncThunkAction|isFulfilled)\s*\(',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Redux middleware patterns from source code."""
        async_thunks = []
        sagas = []
        epics = []
        listeners = []
        custom_middleware = []

        # ── createAsyncThunk ──────────────────────────────────────
        for m in self.ASYNC_THUNK_PATTERN.finditer(content):
            name = m.group(1)
            type_params = m.group(2) or ""
            type_prefix = m.group(3)
            line = content[:m.start()].count('\n') + 1

            # Parse type parameters
            return_type = ""
            arg_type = ""
            if type_params:
                parts = [p.strip() for p in type_params.split(',')]
                if len(parts) >= 1:
                    return_type = parts[0]
                if len(parts) >= 2:
                    arg_type = parts[1]

            # Analyze thunk body
            after = content[m.end():m.end() + 3000]
            body = self._extract_thunk_body(after)

            has_condition = bool(re.search(r'condition\s*:', after[:500]))
            has_dispatch = 'dispatch' in body or 'thunkAPI.dispatch' in body
            has_get_state = 'getState' in body or 'thunkAPI.getState' in body
            has_reject = 'rejectWithValue' in body
            has_extra = 'extra' in body and 'thunkAPI.extra' in body

            # Detect API endpoint
            api_endpoint = ""
            api_match = re.search(r'(?:fetch|axios|api)\s*(?:\.|\.get|\.post|\.put|\.delete|\.patch)?\s*\(\s*[\'"`]([^\'"` ]+)', body)
            if api_match:
                api_endpoint = api_match.group(1)

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            async_thunks.append(ReduxAsyncThunkInfo(
                name=name,
                file=file_path,
                line_number=line,
                type_prefix=type_prefix,
                return_type=return_type,
                arg_type=arg_type,
                has_condition=has_condition,
                has_dispatch_access=has_dispatch,
                has_get_state=has_get_state,
                has_reject_with_value=has_reject,
                has_extra=has_extra,
                is_exported=is_exported,
                api_endpoint=api_endpoint[:200],
            ))

        # ── createListenerMiddleware ──────────────────────────────
        listener_mw_names = set()
        for m in self.LISTENER_MW_PATTERN.finditer(content):
            listener_mw_names.add(m.group(1))

        for m in self.START_LISTENING_PATTERN.finditer(content):
            mw_name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            body_start = m.end() - 1
            body = self._extract_balanced_braces(content[body_start:])

            # Extract action creator
            action_match = re.search(r'actionCreator\s*:\s*(\w+(?:\.\w+)?)', body)
            action_creator = action_match.group(1) if action_match else ""

            # Extract matcher
            matcher_match = re.search(r'matcher\s*:\s*(is(?:AnyOf|AllOf)\s*\([^)]+\)|\w+)', body)
            matcher = matcher_match.group(1) if matcher_match else ""

            # Extract type
            type_match = re.search(r'type\s*:\s*[\'"]([^\'"]+)[\'"]', body)
            if type_match and not action_creator:
                action_creator = type_match.group(1)

            has_condition = bool(re.search(r'condition\s*:', body))
            has_cancel = 'cancelActiveListeners' in body or 'cancel' in body

            listeners.append(ReduxListenerInfo(
                name=f"{mw_name}.startListening",
                file=file_path,
                line_number=line,
                action_creator=action_creator,
                matcher=matcher[:100],
                has_condition=has_condition,
                has_cancel=has_cancel,
                effect_type="effect",
            ))

        # ── redux-saga ────────────────────────────────────────────
        saga_imports = bool(re.search(
            r"from\s+['\"]redux-saga|require\(['\"]redux-saga",
            content
        ))
        saga_effects_import = bool(re.search(
            r"from\s+['\"]redux-saga/effects['\"]",
            content
        ))

        if saga_imports or saga_effects_import:
            for m in self.SAGA_FUNCTION_PATTERN.finditer(content):
                name = m.group(1)
                line = content[:m.start()].count('\n') + 1
                body_end = self._find_function_end(content, m.end())
                body = content[m.end():body_end]

                # Determine saga type
                saga_type = "worker"
                watcher_effects = self.SAGA_WATCHER_PATTERN.findall(body)
                if watcher_effects:
                    saga_type = "watcher"
                elif 'all' in body and 'fork' in body:
                    saga_type = "root"

                # Extract effects used
                all_effects = ['takeEvery', 'takeLatest', 'takeLeading', 'call', 'put',
                               'select', 'fork', 'spawn', 'all', 'race', 'delay',
                               'throttle', 'debounce', 'cancel', 'cancelled', 'retry']
                effects_used = [eff for eff in all_effects if eff in body]

                # Extract watched actions
                watched_action = ""
                watch_mode = ""
                if watcher_effects:
                    watch_mode = watcher_effects[0][0]
                    watched_action = watcher_effects[0][1] or watcher_effects[0][2]

                # Extract calls
                calls = [c.group(1) for c in self.SAGA_CALL_PATTERN.finditer(body)]

                # Extract puts
                puts = [p.group(1) for p in self.SAGA_PUT_PATTERN.finditer(body)]

                # Extract selects
                selects = [s.group(1) for s in self.SAGA_SELECT_PATTERN.finditer(body)]

                is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

                sagas.append(ReduxSagaInfo(
                    name=name,
                    file=file_path,
                    line_number=line,
                    saga_type=saga_type,
                    effects_used=effects_used[:15],
                    watched_action=watched_action,
                    watch_mode=watch_mode,
                    calls=calls[:15],
                    puts=puts[:15],
                    selects=selects[:10],
                    is_exported=is_exported,
                ))

        # ── redux-observable Epics ────────────────────────────────
        observable_imports = bool(re.search(
            r"from\s+['\"]redux-observable|require\(['\"]redux-observable",
            content
        ))

        if observable_imports:
            for m in self.EPIC_PATTERN.finditer(content):
                name = m.group(1)
                line = content[:m.start()].count('\n') + 1
                after = content[m.end():m.end() + 3000]

                # Extract action types from ofType
                action_types = [t[0] or t[1] for t in self.OF_TYPE_PATTERN.findall(after)]

                # Extract RxJS operators
                rxjs_ops = ['mergeMap', 'switchMap', 'exhaustMap', 'concatMap', 'map',
                            'filter', 'tap', 'catchError', 'debounceTime', 'throttleTime',
                            'distinctUntilChanged', 'takeUntil', 'retry', 'timeout',
                            'withLatestFrom', 'combineLatest']
                operators = [op for op in rxjs_ops if op in after]

                has_error = 'catchError' in after
                has_state = 'state$' in after

                is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

                epics.append(ReduxObservableInfo(
                    name=name,
                    file=file_path,
                    line_number=line,
                    action_types=action_types[:10],
                    operators=operators[:10],
                    has_error_handling=has_error,
                    has_state_access=has_state,
                    is_exported=is_exported,
                ))

        # ── Custom middleware ─────────────────────────────────────
        for m in self.CUSTOM_MW_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            after = content[m.end():m.end() + 2000]

            dispatches = 'dispatch' in after[:500] or 'store.dispatch' in after[:500]
            accesses_state = 'getState' in after[:500] or 'store.getState' in after[:500]

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            custom_middleware.append(ReduxCustomMiddlewareInfo(
                name=name,
                file=file_path,
                line_number=line,
                pattern="arrow",
                has_next_call=True,
                dispatches_actions=dispatches,
                accesses_state=accesses_state,
                is_exported=is_exported,
            ))

        return {
            'async_thunks': async_thunks,
            'sagas': sagas,
            'epics': epics,
            'listeners': listeners,
            'custom_middleware': custom_middleware,
        }

    def _extract_balanced_braces(self, text: str, max_len: int = 5000) -> str:
        """Extract content within balanced braces."""
        depth = 0
        start = None
        for i, ch in enumerate(text[:max_len]):
            if ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and start is not None:
                    return text[start:i + 1]
        return text[:max_len] if start is None else text[start:max_len]

    def _extract_thunk_body(self, text: str) -> str:
        """Extract the async function body from a thunk."""
        # Find first { or arrow
        depth = 0
        for i, ch in enumerate(text[:5000]):
            if ch in '({':
                depth += 1
            elif ch in ')}':
                depth -= 1
                if depth <= 0:
                    return text[:i + 1]
        return text[:2000]

    def _find_function_end(self, content: str, start: int) -> int:
        """Find the end of a generator function body."""
        depth = 0
        in_body = False
        for i in range(start, min(start + 10000, len(content))):
            ch = content[i]
            if ch == '{':
                depth += 1
                in_body = True
            elif ch == '}':
                depth -= 1
                if depth == 0 and in_body:
                    return i + 1
        return min(start + 5000, len(content))
