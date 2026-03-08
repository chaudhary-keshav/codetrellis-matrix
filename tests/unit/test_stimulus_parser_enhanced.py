"""
Tests for EnhancedStimulusParser v1.0 — Stimulus / Hotwire Framework Support.

Tests cover:
- StimulusControllerExtractor: class definitions, lifecycle, static targets/values/classes/outlets
- StimulusTargetExtractor: HTML data-*-target (v1 & v2), JS getters, callbacks
- StimulusActionExtractor: data-action descriptors, params, options, global, keyboard filters
- StimulusValueExtractor: static values, HTML data-*-value, get/set, valueChanged
- StimulusApiExtractor: imports, CDNs, Turbo, Strada, integrations, configs
- EnhancedStimulusParser: is_stimulus_file, parse, version detection, framework detection

Part of CodeTrellis v4.68 - Stimulus / Hotwire Framework Support
"""

import pytest

from codetrellis.extractors.stimulus import (
    StimulusControllerExtractor, StimulusControllerInfo,
    StimulusTargetExtractor, StimulusTargetInfo,
    StimulusActionExtractor, StimulusActionInfo,
    StimulusValueExtractor, StimulusValueInfo,
    StimulusApiExtractor, StimulusImportInfo, StimulusIntegrationInfo,
    StimulusConfigInfo, StimulusCDNInfo,
)
from codetrellis.stimulus_parser_enhanced import (
    EnhancedStimulusParser, StimulusParseResult,
)


# ============================================================================
# Controller Extractor Tests
# ============================================================================

class TestStimulusControllerExtractor:
    """Tests for StimulusControllerExtractor."""

    def setup_method(self):
        self.extractor = StimulusControllerExtractor()

    def test_basic_controller(self):
        content = '''
import { Controller } from "@hotwired/stimulus"

export default class HelloController extends Controller {
    connect() {
        console.log("Hello, Stimulus!")
    }
}
'''
        result = self.extractor.extract(content)
        assert len(result) >= 1
        ctrl = result[0]
        assert ctrl.name == "HelloController"
        assert ctrl.has_connect is True

    def test_controller_with_targets(self):
        content = '''
import { Controller } from "@hotwired/stimulus"

export default class SearchController extends Controller {
    static targets = ["input", "output", "loading"]

    connect() {}

    search() {
        this.inputTarget.value
        this.outputTarget.textContent = "results"
    }
}
'''
        result = self.extractor.extract(content)
        assert len(result) >= 1
        ctrl = result[0]
        assert "input" in ctrl.static_targets
        assert "output" in ctrl.static_targets
        assert "loading" in ctrl.static_targets

    def test_controller_with_values(self):
        content = '''
import { Controller } from "@hotwired/stimulus"

export default class SlideshowController extends Controller {
    static values = { index: Number, autoplay: Boolean }

    next() {
        this.indexValue++
    }
}
'''
        result = self.extractor.extract(content)
        assert len(result) >= 1
        ctrl = result[0]
        assert len(ctrl.static_values) >= 1

    def test_controller_with_outlets_v3(self):
        content = '''
import { Controller } from "@hotwired/stimulus"

export default class ModalController extends Controller {
    static outlets = ["overlay", "content"]

    open() {
        this.overlayOutlet.show()
    }
}
'''
        result = self.extractor.extract(content)
        assert len(result) >= 1
        ctrl = result[0]
        assert "overlay" in ctrl.static_outlets
        assert "content" in ctrl.static_outlets
        assert ctrl.version_hint == "v3"

    def test_controller_with_classes(self):
        content = '''
import { Controller } from "@hotwired/stimulus"

export default class DropdownController extends Controller {
    static classes = ["active", "hidden"]

    toggle() {
        this.element.classList.toggle(this.activeClass)
    }
}
'''
        result = self.extractor.extract(content)
        assert len(result) >= 1
        ctrl = result[0]
        assert "active" in ctrl.static_classes
        assert "hidden" in ctrl.static_classes

    def test_controller_lifecycle_methods(self):
        content = '''
import { Controller } from "@hotwired/stimulus"

export default class FormController extends Controller {
    initialize() {
        this.form = null
    }

    connect() {
        this.form = this.element
    }

    disconnect() {
        this.form = null
    }
}
'''
        result = self.extractor.extract(content)
        assert len(result) >= 1
        ctrl = result[0]
        assert ctrl.has_initialize is True
        assert ctrl.has_connect is True
        assert ctrl.has_disconnect is True

    def test_empty_content(self):
        result = self.extractor.extract("")
        assert result == []

    def test_no_stimulus(self):
        content = "function hello() { console.log('hi') }"
        result = self.extractor.extract(content)
        assert result == []


