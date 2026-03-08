"""
EnhancedSvelteParser v1.0 - Comprehensive Svelte/SvelteKit parser using all extractors.

This parser integrates all Svelte extractors to provide complete parsing of
Svelte source files (.svelte, .svelte.ts, .svelte.js, +page.ts, +server.ts, etc.).

Supports:
- Svelte 3.x (reactive declarations $:, export let props, createEventDispatcher, stores)
- Svelte 4.x (improved TypeScript, performance improvements, transition API updates)
- Svelte 5.x (Runes: $state, $derived, $effect, $props, $bindable, $inspect,
              Snippets: {#snippet}, {@render}, Event handlers as props,
              Fine-grained reactivity, $effect.pre, $effect.root, $state.raw,
              $state.snapshot, $host, Component class deprecation)

SvelteKit Support:
- SvelteKit 1.x (file-based routing, load functions, form actions, hooks,
                 adapters, env, $app stores, prerendering, SSR/CSR/SSG)
- SvelteKit 2.x (shallow routing, enhanced forms, improved hooks,
                 streaming, universal/server load, reroute hook,
                 $env improvements, path resolution)

Component patterns:
- Single File Components (.svelte) with <script>, <style>, and template
- <script context="module"> / <script module> for module-level code
- <script lang="ts"> for TypeScript support
- Props: export let (Svelte 3/4), $props rune (Svelte 5)
- Events: createEventDispatcher (Svelte 3/4), callback props (Svelte 5)
- Slots: <slot> (Svelte 3/4), {#snippet}/{@render} (Svelte 5)
- Two-way binding: bind:value, bind:this, bind:group
- Transitions: transition:, in:, out:, animate:
- Actions: use: directive
- Special elements: svelte:window, svelte:body, svelte:head, svelte:component,
                    svelte:self, svelte:fragment, svelte:element, svelte:options

Reactivity (Svelte 3/4):
- $: reactive declarations/statements
- Reactive store subscriptions ($store)
- export let for props

Reactivity (Svelte 5 Runes):
- $state() - reactive state
- $state.raw() - non-deeply-reactive state
- $state.snapshot() - get plain snapshot
- $derived() - computed values
- $derived.by() - computed with function
- $effect() - side effects (replaces $: and onMount/afterUpdate)
- $effect.pre() - pre-update effects (replaces beforeUpdate)
- $effect.root() - manual cleanup root
- $props() - component props
- $bindable() - bindable props
- $inspect() - debug reactivity
- $host() - custom element host

State management:
- svelte/store: writable, readable, derived, get
- Custom stores (store contract)
- SvelteKit stores: page, navigating, updated
- Svelte 5: $state in .svelte.ts/.svelte.js modules

Routing (SvelteKit):
- File-based routing: +page.svelte, +layout.svelte, +error.svelte
- API routes: +server.ts with GET/POST/PUT/PATCH/DELETE
- Data loading: +page.ts (universal), +page.server.ts (server-only)
- Form actions: +page.server.ts actions
- Hooks: hooks.server.ts, hooks.client.ts
- Param matchers: src/params/*.ts
- Route groups: (group)/route
- Dynamic routes: [param], [...rest], [[optional]]

Framework detection (60+ Svelte ecosystem patterns):
- Core: Svelte 3/4/5, SvelteKit 1/2
- UI Libraries: Skeleton UI, shadcn-svelte, Flowbite Svelte, DaisyUI,
                Svelte Headless UI, Carbon Components Svelte,
                Svelte Material UI, Attractions
- State: svelte/store, Svelte 5 runes, nanostores
- Forms: Superforms, Formsnap, Felte
- Testing: Vitest, Playwright, Testing Library Svelte, Svelte Testing Library
- Data: TanStack Query Svelte, tRPC Svelte, Houdini (GraphQL)
- Animation: svelte/motion, svelte/transition, svelte/animate, Motion One
- Auth: Lucia, Auth.js/SvelteKit Auth, Supabase Auth
- Build: Vite, svelte-kit, svelte-preprocess
- Utilities: svelte-i18n, paraglide-js, typesafe-i18n,
             svelte-meta-tags, svelte-persisted-store

Optional AST support via tree-sitter-svelte (for template parsing).
Optional LSP support via Svelte Language Server (svelte-language-server).

Part of CodeTrellis v4.35 - Svelte/SvelteKit Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Svelte extractors
from .extractors.svelte import (
    SvelteComponentExtractor, SvelteComponentInfo, SveltePropInfo,
    SvelteEventInfo, SvelteSlotInfo, SvelteBindingInfo,
    SvelteStoreExtractor, SvelteStoreInfo, SvelteStoreSubscriptionInfo,
    SvelteActionExtractor, SvelteActionInfo,
    SvelteRoutingExtractor, SvelteRouteInfo, SvelteLoadFunctionInfo,
    SvelteFormActionInfo, SvelteHookInfo, SvelteParamMatcherInfo,
    SvelteLifecycleExtractor, SvelteLifecycleHookInfo, SvelteContextInfo,
    SvelteRuneInfo,
)


@dataclass
class SvelteParseResult:
    """Complete parse result for a Svelte/SvelteKit file."""
    file_path: str
    file_type: str = "svelte"  # svelte, ts, js, svelte.ts, svelte.js

    # Components
    components: List[SvelteComponentInfo] = field(default_factory=list)

    # Stores
    stores: List[SvelteStoreInfo] = field(default_factory=list)
    store_subscriptions: List[SvelteStoreSubscriptionInfo] = field(default_factory=list)

    # Actions
    actions: List[SvelteActionInfo] = field(default_factory=list)

    # Routing (SvelteKit)
    routes: List[SvelteRouteInfo] = field(default_factory=list)
    load_functions: List[SvelteLoadFunctionInfo] = field(default_factory=list)
    form_actions: List[SvelteFormActionInfo] = field(default_factory=list)
    hooks: List[SvelteHookInfo] = field(default_factory=list)
    param_matchers: List[SvelteParamMatcherInfo] = field(default_factory=list)

    # Lifecycle
    lifecycle_hooks: List[SvelteLifecycleHookInfo] = field(default_factory=list)
    contexts: List[SvelteContextInfo] = field(default_factory=list)
    runes: List[SvelteRuneInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    svelte_version: str = ""  # Detected minimum Svelte version
    sveltekit_version: str = ""  # Detected SvelteKit version
    uses_runes: bool = False
    uses_typescript: bool = False
    has_sveltekit: bool = False
    has_ssr: bool = False
    has_csr: bool = False
    has_prerender: bool = False


class EnhancedSvelteParser:
    """
    Enhanced Svelte/SvelteKit parser that uses all extractors for comprehensive parsing.

    This parser handles .svelte component files, .svelte.ts/.svelte.js module files,
    and SvelteKit routing files (+page.ts, +server.ts, etc.).

    Framework detection supports 60+ Svelte ecosystem libraries across:
    - Core (Svelte 3/4/5, SvelteKit 1/2)
    - UI Libraries (Skeleton, shadcn-svelte, Flowbite, DaisyUI, Carbon)
    - State Management (svelte/store, Svelte 5 runes, nanostores)
    - Forms (Superforms, Formsnap, Felte)
    - Testing (Vitest, Playwright, Testing Library)
    - Data Fetching (TanStack Query, tRPC, Houdini)
    - Animation (svelte/motion, svelte/transition)
    - Auth (Lucia, Auth.js, Supabase)
    - Build (Vite, svelte-kit, svelte-preprocess)
    - i18n (svelte-i18n, paraglide-js, typesafe-i18n)

    Optional AST: tree-sitter-svelte
    Optional LSP: Svelte Language Server (svelte-language-server)
    """

    # Svelte ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core ──────────────────────────────────────────────────
        'svelte': re.compile(
            r"from\s+['\"]svelte['/\"]|"
            r"<script|<style|export\s+let\s+|"
            r"\$state\s*\(|\$derived\s*[.(]|\$effect\s*\(|\$props\s*\(|"
            r"onMount|onDestroy|createEventDispatcher",
            re.MULTILINE
        ),
        'sveltekit': re.compile(
            r"from\s+['\"](?:\$app|@sveltejs/kit)['/\"]|"
            r"\+page\.svelte|\+layout\.svelte|\+server\.|"
            r"\+page\.server\.|hooks\.server\.|"
            r"import.*from\s+['\"]\.\/\$types['\"]|"
            r"svelte\.config\.|sveltekit|"
            r"export\s+const\s+(?:prerender|ssr|csr)|"
            r"export\s+const\s+actions\b",
            re.MULTILINE
        ),

        # ── UI Libraries ──────────────────────────────────────────
        'skeleton-ui': re.compile(
            r"from\s+['\"]@skeletonlabs/skeleton['/\"]|"
            r"from\s+['\"]@skeletonlabs/['\"]|"
            r"AppShell|AppBar|AppRail|SlideToggle|TabGroup|TabAnchor|"
            r"ProgressBar|RangeSlider",
            re.MULTILINE
        ),
        'shadcn-svelte': re.compile(
            r"from\s+['\"](?:\$lib/components/ui/|@/components/ui/)|"
            r"from\s+['\"]bits-ui['\"]",
            re.MULTILINE
        ),
        'flowbite-svelte': re.compile(
            r"from\s+['\"]flowbite-svelte['/\"]|"
            r"Button|Card|Modal|Navbar.*flowbite",
            re.MULTILINE
        ),
        'daisyui': re.compile(
            r"daisyui|class=\"[^\"]*(?:btn|card|hero|navbar|drawer|modal|collapse)",
            re.MULTILINE
        ),
        'carbon-svelte': re.compile(
            r"from\s+['\"]carbon-components-svelte['/\"]|"
            r"from\s+['\"]carbon-icons-svelte['/\"]",
            re.MULTILINE
        ),
        'svelte-headless-ui': re.compile(
            r"from\s+['\"]svelte-headless-ui['/\"]|"
            r"from\s+['\"]@rgossiaux/svelte-headlessui['/\"]",
            re.MULTILINE
        ),
        'smui': re.compile(
            r"from\s+['\"]@smui/['\"]|"
            r"from\s+['\"]svelte-material-ui['\"]",
            re.MULTILINE
        ),
        'melt-ui': re.compile(
            r"from\s+['\"]@melt-ui/svelte['/\"]|"
            r"createDialog|createMenu|createTabs.*melt",
            re.MULTILINE
        ),
        'bits-ui': re.compile(
            r"from\s+['\"]bits-ui['/\"]",
            re.MULTILINE
        ),
        'attractions': re.compile(
            r"from\s+['\"]attractions['/\"]",
            re.MULTILINE
        ),

        # ── State Management ──────────────────────────────────────
        'svelte-store': re.compile(
            r"from\s+['\"]svelte/store['\"]|"
            r"writable\s*\(|readable\s*\(|derived\s*\(",
            re.MULTILINE
        ),
        'nanostores': re.compile(
            r"from\s+['\"](?:nanostores|@nanostores/)['/\"]|"
            r"from\s+['\"]nanostores['\"]",
            re.MULTILINE
        ),
        'svelte-persisted-store': re.compile(
            r"from\s+['\"]svelte-persisted-store['\"]|"
            r"from\s+['\"]svelte-local-storage-store['\"]",
            re.MULTILINE
        ),

        # ── Forms ─────────────────────────────────────────────────
        'superforms': re.compile(
            r"from\s+['\"]sveltekit-superforms['/\"]|"
            r"superForm|superValidate|message\b",
            re.MULTILINE
        ),
        'formsnap': re.compile(
            r"from\s+['\"]formsnap['/\"]",
            re.MULTILINE
        ),
        'felte': re.compile(
            r"from\s+['\"]felte['/\"]|"
            r"from\s+['\"]@felte/['\"]",
            re.MULTILINE
        ),

        # ── Validation ────────────────────────────────────────────
        'zod': re.compile(
            r"from\s+['\"]zod['\"]|z\.object|z\.string|z\.number",
            re.MULTILINE
        ),
        'valibot': re.compile(
            r"from\s+['\"]valibot['\"]",
            re.MULTILINE
        ),

        # ── Testing ───────────────────────────────────────────────
        'vitest': re.compile(
            r"from\s+['\"]vitest['\"]|vi\.mock|vi\.fn|describe\s*\(",
            re.MULTILINE
        ),
        'playwright': re.compile(
            r"from\s+['\"]@playwright/test['\"]|"
            r"from\s+['\"]playwright['\"]|"
            r"test\.describe|page\.goto",
            re.MULTILINE
        ),
        'testing-library-svelte': re.compile(
            r"from\s+['\"]@testing-library/svelte['\"]|"
            r"render\s*\(|fireEvent\.",
            re.MULTILINE
        ),
        'svelte-testing-library': re.compile(
            r"from\s+['\"]svelte-testing-library['\"]",
            re.MULTILINE
        ),

        # ── Data Fetching ─────────────────────────────────────────
        'tanstack-query-svelte': re.compile(
            r"from\s+['\"]@tanstack/svelte-query['\"]|"
            r"createQuery|createMutation|QueryClientProvider",
            re.MULTILINE
        ),
        'trpc-svelte': re.compile(
            r"from\s+['\"]trpc-svelte-query['/\"]|"
            r"from\s+['\"]@trpc/client['\"].*svelte",
            re.MULTILINE
        ),
        'houdini': re.compile(
            r"from\s+['\"](?:\$houdini|\.\./\$houdini)['/\"]|"
            r"from\s+['\"]houdini['\"]|graphql\s*`",
            re.MULTILINE
        ),

        # ── Authentication ────────────────────────────────────────
        'lucia': re.compile(
            r"from\s+['\"]lucia['/\"]|"
            r"from\s+['\"]@lucia-auth/['\"]",
            re.MULTILINE
        ),
        'authjs-sveltekit': re.compile(
            r"from\s+['\"]@auth/sveltekit['\"]|"
            r"from\s+['\"]@auth/core['\"]|SvelteKitAuth",
            re.MULTILINE
        ),
        'supabase-sveltekit': re.compile(
            r"from\s+['\"]@supabase/ssr['\"]|"
            r"from\s+['\"]@supabase/supabase-js['\"].*sveltekit|"
            r"createBrowserClient|createServerClient",
            re.MULTILINE
        ),

        # ── ORM / Database ────────────────────────────────────────
        'prisma': re.compile(
            r"from\s+['\"]@prisma/client['\"]|PrismaClient|prisma\.\w+\.",
            re.MULTILINE
        ),
        'drizzle': re.compile(
            r"from\s+['\"]drizzle-orm['/\"]|"
            r"from\s+['\"]drizzle-kit['\"]",
            re.MULTILINE
        ),

        # ── HTTP ──────────────────────────────────────────────────
        'axios': re.compile(
            r"from\s+['\"]axios['\"]|axios\.\w+",
            re.MULTILINE
        ),
        'ky': re.compile(
            r"from\s+['\"]ky['\"]",
            re.MULTILINE
        ),

        # ── i18n ──────────────────────────────────────────────────
        'svelte-i18n': re.compile(
            r"from\s+['\"]svelte-i18n['/\"]|"
            r"init\s*\(.*locale|_\s*\(|format\s*\(",
            re.MULTILINE
        ),
        'paraglide-js': re.compile(
            r"from\s+['\"]@inlang/paraglide-js['/\"]|"
            r"from\s+['\"]@inlang/paraglide-sveltekit['/\"]",
            re.MULTILINE
        ),
        'typesafe-i18n': re.compile(
            r"from\s+['\"]typesafe-i18n['/\"]",
            re.MULTILINE
        ),

        # ── Animation ─────────────────────────────────────────────
        'svelte-motion': re.compile(
            r"from\s+['\"]svelte/motion['\"]|tweened|spring",
            re.MULTILINE
        ),
        'svelte-transition': re.compile(
            r"from\s+['\"]svelte/transition['\"]|"
            r"fade|fly|slide|scale|blur|crossfade|draw",
            re.MULTILINE
        ),
        'motion-one-svelte': re.compile(
            r"from\s+['\"]@motionone/svelte['\"]",
            re.MULTILINE
        ),

        # ── Build / Tooling ───────────────────────────────────────
        'vite': re.compile(
            r"from\s+['\"]vite['\"]|import\.meta\.env|import\.meta\.hot",
            re.MULTILINE
        ),
        'svelte-preprocess': re.compile(
            r"from\s+['\"]svelte-preprocess['\"]|"
            r"preprocess\s*\(",
            re.MULTILINE
        ),
        'mdsvex': re.compile(
            r"from\s+['\"]mdsvex['\"]|"
            r"\.svx\b",
            re.MULTILINE
        ),

        # ── Utilities ─────────────────────────────────────────────
        'svelte-meta-tags': re.compile(
            r"from\s+['\"]svelte-meta-tags['\"]|MetaTags",
            re.MULTILINE
        ),
        'svelte-french-toast': re.compile(
            r"from\s+['\"]svelte-french-toast['\"]|toast\.",
            re.MULTILINE
        ),
        'svelte-sonner': re.compile(
            r"from\s+['\"]svelte-sonner['\"]",
            re.MULTILINE
        ),

        # ── CSS / Styling ─────────────────────────────────────────
        'tailwindcss': re.compile(
            r"class=\"[^\"]*(?:flex|grid|p-|m-|text-|bg-|w-|h-)|"
            r"tailwind\.config|@tailwind",
            re.MULTILINE
        ),
        'unocss': re.compile(
            r"from\s+['\"]unocss['/\"]|uno\.config",
            re.MULTILINE
        ),

        # ── GraphQL ───────────────────────────────────────────────
        'urql-svelte': re.compile(
            r"from\s+['\"]@urql/svelte['\"]",
            re.MULTILINE
        ),
    }

    # Svelte version detection from features used
    SVELTE_VERSION_FEATURES = {
        # Svelte 5 features (runes)
        '$state': '5.0',
        '$derived': '5.0',
        '$effect': '5.0',
        '$props': '5.0',
        '$bindable': '5.0',
        '$inspect': '5.0',
        '$host': '5.0',
        '$state.raw': '5.0',
        '$state.snapshot': '5.0',
        '$derived.by': '5.0',
        '$effect.pre': '5.0',
        '$effect.root': '5.0',
        '{#snippet': '5.0',
        '{@render': '5.0',

        # Svelte 4 features
        'satisfies': '4.0',

        # Svelte 3 features (base)
        'export let': '3.0',
        'createEventDispatcher': '3.0',
        'onMount': '3.0',
        'onDestroy': '3.0',
        '$:': '3.0',
        'writable(': '3.0',
        'readable(': '3.0',
        'derived(': '3.0',
    }

    # SvelteKit version features
    SVELTEKIT_VERSION_FEATURES = {
        # SvelteKit 2
        'reroute': '2.0',
        'shallow routing': '2.0',
        'pushState': '2.0',
        'replaceState': '2.0',

        # SvelteKit 1
        '+page.svelte': '1.0',
        '+layout.svelte': '1.0',
        '+server.': '1.0',
        '+page.server.': '1.0',
        'hooks.server.': '1.0',
    }

    def __init__(self):
        """Initialize the parser with all Svelte extractors."""
        self.component_extractor = SvelteComponentExtractor()
        self.store_extractor = SvelteStoreExtractor()
        self.action_extractor = SvelteActionExtractor()
        self.routing_extractor = SvelteRoutingExtractor()
        self.lifecycle_extractor = SvelteLifecycleExtractor()

    def parse(self, content: str, file_path: str = "") -> SvelteParseResult:
        """
        Parse Svelte/SvelteKit source code and extract all information.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            SvelteParseResult with all extracted information
        """
        result = SvelteParseResult(file_path=file_path)

        # Detect file type
        if file_path.endswith('.svelte'):
            result.file_type = "svelte"
        elif file_path.endswith('.svelte.ts'):
            result.file_type = "svelte.ts"
        elif file_path.endswith('.svelte.js'):
            result.file_type = "svelte.js"
        elif file_path.endswith('.ts'):
            result.file_type = "ts"
        elif file_path.endswith('.js'):
            result.file_type = "js"

        # Detect TypeScript
        result.uses_typescript = (
            result.file_type in ('ts', 'svelte.ts') or
            'lang="ts"' in content or
            "lang='ts'" in content or
            'lang="typescript"' in content
        )

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect SvelteKit
        result.has_sveltekit = 'sveltekit' in result.detected_frameworks

        # ── Extract components ────────────────────────────────────
        if file_path.endswith('.svelte'):
            comp_result = self.component_extractor.extract(content, file_path)
            result.components = comp_result.get('components', [])

            # Detect runes from components
            for comp in result.components:
                if comp.uses_runes:
                    result.uses_runes = True

        # ── Extract stores ────────────────────────────────────────
        store_result = self.store_extractor.extract(content, file_path)
        result.stores = store_result.get('stores', [])
        result.store_subscriptions = store_result.get('subscriptions', [])

        # ── Extract actions ───────────────────────────────────────
        action_result = self.action_extractor.extract(content, file_path)
        result.actions = action_result.get('actions', [])

        # ── Extract routing ───────────────────────────────────────
        routing_result = self.routing_extractor.extract(content, file_path)
        result.routes = routing_result.get('routes', [])
        result.load_functions = routing_result.get('load_functions', [])
        result.form_actions = routing_result.get('form_actions', [])
        result.hooks = routing_result.get('hooks', [])
        result.param_matchers = routing_result.get('param_matchers', [])

        # ── Extract lifecycle ─────────────────────────────────────
        lifecycle_result = self.lifecycle_extractor.extract(content, file_path)
        result.lifecycle_hooks = lifecycle_result.get('lifecycle_hooks', [])
        result.contexts = lifecycle_result.get('contexts', [])
        result.runes = lifecycle_result.get('runes', [])

        if result.runes:
            result.uses_runes = True

        # ── Detect rendering config ──────────────────────────────
        self._detect_rendering_config(content, result)

        # ── Detect versions ───────────────────────────────────────
        result.svelte_version = self._detect_svelte_version(content)
        result.sveltekit_version = self._detect_sveltekit_version(content, file_path)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Svelte ecosystem frameworks/libraries are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            try:
                if pattern.search(content):
                    frameworks.append(framework)
            except Exception:
                pass
        return frameworks

    def _detect_svelte_version(self, content: str) -> str:
        """
        Detect the minimum Svelte version required by the file.

        Returns version string (e.g., '5.0', '4.0', '3.0').
        """
        max_version = '0.0'

        for feature, version in self.SVELTE_VERSION_FEATURES.items():
            if feature in content:
                if self._version_compare(version, max_version) > 0:
                    max_version = version

        return max_version if max_version != '0.0' else ''

    def _detect_sveltekit_version(self, content: str, file_path: str) -> str:
        """Detect SvelteKit version from features."""
        max_version = '0.0'

        combined = content + ' ' + file_path
        for feature, version in self.SVELTEKIT_VERSION_FEATURES.items():
            if feature in combined:
                if self._version_compare(version, max_version) > 0:
                    max_version = version

        return max_version if max_version != '0.0' else ''

    def _detect_rendering_config(self, content: str, result: SvelteParseResult):
        """Detect SSR/CSR/prerender configuration."""
        if re.search(r'export\s+const\s+ssr\s*=\s*(?:true|false)', content):
            result.has_ssr = True
        if re.search(r'export\s+const\s+csr\s*=\s*(?:true|false)', content):
            result.has_csr = True
        if re.search(r'export\s+const\s+prerender\s*=\s*(?:true|false|[\'"]auto[\'"])', content):
            result.has_prerender = True

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings."""
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        for a, b in zip(parts1, parts2):
            if a != b:
                return a - b
        return len(parts1) - len(parts2)

    def is_svelte_file(self, content: str, file_path: str = "") -> bool:
        """
        Determine if a file contains Svelte code worth parsing.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            True if the file likely contains Svelte code
        """
        # .svelte files are always Svelte
        if file_path.endswith('.svelte'):
            return True

        # .svelte.ts and .svelte.js are Svelte modules
        if file_path.endswith('.svelte.ts') or file_path.endswith('.svelte.js'):
            return True

        # SvelteKit routing files
        sveltekit_patterns = [
            '+page.ts', '+page.js', '+page.server.ts', '+page.server.js',
            '+layout.ts', '+layout.js', '+layout.server.ts', '+layout.server.js',
            '+server.ts', '+server.js', '+error.svelte',
            'hooks.server.ts', 'hooks.server.js',
            'hooks.client.ts', 'hooks.client.js',
            'hooks.ts', 'hooks.js',
        ]
        for pattern in sveltekit_patterns:
            if file_path.endswith(pattern):
                return True

        # Check for param matchers
        if '/params/' in file_path and (file_path.endswith('.ts') or file_path.endswith('.js')):
            if re.search(r'export\s+(?:const\s+)?match\b', content):
                return True

        # Check for Svelte imports in JS/TS files
        if re.search(r"from\s+['\"]svelte['/\"]", content):
            return True

        # Check for SvelteKit imports
        if re.search(r"from\s+['\"](?:\$app|\@sveltejs/kit)['/\"]", content):
            return True

        # Check for svelte/store usage
        if re.search(r"from\s+['\"]svelte/store['\"]", content):
            return True

        # Check for Svelte 5 runes in .ts/.js files
        if re.search(r'\$(?:state|derived|effect|props|bindable|inspect)\s*[.(]', content):
            return True

        return False
