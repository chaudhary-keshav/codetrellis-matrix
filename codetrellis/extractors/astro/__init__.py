"""
CodeTrellis Astro Framework Extractors Module v1.0

Provides comprehensive extractors for Astro framework constructs:

Component Extractor:
- AstroComponentExtractor: .astro component files, Astro.props interface,
                            TypeScript Props type, slots (default/named),
                            HTML template expressions ({expression}), component imports,
                            <Fragment>, set:html/set:text directives,
                            class:list and style objects, define:vars

Frontmatter Extractor:
- AstroFrontmatterExtractor: --- fenced code blocks, import statements,
                              variable declarations, data fetching (fetch/Astro.glob/
                              getCollection/getEntry), TypeScript types,
                              exported functions, Astro.redirect, Astro.response,
                              content collections schema (defineCollection/z)

Island Extractor:
- AstroIslandExtractor: client:load, client:idle, client:visible,
                         client:media, client:only directives for partial
                         hydration, framework component detection
                         (React/Vue/Svelte/Solid/Preact/Lit/Alpine)

Routing Extractor:
- AstroRoutingExtractor: File-based routing (src/pages/), dynamic routes
                          ([param], [...spread], [...rest]), API endpoints
                          (GET/POST/PUT/DELETE/PATCH/ALL in .ts/.js),
                          middleware (src/middleware.ts), SSR/SSG/hybrid
                          rendering modes, redirects, rewrites,
                          i18n routing, view transitions

API Extractor:
- AstroApiExtractor: Astro imports (astro:content, astro:assets, astro:transitions,
                      astro:middleware, astro:i18n, astro:env),
                      integrations (@astrojs/react, @astrojs/vue, @astrojs/svelte,
                      @astrojs/solid-js, @astrojs/preact, @astrojs/lit,
                      @astrojs/tailwind, @astrojs/mdx, @astrojs/image,
                      @astrojs/sitemap, @astrojs/partytown, @astrojs/db,
                      @astrojs/node, @astrojs/vercel, @astrojs/netlify,
                      @astrojs/cloudflare), astro.config.mjs detection,
                      TypeScript types, version detection (v1-v5)

Part of CodeTrellis v4.60 - Astro Framework Support
"""

from .component_extractor import (
    AstroComponentExtractor,
    AstroComponentInfo,
    AstroSlotInfo,
    AstroExpressionInfo,
)
from .frontmatter_extractor import (
    AstroFrontmatterExtractor,
    AstroFrontmatterInfo,
    AstroDataFetchInfo,
    AstroCollectionInfo,
)
from .island_extractor import (
    AstroIslandExtractor,
    AstroIslandInfo,
)
from .routing_extractor import (
    AstroRoutingExtractor,
    AstroRouteInfo,
    AstroEndpointInfo,
    AstroMiddlewareInfo,
)
from .api_extractor import (
    AstroApiExtractor,
    AstroImportInfo,
    AstroIntegrationInfo,
    AstroConfigInfo,
    AstroTypeInfo,
)

__all__ = [
    # Component
    "AstroComponentExtractor",
    "AstroComponentInfo",
    "AstroSlotInfo",
    "AstroExpressionInfo",
    # Frontmatter
    "AstroFrontmatterExtractor",
    "AstroFrontmatterInfo",
    "AstroDataFetchInfo",
    "AstroCollectionInfo",
    # Island
    "AstroIslandExtractor",
    "AstroIslandInfo",
    # Routing
    "AstroRoutingExtractor",
    "AstroRouteInfo",
    "AstroEndpointInfo",
    "AstroMiddlewareInfo",
    # API
    "AstroApiExtractor",
    "AstroImportInfo",
    "AstroIntegrationInfo",
    "AstroConfigInfo",
    "AstroTypeInfo",
]
