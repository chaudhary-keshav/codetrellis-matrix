"""
Enhanced Laravel Framework Parser for CodeTrellis.

v5.3: Full Laravel framework support (5.x through 11.x).
Extracts Eloquent models, Blade templates, Artisan commands, middleware,
routes, service providers, facades, migrations, policies, events, observers,
notifications, jobs, mail, form requests, resources, seeders, factories.

Runs AFTER the base PHP parser when Laravel framework is detected.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


# ===== DATACLASSES =====

@dataclass
class LaravelRouteInfo:
    """Information about a Laravel route."""
    method: str  # GET, POST, PUT, PATCH, DELETE, ANY, resource, apiResource
    path: str
    controller: str = ""
    action: str = ""
    name: str = ""
    middleware: List[str] = field(default_factory=list)
    prefix: str = ""
    namespace: str = ""
    is_api: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class LaravelControllerInfo:
    """Information about a Laravel controller."""
    name: str
    parent_class: str = ""
    actions: List[str] = field(default_factory=list)
    middleware: List[str] = field(default_factory=list)
    is_resource: bool = False
    is_api_resource: bool = False
    is_invokable: bool = False
    form_requests: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class LaravelModelInfo:
    """Information about a Laravel Eloquent model."""
    name: str
    table_name: str = ""
    parent_class: str = ""
    fillable: List[str] = field(default_factory=list)
    guarded: List[str] = field(default_factory=list)
    hidden: List[str] = field(default_factory=list)
    casts: Dict[str, str] = field(default_factory=dict)
    relationships: List[Dict[str, str]] = field(default_factory=list)
    scopes: List[str] = field(default_factory=list)
    accessors: List[str] = field(default_factory=list)
    mutators: List[str] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)
    uses_soft_deletes: bool = False
    uses_uuid: bool = False
    uses_factory: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class LaravelMigrationInfo:
    """Information about a Laravel migration."""
    name: str
    tables_created: List[str] = field(default_factory=list)
    tables_modified: List[str] = field(default_factory=list)
    columns: List[Dict[str, str]] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)
    foreign_keys: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class LaravelMiddlewareInfo:
    """Information about a Laravel middleware."""
    name: str
    class_name: str = ""
    is_global: bool = False
    is_group: bool = False
    group_name: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class LaravelServiceProviderInfo:
    """Information about a Laravel service provider."""
    name: str
    bindings: List[Dict[str, str]] = field(default_factory=list)
    singletons: List[str] = field(default_factory=list)
    deferred: bool = False
    provides: List[str] = field(default_factory=list)
    events: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class LaravelJobInfo:
    """Information about a Laravel job."""
    name: str
    queue: str = ""
    connection: str = ""
    tries: int = 0
    timeout: int = 0
    is_unique: bool = False
    traits: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class LaravelEventInfo:
    """Information about a Laravel event."""
    name: str
    listeners: List[str] = field(default_factory=list)
    is_broadcastable: bool = False
    channel: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class LaravelNotificationInfo:
    """Information about a Laravel notification."""
    name: str
    channels: List[str] = field(default_factory=list)
    is_queued: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class LaravelMailInfo:
    """Information about a Laravel mailable."""
    name: str
    subject: str = ""
    view: str = ""
    is_queued: bool = False
    is_markdown: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class LaravelPolicyInfo:
    """Information about a Laravel policy."""
    name: str
    model: str = ""
    methods: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class LaravelCommandInfo:
    """Information about a Laravel Artisan command."""
    name: str
    signature: str = ""
    description: str = ""
    schedule: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class LaravelObserverInfo:
    """Information about a Laravel observer."""
    name: str
    model: str = ""
    events: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class LaravelFormRequestInfo:
    """Information about a Laravel form request."""
    name: str
    rules: List[str] = field(default_factory=list)
    authorize: bool = True
    file: str = ""
    line_number: int = 0


@dataclass
class LaravelResourceInfo:
    """Information about a Laravel API resource."""
    name: str
    model: str = ""
    is_collection: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class LaravelBladeInfo:
    """Information about a Blade template component."""
    name: str
    kind: str = ""  # component, directive, layout, partial
    slots: List[str] = field(default_factory=list)
    props: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class LaravelConfigInfo:
    """Information about Laravel configuration."""
    key: str
    value: str = ""
    environment: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class LaravelParseResult:
    """Complete parse result for a Laravel file."""
    file_path: str
    file_type: str = "php"

    # Routes
    routes: List[LaravelRouteInfo] = field(default_factory=list)

    # Controllers
    controllers: List[LaravelControllerInfo] = field(default_factory=list)

    # Models
    models: List[LaravelModelInfo] = field(default_factory=list)
    migrations: List[LaravelMigrationInfo] = field(default_factory=list)

    # Middleware
    middleware: List[LaravelMiddlewareInfo] = field(default_factory=list)

    # Service Providers
    service_providers: List[LaravelServiceProviderInfo] = field(default_factory=list)

    # Jobs
    jobs: List[LaravelJobInfo] = field(default_factory=list)

    # Events
    events: List[LaravelEventInfo] = field(default_factory=list)

    # Notifications
    notifications: List[LaravelNotificationInfo] = field(default_factory=list)

    # Mail
    mailables: List[LaravelMailInfo] = field(default_factory=list)

    # Policies
    policies: List[LaravelPolicyInfo] = field(default_factory=list)

    # Commands
    commands: List[LaravelCommandInfo] = field(default_factory=list)

    # Observers
    observers: List[LaravelObserverInfo] = field(default_factory=list)

    # Form Requests
    form_requests: List[LaravelFormRequestInfo] = field(default_factory=list)

    # API Resources
    resources: List[LaravelResourceInfo] = field(default_factory=list)

    # Blade components
    blade_components: List[LaravelBladeInfo] = field(default_factory=list)

    # Configuration
    configs: List[LaravelConfigInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    laravel_version: str = ""
    is_api_only: bool = False
    has_livewire: bool = False
    has_inertia: bool = False
    has_jetstream: bool = False
    has_breeze: bool = False
    has_nova: bool = False
    has_horizon: bool = False
    has_telescope: bool = False
    has_sanctum: bool = False
    has_passport: bool = False


# ===== PARSER =====

class EnhancedLaravelParser:
    """
    Enhanced parser for Laravel framework (5.x through 11.x).
    Extracts routes, controllers, models, migrations, middleware,
    service providers, jobs, events, notifications, mail, policies,
    commands, observers, form requests, API resources, Blade components.
    """

    # Detection pattern - must match to proceed with parsing
    LARAVEL_DETECT = re.compile(
        r"(?:Illuminate\\|Laravel\\|Artisan|Eloquent|"
        r"Route::|Auth::|app\(\)|config\(\)|env\(\)|"
        r"use\s+App\\|namespace\s+App\\|"
        r"extends\s+(?:Controller|Model|FormRequest|Mailable|"
        r"Notification|Job|Event|Policy|Command|"
        r"ServiceProvider|Middleware|Resource|"
        r"JsonResource|ResourceCollection)|"
        r"class\s+\w+\s+extends\s+Migration)",
        re.MULTILINE,
    )

    # Framework ecosystem patterns
    FRAMEWORK_PATTERNS = {
        'laravel': re.compile(r'(?:Illuminate\\|Laravel\\|Artisan)'),
        'livewire': re.compile(r'(?:Livewire\\|LivewireComponent|wire:model|wire:click)'),
        'inertia': re.compile(r'(?:Inertia\\|Inertia::render|inertia\()'),
        'jetstream': re.compile(r'(?:Jetstream\\|Laravel\\Fortify)'),
        'breeze': re.compile(r'(?:laravel/breeze)'),
        'nova': re.compile(r'(?:Laravel\\Nova|Nova::)'),
        'horizon': re.compile(r'(?:Laravel\\Horizon|Horizon::)'),
        'telescope': re.compile(r'(?:Laravel\\Telescope)'),
        'sanctum': re.compile(r'(?:Laravel\\Sanctum|HasApiTokens)'),
        'passport': re.compile(r'(?:Laravel\\Passport)'),
        'socialite': re.compile(r'(?:Laravel\\Socialite|Socialite::)'),
        'cashier': re.compile(r'(?:Laravel\\Cashier|Billable)'),
        'scout': re.compile(r'(?:Laravel\\Scout|Searchable)'),
        'octane': re.compile(r'(?:Laravel\\Octane)'),
        'vapor': re.compile(r'(?:Laravel\\Vapor)'),
        'pennant': re.compile(r'(?:Laravel\\Pennant|Feature::)'),
        'pulse': re.compile(r'(?:Laravel\\Pulse)'),
        'reverb': re.compile(r'(?:Laravel\\Reverb)'),
        'folio': re.compile(r'(?:Laravel\\Folio)'),
        'volt': re.compile(r'(?:Laravel\\Volt|Volt::)'),
        'filament': re.compile(r'(?:Filament\\|FilamentResource)'),
        'spatie': re.compile(r'(?:Spatie\\)'),
    }

    # Route patterns
    ROUTE_PATTERN = re.compile(
        r"Route::(get|post|put|patch|delete|any|options|match|resource|apiResource)\s*\(\s*"
        r"['\"]([^'\"]+)['\"]"
        r"(?:\s*,\s*(?:\[([^\]]*)\]|['\"]?([^'\")\s,]+)['\"]?))?",
        re.MULTILINE,
    )
    ROUTE_NAME = re.compile(r"->name\s*\(\s*['\"]([^'\"]+)['\"]")
    ROUTE_MIDDLEWARE = re.compile(r"->middleware\s*\(\s*(?:\[([^\]]*)\]|['\"]([^'\"]+)['\"])")
    ROUTE_PREFIX = re.compile(r"Route::prefix\s*\(\s*['\"]([^'\"]+)['\"]")
    ROUTE_GROUP = re.compile(r"Route::group\s*\(\s*\[([^\]]*)\]")

    # Controller pattern
    CONTROLLER_PATTERN = re.compile(
        r"class\s+(\w+Controller)\s+extends\s+(\w+)",
        re.MULTILINE,
    )
    CONTROLLER_MIDDLEWARE = re.compile(
        r"\$this->middleware\s*\(\s*(?:\[([^\]]*)\]|['\"]([^'\"]+)['\"])",
    )
    CONTROLLER_ACTION = re.compile(
        r"public\s+function\s+(\w+)\s*\(",
    )

    # Model patterns
    MODEL_PATTERN = re.compile(
        r"class\s+(\w+)\s+extends\s+(?:Model|Eloquent|Authenticatable|Pivot)",
        re.MULTILINE,
    )
    FILLABLE = re.compile(
        r"(?:protected|public)\s+\$fillable\s*=\s*\[([^\]]*)\]",
        re.DOTALL,
    )
    GUARDED = re.compile(
        r"(?:protected|public)\s+\$guarded\s*=\s*\[([^\]]*)\]",
        re.DOTALL,
    )
    HIDDEN = re.compile(
        r"(?:protected|public)\s+\$hidden\s*=\s*\[([^\]]*)\]",
        re.DOTALL,
    )
    CASTS = re.compile(
        r"(?:protected|public)\s+\$casts\s*=\s*\[([^\]]*)\]",
        re.DOTALL,
    )
    TABLE_NAME = re.compile(
        r"(?:protected|public)\s+\$table\s*=\s*['\"](\w+)['\"]",
    )
    RELATIONSHIP = re.compile(
        r"(?:return\s+\$this->)?(hasOne|hasMany|belongsTo|belongsToMany|"
        r"morphOne|morphMany|morphTo|morphToMany|morphedByMany|"
        r"hasManyThrough|hasOneThrough)\s*\(\s*"
        r"(?:\\?(\w+(?:\\\w+)*)::class|['\"]([^'\"]+)['\"])",
        re.MULTILINE,
    )
    SCOPE = re.compile(
        r"public\s+function\s+scope(\w+)\s*\(",
    )
    ACCESSOR = re.compile(
        r"(?:public\s+function\s+get(\w+)Attribute\s*\(|"
        r"protected\s+function\s+(\w+)\s*\(\)\s*:\s*Attribute)",
    )
    MUTATOR = re.compile(
        r"public\s+function\s+set(\w+)Attribute\s*\(",
    )

    # Migration patterns
    MIGRATION_PATTERN = re.compile(
        r"class\s+(\w+)\s+extends\s+Migration",
        re.MULTILINE,
    )
    CREATE_TABLE = re.compile(
        r"Schema::create\s*\(\s*['\"](\w+)['\"]",
    )
    ALTER_TABLE = re.compile(
        r"Schema::table\s*\(\s*['\"](\w+)['\"]",
    )
    COLUMN_DEF = re.compile(
        r"\$table->(string|integer|bigInteger|boolean|text|longText|"
        r"timestamp|date|datetime|decimal|float|double|binary|json|"
        r"jsonb|uuid|foreignId|unsignedBigInteger|enum|char|"
        r"tinyInteger|smallInteger|mediumInteger|mediumText|"
        r"foreignUuid|ulid|foreignUlid|id|timestamps|softDeletes|"
        r"rememberToken|morphs|nullableMorphs)\s*\(\s*(?:['\"](\w+)['\"])?",
    )
    INDEX_DEF = re.compile(
        r"\$table->(index|unique|primary|fullText|spatialIndex)\s*\(",
    )
    FOREIGN_KEY = re.compile(
        r"\$table->foreign(?:Id)?\s*\(\s*['\"](\w+)['\"]",
    )

    # Middleware patterns
    MIDDLEWARE_CLASS = re.compile(
        r"class\s+(\w+(?:Middleware)?)\s+(?:extends\s+\w+\s+)?(?:implements\s+\w+)?\s*\{",
        re.MULTILINE,
    )
    MIDDLEWARE_HANDLE = re.compile(
        r"public\s+function\s+handle\s*\(\s*(?:\$request|Request\s+\$request)",
    )

    # Service Provider patterns
    PROVIDER_PATTERN = re.compile(
        r"class\s+(\w+ServiceProvider)\s+extends\s+ServiceProvider",
        re.MULTILINE,
    )
    BIND_PATTERN = re.compile(
        r"\$this->app->(?:bind|singleton|instance)\s*\(\s*"
        r"(?:(\w+(?:\\\w+)*)::class|['\"]([^'\"]+)['\"])",
    )

    # Job patterns
    JOB_PATTERN = re.compile(
        r"class\s+(\w+)\s+(?:extends\s+\w+\s+)?implements\s+ShouldQueue|"
        r"class\s+(\w+Job)\s+extends\s+\w+",
        re.MULTILINE,
    )
    JOB_QUEUE = re.compile(r"(?:public|protected)\s+\$queue\s*=\s*['\"](\w+)['\"]")
    JOB_TRIES = re.compile(r"(?:public|protected)\s+\$tries\s*=\s*(\d+)")
    JOB_TIMEOUT = re.compile(r"(?:public|protected)\s+\$timeout\s*=\s*(\d+)")

    # Event patterns
    EVENT_PATTERN = re.compile(
        r"class\s+(\w+(?:Event)?)\s+(?:extends\s+\w+\s+)?(?:implements\s+ShouldBroadcast)?",
        re.MULTILINE,
    )
    EVENT_CHANNEL = re.compile(
        r"public\s+function\s+broadcastOn\s*\([^)]*\).*?"
        r"(?:Channel|PrivateChannel|PresenceChannel)\s*\(\s*['\"]([^'\"]+)['\"]",
        re.DOTALL,
    )

    # Notification patterns
    NOTIFICATION_PATTERN = re.compile(
        r"class\s+(\w+)\s+extends\s+Notification",
        re.MULTILINE,
    )
    NOTIFICATION_VIA = re.compile(
        r"public\s+function\s+via\s*\([^)]*\).*?return\s+\[([^\]]*)\]",
        re.DOTALL,
    )

    # Mail patterns
    MAIL_PATTERN = re.compile(
        r"class\s+(\w+)\s+extends\s+Mailable",
        re.MULTILINE,
    )
    MAIL_SUBJECT = re.compile(
        r"->subject\s*\(\s*['\"]([^'\"]+)['\"]",
    )
    MAIL_VIEW = re.compile(
        r"->(?:view|markdown)\s*\(\s*['\"]([^'\"]+)['\"]",
    )

    # Policy patterns
    POLICY_PATTERN = re.compile(
        r"class\s+(\w+Policy)\s+",
        re.MULTILINE,
    )
    POLICY_METHOD = re.compile(
        r"public\s+function\s+(viewAny|view|create|update|delete|restore|forceDelete|"
        r"\w+)\s*\(",
    )

    # Command patterns
    COMMAND_PATTERN = re.compile(
        r"class\s+(\w+)\s+extends\s+Command",
        re.MULTILINE,
    )
    COMMAND_SIGNATURE = re.compile(
        r"(?:protected|public)\s+\$signature\s*=\s*['\"]([^'\"]+)['\"]",
    )
    COMMAND_DESC = re.compile(
        r"(?:protected|public)\s+\$description\s*=\s*['\"]([^'\"]+)['\"]",
    )

    # Observer patterns
    OBSERVER_PATTERN = re.compile(
        r"class\s+(\w+Observer)\s+",
        re.MULTILINE,
    )
    OBSERVER_METHOD = re.compile(
        r"public\s+function\s+(creating|created|updating|updated|"
        r"saving|saved|deleting|deleted|restoring|restored|"
        r"retrieved|replicating|forceDeleting|forceDeleted)\s*\(",
    )

    # Form Request patterns
    FORM_REQUEST_PATTERN = re.compile(
        r"class\s+(\w+Request)\s+extends\s+FormRequest",
        re.MULTILINE,
    )
    FORM_RULES = re.compile(
        r"public\s+function\s+rules\s*\([^)]*\).*?return\s+\[([^\]]*(?:\[[^\]]*\][^\]]*)*)\]",
        re.DOTALL,
    )

    # Resource patterns
    RESOURCE_PATTERN = re.compile(
        r"class\s+(\w+(?:Resource|Collection))\s+extends\s+(?:JsonResource|ResourceCollection)",
        re.MULTILINE,
    )

    # Config patterns
    CONFIG_RETURN = re.compile(
        r"return\s+\[\s*(?:['\"](\w+)['\"])\s*=>",
    )
    ENV_CALL = re.compile(
        r"env\s*\(\s*['\"]([^'\"]+)['\"]",
    )

    # Version detection (from composer.json or code patterns)
    VERSION_PATTERNS = [
        (r'Laravel\\Reverb|Laravel\\Pulse|Laravel\\Pennant', '11.x'),
        (r'Laravel\\Folio|Laravel\\Volt', '10.x'),
        (r'Laravel\\Octane|Illuminate\\Support\\Enum', '9.x'),
        (r'Illuminate\\Database\\Eloquent\\Factories\\HasFactory', '8.x'),
        (r'Illuminate\\Contracts\\Queue\\ShouldBeUnique', '8.x'),
        (r'Illuminate\\Http\\Client', '7.x'),
        (r'Illuminate\\Support\\Facades\\Http', '7.x'),
        (r'Illuminate\\Foundation\\Auth\\Access\\AuthorizesRequests', '6.x'),
        (r'Illuminate\\Routing\\Controller', '5.x'),
    ]

    def parse(self, content: str, file_path: str = "") -> LaravelParseResult:
        """Parse PHP source code for Laravel-specific patterns."""
        result = LaravelParseResult(file_path=file_path)

        if not content.strip():
            return result

        # Check if this file uses Laravel
        if not self.LARAVEL_DETECT.search(content):
            return result

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect version
        result.laravel_version = self._detect_version(content)

        # Ecosystem detection
        result.has_livewire = bool(self.FRAMEWORK_PATTERNS['livewire'].search(content))
        result.has_inertia = bool(self.FRAMEWORK_PATTERNS['inertia'].search(content))
        result.has_jetstream = bool(self.FRAMEWORK_PATTERNS['jetstream'].search(content))
        result.has_breeze = bool(self.FRAMEWORK_PATTERNS['breeze'].search(content))
        result.has_nova = bool(self.FRAMEWORK_PATTERNS['nova'].search(content))
        result.has_horizon = bool(self.FRAMEWORK_PATTERNS['horizon'].search(content))
        result.has_telescope = bool(self.FRAMEWORK_PATTERNS['telescope'].search(content))
        result.has_sanctum = bool(self.FRAMEWORK_PATTERNS['sanctum'].search(content))
        result.has_passport = bool(self.FRAMEWORK_PATTERNS['passport'].search(content))

        # API-only detection
        result.is_api_only = bool(re.search(
            r"'api'\s*=>\s*\[|Route::prefix\s*\(\s*['\"]api['\"]|"
            r"return\s+.*JsonResource|apiResource",
            content,
        ))

        # Extract all entities
        self._extract_routes(content, file_path, result)
        self._extract_controllers(content, file_path, result)
        self._extract_models(content, file_path, result)
        self._extract_migrations(content, file_path, result)
        self._extract_middleware(content, file_path, result)
        self._extract_service_providers(content, file_path, result)
        self._extract_jobs(content, file_path, result)
        self._extract_events(content, file_path, result)
        self._extract_notifications(content, file_path, result)
        self._extract_mailables(content, file_path, result)
        self._extract_policies(content, file_path, result)
        self._extract_commands(content, file_path, result)
        self._extract_observers(content, file_path, result)
        self._extract_form_requests(content, file_path, result)
        self._extract_resources(content, file_path, result)
        self._extract_configs(content, file_path, result)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect Laravel ecosystem frameworks used."""
        detected = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """Detect Laravel version from code features."""
        for pattern, version in self.VERSION_PATTERNS:
            if re.search(pattern, content):
                return version
        return ""

    def _get_line(self, content: str, pos: int) -> int:
        """Get 1-based line number for a position."""
        return content[:pos].count('\n') + 1

    def _extract_routes(self, content: str, file_path: str, result: LaravelParseResult):
        """Extract Laravel route definitions."""
        for m in self.ROUTE_PATTERN.finditer(content):
            method = m.group(1).upper()
            path = m.group(2)
            handler = m.group(3) or m.group(4) or ""
            line = self._get_line(content, m.start())

            # Parse controller@action
            controller = ""
            action = ""
            if '@' in handler:
                parts = handler.split('@')
                controller = parts[0]
                action = parts[1] if len(parts) > 1 else ""
            elif '::class' in handler:
                controller = handler.replace('::class', '').strip()
            else:
                controller = handler

            # Check for route name
            name = ""
            rest = content[m.end():m.end() + 200]
            name_m = self.ROUTE_NAME.search(rest)
            if name_m:
                name = name_m.group(1)

            # Check for middleware
            middleware = []
            mw_m = self.ROUTE_MIDDLEWARE.search(rest)
            if mw_m:
                mw_str = mw_m.group(1) or mw_m.group(2)
                middleware = [s.strip().strip("'\"") for s in mw_str.split(',') if s.strip()]

            route = LaravelRouteInfo(
                method=method,
                path=path,
                controller=controller,
                action=action,
                name=name,
                middleware=middleware,
                is_api='/api/' in path or path.startswith('api/'),
                file=file_path,
                line_number=line,
            )
            result.routes.append(route)

    def _extract_controllers(self, content: str, file_path: str, result: LaravelParseResult):
        """Extract Laravel controller definitions."""
        for m in self.CONTROLLER_PATTERN.finditer(content):
            name = m.group(1)
            parent = m.group(2)
            line = self._get_line(content, m.start())

            # Extract actions (public methods)
            actions = [am.group(1) for am in self.CONTROLLER_ACTION.finditer(content)
                       if am.group(1) != '__construct']

            # Extract middleware
            middleware = []
            for mw_m in self.CONTROLLER_MIDDLEWARE.finditer(content):
                mw_str = mw_m.group(1) or mw_m.group(2)
                middleware.extend(s.strip().strip("'\"") for s in mw_str.split(',') if s.strip())

            # Check for invokable controller
            is_invokable = bool(re.search(r'public\s+function\s+__invoke\s*\(', content))

            # Check for resource/API resource
            is_resource = bool(re.search(
                r'(?:index|create|store|show|edit|update|destroy)',
                ' '.join(actions),
            ))

            ctrl = LaravelControllerInfo(
                name=name,
                parent_class=parent,
                actions=actions[:30],
                middleware=middleware[:10],
                is_resource=is_resource,
                is_invokable=is_invokable,
                file=file_path,
                line_number=line,
            )
            result.controllers.append(ctrl)

    def _extract_models(self, content: str, file_path: str, result: LaravelParseResult):
        """Extract Laravel Eloquent model definitions."""
        for m in self.MODEL_PATTERN.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())

            # Table name
            table = ""
            table_m = self.TABLE_NAME.search(content)
            if table_m:
                table = table_m.group(1)

            # Fillable
            fillable = []
            fill_m = self.FILLABLE.search(content)
            if fill_m:
                fillable = [s.strip().strip("'\"") for s in fill_m.group(1).split(',') if s.strip().strip("'\"")]

            # Guarded
            guarded = []
            guard_m = self.GUARDED.search(content)
            if guard_m:
                guarded = [s.strip().strip("'\"") for s in guard_m.group(1).split(',') if s.strip().strip("'\"")]

            # Hidden
            hidden = []
            hid_m = self.HIDDEN.search(content)
            if hid_m:
                hidden = [s.strip().strip("'\"") for s in hid_m.group(1).split(',') if s.strip().strip("'\"")]

            # Casts
            casts = {}
            cast_m = self.CASTS.search(content)
            if cast_m:
                for pair in re.finditer(r"['\"](\w+)['\"]\s*=>\s*['\"]?(\w+)['\"]?", cast_m.group(1)):
                    casts[pair.group(1)] = pair.group(2)

            # Relationships
            relationships = []
            for rel_m in self.RELATIONSHIP.finditer(content):
                rel_type = rel_m.group(1)
                related = rel_m.group(2) or rel_m.group(3)
                if related:
                    related = related.split('\\')[-1]
                    relationships.append({"type": rel_type, "related": related})

            # Scopes
            scopes = [sm.group(1) for sm in self.SCOPE.finditer(content)]

            # Accessors
            accessors = []
            for am in self.ACCESSOR.finditer(content):
                accessors.append(am.group(1) or am.group(2) or "")

            # Mutators
            mutators = [mm.group(1) for mm in self.MUTATOR.finditer(content)]

            # Traits
            traits = []
            use_m = re.findall(r'use\s+([\w\\]+(?:,\s*[\w\\]+)*)\s*;', content)
            for uses in use_m:
                for t in uses.split(','):
                    t = t.strip().split('\\')[-1]
                    if t in ('SoftDeletes', 'HasFactory', 'Notifiable', 'HasApiTokens',
                             'Searchable', 'HasRoles', 'HasUuids', 'HasUlids',
                             'Billable', 'Prunable', 'MassPrunable'):
                        traits.append(t)

            model = LaravelModelInfo(
                name=name,
                table_name=table,
                fillable=fillable[:20],
                guarded=guarded[:10],
                hidden=hidden[:10],
                casts=casts,
                relationships=relationships[:20],
                scopes=scopes[:15],
                accessors=[a for a in accessors if a][:10],
                mutators=mutators[:10],
                traits=traits,
                uses_soft_deletes='SoftDeletes' in traits,
                uses_uuid='HasUuids' in traits,
                uses_factory='HasFactory' in traits,
                file=file_path,
                line_number=line,
            )
            result.models.append(model)

    def _extract_migrations(self, content: str, file_path: str, result: LaravelParseResult):
        """Extract Laravel migration definitions."""
        for m in self.MIGRATION_PATTERN.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())

            tables_created = [t.group(1) for t in self.CREATE_TABLE.finditer(content)]
            tables_modified = [t.group(1) for t in self.ALTER_TABLE.finditer(content)]

            columns = []
            for col_m in self.COLUMN_DEF.finditer(content):
                col_type = col_m.group(1)
                col_name = col_m.group(2) or col_type
                columns.append({"name": col_name, "type": col_type})

            indexes = [idx.group(1) for idx in self.INDEX_DEF.finditer(content)]
            foreign_keys = [fk.group(1) for fk in self.FOREIGN_KEY.finditer(content)]

            mig = LaravelMigrationInfo(
                name=name,
                tables_created=tables_created,
                tables_modified=tables_modified,
                columns=columns[:30],
                indexes=indexes[:10],
                foreign_keys=foreign_keys[:10],
                file=file_path,
                line_number=line,
            )
            result.migrations.append(mig)

    def _extract_middleware(self, content: str, file_path: str, result: LaravelParseResult):
        """Extract Laravel middleware definitions."""
        if not self.MIDDLEWARE_HANDLE.search(content):
            return
        for m in self.MIDDLEWARE_CLASS.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())
            mw = LaravelMiddlewareInfo(
                name=name,
                class_name=name,
                file=file_path,
                line_number=line,
            )
            result.middleware.append(mw)

    def _extract_service_providers(self, content: str, file_path: str, result: LaravelParseResult):
        """Extract Laravel service provider definitions."""
        for m in self.PROVIDER_PATTERN.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())

            bindings = []
            for bind_m in self.BIND_PATTERN.finditer(content):
                abstract = bind_m.group(1) or bind_m.group(2)
                if abstract:
                    bindings.append({"abstract": abstract.split('\\')[-1]})

            singletons = []
            for sing_m in re.finditer(r"\$this->app->singleton\s*\(\s*(?:(\w+(?:\\\w+)*)::class|['\"]([^'\"]+)['\"])", content):
                singletons.append((sing_m.group(1) or sing_m.group(2) or "").split('\\')[-1])

            deferred = bool(re.search(r"implements\s+DeferrableProvider", content))

            sp = LaravelServiceProviderInfo(
                name=name,
                bindings=bindings[:15],
                singletons=singletons[:10],
                deferred=deferred,
                file=file_path,
                line_number=line,
            )
            result.service_providers.append(sp)

    def _extract_jobs(self, content: str, file_path: str, result: LaravelParseResult):
        """Extract Laravel job definitions."""
        for m in self.JOB_PATTERN.finditer(content):
            name = m.group(1) or m.group(2)
            if not name:
                continue
            line = self._get_line(content, m.start())

            queue = ""
            q_m = self.JOB_QUEUE.search(content)
            if q_m:
                queue = q_m.group(1)

            tries = 0
            tries_m = self.JOB_TRIES.search(content)
            if tries_m:
                tries = int(tries_m.group(1))

            timeout = 0
            to_m = self.JOB_TIMEOUT.search(content)
            if to_m:
                timeout = int(to_m.group(1))

            is_unique = bool(re.search(r'ShouldBeUnique', content))

            job = LaravelJobInfo(
                name=name,
                queue=queue,
                tries=tries,
                timeout=timeout,
                is_unique=is_unique,
                file=file_path,
                line_number=line,
            )
            result.jobs.append(job)

    def _extract_events(self, content: str, file_path: str, result: LaravelParseResult):
        """Extract Laravel event definitions."""
        # Only parse files that look like events
        if not re.search(r'class\s+\w+.*?(?:Event|ShouldBroadcast)', content):
            return
        # Check for event-like patterns (avoid false positives)
        if not re.search(r'(?:use\s+.*Dispatchable|InteractsWithSockets|SerializesModels|Illuminate\\.*Event)', content):
            return
        for m in self.EVENT_PATTERN.finditer(content):
            name = m.group(1)
            if 'Controller' in name or 'Provider' in name or 'Model' in name:
                continue
            line = self._get_line(content, m.start())
            is_broadcastable = bool(re.search(r'ShouldBroadcast', content))
            channel = ""
            ch_m = self.EVENT_CHANNEL.search(content)
            if ch_m:
                channel = ch_m.group(1)
            event = LaravelEventInfo(
                name=name,
                is_broadcastable=is_broadcastable,
                channel=channel,
                file=file_path,
                line_number=line,
            )
            result.events.append(event)

    def _extract_notifications(self, content: str, file_path: str, result: LaravelParseResult):
        """Extract Laravel notification definitions."""
        for m in self.NOTIFICATION_PATTERN.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())
            channels = []
            via_m = self.NOTIFICATION_VIA.search(content)
            if via_m:
                channels = [c.strip().strip("'\"") for c in via_m.group(1).split(',') if c.strip()]
            is_queued = bool(re.search(r'ShouldQueue', content))
            notif = LaravelNotificationInfo(
                name=name,
                channels=channels[:5],
                is_queued=is_queued,
                file=file_path,
                line_number=line,
            )
            result.notifications.append(notif)

    def _extract_mailables(self, content: str, file_path: str, result: LaravelParseResult):
        """Extract Laravel mailable definitions."""
        for m in self.MAIL_PATTERN.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())
            subject = ""
            sub_m = self.MAIL_SUBJECT.search(content)
            if sub_m:
                subject = sub_m.group(1)
            view = ""
            view_m = self.MAIL_VIEW.search(content)
            if view_m:
                view = view_m.group(1)
            is_markdown = bool(re.search(r'->markdown\s*\(', content))
            is_queued = bool(re.search(r'ShouldQueue', content))
            mail = LaravelMailInfo(
                name=name,
                subject=subject,
                view=view,
                is_queued=is_queued,
                is_markdown=is_markdown,
                file=file_path,
                line_number=line,
            )
            result.mailables.append(mail)

    def _extract_policies(self, content: str, file_path: str, result: LaravelParseResult):
        """Extract Laravel policy definitions."""
        for m in self.POLICY_PATTERN.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())
            methods = [pm.group(1) for pm in self.POLICY_METHOD.finditer(content)]
            # Try to detect associated model
            model = ""
            model_m = re.search(r'(?:public\s+function\s+\w+\s*\(\s*\w+\s+\$\w+\s*,\s*)?(\w+)\s+\$', content)
            if model_m:
                model = model_m.group(1)
            policy = LaravelPolicyInfo(
                name=name,
                model=model,
                methods=methods[:15],
                file=file_path,
                line_number=line,
            )
            result.policies.append(policy)

    def _extract_commands(self, content: str, file_path: str, result: LaravelParseResult):
        """Extract Laravel Artisan command definitions."""
        for m in self.COMMAND_PATTERN.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())
            signature = ""
            sig_m = self.COMMAND_SIGNATURE.search(content)
            if sig_m:
                signature = sig_m.group(1)
            description = ""
            desc_m = self.COMMAND_DESC.search(content)
            if desc_m:
                description = desc_m.group(1)
            cmd = LaravelCommandInfo(
                name=name,
                signature=signature,
                description=description,
                file=file_path,
                line_number=line,
            )
            result.commands.append(cmd)

    def _extract_observers(self, content: str, file_path: str, result: LaravelParseResult):
        """Extract Laravel observer definitions."""
        for m in self.OBSERVER_PATTERN.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())
            events = [om.group(1) for om in self.OBSERVER_METHOD.finditer(content)]
            # Try to infer model name from observer name
            model = name.replace('Observer', '')
            obs = LaravelObserverInfo(
                name=name,
                model=model,
                events=events[:15],
                file=file_path,
                line_number=line,
            )
            result.observers.append(obs)

    def _extract_form_requests(self, content: str, file_path: str, result: LaravelParseResult):
        """Extract Laravel form request definitions."""
        for m in self.FORM_REQUEST_PATTERN.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())
            rules = []
            rules_m = self.FORM_RULES.search(content)
            if rules_m:
                for r in re.finditer(r"['\"](\w+(?:\.\w+)?)['\"]", rules_m.group(1)):
                    rules.append(r.group(1))
            authorize = not bool(re.search(r'return\s+false\s*;.*?function\s+authorize', content, re.DOTALL))
            fr = LaravelFormRequestInfo(
                name=name,
                rules=rules[:20],
                authorize=authorize,
                file=file_path,
                line_number=line,
            )
            result.form_requests.append(fr)

    def _extract_resources(self, content: str, file_path: str, result: LaravelParseResult):
        """Extract Laravel API resource definitions."""
        for m in self.RESOURCE_PATTERN.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())
            is_collection = 'Collection' in name or 'extends ResourceCollection' in content
            # Infer model from resource name
            model = name.replace('Resource', '').replace('Collection', '')
            res = LaravelResourceInfo(
                name=name,
                model=model,
                is_collection=is_collection,
                file=file_path,
                line_number=line,
            )
            result.resources.append(res)

    def _extract_configs(self, content: str, file_path: str, result: LaravelParseResult):
        """Extract Laravel configuration keys."""
        if not file_path.endswith('.php') or '/config/' not in file_path:
            return
        for m in self.ENV_CALL.finditer(content):
            cfg = LaravelConfigInfo(
                key=m.group(1),
                file=file_path,
                line_number=self._get_line(content, m.start()),
            )
            result.configs.append(cfg)
