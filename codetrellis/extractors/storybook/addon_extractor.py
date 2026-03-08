"""
Storybook Addon Extractor for CodeTrellis

Extracts Storybook addon configurations and usage:
- Addon registrations in main.{js,ts} (addons array)
- Addon-specific parameters in stories
- Custom addon panels/tabs
- Decorator-based addons
- Tool registration (toolbar items)
- ArgTypes enhancers
- Global types (globalTypes)

Supports:
- Storybook 5.x (addon-knobs, addon-actions, addon-links)
- Storybook 6.x (addon-essentials, addon-controls, addon-docs)
- Storybook 7.x (addon-interactions, addon-coverage, addon-designs)
- Storybook 8.x (addon-test, addon-vitest, visual tests)

Part of CodeTrellis v4.70 - Storybook Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StorybookAddonInfo:
    """Information about a Storybook addon."""
    name: str  # Addon package name (e.g., "@storybook/addon-essentials")
    file: str = ""
    line_number: int = 0
    addon_type: str = ""  # registration, parameter, decorator, panel, tool
    is_official: bool = False  # @storybook/ namespace
    is_essential: bool = False  # Part of addon-essentials
    has_options: bool = False  # Configured with options
    options_keys: List[str] = field(default_factory=list)
    short_name: str = ""  # Human-friendly name


# ── Official Storybook addons ──────────────────────────────────────
OFFICIAL_ADDONS = {
    "@storybook/addon-essentials",
    "@storybook/addon-actions",
    "@storybook/addon-controls",
    "@storybook/addon-docs",
    "@storybook/addon-viewport",
    "@storybook/addon-backgrounds",
    "@storybook/addon-toolbars",
    "@storybook/addon-measure",
    "@storybook/addon-outline",
    "@storybook/addon-highlight",
    "@storybook/addon-interactions",
    "@storybook/addon-links",
    "@storybook/addon-a11y",
    "@storybook/addon-storysource",
    "@storybook/addon-designs",
    "@storybook/addon-coverage",
    "@storybook/addon-test",
    "@storybook/addon-themes",
    "@storybook/addon-onboarding",
    "@storybook/addon-mdx-gfm",
}

# ── Essential sub-addons (included in addon-essentials) ───────────
ESSENTIAL_ADDONS = {
    "@storybook/addon-essentials",
    "@storybook/addon-actions",
    "@storybook/addon-controls",
    "@storybook/addon-docs",
    "@storybook/addon-viewport",
    "@storybook/addon-backgrounds",
    "@storybook/addon-toolbars",
    "@storybook/addon-measure",
    "@storybook/addon-outline",
    "@storybook/addon-highlight",
}

# ── Addon in addons array ──────────────────────────────────────────
# addons: ['@storybook/addon-essentials', ...]
# addons: [{ name: '@storybook/addon-docs', options: { ... } }, ...]
ADDON_STRING_PATTERN = re.compile(
    r"""['"](@?[\w\-/.]+(?:/[\w\-]+)*)['"]""",
    re.MULTILINE
)

ADDON_OBJECT_PATTERN = re.compile(
    r"""\{\s*name\s*:\s*['"]([^"']+)['"]""",
    re.MULTILINE
)

# ── Addons array in config ────────────────────────────────────────
ADDONS_ARRAY_PATTERN = re.compile(
    r'addons\s*:\s*\[',
    re.MULTILINE
)

# ── Options keys in addon object ──────────────────────────────────
OPTIONS_PATTERN = re.compile(
    r'options\s*:\s*\{([^}]*)\}',
    re.DOTALL
)

# ── Global types (toolbar items) ──────────────────────────────────
GLOBAL_TYPES_PATTERN = re.compile(
    r'\bglobalTypes\s*:\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
    re.DOTALL
)

# ── Custom panel/tab registration ──────────────────────────────────
ADDON_PANEL_PATTERN = re.compile(
    r'addons\.register\s*\(\s*["\']([^"\']+)["\']',
    re.MULTILINE
)

# ── makeDecorator (custom decorator addon) ─────────────────────────
MAKE_DECORATOR_PATTERN = re.compile(
    r'makeDecorator\s*\(\s*\{[^}]*name\s*:\s*["\']([^"\']+)["\']',
    re.DOTALL
)


