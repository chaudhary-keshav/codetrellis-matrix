"""
Tests for EnhancedHTMLParser — full integration test of all HTML extractors.

Part of CodeTrellis v4.16 HTML Language Support.
"""

import pytest
from codetrellis.html_parser_enhanced import EnhancedHTMLParser


@pytest.fixture
def parser():
    return EnhancedHTMLParser()


class TestHTMLParserBasicParsing:
    """Tests for basic HTML parsing."""

    def test_empty_content(self, parser):
        result = parser.parse("", "empty.html")
        assert result is not None

    def test_minimal_html5(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test Page</title>
</head>
<body>
    <h1>Hello World</h1>
</body>
</html>'''
        result = parser.parse(code, "test.html")
        assert result.document is not None
        assert result.document.title == "Test Page"
        assert result.document.lang == "en"
        assert result.document.charset == "UTF-8"

    def test_html_version_detection_html5(self, parser):
        code = '<!DOCTYPE html><html><head><title>T</title></head><body></body></html>'
        result = parser.parse(code, "test.html")
        assert result.document is not None
        assert "5" in result.document.html_version or "living" in result.document.html_version.lower()

    def test_heading_extraction(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <h1>Main Title</h1>
    <h2>Sub Section</h2>
    <h3>Detail</h3>
</body>
</html>'''
        result = parser.parse(code, "test.html")
        assert result.document is not None
        assert len(result.document.headings) >= 3

    def test_landmark_detection(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <header><h1>Site</h1></header>
    <nav>Navigation</nav>
    <main>
        <article>Article content</article>
        <aside>Sidebar</aside>
    </main>
    <footer>Footer</footer>
</body>
</html>'''
        result = parser.parse(code, "test.html")
        assert result.document is not None
        assert len(result.document.landmarks) >= 5


class TestHTMLParserSemanticElements:
    """Tests for semantic element extraction."""

    def test_semantic_elements(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <article id="post-1">
        <header><h2>Article Title</h2></header>
        <section>Content</section>
        <footer>By Author</footer>
    </article>
    <aside>Related</aside>
    <figure>
        <img src="photo.jpg" alt="Photo">
        <figcaption>A photo</figcaption>
    </figure>
    <details>
        <summary>More info</summary>
        <p>Detail text</p>
    </details>
</body>
</html>'''
        result = parser.parse(code, "test.html")
        assert len(result.semantic_elements) > 0
        tags = [e.tag for e in result.semantic_elements]
        assert "article" in tags
        assert "figure" in tags

    def test_microdata_extraction(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <div itemscope itemtype="https://schema.org/Person">
        <span itemprop="name">John Doe</span>
        <span itemprop="email">john@example.com</span>
    </div>
</body>
</html>'''
        result = parser.parse(code, "test.html")
        assert len(result.microdata) > 0
        assert result.microdata[0].schema_type == "https://schema.org/Person"


class TestHTMLParserForms:
    """Tests for form extraction."""

    def test_basic_form(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <form action="/login" method="post" id="login-form">
        <label for="email">Email</label>
        <input type="email" id="email" name="email" required>
        <label for="password">Password</label>
        <input type="password" id="password" name="password" required minlength="8">
        <button type="submit">Login</button>
    </form>
</body>
</html>'''
        result = parser.parse(code, "test.html")
        assert len(result.forms) == 1
        form = result.forms[0]
        assert form.action == "/login"
        assert form.method.lower() == "post"
        assert form.id == "login-form"
        assert len(form.inputs) >= 2

    def test_form_with_csrf(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <form action="/submit" method="post">
        <input type="hidden" name="_csrf" value="abc123">
        <input type="text" name="data">
        <button type="submit">Submit</button>
    </form>
</body>
</html>'''
        result = parser.parse(code, "test.html")
        assert len(result.forms) == 1
        assert result.forms[0].has_csrf_token is True

    def test_form_file_upload(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="document" accept=".pdf,.doc">
        <button type="submit">Upload</button>
    </form>
</body>
</html>'''
        result = parser.parse(code, "test.html")
        assert len(result.forms) == 1
        assert result.forms[0].has_file_upload is True
        assert result.forms[0].enctype == "multipart/form-data"


class TestHTMLParserMeta:
    """Tests for meta tag extraction."""

    def test_meta_tags(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="Test page description">
    <meta name="author" content="John Doe">
    <title>Test</title>
</head>
<body></body>
</html>'''
        result = parser.parse(code, "test.html")
        assert len(result.metas) >= 3
        names = [m.name for m in result.metas if m.name]
        assert "description" in names or "viewport" in names

    def test_open_graph(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test</title>
    <meta property="og:type" content="article">
    <meta property="og:title" content="My Article">
    <meta property="og:description" content="Article description">
    <meta property="og:image" content="https://example.com/image.jpg">
    <meta property="og:url" content="https://example.com/article">
</head>
<body></body>
</html>'''
        result = parser.parse(code, "test.html")
        assert result.open_graph is not None
        assert result.open_graph.og_type == "article"
        assert result.open_graph.og_title == "My Article"

    def test_json_ld(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test</title>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Acme Corp",
        "url": "https://acme.com"
    }
    </script>
</head>
<body></body>
</html>'''
        result = parser.parse(code, "test.html")
        assert len(result.json_ld) >= 1
        assert result.json_ld[0].schema_type == "Organization"
        assert result.json_ld[0].name == "Acme Corp"

    def test_link_tags(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test</title>
    <link rel="stylesheet" href="/css/main.css">
    <link rel="icon" href="/favicon.ico">
    <link rel="canonical" href="https://example.com/page">
    <link rel="preconnect" href="https://fonts.googleapis.com">
</head>
<body></body>
</html>'''
        result = parser.parse(code, "test.html")
        assert len(result.links) >= 3


class TestHTMLParserAccessibility:
    """Tests for accessibility extraction."""

    def test_missing_lang(self, parser):
        code = '''<!DOCTYPE html>
<html>
<head><title>T</title></head>
<body><p>Hello</p></body>
</html>'''
        result = parser.parse(code, "test.html")
        # Should detect missing lang as a11y issue
        rules = [i.rule for i in result.a11y_issues]
        assert "WCAG-3.1.1" in rules or len(result.a11y_issues) > 0

    def test_missing_alt(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <img src="photo.jpg">
</body>
</html>'''
        result = parser.parse(code, "test.html")
        rules = [i.rule for i in result.a11y_issues]
        assert "WCAG-1.1.1" in rules

    def test_aria_roles(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <div role="alert" aria-live="assertive">Error message</div>
    <div role="navigation" aria-label="Main menu"></div>
</body>
</html>'''
        result = parser.parse(code, "test.html")
        assert len(result.aria_elements) > 0


class TestHTMLParserAssets:
    """Tests for script and style extraction."""

    def test_external_scripts(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>T</title>
    <script src="https://cdn.example.com/lib.js" defer></script>
</head>
<body>
    <script src="/js/app.js" type="module"></script>
</body>
</html>'''
        result = parser.parse(code, "test.html")
        assert len(result.scripts) >= 2
        srcs = [s.src for s in result.scripts if s.src]
        assert any("lib.js" in s for s in srcs)

    def test_inline_script(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <script>
        console.log("hello");
    </script>
</body>
</html>'''
        result = parser.parse(code, "test.html")
        inline_scripts = [s for s in result.scripts if s.is_inline]
        assert len(inline_scripts) >= 1

    def test_styles(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>T</title>
    <link rel="stylesheet" href="/css/main.css">
    <style>
        :root { --primary: #333; }
        body { color: var(--primary); }
    </style>
</head>
<body></body>
</html>'''
        result = parser.parse(code, "test.html")
        assert len(result.styles) >= 1

    def test_preload_hints(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>T</title>
    <link rel="preload" href="/font.woff2" as="font" crossorigin>
    <link rel="prefetch" href="/next-page.html">
    <link rel="preconnect" href="https://api.example.com">
</head>
<body></body>
</html>'''
        result = parser.parse(code, "test.html")
        assert len(result.preloads) >= 3


class TestHTMLParserTemplateEngines:
    """Tests for template engine detection."""

    def test_jinja2_detection(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>{{ page_title }}</title></head>
<body>
    {% extends "base.html" %}
    {% block content %}
    {% for item in items %}
        <p>{{ item.name | capitalize }}</p>
    {% endfor %}
    {% endblock %}
</body>
</html>'''
        result = parser.parse(code, "template.html")
        assert result.template_engine in ("jinja2", "django", "nunjucks")
        assert result.template_info is not None

    def test_ejs_detection(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title><%= pageTitle %></title></head>
<body>
    <% items.forEach(function(item) { %>
        <p><%= item.name %></p>
    <% }); %>
</body>
</html>'''
        result = parser.parse(code, "template.ejs")
        assert result.template_engine == "ejs"

    def test_handlebars_detection(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>{{pageTitle}}</title></head>
<body>
    {{#each items}}
        <p>{{this.name}}</p>
    {{/each}}
    {{> header}}
</body>
</html>'''
        result = parser.parse(code, "template.hbs")
        assert result.template_engine == "handlebars"


class TestHTMLParserWebComponents:
    """Tests for Web Component detection."""

    def test_custom_elements(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <my-component data-id="1"></my-component>
    <app-header title="My App"></app-header>
    <ui-button variant="primary">Click</ui-button>
</body>
</html>'''
        result = parser.parse(code, "test.html")
        assert len(result.custom_elements) >= 3
        tag_names = [e.tag_name for e in result.custom_elements]
        assert "my-component" in tag_names
        assert "app-header" in tag_names

    def test_shadow_dom_detection(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <my-widget></my-widget>
    <script>
        class MyWidget extends HTMLElement {
            constructor() {
                super();
                this.attachShadow({ mode: 'open' });
            }
        }
        customElements.define('my-widget', MyWidget);
    </script>
</body>
</html>'''
        result = parser.parse(code, "test.html")
        # Should detect custom element registration
        assert len(result.custom_elements) >= 1

    def test_slot_elements(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <template id="my-element">
        <slot name="header">Default Header</slot>
        <slot>Default Content</slot>
    </template>
</body>
</html>'''
        result = parser.parse(code, "test.html")
        assert len(result.slots) >= 1


class TestHTMLParserFrameworkDetection:
    """Tests for CSS/JS framework detection."""

    def test_bootstrap_detection(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>T</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5/dist/css/bootstrap.min.css">
</head>
<body>
    <div class="container">
        <div class="row">
            <div class="col-md-6">Content</div>
        </div>
    </div>
</body>
</html>'''
        result = parser.parse(code, "test.html")
        assert "bootstrap" in result.detected_frameworks

    def test_tailwind_detection(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body class="bg-gray-100">
    <div class="flex items-center justify-center min-h-screen">
        <div class="p-6 bg-white rounded-lg shadow-lg">
            <h1 class="text-2xl font-bold text-gray-800">Hello</h1>
        </div>
    </div>
</body>
</html>'''
        result = parser.parse(code, "test.html")
        assert "tailwind" in result.detected_frameworks

    def test_htmx_detection(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>T</title>
    <script src="https://unpkg.com/htmx.org"></script>
</head>
<body>
    <button hx-get="/api/data" hx-target="#result" hx-swap="innerHTML">
        Load Data
    </button>
    <div id="result"></div>
</body>
</html>'''
        result = parser.parse(code, "test.html")
        assert "htmx" in result.detected_frameworks


class TestHTMLParserEdgeCases:
    """Tests for edge cases and error handling."""

    def test_malformed_html(self, parser):
        code = '''<html>
<head><title>Missing DOCTYPE</title>
<body>
    <p>Unclosed paragraph
    <div>Nested wrong</p></div>
</body>'''
        result = parser.parse(code, "bad.html")
        # Should not crash
        assert result is not None

    def test_html_with_svg(self, parser):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
        <circle cx="50" cy="50" r="40" fill="red"/>
    </svg>
</body>
</html>'''
        result = parser.parse(code, "test.html")
        assert result is not None

    def test_large_file(self, parser):
        # Generate a moderately large HTML file
        rows = "\n".join(f'<tr><td>Row {i}</td><td>Data {i}</td></tr>' for i in range(200))
        code = f'''<!DOCTYPE html>
<html lang="en">
<head><title>Large Table</title></head>
<body>
    <table>
        <thead><tr><th>Name</th><th>Value</th></tr></thead>
        <tbody>{rows}</tbody>
    </table>
</body>
</html>'''
        result = parser.parse(code, "large.html")
        assert result is not None
        assert result.document is not None

    def test_xhtml_file(self, parser):
        code = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
    <title>XHTML Page</title>
</head>
<body>
    <p>XHTML content</p>
</body>
</html>'''
        result = parser.parse(code, "test.xhtml")
        assert result is not None
        assert result.document is not None
