"""
Tests for HTML Structure, Semantic, and Form extractors.

Part of CodeTrellis v4.16 HTML Language Support.
"""

import pytest
from codetrellis.extractors.html.structure_extractor import HTMLStructureExtractor
from codetrellis.extractors.html.semantic_extractor import HTMLSemanticExtractor
from codetrellis.extractors.html.form_extractor import HTMLFormExtractor


class TestHTMLStructureExtractor:
    """Tests for HTMLStructureExtractor."""

    @pytest.fixture
    def extractor(self):
        return HTMLStructureExtractor()

    def test_basic_document(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test Page</title>
</head>
<body>
    <h1>Title</h1>
    <p>Content</p>
</body>
</html>'''
        result = extractor.extract(code, "test.html")
        assert result is not None
        assert result.title == "Test Page"
        assert result.lang == "en"
        assert result.charset == "UTF-8"

    def test_headings(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <h1>Main</h1>
    <h2 id="sec1">Section 1</h2>
    <h3>Sub 1.1</h3>
    <h2 id="sec2">Section 2</h2>
</body>
</html>'''
        result = extractor.extract(code, "test.html")
        assert len(result.headings) == 4
        assert result.headings[0].level == 1
        assert result.headings[0].text == "Main"
        assert result.headings[1].id == "sec1"

    def test_landmarks(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <header>Header</header>
    <nav aria-label="Main">Nav</nav>
    <main>
        <article>Article</article>
        <aside>Sidebar</aside>
    </main>
    <footer>Footer</footer>
</body>
</html>'''
        result = extractor.extract(code, "test.html")
        assert len(result.landmarks) >= 5
        tags = [l.tag for l in result.landmarks]
        assert "header" in tags
        assert "nav" in tags
        assert "main" in tags
        assert "footer" in tags

    def test_html5_doctype(self, extractor):
        code = '<!DOCTYPE html><html><head><title>T</title></head><body></body></html>'
        result = extractor.extract(code, "test.html")
        assert result.has_html5_doctype is True

    def test_sections(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <section id="about" class="intro">About Us</section>
    <section id="services">Services</section>
</body>
</html>'''
        result = extractor.extract(code, "test.html")
        assert len(result.sections) >= 2


class TestHTMLSemanticExtractor:
    """Tests for HTMLSemanticExtractor."""

    @pytest.fixture
    def extractor(self):
        return HTMLSemanticExtractor()

    def test_semantic_elements(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <article id="post-1" class="blog-post">
        <header><h2>Title</h2></header>
        <figure>
            <img src="photo.jpg" alt="Photo">
            <figcaption>Caption</figcaption>
        </figure>
    </article>
    <aside>Related</aside>
    <nav>Navigation</nav>
</body>
</html>'''
        result = extractor.extract(code, "test.html")
        elements = result['semantic_elements']
        assert len(elements) > 0
        tags = [e.tag for e in elements]
        assert "article" in tags

    def test_microdata(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <div itemscope itemtype="https://schema.org/Product">
        <span itemprop="name">Widget</span>
        <span itemprop="price">$19.99</span>
    </div>
</body>
</html>'''
        result = extractor.extract(code, "test.html")
        microdata = result['microdata']
        assert len(microdata) > 0
        assert microdata[0].schema_type == "https://schema.org/Product"
        assert "name" in microdata[0].properties


class TestHTMLFormExtractor:
    """Tests for HTMLFormExtractor."""

    @pytest.fixture
    def extractor(self):
        return HTMLFormExtractor()

    def test_basic_form(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <form action="/submit" method="post" id="myform">
        <input type="text" name="name" required>
        <input type="email" name="email" required>
        <textarea name="message"></textarea>
        <button type="submit">Send</button>
    </form>
</body>
</html>'''
        forms = extractor.extract(code, "test.html")
        assert len(forms) == 1
        form = forms[0]
        assert form.action == "/submit"
        assert form.method.lower() == "post"
        assert form.id == "myform"
        assert len(form.inputs) >= 2

    def test_form_validation(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <form>
        <input type="text" name="zip" pattern="[0-9]{5}" required>
        <input type="number" name="age" min="18" max="120">
        <input type="password" name="pass" minlength="8">
    </form>
</body>
</html>'''
        forms = extractor.extract(code, "test.html")
        assert len(forms) == 1
        inputs = forms[0].inputs
        # Check pattern attribute is captured
        zip_inputs = [i for i in inputs if i.name == "zip"]
        assert len(zip_inputs) == 1
        assert zip_inputs[0].required is True

    def test_fieldsets(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <form>
        <fieldset>
            <legend>Personal Info</legend>
            <input type="text" name="name">
            <input type="email" name="email">
        </fieldset>
        <fieldset>
            <legend>Address</legend>
            <input type="text" name="street">
            <input type="text" name="city">
        </fieldset>
    </form>
</body>
</html>'''
        forms = extractor.extract(code, "test.html")
        assert len(forms) == 1
        assert len(forms[0].fieldsets) >= 2
        legends = [f.legend for f in forms[0].fieldsets]
        assert "Personal Info" in legends

    def test_csrf_detection(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <form method="post">
        <input type="hidden" name="csrf_token" value="abc123">
        <input type="text" name="data">
    </form>
</body>
</html>'''
        forms = extractor.extract(code, "test.html")
        assert len(forms) == 1
        assert forms[0].has_csrf_token is True

    def test_multiple_forms(self, extractor):
        code = '''<!DOCTYPE html>
<html lang="en">
<head><title>T</title></head>
<body>
    <form id="search" action="/search" method="get">
        <input type="search" name="q">
    </form>
    <form id="login" action="/login" method="post">
        <input type="text" name="username">
        <input type="password" name="password">
    </form>
</body>
</html>'''
        forms = extractor.extract(code, "test.html")
        assert len(forms) == 2
