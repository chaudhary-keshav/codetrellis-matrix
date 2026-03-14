"""
Tests for React Native extractors and EnhancedReactNativeParser.

Part of CodeTrellis v5.6 React Native Language Support.
Tests cover:
- Component extraction (core RN, animated, lists)
- Navigation extraction (React Navigation, Expo Router, deep links)
- Native module extraction (NativeModules, TurboModules, Fabric)
- Styling extraction (StyleSheet, NativeWind, themes)
- Platform extraction (Platform.OS, permissions, lifecycle)
- React Native parser integration (framework detection, version detection)
"""

import pytest
from codetrellis.react_native_parser_enhanced import (
    EnhancedReactNativeParser,
    ReactNativeParseResult,
)
from codetrellis.extractors.react_native import (
    ReactNativeComponentExtractor,
    ReactNativeNavigationExtractor,
    ReactNativeNativeModuleExtractor,
    ReactNativeStylingExtractor,
    ReactNativePlatformExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedReactNativeParser()


@pytest.fixture
def component_extractor():
    return ReactNativeComponentExtractor()


@pytest.fixture
def navigation_extractor():
    return ReactNativeNavigationExtractor()


@pytest.fixture
def native_module_extractor():
    return ReactNativeNativeModuleExtractor()


@pytest.fixture
def styling_extractor():
    return ReactNativeStylingExtractor()


@pytest.fixture
def platform_extractor():
    return ReactNativePlatformExtractor()


# ═══════════════════════════════════════════════════════════════════
# Component Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestRNComponentExtractor:
    """Tests for ReactNativeComponentExtractor."""

    def test_core_rn_component_imports(self, component_extractor):
        code = '''
import { View, Text, ScrollView, Image, TouchableOpacity } from 'react-native';

export function HomeScreen() {
    return (
        <ScrollView>
            <View>
                <Text>Hello World</Text>
                <Image source={{ uri: 'https://example.com/img.png' }} />
                <TouchableOpacity onPress={() => {}}>
                    <Text>Press me</Text>
                </TouchableOpacity>
            </View>
        </ScrollView>
    );
}
'''
        result = component_extractor.extract(code, "HomeScreen.tsx")
        components = result.get('components', [])
        names = [c.name for c in components]
        assert 'View' in names
        assert 'Text' in names
        assert 'ScrollView' in names
        assert 'Image' in names
        assert 'TouchableOpacity' in names

    def test_flatlist_component(self, component_extractor):
        code = '''
import { FlatList, View, Text } from 'react-native';

export function UserList({ users }) {
    return (
        <FlatList
            data={users}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => <Text>{item.name}</Text>}
            onEndReached={loadMore}
            onEndReachedThreshold={0.5}
            onRefresh={onRefresh}
            refreshing={isRefreshing}
        />
    );
}
'''
        result = component_extractor.extract(code, "UserList.tsx")
        lists = result.get('list_components', [])
        assert len(lists) >= 1
        fl = lists[0]
        assert fl.list_type == "FlatList"
        assert fl.has_key_extractor
        assert fl.has_render_item
        assert fl.has_pagination
        assert fl.has_pull_to_refresh

    def test_animated_api(self, component_extractor):
        code = '''
import { Animated, View } from 'react-native';

export function FadeIn({ children }) {
    const fadeAnim = useRef(new Animated.Value(0)).current;

    useEffect(() => {
        Animated.timing(fadeAnim, {
            toValue: 1,
            duration: 500,
            useNativeDriver: true,
        }).start();
    }, []);

    return <Animated.View style={{ opacity: fadeAnim }}>{children}</Animated.View>;
}
'''
        result = component_extractor.extract(code, "FadeIn.tsx")
        animated = result.get('animated_components', [])
        assert len(animated) >= 1
        anim = animated[0]
        assert anim.animation_type == "animated_api"
        assert anim.uses_native_driver

    def test_reanimated_v3(self, component_extractor):
        code = '''
import { useSharedValue, useAnimatedStyle, withTiming } from 'react-native-reanimated';
import { GestureDetector, Gesture } from 'react-native-gesture-handler';

export function DraggableCard() {
    const offset = useSharedValue(0);
    const animatedStyle = useAnimatedStyle(() => ({
        transform: [{ translateY: offset.value }],
    }));
    return <Animated.View style={animatedStyle} />;
}
'''
        result = component_extractor.extract(code, "DraggableCard.tsx")
        animated = result.get('animated_components', [])
        reanimated = [a for a in animated if a.animation_type == "reanimated"]
        assert len(reanimated) >= 1
        assert reanimated[0].is_gesture_based

    def test_require_native_component(self, component_extractor):
        code = '''
import { requireNativeComponent } from 'react-native';

const RCTMyNativeView = requireNativeComponent<MyNativeViewProps>('RCTMyNativeView');

export default RCTMyNativeView;
'''
        result = component_extractor.extract(code, "MyNativeView.tsx")
        components = result.get('components', [])
        native = [c for c in components if c.wraps_native]
        assert len(native) >= 1
        assert native[0].name == 'RCTMyNativeView'

    def test_flashlist(self, component_extractor):
        code = '''
import { FlashList } from '@shopify/flash-list';

export function FastList({ data }) {
    return (
        <FlashList
            data={data}
            renderItem={({ item }) => <Text>{item.title}</Text>}
            estimatedItemSize={100}
        />
    );
}
'''
        result = component_extractor.extract(code, "FastList.tsx")
        lists = result.get('list_components', [])
        flash = [l for l in lists if l.list_type == "FlashList"]
        assert len(flash) >= 1
        assert flash[0].has_render_item
        assert flash[0].estimated_item_size

    def test_third_party_components(self, component_extractor):
        code = '''
import { SafeAreaView, SafeAreaProvider } from 'react-native-safe-area-context';
import MapView, { Marker } from 'react-native-maps';

export function MapScreen() {
    return (
        <SafeAreaView>
            <MapView>
                <Marker coordinate={{ latitude: 37.78, longitude: -122.43 }} />
            </MapView>
        </SafeAreaView>
    );
}
'''
        result = component_extractor.extract(code, "MapScreen.tsx")
        components = result.get('components', [])
        names = [c.name for c in components]
        assert 'SafeAreaView' in names
        assert 'MapView' in names


# ═══════════════════════════════════════════════════════════════════
# Navigation Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestRNNavigationExtractor:
    """Tests for ReactNativeNavigationExtractor."""

    def test_stack_navigator(self, navigation_extractor):
        code = '''
import { createNativeStackNavigator } from '@react-navigation/native-stack';

const Stack = createNativeStackNavigator();

function AppNavigator() {
    return (
        <Stack.Navigator screenOptions={{ headerShown: false }}>
            <Stack.Screen name="Home" component={HomeScreen} />
            <Stack.Screen name="Profile" component={ProfileScreen} />
            <Stack.Screen name="Settings" component={SettingsScreen} />
        </Stack.Navigator>
    );
}
'''
        result = navigation_extractor.extract(code, "AppNavigator.tsx")
        navigators = result.get('navigators', [])
        assert len(navigators) >= 1
        nav = navigators[0]
        assert nav.navigator_type == "native_stack"
        assert 'Home' in nav.screens
        assert 'Profile' in nav.screens

        screens = result.get('screens', [])
        assert len(screens) >= 3

    def test_bottom_tab_navigator(self, navigation_extractor):
        code = '''
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

const Tab = createBottomTabNavigator();

function MainTabs() {
    return (
        <Tab.Navigator tabBarOptions={{ activeTintColor: 'blue' }}>
            <Tab.Screen name="Feed" component={FeedScreen} />
            <Tab.Screen name="Search" component={SearchScreen} />
            <Tab.Screen name="Messages" component={MessagesScreen} />
        </Tab.Navigator>
    );
}
'''
        result = navigation_extractor.extract(code, "MainTabs.tsx")
        navigators = result.get('navigators', [])
        assert len(navigators) >= 1
        assert navigators[0].navigator_type == "bottom_tab"

    def test_deep_linking(self, navigation_extractor):
        code = '''
const linking = {
    prefixes: ['myapp://', 'https://myapp.com'],
    config: {
        screens: {
            Home: {
                path: 'home',
            },
            Profile: {
                path: 'user/:userId',
            },
            Settings: {
                path: 'settings',
            },
        },
    },
};
'''
        result = navigation_extractor.extract(code, "linking.ts")
        deep_links = result.get('deep_links', [])
        assert len(deep_links) >= 1
        paths = [dl.path_pattern for dl in deep_links]
        assert any(':userId' in p for p in paths)

    def test_expo_router(self, navigation_extractor):
        code = '''
import { Stack, useRouter, useLocalSearchParams } from 'expo-router';

export default function Layout() {
    return (
        <Stack>
            <Stack.Screen name="index" options={{ title: 'Home' }} />
            <Stack.Screen name="[id]" options={{ title: 'Details' }} />
        </Stack>
    );
}
'''
        result = navigation_extractor.extract(code, "app/_layout.tsx")
        navigators = result.get('navigators', [])
        assert len(navigators) >= 1
        assert navigators[0].library == "expo-router"


# ═══════════════════════════════════════════════════════════════════
# Native Module Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestRNNativeModuleExtractor:
    """Tests for ReactNativeNativeModuleExtractor."""

    def test_native_modules_access(self, native_module_extractor):
        code = '''
import { NativeModules } from 'react-native';

const { CalendarModule } = NativeModules;

function createEvent(title, date) {
    NativeModules.CalendarModule.createCalendarEvent(title, date);
}
'''
        result = native_module_extractor.extract(code, "calendar.ts")
        modules = result.get('native_modules', [])
        names = [m.name for m in modules]
        assert 'CalendarModule' in names
        calendar = next(m for m in modules if m.name == 'CalendarModule')
        assert calendar.architecture == "bridge"

    def test_turbo_module_spec(self, native_module_extractor):
        code = '''
import type { TurboModule } from 'react-native';
import { TurboModuleRegistry } from 'react-native';

export interface NativeCalculatorSpec extends TurboModule {
    add(a: number, b: number): number;
    multiply(a: number, b: number): Promise<number>;
    getConstants(): { PI: number };
}

export default TurboModuleRegistry.getEnforcing<NativeCalculatorSpec>('NativeCalculator');
'''
        result = native_module_extractor.extract(code, "NativeCalculator.ts")
        turbo = result.get('turbo_modules', [])
        assert len(turbo) >= 1
        assert turbo[0].spec_name == "NativeCalculatorSpec"
        assert 'add' in turbo[0].methods or 'multiply' in turbo[0].methods

    def test_fabric_component(self, native_module_extractor):
        code = '''
import codegenNativeComponent from 'react-native/Libraries/Utilities/codegenNativeComponent';
import type { ViewProps } from 'react-native';
import type { BubblingEventHandler } from 'react-native/Libraries/Types/CodegenTypes';

interface NativeProps extends ViewProps {
    color?: string;
    onColorChanged?: BubblingEventHandler<{ color: string }>;
}

export default codegenNativeComponent<NativeProps>('RCTColorView');
'''
        result = native_module_extractor.extract(code, "RCTColorView.ts")
        fabric = result.get('fabric_components', [])
        assert len(fabric) >= 1
        assert fabric[0].component_name == "RCTColorView"
        assert fabric[0].props_type == "NativeProps"

    def test_native_event_emitter(self, native_module_extractor):
        code = '''
import { NativeModules, NativeEventEmitter } from 'react-native';

const eventEmitter = new NativeEventEmitter(NativeModules.LocationModule);

eventEmitter.addListener('LocationUpdate', (event) => {
    console.log(event.latitude, event.longitude);
});
'''
        result = native_module_extractor.extract(code, "location.ts")
        modules = result.get('native_modules', [])
        emitters = [m for m in modules if m.is_event_emitter]
        assert len(emitters) >= 1

    def test_jsi_bindings(self, native_module_extractor):
        code = '''
// JSI binding
const jsiModule = global.__myJSIModule;
jsiModule.calculate(42);
'''
        result = native_module_extractor.extract(code, "jsi.ts")
        modules = result.get('native_modules', [])
        jsi = [m for m in modules if m.architecture == "jsi"]
        assert len(jsi) >= 1


# ═══════════════════════════════════════════════════════════════════
# Styling Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestRNStylingExtractor:
    """Tests for ReactNativeStylingExtractor."""

    def test_stylesheet_create(self, styling_extractor):
        code = '''
import { StyleSheet } from 'react-native';

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#fff',
    },
    title: {
        fontSize: 24,
        fontWeight: 'bold',
    },
    button: {
        padding: 16,
        borderRadius: 8,
    },
});
'''
        result = styling_extractor.extract(code, "styles.ts")
        sheets = result.get('stylesheets', [])
        assert len(sheets) >= 1
        assert sheets[0].name == "styles"
        assert sheets[0].style_count >= 2

    def test_nativewind_detection(self, styling_extractor):
        code = '''
import { styled } from 'nativewind';
import { View, Text } from 'react-native';

export function Card() {
    return (
        <View className="bg-white rounded-lg p-4 shadow-md dark:bg-gray-800">
            <Text className="text-lg font-bold">Title</Text>
        </View>
    );
}
'''
        result = styling_extractor.extract(code, "Card.tsx")
        themes = result.get('themes', [])
        nw = [t for t in themes if t.theme_library == "nativewind"]
        assert len(nw) >= 1
        assert nw[0].has_dark_mode

    def test_platform_select_style(self, styling_extractor):
        code = '''
import { Platform, StyleSheet } from 'react-native';

const styles = StyleSheet.create({
    shadow: Platform.select({
        ios: {
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 2 },
            shadowOpacity: 0.25,
        },
        android: {
            elevation: 5,
        },
    }),
});
'''
        result = styling_extractor.extract(code, "shadows.ts")
        dynamic = result.get('dynamic_styles', [])
        platform = [d for d in dynamic if d.style_type == "platform_select"]
        assert len(platform) >= 1

    def test_rn_paper_theme(self, styling_extractor):
        code = '''
import { PaperProvider, MD3DarkTheme, MD3LightTheme } from 'react-native-paper';

const theme = {
    ...MD3LightTheme,
    colors: {
        ...MD3LightTheme.colors,
        primary: '#6200ee',
    },
};

export function App() {
    return <PaperProvider theme={theme}><MainApp /></PaperProvider>;
}
'''
        result = styling_extractor.extract(code, "App.tsx")
        themes = result.get('themes', [])
        paper = [t for t in themes if t.theme_library == "react-native-paper"]
        assert len(paper) >= 1
        assert paper[0].has_dark_mode
        assert paper[0].has_provider

    def test_styled_components_native(self, styling_extractor):
        code = '''
import styled from 'styled-components/native';

const Container = styled.View`
    flex: 1;
    background-color: ${({ theme }) => theme.colors.background};
`;

const Title = styled.Text`
    font-size: 24px;
    color: ${({ theme }) => theme.colors.text};
`;
'''
        result = styling_extractor.extract(code, "styled.tsx")
        themes = result.get('themes', [])
        sc = [t for t in themes if t.theme_library == "styled-components"]
        assert len(sc) >= 1


# ═══════════════════════════════════════════════════════════════════
# Platform Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestRNPlatformExtractor:
    """Tests for ReactNativePlatformExtractor."""

    def test_platform_os_check(self, platform_extractor):
        code = '''
import { Platform } from 'react-native';

if (Platform.OS === 'ios') {
    // iOS specific code
}

if (Platform.OS === 'android') {
    // Android specific code
}
'''
        result = platform_extractor.extract(code, "utils.ts")
        usages = result.get('platform_usages', [])
        os_checks = [u for u in usages if u.usage_type == "os_check"]
        assert len(os_checks) >= 2
        platforms = []
        for u in os_checks:
            platforms.extend(u.platforms)
        assert 'ios' in platforms
        assert 'android' in platforms

    def test_platform_select(self, platform_extractor):
        code = '''
import { Platform } from 'react-native';

const headerHeight = Platform.select({
    ios: 44,
    android: 56,
    default: 50,
});
'''
        result = platform_extractor.extract(code, "constants.ts")
        usages = result.get('platform_usages', [])
        selects = [u for u in usages if u.usage_type == "select"]
        assert len(selects) >= 1
        assert 'ios' in selects[0].platforms
        assert 'android' in selects[0].platforms

    def test_platform_specific_file(self, platform_extractor):
        code = '''
// iOS-specific implementation
export function showAlert(message) {
    Alert.alert('Info', message);
}
'''
        result = platform_extractor.extract(code, "alert.ios.ts")
        files = result.get('platform_files', [])
        assert len(files) >= 1
        assert files[0].platform == "ios"

    def test_permissions_android(self, platform_extractor):
        code = '''
import { PermissionsAndroid } from 'react-native';

async function requestCameraPermission() {
    const granted = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.CAMERA,
    );
    return granted === PermissionsAndroid.RESULTS.GRANTED;
}
'''
        result = platform_extractor.extract(code, "permissions.ts")
        perms = result.get('permissions', [])
        assert len(perms) >= 1
        assert perms[0].permission_type == "camera"
        assert perms[0].library == "PermissionsAndroid"

    def test_expo_permissions(self, platform_extractor):
        code = '''
import * as Location from 'expo-location';

async function getLocation() {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status === 'granted') {
        return await Location.getCurrentPositionAsync({});
    }
}
'''
        result = platform_extractor.extract(code, "location.ts")
        perms = result.get('permissions', [])
        assert len(perms) >= 1
        assert perms[0].library == "expo-location"

    def test_back_handler(self, platform_extractor):
        code = '''
import { BackHandler } from 'react-native';

useEffect(() => {
    const subscription = BackHandler.addEventListener('hardwareBackPress', () => {
        navigation.goBack();
        return true;
    });
    return () => subscription.remove();
}, []);
'''
        result = platform_extractor.extract(code, "screen.tsx")
        usages = result.get('platform_usages', [])
        back = [u for u in usages if u.name == "BackHandler"]
        assert len(back) >= 1
        assert 'android' in back[0].platforms

    def test_app_state_lifecycle(self, platform_extractor):
        code = '''
import { AppState } from 'react-native';

useEffect(() => {
    const subscription = AppState.addEventListener('change', (nextAppState) => {
        if (nextAppState === 'active') {
            refreshData();
        }
    });
    return () => subscription.remove();
}, []);
'''
        result = platform_extractor.extract(code, "lifecycle.ts")
        usages = result.get('platform_usages', [])
        lifecycle = [u for u in usages if u.name == "AppState"]
        assert len(lifecycle) >= 1

    def test_linking_api(self, platform_extractor):
        code = '''
import { Linking } from 'react-native';

async function openURL(url) {
    const supported = await Linking.canOpenURL(url);
    if (supported) {
        await Linking.openURL(url);
    }
}
'''
        result = platform_extractor.extract(code, "linking.ts")
        usages = result.get('platform_usages', [])
        link = [u for u in usages if u.name == "Linking"]
        assert len(link) >= 1


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedReactNativeParser:
    """Tests for the integrated EnhancedReactNativeParser."""

    def test_is_react_native_file_positive(self, parser):
        code = '''
import { View, Text, StyleSheet } from 'react-native';
'''
        assert parser.is_react_native_file(code, "App.tsx")

    def test_is_react_native_file_rn_library(self, parser):
        code = '''
import { useNavigation } from '@react-navigation/native';
'''
        assert parser.is_react_native_file(code, "screen.tsx")

    def test_is_react_native_file_expo(self, parser):
        code = '''
import * as Location from 'expo-location';
'''
        assert parser.is_react_native_file(code, "locations.ts")

    def test_is_react_native_file_platform_ext(self, parser):
        code = '''
export function nativeImpl() {}
'''
        assert parser.is_react_native_file(code, "service.ios.ts")
        assert parser.is_react_native_file(code, "service.android.js")
        assert parser.is_react_native_file(code, "service.native.tsx")

    def test_is_react_native_file_negative(self, parser):
        code = '''
import React from 'react';
export function WebComponent() { return <div>Hello</div>; }
'''
        assert not parser.is_react_native_file(code, "component.tsx")

    def test_framework_detection(self, parser):
        code = '''
import { View, Text } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import Animated, { useSharedValue, useAnimatedStyle, withSpring } from 'react-native-reanimated';
import { GestureDetector, Gesture } from 'react-native-gesture-handler';
import AsyncStorage from '@react-native-async-storage/async-storage';
'''
        result = parser.parse(code, "App.tsx")
        assert 'react-native' in result.detected_frameworks
        assert 'react-navigation' in result.detected_frameworks
        assert 'reanimated' in result.detected_frameworks
        assert 'gesture-handler' in result.detected_frameworks
        assert 'async-storage' in result.detected_frameworks

    def test_rn_version_detection_new_arch(self, parser):
        code = '''
import { TurboModuleRegistry } from 'react-native';
export default TurboModuleRegistry.getEnforcing('MyModule');
'''
        result = parser.parse(code, "module.ts")
        assert result.rn_version == "0.68"

    def test_rn_version_detection_pressable(self, parser):
        code = '''
import { Pressable, View } from 'react-native';
export function Btn() { return <Pressable><View /></Pressable>; }
'''
        result = parser.parse(code, "btn.tsx")
        assert result.rn_version == "0.63"

    def test_architecture_detection_bridge(self, parser):
        code = '''
import { NativeModules } from 'react-native';
const { MyModule } = NativeModules;
MyModule.doSomething();
'''
        result = parser.parse(code, "bridge.ts")
        assert result.architecture == "bridge"

    def test_architecture_detection_new(self, parser):
        code = '''
import { TurboModuleRegistry } from 'react-native';
export default TurboModuleRegistry.getEnforcing('Calculator');
'''
        result = parser.parse(code, "turbo.ts")
        assert result.architecture == "new_architecture"

    def test_full_rn_screen_parse(self, parser):
        """Test parsing a realistic React Native screen file."""
        code = '''
import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, StyleSheet, Platform, ActivityIndicator } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function ProductListScreen() {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigation = useNavigation();

    useEffect(() => {
        fetchProducts();
    }, []);

    const fetchProducts = async () => {
        const cached = await AsyncStorage.getItem('products');
        if (cached) {
            setProducts(JSON.parse(cached));
        }
        setLoading(false);
    };

    if (loading) return <ActivityIndicator size="large" />;

    return (
        <SafeAreaView style={styles.container}>
            <FlatList
                data={products}
                keyExtractor={(item) => item.id}
                renderItem={({ item }) => (
                    <Pressable onPress={() => navigation.navigate('ProductDetail', { id: item.id })}>
                        <View style={styles.item}>
                            <Text style={styles.title}>{item.name}</Text>
                            <Text style={styles.price}>${item.price}</Text>
                        </View>
                    </Pressable>
                )}
                onEndReached={loadMore}
                onEndReachedThreshold={0.3}
            />
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: Platform.select({ ios: '#f5f5f5', android: '#fff' }),
    },
    item: {
        padding: 16,
        borderBottomWidth: StyleSheet.hairlineWidth,
    },
    title: {
        fontSize: 18,
        fontWeight: 'bold',
    },
    price: {
        fontSize: 16,
        color: '#888',
    },
});
'''
        result = parser.parse(code, "ProductListScreen.tsx")

        # Should detect RN framework
        assert 'react-native' in result.detected_frameworks
        assert 'react-navigation' in result.detected_frameworks
        assert 'safe-area-context' in result.detected_frameworks
        assert 'async-storage' in result.detected_frameworks

        # Should extract components
        assert len(result.components) > 0

        # Should extract FlatList
        assert len(result.list_components) > 0
        fl = result.list_components[0]
        assert fl.has_key_extractor
        assert fl.has_render_item

        # Should extract StyleSheet
        assert len(result.stylesheets) > 0
        assert result.stylesheets[0].name == "styles"

        # Should detect Platform.select
        assert len(result.platform_usages) > 0

    def test_expo_project_parse(self, parser):
        """Test parsing an Expo project file."""
        code = '''
import { Stack, useRouter } from 'expo-router';
import * as Notifications from 'expo-notifications';
import * as Location from 'expo-location';

Notifications.setNotificationHandler({
    handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: false,
        shouldSetBadge: false,
    }),
});

export default function Layout() {
    const router = useRouter();
    return (
        <Stack>
            <Stack.Screen name="index" />
            <Stack.Screen name="settings" />
        </Stack>
    );
}
'''
        result = parser.parse(code, "app/_layout.tsx")
        assert 'expo-router' in result.detected_frameworks
        assert 'expo-notifications' in result.detected_frameworks
        assert 'expo' in result.detected_frameworks
        assert len(result.navigators) > 0

    def test_new_architecture_file(self, parser):
        """Test parsing a New Architecture (TurboModule + Fabric) file."""
        code = '''
import type { TurboModule } from 'react-native';
import { TurboModuleRegistry } from 'react-native';
import codegenNativeComponent from 'react-native/Libraries/Utilities/codegenNativeComponent';

export interface NativePaymentSpec extends TurboModule {
    processPayment(amount: number, currency: string): Promise<string>;
    getTransactionHistory(): Promise<Array<{ id: string; amount: number }>>;
}

interface NativePaymentViewProps extends ViewProps {
    amount: number;
    onPaymentComplete?: BubblingEventHandler<{ transactionId: string }>;
}

export const PaymentModule = TurboModuleRegistry.getEnforcing<NativePaymentSpec>('NativePayment');
export default codegenNativeComponent<NativePaymentViewProps>('RCTPaymentView');
'''
        result = parser.parse(code, "NativePayment.ts")
        assert result.architecture == "new_architecture"
        assert len(result.turbo_modules) > 0
        assert len(result.fabric_components) > 0
        assert result.rn_version == "0.68"


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_file(self, parser):
        result = parser.parse("", "empty.tsx")
        assert isinstance(result, ReactNativeParseResult)
        assert result.components == []
        assert result.navigators == []

    def test_non_rn_react_file(self, parser):
        code = '''
import React from 'react';
export function WebApp() { return <div>Hello Web</div>; }
'''
        assert not parser.is_react_native_file(code, "App.tsx")

    def test_file_with_syntax_errors(self, parser):
        code = '''
import { View from 'react-native
const x = {
'''
        # Should not raise - gracefully handle
        result = parser.parse(code, "broken.tsx")
        assert isinstance(result, ReactNativeParseResult)

    def test_mixed_web_and_native(self, parser):
        code = '''
import { Platform } from 'react-native';
import { View, Text } from 'react-native';

const Component = Platform.select({
    web: () => require('./Component.web'),
    default: () => require('./Component.native'),
});
'''
        result = parser.parse(code, "Component.tsx")
        assert 'react-native' in result.detected_frameworks
        selects = [u for u in result.platform_usages if u.usage_type == "select"]
        assert len(selects) > 0