# ============================================================================
# Target Extractor Tests
# ============================================================================

class TestStimulusTargetExtractor:
    """Tests for StimulusTargetExtractor."""

    def setup_method(self):
        self.extractor = StimulusTargetExtractor()

    def test_html_target_v2(self):
        content = '''
<div data-controller="search">
    <input data-search-target="input" type="text">
    <div data-search-target="output"></div>
</div>
'''
        result = self.extractor.extract(content)
        assert len(result) >= 2
        names = [t.name for t in result]
        assert "input" in names
        assert "output" in names

    def test_html_target_v1(self):
        content = '''
<div data-controller="search">
    <input data-target="search.input" type="text">
    <div data-target="search.output"></div>
</div>
'''
        result = self.extractor.extract(content)
        assert len(result) >= 2
        # v1 targets should be detected
        v1_targets = [t for t in result if t.version_hint == "v1"]
        assert len(v1_targets) >= 2

    def test_js_target_getters(self):
        content = '''
export default class extends Controller {
    static targets = ["name", "email"]

    greet() {
        const name = this.nameTarget.value
        const has = this.hasEmailTarget
        const all = this.emailTargets
    }
}
'''
        result = self.extractor.extract(content)
        # Should find nameTarget, hasEmailTarget, emailTargets
        names = [t.name for t in result]
        assert "name" in names or any("name" in n for n in names)

    def test_target_callbacks(self):
        content = '''
export default class extends Controller {
    static targets = ["item"]

    itemTargetConnected(element) {
        console.log("connected", element)
    }

    itemTargetDisconnected(element) {
        console.log("disconnected", element)
    }
}
'''
        result = self.extractor.extract(content)
        callbacks = [t for t in result if t.target_type == "callback"]
        assert len(callbacks) >= 1

    def test_empty_content(self):
        result = self.extractor.extract("")
        assert result == []


# ============================================================================
# Action Extractor Tests
# ============================================================================

class TestStimulusActionExtractor:
    """Tests for StimulusActionExtractor."""

    def setup_method(self):
        self.extractor = StimulusActionExtractor()

    def test_basic_action(self):
        content = '''
<button data-action="click->search#perform">Search</button>
'''
        result = self.extractor.extract(content)
        assert len(result) >= 1
        action = result[0]
        assert action.event_name == "click"
        assert action.controller_name == "search"
        assert action.method_name == "perform"

    def test_multiple_actions(self):
        content = '''
<input data-action="input->search#update keydown.enter->search#submit">
'''
        result = self.extractor.extract(content)
        assert len(result) >= 2

    def test_action_with_prevent(self):
        content = '''
<form data-action="submit->form#save:prevent">
'''
        result = self.extractor.extract(content)
        assert len(result) >= 1
        action = result[0]
        assert action.has_prevent is True

    def test_global_action(self):
        content = '''
<div data-action="keydown@window->modal#close">
'''
        result = self.extractor.extract(content)
        assert len(result) >= 1
        action = result[0]
        assert action.is_global is True
        assert action.global_target == "window"

    def test_keyboard_filter(self):
        content = '''
<input data-action="keydown.enter->search#submit">
'''
        result = self.extractor.extract(content)
        assert len(result) >= 1

    def test_action_params(self):
        content = '''
<button data-action="click->item#add"
        data-item-id-param="123"
        data-item-name-param="Widget">
    Add
</button>
'''
        result = self.extractor.extract(content)
        assert len(result) >= 1
        # Should detect params
        params = result[0].params
        assert len(params) >= 1

    def test_default_event_actions(self):
        content = '''
<button data-action="gallery#next">Next</button>
<form data-action="search#perform">Search</form>
'''
        result = self.extractor.extract(content)
        assert len(result) >= 2

    def test_empty_content(self):
        result = self.extractor.extract("")
        assert result == []


