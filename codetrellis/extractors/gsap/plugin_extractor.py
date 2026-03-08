"""
GSAP Plugin Extractor — Plugins, registration, effects, utilities.

Extracts:
- gsap.registerPlugin() calls
- ScrollTrigger, MotionPath, Flip, Observer, Draggable, DrawSVG, MorphSVG,
  SplitText, ScrollSmoother, TextPlugin, PixiPlugin, EaselPlugin, Inertia,
  ScrambleText, CustomEase, CustomBounce, CustomWiggle, etc.
- gsap.registerEffect() custom effects
- gsap.utils.* utility usage
- gsap.parseEase() custom easing
- GSAP context and matchMedia (v3.11+)

v4.77: Full GSAP plugin support.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class GsapPluginInfo:
    """A GSAP plugin detected in the project."""
    name: str = ""                   # Plugin name (e.g., 'ScrollTrigger', 'Flip')
    file: str = ""
    line_number: int = 0
    plugin_type: str = ""            # 'free', 'club' (members-only), 'utility'
    is_registered: bool = False
    import_source: str = ""          # 'gsap', 'gsap/ScrollTrigger', CDN URL


@dataclass
class GsapRegistrationInfo:
    """A gsap.registerPlugin() call."""
    file: str = ""
    line_number: int = 0
    plugins: List[str] = field(default_factory=list)


@dataclass
class GsapEffectInfo:
    """A gsap.registerEffect() custom effect."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    has_defaults: bool = False
    has_extendTimeline: bool = False


@dataclass
class GsapUtilityInfo:
    """A gsap.utils.* usage."""
    name: str = ""                   # Utility name (e.g., 'toArray', 'clamp', 'wrap', 'mapRange')
    file: str = ""
    line_number: int = 0


# Known GSAP plugins with classification
GSAP_PLUGINS = {
    # Free plugins
    'ScrollTrigger': 'free',
    'Draggable': 'free',
    'MotionPathPlugin': 'free',
    'TextPlugin': 'free',
    'PixiPlugin': 'free',
    'EaselPlugin': 'free',
    'CSSRulePlugin': 'free',
    'Observer': 'free',
    'Flip': 'free',
    'ScrollToPlugin': 'free',
    # Club (Members-Only) plugins
    'DrawSVGPlugin': 'club',
    'MorphSVGPlugin': 'club',
    'SplitText': 'club',
    'ScrollSmoother': 'club',
    'InertiaPlugin': 'club',
    'ScrambleTextPlugin': 'club',
    'GSDevTools': 'club',
    'MotionPathHelper': 'club',
    'CustomEase': 'club',
    'CustomBounce': 'club',
    'CustomWiggle': 'club',
    'Physics2DPlugin': 'club',
    'PhysicsPropsPlugin': 'club',
    # Aliases
    'MotionPath': 'free',
    'Inertia': 'club',
    'ScrambleText': 'club',
    'DrawSVG': 'club',
    'MorphSVG': 'club',
}

# GSAP utility methods
GSAP_UTILS = [
    'toArray', 'selector', 'mapRange', 'pipe', 'clamp', 'wrap', 'wrapYoyo',
    'snap', 'normalize', 'getUnit', 'random', 'distribute', 'shuffle',
    'interpolate', 'unitize', 'splitColor', 'checkPrefix',
]


