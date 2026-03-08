"""
Chart.js Plugin Extractor

Extracts plugin definitions and configurations:
- Plugin registration (Chart.register, Chart.plugins.register)
- Built-in plugins (tooltip, legend, title, subtitle, filler, decimation)
- Ecosystem plugins (chartjs-plugin-datalabels, zoom, annotation, streaming, gradient)
- Custom inline plugins (id + hooks: beforeDraw, afterDraw, etc.)
- Plugin options configuration
- Plugin lifecycle hooks
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ChartPluginInfo:
    """Chart.js plugin definition."""
    name: str  # plugin name or id
    file: str
    line_number: int
    plugin_type: str  # 'builtin', 'ecosystem', 'custom', 'inline'
    plugin_id: str = ""  # plugin id property
    has_options: bool = False
    is_registered: bool = False
    hooks: List[str] = field(default_factory=list)  # lifecycle hooks used
    options_keys: List[str] = field(default_factory=list)


@dataclass
class ChartPluginRegistrationInfo:
    """Chart.js plugin registration call."""
    name: str
    file: str
    line_number: int
    registration_method: str  # 'register', 'plugins_register', 'plugins_array'
    registered_items: List[str] = field(default_factory=list)  # items being registered


class ChartPluginExtractor:
    """Extracts Chart.js plugin constructs."""

    # ── Plugin registration patterns ──────────────────────────────
    # v3+: Chart.register(LineElement, PointElement, LineController, ...)
    # Also handles aliases like ChartJS.register(...) common in React
    CHART_REGISTER_PATTERN = re.compile(
        r'(?:Chart|ChartJS)\.register\s*\(([^)]*)\)',
        re.MULTILINE | re.DOTALL
    )
    # v2: Chart.plugins.register(plugin)
    PLUGINS_REGISTER_PATTERN = re.compile(
        r'(?:Chart|ChartJS)\.plugins\.register\s*\(([^)]*)\)',
        re.MULTILINE
    )
    # v3+ registerables: Chart.register(...registerables)
    REGISTERABLES_PATTERN = re.compile(
        r'(?:Chart|ChartJS)\.register\s*\(\s*\.\.\.registerables\s*\)',
        re.MULTILINE
    )

    # ── Built-in plugin option patterns ───────────────────────────
    # Tooltip plugin
    TOOLTIP_PATTERN = re.compile(
        r'(?:plugins\s*:\s*\{[^}]*?)?tooltip\s*:\s*\{',
        re.MULTILINE | re.DOTALL
    )
    TOOLTIP_OPTIONS_PATTERN = re.compile(
        r'(enabled|mode|intersect|position|callbacks|backgroundColor|'
        r'titleColor|titleFont|bodyColor|bodyFont|footerColor|footerFont|'
        r'padding|caretPadding|caretSize|cornerRadius|displayColors|'
        r'borderColor|borderWidth|multiKeyBackground|titleAlign|'
        r'bodyAlign|footerAlign|xAlign|yAlign|filter|itemSort|'
        r'external|usePointStyle|boxWidth|boxHeight|boxPadding)\s*:',
        re.MULTILINE
    )

    # Legend plugin
    LEGEND_PATTERN = re.compile(
        r'(?:plugins\s*:\s*\{[^}]*?)?legend\s*:\s*\{',
        re.MULTILINE | re.DOTALL
    )
    LEGEND_OPTIONS_PATTERN = re.compile(
        r'(display|position|align|labels|onClick|onHover|onLeave|'
        r'reverse|fullSize|title|maxHeight|maxWidth)\s*:',
        re.MULTILINE
    )

    # Title plugin
    TITLE_PATTERN = re.compile(
        r'(?:plugins\s*:\s*\{[^}]*?)?title\s*:\s*\{',
        re.MULTILINE | re.DOTALL
    )
    TITLE_OPTIONS_PATTERN = re.compile(
        r'(display|text|align|position|color|font|fullSize|padding)\s*:',
        re.MULTILINE
    )

    # Subtitle plugin
    SUBTITLE_PATTERN = re.compile(
        r'subtitle\s*:\s*\{',
        re.MULTILINE
    )

    # ── Ecosystem plugin patterns ─────────────────────────────────
    ECOSYSTEM_PLUGINS = {
        'datalabels': re.compile(
            r"""(?:from\s+['"]chartjs-plugin-datalabels['"]|"""
            r"""require\s*\(\s*['"]chartjs-plugin-datalabels['"]|"""
            r"""ChartDataLabels\b)""",
            re.MULTILINE
        ),
        'zoom': re.compile(
            r"""(?:from\s+['"]chartjs-plugin-zoom['"]|"""
            r"""require\s*\(\s*['"]chartjs-plugin-zoom['"])""",
            re.MULTILINE
        ),
        'annotation': re.compile(
            r"""(?:from\s+['"]chartjs-plugin-annotation['"]|"""
            r"""require\s*\(\s*['"]chartjs-plugin-annotation['"])""",
            re.MULTILINE
        ),
        'streaming': re.compile(
            r"""(?:from\s+['"]chartjs-plugin-streaming['"]|"""
            r"""require\s*\(\s*['"]chartjs-plugin-streaming['"])""",
            re.MULTILINE
        ),
        'gradient': re.compile(
            r"""(?:from\s+['"]chartjs-plugin-gradient['"]|"""
            r"""require\s*\(\s*['"]chartjs-plugin-gradient['"])""",
            re.MULTILINE
        ),
        'crosshair': re.compile(
            r"""(?:from\s+['"]chartjs-plugin-crosshair['"]|"""
            r"""require\s*\(\s*['"]chartjs-plugin-crosshair['"])""",
            re.MULTILINE
        ),
        'deferred': re.compile(
            r"""(?:from\s+['"]chartjs-plugin-deferred['"]|"""
            r"""require\s*\(\s*['"]chartjs-plugin-deferred['"])""",
            re.MULTILINE
        ),
        'stacked100': re.compile(
            r"""(?:from\s+['"]chartjs-plugin-stacked100['"]|"""
            r"""require\s*\(\s*['"]chartjs-plugin-stacked100['"])""",
            re.MULTILINE
        ),
        'draggable': re.compile(
            r"""(?:from\s+['"]chartjs-plugin-dragdata['"]|"""
            r"""require\s*\(\s*['"]chartjs-plugin-dragdata['"])""",
            re.MULTILINE
        ),
        'colorschemes': re.compile(
            r"""(?:from\s+['"]chartjs-plugin-colorschemes['"]|"""
            r"""require\s*\(\s*['"]chartjs-plugin-colorschemes['"])""",
            re.MULTILINE
        ),
    }

    # ── Custom inline plugin patterns ─────────────────────────────
    # { id: 'myPlugin', beforeDraw(chart) { ... } }
    CUSTOM_PLUGIN_ID_PATTERN = re.compile(
        r"""id\s*:\s*['"](\w+)['"]""",
        re.MULTILINE
    )

    # Plugin lifecycle hooks
    PLUGIN_HOOKS = [
        'beforeInit', 'afterInit', 'beforeUpdate', 'afterUpdate',
        'beforeLayout', 'afterLayout', 'beforeDatasetsDraw', 'afterDatasetsDraw',
        'beforeDraw', 'afterDraw', 'beforeDatasetDraw', 'afterDatasetDraw',
        'beforeEvent', 'afterEvent', 'beforeDestroy', 'afterDestroy',
        'resize', 'reset', 'beforeElementsUpdate',
        'beforeDatasetsUpdate', 'afterDatasetsUpdate',
        'beforeRender', 'afterRender',
        'beforeTooltipDraw', 'afterTooltipDraw',
        'install', 'start', 'stop', 'uninstall',
    ]

    HOOK_PATTERN = re.compile(
        r'(beforeInit|afterInit|beforeUpdate|afterUpdate|'
        r'beforeLayout|afterLayout|beforeDatasetsDraw|afterDatasetsDraw|'
        r'beforeDraw|afterDraw|beforeDatasetDraw|afterDatasetDraw|'
        r'beforeEvent|afterEvent|beforeDestroy|afterDestroy|'
        r'resize|reset|beforeElementsUpdate|'
        r'beforeDatasetsUpdate|afterDatasetsUpdate|'
        r'beforeRender|afterRender|'
        r'beforeTooltipDraw|afterTooltipDraw|'
        r'install|start|stop|uninstall)\s*[:(]',
        re.MULTILINE
    )

    # ── Plugins array in config ───────────────────────────────────
    PLUGINS_ARRAY_PATTERN = re.compile(
        r'plugins\s*:\s*\[',
        re.MULTILINE
    )
    # Plugins option object in config
    PLUGINS_OPTION_PATTERN = re.compile(
        r'plugins\s*:\s*\{',
        re.MULTILINE
    )

    # ── Filler plugin detection ───────────────────────────────────
    FILLER_PATTERN = re.compile(
        r'(?:Filler\b|propagate\s*:\s*true)',
        re.MULTILINE
    )

    # ── Decimation plugin detection ───────────────────────────────
    DECIMATION_PATTERN = re.compile(
        r'(?:Decimation\b|decimation\s*:\s*\{)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract plugin constructs from Chart.js code."""
        result: Dict[str, Any] = {
            'plugins': [],
            'registrations': [],
        }

        # ── Chart.register() calls ───────────────────────────────
        for match in self.CHART_REGISTER_PATTERN.finditer(content):
            items_str = match.group(1).strip()
            line_num = content[:match.start()].count('\n') + 1
            items = [s.strip() for s in items_str.split(',') if s.strip()]
            # Remove spread operator
            items = [i.lstrip('.') for i in items]
            result['registrations'].append(ChartPluginRegistrationInfo(
                name='Chart.register',
                file=file_path,
                line_number=line_num,
                registration_method='register',
                registered_items=items[:20],
            ))

        # Registerables
        for match in self.REGISTERABLES_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['registrations'].append(ChartPluginRegistrationInfo(
                name='registerables',
                file=file_path,
                line_number=line_num,
                registration_method='register',
                registered_items=['...registerables'],
            ))

        # v2 plugin registration
        for match in self.PLUGINS_REGISTER_PATTERN.finditer(content):
            items_str = match.group(1).strip()
            line_num = content[:match.start()].count('\n') + 1
            result['registrations'].append(ChartPluginRegistrationInfo(
                name='Chart.plugins.register',
                file=file_path,
                line_number=line_num,
                registration_method='plugins_register',
                registered_items=[items_str] if items_str else [],
            ))

        # ── Built-in plugins ─────────────────────────────────────
        # Tooltip
        for match in self.TOOLTIP_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            after = content[match.start():match.start() + 800]
            options = [m.group(1) for m in self.TOOLTIP_OPTIONS_PATTERN.finditer(after)]
            has_callback = bool(re.search(r'callbacks\s*:', after))
            result['plugins'].append(ChartPluginInfo(
                name='tooltip',
                file=file_path,
                line_number=line_num,
                plugin_type='builtin',
                plugin_id='tooltip',
                has_options=bool(options),
                hooks=['beforeTooltipDraw'] if has_callback else [],
                options_keys=options[:15],
            ))

        # Legend
        for match in self.LEGEND_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            after = content[match.start():match.start() + 500]
            options = [m.group(1) for m in self.LEGEND_OPTIONS_PATTERN.finditer(after)]
            result['plugins'].append(ChartPluginInfo(
                name='legend',
                file=file_path,
                line_number=line_num,
                plugin_type='builtin',
                plugin_id='legend',
                has_options=bool(options),
                options_keys=options[:10],
            ))

        # Title
        for match in self.TITLE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            after = content[match.start():match.start() + 300]
            options = [m.group(1) for m in self.TITLE_OPTIONS_PATTERN.finditer(after)]
            result['plugins'].append(ChartPluginInfo(
                name='title',
                file=file_path,
                line_number=line_num,
                plugin_type='builtin',
                plugin_id='title',
                has_options=bool(options),
                options_keys=options[:10],
            ))

        # Subtitle
        for match in self.SUBTITLE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            result['plugins'].append(ChartPluginInfo(
                name='subtitle',
                file=file_path,
                line_number=line_num,
                plugin_type='builtin',
                plugin_id='subtitle',
            ))

        # Filler
        if self.FILLER_PATTERN.search(content):
            match = self.FILLER_PATTERN.search(content)
            line_num = content[:match.start()].count('\n') + 1
            result['plugins'].append(ChartPluginInfo(
                name='filler',
                file=file_path,
                line_number=line_num,
                plugin_type='builtin',
                plugin_id='filler',
            ))

        # Decimation
        if self.DECIMATION_PATTERN.search(content):
            match = self.DECIMATION_PATTERN.search(content)
            line_num = content[:match.start()].count('\n') + 1
            result['plugins'].append(ChartPluginInfo(
                name='decimation',
                file=file_path,
                line_number=line_num,
                plugin_type='builtin',
                plugin_id='decimation',
            ))

        # ── Ecosystem plugins ────────────────────────────────────
        for plugin_name, pattern in self.ECOSYSTEM_PLUGINS.items():
            if pattern.search(content):
                match = pattern.search(content)
                line_num = content[:match.start()].count('\n') + 1
                result['plugins'].append(ChartPluginInfo(
                    name=plugin_name,
                    file=file_path,
                    line_number=line_num,
                    plugin_type='ecosystem',
                    plugin_id=plugin_name,
                    is_registered=True,
                ))

        # ── Custom inline plugins ────────────────────────────────
        # Look for plugins array with inline plugin objects
        for match in self.PLUGINS_ARRAY_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            after = content[match.start():match.start() + 2000]

            # Find plugin IDs within this array
            for id_match in self.CUSTOM_PLUGIN_ID_PATTERN.finditer(after):
                plugin_id = id_match.group(1)
                # Skip known built-in plugin ids
                if plugin_id in ('tooltip', 'legend', 'title', 'subtitle', 'filler', 'decimation'):
                    continue
                plugin_block = after[id_match.start():id_match.start() + 500]
                hooks = [m.group(1) for m in self.HOOK_PATTERN.finditer(plugin_block)]

                result['plugins'].append(ChartPluginInfo(
                    name=plugin_id,
                    file=file_path,
                    line_number=line_num,
                    plugin_type='custom',
                    plugin_id=plugin_id,
                    hooks=hooks[:10],
                ))

        return result
