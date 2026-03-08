"""
Preact Component Extractor for CodeTrellis

Extracts Preact component definitions from JavaScript/TypeScript source code:
- Functional components (arrow functions, function declarations)
- Class components (extends Component / extends PureComponent)
- Preact.memo wrapped components
- Preact.lazy / dynamic imports
- Preact.forwardRef components
- Fragment usage (<Fragment>, <>...</>)
- Error boundary components (componentDidCatch / getDerivedStateFromError)
- h() / createElement usage
- Server Components via preact-render-to-string
- Props interface/type detection
- Default props detection
- Display name detection
- Preact/compat compatibility mode detection

Supports Preact 8.x through 10.19+:
- Preact 8.x: h(), Component, linked state, preact-compat
- Preact X (10.x): hooks (via preact/hooks), createContext, Fragment
- Preact 10.5+: useId, useErrorBoundary
- Preact 10.11+: Signals integration via @preact/signals

Part of CodeTrellis v4.64 - Preact Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class PreactComponentInfo:
    """Information about a Preact functional component definition."""
    name: str
    file: str = ""
    line_number: int = 0
    component_type: str = "functional"  # functional, class, forwardRef, memo, lazy
    props_type: str = ""  # Name of props interface/type
    props_fields: List[str] = field(default_factory=list)
    hooks_used: List[str] = field(default_factory=list)
    signals_used: List[str] = field(default_factory=list)
    is_exported: bool = False
    is_default_export: bool = False
    is_compat_mode: bool = False  # Uses preact/compat
    has_display_name: bool = False
    has_default_props: bool = False
    has_jsx: bool = True
    uses_h_function: bool = False  # Uses h() instead of JSX
    children_type: str = ""  # VNode, ComponentChildren, etc.
    render_returns: str = ""


@dataclass
class PreactClassComponentInfo:
    """Information about a Preact class component."""
    name: str
    file: str = ""
    line_number: int = 0
    superclass: str = ""  # Component, PureComponent
    props_type: str = ""
    state_type: str = ""
    lifecycle_methods: List[str] = field(default_factory=list)
    is_exported: bool = False
    is_default_export: bool = False
    has_error_boundary: bool = False
    has_linked_state: bool = False  # Preact 8.x linkState


@dataclass
class PreactMemoInfo:
    """Information about a memo wrapped component."""
    name: str
    file: str = ""
    line_number: int = 0
    has_custom_comparison: bool = False
    wrapped_component: str = ""
    is_exported: bool = False


@dataclass
class PreactLazyInfo:
    """Information about a lazy loaded component."""
    name: str
    file: str = ""
    line_number: int = 0
    import_path: str = ""
    is_exported: bool = False


@dataclass
class PreactForwardRefInfo:
    """Information about a forwardRef component."""
    name: str
    file: str = ""
    line_number: int = 0
    ref_type: str = ""
    props_type: str = ""
    is_exported: bool = False


@dataclass
class PreactErrorBoundaryInfo:
    """Information about an error boundary component."""
    name: str
    file: str = ""
    line_number: int = 0
    has_fallback_ui: bool = False
    has_error_logging: bool = False
    has_reset_handler: bool = False
    is_exported: bool = False
    uses_hook: bool = False  # useErrorBoundary hook


class PreactComponentExtractor:
    """
    Extracts Preact component definitions from source code.

    Detects:
    - Functional components (arrow + function declaration)
    - Class components (Component / PureComponent)
    - memo, lazy, forwardRef wrappers
    - ErrorBoundary (componentDidCatch, getDerivedStateFromError, useErrorBoundary)
    - h() / createElement usage
    - Props type/interface detection
    - Preact/compat compatibility
    """

    # Functional component patterns
    # export function ComponentName({ prop1, prop2 }: Props) {
    FUNC_COMPONENT_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+(?:default\s+)?)?'
        r'(?:async\s+)?'
        r'function\s+([A-Z]\w*)\s*'
        r'(?:<[^>]*>)?\s*\('
        r'([^)]*)'
        r'\)',
        re.MULTILINE
    )

    # export const ComponentName = ({ prop }) => { ... }
    ARROW_COMPONENT_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+(?:default\s+)?)?'
        r'(?:const|let|var)\s+([A-Z]\w*)\s*'
        r'(?::\s*(?:FC|FunctionComponent|FunctionalComponent|VFC|'
        r'JSX\.Element|ComponentType|PreactComponent)\s*'
        r'(?:<[^>]*>)?\s*)?'
        r'=\s*(?:async\s+)?'
        r'(?:\([^)]*\)|[\w]+)\s*(?::\s*[^=]+)?\s*=>',
        re.MULTILINE
    )

    # Class component: class X extends Component<Props, State>
    CLASS_COMPONENT_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+(?:default\s+)?)?'
        r'class\s+(\w+)\s+'
        r'extends\s+'
        r'(?:Preact\.)?(?:Component|PureComponent)'
        r'(?:\s*<\s*([^>]*)\s*>)?',
        re.MULTILINE
    )

    # memo() wrapper
    MEMO_PATTERN = re.compile(
        r'(?:export\s+(?:default\s+)?)?'
        r'(?:const|let|var)\s+(\w+)\s*=\s*'
        r'(?:memo|Preact\.memo)\s*\(\s*'
        r'(?:(\w+)|(?:function|\())',
        re.MULTILINE
    )

    # lazy() wrapper
    LAZY_PATTERN = re.compile(
        r'(?:export\s+(?:default\s+)?)?'
        r'(?:const|let|var)\s+(\w+)\s*=\s*'
        r'(?:lazy|Preact\.lazy)\s*\(\s*\(\)\s*=>\s*'
        r'import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
        re.MULTILINE
    )

    # forwardRef() wrapper
    FORWARD_REF_PATTERN = re.compile(
        r'(?:export\s+(?:default\s+)?)?'
        r'(?:const|let|var)\s+(\w+)\s*=\s*'
        r'(?:forwardRef|Preact\.forwardRef)\s*'
        r'(?:<\s*([^>]*)\s*>)?\s*\(',
        re.MULTILINE
    )

    # h() function usage (Preact's virtual DOM)
    H_FUNCTION_PATTERN = re.compile(
        r'\bh\s*\(\s*[\'"]?\w+[\'"]?\s*,',
        re.MULTILINE
    )

    # Display name pattern
    DISPLAY_NAME_PATTERN = re.compile(
        r'(\w+)\.displayName\s*=',
        re.MULTILINE
    )

    # Default props pattern
    DEFAULT_PROPS_PATTERN = re.compile(
        r'(\w+)\.defaultProps\s*=',
        re.MULTILINE
    )

    # Lifecycle methods for class components
    LIFECYCLE_METHODS = [
        'componentDidMount', 'componentDidUpdate', 'componentWillUnmount',
        'componentDidCatch', 'getDerivedStateFromError', 'getDerivedStateFromProps',
        'shouldComponentUpdate', 'getSnapshotBeforeUpdate',
        'componentWillMount', 'componentWillReceiveProps', 'componentWillUpdate',
        'render',
    ]

    # Preact 8.x linked state
    LINKED_STATE_PATTERN = re.compile(
        r'this\.linkState\s*\(',
        re.MULTILINE
    )

    # useErrorBoundary hook
    USE_ERROR_BOUNDARY_PATTERN = re.compile(
        r'useErrorBoundary\s*\(',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Preact component definitions from source code."""
        components: List[PreactComponentInfo] = []
        class_components: List[PreactClassComponentInfo] = []
        memos: List[PreactMemoInfo] = []
        lazies: List[PreactLazyInfo] = []
        forward_refs: List[PreactForwardRefInfo] = []
        error_boundaries: List[PreactErrorBoundaryInfo] = []

        is_compat = 'preact/compat' in content or 'preact-compat' in content
        uses_h = bool(self.H_FUNCTION_PATTERN.search(content))
        display_names = set(m.group(1) for m in self.DISPLAY_NAME_PATTERN.finditer(content))
        default_props = set(m.group(1) for m in self.DEFAULT_PROPS_PATTERN.finditer(content))

        # ── Functional components (function declaration) ──────────
        for m in self.FUNC_COMPONENT_PATTERN.finditer(content):
            name = m.group(1)
            params = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 50):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix
            is_default = 'default' in prefix

            # Extract props type from params
            props_type = ""
            props_fields = []
            type_match = re.search(r':\s*(\w+)', params)
            if type_match:
                props_type = type_match.group(1)
            destr_match = re.search(r'\{\s*([^}]+)\}', params)
            if destr_match:
                props_fields = [p.strip().split('=')[0].split(':')[0].strip()
                                for p in destr_match.group(1).split(',')
                                if p.strip()]

            # Check body for hooks & signals
            body_end = min(len(content), m.end() + 3000)
            body = content[m.end():body_end]
            hooks_used = list(set(re.findall(r'\b(use[A-Z]\w*)\b', body)))
            signals_used = list(set(re.findall(r'\b(signal|computed|effect|useSignal|useComputed)\b', body)))

            comp = PreactComponentInfo(
                name=name,
                file=file_path,
                line_number=line,
                component_type="functional",
                props_type=props_type,
                props_fields=props_fields[:10],
                hooks_used=hooks_used[:15],
                signals_used=signals_used[:10],
                is_exported=is_exported,
                is_default_export=is_default,
                is_compat_mode=is_compat,
                has_display_name=name in display_names,
                has_default_props=name in default_props,
                uses_h_function=uses_h,
            )
            components.append(comp)

        # ── Functional components (arrow function) ────────────────
        for m in self.ARROW_COMPONENT_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 50):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix
            is_default = 'default' in prefix

            body_end = min(len(content), m.end() + 3000)
            body = content[m.end():body_end]
            hooks_used = list(set(re.findall(r'\b(use[A-Z]\w*)\b', body)))
            signals_used = list(set(re.findall(r'\b(signal|computed|effect|useSignal|useComputed)\b', body)))

            comp = PreactComponentInfo(
                name=name,
                file=file_path,
                line_number=line,
                component_type="functional",
                props_type="",
                hooks_used=hooks_used[:15],
                signals_used=signals_used[:10],
                is_exported=is_exported,
                is_default_export=is_default,
                is_compat_mode=is_compat,
                has_display_name=name in display_names,
                has_default_props=name in default_props,
                uses_h_function=uses_h,
            )
            components.append(comp)

        # ── Class components ──────────────────────────────────────
        for m in self.CLASS_COMPONENT_PATTERN.finditer(content):
            name = m.group(1)
            generics = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 50):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix
            is_default = 'default' in prefix

            # Parse generics for Props, State types
            props_type = ""
            state_type = ""
            if generics:
                parts = [p.strip() for p in generics.split(',')]
                if parts:
                    props_type = parts[0]
                if len(parts) > 1:
                    state_type = parts[1]

            # Detect lifecycle methods
            body_end = min(len(content), m.end() + 5000)
            body = content[m.end():body_end]
            lifecycle = [lm for lm in self.LIFECYCLE_METHODS
                         if re.search(rf'\b{lm}\s*\(', body)]

            has_linked_state = bool(self.LINKED_STATE_PATTERN.search(body))
            has_error_boundary = 'componentDidCatch' in lifecycle or 'getDerivedStateFromError' in lifecycle

            # Determine superclass
            super_match = re.search(r'extends\s+(?:Preact\.)?(Component|PureComponent)', m.group(0))
            superclass = super_match.group(1) if super_match else "Component"

            cls = PreactClassComponentInfo(
                name=name,
                file=file_path,
                line_number=line,
                superclass=superclass,
                props_type=props_type,
                state_type=state_type,
                lifecycle_methods=lifecycle,
                is_exported=is_exported,
                is_default_export=is_default,
                has_error_boundary=has_error_boundary,
                has_linked_state=has_linked_state,
            )
            class_components.append(cls)

            # Also add as error boundary if applicable
            if has_error_boundary:
                error_boundaries.append(PreactErrorBoundaryInfo(
                    name=name,
                    file=file_path,
                    line_number=line,
                    has_fallback_ui='fallback' in body.lower() or 'error' in body.lower(),
                    has_error_logging='console' in body or 'log' in body,
                    has_reset_handler='reset' in body.lower(),
                    is_exported=is_exported,
                    uses_hook=False,
                ))

        # ── useErrorBoundary hook usage ───────────────────────────
        for m in self.USE_ERROR_BOUNDARY_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            # Find enclosing component
            comp_name = self._find_enclosing_component(content, m.start())
            error_boundaries.append(PreactErrorBoundaryInfo(
                name=comp_name or "anonymous",
                file=file_path,
                line_number=line,
                has_fallback_ui=True,
                is_exported=False,
                uses_hook=True,
            ))

        # ── memo() ────────────────────────────────────────────────
        for m in self.MEMO_PATTERN.finditer(content):
            name = m.group(1)
            wrapped = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1
            prefix = content[max(0, m.start() - 50):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix

            # Check for custom comparison function
            after = content[m.end():min(len(content), m.end() + 200)]
            has_custom = bool(re.search(r',\s*(?:function|\()', after))

            memos.append(PreactMemoInfo(
                name=name,
                file=file_path,
                line_number=line,
                has_custom_comparison=has_custom,
                wrapped_component=wrapped,
                is_exported=is_exported,
            ))

        # ── lazy() ────────────────────────────────────────────────
        for m in self.LAZY_PATTERN.finditer(content):
            name = m.group(1)
            import_path = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1
            prefix = content[max(0, m.start() - 50):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix

            lazies.append(PreactLazyInfo(
                name=name,
                file=file_path,
                line_number=line,
                import_path=import_path,
                is_exported=is_exported,
            ))

        # ── forwardRef() ──────────────────────────────────────────
        for m in self.FORWARD_REF_PATTERN.finditer(content):
            name = m.group(1)
            generics = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1
            prefix = content[max(0, m.start() - 50):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix

            ref_type = ""
            props_type = ""
            if generics:
                parts = [p.strip() for p in generics.split(',')]
                if parts:
                    ref_type = parts[0]
                if len(parts) > 1:
                    props_type = parts[1]

            forward_refs.append(PreactForwardRefInfo(
                name=name,
                file=file_path,
                line_number=line,
                ref_type=ref_type,
                props_type=props_type,
                is_exported=is_exported,
            ))

        return {
            'components': components,
            'class_components': class_components,
            'memos': memos,
            'lazies': lazies,
            'forward_refs': forward_refs,
            'error_boundaries': error_boundaries,
        }

    def _find_enclosing_component(self, content: str, pos: int) -> Optional[str]:
        """Find the component name that encloses the given position."""
        # Look backwards for function/const declaration
        before = content[max(0, pos - 2000):pos]
        # Try function declaration
        func_match = re.findall(r'function\s+([A-Z]\w*)\s*\(', before)
        if func_match:
            return func_match[-1]
        # Try arrow function
        arrow_match = re.findall(r'(?:const|let|var)\s+([A-Z]\w*)\s*=', before)
        if arrow_match:
            return arrow_match[-1]
        return None
