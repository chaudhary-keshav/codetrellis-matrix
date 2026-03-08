"""
Storybook Config Extractor for CodeTrellis

Extracts Storybook configuration from .storybook/ directory:
- main.{js,ts,mjs,cjs} — core configuration
- preview.{js,ts,jsx,tsx} — preview parameters, decorators, globalTypes
- manager.{js,ts} — manager UI customization
- Framework configuration (framework, builder)
- Stories glob patterns
- Static dirs
- Features and refs
- Webpack/Vite builder configuration
- TypeScript configuration
- Environment variables

Supports:
- Storybook 5.x (config.js, addons.js, webpack.config.js)
- Storybook 6.x (main.js + preview.js, CSF config)
- Storybook 7.x (main.ts + preview.ts, framework packages, vite builder)
- Storybook 8.x (main.ts + preview.ts, portable stories, project annotations)

Part of CodeTrellis v4.70 - Storybook Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StorybookConfigInfo:
    """Information about Storybook configuration."""
    config_type: str  # main, preview, manager, webpack, vite
    file: str = ""
    line_number: int = 0
    framework: str = ""  # @storybook/react-vite, @storybook/nextjs, etc.
    builder: str = ""  # webpack5, vite, etc.
    stories_globs: List[str] = field(default_factory=list)
    static_dirs: List[str] = field(default_factory=list)
    addons: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    refs: List[str] = field(default_factory=list)  # Composition refs
    env_vars: List[str] = field(default_factory=list)
    has_typescript: bool = False
    has_docs: bool = False  # docs: { autodocs: true }
    has_webpack_config: bool = False
    has_vite_config: bool = False
    has_babel_config: bool = False
    has_manager_head: bool = False
    has_preview_head: bool = False
    storybook_version: str = ""  # Detected or configured version


# ── Framework detection ────────────────────────────────────────────
FRAMEWORK_PATTERN = re.compile(
    r"""\bframework\s*:\s*(?:['"]([^"']+)['"]|\{\s*name\s*:\s*['"]([^"']+)['"])""",
    re.MULTILINE
)

# ── Builder detection ──────────────────────────────────────────────
BUILDER_PATTERN = re.compile(
    r"""\bbuilder\s*:\s*(?:['"]([^"']+)['"]|\{\s*name\s*:\s*['"]([^"']+)['"])""",
    re.MULTILINE
)

# ── Stories globs ──────────────────────────────────────────────────
STORIES_PATTERN = re.compile(
    r"""\bstories\s*:\s*\[([^\]]*)\]""",
    re.DOTALL
)

# ── Static dirs ────────────────────────────────────────────────────
STATIC_DIRS_PATTERN = re.compile(
    r"""\bstaticDirs\s*:\s*\[([^\]]*)\]""",
    re.DOTALL
)

# ── Addons array ────────────────────────────────────────────────────
ADDONS_PATTERN = re.compile(
    r"""\baddons\s*:\s*\[""",
    re.MULTILINE
)

# ── Features ────────────────────────────────────────────────────────
FEATURES_PATTERN = re.compile(
    r"""\bfeatures\s*:\s*\{([^}]*)\}""",
    re.DOTALL
)

# ── Refs (composition) ──────────────────────────────────────────────
REFS_PATTERN = re.compile(
    r"""\brefs\s*:\s*\{""",
    re.MULTILINE
)

# ── Docs autodocs ──────────────────────────────────────────────────
DOCS_AUTODOCS_PATTERN = re.compile(
    r"""\bdocs\s*:\s*\{[^}]*autodocs""",
    re.DOTALL
)

# ── TypeScript ──────────────────────────────────────────────────────
TYPESCRIPT_PATTERN = re.compile(
    r"""\btypescript\s*:\s*\{""",
    re.MULTILINE
)

# ── Environment variables ──────────────────────────────────────────
ENV_PATTERN = re.compile(
    r"""\benv\s*:\s*\(?\s*config\s*\)?\s*=>?\s*\{?\s*\(?""",
    re.MULTILINE
)

PROCESS_ENV_PATTERN = re.compile(
    r'process\.env\.(\w+)',
    re.MULTILINE
)

# ── Webpack config ──────────────────────────────────────────────────
WEBPACK_FINAL_PATTERN = re.compile(
    r'\bwebpackFinal\s*:',
    re.MULTILINE
)

# ── Vite config ────────────────────────────────────────────────────
VITE_FINAL_PATTERN = re.compile(
    r'\bviteFinal\s*:',
    re.MULTILINE
)

# ── Babel config ────────────────────────────────────────────────────
BABEL_PATTERN = re.compile(
    r'\bbabel\s*:',
    re.MULTILINE
)

# ── Manager/Preview head ──────────────────────────────────────────
MANAGER_HEAD_PATTERN = re.compile(r'\bmanagerHead\s*:', re.MULTILINE)
PREVIEW_HEAD_PATTERN = re.compile(r'\bpreviewHead\s*:', re.MULTILINE)

# ── Config file type detection ──────────────────────────────────────
CONFIG_FILE_TYPES = {
    "main": re.compile(r'main\.[jt]sx?$|main\.m?[jt]s$'),
    "preview": re.compile(r'preview\.[jt]sx?$|preview\.m?[jt]s$'),
    "manager": re.compile(r'manager\.[jt]sx?$|manager\.m?[jt]s$'),
}

# ── Version detection from imports ─────────────────────────────────
SB_VERSION_IMPORT_PATTERN = re.compile(
    r"""from\s+['"]@storybook/(\w[\w-]*)['"]""",
    re.MULTILINE
)

