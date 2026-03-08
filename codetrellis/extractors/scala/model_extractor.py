"""
ScalaModelExtractor - Extracts Scala database models, migrations, and ORM patterns.

This extractor parses Scala source code and extracts:
- Slick table definitions (TableQuery, Table, column, schema)
- Doobie queries (sql interpolator, Query0, Update0, ConnectionIO)
- Quill queries (quote, query, run)
- Skunk queries (sql interpolator, Query, Command)
- ScalikeJDBC models (SQLSyntaxSupport, NamedDB)
- Play Evolutions / Flyway migrations
- Circe / Play JSON / Spray JSON codecs
- Protobuf message definitions (ScalaPB)
- Avro schema definitions

Supports Slick 3.x, Doobie 1.x, Quill, Skunk, ScalikeJDBC.

Part of CodeTrellis v4.25 - Scala Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ScalaColumnInfo:
    """Information about a database column in a Scala model."""
    name: str
    scala_type: str = ""
    db_type: Optional[str] = None
    is_primary_key: bool = False
    is_auto_inc: bool = False
    is_nullable: bool = False
    is_unique: bool = False
    is_indexed: bool = False
    default_value: Optional[str] = None


@dataclass
class ScalaModelInfo:
    """Information about a Scala ORM model / table definition."""
    name: str
    table_name: Optional[str] = None
    orm: str = "slick"  # slick, doobie, quill, skunk, scalikejdbc, anorm
    columns: List[ScalaColumnInfo] = field(default_factory=list)
    primary_key: Optional[str] = None
    foreign_keys: List[Dict[str, str]] = field(default_factory=list)
    indexes: List[Dict[str, Any]] = field(default_factory=list)
    case_class: Optional[str] = None  # Associated case class name
    file: str = ""
    line_number: int = 0
    is_view: bool = False
    schema: Optional[str] = None
    queries: List[str] = field(default_factory=list)  # Named queries


@dataclass
class ScalaMigrationInfo:
    """Information about a Scala database migration."""
    name: str
    version: Optional[str] = None
    framework: str = "evolutions"  # evolutions, flyway, liquibase
    operations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    direction: str = "up"  # up, down


@dataclass
class ScalaCodecInfo:
    """Information about a Scala serialization codec."""
    name: str
    target_type: str = ""
    framework: str = "circe"  # circe, play_json, spray_json, upickle, jsoniter, protobuf, avro
    kind: str = "codec"  # codec, encoder, decoder, format, reads, writes
    is_auto_derived: bool = False
    file: str = ""
    line_number: int = 0


class ScalaModelExtractor:
    """
    Extracts Scala model and database definitions from source code.

    Handles:
    - Slick table/column definitions and TableQuery
    - Doobie SQL queries and transactors
    - Quill quoted queries
    - Skunk SQL queries
    - ScalikeJDBC syntax support
    - Anorm SQL parsing
    - Play Evolutions migrations
    - Flyway migrations
    - JSON codecs (Circe, Play JSON, Spray JSON, uPickle, jsoniter-scala)
    - Binary codecs (Protobuf/ScalaPB, Avro)
    """

    # ── Slick ───────────────────────────────────────────────────
    SLICK_TABLE_PATTERN = re.compile(
        r'class\s+(?P<name>\w+)\s*\(\s*tag\s*:\s*Tag\s*\)\s+'
        r'extends\s+Table\[(?P<type>\w+)\]\s*\(\s*tag\s*,\s*["\'](?P<table>[^"\']+)["\']\s*\)',
        re.MULTILINE
    )

    SLICK_COLUMN_PATTERN = re.compile(
        r'def\s+(?P<name>\w+)\s*=\s*column\[(?P<type>[^\]]+)\]\s*\(\s*["\'](?P<db_name>[^"\']+)["\']\s*'
        r'(?P<options>[^)]*)\)',
        re.MULTILINE
    )

    SLICK_TABLEQUERY_PATTERN = re.compile(
        r'(?:val|lazy\s+val)\s+(?P<name>\w+)\s*=\s*TableQuery\[(?P<table>\w+)\]',
        re.MULTILINE
    )

    SLICK_FK_PATTERN = re.compile(
        r'def\s+(?P<name>\w+)\s*=\s*foreignKey\s*\(\s*["\'](?P<fk_name>[^"\']+)["\']\s*,\s*'
        r'(?P<source>\w+)\s*,\s*(?P<target>\w+)\s*\)',
        re.MULTILINE
    )

    SLICK_INDEX_PATTERN = re.compile(
        r'def\s+(?P<name>\w+)\s*=\s*index\s*\(\s*["\'](?P<idx_name>[^"\']+)["\']\s*,\s*'
        r'(?P<columns>[^,)]+)(?:\s*,\s*unique\s*=\s*(?P<unique>true|false))?',
        re.MULTILINE
    )

    # ── Doobie ──────────────────────────────────────────────────
    DOOBIE_QUERY_PATTERN = re.compile(
        r'(?:sql|fr)\s*["\'](?P<query>[^"\']+)["\'].*?\.query\[(?P<type>\w+)\]',
        re.MULTILINE | re.DOTALL
    )

    DOOBIE_UPDATE_PATTERN = re.compile(
        r'(?:sql|fr)\s*["\'](?P<query>[^"\']+)["\'].*?\.update',
        re.MULTILINE | re.DOTALL
    )

    # ── Quill ───────────────────────────────────────────────────
    QUILL_QUERY_PATTERN = re.compile(
        r'quote\s*\{\s*query\[(?P<type>\w+)\]',
        re.MULTILINE
    )

    QUILL_SCHEMA_PATTERN = re.compile(
        r'querySchema\[(?P<type>\w+)\]\s*\(\s*["\'](?P<table>[^"\']+)["\']',
        re.MULTILINE
    )

    # ── Skunk ───────────────────────────────────────────────────
    SKUNK_QUERY_PATTERN = re.compile(
        r'sql\s*["\'](?P<query>[^"\']+)["\']\s*\.query(?:\((?P<codec>[^)]+)\))?',
        re.MULTILINE
    )

    SKUNK_COMMAND_PATTERN = re.compile(
        r'sql\s*["\'](?P<query>[^"\']+)["\']\s*\.command',
        re.MULTILINE
    )

    # ── ScalikeJDBC ─────────────────────────────────────────────
    SCALIKEJDBC_PATTERN = re.compile(
        r'object\s+(?P<name>\w+)\s+extends\s+SQLSyntaxSupport\[(?P<type>\w+)\]',
        re.MULTILINE
    )

    # ── Migrations ──────────────────────────────────────────────
    EVOLUTION_PATTERN = re.compile(
        r'#\s*---\s*!(?P<direction>Ups|Downs)',
        re.MULTILINE
    )

    FLYWAY_PATTERN = re.compile(
        r'class\s+(?P<name>V\d+__\w+)\s+extends\s+(?:BaseJavaMigration|JdbcMigration)',
        re.MULTILINE
    )

    # ── JSON Codecs ─────────────────────────────────────────────
    # Circe
    CIRCE_DERIVE_PATTERN = re.compile(
        r'(?:derives|deriving)\s+(?:Codec|Encoder|Decoder)(?:\.AsObject)?',
        re.MULTILINE
    )

    CIRCE_IMPLICIT_PATTERN = re.compile(
        r'implicit\s+(?:val|def|lazy\s+val)\s+(?P<name>\w+)\s*[=:]\s*'
        r'(?:Encoder|Decoder|Codec)(?:\.AsObject)?\[(?P<type>\w+)\]',
        re.MULTILINE
    )

    CIRCE_SEMI_AUTO_PATTERN = re.compile(
        r'(?:deriveEncoder|deriveDecoder|deriveCodec)\[(?P<type>\w+)\]',
        re.MULTILINE
    )

    # Play JSON
    PLAY_JSON_FORMAT_PATTERN = re.compile(
        r'implicit\s+(?:val|def|lazy\s+val)\s+(?P<name>\w+)\s*[=:]\s*'
        r'(?:Json\.format|Json\.reads|Json\.writes|Format|Reads|Writes)\[(?P<type>\w+)\]',
        re.MULTILINE
    )

    PLAY_JSON_MACRO_PATTERN = re.compile(
        r'Json\.(?:format|reads|writes)\[(?P<type>\w+)\]',
        re.MULTILINE
    )

    # Spray JSON
    SPRAY_JSON_PATTERN = re.compile(
        r'(?:jsonFormat\d+|DefaultJsonProtocol)\s*(?:\[(?P<type>\w+)\])?',
        re.MULTILINE
    )

    # uPickle
    UPICKLE_PATTERN = re.compile(
        r'implicit\s+(?:val|def)\s+(?P<name>\w+)\s*[=:]\s*'
        r'(?:ReadWriter|Reader|Writer)\[(?P<type>\w+)\]',
        re.MULTILINE
    )

    # Protobuf (ScalaPB generated)
    PROTOBUF_MESSAGE_PATTERN = re.compile(
        r'final\s+case\s+class\s+(?P<name>\w+)\s*\('
        r'[^)]*\)\s+extends\s+(?:scalapb\.)?GeneratedMessage',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the Scala model extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all model/database definitions from Scala source code.

        Args:
            content: Scala source code
            file_path: Path to the source file

        Returns:
            Dictionary with keys: models, migrations, codecs
        """
        result = {
            'models': [],
            'migrations': [],
            'codecs': [],
        }

        result['models'] = self._extract_models(content, file_path)
        result['migrations'] = self._extract_migrations(content, file_path)
        result['codecs'] = self._extract_codecs(content, file_path)

        return result

    def _extract_models(self, content: str, file_path: str) -> List[ScalaModelInfo]:
        """Extract database model definitions."""
        models = []

        # ── Slick Tables ──
        for match in self.SLICK_TABLE_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            case_class_name = match.group('type')
            table_name = match.group('table')

            # Extract columns from the table class body
            body_start = match.end()
            body = self._extract_class_body(content, body_start)
            columns = []
            foreign_keys = []
            indexes = []
            pk = None

            if body:
                for col_match in self.SLICK_COLUMN_PATTERN.finditer(body):
                    options = col_match.group('options') or ''
                    col = ScalaColumnInfo(
                        name=col_match.group('name'),
                        scala_type=col_match.group('type'),
                        db_type=col_match.group('db_name'),
                        is_primary_key='PrimaryKey' in options or 'O.PrimaryKey' in options,
                        is_auto_inc='AutoInc' in options or 'O.AutoInc' in options,
                        is_nullable='Option[' in col_match.group('type'),
                        is_unique='Unique' in options or 'O.Unique' in options,
                    )
                    columns.append(col)
                    if col.is_primary_key:
                        pk = col.name

                for fk_match in self.SLICK_FK_PATTERN.finditer(body):
                    foreign_keys.append({
                        'name': fk_match.group('fk_name'),
                        'source': fk_match.group('source'),
                        'target': fk_match.group('target'),
                    })

                for idx_match in self.SLICK_INDEX_PATTERN.finditer(body):
                    indexes.append({
                        'name': idx_match.group('idx_name'),
                        'columns': idx_match.group('columns').strip(),
                        'unique': idx_match.group('unique') == 'true' if idx_match.group('unique') else False,
                    })

            model = ScalaModelInfo(
                name=name,
                table_name=table_name,
                orm='slick',
                columns=columns,
                primary_key=pk,
                foreign_keys=foreign_keys,
                indexes=indexes,
                case_class=case_class_name,
                file=file_path,
                line_number=line_number,
            )
            models.append(model)

        # ── Quill Schema ──
        for match in self.QUILL_SCHEMA_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            model = ScalaModelInfo(
                name=match.group('type'),
                table_name=match.group('table'),
                orm='quill',
                case_class=match.group('type'),
                file=file_path,
                line_number=line_number,
            )
            models.append(model)

        # ── ScalikeJDBC ──
        for match in self.SCALIKEJDBC_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            model = ScalaModelInfo(
                name=match.group('name'),
                orm='scalikejdbc',
                case_class=match.group('type'),
                file=file_path,
                line_number=line_number,
            )
            models.append(model)

        return models

    def _extract_migrations(self, content: str, file_path: str) -> List[ScalaMigrationInfo]:
        """Extract database migration definitions."""
        migrations = []

        # Play Evolutions
        if file_path.endswith('.sql') and 'evolutions' in file_path:
            version_match = re.search(r'/(\d+)\.sql$', file_path)
            version = version_match.group(1) if version_match else None

            for match in self.EVOLUTION_PATTERN.finditer(content):
                line_number = content[:match.start()].count('\n') + 1
                direction = 'up' if match.group('direction') == 'Ups' else 'down'

                migration = ScalaMigrationInfo(
                    name=f"Evolution_{version}" if version else "Evolution",
                    version=version,
                    framework='evolutions',
                    direction=direction,
                    file=file_path,
                    line_number=line_number,
                )
                migrations.append(migration)

        # Flyway
        for match in self.FLYWAY_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            version_match = re.search(r'V(\d+)__', name)
            version = version_match.group(1) if version_match else None

            migration = ScalaMigrationInfo(
                name=name,
                version=version,
                framework='flyway',
                file=file_path,
                line_number=line_number,
            )
            migrations.append(migration)

        return migrations

    def _extract_codecs(self, content: str, file_path: str) -> List[ScalaCodecInfo]:
        """Extract serialization codec definitions."""
        codecs = []

        # ── Circe ──
        for match in self.CIRCE_IMPLICIT_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            target_type = match.group('type')

            kind = 'codec'
            if 'Encoder' in content[match.start():match.end()]:
                kind = 'encoder'
            elif 'Decoder' in content[match.start():match.end()]:
                kind = 'decoder'

            codecs.append(ScalaCodecInfo(
                name=name,
                target_type=target_type,
                framework='circe',
                kind=kind,
                file=file_path,
                line_number=line_number,
            ))

        for match in self.CIRCE_SEMI_AUTO_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            target_type = match.group('type')
            kind = 'codec'
            context = content[max(0, match.start() - 20):match.start()]
            if 'Encoder' in context or 'deriveEncoder' in match.group(0):
                kind = 'encoder'
            elif 'Decoder' in context or 'deriveDecoder' in match.group(0):
                kind = 'decoder'

            codecs.append(ScalaCodecInfo(
                name=f"{target_type}_{kind}",
                target_type=target_type,
                framework='circe',
                kind=kind,
                is_auto_derived=True,
                file=file_path,
                line_number=line_number,
            ))

        # ── Play JSON ──
        for match in self.PLAY_JSON_FORMAT_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            target_type = match.group('type')
            kind = 'format'
            segment = content[match.start():match.end()]
            if 'Reads' in segment or 'reads' in segment:
                kind = 'reads'
            elif 'Writes' in segment or 'writes' in segment:
                kind = 'writes'

            codecs.append(ScalaCodecInfo(
                name=name,
                target_type=target_type,
                framework='play_json',
                kind=kind,
                file=file_path,
                line_number=line_number,
            ))

        for match in self.PLAY_JSON_MACRO_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            target_type = match.group('type')
            segment = match.group(0)
            kind = 'format'
            if 'reads' in segment:
                kind = 'reads'
            elif 'writes' in segment:
                kind = 'writes'

            codecs.append(ScalaCodecInfo(
                name=f"{target_type}_{kind}",
                target_type=target_type,
                framework='play_json',
                kind=kind,
                is_auto_derived=True,
                file=file_path,
                line_number=line_number,
            ))

        # ── Spray JSON ──
        for match in self.SPRAY_JSON_PATTERN.finditer(content):
            if match.group('type'):
                line_number = content[:match.start()].count('\n') + 1
                target_type = match.group('type')
                codecs.append(ScalaCodecInfo(
                    name=f"{target_type}_format",
                    target_type=target_type,
                    framework='spray_json',
                    kind='format',
                    file=file_path,
                    line_number=line_number,
                ))

        # ── uPickle ──
        for match in self.UPICKLE_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            target_type = match.group('type')
            kind = 'codec'
            segment = content[match.start():match.end()]
            if 'Reader' in segment and 'Writer' not in segment:
                kind = 'reader'
            elif 'Writer' in segment and 'Reader' not in segment:
                kind = 'writer'

            codecs.append(ScalaCodecInfo(
                name=name,
                target_type=target_type,
                framework='upickle',
                kind=kind,
                file=file_path,
                line_number=line_number,
            ))

        # ── Protobuf (ScalaPB) ──
        for match in self.PROTOBUF_MESSAGE_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            name = match.group('name')
            codecs.append(ScalaCodecInfo(
                name=name,
                target_type=name,
                framework='protobuf',
                kind='codec',
                is_auto_derived=True,
                file=file_path,
                line_number=line_number,
            ))

        return codecs

    def _extract_class_body(self, content: str, start_pos: int) -> Optional[str]:
        """Extract the body of a class/object definition."""
        idx = start_pos
        while idx < len(content) and content[idx] != '{':
            if content[idx] == '\n':
                return None
            idx += 1

        if idx >= len(content):
            return None

        depth = 1
        start = idx + 1
        idx += 1
        in_string = False
        string_char = None

        while idx < len(content) and depth > 0:
            ch = content[idx]
            if in_string:
                if ch == '\\':
                    idx += 1
                elif ch == string_char:
                    in_string = False
            else:
                if ch in ('"', '\''):
                    in_string = True
                    string_char = ch
                elif ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
            idx += 1

        if depth == 0:
            return content[start:idx - 1]
        return None
