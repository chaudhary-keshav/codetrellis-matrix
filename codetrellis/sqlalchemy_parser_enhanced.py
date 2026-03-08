"""
EnhancedSQLAlchemyParser - Deep extraction for SQLAlchemy ORM/Core projects.

Extends the basic SQLAlchemyExtractor with:
- SQLAlchemy 2.0 (mapped_column, Mapped[], DeclarativeBase) AND legacy 1.x
- Core Table() definitions (non-ORM)
- Engine/Session/sessionmaker configuration
- Alembic migration detection
- Hybrid properties, column properties
- Association tables / secondary tables
- Event listeners (@event.listens_for)
- Custom types
- Index and constraint definitions (__table_args__)
- Query patterns and eager loading

Supports SQLAlchemy 0.x through 2.x+ (latest).

Part of CodeTrellis v4.33 - Python Framework Support.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any

from codetrellis.extractors.python.sqlalchemy_extractor import (
    SQLAlchemyExtractor,
    SQLAlchemyModelInfo,
    SQLAlchemyColumnInfo,
    SQLAlchemyRelationshipInfo,
    RelationshipType,
)


# ═══════════════════════════════════════════════════════════════════
# Enhanced Dataclasses
# ═══════════════════════════════════════════════════════════════════

@dataclass
class SQLAlchemyCoreTableInfo:
    """Information about a SQLAlchemy Core Table() definition."""
    name: str
    variable_name: str
    columns: List[Dict[str, Any]] = field(default_factory=list)
    line_number: int = 0


@dataclass
class SQLAlchemyEngineInfo:
    """Information about SQLAlchemy engine configuration."""
    variable_name: str
    url_pattern: str = ""  # postgresql, mysql, sqlite, etc.
    pool_size: Optional[int] = None
    echo: bool = False
    is_async: bool = False
    line_number: int = 0


@dataclass
class SQLAlchemySessionInfo:
    """Information about SQLAlchemy session/sessionmaker configuration."""
    variable_name: str
    session_type: str = "sessionmaker"  # sessionmaker, scoped_session, async_session
    bind: Optional[str] = None
    autocommit: bool = False
    autoflush: bool = True
    expire_on_commit: bool = True
    line_number: int = 0


@dataclass
class SQLAlchemyMigrationInfo:
    """Information about Alembic migration."""
    revision: str
    message: str = ""
    down_revision: Optional[str] = None
    operations: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class SQLAlchemyEventListenerInfo:
    """Information about a SQLAlchemy event listener."""
    target: str
    event_name: str
    handler: str
    line_number: int = 0


@dataclass
class SQLAlchemyHybridPropertyInfo:
    """Information about a SQLAlchemy hybrid property."""
    name: str
    model: str = ""
    has_setter: bool = False
    has_expression: bool = False
    line_number: int = 0


@dataclass
class SQLAlchemyParseResult:
    """Complete parse result for a SQLAlchemy file."""
    file_path: str
    file_type: str = "module"  # model, migration, config, repository, test

    # From base extractor
    models: List[SQLAlchemyModelInfo] = field(default_factory=list)

    # Enhanced extraction
    core_tables: List[SQLAlchemyCoreTableInfo] = field(default_factory=list)
    engines: List[SQLAlchemyEngineInfo] = field(default_factory=list)
    sessions: List[SQLAlchemySessionInfo] = field(default_factory=list)
    migrations: List[SQLAlchemyMigrationInfo] = field(default_factory=list)
    event_listeners: List[SQLAlchemyEventListenerInfo] = field(default_factory=list)
    hybrid_properties: List[SQLAlchemyHybridPropertyInfo] = field(default_factory=list)

    # Aggregate
    detected_frameworks: List[str] = field(default_factory=list)
    sqlalchemy_version: str = ""
    total_models: int = 0
    total_tables: int = 0
    uses_async: bool = False


# ═══════════════════════════════════════════════════════════════════
# Parser
# ═══════════════════════════════════════════════════════════════════

class EnhancedSQLAlchemyParser:
    """
    Enhanced SQLAlchemy parser v1.0 that extends the basic SQLAlchemyExtractor.

    Provides deep extraction for SQLAlchemy 0.x through 2.x+ including
    ORM models, Core tables, engine/session config, Alembic migrations,
    event listeners, hybrid properties, and more.
    """

    # ── SQLAlchemy ecosystem detection patterns ───────────────────
    FRAMEWORK_PATTERNS = {
        # Core SQLAlchemy
        'sqlalchemy': re.compile(
            r'from\s+sqlalchemy\s+import|import\s+sqlalchemy|from\s+sqlalchemy\.',
            re.MULTILINE,
        ),
        'sqlalchemy.orm': re.compile(
            r'from\s+sqlalchemy\.orm|relationship\s*\(|mapped_column\s*\(|Session\b|sessionmaker\b',
            re.MULTILINE,
        ),
        'sqlalchemy.ext': re.compile(
            r'from\s+sqlalchemy\.ext\.|hybrid_property|declarative_base|automap_base',
            re.MULTILINE,
        ),
        'sqlalchemy.engine': re.compile(
            r'create_engine\s*\(|create_async_engine\s*\(',
            re.MULTILINE,
        ),
        'sqlalchemy.types': re.compile(
            r'from\s+sqlalchemy\.types|TypeDecorator\b',
            re.MULTILINE,
        ),
        'sqlalchemy.event': re.compile(
            r'from\s+sqlalchemy\s+import\s+event|from\s+sqlalchemy\.event|@event\.listens_for|listens_for\s*\(',
            re.MULTILINE,
        ),
        'sqlalchemy.schema': re.compile(
            r'from\s+sqlalchemy\.schema|MetaData\s*\(|Table\s*\(',
            re.MULTILINE,
        ),

        # SQLAlchemy 2.0 features
        'sqlalchemy_2_0': re.compile(
            r'DeclarativeBase|MappedAsDataclass|mapped_column|Mapped\[|registry\s*\(',
            re.MULTILINE,
        ),

        # Alembic
        'alembic': re.compile(
            r'from\s+alembic|import\s+alembic|op\.\w+|revision\s*=',
            re.MULTILINE,
        ),

        # Async support
        'sqlalchemy_async': re.compile(
            r'create_async_engine|AsyncSession|async_sessionmaker|AsyncEngine',
            re.MULTILINE,
        ),

        # SQLModel (Pydantic + SQLAlchemy)
        'sqlmodel': re.compile(
            r'from\s+sqlmodel|import\s+sqlmodel|SQLModel\b',
            re.MULTILINE,
        ),

        # Flask-SQLAlchemy
        'flask_sqlalchemy': re.compile(
            r'from\s+flask_sqlalchemy|Flask-SQLAlchemy|db\s*=\s*SQLAlchemy\s*\(',
            re.MULTILINE,
        ),

        # GeoAlchemy2
        'geoalchemy2': re.compile(
            r'from\s+geoalchemy2|import\s+geoalchemy2|Geometry\s*\(',
            re.MULTILINE,
        ),

        # SQLAlchemy-Utils
        'sqlalchemy_utils': re.compile(
            r'from\s+sqlalchemy_utils|import\s+sqlalchemy_utils|ChoiceType|UUIDType|URLType',
            re.MULTILINE,
        ),
    }

    # ── Core Table pattern ────────────────────────────────────────
    CORE_TABLE_PATTERN = re.compile(
        r'(\w+)\s*=\s*Table\s*\(\s*["\'](\w+)["\']\s*,\s*(\w+)',
        re.MULTILINE,
    )

    # ── Engine creation pattern ───────────────────────────────────
    ENGINE_PATTERN = re.compile(
        r'(\w+)\s*=\s*(create_engine|create_async_engine)\s*\(\s*([^)]*)\)',
        re.MULTILINE,
    )

    # ── Session/sessionmaker pattern ──────────────────────────────
    SESSION_PATTERN = re.compile(
        r'(\w+)\s*=\s*(sessionmaker|scoped_session|async_sessionmaker|AsyncSession)\s*\(\s*([^)]*)\)',
        re.MULTILINE,
    )

    # ── Alembic migration pattern ─────────────────────────────────
    REVISION_PATTERN = re.compile(
        r'revision\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE,
    )
    DOWN_REVISION_PATTERN = re.compile(
        r'down_revision\s*=\s*["\']([^"\']*)["\']',
        re.MULTILINE,
    )
    ALEMBIC_OP_PATTERN = re.compile(
        r'op\.(create_table|drop_table|add_column|drop_column|create_index|'
        r'drop_index|alter_column|create_foreign_key|create_unique_constraint|'
        r'rename_table|execute)\s*\(',
        re.MULTILINE,
    )

    # ── Event listener pattern ────────────────────────────────────
    EVENT_LISTENER_DECORATOR_PATTERN = re.compile(
        r'@event\.listens_for\s*\(\s*(\w+)\s*,\s*["\'](\w+)["\']\s*\)\s*\n'
        r'\s*(?:async\s+)?def\s+(\w+)',
        re.MULTILINE,
    )
    EVENT_LISTENER_CALL_PATTERN = re.compile(
        r'event\.listen\s*\(\s*(\w+)\s*,\s*["\'](\w+)["\']\s*,\s*(\w+)\s*\)',
        re.MULTILINE,
    )

    # ── Hybrid property pattern ───────────────────────────────────
    HYBRID_PROPERTY_PATTERN = re.compile(
        r'@hybrid_property\s*\n\s*def\s+(\w+)',
        re.MULTILINE,
    )
    HYBRID_SETTER_PATTERN = re.compile(
        r'@(\w+)\.setter\s*\n\s*def\s+(\w+)',
        re.MULTILINE,
    )
    HYBRID_EXPRESSION_PATTERN = re.compile(
        r'@(\w+)\.expression\s*\n\s*def\s+(\w+)',
        re.MULTILINE,
    )

    # ── Table args pattern ────────────────────────────────────────
    TABLE_ARGS_PATTERN = re.compile(
        r'__table_args__\s*=\s*\(',
        re.MULTILINE,
    )

    # ── Version feature detection ─────────────────────────────────
    SQLALCHEMY_VERSION_FEATURES = {
        'mapped_column': '2.0',
        'Mapped[': '2.0',
        'DeclarativeBase': '2.0',
        'MappedAsDataclass': '2.0',
        'registry': '1.4',
        'async_sessionmaker': '2.0',
        'create_async_engine': '1.4',
        'AsyncSession': '1.4',
        'relationship': '0.6',
        'declarative_base': '0.6',
        'Column': '0.1',
        'sessionmaker': '0.4',
        'scoped_session': '0.5',
        'hybrid_property': '0.7',
        'event.listens_for': '0.7',
        'TypeDecorator': '0.5',
    }

    def __init__(self):
        """Initialize the enhanced SQLAlchemy parser."""
        self.base_extractor = SQLAlchemyExtractor()

    def parse(self, content: str, file_path: str = "") -> SQLAlchemyParseResult:
        """
        Parse SQLAlchemy source code and extract all SQLAlchemy-specific information.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            SQLAlchemyParseResult with all extracted information
        """
        result = SQLAlchemyParseResult(file_path=file_path)

        # Determine file type
        result.file_type = self._classify_file(file_path, content)

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # ── ORM Models (base extractor) ──────────────────────────
        result.models = self.base_extractor.extract(content)

        # ── Core Tables ──────────────────────────────────────────
        self._extract_core_tables(content, result)

        # ── Engine config ────────────────────────────────────────
        self._extract_engines(content, result)

        # ── Session config ───────────────────────────────────────
        self._extract_sessions(content, result)

        # ── Alembic migrations ───────────────────────────────────
        self._extract_migrations(content, result)

        # ── Event listeners ──────────────────────────────────────
        self._extract_event_listeners(content, result)

        # ── Hybrid properties ────────────────────────────────────
        self._extract_hybrid_properties(content, result)

        # Aggregates
        result.total_models = len(result.models)
        result.total_tables = len(result.core_tables)
        result.uses_async = 'sqlalchemy_async' in result.detected_frameworks
        result.sqlalchemy_version = self._detect_sqlalchemy_version(content)

        return result

    # ─── Extraction methods ───────────────────────────────────────

    def _extract_core_tables(self, content: str, result: SQLAlchemyParseResult):
        """Extract Core Table() definitions."""
        for match in self.CORE_TABLE_PATTERN.finditer(content):
            var_name = match.group(1)
            table_name = match.group(2)

            # Try to extract column info from Table args
            columns = []
            table_start = match.end()
            # Find the closing paren - simplified extraction
            depth = 1
            pos = table_start
            while pos < len(content) and depth > 0:
                if content[pos] == '(':
                    depth += 1
                elif content[pos] == ')':
                    depth -= 1
                pos += 1
            table_body = content[table_start:pos]

            # Extract Column() defs within the Table
            for col_match in re.finditer(
                r'Column\s*\(\s*["\'](\w+)["\']\s*,\s*(\w+)', table_body
            ):
                columns.append({
                    'name': col_match.group(1),
                    'type': col_match.group(2),
                })

            result.core_tables.append(SQLAlchemyCoreTableInfo(
                name=table_name,
                variable_name=var_name,
                columns=columns,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_engines(self, content: str, result: SQLAlchemyParseResult):
        """Extract create_engine/create_async_engine calls."""
        for match in self.ENGINE_PATTERN.finditer(content):
            var_name = match.group(1)
            func_name = match.group(2)
            args_str = match.group(3)

            # Detect database URL pattern
            url_pattern = ""
            url_match = re.search(r'["\'](\w+)(?:\+\w+)?://', args_str)
            if url_match:
                url_pattern = url_match.group(1)

            # Extract options
            pool_size = None
            pool_match = re.search(r'pool_size\s*=\s*(\d+)', args_str)
            if pool_match:
                pool_size = int(pool_match.group(1))

            echo = 'echo=True' in args_str or 'echo = True' in args_str

            result.engines.append(SQLAlchemyEngineInfo(
                variable_name=var_name,
                url_pattern=url_pattern,
                pool_size=pool_size,
                echo=echo,
                is_async=func_name == 'create_async_engine',
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_sessions(self, content: str, result: SQLAlchemyParseResult):
        """Extract sessionmaker/session configuration."""
        for match in self.SESSION_PATTERN.finditer(content):
            var_name = match.group(1)
            session_type = match.group(2)
            args_str = match.group(3)

            bind = None
            bind_match = re.search(r'bind\s*=\s*(\w+)', args_str)
            if bind_match:
                bind = bind_match.group(1)

            autocommit = 'autocommit=True' in args_str or 'autocommit = True' in args_str
            autoflush = 'autoflush=False' not in args_str and 'autoflush = False' not in args_str
            expire = 'expire_on_commit=False' not in args_str and 'expire_on_commit = False' not in args_str

            result.sessions.append(SQLAlchemySessionInfo(
                variable_name=var_name,
                session_type=session_type,
                bind=bind,
                autocommit=autocommit,
                autoflush=autoflush,
                expire_on_commit=expire,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_migrations(self, content: str, result: SQLAlchemyParseResult):
        """Extract Alembic migration metadata."""
        rev_match = self.REVISION_PATTERN.search(content)
        if not rev_match:
            return

        revision = rev_match.group(1)

        # Get down revision
        down_rev = None
        down_match = self.DOWN_REVISION_PATTERN.search(content)
        if down_match:
            down_rev = down_match.group(1) or None

        # Get migration message from module docstring or comment
        message = ""
        msg_match = re.search(r'"""([^"]+)"""', content[:500])
        if msg_match:
            message = msg_match.group(1).strip().split('\n')[0]

        # Get operations
        operations = []
        for op_match in self.ALEMBIC_OP_PATTERN.finditer(content):
            operations.append(op_match.group(1))

        result.migrations.append(SQLAlchemyMigrationInfo(
            revision=revision,
            message=message,
            down_revision=down_rev,
            operations=operations,
            line_number=content[:rev_match.start()].count('\n') + 1,
        ))

    def _extract_event_listeners(self, content: str, result: SQLAlchemyParseResult):
        """Extract event listeners."""
        # Decorator-based
        for match in self.EVENT_LISTENER_DECORATOR_PATTERN.finditer(content):
            result.event_listeners.append(SQLAlchemyEventListenerInfo(
                target=match.group(1),
                event_name=match.group(2),
                handler=match.group(3),
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Call-based
        for match in self.EVENT_LISTENER_CALL_PATTERN.finditer(content):
            result.event_listeners.append(SQLAlchemyEventListenerInfo(
                target=match.group(1),
                event_name=match.group(2),
                handler=match.group(3),
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_hybrid_properties(self, content: str, result: SQLAlchemyParseResult):
        """Extract hybrid properties."""
        for match in self.HYBRID_PROPERTY_PATTERN.finditer(content):
            prop_name = match.group(1)

            # Check for setter and expression
            has_setter = bool(re.search(
                rf'@{re.escape(prop_name)}\.setter', content
            ))
            has_expression = bool(re.search(
                rf'@{re.escape(prop_name)}\.expression', content
            ))

            # Find enclosing class name
            model = ""
            before = content[:match.start()]
            class_match = re.search(r'class\s+(\w+)', before[::-1][:5000][::-1])
            if class_match:
                model = class_match.group(1)

            result.hybrid_properties.append(SQLAlchemyHybridPropertyInfo(
                name=prop_name,
                model=model,
                has_setter=has_setter,
                has_expression=has_expression,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    # ─── Helper methods ───────────────────────────────────────────

    def _classify_file(self, file_path: str, content: str) -> str:
        """Classify a SQLAlchemy file by its role."""
        normalized = file_path.replace('\\', '/').lower()
        basename = normalized.split('/')[-1] if normalized else ""

        # Alembic migration
        if '/versions/' in normalized or '/migrations/' in normalized or normalized.startswith('versions/') or normalized.startswith('migrations/'):
            if 'revision' in content and 'op.' in content:
                return 'migration'
        if 'alembic' in basename:
            return 'config'

        if 'model' in basename or 'schema' in basename or 'table' in basename:
            return 'model'
        if 'repo' in basename or 'crud' in basename or 'dal' in basename or 'query' in basename:
            return 'repository'
        if 'test' in basename:
            return 'test'
        if 'config' in basename or 'database' in basename or 'db' in basename:
            return 'config'

        if '/models/' in normalized or '/schemas/' in normalized:
            return 'model'
        if '/repositories/' in normalized or '/crud/' in normalized:
            return 'repository'

        return 'module'

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect SQLAlchemy ecosystem frameworks."""
        frameworks = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(name)
        return frameworks

    def _detect_sqlalchemy_version(self, content: str) -> str:
        """Detect minimum SQLAlchemy version required."""
        max_version = '0.0'
        for feature, version in self.SQLALCHEMY_VERSION_FEATURES.items():
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

    def is_sqlalchemy_file(self, content: str, file_path: str = "") -> bool:
        """Determine if a file is a SQLAlchemy-specific file."""
        # Direct imports
        if re.search(r'from\s+sqlalchemy[\s.]|import\s+sqlalchemy', content):
            return True
        # Common patterns
        if re.search(r'declarative_base\s*\(|DeclarativeBase|mapped_column|Column\s*\(', content):
            if re.search(r'Base\s*=|class\s+\w+\s*\(\s*(?:Base|DeclarativeBase|Model|db\.Model)', content):
                return True
        # Alembic
        if re.search(r'from\s+alembic|op\.create_table|op\.add_column', content):
            return True
        # Flask-SQLAlchemy
        if re.search(r'db\.Model|SQLAlchemy\s*\(', content):
            return True
        return False

    def to_codetrellis_format(self, result: SQLAlchemyParseResult) -> str:
        """Convert parse result to CodeTrellis compressed format."""
        lines = []

        if result.file_path:
            lines.append(f"[FILE:{Path(result.file_path).name}|type:{result.file_type}]")
        if result.detected_frameworks:
            lines.append(f"[SQLALCHEMY_ECOSYSTEM:{','.join(result.detected_frameworks)}]")
        if result.sqlalchemy_version:
            lines.append(f"[SQLALCHEMY_VERSION:>={result.sqlalchemy_version}]")
        lines.append("")

        # ORM Models (enhanced from base extractor)
        if result.models:
            lines.append("=== SQLALCHEMY_ORM_MODELS ===")
            for m in result.models:
                cols = []
                for c in m.columns[:10]:
                    flags = []
                    if c.primary_key:
                        flags.append("PK")
                    if c.foreign_key:
                        flags.append(f"FK:{c.foreign_key}")
                    if c.unique:
                        flags.append("UQ")
                    if not c.nullable:
                        flags.append("!")
                    flag_str = f"[{','.join(flags)}]" if flags else ""
                    cols.append(f"{c.name}:{c.type}{flag_str}")

                rels = []
                for r in m.relationships:
                    rel_map = {
                        RelationshipType.ONE_TO_MANY: "1:N",
                        RelationshipType.MANY_TO_ONE: "N:1",
                        RelationshipType.MANY_TO_MANY: "N:N",
                        RelationshipType.ONE_TO_ONE: "1:1",
                    }
                    rels.append(f"{r.name}->{r.target_model}({rel_map.get(r.relationship_type, 'N:1')})")

                cols_str = f"|cols:{','.join(cols)}" if cols else ""
                rels_str = f"|rels:{','.join(rels)}" if rels else ""
                lines.append(f"  {m.name}|table:{m.table_name}{cols_str}{rels_str}")
            lines.append("")

        # Core Tables
        if result.core_tables:
            lines.append("=== SQLALCHEMY_CORE_TABLES ===")
            for t in result.core_tables:
                cols = ",".join(f"{c['name']}:{c['type']}" for c in t.columns[:8])
                lines.append(f"  {t.name}|var:{t.variable_name}|cols:{cols}")
            lines.append("")

        # Engine config
        if result.engines:
            lines.append("=== SQLALCHEMY_ENGINES ===")
            for e in result.engines:
                async_str = "|async" if e.is_async else ""
                pool_str = f"|pool:{e.pool_size}" if e.pool_size else ""
                lines.append(f"  {e.variable_name}|db:{e.url_pattern}{async_str}{pool_str}")
            lines.append("")

        # Sessions
        if result.sessions:
            lines.append("=== SQLALCHEMY_SESSIONS ===")
            for s in result.sessions:
                bind_str = f"|bind:{s.bind}" if s.bind else ""
                lines.append(f"  {s.variable_name}|type:{s.session_type}{bind_str}")
            lines.append("")

        # Migrations
        if result.migrations:
            lines.append("=== SQLALCHEMY_MIGRATIONS ===")
            for m in result.migrations:
                ops_str = f"|ops:{','.join(m.operations)}" if m.operations else ""
                lines.append(f"  rev:{m.revision}|{m.message}{ops_str}")
            lines.append("")

        # Event listeners
        if result.event_listeners:
            lines.append("=== SQLALCHEMY_EVENTS ===")
            for ev in result.event_listeners:
                lines.append(f"  @{ev.target}.{ev.event_name} → {ev.handler}")
            lines.append("")

        # Hybrid properties
        if result.hybrid_properties:
            lines.append("=== SQLALCHEMY_HYBRID_PROPS ===")
            for hp in result.hybrid_properties:
                flags = []
                if hp.has_setter:
                    flags.append("setter")
                if hp.has_expression:
                    flags.append("expr")
                flag_str = f"[{','.join(flags)}]" if flags else ""
                lines.append(f"  {hp.model}.{hp.name}{flag_str}")
            lines.append("")

        return '\n'.join(lines)
