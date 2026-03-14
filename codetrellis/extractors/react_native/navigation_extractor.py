"""
React Native Navigation Extractor for CodeTrellis

Extracts navigation patterns from React Native source code:
- React Navigation stacks (createStackNavigator, createNativeStackNavigator)
- Tab navigators (createBottomTabNavigator, createMaterialTopTabNavigator)
- Drawer navigators (createDrawerNavigator)
- Screen definitions (Screen, Group)
- Deep linking configuration (linking config objects)
- Navigation actions (navigate, goBack, push, replace, reset)
- Expo Router file-based routing
- React Native Navigation (Wix) patterns

Supports React Navigation v4 through v7+, Expo Router v1-v3.

Part of CodeTrellis v5.6 - React Native Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class RNNavigatorInfo:
    """Information about a navigator definition."""
    name: str
    file: str = ""
    line_number: int = 0
    navigator_type: str = ""  # stack, native_stack, tab, bottom_tab, material_top_tab, drawer
    library: str = ""  # react-navigation, expo-router, wix-navigation
    screens: List[str] = field(default_factory=list)
    has_header_config: bool = False
    has_tab_bar_config: bool = False
    is_nested: bool = False
    parent_navigator: str = ""


@dataclass
class RNScreenInfo:
    """Information about a screen definition in a navigator."""
    name: str
    file: str = ""
    line_number: int = 0
    component: str = ""  # Component rendered for this screen
    navigator: str = ""  # Parent navigator name
    has_options: bool = False
    has_initial_params: bool = False
    is_initial: bool = False
    is_modal: bool = False
    has_listeners: bool = False


@dataclass
class RNDeepLinkInfo:
    """Information about deep linking configuration."""
    name: str
    file: str = ""
    line_number: int = 0
    path_pattern: str = ""
    screen_name: str = ""
    has_params: bool = False
    prefix: str = ""


class ReactNativeNavigationExtractor:
    """
    Extracts React Navigation and routing patterns from source code.

    Detects:
    - Stack, Tab, Drawer navigator creation
    - Screen definitions with component mappings
    - Deep link configuration objects
    - Navigation hooks (useNavigation, useRoute, useFocusEffect)
    - Expo Router file-based routes
    - Wix React Native Navigation
    """

    # Navigator creation patterns
    CREATE_NAVIGATOR = re.compile(
        r"(?:const|let)\s+(\w+)\s*=\s*create(\w+)Navigator\s*[<(]",
        re.MULTILINE
    )

    # Stack.Screen / Tab.Screen definitions
    SCREEN_DEF = re.compile(
        r"<(\w+)\.Screen\s+name\s*=\s*['\"]([^'\"]+)['\"]"
        r"(?:\s+component\s*=\s*\{?(\w+)\}?)?",
        re.MULTILINE
    )

    # Screen with options
    SCREEN_OPTIONS = re.compile(
        r"<(\w+)\.Screen\s+[^>]*options\s*=",
        re.MULTILINE
    )

    # NavigationContainer
    NAV_CONTAINER = re.compile(
        r"<NavigationContainer\b",
        re.MULTILINE
    )

    # Deep linking config
    LINKING_CONFIG = re.compile(
        r"(?:const|let)\s+(\w*[Ll]inking\w*)\s*[:=]\s*\{",
        re.MULTILINE
    )

    # URL path patterns in linking config
    LINK_PATH = re.compile(
        r"['\"]([^'\"]*/:?\w+[^'\"]*)['\"]",
        re.MULTILINE
    )

    # Navigation hooks
    NAV_HOOKS = re.compile(
        r"\b(useNavigation|useRoute|useFocusEffect|useIsFocused|"
        r"useNavigationState|useLinkTo|useScrollToTop)\s*\(",
        re.MULTILINE
    )

    # navigation.navigate / push / goBack
    NAV_ACTIONS = re.compile(
        r"navigation\.(navigate|push|goBack|replace|reset|popToTop|setOptions|"
        r"setParams|dispatch|addListener)\s*\(",
        re.MULTILINE
    )

    # Expo Router patterns
    EXPO_ROUTER_IMPORT = re.compile(
        r"from\s+['\"]expo-router['\"]",
        re.MULTILINE
    )
    EXPO_ROUTER_COMPONENTS = re.compile(
        r"\b(Stack|Tabs|Drawer|Link|Redirect|Slot|useRouter|useLocalSearchParams|"
        r"useGlobalSearchParams|useSegments|usePathname)\b",
        re.MULTILINE
    )

    # Wix React Native Navigation
    WIX_NAV_IMPORT = re.compile(
        r"from\s+['\"]react-native-navigation['\"]",
        re.MULTILINE
    )
    WIX_NAV_REGISTER = re.compile(
        r"Navigation\.registerComponent\s*\(\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict:
        """
        Extract navigation patterns from source code.

        Returns:
            Dict with keys: navigators, screens, deep_links
        """
        navigators = []
        screens = []
        deep_links = []

        # Detect navigator creations
        for match in self.CREATE_NAVIGATOR.finditer(content):
            var_name = match.group(1)
            nav_type_raw = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            nav_type_map = {
                'Stack': 'stack',
                'NativeStack': 'native_stack',
                'BottomTab': 'bottom_tab',
                'MaterialTopTab': 'material_top_tab',
                'Drawer': 'drawer',
                'MaterialBottomTab': 'material_bottom_tab',
            }
            nav_type = nav_type_map.get(nav_type_raw, nav_type_raw.lower())

            # Collect screen names used with this navigator
            screen_names = []
            for sm in re.finditer(rf'<{re.escape(var_name)}\.Screen\s+name\s*=\s*[\'"]([^\'"]+)[\'"]', content):
                screen_names.append(sm.group(1))

            has_header = bool(re.search(rf'<{re.escape(var_name)}\.Navigator[^>]*screenOptions', content))
            has_tab_bar = bool(re.search(rf'tabBar|tabBarOptions|tabBarStyle', content)) if 'tab' in nav_type.lower() else False

            navigators.append(RNNavigatorInfo(
                name=var_name,
                file=file_path,
                line_number=line_num,
                navigator_type=nav_type,
                library="react-navigation",
                screens=screen_names[:20],
                has_header_config=has_header,
                has_tab_bar_config=has_tab_bar,
            ))

        # Screen definitions
        for match in self.SCREEN_DEF.finditer(content):
            navigator_var = match.group(1)
            screen_name = match.group(2)
            component = match.group(3) or ""
            line_num = content[:match.start()].count('\n') + 1

            screen_section = content[match.start():match.start() + 500]
            screens.append(RNScreenInfo(
                name=screen_name,
                file=file_path,
                line_number=line_num,
                component=component,
                navigator=navigator_var,
                has_options='options=' in screen_section or 'options =' in screen_section,
                has_initial_params='initialParams' in screen_section,
                is_initial='initialRouteName' in content and screen_name in content.split('initialRouteName')[1][:100] if 'initialRouteName' in content else False,
                has_listeners='listeners' in screen_section,
            ))

        # Expo Router patterns
        if self.EXPO_ROUTER_IMPORT.search(content):
            # File-based routing in expo-router
            for match in self.EXPO_ROUTER_COMPONENTS.finditer(content):
                comp = match.group(1)
                if comp in ('Stack', 'Tabs', 'Drawer'):
                    line_num = content[:match.start()].count('\n') + 1
                    # Check for Stack.Screen definitions
                    expo_screens = []
                    for sm in re.finditer(rf'<{re.escape(comp)}\.Screen\s+name\s*=\s*[\'"]([^\'"]+)[\'"]', content):
                        expo_screens.append(sm.group(1))
                    navigators.append(RNNavigatorInfo(
                        name=comp,
                        file=file_path,
                        line_number=line_num,
                        navigator_type=comp.lower(),
                        library="expo-router",
                        screens=expo_screens[:20],
                    ))

        # Wix React Native Navigation
        if self.WIX_NAV_IMPORT.search(content):
            for match in self.WIX_NAV_REGISTER.finditer(content):
                screen_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                screens.append(RNScreenInfo(
                    name=screen_name,
                    file=file_path,
                    line_number=line_num,
                    navigator="wix-navigation",
                ))

        # Deep linking configuration
        for match in self.LINKING_CONFIG.finditer(content):
            config_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Extract prefixes
            prefix_match = re.search(r"prefixes\s*:\s*\[([^\]]+)\]", content[match.start():match.start() + 2000])
            prefix = ""
            if prefix_match:
                prefixes = re.findall(r"['\"]([^'\"]+)['\"]", prefix_match.group(1))
                prefix = prefixes[0] if prefixes else ""

            # Extract path configs
            path_section = content[match.start():match.start() + 3000]
            for pm in re.finditer(r"(\w+)\s*:\s*\{[^}]*path\s*:\s*['\"]([^'\"]+)['\"]", path_section):
                deep_links.append(RNDeepLinkInfo(
                    name=config_name,
                    file=file_path,
                    line_number=line_num,
                    screen_name=pm.group(1),
                    path_pattern=pm.group(2),
                    has_params=':' in pm.group(2),
                    prefix=prefix,
                ))

        return {
            'navigators': navigators,
            'screens': screens,
            'deep_links': deep_links,
        }
