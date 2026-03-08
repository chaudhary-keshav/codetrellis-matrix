"""
Tests for Alpine.js parser enhanced (v4.66).

Tests cover:
- DirectiveExtractor: core directives, shorthand, modifiers, version hints
- ComponentExtractor: Alpine.data(), inline x-data, methods, getters
- StoreExtractor: Alpine.store(), $store access, $persist
- PluginExtractor: Alpine.plugin(), @alpinejs/*, custom directives/magics
- ApiExtractor: imports, CDN detection, integrations, types
- EnhancedAlpineParser: is_alpine_file, parse, version detection, framework detection

Part of CodeTrellis v4.66 - Alpine.js Framework Support.
"""

import pytest
from codetrellis.alpinejs_parser_enhanced import EnhancedAlpineParser, AlpineParseResult
from codetrellis.extractors.alpinejs import (
    AlpineDirectiveExtractor, AlpineDirectiveInfo,
    AlpineComponentExtractor, AlpineComponentInfo, AlpineMethodInfo,
    AlpineStoreExtractor, AlpineStoreInfo,
    AlpinePluginExtractor, AlpinePluginInfo, AlpineCustomDirectiveInfo, AlpineCustomMagicInfo,
    AlpineApiExtractor, AlpineImportInfo, AlpineIntegrationInfo, AlpineTypeInfo, AlpineCDNInfo,
)


# ============================================================================
# DirectiveExtractor Tests
# ============================================================================

