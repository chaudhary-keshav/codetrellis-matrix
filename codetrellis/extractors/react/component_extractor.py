"""
React Component Extractor for CodeTrellis

Extracts React component definitions from JavaScript/TypeScript source code:
- Functional components (arrow functions, function declarations)
- Class components (extends React.Component / PureComponent)
- Higher-Order Components (HOC patterns)
- React.forwardRef components
- React.memo wrapped components
- React.lazy / dynamic imports
- ErrorBoundary components (componentDidCatch / getDerivedStateFromError)
- Server Components (React 18+ "use server" / "use client" directives)
- Provider components (wrapping Context.Provider)
- Suspense boundaries
- Props interface/type detection
- Default props detection
- Display name detection

Supports React 0.14 through React 19+:
- React 0.14: Stateless functional components
- React 16.3: React.forwardRef, React.createContext
- React 16.6: React.memo, React.lazy, React.Suspense
- React 16.8: Hooks-based functional components
- React 18: Server Components, Suspense for data fetching, useId
- React 19: use() hook, useFormStatus, useOptimistic, Actions

Part of CodeTrellis v4.32 - React Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class ReactComponentInfo:
    """Information about a React component definition."""
    name: str
    file: str = ""
    line_number: int = 0
    component_type: str = "functional"  # functional, class, forwardRef, memo, lazy
    props_type: str = ""  # Name of props interface/type
    props_fields: List[str] = field(default_factory=list)  # Extracted prop names
    hooks_used: List[str] = field(default_factory=list)
    is_exported: bool = False
    is_default_export: bool = False
    is_server_component: bool = False  # "use server" directive
    is_client_component: bool = False  # "use client" directive
    is_async: bool = False  # async component (React 19 / Server Components)
    has_display_name: bool = False
    has_default_props: bool = False
    superclass: str = ""  # For class components
    render_returns: str = ""  # JSX element type returned
    children: List[str] = field(default_factory=list)  # Child components used
    state_variables: List[str] = field(default_factory=list)  # useState variables
    effects: List[str] = field(default_factory=list)  # useEffect dependency descriptions
    memoized_values: List[str] = field(default_factory=list)  # useMemo descriptions
    callbacks: List[str] = field(default_factory=list)  # useCallback descriptions
    refs: List[str] = field(default_factory=list)  # useRef variables
    context_consumed: List[str] = field(default_factory=list)  # useContext targets


@dataclass
class ReactHOCInfo:
    """Information about a Higher-Order Component."""
    name: str
    file: str = ""
    line_number: int = 0
    wrapped_component: str = ""
    hoc_name: str = ""  # e.g., withRouter, connect, withAuth
    is_exported: bool = False
    added_props: List[str] = field(default_factory=list)


@dataclass
class ReactForwardRefInfo:
    """Information about a React.forwardRef component."""
    name: str
    file: str = ""
    line_number: int = 0
    ref_type: str = ""  # Type of the forwarded ref
    props_type: str = ""
    is_exported: bool = False


@dataclass
class ReactMemoInfo:
    """Information about a React.memo wrapped component."""
    name: str
    file: str = ""
    line_number: int = 0
    has_custom_comparison: bool = False
    wrapped_component: str = ""
    is_exported: bool = False


@dataclass
class ReactLazyInfo:
    """Information about a React.lazy loaded component."""
    name: str
    file: str = ""
    line_number: int = 0
    import_path: str = ""
    is_exported: bool = False


@dataclass
class ReactErrorBoundaryInfo:
    """Information about an ErrorBoundary component."""
    name: str
    file: str = ""
    line_number: int = 0
    has_fallback_ui: bool = False
    has_error_logging: bool = False
    has_reset_handler: bool = False
    is_exported: bool = False


@dataclass
class ReactProviderInfo:
    """Information about a Provider component or composition."""
    name: str
    file: str = ""
    line_number: int = 0
    context_name: str = ""
    is_exported: bool = False
    provides_value_type: str = ""


class ReactComponentExtractor:
    """
    Extracts React component definitions from JavaScript/TypeScript source code.

    Detects:
    - Functional components (arrow + function declaration)
    - Class components (React.Component / PureComponent)
    - HOC patterns (withRouter, connect, compose)
    - React.forwardRef, React.memo, React.lazy
    - ErrorBoundary (componentDidCatch, getDerivedStateFromError)
    - Server/Client component directives
    - Provider wrapper components
    - Props type/interface detection
    """

    # Server/Client component directives (React 18/19)
    SERVER_DIRECTIVE = re.compile(r'^["\']use server["\'];?\s*$', re.MULTILINE)
    CLIENT_DIRECTIVE = re.compile(r'^["\']use client["\'];?\s*$', re.MULTILINE)

    # Functional component patterns
    # export function ComponentName({ prop1, prop2 }: Props) {
    FUNC_COMPONENT_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+(?:default\s+)?)?'
        r'(?:async\s+)?'
        r'function\s+([A-Z]\w*)\s*'
        r'(?:<[^>]*>\s*)?'  # generics
        r'\(\s*'
        r'(?:\{\s*([^}]*)\}\s*(?::\s*([\w.<>,\s|]+))?\s*)?'  # destructured props
        r'(?:(\w+)\s*(?::\s*([\w.<>,\s|]+))?\s*)?'  # named props parameter
        r'\)',
        re.MULTILINE
    )

    # Arrow function component
    # export const ComponentName: React.FC<Props> = ({ prop1 }) => {
    ARROW_COMPONENT_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+(?:default\s+)?)?'
        r'(?:const|let|var)\s+([A-Z]\w*)\s*'
        r'(?::\s*(?:React\.)?(?:FC|FunctionComponent|VFC|ComponentType|ForwardRefRenderFunction)\s*'
        r'(?:<\s*([^>]+?)\s*>)?\s*)?'  # Type annotation with generics
        r'=\s*'
        r'(?:React\.memo\s*\(\s*)?'  # Optional memo wrap
        r'(?:React\.forwardRef\s*(?:<[^>]+>\s*)?\(\s*)?'  # Optional forwardRef wrap
        r'(?:\(\s*(?:\{[^}]*\}|[\w,\s]*)\s*(?:,[^)]*?)?\)\s*=>|'  # Arrow with params
        r'(?:function\s*\([^)]*\)))',  # Function expression
        re.MULTILINE
    )

    # Class component
    CLASS_COMPONENT_PATTERN = re.compile(
        r'^[ \t]*(?:export\s+(?:default\s+)?)?'
        r'class\s+([A-Z]\w*)\s+'
        r'extends\s+(?:React\.)?(?:Component|PureComponent)'
        r'(?:<\s*([^>]+?)\s*>)?'  # Props/State generics
        r'\s*\{',
        re.MULTILINE
    )

    # HOC patterns
    # export default withRouter(connect(mapState)(MyComponent))
    HOC_PATTERN = re.compile(
        r'(?:export\s+default\s+)?'
        r'((?:with\w+|connect|compose|inject|observer|memo|styled)\s*\(\s*)'
        r'(?:(?:mapState|mapDispatch|\w+)\s*(?:,\s*\w+)*\s*\)\s*\(\s*)?'
        r'([A-Z]\w*)',
        re.MULTILINE
    )

    # React.forwardRef
    FORWARD_REF_PATTERN = re.compile(
        r'(?:export\s+(?:default\s+)?)?'
        r'(?:const|let|var)\s+([A-Z]\w*)\s*=\s*'
        r'(?:React\.)?forwardRef\s*'
        r'(?:<\s*([^>]+?)\s*>)?\s*\(',
        re.MULTILINE
    )

    # React.memo
    MEMO_PATTERN = re.compile(
        r'(?:export\s+(?:default\s+)?)?'
        r'(?:const|let|var)\s+([A-Z]\w*)\s*=\s*'
        r'(?:React\.)?memo\s*'
        r'(?:<\s*([^>]+?)\s*>)?\s*\(\s*'
        r'(?:([A-Z]\w*)|function|\()',
        re.MULTILINE
    )

    # React.lazy
    LAZY_PATTERN = re.compile(
        r'(?:export\s+(?:default\s+)?)?'
        r'(?:const|let|var)\s+([A-Z]\w*)\s*=\s*'
        r'(?:React\.)?lazy\s*\(\s*\(\)\s*=>\s*'
        r'import\s*\(\s*[\'"]([^\'"]+)[\'"]',
        re.MULTILINE
    )

    # ErrorBoundary detection
    ERROR_BOUNDARY_METHODS = re.compile(
        r'(?:componentDidCatch|getDerivedStateFromError|static\s+getDerivedStateFromError)',
        re.MULTILINE
    )

    # Provider component
    PROVIDER_PATTERN = re.compile(
        r'(?:export\s+(?:default\s+)?)?'
        r'(?:const|function)\s+([A-Z]\w*Provider)\s*',
        re.MULTILINE
    )

    # useState detection
    USE_STATE_PATTERN = re.compile(
        r'(?:const|let)\s+\[\s*(\w+)\s*,\s*set\w+\s*\]\s*=\s*use(?:State|Reducer)\s*'
        r'(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # useEffect detection
    USE_EFFECT_PATTERN = re.compile(
        r'use(?:Effect|LayoutEffect|InsertionEffect)\s*\(\s*(?:\(\)\s*=>|function)',
        re.MULTILINE
    )

    # useRef detection
    USE_REF_PATTERN = re.compile(
        r'(?:const|let)\s+(\w+)\s*=\s*useRef\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # useContext detection
    USE_CONTEXT_PATTERN = re.compile(
        r'(?:const|let)\s+\w+\s*=\s*useContext\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # useMemo detection
    USE_MEMO_PATTERN = re.compile(
        r'(?:const|let)\s+(\w+)\s*=\s*useMemo\s*\(',
        re.MULTILINE
    )

    # useCallback detection
    USE_CALLBACK_PATTERN = re.compile(
        r'(?:const|let)\s+(\w+)\s*=\s*useCallback\s*\(',
        re.MULTILINE
    )

    # Hook usage (any hook)
    HOOK_USAGE_PATTERN = re.compile(
        r'\buse[A-Z]\w*\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # Display name
    DISPLAY_NAME_PATTERN = re.compile(
        r'(\w+)\.displayName\s*=',
        re.MULTILINE
    )

    # Default props
    DEFAULT_PROPS_PATTERN = re.compile(
        r'(\w+)\.defaultProps\s*=',
        re.MULTILINE
    )

    # JSX child components used
    JSX_COMPONENT_USAGE = re.compile(
        r'<([A-Z]\w*)[\s/>]',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract React components from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'components', 'hocs', 'forward_refs', 'memos',
            'lazies', 'error_boundaries', 'providers'
        """
        # Detect server/client directives
        is_server = bool(self.SERVER_DIRECTIVE.search(content))
        is_client = bool(self.CLIENT_DIRECTIVE.search(content))

        # Check export lines for default
        export_default_lines = set()
        for m in re.finditer(r'^[ \t]*export\s+default\s+', content, re.MULTILINE):
            export_default_lines.add(content[:m.start()].count('\n') + 1)

        export_lines = set()
        for m in re.finditer(r'^[ \t]*export\s+(?!default)', content, re.MULTILINE):
            export_lines.add(content[:m.start()].count('\n') + 1)

        # Collect display names and default props
        display_names = set()
        for m in self.DISPLAY_NAME_PATTERN.finditer(content):
            display_names.add(m.group(1))

        default_props_set = set()
        for m in self.DEFAULT_PROPS_PATTERN.finditer(content):
            default_props_set.add(m.group(1))

        components = []
        hocs = []
        forward_refs = []
        memos = []
        lazies = []
        error_boundaries = []
        providers = []

        # ── Functional Components (function declarations) ─────────
        for m in self.FUNC_COMPONENT_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            # Check if it returns JSX (look at next ~50 lines)
            body_start = m.end()
            body_snippet = content[body_start:body_start + 3000]
            if not re.search(r'(?:return\s*\(?\s*<|<\w+[\s/>]|jsx|React\.createElement)', body_snippet):
                continue

            destructured_props = m.group(2) or ""
            props_type = m.group(3) or m.group(5) or ""
            named_param = m.group(4) or ""

            # Extract props from destructured
            prop_fields = []
            if destructured_props:
                prop_fields = [p.strip().split('=')[0].strip().split(':')[0].strip()
                               for p in destructured_props.split(',')
                               if p.strip() and not p.strip().startswith('...')]

            # Find hooks used in component body
            hooks = self._extract_hooks_in_body(body_snippet)
            state_vars = [m2.group(1) for m2 in self.USE_STATE_PATTERN.finditer(body_snippet)]
            refs = [m2.group(1) for m2 in self.USE_REF_PATTERN.finditer(body_snippet)]
            contexts = [m2.group(1) for m2 in self.USE_CONTEXT_PATTERN.finditer(body_snippet)]
            memoized = [m2.group(1) for m2 in self.USE_MEMO_PATTERN.finditer(body_snippet)]
            callbacks = [m2.group(1) for m2 in self.USE_CALLBACK_PATTERN.finditer(body_snippet)]

            # Find child components
            children = list(set(m2.group(1) for m2 in self.JSX_COMPONENT_USAGE.finditer(body_snippet)
                                if m2.group(1) != name))

            is_exported = line in export_lines or line in export_default_lines
            is_default = line in export_default_lines
            is_async_comp = bool(re.search(r'async\s+function\s+' + re.escape(name), content))

            comp = ReactComponentInfo(
                name=name,
                file=file_path,
                line_number=line,
                component_type="functional",
                props_type=props_type,
                props_fields=prop_fields[:20],
                hooks_used=hooks[:20],
                is_exported=is_exported,
                is_default_export=is_default,
                is_server_component=is_server,
                is_client_component=is_client,
                is_async=is_async_comp,
                has_display_name=name in display_names,
                has_default_props=name in default_props_set,
                children=children[:20],
                state_variables=state_vars[:10],
                refs=refs[:10],
                context_consumed=contexts[:10],
                memoized_values=memoized[:10],
                callbacks=callbacks[:10],
            )
            components.append(comp)

        # ── Arrow Function Components ─────────────────────────────
        for m in self.ARROW_COMPONENT_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            # Skip if already captured as a functional component
            if any(c.name == name for c in components):
                continue

            body_start = m.end()
            body_snippet = content[body_start:body_start + 3000]
            if not re.search(r'(?:return\s*\(?\s*<|<\w+[\s/>]|jsx|React\.createElement|\(?\s*<)', body_snippet):
                continue

            props_type = m.group(2) or ""
            hooks = self._extract_hooks_in_body(body_snippet)
            state_vars = [m2.group(1) for m2 in self.USE_STATE_PATTERN.finditer(body_snippet)]
            refs = [m2.group(1) for m2 in self.USE_REF_PATTERN.finditer(body_snippet)]
            contexts = [m2.group(1) for m2 in self.USE_CONTEXT_PATTERN.finditer(body_snippet)]
            children = list(set(m2.group(1) for m2 in self.JSX_COMPONENT_USAGE.finditer(body_snippet)
                                if m2.group(1) != name))

            is_exported = line in export_lines or line in export_default_lines
            is_default = line in export_default_lines

            comp = ReactComponentInfo(
                name=name,
                file=file_path,
                line_number=line,
                component_type="functional",
                props_type=props_type,
                hooks_used=hooks[:20],
                is_exported=is_exported,
                is_default_export=is_default,
                is_server_component=is_server,
                is_client_component=is_client,
                has_display_name=name in display_names,
                has_default_props=name in default_props_set,
                children=children[:20],
                state_variables=state_vars[:10],
                refs=refs[:10],
                context_consumed=contexts[:10],
            )
            components.append(comp)

        # ── Class Components ──────────────────────────────────────
        for m in self.CLASS_COMPONENT_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            generics = m.group(2) or ""

            body_start = m.end()
            body_snippet = content[body_start:body_start + 5000]

            # Check if it has render method
            if not re.search(r'render\s*\(', body_snippet):
                continue

            # Detect superclass
            superclass_match = re.search(
                r'extends\s+(?:React\.)?(Component|PureComponent)',
                content[m.start():m.end()])
            superclass = superclass_match.group(1) if superclass_match else "Component"

            # Check for error boundary methods
            is_error_boundary = bool(self.ERROR_BOUNDARY_METHODS.search(body_snippet))

            is_exported = line in export_lines or line in export_default_lines
            is_default = line in export_default_lines

            if is_error_boundary:
                eb = ReactErrorBoundaryInfo(
                    name=name,
                    file=file_path,
                    line_number=line,
                    has_fallback_ui=bool(re.search(r'fallback|errorComponent|ErrorFallback', body_snippet)),
                    has_error_logging=bool(re.search(r'console\.\w+|logger\.\w+|Sentry\.|errorService', body_snippet)),
                    has_reset_handler=bool(re.search(r'resetError|onReset|retry', body_snippet, re.IGNORECASE)),
                    is_exported=is_exported,
                )
                error_boundaries.append(eb)

            # Extract props type from generics
            props_type = ""
            if generics:
                parts = generics.split(',')
                if parts:
                    props_type = parts[0].strip()

            children = list(set(m2.group(1) for m2 in self.JSX_COMPONENT_USAGE.finditer(body_snippet)
                                if m2.group(1) != name))

            comp = ReactComponentInfo(
                name=name,
                file=file_path,
                line_number=line,
                component_type="class",
                props_type=props_type,
                is_exported=is_exported,
                is_default_export=is_default,
                is_server_component=is_server,
                is_client_component=is_client,
                has_display_name=name in display_names,
                has_default_props=name in default_props_set,
                superclass=superclass,
                children=children[:20],
            )
            components.append(comp)

        # ── React.forwardRef ──────────────────────────────────────
        for m in self.FORWARD_REF_PATTERN.finditer(content):
            name = m.group(1)
            generics = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1

            ref_type = ""
            props_type = ""
            if generics:
                parts = [p.strip() for p in generics.split(',')]
                if len(parts) >= 1:
                    ref_type = parts[0]
                if len(parts) >= 2:
                    props_type = parts[1]

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            fr = ReactForwardRefInfo(
                name=name,
                file=file_path,
                line_number=line,
                ref_type=ref_type,
                props_type=props_type,
                is_exported=is_exported,
            )
            forward_refs.append(fr)

        # ── React.memo ────────────────────────────────────────────
        for m in self.MEMO_PATTERN.finditer(content):
            name = m.group(1)
            wrapped = m.group(3) or ""
            line = content[:m.start()].count('\n') + 1

            # Check for custom comparison function
            body_after = content[m.end():m.end() + 500]
            has_custom = bool(re.search(r',\s*(?:function|\()', body_after))

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            memo = ReactMemoInfo(
                name=name,
                file=file_path,
                line_number=line,
                has_custom_comparison=has_custom,
                wrapped_component=wrapped,
                is_exported=is_exported,
            )
            memos.append(memo)

        # ── React.lazy ────────────────────────────────────────────
        for m in self.LAZY_PATTERN.finditer(content):
            name = m.group(1)
            import_path = m.group(2)
            line = content[:m.start()].count('\n') + 1

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            lazy = ReactLazyInfo(
                name=name,
                file=file_path,
                line_number=line,
                import_path=import_path,
                is_exported=is_exported,
            )
            lazies.append(lazy)

        # ── HOC patterns ──────────────────────────────────────────
        for m in self.HOC_PATTERN.finditer(content):
            hoc_call = m.group(1).strip()
            wrapped_component = m.group(2)
            line = content[:m.start()].count('\n') + 1

            # Extract HOC function name
            hoc_name = re.match(r'(\w+)', hoc_call)
            hoc_name = hoc_name.group(1) if hoc_name else hoc_call

            is_exported = 'export' in content[max(0, m.start() - 30):m.start()]

            hoc = ReactHOCInfo(
                name=wrapped_component,
                file=file_path,
                line_number=line,
                wrapped_component=wrapped_component,
                hoc_name=hoc_name,
                is_exported=is_exported,
            )
            hocs.append(hoc)

        # ── Provider Components ───────────────────────────────────
        for m in self.PROVIDER_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            body_start = m.end()
            body_snippet = content[body_start:body_start + 1000]

            # Try to find which context it provides
            context_match = re.search(r'(\w+)\.Provider', body_snippet)
            context_name = context_match.group(1) if context_match else ""

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            provider = ReactProviderInfo(
                name=name,
                file=file_path,
                line_number=line,
                context_name=context_name,
                is_exported=is_exported,
            )
            providers.append(provider)

        return {
            'components': components,
            'hocs': hocs,
            'forward_refs': forward_refs,
            'memos': memos,
            'lazy_components': lazies,
            'error_boundaries': error_boundaries,
            'providers': providers,
        }

    def _extract_hooks_in_body(self, body: str) -> List[str]:
        """Extract unique hook names used in a function body."""
        hooks = set()
        for m in self.HOOK_USAGE_PATTERN.finditer(body):
            hook_match = re.match(r'(use[A-Z]\w*)', m.group(0))
            if hook_match:
                hooks.add(hook_match.group(1))
        return sorted(hooks)
