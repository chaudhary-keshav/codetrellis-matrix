"""
PostCSS Transform Extractor for CodeTrellis

Extracts CSS transforms and at-rules that are processed by PostCSS plugins.

Supports:
- @custom-media (postcss-custom-media)
- @custom-selector (postcss-custom-selectors)
- @nest (postcss-nesting)
- CSS nesting (native or postcss-nesting/postcss-nested)
- @apply (postcss-apply, Tailwind CSS)
- @import inlining (postcss-import)
- env() function (postcss-env-function)
- image-set() (postcss-image-set-function)
- :is() / :matches() / :any() pseudo-classes
- :has() pseudo-class
- Logical properties (postcss-logical)
- color() / color-mix() functions
- lab() / lch() / oklch() / oklab() functions
- Custom properties / CSS variables fallbacks
- @layer (cascade layers)
- Container queries

Part of CodeTrellis v4.46 — PostCSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class PostCSSTransformInfo:
    """Information about a CSS transform pattern used via PostCSS."""
    name: str                      # Transform name (e.g., 'custom-media', 'nesting')
    at_rule: str = ""              # The at-rule or function (e.g., '@custom-media', 'env()')
    value: str = ""                # The value/definition
    category: str = ""             # future_css, nesting, custom_properties, colors, etc.
    postcss_plugin: str = ""       # Which plugin handles this transform
    spec_stage: int = -1           # CSS spec stage (0-4, -1 if unknown)
    file: str = ""
    line_number: int = 0


class PostCSSTransformExtractor:
    """
    Extracts CSS transforms that require PostCSS plugin processing.

    Detects at-rules and CSS features that are not natively supported
    and require PostCSS plugins to transform.
    """

    # @custom-media definitions
    CUSTOM_MEDIA_PATTERN = re.compile(
        r'^[ \t]*@custom-media\s+(--[\w-]+)\s+([^;]+);',
        re.MULTILINE
    )

    # @custom-selector definitions
    CUSTOM_SELECTOR_PATTERN = re.compile(
        r'^[ \t]*@custom-selector\s+(:--[\w-]+)\s+(.+);',
        re.MULTILINE
    )

    # @nest rule (postcss-nesting)
    NEST_RULE_PATTERN = re.compile(
        r'@nest\s+([^{]+)\{',
        re.MULTILINE
    )

    # Native CSS nesting (& selector)
    NESTING_PATTERN = re.compile(
        r'&\s*(?:[\w.#:\[\]>~+*-]|::)',
        re.MULTILINE
    )

    # @apply directive
    APPLY_PATTERN = re.compile(
        r'^[ \t]*@apply\s+([^;]+);',
        re.MULTILINE
    )

    # @import (postcss-import inlines these)
    IMPORT_PATTERN = re.compile(
        r'^[ \t]*@import\s+["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # env() function
    ENV_FUNCTION_PATTERN = re.compile(
        r'env\s*\(\s*([\w-]+)',
        re.MULTILINE
    )

    # image-set() function
    IMAGE_SET_PATTERN = re.compile(
        r'image-set\s*\(',
        re.MULTILINE
    )

    # :is() pseudo-class
    IS_PSEUDO_PATTERN = re.compile(
        r':is\s*\(',
        re.MULTILINE
    )

    # :has() pseudo-class
    HAS_PSEUDO_PATTERN = re.compile(
        r':has\s*\(',
        re.MULTILINE
    )

    # :matches() pseudo-class (older spec)
    MATCHES_PSEUDO_PATTERN = re.compile(
        r':matches\s*\(',
        re.MULTILINE
    )

    # :any-link pseudo-class
    ANY_LINK_PATTERN = re.compile(
        r':any-link',
        re.MULTILINE
    )

    # :focus-visible pseudo-class
    FOCUS_VISIBLE_PATTERN = re.compile(
        r':focus-visible',
        re.MULTILINE
    )

    # :focus-within pseudo-class
    FOCUS_WITHIN_PATTERN = re.compile(
        r':focus-within',
        re.MULTILINE
    )

    # Logical properties
    LOGICAL_PROPERTY_PATTERN = re.compile(
        r'(?:margin|padding|border|inset)-(?:block|inline)(?:-start|-end)?',
        re.MULTILINE
    )

    # Color functions (future CSS)
    COLOR_FUNCTION_PATTERN = re.compile(
        r'(?:color-mix|color\s*\(|lab\s*\(|lch\s*\(|oklch\s*\(|oklab\s*\(|hwb\s*\()',
        re.MULTILINE | re.IGNORECASE
    )

    # Hex alpha colors (#RRGGBBAA)
    HEX_ALPHA_PATTERN = re.compile(
        r'#[0-9a-fA-F]{4}(?:[0-9a-fA-F]{4})?(?=[;\s,)}])',
        re.MULTILINE
    )

    # @layer (cascade layers)
    LAYER_PATTERN = re.compile(
        r'^[ \t]*@layer\s+(\S+)',
        re.MULTILINE
    )

    # @container query
    CONTAINER_QUERY_PATTERN = re.compile(
        r'^[ \t]*@container\s+',
        re.MULTILINE
    )

    # clamp() function
    CLAMP_PATTERN = re.compile(
        r'clamp\s*\(',
        re.MULTILINE
    )

    # gap property (shorthand)
    GAP_PATTERN = re.compile(
        r'(?:^|;|\{)\s*gap\s*:',
        re.MULTILINE
    )

    # overflow shorthand (two values)
    OVERFLOW_SHORTHAND_PATTERN = re.compile(
        r'overflow\s*:\s*\w+\s+\w+',
        re.MULTILINE
    )

    # place-* properties
    PLACE_PROPERTIES_PATTERN = re.compile(
        r'place-(?:content|items|self)\s*:',
        re.MULTILINE
    )

    # CSS custom properties (--var usage)
    CUSTOM_PROPERTY_PATTERN = re.compile(
        r'var\s*\(\s*--[\w-]+',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the transform extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract PostCSS transform patterns from CSS content.

        Args:
            content: CSS source code.
            file_path: Path to source file.

        Returns:
            Dict with 'transforms' list and 'stats' dict.
        """
        transforms: List[PostCSSTransformInfo] = []

        if not content or not content.strip():
            return {"transforms": transforms, "stats": {}}

        # @custom-media
        for match in self.CUSTOM_MEDIA_PATTERN.finditer(content):
            transforms.append(PostCSSTransformInfo(
                name=match.group(1),
                at_rule='@custom-media',
                value=match.group(2).strip()[:80],
                category='future_css',
                postcss_plugin='postcss-custom-media',
                spec_stage=3,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @custom-selector
        for match in self.CUSTOM_SELECTOR_PATTERN.finditer(content):
            transforms.append(PostCSSTransformInfo(
                name=match.group(1),
                at_rule='@custom-selector',
                value=match.group(2).strip()[:80],
                category='future_css',
                postcss_plugin='postcss-custom-selectors',
                spec_stage=2,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @nest
        for match in self.NEST_RULE_PATTERN.finditer(content):
            transforms.append(PostCSSTransformInfo(
                name='nest',
                at_rule='@nest',
                value=match.group(1).strip()[:80],
                category='nesting',
                postcss_plugin='postcss-nesting',
                spec_stage=3,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @apply
        for match in self.APPLY_PATTERN.finditer(content):
            transforms.append(PostCSSTransformInfo(
                name='apply',
                at_rule='@apply',
                value=match.group(1).strip()[:80],
                category='utility',
                postcss_plugin='postcss-apply',
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @import (postcss-import)
        for match in self.IMPORT_PATTERN.finditer(content):
            transforms.append(PostCSSTransformInfo(
                name='import',
                at_rule='@import',
                value=match.group(1).strip()[:80],
                category='utility',
                postcss_plugin='postcss-import',
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @layer (cascade layers)
        for match in self.LAYER_PATTERN.finditer(content):
            transforms.append(PostCSSTransformInfo(
                name=match.group(1),
                at_rule='@layer',
                category='future_css',
                postcss_plugin='postcss-cascade-layers',
                spec_stage=4,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @container queries
        for match in self.CONTAINER_QUERY_PATTERN.finditer(content):
            transforms.append(PostCSSTransformInfo(
                name='container_query',
                at_rule='@container',
                category='future_css',
                spec_stage=3,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Detect feature usage (aggregated, not per-instance)
        feature_patterns = [
            (self.NESTING_PATTERN, 'css_nesting', 'nesting', 'postcss-nesting', 3),
            (self.IS_PSEUDO_PATTERN, ':is()', 'selectors', 'postcss-is-pseudo-class', 4),
            (self.HAS_PSEUDO_PATTERN, ':has()', 'selectors', 'postcss-has-pseudo', 4),
            (self.FOCUS_VISIBLE_PATTERN, ':focus-visible', 'selectors', 'postcss-focus-visible', 4),
            (self.FOCUS_WITHIN_PATTERN, ':focus-within', 'selectors', 'postcss-focus-within', 4),
            (self.ANY_LINK_PATTERN, ':any-link', 'selectors', 'postcss-pseudo-class-any-link', 4),
            (self.COLOR_FUNCTION_PATTERN, 'color_functions', 'colors', 'postcss-color-function', 2),
            (self.CLAMP_PATTERN, 'clamp()', 'functions', 'postcss-clamp', 4),
            (self.IMAGE_SET_PATTERN, 'image-set()', 'functions', 'postcss-image-set-function', 4),
            (self.ENV_FUNCTION_PATTERN, 'env()', 'functions', 'postcss-env-function', 3),
            (self.LOGICAL_PROPERTY_PATTERN, 'logical_properties', 'properties', 'postcss-logical', 3),
            (self.GAP_PATTERN, 'gap_shorthand', 'properties', 'postcss-gap-properties', 4),
            (self.PLACE_PROPERTIES_PATTERN, 'place_properties', 'properties', 'postcss-place', 4),
            (self.OVERFLOW_SHORTHAND_PATTERN, 'overflow_shorthand', 'properties', 'postcss-overflow-shorthand', 4),
            (self.HEX_ALPHA_PATTERN, 'hex_alpha', 'colors', 'postcss-color-hex-alpha', 4),
        ]

        seen_features: set = set()
        for pattern, feat_name, category, plugin, stage in feature_patterns:
            if feat_name not in seen_features and pattern.search(content):
                seen_features.add(feat_name)
                match = pattern.search(content)
                transforms.append(PostCSSTransformInfo(
                    name=feat_name,
                    category=category,
                    postcss_plugin=plugin,
                    spec_stage=stage,
                    file=file_path,
                    line_number=content[:match.start()].count('\n') + 1 if match else 0,
                ))

        # Custom properties
        custom_prop_count = len(self.CUSTOM_PROPERTY_PATTERN.findall(content))
        if custom_prop_count > 0:
            transforms.append(PostCSSTransformInfo(
                name=f'custom_properties ({custom_prop_count} usages)',
                category='custom_properties',
                postcss_plugin='postcss-custom-properties',
                spec_stage=4,
                file=file_path,
            ))

        # Stats
        categories = set(t.category for t in transforms if t.category)
        stats = {
            "total_transforms": len(transforms),
            "categories": sorted(categories),
            "has_future_css": 'future_css' in categories,
            "has_nesting": 'nesting' in categories,
            "has_custom_properties": custom_prop_count > 0,
            "custom_property_count": custom_prop_count,
            "has_color_functions": 'colors' in categories,
            "has_logical_properties": 'properties' in categories,
            "import_count": len(self.IMPORT_PATTERN.findall(content)),
            "apply_count": len(self.APPLY_PATTERN.findall(content)),
        }

        return {"transforms": transforms, "stats": stats}