class TestDirectiveExtractor:
    """Tests for AlpineDirectiveExtractor."""

    def setup_method(self):
        self.extractor = AlpineDirectiveExtractor()

    def test_empty_content(self):
        result = self.extractor.extract("", "test.html")
        assert result == []

    def test_x_data_directive(self):
        content = '<div x-data="{ open: false }">'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1
        xdata = [d for d in result if d.directive_name == "x-data"]
        assert len(xdata) == 1
        assert "open" in xdata[0].directive_value

    def test_x_show_directive(self):
        content = '<div x-show="isVisible">content</div>'
        result = self.extractor.extract(content, "test.html")
        names = [d.directive_name for d in result]
        assert "x-show" in names

    def test_x_if_directive(self):
        content = '<template x-if="loggedIn"><div>Hi</div></template>'
        result = self.extractor.extract(content, "test.html")
        names = [d.directive_name for d in result]
        assert "x-if" in names

    def test_x_for_directive(self):
        content = '<template x-for="item in items" :key="item.id"><div x-text="item.name"></div></template>'
        result = self.extractor.extract(content, "test.html")
        names = [d.directive_name for d in result]
        assert "x-for" in names

    def test_x_bind_shorthand(self):
        content = '<div :class="active ? \'bg-blue\' : \'\'">'
        result = self.extractor.extract(content, "test.html")
        bind_dirs = [d for d in result if d.directive_name == "x-bind"]
        assert len(bind_dirs) >= 1
        assert bind_dirs[0].is_shorthand is True

    def test_x_on_shorthand(self):
        content = '<button @click="handleClick()">Click</button>'
        result = self.extractor.extract(content, "test.html")
        on_dirs = [d for d in result if d.directive_name == "x-on"]
        assert len(on_dirs) >= 1
        assert on_dirs[0].is_shorthand is True

    def test_x_model_directive(self):
        content = '<input x-model="searchQuery">'
        result = self.extractor.extract(content, "test.html")
        names = [d.directive_name for d in result]
        assert "x-model" in names

    def test_x_model_debounce_modifier(self):
        content = '<input x-model.debounce.300ms="query">'
        result = self.extractor.extract(content, "test.html")
        model_dirs = [d for d in result if d.directive_name == "x-model"]
        assert len(model_dirs) >= 1
        assert "debounce" in (model_dirs[0].modifiers or [])

    def test_x_transition_directive(self):
        content = '<div x-show="open" x-transition>'
        result = self.extractor.extract(content, "test.html")
        names = [d.directive_name for d in result]
        assert "x-transition" in names

    def test_x_effect_v3(self):
        content = '<div x-effect="console.log(count)">'
        result = self.extractor.extract(content, "test.html")
        effect_dirs = [d for d in result if d.directive_name == "x-effect"]
        assert len(effect_dirs) >= 1
        assert effect_dirs[0].version_hint == "v3"

    def test_x_teleport_v3(self):
        content = '<template x-teleport="body"><div>Portal</div></template>'
        result = self.extractor.extract(content, "test.html")
        teleport_dirs = [d for d in result if d.directive_name == "x-teleport"]
        assert len(teleport_dirs) >= 1
        assert teleport_dirs[0].version_hint == "v3"

    def test_x_ref_directive(self):
        content = '<input x-ref="nameInput" type="text">'
        result = self.extractor.extract(content, "test.html")
        names = [d.directive_name for d in result]
        assert "x-ref" in names

    def test_x_text_directive(self):
        content = '<span x-text="message"></span>'
        result = self.extractor.extract(content, "test.html")
        names = [d.directive_name for d in result]
        assert "x-text" in names

    def test_x_html_directive(self):
        content = '<div x-html="richContent"></div>'
        result = self.extractor.extract(content, "test.html")
        names = [d.directive_name for d in result]
        assert "x-html" in names

    def test_x_init_directive(self):
        content = '<div x-init="fetchData()">'
        result = self.extractor.extract(content, "test.html")
        names = [d.directive_name for d in result]
        assert "x-init" in names

    def test_x_cloak_directive(self):
        content = '<div x-cloak>'
        result = self.extractor.extract(content, "test.html")
        names = [d.directive_name for d in result]
        assert "x-cloak" in names

    def test_x_ignore_v3(self):
        content = '<div x-ignore><p>Static</p></div>'
        result = self.extractor.extract(content, "test.html")
        ignore_dirs = [d for d in result if d.directive_name == "x-ignore"]
        assert len(ignore_dirs) >= 1

    def test_x_spread_v1(self):
        content = '<div x-spread="buttonBindings">'
        result = self.extractor.extract(content, "test.html")
        spread_dirs = [d for d in result if d.directive_name == "x-spread"]
        assert len(spread_dirs) >= 1
        assert spread_dirs[0].version_hint == "v1"

    def test_plugin_directive_x_mask(self):
        content = '<input x-mask="(999) 999-9999">'
        result = self.extractor.extract(content, "test.html")
        mask_dirs = [d for d in result if d.directive_name == "x-mask"]
        assert len(mask_dirs) >= 1

    def test_plugin_directive_x_intersect(self):
        content = '<div x-intersect="visible = true">Content</div>'
        result = self.extractor.extract(content, "test.html")
        names = [d.directive_name for d in result]
        assert "x-intersect" in names

    def test_event_with_modifier(self):
        content = '<form @submit.prevent="handleSubmit()">'
        result = self.extractor.extract(content, "test.html")
        on_dirs = [d for d in result if d.directive_name == "x-on"]
        assert len(on_dirs) >= 1
        # Modifier may be in modifiers list or embedded in event_name
        d = on_dirs[0]
        assert "prevent" in (d.modifiers or []) or "prevent" in (d.event_name or "")

    def test_multiple_directives_same_element(self):
        content = '<div x-data="{ count: 0 }" x-init="count = 1" x-effect="console.log(count)">'
        result = self.extractor.extract(content, "test.html")
        names = [d.directive_name for d in result]
        assert "x-data" in names
        assert "x-init" in names
        assert "x-effect" in names

    def test_line_numbers(self):
        content = 'line1\n<div x-data="{ a: 1 }">\nline3\n<span x-text="a"></span>'
        result = self.extractor.extract(content, "test.html")
        xdata = [d for d in result if d.directive_name == "x-data"]
        xtext = [d for d in result if d.directive_name == "x-text"]
        assert xdata[0].line_number == 2
        assert xtext[0].line_number == 4


# ============================================================================
# ComponentExtractor Tests
# ============================================================================

