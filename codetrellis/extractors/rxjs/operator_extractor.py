"""
RxJS Operator Extractor — Pipeable, creation, transformation, filtering operators.

Extracts:
- Pipeable operators (map, filter, switchMap, mergeMap, concatMap, exhaustMap, etc.)
- Creation operators (of, from, interval, timer, fromEvent, ajax, etc.)
- Combination operators (combineLatest, merge, concat, forkJoin, race, zip, etc.)
- Transformation operators (map, scan, reduce, buffer, window, groupBy, etc.)
- Filtering operators (filter, take, skip, debounceTime, throttleTime, distinctUntilChanged, etc.)
- Error handling operators (catchError, retry, retryWhen, throwError, etc.)
- Utility operators (tap, delay, timeout, toArray, finalize, etc.)
- Higher-order mapping (switchMap, mergeMap, concatMap, exhaustMap)
- Custom operators (pipe-based)

Supports RxJS v5 (operator chaining), v6 (pipeable), v7 (tree-shakable).
v4.77: Full RxJS operator support.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class RxjsOperatorInfo:
    """An RxJS operator usage."""
    name: str = ""                    # Operator name
    file: str = ""
    line_number: int = 0
    category: str = ""                # 'creation', 'transformation', 'filtering', 'combination', 'error', 'utility', 'multicasting', 'higher_order'
    is_pipeable: bool = True          # v6+ pipeable
    is_legacy_chain: bool = False     # v5 .operator() chaining


@dataclass
class RxjsCustomOperatorInfo:
    """A custom RxJS operator definition."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    return_type: str = ""
    uses_pipe: bool = False


@dataclass
class RxjsPipeInfo:
    """A pipe() chain."""
    file: str = ""
    line_number: int = 0
    operator_count: int = 0
    operators: List[str] = field(default_factory=list)


# Operator classification
CREATION_OPERATORS = {
    'of', 'from', 'interval', 'timer', 'range', 'defer', 'empty', 'never',
    'throwError', 'fromEvent', 'fromEventPattern', 'fromPromise',
    'ajax', 'generate', 'iif', 'using', 'EMPTY', 'NEVER',
    'animationFrameScheduler', 'asapScheduler', 'asyncScheduler', 'queueScheduler',
    'scheduled', 'connectable',
}

TRANSFORMATION_OPERATORS = {
    'map', 'scan', 'reduce', 'pluck', 'mapTo', 'switchMap', 'mergeMap',
    'concatMap', 'exhaustMap', 'expand', 'buffer', 'bufferCount', 'bufferTime',
    'bufferWhen', 'bufferToggle', 'window', 'windowCount', 'windowTime',
    'windowWhen', 'windowToggle', 'groupBy', 'pairwise', 'partition',
    'switchScan', 'mergeScan', 'concatMapTo', 'mergeMapTo', 'switchMapTo',
}

FILTERING_OPERATORS = {
    'filter', 'take', 'takeUntil', 'takeWhile', 'takeLast', 'skip',
    'skipUntil', 'skipWhile', 'skipLast', 'first', 'last', 'single',
    'debounce', 'debounceTime', 'throttle', 'throttleTime', 'auditTime',
    'audit', 'sample', 'sampleTime', 'distinct', 'distinctUntilChanged',
    'distinctUntilKeyChanged', 'elementAt', 'ignoreElements',
}

COMBINATION_OPERATORS = {
    'combineLatest', 'combineLatestWith', 'merge', 'mergeWith',
    'concat', 'concatWith', 'forkJoin', 'race', 'raceWith', 'zip',
    'zipWith', 'startWith', 'endWith', 'withLatestFrom', 'combineAll',
    'concatAll', 'mergeAll', 'switchAll', 'exhaustAll',
}

ERROR_OPERATORS = {
    'catchError', 'retry', 'retryWhen', 'throwIfEmpty', 'onErrorResumeNext',
    'throwError',
}

MULTICASTING_OPERATORS = {
    'share', 'shareReplay', 'publish', 'publishReplay', 'publishLast',
    'publishBehavior', 'refCount', 'multicast', 'connect',
}

UTILITY_OPERATORS = {
    'tap', 'delay', 'delayWhen', 'timeout', 'timeoutWith', 'toArray',
    'finalize', 'repeat', 'repeatWhen', 'defaultIfEmpty', 'every',
    'count', 'min', 'max', 'isEmpty', 'materialize', 'dematerialize',
    'observeOn', 'subscribeOn', 'timeInterval', 'timestamp',
}

HIGHER_ORDER_OPERATORS = {
    'switchMap', 'mergeMap', 'concatMap', 'exhaustMap',
    'switchScan', 'mergeScan', 'switchMapTo', 'mergeMapTo', 'concatMapTo',
}


def _classify_operator(name: str) -> str:
    """Classify an operator into its category."""
    if name in HIGHER_ORDER_OPERATORS:
        return 'higher_order'
    if name in CREATION_OPERATORS:
        return 'creation'
    if name in TRANSFORMATION_OPERATORS:
        return 'transformation'
    if name in FILTERING_OPERATORS:
        return 'filtering'
    if name in COMBINATION_OPERATORS:
        return 'combination'
    if name in ERROR_OPERATORS:
        return 'error'
    if name in MULTICASTING_OPERATORS:
        return 'multicasting'
    if name in UTILITY_OPERATORS:
        return 'utility'
    return 'other'


