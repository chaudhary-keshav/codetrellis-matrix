"""
Storybook API Extractor for CodeTrellis

Extracts Storybook API usage patterns:
- Import patterns from @storybook/* packages
- Testing utilities (@storybook/test, composeStories, composeStory)
- Interaction testing (within, userEvent, expect, step, fn, mock)
- Storybook hooks (useArgs, useChannel, useGlobals, useParameter)
- Portable stories API (composeStories, composeStory, setProjectAnnotations)
- Visual testing / Chromatic integration
- Storybook CLI commands (storybook dev, build, init, upgrade)
- Type imports (Meta, StoryObj, StoryFn, Decorator)

Supports:
- Storybook 5.x (@storybook/addons API)
- Storybook 6.x (@storybook/client-api, testing-library)
- Storybook 7.x (@storybook/testing-library, @storybook/jest)
- Storybook 8.x (@storybook/test, vitest, portable stories)

Part of CodeTrellis v4.70 - Storybook Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StorybookImportInfo:
    """Information about a Storybook import."""
    source: str  # Package name (e.g., "@storybook/react")
    file: str = ""
    line_number: int = 0
    named_imports: List[str] = field(default_factory=list)
    default_import: str = ""
    is_type_import: bool = False
    category: str = ""  # framework, addon, testing, types, api


@dataclass
class StorybookTestingInfo:
    """Information about Storybook testing usage."""
    name: str  # Testing function name
    file: str = ""
    line_number: int = 0
    testing_type: str = ""  # interaction, visual, unit, portable
    source_package: str = ""  # @storybook/test, @testing-library/react, etc.
    has_play: bool = False
    has_expect: bool = False
    has_user_event: bool = False
    has_within: bool = False
    has_step: bool = False
    has_fn_mock: bool = False
    has_compose_stories: bool = False
    has_chromatic: bool = False


# ── Import patterns ────────────────────────────────────────────────
STORYBOOK_IMPORT_PATTERN = re.compile(
    r"""(?:import\s+(?:type\s+)?(?:\{([^}]*)\}|(\w+))\s+from\s+['"](@storybook/[\w\-/]+)['"]|"""
    r"""import\s+(?:type\s+)?(?:(\w+)\s*,\s*)?\{([^}]*)\}\s+from\s+['"](@storybook/[\w\-/]+)['"])""",
    re.MULTILINE
)

# Require pattern for CJS
STORYBOOK_REQUIRE_PATTERN = re.compile(
    r"""(?:const|let|var)\s+\{([^}]*)\}\s*=\s*require\s*\(\s*['"](@storybook/[\w\-/]+)['"]\s*\)""",
    re.MULTILINE
)

# ── Type-only import detection ──────────────────────────────────────
TYPE_IMPORT_PATTERN = re.compile(
    r"""import\s+type\s+""",
    re.MULTILINE
)

# ── Storybook package categories ────────────────────────────────────
PACKAGE_CATEGORIES = {
    "framework": {
        "@storybook/react", "@storybook/vue3", "@storybook/angular",
        "@storybook/svelte", "@storybook/web-components", "@storybook/html",
        "@storybook/preact", "@storybook/ember", "@storybook/nextjs",
        "@storybook/sveltekit", "@storybook/nuxt",
        "@storybook/react-vite", "@storybook/react-webpack5",
        "@storybook/vue3-vite", "@storybook/vue3-webpack5",
        "@storybook/svelte-vite", "@storybook/experimental-nextjs-vite",
    },
    "testing": {
        "@storybook/test", "@storybook/testing-library",
        "@storybook/jest", "@storybook/addon-interactions",
        "@storybook/instrumenter", "@storybook/addon-coverage",
        "@storybook/addon-test",
    },
    "addon": {
        "@storybook/addon-essentials", "@storybook/addon-actions",
        "@storybook/addon-controls", "@storybook/addon-docs",
        "@storybook/addon-viewport", "@storybook/addon-backgrounds",
        "@storybook/addon-toolbars", "@storybook/addon-measure",
        "@storybook/addon-outline", "@storybook/addon-highlight",
        "@storybook/addon-links", "@storybook/addon-a11y",
        "@storybook/addon-storysource", "@storybook/addon-designs",
        "@storybook/addon-themes", "@storybook/addon-onboarding",
        "@storybook/addon-mdx-gfm",
    },
    "types": {
        "@storybook/types", "@storybook/csf",
    },
    "api": {
        "@storybook/manager-api", "@storybook/preview-api",
        "@storybook/addons", "@storybook/client-api",
        "@storybook/store", "@storybook/channels",
        "@storybook/theming", "@storybook/components",
        "@storybook/blocks", "@storybook/core-events",
    },
}