class TestComponentExtractor:
    """Tests for AlpineComponentExtractor."""

    def setup_method(self):
        self.extractor = AlpineComponentExtractor()

    def test_empty_content(self):
        comps, methods = self.extractor.extract("", "test.js")
        assert comps == []
        assert methods == []

    def test_alpine_data_registration(self):
        content = """
Alpine.data('dropdown', () => ({
    open: false,
    toggle() { this.open = !this.open },
    close() { this.open = false },
}));
"""
        comps, methods = self.extractor.extract(content, "test.js")
        assert len(comps) >= 1
        assert comps[0].name == "dropdown"
        assert comps[0].component_type == "registered"

    def test_alpine_data_with_init(self):
        content = """
Alpine.data('userList', () => ({
    users: [],
    loading: true,
    init() {
        this.users = [];
        this.loading = false;
    },
}));
"""
        comps, methods = self.extractor.extract(content, "test.js")
        assert len(comps) >= 1
        assert comps[0].has_init is True

    def test_alpine_data_with_destroy(self):
        content = """
Alpine.data('timer', () => ({
    interval: null,
    init() { this.interval = setInterval(() => {}, 1000); },
    destroy() { clearInterval(this.interval); },
}));
"""
        comps, methods = self.extractor.extract(content, "test.js")
        assert len(comps) >= 1
        assert comps[0].has_destroy is True

    def test_inline_xdata(self):
        content = '<div x-data="{ count: 0, name: \'test\' }">'
        comps, methods = self.extractor.extract(content, "test.html")
        assert len(comps) >= 1
        assert comps[0].component_type == "inline"

    def test_getter_detection(self):
        content = """
Alpine.data('cart', () => ({
    items: [],
    get total() {
        return this.items.reduce((s, i) => s + i.price, 0);
    },
}));
"""
        comps, methods = self.extractor.extract(content, "test.js")
        assert len(comps) >= 1
        assert "total" in comps[0].computed_getters

    def test_method_extraction(self):
        content = """
Alpine.data('form', () => ({
    data: {},
    async submit() { await fetch('/api', { body: JSON.stringify(this.data) }); },
    validate() { return true; },
}));
"""
        comps, methods = self.extractor.extract(content, "test.js")
        assert len(methods) >= 2
        method_names = [m.name for m in methods]
        assert "submit" in method_names
        assert "validate" in method_names

    def test_magic_property_detection(self):
        content = """
Alpine.data('notifier', () => ({
    notify(msg) {
        this.$dispatch('notification', { message: msg });
        this.$refs.bell.classList.add('ring');
    },
}));
"""
        comps, methods = self.extractor.extract(content, "test.js")
        if comps:
            magics = comps[0].magics_used
            # Extractor may store with or without $ prefix
            assert "dispatch" in magics or "$dispatch" in magics or "refs" in magics or "$refs" in magics

    def test_multiple_components(self):
        content = """
Alpine.data('dropdown', () => ({ open: false }));
Alpine.data('modal', () => ({ visible: false }));
Alpine.data('tabs', () => ({ active: 0 }));
"""
        comps, methods = self.extractor.extract(content, "test.js")
        assert len(comps) >= 3
        names = [c.name for c in comps]
        assert "dropdown" in names
        assert "modal" in names
        assert "tabs" in names


# ============================================================================
# StoreExtractor Tests
# ============================================================================