class StorybookAddonExtractor:
    """
    Extracts Storybook addon configurations and registrations.

    Detects:
    - Addon declarations in main.{js,ts} addons array
    - Addon-specific options
    - Official vs community addons
    - Essential addon sub-packages
    - Custom panel/tab registrations
    - Toolbar items (globalTypes)
    """

    def extract(self, content: str, file_path: str = "") -> List[StorybookAddonInfo]:
        """Extract addon configurations from source code.

        Args:
            content: File content to parse.
            file_path: Path to the file.

        Returns:
            List of StorybookAddonInfo objects.
        """
        results: List[StorybookAddonInfo] = []
        seen: set = set()

        # Find addons array
        addons_match = ADDONS_ARRAY_PATTERN.search(content)
        if addons_match:
            # Extract the addons array content
            start = addons_match.start()
            array_body = self._extract_bracket_body(content, start)

            # Object addons with options (check FIRST to get has_options)
            for m in ADDON_OBJECT_PATTERN.finditer(array_body):
                addon_name = m.group(1)
                if addon_name in seen or not self._is_addon_name(addon_name):
                    continue
                seen.add(addon_name)

                info = StorybookAddonInfo(
                    name=addon_name,
                    file=file_path,
                    line_number=content[:start + m.start()].count("\n") + 1,
                    addon_type="registration",
                    is_official=addon_name in OFFICIAL_ADDONS,
                    is_essential=addon_name in ESSENTIAL_ADDONS,
                    has_options=True,
                    short_name=self._get_short_name(addon_name),
                )

                # Extract options keys
                obj_start = m.start()
                obj_body = array_body[obj_start:]
                opts_match = OPTIONS_PATTERN.search(obj_body)
                if opts_match:
                    info.options_keys = re.findall(r'(\w+)\s*:', opts_match.group(1))[:10]

                results.append(info)

            # String addons
            for m in ADDON_STRING_PATTERN.finditer(array_body):
                addon_name = m.group(1)
                if addon_name in seen or not self._is_addon_name(addon_name):
                    continue
                seen.add(addon_name)

                info = StorybookAddonInfo(
                    name=addon_name,
                    file=file_path,
                    line_number=content[:start + m.start()].count("\n") + 1,
                    addon_type="registration",
                    is_official=addon_name in OFFICIAL_ADDONS,
                    is_essential=addon_name in ESSENTIAL_ADDONS,
                    short_name=self._get_short_name(addon_name),
                )
                results.append(info)

        # Custom panel registrations
        for m in ADDON_PANEL_PATTERN.finditer(content):
            panel_id = m.group(1)
            if panel_id not in seen:
                seen.add(panel_id)
                results.append(StorybookAddonInfo(
                    name=panel_id,
                    file=file_path,
                    line_number=content[:m.start()].count("\n") + 1,
                    addon_type="panel",
                    short_name=panel_id.split("/")[-1] if "/" in panel_id else panel_id,
                ))

        # makeDecorator addons
        for m in MAKE_DECORATOR_PATTERN.finditer(content):
            dec_name = m.group(1)
            if dec_name not in seen:
                seen.add(dec_name)
                results.append(StorybookAddonInfo(
                    name=dec_name,
                    file=file_path,
                    line_number=content[:m.start()].count("\n") + 1,
                    addon_type="decorator",
                    short_name=dec_name,
                ))

        return results

    def _extract_bracket_body(self, content: str, start: int) -> str:
        """Extract content within brackets starting from a position."""
        bracket_start = content.find("[", start)
        if bracket_start == -1:
            return ""
        depth = 0
        for i in range(bracket_start, min(len(content), bracket_start + 5000)):
            if content[i] == "[":
                depth += 1
            elif content[i] == "]":
                depth -= 1
                if depth == 0:
                    return content[bracket_start:i + 1]
        return content[bracket_start:bracket_start + 2000]

    def _is_addon_name(self, name: str) -> bool:
        """Check if a string looks like an addon package name."""
        if name.startswith("@storybook/addon-"):
            return True
        if name.startswith("storybook-addon-"):
            return True
        if name.startswith("@") and "addon" in name.lower():
            return True
        # Community addons or relative paths
        if name.startswith("./") or name.startswith("../"):
            return True
        # Known community addon patterns
        if any(kw in name.lower() for kw in ("addon", "storybook", "chromatic")):
            return True
        return False

    def _get_short_name(self, name: str) -> str:
        """Get a human-friendly short name from an addon package name."""
        # @storybook/addon-essentials -> essentials
        if name.startswith("@storybook/addon-"):
            return name[len("@storybook/addon-"):]
        if name.startswith("storybook-addon-"):
            return name[len("storybook-addon-"):]
        return name.split("/")[-1]
