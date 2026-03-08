"""
D3.js Scale Extractor

Extracts scale definitions and configurations:
- Continuous scales (linear, log, pow, sqrt, time, utc, radial, symlog, sequential, diverging)
- Ordinal scales (ordinal, band, point)
- Quantizing scales (quantize, quantile, threshold)
- Color scales (schemeCategory10, interpolateViridis, etc.)
- Domain / range detection
- Scale modifiers (clamp, nice, ticks, round, padding)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class D3ScaleInfo:
    """D3 scale definition."""
    name: str  # variable name or scale factory
    file: str
    line_number: int
    scale_type: str  # 'linear', 'log', 'pow', 'sqrt', 'time', 'utc', 'ordinal', 'band', 'point', 'quantize', 'quantile', 'threshold', 'sequential', 'diverging', 'radial', 'symlog', 'identity'
    scale_category: str  # 'continuous', 'ordinal', 'quantizing', 'sequential', 'diverging'
    has_domain: bool = False
    has_range: bool = False
    has_clamp: bool = False
    has_nice: bool = False
    has_ticks: bool = False
    has_invert: bool = False
    has_padding: bool = False  # band/point scales
    has_round: bool = False
    has_interpolate: bool = False
    modifiers: List[str] = field(default_factory=list)


@dataclass
class D3ColorScaleInfo:
    """D3 color scale or scheme."""
    name: str
    file: str
    line_number: int
    color_type: str  # 'categorical', 'sequential', 'diverging', 'cyclical'
    scheme_name: str = ""  # 'Category10', 'Viridis', 'RdYlBu', etc.
    is_interpolator: bool = False  # d3.interpolateViridis vs d3.schemeCategory10
    is_custom: bool = False


class D3ScaleExtractor:
    """Extracts D3.js scale definitions and configurations."""

    # ── Continuous scale patterns ─────────────────────────────────
    CONTINUOUS_SCALE_PATTERNS = {
        'linear': re.compile(r'd3\.scaleLinear\s*\(', re.MULTILINE),
        'log': re.compile(r'd3\.scaleLog\s*\(', re.MULTILINE),
        'pow': re.compile(r'd3\.scalePow\s*\(', re.MULTILINE),
        'sqrt': re.compile(r'd3\.scaleSqrt\s*\(', re.MULTILINE),
        'time': re.compile(r'd3\.scaleTime\s*\(', re.MULTILINE),
        'utc': re.compile(r'd3\.scaleUtc\s*\(', re.MULTILINE),
        'radial': re.compile(r'd3\.scaleRadial\s*\(', re.MULTILINE),
        'symlog': re.compile(r'd3\.scaleSymlog\s*\(', re.MULTILINE),
        'identity': re.compile(r'd3\.scaleIdentity\s*\(', re.MULTILINE),
    }

    # ── Ordinal scale patterns ────────────────────────────────────
    ORDINAL_SCALE_PATTERNS = {
        'ordinal': re.compile(r'd3\.scaleOrdinal\s*\(', re.MULTILINE),
        'band': re.compile(r'd3\.scaleBand\s*\(', re.MULTILINE),
        'point': re.compile(r'd3\.scalePoint\s*\(', re.MULTILINE),
    }

    # ── Quantizing scale patterns ─────────────────────────────────
    QUANTIZING_SCALE_PATTERNS = {
        'quantize': re.compile(r'd3\.scaleQuantize\s*\(', re.MULTILINE),
        'quantile': re.compile(r'd3\.scaleQuantile\s*\(', re.MULTILINE),
        'threshold': re.compile(r'd3\.scaleThreshold\s*\(', re.MULTILINE),
    }

    # ── Sequential / Diverging scale patterns ─────────────────────
    SEQUENTIAL_SCALE_PATTERNS = {
        'sequential': re.compile(r'd3\.scaleSequential(?:Log|Pow|Sqrt|Symlog)?\s*\(', re.MULTILINE),
        'diverging': re.compile(r'd3\.scaleDiverging(?:Log|Pow|Sqrt|Symlog)?\s*\(', re.MULTILINE),
    }

    # ── D3 v3 scale patterns (d3.scale.linear, d3.scale.ordinal, etc.) ──
    V3_SCALE_PATTERNS = {
        'linear': re.compile(r'd3\.scale\.linear\s*\(', re.MULTILINE),
        'log': re.compile(r'd3\.scale\.log\s*\(', re.MULTILINE),
        'pow': re.compile(r'd3\.scale\.pow\s*\(', re.MULTILINE),
        'sqrt': re.compile(r'd3\.scale\.sqrt\s*\(', re.MULTILINE),
        'ordinal': re.compile(r'd3\.scale\.ordinal\s*\(', re.MULTILINE),
        'quantize': re.compile(r'd3\.scale\.quantize\s*\(', re.MULTILINE),
        'quantile': re.compile(r'd3\.scale\.quantile\s*\(', re.MULTILINE),
        'threshold': re.compile(r'd3\.scale\.threshold\s*\(', re.MULTILINE),
        'identity': re.compile(r'd3\.scale\.identity\s*\(', re.MULTILINE),
    }

    # ── Scale modifier detection ──────────────────────────────────
    DOMAIN_PATTERN = re.compile(r'\.domain\s*\(', re.MULTILINE)
    RANGE_PATTERN = re.compile(r'\.range(?:Round)?\s*\(', re.MULTILINE)
    CLAMP_PATTERN = re.compile(r'\.clamp\s*\(', re.MULTILINE)
    NICE_PATTERN = re.compile(r'\.nice\s*\(', re.MULTILINE)
    TICKS_PATTERN = re.compile(r'\.ticks\s*\(', re.MULTILINE)
    INVERT_PATTERN = re.compile(r'\.invert\s*\(', re.MULTILINE)
    PADDING_PATTERN = re.compile(r'\.padding(?:Inner|Outer)?\s*\(', re.MULTILINE)
    ROUND_PATTERN = re.compile(r'\.round\s*\(', re.MULTILINE)
    INTERPOLATE_PATTERN = re.compile(r'\.interpolate\s*\(', re.MULTILINE)
    MODIFIER_PATTERN = re.compile(
        r'\.(domain|range|rangeRound|clamp|nice|ticks|tickFormat|invert|copy|'
        r'padding|paddingInner|paddingOuter|align|round|interpolate|exponent|base|constant)\s*\(',
        re.MULTILINE
    )

    # ── Color scheme patterns (categorical) ───────────────────────
    CATEGORICAL_SCHEME_PATTERN = re.compile(
        r'd3\.(schemeCategory10|schemeAccent|schemeDark2|schemePaired|'
        r'schemePastel1|schemePastel2|schemeSet1|schemeSet2|schemeSet3|'
        r'schemeTableau10)',
        re.MULTILINE
    )

    # ── Color interpolator patterns (sequential) ──────────────────
    SEQUENTIAL_INTERPOLATOR_PATTERN = re.compile(
        r'd3\.(interpolateViridis|interpolateInferno|interpolateMagma|'
        r'interpolatePlasma|interpolateCividis|interpolateWarm|interpolateCool|'
        r'interpolateCubehelixDefault|interpolateBuGn|interpolateBuPu|'
        r'interpolateGnBu|interpolateOrRd|interpolatePuBuGn|interpolatePuBu|'
        r'interpolatePuRd|interpolateRdPu|interpolateYlGnBu|interpolateYlGn|'
        r'interpolateYlOrBr|interpolateYlOrRd|interpolateBlues|interpolateGreens|'
        r'interpolateGreys|interpolateOranges|interpolatePurples|interpolateReds|'
        r'interpolateTurbo|interpolateRainbow|interpolateSinebow)',
        re.MULTILINE
    )

    # ── Color interpolator patterns (diverging) ───────────────────
    DIVERGING_INTERPOLATOR_PATTERN = re.compile(
        r'd3\.(interpolateBrBG|interpolatePRGn|interpolatePiYG|'
        r'interpolateRdBu|interpolateRdGy|interpolateRdYlBu|'
        r'interpolateRdYlGn|interpolateSpectral)',
        re.MULTILINE
    )

    # ── Color scheme patterns (sequential multi-hue) ──────────────
    SEQUENTIAL_SCHEME_PATTERN = re.compile(
        r'd3\.(schemeBuGn|schemeBuPu|schemeGnBu|schemeOrRd|'
        r'schemePuBuGn|schemePuBu|schemePuRd|schemeRdPu|'
        r'schemeYlGnBu|schemeYlGn|schemeYlOrBr|schemeYlOrRd|'
        r'schemeBlues|schemeGreens|schemeGreys|schemeOranges|'
        r'schemePurples|schemeReds)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract scale definitions from D3.js code."""
        result: Dict[str, Any] = {
            'scales': [],
            'color_scales': [],
        }

        # ── Continuous scales ────────────────────────────────────
        for scale_type, pattern in self.CONTINUOUS_SCALE_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                after = content[match.end():match.end() + 500]
                modifiers = [m.group(1) for m in self.MODIFIER_PATTERN.finditer(after[:400])]
                result['scales'].append(D3ScaleInfo(
                    name=scale_type,
                    file=file_path,
                    line_number=line_num,
                    scale_type=scale_type,
                    scale_category='continuous',
                    has_domain=bool(self.DOMAIN_PATTERN.search(after[:400])),
                    has_range=bool(self.RANGE_PATTERN.search(after[:400])),
                    has_clamp=bool(self.CLAMP_PATTERN.search(after[:400])),
                    has_nice=bool(self.NICE_PATTERN.search(after[:400])),
                    has_ticks=bool(self.TICKS_PATTERN.search(after[:400])),
                    has_invert=bool(self.INVERT_PATTERN.search(after[:400])),
                    has_interpolate=bool(self.INTERPOLATE_PATTERN.search(after[:400])),
                    modifiers=modifiers[:10],
                ))

        # ── Ordinal scales ───────────────────────────────────────
        for scale_type, pattern in self.ORDINAL_SCALE_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                after = content[match.end():match.end() + 500]
                modifiers = [m.group(1) for m in self.MODIFIER_PATTERN.finditer(after[:400])]
                result['scales'].append(D3ScaleInfo(
                    name=scale_type,
                    file=file_path,
                    line_number=line_num,
                    scale_type=scale_type,
                    scale_category='ordinal',
                    has_domain=bool(self.DOMAIN_PATTERN.search(after[:400])),
                    has_range=bool(self.RANGE_PATTERN.search(after[:400])),
                    has_padding=bool(self.PADDING_PATTERN.search(after[:400])),
                    has_round=bool(self.ROUND_PATTERN.search(after[:400])),
                    modifiers=modifiers[:10],
                ))

        # ── Quantizing scales ────────────────────────────────────
        for scale_type, pattern in self.QUANTIZING_SCALE_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                after = content[match.end():match.end() + 500]
                modifiers = [m.group(1) for m in self.MODIFIER_PATTERN.finditer(after[:400])]
                result['scales'].append(D3ScaleInfo(
                    name=scale_type,
                    file=file_path,
                    line_number=line_num,
                    scale_type=scale_type,
                    scale_category='quantizing',
                    has_domain=bool(self.DOMAIN_PATTERN.search(after[:400])),
                    has_range=bool(self.RANGE_PATTERN.search(after[:400])),
                    modifiers=modifiers[:10],
                ))

        # ── Sequential / Diverging scales ────────────────────────
        for scale_type, pattern in self.SEQUENTIAL_SCALE_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                after = content[match.end():match.end() + 500]
                modifiers = [m.group(1) for m in self.MODIFIER_PATTERN.finditer(after[:400])]
                result['scales'].append(D3ScaleInfo(
                    name=scale_type,
                    file=file_path,
                    line_number=line_num,
                    scale_type=scale_type,
                    scale_category=scale_type,
                    has_domain=bool(self.DOMAIN_PATTERN.search(after[:400])),
                    has_range=bool(self.RANGE_PATTERN.search(after[:400])),
                    has_clamp=bool(self.CLAMP_PATTERN.search(after[:400])),
                    has_interpolate=bool(self.INTERPOLATE_PATTERN.search(after[:400])),
                    modifiers=modifiers[:10],
                ))

        # ── D3 v3 scales ────────────────────────────────────────
        for scale_type, pattern in self.V3_SCALE_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                after = content[match.end():match.end() + 500]
                category = 'continuous'
                if scale_type in ('ordinal',):
                    category = 'ordinal'
                elif scale_type in ('quantize', 'quantile', 'threshold'):
                    category = 'quantizing'
                modifiers = [m.group(1) for m in self.MODIFIER_PATTERN.finditer(after[:400])]
                result['scales'].append(D3ScaleInfo(
                    name=f"v3_{scale_type}",
                    file=file_path,
                    line_number=line_num,
                    scale_type=scale_type,
                    scale_category=category,
                    has_domain=bool(self.DOMAIN_PATTERN.search(after[:400])),
                    has_range=bool(self.RANGE_PATTERN.search(after[:400])),
                    modifiers=modifiers[:10],
                ))

        # ── Categorical color schemes ────────────────────────────
        for match in self.CATEGORICAL_SCHEME_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            scheme_name = match.group(1).replace('scheme', '')
            result['color_scales'].append(D3ColorScaleInfo(
                name=match.group(1),
                file=file_path,
                line_number=line_num,
                color_type='categorical',
                scheme_name=scheme_name,
                is_interpolator=False,
            ))

        # ── Sequential color interpolators ───────────────────────
        for match in self.SEQUENTIAL_INTERPOLATOR_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            scheme_name = match.group(1).replace('interpolate', '')
            result['color_scales'].append(D3ColorScaleInfo(
                name=match.group(1),
                file=file_path,
                line_number=line_num,
                color_type='sequential',
                scheme_name=scheme_name,
                is_interpolator=True,
            ))

        # ── Diverging color interpolators ────────────────────────
        for match in self.DIVERGING_INTERPOLATOR_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            scheme_name = match.group(1).replace('interpolate', '')
            result['color_scales'].append(D3ColorScaleInfo(
                name=match.group(1),
                file=file_path,
                line_number=line_num,
                color_type='diverging',
                scheme_name=scheme_name,
                is_interpolator=True,
            ))

        # ── Sequential multi-hue schemes ─────────────────────────
        for match in self.SEQUENTIAL_SCHEME_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            scheme_name = match.group(1).replace('scheme', '')
            result['color_scales'].append(D3ColorScaleInfo(
                name=match.group(1),
                file=file_path,
                line_number=line_num,
                color_type='sequential',
                scheme_name=scheme_name,
                is_interpolator=False,
            ))

        return result