class TestStoreExtractor:
    """Tests for AlpineStoreExtractor."""

    def setup_method(self):
        self.extractor = AlpineStoreExtractor()

    def test_empty_content(self):
        result = self.extractor.extract("", "test.js")
        assert result == []

    def test_basic_store(self):
        content = """
Alpine.store('auth', {
    user: null,
    isLoggedIn: false,
    login(userData) { this.user = userData; this.isLoggedIn = true; },
    logout() { this.user = null; this.isLoggedIn = false; },
});
"""
        result = self.extractor.extract(content, "test.js")
        assert len(result) >= 1
        assert result[0].name == "auth"

    def test_store_with_init(self):
        content = """
Alpine.store('config', {
    settings: {},
    init() { this.settings = {}; },
});
"""
        result = self.extractor.extract(content, "test.js")
        assert len(result) >= 1
        assert result[0].has_init is True

    def test_store_with_persist(self):
        content = """
Alpine.store('settings', {
    theme: Alpine.$persist('light'),
});
"""
        result = self.extractor.extract(content, "test.js")
        assert len(result) >= 1
        assert result[0].has_persist is True

    def test_store_access_counting(self):
        content = """
Alpine.store('cart', { items: [] });
// usage
console.log($store.cart.items);
$store.cart.items.push(item);
$store.cart.items.length;
"""
        result = self.extractor.extract(content, "test.js")
        assert len(result) >= 1
        assert result[0].access_count >= 2

    def test_multiple_stores(self):
        content = """
Alpine.store('auth', { user: null });
Alpine.store('cart', { items: [] });
Alpine.store('ui', { theme: 'light' });
"""
        result = self.extractor.extract(content, "test.js")
        assert len(result) >= 3
        names = [s.name for s in result]
        assert "auth" in names
        assert "cart" in names
        assert "ui" in names


# ============================================================================
# PluginExtractor Tests
# ============================================================================

class TestPluginExtractor:
    """Tests for AlpinePluginExtractor."""

    def setup_method(self):
        self.extractor = AlpinePluginExtractor()

    def test_empty_content(self):
        plugins, dirs, magics = self.extractor.extract("", "test.js")
        assert plugins == []
        assert dirs == []
        assert magics == []

    def test_official_plugin_import(self):
        content = """
import mask from '@alpinejs/mask';
import intersect from '@alpinejs/intersect';
Alpine.plugin(mask);
Alpine.plugin(intersect);
"""
        plugins, dirs, magics = self.extractor.extract(content, "test.js")
        assert len(plugins) >= 2
        names = [p.name for p in plugins]
        assert "mask" in names or "@alpinejs/mask" in names

    def test_persist_plugin(self):
        content = "import persist from '@alpinejs/persist';\nAlpine.plugin(persist);"
        plugins, dirs, magics = self.extractor.extract(content, "test.js")
        assert len(plugins) >= 1

    def test_custom_directive(self):
        content = """
Alpine.directive('tooltip', (el, { expression }, { evaluate }) => {
    const text = evaluate(expression);
    el.setAttribute('title', text);
});
"""
        plugins, dirs, magics = self.extractor.extract(content, "test.js")
        assert len(dirs) >= 1
        assert dirs[0].name == "tooltip"

    def test_custom_magic(self):
        content = """
Alpine.magic('clipboard', () => {
    return (text) => navigator.clipboard.writeText(text);
});
"""
        plugins, dirs, magics = self.extractor.extract(content, "test.js")
        assert len(magics) >= 1
        assert magics[0].name == "clipboard"

    def test_cdn_plugin_detection(self):
        content = '<script src="https://cdn.jsdelivr.net/npm/@alpinejs/focus@3.x/dist/cdn.min.js"></script>'
        plugins, dirs, magics = self.extractor.extract(content, "test.html")
        assert len(plugins) >= 1
        names = [p.name for p in plugins]
        assert any("focus" in n for n in names)


# ============================================================================
# ApiExtractor Tests
# ============================================================================