# ── Testing patterns ────────────────────────────────────────────────
COMPOSE_STORIES_PATTERN = re.compile(
    r'\bcomposeStories?\s*\(',
    re.MULTILINE
)

SET_PROJECT_ANNOTATIONS_PATTERN = re.compile(
    r'\bsetProjectAnnotations\s*\(',
    re.MULTILINE
)

EXPECT_PATTERN = re.compile(r'\bexpect\s*\(', re.MULTILINE)
USER_EVENT_PATTERN = re.compile(r'\buserEvent\s*\.', re.MULTILINE)
WITHIN_PATTERN = re.compile(r'\bwithin\s*\(', re.MULTILINE)
STEP_PATTERN = re.compile(r'\bstep\s*\(', re.MULTILINE)
FN_MOCK_PATTERN = re.compile(r'\b(?:fn|mock)\s*\(', re.MULTILINE)

# ── Chromatic / visual testing ──────────────────────────────────────
CHROMATIC_PATTERN = re.compile(
    r"""(?:from\s+['"]chromatic['"]|chromatic\s*:\s*\{|\.chromatic\.)""",
    re.MULTILINE
)

# ── Play function detection ──────────────────────────────────────────
PLAY_FUNCTION_PATTERN = re.compile(
    r'\bplay\s*:\s*(?:async\s+)?\(?\{?\s*(?:canvasElement|mount|step|args)',
    re.MULTILINE
)


