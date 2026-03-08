"""
HTML Template Extractor for CodeTrellis

Detects and extracts template engine syntax from HTML files.
Supports Jinja2/Nunjucks, EJS, Handlebars/Mustache, Blade (Laravel),
Thymeleaf, Pug/Jade (pre-compiled), ERB, Django templates,
Twig, Razor, and Web Components <template> elements.

Part of CodeTrellis v4.16 - HTML Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class HTMLTemplateBlockInfo:
    """Information about a template block/directive."""
    engine: str = ""          # jinja2, ejs, handlebars, blade, thymeleaf, etc.
    block_type: str = ""      # block, if, for, include, extends, component, etc.
    name: str = ""            # Block/variable name
    expression: str = ""      # Full expression
    line_number: int = 0


@dataclass
class HTMLTemplateInfo:
    """Aggregated template information for a file."""
    engine: str = ""                          # Detected template engine
    engine_confidence: float = 0.0            # 0.0-1.0 confidence
    blocks: List[HTMLTemplateBlockInfo] = field(default_factory=list)
    includes: List[str] = field(default_factory=list)
    extends: str = ""
    variables: List[str] = field(default_factory=list)
    filters: List[str] = field(default_factory=list)
    macros: List[str] = field(default_factory=list)
    components: List[str] = field(default_factory=list)


class HTMLTemplateExtractor:
    """Extracts template engine patterns from HTML files."""

    # Jinja2 / Nunjucks / Django
    JINJA2_BLOCK = re.compile(r'\{%[-\s]*(\w+)\s+(.*?)\s*[-]?%\}', re.DOTALL)
    JINJA2_VAR = re.compile(r'\{\{\s*(.+?)\s*\}\}')
    JINJA2_COMMENT = re.compile(r'\{#.*?#\}', re.DOTALL)

    # EJS
    EJS_BLOCK = re.compile(r'<%[-=_]?\s*(.+?)\s*[-_]?%>')

    # Handlebars / Mustache
    HBS_BLOCK = re.compile(r'\{\{[#/]?\s*(\w+)\s*(.*?)\}\}')
    HBS_PARTIAL = re.compile(r'\{\{>\s*(\S+)\s*\}\}')
    HBS_HELPER = re.compile(r'\{\{(\w+)\s+(.+?)\}\}')

    # Blade (Laravel)
    BLADE_DIRECTIVE = re.compile(r'@(\w+)\s*(?:\((.+?)\))?')

    # Thymeleaf
    THYMELEAF_ATTR = re.compile(r'th:(\w+)="([^"]*)"')

    # ERB
    ERB_BLOCK = re.compile(r'<%[=-]?\s*(.+?)\s*[-]?%>')

    # Web Components <template>
    TEMPLATE_TAG = re.compile(r'<template\b([^>]*)>', re.IGNORECASE)

    # Razor (.cshtml patterns found in .html)
    RAZOR_BLOCK = re.compile(r'@\{|@\w+\b|@\(')

    # Angular template syntax
    ANGULAR_BINDING = re.compile(r'\[(\w+)\]="[^"]*"|\((\w+)\)="[^"]*"|\*(\w+)="[^"]*"')
    ANGULAR_INTERPOLATION = re.compile(r'\{\{\s*(.+?)\s*\}\}')

    # Vue template syntax
    VUE_DIRECTIVE = re.compile(r'v-(\w+)(?::(\w+))?="[^"]*"')
    VUE_BINDING = re.compile(r':(\w+)="[^"]*"')

    # Svelte syntax
    SVELTE_BLOCK = re.compile(r'\{#(\w+)\s+(.+?)\}|\{/(\w+)\}|\{@(\w+)\s+(.+?)\}')

    def extract(self, content: str, file_path: str = "") -> HTMLTemplateInfo:
        """Extract template engine patterns from HTML content.

        Args:
            content: HTML source code string.
            file_path: Optional file path for engine hints.

        Returns:
            HTMLTemplateInfo with detected template patterns.
        """
        info = HTMLTemplateInfo()
        scores: Dict[str, float] = {}

        # Detect Jinja2 / Django / Nunjucks
        jinja_blocks = self.JINJA2_BLOCK.findall(content)
        jinja_vars = self.JINJA2_VAR.findall(content)
        if jinja_blocks:
            # Distinguish Django vs Jinja2 vs Nunjucks
            engine = 'jinja2'
            if any(b[0] in ('load', 'csrf_token', 'static', 'url') for b in jinja_blocks):
                engine = 'django'
            elif file_path.endswith('.njk') or file_path.endswith('.nunjucks'):
                engine = 'nunjucks'
            scores[engine] = len(jinja_blocks) * 2.0 + len(jinja_vars)
            for block in jinja_blocks:
                info.blocks.append(HTMLTemplateBlockInfo(
                    engine=engine, block_type=block[0], name=block[1].split()[0] if block[1] else '',
                    expression=f"{{% {block[0]} {block[1]} %}}", line_number=0,
                ))
                if block[0] == 'extends':
                    info.extends = block[1].strip("'\"")
                elif block[0] == 'include':
                    info.includes.append(block[1].strip("'\""))
                elif block[0] == 'macro':
                    info.macros.append(block[1].split('(')[0].strip())
            # Extract variables
            for var in jinja_vars:
                var_name = var.split('|')[0].split('.')[0].strip()
                if var_name and var_name not in info.variables:
                    info.variables.append(var_name)
            # Extract filters
            for var in jinja_vars:
                if '|' in var:
                    for filt in var.split('|')[1:]:
                        fname = filt.split('(')[0].strip()
                        if fname and fname not in info.filters:
                            info.filters.append(fname)

        # Detect EJS
        ejs_blocks = self.EJS_BLOCK.findall(content)
        if ejs_blocks and not jinja_blocks:
            scores['ejs'] = len(ejs_blocks) * 2.0
            for block in ejs_blocks[:50]:
                info.blocks.append(HTMLTemplateBlockInfo(
                    engine='ejs', block_type='expression', expression=block.strip(),
                    line_number=0,
                ))

        # Detect Handlebars
        hbs_blocks = self.HBS_BLOCK.findall(content)
        hbs_partials = self.HBS_PARTIAL.findall(content)
        if hbs_blocks and '{{#' in content:
            scores['handlebars'] = len(hbs_blocks) * 1.5 + len(hbs_partials) * 2
            for block in hbs_blocks[:50]:
                info.blocks.append(HTMLTemplateBlockInfo(
                    engine='handlebars', block_type=block[0], name=block[1] if block[1] else '',
                    expression=f"{{{{{block[0]} {block[1]}}}}}",
                    line_number=0,
                ))
            for partial in hbs_partials:
                info.includes.append(partial)

        # Detect Blade
        blade_directives = self.BLADE_DIRECTIVE.findall(content)
        blade_keywords = {'if', 'else', 'elseif', 'endif', 'foreach', 'endforeach',
                          'for', 'endfor', 'while', 'endwhile', 'section', 'yield',
                          'extends', 'include', 'component', 'slot', 'push', 'stack',
                          'auth', 'guest', 'csrf', 'method', 'livewire', 'php'}
        blade_matches = [d for d in blade_directives if d[0] in blade_keywords]
        if blade_matches:
            scores['blade'] = len(blade_matches) * 3.0
            for d in blade_matches[:50]:
                info.blocks.append(HTMLTemplateBlockInfo(
                    engine='blade', block_type=d[0], name=d[1] if d[1] else '',
                    expression=f"@{d[0]}({d[1]})" if d[1] else f"@{d[0]}",
                    line_number=0,
                ))
                if d[0] == 'extends':
                    info.extends = d[1].strip("'\"")
                elif d[0] == 'include':
                    info.includes.append(d[1].strip("'\""))
                elif d[0] == 'component':
                    info.components.append(d[1].strip("'\""))

        # Detect Thymeleaf
        thymeleaf_attrs = self.THYMELEAF_ATTR.findall(content)
        if thymeleaf_attrs:
            scores['thymeleaf'] = len(thymeleaf_attrs) * 2.5
            for attr in thymeleaf_attrs[:50]:
                info.blocks.append(HTMLTemplateBlockInfo(
                    engine='thymeleaf', block_type=attr[0], expression=f'th:{attr[0]}="{attr[1]}"',
                    line_number=0,
                ))

        # Detect Angular
        angular_bindings = self.ANGULAR_BINDING.findall(content)
        if angular_bindings:
            scores['angular'] = len(angular_bindings) * 2.0
            for b in angular_bindings[:50]:
                binding_name = b[0] or b[1] or b[2]
                info.blocks.append(HTMLTemplateBlockInfo(
                    engine='angular', block_type='binding', name=binding_name,
                    line_number=0,
                ))

        # Detect Vue
        vue_directives = self.VUE_DIRECTIVE.findall(content)
        if vue_directives:
            scores['vue'] = len(vue_directives) * 2.0
            for d in vue_directives[:50]:
                info.blocks.append(HTMLTemplateBlockInfo(
                    engine='vue', block_type=d[0], name=d[1] if d[1] else '',
                    line_number=0,
                ))

        # Detect Svelte
        svelte_blocks = self.SVELTE_BLOCK.findall(content)
        if svelte_blocks:
            scores['svelte'] = len(svelte_blocks) * 2.5

        # Detect ERB (if not already classified)
        if not scores and self.ERB_BLOCK.findall(content):
            erb_blocks = self.ERB_BLOCK.findall(content)
            scores['erb'] = len(erb_blocks) * 1.5

        # Determine primary engine
        if scores:
            primary = max(scores, key=scores.get)
            info.engine = primary
            total_score = sum(scores.values())
            info.engine_confidence = scores[primary] / total_score if total_score > 0 else 0

        return info
