"""
CodeTrellis HTML Extractors Module v1.0

Provides comprehensive extractors for HTML language constructs across
all HTML versions (HTML 1.0 through HTML Living Standard / HTML5.3+).

Core Structure Extractors:
- HTMLStructureExtractor: Document structure, sections, landmarks, headings

Semantic Extractors:
- HTMLSemanticExtractor: Semantic elements (article, nav, aside, header, footer, main, section)

Form Extractors:
- HTMLFormExtractor: Forms, inputs, validation attributes, fieldsets

Meta & Head Extractors:
- HTMLMetaExtractor: meta tags, link tags, Open Graph, Twitter Cards, JSON-LD, favicons

Accessibility Extractors:
- HTMLAccessibilityExtractor: ARIA roles/attributes, alt text, lang, tabindex, a11y patterns

Template Extractors:
- HTMLTemplateExtractor: Template engines (Jinja2, EJS, Handlebars, Blade, Thymeleaf, etc.)

Script & Style Extractors:
- HTMLAssetExtractor: script/style tags, inline JS/CSS, external resources, preload/prefetch

Component Extractors:
- HTMLComponentExtractor: Web Components, custom elements, shadow DOM, slots, templates

Part of CodeTrellis v4.16 - HTML Language Support
"""

from .structure_extractor import (
    HTMLStructureExtractor,
    HTMLDocumentInfo,
    HTMLSectionInfo,
    HTMLHeadingInfo,
    HTMLLandmarkInfo,
)
from .semantic_extractor import (
    HTMLSemanticExtractor,
    HTMLSemanticElementInfo,
    HTMLMicrodataInfo,
)
from .form_extractor import (
    HTMLFormExtractor,
    HTMLFormInfo,
    HTMLInputInfo,
    HTMLFieldsetInfo,
)
from .meta_extractor import (
    HTMLMetaExtractor,
    HTMLMetaInfo,
    HTMLLinkInfo,
    HTMLOpenGraphInfo,
    HTMLJsonLdInfo,
)
from .accessibility_extractor import (
    HTMLAccessibilityExtractor,
    HTMLAriaInfo,
    HTMLA11yIssue,
)
from .template_extractor import (
    HTMLTemplateExtractor,
    HTMLTemplateInfo,
    HTMLTemplateBlockInfo,
)
from .asset_extractor import (
    HTMLAssetExtractor,
    HTMLScriptInfo,
    HTMLStyleInfo,
    HTMLPreloadInfo,
)
from .component_extractor import (
    HTMLComponentExtractor,
    HTMLCustomElementInfo,
    HTMLSlotInfo,
)

__all__ = [
    # Structure extractors
    'HTMLStructureExtractor', 'HTMLDocumentInfo', 'HTMLSectionInfo',
    'HTMLHeadingInfo', 'HTMLLandmarkInfo',
    # Semantic extractors
    'HTMLSemanticExtractor', 'HTMLSemanticElementInfo', 'HTMLMicrodataInfo',
    # Form extractors
    'HTMLFormExtractor', 'HTMLFormInfo', 'HTMLInputInfo', 'HTMLFieldsetInfo',
    # Meta extractors
    'HTMLMetaExtractor', 'HTMLMetaInfo', 'HTMLLinkInfo',
    'HTMLOpenGraphInfo', 'HTMLJsonLdInfo',
    # Accessibility extractors
    'HTMLAccessibilityExtractor', 'HTMLAriaInfo', 'HTMLA11yIssue',
    # Template extractors
    'HTMLTemplateExtractor', 'HTMLTemplateInfo', 'HTMLTemplateBlockInfo',
    # Asset extractors
    'HTMLAssetExtractor', 'HTMLScriptInfo', 'HTMLStyleInfo', 'HTMLPreloadInfo',
    # Component extractors
    'HTMLComponentExtractor', 'HTMLCustomElementInfo', 'HTMLSlotInfo',
]
