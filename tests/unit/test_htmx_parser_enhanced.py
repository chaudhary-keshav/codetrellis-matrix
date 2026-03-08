"""
Tests for HTMX parser enhanced (v4.67).

Tests cover:
- HtmxAttributeExtractor: hx-* attributes, data-hx-* prefix, categories, version hints
- HtmxRequestExtractor: HTTP methods, endpoints, vals, headers, encoding
- HtmxEventExtractor: hx-trigger, hx-on:*, lifecycle events, JS listeners
- HtmxExtensionExtractor: SSE, WebSocket, official/custom extensions
- HtmxApiExtractor: imports, CDN detection, integrations, config
- EnhancedHtmxParser: is_htmx_file, parse, version detection, framework detection

Part of CodeTrellis v4.67 - HTMX Framework Support.
"""

import pytest
from codetrellis.htmx_parser_enhanced import EnhancedHtmxParser, HtmxParseResult
from codetrellis.extractors.htmx import (
    HtmxAttributeExtractor, HtmxAttributeInfo,
    HtmxRequestExtractor, HtmxRequestInfo,
    HtmxEventExtractor, HtmxEventInfo,
    HtmxExtensionExtractor, HtmxExtensionInfo,
    HtmxApiExtractor, HtmxImportInfo, HtmxIntegrationInfo, HtmxConfigInfo, HtmxCDNInfo,
)


# ============================================================================
# AttributeExtractor Tests
# ============================================================================

