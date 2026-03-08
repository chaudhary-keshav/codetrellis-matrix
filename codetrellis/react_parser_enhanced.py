"""
EnhancedReactParser v1.0 - Comprehensive React parser using all extractors.

This parser integrates all React extractors to provide complete parsing of
React source files (.jsx, .tsx). It runs as a supplementary layer on top of
the JavaScript and TypeScript parsers, extracting React-specific semantics.

Supports:
- React 0.14+ (stateless functional components)
- React 15 (PropTypes, createClass legacy)
- React 16 (Error Boundaries, Portals, Fragments, Context API, lazy/Suspense)
- React 17 (JSX transform, no import React needed)
- React 18 (Concurrent features, useId, useSyncExternalStore, useInsertionEffect,
            startTransition, Suspense on server, Server Components)
- React 19 (use(), useFormStatus, useFormState, useOptimistic, useActionState,
            Actions, Server Functions, ref as prop, improved Suspense)

Component patterns:
- Functional components (arrow, function declaration, named export, default export)
- Class components (extends Component, extends PureComponent)
- Higher-Order Components (withRouter, connect, etc.)
- forwardRef, memo, lazy
- Error boundaries (componentDidCatch, getDerivedStateFromError)
- Server Components ('use server' / no 'use client')
- Client Components ('use client')
- Provider components

Hook patterns:
- All built-in hooks (useState through useActionState)
- Custom hooks (use* naming convention)
- Hook dependency analysis
- Hook rules compliance
- React version inference from hooks used

State management:
- Redux Toolkit (createSlice, configureStore, RTK Query)
- Zustand stores
- Jotai atoms
- Recoil atoms/selectors
- MobX observables
- Valtio proxies
- XState machines
- TanStack Query
- SWR

Context:
- createContext definitions
- Provider components
- useContext consumers
- Legacy contextType / Consumer patterns

Routing:
- React Router v5/v6 (Route, Routes, createBrowserRouter, Outlet)
- Next.js Pages Router (getServerSideProps, getStaticProps)
- Next.js App Router (app/ directory, page.tsx, layout.tsx, Server Components)
- TanStack Router
- Remix routing (loader, action, meta)

Framework detection (60+ React ecosystem patterns):
- Core: React, ReactDOM, React Native
- Meta-frameworks: Next.js, Remix, Gatsby, Expo, Create React App
- UI: Material UI, Chakra UI, Ant Design, Mantine, shadcn/ui, Radix, HeadlessUI
- Forms: React Hook Form, Formik, Final Form
- Animation: Framer Motion, React Spring, GSAP, React Transition Group
- Data Fetching: TanStack Query, SWR, Apollo Client, urql, Relay
- State: Redux, Zustand, Jotai, Recoil, MobX, Valtio, XState
- Routing: React Router, TanStack Router
- Testing: React Testing Library, Enzyme
- Styling: styled-components, Emotion, CSS Modules, Tailwind
- Visualization: Recharts, Victory, Nivo, D3-React, Visx
- Utilities: react-helmet, react-i18next, react-dnd, react-window

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.32 - React Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all React extractors
from .extractors.react import (
    ReactComponentExtractor, ReactComponentInfo, ReactHOCInfo,
    ReactForwardRefInfo, ReactMemoInfo, ReactLazyInfo,
    ReactErrorBoundaryInfo, ReactProviderInfo,
    ReactHookExtractor, ReactHookUsageInfo, ReactCustomHookInfo,
    ReactHookDependencyInfo,
    ReactContextExtractor, ReactContextInfo, ReactContextConsumerInfo,
    ReactStateExtractor, ReactStoreInfo, ReactSliceInfo,
    ReactAtomInfo, ReactQueryInfo,
    ReactRoutingExtractor, ReactRouteInfo, ReactLayoutInfo, ReactPageInfo,
)


@dataclass
class ReactParseResult:
    """Complete parse result for a React file."""
    file_path: str
    file_type: str = "jsx"  # jsx, tsx

    # Components
    components: List[ReactComponentInfo] = field(default_factory=list)
    hocs: List[ReactHOCInfo] = field(default_factory=list)
    forward_refs: List[ReactForwardRefInfo] = field(default_factory=list)
    memos: List[ReactMemoInfo] = field(default_factory=list)
    lazy_components: List[ReactLazyInfo] = field(default_factory=list)
    error_boundaries: List[ReactErrorBoundaryInfo] = field(default_factory=list)
    providers: List[ReactProviderInfo] = field(default_factory=list)

    # Hooks
    hook_usages: List[ReactHookUsageInfo] = field(default_factory=list)
    custom_hooks: List[ReactCustomHookInfo] = field(default_factory=list)
    hook_dependencies: List[ReactHookDependencyInfo] = field(default_factory=list)

    # Context
    contexts: List[ReactContextInfo] = field(default_factory=list)
    context_consumers: List[ReactContextConsumerInfo] = field(default_factory=list)

    # State management
    stores: List[ReactStoreInfo] = field(default_factory=list)
    slices: List[ReactSliceInfo] = field(default_factory=list)
    atoms: List[ReactAtomInfo] = field(default_factory=list)
    queries: List[ReactQueryInfo] = field(default_factory=list)

    # Routing
    routes: List[ReactRouteInfo] = field(default_factory=list)
    layouts: List[ReactLayoutInfo] = field(default_factory=list)
    pages: List[ReactPageInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    react_version: str = ""  # Detected minimum React version
    has_jsx: bool = False
    is_server_component: bool = False
    is_client_component: bool = False


class EnhancedReactParser:
    """
    Enhanced React parser that uses all extractors for comprehensive parsing.

    This parser is designed to run AFTER the JavaScript or TypeScript parser
    when React framework is detected. It extracts React-specific semantics
    that the language parsers cannot capture.

    Framework detection supports 60+ React ecosystem libraries across:
    - Core (React, ReactDOM, React Native)
    - Meta-frameworks (Next.js, Remix, Gatsby, Expo)
    - UI Libraries (Material UI, Chakra, Ant Design, Mantine, shadcn/ui)
    - Forms (React Hook Form, Formik, Final Form)
    - Animation (Framer Motion, React Spring, GSAP)
    - Data Fetching (TanStack Query, SWR, Apollo, urql, Relay)
    - State (Redux, Zustand, Jotai, Recoil, MobX, Valtio, XState)
    - Routing (React Router, TanStack Router)
    - Testing (Testing Library, Enzyme)
    - Styling (styled-components, Emotion, Tailwind)
    - Visualization (Recharts, Victory, Nivo, Visx)
    - Utilities (react-helmet, react-i18next, react-dnd, react-window)

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # React ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'react': re.compile(
            r"from\s+['\"]react['\"]|require\(['\"]react['\"]\)|React\.\w+|"
            r"useState|useEffect|useContext|useReducer|useMemo|useCallback|useRef",
            re.MULTILINE
        ),
        'react-dom': re.compile(
            r"from\s+['\"]react-dom['\"]|ReactDOM\.|createRoot|hydrateRoot|"
            r"createPortal|flushSync",
            re.MULTILINE
        ),
        'react-native': re.compile(
            r"from\s+['\"]react-native['\"]|"
            r"from\s+['\"]react-native-|"
            r"StyleSheet\.create|View|Text|TouchableOpacity|ScrollView|FlatList",
            re.MULTILINE
        ),

        # ── Meta-frameworks ───────────────────────────────────────
        'nextjs': re.compile(
            r"from\s+['\"]next['/\"]|NextPage|NextResponse|NextRequest|"
            r"getServerSideProps|getStaticProps|GetStaticPaths|"
            r"useRouter.*from\s+['\"]next|Image.*from\s+['\"]next|"
            r"Link.*from\s+['\"]next|Head.*from\s+['\"]next",
            re.MULTILINE
        ),
        'remix': re.compile(
            r"from\s+['\"]@remix-run['/\"]|"
            r"useLoaderData|useActionData|useFetcher|useMatches|useRouteError|"
            r"json\s*\(|redirect\s*\(",
            re.MULTILINE
        ),
        'gatsby': re.compile(
            r"from\s+['\"]gatsby['\"]|"
            r"graphql\s*`|useStaticQuery|gatsby-node|gatsby-config|"
            r"GatsbyImage|StaticImage",
            re.MULTILINE
        ),
        'expo': re.compile(
            r"from\s+['\"]expo['\"]|from\s+['\"]expo-|"
            r"expo-router|expo-constants|expo-file-system",
            re.MULTILINE
        ),

        # ── UI Libraries ──────────────────────────────────────────
        'material-ui': re.compile(
            r"from\s+['\"]@mui/|from\s+['\"]@material-ui/|"
            r"ThemeProvider|createTheme|makeStyles|styled\(",
            re.MULTILINE
        ),
        'chakra-ui': re.compile(
            r"from\s+['\"]@chakra-ui/|"
            r"ChakraProvider|useColorMode|useDisclosure|useToast",
            re.MULTILINE
        ),
        'ant-design': re.compile(
            r"from\s+['\"]antd['\"]|from\s+['\"]@ant-design/|"
            r"ConfigProvider|Form\.Item|Table|Modal|Button.*from\s+['\"]antd",
            re.MULTILINE
        ),
        'mantine': re.compile(
            r"from\s+['\"]@mantine/|MantineProvider|useMantineTheme",
            re.MULTILINE
        ),
        'shadcn-ui': re.compile(
            r"from\s+['\"]@/components/ui/|"
            r"from\s+['\"]components/ui/|"
            r"cn\(.*className",
            re.MULTILINE
        ),
        'radix-ui': re.compile(
            r"from\s+['\"]@radix-ui/",
            re.MULTILINE
        ),
        'headless-ui': re.compile(
            r"from\s+['\"]@headlessui/react['\"]|"
            r"Listbox|Combobox|Dialog|Transition.*headless",
            re.MULTILINE
        ),

        # ── Forms ─────────────────────────────────────────────────
        'react-hook-form': re.compile(
            r"from\s+['\"]react-hook-form['\"]|"
            r"useForm|useController|useFieldArray|useWatch|FormProvider",
            re.MULTILINE
        ),
        'formik': re.compile(
            r"from\s+['\"]formik['\"]|"
            r"Formik|useFormik|Field|ErrorMessage|FieldArray",
            re.MULTILINE
        ),
        'final-form': re.compile(
            r"from\s+['\"]react-final-form['\"]|from\s+['\"]final-form['\"]",
            re.MULTILINE
        ),

        # ── Animation ─────────────────────────────────────────────
        'framer-motion': re.compile(
            r"from\s+['\"]framer-motion['\"]|from\s+['\"]motion/react['\"]|"
            r"motion\.\w+|AnimatePresence|useAnimation|useMotionValue|useScroll",
            re.MULTILINE
        ),
        'react-spring': re.compile(
            r"from\s+['\"]@react-spring/|from\s+['\"]react-spring['\"]|"
            r"useSpring|useTrail|useTransition|useSprings|animated\.",
            re.MULTILINE
        ),
        'react-transition-group': re.compile(
            r"from\s+['\"]react-transition-group['\"]|"
            r"CSSTransition|TransitionGroup|SwitchTransition",
            re.MULTILINE
        ),

        # ── Data Fetching ─────────────────────────────────────────
        'tanstack-query': re.compile(
            r"from\s+['\"]@tanstack/react-query['\"]|"
            r"useQuery|useMutation|useInfiniteQuery|QueryClient|QueryClientProvider|"
            r"useSuspenseQuery",
            re.MULTILINE
        ),
        'swr': re.compile(
            r"from\s+['\"]swr['\"]|useSWR|useSWRMutation|SWRConfig",
            re.MULTILINE
        ),
        'apollo-client': re.compile(
            r"from\s+['\"]@apollo/client['\"]|"
            r"useQuery.*apollo|useMutation.*apollo|ApolloProvider|ApolloClient|"
            r"gql\s*`",
            re.MULTILINE
        ),
        'urql': re.compile(
            r"from\s+['\"]urql['\"]|from\s+['\"]@urql/|"
            r"useQuery.*urql|useMutation.*urql|Provider.*urql",
            re.MULTILINE
        ),
        'relay': re.compile(
            r"from\s+['\"]react-relay['\"]|from\s+['\"]relay-runtime['\"]|"
            r"useLazyLoadQuery|useFragment|usePreloadedQuery|graphql\s*`",
            re.MULTILINE
        ),

        # ── State Management ──────────────────────────────────────
        'redux': re.compile(
            r"from\s+['\"]react-redux['\"]|from\s+['\"]@reduxjs/toolkit['\"]|"
            r"useSelector|useDispatch|createSlice|configureStore|Provider.*store",
            re.MULTILINE
        ),
        'zustand': re.compile(
            r"from\s+['\"]zustand['\"]|create\s*\(\s*\(set|useStore",
            re.MULTILINE
        ),
        'jotai': re.compile(
            r"from\s+['\"]jotai['\"]|atom\s*\(|useAtom|atomWithStorage",
            re.MULTILINE
        ),
        'recoil': re.compile(
            r"from\s+['\"]recoil['\"]|"
            r"atom\s*\(|selector\s*\(|useRecoilState|useRecoilValue|RecoilRoot",
            re.MULTILINE
        ),
        'mobx-react': re.compile(
            r"from\s+['\"]mobx-react['\"]|from\s+['\"]mobx-react-lite['\"]|"
            r"observer\(|useLocalObservable",
            re.MULTILINE
        ),
        'valtio': re.compile(
            r"from\s+['\"]valtio['\"]|proxy\s*\(|useSnapshot",
            re.MULTILINE
        ),
        'xstate-react': re.compile(
            r"from\s+['\"]@xstate/react['\"]|useMachine|useActor|useSelector.*xstate",
            re.MULTILINE
        ),

        # ── Routing ───────────────────────────────────────────────
        'react-router': re.compile(
            r"from\s+['\"]react-router['\"]|from\s+['\"]react-router-dom['\"]|"
            r"BrowserRouter|HashRouter|Routes|Route|Link|NavLink|Outlet|"
            r"useNavigate|useParams|useLocation|useSearchParams|createBrowserRouter",
            re.MULTILINE
        ),
        'tanstack-router': re.compile(
            r"from\s+['\"]@tanstack/react-router['\"]|"
            r"createRouter|createRoute|createFileRoute|createRootRoute",
            re.MULTILINE
        ),

        # ── Testing ───────────────────────────────────────────────
        'testing-library': re.compile(
            r"from\s+['\"]@testing-library/react['\"]|"
            r"render\s*\(|screen\.\w+|fireEvent\.\w+|waitFor\s*\(|userEvent\.",
            re.MULTILINE
        ),
        'enzyme': re.compile(
            r"from\s+['\"]enzyme['\"]|"
            r"shallow\s*\(|mount\s*\(|wrapper\.\w+",
            re.MULTILINE
        ),

        # ── Styling ───────────────────────────────────────────────
        'styled-components': re.compile(
            r"from\s+['\"]styled-components['\"]|"
            r"styled\.\w+`|styled\(|createGlobalStyle|ThemeProvider.*styled",
            re.MULTILINE
        ),
        'emotion': re.compile(
            r"from\s+['\"]@emotion/|"
            r"css\s*`|styled\.\w+`|jsx\s*pragma|css\s*\(\{",
            re.MULTILINE
        ),
        'tailwind-react': re.compile(
            r"className\s*=\s*[{'\"].*(?:flex|grid|p-|m-|text-|bg-|w-|h-)",
            re.MULTILINE
        ),
        'css-modules': re.compile(
            r"import\s+\w+\s+from\s+['\"][^'\"]+\.module\.(?:css|scss|sass)['\"]|"
            r"styles\.\w+",
            re.MULTILINE
        ),

        # ── Visualization ─────────────────────────────────────────
        'recharts': re.compile(
            r"from\s+['\"]recharts['\"]|"
            r"LineChart|BarChart|PieChart|AreaChart|ResponsiveContainer",
            re.MULTILINE
        ),
        'victory': re.compile(
            r"from\s+['\"]victory['\"]|"
            r"VictoryChart|VictoryLine|VictoryBar|VictoryPie",
            re.MULTILINE
        ),
        'nivo': re.compile(
            r"from\s+['\"]@nivo/|ResponsiveLine|ResponsiveBar|ResponsivePie",
            re.MULTILINE
        ),
        'visx': re.compile(
            r"from\s+['\"]@visx/",
            re.MULTILINE
        ),

        # ── Utilities ─────────────────────────────────────────────
        'react-helmet': re.compile(
            r"from\s+['\"]react-helmet['\"]|from\s+['\"]react-helmet-async['\"]|"
            r"Helmet|HelmetProvider",
            re.MULTILINE
        ),
        'react-i18next': re.compile(
            r"from\s+['\"]react-i18next['\"]|"
            r"useTranslation|Trans|I18nextProvider|i18n\.init",
            re.MULTILINE
        ),
        'react-dnd': re.compile(
            r"from\s+['\"]react-dnd['\"]|"
            r"useDrag|useDrop|DndProvider|useDragLayer",
            re.MULTILINE
        ),
        'react-window': re.compile(
            r"from\s+['\"]react-window['\"]|from\s+['\"]react-virtualized['\"]|"
            r"FixedSizeList|VariableSizeList|FixedSizeGrid",
            re.MULTILINE
        ),
        'react-error-boundary': re.compile(
            r"from\s+['\"]react-error-boundary['\"]|ErrorBoundary|useErrorBoundary",
            re.MULTILINE
        ),
        'react-query-devtools': re.compile(
            r"from\s+['\"]@tanstack/react-query-devtools['\"]|ReactQueryDevtools",
            re.MULTILINE
        ),
        'react-hot-toast': re.compile(
            r"from\s+['\"]react-hot-toast['\"]|from\s+['\"]sonner['\"]|"
            r"toast\.\w+|Toaster",
            re.MULTILINE
        ),
    }

    # React version detection from hooks and features
    REACT_VERSION_FEATURES = {
        # React 19 features
        'useActionState': '19.0',
        'useFormStatus': '19.0',
        'useOptimistic': '19.0',
        'use(': '19.0',  # use() hook
        "'use server'": '19.0',

        # React 18 features
        'useId': '18.0',
        'useSyncExternalStore': '18.0',
        'useInsertionEffect': '18.0',
        'useTransition': '18.0',
        'useDeferredValue': '18.0',
        'startTransition': '18.0',
        'createRoot': '18.0',
        'hydrateRoot': '18.0',
        "'use client'": '18.0',

        # React 17 features (JSX transform)
        'react/jsx-runtime': '17.0',
        'react/jsx-dev-runtime': '17.0',

        # React 16.8 features (hooks)
        'useState': '16.8',
        'useEffect': '16.8',
        'useContext': '16.8',
        'useReducer': '16.8',
        'useMemo': '16.8',
        'useCallback': '16.8',
        'useRef': '16.8',
        'useLayoutEffect': '16.8',
        'useImperativeHandle': '16.8',
        'useDebugValue': '16.8',

        # React 16.6 features
        'React.lazy': '16.6',
        'React.memo': '16.6',
        'Suspense': '16.6',

        # React 16.3 features
        'createContext': '16.3',
        'createRef': '16.3',
        'forwardRef': '16.3',
        'React.createContext': '16.3',
        'React.createRef': '16.3',
        'React.forwardRef': '16.3',

        # React 16.0 features
        'createPortal': '16.0',
        'componentDidCatch': '16.0',
        'getDerivedStateFromError': '16.0',
        'Fragment': '16.0',

        # React 15 features
        'PureComponent': '15.0',
    }

    def __init__(self):
        """Initialize the parser with all React extractors."""
        self.component_extractor = ReactComponentExtractor()
        self.hook_extractor = ReactHookExtractor()
        self.context_extractor = ReactContextExtractor()
        self.state_extractor = ReactStateExtractor()
        self.routing_extractor = ReactRoutingExtractor()

    def parse(self, content: str, file_path: str = "") -> ReactParseResult:
        """
        Parse React source code and extract all React-specific information.

        This should be called AFTER the JavaScript/TypeScript parser has run,
        when React framework is detected. It extracts component structures,
        hook usage, context patterns, state management, and routing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            ReactParseResult with all extracted React information
        """
        result = ReactParseResult(file_path=file_path)

        # Detect file type
        if file_path.endswith('.tsx'):
            result.file_type = "tsx"
        elif file_path.endswith('.jsx'):
            result.file_type = "jsx"
        elif file_path.endswith('.ts'):
            result.file_type = "tsx"  # TS files with React are effectively tsx
        else:
            result.file_type = "jsx"

        # Check for JSX
        result.has_jsx = bool(re.search(
            r'<[A-Z]\w+[\s/>]|<\w+\.\w+[\s/>]|return\s*\(?\s*<\w+[\s/>]|'
            r'<\w+\s+\w+=\{|<>\s*|</\w+>',
            content
        ))

        # Detect server/client component directives
        result.is_client_component = bool(re.search(r"""^['"]use client['"]""", content, re.MULTILINE))
        result.is_server_component = bool(
            re.search(r"""^['"]use server['"]""", content, re.MULTILINE)
        ) or (
            # In Next.js app directory, files without 'use client' are server components
            ('app/' in file_path) and not result.is_client_component
            and ('page.' in file_path or 'layout.' in file_path)
        )

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Extract components ────────────────────────────────────
        comp_result = self.component_extractor.extract(content, file_path)
        result.components = comp_result.get('components', [])
        result.hocs = comp_result.get('hocs', [])
        result.forward_refs = comp_result.get('forward_refs', [])
        result.memos = comp_result.get('memos', [])
        result.lazy_components = comp_result.get('lazy_components', [])
        result.error_boundaries = comp_result.get('error_boundaries', [])
        result.providers = comp_result.get('providers', [])

        # ── Extract hooks ─────────────────────────────────────────
        hook_result = self.hook_extractor.extract(content, file_path)
        result.hook_usages = hook_result.get('hook_usages', [])
        result.custom_hooks = hook_result.get('custom_hooks', [])
        result.hook_dependencies = hook_result.get('hook_dependencies', [])

        # ── Extract context ───────────────────────────────────────
        ctx_result = self.context_extractor.extract(content, file_path)
        result.contexts = ctx_result.get('contexts', [])
        result.context_consumers = ctx_result.get('consumers', [])

        # ── Extract state management ──────────────────────────────
        state_result = self.state_extractor.extract(content, file_path)
        result.stores = state_result.get('stores', [])
        result.slices = state_result.get('slices', [])
        result.atoms = state_result.get('atoms', [])
        result.queries = state_result.get('queries', [])

        # ── Extract routing ───────────────────────────────────────
        routing_result = self.routing_extractor.extract(content, file_path)
        result.routes = routing_result.get('routes', [])
        result.layouts = routing_result.get('layouts', [])
        result.pages = routing_result.get('pages', [])

        # ── Detect React version ──────────────────────────────────
        result.react_version = self._detect_react_version(content)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which React ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_react_version(self, content: str) -> str:
        """
        Detect the minimum React version required by the file.

        Returns version string (e.g., '19.0', '18.0', '16.8').
        Detection is based on hooks and features used in the code.
        """
        max_version = '0.0'

        for feature, version in self.REACT_VERSION_FEATURES.items():
            if feature in content:
                if self._version_compare(version, max_version) > 0:
                    max_version = version

        return max_version if max_version != '0.0' else ''

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings. Returns >0 if v1>v2, <0 if v1<v2, 0 if equal."""
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        for a, b in zip(parts1, parts2):
            if a != b:
                return a - b
        return len(parts1) - len(parts2)

    def is_react_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file contains React code worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file likely contains React code
        """
        # .jsx files are always React
        if file_path.endswith('.jsx'):
            return True

        # .tsx files are always React
        if file_path.endswith('.tsx'):
            return True

        # Check for React imports
        if re.search(r"from\s+['\"]react['\"]", content):
            return True

        # Check for React.createElement or JSX
        if re.search(r'React\.createElement|React\.Component|React\.PureComponent', content):
            return True

        # Check for hooks (strong indicator)
        if re.search(r'\b(?:useState|useEffect|useContext|useReducer|useMemo|useCallback|useRef)\s*\(', content):
            return True

        # Check for JSX (PascalCase tags)
        if re.search(r'<[A-Z]\w+[\s/>]', content) and re.search(r'return\s*\(?\s*<', content):
            return True

        return False
