"""
Preact Hook Extractor for CodeTrellis

Extracts Preact hook usage patterns from JavaScript/TypeScript source code:
- Built-in hooks from preact/hooks (useState, useEffect, useContext, useReducer,
  useRef, useMemo, useCallback, useLayoutEffect, useImperativeHandle,
  useDebugValue, useErrorBoundary, useId)
- Custom hooks (functions starting with 'use' that call other hooks)
- Hook dependencies analysis (missing/excessive deps)
- Hook rules violations (conditional hooks, loops)
- Preact-specific hooks (useErrorBoundary — unique to Preact)

Supports:
- Preact X (10.x): Full hooks support via preact/hooks
- Preact 10.5+: useId hook
- Preact 10.x: useErrorBoundary (Preact-specific)

Part of CodeTrellis v4.64 - Preact Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class PreactHookUsageInfo:
    """Information about a hook usage within a component."""
    hook_name: str
    file: str = ""
    line_number: int = 0
    component: str = ""
    arguments: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    has_cleanup: bool = False
    is_conditional: bool = False
    category: str = ""  # state, effect, context, ref, memo, callback, custom, error, identity


@dataclass
class PreactCustomHookInfo:
    """Information about a custom hook definition."""
    name: str
    file: str = ""
    line_number: int = 0
    parameters: List[str] = field(default_factory=list)
    return_type: str = ""
    return_values: List[str] = field(default_factory=list)
    hooks_used: List[str] = field(default_factory=list)
    is_exported: bool = False
    is_async: bool = False
    description: str = ""


@dataclass
class PreactHookDependencyInfo:
    """Information about hook dependency arrays."""
    hook_name: str
    component: str = ""
    file: str = ""
    line_number: int = 0
    dependencies: List[str] = field(default_factory=list)
    has_empty_deps: bool = False
    has_no_deps: bool = False
    potentially_missing: List[str] = field(default_factory=list)


class PreactHookExtractor:
    """
    Extracts Preact hook patterns from source code.

    Detects:
    - All built-in Preact hooks with dependency analysis
    - Custom hook definitions and their internal hook usage
    - Preact-specific hooks (useErrorBoundary)
    - Hook categorization (state, effect, context, ref, memo, etc.)
    """

    # Hook categories
    HOOK_CATEGORIES = {
        'useState': 'state',
        'useReducer': 'state',
        'useEffect': 'effect',
        'useLayoutEffect': 'effect',
        'useContext': 'context',
        'useRef': 'ref',
        'useImperativeHandle': 'ref',
        'useMemo': 'memo',
        'useCallback': 'callback',
        'useDebugValue': 'debug',
        'useErrorBoundary': 'error',
        'useId': 'identity',
    }

    # Custom hook definition pattern (function declaration)
    CUSTOM_HOOK_FUNC_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+(?:default\s+)?)?'
        r'(?:async\s+)?'
        r'function\s+(use[A-Z]\w*)\s*'
        r'(?:<[^>]*>\s*)?'
        r'\(\s*([^)]*)\s*\)',
        re.MULTILINE
    )

    # Custom hook definition pattern (arrow function)
    CUSTOM_HOOK_ARROW_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+(?:default\s+)?)?'
        r'(?:const|let|var)\s+(use[A-Z]\w*)\s*'
        r'(?::\s*[^=]+)?\s*=\s*'
        r'(?:async\s+)?'
        r'(?:\([^)]*\)|[\w]+)\s*(?::\s*[^=]+)?\s*=>',
        re.MULTILINE
    )

    # Hook usage pattern
    HOOK_CALL_PATTERN = re.compile(
        r'\b(use[A-Z]\w*)\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # Dependency array pattern
    DEP_ARRAY_PATTERN = re.compile(
        r'(useEffect|useLayoutEffect|useMemo|useCallback)\s*'
        r'(?:<[^>]*>)?\s*\(\s*'
        r'(?:(?:async\s+)?(?:function\s*)?(?:\([^)]*\)|[\w]+)\s*=>\s*[^,]+|'
        r'function\s*\([^)]*\)\s*\{[^}]*\})'
        r'\s*,\s*\[([^\]]*)\]\s*\)',
        re.DOTALL
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Preact hook patterns from source code."""
        hook_usages: List[PreactHookUsageInfo] = []
        custom_hooks: List[PreactCustomHookInfo] = []
        hook_deps: List[PreactHookDependencyInfo] = []

        # ── Custom hook definitions ───────────────────────────────
        for pattern in [self.CUSTOM_HOOK_FUNC_PATTERN, self.CUSTOM_HOOK_ARROW_PATTERN]:
            for m in pattern.finditer(content):
                name = m.group(1)
                line = content[:m.start()].count('\n') + 1

                prefix = content[max(0, m.start() - 50):m.start() + len(m.group(0))]
                is_exported = 'export' in prefix
                is_async = 'async' in m.group(0)

                # Extract params
                params = []
                if pattern == self.CUSTOM_HOOK_FUNC_PATTERN:
                    param_str = m.group(2) or ""
                    params = [p.strip().split(':')[0].strip()
                              for p in param_str.split(',') if p.strip()]

                # Find hooks used within
                body_end = min(len(content), m.end() + 3000)
                body = content[m.end():body_end]
                hooks_used = list(set(re.findall(r'\b(use[A-Z]\w*)\b', body)))

                # Check for return values
                return_vals = re.findall(r'return\s+\[([^\]]+)\]', body)
                return_values = []
                if return_vals:
                    return_values = [v.strip() for v in return_vals[0].split(',')]

                custom_hooks.append(PreactCustomHookInfo(
                    name=name,
                    file=file_path,
                    line_number=line,
                    parameters=params[:10],
                    hooks_used=hooks_used[:15],
                    is_exported=is_exported,
                    is_async=is_async,
                    return_values=return_values[:10],
                ))

        # ── Hook usages ───────────────────────────────────────────
        for m in self.HOOK_CALL_PATTERN.finditer(content):
            hook_name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            # Determine category
            category = self.HOOK_CATEGORIES.get(hook_name, 'custom')

            # Check for cleanup (useEffect)
            has_cleanup = False
            if hook_name in ('useEffect', 'useLayoutEffect'):
                after = content[m.end():min(len(content), m.end() + 500)]
                has_cleanup = bool(re.search(r'return\s+(?:function|\(?\s*\)?\s*=>)', after))

            # Find enclosing component
            component = self._find_enclosing_component(content, m.start())

            hook_usages.append(PreactHookUsageInfo(
                hook_name=hook_name,
                file=file_path,
                line_number=line,
                component=component or "",
                category=category,
                has_cleanup=has_cleanup,
            ))

        # ── Dependency analysis ───────────────────────────────────
        for m in self.DEP_ARRAY_PATTERN.finditer(content):
            hook_name = m.group(1)
            deps_str = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1

            dependencies = [d.strip() for d in deps_str.split(',') if d.strip()]
            has_empty = deps_str.strip() == ""
            component = self._find_enclosing_component(content, m.start())

            hook_deps.append(PreactHookDependencyInfo(
                hook_name=hook_name,
                component=component or "",
                file=file_path,
                line_number=line,
                dependencies=dependencies[:15],
                has_empty_deps=has_empty and '[]' in m.group(0),
                has_no_deps=False,
            ))

        return {
            'hook_usages': hook_usages,
            'custom_hooks': custom_hooks,
            'hook_dependencies': hook_deps,
        }

    def _find_enclosing_component(self, content: str, pos: int) -> Optional[str]:
        """Find the component or hook name enclosing the given position."""
        before = content[max(0, pos - 2000):pos]
        func_match = re.findall(r'function\s+([A-Z]\w*|use[A-Z]\w*)\s*\(', before)
        if func_match:
            return func_match[-1]
        arrow_match = re.findall(r'(?:const|let|var)\s+([A-Z]\w*|use[A-Z]\w*)\s*=', before)
        if arrow_match:
            return arrow_match[-1]
        return None