# ============================================================================
# Value Extractor Tests
# ============================================================================

class TestStimulusValueExtractor:
    """Tests for StimulusValueExtractor."""

    def setup_method(self):
        self.extractor = StimulusValueExtractor()

    def test_static_values_simple(self):
        content = '''
export default class extends Controller {
    static values = { url: String, interval: Number, active: Boolean }
}
'''
        result = self.extractor.extract(content)
        assert len(result) >= 1

    def test_html_values(self):
        content = '''
<div data-controller="loader"
     data-loader-url-value="/api/data"
     data-loader-interval-value="5000">
</div>
'''
        result = self.extractor.extract(content)
        assert len(result) >= 2
        names = [v.name for v in result]
        assert any("url" in n for n in names)

    def test_value_changed_callback(self):
        content = '''
export default class extends Controller {
    static values = { count: Number }

    countValueChanged(value, previousValue) {
        console.log(`${previousValue} -> ${value}`)
    }
}
'''
        result = self.extractor.extract(content)
        callbacks = [v for v in result if v.has_change_callback]
        assert len(callbacks) >= 1

    def test_value_getters_setters(self):
        content = '''
export default class extends Controller {
    static values = { index: Number }

    next() {
        this.indexValue++
    }

    get currentIndex() {
        return this.indexValue
    }
}
'''
        result = self.extractor.extract(content)
        assert len(result) >= 1

    def test_empty_content(self):
        result = self.extractor.extract("")
        assert result == []


# ============================================================================
# API Extractor Tests
# ============================================================================

