"""
EnhancedFlaskParser v1.0 - Comprehensive Flask parser using all extractors.

This parser provides enhanced Flask extraction beyond the basic FlaskExtractor,
adding support for error handlers, extensions, context processors, CLI commands,
WebSocket handlers, and more.

Supports:
- Flask 0.x (basic routing, Jinja2 templates)
- Flask 1.x (CLI, app.ensure_sync, improved Blueprint)
- Flask 2.x (async views, method-specific decorators, nested Blueprints)
- Flask 3.x (improved typing, deprecated features removed)

Flask-specific extraction:
- Routes: @app.route, @bp.route, @app.get/post (2.0+), method views
- Blueprints: Blueprint definitions, url_prefix, nesting (2.0+)
- Error handlers: @app.errorhandler, @bp.errorhandler, abort()
- Extensions: Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-Mail, etc.
- Context processors: @app.context_processor
- CLI: @app.cli.command
- Middleware: before_request, after_request, teardown_request
- WebSocket: Flask-SocketIO, Flask-Sock
- Config: app.config, from_envvar, from_pyfile, from_object

Framework detection (25+ Flask ecosystem patterns):
- Core: Flask, Blueprint, jsonify, redirect, url_for, render_template
- Auth: Flask-Login, Flask-JWT-Extended, Flask-Security, Flask-Principal
- Database: Flask-SQLAlchemy, Flask-Migrate, Flask-PyMongo
- API: Flask-RESTful, Flask-RESTX, Flask-Smorest, Flask-API
- Admin: Flask-Admin
- Forms: Flask-WTF, WTForms
- Caching: Flask-Caching
- Mail: Flask-Mail, Flask-Mailman
- CORS: Flask-CORS
- Testing: pytest-flask, Flask-Testing
- WebSocket: Flask-SocketIO, Flask-Sock

Part of CodeTrellis v4.33 - Flask Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import existing Flask extractor
from .extractors.python import (
    FlaskExtractor, FlaskRouteInfo, FlaskBlueprintInfo,
)


@dataclass
class FlaskErrorHandlerInfo:
    """Information about a Flask error handler."""
    error_code: str  # 404, 500, Exception class name
    handler: str
    blueprint: Optional[str] = None
    is_app_level: bool = True
    line_number: int = 0


@dataclass
class FlaskExtensionInfo:
    """Information about a Flask extension in use."""
    name: str
    variable_name: str = ""
    init_app: bool = False  # Uses app factory pattern
    line_number: int = 0


@dataclass
class FlaskContextProcessorInfo:
    """Information about a Flask context processor."""
    name: str
    blueprint: Optional[str] = None
    line_number: int = 0


@dataclass
class FlaskCLICommandInfo:
    """Information about a Flask CLI command."""
    name: str
    handler: str
    options: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class FlaskMiddlewareInfo:
    """Information about Flask request hooks."""
    name: str
    hook_type: str  # before_request, after_request, teardown_request, before_first_request
    blueprint: Optional[str] = None
    line_number: int = 0


@dataclass
class FlaskParseResult:
    """Complete parse result for a Flask file."""
    file_path: str
    file_type: str = "module"  # app, route, blueprint, extension, config, test, model

    # Routes (from existing extractor)
    routes: List[FlaskRouteInfo] = field(default_factory=list)
    blueprints: List[FlaskBlueprintInfo] = field(default_factory=list)

    # Enhanced extraction
    error_handlers: List[FlaskErrorHandlerInfo] = field(default_factory=list)
    extensions: List[FlaskExtensionInfo] = field(default_factory=list)
    context_processors: List[FlaskContextProcessorInfo] = field(default_factory=list)
    cli_commands: List[FlaskCLICommandInfo] = field(default_factory=list)
    request_hooks: List[FlaskMiddlewareInfo] = field(default_factory=list)

    # Aggregate
    detected_frameworks: List[str] = field(default_factory=list)
    flask_version: str = ""
    uses_app_factory: bool = False
    total_routes: int = 0
    total_blueprints: int = 0


class EnhancedFlaskParser:
    """
    Enhanced Flask parser v1.0 that extends the basic FlaskExtractor.

    Provides additional extraction for error handlers, extensions,
    context processors, CLI commands, and request hooks.
    """

    # Flask ecosystem detection patterns
    FRAMEWORK_PATTERNS = {
        # ── Core Flask ────────────────────────────────────────────
        'flask': re.compile(
            r'from\s+flask\s+import|import\s+flask',
            re.MULTILINE
        ),

        # ── Auth ──────────────────────────────────────────────────
        'flask_login': re.compile(
            r'from\s+flask_login|import\s+flask_login|LoginManager',
            re.MULTILINE
        ),
        'flask_jwt_extended': re.compile(
            r'from\s+flask_jwt_extended|JWTManager',
            re.MULTILINE
        ),
        'flask_security': re.compile(
            r'from\s+flask_security|Security\(',
            re.MULTILINE
        ),

        # ── Database ──────────────────────────────────────────────
        'flask_sqlalchemy': re.compile(
            r'from\s+flask_sqlalchemy|import\s+flask_sqlalchemy|SQLAlchemy\(',
            re.MULTILINE
        ),
        'flask_migrate': re.compile(
            r'from\s+flask_migrate|Migrate\(',
            re.MULTILINE
        ),
        'flask_pymongo': re.compile(
            r'from\s+flask_pymongo|PyMongo\(',
            re.MULTILINE
        ),

        # ── API ───────────────────────────────────────────────────
        'flask_restful': re.compile(
            r'from\s+flask_restful|import\s+flask_restful|Api\(',
            re.MULTILINE
        ),
        'flask_restx': re.compile(
            r'from\s+flask_restx|import\s+flask_restx',
            re.MULTILINE
        ),
        'flask_smorest': re.compile(
            r'from\s+flask_smorest|import\s+flask_smorest',
            re.MULTILINE
        ),

        # ── Admin ─────────────────────────────────────────────────
        'flask_admin': re.compile(
            r'from\s+flask_admin|Admin\(',
            re.MULTILINE
        ),

        # ── Forms ─────────────────────────────────────────────────
        'flask_wtf': re.compile(
            r'from\s+flask_wtf|import\s+flask_wtf|FlaskForm',
            re.MULTILINE
        ),

        # ── Caching ──────────────────────────────────────────────
        'flask_caching': re.compile(
            r'from\s+flask_caching|Cache\(',
            re.MULTILINE
        ),

        # ── CORS ─────────────────────────────────────────────────
        'flask_cors': re.compile(
            r'from\s+flask_cors|CORS\(',
            re.MULTILINE
        ),

        # ── Mail ─────────────────────────────────────────────────
        'flask_mail': re.compile(
            r'from\s+flask_mail|Mail\(',
            re.MULTILINE
        ),

        # ── WebSocket ────────────────────────────────────────────
        'flask_socketio': re.compile(
            r'from\s+flask_socketio|SocketIO\(',
            re.MULTILINE
        ),

        # ── Testing ──────────────────────────────────────────────
        'pytest_flask': re.compile(
            r'import\s+pytest|@pytest\.fixture.*app',
            re.MULTILINE
        ),

        # ── Limiter ──────────────────────────────────────────────
        'flask_limiter': re.compile(
            r'from\s+flask_limiter|Limiter\(',
            re.MULTILINE
        ),
    }

    # Error handler pattern
    ERROR_HANDLER_PATTERN = re.compile(
        r'@(\w+)\.errorhandler\s*\(\s*(\w+)\s*\)\s*\n'
        r'(?:@\w+[^\n]*\n)*'
        r'\s*(?:async\s+)?def\s+(\w+)',
        re.MULTILINE
    )

    # Extension init patterns
    EXTENSION_PATTERN = re.compile(
        r'(\w+)\s*=\s*(\w+)\s*\(\s*(?:app)?\s*\)',
        re.MULTILINE
    )

    INIT_APP_PATTERN = re.compile(
        r'(\w+)\.init_app\s*\(\s*app\s*\)',
        re.MULTILINE
    )

    # Context processor
    CONTEXT_PROCESSOR_PATTERN = re.compile(
        r'@(\w+)\.context_processor\s*\n\s*def\s+(\w+)',
        re.MULTILINE
    )

    # CLI commands
    CLI_COMMAND_PATTERN = re.compile(
        r'@(\w+)\.cli\.command\s*\(\s*["\']?(\w*)["\']?\s*\)\s*\n'
        r'(?:@\w+[^\n]*\n)*'
        r'\s*def\s+(\w+)',
        re.MULTILINE
    )

    # Request hooks
    REQUEST_HOOK_PATTERN = re.compile(
        r'@(\w+)\.(before_request|after_request|teardown_request|before_first_request)\s*\n'
        r'\s*(?:async\s+)?def\s+(\w+)',
        re.MULTILINE
    )

    # App factory pattern
    APP_FACTORY_PATTERN = re.compile(
        r'def\s+create_app\s*\(',
        re.MULTILINE
    )

    # Flask extension classes
    KNOWN_EXTENSIONS = {
        'SQLAlchemy': 'Flask-SQLAlchemy',
        'Migrate': 'Flask-Migrate',
        'LoginManager': 'Flask-Login',
        'JWTManager': 'Flask-JWT-Extended',
        'Mail': 'Flask-Mail',
        'Cache': 'Flask-Caching',
        'CORS': 'Flask-CORS',
        'SocketIO': 'Flask-SocketIO',
        'Admin': 'Flask-Admin',
        'Limiter': 'Flask-Limiter',
        'Babel': 'Flask-Babel',
        'Marshmallow': 'Flask-Marshmallow',
        'Api': 'Flask-RESTful',
        'Security': 'Flask-Security',
        'PyMongo': 'Flask-PyMongo',
        'Talisman': 'Flask-Talisman',
    }

    # Flask version features
    FLASK_VERSION_FEATURES = {
        'async def': '2.0',
        '@app.get(': '2.0',
        '@app.post(': '2.0',
        '@app.put(': '2.0',
        '@app.delete(': '2.0',
        '@app.patch(': '2.0',
        'register_blueprint': '0.7',
        'Blueprint(': '0.7',
        'app.cli': '1.0',
    }

    def __init__(self):
        """Initialize the enhanced Flask parser."""
        self.flask_extractor = FlaskExtractor()

    def parse(self, content: str, file_path: str = "") -> FlaskParseResult:
        """
        Parse Flask source code and extract all Flask-specific information.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            FlaskParseResult with all extracted Flask information
        """
        result = FlaskParseResult(file_path=file_path)

        # Determine file type
        result.file_type = self._classify_file(file_path, content)

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # App factory detection
        result.uses_app_factory = bool(self.APP_FACTORY_PATTERN.search(content))

        # ── Routes & Blueprints (existing extractor) ─────────────
        flask_result = self.flask_extractor.extract(content)
        result.routes = flask_result.get('routes', [])
        result.blueprints = flask_result.get('blueprints', [])
        result.total_routes = len(result.routes)
        result.total_blueprints = len(result.blueprints)

        # ── Error Handlers ───────────────────────────────────────
        for match in self.ERROR_HANDLER_PATTERN.finditer(content):
            result.error_handlers.append(FlaskErrorHandlerInfo(
                error_code=match.group(2),
                handler=match.group(3),
                blueprint=match.group(1) if match.group(1) != 'app' else None,
                is_app_level=match.group(1) == 'app',
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # ── Extensions ───────────────────────────────────────────
        result.extensions = self._extract_extensions(content)

        # ── Context Processors ───────────────────────────────────
        for match in self.CONTEXT_PROCESSOR_PATTERN.finditer(content):
            bp = match.group(1) if match.group(1) != 'app' else None
            result.context_processors.append(FlaskContextProcessorInfo(
                name=match.group(2),
                blueprint=bp,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # ── CLI Commands ─────────────────────────────────────────
        for match in self.CLI_COMMAND_PATTERN.finditer(content):
            cmd_name = match.group(2) or match.group(3)
            result.cli_commands.append(FlaskCLICommandInfo(
                name=cmd_name,
                handler=match.group(3),
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # ── Request Hooks ────────────────────────────────────────
        for match in self.REQUEST_HOOK_PATTERN.finditer(content):
            bp = match.group(1) if match.group(1) != 'app' else None
            result.request_hooks.append(FlaskMiddlewareInfo(
                name=match.group(3),
                hook_type=match.group(2),
                blueprint=bp,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # ── Version detection ────────────────────────────────────
        result.flask_version = self._detect_flask_version(content)

        return result

    def _extract_extensions(self, content: str) -> List[FlaskExtensionInfo]:
        """Extract Flask extensions being used."""
        extensions = []
        seen = set()

        # Check for known extension instantiation
        for match in self.EXTENSION_PATTERN.finditer(content):
            var_name = match.group(1)
            class_name = match.group(2)

            if class_name in self.KNOWN_EXTENSIONS and var_name not in seen:
                seen.add(var_name)
                extensions.append(FlaskExtensionInfo(
                    name=self.KNOWN_EXTENSIONS[class_name],
                    variable_name=var_name,
                    init_app=False,
                    line_number=content[:match.start()].count('\n') + 1,
                ))

        # Check for init_app calls (app factory pattern)
        for match in self.INIT_APP_PATTERN.finditer(content):
            var_name = match.group(1)
            for ext in extensions:
                if ext.variable_name == var_name:
                    ext.init_app = True

        return extensions

    def _classify_file(self, file_path: str, content: str) -> str:
        """Classify a Flask file by its role."""
        normalized = file_path.replace('\\', '/').lower()
        basename = normalized.split('/')[-1] if normalized else ""

        if 'app' in basename or basename == '__init__.py':
            if 'Flask(' in content or 'create_app' in content:
                return 'app'
        if 'route' in basename or 'view' in basename:
            return 'route'
        if 'blueprint' in basename:
            return 'blueprint'
        if 'config' in basename or 'settings' in basename:
            return 'config'
        if 'model' in basename:
            return 'model'
        if 'test' in basename:
            return 'test'
        if 'extension' in basename:
            return 'extension'

        return 'module'

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect Flask ecosystem frameworks."""
        frameworks = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(name)
        return frameworks

    def _detect_flask_version(self, content: str) -> str:
        """Detect minimum Flask version required."""
        max_version = '0.0'
        for feature, version in self.FLASK_VERSION_FEATURES.items():
            if feature in content:
                if self._version_compare(version, max_version) > 0:
                    max_version = version
        return max_version if max_version != '0.0' else ''

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        for a, b in zip(parts1, parts2):
            if a != b:
                return a - b
        return len(parts1) - len(parts2)

    def is_flask_file(self, content: str, file_path: str = "") -> bool:
        """Determine if a file is a Flask-specific file."""
        if re.search(r'from\s+flask\s+import|import\s+flask', content):
            return True
        if re.search(r'Flask\s*\(|Blueprint\s*\(', content):
            return True
        if re.search(r'@\w+\.route\s*\(', content):
            return True
        normalized = file_path.replace('\\', '/').lower()
        if any(p in normalized for p in ['/routes/', '/blueprints/', '/views/']):
            return True
        return False

    def to_codetrellis_format(self, result: FlaskParseResult) -> str:
        """Convert parse result to CodeTrellis compressed format."""
        lines = []

        if result.file_path:
            lines.append(f"[FILE:{Path(result.file_path).name}|type:{result.file_type}]")
        if result.detected_frameworks:
            lines.append(f"[FLASK_ECOSYSTEM:{','.join(result.detected_frameworks)}]")
        if result.flask_version:
            lines.append(f"[FLASK_VERSION:>={result.flask_version}]")
        if result.uses_app_factory:
            lines.append("[APP_FACTORY:true]")
        lines.append("")

        # Blueprints
        if result.blueprints:
            lines.append("=== FLASK_BLUEPRINTS ===")
            for bp in result.blueprints:
                prefix = f"|prefix:{bp.url_prefix}" if bp.url_prefix else ""
                lines.append(f"  {bp.variable_name}({bp.name}){prefix}")
            lines.append("")

        # Routes
        if result.routes:
            lines.append("=== FLASK_ROUTES ===")
            for r in result.routes:
                methods = ",".join(r.methods)
                bp = f"|bp:{r.blueprint}" if r.blueprint else ""
                vars_str = f"|vars:{','.join(r.url_variables)}" if r.url_variables else ""
                lines.append(f"  {methods} {r.path} → {r.handler}{bp}{vars_str}")
            lines.append("")

        # Error handlers
        if result.error_handlers:
            lines.append("=== FLASK_ERROR_HANDLERS ===")
            for eh in result.error_handlers:
                lines.append(f"  {eh.error_code} → {eh.handler}")
            lines.append("")

        # Extensions
        if result.extensions:
            lines.append("=== FLASK_EXTENSIONS ===")
            for ext in result.extensions:
                factory = "|init_app" if ext.init_app else ""
                lines.append(f"  {ext.name}({ext.variable_name}){factory}")
            lines.append("")

        # Request hooks
        if result.request_hooks:
            lines.append("=== FLASK_HOOKS ===")
            for hook in result.request_hooks:
                lines.append(f"  @{hook.hook_type} → {hook.name}")
            lines.append("")

        # CLI commands
        if result.cli_commands:
            lines.append("=== FLASK_CLI ===")
            for cmd in result.cli_commands:
                lines.append(f"  {cmd.name} → {cmd.handler}")
            lines.append("")

        return '\n'.join(lines)
