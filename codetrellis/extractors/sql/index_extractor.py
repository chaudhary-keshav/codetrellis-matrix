"""
SQLIndexExtractor - Extracts SQL indexes, constraints, partitions, and foreign keys.

This extractor parses SQL source code and extracts:
- CREATE INDEX / CREATE UNIQUE INDEX
- Composite indexes, partial indexes (WHERE clause), covering indexes (INCLUDE)
- Expression indexes (PostgreSQL, MySQL 8+)
- Full-text indexes (PostgreSQL GIN/GiST, MySQL FULLTEXT, SQL Server)
- Spatial indexes (PostgreSQL GiST, MySQL SPATIAL, SQL Server GEOGRAPHY/GEOMETRY)
- Clustered / Non-clustered indexes (SQL Server)
- Bitmap indexes (Oracle)
- Partition definitions (PARTITION BY RANGE/LIST/HASH)
- Foreign key relationships with ON DELETE/UPDATE actions

Supported SQL dialects:
- PostgreSQL: CONCURRENTLY, USING (btree/hash/gin/gist/brin), INCLUDE, WHERE
- MySQL: FULLTEXT, SPATIAL, VISIBLE/INVISIBLE, index hints
- SQL Server: CLUSTERED/NONCLUSTERED, INCLUDE, FILLFACTOR, ONLINE
- Oracle: BITMAP, GLOBAL/LOCAL, COMPUTE STATISTICS
- SQLite: basic CREATE INDEX support

Part of CodeTrellis v4.15 - SQL Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SQLIndexInfo:
    """Information about a SQL index."""
    name: str
    table_name: str
    schema_name: str = ""
    columns: List[str] = field(default_factory=list)
    include_columns: List[str] = field(default_factory=list)  # INCLUDE (covering index)
    is_unique: bool = False
    is_primary: bool = False
    is_clustered: bool = False         # SQL Server CLUSTERED
    is_nonclustered: bool = False      # SQL Server NONCLUSTERED
    is_concurrent: bool = False        # PostgreSQL CONCURRENTLY
    is_bitmap: bool = False            # Oracle BITMAP
    is_fulltext: bool = False          # MySQL FULLTEXT / PG GIN
    is_spatial: bool = False           # MySQL SPATIAL / PG GiST
    method: str = ""                   # btree, hash, gin, gist, brin, spgist
    where_clause: Optional[str] = None  # Partial index condition
    expression: Optional[str] = None   # Expression index
    tablespace: str = ""
    fillfactor: Optional[int] = None   # SQL Server / PostgreSQL
    dialect: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SQLConstraintInfo:
    """Information about a table constraint (extracted from ALTER TABLE)."""
    name: str
    table_name: str
    schema_name: str = ""
    kind: str = ""                     # PRIMARY KEY, UNIQUE, CHECK, EXCLUDE
    columns: List[str] = field(default_factory=list)
    expression: Optional[str] = None   # CHECK/EXCLUDE expression
    deferrable: bool = False
    initially_deferred: bool = False
    dialect: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SQLPartitionInfo:
    """Information about a table partition definition."""
    table_name: str
    schema_name: str = ""
    strategy: str = ""                 # RANGE, LIST, HASH, KEY
    columns: List[str] = field(default_factory=list)
    sub_partitions: List[Dict[str, Any]] = field(default_factory=list)
    partition_count: int = 0
    dialect: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SQLForeignKeyInfo:
    """Information about a foreign key relationship."""
    name: str
    table_name: str
    schema_name: str = ""
    columns: List[str] = field(default_factory=list)
    ref_table: str = ""
    ref_schema: str = ""
    ref_columns: List[str] = field(default_factory=list)
    on_delete: str = ""                # CASCADE, SET NULL, RESTRICT, NO ACTION
    on_update: str = ""
    is_deferrable: bool = False
    dialect: str = ""
    file: str = ""
    line_number: int = 0


class SQLIndexExtractor:
    """
    Extracts SQL index, constraint, partition, and foreign key definitions.

    v4.15: Comprehensive index extraction across all dialects.
    """

    CREATE_INDEX = re.compile(
        r'CREATE\s+'
        r'(?P<unique>UNIQUE\s+)?'
        r'(?P<fulltext>FULLTEXT\s+)?'
        r'(?P<spatial>SPATIAL\s+)?'
        r'(?P<bitmap>BITMAP\s+)?'
        r'(?P<clustered>(?:CLUSTERED|NONCLUSTERED)\s+)?'
        r'INDEX\s+'
        r'(?P<concurrent>CONCURRENTLY\s+)?'
        r'(?:IF\s+NOT\s+EXISTS\s+)?'
        r'(?P<name>[\w"`.]+)\s+'
        r'ON\s+(?P<schema>[\w"`.]+\.)?(?P<table>[\w"`.]+)\s*'
        r'(?:USING\s+(?P<method>\w+)\s*)?'
        r'\(\s*(?P<columns>[^)]+)\s*\)'
        r'(?:\s+INCLUDE\s*\(\s*(?P<include>[^)]+)\s*\))?'
        r'(?:\s+WHERE\s+(?P<where>.+?))?'
        r'(?:\s+(?:WITH|TABLESPACE|FILLFACTOR)\s+[^;]+)?'
        r'\s*;?',
        re.IGNORECASE | re.DOTALL
    )

    ALTER_ADD_CONSTRAINT = re.compile(
        r'ALTER\s+TABLE\s+'
        r'(?:IF\s+EXISTS\s+)?(?:ONLY\s+)?'
        r'(?P<schema>[\w"`.]+\.)?(?P<table>[\w"`.]+)\s+'
        r'ADD\s+(?:CONSTRAINT\s+(?P<name>[\w"`.]+)\s+)?'
        r'(?P<kind>PRIMARY\s+KEY|UNIQUE|CHECK|EXCLUDE|FOREIGN\s+KEY)\s*'
        r'(?:\(\s*(?P<columns>[^)]+)\s*\))?'
        r'(?:\s+(?P<rest>.+?))?;',
        re.IGNORECASE | re.DOTALL
    )

    ALTER_ADD_FK = re.compile(
        r'ALTER\s+TABLE\s+'
        r'(?:IF\s+EXISTS\s+)?(?:ONLY\s+)?'
        r'(?P<schema>[\w"`.]+\.)?(?P<table>[\w"`.]+)\s+'
        r'ADD\s+(?:CONSTRAINT\s+(?P<name>[\w"`.]+)\s+)?'
        r'FOREIGN\s+KEY\s*\(\s*(?P<columns>[^)]+)\s*\)\s*'
        r'REFERENCES\s+(?P<ref_schema>[\w"`.]+\.)?(?P<ref_table>[\w"`.]+)\s*'
        r'\(\s*(?P<ref_columns>[^)]+)\s*\)'
        r'(?:\s+ON\s+DELETE\s+(?P<on_delete>\w+(?:\s+\w+)?))?'
        r'(?:\s+ON\s+UPDATE\s+(?P<on_update>\w+(?:\s+\w+)?))?',
        re.IGNORECASE | re.DOTALL
    )

    PARTITION_BY = re.compile(
        r'(?:CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<schema>[\w"`.]+\.)?(?P<table>[\w"`.]+)\s*'
        r'\([^)]*\)\s*)?'
        r'PARTITION\s+BY\s+(?P<strategy>RANGE|LIST|HASH|KEY)\s*'
        r'\(\s*(?P<columns>[^)]+)\s*\)',
        re.IGNORECASE | re.DOTALL
    )

    CREATE_PARTITION = re.compile(
        r'CREATE\s+TABLE\s+(?P<name>[\w"`.]+)\s+'
        r'PARTITION\s+OF\s+(?P<parent>[\w"`.]+)\s+'
        r'(?:FOR\s+VALUES\s+(?P<kind>FROM|IN|WITH)\s*(?:\((?P<values>[^)]+)\))?)?',
        re.IGNORECASE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all index, constraint, partition, and FK definitions.

        Returns:
            Dict with keys: indexes, constraints, partitions, foreign_keys
        """
        indexes = self._extract_indexes(content, file_path)
        constraints = self._extract_constraints(content, file_path)
        partitions = self._extract_partitions(content, file_path)
        foreign_keys = self._extract_foreign_keys(content, file_path)

        return {
            'indexes': indexes,
            'constraints': constraints,
            'partitions': partitions,
            'foreign_keys': foreign_keys,
        }

    def _extract_indexes(self, content: str, file_path: str) -> List[SQLIndexInfo]:
        """Extract CREATE INDEX statements."""
        indexes = []
        for m in self.CREATE_INDEX.finditer(content):
            name = self._clean_name(m.group('name'))
            table = self._clean_name(m.group('table'))
            schema = self._clean_name(m.group('schema') or '')

            idx = SQLIndexInfo(
                name=name,
                table_name=table,
                schema_name=schema,
                columns=[c.strip().strip('"').strip('`') for c in m.group('columns').split(',')],
                is_unique=bool(m.group('unique')),
                is_fulltext=bool(m.group('fulltext')),
                is_spatial=bool(m.group('spatial')),
                is_bitmap=bool(m.group('bitmap')),
                is_concurrent=bool(m.group('concurrent')),
                method=m.group('method') or 'btree',
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )

            if m.group('include'):
                idx.include_columns = [c.strip() for c in m.group('include').split(',')]
            if m.group('where'):
                idx.where_clause = m.group('where').strip()

            # Clustered
            clustered = m.group('clustered') or ''
            if 'CLUSTERED' in clustered.upper() and 'NON' not in clustered.upper():
                idx.is_clustered = True
            if 'NONCLUSTERED' in clustered.upper():
                idx.is_nonclustered = True

            # FILLFACTOR
            ff_match = re.search(r'FILLFACTOR\s*=?\s*(\d+)', content[m.start():m.end()+200], re.IGNORECASE)
            if ff_match:
                idx.fillfactor = int(ff_match.group(1))

            indexes.append(idx)
        return indexes

    def _extract_constraints(self, content: str, file_path: str) -> List[SQLConstraintInfo]:
        """Extract ALTER TABLE ADD CONSTRAINT statements."""
        constraints = []
        for m in self.ALTER_ADD_CONSTRAINT.finditer(content):
            kind_raw = m.group('kind').upper()
            if 'FOREIGN' in kind_raw:
                continue  # Handled by FK extractor

            name = self._clean_name(m.group('name') or '')
            table = self._clean_name(m.group('table'))
            schema = self._clean_name(m.group('schema') or '')
            columns = [c.strip() for c in (m.group('columns') or '').split(',')]

            constraint = SQLConstraintInfo(
                name=name,
                table_name=table,
                schema_name=schema,
                kind=kind_raw.strip(),
                columns=columns if m.group('columns') else [],
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )

            rest = m.group('rest') or ''
            if 'CHECK' in kind_raw:
                check_match = re.search(r'\((.+)\)', rest, re.DOTALL)
                if check_match:
                    constraint.expression = check_match.group(1).strip()

            if re.search(r'DEFERRABLE', rest, re.IGNORECASE):
                constraint.deferrable = True
            if re.search(r'INITIALLY\s+DEFERRED', rest, re.IGNORECASE):
                constraint.initially_deferred = True

            constraints.append(constraint)
        return constraints

    def _extract_partitions(self, content: str, file_path: str) -> List[SQLPartitionInfo]:
        """Extract PARTITION BY definitions."""
        partitions = []
        for m in self.PARTITION_BY.finditer(content):
            table = self._clean_name(m.group('table') or '')
            schema = self._clean_name(m.group('schema') or '')

            part = SQLPartitionInfo(
                table_name=table,
                schema_name=schema,
                strategy=m.group('strategy').upper(),
                columns=[c.strip() for c in m.group('columns').split(',')],
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )

            # Count sub-partitions
            sub_pattern = re.compile(
                r'PARTITION\s+(\w+)\s+VALUES',
                re.IGNORECASE
            )
            for sm in sub_pattern.finditer(content[m.end():m.end()+2000]):
                part.sub_partitions.append({'name': sm.group(1)})
            part.partition_count = len(part.sub_partitions)

            partitions.append(part)
        return partitions

    def _extract_foreign_keys(self, content: str, file_path: str) -> List[SQLForeignKeyInfo]:
        """Extract foreign key relationships from ALTER TABLE."""
        fks = []
        for m in self.ALTER_ADD_FK.finditer(content):
            name = self._clean_name(m.group('name') or '')
            table = self._clean_name(m.group('table'))
            schema = self._clean_name(m.group('schema') or '')

            fk = SQLForeignKeyInfo(
                name=name,
                table_name=table,
                schema_name=schema,
                columns=[c.strip() for c in m.group('columns').split(',')],
                ref_table=self._clean_name(m.group('ref_table')),
                ref_schema=self._clean_name(m.group('ref_schema') or ''),
                ref_columns=[c.strip() for c in m.group('ref_columns').split(',')],
                on_delete=(m.group('on_delete') or '').upper(),
                on_update=(m.group('on_update') or '').upper(),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )
            fks.append(fk)
        return fks

    def _clean_name(self, name: str) -> str:
        if not name:
            return name
        return name.strip().strip('"').strip('`').strip('[').strip(']').strip('.')
