"""
Tests for Astro extractors and EnhancedAstroParser.

Part of CodeTrellis v4.60 Astro Framework Support.
Tests cover:
- Component extraction (props, slots, directives, styles, expressions)
- Frontmatter extraction (imports, variables, data fetching, Astro API, collections)
- Island extraction (client:load/idle/visible/media/only, framework detection)
- Routing extraction (file-based routes, API endpoints, middleware)
- API extraction (virtual modules, integrations, config, types, version detection)
- Parser integration (framework detection, version detection, feature detection, is_astro_file)
"""

import pytest
from codetrellis.astro_parser_enhanced import (
    EnhancedAstroParser,
    AstroParseResult,
)
from codetrellis.extractors.astro import (
    AstroComponentExtractor,
    AstroComponentInfo,
    AstroSlotInfo,
    AstroExpressionInfo,
    AstroFrontmatterExtractor,
    AstroFrontmatterInfo,
    AstroDataFetchInfo,
    AstroCollectionInfo,
    AstroIslandExtractor,
    AstroIslandInfo,
    AstroRoutingExtractor,
    AstroRouteInfo,
    AstroEndpointInfo,
    AstroMiddlewareInfo,
    AstroApiExtractor,
    AstroImportInfo,
    AstroIntegrationInfo,
    AstroConfigInfo,
    AstroTypeInfo,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedAstroParser()


@pytest.fixture
def component_extractor():
    return AstroComponentExtractor()


@pytest.fixture
def frontmatter_extractor():
    return AstroFrontmatterExtractor()


@pytest.fixture
def island_extractor():
    return AstroIslandExtractor()


@pytest.fixture
def routing_extractor():
    return AstroRoutingExtractor()


@pytest.fixture
def api_extractor():
    return AstroApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Component Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestAstroComponentExtractor:
    """Tests for AstroComponentExtractor."""

    def test_extract_basic_component(self, component_extractor):
        """Test basic .astro component extraction."""
        code = """---
const title = "Hello";
---
<h1>{title}</h1>
"""
        result = component_extractor.extract(code, "Header.astro")
        assert 'components' in result

    def test_extract_props_interface(self, component_extractor):
        """Test Props interface extraction via Astro.props."""
        code = """---
interface Props {
  title: string;
  description?: string;
}
const { title, description } = Astro.props;
---
<h1>{title}</h1>
{description && <p>{description}</p>}
"""
        result = component_extractor.extract(code, "Card.astro")
        comps = result.get('components', [])
        assert len(comps) >= 1
        comp = comps[0]
        assert isinstance(comp, AstroComponentInfo)
        assert comp.has_props is True
        assert len(comp.prop_names) >= 1

    def test_extract_named_slots(self, component_extractor):
        """Test named slot extraction."""
        code = """---
---
<div>
  <header><slot name="header" /></header>
  <main><slot /></main>
  <footer><slot name="footer"><p>Default footer</p></slot></footer>
</div>
"""
        result = component_extractor.extract(code, "Layout.astro")
        comps = result.get('components', [])
        assert len(comps) >= 1
        comp = comps[0]
        # Should find default slot + named slots
        assert len(comp.slots) >= 2

    def test_extract_scoped_style(self, component_extractor):
        """Test scoped style detection."""
        code = """---
---
<div class="card">Hello</div>
<style>
  .card { border: 1px solid #ccc; }
</style>
"""
        result = component_extractor.extract(code, "Card.astro")
        comps = result.get('components', [])
        assert len(comps) >= 1
        assert comps[0].has_scoped_style is True

    def test_extract_global_style(self, component_extractor):
        """Test global style detection (is:global)."""
        code = """---
---
<div>Hello</div>
<style is:global>
  body { margin: 0; }
</style>
"""
        result = component_extractor.extract(code, "Global.astro")
        comps = result.get('components', [])
        assert len(comps) >= 1
        assert comps[0].has_global_style is True

    def test_extract_directives(self, component_extractor):
        """Test directive extraction (set:html, set:text, class:list, define:vars)."""
        code = """---
const rawHtml = "<b>bold</b>";
const isActive = true;
const color = "red";
---
<div set:html={rawHtml} />
<p set:text="hello" />
<div class:list={['card', { active: isActive }]} />
<style define:vars={{ color }}>
  .card { color: var(--color); }
</style>
"""
        result = component_extractor.extract(code, "Directives.astro")
        comps = result.get('components', [])
        assert len(comps) >= 1
        comp = comps[0]
        assert comp.has_set_html is True
        assert comp.has_set_text is True
        assert comp.has_class_list is True
        assert comp.has_define_vars is True

    def test_extract_view_transitions(self, component_extractor):
        """Test ViewTransitions detection."""
        code = """---
import { ViewTransitions } from 'astro:transitions';
---
<html>
  <head><ViewTransitions /></head>
  <body><slot /></body>
</html>
"""
        result = component_extractor.extract(code, "Layout.astro")
        comps = result.get('components', [])
        assert len(comps) >= 1
        assert comps[0].has_view_transitions is True

    def test_extract_fragment(self, component_extractor):
        """Test Fragment usage detection."""
        code = """---
import { Fragment } from 'astro/components';
---
<Fragment>
  <span>A</span>
  <span>B</span>
</Fragment>
"""
        result = component_extractor.extract(code, "Frag.astro")
        comps = result.get('components', [])
        assert len(comps) >= 1
        assert comps[0].has_fragment is True

    def test_extract_used_components(self, component_extractor):
        """Test detection of used components."""
        code = """---
import Header from '../components/Header.astro';
import Footer from '../components/Footer.astro';
---
<Header />
<main><slot /></main>
<Footer />
"""
        result = component_extractor.extract(code, "Layout.astro")
        comps = result.get('components', [])
        assert len(comps) >= 1
        assert len(comps[0].used_components) >= 2


# ═══════════════════════════════════════════════════════════════════
# Frontmatter Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestAstroFrontmatterExtractor:
    """Tests for AstroFrontmatterExtractor."""

    def test_extract_basic_frontmatter(self, frontmatter_extractor):
        """Test basic frontmatter extraction."""
        code = """---
const title = "Hello";
const count = 42;
---
<h1>{title}</h1>
"""
        result = frontmatter_extractor.extract(code, "page.astro")
        fm = result.get('frontmatter')
        assert fm is not None
        assert isinstance(fm, AstroFrontmatterInfo)

    def test_extract_imports(self, frontmatter_extractor):
        """Test import extraction from frontmatter."""
        code = """---
import Layout from '../layouts/Layout.astro';
import { getCollection } from 'astro:content';
import type { CollectionEntry } from 'astro:content';
---
<Layout><slot /></Layout>
"""
        result = frontmatter_extractor.extract(code, "page.astro")
        fm = result.get('frontmatter')
        assert fm is not None
        assert len(fm.imports) >= 2

    def test_extract_data_fetching_fetch(self, frontmatter_extractor):
        """Test fetch() data fetching detection."""
        code = """---
const response = await fetch('https://api.example.com/data');
const data = await response.json();
---
<div>{data.title}</div>
"""
        result = frontmatter_extractor.extract(code, "page.astro")
        fm = result.get('frontmatter')
        assert fm is not None
        assert len(fm.data_fetches) >= 1

    def test_extract_get_collection(self, frontmatter_extractor):
        """Test getCollection data fetching detection."""
        code = """---
import { getCollection } from 'astro:content';
const posts = await getCollection('blog', ({ data }) => !data.draft);
---
{posts.map(post => <p>{post.data.title}</p>)}
"""
        result = frontmatter_extractor.extract(code, "blog.astro")
        fm = result.get('frontmatter')
        assert fm is not None
        assert len(fm.data_fetches) >= 1

    def test_extract_astro_api_flags(self, frontmatter_extractor):
        """Test Astro API usage flags."""
        code = """---
const session = Astro.cookies.get('session');
if (!session) {
  return Astro.redirect('/login');
}
const url = Astro.url;
const { id } = Astro.params;
---
<p>User: {id}</p>
"""
        result = frontmatter_extractor.extract(code, "dashboard.astro")
        fm = result.get('frontmatter')
        assert fm is not None
        assert fm.uses_astro_cookies is True
        assert fm.uses_astro_redirect is True
        assert fm.uses_astro_url is True
        assert fm.uses_astro_params is True

    def test_extract_get_static_paths(self, frontmatter_extractor):
        """Test getStaticPaths detection."""
        code = """---
export async function getStaticPaths() {
  const posts = await getCollection('blog');
  return posts.map(post => ({
    params: { slug: post.slug },
    props: { post },
  }));
}
const { post } = Astro.props;
---
<h1>{post.data.title}</h1>
"""
        result = frontmatter_extractor.extract(code, "[slug].astro")
        fm = result.get('frontmatter')
        assert fm is not None
        assert fm.has_get_static_paths is True

    def test_extract_collection_config(self, frontmatter_extractor):
        """Test content collection config detection."""
        code = """
import { defineCollection, z } from 'astro:content';

export const collections = {
  blog: defineCollection({
    type: 'content',
    schema: z.object({
      title: z.string(),
      pubDate: z.coerce.date(),
    }),
  }),
};
"""
        result = frontmatter_extractor.extract(code, "src/content/config.ts")
        fm = result.get('frontmatter')
        assert fm is not None
        assert fm.is_collection_config is True
        assert len(fm.collections) >= 1

    def test_extract_typescript_detection(self, frontmatter_extractor):
        """Test TypeScript detection in frontmatter."""
        code = """---
interface Props {
  title: string;
}
const { title }: Props = Astro.props;
---
<h1>{title}</h1>
"""
        result = frontmatter_extractor.extract(code, "page.astro")
        fm = result.get('frontmatter')
        assert fm is not None
        assert fm.has_typescript is True

    def test_extract_paginate(self, frontmatter_extractor):
        """Test paginate detection."""
        code = """---
export async function getStaticPaths({ paginate }) {
  const posts = await getCollection('blog');
  return paginate(posts, { pageSize: 10 });
}
const { page } = Astro.props;
---
"""
        result = frontmatter_extractor.extract(code, "[...page].astro")
        fm = result.get('frontmatter')
        assert fm is not None
        assert fm.has_paginate is True


# ═══════════════════════════════════════════════════════════════════
# Island Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestAstroIslandExtractor:
    """Tests for AstroIslandExtractor."""

    def test_extract_client_load(self, island_extractor):
        """Test client:load directive extraction."""
        code = """---
import AuthMenu from './AuthMenu.tsx';
---
<AuthMenu client:load />
"""
        result = island_extractor.extract(code, "page.astro")
        islands = result.get('islands', [])
        assert len(islands) >= 1
        assert islands[0].directive == "client:load"

    def test_extract_client_visible(self, island_extractor):
        """Test client:visible directive extraction."""
        code = """---
import Comments from './Comments.svelte';
---
<Comments client:visible postId={post.id} />
"""
        result = island_extractor.extract(code, "page.astro")
        islands = result.get('islands', [])
        assert len(islands) >= 1
        assert islands[0].directive == "client:visible"

    def test_extract_client_idle(self, island_extractor):
        """Test client:idle directive extraction."""
        code = """---
import Analytics from './Analytics.jsx';
---
<Analytics client:idle />
"""
        result = island_extractor.extract(code, "page.astro")
        islands = result.get('islands', [])
        assert len(islands) >= 1
        assert islands[0].directive == "client:idle"

    def test_extract_client_media(self, island_extractor):
        """Test client:media directive extraction."""
        code = """---
import MobileNav from './MobileNav.tsx';
---
<MobileNav client:media="(max-width: 768px)" />
"""
        result = island_extractor.extract(code, "page.astro")
        islands = result.get('islands', [])
        assert len(islands) >= 1
        isl = islands[0]
        assert isl.directive == "client:media"
        assert "(max-width: 768px)" in (isl.media_query or "")

    def test_extract_client_only(self, island_extractor):
        """Test client:only directive extraction."""
        code = """---
import Map from './Map';
---
<Map client:only="react" />
"""
        result = island_extractor.extract(code, "page.astro")
        islands = result.get('islands', [])
        assert len(islands) >= 1
        isl = islands[0]
        assert isl.directive == "client:only"
        assert isl.only_framework == "react" or "react" in (isl.framework or "")

    def test_extract_multiple_islands(self, island_extractor):
        """Test extraction of multiple islands with different directives."""
        code = """---
import Auth from './Auth.tsx';
import Comments from './Comments.svelte';
import Analytics from './Analytics.jsx';
---
<Auth client:load />
<Comments client:visible />
<Analytics client:idle />
"""
        result = island_extractor.extract(code, "page.astro")
        islands = result.get('islands', [])
        assert len(islands) >= 3
        directives = {isl.directive for isl in islands}
        assert "client:load" in directives
        assert "client:visible" in directives
        assert "client:idle" in directives

    def test_extract_island_with_props(self, island_extractor):
        """Test island with props detection."""
        code = """---
import Counter from './Counter.tsx';
---
<Counter client:load initialCount={5} label="Click me" />
"""
        result = island_extractor.extract(code, "page.astro")
        islands = result.get('islands', [])
        assert len(islands) >= 1
        assert islands[0].has_props is True

    def test_extract_framework_detection(self, island_extractor):
        """Test framework detection from imports."""
        code = """---
import ReactCounter from './Counter.tsx';
import SvelteWidget from './Widget.svelte';
---
<ReactCounter client:load />
<SvelteWidget client:visible />
"""
        result = island_extractor.extract(code, "page.astro")
        islands = result.get('islands', [])
        frameworks = {isl.framework for isl in islands if isl.framework}
        # Should detect at least one framework
        assert len(frameworks) >= 1


# ═══════════════════════════════════════════════════════════════════
# Routing Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestAstroRoutingExtractor:
    """Tests for AstroRoutingExtractor."""

    def test_extract_static_route(self, routing_extractor):
        """Test static route extraction from file path."""
        code = """---
---
<h1>About</h1>
"""
        result = routing_extractor.extract(code, "src/pages/about.astro")
        routes = result.get('routes', [])
        assert len(routes) >= 1
        route = routes[0]
        assert isinstance(route, AstroRouteInfo)
        assert route.is_dynamic is False

    def test_extract_dynamic_route(self, routing_extractor):
        """Test dynamic route parameter extraction."""
        code = """---
export async function getStaticPaths() {
  return [{ params: { slug: 'hello' } }];
}
---
<h1>Post</h1>
"""
        result = routing_extractor.extract(code, "src/pages/blog/[slug].astro")
        routes = result.get('routes', [])
        assert len(routes) >= 1
        route = routes[0]
        assert route.is_dynamic is True
        assert "slug" in route.param_names

    def test_extract_rest_route(self, routing_extractor):
        """Test rest/catch-all route extraction."""
        code = """---
export async function getStaticPaths({ paginate }) {
  return paginate([], { pageSize: 10 });
}
---
"""
        result = routing_extractor.extract(code, "src/pages/blog/[...page].astro")
        routes = result.get('routes', [])
        assert len(routes) >= 1
        route = routes[0]
        assert route.is_rest is True

    def test_extract_api_endpoint(self, routing_extractor):
        """Test API endpoint extraction."""
        code = """
import type { APIRoute } from 'astro';

export const GET: APIRoute = async ({ params, request }) => {
  return new Response(JSON.stringify({ id: params.id }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
};

export const POST: APIRoute = async ({ request }) => {
  const body = await request.json();
  return new Response(JSON.stringify(body), { status: 201 });
};
"""
        result = routing_extractor.extract(code, "src/pages/api/posts.ts")
        endpoints = result.get('endpoints', [])
        assert len(endpoints) >= 2
        methods = {ep.method for ep in endpoints}
        assert "GET" in methods
        assert "POST" in methods

    def test_extract_middleware(self, routing_extractor):
        """Test middleware extraction."""
        code = """
import { defineMiddleware, sequence } from 'astro:middleware';

const auth = defineMiddleware(async (context, next) => {
  const token = context.cookies.get('token');
  if (!token) {
    return context.redirect('/login');
  }
  context.locals.user = await verify(token);
  return next();
});

export const onRequest = sequence(auth);
"""
        result = routing_extractor.extract(code, "src/middleware.ts")
        middleware = result.get('middleware', [])
        assert len(middleware) >= 1
        mw = middleware[0]
        assert isinstance(mw, AstroMiddlewareInfo)
        assert mw.uses_sequence is True

    def test_extract_prerender(self, routing_extractor):
        """Test prerender export detection."""
        code = """---
export const prerender = true;
---
<h1>Static Page</h1>
"""
        result = routing_extractor.extract(code, "src/pages/about.astro")
        routes = result.get('routes', [])
        assert len(routes) >= 1

    def test_extract_endpoint_json_response(self, routing_extractor):
        """Test endpoint JSON response detection."""
        code = """
export async function GET() {
  const data = await fetchData();
  return new Response(JSON.stringify(data));
}
"""
        result = routing_extractor.extract(code, "src/pages/api/data.ts")
        endpoints = result.get('endpoints', [])
        assert len(endpoints) >= 1
        assert endpoints[0].returns_json is True


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestAstroApiExtractor:
    """Tests for AstroApiExtractor."""

    def test_extract_virtual_module_imports(self, api_extractor):
        """Test virtual module import detection."""
        code = """
import { getCollection } from 'astro:content';
import { Image } from 'astro:assets';
import { ViewTransitions } from 'astro:transitions';
"""
        result = api_extractor.extract(code, "page.astro")
        imports = result.get('imports', [])
        assert len(imports) >= 3
        virtual_count = sum(1 for imp in imports if imp.is_virtual_module)
        assert virtual_count >= 3

    def test_extract_integrations(self, api_extractor):
        """Test integration detection in config file."""
        code = """
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwind from '@astrojs/tailwind';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  integrations: [react(), tailwind(), mdx(), sitemap()],
});
"""
        result = api_extractor.extract(code, "astro.config.mjs")
        integrations = result.get('integrations', [])
        assert len(integrations) >= 4
        names = [intg.name for intg in integrations]
        assert '@astrojs/react' in names or 'react' in names

    def test_extract_config(self, api_extractor):
        """Test Astro config extraction."""
        code = """
import { defineConfig } from 'astro/config';
import vercel from '@astrojs/vercel/serverless';

export default defineConfig({
  output: 'hybrid',
  adapter: vercel(),
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'fr', 'de'],
  },
  prefetch: true,
});
"""
        result = api_extractor.extract(code, "astro.config.mjs")
        config = result.get('config')
        assert config is not None
        assert isinstance(config, AstroConfigInfo)
        assert config.output_mode == "hybrid"
        assert config.has_i18n is True

    def test_extract_types(self, api_extractor):
        """Test TypeScript type detection."""
        code = """
import type { APIRoute, APIContext } from 'astro';
import type { CollectionEntry } from 'astro:content';
"""
        result = api_extractor.extract(code, "page.ts")
        types = result.get('types', [])
        assert len(types) >= 2

    def test_detect_v5_features(self, api_extractor):
        """Test v5 feature detection."""
        code = """
import { defineAction } from 'astro:actions';
import { getSecret } from 'astro:env/server';
"""
        result = api_extractor.extract(code, "actions.ts")
        version = result.get('astro_version', '')
        assert version == "v5"

    def test_detect_v4_features(self, api_extractor):
        """Test v4 feature detection."""
        code = """
import { getRelativeLocaleUrl } from 'astro:i18n';
"""
        result = api_extractor.extract(code, "nav.astro")
        version = result.get('astro_version', '')
        assert version == "v4"

    def test_detect_v3_features(self, api_extractor):
        """Test v3 feature detection."""
        code = """
import { getImage } from 'astro:assets';
const img = await getImage({ src: myImage });
"""
        result = api_extractor.extract(code, "layout.astro")
        version = result.get('astro_version', '')
        assert version == "v3"

    def test_detect_v2_features(self, api_extractor):
        """Test v2 feature detection."""
        code = """
import { defineCollection, z } from 'astro:content';
"""
        result = api_extractor.extract(code, "config.ts")
        version = result.get('astro_version', '')
        assert version == "v2"


# ═══════════════════════════════════════════════════════════════════
# EnhancedAstroParser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedAstroParser:
    """Integration tests for EnhancedAstroParser."""

    def test_is_astro_file_by_extension(self, parser):
        """Test file detection by .astro extension."""
        assert parser.is_astro_file("", "test.astro") is True

    def test_is_astro_file_by_config_name(self, parser):
        """Test file detection by config file name."""
        assert parser.is_astro_file("export default defineConfig({})", "astro.config.mjs") is True
        assert parser.is_astro_file("export default defineConfig({})", "astro.config.ts") is True

    def test_is_astro_file_by_content(self, parser):
        """Test file detection by Astro-specific content."""
        assert parser.is_astro_file("import { getCollection } from 'astro:content';", "") is True
        assert parser.is_astro_file("const data = Astro.props;", "") is True
        assert parser.is_astro_file("client:load", "") is True

    def test_is_astro_file_negative(self, parser):
        """Test that non-Astro files are not detected."""
        assert parser.is_astro_file("import React from 'react';", "app.tsx") is False
        assert parser.is_astro_file("console.log('hello');", "main.js") is False

    def test_parse_returns_astro_parse_result(self, parser):
        """Test that parse returns AstroParseResult."""
        code = """---
const title = "Hello";
---
<h1>{title}</h1>
"""
        result = parser.parse(code, "page.astro")
        assert isinstance(result, AstroParseResult)
        assert result.file_path == "page.astro"
        assert result.file_type == "astro"

    def test_parse_file_type_detection(self, parser):
        """Test file type detection."""
        assert parser.parse("", "page.astro").file_type == "astro"
        assert parser.parse("", "config.ts").file_type == "ts"
        assert parser.parse("", "config.mjs").file_type == "js"
        assert parser.parse("", "post.mdx").file_type == "mdx"

    def test_parse_framework_detection(self, parser):
        """Test framework detection via FRAMEWORK_PATTERNS."""
        code = """
import react from '@astrojs/react';
import { getCollection } from 'astro:content';
import { Image } from 'astro:assets';
"""
        result = parser.parse(code, "config.mjs")
        assert "astro-react" in result.detected_frameworks or len(result.detected_frameworks) > 0

    def test_parse_feature_detection(self, parser):
        """Test feature detection via FEATURE_PATTERNS."""
        code = """---
const { title } = Astro.props;
---
<div class:list={['card']}>
  <slot name="header" />
  <slot />
</div>
<style>
  .card { border: 1px solid; }
</style>
"""
        result = parser.parse(code, "Card.astro")
        assert "astro_props" in result.detected_features
        assert "class_list" in result.detected_features
        assert "astro_slots" in result.detected_features
        assert "scoped_style" in result.detected_features

    def test_parse_version_detection_v5(self, parser):
        """Test v5 version detection."""
        code = """
import { defineAction } from 'astro:actions';
import { getSecret } from 'astro:env/server';
"""
        result = parser.parse(code, "actions.ts")
        assert result.astro_version == "v5"

    def test_parse_version_detection_v4(self, parser):
        """Test v4 version detection."""
        code = """
import { getRelativeLocaleUrl } from 'astro:i18n';
"""
        result = parser.parse(code, "nav.ts")
        assert result.astro_version == "v4"

    def test_parse_version_detection_v3(self, parser):
        """Test v3 version detection."""
        code = """---
import { getImage } from 'astro:assets';
---
<Picture src={hero} alt="hero" />
"""
        result = parser.parse(code, "layout.astro")
        assert result.astro_version == "v3"

    def test_parse_version_detection_v2(self, parser):
        """Test v2 version detection."""
        code = """
import { defineCollection, z } from 'astro:content';
const blog = defineCollection({
  schema: z.object({ title: z.string() }),
});
"""
        result = parser.parse(code, "config.ts")
        assert result.astro_version == "v2"

    def test_parse_version_detection_v1(self, parser):
        """Test v1 version detection."""
        code = """---
const posts = await Astro.glob('../posts/*.md');
---
"""
        result = parser.parse(code, "blog.astro")
        assert result.astro_version == "v1"

    def test_parse_full_component(self, parser):
        """Test full .astro component parsing with all extractors."""
        code = """---
import Layout from '../layouts/Layout.astro';
import Counter from '../components/Counter.tsx';
import { getCollection } from 'astro:content';
import type { CollectionEntry } from 'astro:content';

interface Props {
  post: CollectionEntry<'blog'>;
}

const { post } = Astro.props;
const posts = await getCollection('blog');
---

<Layout title={post.data.title}>
  <article>
    <h1>{post.data.title}</h1>
    <Counter client:visible initialCount={0} />
    <div set:html={post.body} />
  </article>
</Layout>

<style>
  article { max-width: 65ch; margin: 0 auto; }
</style>
"""
        result = parser.parse(code, "src/pages/blog/[slug].astro")
        assert isinstance(result, AstroParseResult)
        assert result.file_type == "astro"
        assert result.has_typescript is True
        assert len(result.components) >= 1
        assert result.frontmatter is not None
        assert len(result.islands) >= 1
        assert "astro_props" in result.detected_features
        assert "set_html" in result.detected_features

    def test_parse_config_file(self, parser):
        """Test astro.config.mjs parsing."""
        code = """
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwind from '@astrojs/tailwind';
import mdx from '@astrojs/mdx';
import vercel from '@astrojs/vercel/serverless';

export default defineConfig({
  output: 'hybrid',
  adapter: vercel(),
  integrations: [react(), tailwind(), mdx()],
  i18n: { defaultLocale: 'en', locales: ['en', 'fr'] },
  prefetch: true,
});
"""
        result = parser.parse(code, "astro.config.mjs")
        assert len(result.integrations) >= 3
        assert result.config is not None

    def test_parse_middleware_file(self, parser):
        """Test middleware.ts parsing."""
        code = """
import { defineMiddleware, sequence } from 'astro:middleware';

const auth = defineMiddleware(async (context, next) => {
  const token = context.cookies.get('token');
  context.locals.user = token ? await verify(token) : null;
  return next();
});

export const onRequest = sequence(auth);
"""
        result = parser.parse(code, "src/middleware.ts")
        assert len(result.middleware) >= 1
        assert "astro-middleware" in result.detected_frameworks or "middleware" in result.detected_features

    def test_parse_api_endpoint(self, parser):
        """Test API endpoint file parsing."""
        code = """
import type { APIRoute } from 'astro';

export async function GET({ params }) {
  const data = await db.find(params.id);
  return new Response(JSON.stringify(data));
}

export async function DELETE({ params }) {
  await db.delete(params.id);
  return new Response(null, { status: 204 });
}
"""
        result = parser.parse(code, "src/pages/api/items/[id].ts")
        assert len(result.endpoints) >= 1
        assert "api_endpoint" in result.detected_features

    def test_parse_content_collection_config(self, parser):
        """Test content collection config parsing."""
        code = """
import { defineCollection, z, reference } from 'astro:content';

export const collections = {
  blog: defineCollection({
    type: 'content',
    schema: z.object({
      title: z.string(),
      author: reference('authors'),
      pubDate: z.coerce.date(),
      draft: z.boolean().default(false),
    }),
  }),
  authors: defineCollection({
    type: 'data',
    schema: z.object({
      name: z.string(),
      bio: z.string(),
    }),
  }),
};
"""
        result = parser.parse(code, "src/content/config.ts")
        assert result.has_content_collections is True
        assert len(result.collections) >= 2

    def test_parse_has_islands_flag(self, parser):
        """Test has_islands flag is set correctly."""
        code = """---
import Counter from './Counter.tsx';
---
<Counter client:load />
"""
        result = parser.parse(code, "page.astro")
        assert result.has_islands is True

    def test_parse_has_view_transitions_flag(self, parser):
        """Test has_view_transitions flag is set correctly."""
        code = """---
import { ViewTransitions } from 'astro:transitions';
---
<ViewTransitions />
"""
        result = parser.parse(code, "layout.astro")
        assert result.has_view_transitions is True

    def test_version_compare(self, parser):
        """Test version comparison utility."""
        assert EnhancedAstroParser._version_compare("v5", "v4") > 0
        assert EnhancedAstroParser._version_compare("v3", "v4") < 0
        assert EnhancedAstroParser._version_compare("v2", "v2") == 0
        assert EnhancedAstroParser._version_compare("v1", "") > 0
        assert EnhancedAstroParser._version_compare("", "v1") < 0

    def test_parse_empty_file(self, parser):
        """Test parsing empty file returns result with default component."""
        result = parser.parse("", "page.astro")
        assert isinstance(result, AstroParseResult)
        # .astro files always create a component entry for the file itself
        assert len(result.components) <= 1
        assert len(result.islands) == 0

    def test_parse_non_astro_content(self, parser):
        """Test parsing non-Astro content in a .ts file."""
        code = """
import React from 'react';
const App = () => <div>Hello</div>;
export default App;
"""
        result = parser.parse(code, "App.tsx")
        assert isinstance(result, AstroParseResult)
        # Should not crash, just return sparse result