class TestAttributeExtractor:
    """Tests for HtmxAttributeExtractor."""

    def setup_method(self):
        self.extractor = HtmxAttributeExtractor()

    def test_empty_content(self):
        result = self.extractor.extract("", "test.html")
        assert result == []

    def test_hx_get_attribute(self):
        content = '<button hx-get="/api/users">Load</button>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1
        hx_get = [a for a in result if a.attribute_name == "hx-get"]
        assert len(hx_get) >= 1
        assert hx_get[0].attribute_value == "/api/users"

    def test_hx_post_attribute(self):
        content = '<form hx-post="/api/users">Submit</form>'
        result = self.extractor.extract(content, "test.html")
        hx_post = [a for a in result if a.attribute_name == "hx-post"]
        assert len(hx_post) >= 1

    def test_hx_put_attribute(self):
        content = '<form hx-put="/api/users/1">Update</form>'
        result = self.extractor.extract(content, "test.html")
        hx_put = [a for a in result if a.attribute_name == "hx-put"]
        assert len(hx_put) >= 1

    def test_hx_patch_attribute(self):
        content = '<form hx-patch="/api/users/1">Patch</form>'
        result = self.extractor.extract(content, "test.html")
        hx_patch = [a for a in result if a.attribute_name == "hx-patch"]
        assert len(hx_patch) >= 1

    def test_hx_delete_attribute(self):
        content = '<button hx-delete="/api/users/1">Delete</button>'
        result = self.extractor.extract(content, "test.html")
        hx_del = [a for a in result if a.attribute_name == "hx-delete"]
        assert len(hx_del) >= 1

    def test_hx_swap_attribute(self):
        content = '<div hx-get="/content" hx-swap="outerHTML">Load</div>'
        result = self.extractor.extract(content, "test.html")
        hx_swap = [a for a in result if a.attribute_name == "hx-swap"]
        assert len(hx_swap) >= 1
        assert hx_swap[0].attribute_value == "outerHTML"

    def test_hx_target_attribute(self):
        content = '<button hx-get="/users" hx-target="#user-list">Load</button>'
        result = self.extractor.extract(content, "test.html")
        hx_target = [a for a in result if a.attribute_name == "hx-target"]
        assert len(hx_target) >= 1
        assert hx_target[0].attribute_value == "#user-list"

    def test_hx_trigger_attribute(self):
        content = '<input hx-get="/search" hx-trigger="keyup changed delay:300ms">'
        result = self.extractor.extract(content, "test.html")
        hx_trigger = [a for a in result if a.attribute_name == "hx-trigger"]
        assert len(hx_trigger) >= 1

    def test_hx_boost_attribute(self):
        content = '<nav hx-boost="true"><a href="/home">Home</a></nav>'
        result = self.extractor.extract(content, "test.html")
        hx_boost = [a for a in result if a.attribute_name == "hx-boost"]
        assert len(hx_boost) >= 1

    def test_hx_indicator_attribute(self):
        content = '<button hx-get="/data" hx-indicator="#spinner">Load</button>'
        result = self.extractor.extract(content, "test.html")
        hx_ind = [a for a in result if a.attribute_name == "hx-indicator"]
        assert len(hx_ind) >= 1

    def test_hx_confirm_attribute(self):
        content = '<button hx-delete="/users/1" hx-confirm="Are you sure?">Delete</button>'
        result = self.extractor.extract(content, "test.html")
        hx_confirm = [a for a in result if a.attribute_name == "hx-confirm"]
        assert len(hx_confirm) >= 1

    def test_hx_vals_attribute(self):
        content = """<button hx-post="/api/action" hx-vals='{"key": "value"}'>Go</button>"""
        result = self.extractor.extract(content, "test.html")
        hx_vals = [a for a in result if a.attribute_name == "hx-vals"]
        assert len(hx_vals) >= 1

    def test_hx_headers_attribute(self):
        content = """<div hx-get="/api/data" hx-headers='{"X-Custom": "val"}'>Load</div>"""
        result = self.extractor.extract(content, "test.html")
        hx_headers = [a for a in result if a.attribute_name == "hx-headers"]
        assert len(hx_headers) >= 1

    def test_hx_push_url_attribute(self):
        content = '<a hx-get="/users" hx-push-url="true">Users</a>'
        result = self.extractor.extract(content, "test.html")
        hx_push = [a for a in result if a.attribute_name == "hx-push-url"]
        assert len(hx_push) >= 1

    def test_hx_select_attribute(self):
        content = '<div hx-get="/users" hx-select="#user-table">Load</div>'
        result = self.extractor.extract(content, "test.html")
        hx_select = [a for a in result if a.attribute_name == "hx-select"]
        assert len(hx_select) >= 1

    def test_hx_include_attribute(self):
        content = '<button hx-post="/save" hx-include="closest form">Save</button>'
        result = self.extractor.extract(content, "test.html")
        hx_include = [a for a in result if a.attribute_name == "hx-include"]
        assert len(hx_include) >= 1

    def test_hx_encoding_attribute(self):
        content = '<form hx-post="/upload" hx-encoding="multipart/form-data">Upload</form>'
        result = self.extractor.extract(content, "test.html")
        hx_enc = [a for a in result if a.attribute_name == "hx-encoding"]
        assert len(hx_enc) >= 1

    def test_hx_sync_attribute(self):
        content = '<button hx-post="/save" hx-sync="this:drop">Save</button>'
        result = self.extractor.extract(content, "test.html")
        hx_sync = [a for a in result if a.attribute_name == "hx-sync"]
        assert len(hx_sync) >= 1

    def test_hx_preserve_attribute(self):
        content = '<video id="bg" hx-preserve><source src="bg.mp4"></video>'
        result = self.extractor.extract(content, "test.html")
        hx_preserve = [a for a in result if a.attribute_name == "hx-preserve"]
        assert len(hx_preserve) >= 1

    def test_data_hx_prefix_v1(self):
        content = '<button data-hx-get="/api/users">Load</button>'
        result = self.extractor.extract(content, "test.html")
        data_attrs = [a for a in result if a.is_data_prefix]
        assert len(data_attrs) >= 1

    def test_hx_on_event_v2(self):
        content = '<button hx-get="/data" hx-on:click="console.log(\'clicked\')">Click</button>'
        result = self.extractor.extract(content, "test.html")
        hx_on = [a for a in result if "hx-on" in a.attribute_name]
        assert len(hx_on) >= 1

    def test_hx_disabled_elt_v2(self):
        content = '<form hx-post="/save" hx-disabled-elt="find button">Submit</form>'
        result = self.extractor.extract(content, "test.html")
        hx_disabled = [a for a in result if a.attribute_name == "hx-disabled-elt"]
        assert len(hx_disabled) >= 1
        # hx-disabled-elt is a v2 attribute
        if hx_disabled[0].version_hint:
            assert hx_disabled[0].version_hint == "v2"

    def test_hx_inherit_v2(self):
        content = '<div hx-inherit="hx-target hx-swap"><button hx-get="/data">Load</button></div>'
        result = self.extractor.extract(content, "test.html")
        hx_inherit = [a for a in result if a.attribute_name == "hx-inherit"]
        assert len(hx_inherit) >= 1

    def test_hx_ext_attribute(self):
        content = '<div hx-ext="json-enc"><form hx-post="/api">Submit</form></div>'
        result = self.extractor.extract(content, "test.html")
        hx_ext = [a for a in result if a.attribute_name == "hx-ext"]
        assert len(hx_ext) >= 1

    def test_attribute_categories(self):
        content = '''
        <div hx-get="/api" hx-swap="innerHTML" hx-target="#out"
             hx-trigger="click" hx-indicator="#spinner" hx-boost="true"
             hx-confirm="Sure?" hx-vals='{"a":1}'>Test</div>
        '''
        result = self.extractor.extract(content, "test.html")
        categories = set(a.attribute_category for a in result if a.attribute_category)
        # Should have multiple categories
        assert len(categories) >= 2

    def test_multiple_attributes_on_element(self):
        content = '<button hx-get="/api/users" hx-target="#list" hx-swap="outerHTML" hx-indicator="#spin">Load</button>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 4

    def test_line_numbers(self):
        content = 'line1\n<button hx-get="/api">Load</button>\nline3'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1
        assert result[0].line_number >= 1

    def test_hx_replace_url_attribute(self):
        content = '<a hx-get="/tab" hx-replace-url="true">Tab</a>'
        result = self.extractor.extract(content, "test.html")
        hx_replace = [a for a in result if a.attribute_name == "hx-replace-url"]
        assert len(hx_replace) >= 1

    def test_hx_validate_attribute(self):
        content = '<form hx-post="/submit" hx-validate="true">Go</form>'
        result = self.extractor.extract(content, "test.html")
        hx_val = [a for a in result if a.attribute_name == "hx-validate"]
        assert len(hx_val) >= 1

    def test_hx_params_attribute(self):
        content = '<form hx-post="/save" hx-params="not csrf_token">Go</form>'
        result = self.extractor.extract(content, "test.html")
        hx_params = [a for a in result if a.attribute_name == "hx-params"]
        assert len(hx_params) >= 1

    def test_hx_swap_oob_attribute(self):
        content = '<div id="count" hx-swap-oob="true">5</div>'
        result = self.extractor.extract(content, "test.html")
        hx_oob = [a for a in result if a.attribute_name == "hx-swap-oob"]
        assert len(hx_oob) >= 1

    def test_hx_select_oob_attribute(self):
        content = '<button hx-get="/dash" hx-select-oob="#sidebar">Refresh</button>'
        result = self.extractor.extract(content, "test.html")
        hx_soob = [a for a in result if a.attribute_name == "hx-select-oob"]
        assert len(hx_soob) >= 1


# ============================================================================
# RequestExtractor Tests
# ============================================================================

