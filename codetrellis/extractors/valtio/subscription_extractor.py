"""
Valtio Subscription Extractor for CodeTrellis

Extracts Valtio subscription patterns:
- subscribe(proxyState, callback) — subscribe to all state changes
- subscribe(proxyState.nested, callback) — subscribe to nested object changes
- subscribeKey(proxyState, 'key', callback) — subscribe to primitive key changes
- watch(callback) — deprecated reactive effect (v2.3.0+ deprecated)
- Unsubscribe patterns (const unsub = subscribe(...); unsub())
- notifyInSync option
- useEffect subscribe patterns (React integration)

Supports:
- Valtio v1.x (subscribe from 'valtio', subscribeKey/watch from 'valtio/utils')
- Valtio v2.x (subscribe from 'valtio/vanilla', subscribeKey from 'valtio/vanilla/utils',
                watch deprecated in v2.3.0)

Part of CodeTrellis v4.56 - Valtio Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ValtioSubscribeInfo:
    """Information about a subscribe() call."""
    file: str = ""
    line_number: int = 0
    proxy_name: str = ""  # Which proxy is subscribed to
    is_nested: bool = False  # subscribe(state.nested, ...)
    nested_path: str = ""  # e.g., "state.obj"
    has_notify_in_sync: bool = False
    has_unsubscribe: bool = False  # Stores unsubscribe function
    unsubscribe_name: str = ""  # Name of unsubscribe variable
    is_in_use_effect: bool = False  # Inside useEffect
    is_module_level: bool = False  # At module scope


@dataclass
class ValtioSubscribeKeyInfo:
    """Information about a subscribeKey() call."""
    file: str = ""
    line_number: int = 0
    proxy_name: str = ""  # Which proxy
    key_name: str = ""  # Which key is subscribed to
    has_notify_in_sync: bool = False
    has_unsubscribe: bool = False


@dataclass
class ValtioWatchInfo:
    """Information about a watch() call (deprecated in v2.3.0)."""
    file: str = ""
    line_number: int = 0
    has_cleanup: bool = False  # Returns cleanup function
    has_sync_option: bool = False
    tracked_proxies: List[str] = field(default_factory=list)  # get(state) calls


class ValtioSubscriptionExtractor:
    """
    Extracts Valtio subscription patterns from source code.

    Detects:
    - subscribe() state subscriptions
    - subscribeKey() primitive key subscriptions
    - watch() reactive effects (deprecated)
    - Unsubscribe patterns
    - useEffect subscription patterns
    - Module-level subscriptions
    """

    # subscribe(state, callback) or subscribe(state, callback, notifyInSync)
    SUBSCRIBE_PATTERN = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?'
        r'subscribe\s*\(\s*([^,]+?)\s*,\s*(?:\([^)]*\)|[^,)]+)'
        r'(?:\s*,\s*(true|false))?\s*\)',
        re.MULTILINE
    )

    # subscribeKey(state, 'key', callback)
    SUBSCRIBE_KEY_PATTERN = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?'
        r'subscribeKey\s*\(\s*(\w+)\s*,\s*[\'"](\w+)[\'"]\s*,',
        re.MULTILINE
    )

    # watch((get) => { ... })
    WATCH_PATTERN = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?'
        r'watch\s*\(\s*\(\s*get\s*\)\s*=>',
        re.MULTILINE
    )

    # get(state) inside watch callback
    WATCH_GET_PATTERN = re.compile(
        r'get\s*\(\s*(\w+)\s*\)',
        re.MULTILINE
    )

    # useEffect with subscribe
    USE_EFFECT_SUBSCRIBE_PATTERN = re.compile(
        r'useEffect\s*\(\s*\(\s*\)\s*=>\s*\{[^}]*subscribe\s*\(',
        re.MULTILINE | re.DOTALL
    )

    # useEffect returning subscribe (cleanup pattern)
    USE_EFFECT_RETURN_SUBSCRIBE_PATTERN = re.compile(
        r'useEffect\s*\(\s*\(\s*\)\s*=>\s*(?:\{[^}]*return\s+)?subscribe\s*\(',
        re.MULTILINE | re.DOTALL
    )

    def __init__(self) -> None:
        """Initialize the subscription extractor."""

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Valtio subscription patterns from source code.

        Args:
            content: Source code content.
            file_path: Path to source file.

        Returns:
            Dictionary with 'subscribes', 'subscribe_keys', and 'watches' lists.
        """
        subscribes: List[ValtioSubscribeInfo] = []
        subscribe_keys: List[ValtioSubscribeKeyInfo] = []
        watches: List[ValtioWatchInfo] = []

        lines = content.split('\n')

        # Find useEffect regions containing subscribe
        use_effect_lines = set()
        for match in self.USE_EFFECT_SUBSCRIBE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            for i in range(line_num, min(line_num + 15, len(lines) + 1)):
                use_effect_lines.add(i)

        for match in self.USE_EFFECT_RETURN_SUBSCRIBE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            for i in range(line_num, min(line_num + 15, len(lines) + 1)):
                use_effect_lines.add(i)

        # Extract subscribe() calls
        for match in self.SUBSCRIBE_PATTERN.finditer(content):
            unsub_name = match.group(1) or ""
            proxy_ref = match.group(2).strip()
            notify_sync = match.group(3) or ""
            line_num = content[:match.start()].count('\n') + 1

            is_nested = '.' in proxy_ref
            proxy_name = proxy_ref.split('.')[0] if is_nested else proxy_ref

            # Determine scope
            line_text = lines[line_num - 1] if line_num <= len(lines) else ""
            indent_level = len(line_text) - len(line_text.lstrip())
            is_module = indent_level == 0
            is_in_effect = line_num in use_effect_lines

            subscribes.append(ValtioSubscribeInfo(
                file=file_path,
                line_number=line_num,
                proxy_name=proxy_name,
                is_nested=is_nested,
                nested_path=proxy_ref if is_nested else "",
                has_notify_in_sync=notify_sync == 'true',
                has_unsubscribe=bool(unsub_name),
                unsubscribe_name=unsub_name,
                is_in_use_effect=is_in_effect,
                is_module_level=is_module,
            ))

        # Extract subscribeKey() calls
        for match in self.SUBSCRIBE_KEY_PATTERN.finditer(content):
            unsub_name = match.group(1) or ""
            proxy_name = match.group(2)
            key_name = match.group(3)
            line_num = content[:match.start()].count('\n') + 1

            subscribe_keys.append(ValtioSubscribeKeyInfo(
                file=file_path,
                line_number=line_num,
                proxy_name=proxy_name,
                key_name=key_name,
                has_unsubscribe=bool(unsub_name),
            ))

        # Extract watch() calls (deprecated)
        for match in self.WATCH_PATTERN.finditer(content):
            stop_name = match.group(1) or ""
            line_num = content[:match.start()].count('\n') + 1

            # Find tracked proxies (get(state) calls) in the watch body
            # Look ahead up to 500 chars
            watch_body = content[match.start():match.start() + 500]
            tracked = [m.group(1) for m in self.WATCH_GET_PATTERN.finditer(watch_body)]

            watches.append(ValtioWatchInfo(
                file=file_path,
                line_number=line_num,
                has_cleanup=bool(stop_name),
                tracked_proxies=list(dict.fromkeys(tracked))[:10],
            ))

        return {
            'subscribes': subscribes,
            'subscribe_keys': subscribe_keys,
            'watches': watches,
        }
