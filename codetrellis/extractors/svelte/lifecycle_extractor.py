"""
Svelte Lifecycle & Rune Extractor for CodeTrellis

Extracts lifecycle hooks, context API usage, and Svelte 5 runes:
- Lifecycle hooks: onMount, onDestroy, beforeUpdate, afterUpdate, tick
- Context API: setContext, getContext, hasContext, getAllContexts
- Svelte 5 runes: $effect, $effect.pre, $effect.root, $state.raw,
                  $state.snapshot, $host

Supports Svelte 3.x through 5.x:
- Svelte 3/4: onMount, onDestroy, beforeUpdate, afterUpdate, tick
- Svelte 5: $effect (replaces onMount/afterUpdate), $effect.pre (replaces beforeUpdate),
            $effect.root (manual cleanup), $state.raw, $state.snapshot

Part of CodeTrellis v4.35 - Svelte/SvelteKit Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SvelteLifecycleHookInfo:
    """Information about a Svelte lifecycle hook usage."""
    name: str  # onMount, onDestroy, beforeUpdate, afterUpdate, tick
    file: str = ""
    line_number: int = 0
    has_cleanup: bool = False  # onMount returning a cleanup function
    is_async: bool = False  # async onMount


@dataclass
class SvelteContextInfo:
    """Information about Svelte context API usage."""
    key: str
    kind: str = ""  # set, get, has, getAll
    type: str = ""  # TypeScript type
    file: str = ""
    line_number: int = 0


@dataclass
class SvelteRuneInfo:
    """Information about a Svelte 5 rune usage."""
    name: str  # $state, $derived, $effect, $props, $bindable, $inspect, etc.
    variant: str = ""  # e.g., 'pre' for $effect.pre, 'raw' for $state.raw
    variable_name: str = ""  # the variable being assigned
    file: str = ""
    line_number: int = 0
    type_param: str = ""  # TypeScript generic type


class SvelteLifecycleExtractor:
    """
    Extracts lifecycle hooks, context usage, and rune patterns.

    Handles:
    - Traditional lifecycle hooks (Svelte 3/4)
    - Context API usage
    - Svelte 5 rune effects and state management
    """

    # Lifecycle hook patterns
    LIFECYCLE_HOOKS = {
        'onMount': re.compile(r'\bonMount\s*\(\s*(async\s*)?\(', re.MULTILINE),
        'onDestroy': re.compile(r'\bonDestroy\s*\(', re.MULTILINE),
        'beforeUpdate': re.compile(r'\bbeforeUpdate\s*\(', re.MULTILINE),
        'afterUpdate': re.compile(r'\bafterUpdate\s*\(', re.MULTILINE),
        'tick': re.compile(r'\btick\s*\(', re.MULTILINE),
    }

    # onMount with cleanup return
    ONMOUNT_CLEANUP_PATTERN = re.compile(
        r'onMount\s*\(\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{[^}]*return\s+',
        re.MULTILINE | re.DOTALL
    )

    # Context patterns
    SET_CONTEXT_PATTERN = re.compile(
        r'setContext\s*(?:<([^>]+)>)?\s*\(\s*[\'"]([^\'"]+)[\'"]',
        re.MULTILINE
    )
    GET_CONTEXT_PATTERN = re.compile(
        r'getContext\s*(?:<([^>]+)>)?\s*\(\s*[\'"]([^\'"]+)[\'"]',
        re.MULTILINE
    )
    HAS_CONTEXT_PATTERN = re.compile(
        r'hasContext\s*\(\s*[\'"]([^\'"]+)[\'"]',
        re.MULTILINE
    )
    GET_ALL_CONTEXTS_PATTERN = re.compile(
        r'getAllContexts\s*\(',
        re.MULTILINE
    )

    # Svelte 5 rune patterns
    RUNE_PATTERNS = {
        '$state': re.compile(
            r'(?:let|const)\s+(\w+)\s*=\s*\$state\s*(?:<([^>]+)>)?\s*\(',
            re.MULTILINE
        ),
        '$state.raw': re.compile(
            r'(?:let|const)\s+(\w+)\s*=\s*\$state\.raw\s*(?:<([^>]+)>)?\s*\(',
            re.MULTILINE
        ),
        '$state.snapshot': re.compile(
            r'\$state\.snapshot\s*\(',
            re.MULTILINE
        ),
        '$derived': re.compile(
            r'(?:let|const)\s+(\w+)\s*=\s*\$derived\s*(?:<([^>]+)>)?\s*[.(]',
            re.MULTILINE
        ),
        '$derived.by': re.compile(
            r'(?:let|const)\s+(\w+)\s*=\s*\$derived\.by\s*\(',
            re.MULTILINE
        ),
        '$effect': re.compile(
            r'\$effect\s*\(',
            re.MULTILINE
        ),
        '$effect.pre': re.compile(
            r'\$effect\.pre\s*\(',
            re.MULTILINE
        ),
        '$effect.root': re.compile(
            r'\$effect\.root\s*\(',
            re.MULTILINE
        ),
        '$props': re.compile(
            r'\$props\s*\(',
            re.MULTILINE
        ),
        '$bindable': re.compile(
            r'\$bindable\s*\(',
            re.MULTILINE
        ),
        '$inspect': re.compile(
            r'\$inspect\s*\(',
            re.MULTILINE
        ),
        '$host': re.compile(
            r'\$host\s*\(',
            re.MULTILINE
        ),
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract lifecycle hooks, context usage, and runes.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'lifecycle_hooks', 'contexts', 'runes'
        """
        lifecycle_hooks = []
        contexts = []
        runes = []

        # Extract lifecycle hooks
        for hook_name, pattern in self.LIFECYCLE_HOOKS.items():
            for match in pattern.finditer(content):
                is_async = bool(match.group(1)) if match.lastindex and match.lastindex >= 1 else False
                has_cleanup = False
                if hook_name == 'onMount':
                    has_cleanup = bool(self.ONMOUNT_CLEANUP_PATTERN.search(content))

                hook = SvelteLifecycleHookInfo(
                    name=hook_name,
                    file=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                    has_cleanup=has_cleanup,
                    is_async=is_async if hook_name == 'onMount' else False,
                )
                lifecycle_hooks.append(hook)

        # Extract context usage
        for match in self.SET_CONTEXT_PATTERN.finditer(content):
            type_param = match.group(1) or ''
            key = match.group(2)
            contexts.append(SvelteContextInfo(
                key=key,
                kind='set',
                type=type_param,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        for match in self.GET_CONTEXT_PATTERN.finditer(content):
            type_param = match.group(1) or ''
            key = match.group(2)
            contexts.append(SvelteContextInfo(
                key=key,
                kind='get',
                type=type_param,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        for match in self.HAS_CONTEXT_PATTERN.finditer(content):
            key = match.group(1)
            contexts.append(SvelteContextInfo(
                key=key,
                kind='has',
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        if self.GET_ALL_CONTEXTS_PATTERN.search(content):
            contexts.append(SvelteContextInfo(
                key='*',
                kind='getAll',
                file=file_path,
            ))

        # Extract runes
        for rune_name, pattern in self.RUNE_PATTERNS.items():
            for match in pattern.finditer(content):
                variable_name = ''
                type_param = ''

                if match.lastindex and match.lastindex >= 1:
                    variable_name = match.group(1) or ''
                if match.lastindex and match.lastindex >= 2:
                    type_param = match.group(2) or ''

                # Determine variant
                variant = ''
                if '.' in rune_name:
                    parts = rune_name.split('.')
                    variant = parts[1] if len(parts) > 1 else ''

                rune = SvelteRuneInfo(
                    name=rune_name.split('.')[0],
                    variant=variant,
                    variable_name=variable_name,
                    file=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                    type_param=type_param,
                )
                runes.append(rune)

        return {
            'lifecycle_hooks': lifecycle_hooks,
            'contexts': contexts,
            'runes': runes,
        }