class TestStimulusApiExtractor:
    """Tests for StimulusApiExtractor."""

    def setup_method(self):
        self.extractor = StimulusApiExtractor()

    # ---- Imports ----

    def test_esm_import_stimulus(self):
        content = '''
import { Controller } from "@hotwired/stimulus"
'''
        result = self.extractor.extract_imports(content)
        assert len(result) >= 1
        imp = result[0]
        assert imp.source == "@hotwired/stimulus"
        assert "Controller" in imp.named_imports
        assert imp.import_type == "esm"
        assert imp.version_hint == "v2"

    def test_esm_import_turbo(self):
        content = '''
import "@hotwired/turbo"
import { connectStreamSource } from "@hotwired/turbo"
'''
        result = self.extractor.extract_imports(content)
        assert len(result) >= 1

    def test_legacy_import_v1(self):
        content = '''
import { Controller } from "stimulus"
'''
        result = self.extractor.extract_imports(content)
        assert len(result) >= 1
        imp = result[0]
        assert imp.source == "stimulus"
        assert imp.version_hint == "v1"

    def test_cjs_require(self):
        content = '''
const { Controller, Application } = require("@hotwired/stimulus")
'''
        result = self.extractor.extract_imports(content)
        assert len(result) >= 1
        imp = result[0]
        assert imp.import_type == "cjs"

    def test_dynamic_import(self):
        content = '''
const stimulus = await import("@hotwired/stimulus")
'''
        result = self.extractor.extract_imports(content)
        assert len(result) >= 1
        imp = result[0]
        assert imp.import_type == "dynamic"

    def test_strada_import(self):
        content = '''
import { BridgeComponent } from "@hotwired/strada"
'''
        result = self.extractor.extract_imports(content)
        assert len(result) >= 1
        imp = result[0]
        assert imp.source == "@hotwired/strada"

    def test_non_hotwire_import_ignored(self):
        content = '''
import React from "react"
import { useState } from "react"
'''
        result = self.extractor.extract_imports(content)
        assert len(result) == 0

    # ---- CDNs ----

    def test_cdn_detection(self):
        content = '''
<script src="https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.min.js" defer></script>
'''
        result = self.extractor.extract_cdns(content)
        assert len(result) >= 1
        cdn = result[0]
        assert "3.2.2" in cdn.version
        assert cdn.has_defer is True
        assert cdn.package == "stimulus"

    def test_turbo_cdn(self):
        content = '''
<script src="https://cdn.jsdelivr.net/npm/@hotwired/turbo@8.0.0/dist/turbo.es2017-esm.js"></script>
'''
        result = self.extractor.extract_cdns(content)
        assert len(result) >= 1
        cdn = result[0]
        assert cdn.package == "turbo"

    # ---- Integrations ----

    def test_turbo_frame_integration(self):
        content = '''
<turbo-frame id="messages">
    <div>Loading messages...</div>
</turbo-frame>
'''
        result = self.extractor.extract_integrations(content)
        names = [i.name for i in result]
        assert "turbo-frame" in names

    def test_turbo_stream_integration(self):
        content = '''
<turbo-stream action="append" target="messages">
    <template><div>New message</div></template>
</turbo-stream>
'''
        result = self.extractor.extract_integrations(content)
        names = [i.name for i in result]
        assert "turbo-stream" in names

    def test_rails_integration(self):
        content = '''
<%= turbo_frame_tag "messages" do %>
    <%= render @messages %>
<% end %>
'''
        result = self.extractor.extract_integrations(content)
        names = [i.name for i in result]
        assert "rails" in names

    def test_importmap_integration(self):
        content = '''
pin "@hotwired/stimulus", to: "stimulus.min.js", preload: true
pin "@hotwired/turbo-rails", to: "turbo.min.js", preload: true
'''
        result = self.extractor.extract_integrations(content)
        names = [i.name for i in result]
        assert "importmap" in names

    def test_webpack_integration(self):
        content = '''
import { definitionsFromContext } from "stimulus-webpack-helpers"
const application = Application.start()
const context = require.context("./controllers", true, /\.js$/)
application.load(definitionsFromContext(context))
'''
        result = self.extractor.extract_integrations(content)
        names = [i.name for i in result]
        assert "webpack" in names

    def test_strada_integration(self):
        content = '''
import { BridgeComponent } from "@hotwired/strada"

export default class NavComponent extends BridgeComponent {
    static component = "nav"
}
'''
        result = self.extractor.extract_integrations(content)
        names = [i.name for i in result]
        assert "strada" in names

    def test_turbo_events(self):
        content = '''
document.addEventListener("turbo:load", () => {
    console.log("Page loaded via Turbo")
})
'''
        result = self.extractor.extract_integrations(content)
        names = [i.name for i in result]
        assert "turbo-events" in names

    # ---- Configs ----

    def test_turbo_config(self):
        content = '''
Turbo.session.drive = false
Turbo.session.formMode = "optin"
'''
        result = self.extractor.extract_configs(content)
        assert len(result) >= 2
        keys = [c.config_key for c in result]
        assert "Turbo.session.drive" in keys

    def test_application_start(self):
        content = '''
const application = Application.start()
'''
        result = self.extractor.extract_configs(content)
        assert len(result) >= 1
        keys = [c.config_key for c in result]
        assert "Application.start" in keys

    # ---- Empty content ----

    def test_empty_imports(self):
        assert self.extractor.extract_imports("") == []

    def test_empty_integrations(self):
        assert self.extractor.extract_integrations("") == []

    def test_empty_configs(self):
        assert self.extractor.extract_configs("") == []

    def test_empty_cdns(self):
        assert self.extractor.extract_cdns("") == []


# ============================================================================
# EnhancedStimulusParser Tests
# ============================================================================

