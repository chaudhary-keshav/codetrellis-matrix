"""
CSS Property Extractor for CodeTrellis

Extracts CSS property declarations, shorthands, vendor prefixes,
and declaration blocks from CSS/SCSS/Less source code.

Supports:
- All CSS1-CSS3 standard properties
- CSS4 properties (accent-color, aspect-ratio, contain, content-visibility)
- Vendor-prefixed properties (-webkit-, -moz-, -ms-, -o-)
- Shorthand detection (margin, padding, background, font, border, etc.)
- Important declarations (!important)
- Logical properties (inline-start, block-end, etc.)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CSSPropertyInfo:
    """Information about a CSS property declaration."""
    property_name: str
    value: str = ""
    file: str = ""
    line_number: int = 0
    is_shorthand: bool = False
    is_important: bool = False
    is_vendor_prefixed: bool = False
    vendor_prefix: str = ""
    is_custom_property: bool = False
    is_logical_property: bool = False
    category: str = ""  # layout, typography, color, animation, etc.


@dataclass
class CSSDeclarationBlockInfo:
    """Information about a CSS declaration block."""
    selector: str
    file: str = ""
    line_number: int = 0
    properties: List[CSSPropertyInfo] = field(default_factory=list)
    property_count: int = 0


class CSSPropertyExtractor:
    """
    Extracts CSS properties and their values from source code.

    Detects:
    - Standard properties across all CSS versions
    - Shorthand properties and their expansions
    - Vendor-prefixed properties
    - !important declarations
    - Logical properties (CSS Logical Properties Level 1)
    - Property categories (layout, typography, color, etc.)
    """

    SHORTHAND_PROPERTIES = {
        'margin', 'padding', 'border', 'background', 'font',
        'flex', 'grid', 'animation', 'transition', 'outline',
        'list-style', 'columns', 'gap', 'place-items', 'place-content',
        'place-self', 'overflow', 'text-decoration', 'border-radius',
        'inset', 'contain-intrinsic-size', 'scroll-margin', 'scroll-padding',
        'border-block', 'border-inline', 'margin-block', 'margin-inline',
        'padding-block', 'padding-inline',
    }

    LOGICAL_PROPERTY_KEYWORDS = {
        'inline-start', 'inline-end', 'block-start', 'block-end',
        'inline-size', 'block-size', 'margin-inline', 'margin-block',
        'padding-inline', 'padding-block', 'border-inline', 'border-block',
        'inset-inline', 'inset-block',
    }

    PROPERTY_CATEGORIES = {
        'layout': {'display', 'position', 'top', 'right', 'bottom', 'left',
                   'float', 'clear', 'z-index', 'overflow', 'visibility',
                   'flex', 'flex-direction', 'flex-wrap', 'flex-flow',
                   'flex-grow', 'flex-shrink', 'flex-basis', 'align-items',
                   'align-self', 'align-content', 'justify-content',
                   'justify-items', 'justify-self', 'order',
                   'grid', 'grid-template', 'grid-template-columns',
                   'grid-template-rows', 'grid-column', 'grid-row',
                   'grid-area', 'gap', 'row-gap', 'column-gap',
                   'place-items', 'place-content', 'place-self',
                   'container-type', 'container-name', 'contain',
                   'aspect-ratio', 'inset', 'width', 'height',
                   'min-width', 'max-width', 'min-height', 'max-height',
                   'box-sizing', 'margin', 'padding'},
        'typography': {'font', 'font-family', 'font-size', 'font-weight',
                       'font-style', 'font-variant', 'line-height',
                       'letter-spacing', 'word-spacing', 'text-align',
                       'text-decoration', 'text-transform', 'text-indent',
                       'text-shadow', 'white-space', 'word-break',
                       'overflow-wrap', 'hyphens', 'text-overflow',
                       'writing-mode', 'direction', 'unicode-bidi',
                       'font-feature-settings', 'font-variation-settings',
                       'text-underline-offset', 'text-decoration-thickness'},
        'color': {'color', 'background', 'background-color', 'opacity',
                  'accent-color', 'caret-color', 'color-scheme',
                  'forced-color-adjust', 'print-color-adjust'},
        'animation': {'animation', 'animation-name', 'animation-duration',
                      'animation-timing-function', 'animation-delay',
                      'animation-iteration-count', 'animation-direction',
                      'animation-fill-mode', 'animation-play-state',
                      'transition', 'transition-property', 'transition-duration',
                      'transition-timing-function', 'transition-delay',
                      'will-change', 'animation-timeline',
                      'scroll-timeline', 'view-timeline'},
        'visual': {'border', 'border-radius', 'box-shadow', 'outline',
                   'filter', 'backdrop-filter', 'mix-blend-mode',
                   'isolation', 'clip-path', 'mask', 'transform',
                   'perspective', 'backface-visibility',
                   'content-visibility', 'image-rendering',
                   'object-fit', 'object-position'},
        'interaction': {'cursor', 'pointer-events', 'user-select',
                        'touch-action', 'resize', 'scroll-behavior',
                        'scroll-snap-type', 'scroll-snap-align',
                        'overscroll-behavior', 'scrollbar-width',
                        'scrollbar-color', 'scrollbar-gutter'},
    }

    # Property declaration pattern - matches properties within rule blocks
    # Uses lookbehind to avoid consuming the delimiter that precedes the property
    PROPERTY_PATTERN = re.compile(
        r'(?:(?<=\{)|(?<=;)|^)\s*([\w-]+)\s*:\s*([^;{}]+?)\s*(!important)?\s*;',
        re.MULTILINE
    )

    VENDOR_PREFIX_PATTERN = re.compile(r'^-(webkit|moz|ms|o)-')

    def __init__(self):
        # Build reverse category lookup
        self._category_map: Dict[str, str] = {}
        for cat, props in self.PROPERTY_CATEGORIES.items():
            for prop in props:
                self._category_map[prop] = cat

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all CSS properties from source code.

        Returns dict with:
          - properties: List[CSSPropertyInfo]
          - blocks: List[CSSDeclarationBlockInfo]
          - stats: Dict with property counts by category
        """
        properties: List[CSSPropertyInfo] = []
        stats: Dict[str, int] = {
            "total_properties": 0,
            "shorthand_count": 0,
            "important_count": 0,
            "vendor_prefixed_count": 0,
            "custom_property_count": 0,
            "logical_property_count": 0,
        }
        category_counts: Dict[str, int] = {}

        # Remove comments
        clean = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        clean = re.sub(r'//[^\n]*', '', clean)

        for match in self.PROPERTY_PATTERN.finditer(clean):
            prop_name = match.group(1).strip()
            value = match.group(2).strip()
            important = match.group(3) is not None
            line_num = clean[:match.start()].count('\n') + 1

            # Detect vendor prefix
            vendor_match = self.VENDOR_PREFIX_PATTERN.match(prop_name)
            vendor_prefix = vendor_match.group(1) if vendor_match else ""
            base_prop = self.VENDOR_PREFIX_PATTERN.sub('', prop_name) if vendor_match else prop_name

            # Detect custom property
            is_custom = prop_name.startswith('--')

            # Detect shorthand
            is_shorthand = base_prop in self.SHORTHAND_PROPERTIES

            # Detect logical property
            is_logical = any(kw in prop_name for kw in self.LOGICAL_PROPERTY_KEYWORDS)

            # Categorize
            category = self._category_map.get(base_prop, "other")

            prop_info = CSSPropertyInfo(
                property_name=prop_name,
                value=value[:100],  # Truncate long values
                file=file_path,
                line_number=line_num,
                is_shorthand=is_shorthand,
                is_important=important,
                is_vendor_prefixed=bool(vendor_prefix),
                vendor_prefix=vendor_prefix,
                is_custom_property=is_custom,
                is_logical_property=is_logical,
                category=category,
            )
            properties.append(prop_info)

            # Update stats
            stats["total_properties"] += 1
            if is_shorthand:
                stats["shorthand_count"] += 1
            if important:
                stats["important_count"] += 1
            if vendor_prefix:
                stats["vendor_prefixed_count"] += 1
            if is_custom:
                stats["custom_property_count"] += 1
            if is_logical:
                stats["logical_property_count"] += 1

            category_counts[category] = category_counts.get(category, 0) + 1

        stats["categories"] = category_counts

        return {
            "properties": properties,
            "stats": stats,
        }