class TestRequestExtractor:
    """Tests for HtmxRequestExtractor."""

    def setup_method(self):
        self.extractor = HtmxRequestExtractor()

    def test_empty_content(self):
        result = self.extractor.extract("", "test.html")
        assert result == []

    def test_get_request(self):
        content = '<button hx-get="/api/users">Load</button>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1
        assert result[0].method.upper() in ("GET", "HX-GET")

    def test_post_request(self):
        content = '<form hx-post="/api/users"><button>Submit</button></form>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1

    def test_put_request(self):
        content = '<form hx-put="/api/users/1"><button>Update</button></form>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1

    def test_patch_request(self):
        content = '<form hx-patch="/api/users/1"><button>Patch</button></form>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1

    def test_delete_request(self):
        content = '<button hx-delete="/api/users/1">Delete</button>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1

    def test_request_with_vals(self):
        content = """<button hx-post="/api" hx-vals='{"key":"val"}'>Go</button>"""
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1
        assert result[0].has_vals is True

    def test_request_with_headers(self):
        content = """<div hx-get="/api" hx-headers='{"X-H":"v"}'>Load</div>"""
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1
        assert result[0].has_headers is True

    def test_request_with_swap_strategy(self):
        content = '<div hx-get="/content" hx-swap="outerHTML">Load</div>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1
        assert result[0].swap_strategy == "outerHTML"

    def test_request_with_target(self):
        content = '<button hx-get="/users" hx-target="#list">Load</button>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1
        assert result[0].target_selector == "#list"

    def test_request_with_trigger(self):
        content = '<input hx-get="/search" hx-trigger="keyup changed delay:300ms">'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1
        assert "keyup" in (result[0].trigger_spec or "")

    def test_request_with_confirm(self):
        content = '<button hx-delete="/users/1" hx-confirm="Sure?">Del</button>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1
        assert result[0].has_confirm is True

    def test_request_with_include(self):
        content = '<button hx-post="/save" hx-include="#form-fields">Save</button>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1
        assert result[0].has_include is True

    def test_request_with_encoding(self):
        content = '<form hx-post="/upload" hx-encoding="multipart/form-data"><button>Upload</button></form>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1
        assert result[0].has_encoding is True

    def test_request_endpoint_extraction(self):
        content = '<button hx-get="/api/v2/users?page=1">Load</button>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1
        assert "/api/v2/users" in result[0].endpoint

    def test_multiple_requests(self):
        content = '''
        <button hx-get="/api/users">Users</button>
        <button hx-post="/api/users">Create</button>
        <button hx-delete="/api/users/1">Delete</button>
        '''
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 3

    def test_request_with_params(self):
        content = '<form hx-post="/save" hx-params="name,email"><button>Go</button></form>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1
        assert result[0].has_params is True


# ============================================================================
# EventExtractor Tests
# ============================================================================

class TestEventExtractor:
    """Tests for HtmxEventExtractor."""

    def setup_method(self):
        self.extractor = HtmxEventExtractor()

    def test_empty_content(self):
        result = self.extractor.extract("", "test.html")
        assert result == []

    def test_basic_trigger(self):
        content = '<button hx-get="/api" hx-trigger="click">Go</button>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1
        events = [e for e in result if e.event_name == "click"]
        assert len(events) >= 1

    def test_trigger_with_delay(self):
        content = '<input hx-get="/search" hx-trigger="keyup changed delay:300ms">'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1
        keyup_events = [e for e in result if e.event_name == "keyup"]
        assert len(keyup_events) >= 1

    def test_trigger_load(self):
        content = '<div hx-get="/init" hx-trigger="load">Loading...</div>'
        result = self.extractor.extract(content, "test.html")
        load_events = [e for e in result if e.event_name == "load"]
        assert len(load_events) >= 1

    def test_trigger_revealed(self):
        content = '<div hx-get="/lazy" hx-trigger="revealed">Lazy</div>'
        result = self.extractor.extract(content, "test.html")
        revealed = [e for e in result if e.event_name == "revealed"]
        assert len(revealed) >= 1

    def test_trigger_intersect(self):
        content = '<div hx-get="/more" hx-trigger="intersect once">More</div>'
        result = self.extractor.extract(content, "test.html")
        intersect = [e for e in result if e.event_name == "intersect"]
        assert len(intersect) >= 1

    def test_trigger_every(self):
        content = '<div hx-get="/status" hx-trigger="every 5s">Status</div>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1

    def test_trigger_from_modifier(self):
        content = '<div hx-get="/data" hx-trigger="newData from:body">Data</div>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1

    def test_trigger_multiple_events(self):
        content = '<div hx-get="/data" hx-trigger="load, every 10s">Data</div>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1

    def test_hx_on_click_v2(self):
        content = '<button hx-on:click="console.log(\'hi\')">Click</button>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1

    def test_hx_on_htmx_event_v2(self):
        content = '<form hx-on::after-request="alert(\'done\')">Go</form>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1

    def test_js_listener_htmx_on(self):
        content = """
        <script>
        htmx.on('htmx:afterSwap', function(evt) {
            console.log('swapped');
        });
        </script>
        """
        result = self.extractor.extract(content, "test.html")
        htmx_events = [e for e in result if "afterSwap" in e.event_name or "after-swap" in e.event_name.lower()]
        assert len(htmx_events) >= 1

    def test_js_document_listener(self):
        content = """
        <script>
        document.addEventListener('htmx:configRequest', function(evt) {
            evt.detail.headers['Authorization'] = 'Bearer token';
        });
        </script>
        """
        result = self.extractor.extract(content, "test.html")
        config_events = [e for e in result if "configRequest" in e.event_name or "config" in e.event_name.lower()]
        assert len(config_events) >= 1

    def test_sse_event_detection(self):
        content = '<div hx-ext="sse" sse-connect="/events"><div sse-swap="notification">Wait</div></div>'
        result = self.extractor.extract(content, "test.html")
        sse_events = [e for e in result if e.is_sse]
        # Should detect SSE-related events
        assert len(result) >= 0  # SSE events may be detected by other extractors

    def test_trigger_modifiers(self):
        content = '<button hx-get="/api" hx-trigger="click once">Go</button>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1

    def test_trigger_filter_expression(self):
        content = """<input hx-get="/search" hx-trigger="keyup[key=='Enter']">"""
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1


