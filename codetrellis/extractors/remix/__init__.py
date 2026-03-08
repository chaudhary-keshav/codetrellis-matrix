"""
CodeTrellis Remix Framework Extractors Module v1.0

Provides comprehensive extractors for Remix / React Router v7 framework constructs:

Route Extractor:
- RemixRouteExtractor: File-based routing (routes.ts config, @remix-run/fs-routes,
                        @react-router/fs-routes), nested routes, dynamic segments
                        (/:param, /*splat), layout routes, index routes, route()
                        and index() config helpers, Outlet usage, root.tsx

Loader Extractor:
- RemixLoaderExtractor: loader (server), clientLoader (browser), data fetching,
                         useLoaderData, json(), defer(), redirect(),
                         typed loader data (typeof loader, Route.LoaderArgs),
                         cache headers, streaming (defer + Await/Suspense)

Action Extractor:
- RemixActionExtractor: action (server), clientAction (browser), Form/useFetcher,
                         useActionData, request.formData(), mutations,
                         optimistic UI, revalidation, useSubmit, useNavigation

Meta Extractor:
- RemixMetaExtractor: meta function, links function, headers function,
                       handle export, ErrorBoundary, HydrateFallback,
                       shouldRevalidate, CatchBoundary (v1), V2_MetaFunction,
                       middleware, clientMiddleware

API Extractor:
- RemixApiExtractor: @remix-run/* imports, react-router imports,
                      adapters (express, cloudflare, vercel, netlify, architect, deno),
                      remix.config.js / vite.config.ts, entry.server / entry.client,
                      version detection (v1, v2, React Router v7), TypeScript types,
                      ecosystem (Prisma, Drizzle, Supabase, Tailwind, etc.)

Part of CodeTrellis v4.61 - Remix Framework Support
"""

from .route_extractor import (
    RemixRouteExtractor,
    RemixRouteInfo,
    RemixLayoutInfo,
    RemixOutletInfo,
)
from .loader_extractor import (
    RemixLoaderExtractor,
    RemixLoaderInfo,
    RemixClientLoaderInfo,
    RemixFetcherInfo,
)
from .action_extractor import (
    RemixActionExtractor,
    RemixActionInfo,
    RemixClientActionInfo,
    RemixFormInfo,
)
from .meta_extractor import (
    RemixMetaExtractor,
    RemixMetaInfo,
    RemixLinksInfo,
    RemixHeadersInfo,
    RemixErrorBoundaryInfo,
)
from .api_extractor import (
    RemixApiExtractor,
    RemixImportInfo,
    RemixAdapterInfo,
    RemixConfigInfo,
    RemixTypeInfo,
)

__all__ = [
    # Route
    "RemixRouteExtractor",
    "RemixRouteInfo",
    "RemixLayoutInfo",
    "RemixOutletInfo",
    # Loader
    "RemixLoaderExtractor",
    "RemixLoaderInfo",
    "RemixClientLoaderInfo",
    "RemixFetcherInfo",
    # Action
    "RemixActionExtractor",
    "RemixActionInfo",
    "RemixClientActionInfo",
    "RemixFormInfo",
    # Meta
    "RemixMetaExtractor",
    "RemixMetaInfo",
    "RemixLinksInfo",
    "RemixHeadersInfo",
    "RemixErrorBoundaryInfo",
    # API
    "RemixApiExtractor",
    "RemixImportInfo",
    "RemixAdapterInfo",
    "RemixConfigInfo",
    "RemixTypeInfo",
]
