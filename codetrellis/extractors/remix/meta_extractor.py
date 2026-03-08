"""
Remix Meta Extractor v1.0

Extracts meta/head-related patterns from Remix / React Router v7 files:
- meta function (title, og:title, description, etc.)
- links function (stylesheets, preload, icons)
- headers function (Cache-Control, custom headers)
- handle export (breadcrumbs, custom data)
- ErrorBoundary component
- CatchBoundary (v1)
- HydrateFallback component
- shouldRevalidate function
- middleware / clientMiddleware (RR v7)

Supports:
- Remix v1.x (meta object, CatchBoundary, V1_Meta)
- Remix v2.x (meta array of descriptors, V2_MetaFunction)
- React Router v7 (Route.MetaArgs, middleware, clientMiddleware)

Part of CodeTrellis v4.61 - Remix Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class RemixMetaInfo:
    """Information about a meta function export."""
    file_path: str = ""
    line_number: int = 0

    # Meta format
    meta_format: str = ""  # v1_object, v2_array, rr7_array
    has_title: bool = False
    has_description: bool = False
    has_og_tags: bool = False
    has_twitter_tags: bool = False
    has_charset: bool = False
    has_viewport: bool = False

    # Dynamic meta
    uses_loader_data: bool = False
    uses_params: bool = False
    uses_matches: bool = False
    uses_location: bool = False

    # Type safety
    has_typed_args: bool = False
    args_type: str = ""  # MetaFunction, V2_MetaFunction, Route.MetaArgs


@dataclass
class RemixLinksInfo:
    """Information about a links function export."""
    file_path: str = ""
    line_number: int = 0
    link_count: int = 0
    has_stylesheet: bool = False
    has_preload: bool = False
    has_icon: bool = False
    has_prefetch: bool = False
    has_canonical: bool = False


@dataclass
class RemixHeadersInfo:
    """Information about a headers function export."""
    file_path: str = ""
    line_number: int = 0
    has_cache_control: bool = False
    has_custom_headers: bool = False
    headers_list: List[str] = field(default_factory=list)


@dataclass
class RemixErrorBoundaryInfo:
    """Information about an ErrorBoundary/CatchBoundary."""
    file_path: str = ""
    line_number: int = 0
    boundary_type: str = ""  # error_boundary, catch_boundary
    uses_route_error: bool = False
    uses_is_route_error_response: bool = False
    uses_caught: bool = False  # v1 useCatch


class RemixMetaExtractor:
    """Extracts meta/head-related patterns from Remix/RR7 files."""

    # Meta function patterns
    META_FUNCTION = re.compile(
        r'export\s+(?:const|function)\s+meta\s*(?:\(\s*(?:\{\s*([^}]*)\}\s*(?::\s*(\w[\w.]*))?)?\s*\))?',
        re.MULTILINE
    )

    # Meta v1 (returns object: { title, description, ... })
    META_V1_OBJECT = re.compile(
        r'return\s*\{\s*(?:title|description|charset|viewport|"og:)',
        re.MULTILINE
    )

    # Meta v2/RR7 (returns array of descriptors)
    META_V2_ARRAY = re.compile(
        r'return\s*\[\s*(?:\{\s*(?:title|name|property|charset|httpEquiv))',
        re.MULTILINE
    )

    # Meta content detection
    META_TITLE = re.compile(r'\btitle\b\s*[:\]},]|"title"', re.MULTILINE)
    META_DESCRIPTION = re.compile(r'"description"|name:\s*["\']description["\']', re.MULTILINE)
    META_OG = re.compile(r'"og:|property:\s*["\']og:', re.MULTILINE)
    META_TWITTER = re.compile(r'"twitter:|name:\s*["\']twitter:', re.MULTILINE)
    META_CHARSET = re.compile(r'charset', re.MULTILINE)
    META_VIEWPORT = re.compile(r'viewport', re.MULTILINE)

    # Meta data sources
    META_USES_DATA = re.compile(r'\bdata\b|\bloaderData\b', re.MULTILINE)
    META_USES_PARAMS = re.compile(r'\bparams\b', re.MULTILINE)
    META_USES_MATCHES = re.compile(r'\bmatches\b', re.MULTILINE)
    META_USES_LOCATION = re.compile(r'\blocation\b', re.MULTILINE)

    # Links function
    LINKS_FUNCTION = re.compile(
        r'export\s+(?:const|function)\s+links\b',
        re.MULTILINE
    )
    LINKS_STYLESHEET = re.compile(r'rel:\s*["\']stylesheet["\']', re.MULTILINE)
    LINKS_PRELOAD = re.compile(r'rel:\s*["\']preload["\']', re.MULTILINE)
    LINKS_ICON = re.compile(r'rel:\s*["\']icon["\']', re.MULTILINE)
    LINKS_PREFETCH = re.compile(r'rel:\s*["\']prefetch["\']', re.MULTILINE)
    LINKS_CANONICAL = re.compile(r'rel:\s*["\']canonical["\']', re.MULTILINE)

    # Headers function
    HEADERS_FUNCTION = re.compile(
        r'export\s+(?:const|function)\s+headers\b',
        re.MULTILINE
    )
    HEADERS_CACHE = re.compile(r'Cache-Control', re.MULTILINE)
    HEADER_NAMES = re.compile(r'["\']([A-Z][\w-]+)["\']\s*:', re.MULTILINE)

    # Handle export
    HANDLE_EXPORT = re.compile(
        r'export\s+(?:const|let)\s+handle\s*=',
        re.MULTILINE
    )

    # ErrorBoundary
    ERROR_BOUNDARY = re.compile(
        r'export\s+(?:function|const)\s+ErrorBoundary\b',
        re.MULTILINE
    )
    USE_ROUTE_ERROR = re.compile(r'useRouteError\s*\(\s*\)', re.MULTILINE)
    IS_ROUTE_ERROR_RESPONSE = re.compile(r'isRouteErrorResponse\s*\(', re.MULTILINE)

    # CatchBoundary (v1)
    CATCH_BOUNDARY = re.compile(
        r'export\s+(?:function|const)\s+CatchBoundary\b',
        re.MULTILINE
    )
    USE_CAUGHT = re.compile(r'useCatch\s*\(\s*\)', re.MULTILINE)

    # HydrateFallback
    HYDRATE_FALLBACK = re.compile(
        r'export\s+(?:function|const)\s+HydrateFallback\b',
        re.MULTILINE
    )

    # shouldRevalidate
    SHOULD_REVALIDATE = re.compile(
        r'export\s+(?:function|const)\s+shouldRevalidate\b',
        re.MULTILINE
    )

    # Middleware (React Router v7)
    MIDDLEWARE_EXPORT = re.compile(
        r'export\s+(?:const|let)\s+middleware\s*=',
        re.MULTILINE
    )

    CLIENT_MIDDLEWARE_EXPORT = re.compile(
        r'export\s+(?:const|let)\s+clientMiddleware\s*=',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract meta/head-related information from source.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with meta, links, headers, error_boundaries, etc.
        """
        meta_info: Optional[RemixMetaInfo] = None
        links_info: Optional[RemixLinksInfo] = None
        headers_info: Optional[RemixHeadersInfo] = None
        error_boundaries: List[RemixErrorBoundaryInfo] = []

        # Extract meta
        meta_info = self._extract_meta(content, file_path)

        # Extract links
        links_info = self._extract_links(content, file_path)

        # Extract headers
        headers_info = self._extract_headers(content, file_path)

        # Extract error boundaries
        error_boundaries = self._extract_error_boundaries(content, file_path)

        return {
            'meta': meta_info,
            'links': links_info,
            'headers': headers_info,
            'error_boundaries': error_boundaries,
            'has_handle': bool(self.HANDLE_EXPORT.search(content)),
            'has_should_revalidate': bool(self.SHOULD_REVALIDATE.search(content)),
            'has_hydrate_fallback': bool(self.HYDRATE_FALLBACK.search(content)),
            'has_middleware': bool(self.MIDDLEWARE_EXPORT.search(content)),
            'has_client_middleware': bool(self.CLIENT_MIDDLEWARE_EXPORT.search(content)),
        }

    def _extract_meta(self, content: str, file_path: str) -> Optional[RemixMetaInfo]:
        """Extract meta function information."""
        match = self.META_FUNCTION.search(content)
        if not match:
            return None

        meta = RemixMetaInfo(file_path=file_path)
        meta.line_number = content[:match.start()].count('\n') + 1

        params = match.group(1) or ""
        type_name = match.group(2) or ""

        if type_name:
            meta.has_typed_args = True
            meta.args_type = type_name

        # Determine meta format
        if self.META_V1_OBJECT.search(content):
            meta.meta_format = "v1_object"
        elif self.META_V2_ARRAY.search(content):
            meta.meta_format = "v2_array"
        else:
            meta.meta_format = "v2_array"  # default to v2

        # Content detection
        meta.has_title = bool(self.META_TITLE.search(content))
        meta.has_description = bool(self.META_DESCRIPTION.search(content))
        meta.has_og_tags = bool(self.META_OG.search(content))
        meta.has_twitter_tags = bool(self.META_TWITTER.search(content))
        meta.has_charset = bool(self.META_CHARSET.search(content))
        meta.has_viewport = bool(self.META_VIEWPORT.search(content))

        # Data sources
        meta.uses_loader_data = bool(self.META_USES_DATA.search(content))
        meta.uses_params = bool(self.META_USES_PARAMS.search(content))
        meta.uses_matches = bool(self.META_USES_MATCHES.search(content))
        meta.uses_location = bool(self.META_USES_LOCATION.search(content))

        return meta

    def _extract_links(self, content: str, file_path: str) -> Optional[RemixLinksInfo]:
        """Extract links function information."""
        match = self.LINKS_FUNCTION.search(content)
        if not match:
            return None

        links = RemixLinksInfo(file_path=file_path)
        links.line_number = content[:match.start()].count('\n') + 1

        links.has_stylesheet = bool(self.LINKS_STYLESHEET.search(content))
        links.has_preload = bool(self.LINKS_PRELOAD.search(content))
        links.has_icon = bool(self.LINKS_ICON.search(content))
        links.has_prefetch = bool(self.LINKS_PREFETCH.search(content))
        links.has_canonical = bool(self.LINKS_CANONICAL.search(content))

        # Count links
        link_count = 0
        if links.has_stylesheet:
            link_count += 1
        if links.has_preload:
            link_count += 1
        if links.has_icon:
            link_count += 1
        if links.has_prefetch:
            link_count += 1
        if links.has_canonical:
            link_count += 1
        links.link_count = link_count

        return links

    def _extract_headers(self, content: str, file_path: str) -> Optional[RemixHeadersInfo]:
        """Extract headers function information."""
        match = self.HEADERS_FUNCTION.search(content)
        if not match:
            return None

        headers = RemixHeadersInfo(file_path=file_path)
        headers.line_number = content[:match.start()].count('\n') + 1

        headers.has_cache_control = bool(self.HEADERS_CACHE.search(content))

        # Extract header names
        for h_match in self.HEADER_NAMES.finditer(content):
            header_name = h_match.group(1)
            if header_name not in headers.headers_list:
                headers.headers_list.append(header_name)

        headers.has_custom_headers = len(headers.headers_list) > 0

        return headers

    def _extract_error_boundaries(self, content: str, file_path: str) -> List[RemixErrorBoundaryInfo]:
        """Extract error boundary components."""
        boundaries: List[RemixErrorBoundaryInfo] = []

        # ErrorBoundary (v2/RR7)
        eb_match = self.ERROR_BOUNDARY.search(content)
        if eb_match:
            line_num = content[:eb_match.start()].count('\n') + 1
            boundaries.append(RemixErrorBoundaryInfo(
                file_path=file_path,
                line_number=line_num,
                boundary_type="error_boundary",
                uses_route_error=bool(self.USE_ROUTE_ERROR.search(content)),
                uses_is_route_error_response=bool(self.IS_ROUTE_ERROR_RESPONSE.search(content)),
            ))

        # CatchBoundary (v1)
        cb_match = self.CATCH_BOUNDARY.search(content)
        if cb_match:
            line_num = content[:cb_match.start()].count('\n') + 1
            boundaries.append(RemixErrorBoundaryInfo(
                file_path=file_path,
                line_number=line_num,
                boundary_type="catch_boundary",
                uses_caught=bool(self.USE_CAUGHT.search(content)),
            ))

        return boundaries