class StorybookApiExtractor:
    """
    Extracts Storybook API usage patterns from source code.

    Detects:
    - @storybook/* imports and their categories
    - Testing utilities (interaction testing, portable stories)
    - Visual testing (Chromatic)
    - Storybook hooks and APIs
    - Type imports (Meta, StoryObj, etc.)
    """

    def extract(self, content: str, file_path: str = "") -> list:
        """Extract all Storybook API patterns (imports + testing).

        Args:
            content: File content to parse.
            file_path: Path to the file.

        Returns:
            Combined list of StorybookImportInfo and StorybookTestingInfo objects.
        """
        results: list = []
        results.extend(self.extract_imports(content, file_path))
        results.extend(self.extract_testing(content, file_path))
        return results

    def extract_imports(self, content: str, file_path: str = "") -> List[StorybookImportInfo]:
        """Extract Storybook import patterns.

        Args:
            content: File content to parse.
            file_path: Path to the file.

        Returns:
            List of StorybookImportInfo objects.
        """
        results: List[StorybookImportInfo] = []
        seen_sources: set = set()

        # ESM imports
        for m in STORYBOOK_IMPORT_PATTERN.finditer(content):
            named = m.group(1) or m.group(5) or ""
            default = m.group(2) or m.group(4) or ""
            source = m.group(3) or m.group(6) or ""

            if not source or source in seen_sources:
                continue
            seen_sources.add(source)

            named_list = [n.strip().split(" as ")[0].strip()
                          for n in named.split(",") if n.strip()] if named else []

            # Detect type import
            line_start = content.rfind("\n", 0, m.start()) + 1
            line = content[line_start:m.end()]
            is_type = bool(TYPE_IMPORT_PATTERN.match(line))

            info = StorybookImportInfo(
                source=source,
                file=file_path,
                line_number=content[:m.start()].count("\n") + 1,
                named_imports=named_list[:15],
                default_import=default,
                is_type_import=is_type,
                category=self._categorize_package(source),
            )
            results.append(info)

        # CJS requires
        for m in STORYBOOK_REQUIRE_PATTERN.finditer(content):
            named = m.group(1)
            source = m.group(2)
            if source in seen_sources:
                continue
            seen_sources.add(source)

            named_list = [n.strip().split(":")[0].strip()
                          for n in named.split(",") if n.strip()]

            info = StorybookImportInfo(
                source=source,
                file=file_path,
                line_number=content[:m.start()].count("\n") + 1,
                named_imports=named_list[:15],
                category=self._categorize_package(source),
            )
            results.append(info)

        return results

    def extract_testing(self, content: str, file_path: str = "") -> List[StorybookTestingInfo]:
        """Extract Storybook testing patterns.

        Args:
            content: File content to parse.
            file_path: Path to the file.

        Returns:
            List of StorybookTestingInfo objects.
        """
        results: List[StorybookTestingInfo] = []

        # Portable stories (composeStories / composeStory)
        if COMPOSE_STORIES_PATTERN.search(content):
            info = StorybookTestingInfo(
                name="composeStories",
                file=file_path,
                line_number=content[:COMPOSE_STORIES_PATTERN.search(content).start()].count("\n") + 1,
                testing_type="portable",
                source_package=self._find_import_source(content, "composeStories"),
                has_expect=bool(EXPECT_PATTERN.search(content)),
                has_compose_stories=True,
            )
            results.append(info)

        # setProjectAnnotations
        if SET_PROJECT_ANNOTATIONS_PATTERN.search(content):
            info = StorybookTestingInfo(
                name="setProjectAnnotations",
                file=file_path,
                line_number=content[:SET_PROJECT_ANNOTATIONS_PATTERN.search(content).start()].count("\n") + 1,
                testing_type="portable",
                source_package=self._find_import_source(content, "setProjectAnnotations"),
            )
            results.append(info)

        # Play function interaction testing
        play_match = PLAY_FUNCTION_PATTERN.search(content)
        if play_match:
            info = StorybookTestingInfo(
                name="play",
                file=file_path,
                line_number=content[:play_match.start()].count("\n") + 1,
                testing_type="interaction",
                has_play=True,
                has_expect=bool(EXPECT_PATTERN.search(content)),
                has_user_event=bool(USER_EVENT_PATTERN.search(content)),
                has_within=bool(WITHIN_PATTERN.search(content)),
                has_step=bool(STEP_PATTERN.search(content)),
                has_fn_mock=bool(FN_MOCK_PATTERN.search(content)),
            )
            results.append(info)

        # Chromatic visual testing
        if CHROMATIC_PATTERN.search(content):
            info = StorybookTestingInfo(
                name="chromatic",
                file=file_path,
                line_number=content[:CHROMATIC_PATTERN.search(content).start()].count("\n") + 1,
                testing_type="visual",
                source_package="chromatic",
                has_chromatic=True,
            )
            results.append(info)

        return results

    def _categorize_package(self, package: str) -> str:
        """Categorize a @storybook package."""
        for category, packages in PACKAGE_CATEGORIES.items():
            if package in packages:
                return category
        if "addon" in package:
            return "addon"
        return "api"

    def _find_import_source(self, content: str, name: str) -> str:
        """Find the import source for a given name."""
        pattern = re.compile(
            r"""from\s+['"]([^"']+)['"]\s*""",
            re.MULTILINE
        )
        for m in pattern.finditer(content):
            line_start = content.rfind("\n", 0, m.start()) + 1
            line = content[line_start:m.end()]
            if name in line:
                return m.group(1)
        return ""
