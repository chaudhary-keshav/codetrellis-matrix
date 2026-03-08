"""
Tests for HTML Meta, Accessibility, Template, Asset, and Component extractors.

Part of CodeTrellis v4.16 HTML Language Support.
"""

import pytest
from codetrellis.extractors.html.meta_extractor import HTMLMetaExtractor
from codetrellis.extractors.html.accessibility_extractor import HTMLAccessibilityExtractor
from codetrellis.extractors.html.template_extractor import HTMLTemplateExtractor
from codetrellis.extractors.html.asset_extractor import HTMLAssetExtractor
from codetrellis.extractors.html.component_extractor import HTMLComponentExtractor


class TestHTMLMetaExtractor:
    """Tests for HTMLMetaExtractor."""

    @pytest.fixture
    def extractor(self):
        return HTMLMetaExtractor()

    def test_basic_meta(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="description" content="Test description">
    <meta name="keywords" content="test, html">
    <title>Test</title>
</head>
<body></body>
</html>'''
        result = extractor.extract(code, "test.html")
        assert len(result['metas']) >= 2

    def test_open_graph(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test</title>
    <meta property="og:type" content="website">
    <meta property="og:title" content="My Website">
    <meta property="og:description" content="Description here">
    <meta property="og:image" content="https://example.com/img.jpg">
    <meta property="og:url" content="https://example.com">
    <meta name="twitter:card" content="summary_large_image">
</head>
<body></body>
</html>'''
        result = extractor.extract(code, "test.html")
        og = result['open_graph']
        assert og is not None
        assert og.og_type == "website"
        assert og.og_title == "My Website"
        assert og.twitter_card == "summary_large_image"

    def test_json_ld(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test</title>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "My Site",
        "url": "https://example.com"
    }
    </script>
</head>
<body></body>
</html>'''
        result = extractor.extract(code, "test.html")
        json_ld = result['json_ld']
        assert len(json_ld) >= 1
        assert json_ld[0].schema_type == "WebSite"

    def test_link_tags(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test</title>
    <link rel="stylesheet" href="/css/main.css">
    <link rel="icon" type="image/x-icon" href="/favicon.ico">
    <link rel="canonical" href="https://example.com/page">
</head>
<body></body>
</html>'''
        result = extractor.extract(code, "test.html")
        assert len(result['links']) >= 3


class TestHTMLAccessibilityExtractor:
    """Tests for HTMLAccessibilityExtractor."""

    @pytest.fixture
    def extractor(self):
        return HTMLAccessibilityExtractor()

    def test_missing_lang(self, extractor):
        code = '''<!DOCTYPE html>
<html>
<head><title>T</title></head>
<body><p>Hello</p></body>
</html>'''
        result = extractor.extract(code, "test.html")
        issues = result['issues']
        rules = [i.rule for i in issues]
        assert "WCAG-3.1.1" in rules

    def test_missing_alt(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <img src="photo.jpg">
    <img src="logo.png" alt="Company logo">
</body>
</html>'''
        result = extractor.extract(code, "test.html")
        issues = result['issues']
        rules = [i.rule for i in issues]
        assert "WCAG-1.1.1" in rules

    def test_good_alt(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <img src="photo.jpg" alt="A beautiful sunset">
    <img src="decoration.png" alt="">
</body>
</html>'''
        result = extractor.extract(code, "test.html")
        issues = result['issues']
        alt_issues = [i for i in issues if i.rule == "WCAG-1.1.1"]
        assert len(alt_issues) == 0

    def test_aria_roles(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <div role="banner" aria-label="Site banner"></div>
    <div role="search" aria-label="Search"></div>
    <div role="alert" aria-live="assertive">Error</div>
</body>
</html>'''
        result = extractor.extract(code, "test.html")
        aria = result['aria_elements']
        assert len(aria) >= 3
        roles = [a.role for a in aria]
        assert "banner" in roles
        assert "search" in roles

    def test_tabindex_issues(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <div tabindex="5">Bad tabindex</div>
    <div tabindex="0">OK</div>
    <div tabindex="-1">Programmatic only</div>
</body>
</html>'''
        result = extractor.extract(code, "test.html")
        issues = result['issues']
        tab_issues = [i for i in issues if i.rule == "WCAG-2.4.3"]
        assert len(tab_issues) >= 1


class TestHTMLTemplateExtractor:
    """Tests for HTMLTemplateExtractor."""

    @pytest.fixture
    def extractor(self):
        return HTMLTemplateExtractor()

    def test_jinja2(self, extractor):
        code = '''{% extends "base.html" %}
{% block title %}{{ page_title }}{% endblock %}
{% block content %}
    {% for item in items %}
        <p>{{ item.name | capitalize }}</p>
    {% endfor %}
    {% include "partial.html" %}
{% endblock %}'''
        result = extractor.extract(code, "page.html")
        assert result is not None
        assert result.engine in ("jinja2", "django", "nunjucks")
        assert result.extends == "base.html"
        assert len(result.includes) > 0
        assert "page_title" in result.variables or len(result.variables) > 0

    def test_ejs(self, extractor):
        code = '''<!DOCTYPE html>
<html>
<head><title><%= title %></title></head>
<body>
    <% if (user) { %>
        <p>Hello, <%= user.name %></p>
    <% } %>
    <% items.forEach(function(item) { %>
        <li><%= item %></li>
    <% }); %>
</body>
</html>'''
        result = extractor.extract(code, "page.ejs")
        assert result is not None
        assert result.engine == "ejs"

    def test_handlebars(self, extractor):
        code = '''{{> header}}
<div class="content">
    {{#each items}}
        <p>{{this.name}}</p>
    {{/each}}
    {{#if showFooter}}
        {{> footer}}
    {{/if}}
</div>'''
        result = extractor.extract(code, "page.hbs")
        assert result is not None
        assert result.engine == "handlebars"

    def test_no_template(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>Plain</title></head>
<body><p>No template syntax</p></body>
</html>'''
        result = extractor.extract(code, "plain.html")
        # Should return None or low confidence
        assert result is None or result.engine_confidence < 0.3


class TestHTMLAssetExtractor:
    """Tests for HTMLAssetExtractor."""

    @pytest.fixture
    def extractor(self):
        return HTMLAssetExtractor()

    def test_scripts(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>T</title>
    <script src="https://cdn.example.com/lib.js" integrity="sha384-abc" crossorigin="anonymous"></script>
</head>
<body>
    <script src="/js/app.js" defer></script>
    <script type="module" src="/js/module.js"></script>
    <script>console.log("inline");</script>
</body>
</html>'''
        result = extractor.extract(code, "test.html")
        scripts = result['scripts']
        assert len(scripts) >= 4
        external = [s for s in scripts if s.src]
        assert len(external) >= 3
        inline = [s for s in scripts if s.is_inline]
        assert len(inline) >= 1
        modules = [s for s in scripts if s.is_module]
        assert len(modules) >= 1

    def test_styles(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>T</title>
    <link rel="stylesheet" href="/css/main.css">
    <style>
        :root { --primary: blue; }
        body { color: var(--primary); }
    </style>
</head>
<body></body>
</html>'''
        result = extractor.extract(code, "test.html")
        styles = result['styles']
        assert len(styles) >= 1

    def test_preloads(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>T</title>
    <link rel="preload" href="/font.woff2" as="font" crossorigin>
    <link rel="prefetch" href="/next.html">
    <link rel="preconnect" href="https://api.example.com">
    <link rel="dns-prefetch" href="https://cdn.example.com">
    <link rel="modulepreload" href="/modules/app.js">
</head>
<body></body>
</html>'''
        result = extractor.extract(code, "test.html")
        preloads = result['preloads']
        assert len(preloads) >= 5
        types = [p.hint_type for p in preloads]
        assert "preload" in types
        assert "prefetch" in types
        assert "preconnect" in types


class TestHTMLComponentExtractor:
    """Tests for HTMLComponentExtractor."""

    @pytest.fixture
    def extractor(self):
        return HTMLComponentExtractor()

    def test_custom_elements(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <my-header title="Hello"></my-header>
    <app-content>
        <my-card data-id="1">Card content</my-card>
    </app-content>
    <my-footer></my-footer>
</body>
</html>'''
        result = extractor.extract(code, "test.html")
        elements = result['custom_elements']
        assert len(elements) >= 4
        tag_names = [e.tag_name for e in elements]
        assert "my-header" in tag_names
        assert "my-card" in tag_names

    def test_customized_builtin(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <button is="fancy-button">Click me</button>
</body>
</html>'''
        result = extractor.extract(code, "test.html")
        elements = result['custom_elements']
        builtin = [e for e in elements if not e.is_autonomous]
        assert len(builtin) >= 1

    def test_slots(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <template id="my-comp">
        <slot name="header">Default Header</slot>
        <div class="body">
            <slot>Default content</slot>
        </div>
        <slot name="footer"></slot>
    </template>
</body>
</html>'''
        result = extractor.extract(code, "test.html")
        slots = result['slots']
        assert len(slots) >= 2
        named = [s for s in slots if s.name]
        assert len(named) >= 2

    def test_custom_element_registration(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <my-widget data-value="42"></my-widget>
    <script>
        class MyWidget extends HTMLElement {
            connectedCallback() {
                this.innerHTML = '<p>Widget</p>';
            }
        }
        customElements.define('my-widget', MyWidget);
    </script>
</body>
</html>'''
        result = extractor.extract(code, "test.html")
        elements = result['custom_elements']
        assert len(elements) >= 1
        my_widget = [e for e in elements if e.tag_name == "my-widget"]
        assert len(my_widget) >= 1
