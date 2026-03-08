"""
Recoil Hook Extractor for CodeTrellis

Extracts Recoil hook usage patterns:
- useRecoilState(atom) → [value, setValue]
- useRecoilValue(atom) → value (read-only)
- useSetRecoilState(atom) → setValue (write-only)
- useResetRecoilState(atom) → resetFn
- useRecoilStateLoadable(atom) → [loadable, setValue]
- useRecoilValueLoadable(atom) → loadable
- useRecoilCallback(({snapshot, set, reset, gotoSnapshot, refresh}) => ...)
- useRecoilTransaction_UNSTABLE(({get, set, reset}) => ...)
- useRecoilRefresher_UNSTABLE(selector) → refreshFn
- useRecoilBridgeAcrossReactRoots_UNSTABLE() → RecoilBridge
- isRecoilValue(value) → boolean (utility)

Supports:
- Recoil 0.0.x through 0.7.x+

Part of CodeTrellis v4.50 - Recoil Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RecoilHookUsageInfo:
    """Information about a Recoil hook usage."""
    hook_name: str
    file: str = ""
    line_number: int = 0
    atom_name: str = ""  # atom/selector being used
    destructured_names: List[str] = field(default_factory=list)


@dataclass
class RecoilCallbackInfo:
    """Information about a useRecoilCallback or useRecoilTransaction usage."""
    name: str
    file: str = ""
    line_number: int = 0
    callback_type: str = ""  # callback, transaction
    uses_snapshot: bool = False
    uses_set: bool = False
    uses_reset: bool = False
    uses_goto_snapshot: bool = False
    uses_refresh: bool = False
    is_async: bool = False
    dependencies: List[str] = field(default_factory=list)


class RecoilHookExtractor:
    """
    Extracts Recoil hook usage patterns from source code.

    Detects:
    - useRecoilState, useRecoilValue, useSetRecoilState, useResetRecoilState
    - useRecoilStateLoadable, useRecoilValueLoadable
    - useRecoilCallback, useRecoilTransaction_UNSTABLE
    - useRecoilRefresher_UNSTABLE
    - useRecoilBridgeAcrossReactRoots_UNSTABLE
    - isRecoilValue
    """

    # Basic hooks: useRecoilState(atom), useRecoilValue(atom), etc.
    HOOK_PATTERNS = {
        'useRecoilState': re.compile(
            r'(?:const\s+)?(?:\[([^\]]*)\]\s*=\s*)?'
            r'useRecoilState\s*\(\s*(\w+)',
            re.MULTILINE
        ),
        'useRecoilValue': re.compile(
            r'(?:const\s+)?(?:(\w+)\s*=\s*)?'
            r'useRecoilValue\s*\(\s*(\w+)',
            re.MULTILINE
        ),
        'useSetRecoilState': re.compile(
            r'(?:const\s+)?(?:(\w+)\s*=\s*)?'
            r'useSetRecoilState\s*\(\s*(\w+)',
            re.MULTILINE
        ),
        'useResetRecoilState': re.compile(
            r'(?:const\s+)?(?:(\w+)\s*=\s*)?'
            r'useResetRecoilState\s*\(\s*(\w+)',
            re.MULTILINE
        ),
        'useRecoilStateLoadable': re.compile(
            r'(?:const\s+)?(?:\[([^\]]*)\]\s*=\s*)?'
            r'useRecoilStateLoadable\s*\(\s*(\w+)',
            re.MULTILINE
        ),
        'useRecoilValueLoadable': re.compile(
            r'(?:const\s+)?(?:(\w+)\s*=\s*)?'
            r'useRecoilValueLoadable\s*\(\s*(\w+)',
            re.MULTILINE
        ),
        'useRecoilRefresher_UNSTABLE': re.compile(
            r'(?:const\s+)?(?:(\w+)\s*=\s*)?'
            r'useRecoilRefresher_UNSTABLE\s*\(\s*(\w+)',
            re.MULTILINE
        ),
    }

    # useRecoilCallback(({snapshot, set, reset, gotoSnapshot, refresh}, ...args) => ...)
    CALLBACK_PATTERN = re.compile(
        r'(?:const\s+)?(\w+)\s*=\s*'
        r'useRecoilCallback\s*\(\s*'
        r'(?:async\s+)?\(\s*\{([^}]*)\}',
        re.MULTILINE
    )

    # useRecoilTransaction_UNSTABLE(({get, set, reset}) => ...)
    TRANSACTION_PATTERN = re.compile(
        r'(?:const\s+)?(\w+)\s*=\s*'
        r'useRecoilTransaction_UNSTABLE\s*\(\s*'
        r'(?:async\s+)?\(\s*\{([^}]*)\}',
        re.MULTILINE
    )

    # useRecoilBridgeAcrossReactRoots_UNSTABLE()
    BRIDGE_PATTERN = re.compile(
        r'(?:const\s+)?(\w+)\s*=\s*'
        r'useRecoilBridgeAcrossReactRoots_UNSTABLE\s*\(',
        re.MULTILINE
    )

    # isRecoilValue(value)
    IS_RECOIL_VALUE_PATTERN = re.compile(
        r'isRecoilValue\s*\(\s*(\w+)\s*\)',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Recoil hook usage patterns from source code."""
        hook_usages = []
        callbacks = []

        # ── Standard hooks ─────────────────────────────────────
        for hook_name, pattern in self.HOOK_PATTERNS.items():
            for m in pattern.finditer(content):
                line = content[:m.start()].count('\n') + 1
                atom_name = m.group(2) if m.group(2) else ""

                destructured = []
                if m.group(1):
                    raw = m.group(1).strip()
                    if raw:
                        destructured = [s.strip() for s in raw.split(',') if s.strip()]

                hook_usages.append(RecoilHookUsageInfo(
                    hook_name=hook_name,
                    file=file_path,
                    line_number=line,
                    atom_name=atom_name,
                    destructured_names=destructured[:10],
                ))

        # ── useRecoilCallback ──────────────────────────────────
        for m in self.CALLBACK_PATTERN.finditer(content):
            name = m.group(1)
            params = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1

            ctx = content[m.start():min(len(content), m.start() + 300)]

            param_names = set(re.findall(r'\b(\w+)\b', params))

            callbacks.append(RecoilCallbackInfo(
                name=name,
                file=file_path,
                line_number=line,
                callback_type="callback",
                uses_snapshot='snapshot' in param_names,
                uses_set='set' in param_names,
                uses_reset='reset' in param_names,
                uses_goto_snapshot='gotoSnapshot' in param_names,
                uses_refresh='refresh' in param_names,
                is_async='async' in ctx[:60],
            ))

        # ── useRecoilTransaction_UNSTABLE ──────────────────────
        for m in self.TRANSACTION_PATTERN.finditer(content):
            name = m.group(1)
            params = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1

            param_names = set(re.findall(r'\b(\w+)\b', params))

            callbacks.append(RecoilCallbackInfo(
                name=name,
                file=file_path,
                line_number=line,
                callback_type="transaction",
                uses_set='set' in param_names,
                uses_reset='reset' in param_names,
            ))

        # ── useRecoilBridgeAcrossReactRoots_UNSTABLE ───────────
        for m in self.BRIDGE_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            hook_usages.append(RecoilHookUsageInfo(
                hook_name="useRecoilBridgeAcrossReactRoots_UNSTABLE",
                file=file_path,
                line_number=line,
                atom_name="",
            ))

        return {
            'hook_usages': hook_usages,
            'callbacks': callbacks,
        }
