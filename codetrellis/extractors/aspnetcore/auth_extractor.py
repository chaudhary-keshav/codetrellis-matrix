"""
ASP.NET Core Authentication/Authorization Extractor.

Extracts auth schemes, policies, requirements, and role-based access patterns.

Supports:
- JWT Bearer, Cookie, OAuth, OpenID Connect schemes
- Authorization policies with requirements
- Role-based authorization
- Claims-based authorization
- Resource-based authorization
- Custom authorization handlers
- Identity configuration

Part of CodeTrellis v4.96
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class AspNetAuthSchemeInfo:
    """Information about an authentication scheme."""
    name: str = ""                 # Scheme name
    kind: str = ""                 # jwt, cookie, oauth, oidc, custom
    handler_type: str = ""         # JwtBearerHandler, CookieAuthenticationHandler, etc.
    options: Dict[str, str] = field(default_factory=dict)
    file: str = ""
    line_number: int = 0


@dataclass
class AspNetAuthPolicyInfo:
    """Information about an authorization policy."""
    name: str = ""
    requirements: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    claims: List[str] = field(default_factory=list)
    schemes: List[str] = field(default_factory=list)
    is_default: bool = False
    is_fallback: bool = False
    file: str = ""
    line_number: int = 0


class AspNetCoreAuthExtractor:
    """Extracts ASP.NET Core authentication and authorization configuration."""

    # AddAuthentication().AddJwtBearer()
    ADD_AUTH_PATTERN = re.compile(
        r'\.AddAuthentication\s*\(\s*(?:["\'](\w+)["\']|(\w+\.\w+))?\s*\)',
        re.MULTILINE
    )

    # Scheme-specific patterns
    SCHEME_PATTERNS = {
        'jwt': re.compile(r'\.AddJwtBearer\s*\(', re.MULTILINE),
        'cookie': re.compile(r'\.AddCookie\s*\(', re.MULTILINE),
        'oauth': re.compile(r'\.AddOAuth\s*\(', re.MULTILINE),
        'oidc': re.compile(r'\.AddOpenIdConnect\s*\(', re.MULTILINE),
        'google': re.compile(r'\.AddGoogle\s*\(', re.MULTILINE),
        'microsoft': re.compile(r'\.AddMicrosoftAccount\s*\(', re.MULTILINE),
        'github': re.compile(r'\.AddGitHub\s*\(', re.MULTILINE),
    }

    # AddAuthorization with policies
    ADD_AUTHORIZATION_PATTERN = re.compile(
        r'\.AddAuthorization\s*\(\s*(?:options|opts|o)\s*=>',
        re.MULTILINE
    )

    # Policy.AddPolicy
    ADD_POLICY_PATTERN = re.compile(
        r'\.AddPolicy\s*\(\s*["\'](\w+)["\']\s*,\s*(?:policy|p|builder)\s*=>',
        re.MULTILINE
    )

    # RequireRole
    REQUIRE_ROLE_PATTERN = re.compile(
        r'\.RequireRole\s*\(\s*["\']([^"\']+)["\']\s*(?:,\s*["\']([^"\']+)["\']\s*)*\)',
        re.MULTILINE
    )

    # RequireClaim
    REQUIRE_CLAIM_PATTERN = re.compile(
        r'\.RequireClaim\s*\(\s*["\']([^"\']+)["\']\s*(?:,\s*["\']([^"\']+)["\'])?\s*\)',
        re.MULTILINE
    )

    # Custom AuthorizationHandler
    AUTH_HANDLER_PATTERN = re.compile(
        r'class\s+(\w+)\s*:\s*AuthorizationHandler\s*<\s*(\w+)\s*(?:,\s*(\w+))?\s*>',
        re.MULTILINE
    )

    # IAuthorizationRequirement
    AUTH_REQUIREMENT_PATTERN = re.compile(
        r'class\s+(\w+)\s*:\s*IAuthorizationRequirement',
        re.MULTILINE
    )

    # DefaultPolicy / FallbackPolicy
    DEFAULT_POLICY_PATTERN = re.compile(
        r'\.DefaultPolicy\s*=|\.FallbackPolicy\s*=',
        re.MULTILINE
    )

    # AddIdentity<TUser, TRole>
    ADD_IDENTITY_PATTERN = re.compile(
        r'\.AddIdentity\s*<\s*(\w+)\s*,\s*(\w+)\s*>\s*\(',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract authentication and authorization configuration."""
        result = {
            'auth_schemes': [],
            'auth_policies': [],
            'auth_handlers': [],
            'auth_requirements': [],
            'identity_config': None,
        }

        if not content or not content.strip():
            return result

        # Extract auth schemes
        for scheme_name, pattern in self.SCHEME_PATTERNS.items():
            for match in pattern.finditer(content):
                line = content[:match.start()].count('\n') + 1
                result['auth_schemes'].append(AspNetAuthSchemeInfo(
                    name=scheme_name,
                    kind=scheme_name,
                    file=file_path,
                    line_number=line,
                ))

        # Extract policies
        for match in self.ADD_POLICY_PATTERN.finditer(content):
            policy_name = match.group(1)
            line = content[:match.start()].count('\n') + 1

            # Look ahead for requirements
            after = content[match.end():match.end() + 500]
            roles = []
            claims = []
            requirements = []

            for role_match in self.REQUIRE_ROLE_PATTERN.finditer(after):
                roles.append(role_match.group(1))
                if role_match.group(2):
                    roles.append(role_match.group(2))

            for claim_match in self.REQUIRE_CLAIM_PATTERN.finditer(after):
                claims.append(claim_match.group(1))

            # RequireAuthenticatedUser
            if 'RequireAuthenticatedUser' in after[:300]:
                requirements.append('RequireAuthenticatedUser')

            result['auth_policies'].append(AspNetAuthPolicyInfo(
                name=policy_name,
                requirements=requirements,
                roles=roles,
                claims=claims,
                file=file_path,
                line_number=line,
            ))

        # Custom handlers
        for match in self.AUTH_HANDLER_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['auth_handlers'].append({
                'name': match.group(1),
                'requirement': match.group(2),
                'resource': match.group(3) or "",
                'file': file_path,
                'line': line,
            })

        # Custom requirements
        for match in self.AUTH_REQUIREMENT_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['auth_requirements'].append(match.group(1))

        # Identity config
        identity_match = self.ADD_IDENTITY_PATTERN.search(content)
        if identity_match:
            result['identity_config'] = {
                'user_type': identity_match.group(1),
                'role_type': identity_match.group(2),
            }

        return result