# Known Storybook framework packages
FRAMEWORK_PACKAGES = {
    "@storybook/react-vite": "react",
    "@storybook/react-webpack5": "react",
    "@storybook/vue3-vite": "vue3",
    "@storybook/vue3-webpack5": "vue3",
    "@storybook/angular": "angular",
    "@storybook/svelte-vite": "svelte",
    "@storybook/svelte-webpack5": "svelte",
    "@storybook/web-components-vite": "web-components",
    "@storybook/web-components-webpack5": "web-components",
    "@storybook/html-vite": "html",
    "@storybook/html-webpack5": "html",
    "@storybook/preact-vite": "preact",
    "@storybook/preact-webpack5": "preact",
    "@storybook/ember": "ember",
    "@storybook/nextjs": "nextjs",
    "@storybook/sveltekit": "sveltekit",
    "@storybook/experimental-nextjs-vite": "nextjs",
    "@storybook/nuxt": "nuxt",
    "@storybook/remix": "remix",
    # Legacy
    "@storybook/react": "react",
    "@storybook/vue": "vue",
    "@storybook/vue3": "vue3",
}


class StorybookConfigExtractor:
    """
    Extracts Storybook configuration from config files.

    Detects:
    - Framework and builder configuration
    - Stories glob patterns
    - Addon declarations
    - Feature flags
    - Static directories
    - Webpack/Vite final overrides
    - TypeScript configuration
    - Composition refs
    """

    def extract(self, content: str, file_path: str = "") -> List[StorybookConfigInfo]:
        """Extract Storybook config information.

        Args:
            content: File content to parse.
            file_path: Path to the file.

        Returns:
            List of StorybookConfigInfo objects.
        """
        results: List[StorybookConfigInfo] = []

        # Determine config type from filename
        config_type = self._detect_config_type(file_path)
        if not config_type:
            return results

        info = StorybookConfigInfo(
            config_type=config_type,
            file=file_path,
            line_number=1,
        )

        # Framework
        fw_match = FRAMEWORK_PATTERN.search(content)
        if fw_match:
            info.framework = fw_match.group(1) or fw_match.group(2) or ""

        # Builder
        builder_match = BUILDER_PATTERN.search(content)
        if builder_match:
            info.builder = builder_match.group(1) or builder_match.group(2) or ""
        elif info.framework:
            # Infer builder from framework package name
            if "vite" in info.framework:
                info.builder = "vite"
            elif "webpack5" in info.framework:
                info.builder = "webpack5"

        # Stories globs
        stories_match = STORIES_PATTERN.search(content)
        if stories_match:
            info.stories_globs = re.findall(r'["\']([^"\']+)["\']', stories_match.group(1))[:10]

        # Static dirs
        static_match = STATIC_DIRS_PATTERN.search(content)
        if static_match:
            info.static_dirs = re.findall(r'["\']([^"\']+)["\']', static_match.group(1))[:10]

        # Features
        features_match = FEATURES_PATTERN.search(content)
        if features_match:
            info.features = re.findall(r'(\w+)\s*:', features_match.group(1))[:10]

        # Refs
        if REFS_PATTERN.search(content):
            refs_body = self._extract_brace_body(content, REFS_PATTERN.search(content).start())
            info.refs = re.findall(r'["\']([^"\']+)["\']', refs_body)[:10]

        # Docs
        info.has_docs = bool(DOCS_AUTODOCS_PATTERN.search(content))

        # TypeScript
        info.has_typescript = bool(TYPESCRIPT_PATTERN.search(content))

        # Webpack
        info.has_webpack_config = bool(WEBPACK_FINAL_PATTERN.search(content))

        # Vite
        info.has_vite_config = bool(VITE_FINAL_PATTERN.search(content))

        # Babel
        info.has_babel_config = bool(BABEL_PATTERN.search(content))

        # Manager/Preview head
        info.has_manager_head = bool(MANAGER_HEAD_PATTERN.search(content))
        info.has_preview_head = bool(PREVIEW_HEAD_PATTERN.search(content))

        # Environment variables
        info.env_vars = list(set(PROCESS_ENV_PATTERN.findall(content)))[:10]

        # Version hint from framework package
        if info.framework:
            info.storybook_version = self._detect_version_hint(content, info.framework)

        results.append(info)
        return results

    def _detect_config_type(self, file_path: str) -> str:
        """Detect config file type from path."""
        if not file_path:
            return ""
        for config_type, pattern in CONFIG_FILE_TYPES.items():
            if pattern.search(file_path):
                return config_type
        return ""

    def _detect_version_hint(self, content: str, framework: str) -> str:
        """Detect Storybook version hint from content."""
        # v8 indicators
        if re.search(r'@storybook/test|tags\s*:\s*\[|beforeEach|portable\s*stories', content):
            return "v8"
        # v7 indicators
        if re.search(r'@storybook/\w+-(?:vite|webpack5)|autodocs|play\s*:', content):
            return "v7"
        # v6 indicators
        if re.search(r'@storybook/addon-essentials|Template\.bind', content):
            return "v6"
        return ""

    def _extract_brace_body(self, content: str, start: int) -> str:
        """Extract content within braces."""
        brace_start = content.find("{", start)
        if brace_start == -1:
            return ""
        depth = 0
        for i in range(brace_start, min(len(content), brace_start + 3000)):
            if content[i] == "{":
                depth += 1
            elif content[i] == "}":
                depth -= 1
                if depth == 0:
                    return content[brace_start:i + 1]
        return content[brace_start:brace_start + 1000]
