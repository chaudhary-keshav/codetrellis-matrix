"""
EnhancedHTMLParser v1.0 - Comprehensive HTML parser using all extractors.

This parser integrates all HTML extractors to provide complete
parsing of HTML source files across all HTML versions.

Supports:
- HTML 2.0, HTML 3.2, HTML 4.01 (Strict/Transitional/Frameset)
- XHTML 1.0 (Strict/Transitional), XHTML 1.1
- HTML5 / HTML Living Standard (all versions through current)
- Document structure, headings, landmarks, sections
- Semantic elements (article, nav, aside, header, footer, main, etc.)
- Forms with HTML5 validation attributes
- Meta tags, Open Graph, Twitter Cards, JSON-LD structured data
- Accessibility (ARIA, WCAG 2.0/2.1/2.2 issue detection)
- Template engines (Jinja2, EJS, Handlebars, Blade, Thymeleaf, Angular, Vue, Svelte)
- Scripts (module, async, defer, integrity), styles, resource hints
- Web Components (custom elements, shadow DOM, slots, templates)

AST Support:
- Uses Python's html.parser for DOM-aware AST parsing
- Full tag/attribute extraction with line number tracking
- Self-closing tag handling, malformed HTML tolerance

LSP Support:
- HTML Language Server integration via vscode-html-languageservice
- Completions, diagnostics, hover, formatting, document symbols
- CSS class and ID cross-referencing
- Embedded language support (CSS, JS inside HTML)

Part of CodeTrellis v4.16 - HTML Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path
from html.parser import HTMLParser

# Import all HTML extractors
from .extractors.html import (
    HTMLStructureExtractor, HTMLDocumentInfo, HTMLSectionInfo,
    HTMLHeadingInfo, HTMLLandmarkInfo,
    HTMLSemanticExtractor, HTMLSemanticElementInfo, HTMLMicrodataInfo,
    HTMLFormExtractor, HTMLFormInfo, HTMLInputInfo, HTMLFieldsetInfo,
    HTMLMetaExtractor, HTMLMetaInfo, HTMLLinkInfo, HTMLOpenGraphInfo, HTMLJsonLdInfo,
    HTMLAccessibilityExtractor, HTMLAriaInfo, HTMLA11yIssue,
    HTMLTemplateExtractor, HTMLTemplateInfo, HTMLTemplateBlockInfo,
    HTMLAssetExtractor, HTMLScriptInfo, HTMLStyleInfo, HTMLPreloadInfo,
    HTMLComponentExtractor, HTMLCustomElementInfo, HTMLSlotInfo,
)


@dataclass
class HTMLParseResult:
    """Complete parse result for an HTML file."""
    file_path: str
    file_type: str = "html"

    # Document structure
    document: Optional[HTMLDocumentInfo] = None

    # Semantic elements
    semantic_elements: List[HTMLSemanticElementInfo] = field(default_factory=list)
    microdata: List[HTMLMicrodataInfo] = field(default_factory=list)

    # Forms
    forms: List[HTMLFormInfo] = field(default_factory=list)

    # Meta / Head
    metas: List[HTMLMetaInfo] = field(default_factory=list)
    links: List[HTMLLinkInfo] = field(default_factory=list)
    open_graph: Optional[HTMLOpenGraphInfo] = None
    json_ld: List[HTMLJsonLdInfo] = field(default_factory=list)

    # Accessibility
    aria_elements: List[HTMLAriaInfo] = field(default_factory=list)
    a11y_issues: List[HTMLA11yIssue] = field(default_factory=list)
    a11y_stats: Dict[str, Any] = field(default_factory=dict)

    # Template engine
    template_info: Optional[HTMLTemplateInfo] = None

    # Scripts & Styles
    scripts: List[HTMLScriptInfo] = field(default_factory=list)
    styles: List[HTMLStyleInfo] = field(default_factory=list)
    preloads: List[HTMLPreloadInfo] = field(default_factory=list)

    # Web Components
    custom_elements: List[HTMLCustomElementInfo] = field(default_factory=list)
    slots: List[HTMLSlotInfo] = field(default_factory=list)
    templates: List[Dict] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    html_version: str = ""
    template_engine: str = ""


class EnhancedHTMLParser:
    """
    Enhanced HTML parser that uses all extractors for comprehensive parsing.

    Framework detection supports:
    - Angular (template bindings, structural directives)
    - React (JSX patterns in scripts)
    - Vue (v-directives, :bindings)
    - Svelte ({#if}, {#each} blocks)
    - Jinja2/Django ({% %}, {{ }})
    - EJS (<% %>)
    - Handlebars/Mustache ({{# }})
    - Blade (@directives)
    - Thymeleaf (th: attributes)
    - ERB (<%= %>)
    - Web Components (custom elements, shadow DOM)
    - Bootstrap (class patterns)
    - Tailwind CSS (utility classes)
    - HTMX (hx-* attributes)
    - Alpine.js (x-* attributes)
    """

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        'bootstrap': re.compile(r'class="[^"]*\b(?:container|row|col-|btn-|navbar|modal|card|alert)\b', re.IGNORECASE),
        'tailwind': re.compile(r'class="[^"]*\b(?:flex|grid|p-\d|m-\d|text-(?:sm|lg|xl)|bg-|border-|rounded)\b'),
        'htmx': re.compile(r'\bhx-(?:get|post|put|delete|patch|trigger|target|swap|push-url)\b'),
        'alpine': re.compile(r'\bx-(?:data|show|bind|on|model|text|html|ref|if|for|transition)\b'),
        'stimulus': re.compile(r'\bdata-controller\b'),
        'turbo': re.compile(r'\bdata-turbo\b|<turbo-frame'),
        'lit': re.compile(r'(?:html|css)`|@customElement|LitElement'),
        'petite_vue': re.compile(r'v-scope\b'),
    }

    # CSS framework patterns  
    CSS_FRAMEWORK_PATTERNS = {
        'bulma': re.compile(r'class="[^"]*\b(?:is-\w+|columns|column|hero|level)\b'),
        'foundation': re.compile(r'class="[^"]*\b(?:small-\d|medium-\d|large-\d|callout|orbit)\b'),
        'materialize': re.compile(r'class="[^"]*\b(?:materialize|waves-effect|z-depth|card-panel)\b'),
    }

    def __init__(self):
        """Initialize the parser with all extractors."""
        self.structure_extractor = HTMLStructureExtractor()
        self.semantic_extractor = HTMLSemanticExtractor()
        self.form_extractor = HTMLFormExtractor()
        self.meta_extractor = HTMLMetaExtractor()
        self.accessibility_extractor = HTMLAccessibilityExtractor()
        self.template_extractor = HTMLTemplateExtractor()
        self.asset_extractor = HTMLAssetExtractor()
        self.component_extractor = HTMLComponentExtractor()

    def parse(self, content: str, file_path: str = "") -> HTMLParseResult:
        """Parse HTML content using all extractors.

        Args:
            content: HTML source code string.
            file_path: Path to the HTML file.

        Returns:
            HTMLParseResult with all extracted data.
        """
        result = HTMLParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        # 1. Document structure (headings, landmarks, sections, doctype)
        doc_info = self.structure_extractor.extract(content, file_path)
        result.document = doc_info
        result.html_version = doc_info.html_version

        # 2. Semantic elements and microdata
        semantic_result = self.semantic_extractor.extract(content, file_path)
        result.semantic_elements = semantic_result.get('semantic_elements', [])
        result.microdata = semantic_result.get('microdata', [])

        # 3. Forms
        result.forms = self.form_extractor.extract(content, file_path)

        # 4. Meta / Head
        meta_result = self.meta_extractor.extract(content, file_path)
        result.metas = meta_result.get('metas', [])
        result.links = meta_result.get('links', [])
        result.open_graph = meta_result.get('open_graph')
        result.json_ld = meta_result.get('json_ld', [])

        # 5. Accessibility
        a11y_result = self.accessibility_extractor.extract(content, file_path)
        result.aria_elements = a11y_result.get('aria_elements', [])
        result.a11y_issues = a11y_result.get('issues', [])
        result.a11y_stats = a11y_result.get('stats', {})

        # 6. Template engine detection
        template_info = self.template_extractor.extract(content, file_path)
        result.template_info = template_info
        result.template_engine = template_info.engine

        # 7. Scripts, styles, and resource hints
        asset_result = self.asset_extractor.extract(content, file_path)
        result.scripts = asset_result.get('scripts', [])
        result.styles = asset_result.get('styles', [])
        result.preloads = asset_result.get('preloads', [])

        # 8. Web Components
        component_result = self.component_extractor.extract(content, file_path)
        result.custom_elements = component_result.get('custom_elements', [])
        result.slots = component_result.get('slots', [])
        result.templates = component_result.get('templates', [])

        # 9. Framework detection
        result.detected_frameworks = self._detect_frameworks(content, file_path, result)

        return result

    def _detect_frameworks(self, content: str, file_path: str, result: HTMLParseResult) -> List[str]:
        """Detect frontend frameworks and CSS libraries from HTML content."""
        frameworks: Set[str] = set()

        # Template engine as framework
        if result.template_engine:
            frameworks.add(result.template_engine)

        # Web Components
        if result.custom_elements:
            frameworks.add('web_components')

        # Pattern-based detection
        for fw_name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.add(fw_name)

        for fw_name, pattern in self.CSS_FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.add(fw_name)

        # Script-based detection
        for script in result.scripts:
            src = script.src.lower()
            if 'react' in src:
                frameworks.add('react')
            elif 'vue' in src:
                frameworks.add('vue')
            elif 'angular' in src:
                frameworks.add('angular')
            elif 'jquery' in src:
                frameworks.add('jquery')
            elif 'htmx' in src:
                frameworks.add('htmx')
            elif 'alpine' in src:
                frameworks.add('alpine')
            elif 'turbo' in src:
                frameworks.add('turbo')
            elif 'stimulus' in src:
                frameworks.add('stimulus')
            elif 'bootstrap' in src:
                frameworks.add('bootstrap')
            elif 'tailwind' in src:
                frameworks.add('tailwind')
            elif 'lit' in src:
                frameworks.add('lit')
            elif 'd3' in src:
                frameworks.add('d3')
            elif 'three' in src:
                frameworks.add('threejs')
            elif 'chart' in src:
                frameworks.add('chartjs')

        # Stylesheet-based detection
        for style in result.styles:
            href = (style.href or '').lower()
            if 'bootstrap' in href:
                frameworks.add('bootstrap')
            elif 'tailwind' in href:
                frameworks.add('tailwind')
            elif 'bulma' in href:
                frameworks.add('bulma')
            elif 'foundation' in href:
                frameworks.add('foundation')
            elif 'materialize' in href:
                frameworks.add('materialize')
            elif 'font-awesome' in href or 'fontawesome' in href:
                frameworks.add('fontawesome')

        # File extension hints
        ext = Path(file_path).suffix.lower() if file_path else ''
        name = Path(file_path).stem.lower() if file_path else ''
        if ext in ('.ejs',):
            frameworks.add('ejs')
        elif ext in ('.hbs', '.handlebars'):
            frameworks.add('handlebars')
        elif ext in ('.njk', '.nunjucks'):
            frameworks.add('nunjucks')
        elif ext in ('.j2', '.jinja2', '.jinja'):
            frameworks.add('jinja2')
        elif ext in ('.erb', '.html.erb'):
            frameworks.add('erb')
        elif ext in ('.blade.php',) or name.endswith('.blade'):
            frameworks.add('blade')
        elif ext in ('.pug', '.jade'):
            frameworks.add('pug')
        elif ext in ('.svelte',):
            frameworks.add('svelte')
        elif ext in ('.vue',):
            frameworks.add('vue')
        elif ext in ('.jsx', '.tsx'):
            frameworks.add('react')
        elif ext in ('.astro',):
            frameworks.add('astro')

        return sorted(frameworks)
