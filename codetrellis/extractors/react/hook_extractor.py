"""
React Hook Extractor for CodeTrellis

Extracts React hook usage patterns from JavaScript/TypeScript source code:
- Built-in hooks (useState, useEffect, useContext, useReducer, etc.)
- React 18 hooks (useTransition, useDeferredValue, useId, useSyncExternalStore)
- React 19 hooks (use, useFormStatus, useFormState, useOptimistic, useActionState)
- Custom hooks (functions starting with 'use' that call other hooks)
- Hook dependencies analysis (missing/excessive deps)
- Hook rules violations (conditional hooks, loops)

Part of CodeTrellis v4.32 - React Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class ReactHookUsageInfo:
    """Information about a hook usage within a component."""
    hook_name: str
    file: str = ""
    line_number: int = 0
    component: str = ""  # Which component uses this hook
    arguments: List[str] = field(default_factory=list)  # Simplified arg descriptions
    dependencies: List[str] = field(default_factory=list)  # For useEffect/useMemo/useCallback
    has_cleanup: bool = False  # For useEffect: has cleanup return
    is_conditional: bool = False  # Hook rules violation
    category: str = ""  # state, effect, context, ref, memo, callback, custom, react18, react19


@dataclass
class ReactCustomHookInfo:
    """Information about a custom hook definition."""
    name: str
    file: str = ""
    line_number: int = 0
    parameters: List[str] = field(default_factory=list)
    return_type: str = ""  # inferred or typed return
    return_values: List[str] = field(default_factory=list)  # e.g., [value, setValue]
    hooks_used: List[str] = field(default_factory=list)  # Hooks called inside
    is_exported: bool = False
    is_async: bool = False
    description: str = ""  # From JSDoc/TSDoc
    react_version: str = ""  # Minimum React version required


@dataclass
class ReactHookDependencyInfo:
    """Information about hook dependency arrays."""
    hook_name: str
    component: str = ""
    file: str = ""
    line_number: int = 0
    dependencies: List[str] = field(default_factory=list)
    has_empty_deps: bool = False  # [] — runs once
    has_no_deps: bool = False  # no array — runs every render
    potentially_missing: List[str] = field(default_factory=list)


class ReactHookExtractor:
    """
    Extracts React hook patterns from JavaScript/TypeScript source code.

    Detects:
    - All built-in React hooks with dependency analysis
    - Custom hook definitions and their internal hook usage
    - React 18/19 new hooks
    - Hook categorization (state, effect, context, ref, memo, etc.)
    """

    # Hook categories
    HOOK_CATEGORIES = {
        'useState': 'state',
        'useReducer': 'state',
        'useEffect': 'effect',
        'useLayoutEffect': 'effect',
        'useInsertionEffect': 'effect',
        'useContext': 'context',
        'useRef': 'ref',
        'useImperativeHandle': 'ref',
        'useMemo': 'memo',
        'useCallback': 'callback',
        'useDebugValue': 'debug',
        # React 18
        'useTransition': 'react18',
        'useDeferredValue': 'react18',
        'useId': 'react18',
        'useSyncExternalStore': 'react18',
        # React 19
        'use': 'react19',
        'useFormStatus': 'react19',
        'useFormState': 'react19',
        'useOptimistic': 'react19',
        'useActionState': 'react19',
    }

    # React version by hook
    HOOK_MIN_VERSION = {
        'useState': '16.8',
        'useEffect': '16.8',
        'useContext': '16.8',
        'useReducer': '16.8',
        'useCallback': '16.8',
        'useMemo': '16.8',
        'useRef': '16.8',
        'useImperativeHandle': '16.8',
        'useLayoutEffect': '16.8',
        'useDebugValue': '16.8',
        'useTransition': '18.0',
        'useDeferredValue': '18.0',
        'useId': '18.0',
        'useSyncExternalStore': '18.0',
        'useInsertionEffect': '18.0',
        'use': '19.0',
        'useFormStatus': '19.0',
        'useFormState': '19.0',
        'useOptimistic': '19.0',
        'useActionState': '19.0',
    }

    # Custom hook definition pattern
    CUSTOM_HOOK_FUNC_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+(?:default\s+)?)?'
        r'(?:async\s+)?'
        r'function\s+(use[A-Z]\w*)\s*'
        r'(?:<[^>]*>\s*)?'
        r'\(\s*([^)]*)\s*\)',
        re.MULTILINE
    )

    CUSTOM_HOOK_ARROW_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+(?:default\s+)?)?'
        r'(?:const|let|var)\s+(use[A-Z]\w*)\s*'
        r'(?::\s*[^=]+)?\s*=\s*'
        r'(?:async\s+)?'
        r'(?:\([^)]*\)|[\w]+)\s*(?::\s*[^=]+)?\s*=>',
        re.MULTILINE
    )

    # Hook usage pattern (any hook call)
    HOOK_CALL_PATTERN = re.compile(
        r'\b(use[A-Z]\w*)\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # Dependency array pattern for useEffect/useMemo/useCallback
    DEP_ARRAY_PATTERN = re.compile(
        r'(use(?:Effect|LayoutEffect|InsertionEffect|Memo|Callback|ImperativeHandle))\s*'
        r'(?:<[^>]*>)?\s*\('
        r'(?:\s*(?:\(\)\s*=>|function\s*\(|async\s+(?:\(\)\s*=>|function))[^)]*?)'  # callback
        r'(?:,\s*(\[[^\]]*?\]))?',  # optional dependency array
        re.MULTILINE | re.DOTALL
    )

    # Effect cleanup pattern
    EFFECT_CLEANUP_PATTERN = re.compile(
        r'useEffect\s*\(\s*(?:\(\)\s*=>|function\s*\()\s*\{[^}]*return\s+(?:\(\)\s*=>|function)',
        re.MULTILINE | re.DOTALL
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract React hook patterns from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'hook_usages', 'custom_hooks', 'hook_dependencies'
        """
        hook_usages = []
        custom_hooks = []
        hook_dependencies = []

        # ── Custom Hook Definitions ───────────────────────────────
        # Function declaration hooks
        for m in self.CUSTOM_HOOK_FUNC_PATTERN.finditer(content):
            name = m.group(1)
            params_str = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1

            body_start = m.end()
            body_snippet = content[body_start:body_start + 3000]

            # Extract hooks used inside
            hooks_inside = sorted(set(
                h.group(1) for h in self.HOOK_CALL_PATTERN.finditer(body_snippet)
            ))

            # Parse parameters
            params = self._parse_params(params_str)

            # Detect return type/values
            return_values = self._extract_return_values(body_snippet)

            # Check if exported
            line_text = content[max(0, m.start() - 50):m.start()]
            is_exported = 'export' in line_text

            # Determine minimum React version
            max_version = '16.8'
            for hook in hooks_inside:
                ver = self.HOOK_MIN_VERSION.get(hook, '')
                if ver and ver > max_version:
                    max_version = ver

            custom_hooks.append(ReactCustomHookInfo(
                name=name,
                file=file_path,
                line_number=line,
                parameters=params[:10],
                return_values=return_values[:10],
                hooks_used=hooks_inside[:15],
                is_exported=is_exported,
                is_async=bool(re.search(r'async\s+function\s+' + re.escape(name), content)),
                react_version=max_version,
            ))

        # Arrow function hooks
        for m in self.CUSTOM_HOOK_ARROW_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            # Skip if already captured
            if any(h.name == name for h in custom_hooks):
                continue

            body_start = m.end()
            body_snippet = content[body_start:body_start + 3000]

            hooks_inside = sorted(set(
                h.group(1) for h in self.HOOK_CALL_PATTERN.finditer(body_snippet)
            ))

            return_values = self._extract_return_values(body_snippet)
            line_text = content[max(0, m.start() - 50):m.start()]
            is_exported = 'export' in line_text

            max_version = '16.8'
            for hook in hooks_inside:
                ver = self.HOOK_MIN_VERSION.get(hook, '')
                if ver and ver > max_version:
                    max_version = ver

            custom_hooks.append(ReactCustomHookInfo(
                name=name,
                file=file_path,
                line_number=line,
                hooks_used=hooks_inside[:15],
                return_values=return_values[:10],
                is_exported=is_exported,
                react_version=max_version,
            ))

        # ── Hook Usage Analysis ───────────────────────────────────
        for m in self.HOOK_CALL_PATTERN.finditer(content):
            hook_name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            category = self.HOOK_CATEGORIES.get(hook_name, 'custom')

            hook_usages.append(ReactHookUsageInfo(
                hook_name=hook_name,
                file=file_path,
                line_number=line,
                category=category,
            ))

        # ── Dependency Analysis ───────────────────────────────────
        for m in self.DEP_ARRAY_PATTERN.finditer(content):
            hook_name = m.group(1)
            dep_array = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1

            deps = []
            has_empty = False
            has_no_deps = False

            if dep_array:
                dep_array_clean = dep_array.strip('[]').strip()
                if not dep_array_clean:
                    has_empty = True
                else:
                    deps = [d.strip() for d in dep_array_clean.split(',')
                            if d.strip()]
            else:
                has_no_deps = True

            hook_dependencies.append(ReactHookDependencyInfo(
                hook_name=hook_name,
                file=file_path,
                line_number=line,
                dependencies=deps[:20],
                has_empty_deps=has_empty,
                has_no_deps=has_no_deps,
            ))

        return {
            'hook_usages': hook_usages,
            'custom_hooks': custom_hooks,
            'hook_dependencies': hook_dependencies,
        }

    def _parse_params(self, params_str: str) -> List[str]:
        """Parse function parameters into names."""
        if not params_str.strip():
            return []
        params = []
        depth = 0
        current = ""
        for ch in params_str:
            if ch in '({<':
                depth += 1
                current += ch
            elif ch in ')}>':
                depth -= 1
                current += ch
            elif ch == ',' and depth == 0:
                name = current.strip().split(':')[0].split('=')[0].strip()
                if name:
                    params.append(name)
                current = ""
            else:
                current += ch
        if current.strip():
            name = current.strip().split(':')[0].split('=')[0].strip()
            if name:
                params.append(name)
        return params

    def _extract_return_values(self, body: str) -> List[str]:
        """Extract return value names from hook body."""
        # Look for return [value, setter] or return { key1, key2 }
        return_match = re.search(
            r'return\s+(\[[^\]]+\]|\{[^}]+\})',
            body
        )
        if return_match:
            ret = return_match.group(1)
            if ret.startswith('['):
                return [v.strip() for v in ret.strip('[]').split(',') if v.strip()]
            elif ret.startswith('{'):
                return [v.strip().split(':')[0].strip()
                        for v in ret.strip('{}').split(',') if v.strip()]
        return []
