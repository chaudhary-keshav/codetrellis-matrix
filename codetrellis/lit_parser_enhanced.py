"""
EnhancedLitParser v1.0 - Comprehensive Lit / Web Components parser using all extractors.

This parser integrates all Lit extractors to provide complete parsing of
Lit and Web Components framework usage across TypeScript/JavaScript source files.
It runs as a supplementary layer on top of the JavaScript/TypeScript parsers,
extracting Lit-specific semantics.

Supports:
- Polymer 1.x (Polymer({}) legacy factory)
- Polymer 2.x (class extends Polymer.Element)
- Polymer 3.x (class extends PolymerElement, LitElement migration path)
- lit-element 2.x (LitElement base class, @property, @customElement)
- lit-html 1.x (html``, render(), directives)
- lit 2.x (unified package, reactive controllers, SSR-ready)
- lit 3.x (latest, @lit/task, @lit/context, @lit/localize, improved decorators)

Core API:
- LitElement — base class for Lit components
- ReactiveElement — lower-level reactive base class
- html`` — tagged template for HTML templates
- svg`` — tagged template for SVG templates
- css`` — tagged template for styles
- render(template, container) — standalone rendering
- nothing, noChange — sentinel values

Decorators:
- @customElement('tag-name') — register custom element
- @property({type, reflect, attribute, converter, hasChanged}) — reactive property
- @state() — internal reactive state
- @query('selector') — DOM query shorthand
- @queryAll('selector') — DOM queryAll shorthand
- @queryAsync('selector') — async DOM query
- @queryAssignedElements({slot, selector}) — slot query
- @queryAssignedNodes({slot}) — slot nodes query
- @eventOptions({passive, capture, once}) — event listener options

Reactive Controllers:
- ReactiveController interface — reusable reactive logic
- ReactiveControllerHost — host interface
- addController(controller) — register controller
- removeController(controller) — unregister controller
- requestUpdate() — trigger update cycle

Lifecycle:
- connectedCallback() — element connected to DOM
- disconnectedCallback() — element disconnected from DOM
- attributeChangedCallback(name, old, new) — attribute change
- adoptedCallback() — element moved to new document
- requestUpdate(name?, oldValue?) — request reactive update
- performUpdate() — execute update
- shouldUpdate(changedProperties) — guard update
- willUpdate(changedProperties) — pre-render hook
- update(changedProperties) — apply update
- render() — return template
- firstUpdated(changedProperties) — after first render
- updated(changedProperties) — after each render
- updateComplete — promise resolving after update

Directives (lit/directives/*):
- repeat(items, keyFn, template) — keyed list rendering
- classMap({class: bool}) — conditional class names
- styleMap({prop: value}) — inline styles
- when(condition, trueCase, falseCase) — conditional rendering
- choose(value, cases, defaultCase) — multi-branch conditional
- map(items, fn) — simple list mapping
- join(items, joiner) — list with separators
- range(start, end, step) — numeric range
- ifDefined(value) — omit attribute if undefined
- live(value) — check live DOM value
- ref(refOrCallback) — element reference
- cache(template) — cache rendered DOM
- guard(deps, fn) — guard re-render
- until(promise, ...fallbacks) — async content
- asyncAppend/asyncReplace — async iterables
- templateContent(template) — stamp <template>
- unsafeHTML(string) — parse HTML string
- unsafeSVG(string) — parse SVG string
- keyed(key, template) — force re-create

CSS Features:
- :host, :host() — shadow host styling
- ::slotted() — slotted content styling
- ::part() — shadow part styling
- CSS custom properties (--*) — theming
- adoptedStyleSheets — shared style sheets
- css`` tagged template — CSSResult
- unsafeCSS(string) — raw CSS string

Shadow DOM:
- Declarative Shadow DOM (<template shadowrootmode>)
- Open shadow root (default)
- Light DOM (override createRenderRoot)
- Scoped custom element registry

Context Protocol (@lit/context):
- createContext(key) — create context
- ContextProvider — provide context
- ContextConsumer — consume context
- @provide({context}) — decorator
- @consume({context}) — decorator

SSR (@lit-labs/ssr):
- render(template) — server-side render
- LitElementRenderer — element renderer
- @lit-labs/ssr-client — client hydration
- Declarative Shadow DOM support

Ecosystem Detection (30+ patterns):
- Core: lit, lit-element, lit-html, @lit/reactive-element
- Labs: @lit-labs/ssr, @lit-labs/router, @lit-labs/motion, @lit-labs/virtualizer
- Stable: @lit/task, @lit/context, @lit/localize
- UI: Vaadin, Shoelace, Spectrum, Lion, Material Web
- Tooling: @open-wc/testing, @web/dev-server, @web/test-runner
- Legacy: Polymer, @polymer/polymer

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.65 - Lit / Web Components Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Lit extractors
from .extractors.lit import (
    LitComponentExtractor, LitComponentInfo, LitMixinInfo, LitControllerInfo,
    LitPropertyExtractor, LitPropertyInfo, LitStateInfo,
    LitEventExtractor, LitEventInfo, LitEventListenerInfo,
    LitTemplateExtractor, LitTemplateInfo, LitDirectiveUsageInfo, LitCSSInfo,
    LitApiExtractor, LitImportInfo, LitIntegrationInfo, LitTypeInfo, LitSSRInfo,
)


@dataclass
class LitParseResult:
    """Complete parse result for a file with Lit / Web Components usage."""
    file_path: str
    file_type: str = "ts"  # ts, js, mjs, cjs

    # Components
    components: List[LitComponentInfo] = field(default_factory=list)
    mixins: List[LitMixinInfo] = field(default_factory=list)
    controllers: List[LitControllerInfo] = field(default_factory=list)

    # Properties
    properties: List[LitPropertyInfo] = field(default_factory=list)
    states: List[LitStateInfo] = field(default_factory=list)

    # Events
    events: List[LitEventInfo] = field(default_factory=list)
    event_listeners: List[LitEventListenerInfo] = field(default_factory=list)

    # Templates
    templates: List[LitTemplateInfo] = field(default_factory=list)
    directive_usages: List[LitDirectiveUsageInfo] = field(default_factory=list)
    css_info: List[LitCSSInfo] = field(default_factory=list)

    # API
    imports: List[LitImportInfo] = field(default_factory=list)
    integrations: List[LitIntegrationInfo] = field(default_factory=list)
    types: List[LitTypeInfo] = field(default_factory=list)
    ssr_patterns: List[LitSSRInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    lit_version: str = ""  # polymer-1, polymer-2, polymer-3, lit-element-2, lit-2, lit-3


class EnhancedLitParser:
    """
    Enhanced Lit / Web Components parser that uses all extractors.

    This parser runs AFTER the JavaScript/TypeScript parser when Lit
    framework is detected. It extracts Lit-specific semantics
    that the language parsers cannot capture.

    Framework detection supports 30+ Lit ecosystem libraries.

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Lit ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'lit': re.compile(
            r"from\s+['\"]lit['\"]|require\(['\"]lit['\"]\)",
            re.MULTILINE
        ),
        'lit-element': re.compile(
            r"from\s+['\"]lit-element['\"]|require\(['\"]lit-element['\"]\)",
            re.MULTILINE
        ),
        'lit-html': re.compile(
            r"from\s+['\"]lit-html['\"]|require\(['\"]lit-html['\"]\)",
            re.MULTILINE
        ),
        'lit-decorators': re.compile(
            r"from\s+['\"]lit/decorators(?:\.js)?['\"]",
            re.MULTILINE
        ),
        'lit-directives': re.compile(
            r"from\s+['\"]lit/directives/",
            re.MULTILINE
        ),
        'reactive-element': re.compile(
            r"from\s+['\"]@lit/reactive-element['\"]",
            re.MULTILINE
        ),
        'lit-static-html': re.compile(
            r"from\s+['\"]lit/static-html(?:\.js)?['\"]",
            re.MULTILINE
        ),

        # ── Stable packages (@lit/) ──────────────────────────────
        'lit-task': re.compile(
            r"from\s+['\"]@lit/task['\"]",
            re.MULTILINE
        ),
        'lit-context': re.compile(
            r"from\s+['\"]@lit/context['\"]",
            re.MULTILINE
        ),
        'lit-localize': re.compile(
            r"from\s+['\"]@lit/localize['\"]",
            re.MULTILINE
        ),

        # ── Labs (@lit-labs/) ─────────────────────────────────────
        'lit-labs-ssr': re.compile(
            r"from\s+['\"]@lit-labs/ssr",
            re.MULTILINE
        ),
        'lit-labs-ssr-client': re.compile(
            r"from\s+['\"]@lit-labs/ssr-client",
            re.MULTILINE
        ),
        'lit-labs-router': re.compile(
            r"from\s+['\"]@lit-labs/router['\"]",
            re.MULTILINE
        ),
        'lit-labs-motion': re.compile(
            r"from\s+['\"]@lit-labs/motion['\"]",
            re.MULTILINE
        ),
        'lit-labs-task': re.compile(
            r"from\s+['\"]@lit-labs/task['\"]",
            re.MULTILINE
        ),
        'lit-labs-context': re.compile(
            r"from\s+['\"]@lit-labs/context['\"]",
            re.MULTILINE
        ),
        'lit-labs-observers': re.compile(
            r"from\s+['\"]@lit-labs/observers['\"]",
            re.MULTILINE
        ),
        'lit-labs-virtualizer': re.compile(
            r"from\s+['\"]@lit-labs/virtualizer['\"]",
            re.MULTILINE
        ),
        'lit-labs-react': re.compile(
            r"from\s+['\"]@lit-labs/react['\"]",
            re.MULTILINE
        ),
        'lit-labs-scoped-registry': re.compile(
            r"from\s+['\"]@lit-labs/scoped-registry-mixin['\"]",
            re.MULTILINE
        ),

        # ── UI Libraries ──────────────────────────────────────────
        'vaadin': re.compile(
            r"(?:from|import)\s+['\"]@vaadin/",
            re.MULTILINE
        ),
        'shoelace': re.compile(
            r"from\s+['\"]@shoelace-style/shoelace",
            re.MULTILINE
        ),
        'spectrum-web-components': re.compile(
            r"from\s+['\"]@spectrum-web-components/",
            re.MULTILINE
        ),
        'lion': re.compile(
            r"from\s+['\"]@lion/",
            re.MULTILINE
        ),
        'material-web': re.compile(
            r"from\s+['\"]@material/web",
            re.MULTILINE
        ),

        # ── Tooling ───────────────────────────────────────────────
        'open-wc-testing': re.compile(
            r"from\s+['\"]@open-wc/testing['\"]",
            re.MULTILINE
        ),
        'open-wc-scoped-elements': re.compile(
            r"from\s+['\"]@open-wc/scoped-elements['\"]",
            re.MULTILINE
        ),
        'web-dev-server': re.compile(
            r"from\s+['\"]@web/dev-server['\"]|@web/dev-server",
            re.MULTILINE
        ),
        'web-test-runner': re.compile(
            r"from\s+['\"]@web/test-runner['\"]|@web/test-runner",
            re.MULTILINE
        ),
        'storybook-wc': re.compile(
            r"@storybook/web-components",
            re.MULTILINE
        ),
        'custom-elements-manifest': re.compile(
            r"custom-elements-manifest|@custom-elements-manifest",
            re.MULTILINE
        ),

        # ── Legacy Polymer ────────────────────────────────────────
        'polymer': re.compile(
            r"from\s+['\"]@polymer/polymer|from\s+['\"]@polymer/",
            re.MULTILINE
        ),
        'polymer-legacy': re.compile(
            r"Polymer\s*\(\s*\{|Polymer\.Element",
            re.MULTILINE
        ),

        # ── Other Web Component frameworks ────────────────────────
        'fast-element': re.compile(
            r"from\s+['\"]@microsoft/fast-element",
            re.MULTILINE
        ),
        'stencil': re.compile(
            r"from\s+['\"]@stencil/core['\"]",
            re.MULTILINE
        ),
    }

    # Feature detection patterns
    FEATURE_PATTERNS = {
        # Component patterns
        'custom_element_decorator': re.compile(r'@customElement\s*\(', re.MULTILINE),
        'extends_lit_element': re.compile(r'extends\s+LitElement\b', re.MULTILINE),
        'extends_reactive_element': re.compile(r'extends\s+ReactiveElement\b', re.MULTILINE),
        'custom_elements_define': re.compile(r'customElements\.define\s*\(', re.MULTILINE),

        # Property patterns
        'property_decorator': re.compile(r'@property\s*\(', re.MULTILINE),
        'state_decorator': re.compile(r'@state\s*\(', re.MULTILINE),
        'static_properties': re.compile(r'static\s+(?:get\s+)?properties\b', re.MULTILINE),

        # Query decorators
        'query_decorator': re.compile(r'@query\s*\(', re.MULTILINE),
        'query_all_decorator': re.compile(r'@queryAll\s*\(', re.MULTILINE),
        'query_async_decorator': re.compile(r'@queryAsync\s*\(', re.MULTILINE),
        'query_assigned_elements': re.compile(r'@queryAssignedElements\s*\(', re.MULTILINE),
        'query_assigned_nodes': re.compile(r'@queryAssignedNodes\s*\(', re.MULTILINE),

        # Template patterns
        'html_template': re.compile(r'\bhtml\s*`', re.MULTILINE),
        'svg_template': re.compile(r'\bsvg\s*`', re.MULTILINE),
        'css_template': re.compile(r'\bcss\s*`', re.MULTILINE),
        'static_html': re.compile(r'\bstaticHtml\s*`', re.MULTILINE),
        'nothing': re.compile(r'\bnothing\b', re.MULTILINE),
        'no_change': re.compile(r'\bnoChange\b', re.MULTILINE),

        # Directive patterns
        'repeat_directive': re.compile(r'\brepeat\s*\(', re.MULTILINE),
        'class_map': re.compile(r'\bclassMap\s*\(', re.MULTILINE),
        'style_map': re.compile(r'\bstyleMap\s*\(', re.MULTILINE),
        'when_directive': re.compile(r'\bwhen\s*\(', re.MULTILINE),
        'choose_directive': re.compile(r'\bchoose\s*\(', re.MULTILINE),
        'if_defined': re.compile(r'\bifDefined\s*\(', re.MULTILINE),
        'live_directive': re.compile(r'\blive\s*\(', re.MULTILINE),
        'ref_directive': re.compile(r'\bref\s*\(', re.MULTILINE),
        'cache_directive': re.compile(r'\bcache\s*\(', re.MULTILINE),
        'guard_directive': re.compile(r'\bguard\s*\(', re.MULTILINE),
        'until_directive': re.compile(r'\buntil\s*\(', re.MULTILINE),
        'unsafe_html': re.compile(r'\bunsafeHTML\s*\(', re.MULTILINE),
        'unsafe_svg': re.compile(r'\bunsafeSVG\s*\(', re.MULTILINE),
        'keyed_directive': re.compile(r'\bkeyed\s*\(', re.MULTILINE),
        'template_content': re.compile(r'\btemplateContent\s*\(', re.MULTILINE),
        'async_append': re.compile(r'\basyncAppend\s*\(', re.MULTILINE),
        'async_replace': re.compile(r'\basyncReplace\s*\(', re.MULTILINE),
        'map_directive': re.compile(r'\bmap\s*\(', re.MULTILINE),
        'join_directive': re.compile(r'\bjoin\s*\(', re.MULTILINE),
        'range_directive': re.compile(r'\brange\s*\(', re.MULTILINE),

        # Reactive controller patterns
        'reactive_controller': re.compile(r'ReactiveController\b', re.MULTILINE),
        'add_controller': re.compile(r'addController\s*\(', re.MULTILINE),

        # CSS patterns
        'host_selector': re.compile(r':host\b', re.MULTILINE),
        'slotted_selector': re.compile(r'::slotted\s*\(', re.MULTILINE),
        'part_selector': re.compile(r'::part\s*\(', re.MULTILINE),
        'adopted_stylesheets': re.compile(r'adoptedStyleSheets', re.MULTILINE),
        'css_custom_property': re.compile(r'--[\w-]+\s*:', re.MULTILINE),

        # Shadow DOM patterns
        'shadow_dom': re.compile(r'attachShadow\s*\(|createRenderRoot', re.MULTILINE),
        'light_dom': re.compile(r'createRenderRoot\s*\(\s*\)\s*\{[^}]*return\s+this\b', re.MULTILINE),
        'slot_element': re.compile(r'<slot\b', re.MULTILINE),

        # Event patterns
        'dispatch_event': re.compile(r'dispatchEvent\s*\(\s*new\s+CustomEvent', re.MULTILINE),
        'event_options': re.compile(r'@eventOptions\s*\(', re.MULTILINE),

        # Lifecycle
        'connected_callback': re.compile(r'connectedCallback\s*\(', re.MULTILINE),
        'disconnected_callback': re.compile(r'disconnectedCallback\s*\(', re.MULTILINE),
        'first_updated': re.compile(r'firstUpdated\s*\(', re.MULTILINE),
        'updated': re.compile(r'updated\s*\(', re.MULTILINE),
        'should_update': re.compile(r'shouldUpdate\s*\(', re.MULTILINE),
        'will_update': re.compile(r'willUpdate\s*\(', re.MULTILINE),
        'update_complete': re.compile(r'updateComplete\b', re.MULTILINE),
        'request_update': re.compile(r'requestUpdate\s*\(', re.MULTILINE),

        # Context protocol
        'context_provider': re.compile(r'ContextProvider\b|@provide\s*\(', re.MULTILINE),
        'context_consumer': re.compile(r'ContextConsumer\b|@consume\s*\(', re.MULTILINE),
        'create_context': re.compile(r'createContext\s*\(', re.MULTILINE),

        # Task controller
        'task_controller': re.compile(r'Task\b.*?\bfrom\b|new\s+Task\s*\(', re.MULTILINE),

        # SSR
        'server_render': re.compile(r'@lit-labs/ssr|renderToString', re.MULTILINE),
        'declarative_shadow_dom': re.compile(r'shadowrootmode|shadowroot\b', re.MULTILINE),

        # Polymer legacy
        'polymer_factory': re.compile(r'Polymer\s*\(\s*\{', re.MULTILINE),
        'polymer_behaviors': re.compile(r'behaviors\s*:\s*\[', re.MULTILINE),
    }

    def __init__(self):
        """Initialize all Lit extractors."""
        self.component_extractor = LitComponentExtractor()
        self.property_extractor = LitPropertyExtractor()
        self.event_extractor = LitEventExtractor()
        self.template_extractor = LitTemplateExtractor()
        self.api_extractor = LitApiExtractor()

    def is_lit_file(self, content: str, file_path: str = "") -> bool:
        """
        Check if a file contains Lit / Web Components code.

        Returns True if the file imports from Lit ecosystem
        or uses Lit-specific patterns.
        """
        lit_indicators = [
            # lit (unified package)
            "from 'lit'", 'from "lit"',
            "from 'lit/decorators.js'", 'from "lit/decorators.js"',
            "from 'lit/decorators'", 'from "lit/decorators"',
            "from 'lit/directives/", 'from "lit/directives/',
            "from 'lit/static-html.js'", 'from "lit/static-html.js"',
            # lit-element (standalone)
            "from 'lit-element'", 'from "lit-element"',
            "from 'lit-element/", 'from "lit-element/',
            # lit-html (standalone)
            "from 'lit-html'", 'from "lit-html"',
            "from 'lit-html/", 'from "lit-html/',
            # @lit/ packages
            "from '@lit/reactive-element'", 'from "@lit/reactive-element"',
            "from '@lit/task'", 'from "@lit/task"',
            "from '@lit/context'", 'from "@lit/context"',
            "from '@lit/localize'", 'from "@lit/localize"',
            # @lit-labs/ packages
            "from '@lit-labs/ssr", 'from "@lit-labs/ssr',
            "from '@lit-labs/router'", 'from "@lit-labs/router"',
            "from '@lit-labs/motion'", 'from "@lit-labs/motion"',
            "from '@lit-labs/task'", 'from "@lit-labs/task"',
            "from '@lit-labs/context'", 'from "@lit-labs/context"',
            "from '@lit-labs/observers'", 'from "@lit-labs/observers"',
            "from '@lit-labs/virtualizer'", 'from "@lit-labs/virtualizer"',
            "from '@lit-labs/react'", 'from "@lit-labs/react"',
            "from '@lit-labs/scoped-registry-mixin'",
            # Polymer
            "from '@polymer/polymer'", 'from "@polymer/polymer"',
            "from '@polymer/", 'from "@polymer/',
            "Polymer({",
            # Web Components patterns (combined with class extends)
            'extends LitElement',
            'extends ReactiveElement',
            'extends PolymerElement',
            '@customElement(',
            'customElements.define(',
            # require()
            "require('lit')", 'require("lit")',
            "require('lit-element')", 'require("lit-element")',
        ]
        return any(ind in content for ind in lit_indicators)

    def parse(self, content: str, file_path: str = "") -> LitParseResult:
        """
        Parse a source file for Lit / Web Components patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            LitParseResult with all extracted information
        """
        # Determine file type
        file_type = "ts"
        if file_path.endswith('.tsx'):
            file_type = "tsx"
        elif file_path.endswith('.jsx'):
            file_type = "jsx"
        elif file_path.endswith('.js') or file_path.endswith('.mjs') or file_path.endswith('.cjs'):
            file_type = "js"

        result = LitParseResult(file_path=file_path, file_type=file_type)

        # ── Framework detection ────────────────────────────────────
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_features = self._detect_features(content)
        result.lit_version = self._detect_version(content)

        # ── Component extraction ───────────────────────────────────
        try:
            comp_result = self.component_extractor.extract(content, file_path)
            result.components = comp_result.get('components', [])
            result.mixins = comp_result.get('mixins', [])
            result.controllers = comp_result.get('controllers', [])
        except Exception:
            pass

        # ── Property extraction ────────────────────────────────────
        try:
            prop_result = self.property_extractor.extract(content, file_path)
            result.properties = prop_result.get('properties', [])
            result.states = prop_result.get('states', [])
        except Exception:
            pass

        # ── Event extraction ───────────────────────────────────────
        try:
            event_result = self.event_extractor.extract(content, file_path)
            result.events = event_result.get('events', [])
            result.event_listeners = event_result.get('listeners', [])
        except Exception:
            pass

        # ── Template extraction ────────────────────────────────────
        try:
            tpl_result = self.template_extractor.extract(content, file_path)
            result.templates = tpl_result.get('templates', [])
            result.directive_usages = tpl_result.get('directives', [])
            result.css_info = tpl_result.get('css', [])
        except Exception:
            pass

        # ── API extraction ─────────────────────────────────────────
        try:
            api_result = self.api_extractor.extract(content, file_path)
            result.imports = api_result.get('imports', [])
            result.integrations = api_result.get('integrations', [])
            result.types = api_result.get('types', [])
            result.ssr_patterns = api_result.get('ssr_patterns', [])
        except Exception:
            pass

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Lit ecosystem frameworks are used."""
        detected = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_features(self, content: str) -> List[str]:
        """Detect which Lit features are used."""
        detected = []
        for name, pattern in self.FEATURE_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """
        Detect Lit version based on API usage and import patterns.

        Returns:
            - 'lit-3' if @lit/task, @lit/context, @lit/localize (stable promotions)
            - 'lit-2' if from 'lit' unified import
            - 'lit-element-2' if from 'lit-element' (standalone)
            - 'polymer-3' if from '@polymer/polymer' or PolymerElement class
            - 'polymer-2' if Polymer.Element class syntax
            - 'polymer-1' if Polymer({}) factory
            - '' if unknown
        """
        # lit 3.x indicators: stable @lit/ packages (promoted from @lit-labs/)
        lit_3_indicators = [
            "@lit/task",
            "@lit/context",
            "@lit/localize",
        ]
        if any(ind in content for ind in lit_3_indicators):
            return "lit-3"

        # lit 2.x indicators: unified lit package
        lit_2_indicators = [
            "from 'lit'",
            'from "lit"',
            "from 'lit/",
            'from "lit/',
            '@lit-labs/',
        ]
        if any(ind in content for ind in lit_2_indicators):
            return "lit-2"

        # lit-element 2.x indicators: standalone lit-element import
        lit_element_2_indicators = [
            "from 'lit-element'",
            'from "lit-element"',
            "from 'lit-element/",
            'from "lit-element/',
        ]
        if any(ind in content for ind in lit_element_2_indicators):
            return "lit-element-2"

        # Polymer 3.x indicators: @polymer/ scoped package
        polymer_3_indicators = [
            "@polymer/polymer",
            "@polymer/",
            "extends PolymerElement",
        ]
        if any(ind in content for ind in polymer_3_indicators):
            return "polymer-3"

        # Polymer 2.x indicators: Polymer.Element class syntax
        if re.search(r'extends\s+Polymer\.Element\b', content):
            return "polymer-2"

        # Polymer 1.x indicators: Polymer({}) factory call
        if re.search(r'Polymer\s*\(\s*\{', content):
            return "polymer-1"

        # Generic LitElement extends (could be lit-element 2 or lit 2+)
        if 'extends LitElement' in content or 'extends ReactiveElement' in content:
            return "lit-2"

        # customElements.define without specific imports
        if 'customElements.define' in content and 'extends HTMLElement' in content:
            return "vanilla-wc"

        return ""

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings. Returns >0 if v1 > v2."""
        version_order = {
            '': 0, 'polymer-1': 1, 'polymer-2': 2, 'polymer-3': 3,
            'lit-element-2': 4, 'vanilla-wc': 4, 'lit-2': 5, 'lit-3': 6,
        }
        return version_order.get(v1, 0) - version_order.get(v2, 0)