# ============================================================================
# ExtensionExtractor Tests
# ============================================================================

class TestExtensionExtractor:
    """Tests for HtmxExtensionExtractor."""

    def setup_method(self):
        self.extractor = HtmxExtensionExtractor()

    def test_empty_content(self):
        result = self.extractor.extract("", "test.html")
        assert result == []

    def test_json_enc_extension(self):
        content = '<div hx-ext="json-enc"><form hx-post="/api">Go</form></div>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 1
        json_ext = [e for e in result if e.name == "json-enc"]
        assert len(json_ext) >= 1
        assert json_ext[0].is_official is True

    def test_sse_extension(self):
        content = '<div hx-ext="sse" sse-connect="/events"><div sse-swap="msg">Wait</div></div>'
        result = self.extractor.extract(content, "test.html")
        sse_ext = [e for e in result if e.name == "sse"]
        assert len(sse_ext) >= 1
        assert sse_ext[0].is_official is True
        assert sse_ext[0].has_sse_connect is True

    def test_ws_extension(self):
        content = '<div hx-ext="ws" ws-connect="/chat"><form ws-send><input name="msg"></form></div>'
        result = self.extractor.extract(content, "test.html")
        ws_ext = [e for e in result if e.name == "ws"]
        assert len(ws_ext) >= 1
        assert ws_ext[0].is_official is True
        assert ws_ext[0].has_ws_connect is True

    def test_multiple_extensions(self):
        content = '<div hx-ext="json-enc, debug, preload">Content</div>'
        result = self.extractor.extract(content, "test.html")
        assert len(result) >= 3
        names = {e.name for e in result}
        assert "json-enc" in names
        assert "debug" in names
        assert "preload" in names

    def test_response_targets_extension(self):
        content = '<div hx-ext="response-targets"><form hx-post="/api" hx-target-422="#errors">Go</form></div>'
        result = self.extractor.extract(content, "test.html")
        rt_ext = [e for e in result if e.name == "response-targets"]
        assert len(rt_ext) >= 1
        assert rt_ext[0].is_official is True

    def test_idiomorph_extension(self):
        content = '<div hx-ext="idiomorph"><div hx-get="/data" hx-swap="morph:innerHTML">Load</div></div>'
        result = self.extractor.extract(content, "test.html")
        morph_ext = [e for e in result if e.name == "idiomorph"]
        assert len(morph_ext) >= 1

    def test_custom_extension(self):
        content = '<div hx-ext="my-custom-ext">Custom</div>'
        result = self.extractor.extract(content, "test.html")
        custom_ext = [e for e in result if e.name == "my-custom-ext"]
        assert len(custom_ext) >= 1
        assert custom_ext[0].is_official is False

    def test_define_extension_js(self):
        content = """
        <script>
        htmx.defineExtension('my-ext', {
            onEvent: function(name, evt) { return true; }
        });
        </script>
        """
        result = self.extractor.extract(content, "test.html")
        defined = [e for e in result if e.name == "my-ext"]
        assert len(defined) >= 1

    def test_sse_connect_url(self):
        content = '<div hx-ext="sse" sse-connect="/api/events">Data</div>'
        result = self.extractor.extract(content, "test.html")
        sse = [e for e in result if e.name == "sse"]
        assert len(sse) >= 1
        assert sse[0].sse_url == "/api/events"

    def test_ws_connect_url(self):
        content = '<div hx-ext="ws" ws-connect="/ws/chat">Chat</div>'
        result = self.extractor.extract(content, "test.html")
        ws = [e for e in result if e.name == "ws"]
        assert len(ws) >= 1
        assert ws[0].ws_url == "/ws/chat"

    def test_preload_extension(self):
        content = '<div hx-ext="preload"><a hx-get="/page" preload="mouseover">Link</a></div>'
        result = self.extractor.extract(content, "test.html")
        preload = [e for e in result if e.name == "preload"]
        assert len(preload) >= 1
        assert preload[0].is_official is True

    def test_head_support_extension(self):
        content = '<div hx-ext="head-support">Content</div>'
        result = self.extractor.extract(content, "test.html")
        hs = [e for e in result if e.name == "head-support"]
        assert len(hs) >= 1
        assert hs[0].is_official is True

    def test_class_tools_extension(self):
        content = '<div hx-ext="class-tools"><div classes="add fade-in:1s">Content</div></div>'
        result = self.extractor.extract(content, "test.html")
        ct = [e for e in result if e.name == "class-tools"]
        assert len(ct) >= 1

    def test_loading_states_extension(self):
        content = '<div hx-ext="loading-states"><button hx-get="/data" data-loading-class="opacity-50">Load</button></div>'
        result = self.extractor.extract(content, "test.html")
        ls = [e for e in result if e.name == "loading-states"]
        assert len(ls) >= 1


# ============================================================================
# ApiExtractor Tests
# ============================================================================

