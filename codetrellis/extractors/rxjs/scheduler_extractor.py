"""
RxJS Scheduler Extractor — Scheduler types, testing utilities.

Extracts:
- Scheduler types (asyncScheduler, asapScheduler, queueScheduler, animationFrameScheduler)
- TestScheduler (marble testing)
- VirtualTimeScheduler
- observeOn / subscribeOn usage
- Marble testing patterns (hot, cold, expectObservable, expectSubscriptions)
- Scheduler injection patterns

Supports RxJS v5, v6, v7.
v4.77: Full RxJS scheduler + testing support.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class RxjsSchedulerInfo:
    """A scheduler usage."""
    name: str = ""                    # Scheduler name
    file: str = ""
    line_number: int = 0
    scheduler_type: str = ""          # 'async', 'asap', 'queue', 'animationFrame', 'test', 'virtual'
    usage_context: str = ""           # 'observeOn', 'subscribeOn', 'operator_arg', 'direct'


@dataclass
class RxjsTestingInfo:
    """A testing utility usage."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    testing_type: str = ""            # 'marble', 'testScheduler', 'hot', 'cold', 'expectObservable', 'expectSubscriptions', 'flush'
    has_marble_diagram: bool = False


@dataclass
class RxjsMarbleInfo:
    """A marble diagram definition."""
    diagram: str = ""
    file: str = ""
    line_number: int = 0
    marble_type: str = ""             # 'hot', 'cold', 'expected'


SCHEDULER_TYPES = {
    'asyncScheduler': 'async',
    'asapScheduler': 'asap',
    'queueScheduler': 'queue',
    'animationFrameScheduler': 'animationFrame',
    'TestScheduler': 'test',
    'VirtualTimeScheduler': 'virtual',
    # v5 names
    'async': 'async',
    'asap': 'asap',
    'queue': 'queue',
    'animationFrame': 'animationFrame',
}