class TestEnhancedStimulusParser:
    """Tests for EnhancedStimulusParser."""

    def setup_method(self):
        self.parser = EnhancedStimulusParser()

    # ---- is_stimulus_file ----

    def test_is_stimulus_file_import(self):
        content = '''import { Controller } from "@hotwired/stimulus"'''
        assert self.parser.is_stimulus_file(content) is True

    def test_is_stimulus_file_data_controller(self):
        content = '''<div data-controller="hello">'''
        assert self.parser.is_stimulus_file(content) is True

    def test_is_stimulus_file_data_action(self):
        content = '''<button data-action="click->hello#greet">'''
        assert self.parser.is_stimulus_file(content) is True

    def test_is_stimulus_file_controller_class(self):
        content = '''class HelloController extends Controller {'''
        assert self.parser.is_stimulus_file(content) is True

    def test_is_stimulus_file_turbo_frame(self):
        content = '''<turbo-frame id="messages">'''
        assert self.parser.is_stimulus_file(content) is True

    def test_is_stimulus_file_turbo_stream(self):
        content = '''<turbo-stream action="append" target="list">'''
        assert self.parser.is_stimulus_file(content) is True

    def test_is_stimulus_file_turbo_import(self):
        content = '''import "@hotwired/turbo"'''
        assert self.parser.is_stimulus_file(content) is True

    def test_is_stimulus_file_strada(self):
        content = '''import { BridgeComponent } from "@hotwired/strada"'''
        assert self.parser.is_stimulus_file(content) is True

    def test_is_stimulus_file_legacy_v1(self):
        content = '''import { Controller } from "stimulus"'''
        assert self.parser.is_stimulus_file(content) is True

    def test_is_stimulus_file_negative(self):
        content = '''const x = 42; console.log("hello")'''
        assert self.parser.is_stimulus_file(content) is False

    def test_is_stimulus_file_empty(self):
        assert self.parser.is_stimulus_file("") is False
        assert self.parser.is_stimulus_file("   ") is False

    # ---- parse ----

    def test_parse_full_controller(self):
        content = '''
import { Controller } from "@hotwired/stimulus"

export default class SearchController extends Controller {
    static targets = ["input", "output"]
    static values = { url: String }

    connect() {
        this.search()
    }

    search() {
        fetch(this.urlValue)
            .then(r => r.text())
            .then(html => this.outputTarget.innerHTML = html)
    }
}
'''
        result = self.parser.parse(content, "search_controller.js")
        assert isinstance(result, StimulusParseResult)
        assert result.file_type == "js"
        assert len(result.controllers) >= 1
        assert len(result.imports) >= 1

    def test_parse_html_with_actions(self):
        content = '''
<div data-controller="search">
    <input data-search-target="input"
           data-action="input->search#update keydown.enter->search#submit"
           type="text">
    <button data-action="click->search#submit">Search</button>
    <div data-search-target="output"></div>
</div>
'''
        result = self.parser.parse(content, "index.html")
        assert result.file_type == "html"
        assert len(result.targets) >= 2
        assert len(result.actions) >= 2

    def test_parse_turbo_integration(self):
        content = '''
<turbo-frame id="user_1">
    <div data-controller="user">
        <span data-user-target="name">John</span>
    </div>
</turbo-frame>

<turbo-stream action="append" target="users">
    <template>
        <div>New user</div>
    </template>
</turbo-stream>
'''
        result = self.parser.parse(content, "users.html")
        assert result.has_turbo is True
        assert "turbo-frame" in result.detected_features or any(
            i.name == "turbo-frame" for i in result.integrations
        )

    def test_parse_empty_content(self):
        result = self.parser.parse("", "empty.js")
        assert isinstance(result, StimulusParseResult)
        assert len(result.controllers) == 0
        assert len(result.targets) == 0
        assert len(result.actions) == 0
        assert len(result.values) == 0
        assert len(result.imports) == 0

    # ---- Version detection ----

    def test_version_v1_legacy(self):
        content = '''
import { Controller } from "stimulus"

export default class extends Controller {
}
'''
        result = self.parser.parse(content)
        assert result.stimulus_version == "v1"

    def test_version_v2_hotwired(self):
        content = '''
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
    static targets = ["name"]
    static values = { url: String }
}
'''
        result = self.parser.parse(content)
        assert result.stimulus_version in ("v2", "v3")

    def test_version_v3_outlets(self):
        content = '''
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
    static outlets = ["result"]

    resultOutletConnected(outlet) {
        console.log("connected")
    }
}
'''
        result = self.parser.parse(content)
        assert result.stimulus_version == "v3"

    # ---- Framework detection ----

    def test_detect_stimulus_framework(self):
        content = '''import { Controller } from "@hotwired/stimulus"'''
        result = self.parser.parse(content)
        assert "stimulus" in result.detected_frameworks

    def test_detect_turbo_framework(self):
        content = '''
import "@hotwired/turbo"
<turbo-frame id="test"></turbo-frame>
'''
        result = self.parser.parse(content)
        assert "turbo" in result.detected_frameworks

    def test_detect_strada_framework(self):
        content = '''
import { BridgeComponent } from "@hotwired/strada"
'''
        result = self.parser.parse(content)
        assert "strada" in result.detected_frameworks

    def test_detect_rails_framework(self):
        content = '''
<%= turbo_frame_tag "messages" do %>
    <%= render @messages %>
<% end %>
'''
        result = self.parser.parse(content)
        assert "rails" in result.detected_frameworks

    def test_detect_stimulus_use(self):
        content = '''
import { useClickOutside, useDebounce } from "stimulus-use"
'''
        result = self.parser.parse(content)
        assert "stimulus-use" in result.detected_frameworks

    def test_detect_webpack_helpers(self):
        content = '''
import { definitionsFromContext } from "stimulus-webpack-helpers"
'''
        result = self.parser.parse(content)
        assert "stimulus-webpack-helpers" in result.detected_frameworks

    # ---- Feature detection ----

    def test_detect_controller_class(self):
        content = '''class HelloController extends Controller {}'''
        result = self.parser.parse(content)
        assert "controller-class" in result.detected_features

    def test_detect_static_targets(self):
        content = '''
class X extends Controller {
    static targets = ["name"]
}
'''
        result = self.parser.parse(content)
        assert "static-targets" in result.detected_features

    def test_detect_turbo_frame_feature(self):
        content = '''<turbo-frame id="test">content</turbo-frame>'''
        result = self.parser.parse(content)
        assert "turbo-frame" in result.detected_features

    def test_detect_turbo_stream_feature(self):
        content = '''<turbo-stream action="append" target="list">'''
        result = self.parser.parse(content)
        assert "turbo-stream" in result.detected_features

    def test_detect_app_start(self):
        content = '''const app = Application.start()'''
        result = self.parser.parse(content)
        assert "app-start" in result.detected_features

    # ---- File type detection ----

    def test_file_type_html(self):
        result = self.parser.parse("", "index.html")
        assert result.file_type == "html"

    def test_file_type_erb(self):
        result = self.parser.parse("", "index.html.erb")
        assert result.file_type == "erb"

    def test_file_type_js(self):
        result = self.parser.parse("", "controller.js")
        assert result.file_type == "js"

    def test_file_type_ts(self):
        result = self.parser.parse("", "controller.ts")
        assert result.file_type == "ts"

    def test_file_type_blade(self):
        result = self.parser.parse("", "view.blade.php")
        assert result.file_type == "blade"

    # ---- has_turbo / has_strada ----

    def test_has_turbo_from_import(self):
        content = '''import "@hotwired/turbo"'''
        result = self.parser.parse(content)
        assert result.has_turbo is True

    def test_has_turbo_from_element(self):
        content = '''<turbo-frame id="test">'''
        result = self.parser.parse(content)
        assert result.has_turbo is True

    def test_has_strada_from_import(self):
        content = '''import { BridgeComponent } from "@hotwired/strada"'''
        result = self.parser.parse(content)
        assert result.has_strada is True

    def test_has_strada_from_class(self):
        content = '''class NavComponent extends BridgeComponent {}'''
        result = self.parser.parse(content)
        assert result.has_strada is True

    def test_no_turbo_no_strada(self):
        content = '''
import { Controller } from "@hotwired/stimulus"
export default class extends Controller {}
'''
        result = self.parser.parse(content)
        assert result.has_turbo is False
        assert result.has_strada is False

    # ---- Version comparison ----

    def test_version_compare(self):
        assert self.parser._version_compare("v3", "v2") > 0
        assert self.parser._version_compare("v1", "v2") < 0
        assert self.parser._version_compare("v2", "v2") == 0
        assert self.parser._version_compare("v1", "") > 0
        assert self.parser._version_compare("", "v1") < 0
        assert self.parser._version_compare("", "") == 0


