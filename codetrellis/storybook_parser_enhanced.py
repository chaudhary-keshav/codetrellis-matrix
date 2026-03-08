"""
EnhancedStorybookParser v1.0 - Comprehensive Storybook parser using all extractors.

This parser integrates all Storybook extractors to provide complete parsing of
Storybook framework usage across JavaScript, TypeScript, and MDX source files.
It runs as a supplementary layer on top of the JavaScript/TypeScript parsers,
extracting Storybook-specific semantics.

Supports:
- Storybook 5.x (storiesOf API, addon-knobs, legacy config)
- Storybook 6.x (CSF 2.0, Template.bind, args/argTypes, controls,
                  addon-essentials, actions, MDX 1, docs addon)
- Storybook 7.x (CSF 3.0, play functions, MDX 2, framework packages,
                  vite builder, autodocs, interaction testing, tags,
                  @storybook/testing-library)
- Storybook 8.x (CSF 3.0+, MDX 3, portable stories, mount in play,
                  beforeEach, @storybook/test unified testing,
                  vitest integration, visual testing, project annotations,
                  experimental-nextjs-vite)

Story Formats:
- CSF 1.0 — Function export stories (v5.x)
- CSF 2.0 — Template.bind({}) stories with args (v6.x)
- CSF 3.0 — Object notation stories with render/play/args (v7+)
- storiesOf — Legacy imperative API (v5.x)
- MDX — Documentation-first stories with <Meta>/<Story>/<Canvas>

Framework Integration:
- React (@storybook/react, @storybook/react-vite, @storybook/react-webpack5)
- Vue 3 (@storybook/vue3-vite, @storybook/vue3-webpack5)
- Angular (@storybook/angular)
- Svelte (@storybook/svelte-vite, @storybook/svelte-webpack5)
- Web Components (@storybook/web-components-vite)
- HTML (@storybook/html-vite)
- Preact (@storybook/preact-vite)
- Next.js (@storybook/nextjs, @storybook/experimental-nextjs-vite)
- SvelteKit (@storybook/sveltekit)
- Nuxt (@storybook/nuxt)
- Ember (@storybook/ember)

Testing Integration:
- Interaction testing (play functions, userEvent, expect, within, step)
- Portable stories (composeStories, composeStory, setProjectAnnotations)
- Visual testing (Chromatic)
- @storybook/test (v8 unified testing)
- @storybook/testing-library (v7)
- @storybook/jest (v7, deprecated in v8)

Addon Ecosystem:
- addon-essentials (actions, controls, docs, viewport, backgrounds,
                     toolbars, measure, outline, highlight)
- addon-interactions (step-through debugging)
- addon-a11y (accessibility checks)
- addon-designs (Figma/Zeplin embeds)
- addon-themes (theme switching)
- addon-storysource (story source code display)
- addon-coverage (code coverage)
- addon-test (v8 vitest integration)

Optional AST support via tree-sitter-javascript / tree-sitter-typescript.
Optional LSP support via typescript-language-server (tsserver).

Part of CodeTrellis v4.70 - Storybook Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Import all Storybook extractors
from .extractors.storybook import (
    StorybookStoryExtractor, StorybookStoryInfo,
    StorybookComponentExtractor, StorybookComponentInfo,
    StorybookAddonExtractor, StorybookAddonInfo,
    StorybookConfigExtractor, StorybookConfigInfo,
    StorybookApiExtractor, StorybookImportInfo, StorybookTestingInfo,
)


@dataclass
class StorybookParseResult:
    """Complete parse result for a file with Storybook usage."""
    file_path: str
    file_type: str = "js"  # js, ts, jsx, tsx, mdx

    # Stories
    stories: List[StorybookStoryInfo] = field(default_factory=list)

    # Components
    components: List[StorybookComponentInfo] = field(default_factory=list)

    # Addons
    addons: List[StorybookAddonInfo] = field(default_factory=list)

    # Config
    configs: List[StorybookConfigInfo] = field(default_factory=list)

    # API / Imports
    imports: List[StorybookImportInfo] = field(default_factory=list)

    # Testing
    testing: List[StorybookTestingInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_features: List[str] = field(default_factory=list)
    storybook_version: str = ""  # v5, v6, v7, v8
    csf_version: str = ""  # csf1, csf2, csf3, legacy, mdx
    has_play_functions: bool = False
    has_interaction_testing: bool = False
    has_portable_stories: bool = False
    has_chromatic: bool = False
    has_autodocs: bool = False

    @property
    def detected_version(self) -> str:
        """Alias for storybook_version for convenience."""
        return self.storybook_version

    @property
    def detected_csf_version(self) -> str:
        """Alias for csf_version for convenience."""
        return self.csf_version


class EnhancedStorybookParser:
    """
    Enhanced Storybook parser that uses all extractors.

    This parser runs AFTER the JavaScript/TypeScript parser when Storybook
    framework is detected. It extracts Storybook-specific semantics
    that the language parsers cannot capture.

    Framework detection supports 30+ Storybook ecosystem packages.

    Optional AST: tree-sitter-javascript / tree-sitter-typescript
    Optional LSP: typescript-language-server (tsserver)
    """

    # Storybook ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core Framework Packages ──────────────────────────────
        '@storybook/core': re.compile(
            r"""(?:from\s+['"]@storybook/[\w\-]+['"]|"""
            r"""require\(['"]@storybook/[\w\-]+['"]\)|"""
            r"""['"]@storybook/[\w\-]+['"]\s*[,\]])""",
            re.MULTILINE
        ),
        '@storybook/react': re.compile(
            r"""(?:from\s+['"]@storybook/react(?:-(?:vite|webpack5))?['"]|"""
            r"""framework\s*:\s*['"]@storybook/react)""",
            re.MULTILINE
        ),
        '@storybook/vue3': re.compile(
            r"""(?:from\s+['"]@storybook/vue3?(?:-(?:vite|webpack5))?['"]|"""
            r"""framework\s*:\s*['"]@storybook/vue)""",
            re.MULTILINE
        ),
        '@storybook/angular': re.compile(
            r"""(?:from\s+['"]@storybook/angular['"]|"""
            r"""framework\s*:\s*['"]@storybook/angular)""",
            re.MULTILINE
        ),
        '@storybook/svelte': re.compile(
            r"""(?:from\s+['"]@storybook/svelte(?:-(?:vite|webpack5)|kit)?['"]|"""
            r"""framework\s*:\s*['"]@storybook/svelte)""",
            re.MULTILINE
        ),
        '@storybook/nextjs': re.compile(
            r"""(?:from\s+['"]@storybook/(?:nextjs|experimental-nextjs-vite)['"]|"""
            r"""framework\s*:\s*['"]@storybook/(?:nextjs|experimental-nextjs-vite))""",
            re.MULTILINE
        ),
        '@storybook/web-components': re.compile(
            r"""(?:from\s+['"]@storybook/web-components(?:-(?:vite|webpack5))?['"]|"""
            r"""framework\s*:\s*['"]@storybook/web-components)""",
            re.MULTILINE
        ),
        '@storybook/html': re.compile(
            r"""(?:from\s+['"]@storybook/html(?:-(?:vite|webpack5))?['"]|"""
            r"""framework\s*:\s*['"]@storybook/html)""",
            re.MULTILINE
        ),
        '@storybook/preact': re.compile(
            r"""(?:from\s+['"]@storybook/preact(?:-(?:vite|webpack5))?['"]|"""
            r"""framework\s*:\s*['"]@storybook/preact)""",
            re.MULTILINE
        ),

        # ── Testing ──────────────────────────────────────────────
        '@storybook/test': re.compile(
            r"""from\s+['"]@storybook/test['"]""",
            re.MULTILINE
        ),
        '@storybook/testing-library': re.compile(
            r"""from\s+['"]@storybook/testing-library['"]""",
            re.MULTILINE
        ),
        '@storybook/jest': re.compile(
            r"""from\s+['"]@storybook/jest['"]""",
            re.MULTILINE
        ),
        '@storybook/addon-interactions': re.compile(
            r"""['"]@storybook/addon-interactions['"]""",
            re.MULTILINE
        ),
        '@storybook/addon-test': re.compile(
            r"""['"]@storybook/addon-test['"]""",
            re.MULTILINE
        ),
        'chromatic': re.compile(
            r"""(?:from\s+['"]chromatic['"]|chromatic\s*:\s*\{)""",
            re.MULTILINE
        ),

        # ── Addons ────────────────────────────────────────────────
        '@storybook/addon-essentials': re.compile(
            r"""['"]@storybook/addon-essentials['"]""",
            re.MULTILINE
        ),
        '@storybook/addon-a11y': re.compile(
            r"""['"]@storybook/addon-a11y['"]""",
            re.MULTILINE
        ),
        '@storybook/addon-docs': re.compile(
            r"""['"]@storybook/addon-docs['"]""",
            re.MULTILINE
        ),
        '@storybook/addon-controls': re.compile(
            r"""['"]@storybook/addon-controls['"]""",
            re.MULTILINE
        ),
        '@storybook/addon-actions': re.compile(
            r"""['"]@storybook/addon-actions['"]""",
            re.MULTILINE
        ),
        '@storybook/addon-viewport': re.compile(
            r"""['"]@storybook/addon-viewport['"]""",
            re.MULTILINE
        ),
        '@storybook/addon-backgrounds': re.compile(
            r"""['"]@storybook/addon-backgrounds['"]""",
            re.MULTILINE
        ),
        '@storybook/addon-themes': re.compile(
            r"""['"]@storybook/addon-themes['"]""",
            re.MULTILINE
        ),
        '@storybook/addon-designs': re.compile(
            r"""['"]@storybook/addon-designs['"]""",
            re.MULTILINE
        ),
        '@storybook/addon-storysource': re.compile(
            r"""['"]@storybook/addon-storysource['"]""",
            re.MULTILINE
        ),
        '@storybook/addon-coverage': re.compile(
            r"""['"]@storybook/addon-coverage['"]""",
            re.MULTILINE
        ),

        # ── Builder ──────────────────────────────────────────────
        '@storybook/builder-vite': re.compile(
            r"""(?:['"]@storybook/builder-vite['"]|"""
            r"""builder\s*:\s*['"]@storybook/builder-vite)""",
            re.MULTILINE
        ),

        # ── API / Blocks ─────────────────────────────────────────
        '@storybook/blocks': re.compile(
            r"""from\s+['"]@storybook/blocks['"]""",
            re.MULTILINE
        ),
        '@storybook/theming': re.compile(
            r"""from\s+['"]@storybook/theming['"]""",
            re.MULTILINE
        ),
        '@storybook/manager-api': re.compile(
            r"""from\s+['"]@storybook/manager-api['"]""",
            re.MULTILINE
        ),
        '@storybook/preview-api': re.compile(
            r"""from\s+['"]@storybook/preview-api['"]""",
            re.MULTILINE
        ),
    }

    # Feature detection patterns
    FEATURE_PATTERNS = {
        'csf3': re.compile(r'(?:Story|StoryObj)\s*(?:<|=)', re.MULTILINE),
        'csf2': re.compile(r'Template\.bind\s*\(\s*\{', re.MULTILINE),
        'csf1': re.compile(r'export\s+const\s+\w+\s*=\s*\([^)]*\)\s*=>', re.MULTILINE),
        'stories_of': re.compile(r'storiesOf\s*\(', re.MULTILINE),
        'mdx': re.compile(r'<(?:Meta|Story|Canvas)\s', re.MULTILINE),
        'play_functions': re.compile(r'\bplay\s*:\s*(?:async\s+)?\(?', re.MULTILINE),
        'interaction_testing': re.compile(
            r'(?:userEvent|expect|within|step)\s*[\.(]', re.MULTILINE
        ),
        'portable_stories': re.compile(
            r'(?:composeStories?|setProjectAnnotations)\s*\(', re.MULTILINE
        ),
        'autodocs': re.compile(
            r"""tags\s*:\s*\[.*?['"]autodocs['"]""", re.DOTALL
        ),
        'decorators': re.compile(r'\bdecorators\s*:\s*\[', re.MULTILINE),
        'loaders': re.compile(r'\bloaders\s*:\s*\[', re.MULTILINE),
        'args': re.compile(r'\bargs\s*:\s*\{', re.MULTILINE),
        'arg_types': re.compile(r'\bargTypes\s*:\s*\{', re.MULTILINE),
        'parameters': re.compile(r'\bparameters\s*:\s*\{', re.MULTILINE),
        'render': re.compile(r'\brender\s*:\s*(?:\(|function)', re.MULTILINE),
        'tags': re.compile(r'\btags\s*:\s*\[', re.MULTILINE),
        'before_each': re.compile(r'\bbeforeEach\s*:', re.MULTILINE),
        'mount': re.compile(
            r'\bmount\s*\(', re.MULTILINE
        ),
        'global_types': re.compile(r'\bglobalTypes\s*:\s*\{', re.MULTILINE),
        'chromatic': re.compile(r'chromatic', re.MULTILINE),
        'vite_builder': re.compile(
            r"""(?:builder-vite|react-vite|vue3-vite|svelte-vite|html-vite|web-components-vite)""",
            re.MULTILINE
        ),
        'webpack_builder': re.compile(
            r"""(?:react-webpack5|vue3-webpack5|svelte-webpack5|html-webpack5|web-components-webpack5)""",
            re.MULTILINE
        ),
        'composition': re.compile(r'\brefs\s*:\s*\{', re.MULTILINE),
        'docs_blocks': re.compile(
            r'<(?:Description|Primary|Controls|Stories|Source|ArgTypes|ArgsTable)', re.MULTILINE
        ),
    }

    # Story file detection patterns
    STORY_FILE_PATTERNS = [
        re.compile(r'\.stories?\.[jt]sx?$', re.IGNORECASE),
        re.compile(r'\.stories?\.mdx$', re.IGNORECASE),
        re.compile(r'\.story\.[jt]sx?$', re.IGNORECASE),
    ]

    # Config file detection patterns
    CONFIG_FILE_PATTERNS = [
        re.compile(r'\.storybook/(?:main|preview|manager)\.[jt]sx?$'),
        re.compile(r'\.storybook/(?:main|preview|manager)\.m?[jt]s$'),
    ]

    def __init__(self):
        """Initialize the parser with all extractors."""
        self.story_extractor = StorybookStoryExtractor()
        self.component_extractor = StorybookComponentExtractor()
        self.addon_extractor = StorybookAddonExtractor()
        self.config_extractor = StorybookConfigExtractor()
        self.api_extractor = StorybookApiExtractor()

    def is_storybook_file(self, file_path: str, content: str = "") -> bool:
        """Check if a file contains Storybook code.

        Args:
            file_path: Path to the file.
            content: File content (optional, for content-based detection).

        Returns:
            True if the file is a Storybook file.
        """
        # Check file name patterns
        for pattern in self.STORY_FILE_PATTERNS:
            if pattern.search(file_path):
                return True

        for pattern in self.CONFIG_FILE_PATTERNS:
            if pattern.search(file_path):
                return True

        # Check content for Storybook imports
        if re.search(r"""from\s+['"]@storybook/""", content):
            return True

        # Check for storiesOf API
        if re.search(r'storiesOf\s*\(', content):
            return True

        # Check for MDX storybook components
        if re.search(r'<(?:Meta|Story|Canvas)\s', content):
            return True

        return False

    def parse(self, content: str, file_path: str = "") -> StorybookParseResult:
        """
        Parse source code for Storybook usage.

        Args:
            content: Source code content.
            file_path: Path to source file.

        Returns:
            StorybookParseResult with all extracted information.
        """
        result = StorybookParseResult(file_path=file_path)

        # Detect file type
        if file_path.endswith('.tsx'):
            result.file_type = "tsx"
        elif file_path.endswith('.ts') or file_path.endswith('.mts'):
            result.file_type = "ts"
        elif file_path.endswith('.jsx'):
            result.file_type = "jsx"
        elif file_path.endswith('.mdx'):
            result.file_type = "mdx"
        else:
            result.file_type = "js"

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect features
        result.detected_features = self._detect_features(content)

        # Detect version
        result.storybook_version = self._detect_version(content)

        # Detect CSF version
        result.csf_version = self._detect_csf_version(content)

        # Extract stories
        result.stories = self.story_extractor.extract(content, file_path)

        # Extract component documentation
        result.components = self.component_extractor.extract(content, file_path)

        # Extract addons (mainly from config files)
        result.addons = self.addon_extractor.extract(content, file_path)

        # Extract config (from .storybook/ config files)
        for pattern in self.CONFIG_FILE_PATTERNS:
            if pattern.search(file_path):
                result.configs = self.config_extractor.extract(content, file_path)
                break

        # Extract imports
        result.imports = self.api_extractor.extract_imports(content, file_path)

        # Extract testing patterns
        result.testing = self.api_extractor.extract_testing(content, file_path)

        # Set metadata flags
        result.has_play_functions = "play_functions" in result.detected_features
        result.has_interaction_testing = "interaction_testing" in result.detected_features
        result.has_portable_stories = "portable_stories" in result.detected_features
        result.has_chromatic = "chromatic" in result.detected_features
        result.has_autodocs = "autodocs" in result.detected_features

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Storybook ecosystem frameworks are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_features(self, content: str) -> List[str]:
        """Detect which Storybook features are used."""
        features = []
        for feature, pattern in self.FEATURE_PATTERNS.items():
            if pattern.search(content):
                features.append(feature)
        return features

    def _detect_version(self, content: str) -> str:
        """Detect Storybook version from content patterns."""
        # v8 indicators
        if any(kw in content for kw in [
            "@storybook/test", "beforeEach:", "mount(",
            "experimental-nextjs-vite", "addon-test",
            "setProjectAnnotations"
        ]):
            return "v8"

        # v7 indicators
        if any(kw in content for kw in [
            "react-vite", "vue3-vite", "svelte-vite",
            "react-webpack5", "vue3-webpack5",
            "StoryObj", "autodocs", "@storybook/blocks",
            "@storybook/testing-library",
        ]):
            return "v7"

        # v6 indicators
        if any(kw in content for kw in [
            "Template.bind", "@storybook/addon-essentials",
            "addon-controls", "addon-docs",
        ]):
            return "v6"

        # v5 indicators
        if any(kw in content for kw in [
            "storiesOf(", "addon-knobs", "addon-info",
            "@storybook/addons",
        ]):
            return "v5"

        return ""

    def _detect_csf_version(self, content: str) -> str:
        """Detect CSF (Component Story Format) version."""
        if re.search(r'<(?:Meta|Story|Canvas)\s', content):
            return "mdx"
        if re.search(r'storiesOf\s*\(', content):
            return "legacy"
        if re.search(r'(?:Story|StoryObj)\s*(?:<|=)', content):
            return "csf3"
        if re.search(r'Template\.bind\s*\(', content):
            return "csf2"
        if re.search(r'export\s+const\s+\w+\s*=\s*\(', content):
            return "csf1"
        return ""

    def _version_compare(self, v1: str, v2: str) -> int:
        """Compare version strings. Returns >0 if v1>v2, <0 if v1<v2, 0 if equal."""
        version_order = {"": 0, "v5": 5, "v6": 6, "v7": 7, "v8": 8}
        return version_order.get(v1, 0) - version_order.get(v2, 0)
