"""
Tests for Expo extractors and EnhancedExpoParser.

Part of CodeTrellis v5.7 Expo Framework Support.
Tests cover:
- Config extraction (app.json, app.config.js, eas.json)
- Module extraction (50+ expo-* SDK modules, permissions, assets)
- Router extraction (routes, layouts, groups, API routes, versions)
- Plugin extraction (config plugins, custom plugins, Modules API)
- API extraction (imports, SDK version, EAS, workflow, integrations)
- Expo parser integration (framework detection, SDK version, is_expo_file)
"""

import pytest
from codetrellis.expo_parser_enhanced import (
    EnhancedExpoParser,
    ExpoParseResult,
)
from codetrellis.extractors.expo import (
    ExpoConfigExtractor,
    ExpoConfigInfo,
    ExpoEASConfigInfo,
    ExpoPluginConfigInfo,
    ExpoModuleExtractor,
    ExpoModuleUsageInfo,
    ExpoPermissionInfo,
    ExpoAssetInfo,
    ExpoRouterExtractor,
    ExpoRouteInfo,
    ExpoLayoutInfo,
    ExpoRouteGroupInfo,
    ExpoApiRouteInfo,
    ExpoPluginExtractor,
    ExpoConfigPluginInfo,
    ExpoModulesAPIInfo,
    ExpoApiExtractor,
    ExpoImportInfo,
    ExpoIntegrationInfo,
    ExpoEASInfo,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedExpoParser()


@pytest.fixture
def config_extractor():
    return ExpoConfigExtractor()


@pytest.fixture
def module_extractor():
    return ExpoModuleExtractor()


@pytest.fixture
def router_extractor():
    return ExpoRouterExtractor()


@pytest.fixture
def plugin_extractor():
    return ExpoPluginExtractor()


@pytest.fixture
def api_extractor():
    return ExpoApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Config Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestExpoConfigExtractor:
    """Tests for ExpoConfigExtractor."""

    def test_app_json_basic(self, config_extractor):
        content = '''{
  "expo": {
    "name": "MyExpoApp",
    "slug": "my-expo-app",
    "sdkVersion": "52.0.0",
    "version": "1.0.0",
    "platforms": ["ios", "android", "web"],
    "scheme": "myapp",
    "orientation": "portrait",
    "userInterfaceStyle": "automatic",
    "icon": "./assets/icon.png",
    "splash": {
      "image": "./assets/splash.png",
      "resizeMode": "contain"
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./assets/adaptive-icon.png"
      }
    }
  }
}'''
        result = config_extractor.extract(content, "app.json")
        configs = result.get('configs', [])
        assert len(configs) >= 1
        cfg = configs[0]
        assert cfg.name == "MyExpoApp"
        assert cfg.slug == "my-expo-app"
        assert cfg.sdk_version == "52.0.0"
        assert cfg.version == "1.0.0"
        assert 'ios' in cfg.platforms
        assert 'android' in cfg.platforms
        assert cfg.scheme == "myapp"
        assert cfg.has_splash
        assert cfg.has_icon
        assert cfg.has_adaptive_icon
        assert cfg.orientation == "portrait"
        assert cfg.user_interface_style == "automatic"
        assert cfg.config_type == "app.json"
        assert cfg.workflow == "managed"

    def test_app_json_with_plugins(self, config_extractor):
        content = '''{
  "expo": {
    "name": "PluginApp",
    "slug": "plugin-app",
    "plugins": [
      "expo-camera",
      "expo-location",
      ["expo-build-properties", { "android": { "compileSdkVersion": 34 } }],
      "expo-router"
    ]
  }
}'''
        result = config_extractor.extract(content, "app.json")
        configs = result.get('configs', [])
        assert len(configs) >= 1
        cfg = configs[0]
        assert 'expo-camera' in cfg.plugins
        assert 'expo-location' in cfg.plugins
        assert 'expo-build-properties' in cfg.plugins
        assert 'expo-router' in cfg.plugins

        plugin_configs = result.get('plugin_configs', [])
        assert len(plugin_configs) >= 4
        names = [p.name for p in plugin_configs]
        assert 'expo-camera' in names
        build_props = [p for p in plugin_configs if p.name == 'expo-build-properties']
        assert len(build_props) >= 1
        assert build_props[0].options.get('android', {}).get('compileSdkVersion') == 34

    def test_app_json_with_runtime_version_policy(self, config_extractor):
        content = '''{
  "expo": {
    "name": "OTAApp",
    "slug": "ota-app",
    "runtimeVersion": {
      "policy": "fingerprint"
    },
    "updates": {
      "url": "https://u.expo.dev/my-project-id"
    }
  }
}'''
        result = config_extractor.extract(content, "app.json")
        configs = result.get('configs', [])
        cfg = configs[0]
        assert cfg.runtime_version == "fingerprint"
        assert cfg.updates_url == "https://u.expo.dev/my-project-id"

    def test_app_config_js(self, config_extractor):
        content = '''
export default ({ config }) => ({
  ...config,
  name: "DynamicApp",
  slug: "dynamic-app",
  scheme: "dynamicapp",
  platforms: ["ios", "android"],
  splash: {
    image: "./assets/splash.png",
  },
  icon: "./assets/icon.png",
  plugins: [
    "expo-camera",
    "expo-router"
  ],
});
'''
        result = config_extractor.extract(content, "app.config.js")
        configs = result.get('configs', [])
        assert len(configs) >= 1
        cfg = configs[0]
        assert cfg.name == "DynamicApp"
        assert cfg.slug == "dynamic-app"
        assert cfg.scheme == "dynamicapp"
        assert cfg.config_type == "app.config.js"
        assert cfg.has_splash
        assert cfg.has_icon

    def test_app_config_ts(self, config_extractor):
        content = '''
import { ExpoConfig, ConfigContext } from "expo/config";

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: "TypedApp",
  slug: "typed-app",
  runtimeVersion: "1.0.0",
});
'''
        result = config_extractor.extract(content, "app.config.ts")
        configs = result.get('configs', [])
        assert len(configs) >= 1
        cfg = configs[0]
        assert cfg.name == "TypedApp"
        assert cfg.config_type == "app.config.ts"
        assert cfg.runtime_version == "1.0.0"

    def test_eas_json(self, config_extractor):
        content = '''{
  "cli": {
    "version": ">= 3.0.0"
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "channel": "development"
    },
    "preview": {
      "distribution": "internal",
      "channel": "preview"
    },
    "production": {
      "distribution": "store",
      "channel": "production"
    }
  },
  "submit": {
    "production": {
      "ios": {
        "appleId": "user@example.com"
      }
    }
  }
}'''
        result = config_extractor.extract(content, "eas.json")
        eas_configs = result.get('eas_configs', [])
        assert len(eas_configs) >= 1
        eas = eas_configs[0]
        assert 'development' in eas.build_profiles
        assert 'preview' in eas.build_profiles
        assert 'production' in eas.build_profiles
        assert eas.has_eas_submit
        assert eas.has_eas_update
        assert 'development' in eas.update_channels
        assert 'production' in eas.update_channels

    def test_inline_config_constants(self, config_extractor):
        content = '''
import Constants from 'expo-constants';

const appName = Constants.expoConfig?.name;
const version = Constants.manifest?.version;
'''
        result = config_extractor.extract(content, "utils.ts")
        configs = result.get('configs', [])
        assert len(configs) >= 1
        assert configs[0].config_type == 'inline'

    def test_invalid_json_graceful(self, config_extractor):
        content = '{ invalid json ,,, }'
        result = config_extractor.extract(content, "app.json")
        assert 'configs' in result


# ═══════════════════════════════════════════════════════════════════
# Module Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestExpoModuleExtractor:
    """Tests for ExpoModuleExtractor."""

    def test_basic_module_imports(self, module_extractor):
        code = '''
import * as Camera from 'expo-camera';
import * as Location from 'expo-location';
import * as FileSystem from 'expo-file-system';
'''
        result = module_extractor.extract(code, "screen.tsx")
        modules = result.get('modules', [])
        module_names = [m.module for m in modules]
        assert 'expo-camera' in module_names
        assert 'expo-location' in module_names
        assert 'expo-file-system' in module_names

    def test_module_categories(self, module_extractor):
        code = '''
import { Camera } from 'expo-camera';
import * as Location from 'expo-location';
import * as SecureStore from 'expo-secure-store';
import * as Notifications from 'expo-notifications';
'''
        result = module_extractor.extract(code, "app.tsx")
        modules = result.get('modules', [])
        categories = {m.module: m.category for m in modules}
        assert categories.get('expo-camera') == 'media'
        assert categories.get('expo-location') == 'location'
        assert categories.get('expo-secure-store') == 'storage'
        assert categories.get('expo-notifications') == 'notifications'

    def test_permission_requires(self, module_extractor):
        code = '''
import { Camera } from 'expo-camera';
import * as Notifications from 'expo-notifications';
import { LinearGradient } from 'expo-linear-gradient';
'''
        result = module_extractor.extract(code, "screen.tsx")
        modules = result.get('modules', [])
        perm_required = {m.module: m.requires_permission for m in modules}
        assert perm_required.get('expo-camera') is True
        assert perm_required.get('expo-notifications') is True
        assert perm_required.get('expo-linear-gradient') is False

    def test_named_imports_as_apis(self, module_extractor):
        code = '''
import { CameraView, useCameraPermissions, CameraType } from 'expo-camera';
'''
        result = module_extractor.extract(code, "camera.tsx")
        modules = result.get('modules', [])
        assert len(modules) >= 1
        cam = modules[0]
        assert 'CameraView' in cam.apis_used
        assert 'useCameraPermissions' in cam.apis_used

    def test_camera_permission(self, module_extractor):
        code = '''
import { CameraView, useCameraPermissions } from 'expo-camera';

export function CameraScreen() {
    const [permission, requestPermission] = useCameraPermissions();
    if (!permission?.granted) {
        return <Button onPress={requestPermission} title="Grant Camera" />;
    }
    return <CameraView style={{ flex: 1 }} />;
}
'''
        result = module_extractor.extract(code, "camera.tsx")
        permissions = result.get('permissions', [])
        assert len(permissions) >= 1
        assert permissions[0].permission_type == 'camera'

    def test_location_foreground_permission(self, module_extractor):
        code = '''
import * as Location from 'expo-location';

async function getLocation() {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status === 'granted') {
        return await Location.getCurrentPositionAsync({});
    }
}
'''
        result = module_extractor.extract(code, "location.ts")
        permissions = result.get('permissions', [])
        fg = [p for p in permissions if p.is_foreground]
        assert len(fg) >= 1
        assert fg[0].permission_type == 'location'

    def test_location_background_permission(self, module_extractor):
        code = '''
import * as Location from 'expo-location';

async function enableBackground() {
    await Location.requestBackgroundPermissionsAsync();
}
'''
        result = module_extractor.extract(code, "background.ts")
        permissions = result.get('permissions', [])
        bg = [p for p in permissions if p.is_background]
        assert len(bg) >= 1

    def test_notification_permission(self, module_extractor):
        code = '''
import * as Notifications from 'expo-notifications';

async function requestPushPerms() {
    const { status } = await Notifications.requestPermissionsAsync();
    return status;
}
'''
        result = module_extractor.extract(code, "push.ts")
        permissions = result.get('permissions', [])
        notif = [p for p in permissions if p.permission_type == 'notifications']
        assert len(notif) >= 1

    def test_font_loading_asset(self, module_extractor):
        code = '''
import { useFonts } from 'expo-font';

export function App() {
    const [loaded] = useFonts({
        'SpaceMono': require('./assets/fonts/SpaceMono-Regular.ttf'),
        'Inter': require('./assets/fonts/Inter-Regular.ttf'),
    });
    if (!loaded) return null;
    return <Main />;
}
'''
        result = module_extractor.extract(code, "App.tsx")
        assets = result.get('assets', [])
        fonts = [a for a in assets if a.asset_type == 'font']
        assert len(fonts) >= 1
        assert fonts[0].source == 'expo-font'
        assert fonts[0].is_preloaded

    def test_vector_icons_asset(self, module_extractor):
        code = '''
import { Ionicons } from '@expo/vector-icons';
import { MaterialIcons } from '@expo/vector-icons/MaterialIcons';
'''
        result = module_extractor.extract(code, "icons.tsx")
        assets = result.get('assets', [])
        icons = [a for a in assets if a.asset_type == 'icon']
        assert len(icons) >= 1
        assert icons[0].source == '@expo/vector-icons'

    def test_async_api_detection(self, module_extractor):
        code = '''
import * as FileSystem from 'expo-file-system';

const data = await FileSystem.readAsStringAsync(uri);
'''
        result = module_extractor.extract(code, "files.ts")
        modules = result.get('modules', [])
        fs = [m for m in modules if m.module == 'expo-file-system']
        assert len(fs) >= 1


# ═══════════════════════════════════════════════════════════════════
# Router Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestExpoRouterExtractor:
    """Tests for ExpoRouterExtractor."""

    def test_stack_layout(self, router_extractor):
        code = '''
import { Stack } from 'expo-router';

export default function Layout() {
    return (
        <Stack>
            <Stack.Screen name="index" options={{ title: 'Home' }} />
            <Stack.Screen name="profile" options={{ title: 'Profile' }} />
            <Stack.Screen name="settings" options={{ headerShown: false }} />
        </Stack>
    );
}
'''
        result = router_extractor.extract(code, "app/_layout.tsx")
        layouts = result.get('layouts', [])
        assert len(layouts) >= 1
        layout = layouts[0]
        assert layout.layout_type == "stack"
        assert 'index' in layout.screens
        assert 'profile' in layout.screens
        assert 'settings' in layout.screens
        assert layout.has_header_config

    def test_tabs_layout(self, router_extractor):
        code = '''
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function TabLayout() {
    return (
        <Tabs>
            <Tabs.Screen
                name="index"
                options={{
                    title: 'Home',
                    tabBarIcon: ({ color }) => <Ionicons name="home" color={color} />,
                }}
            />
            <Tabs.Screen
                name="explore"
                options={{
                    title: 'Explore',
                    tabBarLabel: 'Explore',
                }}
            />
        </Tabs>
    );
}
'''
        result = router_extractor.extract(code, "app/(tabs)/_layout.tsx")
        layouts = result.get('layouts', [])
        assert len(layouts) >= 1
        layout = layouts[0]
        assert layout.layout_type == "tabs"
        assert layout.has_tab_bar_config
        assert layout.route_group == "tabs"

    def test_drawer_layout(self, router_extractor):
        code = '''
import { Drawer } from 'expo-router/drawer';

export default function DrawerLayout() {
    return (
        <Drawer>
            <Drawer.Screen name="index" />
            <Drawer.Screen name="about" />
        </Drawer>
    );
}
'''
        result = router_extractor.extract(code, "app/_layout.tsx")
        layouts = result.get('layouts', [])
        assert len(layouts) >= 1
        assert layouts[0].layout_type == "drawer"

    def test_route_from_file_path(self, router_extractor):
        code = '''
export default function SettingsScreen() {
    return <View><Text>Settings</Text></View>;
}
'''
        result = router_extractor.extract(code, "app/settings.tsx")
        routes = result.get('routes', [])
        assert len(routes) >= 1
        assert routes[0].route_path == "/settings"
        assert not routes[0].is_dynamic

    def test_index_route(self, router_extractor):
        code = '''
export default function Home() {
    return <View><Text>Home</Text></View>;
}
'''
        result = router_extractor.extract(code, "app/index.tsx")
        routes = result.get('routes', [])
        assert len(routes) >= 1
        assert routes[0].route_path == "/"
        assert routes[0].is_index

    def test_dynamic_route(self, router_extractor):
        code = '''
import { useLocalSearchParams } from 'expo-router';

export default function UserProfile() {
    const { id } = useLocalSearchParams();
    return <Text>User: {id}</Text>;
}
'''
        result = router_extractor.extract(code, "app/user/[id].tsx")
        routes = result.get('routes', [])
        assert len(routes) >= 1
        route = routes[0]
        assert route.is_dynamic
        assert 'id' in route.dynamic_params
        assert route.route_path == "/user/[id]"

    def test_catch_all_route(self, router_extractor):
        code = '''
export default function NotFound() {
    return <Text>Not found</Text>;
}
'''
        result = router_extractor.extract(code, "app/[...missing].tsx")
        routes = result.get('routes', [])
        assert len(routes) >= 1
        assert routes[0].is_catch_all
        assert 'missing' in routes[0].dynamic_params

    def test_api_route(self, router_extractor):
        code = '''
export async function GET(request: Request) {
    return Response.json({ users: [] });
}

export async function POST(request: Request) {
    const body = await request.json();
    return Response.json({ created: true });
}
'''
        result = router_extractor.extract(code, "app/api/users+api.ts")
        api_routes = result.get('api_routes', [])
        assert len(api_routes) >= 1
        api = api_routes[0]
        assert 'GET' in api.http_methods
        assert 'POST' in api.http_methods

    def test_route_group(self, router_extractor):
        code = '''
export default function AuthScreen() {
    return <View><Text>Login</Text></View>;
}
'''
        result = router_extractor.extract(code, "app/(auth)/login.tsx")
        groups = result.get('route_groups', [])
        assert len(groups) >= 1
        assert groups[0].group_name == "auth"

    def test_error_boundary_export(self, router_extractor):
        code = '''
export default function Screen() {
    return <View />;
}

export function ErrorBoundary({ error }) {
    return <Text>Error: {error.message}</Text>;
}
'''
        result = router_extractor.extract(code, "app/details.tsx")
        routes = result.get('routes', [])
        assert len(routes) >= 1
        assert routes[0].has_error_boundary
        assert 'ErrorBoundary' in routes[0].exports

    def test_navigation_hooks(self, router_extractor):
        code = '''
import { useRouter, useLocalSearchParams, useSegments, usePathname } from 'expo-router';

export default function Screen() {
    const router = useRouter();
    const params = useLocalSearchParams();
    const segments = useSegments();
    const pathname = usePathname();
    return null;
}
'''
        result = router_extractor.extract(code, "app/screen.tsx")
        hooks = result.get('navigation_hooks', [])
        assert 'useRouter' in hooks
        assert 'useLocalSearchParams' in hooks
        assert 'useSegments' in hooks
        assert 'usePathname' in hooks

    def test_router_version_v3_typed(self, router_extractor):
        code = '''
import { useRouter, Link, Href } from 'expo-router';

export default function Home() {
    const router = useRouter();
    return <Link href="/profile" />;
}
'''
        result = router_extractor.extract(code, "app/index.tsx")
        assert result.get('router_version') == 3

    def test_router_version_v2(self, router_extractor):
        code = '''
import { useRouter, Link } from 'expo-router';

export default function Home() {
    const router = useRouter();
    return <Link href="/profile">Go</Link>;
}
'''
        result = router_extractor.extract(code, "app/index.tsx")
        assert result.get('router_version') == 2

    def test_non_app_directory_no_routes(self, router_extractor):
        code = '''
export default function Component() { return null; }
'''
        result = router_extractor.extract(code, "src/components/Button.tsx")
        routes = result.get('routes', [])
        assert len(routes) == 0


# ═══════════════════════════════════════════════════════════════════
# Plugin Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestExpoPluginExtractor:
    """Tests for ExpoPluginExtractor."""

    def test_plugins_from_app_json(self, plugin_extractor):
        content = '''{
  "expo": {
    "plugins": [
      "expo-camera",
      "expo-location",
      "sentry-expo",
      "./my-custom-plugin"
    ]
  }
}'''
        result = plugin_extractor.extract(content, "app.json")
        plugins = result.get('config_plugins', [])
        names = [p.name for p in plugins]
        assert 'expo-camera' in names
        assert 'expo-location' in names
        assert 'sentry-expo' in names
        custom = [p for p in plugins if p.is_custom]
        assert len(custom) >= 1
        assert custom[0].name == './my-custom-plugin'

    def test_custom_plugin_with_android_manifest(self, plugin_extractor):
        code = '''
import { withAndroidManifest } from '@expo/config-plugins';

const withCustomPermissions = (config) => {
    return withAndroidManifest(config, (config) => {
        const manifest = config.modResults;
        manifest.manifest.permission = manifest.manifest.permission || [];
        return config;
    });
};

module.exports = withCustomPermissions;
'''
        result = plugin_extractor.extract(code, "plugins/custom-permissions.js")
        assert result.get('has_custom_plugins') is True
        plugins = result.get('config_plugins', [])
        android_plugins = [p for p in plugins if p.modifies_android]
        assert len(android_plugins) >= 1
        assert android_plugins[0].name == 'withAndroidManifest'

    def test_custom_plugin_with_info_plist(self, plugin_extractor):
        code = '''
import { withInfoPlist } from '@expo/config-plugins';

const withBackgroundModes = (config) => {
    return withInfoPlist(config, (config) => {
        config.modResults.UIBackgroundModes = ['location', 'audio'];
        return config;
    });
};
'''
        result = plugin_extractor.extract(code, "plugins/bg-modes.js")
        assert result.get('has_custom_plugins') is True
        plugins = result.get('config_plugins', [])
        ios_plugins = [p for p in plugins if p.modifies_ios]
        assert len(ios_plugins) >= 1
        assert ios_plugins[0].name == 'withInfoPlist'

    def test_dangerous_mod_detection(self, plugin_extractor):
        code = '''
import { withDangerousMod } from '@expo/config-plugins';

const withCustomNativeCode = (config) => {
    return withDangerousMod(config, ['ios', async (config) => {
        return config;
    }]);
};
'''
        result = plugin_extractor.extract(code, "plugins/dangerous.js")
        plugins = result.get('config_plugins', [])
        dangerous = [p for p in plugins if p.name == 'withDangerousMod']
        assert len(dangerous) >= 1
        assert dangerous[0].modifies_android
        assert dangerous[0].modifies_ios

    def test_expo_modules_api_swift(self, plugin_extractor):
        code = '''
import ExpoModulesCore

public class MyModule: Module {
    public func definition() -> ModuleDefinition {
        Name("MyModule")

        AsyncFunction("fetchData") { (url: String) -> String in
            return try await fetch(url)
        }

        Function("computeHash") { (data: String) -> String in
            return hash(data)
        }

        Property("isReady") {
            return true
        }

        Events("onDataReceived", "onError")

        View(MyNativeView.self) {
            Prop("title") { (view: MyNativeView, title: String) in
                view.title = title
            }
        }
    }
}
'''
        result = plugin_extractor.extract(code, "ios/MyModule.swift")
        modules_api = result.get('modules_api', [])
        assert len(modules_api) >= 1
        mod = modules_api[0]
        assert mod.module_name == "MyModule"
        assert mod.language == "swift"
        assert mod.has_view
        assert mod.has_events
        assert mod.has_async_function
        assert 'fetchData' in mod.exported_methods or 'computeHash' in mod.exported_methods
        assert 'isReady' in mod.exported_properties

    def test_expo_modules_api_kotlin(self, plugin_extractor):
        code = '''
package com.myapp

import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition

class SensorModule : Module() {
    override fun definition() = ModuleDefinition {
        Name("SensorModule")

        Function("startListening") {
            sensorManager.start()
        }

        Property("isListening") {
            return@Property sensorManager.isActive
        }
    }
}
'''
        result = plugin_extractor.extract(code, "android/SensorModule.kt")
        modules_api = result.get('modules_api', [])
        assert len(modules_api) >= 1
        assert modules_api[0].module_name == "SensorModule"
        assert modules_api[0].language == "kotlin"

    def test_no_plugins_in_regular_code(self, plugin_extractor):
        code = '''
import { View, Text } from 'react-native';
export default function Home() { return <View><Text>Hi</Text></View>; }
'''
        result = plugin_extractor.extract(code, "app/index.tsx")
        assert result.get('has_custom_plugins') is False
        assert len(result.get('config_plugins', [])) == 0


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestExpoApiExtractor:
    """Tests for ExpoApiExtractor."""

    def test_expo_imports(self, api_extractor):
        code = '''
import * as Camera from 'expo-camera';
import * as Location from 'expo-location';
import { useRouter } from 'expo-router';
import Constants from 'expo-constants';
'''
        result = api_extractor.extract(code, "screen.tsx")
        imports = result.get('imports')
        assert imports is not None
        assert 'expo-camera' in imports.expo_imports
        assert 'expo-location' in imports.expo_imports
        assert 'expo-router' in imports.expo_imports
        assert 'expo-constants' in imports.expo_imports
        assert imports.has_expo_router
        assert imports.import_count >= 4

    def test_sdk_version_from_json(self, api_extractor):
        content = '''{
  "expo": {
    "sdkVersion": "52.0.0"
  }
}'''
        result = api_extractor.extract(content, "app.json")
        assert result.get('sdk_version') == 52

    def test_sdk_version_from_package(self, api_extractor):
        content = '''{
  "dependencies": {
    "expo": "~51.0.0",
    "expo-router": "^3.0.0"
  }
}'''
        result = api_extractor.extract(content, "package.json")
        assert result.get('sdk_version') == 51

    def test_eas_config_detection(self, api_extractor):
        content = '''{
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "channel": "development"
    },
    "production": {
      "channel": "production"
    }
  },
  "submit": {
    "production": {}
  }
}'''
        result = api_extractor.extract(content, "eas.json")
        eas = result.get('eas')
        assert eas is not None
        assert eas.has_eas_build
        assert eas.has_eas_submit
        assert eas.has_eas_update
        assert 'development' in eas.update_channels
        assert 'production' in eas.update_channels

    def test_managed_workflow_detection(self, api_extractor):
        code = '''
import Constants from 'expo-constants';
const config = Constants.expoConfig;
'''
        result = api_extractor.extract(code, "config.ts")
        assert result.get('workflow') == 'managed'

    def test_bare_workflow_detection(self, api_extractor):
        code = '''
// Build commands
// react-native run-ios
// react-native run-android
// ios/Podfile present
'''
        result = api_extractor.extract(code, "README.md")
        assert result.get('workflow') == 'bare'

    def test_deep_linking_integration(self, api_extractor):
        code = '''
import * as Linking from 'expo-linking';

const url = Linking.createURL('home', { queryParams: { id: '123' } });
'''
        result = api_extractor.extract(code, "linking.ts")
        integrations = result.get('integrations', [])
        deep = [i for i in integrations if i.pattern_name == 'deep-linking']
        assert len(deep) >= 1
        assert 'expo-linking' in deep[0].modules_involved

    def test_push_notification_integration(self, api_extractor):
        code = '''
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';

async function registerForPushNotificationsAsync() {
    if (!Device.isDevice) return;
    const token = await Notifications.getExpoPushTokenAsync();
    return token;
}
'''
        result = api_extractor.extract(code, "push.ts")
        integrations = result.get('integrations', [])
        push = [i for i in integrations if i.pattern_name == 'push-notifications']
        assert len(push) >= 1

    def test_social_auth_integration(self, api_extractor):
        code = '''
import * as AuthSession from 'expo-auth-session';
import * as WebBrowser from 'expo-web-browser';

const redirectUri = AuthSession.makeRedirectUri({ useProxy: true });
'''
        result = api_extractor.extract(code, "auth.ts")
        integrations = result.get('integrations', [])
        auth = [i for i in integrations if i.pattern_name == 'social-auth']
        assert len(auth) >= 1

    def test_dev_client_detection(self, api_extractor):
        code = '''
import devClient from 'expo-dev-client';
'''
        result = api_extractor.extract(code, "index.ts")
        imports = result.get('imports')
        assert imports is not None
        assert imports.has_expo_dev_client

    def test_runtime_version_policy(self, api_extractor):
        content = '''{
  "build": {
    "production": {
      "channel": "production"
    }
  },
  "runtimeVersion": {
    "policy": "fingerprint"
  }
}'''
        result = api_extractor.extract(content, "eas.json")
        eas = result.get('eas')
        assert eas is not None
        assert eas.runtime_version_policy == 'fingerprint'


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedExpoParser:
    """Tests for the integrated EnhancedExpoParser."""

    def test_is_expo_file_config(self, parser):
        assert parser.is_expo_file("", "app.json")
        assert parser.is_expo_file("", "app.config.js")
        assert parser.is_expo_file("", "app.config.ts")
        assert parser.is_expo_file("", "eas.json")

    def test_is_expo_file_expo_imports(self, parser):
        code = "import * as Camera from 'expo-camera';"
        assert parser.is_expo_file(code, "screen.tsx")

    def test_is_expo_file_expo_at_imports(self, parser):
        code = "import { Ionicons } from '@expo/vector-icons';"
        assert parser.is_expo_file(code, "icons.tsx")

    def test_is_expo_file_app_directory(self, parser):
        code = "export default function Screen() { return null; }"
        assert parser.is_expo_file(code, "app/home.tsx")

    def test_is_expo_file_config_plugin(self, parser):
        code = '''
import { withAndroidManifest } from '@expo/config-plugins';
'''
        assert parser.is_expo_file(code, "plugins/custom.js")

    def test_is_expo_file_expo_apis(self, parser):
        code = "SplashScreen.preventAutoHideAsync();"
        assert parser.is_expo_file(code, "app.tsx")

    def test_is_expo_file_negative(self, parser):
        code = '''
import React from 'react';
export function WebApp() { return <div>Hello</div>; }
'''
        assert not parser.is_expo_file(code, "component.tsx")

    def test_is_config_file(self, parser):
        assert parser.is_config_file("app.json")
        assert parser.is_config_file("app.config.js")
        assert parser.is_config_file("app.config.ts")
        assert parser.is_config_file("eas.json")
        assert not parser.is_config_file("package.json")
        assert not parser.is_config_file("tsconfig.json")

    def test_framework_detection_core(self, parser):
        code = '''
import { registerRootComponent } from 'expo';
import Constants from 'expo-constants';
import * as Updates from 'expo-updates';
'''
        result = parser.parse(code, "App.tsx")
        assert 'expo' in result.detected_frameworks
        assert 'expo-constants' in result.detected_frameworks
        assert 'expo-updates' in result.detected_frameworks

    def test_framework_detection_router(self, parser):
        code = '''
import { Stack, useRouter, useLocalSearchParams } from 'expo-router';
'''
        result = parser.parse(code, "app/_layout.tsx")
        assert 'expo-router' in result.detected_frameworks

    def test_framework_detection_media(self, parser):
        code = '''
import { CameraView, useCameraPermissions } from 'expo-camera';
import { Audio, Video } from 'expo-av';
import * as ImagePicker from 'expo-image-picker';
import { Image } from 'expo-image';
'''
        result = parser.parse(code, "media.tsx")
        assert 'expo-camera' in result.detected_frameworks
        assert 'expo-av' in result.detected_frameworks
        assert 'expo-image-picker' in result.detected_frameworks
        assert 'expo-image' in result.detected_frameworks

    def test_framework_detection_auth(self, parser):
        code = '''
import { useAuthRequest, makeRedirectUri } from 'expo-auth-session';
import * as WebBrowser from 'expo-web-browser';
import * as AppleAuth from 'expo-apple-authentication';
import * as LocalAuth from 'expo-local-authentication';
'''
        result = parser.parse(code, "auth.tsx")
        assert 'expo-auth-session' in result.detected_frameworks
        assert 'expo-web-browser' in result.detected_frameworks
        assert 'expo-apple-authentication' in result.detected_frameworks
        assert 'expo-local-authentication' in result.detected_frameworks

    def test_framework_detection_config_plugins(self, parser):
        code = '''
import { withAndroidManifest, withInfoPlist } from '@expo/config-plugins';
'''
        result = parser.parse(code, "plugin.js")
        assert 'expo-config-plugins' in result.detected_frameworks

    def test_framework_detection_icons(self, parser):
        code = '''
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
'''
        result = parser.parse(code, "icons.tsx")
        assert 'expo-vector-icons' in result.detected_frameworks

    def test_sdk_version_detection_52(self, parser):
        code = '''
import { useFormStatus, useOptimistic } from 'react';
'''
        result = parser.parse(code, "form.tsx")
        assert result.sdk_version == 52

    def test_sdk_version_detection_51(self, parser):
        code = '''
import { CameraView } from 'expo-camera';
import { useVideoPlayer, VideoView } from 'expo-video';
'''
        result = parser.parse(code, "video.tsx")
        assert result.sdk_version == 51

    def test_sdk_version_detection_50(self, parser):
        code = '''
import { Href } from 'expo-router';
'''
        result = parser.parse(code, "nav.tsx")
        assert result.sdk_version == 50

    def test_sdk_version_detection_48(self, parser):
        code = '''
import { useLocalSearchParams } from 'expo-router';
'''
        result = parser.parse(code, "detail.tsx")
        assert result.sdk_version == 48

    def test_sdk_version_from_config(self, parser):
        content = '''{
  "expo": {
    "name": "TestApp",
    "slug": "test-app",
    "sdkVersion": "52.0.0"
  }
}'''
        result = parser.parse(content, "app.json")
        assert result.sdk_version == 52

    def test_full_expo_screen_parse(self, parser):
        """Test parsing a realistic Expo screen file."""
        code = '''
import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, StyleSheet } from 'react-native';
import { useRouter, useLocalSearchParams, Link } from 'expo-router';
import * as Location from 'expo-location';
import * as Haptics from 'expo-haptics';
import { Image } from 'expo-image';
import { Ionicons } from '@expo/vector-icons';

export default function NearbyScreen() {
    const router = useRouter();
    const [places, setPlaces] = useState([]);

    useEffect(() => {
        (async () => {
            const { status } = await Location.requestForegroundPermissionsAsync();
            if (status === 'granted') {
                const loc = await Location.getCurrentPositionAsync({});
                fetchNearby(loc.coords);
            }
        })();
    }, []);

    const onSelect = (place) => {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
        router.push(`/place/${place.id}`);
    };

    return (
        <View style={styles.container}>
            <FlatList
                data={places}
                keyExtractor={(item) => item.id}
                renderItem={({ item }) => (
                    <Link href={`/place/${item.id}`} asChild>
                        <View>
                            <Image source={{ uri: item.imageUrl }} contentFit="cover" />
                            <Text>{item.name}</Text>
                            <Ionicons name="location" />
                        </View>
                    </Link>
                )}
            />
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1 },
});
'''
        result = parser.parse(code, "app/nearby.tsx")

        # Framework detection
        assert 'expo-router' in result.detected_frameworks
        assert 'expo-location' in result.detected_frameworks
        assert 'expo-haptics' in result.detected_frameworks
        assert 'expo-image' in result.detected_frameworks
        assert 'expo-vector-icons' in result.detected_frameworks

        # Modules
        module_names = [m.module for m in result.modules]
        assert 'expo-location' in module_names
        assert 'expo-haptics' in module_names
        assert 'expo-image' in module_names

        # Permissions
        assert len(result.permissions) >= 1

        # Route
        assert len(result.routes) >= 1
        assert result.routes[0].route_path == "/nearby"

        # Navigation hooks
        assert 'useRouter' in result.navigation_hooks
        assert 'useLocalSearchParams' in result.navigation_hooks

        # SDK version (expo-image → 49, useLocalSearchParams → 48)
        assert result.sdk_version >= 49

    def test_full_expo_layout_parse(self, parser):
        """Test parsing a layout file with tabs."""
        code = '''
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export default function TabLayout() {
    const insets = useSafeAreaInsets();
    return (
        <Tabs
            screenOptions={{
                headerShown: false,
                tabBarStyle: { paddingBottom: insets.bottom },
            }}
        >
            <Tabs.Screen
                name="index"
                options={{
                    title: 'Home',
                    tabBarIcon: ({ color, size }) => (
                        <Ionicons name="home-outline" size={size} color={color} />
                    ),
                }}
            />
            <Tabs.Screen
                name="explore"
                options={{
                    title: 'Explore',
                    tabBarIcon: ({ color, size }) => (
                        <Ionicons name="compass-outline" size={size} color={color} />
                    ),
                }}
            />
            <Tabs.Screen
                name="profile"
                options={{
                    title: 'Profile',
                    tabBarIcon: ({ color, size }) => (
                        <Ionicons name="person-outline" size={size} color={color} />
                    ),
                }}
            />
        </Tabs>
    );
}
'''
        result = parser.parse(code, "app/(tabs)/_layout.tsx")

        # Layouts
        assert len(result.layouts) >= 1
        layout = result.layouts[0]
        assert layout.layout_type == "tabs"
        assert layout.has_tab_bar_config
        assert 'index' in layout.screens
        assert 'explore' in layout.screens
        assert 'profile' in layout.screens

        # Framework detection
        assert 'expo-router' in result.detected_frameworks
        assert 'expo-vector-icons' in result.detected_frameworks

    def test_expo_api_route_parse(self, parser):
        """Test parsing an API route file."""
        code = '''
export async function GET(request: Request) {
    const items = await db.items.findAll();
    return Response.json(items);
}

export async function POST(request: Request) {
    const body = await request.json();
    const item = await db.items.create(body);
    return Response.json(item, { status: 201 });
}

export async function DELETE(request: Request) {
    const url = new URL(request.url);
    const id = url.searchParams.get('id');
    await db.items.delete(id);
    return new Response(null, { status: 204 });
}
'''
        result = parser.parse(code, "app/api/items+api.ts")

        api_routes = result.api_routes
        assert len(api_routes) >= 1
        methods = api_routes[0].http_methods
        assert 'GET' in methods
        assert 'POST' in methods
        assert 'DELETE' in methods

    def test_expo_config_plugin_parse(self, parser):
        """Test parsing a config plugin file."""
        code = '''
import { withAndroidManifest, withInfoPlist, withDangerousMod } from '@expo/config-plugins';

const withCustomConfig = (config) => {
    config = withAndroidManifest(config, (config) => {
        return config;
    });

    config = withInfoPlist(config, (config) => {
        config.modResults.NSLocationAlwaysUsageDescription = 'Required for background location';
        return config;
    });

    return config;
};

module.exports = withCustomConfig;
'''
        result = parser.parse(code, "plugins/with-custom.js")

        assert 'expo-config-plugins' in result.detected_frameworks
        assert result.has_custom_plugins
        assert len(result.config_plugins) >= 2

        android_mods = [p for p in result.config_plugins if p.modifies_android]
        ios_mods = [p for p in result.config_plugins if p.modifies_ios]
        assert len(android_mods) >= 1
        assert len(ios_mods) >= 1

    def test_expo_notifications_full_setup(self, parser):
        """Test parsing notification setup with permissions."""
        code = '''
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';

Notifications.setNotificationHandler({
    handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
    }),
});

async function registerForPushNotificationsAsync() {
    if (!Device.isDevice) {
        alert('Physical device required for push notifications');
        return;
    }

    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;
    if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
    }

    const token = await Notifications.getExpoPushTokenAsync({
        projectId: Constants.expoConfig?.extra?.eas?.projectId,
    });
    return token.data;
}

async function schedulePushNotification() {
    await Notifications.scheduleNotificationAsync({
        content: { title: "Reminder", body: "Don't forget!" },
        trigger: { seconds: 60 },
    });
}
'''
        result = parser.parse(code, "services/notifications.ts")

        assert 'expo-notifications' in result.detected_frameworks
        assert 'expo-device' in result.detected_frameworks
        assert 'expo-constants' in result.detected_frameworks

        # Modules
        module_names = [m.module for m in result.modules]
        assert 'expo-notifications' in module_names
        assert 'expo-device' in module_names
        assert 'expo-constants' in module_names

        # Permissions
        assert len(result.permissions) >= 1
        notif_perms = [p for p in result.permissions if p.permission_type == 'notifications']
        assert len(notif_perms) >= 1

    def test_parse_result_dataclass_defaults(self, parser):
        result = parser.parse("", "empty.tsx")
        assert isinstance(result, ExpoParseResult)
        assert result.file_path == "empty.tsx"
        assert result.detected_frameworks == []
        assert result.modules == []
        assert result.permissions == []
        assert result.routes == []
        assert result.layouts == []
        assert result.config_plugins == []
        assert result.sdk_version == 0

    def test_file_type_detection(self, parser):
        assert parser.parse("", "file.tsx").file_type == "tsx"
        assert parser.parse("", "file.jsx").file_type == "jsx"
        assert parser.parse("", "file.ts").file_type == "ts"
        assert parser.parse("", "file.json").file_type == "json"
        assert parser.parse("", "file.js").file_type == "js"

    def test_app_json_full_parse(self, parser):
        """Test that parsing app.json populates config correctly."""
        content = '''{
  "expo": {
    "name": "FullApp",
    "slug": "full-app",
    "sdkVersion": "51.0.0",
    "version": "2.0.0",
    "platforms": ["ios", "android"],
    "scheme": "fullapp",
    "splash": { "image": "./splash.png" },
    "icon": "./icon.png",
    "plugins": ["expo-camera", "expo-router"]
  }
}'''
        result = parser.parse(content, "app.json")
        assert result.config.name == "FullApp"
        assert result.config.slug == "full-app"
        assert result.config.sdk_version == "51.0.0"
        assert result.sdk_version == 51
        assert result.config.scheme == "fullapp"
        assert result.config.has_splash
        assert result.config.has_icon
        assert 'expo-camera' in result.config.plugins


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_file(self, parser):
        result = parser.parse("", "empty.tsx")
        assert isinstance(result, ExpoParseResult)
        assert result.detected_frameworks == []
        assert result.modules == []

    def test_non_expo_react_native_file(self, parser):
        code = '''
import { View, Text } from 'react-native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
export function App() { return <View><Text>RN Only</Text></View>; }
'''
        assert not parser.is_expo_file(code, "App.tsx")

    def test_plain_web_react_file(self, parser):
        code = '''
import React from 'react';
export function WebApp() { return <div>Hello Web</div>; }
'''
        assert not parser.is_expo_file(code, "App.tsx")

    def test_malformed_json_config(self, parser):
        content = '{ this is not valid json }'
        result = parser.parse(content, "app.json")
        assert isinstance(result, ExpoParseResult)

    def test_file_with_syntax_errors(self, parser):
        code = '''
import { Camera from 'expo-camera
const x = {
'''
        result = parser.parse(code, "broken.tsx")
        assert isinstance(result, ExpoParseResult)

    def test_multiple_framework_detections(self, parser):
        code = '''
import { CameraView } from 'expo-camera';
import { Audio } from 'expo-av';
import * as Location from 'expo-location';
import * as FileSystem from 'expo-file-system';
import * as SecureStore from 'expo-secure-store';
import * as Notifications from 'expo-notifications';
import { useAuthRequest } from 'expo-auth-session';
import { BlurView } from 'expo-blur';
import * as Haptics from 'expo-haptics';
import * as Device from 'expo-device';
import * as Sharing from 'expo-sharing';
'''
        result = parser.parse(code, "all.tsx")
        assert len(result.detected_frameworks) >= 10
        assert 'expo-camera' in result.detected_frameworks
        assert 'expo-location' in result.detected_frameworks
        assert 'expo-notifications' in result.detected_frameworks
        assert 'expo-auth-session' in result.detected_frameworks

    def test_require_style_imports(self, parser):
        code = '''
const Camera = require('expo-camera');
const Location = require('expo-location');
'''
        result = parser.parse(code, "legacy.js")
        module_names = [m.module for m in result.modules]
        assert 'expo-camera' in module_names
        assert 'expo-location' in module_names

    def test_expo_in_subdirectory(self, parser):
        code = '''
import { useRouter } from 'expo-router';
export default function Screen() { return null; }
'''
        assert parser.is_expo_file(code, "src/app/home.tsx")

    def test_config_sdk_version_overrides_code_detection(self, parser):
        """Config SDK version should be used if higher than code detection."""
        content = '''{
  "expo": {
    "name": "App",
    "slug": "app",
    "sdkVersion": "52.0.0"
  }
}'''
        result = parser.parse(content, "app.json")
        assert result.sdk_version == 52

    def test_mixed_expo_and_rn_file(self, parser):
        code = '''
import { View, Text, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import * as SecureStore from 'expo-secure-store';

export default function ProfileScreen() {
    const router = useRouter();
    const token = SecureStore.getItemAsync('auth_token');
    return <View><Text>Profile</Text></View>;
}
'''
        result = parser.parse(code, "app/profile.tsx")
        assert parser.is_expo_file(code, "app/profile.tsx")
        assert 'expo-router' in result.detected_frameworks
        assert 'expo-secure-store' in result.detected_frameworks
        module_names = [m.module for m in result.modules]
        assert 'expo-secure-store' in module_names


# ═══════════════════════════════════════════════════════════════════
# SDK Version & Historical Support Tests
# ═══════════════════════════════════════════════════════════════════

class TestSDKVersionSupport:
    """Tests for SDK version detection across SDK 44-52."""

    def test_sdk_44_dev_client(self, parser):
        code = "import 'expo-dev-client';"
        result = parser.parse(code, "index.ts")
        assert result.sdk_version == 44

    def test_sdk_45_modules_api(self, parser):
        code = "import { requireNativeModule } from 'expo-modules-core';"
        result = parser.parse(code, "native.ts")
        assert result.sdk_version == 45

    def test_sdk_46_eas_update(self, parser):
        code = "Updates.checkForUpdateAsync();"
        result = parser.parse(code, "updates.ts")
        assert result.sdk_version == 46

    def test_sdk_47_expo_router(self, parser):
        code = "import { Stack } from 'expo-router';"
        result = parser.parse(code, "layout.tsx")
        assert result.sdk_version >= 47

    def test_sdk_49_expo_image(self, parser):
        code = "import { Image, ImageContentFit } from 'expo-image';"
        result = parser.parse(code, "image.tsx")
        assert result.sdk_version >= 49

    def test_sdk_50_typed_routes(self, parser):
        code = '''
import { Href } from 'expo-router';
import type { Href as TypedHref } from 'expo-router';
'''
        result = parser.parse(code, "nav.tsx")
        assert result.sdk_version >= 50

    def test_sdk_51_new_apis(self, parser):
        code = "import { useVideoPlayer, VideoView } from 'expo-video';"
        result = parser.parse(code, "video.tsx")
        assert result.sdk_version >= 51

    def test_sdk_52_react_19(self, parser):
        code = "const status = useFormStatus();"
        result = parser.parse(code, "form.tsx")
        assert result.sdk_version >= 52