# ============================================================================
# Integration / Combined Tests
# ============================================================================

class TestStimulusIntegration:
    """Integration tests combining multiple extractors."""

    def setup_method(self):
        self.parser = EnhancedStimulusParser()

    def test_full_rails_stimulus_app(self):
        """Test a realistic Rails + Stimulus + Turbo HTML page."""
        content = '''
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.2.2/dist/stimulus.min.js" defer></script>
</head>
<body>
    <turbo-frame id="chat">
        <div data-controller="chat" data-chat-room-value="general">
            <div data-chat-target="messages"></div>
            <form data-action="submit->chat#send:prevent">
                <input data-chat-target="input" type="text">
                <button type="submit">Send</button>
            </form>
        </div>
    </turbo-frame>

    <turbo-stream action="append" target="messages">
        <template>
            <div>New message</div>
        </template>
    </turbo-stream>
</body>
</html>
'''
        result = self.parser.parse(content, "chat.html")
        assert result.file_type == "html"
        assert len(result.targets) >= 2
        assert len(result.actions) >= 1
        assert len(result.values) >= 1
        assert len(result.cdns) >= 1
        assert result.has_turbo is True
        assert "turbo-frame" in result.detected_features or any(
            i.name == "turbo-frame" for i in result.integrations
        )

    def test_full_stimulus_controller_js(self):
        """Test a realistic Stimulus controller JS file."""
        content = '''
import { Controller } from "@hotwired/stimulus"
import { useDebounce } from "stimulus-use"

export default class AutocompleteController extends Controller {
    static targets = ["input", "results", "hidden"]
    static values = {
        url: String,
        minLength: { type: Number, default: 3 },
        delay: { type: Number, default: 300 }
    }
    static classes = ["active", "loading"]
    static outlets = ["dropdown"]

    static debounces = ['search']

    connect() {
        useDebounce(this)
    }

    disconnect() {
        this.resultsTarget.innerHTML = ""
    }

    search() {
        if (this.inputTarget.value.length < this.minLengthValue) return

        fetch(this.urlValue + "?q=" + this.inputTarget.value)
            .then(r => r.html())
            .then(html => {
                this.resultsTarget.innerHTML = html
                this.dropdownOutlet.show()
            })
    }

    select(event) {
        this.inputTarget.value = event.target.dataset.label
        this.hiddenTarget.value = event.target.dataset.value
        this.dropdownOutlet.hide()
    }

    minLengthValueChanged(value) {
        console.log("minLength changed to", value)
    }
}
'''
        result = self.parser.parse(content, "autocomplete_controller.js")
        assert result.file_type == "js"
        assert len(result.controllers) >= 1

        ctrl = result.controllers[0]
        assert ctrl.name == "AutocompleteController"
        assert "input" in ctrl.static_targets
        assert "results" in ctrl.static_targets
        assert len(ctrl.static_outlets) >= 1
        assert ctrl.has_connect is True
        assert ctrl.has_disconnect is True

        assert len(result.imports) >= 1
        assert result.stimulus_version in ("v2", "v3")
        assert "stimulus-use" in result.detected_frameworks

    def test_turbo_rails_erb(self):
        """Test a Rails ERB template with Turbo features."""
        content = '''
<%= turbo_frame_tag "user_#{@user.id}" do %>
    <div data-controller="user-profile" data-user-profile-id-value="<%= @user.id %>">
        <span data-user-profile-target="name"><%= @user.name %></span>
        <button data-action="click->user-profile#edit">Edit</button>
    </div>
<% end %>
'''
        result = self.parser.parse(content, "show.html.erb")
        assert result.file_type == "erb"
        assert len(result.targets) >= 1
        assert len(result.actions) >= 1
        assert "rails" in result.detected_frameworks