ALL_KNOWN_OPERATORS = (
    CREATION_OPERATORS | TRANSFORMATION_OPERATORS | FILTERING_OPERATORS |
    COMBINATION_OPERATORS | ERROR_OPERATORS | MULTICASTING_OPERATORS |
    UTILITY_OPERATORS | HIGHER_ORDER_OPERATORS
)


class RxjsOperatorExtractor:
    """
    Extracts RxJS operator patterns from source code.
    """

    # Import pattern to identify operators
    OPERATOR_IMPORT = re.compile(
        r"import\s+\{([^}]*)\}\s+from\s+['\"]rxjs(?:/operators)?['\"]",
        re.MULTILINE
    )

    # Pipe usage
    PIPE_PATTERN = re.compile(
        r'\.pipe\s*\(',
        re.MULTILINE
    )

    # Operator usage inside pipe
    OPERATOR_IN_PIPE = re.compile(
        r'\b(' + '|'.join(sorted(ALL_KNOWN_OPERATORS, key=len, reverse=True)) + r')\s*\(',
    )

    # Legacy v5 chaining
    LEGACY_CHAIN = re.compile(
        r'\.\s*(' + '|'.join(sorted(ALL_KNOWN_OPERATORS, key=len, reverse=True)) + r')\s*\(',
    )

    # Custom operator definition
    CUSTOM_OPERATOR = re.compile(
        r'(?:export\s+)?(?:function|const|let|var)\s+(\w+)\s*[=:]\s*(?:\([^)]*\)\s*(?:=>|:).*?)?(?:pipe|OperatorFunction|MonoTypeOperatorFunction)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract all RxJS operator constructs."""
        operators = []
        custom_operators = []
        pipes = []
        seen_ops = set()

        # ── Imported operators ──────────────────────────────────
        imported_ops = set()
        for match in self.OPERATOR_IMPORT.finditer(content):
            names = [n.strip().split(' as ')[0].strip()
                     for n in match.group(1).split(',') if n.strip()]
            imported_ops.update(names)

        # ── Operator usage inside pipe() ─────────────────────────
        for match in self.PIPE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            # Get the content inside this pipe()
            depth = 1
            start = match.end()
            idx = start
            while idx < len(content) and depth > 0:
                if content[idx] == '(':
                    depth += 1
                elif content[idx] == ')':
                    depth -= 1
                idx += 1
            pipe_content = content[start:idx-1] if idx > start else ""

            pipe_ops = []
            for op_match in self.OPERATOR_IN_PIPE.finditer(pipe_content):
                op_name = op_match.group(1)
                if op_name in ALL_KNOWN_OPERATORS:
                    pipe_ops.append(op_name)
                    op_key = f"{op_name}:{file_path}"
                    if op_key not in seen_ops:
                        seen_ops.add(op_key)
                        op_line = content[:match.start() + op_match.start()].count('\n') + 1
                        operators.append(RxjsOperatorInfo(
                            name=op_name,
                            file=file_path,
                            line_number=op_line,
                            category=_classify_operator(op_name),
                            is_pipeable=True,
                        ))

            if pipe_ops:
                pipes.append(RxjsPipeInfo(
                    file=file_path,
                    line_number=line_num,
                    operator_count=len(pipe_ops),
                    operators=pipe_ops[:20],
                ))

        # ── Creation operators at top level ──────────────────────
        for op_name in CREATION_OPERATORS:
            if op_name in imported_ops:
                pattern = re.compile(r'\b' + re.escape(op_name) + r'\s*\(')
                for m in pattern.finditer(content):
                    line_num = content[:m.start()].count('\n') + 1
                    key = f"{op_name}:{file_path}:creation"
                    if key not in seen_ops:
                        seen_ops.add(key)
                        operators.append(RxjsOperatorInfo(
                            name=op_name,
                            file=file_path,
                            line_number=line_num,
                            category='creation',
                            is_pipeable=False,
                        ))
                    break  # Only record once per file

        # ── Legacy v5 chaining ──────────────────────────────────
        # Check for .map(), .filter(), etc. without pipe()
        if not self.PIPE_PATTERN.search(content):
            for match in self.LEGACY_CHAIN.finditer(content):
                op_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                key = f"{op_name}:{file_path}:legacy"
                if key not in seen_ops:
                    seen_ops.add(key)
                    operators.append(RxjsOperatorInfo(
                        name=op_name,
                        file=file_path,
                        line_number=line_num,
                        category=_classify_operator(op_name),
                        is_pipeable=False,
                        is_legacy_chain=True,
                    ))

        # ── Custom operators ─────────────────────────────────────
        for match in self.CUSTOM_OPERATOR.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            custom_operators.append(RxjsCustomOperatorInfo(
                name=match.group(1),
                file=file_path,
                line_number=line_num,
                uses_pipe='pipe' in content[match.start():match.start()+200],
            ))

        return {
            'operators': operators[:100],
            'custom_operators': custom_operators[:20],
            'pipes': pipes[:50],
        }
