"""
CodeTrellis Next.js Extractors Module v1.0

Provides comprehensive extractors for Next.js framework constructs:

Page Extractor:
- NextPageExtractor: Pages Router pages (getServerSideProps, getStaticProps,
                      getStaticPaths), App Router pages (page.tsx, layout.tsx,
                      loading.tsx, error.tsx, not-found.tsx, template.tsx),
                      metadata (generateMetadata, export const metadata),
                      segment config (dynamic, revalidate, runtime, fetchCache),
                      parallel routes (@folder), intercepting routes ((..)folder),
                      route groups ((group))

Route Handler Extractor:
- NextRouteHandlerExtractor: App Router route handlers (route.ts GET/POST/PUT/DELETE/PATCH),
                               Pages Router API routes (pages/api/), Edge API routes,
                               streaming responses, Next.js middleware (middleware.ts),
                               rewrite/redirect rules

Config Extractor:
- NextConfigExtractor: next.config.js/mjs/ts parsing (images, i18n, headers,
                         rewrites, redirects, webpack, turbopack, env, basePath,
                         experimental features), instrumentation.ts, module aliases

Server Action Extractor:
- NextServerActionExtractor: 'use server' directive functions, inline server actions,
                               server action files, form actions, useFormState/useFormStatus,
                               revalidatePath/revalidateTag, mutation patterns

Data Fetching Extractor:
- NextDataFetchingExtractor: fetch() with next cache options, unstable_cache,
                               React cache(), generateStaticParams, dynamic rendering,
                               parallel data fetching, streaming with Suspense,
                               ISR (revalidate), on-demand revalidation

Part of CodeTrellis v4.33 - Next.js Language Support
"""

from .page_extractor import (
    NextPageExtractor,
    NextPageInfo,
    NextLayoutInfo,
    NextLoadingInfo,
    NextErrorInfo,
    NextTemplateInfo,
    NextMetadataInfo,
    NextSegmentConfigInfo,
)
from .route_handler_extractor import (
    NextRouteHandlerExtractor,
    NextRouteHandlerInfo,
    NextAPIRouteInfo,
    NextMiddlewareInfo,
    NextRewriteInfo,
    NextRedirectInfo,
)
from .config_extractor import (
    NextConfigExtractor,
    NextConfigInfo,
    NextImageConfigInfo,
    NextI18nConfigInfo,
    NextExperimentalInfo,
)
from .server_action_extractor import (
    NextServerActionExtractor,
    NextServerActionInfo,
    NextFormActionInfo,
)
from .data_fetching_extractor import (
    NextDataFetchingExtractor,
    NextFetchCallInfo,
    NextCacheInfo,
    NextStaticParamsInfo,
)

__all__ = [
    # Page extractor
    "NextPageExtractor",
    "NextPageInfo",
    "NextLayoutInfo",
    "NextLoadingInfo",
    "NextErrorInfo",
    "NextTemplateInfo",
    "NextMetadataInfo",
    "NextSegmentConfigInfo",
    # Route handler extractor
    "NextRouteHandlerExtractor",
    "NextRouteHandlerInfo",
    "NextAPIRouteInfo",
    "NextMiddlewareInfo",
    "NextRewriteInfo",
    "NextRedirectInfo",
    # Config extractor
    "NextConfigExtractor",
    "NextConfigInfo",
    "NextImageConfigInfo",
    "NextI18nConfigInfo",
    "NextExperimentalInfo",
    # Server action extractor
    "NextServerActionExtractor",
    "NextServerActionInfo",
    "NextFormActionInfo",
    # Data fetching extractor
    "NextDataFetchingExtractor",
    "NextFetchCallInfo",
    "NextCacheInfo",
    "NextStaticParamsInfo",
]
