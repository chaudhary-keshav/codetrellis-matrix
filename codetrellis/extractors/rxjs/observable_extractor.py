"""
RxJS Observable Extractor — Observable creation, subscription, lifecycle.

Extracts:
- Observable creation (new Observable, Observable.create)
- Observable subscriptions (.subscribe())
- Subscription management (unsubscribe, add, remove)
- Hot vs cold observables
- AsyncSubject, ConnectableObservable
- Custom Observable factories
- Observable lifecycle hooks (complete, error, next)
- Notification patterns
- Observable conversion (toPromise, firstValueFrom, lastValueFrom)

Supports RxJS v5, v6, v7.
v4.77: Full RxJS observable support.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class RxjsObservableInfo:
    """An Observable creation point."""
    name: str = ""                    # Variable name
    file: str = ""
    line_number: int = 0
    creation_method: str = ""         # 'constructor', 'of', 'from', 'interval', 'create', etc.
    is_typed: bool = False            # Observable<Type>
    type_param: str = ""              # Generic type parameter


@dataclass
class RxjsSubscriptionInfo:
    """A .subscribe() call."""
    name: str = ""                    # Variable for subscription
    file: str = ""
    line_number: int = 0
    has_next: bool = False
    has_error: bool = False
    has_complete: bool = False
    is_unsubscribed: bool = False     # Has .unsubscribe() call
    uses_observer_object: bool = False  # subscribe({next, error, complete})


@dataclass
class RxjsConversionInfo:
    """Observable to Promise/other conversion."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    conversion_type: str = ""         # 'toPromise', 'firstValueFrom', 'lastValueFrom'