class GsapPluginExtractor:
    """
    Extracts GSAP plugin registrations, effects, and utility usage.
    """

    # gsap.registerPlugin(...)
    REGISTER_PLUGIN = re.compile(
        r'gsap\.registerPlugin\s*\(\s*([^)]+)\)',
        re.MULTILINE
    )

    # gsap.registerEffect(...)
    REGISTER_EFFECT = re.compile(
        r'gsap\.registerEffect\s*\(\s*\{[^}]*name\s*:\s*["\'](\w+)["\']',
        re.DOTALL
    )

    # Import patterns for plugins
    PLUGIN_IMPORT = re.compile(
        r"(?:import\s+\{?\s*([^}]*?)\s*\}?\s+from\s+['\"]([^'\"]*gsap[^'\"]*)['\"]"
        r"|require\s*\(\s*['\"]([^'\"]*gsap[^'\"]*)['\"])",
        re.MULTILINE
    )

    # CDN script tags
    CDN_PATTERN = re.compile(
        r'<script[^>]*src\s*=\s*["\']([^"\']*(?:gsap|greensock|TweenMax|ScrollTrigger)[^"\']*)["\']',
        re.IGNORECASE
    )

    # gsap.utils.* usage
    UTILS_PATTERN = re.compile(
        r'gsap\.utils\.(\w+)\s*\('
    )

    # gsap.parseEase()
    PARSE_EASE = re.compile(
        r'gsap\.parseEase\s*\('
    )

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract all GSAP plugin constructs."""
        plugins = []
        registrations = []
        effects = []
        utilities = []

        # ── Plugin registrations ────────────────────────────────
        for match in self.REGISTER_PLUGIN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            plugin_list = [p.strip() for p in match.group(1).split(',') if p.strip()]
            registrations.append(GsapRegistrationInfo(
                file=file_path,
                line_number=line_num,
                plugins=plugin_list,
            ))
            for p in plugin_list:
                p_clean = p.strip()
                plugin_type = GSAP_PLUGINS.get(p_clean, 'unknown')
                plugins.append(GsapPluginInfo(
                    name=p_clean,
                    file=file_path,
                    line_number=line_num,
                    plugin_type=plugin_type,
                    is_registered=True,
                    import_source='registered',
                ))

        # ── Plugin imports ──────────────────────────────────────
        for match in self.PLUGIN_IMPORT.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            names = match.group(1) or ''
            source = match.group(2) or match.group(3) or ''

            for name in names.split(','):
                name = name.strip().split(' as ')[0].strip()
                if name and name in GSAP_PLUGINS:
                    # Check if already detected via registration
                    already = any(p.name == name for p in plugins)
                    if not already:
                        plugins.append(GsapPluginInfo(
                            name=name,
                            file=file_path,
                            line_number=line_num,
                            plugin_type=GSAP_PLUGINS.get(name, 'unknown'),
                            is_registered=False,
                            import_source=source,
                        ))

        # ── CDN detection ───────────────────────────────────────
        for match in self.CDN_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            url = match.group(1)
            # Try to detect plugin name from URL
            for plugin_name in GSAP_PLUGINS:
                if plugin_name.lower() in url.lower():
                    plugins.append(GsapPluginInfo(
                        name=plugin_name,
                        file=file_path,
                        line_number=line_num,
                        plugin_type=GSAP_PLUGINS.get(plugin_name, 'unknown'),
                        is_registered=False,
                        import_source=url,
                    ))
                    break

        # ── Custom effects ──────────────────────────────────────
        for match in self.REGISTER_EFFECT.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            ctx = content[match.start():match.start() + 500]
            effects.append(GsapEffectInfo(
                name=match.group(1),
                file=file_path,
                line_number=line_num,
                has_defaults='defaults' in ctx,
                has_extendTimeline='extendTimeline' in ctx,
            ))

        # ── Utility usage ───────────────────────────────────────
        seen_utils = set()
        for match in self.UTILS_PATTERN.finditer(content):
            util_name = match.group(1)
            if util_name in seen_utils:
                continue
            seen_utils.add(util_name)
            line_num = content[:match.start()].count('\n') + 1
            utilities.append(GsapUtilityInfo(
                name=util_name,
                file=file_path,
                line_number=line_num,
            ))

        # Deduplicate plugins by name
        seen = set()
        unique_plugins = []
        for p in plugins:
            if p.name not in seen:
                seen.add(p.name)
                unique_plugins.append(p)

        return {
            'plugins': unique_plugins[:30],
            'registrations': registrations[:20],
            'effects': effects[:20],
            'utilities': utilities[:30],
        }
