"""
ASP.NET Core Middleware Extractor.

Extracts middleware registrations, custom middleware classes, and pipeline configuration.

Supports:
- app.UseMiddleware<T>() / app.Use() / app.Map() / app.Run()
- IMiddleware interface implementations
- Inline middleware (app.Use(async (context, next) => {...}))
- Startup.Configure() pipeline analysis
- WebApplication pipeline (minimal hosting)
- Health check middleware
- CORS, Authentication, Authorization middleware ordering

Part of CodeTrellis v4.96
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class AspNetMiddlewareInfo:
    """Information about a middleware registration or definition."""
    name: str = ""
    kind: str = ""          # builtin, custom, inline
    method: str = ""        # Use, UseMiddleware, Run, Map, MapWhen
    order: int = 0          # Pipeline order
    condition: str = ""     # For MapWhen/UseWhen conditions
    file: str = ""
    line_number: int = 0


@dataclass
class AspNetMiddlewarePipelineInfo:
    """Information about the overall middleware pipeline."""
    middlewares: List[AspNetMiddlewareInfo] = field(default_factory=list)
    has_auth: bool = False
    has_cors: bool = False
    has_https_redirect: bool = False
    has_static_files: bool = False
    has_routing: bool = False
    has_health_checks: bool = False
    has_swagger: bool = False
    has_rate_limiting: bool = False
    has_response_caching: bool = False
    hosting_model: str = ""  # "startup" or "minimal"
    file: str = ""


class AspNetCoreMiddlewareExtractor:
    """Extracts ASP.NET Core middleware pipeline and custom middleware definitions."""

    # Built-in middleware patterns
    BUILTIN_MIDDLEWARE = {
        'UseAuthentication': 'authentication',
        'UseAuthorization': 'authorization',
        'UseCors': 'cors',
        'UseHttpsRedirection': 'https_redirect',
        'UseStaticFiles': 'static_files',
        'UseRouting': 'routing',
        'UseEndpoints': 'endpoints',
        'UseHealthChecks': 'health_checks',
        'UseSwagger': 'swagger',
        'UseSwaggerUI': 'swagger_ui',
        'UseRateLimiter': 'rate_limiting',
        'UseResponseCaching': 'response_caching',
        'UseResponseCompression': 'response_compression',
        'UseExceptionHandler': 'exception_handler',
        'UseDeveloperExceptionPage': 'developer_exception_page',
        'UseHsts': 'hsts',
        'UseSession': 'session',
        'UseMvc': 'mvc',
        'UseWebSockets': 'websockets',
        'UseSignalR': 'signalr',
        'UseSerilogRequestLogging': 'serilog_logging',
        'UseForwardedHeaders': 'forwarded_headers',
        'UseOutputCache': 'output_cache',
        'UseRequestLocalization': 'localization',
        'UseDefaultFiles': 'default_files',
    }

    # Middleware registration pattern
    USE_PATTERN = re.compile(
        r'(?:app|builder|webApp)\s*\.\s*(Use\w*|Map\w*|Run)\s*[<(]',
        re.MULTILINE
    )

    # UseMiddleware<T> pattern
    USE_MIDDLEWARE_PATTERN = re.compile(
        r'\.UseMiddleware\s*<\s*(\w+)\s*>\s*\(\s*\)',
        re.MULTILINE
    )

    # Custom middleware class (IMiddleware)
    CUSTOM_MIDDLEWARE_PATTERN = re.compile(
        r'class\s+(\w+)\s*:\s*IMiddleware',
        re.MULTILINE
    )

    # Convention-based middleware (has InvokeAsync/Invoke method with HttpContext)
    CONVENTION_MIDDLEWARE_PATTERN = re.compile(
        r'class\s+(\w+)(?:\s*:\s*\w+)?\s*\{[^}]*?'
        r'(?:public\s+(?:async\s+)?Task\s+(?:InvokeAsync|Invoke)\s*\(\s*HttpContext)',
        re.MULTILINE | re.DOTALL
    )

    # Startup.Configure method
    CONFIGURE_PATTERN = re.compile(
        r'public\s+void\s+Configure\s*\(\s*IApplicationBuilder\s+\w+',
        re.MULTILINE
    )

    # MapWhen/UseWhen condition
    MAP_WHEN_PATTERN = re.compile(
        r'\.(MapWhen|UseWhen)\s*\(\s*(?:context\s*=>|ctx\s*=>)\s*([^,]+),',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract middleware pipeline and custom middleware."""
        result = {
            'middlewares': [],
            'pipeline': None,
            'custom_middlewares': [],
        }

        if not content or not content.strip():
            return result

        # Extract pipeline
        middlewares = self._extract_pipeline(content, file_path)
        result['middlewares'] = middlewares

        # Build pipeline info
        result['pipeline'] = self._build_pipeline_info(middlewares, content, file_path)

        # Extract custom middleware classes
        result['custom_middlewares'] = self._extract_custom_middlewares(content, file_path)

        return result

    def _extract_pipeline(self, content: str, file_path: str) -> List[AspNetMiddlewareInfo]:
        """Extract middleware registrations in order."""
        middlewares = []
        order = 0

        for match in self.USE_PATTERN.finditer(content):
            method_name = match.group(1)
            line = content[:match.start()].count('\n') + 1

            # Determine kind
            kind = "builtin" if method_name in self.BUILTIN_MIDDLEWARE else "custom"
            if method_name in ('Use', 'Run'):
                # Check if it's inline
                after = content[match.end():match.end() + 100]
                if '=>' in after or 'async' in after:
                    kind = "inline"

            order += 1
            middlewares.append(AspNetMiddlewareInfo(
                name=self.BUILTIN_MIDDLEWARE.get(method_name, method_name),
                kind=kind,
                method=method_name,
                order=order,
                file=file_path,
                line_number=line,
            ))

        # UseMiddleware<T>
        for match in self.USE_MIDDLEWARE_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            order += 1
            middlewares.append(AspNetMiddlewareInfo(
                name=match.group(1),
                kind="custom",
                method="UseMiddleware",
                order=order,
                file=file_path,
                line_number=line,
            ))

        # MapWhen/UseWhen
        for match in self.MAP_WHEN_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            order += 1
            middlewares.append(AspNetMiddlewareInfo(
                name=match.group(1),
                kind="conditional",
                method=match.group(1),
                condition=match.group(2).strip()[:100],
                order=order,
                file=file_path,
                line_number=line,
            ))

        return middlewares

    def _extract_custom_middlewares(self, content: str, file_path: str) -> List[AspNetMiddlewareInfo]:
        """Extract custom middleware class definitions."""
        custom = []

        # IMiddleware interface
        for match in self.CUSTOM_MIDDLEWARE_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            custom.append(AspNetMiddlewareInfo(
                name=match.group(1),
                kind="custom_class",
                method="IMiddleware",
                file=file_path,
                line_number=line,
            ))

        # Convention-based middleware
        for match in self.CONVENTION_MIDDLEWARE_PATTERN.finditer(content):
            name = match.group(1)
            # Avoid duplicates with IMiddleware
            if not any(m.name == name for m in custom):
                line = content[:match.start()].count('\n') + 1
                custom.append(AspNetMiddlewareInfo(
                    name=name,
                    kind="custom_convention",
                    method="InvokeAsync",
                    file=file_path,
                    line_number=line,
                ))

        return custom

    def _build_pipeline_info(self, middlewares: List[AspNetMiddlewareInfo],
                             content: str, file_path: str) -> AspNetMiddlewarePipelineInfo:
        """Build aggregate pipeline information."""
        names = {m.name for m in middlewares}

        # Detect hosting model
        hosting = "minimal"
        if self.CONFIGURE_PATTERN.search(content):
            hosting = "startup"

        return AspNetMiddlewarePipelineInfo(
            middlewares=middlewares,
            has_auth='authentication' in names or 'authorization' in names,
            has_cors='cors' in names,
            has_https_redirect='https_redirect' in names,
            has_static_files='static_files' in names,
            has_routing='routing' in names,
            has_health_checks='health_checks' in names,
            has_swagger='swagger' in names or 'swagger_ui' in names,
            has_rate_limiting='rate_limiting' in names,
            has_response_caching='response_caching' in names or 'output_cache' in names,
            hosting_model=hosting,
            file=file_path,
        )