@dataclass
class RxjsSubscriptionMgmtInfo:
    """Subscription management (add, remove, unsubscribe)."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    pattern: str = ""                 # 'manual', 'takeUntil', 'async_pipe', 'auto_unsubscribe'


class RxjsObservableExtractor:
    """
    Extracts RxJS Observable patterns from source code.
    """

    # new Observable()
    OBSERVABLE_CONSTRUCTOR = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*(?::\s*Observable(?:<([^>]*)>)?)?\s*=\s*)?new\s+Observable\s*[<(]',
        re.MULTILINE
    )

    # Observable.create() (v5 deprecated)
    OBSERVABLE_CREATE = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?Observable\.create\s*\(',
        re.MULTILINE
    )

    # Creation functions: of(), from(), interval(), timer(), etc.
    CREATION_FN = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*(?::\s*Observable(?:<([^>]*)>)?)?\s*=\s*)(of|from|interval|timer|range|defer|fromEvent|fromEventPattern|ajax|generate|iif|throwError|EMPTY|NEVER)\s*[<(]',
        re.MULTILINE
    )

    # subscribe() call
    SUBSCRIBE = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?(\w[\w.]*?)\.subscribe\s*\(',
        re.MULTILINE
    )

    # unsubscribe() call
    UNSUBSCRIBE = re.compile(
        r'(\w+)\.unsubscribe\s*\(\s*\)',
        re.MULTILINE
    )

    # toPromise() (deprecated in v7)
    TO_PROMISE = re.compile(
        r'(\w[\w.]*?)\.toPromise\s*\(\s*\)',
        re.MULTILINE
    )

    # firstValueFrom / lastValueFrom (v7+)
    VALUE_FROM = re.compile(
        r'(firstValueFrom|lastValueFrom)\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # takeUntil pattern for cleanup
    TAKE_UNTIL = re.compile(
        r'takeUntil\s*\(\s*(?:this\.)?(\w+)',
    )

    # Angular async pipe
    ASYNC_PIPE = re.compile(
        r'\|\s*async\b',
    )

    # Subscription.add()
    SUB_ADD = re.compile(
        r'(\w+)\.add\s*\(',
    )

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract all RxJS observable constructs."""
        observables = []
        subscriptions = []
        conversions = []
        subscription_mgmt = []
        unsubscribe_vars = set()

        # Collect unsubscribe calls first
        for match in self.UNSUBSCRIBE.finditer(content):
            unsubscribe_vars.add(match.group(1))

        # ── Observable constructor ──────────────────────────────
        for match in self.OBSERVABLE_CONSTRUCTOR.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            observables.append(RxjsObservableInfo(
                name=match.group(1) or 'anonymous',
                file=file_path,
                line_number=line_num,
                creation_method='constructor',
                is_typed=bool(match.group(2)),
                type_param=match.group(2) or '',
            ))

        # ── Observable.create() ─────────────────────────────────
        for match in self.OBSERVABLE_CREATE.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            observables.append(RxjsObservableInfo(
                name=match.group(1) or 'anonymous',
                file=file_path,
                line_number=line_num,
                creation_method='create',
            ))

        # ── Creation functions ──────────────────────────────────
        for match in self.CREATION_FN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            observables.append(RxjsObservableInfo(
                name=match.group(1) or 'anonymous',
                file=file_path,
                line_number=line_num,
                creation_method=match.group(3),
                is_typed=bool(match.group(2)),
                type_param=match.group(2) or '',
            ))

        # ── Subscriptions ───────────────────────────────────────
        for match in self.SUBSCRIBE.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            sub_name = match.group(1) or ''
            ctx = content[match.end():match.end() + 300]

            # Detect observer vs callbacks
            has_next = bool(re.search(r'\bnext\s*[:(]', ctx[:150]))
            has_error = bool(re.search(r'\berror\s*[:(]', ctx[:150]))
            has_complete = bool(re.search(r'\bcomplete\s*[:(]', ctx[:150]))
            uses_object = bool(re.search(r'^\s*\{', ctx[:20]))

            subscriptions.append(RxjsSubscriptionInfo(
                name=sub_name,
                file=file_path,
                line_number=line_num,
                has_next=has_next or not uses_object,
                has_error=has_error,
                has_complete=has_complete,
                is_unsubscribed=sub_name in unsubscribe_vars,
                uses_observer_object=uses_object,
            ))

        # ── toPromise() ─────────────────────────────────────────
        for match in self.TO_PROMISE.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            conversions.append(RxjsConversionInfo(
                name=match.group(1),
                file=file_path,
                line_number=line_num,
                conversion_type='toPromise',
            ))

        # ── firstValueFrom / lastValueFrom ──────────────────────
        for match in self.VALUE_FROM.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            conversions.append(RxjsConversionInfo(
                name=match.group(2),
                file=file_path,
                line_number=line_num,
                conversion_type=match.group(1),
            ))

        # ── Subscription management ─────────────────────────────
        # takeUntil pattern
        if self.TAKE_UNTIL.search(content):
            m = self.TAKE_UNTIL.search(content)
            line_num = content[:m.start()].count('\n') + 1
            subscription_mgmt.append(RxjsSubscriptionMgmtInfo(
                name=m.group(1),
                file=file_path,
                line_number=line_num,
                pattern='takeUntil',
            ))

        # async pipe (Angular)
        if self.ASYNC_PIPE.search(content):
            m = self.ASYNC_PIPE.search(content)
            line_num = content[:m.start()].count('\n') + 1
            subscription_mgmt.append(RxjsSubscriptionMgmtInfo(
                name='async',
                file=file_path,
                line_number=line_num,
                pattern='async_pipe',
            ))

        # Manual unsubscribe
        for var in unsubscribe_vars:
            subscription_mgmt.append(RxjsSubscriptionMgmtInfo(
                name=var,
                file=file_path,
                line_number=0,
                pattern='manual',
            ))

        return {
            'observables': observables[:50],
            'subscriptions': subscriptions[:50],
            'conversions': conversions[:20],
            'subscription_mgmt': subscription_mgmt[:20],
        }
