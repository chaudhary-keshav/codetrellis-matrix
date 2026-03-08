"""
Astro Island Extractor v1.0

Extracts island architecture (partial hydration) information from Astro files:
- client:load — Hydrate immediately on page load
- client:idle — Hydrate when the browser is idle (requestIdleCallback)
- client:visible — Hydrate when the component enters the viewport (IntersectionObserver)
- client:media — Hydrate when a media query matches
- client:only — Skip SSR, render only on client (requires framework hint)
- Framework component detection (React, Vue, Svelte, Solid, Preact, Lit, Alpine)
- Island counts and hydration strategy analysis

Supports Astro v1.x - v5.x island architecture.

Part of CodeTrellis v4.60 - Astro Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class AstroIslandInfo:
    """Information about a client-side island in an Astro file."""
    component_name: str = ""
    directive: str = ""  # client:load, client:idle, client:visible, client:media, client:only
    line_number: int = 0
    framework: str = ""  # react, vue, svelte, solid, preact, lit, alpine
    media_query: str = ""  # For client:media="(max-width: 768px)"
    only_framework: str = ""  # For client:only="react"
    has_props: bool = False
    is_in_slot: bool = False


class AstroIslandExtractor:
    """Extracts island architecture information from Astro files."""

    # Client directive patterns
    CLIENT_LOAD = re.compile(
        r'<([A-Z][a-zA-Z0-9.]*)\s+[^>]*?client:load\b',
        re.MULTILINE | re.DOTALL
    )
    CLIENT_IDLE = re.compile(
        r'<([A-Z][a-zA-Z0-9.]*)\s+[^>]*?client:idle\b',
        re.MULTILINE | re.DOTALL
    )
    CLIENT_VISIBLE = re.compile(
        r'<([A-Z][a-zA-Z0-9.]*)\s+[^>]*?client:visible\b',
        re.MULTILINE | re.DOTALL
    )
    CLIENT_MEDIA = re.compile(
        r'<([A-Z][a-zA-Z0-9.]*)\s+[^>]*?client:media\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE | re.DOTALL
    )
    CLIENT_ONLY = re.compile(
        r'<([A-Z][a-zA-Z0-9.]*)\s+[^>]*?client:only\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE | re.DOTALL
    )

    # Generic client directive (any)
    CLIENT_ANY = re.compile(
        r'<([A-Z][a-zA-Z0-9.]*)\s+[^>]*?client:(\w+)\b(?:\s*=\s*["\']([^"\']*)["\'])?',
        re.MULTILINE | re.DOTALL
    )

    # Framework detection from imports in frontmatter
    FRAMEWORK_IMPORTS = {
        'react': re.compile(
            r"from\s+['\"](?:react|@/components/.*\.(?:jsx|tsx))['\"]|"
            r"\.(?:jsx|tsx)['\"]",
            re.MULTILINE
        ),
        'vue': re.compile(
            r"from\s+['\"].*\.vue['\"]|from\s+['\"]vue['\"]",
            re.MULTILINE
        ),
        'svelte': re.compile(
            r"from\s+['\"].*\.svelte['\"]|from\s+['\"]svelte['\"]",
            re.MULTILINE
        ),
        'solid': re.compile(
            r"from\s+['\"]solid-js['\"]|\.solid\.[jt]sx?['\"]",
            re.MULTILINE
        ),
        'preact': re.compile(
            r"from\s+['\"]preact['\"]",
            re.MULTILINE
        ),
        'lit': re.compile(
            r"from\s+['\"]lit['\"]|from\s+['\"]@lit/",
            re.MULTILINE
        ),
        'alpine': re.compile(
            r"from\s+['\"]alpinejs['\"]|x-data\b",
            re.MULTILINE
        ),
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract island architecture information from an Astro file.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with island information
        """
        islands: List[AstroIslandInfo] = []

        # Split frontmatter and template
        frontmatter, template = self._split_frontmatter(content)

        # Detect frameworks used in this file
        frameworks_used = self._detect_frameworks(frontmatter)

        # Frontmatter line count for line offset
        fm_lines = frontmatter.count('\n') + 2 if frontmatter else 0

        # Extract all client directives
        for m in self.CLIENT_ANY.finditer(template):
            comp_name = m.group(1)
            directive_type = m.group(2)  # load, idle, visible, media, only
            directive_value = m.group(3) or ""
            line = template[:m.start()].count('\n') + fm_lines + 1

            island = AstroIslandInfo(
                component_name=comp_name,
                directive=f"client:{directive_type}",
                line_number=line,
            )

            # Set framework-specific data
            if directive_type == "media":
                island.media_query = directive_value
            elif directive_type == "only":
                island.only_framework = directive_value
                island.framework = directive_value

            # Detect framework from component name / imports
            if not island.framework:
                island.framework = self._guess_framework(comp_name, frontmatter, frameworks_used)

            # Check if component has props
            # Look for attributes after the component name
            tag_region = template[m.start():m.start() + 300]
            if re.search(r'\b\w+\s*=\s*[{"\']', tag_region):
                island.has_props = True

            islands.append(island)

        return {"islands": islands}

    def _split_frontmatter(self, content: str) -> tuple:
        """Split an Astro file into frontmatter and template sections."""
        fm_pattern = re.compile(r'^---\s*\n(.*?)\n---', re.DOTALL)
        match = fm_pattern.search(content)
        if match:
            return match.group(1), content[match.end():]
        return "", content

    def _detect_frameworks(self, frontmatter: str) -> List[str]:
        """Detect UI frameworks from import statements."""
        detected: List[str] = []
        for fw, pattern in self.FRAMEWORK_IMPORTS.items():
            if pattern.search(frontmatter):
                detected.append(fw)
        return detected

    def _guess_framework(self, comp_name: str, frontmatter: str,
                         frameworks_used: List[str]) -> str:
        """Guess framework for a component based on imports and context."""
        # Check if the component is imported from a framework-specific path
        import_pattern = re.compile(
            rf"import\s+(?:\{{[^}}]*\}}|{re.escape(comp_name)})\s+from\s+['\"]([^'\"]+)['\"]",
            re.MULTILINE
        )
        for m in import_pattern.finditer(frontmatter):
            source = m.group(1)
            if source.endswith('.tsx') or source.endswith('.jsx'):
                return 'react'
            if source.endswith('.vue'):
                return 'vue'
            if source.endswith('.svelte'):
                return 'svelte'

        # If only one framework is used, assume it's that
        if len(frameworks_used) == 1:
            return frameworks_used[0]

        return ""
