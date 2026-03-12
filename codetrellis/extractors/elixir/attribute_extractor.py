"""
Elixir Attribute Extractor for CodeTrellis

Extracts module-level attributes and directives from Elixir source code:
- Module attributes (@moduledoc, @doc, @behaviour, custom @attrs)
- use/import/alias/require directives
- Module configuration (@derive, @enforce_keys, @primary_key, @foreign_key_type)
- Compile-time attributes (@compile, @on_definition, @before_compile, @after_compile)

Part of CodeTrellis - Elixir Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ElixirModuleAttributeInfo:
    """Information about a module attribute."""
    name: str
    value: str = ""
    file: str = ""
    line_number: int = 0
    attr_type: str = "custom"  # custom, doc, config, compile, behaviour


@dataclass
class ElixirUseDirectiveInfo:
    """Information about a use/import/alias/require directive."""
    module: str
    directive: str = "use"  # use, import, alias, require
    file: str = ""
    line_number: int = 0
    options: str = ""


class ElixirAttributeExtractor:
    """Extracts module attributes and directives from Elixir source code."""

    # Module attribute patterns
    _ATTR_RE = re.compile(
        r'^\s*@(\w+)\s+(.+?)$',
        re.MULTILINE
    )

    # Directives
    _USE_RE = re.compile(
        r'^\s*use\s+([\w.]+)(?:\s*,\s*(.+))?$',
        re.MULTILINE
    )
    _IMPORT_RE = re.compile(
        r'^\s*import\s+([\w.]+)(?:\s*,\s*(.+))?$',
        re.MULTILINE
    )
    _ALIAS_RE = re.compile(
        r'^\s*alias\s+([\w.{}]+)(?:\s*,\s*as:\s*(\w+))?',
        re.MULTILINE
    )
    _REQUIRE_RE = re.compile(
        r'^\s*require\s+([\w.]+)',
        re.MULTILINE
    )

    # Known attribute categories
    _DOC_ATTRS = {"moduledoc", "doc", "typedoc"}
    _CONFIG_ATTRS = {
        "derive", "enforce_keys", "primary_key", "foreign_key_type",
        "schema_prefix", "timestamps_opts",
    }
    _COMPILE_ATTRS = {
        "compile", "on_definition", "before_compile", "after_compile",
        "on_load", "external_resource",
    }
    _BEHAVIOUR_ATTRS = {"behaviour", "behavior"}

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract all module attributes and directives."""
        attributes = self._extract_attributes(content, file_path)
        directives = self._extract_directives(content, file_path)

        return {
            "attributes": attributes,
            "directives": directives,
        }

    def _extract_attributes(self, content: str, file_path: str) -> List[ElixirModuleAttributeInfo]:
        attributes = []
        for m in self._ATTR_RE.finditer(content):
            name = m.group(1)
            value = m.group(2).strip()
            line = content[:m.start()].count('\n') + 1

            # Skip multiline doc strings — they're captured elsewhere
            if name in self._DOC_ATTRS and (value.startswith('"""') or value.startswith("~S")):
                attr_type = "doc"
                value = "(multiline)"
            elif name in self._DOC_ATTRS:
                attr_type = "doc"
            elif name in self._CONFIG_ATTRS:
                attr_type = "config"
            elif name in self._COMPILE_ATTRS:
                attr_type = "compile"
            elif name in self._BEHAVIOUR_ATTRS:
                attr_type = "behaviour"
            elif name == "impl":
                continue  # Skip @impl — tracked by function_extractor
            elif name == "spec":
                continue  # Skip @spec — tracked by type_extractor
            elif name == "type" or name == "typep" or name == "opaque":
                continue  # Skip type definitions — tracked by type_extractor
            elif name == "callback" or name == "optional_callbacks":
                continue  # Skip callbacks — tracked by type_extractor
            else:
                attr_type = "custom"

            attributes.append(ElixirModuleAttributeInfo(
                name=name,
                value=value[:120],
                file=file_path,
                line_number=line,
                attr_type=attr_type,
            ))
        return attributes

    def _extract_directives(self, content: str, file_path: str) -> List[ElixirUseDirectiveInfo]:
        directives = []

        for m in self._USE_RE.finditer(content):
            module = m.group(1)
            options = (m.group(2) or "").strip()
            line = content[:m.start()].count('\n') + 1
            directives.append(ElixirUseDirectiveInfo(
                module=module,
                directive="use",
                file=file_path,
                line_number=line,
                options=options[:100],
            ))

        for m in self._IMPORT_RE.finditer(content):
            module = m.group(1)
            options = (m.group(2) or "").strip()
            line = content[:m.start()].count('\n') + 1
            directives.append(ElixirUseDirectiveInfo(
                module=module,
                directive="import",
                file=file_path,
                line_number=line,
                options=options[:100],
            ))

        for m in self._ALIAS_RE.finditer(content):
            module = m.group(1)
            alias_as = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1
            directives.append(ElixirUseDirectiveInfo(
                module=module,
                directive="alias",
                file=file_path,
                line_number=line,
                options=f"as: {alias_as}" if alias_as else "",
            ))

        for m in self._REQUIRE_RE.finditer(content):
            module = m.group(1)
            line = content[:m.start()].count('\n') + 1
            directives.append(ElixirUseDirectiveInfo(
                module=module,
                directive="require",
                file=file_path,
                line_number=line,
            ))

        return directives
