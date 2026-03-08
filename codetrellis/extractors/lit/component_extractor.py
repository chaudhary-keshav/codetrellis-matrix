"""
Lit Component Extractor for CodeTrellis

Extracts Lit and Web Component definitions from JavaScript/TypeScript source code:
- LitElement subclasses with @customElement decorator
- ReactiveElement subclasses
- Plain HTMLElement / custom elements (customElements.define)
- Lifecycle methods (connectedCallback, disconnectedCallback, firstUpdated, updated,
  willUpdate, attributeChangedCallback, adoptedCallback, createRenderRoot)
- Static styles (css``, adoptedStyleSheets, CSSStyleSheet)
- Shadow DOM / Light DOM detection
- Mixin patterns (dedupeMixin, superclass pattern)
- ReactiveController implementations (hostConnected, hostDisconnected, hostUpdate, hostUpdated)
- Decorators (@customElement, @queryAssignedElements, @queryAssignedNodes,
  @query, @queryAll, @queryAsync)

Supports:
- Polymer 1.x-3.x (Polymer.Element, Polymer({ is: ... }))
- lit-element 2.x (LitElement, customElement, css, html)
- lit 2.x-3.x (unified lit package, decorators.js)
- @lit/reactive-element (ReactiveElement base class)
- Vanilla Web Components (HTMLElement + customElements.define)

Part of CodeTrellis v4.65 - Lit / Web Components Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class LitComponentInfo:
    """Information about a Lit or Web Component class definition."""
    name: str
    file: str = ""
    line_number: int = 0
    tag_name: str = ""  # Custom element tag name (e.g., 'my-element')
    superclass: str = ""  # LitElement, ReactiveElement, HTMLElement, PolymerElement
    component_type: str = "lit"  # lit, reactive-element, vanilla, polymer
    has_decorator: bool = False  # @customElement decorator used
    has_shadow_dom: bool = True  # Default true for LitElement
    has_render: bool = False
    has_static_styles: bool = False
    has_static_properties: bool = False
    lifecycle_methods: List[str] = field(default_factory=list)
    query_decorators: List[str] = field(default_factory=list)
    controllers_used: List[str] = field(default_factory=list)
    mixins_used: List[str] = field(default_factory=list)
    is_exported: bool = False
    is_abstract: bool = False
    has_typescript: bool = False
    properties_count: int = 0
    events_dispatched: List[str] = field(default_factory=list)


@dataclass
class LitMixinInfo:
    """Information about a Lit mixin definition."""
    name: str
    file: str = ""
    line_number: int = 0
    superclass_param: str = ""  # Parameter name for superclass
    has_deduplication: bool = False  # Uses dedupeMixin
    is_exported: bool = False
    methods_added: List[str] = field(default_factory=list)
    properties_added: List[str] = field(default_factory=list)


@dataclass
class LitControllerInfo:
    """Information about a ReactiveController implementation."""
    name: str
    file: str = ""
    line_number: int = 0
    controller_type: str = ""  # custom, task, context, observer, etc.
    has_host_connected: bool = False
    has_host_disconnected: bool = False
    has_host_update: bool = False
    has_host_updated: bool = False
    is_exported: bool = False
    host_type: str = ""  # ReactiveControllerHost type


class LitComponentExtractor:
    """
    Extracts Lit component and Web Component definitions from source code.

    Detects:
    - LitElement subclasses with @customElement('tag-name')
    - ReactiveElement subclasses
    - Plain HTMLElement subclasses with customElements.define()
    - Polymer element definitions
    - Component lifecycle methods
    - Static styles using css`` tagged template
    - Shadow/Light DOM configuration via createRenderRoot
    - Mixin patterns
    - ReactiveController implementations
    """

    # Custom element decorator pattern: @customElement('tag-name')
    CUSTOM_ELEMENT_DECORATOR = re.compile(
        r'@customElement\s*\(\s*[\'"]([a-z][a-z0-9-]*)[\'"]'
        r'\s*\)',
        re.MULTILINE
    )

    # Class extending LitElement / ReactiveElement / HTMLElement / PolymerElement
    CLASS_EXTENDS = re.compile(
        r'(?:export\s+)?(?:abstract\s+)?class\s+(\w+)\s+'
        r'extends\s+((?:\w+\.)*(?:LitElement|ReactiveElement|HTMLElement|'
        r'PolymerElement|Polymer\.Element|FASTElement)(?:\s*\([^)]*\))?)',
        re.MULTILINE
    )

    # Class extending a mixin: class X extends MyMixin(LitElement)
    CLASS_EXTENDS_MIXIN = re.compile(
        r'(?:export\s+)?(?:abstract\s+)?class\s+(\w+)\s+'
        r'extends\s+(\w+)\s*\(\s*(LitElement|ReactiveElement|HTMLElement)\s*\)',
        re.MULTILINE
    )

    # customElements.define('tag-name', ClassName)
    CUSTOM_ELEMENTS_DEFINE = re.compile(
        r'customElements\.define\s*\(\s*[\'"]([a-z][a-z0-9-]*)[\'"]'
        r'\s*,\s*(\w+)',
        re.MULTILINE
    )

    # Polymer legacy: Polymer({ is: 'tag-name', ... })
    POLYMER_LEGACY = re.compile(
        r'Polymer\s*\(\s*\{[^}]*is\s*:\s*[\'"]([a-z][a-z0-9-]*)[\'"]',
        re.MULTILINE | re.DOTALL
    )

    # Lifecycle methods
    LIFECYCLE_METHODS = [
        'connectedCallback', 'disconnectedCallback', 'attributeChangedCallback',
        'adoptedCallback', 'firstUpdated', 'updated', 'willUpdate',
        'createRenderRoot', 'render', 'performUpdate', 'shouldUpdate',
        'getUpdateComplete', 'requestUpdate',
    ]

    # Query decorators
    QUERY_DECORATOR = re.compile(
        r'@(query|queryAll|queryAsync|queryAssignedElements|queryAssignedNodes)\s*\(',
        re.MULTILINE
    )

    # Controller usage: addController(new SomeController(this))
    ADD_CONTROLLER = re.compile(
        r'(?:this\.)?addController\s*\(\s*new\s+(\w+)',
        re.MULTILINE
    )

    # Mixin definition: const MyMixin = (superClass) => class extends superClass
    MIXIN_ARROW = re.compile(
        r'(?:export\s+)?(?:const|function)\s+(\w+)\s*=\s*'
        r'(?:\([^)]*\)|(\w+))\s*=>\s*class\s+extends\s+',
        re.MULTILINE
    )

    # dedupeMixin pattern
    DEDUP_MIXIN = re.compile(
        r'dedupeMixin\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # ReactiveController class
    CONTROLLER_CLASS = re.compile(
        r'(?:export\s+)?class\s+(\w+)\s+implements\s+ReactiveController',
        re.MULTILINE
    )

    # Dispatch event: this.dispatchEvent(new CustomEvent('name'))
    DISPATCH_EVENT = re.compile(
        r'this\.dispatchEvent\s*\(\s*new\s+(?:Custom)?Event\s*\(\s*'
        r'[\'"]([a-z][a-z0-9-]*)[\'"]',
        re.MULTILINE
    )

    # Static styles
    STATIC_STYLES = re.compile(
        r'static\s+(?:get\s+)?styles\b',
        re.MULTILINE
    )

    # Static properties
    STATIC_PROPERTIES = re.compile(
        r'static\s+(?:get\s+)?properties\b',
        re.MULTILINE
    )

    # createRenderRoot override (light DOM indicator)
    CREATE_RENDER_ROOT = re.compile(
        r'createRenderRoot\s*\(\s*\)\s*\{[^}]*return\s+this\b',
        re.MULTILINE | re.DOTALL
    )

    def extract(self, content: str, file_path: str = "") -> Dict:
        """
        Extract Lit component information from source code.

        Returns dict with keys: components, mixins, controllers
        """
        components: List[LitComponentInfo] = []
        mixins: List[LitMixinInfo] = []
        controllers: List[LitControllerInfo] = []

        lines = content.split('\n')
        is_exported_at_line = {}
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('export '):
                is_exported_at_line[i] = True

        # ── Extract components from class declarations ────────────
        # First, find @customElement decorators and their tag names
        decorator_tags: Dict[int, str] = {}
        for m in self.CUSTOM_ELEMENT_DECORATOR.finditer(content):
            tag_name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1
            # The decorator is on the line before the class
            decorator_tags[line_num] = tag_name
            # Also check line_num + 1 (decorator may be on previous line)
            decorator_tags[line_num + 1] = tag_name

        # Find classes extending LitElement/ReactiveElement/HTMLElement
        for m in self.CLASS_EXTENDS.finditer(content):
            name = m.group(1)
            superclass_raw = m.group(2)
            line_num = content[:m.start()].count('\n') + 1

            # Determine superclass type
            if 'LitElement' in superclass_raw:
                comp_type = "lit"
                superclass = "LitElement"
            elif 'ReactiveElement' in superclass_raw:
                comp_type = "reactive-element"
                superclass = "ReactiveElement"
            elif 'PolymerElement' in superclass_raw or 'Polymer.Element' in superclass_raw:
                comp_type = "polymer"
                superclass = "PolymerElement"
            elif 'FASTElement' in superclass_raw:
                comp_type = "fast"
                superclass = "FASTElement"
            else:
                comp_type = "vanilla"
                superclass = "HTMLElement"

            # Check for @customElement decorator
            tag_name = decorator_tags.get(line_num, "")
            if not tag_name:
                tag_name = decorator_tags.get(line_num - 1, "")
            has_decorator = bool(tag_name)

            is_exported = 'export ' in (lines[line_num - 1] if line_num <= len(lines) else "")
            is_abstract = 'abstract ' in (lines[line_num - 1] if line_num <= len(lines) else "")

            # Extract component body info
            comp = LitComponentInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                tag_name=tag_name,
                superclass=superclass,
                component_type=comp_type,
                has_decorator=has_decorator,
                has_shadow_dom=comp_type in ('lit', 'reactive-element', 'polymer'),
                is_exported=is_exported,
                is_abstract=is_abstract,
                has_typescript=file_path.endswith('.ts'),
            )

            # Scan class body for lifecycle, render, etc.
            self._analyze_class_body(content, m.start(), comp)
            components.append(comp)

        # Find classes extending mixins: class X extends MyMixin(LitElement)
        for m in self.CLASS_EXTENDS_MIXIN.finditer(content):
            name = m.group(1)
            mixin_name = m.group(2)
            base_class = m.group(3)
            line_num = content[:m.start()].count('\n') + 1

            tag_name = decorator_tags.get(line_num, "")
            if not tag_name:
                tag_name = decorator_tags.get(line_num - 1, "")

            is_exported = 'export ' in (lines[line_num - 1] if line_num <= len(lines) else "")

            comp = LitComponentInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                tag_name=tag_name,
                superclass=base_class,
                component_type="lit" if base_class == "LitElement" else "reactive-element",
                has_decorator=bool(tag_name),
                has_shadow_dom=base_class != "HTMLElement",
                mixins_used=[mixin_name],
                is_exported=is_exported,
                has_typescript=file_path.endswith('.ts'),
            )
            self._analyze_class_body(content, m.start(), comp)
            components.append(comp)

        # Find customElements.define() for un-decorated components
        for m in self.CUSTOM_ELEMENTS_DEFINE.finditer(content):
            tag_name = m.group(1)
            class_name = m.group(2)
            # Check if this class is already tracked
            existing = [c for c in components if c.name == class_name]
            if existing:
                if not existing[0].tag_name:
                    existing[0].tag_name = tag_name
            else:
                line_num = content[:m.start()].count('\n') + 1
                comp = LitComponentInfo(
                    name=class_name,
                    file=file_path,
                    line_number=line_num,
                    tag_name=tag_name,
                    superclass="HTMLElement",
                    component_type="vanilla",
                    has_shadow_dom=False,
                )
                components.append(comp)

        # Polymer legacy elements
        for m in self.POLYMER_LEGACY.finditer(content):
            tag_name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1
            comp = LitComponentInfo(
                name=tag_name.replace('-', '_').title().replace('_', ''),
                file=file_path,
                line_number=line_num,
                tag_name=tag_name,
                superclass="PolymerElement",
                component_type="polymer",
                has_shadow_dom=True,
            )
            components.append(comp)

        # ── Extract mixins ────────────────────────────────────────
        for m in self.MIXIN_ARROW.finditer(content):
            name = m.group(1)
            param = m.group(2) or "superClass"
            line_num = content[:m.start()].count('\n') + 1
            is_exported = 'export ' in (lines[line_num - 1] if line_num <= len(lines) else "")

            mixin = LitMixinInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                superclass_param=param,
                is_exported=is_exported,
            )
            mixins.append(mixin)

        for m in self.DEDUP_MIXIN.finditer(content):
            name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1
            # Update existing mixin if found
            for mixin in mixins:
                if mixin.name == name:
                    mixin.has_deduplication = True

        # ── Extract controllers ───────────────────────────────────
        for m in self.CONTROLLER_CLASS.finditer(content):
            name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1
            is_exported = 'export ' in (lines[line_num - 1] if line_num <= len(lines) else "")

            ctrl = LitControllerInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                controller_type="custom",
                is_exported=is_exported,
            )

            # Check for lifecycle methods in body
            body_start = content.find('{', m.end())
            if body_start != -1:
                # Simple brace counting
                depth = 1
                pos = body_start + 1
                while pos < len(content) and depth > 0:
                    if content[pos] == '{':
                        depth += 1
                    elif content[pos] == '}':
                        depth -= 1
                    pos += 1
                body = content[body_start:pos]
                ctrl.has_host_connected = 'hostConnected' in body
                ctrl.has_host_disconnected = 'hostDisconnected' in body
                ctrl.has_host_update = 'hostUpdate' in body
                ctrl.has_host_updated = 'hostUpdated' in body

            controllers.append(ctrl)

        return {
            'components': components,
            'mixins': mixins,
            'controllers': controllers,
        }

    def _analyze_class_body(self, content: str, class_start: int, comp: LitComponentInfo):
        """Analyze a class body for lifecycle methods, styles, render, etc."""
        # Find class body opening brace
        body_start = content.find('{', class_start)
        if body_start == -1:
            return

        # Simple brace counting to find class body end
        depth = 1
        pos = body_start + 1
        while pos < len(content) and depth > 0:
            if content[pos] == '{':
                depth += 1
            elif content[pos] == '}':
                depth -= 1
            pos += 1

        body = content[body_start:pos]

        # Check lifecycle methods
        for method in self.LIFECYCLE_METHODS:
            pattern = re.compile(r'\b' + re.escape(method) + r'\s*\(', re.MULTILINE)
            if pattern.search(body):
                comp.lifecycle_methods.append(method)
                if method == 'render':
                    comp.has_render = True

        # Check static styles
        if self.STATIC_STYLES.search(body):
            comp.has_static_styles = True

        # Check static properties
        if self.STATIC_PROPERTIES.search(body):
            comp.has_static_properties = True

        # Check query decorators
        for m in self.QUERY_DECORATOR.finditer(body):
            comp.query_decorators.append(m.group(1))

        # Check controllers
        for m in self.ADD_CONTROLLER.finditer(body):
            comp.controllers_used.append(m.group(1))

        # Check shadow DOM override
        if self.CREATE_RENDER_ROOT.search(body):
            comp.has_shadow_dom = False

        # Check dispatched events
        for m in self.DISPATCH_EVENT.finditer(body):
            event_name = m.group(1)
            if event_name not in comp.events_dispatched:
                comp.events_dispatched.append(event_name)
