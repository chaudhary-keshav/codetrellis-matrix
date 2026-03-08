"""
EnhancedASPNetCoreParser v1.0 - Comprehensive per-file ASP.NET Core parser.

This parser integrates all ASP.NET Core extractors to provide complete per-file
parsing. It runs as a supplementary layer on top of the C# parser when ASP.NET
Core framework is detected.

Supports:
- ASP.NET Core 2.x (Initial minimal hosting patterns)
- ASP.NET Core 3.x (Endpoint routing, gRPC support)
- ASP.NET Core 5.x (Minimal APIs preview)
- ASP.NET Core 6.x (Minimal APIs, WebApplicationBuilder)
- ASP.NET Core 7.x (Rate limiting, output caching, route groups)
- ASP.NET Core 8.x (Keyed services, short-circuit routing, native AOT)
- ASP.NET Core 9.x (HybridCache, OpenAPI improvements)

ASP.NET Core extraction:
- Controllers: MVC/API controllers, action methods, route attributes, filters
- Minimal APIs: MapGet/MapPost/MapPut/MapDelete, route groups, endpoint filters
- Middleware: Pipeline order, built-in + custom middleware, IMiddleware
- DI: Service registrations (singleton/scoped/transient), factories, keyed services
- Configuration: IOptions<T> pattern, configuration binding, sections
- Authentication: JWT, Cookie, OAuth, OpenID Connect, Identity
- Authorization: Policies, requirements, roles, claims
- Health checks, API versioning, CORS, response caching

Part of CodeTrellis v4.96 - .NET Framework Enhanced Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path

from .extractors.aspnetcore import (
    AspNetCoreControllerExtractor,
    AspNetControllerInfo,
    AspNetEndpointInfo,
    AspNetMinimalApiInfo,
    AspNetFilterInfo,
    AspNetCoreMiddlewareExtractor,
    AspNetMiddlewareInfo,
    AspNetMiddlewarePipelineInfo,
    AspNetCoreDIExtractor,
    AspNetServiceRegistration,
    AspNetDIContainerInfo,
    AspNetCoreConfigExtractor,
    AspNetConfigBindingInfo,
    AspNetOptionsPatternInfo,
    AspNetCoreAuthExtractor,
    AspNetAuthSchemeInfo,
    AspNetAuthPolicyInfo,
)


@dataclass
class ASPNetCoreParseResult:
    """Complete parse result for an ASP.NET Core file."""
    file_path: str
    file_type: str = "unknown"  # controller, startup, program, middleware, config, service, hub

    # Controllers & Endpoints
    controllers: List[AspNetControllerInfo] = field(default_factory=list)
    minimal_apis: List[AspNetMinimalApiInfo] = field(default_factory=list)
    filters: List[AspNetFilterInfo] = field(default_factory=list)

    # Middleware
    middlewares: List[AspNetMiddlewareInfo] = field(default_factory=list)
    pipeline: Optional[AspNetMiddlewarePipelineInfo] = None
    custom_middlewares: List[AspNetMiddlewareInfo] = field(default_factory=list)

    # DI
    di_registrations: List[AspNetServiceRegistration] = field(default_factory=list)
    di_container: Optional[AspNetDIContainerInfo] = None

    # Configuration
    config_bindings: List[AspNetConfigBindingInfo] = field(default_factory=list)
    options_patterns: List[AspNetOptionsPatternInfo] = field(default_factory=list)

    # Auth
    auth_schemes: List[AspNetAuthSchemeInfo] = field(default_factory=list)
    auth_policies: List[AspNetAuthPolicyInfo] = field(default_factory=list)

    # Aggregate signals
    detected_frameworks: List[str] = field(default_factory=list)
    aspnetcore_version: str = ""
    total_endpoints: int = 0
    total_minimal_apis: int = 0
    total_di_registrations: int = 0
    hosting_model: str = ""  # "startup", "minimal", "unknown"
    has_swagger: bool = False
    has_health_checks: bool = False
    has_signalr: bool = False
    has_grpc: bool = False


class EnhancedASPNetCoreParser:
    """
    Enhanced per-file ASP.NET Core parser that uses all extractors.

    This parser is designed to run AFTER the C# parser when ASP.NET Core
    framework is detected. It extracts ASP.NET Core-specific semantics per-file.
    """

    # ASP.NET Core ecosystem framework detection patterns
    FRAMEWORK_PATTERNS = {
        'aspnetcore': re.compile(r'using\s+Microsoft\.AspNetCore\b', re.MULTILINE),
        'aspnetcore-mvc': re.compile(r'using\s+Microsoft\.AspNetCore\.Mvc\b', re.MULTILINE),
        'aspnetcore-routing': re.compile(r'using\s+Microsoft\.AspNetCore\.Routing\b|MapGet|MapPost|UseRouting', re.MULTILINE),
        'aspnetcore-auth': re.compile(r'using\s+Microsoft\.AspNetCore\.Authentication\b|AddAuthentication|UseAuthentication', re.MULTILINE),
        'aspnetcore-identity': re.compile(r'using\s+Microsoft\.AspNetCore\.Identity\b|AddIdentity|UserManager|SignInManager', re.MULTILINE),
        'aspnetcore-signalr': re.compile(r'using\s+Microsoft\.AspNetCore\.SignalR\b|MapHub|Hub<', re.MULTILINE),
        'aspnetcore-grpc': re.compile(r'using\s+Grpc\.AspNetCore\b|MapGrpcService|AddGrpc', re.MULTILINE),
        'aspnetcore-healthchecks': re.compile(r'AddHealthChecks|MapHealthChecks|UseHealthChecks|IHealthCheck', re.MULTILINE),
        'aspnetcore-versioning': re.compile(r'AddApiVersioning|ApiVersion|MapToApiVersion', re.MULTILINE),
        'aspnetcore-ratelimiting': re.compile(r'AddRateLimiter|UseRateLimiter|RateLimitPartition|EnableRateLimiting', re.MULTILINE),
        'aspnetcore-outputcache': re.compile(r'AddOutputCache|UseOutputCache|OutputCache', re.MULTILINE),
        'aspnetcore-minimalapis': re.compile(r'WebApplication\.Create|app\.Map(?:Get|Post|Put|Delete|Patch)|MapGroup', re.MULTILINE),
        'swashbuckle': re.compile(r'AddSwaggerGen|UseSwagger|UseSwaggerUI|SwaggerDoc', re.MULTILINE),
        'nswag': re.compile(r'using\s+NSwag\b|AddOpenApiDocument', re.MULTILINE),
        'fluentvalidation': re.compile(r'using\s+FluentValidation\b|AbstractValidator|IRuleBuilder', re.MULTILINE),
        'serilog': re.compile(r'using\s+Serilog\b|UseSerilog|Log\.Information|LoggerConfiguration', re.MULTILINE),
        'automapper': re.compile(r'using\s+AutoMapper\b|AddAutoMapper|IMapper', re.MULTILINE),
        'mediatr': re.compile(r'using\s+MediatR\b|AddMediatR|IMediator|ISender', re.MULTILINE),
        'polly': re.compile(r'using\s+Polly\b|AddPolicyHandler|AddTransientHttpErrorPolicy', re.MULTILINE),
        'hangfire': re.compile(r'using\s+Hangfire\b|AddHangfire|UseHangfire', re.MULTILINE),
        'masstransit': re.compile(r'using\s+MassTransit\b|AddMassTransit|IBus', re.MULTILINE),
    }

    # ASP.NET Core version detection
    VERSION_FEATURES = {
        'WebApplication.CreateBuilder': '6.0',
        'WebApplicationBuilder': '6.0',
        'app.MapGet': '6.0',
        'app.MapPost': '6.0',
        'builder.Services': '6.0',
        'AddRateLimiter': '7.0',
        'MapGroup': '7.0',
        'AddOutputCache': '7.0',
        'UseOutputCache': '7.0',
        'ShortCircuit': '8.0',
        'AddKeyedSingleton': '8.0',
        'AddKeyedScoped': '8.0',
        'AddKeyedTransient': '8.0',
        'HybridCache': '9.0',
        'IDistributedApplicationBuilder': '8.0',  # Aspire
        'RequireAuthorization': '3.0',
        'UseEndpoints': '3.0',
        'ConfigureKestrel': '2.0',
        'ConfigureWebHostDefaults': '3.0',
    }

    def __init__(self):
        """Initialize the parser with all ASP.NET Core extractors."""
        self.controller_extractor = AspNetCoreControllerExtractor()
        self.middleware_extractor = AspNetCoreMiddlewareExtractor()
        self.di_extractor = AspNetCoreDIExtractor()
        self.config_extractor = AspNetCoreConfigExtractor()
        self.auth_extractor = AspNetCoreAuthExtractor()

    def parse(self, content: str, file_path: str = "") -> ASPNetCoreParseResult:
        """
        Parse ASP.NET Core source code and extract all framework-specific information.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            ASPNetCoreParseResult with all extracted ASP.NET Core information
        """
        result = ASPNetCoreParseResult(file_path=file_path)

        if not content or not content.strip():
            return result

        # Determine file type
        result.file_type = self._classify_file(file_path, content)

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Controllers & Endpoints ─────────────────────────────
        ctrl_result = self.controller_extractor.extract(content, file_path)
        result.controllers = ctrl_result.get('controllers', [])
        result.minimal_apis = ctrl_result.get('minimal_apis', [])
        result.filters = ctrl_result.get('filters', [])
        result.total_endpoints = sum(len(c.endpoints) for c in result.controllers)
        result.total_minimal_apis = len(result.minimal_apis)

        # ── Middleware ───────────────────────────────────────────
        mw_result = self.middleware_extractor.extract(content, file_path)
        result.middlewares = mw_result.get('middlewares', [])
        result.pipeline = mw_result.get('pipeline')
        result.custom_middlewares = mw_result.get('custom_middlewares', [])

        # ── DI ───────────────────────────────────────────────────
        di_result = self.di_extractor.extract(content, file_path)
        result.di_registrations = di_result.get('registrations', [])
        result.di_container = di_result.get('container_info')
        result.total_di_registrations = len(result.di_registrations)

        # ── Configuration ────────────────────────────────────────
        cfg_result = self.config_extractor.extract(content, file_path)
        result.config_bindings = cfg_result.get('config_bindings', [])
        result.options_patterns = cfg_result.get('options_patterns', [])

        # ── Authentication & Authorization ───────────────────────
        auth_result = self.auth_extractor.extract(content, file_path)
        result.auth_schemes = auth_result.get('auth_schemes', [])
        result.auth_policies = auth_result.get('auth_policies', [])

        # ── Version detection ────────────────────────────────────
        result.aspnetcore_version = self._detect_version(content)

        # ── Hosting model ────────────────────────────────────────
        if 'WebApplication.CreateBuilder' in content or 'WebApplication.Create' in content:
            result.hosting_model = "minimal"
        elif 'IHostBuilder' in content or 'ConfigureWebHostDefaults' in content:
            result.hosting_model = "generic_host"
        elif 'Startup' in content and 'ConfigureServices' in content:
            result.hosting_model = "startup"
        else:
            result.hosting_model = "unknown"

        # Aggregate signals
        result.has_swagger = 'swashbuckle' in result.detected_frameworks or 'nswag' in result.detected_frameworks
        result.has_health_checks = 'aspnetcore-healthchecks' in result.detected_frameworks
        result.has_signalr = 'aspnetcore-signalr' in result.detected_frameworks
        result.has_grpc = 'aspnetcore-grpc' in result.detected_frameworks

        return result

    def _classify_file(self, file_path: str, content: str) -> str:
        """Classify an ASP.NET Core file by its role."""
        normalized = file_path.replace('\\', '/').lower()
        basename = normalized.split('/')[-1] if normalized else ""

        if basename in ('program.cs', 'program.cs'):
            return 'program'
        if basename in ('startup.cs',):
            return 'startup'
        if 'controller' in basename:
            return 'controller'
        if 'middleware' in basename:
            return 'middleware'
        if 'hub' in basename:
            return 'hub'
        if 'filter' in basename:
            return 'filter'

        # Content-based
        if 'WebApplication.CreateBuilder' in content or 'IHostBuilder' in content:
            return 'program'
        if 'ConfigureServices' in content and 'Configure' in content:
            return 'startup'
        if 'ControllerBase' in content or '[ApiController]' in content:
            return 'controller'
        if 'IMiddleware' in content or 'InvokeAsync' in content:
            return 'middleware'

        return 'service'

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which ASP.NET Core ecosystem frameworks are used."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_version(self, content: str) -> str:
        """Detect the minimum ASP.NET Core version required."""
        max_version = '0.0'
        for feature, version in self.VERSION_FEATURES.items():
            if feature in content:
                if self._version_compare(version, max_version) > 0:
                    max_version = version
        return max_version if max_version != '0.0' else ''

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings."""
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        for a, b in zip(parts1, parts2):
            if a != b:
                return a - b
        return len(parts1) - len(parts2)

    def is_aspnetcore_file(self, content: str, file_path: str = "") -> bool:
        """Determine if a file is an ASP.NET Core file worth parsing."""
        # ASP.NET Core imports
        if re.search(r'using\s+Microsoft\.AspNetCore\b', content):
            return True
        # Controller pattern
        if '[ApiController]' in content or ': ControllerBase' in content or ': Controller' in content:
            return True
        # Minimal API pattern
        if 'WebApplication.CreateBuilder' in content or 'app.MapGet' in content:
            return True
        # Startup pattern
        if 'ConfigureServices' in content and 'IServiceCollection' in content:
            return True
        # Middleware
        if 'IMiddleware' in content or ('InvokeAsync' in content and 'HttpContext' in content):
            return True
        return False
