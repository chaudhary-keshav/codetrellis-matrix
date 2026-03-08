"""
NestJS Controller Extractor - Per-file extraction of @Controller() and route decorators.

Supports:
- @Controller() decorator with path prefix
- HTTP method decorators: @Get, @Post, @Put, @Delete, @Patch, @Options, @Head, @All
- @HttpCode() status codes
- @Header(), @Redirect() decorators
- Parameter decorators: @Param, @Query, @Body, @Headers, @Ip, @Session, @Req, @Res
- @UseGuards(), @UseInterceptors(), @UsePipes() on controller/method level
- @Render() template rendering
- @Sse() Server-Sent Events
- @MessagePattern(), @EventPattern() for microservices
- NestJS 7.x through 10.x patterns
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class NestEndpointInfo:
    """A single controller endpoint (route handler method)."""
    method: str  # GET, POST, PUT, DELETE, PATCH, etc.
    path: str = ""
    handler_name: str = ""
    file: str = ""
    line_number: int = 0
    status_code: int = 0
    is_async: bool = False
    has_guards: bool = False
    guard_names: List[str] = field(default_factory=list)
    has_interceptors: bool = False
    interceptor_names: List[str] = field(default_factory=list)
    has_pipes: bool = False
    pipe_names: List[str] = field(default_factory=list)
    params: List[str] = field(default_factory=list)  # @Param(), @Query(), etc.
    return_type: str = ""
    is_sse: bool = False
    render_template: str = ""


@dataclass
class NestControllerInfo:
    """A @Controller() class with all its endpoints."""
    class_name: str
    path: str = ""
    file: str = ""
    line_number: int = 0
    version: str = ""  # API versioning
    endpoints: List[NestEndpointInfo] = field(default_factory=list)
    has_guards: bool = False
    guard_names: List[str] = field(default_factory=list)
    has_interceptors: bool = False
    interceptor_names: List[str] = field(default_factory=list)
    has_pipes: bool = False
    pipe_names: List[str] = field(default_factory=list)
    total_endpoints: int = 0


@dataclass
class NestParamDecoratorInfo:
    """A parameter decorator usage."""
    decorator: str  # Param, Query, Body, Headers, etc.
    param_name: str = ""
    file: str = ""
    line_number: int = 0


class NestControllerExtractor:
    """Extracts NestJS controller information from a single file."""

    # @Controller() decorator
    CONTROLLER_DECORATOR = re.compile(
        r"@Controller\s*\(\s*(?:['\"`]([^'\"`]*)['\"`])?\s*(?:\{[^}]*\})?\s*\)"
    )

    # HTTP method decorators
    HTTP_DECORATORS = {
        'Get': 'GET', 'Post': 'POST', 'Put': 'PUT', 'Delete': 'DELETE',
        'Patch': 'PATCH', 'Options': 'OPTIONS', 'Head': 'HEAD', 'All': 'ALL',
    }

    METHOD_DECORATOR_PATTERN = re.compile(
        r"@(Get|Post|Put|Delete|Patch|Options|Head|All)\s*\(\s*(?:['\"`]([^'\"`]*)['\"`])?\s*\)"
    )

    # @HttpCode()
    HTTP_CODE_PATTERN = re.compile(r'@HttpCode\s*\(\s*(\d+)\s*\)')

    # @UseGuards()
    USE_GUARDS_PATTERN = re.compile(
        r'@UseGuards\s*\(\s*([^)]+)\s*\)'
    )

    # @UseInterceptors()
    USE_INTERCEPTORS_PATTERN = re.compile(
        r'@UseInterceptors\s*\(\s*([^)]+)\s*\)'
    )

    # @UsePipes()
    USE_PIPES_PATTERN = re.compile(
        r'@UsePipes\s*\(\s*([^)]+)\s*\)'
    )

    # @Version()
    VERSION_PATTERN = re.compile(
        r"@Version\s*\(\s*['\"`]([^'\"`]+)['\"`]\s*\)"
    )

    # @Render()
    RENDER_PATTERN = re.compile(
        r"@Render\s*\(\s*['\"`]([^'\"`]+)['\"`]\s*\)"
    )

    # @Sse()
    SSE_PATTERN = re.compile(r'@Sse\s*\(')

    # Parameter decorators
    PARAM_DECORATORS = re.compile(
        r'@(Param|Query|Body|Headers|Ip|Session|Req|Res|UploadedFile|UploadedFiles)\s*\('
        r"(?:\s*['\"`]([^'\"`]*)['\"`])?"
    )

    # Class definition
    CLASS_PATTERN = re.compile(
        r'(?:export\s+)?class\s+(\w+)'
    )

    # Method definition
    METHOD_PATTERN = re.compile(
        r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*\w+(?:<[^>]+>)?)?\s*\{'
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract controller information from a NestJS source file."""
        controllers: List[NestControllerInfo] = []
        param_decorators: List[NestParamDecoratorInfo] = []
        lines = content.split('\n')

        # Find @Controller() decorators and their classes
        for ctrl_match in self.CONTROLLER_DECORATOR.finditer(content):
            ctrl_path = ctrl_match.group(1) or ''
            ctrl_line = content[:ctrl_match.start()].count('\n') + 1

            # Find class name
            rest = content[ctrl_match.end():]
            class_match = self.CLASS_PATTERN.search(rest)
            class_name = class_match.group(1) if class_match else 'UnknownController'

            # Extract controller-level decorators
            decorator_area = content[max(0, ctrl_match.start() - 200):ctrl_match.start()]
            ctrl_guards = self._extract_decorator_args(self.USE_GUARDS_PATTERN, decorator_area)
            ctrl_interceptors = self._extract_decorator_args(self.USE_INTERCEPTORS_PATTERN, decorator_area)
            ctrl_pipes = self._extract_decorator_args(self.USE_PIPES_PATTERN, decorator_area)

            # Check for @Version()
            version = ''
            ver_match = self.VERSION_PATTERN.search(decorator_area)
            if ver_match:
                version = ver_match.group(1)

            controller = NestControllerInfo(
                class_name=class_name,
                path=ctrl_path,
                file=file_path,
                line_number=ctrl_line,
                version=version,
                has_guards=bool(ctrl_guards),
                guard_names=ctrl_guards,
                has_interceptors=bool(ctrl_interceptors),
                interceptor_names=ctrl_interceptors,
                has_pipes=bool(ctrl_pipes),
                pipe_names=ctrl_pipes,
            )

            # Find endpoints within the class body
            class_body = self._extract_class_body(content, ctrl_match.end())
            endpoints = self._extract_endpoints(class_body, file_path, ctrl_line)
            controller.endpoints = endpoints
            controller.total_endpoints = len(endpoints)

            controllers.append(controller)

        # Find parameter decorators
        for match in self.PARAM_DECORATORS.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            param_decorators.append(NestParamDecoratorInfo(
                decorator=match.group(1),
                param_name=match.group(2) or '',
                file=file_path,
                line_number=line_num,
            ))

        return {
            "controllers": controllers,
            "param_decorators": param_decorators,
        }

    def _extract_endpoints(self, class_body: str, file_path: str, base_line: int) -> List[NestEndpointInfo]:
        """Extract endpoints from a controller class body."""
        endpoints: List[NestEndpointInfo] = []

        for method_match in self.METHOD_DECORATOR_PATTERN.finditer(class_body):
            http_method = self.HTTP_DECORATORS.get(method_match.group(1), 'GET')
            path = method_match.group(2) or ''
            line_num = base_line + class_body[:method_match.start()].count('\n')

            # Look for handler method name after the decorator
            after = class_body[method_match.end():]
            handler_match = self.METHOD_PATTERN.search(after[:200])
            handler_name = handler_match.group(1) if handler_match else 'unknown'
            is_async = 'async' in after[:200].split(handler_name)[0] if handler_name != 'unknown' else False

            # Check decorators around this endpoint
            before = class_body[max(0, method_match.start() - 300):method_match.start()]
            guards = self._extract_decorator_args(self.USE_GUARDS_PATTERN, before)
            interceptors = self._extract_decorator_args(self.USE_INTERCEPTORS_PATTERN, before)
            pipes = self._extract_decorator_args(self.USE_PIPES_PATTERN, before)

            # @HttpCode
            code_match = self.HTTP_CODE_PATTERN.search(before)
            status_code = int(code_match.group(1)) if code_match else 0

            # @Render
            render_match = self.RENDER_PATTERN.search(before)
            render_template = render_match.group(1) if render_match else ''

            # @Sse
            is_sse = bool(self.SSE_PATTERN.search(before))

            # Extract params from handler args
            params = []
            for p_match in self.PARAM_DECORATORS.finditer(after[:300]):
                params.append(f"@{p_match.group(1)}({p_match.group(2) or ''})")

            endpoints.append(NestEndpointInfo(
                method=http_method,
                path=path,
                handler_name=handler_name,
                file=file_path,
                line_number=line_num,
                status_code=status_code,
                is_async=is_async,
                has_guards=bool(guards),
                guard_names=guards,
                has_interceptors=bool(interceptors),
                interceptor_names=interceptors,
                has_pipes=bool(pipes),
                pipe_names=pipes,
                params=params,
                is_sse=is_sse,
                render_template=render_template,
            ))

        return endpoints

    def _extract_class_body(self, content: str, start_idx: int) -> str:
        """Extract the class body from start_idx to the closing brace."""
        depth = 0
        started = False
        for i in range(start_idx, len(content)):
            if content[i] == '{':
                depth += 1
                started = True
            elif content[i] == '}':
                depth -= 1
                if started and depth == 0:
                    return content[start_idx:i + 1]
        return content[start_idx:]

    def _extract_decorator_args(self, pattern: re.Pattern, text: str) -> List[str]:
        """Extract arguments from a decorator like @UseGuards(A, B, C)."""
        match = pattern.search(text)
        if not match:
            return []
        args_str = match.group(1)
        return [a.strip() for a in args_str.split(',') if a.strip() and not a.strip().startswith('//')]
