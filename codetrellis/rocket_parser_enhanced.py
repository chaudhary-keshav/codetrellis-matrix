"""
EnhancedRocketParser v1.0 - Comprehensive Rocket framework parser.

Extracts Rocket-specific patterns from Rust source files:
- Route handlers (#[get], #[post], #[catch], #[launch])
- Fairings (attach, on_ignite, on_liftoff, on_request, on_response)
- Request guards (FromRequest trait)
- Managed state (State<T>, manage())
- Responders (Responder trait, Json, Template, Redirect)
- Catchers (#[catch(404)])
- Configuration (Rocket.toml, Figment)
- Mounting and ignite
- URI macros (uri!)

Supports Rocket 0.3 through 0.5+.

Part of CodeTrellis - Rust Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RocketRouteInfo:
    method: str
    path: str
    handler: str
    file: str = ""
    line_number: int = 0
    rank: int = 0
    data_param: str = ""
    format: str = ""
    guards: List[str] = field(default_factory=list)


@dataclass
class RocketCatcherInfo:
    status_code: int
    handler: str
    file: str = ""
    line_number: int = 0


@dataclass
class RocketFairingInfo:
    name: str
    kind: str = ""  # on_ignite, on_liftoff, on_request, on_response, attach
    file: str = ""
    line_number: int = 0
    is_custom: bool = False


@dataclass
class RocketGuardInfo:
    name: str
    kind: str = ""  # FromRequest, FromData, FromForm, FromParam, FromSegments
    file: str = ""
    line_number: int = 0


@dataclass
class RocketStateInfo:
    type_name: str
    registration: str = ""  # manage, State
    file: str = ""
    line_number: int = 0


@dataclass
class RocketResponderInfo:
    name: str
    kind: str = ""  # Responder derive, impl, built-in
    file: str = ""
    line_number: int = 0


@dataclass
class RocketMountInfo:
    base: str
    routes: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class RocketParseResult:
    file_path: str
    file_type: str = "rust"

    routes: List[RocketRouteInfo] = field(default_factory=list)
    catchers: List[RocketCatcherInfo] = field(default_factory=list)
    fairings: List[RocketFairingInfo] = field(default_factory=list)
    guards: List[RocketGuardInfo] = field(default_factory=list)
    state: List[RocketStateInfo] = field(default_factory=list)
    responders: List[RocketResponderInfo] = field(default_factory=list)
    mounts: List[RocketMountInfo] = field(default_factory=list)

    detected_frameworks: List[str] = field(default_factory=list)
    rocket_version: str = ""


class EnhancedRocketParser:
    """
    Enhanced Rocket parser for comprehensive framework analysis.

    Supports Rocket 0.3 through 0.5+:
    - v0.3-0.4: Nightly Rust, codegen, Rocket::ignite()
    - v0.5: Stable Rust, async, #[launch], Figment config, Sentinels
    """

    ROCKET_DETECT = re.compile(
        r'(?:use\s+rocket|rocket::|#\[(?:get|post|put|delete|patch|launch|catch)\s*\(|Rocket::(?:build|ignite))',
        re.MULTILINE
    )

    FRAMEWORK_PATTERNS = {
        'rocket': re.compile(r'\brocket\b'),
        'rocket-contrib': re.compile(r'\brocket_contrib\b'),
        'rocket-dyn-templates': re.compile(r'\brocket_dyn_templates\b'),
        'rocket-db-pools': re.compile(r'\brocket_db_pools\b'),
        'rocket-ws': re.compile(r'\brocket_ws\b'),
        'rocket-sync-db-pools': re.compile(r'\brocket_sync_db_pools\b'),
    }

    # Route attrs: #[get("/path")], #[post("/path", data = "<input>")]
    ROUTE_ATTR = re.compile(
        r'#\[(?:rocket::)?(?P<method>get|post|put|delete|patch|head|options)\s*\(\s*"(?P<path>[^"]+)"'
        r'(?:\s*,\s*(?:data\s*=\s*"(?P<data>[^"]+)"))?'
        r'(?:\s*,\s*(?:format\s*=\s*"(?P<format>[^"]+)"))?'
        r'(?:\s*,\s*(?:rank\s*=\s*(?P<rank>\d+)))?',
        re.MULTILINE
    )

    # Generic #[route(METHOD, path = "/")]
    ROUTE_GENERIC = re.compile(
        r'#\[route\s*\(\s*(?P<method>\w+)\s*,\s*path\s*=\s*"(?P<path>[^"]+)"',
        re.MULTILINE
    )

    HANDLER_FN = re.compile(
        r'(?:pub\s+)?(?:async\s+)?fn\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # Catch: #[catch(404)]
    CATCH_ATTR = re.compile(
        r'#\[catch\s*\(\s*(?P<code>\d+|default)\s*\)\]',
        re.MULTILINE
    )

    # Fairing: impl Fairing for X / attach(XFairing) / on_ignite, etc.
    FAIRING_IMPL = re.compile(
        r'impl\s+Fairing\s+for\s+(?P<name>\w+)',
        re.MULTILINE
    )
    FAIRING_METHOD = re.compile(
        r'(?:async\s+)?fn\s+(?P<kind>on_ignite|on_liftoff|on_request|on_response|on_shutdown)',
        re.MULTILINE
    )
    ATTACH_FAIRING = re.compile(
        r'\.attach\s*\(\s*(?P<fairing>[^)]+)\)',
        re.MULTILINE
    )

    # Request guards: impl FromRequest / FromData / FromForm / FromParam
    GUARD_IMPL = re.compile(
        r'impl\s*(?:<[^>]+>\s*)?(?P<kind>FromRequest|FromData|FromForm|FromParam|FromSegments)\s*(?:<[^>]+>)?\s+for\s+(?P<name>\w+)',
        re.MULTILINE
    )

    # State: State<T>, manage()
    STATE_PATTERN = re.compile(
        r'(?:&\s*)?State\s*<\s*(?P<type>[^>]+)>',
    )
    MANAGE_PATTERN = re.compile(
        r'\.manage\s*\(\s*(?P<state>[^)]+)\)',
        re.MULTILINE
    )

    # Responder derive / impl
    RESPONDER_DERIVE = re.compile(
        r'#\[derive\([^)]*Responder[^)]*\)\]',
        re.MULTILINE
    )
    RESPONDER_IMPL = re.compile(
        r"impl\s+(?:<[^>]+>\s+)?(?:rocket::response::)?Responder\s*(?:<[^>]+>)?\s+for\s+(?P<name>\w+)",
        re.MULTILINE
    )

    # Mount: .mount("/base", routes![...])
    MOUNT_PATTERN = re.compile(
        r'\.mount\s*\(\s*"(?P<base>[^"]+)"\s*,\s*(?:routes!\s*\[\s*(?P<routes>[^\]]+)\]|(?P<handler>[^)]+))',
        re.MULTILINE
    )

    # #[launch] attribute
    LAUNCH_ATTR = re.compile(r'#\[(?:rocket::)?launch\]', re.MULTILINE)

    # uri! macro usage
    URI_MACRO = re.compile(r'uri!\s*\(\s*(?P<target>[^)]+)\)', re.MULTILINE)

    VERSION_FEATURES = {
        '0.5': [r'#\[launch\]', r'Rocket::build\(\)', r'#\[rocket::main\]', r'Figment'],
        '0.4': [r'Rocket::ignite\(\)', r'rocket_contrib'],
        '0.3': [r'Rocket::ignite\(\)', r'rocket_codegen'],
    }

    def __init__(self):
        pass

    def parse(self, content: str, file_path: str = "") -> RocketParseResult:
        result = RocketParseResult(file_path=file_path)
        if not self.ROCKET_DETECT.search(content):
            return result

        result.detected_frameworks = self._detect_frameworks(content)
        result.rocket_version = self._detect_version(content)
        result.routes = self._extract_routes(content, file_path)
        result.catchers = self._extract_catchers(content, file_path)
        result.fairings = self._extract_fairings(content, file_path)
        result.guards = self._extract_guards(content, file_path)
        result.state = self._extract_state(content, file_path)
        result.responders = self._extract_responders(content, file_path)
        result.mounts = self._extract_mounts(content, file_path)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        return [n for n, p in self.FRAMEWORK_PATTERNS.items() if p.search(content)]

    def _detect_version(self, content: str) -> str:
        for ver, patterns in self.VERSION_FEATURES.items():
            for p in patterns:
                if re.search(p, content):
                    return ver
        return ""

    def _extract_routes(self, content: str, file_path: str) -> List[RocketRouteInfo]:
        routes = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            m = self.ROUTE_ATTR.search(line)
            if m:
                handler = ""
                for j in range(i, min(i + 5, len(lines) + 1)):
                    hm = self.HANDLER_FN.search(lines[j - 1])
                    if hm and not lines[j - 1].strip().startswith('#'):
                        handler = hm.group('name')
                        break
                routes.append(RocketRouteInfo(
                    method=m.group('method').upper(), path=m.group('path'),
                    handler=handler, file=file_path, line_number=i,
                    data_param=m.group('data') or '',
                    format=m.group('format') or '',
                    rank=int(m.group('rank')) if m.group('rank') else 0,
                ))
                continue

            m = self.ROUTE_GENERIC.search(line)
            if m:
                handler = ""
                for j in range(i, min(i + 5, len(lines) + 1)):
                    hm = self.HANDLER_FN.search(lines[j - 1])
                    if hm and not lines[j - 1].strip().startswith('#'):
                        handler = hm.group('name')
                        break
                routes.append(RocketRouteInfo(
                    method=m.group('method').upper(), path=m.group('path'),
                    handler=handler, file=file_path, line_number=i,
                ))

        return routes

    def _extract_catchers(self, content: str, file_path: str) -> List[RocketCatcherInfo]:
        catchers = []
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            m = self.CATCH_ATTR.search(line)
            if m:
                code_str = m.group('code')
                code = int(code_str) if code_str != 'default' else 0
                handler = ""
                for j in range(i, min(i + 5, len(lines) + 1)):
                    hm = self.HANDLER_FN.search(lines[j - 1])
                    if hm:
                        handler = hm.group('name')
                        break
                catchers.append(RocketCatcherInfo(
                    status_code=code, handler=handler,
                    file=file_path, line_number=i,
                ))
        return catchers

    def _extract_fairings(self, content: str, file_path: str) -> List[RocketFairingInfo]:
        fairings = []
        seen = set()

        for m in self.FAIRING_IMPL.finditer(content):
            name = m.group('name')
            if name not in seen:
                seen.add(name)
                line_num = content[:m.start()].count('\n') + 1
                fairings.append(RocketFairingInfo(
                    name=name, kind='impl', is_custom=True,
                    file=file_path, line_number=line_num,
                ))

        for m in self.ATTACH_FAIRING.finditer(content):
            name = m.group('fairing').strip().split('(')[0].split(':')[-1].strip()
            if name and name not in seen:
                seen.add(name)
                line_num = content[:m.start()].count('\n') + 1
                fairings.append(RocketFairingInfo(
                    name=name, kind='attach',
                    file=file_path, line_number=line_num,
                ))

        return fairings

    def _extract_guards(self, content: str, file_path: str) -> List[RocketGuardInfo]:
        guards = []
        for m in self.GUARD_IMPL.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            guards.append(RocketGuardInfo(
                name=m.group('name'), kind=m.group('kind'),
                file=file_path, line_number=line_num,
            ))
        return guards

    def _extract_state(self, content: str, file_path: str) -> List[RocketStateInfo]:
        states = []
        seen = set()

        for m in self.STATE_PATTERN.finditer(content):
            type_name = m.group('type').strip()
            if type_name not in seen:
                seen.add(type_name)
                line_num = content[:m.start()].count('\n') + 1
                states.append(RocketStateInfo(
                    type_name=type_name, registration='State',
                    file=file_path, line_number=line_num,
                ))

        for m in self.MANAGE_PATTERN.finditer(content):
            state_expr = m.group('state').strip().split('(')[0].strip()
            if state_expr and state_expr not in seen:
                seen.add(state_expr)
                line_num = content[:m.start()].count('\n') + 1
                states.append(RocketStateInfo(
                    type_name=state_expr, registration='manage',
                    file=file_path, line_number=line_num,
                ))

        return states

    def _extract_responders(self, content: str, file_path: str) -> List[RocketResponderInfo]:
        responders = []
        for m in self.RESPONDER_IMPL.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            responders.append(RocketResponderInfo(
                name=m.group('name'), kind='impl',
                file=file_path, line_number=line_num,
            ))

        # Check for Responder derive
        struct_re = re.compile(r'#\[derive\([^)]*Responder[^)]*\)\]\s*(?:pub\s+)?struct\s+(\w+)', re.MULTILINE)
        for m in struct_re.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            responders.append(RocketResponderInfo(
                name=m.group(1), kind='derive',
                file=file_path, line_number=line_num,
            ))

        return responders

    def _extract_mounts(self, content: str, file_path: str) -> List[RocketMountInfo]:
        mounts = []
        for m in self.MOUNT_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            routes_str = m.group('routes') or m.group('handler') or ''
            route_list = [r.strip() for r in routes_str.split(',') if r.strip()]
            mounts.append(RocketMountInfo(
                base=m.group('base'), routes=route_list,
                file=file_path, line_number=line_num,
            ))
        return mounts
