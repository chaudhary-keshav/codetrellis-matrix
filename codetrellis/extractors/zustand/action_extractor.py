"""
Zustand Action Extractor for CodeTrellis

Extracts Zustand action patterns and state mutation operations:
- set() calls with state updaters
- get() calls for state access in actions
- subscribe() / subscribe with selector
- getState() / setState() imperative API
- destroy() store cleanup
- Temporal (undo/redo) actions (zundo)
- Async actions (async set patterns)

Supports:
- Zustand v1-v3 (setState/getState/subscribe/destroy)
- Zustand v4 (same API + subscribeWithSelector)
- Zustand v5 (same API + getInitialState)
- Vanilla store API (createStore)

Part of CodeTrellis v4.48 - Zustand Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ZustandActionInfo:
    """Information about a Zustand action (state mutation)."""
    name: str
    file: str = ""
    line_number: int = 0
    action_type: str = ""  # sync, async, thunk
    uses_set: bool = False
    uses_get: bool = False
    uses_produce: bool = False  # immer produce
    is_exported: bool = False
    parameters: List[str] = field(default_factory=list)


@dataclass
class ZustandSubscriptionInfo:
    """Information about a Zustand subscription."""
    name: str
    file: str = ""
    line_number: int = 0
    store_name: str = ""
    subscription_type: str = ""  # subscribe, subscribeWithSelector
    has_selector: bool = False
    has_equality_fn: bool = False
    has_fireImmediately: bool = False
    is_cleanup: bool = False  # returns unsubscribe


@dataclass
class ZustandImperativeInfo:
    """Information about imperative Zustand API usage."""
    name: str
    file: str = ""
    line_number: int = 0
    api_method: str = ""  # getState, setState, subscribe, destroy, getInitialState
    store_name: str = ""
    is_outside_react: bool = False


class ZustandActionExtractor:
    """
    Extracts Zustand action patterns and imperative API usage.

    Detects:
    - set() calls within store definitions (state mutations)
    - get() calls within store definitions (state access)
    - Async actions (async () => { set(...) })
    - Imperative API: store.getState(), store.setState()
    - Subscriptions: store.subscribe(listener)
    - Destroy: store.destroy()
    - Temporal actions: undo(), redo(), clear() (zundo)
    """

    # Action definition within store: name: (args) => { set(...) }
    ACTION_DEF_PATTERN = re.compile(
        r'(\w+)\s*:\s*(?:async\s+)?\(([^)]*)\)\s*=>\s*(?:\{|set|get)',
        re.MULTILINE
    )

    # Async action: name: async (...) => { ... set(...) }
    ASYNC_ACTION_PATTERN = re.compile(
        r'(\w+)\s*:\s*async\s+\(',
        re.MULTILINE
    )

    # Imperative getState: store.getState()
    GET_STATE_PATTERN = re.compile(
        r'(\w+)\.getState\s*\(\s*\)',
        re.MULTILINE
    )

    # Imperative setState: store.setState(...)
    SET_STATE_PATTERN = re.compile(
        r'(\w+)\.setState\s*\(',
        re.MULTILINE
    )

    # Subscribe: store.subscribe(callback) or store.subscribe(selector, callback)
    SUBSCRIBE_PATTERN = re.compile(
        r'(\w+)\.subscribe\s*\(',
        re.MULTILINE
    )

    # Destroy: store.destroy()
    DESTROY_PATTERN = re.compile(
        r'(\w+)\.destroy\s*\(\s*\)',
        re.MULTILINE
    )

    # getInitialState (v5): store.getInitialState()
    GET_INITIAL_STATE_PATTERN = re.compile(
        r'(\w+)\.getInitialState\s*\(\s*\)',
        re.MULTILINE
    )

    # Temporal actions: undo(), redo(), clear() from zundo
    TEMPORAL_ACTION_PATTERN = re.compile(
        r'(?:const|let|var)\s+\{\s*([^}]*(?:undo|redo|clear|pastStates|futureStates)[^}]*)\}\s*=\s*'
        r'(\w+)\.temporal\.getState\s*\(\s*\)',
        re.MULTILINE
    )

    # set() usage with produce (immer)
    SET_PRODUCE_PATTERN = re.compile(
        r'set\s*\(\s*produce\s*\(',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Zustand action patterns from source code."""
        actions = []
        subscriptions = []
        imperative_usages = []

        # ── Action definitions ────────────────────────────────────
        for m in self.ACTION_DEF_PATTERN.finditer(content):
            name = m.group(1)
            params_str = m.group(2)
            line = content[:m.start()].count('\n') + 1

            # Skip common non-action names
            if name in ('get', 'set', 'subscribe', 'destroy', 'getState', 'setState'):
                continue

            params = [p.strip().split(':')[0].strip() for p in params_str.split(',') if p.strip()]

            # Check if async
            is_async = bool(re.search(r'async\s+\(', content[max(0, m.start() - 10):m.end()]))

            # Check if uses set/get
            action_end = min(len(content), m.end() + 500)
            action_body = content[m.end():action_end]
            uses_set = bool(re.search(r'\bset\s*\(', action_body))
            uses_get = bool(re.search(r'\bget\s*\(', action_body))
            uses_produce = bool(self.SET_PRODUCE_PATTERN.search(action_body))

            actions.append(ZustandActionInfo(
                name=name,
                file=file_path,
                line_number=line,
                action_type="async" if is_async else "sync",
                uses_set=uses_set,
                uses_get=uses_get,
                uses_produce=uses_produce,
                parameters=params[:5],
            ))

        # ── Imperative getState() ─────────────────────────────────
        for m in self.GET_STATE_PATTERN.finditer(content):
            store_name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            imperative_usages.append(ZustandImperativeInfo(
                name=f"{store_name}.getState",
                file=file_path,
                line_number=line,
                api_method="getState",
                store_name=store_name,
                is_outside_react=True,
            ))

        # ── Imperative setState() ─────────────────────────────────
        for m in self.SET_STATE_PATTERN.finditer(content):
            store_name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            imperative_usages.append(ZustandImperativeInfo(
                name=f"{store_name}.setState",
                file=file_path,
                line_number=line,
                api_method="setState",
                store_name=store_name,
                is_outside_react=True,
            ))

        # ── Subscriptions ─────────────────────────────────────────
        for m in self.SUBSCRIBE_PATTERN.finditer(content):
            store_name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            # Check if subscription has selector
            sub_context_end = min(len(content), m.end() + 300)
            sub_context = content[m.end():sub_context_end]
            has_selector = bool(re.search(r'(?:state|s)\s*=>', sub_context))
            has_equality = bool(re.search(r',\s*\{[^}]*equalityFn', sub_context))
            has_fire_immediately = bool(re.search(r'fireImmediately\s*:\s*true', sub_context))

            subscriptions.append(ZustandSubscriptionInfo(
                name=f"{store_name}.subscribe",
                file=file_path,
                line_number=line,
                store_name=store_name,
                subscription_type="subscribeWithSelector" if has_selector else "subscribe",
                has_selector=has_selector,
                has_equality_fn=has_equality,
                has_fireImmediately=has_fire_immediately,
            ))

        # ── Destroy ───────────────────────────────────────────────
        for m in self.DESTROY_PATTERN.finditer(content):
            store_name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            imperative_usages.append(ZustandImperativeInfo(
                name=f"{store_name}.destroy",
                file=file_path,
                line_number=line,
                api_method="destroy",
                store_name=store_name,
            ))

        # ── getInitialState (v5) ──────────────────────────────────
        for m in self.GET_INITIAL_STATE_PATTERN.finditer(content):
            store_name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            imperative_usages.append(ZustandImperativeInfo(
                name=f"{store_name}.getInitialState",
                file=file_path,
                line_number=line,
                api_method="getInitialState",
                store_name=store_name,
            ))

        # ── Temporal actions (zundo) ──────────────────────────────
        for m in self.TEMPORAL_ACTION_PATTERN.finditer(content):
            names_str = m.group(1)
            store_name = m.group(2)
            line = content[:m.start()].count('\n') + 1

            temporal_names = [n.strip() for n in names_str.split(',') if n.strip()]
            for tname in temporal_names:
                imperative_usages.append(ZustandImperativeInfo(
                    name=f"{store_name}.temporal.{tname}",
                    file=file_path,
                    line_number=line,
                    api_method=f"temporal.{tname}",
                    store_name=store_name,
                ))

        return {
            'actions': actions,
            'subscriptions': subscriptions,
            'imperative_usages': imperative_usages,
        }
