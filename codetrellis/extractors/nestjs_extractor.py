"""
CodeTrellis NestJS Extractor
=======================

Phase C (WS-6 / G-22 + G-23): Extracts NestJS-specific architecture context.

G-22: NestJS module/DI graph extraction
  - Module declarations (imports, providers, controllers, exports)
  - Dependency injection relationships
  - Module hierarchy

G-23: Guard/Interceptor/Pipe/Middleware extraction
  - @Injectable guards implementing CanActivate
  - @Injectable interceptors implementing NestInterceptor
  - @Injectable pipes implementing PipeTransform
  - Middleware classes implementing NestMiddleware
  - @UseGuards(), @UseInterceptors(), @UsePipes() usage on controllers

Output feeds into:
- [NESTJS_MODULES] section in matrix.prompt
- [NESTJS_PIPELINE] section in matrix.prompt
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class NestJSModule:
    """A NestJS @Module() declaration"""
    name: str
    file_path: str
    imports: List[str] = field(default_factory=list)
    providers: List[str] = field(default_factory=list)
    controllers: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    is_global: bool = False
    is_dynamic: bool = False

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "name": self.name,
            "file": self.file_path,
        }
        if self.imports:
            result["imports"] = self.imports
        if self.providers:
            result["providers"] = self.providers
        if self.controllers:
            result["controllers"] = self.controllers
        if self.exports:
            result["exports"] = self.exports
        if self.is_global:
            result["global"] = True
        if self.is_dynamic:
            result["dynamic"] = True
        return result


@dataclass
class NestJSGuard:
    """A NestJS guard (@Injectable implementing CanActivate)"""
    name: str
    file_path: str
    guard_type: str = ""  # jwt, roles, throttle, custom
    extends: Optional[str] = None
    used_by: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "name": self.name,
            "file": self.file_path,
            "type": self.guard_type,
        }
        if self.extends:
            result["extends"] = self.extends
        if self.used_by:
            result["used_by"] = self.used_by
        return result


@dataclass
class NestJSInterceptor:
    """A NestJS interceptor (@Injectable implementing NestInterceptor)"""
    name: str
    file_path: str
    purpose: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "name": self.name,
            "file": self.file_path,
        }
        if self.purpose:
            result["purpose"] = self.purpose
        return result


@dataclass
class NestJSPipe:
    """A NestJS pipe (@Injectable implementing PipeTransform)"""
    name: str
    file_path: str
    purpose: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "name": self.name,
            "file": self.file_path,
        }
        if self.purpose:
            result["purpose"] = self.purpose
        return result


@dataclass
class NestJSMiddleware:
    """A NestJS middleware (implementing NestMiddleware)"""
    name: str
    file_path: str
    applied_to: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "name": self.name,
            "file": self.file_path,
        }
        if self.applied_to:
            result["applied_to"] = self.applied_to
        return result


@dataclass
class NestJSGatewayEvent:
    """A single @SubscribeMessage handler in a WebSocket gateway."""
    event_name: str
    handler_name: str
    return_type: Optional[str] = None


@dataclass
class NestJSGateway:
    """A NestJS @WebSocketGateway() declaration (Gap 2.5)."""
    name: str
    file_path: str
    port: Optional[int] = None
    namespace: Optional[str] = None
    events: List[NestJSGatewayEvent] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "name": self.name,
            "file": self.file_path,
        }
        if self.port is not None:
            result["port"] = self.port
        if self.namespace:
            result["namespace"] = self.namespace
        if self.events:
            result["events"] = [
                {"event": e.event_name, "handler": e.handler_name}
                for e in self.events
            ]
        return result


@dataclass
class NestJSInfo:
    """Complete NestJS architecture information"""
    modules: List[NestJSModule] = field(default_factory=list)
    guards: List[NestJSGuard] = field(default_factory=list)
    interceptors: List[NestJSInterceptor] = field(default_factory=list)
    pipes: List[NestJSPipe] = field(default_factory=list)
    middleware: List[NestJSMiddleware] = field(default_factory=list)
    gateways: List[NestJSGateway] = field(default_factory=list)  # Gap 2.5
    # Guard usage mapping: controller → guards applied
    guard_usage: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "modules": [m.to_dict() for m in self.modules],
            "guards": [g.to_dict() for g in self.guards],
            "interceptors": [i.to_dict() for i in self.interceptors],
            "pipes": [p.to_dict() for p in self.pipes],
            "middleware": [m.to_dict() for m in self.middleware],
            "gateways": [g.to_dict() for g in self.gateways],
            "guard_usage": self.guard_usage,
        }


class NestJSExtractor:
    """
    Extracts NestJS architectural context from a project.

    Parses:
    - *.module.ts files for module graph (G-22)
    - *.guard.ts files for guard definitions (G-23)
    - *.interceptor.ts files for interceptor definitions (G-23)
    - *.pipe.ts files for pipe definitions (G-23)
    - *.middleware.ts files for middleware definitions (G-23)
    - *.controller.ts files for @UseGuards/@UseInterceptors usage (G-23)

    Used by: scanner.py → compressor.py → [NESTJS_MODULES] + [NESTJS_PIPELINE]
    """

    def extract(self, root_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract NestJS architecture information from a project.

        Args:
            root_path: Path to project root

        Returns:
            Dict with NestJS info, or None if not a NestJS project
        """
        root = Path(root_path)

        # Check if this is a NestJS project
        if not self._is_nestjs_project(root):
            return None

        info = NestJSInfo()
        ignore_dirs = {'node_modules', '.git', '_archive', 'dist', 'build',
                       '__pycache__', '.venv', 'venv', 'test', 'tests', '__tests__'}

        for dirpath, dirnames, filenames in __import__('os').walk(root):
            dirnames[:] = [d for d in dirnames if d not in ignore_dirs]

            for filename in filenames:
                file_path = Path(dirpath) / filename

                try:
                    rel_path = str(file_path.relative_to(root))
                except ValueError:
                    rel_path = str(file_path)

                try:
                    if filename.endswith('.module.ts'):
                        self._parse_module_file(file_path, rel_path, info)
                    elif filename.endswith('.guard.ts'):
                        self._parse_guard_file(file_path, rel_path, info)
                    elif filename.endswith('.interceptor.ts'):
                        self._parse_interceptor_file(file_path, rel_path, info)
                    elif filename.endswith('.pipe.ts'):
                        self._parse_pipe_file(file_path, rel_path, info)
                    elif filename.endswith('.middleware.ts'):
                        self._parse_middleware_file(file_path, rel_path, info)
                    elif filename.endswith('.controller.ts'):
                        self._extract_guard_usage(file_path, rel_path, info)
                    elif filename.endswith('.gateway.ts'):
                        self._parse_gateway_file(file_path, rel_path, info)  # Gap 2.5
                except Exception:
                    pass

        # Cross-reference guard usage with guard definitions
        self._cross_reference_guards(info)

        if not info.modules and not info.guards:
            return None

        return info.to_dict()

    def _is_nestjs_project(self, root: Path) -> bool:
        """Check if this is a NestJS project by looking for @nestjs/core dependency."""
        # Check root package.json
        pkg = root / 'package.json'
        if pkg.exists():
            try:
                content = pkg.read_text(encoding='utf-8')
                if '@nestjs/core' in content or '@nestjs/common' in content:
                    return True
            except Exception:
                pass

        # Check for nested package.json in services/
        for services_dir in ['services', 'apps', 'packages']:
            svc_path = root / services_dir
            if svc_path.exists():
                for subdir in svc_path.iterdir():
                    if subdir.is_dir():
                        nested_pkg = subdir / 'package.json'
                        if nested_pkg.exists():
                            try:
                                content = nested_pkg.read_text(encoding='utf-8')
                                if '@nestjs/core' in content or '@nestjs/common' in content:
                                    return True
                            except Exception:
                                pass
        return False

    def _parse_module_file(self, file_path: Path, rel_path: str, info: NestJSInfo):
        """Parse a *.module.ts file to extract @Module() declaration."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return

        # Find class name
        class_match = re.search(r'export\s+class\s+(\w+Module)', content)
        if not class_match:
            return

        module_name = class_match.group(1)

        module = NestJSModule(name=module_name, file_path=rel_path)

        # Check for @Global()
        module.is_global = bool(re.search(r'@Global\(\)', content))

        # Check for dynamic module (forRoot, forRootAsync, register)
        module.is_dynamic = bool(re.search(
            r'static\s+(?:forRoot|forRootAsync|register|forFeature)',
            content
        ))

        # Find @Module() decorator block
        module_match = re.search(r'@Module\s*\(\s*\{(.*?)\}\s*\)', content, re.DOTALL)
        if module_match:
            module_body = module_match.group(1)

            # Extract imports
            module.imports = self._extract_array_items(module_body, 'imports')

            # Extract providers
            module.providers = self._extract_array_items(module_body, 'providers')

            # Extract controllers
            module.controllers = self._extract_array_items(module_body, 'controllers')

            # Extract exports
            module.exports = self._extract_array_items(module_body, 'exports')

        info.modules.append(module)

    def _parse_guard_file(self, file_path: Path, rel_path: str, info: NestJSInfo):
        """Parse a *.guard.ts file."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return

        # Find class declarations with @Injectable
        classes = re.findall(
            r'@Injectable\(\)\s*export\s+class\s+(\w+)\s*(?:extends\s+(\w+))?\s*(?:implements\s+([^{]+))?\s*\{',
            content
        )

        for match in classes:
            class_name = match[0]
            extends = match[1] if match[1] else None
            implements = match[2].strip() if match[2] else ''

            guard = NestJSGuard(
                name=class_name,
                file_path=rel_path,
                extends=extends,
            )

            # Determine guard type
            name_lower = class_name.lower()
            if 'jwt' in name_lower or 'auth' in name_lower:
                guard.guard_type = 'auth'
            elif 'role' in name_lower or 'permission' in name_lower:
                guard.guard_type = 'roles'
            elif 'throttl' in name_lower or 'rate' in name_lower:
                guard.guard_type = 'throttle'
            elif 'tenant' in name_lower:
                guard.guard_type = 'tenant'
            elif 'api' in name_lower and 'key' in name_lower:
                guard.guard_type = 'api-key'
            else:
                guard.guard_type = 'custom'

            info.guards.append(guard)

    def _parse_interceptor_file(self, file_path: Path, rel_path: str, info: NestJSInfo):
        """Parse a *.interceptor.ts file."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return

        classes = re.findall(
            r'@Injectable\(\)\s*export\s+class\s+(\w+)',
            content
        )

        for class_name in classes:
            interceptor = NestJSInterceptor(
                name=class_name,
                file_path=rel_path,
            )

            # Determine purpose from name
            name_lower = class_name.lower()
            if 'logging' in name_lower or 'logger' in name_lower:
                interceptor.purpose = 'logging'
            elif 'transform' in name_lower:
                interceptor.purpose = 'response-transform'
            elif 'timeout' in name_lower:
                interceptor.purpose = 'timeout'
            elif 'cache' in name_lower:
                interceptor.purpose = 'caching'
            elif 'error' in name_lower or 'exception' in name_lower:
                interceptor.purpose = 'error-handling'
            elif 'serialize' in name_lower:
                interceptor.purpose = 'serialization'

            info.interceptors.append(interceptor)

    def _parse_pipe_file(self, file_path: Path, rel_path: str, info: NestJSInfo):
        """Parse a *.pipe.ts file."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return

        classes = re.findall(
            r'@Injectable\(\)\s*export\s+class\s+(\w+)',
            content
        )

        for class_name in classes:
            pipe = NestJSPipe(
                name=class_name,
                file_path=rel_path,
            )

            name_lower = class_name.lower()
            if 'validation' in name_lower or 'validate' in name_lower:
                pipe.purpose = 'validation'
            elif 'parse' in name_lower:
                pipe.purpose = 'parsing'
            elif 'transform' in name_lower:
                pipe.purpose = 'transformation'
            elif 'file' in name_lower or 'upload' in name_lower:
                pipe.purpose = 'file-processing'

            info.pipes.append(pipe)

    def _parse_middleware_file(self, file_path: Path, rel_path: str, info: NestJSInfo):
        """Parse a *.middleware.ts file."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return

        classes = re.findall(
            r'@Injectable\(\)\s*export\s+class\s+(\w+)',
            content
        )

        for class_name in classes:
            middleware = NestJSMiddleware(
                name=class_name,
                file_path=rel_path,
            )

            # Check for route application in the same file or nearby module
            # (cross-reference happens later)
            info.middleware.append(middleware)

    def _extract_guard_usage(self, file_path: Path, rel_path: str, info: NestJSInfo):
        """Extract @UseGuards(), @UseInterceptors(), @UsePipes() from controller files."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return

        # Find controller class name
        ctrl_match = re.search(r'export\s+class\s+(\w+Controller)', content)
        if not ctrl_match:
            return
        ctrl_name = ctrl_match.group(1)

        # Extract @UseGuards
        guard_matches = re.findall(r'@UseGuards\(([^)]+)\)', content)
        guards = []
        for match in guard_matches:
            items = [g.strip() for g in match.split(',')]
            guards.extend(items)

        if guards:
            info.guard_usage[ctrl_name] = list(set(guards))

    def _cross_reference_guards(self, info: NestJSInfo):
        """Cross-reference guard usage with guard definitions."""
        guard_names = {g.name for g in info.guards}

        for ctrl_name, used_guards in info.guard_usage.items():
            for guard_name in used_guards:
                for guard in info.guards:
                    if guard.name == guard_name:
                        if ctrl_name not in guard.used_by:
                            guard.used_by.append(ctrl_name)

    def _extract_array_items(self, body: str, key: str) -> List[str]:
        """Extract items from an array declaration like 'imports: [Foo, Bar]'.

        Handles complex expressions like:
        - ConfigModule.forRoot({...})  → "ConfigModule.forRoot"
        - ClientsModule.register([...])  → "ClientsModule.register"
        - Simple identifiers like FooModule  → "FooModule"
        - Spread expressions like ...providers  → ignored
        - Comments  → ignored
        """
        pattern = rf'{key}\s*:\s*\[(.*?)\]'
        # Need to find the matching ] accounting for nesting
        key_pattern = rf'{key}\s*:\s*\['
        match = re.search(key_pattern, body)
        if not match:
            return []

        start = match.end()
        depth = 1
        pos = start
        while pos < len(body) and depth > 0:
            if body[pos] == '[':
                depth += 1
            elif body[pos] == ']':
                depth -= 1
            pos += 1

        items_str = body[start:pos - 1]
        items = []

        # Split by comma at depth 0, ignoring nested content
        depth = 0
        current = ""
        for char in items_str:
            if char in '({[':
                depth += 1
            elif char in ')}]':
                depth -= 1
            elif char == ',' and depth == 0:
                item = self._clean_module_item(current)
                if item:
                    items.append(item)
                current = ""
                continue
            current += char

        # Last item
        item = self._clean_module_item(current)
        if item:
            items.append(item)

        return items

    def _clean_module_item(self, raw: str) -> Optional[str]:
        """Clean a raw module array item into a concise identifier.

        Examples:
        - "  ConfigModule.forRoot({...})  "  → "ConfigModule.forRoot"
        - "  FooModule  "  → "FooModule"
        - "// comment"  → None
        - "  ...providers"  → None
        """
        # Strip whitespace
        item = raw.strip()
        if not item:
            return None

        # Remove line comments
        item = re.sub(r'//.*$', '', item, flags=re.MULTILINE).strip()
        if not item:
            return None

        # Skip spread expressions
        if item.startswith('...'):
            return None

        # Remove block comments
        item = re.sub(r'/\*.*?\*/', '', item, flags=re.DOTALL).strip()
        if not item:
            return None

        # Extract just the identifier part: "ConfigModule.forRoot({...})" → "ConfigModule.forRoot"
        # Match: word chars, dots, but stop at parentheses
        ident_match = re.match(r'^([\w.]+)', item)
        if ident_match:
            return ident_match.group(1)

        return None

    def _parse_gateway_file(self, file_path: Path, rel_path: str, info: NestJSInfo):
        """
        Parse a *.gateway.ts file to extract @WebSocketGateway() + @SubscribeMessage() handlers.

        Gap 2.5: Extracts WebSocket gateway patterns from NestJS.
        Detects:
        - @WebSocketGateway(port?, { namespace? })
        - @SubscribeMessage('eventName') handlers
        """
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return

        # Detect @WebSocketGateway decorator
        gateway_pattern = re.compile(
            r'@WebSocketGateway\(([^)]*)\)\s*\n\s*(?:export\s+)?class\s+(\w+)',
            re.DOTALL
        )
        gateway_match = gateway_pattern.search(content)
        if not gateway_match:
            return

        gateway_args = gateway_match.group(1).strip()
        gateway_name = gateway_match.group(2)

        # Extract port and namespace from arguments
        port = None
        namespace = None

        port_match = re.search(r'(\d+)', gateway_args)
        if port_match:
            port = int(port_match.group(1))

        ns_match = re.search(r'namespace:\s*[\'"]([^\'"]+)[\'"]', gateway_args)
        if ns_match:
            namespace = ns_match.group(1)

        # Extract @SubscribeMessage('event') handlers
        subscribe_pattern = re.compile(
            r'@SubscribeMessage\(\s*[\'"]([^\'"]+)[\'"]\s*\)\s*\n\s*(?:async\s+)?(\w+)\s*\(',
        )
        events = []
        for sub_match in subscribe_pattern.finditer(content):
            event_name = sub_match.group(1)
            handler_name = sub_match.group(2)
            events.append(NestJSGatewayEvent(
                event_name=event_name,
                handler_name=handler_name,
            ))

        gateway = NestJSGateway(
            name=gateway_name,
            file_path=rel_path,
            port=port,
            namespace=namespace,
            events=events,
        )
        info.gateways.append(gateway)