class RxjsSchedulerExtractor:
    """
    Extracts RxJS scheduler and testing patterns.
    """

    # Scheduler imports
    SCHEDULER_IMPORT = re.compile(
        r"import\s+\{([^}]*(?:Scheduler|asyncScheduler|asapScheduler|queueScheduler|animationFrameScheduler|TestScheduler|VirtualTimeScheduler)[^}]*)\}\s+from\s+['\"]rxjs(?:/[^'\"]*)?['\"]",
        re.MULTILINE
    )

    # observeOn / subscribeOn usage
    OBSERVE_ON = re.compile(
        r'\bobserveOn\s*\(\s*(\w+)',
    )

    SUBSCRIBE_ON = re.compile(
        r'\bsubscribeOn\s*\(\s*(\w+)',
    )

    # TestScheduler creation
    TEST_SCHEDULER = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?new\s+TestScheduler\s*\(',
        re.MULTILINE
    )

    # Marble testing patterns
    HOT_PATTERN = re.compile(
        r"(?:scheduler|testScheduler|this\.scheduler)\s*\.\s*createHotObservable\s*\(\s*['\"]([^'\"]*)['\"]",
    )

    COLD_PATTERN = re.compile(
        r"(?:scheduler|testScheduler|this\.scheduler)\s*\.\s*createColdObservable\s*\(\s*['\"]([^'\"]*)['\"]",
    )

    # hot() and cold() helpers
    HOT_HELPER = re.compile(
        r"\bhot\s*\(\s*['\"]([^'\"]*)['\"]",
    )

    COLD_HELPER = re.compile(
        r"\bcold\s*\(\s*['\"]([^'\"]*)['\"]",
    )

    # expectObservable
    EXPECT_OBSERVABLE = re.compile(
        r'expectObservable\s*\(',
    )

    # expectSubscriptions
    EXPECT_SUBSCRIPTIONS = re.compile(
        r'expectSubscriptions\s*\(',
    )

    # flush()
    FLUSH = re.compile(
        r'(\w+)\.flush\s*\(\s*\)',
    )

    # run() on TestScheduler (v7 pattern)
    RUN_PATTERN = re.compile(
        r'(\w+)\.run\s*\(\s*(?:\(\s*\{([^}]*)\}\s*\)|(\w+))\s*=>',
    )

    # Marble diagram strings
    MARBLE_DIAGRAM = re.compile(
        r"['\"]([- |a-zA-Z0-9#^()]+)['\"]",
    )

    # Scheduler as operator argument
    SCHEDULER_ARG = re.compile(
        r'\b(?:of|from|interval|timer|delay|debounceTime|throttleTime|bufferTime|windowTime|timeout|sampleTime|auditTime)\s*\([^)]*,\s*(asyncScheduler|asapScheduler|queueScheduler|animationFrameScheduler)',
    )

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract all RxJS scheduler and testing constructs."""
        schedulers = []
        testing = []
        marbles = []

        # ── Scheduler usage via observeOn ───────────────────────
        for match in self.OBSERVE_ON.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            sched_name = match.group(1)
            sched_type = SCHEDULER_TYPES.get(sched_name, 'unknown')
            schedulers.append(RxjsSchedulerInfo(
                name=sched_name,
                file=file_path,
                line_number=line_num,
                scheduler_type=sched_type,
                usage_context='observeOn',
            ))

        # ── Scheduler usage via subscribeOn ─────────────────────
        for match in self.SUBSCRIBE_ON.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            sched_name = match.group(1)
            sched_type = SCHEDULER_TYPES.get(sched_name, 'unknown')
            schedulers.append(RxjsSchedulerInfo(
                name=sched_name,
                file=file_path,
                line_number=line_num,
                scheduler_type=sched_type,
                usage_context='subscribeOn',
            ))

        # ── Scheduler as operator argument ──────────────────────
        for match in self.SCHEDULER_ARG.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            sched_name = match.group(1)
            sched_type = SCHEDULER_TYPES.get(sched_name, 'unknown')
            schedulers.append(RxjsSchedulerInfo(
                name=sched_name,
                file=file_path,
                line_number=line_num,
                scheduler_type=sched_type,
                usage_context='operator_arg',
            ))

        # ── TestScheduler ──────────────────────────────────────
        for match in self.TEST_SCHEDULER.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            testing.append(RxjsTestingInfo(
                name=match.group(1) or 'testScheduler',
                file=file_path,
                line_number=line_num,
                testing_type='testScheduler',
            ))

        # ── TestScheduler.run() (v7 pattern) ───────────────────
        for match in self.RUN_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            helpers = match.group(2) or ''
            testing.append(RxjsTestingInfo(
                name=match.group(1),
                file=file_path,
                line_number=line_num,
                testing_type='testScheduler.run',
                has_marble_diagram='hot' in helpers or 'cold' in helpers,
            ))

        # ── Hot observables (marble testing) ────────────────────
        for pattern in [self.HOT_PATTERN, self.HOT_HELPER]:
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                marbles.append(RxjsMarbleInfo(
                    diagram=match.group(1),
                    file=file_path,
                    line_number=line_num,
                    marble_type='hot',
                ))

        # ── Cold observables (marble testing) ───────────────────
        for pattern in [self.COLD_PATTERN, self.COLD_HELPER]:
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                marbles.append(RxjsMarbleInfo(
                    diagram=match.group(1),
                    file=file_path,
                    line_number=line_num,
                    marble_type='cold',
                ))

        # ── expectObservable ────────────────────────────────────
        for match in self.EXPECT_OBSERVABLE.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            testing.append(RxjsTestingInfo(
                name='expectObservable',
                file=file_path,
                line_number=line_num,
                testing_type='expectObservable',
            ))

        # ── expectSubscriptions ─────────────────────────────────
        for match in self.EXPECT_SUBSCRIPTIONS.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            testing.append(RxjsTestingInfo(
                name='expectSubscriptions',
                file=file_path,
                line_number=line_num,
                testing_type='expectSubscriptions',
            ))

        # ── flush() ─────────────────────────────────────────────
        for match in self.FLUSH.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            testing.append(RxjsTestingInfo(
                name=match.group(1) + '.flush',
                file=file_path,
                line_number=line_num,
                testing_type='flush',
            ))

        return {
            'schedulers': schedulers[:30],
            'testing': testing[:30],
            'marbles': marbles[:30],
        }
