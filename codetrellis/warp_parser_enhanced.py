"""
EnhancedWarpParser v1.0 - Comprehensive Warp framework parser.

Extracts Warp-specific patterns from Rust source files:
- Filter composition (warp::path, and, and_then, map, or)
- Route definitions (warp::get, warp::post, etc.)
- Rejection handling (reject::custom, recover)
- Reply types (warp::reply::json, warp::reply::html, with_status)
- WebSocket (warp::ws())
- CORS (warp::cors())
- Logging and tracing (warp::trace, warp::log)
- Filter extraction (warp::body::json, warp::query, warp::header)
- Server configuration (warp::serve, TLS)

Supports Warp 0.1 through 0.3+.

Part of CodeTrellis - Rust Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class WarpRouteInfo:
    method: str
    path: str
    handler: str = ""
    file: str = ""
    line_number: int = 0
    filters: List[str] = field(default_factory=list)
    reply_type: str = ""


@dataclass
class WarpFilterInfo:
    name: str
    kind: str = ""  # path, method, body, query, header, cookie, custom
    file: str = ""
    line_number: int = 0


@dataclass
class WarpRejectionInfo:
    name: str
    kind: str = ""  # custom, recover, handle_rejection
    file: str = ""
    line_number: int = 0


@dataclass
class WarpReplyInfo:
    kind: str  # json, html, with_status, Response, custom
    file: str = ""
    line_number: int = 0


@dataclass
class WarpWebSocketInfo:
    handler: str = ""
    path: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class WarpConfigInfo:
    kind: str  # serve, tls, cors, log, trace
    setting: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class WarpParseResult:
    file_path: str
    file_type: str = "rust"

    routes: List[WarpRouteInfo] = field(default_factory=list)
    filters: List[WarpFilterInfo] = field(default_factory=list)
    rejections: List[WarpRejectionInfo] = field(default_factory=list)
    replies: List[WarpReplyInfo] = field(default_factory=list)
    websockets: List[WarpWebSocketInfo] = field(default_factory=list)
    configs: List[WarpConfigInfo] = field(default_factory=list)

    detected_frameworks: List[str] = field(default_factory=list)
    warp_version: str = ""


class EnhancedWarpParser:
    """
    Enhanced Warp parser for comprehensive framework analysis.

    Supports Warp 0.1 through 0.3+:
    - v0.1: Initial filter-based API
    - v0.2: Major API stabilization, improved filters
    - v0.3: tokio 1.0 support, hyper 0.14 backend
    """

    WARP_DETECT = re.compile(
        r'(?:use\s+warp|warp::|warp::serve|warp::Filter)',
        re.MULTILINE
    )

    FRAMEWORK_PATTERNS = {
        'warp': re.compile(r'\bwarp\b'),
        'warp-ws': re.compile(r'warp::ws'),
        'warp-cors': re.compile(r'warp::cors'),
    }

    # warp::path("segment") or warp::path!("segment" / "other")
    PATH_FILTER = re.compile(
        r'warp::path\s*(?:!\s*\(\s*"?(?P<macro_path>[^)"]+)"?\s*\)|\(\s*"(?P<path>[^"]+)")',
        re.MULTILINE
    )

    # warp::get(), warp::post(), etc.
    METHOD_FILTER = re.compile(
        r'warp::(?P<method>get|post|put|delete|patch|head|options|any)\s*\(\s*\)',
    )

    # .and(filter), .or(filter), .and_then(handler), .map(handler)
    COMBINATOR = re.compile(
        r'\.(?P<kind>and|or|and_then|map|untuple_one|with)\s*\(\s*(?P<target>[^)]*)\)',
        re.MULTILINE
    )

    # warp::body::json(), warp::body::bytes(), warp::query()
    BODY_FILTER = re.compile(
        r'warp::(?P<kind>body::json|body::bytes|body::form|body::aggregate|query|header|cookie)',
    )

    # Custom rejection: impl warp::reject::Reject / reject::custom
    REJECTION_CUSTOM = re.compile(
        r'(?:impl\s+(?:warp::)?reject::Reject\s+for\s+(?P<name>\w+)|reject::custom\s*\(\s*(?P<custom>\w+))',
        re.MULTILINE
    )

    # .recover(handler)
    RECOVER = re.compile(
        r'\.recover\s*\(\s*(?P<handler>\w+)',
        re.MULTILINE
    )

    # Reply helpers: warp::reply::json, warp::reply::html, etc.
    REPLY_PATTERN = re.compile(
        r'(?:warp::)?reply::(?P<kind>json|html|with_status|with_header|Response)',
    )

    # WebSocket: warp::ws()
    WS_PATTERN = re.compile(
        r'warp::ws\s*\(\s*\)',
    )

    # warp::serve(routes)
    SERVE_PATTERN = re.compile(
        r'warp::serve\s*\(\s*(?P<routes>[^)]+)\)',
        re.MULTILINE
    )

    # TLS: .tls()
    TLS_PATTERN = re.compile(r'\.tls\s*\(\s*\)', re.MULTILINE)

    # CORS: warp::cors()
    CORS_PATTERN = re.compile(
        r'warp::cors\s*\(\s*\)|\.allow_origin|\.allow_methods|\.allow_headers',
    )

    # Logging: warp::trace, warp::log
    LOG_PATTERN = re.compile(
        r'warp::(?P<kind>trace|log)\s*(?:::\w+)?\s*\(',
    )

    VERSION_FEATURES = {
        '0.3': [r'tokio::main', r'warp\s*=\s*"0\.3'],
        '0.2': [r'warp\s*=\s*"0\.2'],
        '0.1': [r'warp\s*=\s*"0\.1'],
    }

    def __init__(self):
        pass

    def parse(self, content: str, file_path: str = "") -> WarpParseResult:
        result = WarpParseResult(file_path=file_path)
        if not self.WARP_DETECT.search(content):
            return result

        result.detected_frameworks = self._detect_frameworks(content)
        result.warp_version = self._detect_version(content)
        result.routes = self._extract_routes(content, file_path)
        result.filters = self._extract_filters(content, file_path)
        result.rejections = self._extract_rejections(content, file_path)
        result.replies = self._extract_replies(content, file_path)
        result.websockets = self._extract_websockets(content, file_path)
        result.configs = self._extract_configs(content, file_path)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        return [n for n, p in self.FRAMEWORK_PATTERNS.items() if p.search(content)]

    def _detect_version(self, content: str) -> str:
        for ver, patterns in self.VERSION_FEATURES.items():
            for p in patterns:
                if re.search(p, content):
                    return ver
        return ""

    def _extract_routes(self, content: str, file_path: str) -> List[WarpRouteInfo]:
        routes = []
        # Warp uses filter composition to define routes, so we reconstruct from path + method
        paths = {}
        for m in self.PATH_FILTER.finditer(content):
            path = m.group('macro_path') or m.group('path') or ''
            line_num = content[:m.start()].count('\n') + 1
            paths[line_num] = path

        for m in self.METHOD_FILTER.finditer(content):
            method = m.group('method').upper()
            line_num = content[:m.start()].count('\n') + 1
            # Find closest path within 10 lines
            closest_path = ""
            for pline, ppath in sorted(paths.items()):
                if abs(pline - line_num) <= 10:
                    closest_path = '/' + ppath.replace('"', '').replace(' / ', '/')
                    break

            # Find handler via .and_then() or .map()
            handler = ""
            handler_re = re.compile(r'\.(?:and_then|map)\s*\(\s*(\w+)')
            search_area = content[m.start():m.start() + 500]
            hm = handler_re.search(search_area)
            if hm:
                handler = hm.group(1)

            routes.append(WarpRouteInfo(
                method=method, path=closest_path,
                handler=handler, file=file_path, line_number=line_num,
            ))

        return routes

    def _extract_filters(self, content: str, file_path: str) -> List[WarpFilterInfo]:
        filters = []
        seen = set()

        for m in self.BODY_FILTER.finditer(content):
            name = m.group('kind')
            if name not in seen:
                seen.add(name)
                line_num = content[:m.start()].count('\n') + 1
                filters.append(WarpFilterInfo(
                    name=name, kind='body' if 'body' in name else name,
                    file=file_path, line_number=line_num,
                ))

        for m in self.PATH_FILTER.finditer(content):
            path = m.group('macro_path') or m.group('path') or ''
            name = f'path:{path}'
            if name not in seen:
                seen.add(name)
                line_num = content[:m.start()].count('\n') + 1
                filters.append(WarpFilterInfo(
                    name=name, kind='path',
                    file=file_path, line_number=line_num,
                ))

        return filters

    def _extract_rejections(self, content: str, file_path: str) -> List[WarpRejectionInfo]:
        rejections = []
        for m in self.REJECTION_CUSTOM.finditer(content):
            name = m.group('name') or m.group('custom') or ''
            line_num = content[:m.start()].count('\n') + 1
            rejections.append(WarpRejectionInfo(
                name=name, kind='custom',
                file=file_path, line_number=line_num,
            ))

        for m in self.RECOVER.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            rejections.append(WarpRejectionInfo(
                name=m.group('handler'), kind='recover',
                file=file_path, line_number=line_num,
            ))

        return rejections

    def _extract_replies(self, content: str, file_path: str) -> List[WarpReplyInfo]:
        replies = []
        seen = set()
        for m in self.REPLY_PATTERN.finditer(content):
            kind = m.group('kind')
            if kind not in seen:
                seen.add(kind)
                line_num = content[:m.start()].count('\n') + 1
                replies.append(WarpReplyInfo(
                    kind=kind, file=file_path, line_number=line_num,
                ))
        return replies

    def _extract_websockets(self, content: str, file_path: str) -> List[WarpWebSocketInfo]:
        websockets = []
        for m in self.WS_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            websockets.append(WarpWebSocketInfo(
                file=file_path, line_number=line_num,
            ))
        return websockets

    def _extract_configs(self, content: str, file_path: str) -> List[WarpConfigInfo]:
        configs = []
        for m in self.SERVE_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            configs.append(WarpConfigInfo(
                kind='serve', setting=m.group('routes').strip(),
                file=file_path, line_number=line_num,
            ))
        for m in self.TLS_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            configs.append(WarpConfigInfo(
                kind='tls', file=file_path, line_number=line_num,
            ))
        for m in self.CORS_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            configs.append(WarpConfigInfo(
                kind='cors', file=file_path, line_number=line_num,
            ))
        for m in self.LOG_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            configs.append(WarpConfigInfo(
                kind=m.group('kind'), file=file_path, line_number=line_num,
            ))
        return configs
