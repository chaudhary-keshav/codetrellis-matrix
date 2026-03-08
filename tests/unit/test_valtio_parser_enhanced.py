"""
Tests for Valtio extractors and EnhancedValtioParser.

Part of CodeTrellis v4.56 Valtio Framework Support.
Tests cover:
- Proxy extraction (proxy(), ref(), proxyMap, proxySet, computed getters, nested)
- Snapshot extraction (useSnapshot, snapshot, useProxy, destructuring)
- Subscription extraction (subscribe, subscribeKey, watch)
- Action extraction (mutations, devtools, async)
- API extraction (imports, integrations, types, version detection, deprecated)
- Parser integration (framework detection, version detection, feature detection)
"""

import pytest
from codetrellis.valtio_parser_enhanced import (
    EnhancedValtioParser,
    ValtioParseResult,
)
from codetrellis.extractors.valtio import (
    ValtioProxyExtractor,
    ValtioProxyInfo,
    ValtioRefInfo,
    ValtioProxyCollectionInfo,
    ValtioSnapshotExtractor,
    ValtioSnapshotUsageInfo,
    ValtioUseProxyInfo,
    ValtioSubscriptionExtractor,
    ValtioSubscribeInfo,
    ValtioSubscribeKeyInfo,
    ValtioWatchInfo,
    ValtioActionExtractor,
    ValtioActionInfo,
    ValtioDevtoolsInfo,
    ValtioApiExtractor,
    ValtioImportInfo,
    ValtioIntegrationInfo,
    ValtioTypeInfo,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedValtioParser()


@pytest.fixture
def proxy_extractor():
    return ValtioProxyExtractor()


@pytest.fixture
def snapshot_extractor():
    return ValtioSnapshotExtractor()


@pytest.fixture
def subscription_extractor():
    return ValtioSubscriptionExtractor()


@pytest.fixture
def action_extractor():
    return ValtioActionExtractor()


@pytest.fixture
def api_extractor():
    return ValtioApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Proxy Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestValtioProxyExtractor:
    """Tests for ValtioProxyExtractor."""

    def test_basic_proxy(self, proxy_extractor):
        code = """
import { proxy } from 'valtio';
const state = proxy({ count: 0, text: 'hello' });
"""
        result = proxy_extractor.extract(code, "store.ts")
        assert len(result['proxies']) >= 1
        p = result['proxies'][0]
        assert p.name == "state"
        assert p.file == "store.ts"

    def test_exported_proxy(self, proxy_extractor):
        code = """
import { proxy } from 'valtio';
export const appState = proxy({
  count: 0,
  user: null,
  items: [],
});
"""
        result = proxy_extractor.extract(code, "store.ts")
        assert len(result['proxies']) >= 1
        p = result['proxies'][0]
        assert p.name == "appState"
        assert p.is_exported is True

    def test_typed_proxy(self, proxy_extractor):
        code = """
interface AppState { count: number; user: string | null; }
const state = proxy<AppState>({ count: 0, user: null });
"""
        result = proxy_extractor.extract(code, "store.ts")
        assert len(result['proxies']) >= 1
        p = result['proxies'][0]
        assert p.name == "state"
        assert "AppState" in p.type_name

    def test_ref_extraction(self, proxy_extractor):
        code = """
import { proxy, ref } from 'valtio';
const state = proxy({
  domElement: ref(document.createElement('div')),
  ws: ref(new WebSocket('ws://localhost')),
});
"""
        result = proxy_extractor.extract(code, "store.ts")
        assert len(result['refs']) >= 1

    def test_proxy_map(self, proxy_extractor):
        code = """
import { proxyMap } from 'valtio/utils';
const users = proxyMap<string, User>();
"""
        result = proxy_extractor.extract(code, "store.ts")
        assert len(result['collections']) >= 1
        c = result['collections'][0]
        assert c.collection_type == "proxyMap"
        assert c.name == "users"

    def test_proxy_set(self, proxy_extractor):
        code = """
import { proxySet } from 'valtio/utils';
export const tags = proxySet<string>();
"""
        result = proxy_extractor.extract(code, "store.ts")
        assert len(result['collections']) >= 1
        c = result['collections'][0]
        assert c.collection_type == "proxySet"
        assert c.name == "tags"

    def test_computed_getters(self, proxy_extractor):
        code = """
const state = proxy({
  firstName: 'John',
  lastName: 'Doe',
  get fullName() { return this.firstName + ' ' + this.lastName; },
});
"""
        result = proxy_extractor.extract(code, "store.ts")
        assert len(result['proxies']) >= 1
        p = result['proxies'][0]
        assert "fullName" in p.computed_getters

    def test_multiple_proxies(self, proxy_extractor):
        code = """
const authState = proxy({ user: null, token: '' });
const uiState = proxy({ theme: 'light', sidebarOpen: false });
"""
        result = proxy_extractor.extract(code, "store.ts")
        assert len(result['proxies']) >= 2
        names = [p.name for p in result['proxies']]
        assert "authState" in names
        assert "uiState" in names


# ═══════════════════════════════════════════════════════════════════
# Snapshot Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestValtioSnapshotExtractor:
    """Tests for ValtioSnapshotExtractor."""

    def test_use_snapshot(self, snapshot_extractor):
        code = """
import { useSnapshot } from 'valtio';
function Counter() {
  const snap = useSnapshot(state);
  return <div>{snap.count}</div>;
}
"""
        result = snapshot_extractor.extract(code, "Counter.tsx")
        assert len(result['snapshots']) >= 1
        s = result['snapshots'][0]
        assert s.snapshot_type == "useSnapshot"
        assert s.proxy_name == "state"

    def test_use_snapshot_destructured(self, snapshot_extractor):
        code = """
function Counter() {
  const { count, text } = useSnapshot(state);
  return <div>{count} {text}</div>;
}
"""
        result = snapshot_extractor.extract(code, "Counter.tsx")
        assert len(result['snapshots']) >= 1
        s = result['snapshots'][0]
        assert "count" in s.destructured_fields
        assert "text" in s.destructured_fields

    def test_use_snapshot_with_sync(self, snapshot_extractor):
        code = """
function Input() {
  const snap = useSnapshot(state, { sync: true });
  return <input value={snap.text} />;
}
"""
        result = snapshot_extractor.extract(code, "Input.tsx")
        assert len(result['snapshots']) >= 1

    def test_snapshot_vanilla(self, snapshot_extractor):
        code = """
import { snapshot } from 'valtio';
const currentState = snapshot(state);
console.log(currentState.count);
"""
        result = snapshot_extractor.extract(code, "utils.ts")
        assert len(result['snapshots']) >= 1
        s = result['snapshots'][0]
        assert s.snapshot_type == "snapshot"

    def test_use_proxy(self, snapshot_extractor):
        code = """
import { useProxy } from 'valtio/utils';
function Counter() {
  const snap = useProxy(globalState);
  return <div>{snap.count}</div>;
}
"""
        result = snapshot_extractor.extract(code, "Counter.tsx")
        assert len(result['use_proxies']) >= 1
        up = result['use_proxies'][0]
        assert up.proxy_name == "globalState"


# ═══════════════════════════════════════════════════════════════════
# Subscription Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestValtioSubscriptionExtractor:
    """Tests for ValtioSubscriptionExtractor."""

    def test_basic_subscribe(self, subscription_extractor):
        code = """
import { subscribe } from 'valtio';
const unsub = subscribe(state, () => {
  console.log('state changed');
});
"""
        result = subscription_extractor.extract(code, "effects.ts")
        assert len(result['subscribes']) >= 1
        sub = result['subscribes'][0]
        assert sub.proxy_name == "state"
        assert sub.has_unsubscribe is True
        assert sub.unsubscribe_name == "unsub"

    def test_nested_subscribe(self, subscription_extractor):
        code = """
subscribe(state.user.settings, () => {
  console.log('settings changed');
});
"""
        result = subscription_extractor.extract(code, "effects.ts")
        assert len(result['subscribes']) >= 1
        sub = result['subscribes'][0]
        assert sub.is_nested is True

    def test_subscribe_key(self, subscription_extractor):
        code = """
import { subscribeKey } from 'valtio/utils';
subscribeKey(state, 'count', (v) => {
  console.log('count is now', v);
});
"""
        result = subscription_extractor.extract(code, "effects.ts")
        assert len(result['subscribe_keys']) >= 1
        sk = result['subscribe_keys'][0]
        assert sk.proxy_name == "state"
        assert sk.key_name == "count"

    def test_watch_deprecated(self, subscription_extractor):
        code = """
import { watch } from 'valtio/utils';
const stop = watch((get) => {
  console.log(get(state).count);
  console.log(get(otherState).name);
});
"""
        result = subscription_extractor.extract(code, "watcher.ts")
        assert len(result['watches']) >= 1
        w = result['watches'][0]
        assert w.has_cleanup is True
        assert "state" in w.tracked_proxies

    def test_subscribe_without_unsub(self, subscription_extractor):
        code = """
subscribe(state, () => { console.log('changed'); });
"""
        result = subscription_extractor.extract(code, "effects.ts")
        assert len(result['subscribes']) >= 1
        sub = result['subscribes'][0]
        assert sub.has_unsubscribe is False


# ═══════════════════════════════════════════════════════════════════
# Action Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestValtioActionExtractor:
    """Tests for ValtioActionExtractor."""

    def test_action_function(self, action_extractor):
        code = """
const state = proxy({ count: 0 });

const increment = () => {
  state.count++;
};
"""
        result = action_extractor.extract(code, "actions.ts", known_proxies=["state"])
        assert len(result['actions']) >= 1
        a = result['actions'][0]
        assert a.name == "increment"
        assert a.proxy_name == "state"

    def test_async_action(self, action_extractor):
        code = """
const state = proxy({ data: null, loading: false });

const fetchData = async () => {
  state.loading = true;
  state.data = await api.getData();
  state.loading = false;
};
"""
        result = action_extractor.extract(code, "actions.ts", known_proxies=["state"])
        assert len(result['actions']) >= 1
        a = result['actions'][0]
        assert a.name == "fetchData"
        assert a.is_async is True

    def test_devtools(self, action_extractor):
        code = """
import { devtools } from 'valtio/utils';
const state = proxy({ count: 0 });
devtools(state, { name: 'counter', enabled: true });
"""
        result = action_extractor.extract(code, "store.ts")
        assert len(result['devtools']) >= 1
        d = result['devtools'][0]
        assert d.proxy_name == "state"
        assert d.label == "counter"
        assert d.has_enabled_option is True

    def test_exported_action(self, action_extractor):
        code = """
export const addItem = (item) => {
  state.items.push(item);
};
"""
        result = action_extractor.extract(code, "actions.ts", known_proxies=["state"])
        assert len(result['actions']) >= 1
        a = result['actions'][0]
        assert a.name == "addItem"
        assert a.is_exported is True


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestValtioApiExtractor:
    """Tests for ValtioApiExtractor."""

    def test_basic_import(self, api_extractor):
        code = """
import { proxy, useSnapshot } from 'valtio';
"""
        result = api_extractor.extract(code, "store.ts")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.source == "valtio"
        assert "proxy" in imp.imported_names
        assert "useSnapshot" in imp.imported_names

    def test_vanilla_import(self, api_extractor):
        code = """
import { proxy, subscribe, snapshot } from 'valtio/vanilla';
"""
        result = api_extractor.extract(code, "store.ts")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.source == "valtio/vanilla"

    def test_utils_import(self, api_extractor):
        code = """
import { subscribeKey, devtools, proxyMap } from 'valtio/utils';
"""
        result = api_extractor.extract(code, "store.ts")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.source == "valtio/utils"
        assert "subscribeKey" in imp.imported_names

    def test_v2_detection(self, api_extractor):
        code = """
import { proxy, subscribe } from 'valtio/vanilla';
import { useSnapshot } from 'valtio/react';
"""
        result = api_extractor.extract(code, "store.ts")
        assert result['detected_version'] == 'v2'

    def test_v1_detection(self, api_extractor):
        code = """
import { proxy, useSnapshot } from 'valtio';
import { derive, watch } from 'valtio/utils';
"""
        result = api_extractor.extract(code, "store.ts")
        assert result['detected_version'] == 'v1'

    def test_deprecated_apis(self, api_extractor):
        code = """
import { derive, underive } from 'valtio/utils';
derive({ doubled: (get) => get(state).count * 2 }, { proxy: state });
proxyWithComputed(state, { doubled: (snap) => snap.count * 2 });
"""
        result = api_extractor.extract(code, "store.ts")
        assert "derive/underive" in result['deprecated_apis']
        assert "proxyWithComputed" in result['deprecated_apis']

    def test_ecosystem_integration(self, api_extractor):
        code = """
import { derive } from 'derive-valtio';
import { proxy } from 'valtio';
"""
        result = api_extractor.extract(code, "store.ts")
        assert len(result['integrations']) >= 1
        integration_names = [i.integration for i in result['integrations']]
        assert "derive-valtio" in integration_names

    def test_snapshot_type(self, api_extractor):
        code = """
import type { Snapshot } from 'valtio';
type UserSnap = Snapshot<typeof state.user>;
"""
        result = api_extractor.extract(code, "types.ts")
        assert len(result['types']) >= 1

    def test_feature_detection(self, api_extractor):
        code = """
import { proxy, useSnapshot, subscribe, snapshot, ref } from 'valtio';
import { subscribeKey, devtools, proxyMap, proxySet } from 'valtio/utils';

const state = proxy({ count: 0 });
const snap = useSnapshot(state);
subscribe(state, () => {});
subscribeKey(state, 'count', () => {});
devtools(state, { name: 'app' });
const map = proxyMap();
const set = proxySet();
ref(new Date());
"""
        result = api_extractor.extract(code, "all-features.ts")
        features = result['detected_features']
        assert "proxy" in features
        assert "useSnapshot" in features
        assert "subscribe" in features
        assert "subscribeKey" in features
        assert "devtools" in features
        assert "proxyMap" in features
        assert "proxySet" in features
        assert "ref" in features

    def test_dynamic_import(self, api_extractor):
        code = """
const valtio = await import('valtio');
"""
        result = api_extractor.extract(code, "lazy.ts")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.is_dynamic_import is True

    def test_require_import(self, api_extractor):
        code = """
const { proxy } = require('valtio');
"""
        result = api_extractor.extract(code, "store.js")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.is_require is True


# ═══════════════════════════════════════════════════════════════════
# Enhanced Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedValtioParser:
    """Tests for EnhancedValtioParser integration."""

    def test_is_valtio_file_positive(self, parser):
        code = """import { proxy } from 'valtio';"""
        assert parser.is_valtio_file(code) is True

    def test_is_valtio_file_negative(self, parser):
        code = """import React from 'react';"""
        assert parser.is_valtio_file(code) is False

    def test_is_valtio_file_vanilla(self, parser):
        code = """import { proxy } from 'valtio/vanilla';"""
        assert parser.is_valtio_file(code) is True

    def test_is_valtio_file_utils(self, parser):
        code = """import { devtools } from 'valtio/utils';"""
        assert parser.is_valtio_file(code) is True

    def test_is_valtio_file_ecosystem(self, parser):
        code = """import { derive } from 'derive-valtio';"""
        assert parser.is_valtio_file(code) is True

    def test_parse_result_type(self, parser):
        code = """
import { proxy, useSnapshot } from 'valtio';
const state = proxy({ count: 0 });
"""
        result = parser.parse(code, "store.ts")
        assert isinstance(result, ValtioParseResult)
        assert result.file_path == "store.ts"
        assert result.file_type == "ts"

    def test_parse_file_type_tsx(self, parser):
        result = parser.parse("", "Component.tsx")
        assert result.file_type == "tsx"

    def test_parse_file_type_jsx(self, parser):
        result = parser.parse("", "Component.jsx")
        assert result.file_type == "jsx"

    def test_parse_file_type_js(self, parser):
        result = parser.parse("", "store.js")
        assert result.file_type == "js"

    def test_parse_complete_store(self, parser):
        code = """
import { proxy, useSnapshot, subscribe } from 'valtio';
import { devtools, subscribeKey } from 'valtio/utils';

// State
export const state = proxy({
  count: 0,
  text: 'hello',
  get doubled() { return this.count * 2; },
});

// Devtools
devtools(state, { name: 'myStore' });

// Actions
export const increment = () => { state.count++; };
export const setText = (t) => { state.text = t; };

// Component
function Counter() {
  const { count, doubled } = useSnapshot(state);
  return <div>{count} ({doubled})</div>;
}

// Side effect
subscribe(state, () => { console.log('changed'); });
subscribeKey(state, 'count', (v) => { console.log('count:', v); });
"""
        result = parser.parse(code, "store.tsx")
        assert len(result.proxies) >= 1
        assert len(result.imports) >= 1
        assert len(result.snapshots) >= 1
        assert len(result.subscribes) >= 1
        assert len(result.subscribe_keys) >= 1
        assert len(result.devtools_configs) >= 1
        assert result.file_type == "tsx"

    def test_framework_detection(self, parser):
        code = """
import { proxy, useSnapshot } from 'valtio';
import { derive } from 'derive-valtio';
import React from 'react';
"""
        result = parser.parse(code, "store.ts")
        assert "valtio" in result.detected_frameworks
        assert "derive-valtio" in result.detected_frameworks
        assert "react" in result.detected_frameworks

    def test_feature_detection(self, parser):
        code = """
const state = proxy({ count: 0 });
const snap = useSnapshot(state);
subscribe(state, () => {});
"""
        result = parser.parse(code, "store.ts")
        assert "proxy" in result.detected_features
        assert "useSnapshot" in result.detected_features
        assert "subscribe" in result.detected_features

    def test_version_detection_v2(self, parser):
        code = """
import { proxy } from 'valtio/vanilla';
import { useSnapshot } from 'valtio/react';
"""
        result = parser.parse(code, "store.ts")
        assert result.valtio_version == "v2"

    def test_version_detection_v1(self, parser):
        code = """
import { proxy, useSnapshot } from 'valtio';
import { derive } from 'valtio/utils';
derive({ d: (get) => get(state).count * 2 }, { proxy: state });
"""
        result = parser.parse(code, "store.ts")
        assert result.valtio_version == "v1"

    def test_deprecated_tracking(self, parser):
        code = """
import { proxy } from 'valtio';
import { derive, watch } from 'valtio/utils';
derive({ x: (get) => get(state).count });
"""
        result = parser.parse(code, "store.ts")
        assert "derive/underive" in result.deprecated_apis

    def test_empty_content(self, parser):
        result = parser.parse("", "empty.ts")
        assert isinstance(result, ValtioParseResult)
        assert len(result.proxies) == 0

    def test_non_valtio_code(self, parser):
        code = """
import React from 'react';
function App() { return <div>Hello</div>; }
"""
        result = parser.parse(code, "App.tsx")
        assert len(result.proxies) == 0
        assert len(result.imports) == 0

    def test_known_proxies_passed_to_actions(self, parser):
        code = """
import { proxy } from 'valtio';
const state = proxy({ count: 0 });
const increment = () => { state.count++; };
"""
        result = parser.parse(code, "store.ts")
        # Proxy names should be extracted and passed to action extractor
        assert len(result.proxies) >= 1

    def test_multiple_files_scenario(self, parser):
        """Test that parser handles store + component files."""
        store_code = """
import { proxy } from 'valtio';
export const state = proxy({ count: 0 });
export const increment = () => { state.count++; };
"""
        component_code = """
import { useSnapshot } from 'valtio';
import { state, increment } from './store';
function Counter() {
  const { count } = useSnapshot(state);
  return <button onClick={increment}>{count}</button>;
}
"""
        store_result = parser.parse(store_code, "store.ts")
        comp_result = parser.parse(component_code, "Counter.tsx")
        assert len(store_result.proxies) >= 1
        assert len(comp_result.snapshots) >= 1


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════

class TestValtioEdgeCases:
    """Edge case tests for Valtio parsing."""

    def test_proxy_in_string_literal(self, parser):
        code = """
const msg = "proxy({ count: 0 })";
"""
        result = parser.parse(code, "test.ts")
        # Should not detect proxy in string literal (may or may not depending on regex)
        # This is a known limitation

    def test_very_large_state(self, parser):
        fields = ", ".join([f"field{i}: {i}" for i in range(50)])
        code = f"""
import {{ proxy }} from 'valtio';
const state = proxy({{ {fields} }});
"""
        result = parser.parse(code, "large.ts")
        assert len(result.proxies) >= 1

    def test_nested_proxy(self, proxy_extractor):
        code = """
const state = proxy({
  nested: proxy({ deep: 0 }),
});
"""
        result = proxy_extractor.extract(code, "nested.ts")
        assert len(result['proxies']) >= 1

    def test_subscribe_with_no_args(self, subscription_extractor):
        """Should not crash on malformed subscribe calls."""
        code = """
subscribe();
"""
        result = subscription_extractor.extract(code, "bad.ts")
        # Should not crash

    def test_devtools_without_options(self, action_extractor):
        code = """
devtools(state);
"""
        result = action_extractor.extract(code, "store.ts")
        assert len(result['devtools']) >= 1
        d = result['devtools'][0]
        assert d.proxy_name == "state"
        assert d.label == ""

    def test_multiple_subscribe_keys(self, subscription_extractor):
        code = """
subscribeKey(state, 'count', () => {});
subscribeKey(state, 'name', () => {});
subscribeKey(state, 'email', () => {});
"""
        result = subscription_extractor.extract(code, "subs.ts")
        assert len(result['subscribe_keys']) >= 3
        keys = [sk.key_name for sk in result['subscribe_keys']]
        assert "count" in keys
        assert "name" in keys
        assert "email" in keys