class TestApiExtractor:
    """Tests for AlpineApiExtractor."""

    def setup_method(self):
        self.extractor = AlpineApiExtractor()

    def test_empty_content(self):
        imports, integrations, types, cdns = self.extractor.extract("", "test.js")
        assert imports == []
        assert integrations == []
        assert types == []
        assert cdns == []

    def test_esm_import(self):
        content = "import Alpine from 'alpinejs';"
        imports, integrations, types, cdns = self.extractor.extract(content, "test.js")
        assert len(imports) >= 1
        assert imports[0].source == "alpinejs"
        assert imports[0].default_import == "Alpine"

    def test_named_import(self):
        content = "import { Alpine } from 'alpinejs';"
        imports, integrations, types, cdns = self.extractor.extract(content, "test.js")
        assert len(imports) >= 1

    def test_plugin_import(self):
        content = "import mask from '@alpinejs/mask';"
        imports, integrations, types, cdns = self.extractor.extract(content, "test.js")
        assert len(imports) >= 1
        assert imports[0].source == "@alpinejs/mask"

    def test_cdn_detection(self):
        content = '<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.14.0/dist/cdn.min.js"></script>'
        imports, integrations, types, cdns = self.extractor.extract(content, "test.html")
        assert len(cdns) >= 1
        assert "3.14.0" in (cdns[0].version or "")

    def test_cdn_unpkg(self):
        content = '<script src="https://unpkg.com/alpinejs@3.13.0/dist/cdn.min.js"></script>'
        imports, integrations, types, cdns = self.extractor.extract(content, "test.html")
        assert len(cdns) >= 1

    def test_cdn_module_type(self):
        content = '<script type="module" src="https://cdn.jsdelivr.net/npm/alpinejs@3.x/dist/module.esm.js"></script>'
        imports, integrations, types, cdns = self.extractor.extract(content, "test.html")
        assert len(cdns) >= 1
        # CDN detected regardless of module type
        assert cdns[0].url != ""

    def test_htmx_integration(self):
        content = '<div hx-get="/api/data" hx-swap="innerHTML">Load</div>'
        imports, integrations, types, cdns = self.extractor.extract(content, "test.html")
        integ_names = [i.name for i in integrations]
        assert "htmx" in integ_names

    def test_livewire_integration(self):
        content = '<div wire:click="save">Save</div>'
        imports, integrations, types, cdns = self.extractor.extract(content, "test.html")
        integ_names = [i.name for i in integrations]
        assert "livewire" in integ_names

    def test_tailwind_integration(self):
        content = '<div class="flex items-center p-4 bg-blue-500 text-white">'
        imports, integrations, types, cdns = self.extractor.extract(content, "test.html")
        integ_names = [i.name for i in integrations]
        assert "tailwind" in integ_names

    def test_typescript_type(self):
        content = "import type { Alpine as AlpineType } from 'alpinejs';"
        imports, integrations, types, cdns = self.extractor.extract(content, "test.ts")
        assert len(types) >= 1 or any(i.is_type_import for i in imports)

    def test_cjs_require(self):
        content = "const Alpine = require('alpinejs');"
        imports, integrations, types, cdns = self.extractor.extract(content, "test.js")
        assert len(imports) >= 1


# ============================================================================
# EnhancedAlpineParser Tests
# ============================================================================

