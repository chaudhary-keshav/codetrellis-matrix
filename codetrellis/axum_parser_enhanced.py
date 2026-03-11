"""
EnhancedAxumParser v1.0 - Comprehensive Axum framework parser.

Extracts Axum-specific patterns from Rust source files:
- Router routes (.route(), .nest(), .merge())
- Handler functions with extractors (State, Json, Path, Query, Extension)
- Middleware layers (tower::ServiceBuilder, from_fn, middleware::map_request)
- State management (with_state, FromRef)
- Error handling (IntoResponse, rejection)
- WebSocket (ws::WebSocket, ws::WebSocketUpgrade)
- Typed headers and extractors
- Tower layer/service integration
- Router nesting and merging
- Fallback handlers

Supports Axum 0.5 through 0.8+.

Part of CodeTrellis - Rust Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


# ─── Dataclasses ────────────────────────────────────────────────────────────────

@dataclass
class AxumRouteInfo:
    """Axum route definition."""
    method: str  # get, post, put, delete, patch, any, method_routing
    path: str
    handler: str
    file: str = ""
    line_number: int = 0
    extractors: List[str] = field(default_factory=list)
    is_nested: bool = False
    is_merged: bool = False


@dataclass
class AxumLayerInfo:
    """Axum middleware layer."""
    name: str
    kind: str = ""  # layer, from_fn, map_request, map_response, tower
    file: str = ""
    line_number: int = 0
    is_custom: bool = False


@dataclass
class AxumExtractorInfo:
    """Axum extractor usage."""
    extractor_type: str  # State, Json, Path, Query, Extension, Form, etc.
    inner_type: str = ""
    handler: str = ""
    file: str = ""
    line_number: int = 0
    is_custom: bool = False


@dataclass
class AxumStateInfo:
    """Axum application state."""
    type_name: str
    registration: str = ""  # with_state, Extension, FromRef
    file: str = ""
    line_number: int = 0


@dataclass
class AxumErrorInfo:
    """Axum error handling."""
    name: str
    kind: str = ""  # IntoResponse, rejection, error handler
    file: str = ""
    line_number: int = 0


@dataclass
class AxumWebSocketInfo:
    """Axum WebSocket endpoint."""
    handler: str
    path: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class AxumNestInfo:
    """Axum router nesting."""
    path: str
    router: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class AxumParseResult:
    """Complete parse result for Axum framework analysis."""
    file_path: str
    file_type: str = "rust"

    routes: List[AxumRouteInfo] = field(default_factory=list)
    layers: List[AxumLayerInfo] = field(default_factory=list)
    extractors: List[AxumExtractorInfo] = field(default_factory=list)
    state: List[AxumStateInfo] = field(default_factory=list)
    errors: List[AxumErrorInfo] = field(default_factory=list)
    websockets: List[AxumWebSocketInfo] = field(default_factory=list)
    nests: List[AxumNestInfo] = field(default_factory=list)

    detected_frameworks: List[str] = field(default_factory=list)
    axum_version: str = ""


# ─── Parser ─────────────────────────────────────────────────────────────────────

class EnhancedAxumParser:
    """
    Enhanced Axum parser for comprehensive framework analysis.

    Supports Axum 0.5 through 0.8+:
    - v0.5: First stable release, Router, extractors
    - v0.6: State extraction rework, with_state API
    - v0.7: Router simplification, path-based nesting
    - v0.8+: Improved type inference, new middleware patterns
    """

    AXUM_DETECT = re.compile(
        r'(?:use\s+axum|axum::|Router::new|axum::Router)',
        re.MULTILINE
    )

    FRAMEWORK_PATTERNS = {
        'axum': re.compile(r'\baxum\b'),
        'axum-extra': re.compile(r'\baxum_extra\b'),
        'axum-macros': re.compile(r'\baxum_macros\b'),
        'tower': re.compile(r'\btower\b'),
        'tower-http': re.compile(r'\btower_http\b'),
        'tower-cookies': re.compile(r'\btower_cookies\b'),
        'tower-sessions': re.compile(r'\btower_sessions\b'),
        'axum-login': re.compile(r'\baxum_login\b'),
        'axum-csrf': re.compile(r'\baxum_csrf\b'),
        'axum-template': re.compile(r'\baxum_template\b'),
    }

    # .route("/path", get(handler)) or .route("/path", get(handler).post(handler2))
    ROUTE_PATTERN = re.compile(
        r'\.route\s*\(\s*"(?P<path>[^"]+)"\s*,\s*(?P<methods>[^)]+)\)',
        re.MULTILINE
    )

    # Method handler in route: get(handler), post(handler), etc.
    METHOD_HANDLER = re.compile(
        r'(?P<method>get|post|put|delete|patch|head|options|any|trace)\s*\(\s*(?P<handler>[a-zA-Z_]\w*)',
    )

    # .nest("/path", router)
    NEST_PATTERN = re.compile(
        r'\.nest\s*\(\s*"(?P<path>[^"]+)"\s*,\s*(?P<router>[^)]+)\)',
        re.MULTILINE
    )

    # .merge(router)
    MERGE_PATTERN = re.compile(
        r'\.merge\s*\(\s*(?P<router>[^)]+)\)',
        re.MULTILINE
    )

    # .layer(xxx)
    LAYER_PATTERN = re.compile(
        r'\.layer\s*\(\s*(?P<layer>[^)]+)\)',
        re.MULTILINE
    )

    # middleware::from_fn(xxx) / middleware::map_request / middleware::map_response
    MIDDLEWARE_FN = re.compile(
        r'middleware::(?P<kind>from_fn|from_fn_with_state|map_request|map_response)\s*(?:\(\s*(?P<name>[a-zA-Z_]\w*))?',
        re.MULTILINE
    )

    # Axum extractors in function params
    EXTRACTOR_PATTERN = re.compile(
        r'(?:axum::extract::)?(?P<type>State|Json|Path|Query|Extension|Form|Multipart|ConnectInfo|OriginalUri|MatchedPath|Host|RawQuery|BodyStream|TypedHeader|HeaderMap)\s*(?:<\s*(?P<inner>[^>]+)>)?',
    )

    # with_state
    WITH_STATE = re.compile(
        r'\.with_state\s*\(\s*(?P<state>[^)]+)\)',
        re.MULTILINE
    )

    # Extension::from
    EXTENSION = re.compile(
        r'Extension\s*\(\s*(?P<type>\w+)',
    )

    # FromRef derive / impl
    FROM_REF = re.compile(
        r'(?:#\[derive\([^)]*FromRef[^)]*\)\]|impl\s+FromRef\s*<[^>]+>\s+for\s+(?P<name>\w+))',
        re.MULTILINE
    )

    # IntoResponse impl
    INTO_RESPONSE = re.compile(
        r'impl\s+(?:axum::response::)?IntoResponse\s+for\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # WebSocket
    WS_PATTERN = re.compile(
        r'(?:ws::WebSocketUpgrade|WebSocketUpgrade)',
        re.MULTILINE
    )

    # Fallback handler
    FALLBACK_PATTERN = re.compile(
        r'\.fallback\s*\(\s*(?P<handler>\w+)',
        re.MULTILINE
    )

    # tower-http layers
    TOWER_HTTP_LAYER = re.compile(
        r'(?:tower_http::)?(?P<layer>TraceLayer|CorsLayer|CompressionLayer|RequestBodyLimitLayer|TimeoutLayer|SetRequestHeaderLayer|PropagateRequestIdLayer|CatchPanicLayer)',
    )

    VERSION_FEATURES = {
        '0.8': [r'\.with_state_arc', r'axum::serve'],
        '0.7': [r'axum::serve', r'Router::new\(\)\.route'],
        '0.6': [r'\.with_state\(', r'FromRef'],
        '0.5': [r'Router::new', r'axum::Router'],
    }

    def __init__(self):
        pass

    def parse(self, content: str, file_path: str = "") -> AxumParseResult:
        result = AxumParseResult(file_path=file_path)
        if not self.AXUM_DETECT.search(content):
            return result

        result.detected_frameworks = self._detect_frameworks(content)
        result.axum_version = self._detect_version(content)
        result.routes = self._extract_routes(content, file_path)
        result.layers = self._extract_layers(content, file_path)
        result.extractors = self._extract_extractors(content, file_path)
        result.state = self._extract_state(content, file_path)
        result.errors = self._extract_errors(content, file_path)
        result.websockets = self._extract_websockets(content, file_path)
        result.nests = self._extract_nests(content, file_path)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        return [n for n, p in self.FRAMEWORK_PATTERNS.items() if p.search(content)]

    def _detect_version(self, content: str) -> str:
        for ver, patterns in self.VERSION_FEATURES.items():
            for p in patterns:
                if re.search(p, content):
                    return ver
        return ""

    def _extract_routes(self, content: str, file_path: str) -> List[AxumRouteInfo]:
        routes = []
        for m in self.ROUTE_PATTERN.finditer(content):
            path = m.group('path')
            methods_str = m.group('methods')
            line_num = content[:m.start()].count('\n') + 1

            for hm in self.METHOD_HANDLER.finditer(methods_str):
                routes.append(AxumRouteInfo(
                    method=hm.group('method').upper(),
                    path=path, handler=hm.group('handler'),
                    file=file_path, line_number=line_num,
                ))

        # Fallback
        for m in self.FALLBACK_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            routes.append(AxumRouteInfo(
                method='FALLBACK', path='*',
                handler=m.group('handler'),
                file=file_path, line_number=line_num,
            ))

        return routes

    def _extract_layers(self, content: str, file_path: str) -> List[AxumLayerInfo]:
        layers = []
        seen = set()

        for m in self.LAYER_PATTERN.finditer(content):
            name = m.group('layer').strip().split('(')[0].split(':')[-1].strip()
            if name and name not in seen:
                seen.add(name)
                line_num = content[:m.start()].count('\n') + 1
                layers.append(AxumLayerInfo(
                    name=name, kind='layer',
                    file=file_path, line_number=line_num,
                ))

        for m in self.MIDDLEWARE_FN.finditer(content):
            name = m.group('name') or m.group('kind')
            if name not in seen:
                seen.add(name)
                line_num = content[:m.start()].count('\n') + 1
                layers.append(AxumLayerInfo(
                    name=name, kind=m.group('kind'), is_custom=True,
                    file=file_path, line_number=line_num,
                ))

        for m in self.TOWER_HTTP_LAYER.finditer(content):
            name = m.group('layer')
            if name not in seen:
                seen.add(name)
                line_num = content[:m.start()].count('\n') + 1
                layers.append(AxumLayerInfo(
                    name=name, kind='tower-http',
                    file=file_path, line_number=line_num,
                ))

        return layers

    def _extract_extractors(self, content: str, file_path: str) -> List[AxumExtractorInfo]:
        extractors = []
        for m in self.EXTRACTOR_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            extractors.append(AxumExtractorInfo(
                extractor_type=m.group('type'),
                inner_type=(m.group('inner') or '').strip(),
                file=file_path, line_number=line_num,
            ))
        return extractors

    def _extract_state(self, content: str, file_path: str) -> List[AxumStateInfo]:
        states = []
        seen = set()

        for m in self.WITH_STATE.finditer(content):
            name = m.group('state').strip()
            if name not in seen:
                seen.add(name)
                line_num = content[:m.start()].count('\n') + 1
                states.append(AxumStateInfo(
                    type_name=name, registration='with_state',
                    file=file_path, line_number=line_num,
                ))

        for m in self.FROM_REF.finditer(content):
            name = m.group('name') if m.group('name') else 'FromRef'
            if name not in seen:
                seen.add(name)
                line_num = content[:m.start()].count('\n') + 1
                states.append(AxumStateInfo(
                    type_name=name, registration='FromRef',
                    file=file_path, line_number=line_num,
                ))

        return states

    def _extract_errors(self, content: str, file_path: str) -> List[AxumErrorInfo]:
        errors = []
        for m in self.INTO_RESPONSE.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            errors.append(AxumErrorInfo(
                name=m.group('name'), kind='IntoResponse',
                file=file_path, line_number=line_num,
            ))
        return errors

    def _extract_websockets(self, content: str, file_path: str) -> List[AxumWebSocketInfo]:
        websockets = []
        for m in self.WS_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            websockets.append(AxumWebSocketInfo(
                handler='ws_handler', file=file_path, line_number=line_num,
            ))
        return websockets

    def _extract_nests(self, content: str, file_path: str) -> List[AxumNestInfo]:
        nests = []
        for m in self.NEST_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            nests.append(AxumNestInfo(
                path=m.group('path'),
                router=m.group('router').strip(),
                file=file_path, line_number=line_num,
            ))
        for m in self.MERGE_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            nests.append(AxumNestInfo(
                path='/',
                router=m.group('router').strip(),
                file=file_path, line_number=line_num,
            ))
        return nests
