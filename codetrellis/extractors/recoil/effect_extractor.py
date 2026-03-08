"""
Recoil Effect Extractor for CodeTrellis

Extracts Recoil atom effect patterns:
- Atom effects array in atom({effects: [...]}) / atom({effects_UNSTABLE: [...]})
- Named effect factories: const myEffect = ({onSet, setSelf, resetSelf, ...}) => ...
- Inline effects within atom definitions
- Effect parameters: onSet, setSelf, resetSelf, trigger, storeID, node,
                      parentStoreID_UNSTABLE, getLoadable, getPromise, getInfo_UNSTABLE
- Persistence effects (localStorage, sessionStorage, URL sync)
- Logging/validation/sync/broadcast effects
- Effect cleanup (return () => { ... })

Supports:
- Recoil 0.2.x+ (atom effects introduction)
- Recoil 0.6.x+ (storeID)
- Recoil 0.7.x (latest)

Part of CodeTrellis v4.50 - Recoil Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RecoilEffectInfo:
    """Information about a Recoil atom effect."""
    name: str
    file: str = ""
    line_number: int = 0
    effect_type: str = ""  # persistence, logging, validation, sync, broadcast, custom
    has_on_set: bool = False
    has_set_self: bool = False
    has_reset_self: bool = False
    has_cleanup: bool = False
    has_trigger: bool = False
    has_store_id: bool = False
    storage_type: str = ""  # localStorage, sessionStorage, asyncStorage, url, custom
    is_factory: bool = False  # Is it a reusable effect factory function?
    is_exported: bool = False
    atom_name: str = ""  # atom this effect belongs to (if inline)


class RecoilEffectExtractor:
    """
    Extracts Recoil atom effect patterns from source code.

    Detects:
    - Named effect factory functions
    - Inline effects in atom definitions
    - Effect API usage (onSet, setSelf, resetSelf, trigger, etc.)
    - Persistence patterns (localStorage, sessionStorage, URL sync)
    - Cleanup patterns
    """

    # Named effect factory: const myEffect = ({onSet, setSelf, ...}) => { ... }
    # Also: const myEffect: AtomEffect<T> = ({onSet, ...}) => { ... }
    EFFECT_FACTORY_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*'
        r'(?::\s*AtomEffect\s*(?:<[^>]*>)?\s*)?=\s*'
        r'(?:\(\s*\{([^}]*)\}\s*\)|\(\s*\w+\s*\))\s*=>',
        re.MULTILINE
    )

    # Effect factory as function declaration: function myEffect({onSet, ...}) { ... }
    EFFECT_FUNCTION_PATTERN = re.compile(
        r'(?:export\s+)?function\s+(\w+)\s*\(\s*\{([^}]*)\}\s*\)',
        re.MULTILINE
    )

    # Parameterized effect factory: const myEffect = (param) => ({onSet, setSelf, ...}) => { ... }
    PARAMETERIZED_EFFECT_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'\([^)]*\)\s*=>\s*\(\s*\{([^}]*)\}\s*\)\s*=>',
        re.MULTILINE
    )

    # Detect effects array in atom: effects: [ ... ] or effects_UNSTABLE: [ ... ]
    ATOM_EFFECTS_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*atom\s*(?:<[^>]*)?\s*\(\s*\{[^}]*'
        r'effects(?:_UNSTABLE)?\s*:\s*\[',
        re.DOTALL
    )

    # Effect API members
    ON_SET_PATTERN = re.compile(r'\bonSet\b', re.MULTILINE)
    SET_SELF_PATTERN = re.compile(r'\bsetSelf\b', re.MULTILINE)
    RESET_SELF_PATTERN = re.compile(r'\bresetSelf\b', re.MULTILINE)
    TRIGGER_PATTERN = re.compile(r'\btrigger\b', re.MULTILINE)
    STORE_ID_PATTERN = re.compile(r'\bstoreID\b', re.MULTILINE)
    CLEANUP_PATTERN = re.compile(r'return\s+\(\)\s*=>', re.MULTILINE)

    # Storage patterns
    LOCAL_STORAGE_PATTERN = re.compile(r'localStorage\b', re.MULTILINE)
    SESSION_STORAGE_PATTERN = re.compile(r'sessionStorage\b', re.MULTILINE)
    ASYNC_STORAGE_PATTERN = re.compile(r'AsyncStorage\b', re.MULTILINE)
    URL_SYNC_PATTERN = re.compile(r'(?:URLSearchParams|location\.search|location\.hash|history\.push|router\.push)', re.MULTILINE)

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Recoil atom effect patterns from source code."""
        effects = []
        seen_names = set()

        # ── Parameterized effect factories ─────────────────────
        for m in self.PARAMETERIZED_EFFECT_PATTERN.finditer(content):
            name = m.group(1)
            params = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            # Get surrounding context
            ctx = content[m.start():min(len(content), m.start() + 500)]

            effects.append(self._build_effect_info(
                name=name,
                params=params,
                context=ctx,
                file_path=file_path,
                line=line,
                is_exported=is_exported,
                is_factory=True,
            ))
            seen_names.add(name)

        # ── Named effect factories ─────────────────────────────
        for m in self.EFFECT_FACTORY_PATTERN.finditer(content):
            name = m.group(1)
            if name in seen_names:
                continue
            params = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            ctx = content[m.start():min(len(content), m.start() + 500)]

            # Check if this is an AtomEffect (has effect-related params)
            effect_params = {'onSet', 'setSelf', 'resetSelf', 'trigger', 'storeID',
                            'node', 'getLoadable', 'getPromise', 'getInfo_UNSTABLE'}
            param_names = set(re.findall(r'\b(\w+)\b', params))
            if not param_names.intersection(effect_params):
                continue

            effects.append(self._build_effect_info(
                name=name,
                params=params,
                context=ctx,
                file_path=file_path,
                line=line,
                is_exported=is_exported,
                is_factory=True,
            ))
            seen_names.add(name)

        # ── Effect function declarations ───────────────────────
        for m in self.EFFECT_FUNCTION_PATTERN.finditer(content):
            name = m.group(1)
            if name in seen_names:
                continue
            params = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 10):m.start() + 5]

            effect_params = {'onSet', 'setSelf', 'resetSelf', 'trigger', 'storeID',
                            'node', 'getLoadable', 'getPromise', 'getInfo_UNSTABLE'}
            param_names = set(re.findall(r'\b(\w+)\b', params))
            if not param_names.intersection(effect_params):
                continue

            ctx = content[m.start():min(len(content), m.start() + 500)]

            effects.append(self._build_effect_info(
                name=name,
                params=params,
                context=ctx,
                file_path=file_path,
                line=line,
                is_exported=is_exported,
                is_factory=True,
            ))
            seen_names.add(name)

        return {
            'effects': effects,
        }

    def _build_effect_info(
        self,
        name: str,
        params: str,
        context: str,
        file_path: str,
        line: int,
        is_exported: bool,
        is_factory: bool = False,
        atom_name: str = "",
    ) -> RecoilEffectInfo:
        """Build a RecoilEffectInfo from extracted data."""
        has_on_set = bool(self.ON_SET_PATTERN.search(context))
        has_set_self = bool(self.SET_SELF_PATTERN.search(context))
        has_reset_self = bool(self.RESET_SELF_PATTERN.search(context))
        has_cleanup = bool(self.CLEANUP_PATTERN.search(context))
        has_trigger = bool(self.TRIGGER_PATTERN.search(context))
        has_store_id = bool(self.STORE_ID_PATTERN.search(context))

        # Determine effect type and storage type
        effect_type = "custom"
        storage_type = ""

        if self.LOCAL_STORAGE_PATTERN.search(context):
            effect_type = "persistence"
            storage_type = "localStorage"
        elif self.SESSION_STORAGE_PATTERN.search(context):
            effect_type = "persistence"
            storage_type = "sessionStorage"
        elif self.ASYNC_STORAGE_PATTERN.search(context):
            effect_type = "persistence"
            storage_type = "asyncStorage"
        elif self.URL_SYNC_PATTERN.search(context):
            effect_type = "sync"
            storage_type = "url"
        elif 'console.log' in context or 'logger' in context.lower():
            effect_type = "logging"
        elif 'validate' in context.lower() or 'valid' in name.lower():
            effect_type = "validation"
        elif 'broadcast' in context.lower() or 'BroadcastChannel' in context:
            effect_type = "broadcast"

        return RecoilEffectInfo(
            name=name,
            file=file_path,
            line_number=line,
            effect_type=effect_type,
            has_on_set=has_on_set,
            has_set_self=has_set_self,
            has_reset_self=has_reset_self,
            has_cleanup=has_cleanup,
            has_trigger=has_trigger,
            has_store_id=has_store_id,
            storage_type=storage_type,
            is_factory=is_factory,
            is_exported=is_exported,
            atom_name=atom_name,
        )
