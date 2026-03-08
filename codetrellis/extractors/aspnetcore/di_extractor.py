"""
ASP.NET Core Dependency Injection Extractor.

Extracts service registrations, DI container configuration, and lifetime management.

Supports:
- AddSingleton, AddScoped, AddTransient registrations
- Interface-to-implementation bindings
- Factory registrations
- Named/keyed services (.NET 8+)
- Extension method registrations (AddDbContext, AddIdentity, AddSwaggerGen, etc.)
- IServiceCollection configuration

Part of CodeTrellis v4.96
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class AspNetServiceRegistration:
    """Information about a DI service registration."""
    service_type: str = ""         # Interface or abstract class
    implementation_type: str = ""  # Concrete class
    lifetime: str = ""             # singleton, scoped, transient
    method: str = ""               # AddSingleton, AddScoped, AddTransient, etc.
    is_factory: bool = False       # Factory-based registration
    is_keyed: bool = False         # .NET 8 keyed services
    key: str = ""                  # Key for keyed services
    is_extension: bool = False     # Extension method (AddDbContext, etc.)
    file: str = ""
    line_number: int = 0


@dataclass
class AspNetDIContainerInfo:
    """Aggregate DI container information."""
    registrations: List[AspNetServiceRegistration] = field(default_factory=list)
    singleton_count: int = 0
    scoped_count: int = 0
    transient_count: int = 0
    factory_count: int = 0
    has_keyed_services: bool = False
    hosting_model: str = ""  # "startup" or "minimal"
    file: str = ""


class AspNetCoreDIExtractor:
    """Extracts ASP.NET Core dependency injection configuration."""

    # Standard lifetime registrations
    LIFETIME_PATTERNS = {
        'singleton': re.compile(
            r'\.AddSingleton\s*<\s*(\w+(?:<[^>]+>)?)\s*(?:,\s*(\w+(?:<[^>]+>)?)\s*)?>\s*\(',
            re.MULTILINE
        ),
        'scoped': re.compile(
            r'\.AddScoped\s*<\s*(\w+(?:<[^>]+>)?)\s*(?:,\s*(\w+(?:<[^>]+>)?)\s*)?>\s*\(',
            re.MULTILINE
        ),
        'transient': re.compile(
            r'\.AddTransient\s*<\s*(\w+(?:<[^>]+>)?)\s*(?:,\s*(\w+(?:<[^>]+>)?)\s*)?>\s*\(',
            re.MULTILINE
        ),
    }

    # Non-generic registrations: AddSingleton(typeof(IService), typeof(Service))
    TYPEOF_PATTERN = re.compile(
        r'\.(AddSingleton|AddScoped|AddTransient)\s*\(\s*typeof\(\s*(\w+)\s*\)\s*,\s*typeof\(\s*(\w+)\s*\)',
        re.MULTILINE
    )

    # Keyed service registrations (.NET 8+)
    KEYED_PATTERN = re.compile(
        r'\.(AddKeyed(?:Singleton|Scoped|Transient))\s*<\s*(\w+(?:<[^>]+>)?)\s*(?:,\s*(\w+(?:<[^>]+>)?)\s*)?>'
        r'\s*\(\s*["\'](\w+)["\']\s*\)',
        re.MULTILINE
    )

    # Extension method registrations (common framework registrations)
    EXTENSION_PATTERNS = {
        'AddDbContext': re.compile(r'\.AddDbContext\s*<\s*(\w+)\s*>\s*\(', re.MULTILINE),
        'AddIdentity': re.compile(r'\.AddIdentity\s*<\s*(\w+)\s*,\s*(\w+)\s*>\s*\(', re.MULTILINE),
        'AddSwaggerGen': re.compile(r'\.AddSwaggerGen\s*\(', re.MULTILINE),
        'AddControllers': re.compile(r'\.AddControllers\s*\(', re.MULTILINE),
        'AddControllersWithViews': re.compile(r'\.AddControllersWithViews\s*\(', re.MULTILINE),
        'AddRazorPages': re.compile(r'\.AddRazorPages\s*\(', re.MULTILINE),
        'AddSignalR': re.compile(r'\.AddSignalR\s*\(', re.MULTILINE),
        'AddGrpc': re.compile(r'\.AddGrpc\s*\(', re.MULTILINE),
        'AddHealthChecks': re.compile(r'\.AddHealthChecks\s*\(', re.MULTILINE),
        'AddMediatR': re.compile(r'\.AddMediatR\s*\(', re.MULTILINE),
        'AddAutoMapper': re.compile(r'\.AddAutoMapper\s*\(', re.MULTILINE),
        'AddMassTransit': re.compile(r'\.AddMassTransit\s*\(', re.MULTILINE),
        'AddHangfire': re.compile(r'\.AddHangfire\s*\(', re.MULTILINE),
        'AddAuthentication': re.compile(r'\.AddAuthentication\s*\(', re.MULTILINE),
        'AddAuthorization': re.compile(r'\.AddAuthorization\s*\(', re.MULTILINE),
        'AddCors': re.compile(r'\.AddCors\s*\(', re.MULTILINE),
        'AddMemoryCache': re.compile(r'\.AddMemoryCache\s*\(', re.MULTILINE),
        'AddStackExchangeRedisCache': re.compile(r'\.AddStackExchangeRedisCache\s*\(', re.MULTILINE),
        'AddHttpClient': re.compile(r'\.AddHttpClient\s*(?:<\s*(\w+)\s*>)?\s*\(', re.MULTILINE),
        'AddLogging': re.compile(r'\.AddLogging\s*\(', re.MULTILINE),
    }

    # ConfigureServices method
    CONFIGURE_SERVICES_PATTERN = re.compile(
        r'(?:public\s+void\s+ConfigureServices|void\s+ConfigureServices)\s*\(\s*IServiceCollection',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract DI registrations and container configuration."""
        result = {
            'registrations': [],
            'container_info': None,
        }

        if not content or not content.strip():
            return result

        registrations = []

        # Standard lifetime registrations
        for lifetime, pattern in self.LIFETIME_PATTERNS.items():
            for match in pattern.finditer(content):
                service_type = match.group(1)
                impl_type = match.group(2) or service_type
                line = content[:match.start()].count('\n') + 1

                # Check if factory (lambda after opening paren)
                after = content[match.end():match.end() + 100]
                is_factory = '=>' in after.split(')')[0] if ')' in after else False

                registrations.append(AspNetServiceRegistration(
                    service_type=service_type,
                    implementation_type=impl_type,
                    lifetime=lifetime,
                    method=f"Add{lifetime.capitalize()}",
                    is_factory=is_factory,
                    file=file_path,
                    line_number=line,
                ))

        # typeof() registrations
        for match in self.TYPEOF_PATTERN.finditer(content):
            method = match.group(1)
            lifetime = method.replace('Add', '').lower()
            line = content[:match.start()].count('\n') + 1
            registrations.append(AspNetServiceRegistration(
                service_type=match.group(2),
                implementation_type=match.group(3),
                lifetime=lifetime,
                method=method,
                file=file_path,
                line_number=line,
            ))

        # Keyed services
        for match in self.KEYED_PATTERN.finditer(content):
            method = match.group(1)
            lifetime = 'singleton' if 'Singleton' in method else ('scoped' if 'Scoped' in method else 'transient')
            line = content[:match.start()].count('\n') + 1
            registrations.append(AspNetServiceRegistration(
                service_type=match.group(2),
                implementation_type=match.group(3) or match.group(2),
                lifetime=lifetime,
                method=method,
                is_keyed=True,
                key=match.group(4),
                file=file_path,
                line_number=line,
            ))

        # Extension method registrations
        for ext_name, pattern in self.EXTENSION_PATTERNS.items():
            for match in pattern.finditer(content):
                line = content[:match.start()].count('\n') + 1
                service_type = match.group(1) if match.lastindex and match.group(1) else ext_name
                registrations.append(AspNetServiceRegistration(
                    service_type=service_type,
                    implementation_type="",
                    lifetime="extension",
                    method=ext_name,
                    is_extension=True,
                    file=file_path,
                    line_number=line,
                ))

        result['registrations'] = registrations

        # Build container info
        singleton_count = sum(1 for r in registrations if r.lifetime == 'singleton')
        scoped_count = sum(1 for r in registrations if r.lifetime == 'scoped')
        transient_count = sum(1 for r in registrations if r.lifetime == 'transient')

        hosting = "minimal"
        if self.CONFIGURE_SERVICES_PATTERN.search(content):
            hosting = "startup"

        result['container_info'] = AspNetDIContainerInfo(
            registrations=registrations,
            singleton_count=singleton_count,
            scoped_count=scoped_count,
            transient_count=transient_count,
            factory_count=sum(1 for r in registrations if r.is_factory),
            has_keyed_services=any(r.is_keyed for r in registrations),
            hosting_model=hosting,
            file=file_path,
        )

        return result