class TestEnhancedAlpineParser:
    """Tests for EnhancedAlpineParser."""

    def setup_method(self):
        self.parser = EnhancedAlpineParser()

    # ── is_alpine_file ──────────────────────────────────────────

    def test_is_alpine_file_empty(self):
        assert self.parser.is_alpine_file("") is False
        assert self.parser.is_alpine_file("   ") is False

    def test_is_alpine_file_xdata(self):
        assert self.parser.is_alpine_file('<div x-data="{}">') is True

    def test_is_alpine_file_import(self):
        assert self.parser.is_alpine_file("import Alpine from 'alpinejs';") is True

    def test_is_alpine_file_cdn(self):
        assert self.parser.is_alpine_file('<script src="https://cdn.jsdelivr.net/npm/alpinejs"></script>') is True

    def test_is_alpine_file_alpine_start(self):
        assert self.parser.is_alpine_file("Alpine.start();") is True

    def test_is_alpine_file_alpine_store(self):
        assert self.parser.is_alpine_file("Alpine.store('auth', {});") is True

    def test_is_alpine_file_alpine_data(self):
        assert self.parser.is_alpine_file("Alpine.data('dropdown', () => ({}));") is True

    def test_is_alpine_file_alpine_init_event(self):
        assert self.parser.is_alpine_file("document.addEventListener('alpine:init', () => {});") is True

    def test_is_alpine_file_plain_html(self):
        assert self.parser.is_alpine_file("<div><p>Hello</p></div>") is False

    def test_is_alpine_file_plain_js(self):
        assert self.parser.is_alpine_file("const x = 1; console.log(x);") is False

    # ── parse ───────────────────────────────────────────────────

    def test_parse_empty(self):
        result = self.parser.parse("", "test.html")
        assert isinstance(result, AlpineParseResult)
        assert result.directives == []
        assert result.components == []

    def test_parse_full_html(self):
        content = """
<html>
<head>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.14.0/dist/cdn.min.js"></script>
</head>
<body>
<div x-data="{ open: false, count: 0 }" x-cloak>
    <button @click="open = !open" :class="open && 'active'">Toggle</button>
    <div x-show="open" x-transition>
        <span x-text="count"></span>
        <button @click="count++">+</button>
    </div>
</div>
</body>
</html>
"""
        result = self.parser.parse(content, "index.html")
        assert len(result.directives) > 0
        assert len(result.cdns) >= 1
        directive_names = [d.directive_name for d in result.directives]
        assert "x-data" in directive_names
        assert "x-show" in directive_names
        assert "x-cloak" in directive_names

    def test_parse_full_js(self):
        content = """
import Alpine from 'alpinejs';
import persist from '@alpinejs/persist';

Alpine.plugin(persist);

Alpine.data('dropdown', () => ({
    open: false,
    toggle() { this.open = !this.open },
}));

Alpine.store('auth', {
    user: null,
    login(data) { this.user = data; },
});

Alpine.start();
"""
        result = self.parser.parse(content, "app.js")
        assert len(result.imports) >= 2
        assert len(result.components) >= 1
        assert len(result.stores) >= 1
        assert len(result.plugins) >= 1

    def test_parse_returns_file_path(self):
        result = self.parser.parse("<div x-data='{}'>", "test.html")
        assert result.file_path == "test.html"

    # ── File type detection ─────────────────────────────────────

    def test_detect_file_type_html(self):
        assert self.parser._detect_file_type("page.html") == "html"
        assert self.parser._detect_file_type("page.htm") == "html"

    def test_detect_file_type_js(self):
        assert self.parser._detect_file_type("app.js") == "js"
        assert self.parser._detect_file_type("app.mjs") == "js"
        assert self.parser._detect_file_type("app.cjs") == "js"

    def test_detect_file_type_ts(self):
        assert self.parser._detect_file_type("app.ts") == "ts"
        assert self.parser._detect_file_type("app.tsx") == "tsx"

    def test_detect_file_type_blade(self):
        assert self.parser._detect_file_type("page.blade.php") == "blade"

    def test_detect_file_type_vue(self):
        assert self.parser._detect_file_type("App.vue") == "vue"

    # ── Framework detection ─────────────────────────────────────

    def test_detect_frameworks_alpinejs(self):
        content = "import Alpine from 'alpinejs';"
        fws = self.parser._detect_frameworks(content)
        assert "alpinejs" in fws

    def test_detect_frameworks_htmx(self):
        content = '<div hx-get="/api/data" hx-swap="innerHTML">'
        fws = self.parser._detect_frameworks(content)
        assert "htmx" in fws

    def test_detect_frameworks_livewire(self):
        content = '<div wire:click="save">'
        fws = self.parser._detect_frameworks(content)
        assert "livewire" in fws

    def test_detect_frameworks_tailwind(self):
        content = '<div class="flex items-center p-4 bg-blue-500">'
        fws = self.parser._detect_frameworks(content)
        assert "tailwind" in fws

    def test_detect_frameworks_plugin_mask(self):
        content = '<input x-mask="(999) 999-9999">'
        fws = self.parser._detect_frameworks(content)
        assert "alpine-mask" in fws

    def test_detect_frameworks_plugin_intersect(self):
        content = '<div x-intersect="visible = true">'
        fws = self.parser._detect_frameworks(content)
        assert "alpine-intersect" in fws

    def test_detect_frameworks_plugin_persist(self):
        content = "Alpine.$persist('value')"
        fws = self.parser._detect_frameworks(content)
        assert "alpine-persist" in fws

    def test_detect_frameworks_turbo(self):
        content = '<turbo-frame id="frame"><div>Content</div></turbo-frame>'
        fws = self.parser._detect_frameworks(content)
        assert "turbo" in fws

    # ── Feature detection ───────────────────────────────────────

    def test_detect_features_x_data(self):
        content = '<div x-data="{ a: 1 }">'
        feats = self.parser._detect_features(content)
        assert "x-data" in feats

    def test_detect_features_x_bind(self):
        content = '<div :class="cls">'
        feats = self.parser._detect_features(content)
        assert "x-bind" in feats

    def test_detect_features_x_on(self):
        content = '<button @click="fn()">'
        feats = self.parser._detect_features(content)
        assert "x-on" in feats

    def test_detect_features_alpine_start(self):
        content = "Alpine.start();"
        feats = self.parser._detect_features(content)
        assert "alpine_start" in feats

    def test_detect_features_alpine_store(self):
        content = "Alpine.store('x', {});"
        feats = self.parser._detect_features(content)
        assert "alpine_store" in feats

    def test_detect_features_magic_refs(self):
        content = "this.$refs.input.focus();"
        feats = self.parser._detect_features(content)
        assert "magic_refs" in feats

    def test_detect_features_magic_dispatch(self):
        content = "$dispatch('event-name', { data: 1 });"
        feats = self.parser._detect_features(content)
        assert "magic_dispatch" in feats

    def test_detect_features_x_spread_v1(self):
        content = '<div x-spread="bindings">'
        feats = self.parser._detect_features(content)
        assert "x-spread" in feats

    # ── Version detection ───────────────────────────────────────

    def test_detect_version_v3_from_alpine_start(self):
        content = "import Alpine from 'alpinejs';\nAlpine.start();"
        result = self.parser.parse(content, "test.js")
        assert result.alpine_version == "v3"

    def test_detect_version_v3_from_alpine_data(self):
        content = "Alpine.data('comp', () => ({}));"
        result = self.parser.parse(content, "test.js")
        assert result.alpine_version == "v3"

    def test_detect_version_v3_from_x_effect(self):
        content = '<div x-effect="console.log(x)">'
        result = self.parser.parse(content, "test.html")
        assert result.alpine_version == "v3"

    def test_detect_version_v3_from_x_teleport(self):
        content = '<template x-teleport="body"><div>Hi</div></template>'
        result = self.parser.parse(content, "test.html")
        assert result.alpine_version == "v3"

    def test_detect_version_v1_from_x_spread(self):
        content = '<div x-spread="bindings">'
        result = self.parser.parse(content, "test.html")
        assert result.alpine_version == "v1"

    def test_detect_version_v2_from_basic_directives(self):
        content = '<div x-data="{ open: false }" x-show="open">'
        result = self.parser.parse(content, "test.html")
        assert result.alpine_version == "v2"

    def test_detect_version_v3_from_npm_import(self):
        content = "import Alpine from 'alpinejs';"
        result = self.parser.parse(content, "test.js")
        assert result.alpine_version == "v3"

    def test_detect_version_v3_from_cdn_version(self):
        content = '<script src="https://cdn.jsdelivr.net/npm/alpinejs@3.14.0/dist/cdn.min.js"></script>'
        result = self.parser.parse(content, "test.html")
        assert result.alpine_version == "v3"

    # ── version_compare ─────────────────────────────────────────

    def test_version_compare_v3_gt_v2(self):
        assert self.parser._version_compare("v3", "v2") > 0

    def test_version_compare_v2_gt_v1(self):
        assert self.parser._version_compare("v2", "v1") > 0

    def test_version_compare_equal(self):
        assert self.parser._version_compare("v3", "v3") == 0

    def test_version_compare_v1_lt_v3(self):
        assert self.parser._version_compare("v1", "v3") < 0

    def test_version_compare_empty(self):
        assert self.parser._version_compare("v3", "") > 0
        assert self.parser._version_compare("", "v3") < 0
        assert self.parser._version_compare("", "") == 0

    # ── Integration tests ───────────────────────────────────────

    def test_full_alpine_app(self):
        """Test a realistic Alpine.js application with components, stores, plugins."""
        content = """
import Alpine from 'alpinejs';
import persist from '@alpinejs/persist';
import intersect from '@alpinejs/intersect';

Alpine.plugin(persist);
Alpine.plugin(intersect);

Alpine.store('darkMode', {
    on: Alpine.$persist(false),
    toggle() { this.on = !this.on; },
});

Alpine.data('searchForm', () => ({
    query: '',
    results: [],
    loading: false,

    get hasResults() {
        return this.results.length > 0;
    },

    async search() {
        this.loading = true;
        const res = await fetch('/api/search?q=' + this.query);
        this.results = await res.json();
        this.loading = false;
    },

    init() {
        this.$watch('query', (value) => {
            if (value.length > 2) this.search();
        });
    },
}));

Alpine.directive('focus', (el) => { el.focus(); });

Alpine.magic('now', () => new Date());

Alpine.start();
"""
        result = self.parser.parse(content, "app.js")

        # Imports
        assert len(result.imports) >= 3

        # Components
        assert len(result.components) >= 1
        search_comp = [c for c in result.components if c.name == "searchForm"]
        assert len(search_comp) == 1
        assert search_comp[0].has_init is True

        # Stores
        assert len(result.stores) >= 1
        dm_store = [s for s in result.stores if s.name == "darkMode"]
        assert len(dm_store) == 1
        assert dm_store[0].has_persist is True

        # Plugins
        assert len(result.plugins) >= 2

        # Custom directives
        assert len(result.custom_directives) >= 1
        assert result.custom_directives[0].name == "focus"

        # Custom magics
        assert len(result.custom_magics) >= 1
        assert result.custom_magics[0].name == "now"

        # Version
        assert result.alpine_version == "v3"

        # Frameworks
        assert "alpinejs" in result.detected_frameworks

    def test_alpine_html_with_cdn_and_htmx(self):
        """Test an HTML file with CDN Alpine.js and HTMX integration."""
        content = """
<!DOCTYPE html>
<html>
<head>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.14.0/dist/cdn.min.js"></script>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <style>[x-cloak] { display: none; }</style>
</head>
<body>
<div x-data="{ items: [], loading: false }" x-cloak>
    <div hx-get="/api/items" hx-trigger="load" hx-target="#items"
         @htmx:before-request="loading = true"
         @htmx:after-request="loading = false">
        <span x-show="loading" x-transition>Loading...</span>
    </div>
    <div id="items">
        <template x-for="item in items" :key="item.id">
            <div x-text="item.name" :class="item.active && 'highlight'"></div>
        </template>
    </div>
</div>
</body>
</html>
"""
        result = self.parser.parse(content, "index.html")

        # CDN detected
        assert len(result.cdns) >= 1
        assert result.alpine_version == "v3"

        # Directives
        directive_names = [d.directive_name for d in result.directives]
        assert "x-data" in directive_names
        assert "x-cloak" in directive_names
        assert "x-show" in directive_names
        assert "x-for" in directive_names
        assert "x-text" in directive_names

        # HTMX integration
        integ_names = [i.name for i in result.integrations]
        assert "htmx" in integ_names

    def test_alpine_livewire_blade(self):
        """Test Alpine.js with Laravel Livewire in a Blade template."""
        content = """
<div x-data="{ open: false }">
    <button wire:click="save" @click="open = false">Save</button>
    <div x-show="open" x-transition>
        <input x-model="$wire.name" type="text">
    </div>
</div>
"""
        result = self.parser.parse(content, "form.blade.php")
        assert result.file_type == "blade"

        # Directives
        directive_names = [d.directive_name for d in result.directives]
        assert "x-data" in directive_names
        assert "x-show" in directive_names
        assert "x-model" in directive_names

        # Livewire integration
        integ_names = [i.name for i in result.integrations]
        assert "livewire" in integ_names
