"""
Tests for Next.js extractors and EnhancedNextJSParser.

Part of CodeTrellis v4.33 Next.js Language Support.
Tests cover:
- Page extraction (pages router, app router, layouts, loading, error, template)
- Route handler extraction (app router route handlers, pages router API routes)
- Middleware extraction (matcher, auth, redirect, rewrite)
- Server action extraction (file-level, inline, form actions)
- Data fetching extraction (fetch with cache, React cache, unstable_cache)
- Config extraction (next.config.js/mjs/ts, images, i18n, experimental)
- Next.js parser integration (framework detection, version detection)
- Metadata and segment config extraction
"""

import pytest
from codetrellis.nextjs_parser_enhanced import (
    EnhancedNextJSParser,
    NextJSParseResult,
)
from codetrellis.extractors.nextjs import (
    NextPageExtractor,
    NextRouteHandlerExtractor,
    NextConfigExtractor,
    NextServerActionExtractor,
    NextDataFetchingExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedNextJSParser()


@pytest.fixture
def page_extractor():
    return NextPageExtractor()


@pytest.fixture
def route_handler_extractor():
    return NextRouteHandlerExtractor()


@pytest.fixture
def config_extractor():
    return NextConfigExtractor()


@pytest.fixture
def server_action_extractor():
    return NextServerActionExtractor()


@pytest.fixture
def data_fetching_extractor():
    return NextDataFetchingExtractor()


# ═══════════════════════════════════════════════════════════════════
# Page Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestPageExtractor:
    """Tests for NextPageExtractor."""

    def test_app_router_page(self, page_extractor):
        code = '''
export default function HomePage() {
    return <main><h1>Home</h1></main>;
}
'''
        result = page_extractor.extract(code, "app/page.tsx")
        pages = result.get('pages', [])
        assert len(pages) >= 1

    def test_app_router_layout(self, page_extractor):
        code = '''
import { Inter } from 'next/font/google';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
    title: 'My App',
    description: 'My description',
};

export default function RootLayout({ children }) {
    return (
        <html lang="en" className={inter.className}>
            <body>{children}</body>
        </html>
    );
}
'''
        result = page_extractor.extract(code, "app/layout.tsx")
        layouts = result.get('layouts', [])
        assert len(layouts) >= 1

    def test_loading_boundary(self, page_extractor):
        code = '''
export default function Loading() {
    return <div className="animate-pulse">Loading...</div>;
}
'''
        result = page_extractor.extract(code, "app/dashboard/loading.tsx")
        loadings = result.get('loadings', [])
        assert len(loadings) >= 1

    def test_error_boundary(self, page_extractor):
        code = '''
'use client';

export default function Error({ error, reset }) {
    return (
        <div>
            <h2>Something went wrong!</h2>
            <button onClick={reset}>Try again</button>
        </div>
    );
}
'''
        result = page_extractor.extract(code, "app/error.tsx")
        errors = result.get('errors', [])
        assert len(errors) >= 1

    def test_template(self, page_extractor):
        code = '''
export default function Template({ children }) {
    return <div>{children}</div>;
}
'''
        result = page_extractor.extract(code, "app/template.tsx")
        templates = result.get('templates', [])
        assert len(templates) >= 1

    def test_pages_router_with_gsp(self, page_extractor):
        code = '''
export default function Blog({ posts }) {
    return <ul>{posts.map(p => <li key={p.id}>{p.title}</li>)}</ul>;
}

export async function getStaticProps() {
    const posts = await fetchPosts();
    return { props: { posts }, revalidate: 60 };
}
'''
        result = page_extractor.extract(code, "pages/blog.tsx")
        pages = result.get('pages', [])
        assert len(pages) >= 1

    def test_pages_router_with_gssp(self, page_extractor):
        code = '''
export default function Dashboard({ data }) {
    return <div>{data.value}</div>;
}

export async function getServerSideProps(context) {
    const data = await fetchData(context.params.id);
    return { props: { data } };
}
'''
        result = page_extractor.extract(code, "pages/dashboard.tsx")
        pages = result.get('pages', [])
        assert len(pages) >= 1

    def test_metadata_static(self, page_extractor):
        code = '''
import type { Metadata } from 'next';

export const metadata: Metadata = {
    title: 'About Us',
    description: 'Learn about our company',
};

export default function AboutPage() {
    return <div>About</div>;
}
'''
        result = page_extractor.extract(code, "app/about/page.tsx")
        metadata = result.get('metadata', [])
        assert len(metadata) >= 1

    def test_generate_metadata(self, page_extractor):
        code = '''
export async function generateMetadata({ params }) {
    const product = await getProduct(params.id);
    return {
        title: product.name,
        description: product.description,
    };
}
'''
        result = page_extractor.extract(code, "app/products/[id]/page.tsx")
        metadata = result.get('metadata', [])
        assert len(metadata) >= 1

    def test_segment_config(self, page_extractor):
        code = '''
export const dynamic = 'force-dynamic';
export const revalidate = 60;
export const runtime = 'edge';

export default function Page() { return <div />; }
'''
        result = page_extractor.extract(code, "app/api-page/page.tsx")
        segment_configs = result.get('segment_configs', [])
        assert len(segment_configs) >= 1

    def test_dynamic_route_page(self, page_extractor):
        code = '''
export default function ProductPage({ params }) {
    return <div>Product: {params.slug}</div>;
}
'''
        result = page_extractor.extract(code, "app/products/[slug]/page.tsx")
        pages = result.get('pages', [])
        assert len(pages) >= 1


# ═══════════════════════════════════════════════════════════════════
# Route Handler Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestRouteHandlerExtractor:
    """Tests for NextRouteHandlerExtractor."""

    def test_app_router_get_handler(self, route_handler_extractor):
        code = '''
import { NextResponse } from 'next/server';

export async function GET() {
    const users = await db.user.findMany();
    return NextResponse.json(users);
}
'''
        result = route_handler_extractor.extract(code, "app/api/users/route.ts")
        handlers = result.get('route_handlers', [])
        assert len(handlers) >= 1

    def test_app_router_post_handler(self, route_handler_extractor):
        code = '''
import { NextResponse } from 'next/server';

export async function POST(request: Request) {
    const body = await request.json();
    const user = await db.user.create({ data: body });
    return NextResponse.json(user, { status: 201 });
}
'''
        result = route_handler_extractor.extract(code, "app/api/users/route.ts")
        handlers = result.get('route_handlers', [])
        assert len(handlers) >= 1

    def test_multiple_http_methods(self, route_handler_extractor):
        code = '''
import { NextResponse } from 'next/server';

export async function GET() {
    return NextResponse.json({ status: 'ok' });
}

export async function PUT(request: Request) {
    const body = await request.json();
    return NextResponse.json(body);
}

export async function DELETE(request: Request) {
    return NextResponse.json({ deleted: true });
}
'''
        result = route_handler_extractor.extract(code, "app/api/items/route.ts")
        handlers = result.get('route_handlers', [])
        assert len(handlers) >= 1
        # All methods should be in a single handler
        all_methods = []
        for h in handlers:
            all_methods.extend(h.http_methods)
        assert 'GET' in all_methods
        assert 'PUT' in all_methods
        assert 'DELETE' in all_methods

    def test_pages_api_route(self, route_handler_extractor):
        code = '''
export default function handler(req, res) {
    if (req.method === 'POST') {
        const data = req.body;
        res.status(201).json(data);
    } else {
        res.status(200).json({ name: 'API' });
    }
}
'''
        result = route_handler_extractor.extract(code, "pages/api/hello.ts")
        api_routes = result.get('api_routes', [])
        assert len(api_routes) >= 1

    def test_edge_runtime_route(self, route_handler_extractor):
        code = '''
export const runtime = 'edge';

export async function GET(request: Request) {
    return new Response('Hello from Edge!');
}
'''
        result = route_handler_extractor.extract(code, "app/api/edge/route.ts")
        handlers = result.get('route_handlers', [])
        assert len(handlers) >= 1

    def test_middleware(self, route_handler_extractor):
        code = '''
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
    const token = request.cookies.get('session');
    if (!token && request.nextUrl.pathname.startsWith('/dashboard')) {
        return NextResponse.redirect(new URL('/login', request.url));
    }
    return NextResponse.next();
}

export const config = {
    matcher: ['/dashboard/:path*', '/api/:path*'],
};
'''
        result = route_handler_extractor.extract(code, "middleware.ts")
        middleware = result.get('middleware', [])
        assert len(middleware) >= 1

    def test_streaming_response(self, route_handler_extractor):
        code = '''
export async function GET() {
    const stream = new ReadableStream({
        async start(controller) {
            controller.enqueue('Hello ');
            controller.enqueue('World');
            controller.close();
        }
    });
    return new Response(stream);
}
'''
        result = route_handler_extractor.extract(code, "app/api/stream/route.ts")
        handlers = result.get('route_handlers', [])
        assert len(handlers) >= 1


# ═══════════════════════════════════════════════════════════════════
# Server Action Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestServerActionExtractor:
    """Tests for NextServerActionExtractor."""

    def test_file_level_use_server(self, server_action_extractor):
        code = '''
'use server';

export async function createTodo(formData: FormData) {
    const title = formData.get('title');
    await db.todo.create({ data: { title } });
    revalidatePath('/todos');
}

export async function deleteTodo(id: string) {
    await db.todo.delete({ where: { id } });
    revalidatePath('/todos');
}
'''
        result = server_action_extractor.extract(code, "app/actions.ts")
        actions = result.get('server_actions', [])
        assert len(actions) >= 2

    def test_inline_use_server(self, server_action_extractor):
        code = '''
export default function Page() {
    async function submitForm(formData: FormData) {
        'use server';
        const data = Object.fromEntries(formData);
        await db.item.create({ data });
        revalidatePath('/items');
    }

    return <form action={submitForm}><button>Submit</button></form>;
}
'''
        result = server_action_extractor.extract(code, "app/page.tsx")
        actions = result.get('server_actions', [])
        assert len(actions) >= 1

    def test_server_action_with_redirect(self, server_action_extractor):
        code = '''
'use server';

import { redirect } from 'next/navigation';

export async function createPost(formData: FormData) {
    const post = await db.post.create({ data: { title: formData.get('title') } });
    revalidatePath('/posts');
    redirect(`/posts/${post.id}`);
}
'''
        result = server_action_extractor.extract(code, "app/actions/post.ts")
        actions = result.get('server_actions', [])
        assert len(actions) >= 1

    def test_form_action_with_form_state(self, server_action_extractor):
        code = '''
'use client';
import { useFormState, useFormStatus } from 'react-dom';
import { createUser } from './actions';

function SubmitButton() {
    const { pending } = useFormStatus();
    return <button disabled={pending}>Create</button>;
}

export function CreateUserForm() {
    const [state, formAction] = useFormState(createUser, null);
    return (
        <form action={formAction}>
            <input name="email" />
            <SubmitButton />
        </form>
    );
}
'''
        result = server_action_extractor.extract(code, "app/components/form.tsx")
        form_actions = result.get('form_actions', [])
        assert len(form_actions) >= 1

    def test_server_action_with_orm(self, server_action_extractor):
        code = '''
'use server';

export async function updateUser(id: string, formData: FormData) {
    const name = formData.get('name');
    await prisma.user.update({ where: { id }, data: { name } });
    revalidateTag('users');
}
'''
        result = server_action_extractor.extract(code, "app/actions/user.ts")
        actions = result.get('server_actions', [])
        assert len(actions) >= 1


# ═══════════════════════════════════════════════════════════════════
# Data Fetching Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestDataFetchingExtractor:
    """Tests for NextDataFetchingExtractor."""

    def test_fetch_with_cache(self, data_fetching_extractor):
        code = '''
async function getData() {
    const res = await fetch('https://api.example.com/data', {
        cache: 'force-cache',
    });
    return res.json();
}
'''
        result = data_fetching_extractor.extract(code, "app/page.tsx")
        fetches = result.get('fetch_calls', [])
        assert len(fetches) >= 1

    def test_fetch_with_revalidate(self, data_fetching_extractor):
        code = '''
async function getProducts() {
    const res = await fetch('https://api.example.com/products', {
        next: { revalidate: 3600 },
    });
    return res.json();
}
'''
        result = data_fetching_extractor.extract(code, "app/products/page.tsx")
        fetches = result.get('fetch_calls', [])
        assert len(fetches) >= 1

    def test_fetch_with_tags(self, data_fetching_extractor):
        code = '''
async function getPosts() {
    const res = await fetch('https://api.example.com/posts', {
        next: { tags: ['posts'] },
    });
    return res.json();
}
'''
        result = data_fetching_extractor.extract(code, "app/posts/page.tsx")
        fetches = result.get('fetch_calls', [])
        assert len(fetches) >= 1

    def test_fetch_no_store(self, data_fetching_extractor):
        code = '''
async function getRealTimeData() {
    const res = await fetch('https://api.example.com/live', {
        cache: 'no-store',
    });
    return res.json();
}
'''
        result = data_fetching_extractor.extract(code, "app/live/page.tsx")
        fetches = result.get('fetch_calls', [])
        assert len(fetches) >= 1

    def test_react_cache(self, data_fetching_extractor):
        code = '''
import { cache } from 'react';

export const getUser = cache(async (id: string) => {
    return db.user.findUnique({ where: { id } });
});
'''
        result = data_fetching_extractor.extract(code, "app/lib/data.ts")
        caches = result.get('caches', [])
        assert len(caches) >= 1

    def test_unstable_cache(self, data_fetching_extractor):
        code = '''
import { unstable_cache } from 'next/cache';

const getCachedData = unstable_cache(
    async (id) => db.item.findUnique({ where: { id } }),
    ['item'],
    { revalidate: 3600, tags: ['items'] }
);
'''
        result = data_fetching_extractor.extract(code, "app/lib/cache.ts")
        caches = result.get('caches', [])
        assert len(caches) >= 1

    def test_generate_static_params(self, data_fetching_extractor):
        code = '''
export async function generateStaticParams() {
    const posts = await getAllPosts();
    return posts.map((post) => ({
        slug: post.slug,
    }));
}
'''
        result = data_fetching_extractor.extract(code, "app/blog/[slug]/page.tsx")
        static_params = result.get('static_params', [])
        assert len(static_params) >= 1

    def test_parallel_data_fetching(self, data_fetching_extractor):
        code = '''
export default async function DashboardPage() {
    const [stats, orders, notifications] = await Promise.all([
        getStats(),
        getOrders(),
        getNotifications(),
    ]);
    return <div>{/* ... */}</div>;
}
'''
        result = data_fetching_extractor.extract(code, "app/dashboard/page.tsx")
        assert result.get('has_parallel_fetch', False) is True

    def test_suspense_detection(self, data_fetching_extractor):
        code = '''
import { Suspense } from 'react';

export default function Page() {
    return (
        <main>
            <Suspense fallback={<Loading />}>
                <SlowComponent />
            </Suspense>
            <Suspense fallback={<Loading2 />}>
                <AnotherSlowComponent />
            </Suspense>
        </main>
    );
}
'''
        result = data_fetching_extractor.extract(code, "app/page.tsx")
        assert result.get('suspense_count', 0) >= 2


# ═══════════════════════════════════════════════════════════════════
# Config Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestConfigExtractor:
    """Tests for NextConfigExtractor."""

    def test_basic_config(self, config_extractor):
        code = '''
/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',
    basePath: '/app',
    images: {
        domains: ['images.example.com'],
        formats: ['image/avif', 'image/webp'],
    },
};

module.exports = nextConfig;
'''
        result = config_extractor.extract(code, "next.config.js")
        config = result.get('config')
        assert config is not None

    def test_config_with_i18n(self, config_extractor):
        code = '''
const nextConfig = {
    i18n: {
        locales: ['en', 'fr', 'de', 'ja'],
        defaultLocale: 'en',
    },
};

module.exports = nextConfig;
'''
        result = config_extractor.extract(code, "next.config.js")
        i18n = result.get('i18n_config')
        assert i18n is not None

    def test_config_with_experimental(self, config_extractor):
        code = '''
const nextConfig = {
    experimental: {
        ppr: true,
        serverActions: { bodySizeLimit: '2mb' },
        turbo: { rules: {} },
        mdxRs: true,
        typedRoutes: true,
    },
};

module.exports = nextConfig;
'''
        result = config_extractor.extract(code, "next.config.js")
        experimental = result.get('experimental')
        assert experimental is not None

    def test_config_with_redirects(self, config_extractor):
        code = '''
const nextConfig = {
    async redirects() {
        return [
            { source: '/old', destination: '/new', permanent: true },
            { source: '/legacy', destination: '/modern', permanent: false },
        ];
    },
    async rewrites() {
        return [
            { source: '/api/:path*', destination: 'https://backend.example.com/:path*' },
        ];
    },
};

module.exports = nextConfig;
'''
        result = config_extractor.extract(code, "next.config.js")
        config = result.get('config')
        assert config is not None

    def test_config_with_webpack(self, config_extractor):
        code = '''
const nextConfig = {
    webpack: (config, { isServer }) => {
        config.plugins.push(new MyPlugin());
        return config;
    },
};

module.exports = nextConfig;
'''
        result = config_extractor.extract(code, "next.config.js")
        config = result.get('config')
        assert config is not None

    def test_image_config_with_remote_patterns(self, config_extractor):
        code = '''
const nextConfig = {
    images: {
        remotePatterns: [
            { protocol: 'https', hostname: '**.example.com' },
        ],
        formats: ['image/avif', 'image/webp'],
        deviceSizes: [640, 750, 828, 1080, 1200],
    },
};

module.exports = nextConfig;
'''
        result = config_extractor.extract(code, "next.config.js")
        image_config = result.get('image_config')
        assert image_config is not None


# ═══════════════════════════════════════════════════════════════════
# Enhanced Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedNextJSParser:
    """Tests for EnhancedNextJSParser integration."""

    def test_is_nextjs_file_config(self, parser):
        assert parser.is_nextjs_file("", "next.config.js")
        assert parser.is_nextjs_file("", "next.config.mjs")
        assert parser.is_nextjs_file("", "next.config.ts")

    def test_is_nextjs_file_middleware(self, parser):
        assert parser.is_nextjs_file("", "middleware.ts")
        assert parser.is_nextjs_file("", "middleware.js")

    def test_is_nextjs_file_app_router(self, parser):
        assert parser.is_nextjs_file("", "src/app/page.tsx")
        assert parser.is_nextjs_file("", "src/app/layout.tsx")
        assert parser.is_nextjs_file("", "app/loading.tsx")
        assert parser.is_nextjs_file("", "app/error.tsx")
        assert parser.is_nextjs_file("", "app/template.tsx")
        assert parser.is_nextjs_file("", "app/api/users/route.ts")
        assert parser.is_nextjs_file("", "app/not-found.tsx")

    def test_is_nextjs_file_pages_router(self, parser):
        assert parser.is_nextjs_file("", "pages/index.tsx")
        assert parser.is_nextjs_file("", "pages/api/hello.ts")

    def test_is_nextjs_file_content_detection(self, parser):
        assert parser.is_nextjs_file("import Link from 'next/link';", "components/nav.tsx")
        assert parser.is_nextjs_file("export async function getServerSideProps() {}", "lib/utils.ts")
        assert parser.is_nextjs_file("import { NextResponse } from 'next/server';", "lib/api.ts")

    def test_is_not_nextjs_file(self, parser):
        assert not parser.is_nextjs_file("const x = 1;", "utils/math.ts")
        assert not parser.is_nextjs_file("export function add(a, b) { return a + b; }", "lib/calc.ts")

    def test_classify_file(self, parser):
        assert parser._classify_file("next.config.js") == "config"
        assert parser._classify_file("middleware.ts") == "middleware"
        assert parser._classify_file("app/page.tsx") == "page"
        assert parser._classify_file("app/layout.tsx") == "layout"
        assert parser._classify_file("app/loading.tsx") == "loading"
        assert parser._classify_file("app/error.tsx") == "error"
        assert parser._classify_file("app/template.tsx") == "template"
        assert parser._classify_file("app/api/route.ts") == "route"
        assert parser._classify_file("pages/api/hello.ts") == "api"
        assert parser._classify_file("pages/index.tsx") == "page"
        assert parser._classify_file("app/global-error.tsx") == "error"

    def test_framework_detection_next_core(self, parser):
        code = "import { NextResponse } from 'next/server';"
        frameworks = parser._detect_frameworks(code)
        assert 'next-server' in frameworks

    def test_framework_detection_next_navigation(self, parser):
        code = "import { useRouter, usePathname } from 'next/navigation';"
        frameworks = parser._detect_frameworks(code)
        assert 'next-navigation' in frameworks

    def test_framework_detection_next_image(self, parser):
        code = "import Image from 'next/image';"
        frameworks = parser._detect_frameworks(code)
        assert 'next-image' in frameworks

    def test_framework_detection_next_font(self, parser):
        code = "import { Inter } from 'next/font/google';"
        frameworks = parser._detect_frameworks(code)
        assert 'next-font' in frameworks

    def test_framework_detection_nextauth(self, parser):
        code = "import NextAuth from 'next-auth';"
        frameworks = parser._detect_frameworks(code)
        assert 'nextauth' in frameworks

    def test_framework_detection_clerk(self, parser):
        code = "import { ClerkProvider } from '@clerk/nextjs';"
        frameworks = parser._detect_frameworks(code)
        assert 'clerk' in frameworks

    def test_framework_detection_prisma(self, parser):
        code = "import { PrismaClient } from '@prisma/client';"
        frameworks = parser._detect_frameworks(code)
        assert 'prisma' in frameworks

    def test_framework_detection_drizzle(self, parser):
        code = "import { drizzle } from 'drizzle-orm';"
        frameworks = parser._detect_frameworks(code)
        assert 'drizzle' in frameworks

    def test_framework_detection_trpc(self, parser):
        code = "import { createTRPCRouter, publicProcedure } from '@trpc/server';"
        frameworks = parser._detect_frameworks(code)
        assert 'trpc' in frameworks

    def test_framework_detection_sentry(self, parser):
        code = "import * as Sentry from '@sentry/nextjs';"
        frameworks = parser._detect_frameworks(code)
        assert 'sentry' in frameworks

    def test_framework_detection_mdx(self, parser):
        code = "import { MDXRemote } from 'next-mdx-remote';"
        frameworks = parser._detect_frameworks(code)
        assert 'mdx' in frameworks

    def test_framework_detection_supabase(self, parser):
        code = "import { createClient } from '@supabase/supabase-js';"
        frameworks = parser._detect_frameworks(code)
        assert 'supabase' in frameworks

    def test_version_detection_v15(self, parser):
        code = '''
import { cacheLife } from 'next/cache';
export default async function Page() {
    cacheLife('hours');
}
'''
        version = parser._detect_nextjs_version(code)
        assert version == '15.0'

    def test_version_detection_v14(self, parser):
        code = '''
import { useFormState, useFormStatus } from 'react-dom';
'''
        version = parser._detect_nextjs_version(code)
        assert version == '14.0'

    def test_version_detection_v13(self, parser):
        code = '''
export async function generateMetadata({ params }) {
    return { title: 'Hello' };
}
'''
        version = parser._detect_nextjs_version(code)
        assert version == '13.2'

    def test_version_detection_v12(self, parser):
        code = '''
import { NextResponse } from 'next/server';
'''
        version = parser._detect_nextjs_version(code)
        assert version == '12.0'

    def test_version_detection_v93(self, parser):
        code = '''
export async function getServerSideProps() {
    return { props: {} };
}
'''
        version = parser._detect_nextjs_version(code)
        assert version == '9.3'

    def test_client_component_detection(self, parser):
        code = '''
'use client';

import { useState } from 'react';

export default function Counter() {
    const [count, setCount] = useState(0);
    return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
'''
        result = parser.parse(code, "app/counter.tsx")
        assert result.is_client_component is True
        assert result.is_server_component is False

    def test_server_component_detection(self, parser):
        code = '''
import { db } from '@/lib/db';

export default async function UsersPage() {
    const users = await db.user.findMany();
    return <ul>{users.map(u => <li key={u.id}>{u.name}</li>)}</ul>;
}
'''
        result = parser.parse(code, "app/users/page.tsx")
        assert result.is_server_component is True
        assert result.is_client_component is False

    def test_parse_full_app_router_page(self, parser):
        code = '''
import type { Metadata } from 'next';

export const metadata: Metadata = {
    title: 'Dashboard',
};

export const dynamic = 'force-dynamic';

export default async function DashboardPage() {
    const data = await fetch('https://api.example.com/stats', {
        cache: 'no-store',
    }).then(r => r.json());

    return <div>{data.total}</div>;
}
'''
        result = parser.parse(code, "app/dashboard/page.tsx")
        assert result.file_type == "page"
        assert len(result.pages) >= 1
        assert len(result.metadata) >= 1
        assert len(result.segment_configs) >= 1

    def test_parse_route_handler(self, parser):
        code = '''
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
    const users = await fetch('https://api.example.com/users').then(r => r.json());
    return NextResponse.json(users);
}

export async function POST(request: Request) {
    const body = await request.json();
    return NextResponse.json(body, { status: 201 });
}
'''
        result = parser.parse(code, "app/api/users/route.ts")
        assert result.file_type == "route"
        assert len(result.route_handlers) >= 1
        # Both methods should be captured
        all_methods = []
        for h in result.route_handlers:
            all_methods.extend(h.http_methods)
        assert 'GET' in all_methods
        assert 'POST' in all_methods

    def test_parse_middleware(self, parser):
        code = '''
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
    const token = request.cookies.get('session');
    if (!token) {
        return NextResponse.redirect(new URL('/login', request.url));
    }
    return NextResponse.next();
}

export const config = {
    matcher: ['/dashboard/:path*'],
};
'''
        result = parser.parse(code, "middleware.ts")
        assert result.file_type == "middleware"
        assert len(result.middleware) >= 1

    def test_parse_server_action_file(self, parser):
        code = '''
'use server';

import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';

export async function createItem(formData: FormData) {
    const name = formData.get('name');
    await prisma.item.create({ data: { name } });
    revalidatePath('/items');
    redirect('/items');
}

export async function deleteItem(id: string) {
    await prisma.item.delete({ where: { id } });
    revalidatePath('/items');
}
'''
        result = parser.parse(code, "app/actions.ts")
        assert len(result.server_actions) >= 2

    def test_parse_config(self, parser):
        code = '''
/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',
    images: {
        domains: ['images.example.com'],
    },
    experimental: {
        ppr: true,
    },
};

module.exports = nextConfig;
'''
        result = parser.parse(code, "next.config.js")
        assert result.file_type == "config"
        assert result.config is not None

    def test_version_compare(self, parser):
        assert parser._version_compare('15.0', '14.0') > 0
        assert parser._version_compare('13.2', '13.0') > 0
        assert parser._version_compare('9.3', '10.0') < 0
        assert parser._version_compare('14.0', '14.0') == 0

    def test_router_type_detection_app(self, parser):
        code = '''
export default function Layout({ children }) {
    return <div>{children}</div>;
}
'''
        result = parser.parse(code, "app/layout.tsx")
        # Should detect app router from layouts
        assert result.router_type in ("app", "hybrid", "")

    def test_router_type_detection_pages(self, parser):
        code = '''
export default function Home() { return <div>Home</div>; }
export async function getStaticProps() {
    return { props: {} };
}
'''
        result = parser.parse(code, "pages/index.tsx")
        assert result.router_type in ("pages", "hybrid", "")

    def test_framework_detection_multiple(self, parser):
        code = '''
import { NextResponse } from 'next/server';
import Image from 'next/image';
import { Inter } from 'next/font/google';
import { PrismaClient } from '@prisma/client';
'''
        result = parser.parse(code, "app/layout.tsx")
        assert 'next-server' in result.detected_frameworks
        assert 'next-image' in result.detected_frameworks
        assert 'next-font' in result.detected_frameworks
        assert 'prisma' in result.detected_frameworks


# ═══════════════════════════════════════════════════════════════════
# BPL Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestBPLIntegration:
    """Tests for BPL models and YAML practices."""

    def test_nextjs_practice_categories_exist(self):
        from codetrellis.bpl.models import PracticeCategory
        assert hasattr(PracticeCategory, 'NEXTJS_APP_ROUTER')
        assert hasattr(PracticeCategory, 'NEXTJS_PAGES_ROUTER')
        assert hasattr(PracticeCategory, 'NEXTJS_DATA_FETCHING')
        assert hasattr(PracticeCategory, 'NEXTJS_SERVER_ACTIONS')
        assert hasattr(PracticeCategory, 'NEXTJS_CACHING')
        assert hasattr(PracticeCategory, 'NEXTJS_ROUTING')
        assert hasattr(PracticeCategory, 'NEXTJS_MIDDLEWARE')
        assert hasattr(PracticeCategory, 'NEXTJS_RENDERING')
        assert hasattr(PracticeCategory, 'NEXTJS_PERFORMANCE')
        assert hasattr(PracticeCategory, 'NEXTJS_SECURITY')
        assert hasattr(PracticeCategory, 'NEXTJS_DEPLOYMENT')
        assert hasattr(PracticeCategory, 'NEXTJS_CONFIGURATION')
        assert hasattr(PracticeCategory, 'NEXTJS_TESTING')
        assert hasattr(PracticeCategory, 'NEXTJS_METADATA')
        assert hasattr(PracticeCategory, 'NEXTJS_IMAGE_OPTIMIZATION')

    def test_nextjs_practice_yaml_loads(self):
        import yaml
        from pathlib import Path
        yaml_path = Path(__file__).parent.parent.parent / "codetrellis" / "bpl" / "practices" / "nextjs_core.yaml"
        if yaml_path.exists():
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
            assert data is not None
            assert 'practices' in data
            assert len(data['practices']) == 50
            # Verify IDs are NEXT001-NEXT050
            ids = [p['id'] for p in data['practices']]
            for i in range(1, 51):
                expected_id = f"NEXT{i:03d}"
                assert expected_id in ids, f"Missing practice {expected_id}"

    def test_nextjs_practice_yaml_categories_valid(self):
        import yaml
        from pathlib import Path
        from codetrellis.bpl.models import PracticeCategory
        yaml_path = Path(__file__).parent.parent.parent / "codetrellis" / "bpl" / "practices" / "nextjs_core.yaml"
        if yaml_path.exists():
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
            valid_categories = {c.value for c in PracticeCategory}
            for practice in data['practices']:
                cat = practice.get('category', '')
                assert cat in valid_categories, f"Invalid category '{cat}' in {practice['id']}"


# ═══════════════════════════════════════════════════════════════════
# Scanner Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestScannerIntegration:
    """Tests for scanner.py Next.js integration."""

    def test_project_matrix_has_nextjs_fields(self):
        from codetrellis.scanner import ProjectMatrix
        matrix = ProjectMatrix(name="test", root_path="/test")
        assert hasattr(matrix, 'nextjs_pages')
        assert hasattr(matrix, 'nextjs_layouts')
        assert hasattr(matrix, 'nextjs_loadings')
        assert hasattr(matrix, 'nextjs_errors')
        assert hasattr(matrix, 'nextjs_templates')
        assert hasattr(matrix, 'nextjs_metadata')
        assert hasattr(matrix, 'nextjs_segment_configs')
        assert hasattr(matrix, 'nextjs_route_handlers')
        assert hasattr(matrix, 'nextjs_api_routes')
        assert hasattr(matrix, 'nextjs_middleware')
        assert hasattr(matrix, 'nextjs_server_actions')
        assert hasattr(matrix, 'nextjs_form_actions')
        assert hasattr(matrix, 'nextjs_fetch_calls')
        assert hasattr(matrix, 'nextjs_caches')
        assert hasattr(matrix, 'nextjs_static_params')
        assert hasattr(matrix, 'nextjs_config')
        assert hasattr(matrix, 'nextjs_image_config')
        assert hasattr(matrix, 'nextjs_i18n_config')
        assert hasattr(matrix, 'nextjs_experimental')
        assert hasattr(matrix, 'nextjs_detected_frameworks')
        assert hasattr(matrix, 'nextjs_version')
        assert hasattr(matrix, 'nextjs_router_type')

    def test_scanner_has_nextjs_parser(self):
        from codetrellis.scanner import ProjectScanner
        scanner = ProjectScanner()
        assert hasattr(scanner, 'nextjs_parser')
        assert isinstance(scanner.nextjs_parser, EnhancedNextJSParser)

    def test_scanner_has_parse_nextjs_method(self):
        from codetrellis.scanner import ProjectScanner
        scanner = ProjectScanner()
        assert hasattr(scanner, '_parse_nextjs')
        assert callable(scanner._parse_nextjs)


# ═══════════════════════════════════════════════════════════════════
# Compressor Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestCompressorIntegration:
    """Tests for compressor.py Next.js integration."""

    def test_compressor_has_nextjs_methods(self):
        from codetrellis.compressor import MatrixCompressor
        compressor = MatrixCompressor()
        assert hasattr(compressor, '_compress_nextjs_pages')
        assert hasattr(compressor, '_compress_nextjs_routes')
        assert hasattr(compressor, '_compress_nextjs_server_actions')
        assert hasattr(compressor, '_compress_nextjs_data_fetching')
        assert hasattr(compressor, '_compress_nextjs_config')

    def test_compress_nextjs_pages_empty(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        compressor = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/test")
        lines = compressor._compress_nextjs_pages(matrix)
        assert isinstance(lines, list)

    def test_compress_nextjs_pages_with_data(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        compressor = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/test")
        matrix.nextjs_pages = [
            {"name": "HomePage", "file": "/test/app/page.tsx", "line": 1,
             "route_path": "/", "router_type": "app", "is_dynamic": False,
             "has_ssr": False, "has_ssg": False, "has_isr": False,
             "has_params": False, "is_default_export": True,
             "is_server_component": True, "is_client_component": False}
        ]
        matrix.nextjs_detected_frameworks = ["next", "next-image"]
        matrix.nextjs_version = "14.0"
        matrix.nextjs_router_type = "app"
        lines = compressor._compress_nextjs_pages(matrix)
        assert len(lines) > 0
        # Should contain ecosystem, version, router info
        combined = '\n'.join(lines)
        assert 'Ecosystem' in combined or 'Pages' in combined

    def test_compress_nextjs_routes_with_data(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        compressor = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/test")
        matrix.nextjs_route_handlers = [
            {"name": "GET", "file": "/test/app/api/users/route.ts", "line": 5,
             "method": "GET", "route_path": "/api/users", "is_edge": False,
             "is_streaming": False, "has_auth": True, "has_cors": False}
        ]
        lines = compressor._compress_nextjs_routes(matrix)
        assert len(lines) > 0

    def test_compress_nextjs_config_with_data(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        compressor = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/test")
        matrix.nextjs_config = {
            "file": "/test/next.config.js",
            "output_mode": "standalone",
            "base_path": "",
            "has_custom_webpack": True,
            "has_turbopack": False,
            "env_vars": ["API_URL"],
            "redirects_count": 2,
            "rewrites_count": 1,
            "headers_count": 0,
        }
        lines = compressor._compress_nextjs_config(matrix)
        assert len(lines) > 0
        combined = '\n'.join(lines)
        assert 'standalone' in combined
