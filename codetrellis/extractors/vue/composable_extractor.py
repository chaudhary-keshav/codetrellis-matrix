"""
Vue.js Composable Extractor for CodeTrellis

Extracts Composition API composable patterns from Vue.js source code:
- Custom composables (use* functions)
- Reactive state (ref, reactive, shallowRef, shallowReactive, toRef, toRefs)
- Computed properties (computed, writableComputed)
- Watchers (watch, watchEffect, watchPostEffect, watchSyncEffect)
- Lifecycle hooks (onMounted, onUpdated, onUnmounted, onBeforeMount, etc.)
- Dependency injection (provide, inject)
- Template refs (useTemplateRef - Vue 3.5+)
- Next tick (nextTick)

Supports Vue 2 (via @vue/composition-api) through Vue 3.5+.

Part of CodeTrellis v4.34 - Vue.js Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class VueRefInfo:
    """Information about a Vue reactive reference."""
    name: str
    ref_type: str = "ref"  # ref, shallowRef, reactive, shallowReactive, toRef, toRefs, computed
    type_param: str = ""  # TypeScript generic type
    initial_value: Optional[str] = None
    is_readonly: bool = False
    line_number: int = 0


@dataclass
class VueComputedInfo:
    """Information about a Vue computed property."""
    name: str
    is_writable: bool = False  # computed({ get, set })
    dependencies: List[str] = field(default_factory=list)
    type_param: str = ""
    line_number: int = 0


@dataclass
class VueWatcherInfo:
    """Information about a Vue watcher."""
    kind: str = "watch"  # watch, watchEffect, watchPostEffect, watchSyncEffect
    source: str = ""  # watched source expression
    is_immediate: bool = False
    is_deep: bool = False
    line_number: int = 0


@dataclass
class VueLifecycleHookInfo:
    """Information about a Vue lifecycle hook."""
    hook_name: str  # onMounted, onUpdated, onUnmounted, etc.
    line_number: int = 0


@dataclass
class VueComposableInfo:
    """Information about a custom Vue composable function."""
    name: str
    file: str = ""
    line_number: int = 0
    parameters: List[str] = field(default_factory=list)
    return_type: str = ""
    is_exported: bool = False

    # State created
    refs_created: List[str] = field(default_factory=list)
    computeds_created: List[str] = field(default_factory=list)
    watchers_count: int = 0

    # Lifecycle hooks used
    lifecycle_hooks: List[str] = field(default_factory=list)

    # Other composables called
    composables_called: List[str] = field(default_factory=list)


class VueComposableExtractor:
    """
    Extracts Vue Composition API patterns from source code.

    Detects:
    - Custom composable definitions (export function use*())
    - ref/reactive/shallowRef/shallowReactive/toRef/toRefs
    - computed (read-only and writable)
    - watch/watchEffect/watchPostEffect/watchSyncEffect
    - Lifecycle hooks (onMounted, onBeforeMount, onUpdated, etc.)
    - provide/inject in composition context
    - useTemplateRef (Vue 3.5+)
    """

    # Composable definition
    COMPOSABLE_DEF_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+)?(?:(?:async\s+)?function\s+(use[A-Z]\w*)|'
        r'(?:export\s+)?const\s+(use[A-Z]\w*)\s*=\s*(?:async\s*)?\()',
        re.MULTILINE
    )

    # Ref patterns
    REF_PATTERN = re.compile(
        r'(?:const|let)\s+(\w+)\s*=\s*(ref|shallowRef|customRef)\s*(?:<([^>]+)>)?\s*\(([^)]*)\)',
        re.MULTILINE
    )

    REACTIVE_PATTERN = re.compile(
        r'(?:const|let)\s+(\w+)\s*=\s*(reactive|shallowReactive)\s*(?:<([^>]+)>)?\s*\(',
        re.MULTILINE
    )

    TO_REF_PATTERN = re.compile(
        r'(?:const|let)\s+(\w+)\s*=\s*(toRef|toRefs)\s*\((\w+)',
        re.MULTILINE
    )

    READONLY_PATTERN = re.compile(
        r'(?:const|let)\s+(\w+)\s*=\s*readonly\s*\((\w+)\)',
        re.MULTILINE
    )

    # Computed patterns
    COMPUTED_PATTERN = re.compile(
        r'(?:const|let)\s+(\w+)\s*=\s*computed\s*(?:<([^>]+)>)?\s*\(',
        re.MULTILINE
    )

    # Watch patterns
    WATCH_PATTERN = re.compile(
        r'\b(watch|watchEffect|watchPostEffect|watchSyncEffect)\s*\(\s*'
        r'(?:(?:\[\s*)?(\w+(?:\s*,\s*\w+)*)\s*\]?\s*,)?',
        re.MULTILINE
    )

    # Lifecycle hooks
    LIFECYCLE_PATTERN = re.compile(
        r'\b(onMounted|onUpdated|onUnmounted|onBeforeMount|onBeforeUpdate|'
        r'onBeforeUnmount|onActivated|onDeactivated|onErrorCaptured|'
        r'onRenderTracked|onRenderTriggered|onServerPrefetch)\s*\(',
        re.MULTILINE
    )

    # useTemplateRef (Vue 3.5+)
    TEMPLATE_REF_PATTERN = re.compile(
        r'(?:const|let)\s+(\w+)\s*=\s*useTemplateRef\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
        re.MULTILINE
    )

    # Provide/Inject in composition
    PROVIDE_PATTERN = re.compile(
        r'provide\s*\(\s*(?:[\'"]([^\'"]+)[\'"]|(\w+))\s*,',
        re.MULTILINE
    )

    INJECT_PATTERN = re.compile(
        r'inject\s*\(\s*(?:[\'"]([^\'"]+)[\'"]|(\w+))',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Composition API patterns from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'composables', 'refs', 'computeds', 'watchers',
                       'lifecycle_hooks', 'provides', 'injects'
        """
        result: Dict[str, Any] = {
            'composables': [],
            'refs': [],
            'computeds': [],
            'watchers': [],
            'lifecycle_hooks': [],
        }

        # Extract composable definitions
        for m in self.COMPOSABLE_DEF_PATTERN.finditer(content):
            name = m.group(1) or m.group(2)
            line = content[:m.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, m.start() - 20):m.start() + 10]

            composable = VueComposableInfo(
                name=name,
                file=file_path,
                line_number=line,
                is_exported=is_exported,
            )

            # Analyze composable body for internal patterns
            body_start = m.end()
            # Simple heuristic: find the composable body
            depth = 0
            body_end = body_start
            for i in range(body_start, min(body_start + 5000, len(content))):
                if content[i] in '({':
                    depth += 1
                elif content[i] in ')}':
                    depth -= 1
                    if depth <= 0:
                        body_end = i
                        break

            body = content[body_start:body_end]

            # Refs in body
            composable.refs_created = re.findall(
                r'(?:const|let)\s+(\w+)\s*=\s*(?:ref|shallowRef|reactive|shallowReactive)\s*[<(]', body
            )

            # Computeds in body
            composable.computeds_created = re.findall(
                r'(?:const|let)\s+(\w+)\s*=\s*computed\s*[<(]', body
            )

            # Watchers
            composable.watchers_count = len(re.findall(
                r'\b(?:watch|watchEffect|watchPostEffect|watchSyncEffect)\s*\(', body
            ))

            # Lifecycle hooks
            composable.lifecycle_hooks = re.findall(
                r'\b(onMounted|onUpdated|onUnmounted|onBeforeMount|onBeforeUpdate|'
                r'onBeforeUnmount|onActivated|onDeactivated|onErrorCaptured)\s*\(', body
            )

            # Composables called
            composable.composables_called = list(set(
                re.findall(r'\b(use[A-Z]\w+)\s*\(', body)
            ) - {name})

            # Parameters
            params_match = re.search(r'\(\s*([^)]*)\s*\)', content[m.start():m.start() + 200])
            if params_match:
                params = params_match.group(1)
                composable.parameters = [p.strip().split(':')[0].strip()
                                          for p in params.split(',') if p.strip()]

            result['composables'].append(composable)

        # Extract all refs
        for m in self.REF_PATTERN.finditer(content):
            result['refs'].append(VueRefInfo(
                name=m.group(1),
                ref_type=m.group(2),
                type_param=m.group(3) or "",
                initial_value=m.group(4).strip() if m.group(4).strip() else None,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        for m in self.REACTIVE_PATTERN.finditer(content):
            result['refs'].append(VueRefInfo(
                name=m.group(1),
                ref_type=m.group(2),
                type_param=m.group(3) or "",
                line_number=content[:m.start()].count('\n') + 1,
            ))

        for m in self.TO_REF_PATTERN.finditer(content):
            result['refs'].append(VueRefInfo(
                name=m.group(1),
                ref_type=m.group(2),
                line_number=content[:m.start()].count('\n') + 1,
            ))

        for m in self.READONLY_PATTERN.finditer(content):
            result['refs'].append(VueRefInfo(
                name=m.group(1),
                ref_type="readonly",
                is_readonly=True,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Extract computed
        for m in self.COMPUTED_PATTERN.finditer(content):
            # Check if writable (computed({ get() {}, set() {} }))
            after = content[m.end():m.end() + 100]
            is_writable = bool(re.search(r'\{\s*get\s*\(', after))
            result['computeds'].append(VueComputedInfo(
                name=m.group(1),
                is_writable=is_writable,
                type_param=m.group(2) or "",
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Extract watchers
        for m in self.WATCH_PATTERN.finditer(content):
            kind = m.group(1)
            source = m.group(2) or ""
            after = content[m.end():m.end() + 200]
            is_immediate = bool(re.search(r'immediate\s*:\s*true', after))
            is_deep = bool(re.search(r'deep\s*:\s*true', after))
            result['watchers'].append(VueWatcherInfo(
                kind=kind,
                source=source.strip(),
                is_immediate=is_immediate,
                is_deep=is_deep,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Extract lifecycle hooks
        for m in self.LIFECYCLE_PATTERN.finditer(content):
            result['lifecycle_hooks'].append(VueLifecycleHookInfo(
                hook_name=m.group(1),
                line_number=content[:m.start()].count('\n') + 1,
            ))

        return result
