"""
CodeTrellis Security Extractor — Phase 5 of v5.0 Universal Scanner
====================================================================

Extracts security-related patterns from source code:
- Authentication mechanisms (JWT, OAuth2, session, API key)
- Authorization patterns (RBAC, ABAC, middleware guards)
- CORS configuration
- Rate limiting
- Input validation / sanitization
- Crypto usage
- Known vulnerability patterns (hardcoded secrets, SQL injection risk)

Language-agnostic with enhanced detection for Go, Python, TypeScript/JS.

Part of CodeTrellis v5.0 — Universal Scanner
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from codetrellis.file_classifier import FileClassifier, FileType, GitignoreFilter


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class AuthMechanism:
    """A detected authentication mechanism."""
    auth_type: str           # "jwt", "oauth2", "session", "api_key", "basic", "oidc"
    evidence: List[str] = field(default_factory=list)  # file paths or code snippets
    details: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "auth_type": self.auth_type,
            "evidence": self.evidence[:5],
            "details": self.details,
        }


@dataclass
class AuthzPattern:
    """A detected authorization pattern."""
    pattern_type: str        # "rbac", "abac", "middleware_guard", "policy", "decorator"
    name: Optional[str] = None
    source_file: str = ""
    details: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type,
            "name": self.name,
            "source_file": self.source_file,
            "details": self.details,
        }


@dataclass
class SecurityFlag:
    """A potential security concern or finding."""
    severity: str            # "high", "medium", "low", "info"
    category: str            # "hardcoded_secret", "sql_injection", "no_csrf", etc.
    message: str
    file_path: str = ""
    line_number: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
        }


@dataclass
class SecurityResult:
    """Complete security analysis result."""
    auth_mechanisms: List[AuthMechanism] = field(default_factory=list)
    authz_patterns: List[AuthzPattern] = field(default_factory=list)
    cors_config: Optional[Dict[str, Any]] = None
    rate_limiting: bool = False
    rate_limit_details: Optional[str] = None
    input_validation: List[str] = field(default_factory=list)
    flags: List[SecurityFlag] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "auth_mechanisms": [a.to_dict() for a in self.auth_mechanisms],
            "authz_patterns": [a.to_dict() for a in self.authz_patterns],
            "cors_config": self.cors_config,
            "rate_limiting": self.rate_limiting,
            "rate_limit_details": self.rate_limit_details,
            "input_validation": self.input_validation[:10],
            "flags": [f.to_dict() for f in self.flags],
        }

    def to_codetrellis_format(self) -> str:
        """Convert to compact CodeTrellis format."""
        lines = []
        lines.append("# Security Analysis")

        # Auth
        if self.auth_mechanisms:
            types = [a.auth_type for a in self.auth_mechanisms]
            lines.append(f"auth: {', '.join(types)}")
        else:
            lines.append("auth: NONE DETECTED")

        # Authz
        if self.authz_patterns:
            lines.append(f"authz: {len(self.authz_patterns)} pattern(s)")
            for p in self.authz_patterns[:5]:
                lines.append(f"  {p.pattern_type}: {p.name or 'unnamed'}")

        # CORS
        if self.cors_config:
            origins = self.cors_config.get('origins', [])
            lines.append(f"cors: {', '.join(str(o) for o in origins[:3])}")

        # Rate limiting
        if self.rate_limiting:
            lines.append(f"rate_limiting: yes ({self.rate_limit_details or 'detected'})")

        # Validation
        if self.input_validation:
            lines.append(f"validation: {', '.join(self.input_validation[:5])}")

        # Flags
        high = [f for f in self.flags if f.severity == 'high']
        med = [f for f in self.flags if f.severity == 'medium']
        if high or med:
            lines.append(f"## Security Flags ({len(high)} high, {len(med)} medium)")
            for flag in high + med:
                lines.append(f"  [{flag.severity}] {flag.category}: {flag.message}")

        return '\n'.join(lines)


# =============================================================================
# Detection Patterns
# =============================================================================

# Auth detection patterns (lang-agnostic)
AUTH_PATTERNS = {
    'jwt': [
        re.compile(r'jwt\.(?:sign|verify|decode|Parse|New)', re.I),
        re.compile(r'jsonwebtoken', re.I),
        re.compile(r'golang-jwt|dgrijalva/jwt', re.I),
        re.compile(r'PyJWT|jose\.jwt', re.I),
        re.compile(r'JwtModule|JwtService|JwtGuard|JwtStrategy', re.I),
        re.compile(r'Bearer\s+\w', re.I),
    ],
    'oauth2': [
        re.compile(r'oauth2?\.', re.I),
        re.compile(r'passport-oauth|passport-google|passport-github', re.I),
        re.compile(r'golang\.org/x/oauth2', re.I),
        re.compile(r'authlib|oauthlib', re.I),
        re.compile(r'OAuth2PasswordBearer|OAuth2Client', re.I),
    ],
    'session': [
        re.compile(r'express-session|cookie-session', re.I),
        re.compile(r'gorilla/sessions', re.I),
        re.compile(r'SessionMiddleware|session_middleware', re.I),
        re.compile(r'flask[._]session|django\.contrib\.sessions', re.I),
    ],
    'api_key': [
        re.compile(r'[Aa]pi[_-]?[Kk]ey.*(?:header|query|middleware)', re.I),
        re.compile(r'X-API-Key|x-api-key', re.I),
        re.compile(r'ApiKeyGuard|ApiKeyStrategy', re.I),
    ],
    'basic': [
        re.compile(r'BasicAuth|basic_auth|httpBasic', re.I),
        re.compile(r'Authorization.*Basic', re.I),
    ],
    'oidc': [
        re.compile(r'openid-connect|oidc|OpenIDConnect', re.I),
        re.compile(r'coreos/go-oidc', re.I),
    ],
}

# Authz patterns
AUTHZ_PATTERNS = [
    (re.compile(r'@(?:Roles|UseGuards|CanActivate)\(([^)]+)\)', re.I), 'decorator'),
    (re.compile(r'(?:role|permission)_required\(([^)]+)\)', re.I), 'decorator'),
    (re.compile(r'@require_(?:role|permission)\(([^)]+)\)', re.I), 'decorator'),
    (re.compile(r'casbin|casl|authz\.Authorize', re.I), 'policy'),
    (re.compile(r'\.HasRole\(|\.IsAdmin\(|\.HasPermission\(', re.I), 'rbac'),
    (re.compile(r'AuthGuard|PermissionGuard|RolesGuard', re.I), 'middleware_guard'),
    (re.compile(r'@login_required|@permission_classes', re.I), 'decorator'),
]

# CORS patterns
CORS_PATTERNS = [
    re.compile(r'cors\.New\(|cors\.Default\(\)|AllowAllOrigins|AllowOrigins', re.I),
    re.compile(r'@EnableCors|CorsMiddleware|cors\(\)', re.I),
    re.compile(r'Access-Control-Allow-Origin', re.I),
    re.compile(r'CORSMiddleware|CORS_ALLOWED_ORIGINS', re.I),
]

# Rate limiting patterns
RATE_LIMIT_PATTERNS = [
    re.compile(r'rate[_-]?limit|RateLimit|ThrottlerGuard|Throttle', re.I),
    re.compile(r'limiter\.New|tollbooth|golang\.org/x/time/rate', re.I),
    re.compile(r'express-rate-limit|@nestjs/throttler', re.I),
    re.compile(r'slowapi|django-ratelimit|flask-limiter', re.I),
]

# Validation patterns — each entry: (lib_name, regex, frozenset_of_allowed_extensions)
# Language-gated to avoid cross-language false positives (GAP-C1)
VALIDATION_LIBS = [
    ('class-validator', re.compile(r'class-validator|@IsString|@IsEmail|@IsNotEmpty', re.I),
     frozenset({'.ts', '.tsx', '.js', '.jsx'})),
    ('joi', re.compile(r'Joi\.|joi\.object', re.I),
     frozenset({'.ts', '.tsx', '.js', '.jsx'})),
    ('zod', re.compile(r'z\.object\(|z\.string\(\)|from\s+[\'"]zod[\'"]', re.I),
     frozenset({'.ts', '.tsx', '.js', '.jsx'})),
    ('go-validator', re.compile(r'validate:"required|govalidator|binding:"required', re.I),
     frozenset({'.go'})),
    ('pydantic', re.compile(r'from\s+pydantic|import\s+pydantic|BaseModel\)', re.I),
     frozenset({'.py'})),
    ('marshmallow', re.compile(r'from\s+marshmallow|import\s+marshmallow|marshmallow\.Schema', re.I),
     frozenset({'.py'})),
    ('cerberus', re.compile(r'from\s+cerberus|import\s+cerberus|cerberus\.Validator', re.I),
     frozenset({'.py'})),
]

# Hardcoded secret patterns (potential findings)
SECRET_PATTERNS = [
    (re.compile(r'(?:password|secret|api_key|token)\s*=\s*["\'][^"\']{8,}["\']', re.I), 'hardcoded_secret'),
    (re.compile(r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----', re.I), 'hardcoded_private_key'),
    (re.compile(r'(?:AKIA|AGPA|AROA|AIDA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}', re.I), 'aws_key'),
]


# =============================================================================
# Security Extractor
# =============================================================================

class SecurityExtractor:
    """
    Extract security-related patterns from source code.
    """

    IGNORE_DIRS = {
        'node_modules', '.git', 'dist', 'build', '__pycache__',
        'vendor', '.next', 'coverage', 'venv', '.venv',
    }

    # Directories whose content is example/tutorial code (GAP-C4)
    # Now delegates to unified FileClassifier (Phase 1 systemic improvement).
    EXAMPLE_DIRS = FileClassifier.EXAMPLE_DIRS

    SOURCE_EXTENSIONS = {
        '.go', '.py', '.ts', '.js', '.tsx', '.jsx',
        '.java', '.kt', '.rs', '.rb',
    }

    def extract_from_directory(self, root_dir: Path,
                               gitignore_filter: Optional[GitignoreFilter] = None,
                               ) -> Optional[SecurityResult]:
        """
        Scan project for security patterns.

        Args:
            root_dir: Root directory to scan
            gitignore_filter: Optional GitignoreFilter to respect .gitignore rules

        Returns:
            SecurityResult or None if nothing found
        """
        result = SecurityResult()
        auth_evidence: Dict[str, List[str]] = {}

        gi = gitignore_filter

        for root, dirs, files in _walk_compat(root_dir):
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS
                       and not (gi and not gi.is_empty and gi.should_ignore(
                           os.path.relpath(os.path.join(str(root), d), str(root_dir)),
                           is_dir=True))]

            # GAP-C4: Check if we're in an example/vendor/generated directory
            # Uses unified FileClassifier (Phase 1 systemic improvement)
            rel_path = str(root.relative_to(root_dir)) if root != root_dir else ''
            in_example_dir = FileClassifier.should_skip_for_detection(rel_path) if rel_path else False

            for f in files:
                fp = root / f
                ext = fp.suffix.lower()
                name = fp.name.lower()
                
                # Gap #7 Fix: Skip test files and extractor code to avoid false positives
                file_rel_path = str(fp.relative_to(root_dir))
                is_test_file = (
                    FileClassifier.classify_file(file_rel_path) == FileType.TEST or
                    'test' in file_rel_path.lower() or
                    '_test.' in name or
                    '.test.' in name or
                    name.endswith('_extractor.py') or
                    name.endswith('extractor.py')
                )
                
                if is_test_file:
                    continue

                if ext not in self.SOURCE_EXTENSIONS:
                    # Also check package manifests
                    if name not in ('package.json', 'go.mod', 'requirements.txt',
                                    'pyproject.toml', 'Gemfile', 'Cargo.toml'):
                        continue

                try:
                    content = fp.read_text(encoding='utf-8')
                except (OSError, UnicodeDecodeError):
                    continue

                self._scan_cors(content, str(fp), result)
                self._scan_rate_limiting(content, str(fp), result)
                self._scan_validation(content, result, ext)

                # GAP-C4: Skip example/docs files for auth and secret scanning
                # to avoid false positives from tutorial/sample code
                if not in_example_dir:
                    self._scan_auth(content, str(fp), auth_evidence)
                    self._scan_authz(content, str(fp), result)
                    self._scan_flags(content, str(fp), result)

        # Build auth mechanisms
        for auth_type, files_list in auth_evidence.items():
            result.auth_mechanisms.append(AuthMechanism(
                auth_type=auth_type,
                evidence=files_list,
            ))

        return result if (result.auth_mechanisms or result.authz_patterns or
                          result.cors_config or result.rate_limiting or
                          result.flags) else None

    def _scan_auth(self, content: str, file_path: str, evidence: Dict[str, List[str]]) -> None:
        """Detect authentication mechanisms."""
        for auth_type, patterns in AUTH_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(content):
                    if auth_type not in evidence:
                        evidence[auth_type] = []
                    if file_path not in evidence[auth_type]:
                        evidence[auth_type].append(file_path)
                    break

    def _scan_authz(self, content: str, file_path: str, result: SecurityResult) -> None:
        """Detect authorization patterns."""
        for pattern, pattern_type in AUTHZ_PATTERNS:
            for m in pattern.finditer(content):
                name = m.group(1) if m.lastindex else None
                result.authz_patterns.append(AuthzPattern(
                    pattern_type=pattern_type,
                    name=name,
                    source_file=file_path,
                ))

    def _scan_cors(self, content: str, file_path: str, result: SecurityResult) -> None:
        """Detect CORS configuration."""
        for pattern in CORS_PATTERNS:
            if pattern.search(content):
                if result.cors_config is None:
                    result.cors_config = {"detected": True, "files": []}
                if file_path not in result.cors_config.get("files", []):
                    result.cors_config.setdefault("files", []).append(file_path)

                # Try to extract origins
                origins_match = re.search(
                    r'(?:AllowOrigins|CORS_ALLOWED_ORIGINS|origins)\s*[:=]\s*\[([^\]]+)\]',
                    content, re.I
                )
                if origins_match:
                    origins_str = origins_match.group(1)
                    origins = re.findall(r'["\']([^"\']+)["\']', origins_str)
                    result.cors_config["origins"] = origins

    def _scan_rate_limiting(self, content: str, file_path: str, result: SecurityResult) -> None:
        """Detect rate limiting."""
        for pattern in RATE_LIMIT_PATTERNS:
            if pattern.search(content):
                result.rate_limiting = True
                result.rate_limit_details = file_path
                return

    def _scan_validation(self, content: str, result: SecurityResult, file_ext: str = '') -> None:
        """Detect input validation libraries, gated by file language."""
        for lib_name, pattern, allowed_exts in VALIDATION_LIBS:
            # Language-gate: skip if file extension doesn't match library's language
            if file_ext and allowed_exts and file_ext.lower() not in allowed_exts:
                continue
            if pattern.search(content) and lib_name not in result.input_validation:
                result.input_validation.append(lib_name)

    def _scan_flags(self, content: str, file_path: str, result: SecurityResult) -> None:
        """Detect potential security concerns."""
        # Skip test files
        if '/test' in file_path.lower() or '_test.' in file_path.lower() or 'spec.' in file_path.lower():
            return

        # Reduce severity for sample/example env files (GAP-C9)
        file_lower = file_path.lower()
        is_sample = any(tag in file_lower for tag in (
            '.sample', '.example', '.template', '.env.local',
            'docs_src/', 'examples/', 'tutorials/',
        ))

        for pattern, category in SECRET_PATTERNS:
            for i, line in enumerate(content.splitlines(), 1):
                if pattern.search(line):
                    # Skip if it's a comment or env var reference
                    stripped = line.strip()
                    if stripped.startswith(('#', '//', '/*', '*', '--')):
                        continue
                    if 'os.Getenv' in line or 'process.env' in line or 'os.environ' in line:
                        continue

                    severity = 'low' if is_sample else 'high'
                    result.flags.append(SecurityFlag(
                        severity=severity,
                        category=category,
                        message=f"Potential {category.replace('_', ' ')} detected",
                        file_path=file_path,
                        line_number=i,
                    ))
                    break  # One flag per file per pattern


# =============================================================================
# Compatibility helper
# =============================================================================

def _walk_compat(root: Path):
    """os.walk wrapper that yields (Path, dirs, files)."""
    import os
    for dirpath, dirs, files in os.walk(root):
        yield Path(dirpath), dirs, files
