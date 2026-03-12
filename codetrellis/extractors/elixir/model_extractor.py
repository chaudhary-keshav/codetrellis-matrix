"""
Elixir Model Extractor for CodeTrellis

Extracts data model constructs from Elixir source code:
- Ecto-like schema definitions (embedded_schema, schema)
- Changeset patterns
- GenServer state shapes
- Agent state
- ETS table definitions

Part of CodeTrellis - Elixir Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ElixirSchemaFieldInfo:
    """Information about a schema field."""
    name: str
    field_type: str = "field"  # field, belongs_to, has_one, has_many, many_to_many, embeds_one, embeds_many, timestamps
    data_type: str = ""
    line_number: int = 0


@dataclass
class ElixirSchemaInfo:
    """Information about a schema definition."""
    name: str
    table: str = ""
    file: str = ""
    line_number: int = 0
    fields: List[ElixirSchemaFieldInfo] = field(default_factory=list)
    schema_type: str = "schema"  # schema, embedded_schema


@dataclass
class ElixirChangesetInfo:
    """Information about a changeset function."""
    name: str
    file: str = ""
    line_number: int = 0
    cast_fields: List[str] = field(default_factory=list)
    validate_fields: List[str] = field(default_factory=list)


@dataclass
class ElixirGenServerStateInfo:
    """Information about GenServer state shape (from init)."""
    module: str
    file: str = ""
    line_number: int = 0
    state_type: str = ""  # map, struct, tuple, list, keyword


class ElixirModelExtractor:
    """Extracts data model constructs from Elixir source code."""

    # Schema patterns
    _SCHEMA_RE = re.compile(
        r'^\s*(?:schema|embedded_schema)\s+"?(\w*)"?\s+do\b',
        re.MULTILINE
    )

    # Field patterns inside schema blocks
    _FIELD_RE = re.compile(
        r'^\s*(field|belongs_to|has_one|has_many|many_to_many|embeds_one|embeds_many|timestamps)\s+:(\w+)(?:\s*,\s*:?(\w[\w.]*))?',
        re.MULTILINE
    )

    # Changeset patterns
    _CHANGESET_RE = re.compile(
        r'^\s*def\s+(\w*changeset\w*)\s*\(',
        re.MULTILINE
    )

    # cast/validate_required patterns
    _CAST_RE = re.compile(
        r'\|>\s*cast\(\s*(?:\w+,\s*)?\[([^\]]*)\]',
        re.MULTILINE
    )

    _VALIDATE_REQUIRED_RE = re.compile(
        r'\|>\s*validate_required\(\s*\[([^\]]*)\]',
        re.MULTILINE
    )

    # GenServer init patterns to detect state shape
    _GENSERVER_INIT_RE = re.compile(
        r'def\s+init\(.*?\)\s+do\b',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract all model constructs."""
        schemas = self._extract_schemas(content, file_path)
        changesets = self._extract_changesets(content, file_path)
        genserver_states = self._extract_genserver_states(content, file_path)

        return {
            "schemas": schemas,
            "changesets": changesets,
            "genserver_states": genserver_states,
        }

    def _extract_schemas(self, content: str, file_path: str) -> List[ElixirSchemaInfo]:
        schemas = []
        for m in self._SCHEMA_RE.finditer(content):
            table = m.group(1) or ""
            line = content[:m.start()].count('\n') + 1
            schema_type = "embedded_schema" if "embedded_schema" in m.group() else "schema"

            # Determine module name from preceding defmodule
            module_name = self._find_enclosing_module(content, m.start())

            # Extract fields within the schema block
            start = m.end()
            block = self._extract_block(content, start)
            fields = self._extract_fields(block, line)

            schemas.append(ElixirSchemaInfo(
                name=module_name,
                table=table,
                file=file_path,
                line_number=line,
                fields=fields[:50],
                schema_type=schema_type,
            ))
        return schemas

    def _extract_fields(self, block: str, base_line: int) -> List[ElixirSchemaFieldInfo]:
        fields = []
        for m in self._FIELD_RE.finditer(block):
            field_type = m.group(1)
            name = m.group(2)
            data_type = m.group(3) or ""
            line = base_line + block[:m.start()].count('\n')

            if field_type == "timestamps":
                # timestamps doesn't have a name; name here is first arg pattern
                fields.append(ElixirSchemaFieldInfo(
                    name="inserted_at",
                    field_type="timestamps",
                    data_type="naive_datetime",
                    line_number=line,
                ))
                fields.append(ElixirSchemaFieldInfo(
                    name="updated_at",
                    field_type="timestamps",
                    data_type="naive_datetime",
                    line_number=line,
                ))
            else:
                fields.append(ElixirSchemaFieldInfo(
                    name=name,
                    field_type=field_type,
                    data_type=data_type,
                    line_number=line,
                ))
        return fields

    def _extract_changesets(self, content: str, file_path: str) -> List[ElixirChangesetInfo]:
        changesets = []
        for m in self._CHANGESET_RE.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            # Look for cast and validate_required in the function body
            func_block = self._extract_block(content, m.end())

            cast_fields = []
            cast_m = self._CAST_RE.search(func_block)
            if cast_m:
                cast_fields = [f.strip().lstrip(':') for f in cast_m.group(1).split(',') if f.strip()]

            validate_fields = []
            val_m = self._VALIDATE_REQUIRED_RE.search(func_block)
            if val_m:
                validate_fields = [f.strip().lstrip(':') for f in val_m.group(1).split(',') if f.strip()]

            changesets.append(ElixirChangesetInfo(
                name=name,
                file=file_path,
                line_number=line,
                cast_fields=cast_fields[:30],
                validate_fields=validate_fields[:30],
            ))
        return changesets

    def _extract_genserver_states(self, content: str, file_path: str) -> List[ElixirGenServerStateInfo]:
        states = []
        for m in self._GENSERVER_INIT_RE.finditer(content):
            line = content[:m.start()].count('\n') + 1
            module_name = self._find_enclosing_module(content, m.start())

            # Simple heuristic: look at {:ok, ...} return to guess state type
            func_block = self._extract_block(content, m.end())
            state_type = "unknown"
            if '%{' in func_block or '%__MODULE__{' in func_block:
                state_type = "map"
            elif re.search(r'%\w+\{', func_block):
                state_type = "struct"
            elif '{:ok, {' in func_block:
                state_type = "tuple"
            elif '{:ok, [' in func_block:
                state_type = "list"

            states.append(ElixirGenServerStateInfo(
                module=module_name,
                file=file_path,
                line_number=line,
                state_type=state_type,
            ))
        return states

    def _find_enclosing_module(self, content: str, pos: int) -> str:
        """Find the nearest enclosing defmodule name."""
        prefix = content[:pos]
        modules = re.findall(r'defmodule\s+([\w.]+)\s+do', prefix)
        return modules[-1] if modules else "Unknown"

    def _extract_block(self, content: str, start: int) -> str:
        """Extract content up to matching end keyword."""
        depth = 1
        pos = start
        while pos < len(content) and depth > 0:
            # Check for block keywords
            rest = content[pos:]
            if re.match(r'\b(do|fn)\b', rest):
                depth += 1
                pos += 2
            elif re.match(r'\bend\b', rest):
                depth -= 1
                if depth == 0:
                    return content[start:pos]
                pos += 3
            else:
                pos += 1
        return content[start:min(start + 500, len(content))]
