"""
Enhanced CodeIgniter Framework Parser for CodeTrellis.

v5.3: Full CodeIgniter framework support (3.x through 4.x).
Extracts controllers, models, libraries, helpers, views, routes,
filters, commands, entities, database migrations, seeders, validation rules,
configuration, RESTful resources, events.

Runs AFTER the base PHP parser when CodeIgniter framework is detected.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


# ===== DATACLASSES =====

@dataclass
class CodeIgniterRouteInfo:
    """Information about a CodeIgniter route."""
    method: str  # GET, POST, PUT, DELETE, CLI, resource, presenter
    path: str
    handler: str = ""
    namespace: str = ""
    filter: str = ""
    placeholder: str = ""
    is_cli: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class CodeIgniterControllerInfo:
    """Information about a CodeIgniter controller."""
    name: str
    parent_class: str = ""
    methods: List[str] = field(default_factory=list)
    helpers_loaded: List[str] = field(default_factory=list)
    models_loaded: List[str] = field(default_factory=list)
    is_restful: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class CodeIgniterModelInfo:
    """Information about a CodeIgniter model."""
    name: str
    table: str = ""
    primary_key: str = ""
    allowed_fields: List[str] = field(default_factory=list)
    return_type: str = ""  # array, object, entity class
    use_timestamps: bool = False
    use_soft_deletes: bool = False
    validation_rules: Dict[str, str] = field(default_factory=dict)
    before_callbacks: List[str] = field(default_factory=list)
    after_callbacks: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class CodeIgniterEntityInfo:
    """Information about a CodeIgniter entity (CI4)."""
    name: str
    attributes: List[str] = field(default_factory=list)
    casts: Dict[str, str] = field(default_factory=dict)
    dates: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class CodeIgniterMigrationInfo:
    """Information about a CodeIgniter migration."""
    name: str
    tables_created: List[str] = field(default_factory=list)
    tables_modified: List[str] = field(default_factory=list)
    columns: List[Dict[str, str]] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class CodeIgniterFilterInfo:
    """Information about a CodeIgniter filter (CI4)."""
    name: str
    before_methods: List[str] = field(default_factory=list)
    after_methods: List[str] = field(default_factory=list)
    applies_to: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class CodeIgniterLibraryInfo:
    """Information about a CodeIgniter library."""
    name: str
    methods: List[str] = field(default_factory=list)
    is_custom: bool = True
    file: str = ""
    line_number: int = 0


@dataclass
class CodeIgniterHelperInfo:
    """Information about a CodeIgniter helper."""
    name: str
    functions: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class CodeIgniterCommandInfo:
    """Information about a CodeIgniter CLI command (CI4)."""
    name: str
    group: str = ""
    description: str = ""
    usage: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class CodeIgniterConfigInfo:
    """Information about CodeIgniter configuration."""
    key: str
    value: str = ""
    section: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class CodeIgniterParseResult:
    """Complete parse result for a CodeIgniter file."""
    file_path: str
    file_type: str = "php"

    # Routes
    routes: List[CodeIgniterRouteInfo] = field(default_factory=list)

    # Controllers
    controllers: List[CodeIgniterControllerInfo] = field(default_factory=list)

    # Models
    models: List[CodeIgniterModelInfo] = field(default_factory=list)

    # Entities
    entities: List[CodeIgniterEntityInfo] = field(default_factory=list)

    # Migrations
    migrations: List[CodeIgniterMigrationInfo] = field(default_factory=list)

    # Filters
    filters: List[CodeIgniterFilterInfo] = field(default_factory=list)

    # Libraries
    libraries: List[CodeIgniterLibraryInfo] = field(default_factory=list)

    # Helpers
    helpers: List[CodeIgniterHelperInfo] = field(default_factory=list)

    # Commands
    commands: List[CodeIgniterCommandInfo] = field(default_factory=list)

    # Configuration
    configs: List[CodeIgniterConfigInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    codeigniter_version: str = ""  # 3.x or 4.x
    is_ci4: bool = False


# ===== PARSER =====

class EnhancedCodeIgniterParser:
    """
    Enhanced parser for CodeIgniter framework (3.x through 4.x).
    Extracts routes, controllers, models, entities, migrations,
    filters, libraries, helpers, commands, configuration.
    """

    # Detection pattern
    CI_DETECT = re.compile(
        r"(?:CodeIgniter\\|CI_Controller|BaseController.*CodeIgniter|"
        r"extends\s+(?:CI_Controller|CI_Model|BaseController|ResourceController|"
        r"ResourcePresenter|Migration)|"
        r"use\s+CodeIgniter\\|namespace\s+App\\(?:Controllers|Models|Entities|Filters)|"
        r"\$this->load->(?:model|view|library|helper)|"
        r"service\s*\(\s*['\"])",
        re.MULTILINE,
    )

    # Framework ecosystem patterns
    FRAMEWORK_PATTERNS = {
        'codeigniter': re.compile(r'(?:CodeIgniter\\|CI_Controller|CI_Model)'),
        'codeigniter4': re.compile(r'(?:CodeIgniter\\(?:Controller|Model|Entity|Shield)|namespace\s+App\\)'),
        'codeigniter3': re.compile(r'(?:CI_Controller|CI_Model|CI_Form_validation|\$this->load->)'),
        'shield': re.compile(r'(?:CodeIgniter\\Shield)'),
        'myth_auth': re.compile(r'(?:Myth\\Auth)'),
    }

    # Route patterns (CI4)
    ROUTE_CI4 = re.compile(
        r"\$routes->(get|post|put|patch|delete|options|cli|add|match|resource|presenter)\s*\(\s*"
        r"['\"]([^'\"]+)['\"]"
        r"(?:\s*,\s*['\"]?([^'\")\s,]+)['\"]?)?",
        re.MULTILINE,
    )
    ROUTE_GROUP = re.compile(
        r"\$routes->group\s*\(\s*['\"]([^'\"]+)['\"]",
    )

    # Route patterns (CI3)
    ROUTE_CI3 = re.compile(
        r"\$route\s*\[\s*['\"]([^'\"]+)['\"]"
        r"\s*\]\s*=\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # Controller patterns (CI4)
    CONTROLLER_CI4 = re.compile(
        r"class\s+(\w+)\s+extends\s+(BaseController|ResourceController|ResourcePresenter|Controller)",
        re.MULTILINE,
    )
    # Controller patterns (CI3)
    CONTROLLER_CI3 = re.compile(
        r"class\s+(\w+)\s+extends\s+CI_Controller",
        re.MULTILINE,
    )
    CONTROLLER_METHOD = re.compile(
        r"public\s+function\s+(\w+)\s*\(",
    )

    # Model patterns (CI4)
    MODEL_CI4 = re.compile(
        r"class\s+(\w+Model)\s+extends\s+(?:Model|\\CodeIgniter\\Model)",
        re.MULTILINE,
    )
    MODEL_TABLE = re.compile(
        r"(?:protected|public)\s+\$table\s*=\s*['\"](\w+)['\"]",
    )
    MODEL_PK = re.compile(
        r"(?:protected|public)\s+\$primaryKey\s*=\s*['\"](\w+)['\"]",
    )
    MODEL_ALLOWED = re.compile(
        r"(?:protected|public)\s+\$allowedFields\s*=\s*\[([^\]]*)\]",
        re.DOTALL,
    )
    MODEL_RETURN = re.compile(
        r"(?:protected|public)\s+\$returnType\s*=\s*['\"]?(\w+(?:\\\w+)*)['\"]?",
    )
    MODEL_TIMESTAMPS = re.compile(
        r"(?:protected|public)\s+\$useTimestamps\s*=\s*true",
    )
    MODEL_SOFT_DELETE = re.compile(
        r"(?:protected|public)\s+\$useSoftDeletes\s*=\s*true|use\s+SoftDeletes",
    )

    # Model patterns (CI3)
    MODEL_CI3 = re.compile(
        r"class\s+(\w+(?:_model)?)\s+extends\s+CI_Model",
        re.MULTILINE,
    )

    # Entity patterns (CI4)
    ENTITY_CI4 = re.compile(
        r"class\s+(\w+)\s+extends\s+Entity",
        re.MULTILINE,
    )
    ENTITY_CASTS = re.compile(
        r"(?:protected|public)\s+\$casts\s*=\s*\[([^\]]*)\]",
        re.DOTALL,
    )
    ENTITY_DATES = re.compile(
        r"(?:protected|public)\s+\$dates\s*=\s*\[([^\]]*)\]",
        re.DOTALL,
    )

    # Migration patterns
    MIGRATION_CLASS = re.compile(
        r"class\s+(\w+)\s+extends\s+Migration",
        re.MULTILINE,
    )
    MIGRATION_CREATE = re.compile(
        r"\$this->forge->(?:createTable|addField)\s*\(\s*['\"]?(\w+)['\"]?",
    )
    MIGRATION_FIELD = re.compile(
        r"['\"](\w+)['\"].*?['\"]type['\"].*?['\"](\w+)['\"]",
    )

    # Filter patterns (CI4)
    FILTER_CLASS = re.compile(
        r"class\s+(\w+(?:Filter)?)\s+implements\s+FilterInterface",
        re.MULTILINE,
    )

    # Library patterns
    LIBRARY_LOAD = re.compile(
        r"\$this->load->library\s*\(\s*['\"](\w+)['\"]",
    )
    LIBRARY_CLASS = re.compile(
        r"class\s+(\w+)\s*\{",
        re.MULTILINE,
    )

    # Helper patterns
    HELPER_LOAD = re.compile(
        r"(?:\$this->load->helper|helper)\s*\(\s*(?:\[([^\]]*)\]|['\"](\w+)['\"])",
    )

    # Command patterns (CI4)
    COMMAND_CLASS = re.compile(
        r"class\s+(\w+)\s+extends\s+BaseCommand",
        re.MULTILINE,
    )
    COMMAND_GROUP = re.compile(
        r"(?:protected|public)\s+\$group\s*=\s*['\"](\w+)['\"]",
    )
    COMMAND_NAME = re.compile(
        r"(?:protected|public)\s+\$name\s*=\s*['\"]([^'\"]+)['\"]",
    )
    COMMAND_DESC = re.compile(
        r"(?:protected|public)\s+\$description\s*=\s*['\"]([^'\"]+)['\"]",
    )

    # CI3/CI4 version detection
    VERSION_PATTERNS = [
        (r'namespace\s+App\\|CodeIgniter\\', '4.x'),
        (r'CI_Controller|CI_Model|\$this->load->', '3.x'),
    ]

    def parse(self, content: str, file_path: str = "") -> CodeIgniterParseResult:
        """Parse PHP source code for CodeIgniter-specific patterns."""
        result = CodeIgniterParseResult(file_path=file_path)

        if not content.strip():
            return result

        # Check if this file uses CodeIgniter
        if not self.CI_DETECT.search(content):
            return result

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect version
        result.codeigniter_version = self._detect_version(content)
        result.is_ci4 = result.codeigniter_version.startswith('4')

        # Extract all entities
        self._extract_routes(content, file_path, result)
        self._extract_controllers(content, file_path, result)
        self._extract_models(content, file_path, result)
        self._extract_entities(content, file_path, result)
        self._extract_migrations(content, file_path, result)
        self._extract_filters(content, file_path, result)
        self._extract_libraries(content, file_path, result)
        self._extract_helpers(content, file_path, result)
        self._extract_commands(content, file_path, result)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect CodeIgniter ecosystem frameworks used."""
        detected = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """Detect CodeIgniter version from code features."""
        for pattern, version in self.VERSION_PATTERNS:
            if re.search(pattern, content):
                return version
        return ""

    def _get_line(self, content: str, pos: int) -> int:
        """Get 1-based line number for a position."""
        return content[:pos].count('\n') + 1

    def _extract_routes(self, content: str, file_path: str, result: CodeIgniterParseResult):
        """Extract CodeIgniter route definitions."""
        # CI4 routes
        for m in self.ROUTE_CI4.finditer(content):
            method = m.group(1).upper()
            path = m.group(2)
            handler = m.group(3) or ""
            line = self._get_line(content, m.start())
            route = CodeIgniterRouteInfo(
                method=method,
                path=path,
                handler=handler,
                is_cli=method == 'CLI',
                file=file_path,
                line_number=line,
            )
            result.routes.append(route)

        # CI3 routes
        for m in self.ROUTE_CI3.finditer(content):
            path = m.group(1)
            handler = m.group(2)
            line = self._get_line(content, m.start())
            if path == 'default_controller' or path == '404_override' or path == 'translate_uri_dashes':
                continue
            route = CodeIgniterRouteInfo(
                method="ANY",
                path=path,
                handler=handler,
                file=file_path,
                line_number=line,
            )
            result.routes.append(route)

    def _extract_controllers(self, content: str, file_path: str, result: CodeIgniterParseResult):
        """Extract CodeIgniter controller definitions."""
        # CI4
        for m in self.CONTROLLER_CI4.finditer(content):
            name = m.group(1)
            parent = m.group(2)
            line = self._get_line(content, m.start())
            methods = [am.group(1) for am in self.CONTROLLER_METHOD.finditer(content)
                       if am.group(1) not in ('__construct', 'initController')]
            is_restful = parent in ('ResourceController', 'ResourcePresenter')

            # Find loaded helpers and models
            helpers_loaded = [h.group(2) or "" for h in self.HELPER_LOAD.finditer(content)
                              if h.group(2)]
            models_loaded = []
            for ml in re.finditer(r"(?:model|new)\s*\(\s*['\"]?(\w+(?:Model)?)['\"]?", content):
                models_loaded.append(ml.group(1))

            ctrl = CodeIgniterControllerInfo(
                name=name,
                parent_class=parent,
                methods=methods[:30],
                helpers_loaded=helpers_loaded[:10],
                models_loaded=models_loaded[:10],
                is_restful=is_restful,
                file=file_path,
                line_number=line,
            )
            result.controllers.append(ctrl)

        # CI3
        for m in self.CONTROLLER_CI3.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())
            methods = [am.group(1) for am in self.CONTROLLER_METHOD.finditer(content)
                       if am.group(1) != '__construct']

            helpers_loaded = [h.group(2) or "" for h in self.HELPER_LOAD.finditer(content)
                              if h.group(2)]
            models_loaded = []
            for ml in re.finditer(r"\$this->load->model\s*\(\s*['\"](\w+)['\"]", content):
                models_loaded.append(ml.group(1))

            ctrl = CodeIgniterControllerInfo(
                name=name,
                parent_class="CI_Controller",
                methods=methods[:30],
                helpers_loaded=helpers_loaded[:10],
                models_loaded=models_loaded[:10],
                file=file_path,
                line_number=line,
            )
            result.controllers.append(ctrl)

    def _extract_models(self, content: str, file_path: str, result: CodeIgniterParseResult):
        """Extract CodeIgniter model definitions."""
        # CI4
        for m in self.MODEL_CI4.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())

            table = ""
            table_m = self.MODEL_TABLE.search(content)
            if table_m:
                table = table_m.group(1)

            pk = ""
            pk_m = self.MODEL_PK.search(content)
            if pk_m:
                pk = pk_m.group(1)

            allowed = []
            allowed_m = self.MODEL_ALLOWED.search(content)
            if allowed_m:
                allowed = [s.strip().strip("'\"") for s in allowed_m.group(1).split(',') if s.strip().strip("'\"")]

            return_type = ""
            ret_m = self.MODEL_RETURN.search(content)
            if ret_m:
                return_type = ret_m.group(1)

            use_timestamps = bool(self.MODEL_TIMESTAMPS.search(content))
            use_soft_deletes = bool(self.MODEL_SOFT_DELETE.search(content))

            # Validation rules
            rules = {}
            rules_m = re.search(r"(?:protected|public)\s+\$validationRules\s*=\s*\[([^\]]*(?:\[[^\]]*\][^\]]*)*)\]", content, re.DOTALL)
            if rules_m:
                for rule_m in re.finditer(r"['\"](\w+)['\"].*?['\"]([^'\"]+)['\"]", rules_m.group(1)):
                    rules[rule_m.group(1)] = rule_m.group(2)

            model = CodeIgniterModelInfo(
                name=name,
                table=table,
                primary_key=pk,
                allowed_fields=allowed[:30],
                return_type=return_type,
                use_timestamps=use_timestamps,
                use_soft_deletes=use_soft_deletes,
                validation_rules=rules,
                file=file_path,
                line_number=line,
            )
            result.models.append(model)

        # CI3
        for m in self.MODEL_CI3.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())
            model = CodeIgniterModelInfo(
                name=name,
                file=file_path,
                line_number=line,
            )
            result.models.append(model)

    def _extract_entities(self, content: str, file_path: str, result: CodeIgniterParseResult):
        """Extract CodeIgniter entity definitions (CI4)."""
        for m in self.ENTITY_CI4.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())

            attributes = []
            for prop_m in re.finditer(r"(?:protected|private)\s+\$(\w+)", content):
                attr = prop_m.group(1)
                if attr not in ('datamap', 'dates', 'casts', 'attributes'):
                    attributes.append(attr)

            casts = {}
            casts_m = self.ENTITY_CASTS.search(content)
            if casts_m:
                for pair in re.finditer(r"['\"](\w+)['\"]\s*=>\s*['\"]?(\w+)['\"]?", casts_m.group(1)):
                    casts[pair.group(1)] = pair.group(2)

            dates = []
            dates_m = self.ENTITY_DATES.search(content)
            if dates_m:
                dates = [s.strip().strip("'\"") for s in dates_m.group(1).split(',') if s.strip().strip("'\"")]

            entity = CodeIgniterEntityInfo(
                name=name,
                attributes=attributes[:20],
                casts=casts,
                dates=dates[:10],
                file=file_path,
                line_number=line,
            )
            result.entities.append(entity)

    def _extract_migrations(self, content: str, file_path: str, result: CodeIgniterParseResult):
        """Extract CodeIgniter migration definitions."""
        for m in self.MIGRATION_CLASS.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())

            tables_created = [t.group(1) for t in self.MIGRATION_CREATE.finditer(content)]

            mig = CodeIgniterMigrationInfo(
                name=name,
                tables_created=tables_created[:10],
                file=file_path,
                line_number=line,
            )
            result.migrations.append(mig)

    def _extract_filters(self, content: str, file_path: str, result: CodeIgniterParseResult):
        """Extract CodeIgniter filter definitions (CI4)."""
        for m in self.FILTER_CLASS.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())

            has_before = bool(re.search(r'public\s+function\s+before\s*\(', content))
            has_after = bool(re.search(r'public\s+function\s+after\s*\(', content))

            filt = CodeIgniterFilterInfo(
                name=name,
                before_methods=['before'] if has_before else [],
                after_methods=['after'] if has_after else [],
                file=file_path,
                line_number=line,
            )
            result.filters.append(filt)

    def _extract_libraries(self, content: str, file_path: str, result: CodeIgniterParseResult):
        """Extract CodeIgniter library loads."""
        for m in self.LIBRARY_LOAD.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())
            lib = CodeIgniterLibraryInfo(
                name=name,
                file=file_path,
                line_number=line,
            )
            result.libraries.append(lib)

    def _extract_helpers(self, content: str, file_path: str, result: CodeIgniterParseResult):
        """Extract CodeIgniter helper loads and definitions."""
        # Helper loads
        for m in self.HELPER_LOAD.finditer(content):
            names_str = m.group(1) or m.group(2)
            if not names_str:
                continue
            line = self._get_line(content, m.start())
            if m.group(1):
                names = [s.strip().strip("'\"") for s in names_str.split(',') if s.strip().strip("'\"")]
            else:
                names = [names_str]
            for name in names:
                helper = CodeIgniterHelperInfo(
                    name=name,
                    file=file_path,
                    line_number=line,
                )
                result.helpers.append(helper)

        # Helper definitions (function files)
        if '_helper' in file_path:
            functions = [fm.group(1) for fm in re.finditer(r'function\s+(\w+)\s*\(', content)
                         if not fm.group(1).startswith('_')]
            if functions:
                name = file_path.split('/')[-1].replace('.php', '')
                helper = CodeIgniterHelperInfo(
                    name=name,
                    functions=functions[:20],
                    file=file_path,
                    line_number=1,
                )
                result.helpers.append(helper)

    def _extract_commands(self, content: str, file_path: str, result: CodeIgniterParseResult):
        """Extract CodeIgniter CLI command definitions (CI4)."""
        for m in self.COMMAND_CLASS.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())

            group = ""
            grp_m = self.COMMAND_GROUP.search(content)
            if grp_m:
                group = grp_m.group(1)

            cmd_name = ""
            nm_m = self.COMMAND_NAME.search(content)
            if nm_m:
                cmd_name = nm_m.group(1)

            desc = ""
            desc_m = self.COMMAND_DESC.search(content)
            if desc_m:
                desc = desc_m.group(1)

            cmd = CodeIgniterCommandInfo(
                name=name,
                group=group,
                description=desc,
                file=file_path,
                line_number=line,
            )
            result.commands.append(cmd)