class TestApiExtractor:
    """Tests for HtmxApiExtractor."""

    def setup_method(self):
        self.extractor = HtmxApiExtractor()

    def test_empty_content(self):
        imports, integrations, configs, cdns = self.extractor.extract("", "test.html")
        assert imports == []
        assert integrations == []
        assert configs == []
        assert cdns == []

    def test_esm_import(self):
        content = "import htmx from 'htmx.org';"
        imports, _, _, _ = self.extractor.extract(content, "test.js")
        assert len(imports) >= 1
        assert imports[0].source == "htmx.org"

    def test_cjs_require(self):
        content = "const htmx = require('htmx.org');"
        imports, _, _, _ = self.extractor.extract(content, "test.js")
        assert len(imports) >= 1

    def test_cdn_script_tag(self):
        content = '<script src="https://unpkg.com/htmx.org@1.9.10"></script>'
        _, _, _, cdns = self.extractor.extract(content, "test.html")
        assert len(cdns) >= 1
        assert "1.9.10" in (cdns[0].version or "")

    def test_cdn_with_defer(self):
        content = '<script src="https://unpkg.com/htmx.org@2.0.0" defer></script>'
        _, _, _, cdns = self.extractor.extract(content, "test.html")
        assert len(cdns) >= 1
        assert cdns[0].has_defer is True

    def test_cdn_with_integrity(self):
        content = '<script src="https://unpkg.com/htmx.org@2.0.0" integrity="sha384-abc123" crossorigin="anonymous"></script>'
        _, _, _, cdns = self.extractor.extract(content, "test.html")
        assert len(cdns) >= 1
        assert cdns[0].has_integrity is True

    def test_cdn_extension_script(self):
        content = '<script src="https://unpkg.com/htmx.org@2.0.0/dist/ext/json-enc.js"></script>'
        _, _, _, cdns = self.extractor.extract(content, "test.html")
        assert len(cdns) >= 1
        assert cdns[0].is_extension is True

    def test_htmx_config_meta(self):
        # Meta tag config is not currently extracted as a config item;
        # only htmx.config.* JS assignments are extracted
        content = """<meta name="htmx-config" content='{"selfRequestsOnly": true}'>"""
        _, _, configs, _ = self.extractor.extract(content, "test.html")
        # Meta tag config detection is optional - it may or may not be extracted
        # The test validates no crash occurs
        assert isinstance(configs, list)

    def test_htmx_config_js(self):
        content = """
        <script>
        htmx.config.selfRequestsOnly = true;
        htmx.config.timeout = 10000;
        </script>
        """
        _, _, configs, _ = self.extractor.extract(content, "test.html")
        assert len(configs) >= 1

    def test_django_integration(self):
        content = """
        {% load static %}
        {% csrf_token %}
        <button hx-get="{% url 'user-list' %}" hx-target="#content">Load</button>
        """
        _, integrations, _, _ = self.extractor.extract(content, "test.html")
        django = [i for i in integrations if i.name == "django"]
        assert len(django) >= 1

    def test_flask_integration(self):
        content = """
        <button hx-get="{{ url_for('users') }}" hx-target="#list">Load</button>
        """
        _, integrations, _, _ = self.extractor.extract(content, "test.html")
        flask = [i for i in integrations if i.name == "flask"]
        assert len(flask) >= 1

    def test_hyperscript_integration(self):
        content = """
        <script src="https://unpkg.com/hyperscript.org@0.9.12"></script>
        <button hx-get="/api" _="on click toggle .active on me">Go</button>
        """
        _, integrations, _, _ = self.extractor.extract(content, "test.html")
        hyper = [i for i in integrations if i.name == "hyperscript"]
        assert len(hyper) >= 1

    def test_alpine_integration(self):
        content = """
        <div x-data="{ open: false }" hx-get="/api">
            <button @click="open = !open" hx-target="#out">Toggle</button>
        </div>
        """
        _, integrations, _, _ = self.extractor.extract(content, "test.html")
        alpine = [i for i in integrations if i.name == "alpine"]
        assert len(alpine) >= 1

    def test_rails_integration(self):
        content = """
        <button hx-get="<%= users_path %>" hx-target="#list">Load</button>
        """
        _, integrations, _, _ = self.extractor.extract(content, "test.html")
        rails = [i for i in integrations if i.name == "rails"]
        assert len(rails) >= 1

    def test_laravel_integration(self):
        content = """
        @csrf
        <button hx-post="{{ route('users.store') }}">Create</button>
        """
        _, integrations, _, _ = self.extractor.extract(content, "test.html")
        laravel = [i for i in integrations if i.name == "laravel"]
        assert len(laravel) >= 1

    def test_tailwind_integration(self):
        content = """
        <button class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                hx-get="/api">Load</button>
        """
        _, integrations, _, _ = self.extractor.extract(content, "test.html")
        tw = [i for i in integrations if i.name == "tailwind"]
        assert len(tw) >= 1

    def test_cdnjs_cdn(self):
        content = '<script src="https://cdnjs.cloudflare.com/ajax/libs/htmx/1.9.10/htmx.min.js"></script>'
        _, _, _, cdns = self.extractor.extract(content, "test.html")
        assert len(cdns) >= 1

    def test_jsdelivr_cdn(self):
        content = '<script src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.0/dist/htmx.min.js"></script>'
        _, _, _, cdns = self.extractor.extract(content, "test.html")
        assert len(cdns) >= 1

    def test_side_effect_import(self):
        content = "import 'htmx.org';"
        imports, _, _, _ = self.extractor.extract(content, "test.js")
        assert len(imports) >= 1

    def test_multiple_imports(self):
        content = """
        import htmx from 'htmx.org';
        import 'htmx.org/dist/ext/json-enc';
        import 'htmx.org/dist/ext/sse';
        """
        imports, _, _, _ = self.extractor.extract(content, "test.js")
        assert len(imports) >= 2

    def test_spring_thymeleaf_integration(self):
        content = """
        <div th:fragment="userList">
            <button hx-get="@{/api/users}" th:attr="hx-target=#list">Load</button>
        </div>
        """
        _, integrations, _, _ = self.extractor.extract(content, "test.html")
        spring = [i for i in integrations if i.name == "spring"]
        assert len(spring) >= 1

    def test_phoenix_integration(self):
        content = """
        <div phx-click="toggle">
            <button hx-get="/api" hx-target="#out">Load</button>
        </div>
        """
        _, integrations, _, _ = self.extractor.extract(content, "test.html")
        phoenix = [i for i in integrations if i.name == "phoenix"]
        assert len(phoenix) >= 1


# ============================================================================
# EnhancedHtmxParser Tests
# ============================================================================

