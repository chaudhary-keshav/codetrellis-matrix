"""
Solid.js Component Extractor for CodeTrellis

Extracts Solid.js component definitions and patterns:
- Functional components (const/function with JSX return)
- Component with Props type annotations
- Lazy components (lazy(() => import(...)))
- Dynamic components (<Dynamic component={...} />)
- ErrorBoundary components
- Suspense wrappers
- Show/Switch/Match/For/Index/Portal/Suspense control-flow components
- ParentComponent, FlowComponent, VoidComponent types
- Props merging (mergeProps, splitProps)
- Children helper usage
- Component with ref forwarding
- Exported vs non-exported components

Supports:
- Solid.js v1.0 (initial API: createSignal, createEffect, JSX)
- Solid.js v1.1-v1.3 (startTransition, createDeferred, ErrorBoundary improvements)
- Solid.js v1.4-v1.5 (external sources, improved streaming SSR)
- Solid.js v1.6-v1.7 (partial hydration, improved store, createResource improvements)
- Solid.js v1.8 (Transition API refinements, server functions prep)
- Solid.js v2.0 (SolidStart 1.0, async primitives, improved compilation)

Part of CodeTrellis v4.62 - Solid.js Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SolidComponentInfo:
    """Information about a Solid.js component definition."""
    name: str
    file: str = ""
    line_number: int = 0
    component_type: str = ""  # functional, lazy, dynamic, error_boundary
    props_type: str = ""  # TypeScript props interface/type
    has_children: bool = False
    has_ref: bool = False
    is_exported: bool = False
    is_default_export: bool = False
    uses_merge_props: bool = False
    uses_split_props: bool = False
    uses_children_helper: bool = False
    control_flow: List[str] = field(default_factory=list)  # Show, For, Switch, etc.
    signals_used: List[str] = field(default_factory=list)
    effects_used: List[str] = field(default_factory=list)
    solid_type: str = ""  # ParentComponent, FlowComponent, VoidComponent, Component


@dataclass
class SolidControlFlowInfo:
    """Information about Solid.js control flow component usage."""
    name: str  # Show, For, Switch, Match, Index, Portal, Suspense, ErrorBoundary
    file: str = ""
    line_number: int = 0
    parent_component: str = ""
    has_fallback: bool = False
    has_keyed: bool = False  # For keyed prop


class SolidComponentExtractor:
    """
    Extracts Solid.js component definitions from source code.

    Detects:
    - Functional component declarations (const/function)
    - TypeScript Component<Props> type annotations
    - ParentComponent, FlowComponent, VoidComponent types
    - Props utilities (mergeProps, splitProps, children)
    - Lazy-loaded components
    - Control flow components (Show, For, Switch, Match, Index, Portal)
    - Suspense and ErrorBoundary wrappers
    - Dynamic component usage
    """

    # Functional component: const Name = (props) => JSX or function Name(props) { return JSX }
    FUNCTION_COMPONENT_PATTERN = re.compile(
        r'(?:export\s+(?:default\s+)?)?(?:const|let|var)\s+(\w+)'
        r'\s*(?::\s*(?:Component|ParentComponent|FlowComponent|VoidComponent)\s*(?:<([^>]*)>)?)?'
        r'\s*=\s*\(([^)]*)\)\s*(?::\s*\w+)?\s*=>',
        re.MULTILINE
    )

    # function Name(props: Props) { ... }
    FUNCTION_DECL_COMPONENT_PATTERN = re.compile(
        r'(?:export\s+(?:default\s+)?)?function\s+(\w+)\s*\('
        r'([^)]*)\)',
        re.MULTILINE
    )

    # Lazy component: lazy(() => import('./Component'))
    LAZY_COMPONENT_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*lazy\s*\(\s*\(\)\s*=>\s*import\s*\(',
        re.MULTILINE
    )

    # Control flow: <Show>, <For>, <Switch>, <Match>, <Index>, <Portal>, <Suspense>, <ErrorBoundary>
    CONTROL_FLOW_PATTERN = re.compile(
        r'<(Show|For|Switch|Match|Index|Portal|Suspense|ErrorBoundary)\b([^>]*?)(?:/>|>)',
        re.MULTILINE
    )

    # Dynamic component: <Dynamic component={...} />
    DYNAMIC_COMPONENT_PATTERN = re.compile(
        r'<Dynamic\s+component\s*=\s*\{([^}]+)\}',
        re.MULTILINE
    )

    # mergeProps usage
    MERGE_PROPS_PATTERN = re.compile(
        r'mergeProps\s*\(',
        re.MULTILINE
    )

    # splitProps usage
    SPLIT_PROPS_PATTERN = re.compile(
        r'splitProps\s*\(',
        re.MULTILINE
    )

    # children helper
    CHILDREN_HELPER_PATTERN = re.compile(
        r'children\s*\(\s*\(\)\s*=>',
        re.MULTILINE
    )

    # Solid Component types
    SOLID_COMPONENT_TYPE_PATTERN = re.compile(
        r'(?:Component|ParentComponent|FlowComponent|VoidComponent)\s*<',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Solid.js component definitions from source code."""
        components = []
        control_flows = []

        # ── Arrow function components ─────────────────────────────
        for m in self.FUNCTION_COMPONENT_PATTERN.finditer(content):
            name = m.group(1)
            props_type = m.group(2) or ""
            params = m.group(3)
            line = content[:m.start()].count('\n') + 1

            # Skip non-component names (lowercase, common utils)
            if name[0].islower() and name not in ('default',):
                continue

            # Determine export status
            prefix = content[max(0, m.start() - 30):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix
            is_default = 'default' in prefix

            # Detect component type annotation
            solid_type = ""
            type_match = re.search(
                r'(Component|ParentComponent|FlowComponent|VoidComponent)',
                content[m.start():m.end()]
            )
            if type_match:
                solid_type = type_match.group(1)

            # Check for props destructuring
            has_children = 'children' in params or 'props.children' in content[m.end():m.end() + 500]

            # Check for ref
            has_ref = 'ref' in params

            # Check component body for control flow
            body_end = min(len(content), m.end() + 2000)
            body = content[m.end():body_end]
            cf_used = []
            for cf_m in self.CONTROL_FLOW_PATTERN.finditer(body):
                cf_name = cf_m.group(1)
                if cf_name not in cf_used:
                    cf_used.append(cf_name)

            # Check for mergeProps/splitProps/children
            uses_merge = bool(self.MERGE_PROPS_PATTERN.search(body))
            uses_split = bool(self.SPLIT_PROPS_PATTERN.search(body))
            uses_children = bool(self.CHILDREN_HELPER_PATTERN.search(body))

            # Detect signal usage
            signals = re.findall(r'\b(createSignal|createMemo|createEffect|createComputed)\b', body)
            unique_signals = list(dict.fromkeys(signals))

            components.append(SolidComponentInfo(
                name=name,
                file=file_path,
                line_number=line,
                component_type="functional",
                props_type=props_type,
                has_children=has_children,
                has_ref=has_ref,
                is_exported=is_exported,
                is_default_export=is_default,
                uses_merge_props=uses_merge,
                uses_split_props=uses_split,
                uses_children_helper=uses_children,
                control_flow=cf_used,
                signals_used=unique_signals,
                solid_type=solid_type,
            ))

        # ── Function declaration components ───────────────────────
        for m in self.FUNCTION_DECL_COMPONENT_PATTERN.finditer(content):
            name = m.group(1)
            params = m.group(2)
            line = content[:m.start()].count('\n') + 1

            # Skip non-component names (must start uppercase)
            if name[0].islower():
                continue

            # Skip if already detected
            if any(c.name == name and c.line_number == line for c in components):
                continue

            prefix = content[max(0, m.start() - 30):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix
            is_default = 'default' in prefix

            # Extract props type from params
            props_type = ""
            type_match = re.search(r':\s*(\w+)', params)
            if type_match:
                props_type = type_match.group(1)

            body_end = min(len(content), m.end() + 2000)
            body = content[m.end():body_end]

            # Check for JSX return (must have JSX to be a component)
            if not re.search(r'return\s*(?:\(?\s*<|\(?\s*\w+\()', body):
                continue

            cf_used = []
            for cf_m in self.CONTROL_FLOW_PATTERN.finditer(body):
                cf_name = cf_m.group(1)
                if cf_name not in cf_used:
                    cf_used.append(cf_name)

            components.append(SolidComponentInfo(
                name=name,
                file=file_path,
                line_number=line,
                component_type="functional",
                props_type=props_type,
                has_children='children' in params,
                is_exported=is_exported,
                is_default_export=is_default,
                control_flow=cf_used,
            ))

        # ── Lazy components ───────────────────────────────────────
        for m in self.LAZY_COMPONENT_PATTERN.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 20):m.start()]
            is_exported = 'export' in prefix

            components.append(SolidComponentInfo(
                name=name,
                file=file_path,
                line_number=line,
                component_type="lazy",
                is_exported=is_exported,
            ))

        # ── Control flow usage ────────────────────────────────────
        for m in self.CONTROL_FLOW_PATTERN.finditer(content):
            cf_name = m.group(1)
            attrs = m.group(2)
            line = content[:m.start()].count('\n') + 1

            has_fallback = 'fallback' in attrs if attrs else False
            has_keyed = 'keyed' in attrs if attrs else False

            control_flows.append(SolidControlFlowInfo(
                name=cf_name,
                file=file_path,
                line_number=line,
                has_fallback=has_fallback,
                has_keyed=has_keyed,
            ))

        return {
            "components": components,
            "control_flows": control_flows,
        }
