"""
Bootstrap Utility Extractor for CodeTrellis

Extracts Bootstrap utility class usage from HTML, JSX/TSX source code.
Covers Bootstrap v3.x through v5.x utility systems:

Spacing:
- Margins: m-*, mt-*, mb-*, ms-*, me-*, mx-*, my-*
- Padding: p-*, pt-*, pb-*, ps-*, pe-*, px-*, py-*
- Gap: gap-*, row-gap-*, column-gap-*

Display:
- d-none, d-inline, d-inline-block, d-block, d-grid, d-table,
  d-flex, d-inline-flex, d-{breakpoint}-*

Flex:
- flex-row, flex-column, flex-wrap, flex-nowrap
- justify-content-*, align-items-*, align-self-*, align-content-*
- flex-fill, flex-grow-*, flex-shrink-*, order-*

Sizing:
- w-25, w-50, w-75, w-100, w-auto
- h-25, h-50, h-75, h-100, h-auto
- mw-100, mh-100, min-vw-100, min-vh-100, vw-100, vh-100

Colors:
- text-primary, text-secondary, text-success, etc.
- bg-primary, bg-secondary, bg-success, etc.
- bg-opacity-*, text-opacity-*

Borders:
- border, border-top, border-end, border-bottom, border-start
- border-0, border-{side}-0
- border-primary, border-secondary, etc.
- rounded, rounded-*, rounded-circle, rounded-pill

Shadows, Position, Overflow, Opacity, Z-index, Object-fit

Part of CodeTrellis v4.40 - Bootstrap Framework Support
"""

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class BootstrapUtilityInfo:
    """Information about Bootstrap utility class usage."""
    utility_class: str = ""
    file: str = ""
    line_number: int = 0
    category: str = ""           # spacing, display, flex, sizing, colors, borders, etc.
    is_responsive: bool = False
    breakpoint: str = ""
    usage_count: int = 1


@dataclass
class BootstrapUtilitySummary:
    """Aggregated summary of Bootstrap utility usage."""
    category: str = ""
    total_count: int = 0
    unique_classes: int = 0
    responsive_count: int = 0
    top_classes: List[str] = field(default_factory=list)


class BootstrapUtilityExtractor:
    """
    Extracts Bootstrap utility class usage from source code.

    Detects:
    - All Bootstrap utility categories (spacing, display, flex, sizing, etc.)
    - Responsive utility variants
    - Utility API customizations
    - Usage frequency analysis
    """

    # Utility patterns with their categories
    UTILITY_PATTERNS = {
        'spacing': re.compile(
            r'\b([mp][trblxyse]?)-(?:(sm|md|lg|xl|xxl)-)?(n?\d+|auto)\b'
        ),
        'gap': re.compile(
            r'\b(?:row-gap|column-gap|gap)-(?:(sm|md|lg|xl|xxl)-)?\d+\b'
        ),
        'display': re.compile(
            r'\bd-(?:(sm|md|lg|xl|xxl)-)?(none|inline|inline-block|block|'
            r'grid|inline-grid|table|table-row|table-cell|flex|inline-flex)\b'
        ),
        'flex': re.compile(
            r'\b(?:flex|justify-content|align-items|align-self|align-content|order)'
            r'-(?:(sm|md|lg|xl|xxl)-)?[\w-]+\b'
        ),
        'sizing': re.compile(
            r'\b(?:w|h|mw|mh|min-vw|min-vh|vw|vh)-(?:\d+|auto|100)\b'
        ),
        'text_color': re.compile(
            r'\btext-(?:primary|secondary|success|danger|warning|info|'
            r'light|dark|body|muted|white|black-50|white-50|reset|'
            r'decoration-none|lowercase|uppercase|capitalize|'
            r'start|center|end|wrap|nowrap|break|truncate|'
            r'opacity-\d+)\b'
        ),
        'bg_color': re.compile(
            r'\bbg-(?:primary|secondary|success|danger|warning|info|'
            r'light|dark|body|white|transparent|black|'
            r'opacity-\d+|gradient)\b'
        ),
        'border': re.compile(
            r'\bborder(?:-(?:top|end|bottom|start|0|1|2|3|4|5|'
            r'primary|secondary|success|danger|warning|info|'
            r'light|dark|white|opacity-\d+))?\b'
        ),
        'rounded': re.compile(
            r'\brounded(?:-(?:top|end|bottom|start|circle|pill|0|1|2|3|4|5))?\b'
        ),
        'shadow': re.compile(
            r'\bshadow(?:-(?:none|sm|lg))?\b'
        ),
        'position': re.compile(
            r'\b(?:position-(?:static|relative|absolute|fixed|sticky)|'
            r'top-\d+|bottom-\d+|start-\d+|end-\d+|'
            r'translate-middle(?:-[xy])?|'
            r'fixed-top|fixed-bottom|sticky-top|sticky-bottom)\b'
        ),
        'overflow': re.compile(
            r'\boverflow(?:-[xy])?-(?:auto|hidden|visible|scroll)\b'
        ),
        'opacity': re.compile(
            r'\bopacity-(?:0|25|50|75|100)\b'
        ),
        'z_index': re.compile(
            r'\bz-(?:n?\d+|auto)\b'
        ),
        'object_fit': re.compile(
            r'\bobject-fit-(?:(sm|md|lg|xl|xxl)-)?(?:contain|cover|fill|scale|none)\b'
        ),
        'float': re.compile(
            r'\bfloat-(?:(sm|md|lg|xl|xxl)-)?(?:start|end|none)\b'
        ),
        'visibility': re.compile(
            r'\b(?:visible|invisible)\b'
        ),
        'interaction': re.compile(
            r'\b(?:pe-none|pe-auto|user-select-all|user-select-auto|user-select-none)\b'
        ),
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Bootstrap utility class usage from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'utilities' and 'summary' keys
        """
        utilities: List[BootstrapUtilityInfo] = []
        category_counts: Dict[str, Counter] = {}

        if not content or not content.strip():
            return {'utilities': utilities, 'summary': []}

        # Extract all class attributes
        class_pattern = re.compile(
            r'(?:class|className)\s*=\s*["\'{]([^"\'}\)]+)',
            re.IGNORECASE
        )

        for cm in class_pattern.finditer(content):
            class_str = cm.group(1)
            classes = class_str.split()
            line_num = content[:cm.start()].count('\n') + 1

            for cls in classes:
                for category, pattern in self.UTILITY_PATTERNS.items():
                    if pattern.match(cls):
                        # Check for responsive breakpoint
                        bp_match = re.search(r'-(sm|md|lg|xl|xxl)-', cls)
                        is_responsive = bp_match is not None
                        breakpoint = bp_match.group(1) if bp_match else ""

                        utilities.append(BootstrapUtilityInfo(
                            utility_class=cls,
                            file=file_path,
                            line_number=line_num,
                            category=category,
                            is_responsive=is_responsive,
                            breakpoint=breakpoint,
                        ))

                        # Count for summary
                        if category not in category_counts:
                            category_counts[category] = Counter()
                        category_counts[category][cls] += 1
                        break

        # Build summary
        summary = []
        for cat, counter in sorted(category_counts.items()):
            responsive_count = sum(
                1 for u in utilities
                if u.category == cat and u.is_responsive
            )
            summary.append(BootstrapUtilitySummary(
                category=cat,
                total_count=sum(counter.values()),
                unique_classes=len(counter),
                responsive_count=responsive_count,
                top_classes=[cls for cls, _ in counter.most_common(5)],
            ))

        return {'utilities': utilities, 'summary': summary}
