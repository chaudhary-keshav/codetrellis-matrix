"""
Tests for Lit / Web Components extractors and EnhancedLitParser.

Part of CodeTrellis v4.65 Lit / Web Components Framework Support.
Tests cover:
- Component extraction (LitElement, ReactiveElement, controllers, mixins, Polymer)
- Property extraction (@property, @state, static properties, converters)
- Event extraction (CustomEvent dispatch, @eventOptions, template bindings)
- Template extraction (html``, svg``, css``, directives, bindings, slots)
- API extraction (imports, SSR, integrations, types, ecosystem)
- Parser integration (framework detection, version detection, feature detection)
"""

import pytest
from codetrellis.lit_parser_enhanced import (
    EnhancedLitParser,
    LitParseResult,
)
from codetrellis.extractors.lit import (
    LitComponentExtractor,
    LitPropertyExtractor,
    LitEventExtractor,
    LitTemplateExtractor,
    LitApiExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedLitParser()


@pytest.fixture
def component_extractor():
    return LitComponentExtractor()


@pytest.fixture
def property_extractor():
    return LitPropertyExtractor()


@pytest.fixture
def event_extractor():
    return LitEventExtractor()


@pytest.fixture
def template_extractor():
    return LitTemplateExtractor()


@pytest.fixture
def api_extractor():
    return LitApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Component Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestLitComponentExtractor:

    def test_basic_lit_element(self, component_extractor):
        code = '''
        import { LitElement, html } from 'lit';
        import { customElement } from 'lit/decorators.js';

        @customElement('my-element')
        export class MyElement extends LitElement {
            render() {
                return html`<p>Hello</p>`;
            }
        }
        '''
        result = component_extractor.extract(code, "my-element.ts")
        comps = result['components']
        assert len(comps) >= 1
        assert comps[0].name == "MyElement"
        assert comps[0].superclass == "LitElement"
        assert comps[0].tag_name == "my-element"

    def test_reactive_element(self, component_extractor):
        code = '''
        import { ReactiveElement } from '@lit/reactive-element';

        class MyReactiveElement extends ReactiveElement {
            connectedCallback() {
                super.connectedCallback();
            }
        }
        customElements.define('my-reactive', MyReactiveElement);
        '''
        result = component_extractor.extract(code, "reactive.ts")
        comps = result['components']
        assert len(comps) >= 1
        assert comps[0].superclass == "ReactiveElement"

    def test_custom_elements_define(self, component_extractor):
        code = '''
        class AppHeader extends LitElement {
            render() {
                return html`<header>App</header>`;
            }
        }
        customElements.define('app-header', AppHeader);
        '''
        result = component_extractor.extract(code, "header.ts")
        comps = result['components']
        assert len(comps) >= 1

    def test_lifecycle_methods_detected(self, component_extractor):
        code = '''
        @customElement('lifecycle-demo')
        class LifecycleDemo extends LitElement {
            connectedCallback() { super.connectedCallback(); }
            disconnectedCallback() { super.disconnectedCallback(); }
            firstUpdated(changedProperties) {}
            updated(changedProperties) {}
            shouldUpdate(changedProperties) { return true; }
            willUpdate(changedProperties) {}
            render() { return html``; }
        }
        '''
        result = component_extractor.extract(code, "lifecycle.ts")
        comps = result['components']
        assert len(comps) >= 1
        assert 'connectedCallback' in comps[0].lifecycle_methods
        assert 'firstUpdated' in comps[0].lifecycle_methods
        assert 'render' in comps[0].lifecycle_methods

    def test_query_decorators(self, component_extractor):
        code = '''
        @customElement('query-demo')
        class QueryDemo extends LitElement {
            @query('#input') _input;
            @queryAll('.item') _items;
            @queryAsync('#dialog') _dialog;
            @queryAssignedElements({slot: 'header'}) _headerSlot;
            render() { return html``; }
        }
        '''
        result = component_extractor.extract(code, "query.ts")
        comps = result['components']
        assert len(comps) >= 1
        assert 'query' in comps[0].query_decorators
        assert 'queryAll' in comps[0].query_decorators

    def test_controller_usage(self, component_extractor):
        code = '''
        class ClockController {
            constructor(host) {
                this.host = host;
                host.addController(this);
            }
            hostConnected() {}
            hostDisconnected() {}
        }

        @customElement('my-clock')
        class MyClock extends LitElement {
            clock = new ClockController(this);
            render() { return html`${this.clock.value}`; }
        }
        '''
        result = component_extractor.extract(code, "clock.ts")
        controllers = result.get('controllers', [])
        # Controller should be detected via ReactiveController/implements pattern or addController
        # Component should detect controller usage

    def test_mixin_detection(self, component_extractor):
        code = '''
        const MyMixin = (superClass) => class extends superClass {
            mixinMethod() {}
        };

        const DedupMixin = dedupeMixin((superClass) => class extends superClass {
            dedupMethod() {}
        });
        '''
        result = component_extractor.extract(code, "mixins.ts")
        mixins = result.get('mixins', [])
        assert len(mixins) >= 1

    def test_polymer_element(self, component_extractor):
        code = '''
        import { PolymerElement } from '@polymer/polymer';

        class MyPolymerElement extends PolymerElement {
            static get is() { return 'my-polymer'; }
            static get properties() {
                return { name: { type: String } };
            }
        }
        customElements.define('my-polymer', MyPolymerElement);
        '''
        result = component_extractor.extract(code, "polymer.ts")
        comps = result['components']
        assert len(comps) >= 1
        assert comps[0].superclass == "PolymerElement"

    def test_polymer_factory(self, component_extractor):
        code = '''
        Polymer({
            is: 'legacy-element',
            properties: {
                name: { type: String, value: '' }
            },
            listeners: {
                'click': '_handleClick'
            }
        });
        '''
        result = component_extractor.extract(code, "legacy.js")
        comps = result['components']
        assert len(comps) >= 1

    def test_shadow_dom_detection(self, component_extractor):
        code = '''
        @customElement('light-dom')
        class LightDom extends LitElement {
            createRenderRoot() {
                return this;
            }
            render() { return html`<p>Light DOM</p>`; }
        }
        '''
        result = component_extractor.extract(code, "light.ts")
        comps = result['components']
        assert len(comps) >= 1
        # Light DOM override detected
        assert comps[0].has_shadow_dom is False

    def test_event_dispatch_detection(self, component_extractor):
        code = '''
        @customElement('event-demo')
        class EventDemo extends LitElement {
            _handleClick() {
                this.dispatchEvent(new CustomEvent('item-selected', {
                    detail: { item: this.selected },
                    bubbles: true,
                    composed: true,
                }));
            }
        }
        '''
        result = component_extractor.extract(code, "events.ts")
        comps = result['components']
        assert len(comps) >= 1
        assert 'item-selected' in comps[0].events_dispatched

    def test_extends_html_element(self, component_extractor):
        code = '''
        class VanillaElement extends HTMLElement {
            connectedCallback() {
                this.attachShadow({ mode: 'open' });
            }
        }
        customElements.define('vanilla-element', VanillaElement);
        '''
        result = component_extractor.extract(code, "vanilla.ts")
        comps = result['components']
        assert len(comps) >= 1
        assert comps[0].superclass == "HTMLElement"


# ═══════════════════════════════════════════════════════════════════
# Property Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestLitPropertyExtractor:

    def test_property_decorator(self, property_extractor):
        code = '''
        @customElement('prop-demo')
        class PropDemo extends LitElement {
            @property({ type: String }) name = '';
            @property({ type: Number }) count = 0;
            @property({ type: Boolean }) active = false;
        }
        '''
        result = property_extractor.extract(code, "props.ts")
        props = result['properties']
        assert len(props) >= 3
        names = [p.name for p in props]
        assert 'name' in names
        assert 'count' in names

    def test_property_with_reflect(self, property_extractor):
        code = '''
        class ReflectDemo extends LitElement {
            @property({ type: String, reflect: true }) label = '';
        }
        '''
        result = property_extractor.extract(code, "reflect.ts")
        props = result['properties']
        assert len(props) >= 1
        assert props[0].has_reflect is True

    def test_property_with_converter(self, property_extractor):
        code = '''
        class ConverterDemo extends LitElement {
            @property({type: String, converter: myConverter})
            date = new Date();
        }
        '''
        result = property_extractor.extract(code, "converter.ts")
        props = result['properties']
        assert len(props) >= 1
        assert props[0].has_converter is True

    def test_property_with_has_changed(self, property_extractor):
        code = '''
        class ChangedDemo extends LitElement {
            @property({
                hasChanged: (newVal, oldVal) => newVal !== oldVal,
            })
            config = {};
        }
        '''
        result = property_extractor.extract(code, "changed.ts")
        props = result['properties']
        assert len(props) >= 1
        assert props[0].has_has_changed is True

    def test_state_decorator(self, property_extractor):
        code = '''
        class StateDemo extends LitElement {
            @state() private _isOpen = false;
            @state() _selectedIndex = -1;
        }
        '''
        result = property_extractor.extract(code, "state.ts")
        states = result['states']
        assert len(states) >= 2

    def test_static_properties(self, property_extractor):
        code = '''
        class StaticDemo extends LitElement {
            static properties = {
                name: { type: String },
                count: { type: Number, reflect: true },
                items: { type: Array },
            };
        }
        '''
        result = property_extractor.extract(code, "static.ts")
        props = result['properties']
        assert len(props) >= 3

    def test_static_get_properties(self, property_extractor):
        code = '''
        class GetterDemo extends LitElement {
            static get properties() {
                return {
                    name: { type: String },
                    active: { type: Boolean },
                };
            }
        }
        '''
        result = property_extractor.extract(code, "getter.ts")
        props = result['properties']
        assert len(props) >= 2

    def test_property_type_annotation(self, property_extractor):
        code = '''
        class TypedDemo extends LitElement {
            @property({ type: Number }) count: number = 0;
            @property({ type: String }) name: string = '';
        }
        '''
        result = property_extractor.extract(code, "typed.ts")
        props = result['properties']
        assert len(props) >= 2


# ═══════════════════════════════════════════════════════════════════
# Event Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestLitEventExtractor:

    def test_custom_event_dispatch(self, event_extractor):
        code = '''
        class EventDemo extends LitElement {
            _onClick() {
                this.dispatchEvent(new CustomEvent('item-click', {detail: this.id, bubbles: true, composed: true}));
            }
        }
        '''
        result = event_extractor.extract(code, "events.ts")
        events = result['events']
        assert len(events) >= 1
        assert events[0].name == 'item-click'
        assert events[0].has_bubbles is True
        assert events[0].has_composed is True

    def test_event_with_detail(self, event_extractor):
        code = '''
        this.dispatchEvent(new CustomEvent('selection-changed', {
            detail: { selected: this.selected, index: idx },
        }));
        '''
        result = event_extractor.extract(code, "event.ts")
        events = result['events']
        assert len(events) >= 1
        assert events[0].has_detail is True

    def test_event_options_decorator(self, event_extractor):
        code = '''
        class ScrollDemo extends LitElement {
            @eventOptions({ passive: true })
            _handleScroll(e) {
                console.log(e);
            }
            render() {
                return html`<div @scroll=${this._handleScroll}></div>`;
            }
        }
        '''
        result = event_extractor.extract(code, "scroll.ts")
        listeners = result.get('listeners', [])
        # Template binding + @eventOptions should be detected
        assert len(listeners) >= 1
        assert listeners[0].handler_name == '_handleScroll'

    def test_template_event_binding(self, event_extractor):
        code = '''
        render() {
            return html`
                <button @click=${this._handleClick}>Click</button>
                <input @input=${this._handleInput}>
                <form @submit=${this._handleSubmit}>
            `;
        }
        '''
        result = event_extractor.extract(code, "bindings.ts")
        listeners = result.get('listeners', [])
        assert len(listeners) >= 3

    def test_add_event_listener(self, event_extractor):
        code = '''
        connectedCallback() {
            super.connectedCallback();
            this.addEventListener('resize', this._handleResize);
            window.addEventListener('scroll', this._handleScroll);
        }
        '''
        result = event_extractor.extract(code, "listener.ts")
        listeners = result.get('listeners', [])
        assert len(listeners) >= 2

    def test_polymer_fire(self, event_extractor):
        code = '''
        Polymer({
            is: 'old-element',
            _onClick: function() {
                this.fire('item-clicked', { item: this.item });
            }
        });
        '''
        result = event_extractor.extract(code, "polymer.js")
        events = result.get('events', [])
        assert len(events) >= 1

    def test_multiple_custom_events(self, event_extractor):
        code = '''
        class MultiEvent extends LitElement {
            open() {
                this.dispatchEvent(new CustomEvent('dialog-open'));
            }
            close() {
                this.dispatchEvent(new CustomEvent('dialog-close'));
            }
            confirm() {
                this.dispatchEvent(new CustomEvent('dialog-confirm', {
                    detail: { confirmed: true },
                    bubbles: true,
                    composed: true,
                }));
            }
        }
        '''
        result = event_extractor.extract(code, "multi.ts")
        events = result['events']
        assert len(events) >= 3


# ═══════════════════════════════════════════════════════════════════
# Template Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestLitTemplateExtractor:

    def test_html_template(self, template_extractor):
        code = '''
        render() {
            return html`<div class="card"><p>${this.name}</p></div>`;
        }
        '''
        result = template_extractor.extract(code, "template.ts")
        templates = result['templates']
        assert len(templates) >= 1
        assert templates[0].template_type == 'html'

    def test_svg_template(self, template_extractor):
        code = '''
        render() {
            return svg`<circle cx="50" cy="50" r="40"/>`;
        }
        '''
        result = template_extractor.extract(code, "svg.ts")
        templates = result['templates']
        assert len(templates) >= 1
        assert templates[0].template_type == 'svg'

    def test_css_tagged_template(self, template_extractor):
        code = '''
        static styles = css`
            :host { display: block; }
            .title { font-weight: bold; }
        `;
        '''
        result = template_extractor.extract(code, "styles.ts")
        css_info = result.get('css_styles', [])
        assert len(css_info) >= 1

    def test_property_bindings(self, template_extractor):
        code = '''
        render() {
            return html`<child-el .items=${this.items} .config=${this.config}></child-el>`;
        }
        '''
        result = template_extractor.extract(code, "prop-bind.ts")
        templates = result['templates']
        assert len(templates) >= 1
        assert templates[0].property_bindings >= 2

    def test_boolean_bindings(self, template_extractor):
        code = '''
        render() {
            return html`<button ?disabled=${this.loading} ?hidden=${this.invisible}>Go</button>`;
        }
        '''
        result = template_extractor.extract(code, "bool-bind.ts")
        templates = result['templates']
        assert len(templates) >= 1
        assert templates[0].attribute_bindings >= 2

    def test_event_bindings(self, template_extractor):
        code = '''
        render() {
            return html`<button @click=${this._handleClick} @keydown=${this._handleKey}>Go</button>`;
        }
        '''
        result = template_extractor.extract(code, "event-bind.ts")
        templates = result['templates']
        assert len(templates) >= 1
        assert templates[0].event_bindings >= 2

    def test_slot_detection(self, template_extractor):
        code = '''
        render() {
            return html`
                <header><slot name="header"></slot></header>
                <main><slot></slot></main>
                <footer><slot name="footer"></slot></footer>
            `;
        }
        '''
        result = template_extractor.extract(code, "slots.ts")
        templates = result['templates']
        assert len(templates) >= 1
        assert templates[0].has_slot is True

    def test_conditional_rendering(self, template_extractor):
        code = '''
        render() {
            return html`
                ${this.loading
                    ? html`<spinner-element></spinner-element>`
                    : html`<data-view .data=${this.data}></data-view>`
                }
            `;
        }
        '''
        result = template_extractor.extract(code, "conditional.ts")
        templates = result['templates']
        assert len(templates) >= 1

    def test_directive_repeat(self, template_extractor):
        code = '''
        import { repeat } from 'lit/directives/repeat.js';
        render() {
            return html`
                ${repeat(this.items, (item) => item.id, (item) => html`
                    <div>${item.name}</div>
                `)}
            `;
        }
        '''
        result = template_extractor.extract(code, "repeat.ts")
        directives = result.get('directives', [])
        assert len(directives) >= 1
        assert directives[0].directive_name == 'repeat'

    def test_directive_classmap(self, template_extractor):
        code = '''
        import { classMap } from 'lit/directives/class-map.js';
        render() {
            return html`<div class=${classMap({active: this.active})}></div>`;
        }
        '''
        result = template_extractor.extract(code, "classmap.ts")
        directives = result.get('directives', [])
        assert len(directives) >= 1
        assert directives[0].directive_name == 'classMap'

    def test_directive_stylemap(self, template_extractor):
        code = '''
        import { styleMap } from 'lit/directives/style-map.js';
        render() {
            return html`<div style=${styleMap({color: this.color})}></div>`;
        }
        '''
        result = template_extractor.extract(code, "stylemap.ts")
        directives = result.get('directives', [])
        assert len(directives) >= 1
        assert directives[0].directive_name == 'styleMap'

    def test_directive_when(self, template_extractor):
        code = '''
        import { when } from 'lit/directives/when.js';
        render() {
            return html`
                ${when(this.loggedIn,
                    () => html`<user-panel></user-panel>`,
                    () => html`<login-form></login-form>`
                )}
            `;
        }
        '''
        result = template_extractor.extract(code, "when.ts")
        directives = result.get('directives', [])
        assert any(d.directive_name == 'when' for d in directives)

    def test_directive_ref(self, template_extractor):
        code = '''
        import { ref, createRef } from 'lit/directives/ref.js';
        _inputRef = createRef();
        render() {
            return html`<input ${ref(this._inputRef)}>`;
        }
        '''
        result = template_extractor.extract(code, "ref.ts")
        directives = result.get('directives', [])
        assert any(d.directive_name == 'ref' for d in directives)

    def test_directive_cache(self, template_extractor):
        code = '''
        import { cache } from 'lit/directives/cache.js';
        render() {
            return html`${cache(this.show ? html`<a></a>` : html`<b></b>`)}`;
        }
        '''
        result = template_extractor.extract(code, "cache.ts")
        directives = result.get('directives', [])
        assert any(d.directive_name == 'cache' for d in directives)

    def test_directive_unsafe_html(self, template_extractor):
        code = '''
        import { unsafeHTML } from 'lit/directives/unsafe-html.js';
        render() {
            return html`<div>${unsafeHTML(this.content)}</div>`;
        }
        '''
        result = template_extractor.extract(code, "unsafe.ts")
        directives = result.get('directives', [])
        assert any(d.directive_name == 'unsafeHTML' for d in directives)

    def test_css_host_selector(self, template_extractor):
        code = '''
        static styles = css`
            :host { display: block; padding: 16px; }
            :host([disabled]) { opacity: 0.5; }
        `;
        '''
        result = template_extractor.extract(code, "host.ts")
        css_info = result.get('css_styles', [])
        assert len(css_info) >= 1
        assert css_info[0].has_host_selector is True

    def test_css_part_selector(self, template_extractor):
        code = '''
        static styles = css`
            ::part(button) { background: blue; }
        `;
        '''
        result = template_extractor.extract(code, "part.ts")
        css_info = result.get('css_styles', [])
        assert len(css_info) >= 1
        assert css_info[0].has_part_selector is True

    def test_css_slotted_selector(self, template_extractor):
        code = '''
        static styles = css`
            ::slotted(p) { margin: 0; }
        `;
        '''
        result = template_extractor.extract(code, "slotted.ts")
        css_info = result.get('css_styles', [])
        assert len(css_info) >= 1
        assert css_info[0].has_slotted_selector is True

    def test_css_custom_properties(self, template_extractor):
        code = '''
        static styles = css`
            :host {
                --card-bg: var(--app-surface, #fff);
                --card-radius: 8px;
            }
        `;
        '''
        result = template_extractor.extract(code, "vars.ts")
        css_info = result.get('css_styles', [])
        assert len(css_info) >= 1
        assert css_info[0].has_css_custom_properties is True

    def test_adopted_stylesheets(self, template_extractor):
        code = '''
        const sheet = new CSSStyleSheet();
        sheet.replaceSync(':host { display: block; }');
        document.adoptedStyleSheets = [...document.adoptedStyleSheets, sheet];
        '''
        result = template_extractor.extract(code, "adopted.ts")
        css_info = result.get('css_styles', [])
        assert len(css_info) >= 1
        assert css_info[0].style_type == 'adopted'


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestLitApiExtractor:

    def test_core_import(self, api_extractor):
        code = '''
        import { LitElement, html, css } from 'lit';
        '''
        result = api_extractor.extract(code, "core.ts")
        imports = result['imports']
        assert len(imports) >= 1
        assert imports[0].source == 'lit'
        assert imports[0].import_category == 'core'
        assert 'LitElement' in imports[0].named_imports

    def test_decorator_import(self, api_extractor):
        code = '''
        import { customElement, property, state } from 'lit/decorators.js';
        '''
        result = api_extractor.extract(code, "decorators.ts")
        imports = result['imports']
        assert len(imports) >= 1
        assert imports[0].import_category == 'decorators'

    def test_directive_import(self, api_extractor):
        code = '''
        import { repeat } from 'lit/directives/repeat.js';
        import { classMap } from 'lit/directives/class-map.js';
        '''
        result = api_extractor.extract(code, "directives.ts")
        imports = result['imports']
        assert len(imports) >= 2
        assert any(i.import_category == 'directives' for i in imports)

    def test_labs_import(self, api_extractor):
        code = '''
        import { Task } from '@lit-labs/task';
        import { ContextProvider } from '@lit-labs/context';
        '''
        result = api_extractor.extract(code, "labs.ts")
        imports = result['imports']
        assert len(imports) >= 2
        assert any(i.import_category == 'labs' for i in imports)

    def test_stable_lit_packages(self, api_extractor):
        code = '''
        import { Task } from '@lit/task';
        import { createContext, provide, consume } from '@lit/context';
        import { msg, localized } from '@lit/localize';
        '''
        result = api_extractor.extract(code, "stable.ts")
        imports = result['imports']
        assert len(imports) >= 3

    def test_lit_element_standalone_import(self, api_extractor):
        code = '''
        import { LitElement, html, css } from 'lit-element';
        '''
        result = api_extractor.extract(code, "standalone.ts")
        imports = result['imports']
        assert len(imports) >= 1
        assert imports[0].source == 'lit-element'
        assert imports[0].import_category == 'core'

    def test_lit_html_standalone_import(self, api_extractor):
        code = '''
        import { html, render } from 'lit-html';
        '''
        result = api_extractor.extract(code, "lithtml.ts")
        imports = result['imports']
        assert len(imports) >= 1
        assert imports[0].source == 'lit-html'
        assert imports[0].import_category == 'core'

    def test_polymer_import(self, api_extractor):
        code = '''
        import { PolymerElement } from '@polymer/polymer';
        '''
        result = api_extractor.extract(code, "polymer.ts")
        imports = result['imports']
        assert len(imports) >= 1
        assert imports[0].import_category == 'polymer'

    def test_vaadin_integration(self, api_extractor):
        code = '''
        import { Grid } from '@vaadin/grid';
        import { Button } from '@vaadin/button';
        '''
        result = api_extractor.extract(code, "vaadin.ts")
        integrations = result['integrations']
        assert any(i.name == 'vaadin' for i in integrations)

    def test_shoelace_integration(self, api_extractor):
        code = '''
        import { SlButton } from '@shoelace-style/shoelace/dist/components/button/button.js';
        '''
        result = api_extractor.extract(code, "shoelace.ts")
        integrations = result['integrations']
        assert any(i.name == 'shoelace' for i in integrations)

    def test_open_wc_testing(self, api_extractor):
        code = '''
        import { fixture, html, expect } from '@open-wc/testing';
        '''
        result = api_extractor.extract(code, "test.ts")
        integrations = result['integrations']
        assert any(i.name == 'open-wc-testing' for i in integrations)

    def test_ssr_patterns(self, api_extractor):
        code = '''
        import { render } from '@lit-labs/ssr';
        import { LitElementRenderer } from '@lit-labs/ssr/lib/lit-element-renderer.js';
        '''
        result = api_extractor.extract(code, "ssr.ts")
        ssr_patterns = result['ssr_patterns']
        assert len(ssr_patterns) >= 1

    def test_typescript_types(self, api_extractor):
        code = '''
        import { LitElement, PropertyValues, CSSResult } from 'lit';
        class MyEl extends LitElement {
            updated(changedProperties: PropertyValues) {}
        }
        '''
        result = api_extractor.extract(code, "types.ts")
        types = result['types']
        assert any(t.type_name == 'PropertyValues' for t in types)

    def test_type_import(self, api_extractor):
        code = '''
        import type { ReactiveController, ReactiveControllerHost } from 'lit';
        '''
        result = api_extractor.extract(code, "typeimport.ts")
        imports = result['imports']
        assert len(imports) >= 1
        assert imports[0].is_type_import is True

    def test_multiple_sources(self, api_extractor):
        code = '''
        import { LitElement, html } from 'lit';
        import { customElement, property } from 'lit/decorators.js';
        import { repeat } from 'lit/directives/repeat.js';
        import { Task } from '@lit/task';
        '''
        result = api_extractor.extract(code, "multi.ts")
        imports = result['imports']
        assert len(imports) >= 4
        categories = {i.import_category for i in imports}
        assert 'core' in categories
        assert 'decorators' in categories


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedLitParser:

    def test_is_lit_file_core(self, parser):
        code = "import { LitElement, html } from 'lit';"
        assert parser.is_lit_file(code) is True

    def test_is_lit_file_lit_element(self, parser):
        code = "import { LitElement } from 'lit-element';"
        assert parser.is_lit_file(code) is True

    def test_is_lit_file_lit_html(self, parser):
        code = "import { html, render } from 'lit-html';"
        assert parser.is_lit_file(code) is True

    def test_is_lit_file_decorators(self, parser):
        code = "import { customElement, property } from 'lit/decorators.js';"
        assert parser.is_lit_file(code) is True

    def test_is_lit_file_polymer(self, parser):
        code = "import { PolymerElement } from '@polymer/polymer';"
        assert parser.is_lit_file(code) is True

    def test_is_lit_file_labs(self, parser):
        code = "import { Task } from '@lit-labs/task';"
        assert parser.is_lit_file(code) is True

    def test_is_lit_file_context(self, parser):
        code = "import { createContext } from '@lit/context';"
        assert parser.is_lit_file(code) is True

    def test_is_lit_file_custom_element_pattern(self, parser):
        code = "customElements.define('my-el', MyElement);"
        assert parser.is_lit_file(code) is True

    def test_is_lit_file_extends_pattern(self, parser):
        code = "class MyEl extends LitElement {}"
        assert parser.is_lit_file(code) is True

    def test_is_not_lit_file(self, parser):
        code = "import React from 'react';\nconst App = () => <div>Hello</div>;"
        assert parser.is_lit_file(code) is False

    def test_parse_returns_result(self, parser):
        code = '''
        import { LitElement, html, css } from 'lit';
        import { customElement, property } from 'lit/decorators.js';

        @customElement('my-element')
        export class MyElement extends LitElement {
            @property({ type: String }) name = '';
            @state() _count = 0;

            static styles = css`:host { display: block; }`;

            render() {
                return html`<p>Hello ${this.name}! Count: ${this._count}</p>`;
            }
        }
        '''
        result = parser.parse(code, "my-element.ts")
        assert isinstance(result, LitParseResult)
        assert result.file_path == "my-element.ts"
        assert result.file_type == "ts"
        assert len(result.components) >= 1
        assert len(result.imports) >= 1

    def test_parse_full_component(self, parser):
        code = '''
        import { LitElement, html, css } from 'lit';
        import { customElement, property, state } from 'lit/decorators.js';
        import { repeat } from 'lit/directives/repeat.js';
        import { classMap } from 'lit/directives/class-map.js';

        @customElement('todo-list')
        export class TodoList extends LitElement {
            @property({ type: Array }) items = [];
            @state() private _filter = 'all';

            static styles = css`
                :host { display: block; }
                .completed { text-decoration: line-through; }
            `;

            render() {
                return html`
                    <ul>
                        ${repeat(this.items, (i) => i.id, (item) => html`
                            <li class=${classMap({ completed: item.done })}
                                @click=${() => this._toggle(item)}>
                                ${item.text}
                            </li>
                        `)}
                    </ul>
                `;
            }

            _toggle(item) {
                this.dispatchEvent(new CustomEvent('item-toggled', {
                    detail: { item },
                    bubbles: true,
                    composed: true,
                }));
            }
        }
        '''
        result = parser.parse(code, "todo-list.ts")
        assert len(result.components) >= 1
        assert result.components[0].name == "TodoList"
        assert len(result.properties) >= 1
        assert len(result.templates) >= 1
        assert len(result.events) >= 1
        assert len(result.imports) >= 1

    # ─── Version Detection ─────────────────────────────────────────

    def test_detect_version_lit_3(self, parser):
        code = "import { Task } from '@lit/task';"
        result = parser.parse(code, "task.ts")
        assert result.lit_version == "lit-3"

    def test_detect_version_lit_3_context(self, parser):
        code = "import { createContext } from '@lit/context';"
        result = parser.parse(code, "context.ts")
        assert result.lit_version == "lit-3"

    def test_detect_version_lit_2(self, parser):
        code = "import { LitElement } from 'lit';"
        result = parser.parse(code, "lit2.ts")
        assert result.lit_version == "lit-2"

    def test_detect_version_lit_element_2(self, parser):
        code = "import { LitElement } from 'lit-element';"
        result = parser.parse(code, "litel2.ts")
        assert result.lit_version == "lit-element-2"

    def test_detect_version_polymer_3(self, parser):
        code = "import { PolymerElement } from '@polymer/polymer';"
        result = parser.parse(code, "poly3.ts")
        assert result.lit_version == "polymer-3"

    def test_detect_version_polymer_2(self, parser):
        code = "class MyEl extends Polymer.Element {}"
        result = parser.parse(code, "poly2.js")
        assert result.lit_version == "polymer-2"

    def test_detect_version_polymer_1(self, parser):
        code = "Polymer({ is: 'my-el' });"
        result = parser.parse(code, "poly1.js")
        assert result.lit_version == "polymer-1"

    # ─── Framework Detection ───────────────────────────────────────

    def test_detect_framework_lit(self, parser):
        code = "import { LitElement } from 'lit';"
        result = parser.parse(code, "test.ts")
        assert 'lit' in result.detected_frameworks

    def test_detect_framework_lit_decorators(self, parser):
        code = "import { customElement } from 'lit/decorators.js';"
        result = parser.parse(code, "test.ts")
        assert 'lit-decorators' in result.detected_frameworks

    def test_detect_framework_vaadin(self, parser):
        code = "import { Grid } from '@vaadin/grid';"
        result = parser.parse(code, "test.ts")
        assert 'vaadin' in result.detected_frameworks

    def test_detect_framework_polymer(self, parser):
        code = "import { PolymerElement } from '@polymer/polymer';"
        result = parser.parse(code, "test.ts")
        assert 'polymer' in result.detected_frameworks

    def test_detect_framework_stencil(self, parser):
        code = "import { Component, Prop } from '@stencil/core';"
        result = parser.parse(code, "test.ts")
        assert 'stencil' in result.detected_frameworks

    # ─── Feature Detection ─────────────────────────────────────────

    def test_detect_feature_custom_element_decorator(self, parser):
        code = "@customElement('my-el') class MyEl extends LitElement {}"
        result = parser.parse(code, "test.ts")
        assert 'custom_element_decorator' in result.detected_features

    def test_detect_feature_property_decorator(self, parser):
        code = "@property({ type: String }) name = '';"
        result = parser.parse(code, "test.ts")
        assert 'property_decorator' in result.detected_features

    def test_detect_feature_html_template(self, parser):
        code = "html`<p>Hello</p>`;"
        result = parser.parse(code, "test.ts")
        assert 'html_template' in result.detected_features

    def test_detect_feature_css_template(self, parser):
        code = "css`:host { display: block; }`;"
        result = parser.parse(code, "test.ts")
        assert 'css_template' in result.detected_features

    def test_detect_feature_shadow_dom(self, parser):
        code = "createRenderRoot() { return this; }"
        result = parser.parse(code, "test.ts")
        assert 'shadow_dom' in result.detected_features

    def test_detect_feature_dispatch_event(self, parser):
        code = "this.dispatchEvent(new CustomEvent('test'));"
        result = parser.parse(code, "test.ts")
        assert 'dispatch_event' in result.detected_features

    def test_detect_feature_reactive_controller(self, parser):
        code = "class MyCtrl implements ReactiveController {}"
        result = parser.parse(code, "test.ts")
        assert 'reactive_controller' in result.detected_features

    def test_detect_feature_slot(self, parser):
        code = "html`<slot name='header'></slot>`;"
        result = parser.parse(code, "test.ts")
        assert 'slot_element' in result.detected_features

    def test_detect_feature_host_selector(self, parser):
        code = "css`:host { display: block; }`;"
        result = parser.parse(code, "test.ts")
        assert 'host_selector' in result.detected_features

    def test_detect_feature_repeat(self, parser):
        code = "repeat(items, i => i.id, i => html`${i}`);"
        result = parser.parse(code, "test.ts")
        assert 'repeat_directive' in result.detected_features

    # ─── File Type Detection ───────────────────────────────────────

    def test_file_type_ts(self, parser):
        result = parser.parse("", "component.ts")
        assert result.file_type == "ts"

    def test_file_type_js(self, parser):
        result = parser.parse("", "component.js")
        assert result.file_type == "js"

    def test_file_type_tsx(self, parser):
        result = parser.parse("", "component.tsx")
        assert result.file_type == "tsx"

    def test_file_type_mjs(self, parser):
        result = parser.parse("", "component.mjs")
        assert result.file_type == "js"

    # ─── Version Comparison ────────────────────────────────────────

    def test_version_compare_lit3_gt_lit2(self):
        assert EnhancedLitParser._version_compare('lit-3', 'lit-2') > 0

    def test_version_compare_lit2_gt_lit_element_2(self):
        assert EnhancedLitParser._version_compare('lit-2', 'lit-element-2') > 0

    def test_version_compare_lit_element_2_gt_polymer_3(self):
        assert EnhancedLitParser._version_compare('lit-element-2', 'polymer-3') > 0

    def test_version_compare_polymer_3_gt_polymer_1(self):
        assert EnhancedLitParser._version_compare('polymer-3', 'polymer-1') > 0

    def test_version_compare_equal(self):
        assert EnhancedLitParser._version_compare('lit-2', 'lit-2') == 0

    def test_version_compare_empty(self):
        assert EnhancedLitParser._version_compare('', '') == 0

    # ─── Error Handling ────────────────────────────────────────────

    def test_parse_empty_content(self, parser):
        result = parser.parse("", "empty.ts")
        assert isinstance(result, LitParseResult)
        assert len(result.components) == 0

    def test_parse_non_lit_content(self, parser):
        result = parser.parse("const x = 42;", "plain.ts")
        assert isinstance(result, LitParseResult)
        assert len(result.components) == 0

    def test_parse_malformed_code(self, parser):
        code = "@customElement('broken class extends {"
        result = parser.parse(code, "broken.ts")
        assert isinstance(result, LitParseResult)