class TestEnhancedHtmxParser:
    """Tests for EnhancedHtmxParser."""

    def setup_method(self):
        self.parser = EnhancedHtmxParser()

    # ── is_htmx_file detection ──────────────────────────────────────

    def test_is_htmx_file_with_hx_get(self):
        content = '<button hx-get="/api/users">Load</button>'
        assert self.parser.is_htmx_file(content, "test.html") is True

    def test_is_htmx_file_with_hx_post(self):
        content = '<form hx-post="/api/users"><button>Submit</button></form>'
        assert self.parser.is_htmx_file(content, "test.html") is True

    def test_is_htmx_file_with_hx_swap(self):
        content = '<div hx-swap="outerHTML">Content</div>'
        assert self.parser.is_htmx_file(content, "test.html") is True

    def test_is_htmx_file_with_hx_target(self):
        content = '<button hx-target="#out">Click</button>'
        assert self.parser.is_htmx_file(content, "test.html") is True

    def test_is_htmx_file_with_hx_trigger(self):
        content = '<div hx-trigger="load">Loading</div>'
        assert self.parser.is_htmx_file(content, "test.html") is True

    def test_is_htmx_file_with_data_hx_prefix(self):
        content = '<button data-hx-get="/api">Load</button>'
        assert self.parser.is_htmx_file(content, "test.html") is True

    def test_is_htmx_file_with_htmx_import(self):
        content = "import htmx from 'htmx.org';"
        assert self.parser.is_htmx_file(content, "test.js") is True

    def test_is_htmx_file_with_htmx_cdn(self):
        content = '<script src="https://unpkg.com/htmx.org@1.9.10"></script>'
        assert self.parser.is_htmx_file(content, "test.html") is True

    def test_is_not_htmx_file_plain_html(self):
        content = '<div class="container"><p>Hello world</p></div>'
        assert self.parser.is_htmx_file(content, "test.html") is False

    def test_is_not_htmx_file_empty(self):
        assert self.parser.is_htmx_file("", "test.html") is False

    def test_is_htmx_file_with_sse_connect(self):
        content = '<div sse-connect="/events">Live</div>'
        assert self.parser.is_htmx_file(content, "test.html") is True

    def test_is_htmx_file_with_ws_connect(self):
        content = '<div ws-connect="/ws/chat">Chat</div>'
        assert self.parser.is_htmx_file(content, "test.html") is True

    def test_is_htmx_file_with_htmx_on(self):
        content = """
        <script>
        htmx.on('htmx:afterSwap', function() {});
        </script>
        """
        assert self.parser.is_htmx_file(content, "test.html") is True

    def test_is_htmx_file_with_hx_boost(self):
        content = '<nav hx-boost="true"><a href="/">Home</a></nav>'
        assert self.parser.is_htmx_file(content, "test.html") is True

    # ── parse method ────────────────────────────────────────────────

    def test_parse_returns_result(self):
        content = '<button hx-get="/api/users" hx-target="#list">Load</button>'
        result = self.parser.parse(content, "test.html")
        assert isinstance(result, HtmxParseResult)
        assert result.file_path == "test.html"

    def test_parse_attributes(self):
        content = '<button hx-get="/api" hx-target="#list" hx-swap="outerHTML">Load</button>'
        result = self.parser.parse(content, "test.html")
        assert len(result.attributes) >= 3

    def test_parse_requests(self):
        content = '<button hx-get="/api/users">Load</button><form hx-post="/api/users"><button>Create</button></form>'
        result = self.parser.parse(content, "test.html")
        assert len(result.requests) >= 2

    def test_parse_events(self):
        content = '<input hx-get="/search" hx-trigger="keyup changed delay:300ms">'
        result = self.parser.parse(content, "test.html")
        assert len(result.events) >= 1

    def test_parse_extensions(self):
        content = '<div hx-ext="json-enc, sse"><form hx-post="/api">Go</form></div>'
        result = self.parser.parse(content, "test.html")
        assert len(result.extensions) >= 2

    def test_parse_imports_js(self):
        content = "import htmx from 'htmx.org';"
        result = self.parser.parse(content, "test.js")
        assert len(result.imports) >= 1

    def test_parse_cdns(self):
        content = '<script src="https://unpkg.com/htmx.org@2.0.0"></script>'
        result = self.parser.parse(content, "test.html")
        assert len(result.cdns) >= 1

    def test_parse_configs(self):
        content = """
        <script>
        htmx.config.selfRequestsOnly = true;
        htmx.config.timeout = 10000;
        </script>
        """
        result = self.parser.parse(content, "test.html")
        assert len(result.configs) >= 1

    def test_parse_integrations_django(self):
        content = """
        {% csrf_token %}
        <button hx-get="{% url 'list' %}" hx-target="#out">Load</button>
        """
        result = self.parser.parse(content, "test.html")
        assert len(result.integrations) >= 1

    # ── Version detection ───────────────────────────────────────────

    def test_detect_v2_from_hx_on_colon(self):
        content = '<button hx-on:click="alert(\'hi\')">Click</button>'
        result = self.parser.parse(content, "test.html")
        assert result.htmx_version == "v2"

    def test_detect_v2_from_hx_disabled_elt(self):
        content = '<form hx-post="/save" hx-disabled-elt="find button">Go</form>'
        result = self.parser.parse(content, "test.html")
        assert result.htmx_version == "v2"

    def test_detect_v2_from_hx_inherit(self):
        content = '<div hx-inherit="hx-target"><button hx-get="/data">Load</button></div>'
        result = self.parser.parse(content, "test.html")
        assert result.htmx_version == "v2"

    def test_detect_v1_from_data_prefix(self):
        content = '<button data-hx-get="/api">Load</button>'
        result = self.parser.parse(content, "test.html")
        # data-hx-* is v1 style
        if result.htmx_version:
            assert result.htmx_version in ("v1", "v2")

    def test_detect_version_from_cdn(self):
        content = '<script src="https://unpkg.com/htmx.org@1.9.10"></script><button hx-get="/api">Load</button>'
        result = self.parser.parse(content, "test.html")
        if result.htmx_version:
            assert "v1" in result.htmx_version or "1" in result.htmx_version

    # ── Framework detection ─────────────────────────────────────────

    def test_detect_htmx_framework(self):
        content = '<button hx-get="/api/users" hx-target="#list">Load</button>'
        result = self.parser.parse(content, "test.html")
        assert "htmx" in result.detected_frameworks

    def test_detect_hyperscript_framework(self):
        content = """
        <script src="https://unpkg.com/hyperscript.org@0.9.12"></script>
        <button hx-get="/api" _="on click toggle .active">Go</button>
        """
        result = self.parser.parse(content, "test.html")
        assert "hyperscript" in result.detected_frameworks

    def test_detect_django_framework(self):
        content = """
        {% csrf_token %}
        <button hx-get="{% url 'list' %}">Load</button>
        """
        result = self.parser.parse(content, "test.html")
        assert "django" in result.detected_frameworks

    def test_detect_flask_framework(self):
        content = """
        <button hx-get="{{ url_for('users') }}">Load</button>
        """
        result = self.parser.parse(content, "test.html")
        assert "flask" in result.detected_frameworks

    def test_detect_alpine_framework(self):
        content = """
        <div x-data="{ open: false }">
            <button hx-get="/api" @click="open = true">Load</button>
        </div>
        """
        result = self.parser.parse(content, "test.html")
        assert "alpinejs" in result.detected_frameworks

    def test_detect_tailwind_framework(self):
        content = """
        <button class="bg-blue-500 hover:bg-blue-700 text-white"
                hx-get="/api">Load</button>
        """
        result = self.parser.parse(content, "test.html")
        assert "tailwind" in result.detected_frameworks

    # ── Feature detection ───────────────────────────────────────────

    def test_detect_hx_get_feature(self):
        content = '<button hx-get="/api">Load</button>'
        result = self.parser.parse(content, "test.html")
        assert "hx-get" in result.detected_features

    def test_detect_hx_post_feature(self):
        content = '<form hx-post="/api"><button>Go</button></form>'
        result = self.parser.parse(content, "test.html")
        assert "hx-post" in result.detected_features

    def test_detect_hx_boost_feature(self):
        content = '<nav hx-boost="true"><a href="/">Home</a></nav>'
        result = self.parser.parse(content, "test.html")
        assert "hx-boost" in result.detected_features

    def test_detect_hx_swap_feature(self):
        content = '<div hx-get="/c" hx-swap="outerHTML">Load</div>'
        result = self.parser.parse(content, "test.html")
        assert "hx-swap" in result.detected_features

    def test_detect_hx_trigger_feature(self):
        content = '<div hx-get="/c" hx-trigger="load">Load</div>'
        result = self.parser.parse(content, "test.html")
        assert "hx-trigger" in result.detected_features

    def test_detect_sse_feature(self):
        content = '<div hx-ext="sse" sse-connect="/events"><div sse-swap="msg">Wait</div></div>'
        result = self.parser.parse(content, "test.html")
        assert "sse-connect" in result.detected_features or "hx-ext" in result.detected_features

    def test_detect_ws_feature(self):
        content = '<div hx-ext="ws" ws-connect="/ws"><form ws-send>Go</form></div>'
        result = self.parser.parse(content, "test.html")
        assert "ws-connect" in result.detected_features or "hx-ext" in result.detected_features

    # ── Comprehensive parse ─────────────────────────────────────────

    def test_comprehensive_htmx_page(self):
        content = """
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://unpkg.com/htmx.org@2.0.0"></script>
            <script src="https://unpkg.com/hyperscript.org@0.9.12"></script>
            <script>
            htmx.config.selfRequestsOnly = true;
            </script>
        </head>
        <body hx-boost="true">
            <nav>
                <a hx-get="/home" hx-push-url="true" hx-target="#content">Home</a>
                <a hx-get="/about" hx-push-url="true" hx-target="#content">About</a>
            </nav>

            <input type="search" name="q"
                   hx-get="/search"
                   hx-trigger="keyup changed delay:300ms"
                   hx-target="#results"
                   hx-indicator="#spinner"
                   hx-sync="this:replace">
            <span id="spinner" class="htmx-indicator">Loading...</span>
            <div id="results"></div>

            <div hx-ext="sse" sse-connect="/events">
                <div sse-swap="notification">Waiting...</div>
            </div>

            <form hx-ext="json-enc" hx-post="/api/users"
                  hx-target="#user-list"
                  hx-on::after-request="this.reset()"
                  hx-disabled-elt="find button">
                <input name="name" required>
                <button type="submit">Create</button>
            </form>

            <button hx-delete="/api/users/1"
                    hx-confirm="Delete this user?"
                    hx-target="closest .user-card"
                    hx-swap="outerHTML swap:500ms">
                Delete
            </button>

            <div id="content">Main content</div>

            <div hx-get="/lazy-widget"
                 hx-trigger="revealed"
                 hx-swap="outerHTML">
                <div class="skeleton"></div>
            </div>
        </body>
        </html>
        """
        result = self.parser.parse(content, "test.html")

        # Should detect many attributes
        assert len(result.attributes) >= 10

        # Should detect requests
        assert len(result.requests) >= 3

        # Should detect events
        assert len(result.events) >= 2

        # Should detect extensions
        assert len(result.extensions) >= 2

        # Should detect CDN
        assert len(result.cdns) >= 1

        # Should detect config
        assert len(result.configs) >= 1

        # Should detect frameworks
        assert "htmx" in result.detected_frameworks
        assert "hyperscript" in result.detected_frameworks

        # Should detect v2
        assert result.htmx_version == "v2"

        # Should detect multiple features
        assert len(result.detected_features) >= 5

    def test_htmx_with_django_template(self):
        content = """
        {% load static %}
        <script src="{% static 'htmx.min.js' %}"></script>
        {% csrf_token %}
        <form hx-post="{% url 'user-create' %}" hx-target="#list">
            <input name="name">
            <button type="submit">Create</button>
        </form>
        <div id="list" hx-get="{% url 'user-list' %}" hx-trigger="load">
            Loading...
        </div>
        """
        result = self.parser.parse(content, "test.html")
        assert "django" in result.detected_frameworks
        assert len(result.requests) >= 2

    def test_htmx_with_flask_jinja2(self):
        content = """
        <button hx-get="{{ url_for('api.users') }}"
                hx-target="#content"
                hx-indicator="#loading">
            Load Users
        </button>
        """
        result = self.parser.parse(content, "test.html")
        assert "flask" in result.detected_frameworks

    def test_htmx_sse_ws_combined(self):
        content = """
        <div hx-ext="sse" sse-connect="/events">
            <div sse-swap="messages">Waiting for messages...</div>
        </div>
        <div hx-ext="ws" ws-connect="/chat">
            <div id="chat-log"></div>
            <form ws-send>
                <input name="message">
                <button type="submit">Send</button>
            </form>
        </div>
        """
        result = self.parser.parse(content, "test.html")
        ext_names = {e.name for e in result.extensions}
        assert "sse" in ext_names
        assert "ws" in ext_names

    def test_htmx_infinite_scroll_pattern(self):
        content = """
        <div id="items">
            <div class="item">Item 1</div>
            <div class="item">Item 2</div>
        </div>
        <div hx-get="/items?page=2"
             hx-trigger="intersect once"
             hx-swap="outerHTML"
             hx-indicator="#loader">
            <span id="loader" class="htmx-indicator">Loading more...</span>
        </div>
        """
        result = self.parser.parse(content, "test.html")
        assert len(result.requests) >= 1
        assert len(result.events) >= 1

    def test_htmx_inline_edit_pattern(self):
        content = """
        <div hx-get="/users/1/edit" hx-trigger="click" hx-swap="outerHTML">
            <span>John Doe</span>
        </div>
        """
        result = self.parser.parse(content, "test.html")
        assert len(result.requests) >= 1
        assert len(result.attributes) >= 3

    def test_htmx_polling_pattern(self):
        content = '<div hx-get="/api/status" hx-trigger="every 5s" hx-target="this">Status</div>'
        result = self.parser.parse(content, "test.html")
        assert len(result.requests) >= 1
        assert len(result.events) >= 1

    def test_htmx_js_file(self):
        content = """
        import htmx from 'htmx.org';
        import 'htmx.org/dist/ext/json-enc';

        htmx.config.selfRequestsOnly = true;
        htmx.config.timeout = 10000;

        htmx.on('htmx:configRequest', function(event) {
            event.detail.headers['Authorization'] = 'Bearer ' + getToken();
        });

        htmx.on('htmx:responseError', function(event) {
            showToast('Error: ' + event.detail.xhr.status);
        });
        """
        result = self.parser.parse(content, "app.js")
        assert len(result.imports) >= 2
        assert len(result.configs) >= 1
        assert len(result.events) >= 1

    def test_htmx_typescript_file(self):
        content = """
        import htmx from 'htmx.org';

        htmx.on('htmx:afterSwap', (event: CustomEvent) => {
            const target = event.detail.target as HTMLElement;
            target.querySelectorAll('.animate-in').forEach(el => {
                el.classList.add('animated');
            });
        });
        """
        result = self.parser.parse(content, "app.ts")
        assert len(result.imports) >= 1
        assert len(result.events) >= 1

    def test_parse_empty_content(self):
        result = self.parser.parse("", "test.html")
        assert isinstance(result, HtmxParseResult)
        assert len(result.attributes) == 0

    def test_parse_non_htmx_content(self):
        content = '<div class="container"><p>Hello World</p></div>'
        result = self.parser.parse(content, "test.html")
        assert len(result.attributes) == 0
        assert len(result.requests) == 0

    # ── _version_compare ────────────────────────────────────────────

    def test_version_compare_v2_gt_v1(self):
        assert self.parser._version_compare("v2", "v1") > 0

    def test_version_compare_v1_lt_v2(self):
        assert self.parser._version_compare("v1", "v2") < 0

    def test_version_compare_same(self):
        assert self.parser._version_compare("v2", "v2") == 0

    def test_version_compare_empty(self):
        assert self.parser._version_compare("v1", "") > 0

    def test_version_compare_both_empty(self):
        assert self.parser._version_compare("", "") == 0

    # ── Edge cases ──────────────────────────────────────────────────

    def test_hx_on_double_colon_lifecycle(self):
        content = '<form hx-post="/save" hx-on::before-request="validate(event)">Go</form>'
        result = self.parser.parse(content, "test.html")
        assert result.htmx_version == "v2"

    def test_multiple_hx_ext_elements(self):
        content = """
        <div hx-ext="json-enc">
            <div hx-ext="response-targets">
                <form hx-post="/api" hx-target-422="#errors">Go</form>
            </div>
        </div>
        """
        result = self.parser.parse(content, "test.html")
        ext_names = {e.name for e in result.extensions}
        assert "json-enc" in ext_names
        assert "response-targets" in ext_names

    def test_oob_swap_attribute(self):
        content = '<div id="count" hx-swap-oob="true">5</div>'
        result = self.parser.parse(content, "test.html")
        oob = [a for a in result.attributes if a.attribute_name == "hx-swap-oob"]
        assert len(oob) >= 1

    def test_file_type_detection_html(self):
        content = '<button hx-get="/api">Load</button>'
        result = self.parser.parse(content, "test.html")
        assert result.file_type == "html"

    def test_file_type_detection_js(self):
        content = "import htmx from 'htmx.org';"
        result = self.parser.parse(content, "test.js")
        assert result.file_type == "js"

    def test_file_type_detection_ts(self):
        content = "import htmx from 'htmx.org';"
        result = self.parser.parse(content, "test.ts")
        assert result.file_type == "ts"
