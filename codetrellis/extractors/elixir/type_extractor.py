"""
Elixir Type Extractor for CodeTrellis

Extracts type-level constructs from Elixir source code:
- Modules (defmodule)
- Structs (defstruct)
- Protocols (defprotocol) and implementations (defimpl)
- Behaviours (@behaviour/@callback)
- Typespecs (@type, @typep, @opaque, @spec)
- Exceptions (defexception)

Supports Elixir 1.0 through 1.17+.

Part of CodeTrellis - Elixir Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ElixirModuleInfo:
    """Information about an Elixir module."""
    name: str
    file: str = ""
    line_number: int = 0
    is_nested: bool = False
    parent_module: str = ""
    uses: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    requires: List[str] = field(default_factory=list)
    behaviours: List[str] = field(default_factory=list)
    has_struct: bool = False
    has_exception: bool = False
    doc: str = ""


@dataclass
class ElixirStructInfo:
    """Information about an Elixir struct."""
    name: str  # Module name containing the struct
    file: str = ""
    line_number: int = 0
    fields: List[str] = field(default_factory=list)
    enforced_keys: List[str] = field(default_factory=list)
    has_derive: bool = False
    derives: List[str] = field(default_factory=list)


@dataclass
class ElixirProtocolInfo:
    """Information about an Elixir protocol."""
    name: str
    file: str = ""
    line_number: int = 0
    functions: List[str] = field(default_factory=list)
    implementations: List[str] = field(default_factory=list)
    doc: str = ""


@dataclass
class ElixirBehaviourInfo:
    """Information about an Elixir behaviour."""
    name: str
    file: str = ""
    line_number: int = 0
    callbacks: List[str] = field(default_factory=list)
    optional_callbacks: List[str] = field(default_factory=list)


@dataclass
class ElixirTypespecInfo:
    """Information about an Elixir typespec."""
    name: str
    file: str = ""
    line_number: int = 0
    spec_type: str = "type"  # type, typep, opaque, spec
    definition: str = ""


@dataclass
class ElixirExceptionInfo:
    """Information about an Elixir exception."""
    name: str  # Module name
    file: str = ""
    line_number: int = 0
    fields: List[str] = field(default_factory=list)
    message: str = ""


class ElixirTypeExtractor:
    """Extracts type-level constructs from Elixir source code."""

    # Module patterns
    _MODULE_RE = re.compile(
        r'^\s*defmodule\s+([\w.]+)\s+do\b',
        re.MULTILINE
    )

    # Struct patterns
    _STRUCT_RE = re.compile(
        r'^\s*defstruct\s+(.+)',
        re.MULTILINE
    )

    _ENFORCE_KEYS_RE = re.compile(
        r'@enforce_keys\s+\[([^\]]*)\]',
        re.MULTILINE
    )

    _DERIVE_RE = re.compile(
        r'@derive\s+(?:\[([^\]]+)\]|(\w[\w.]+))',
        re.MULTILINE
    )

    # Protocol patterns
    _PROTOCOL_RE = re.compile(
        r'^\s*defprotocol\s+([\w.]+)\s+do\b',
        re.MULTILINE
    )

    _IMPL_RE = re.compile(
        r'^\s*defimpl\s+([\w.]+)\s*,\s*for:\s*([\w.\[\], ]+)',
        re.MULTILINE
    )

    # Behaviour patterns
    _BEHAVIOUR_RE = re.compile(
        r'^\s*@behaviour\s+([\w.]+)',
        re.MULTILINE
    )

    _CALLBACK_RE = re.compile(
        r'^\s*@callback\s+(\w+)',
        re.MULTILINE
    )

    _OPTIONAL_CALLBACK_RE = re.compile(
        r'^\s*@optional_callbacks\s+\[([^\]]*)\]',
        re.MULTILINE
    )

    # Typespec patterns
    _TYPE_RE = re.compile(
        r'^\s*@(type|typep|opaque)\s+(\w+)',
        re.MULTILINE
    )

    _SPEC_RE = re.compile(
        r'^\s*@spec\s+(\w+)',
        re.MULTILINE
    )

    # Exception patterns
    _EXCEPTION_RE = re.compile(
        r'^\s*defexception\s+(.+)',
        re.MULTILINE
    )

    # Use/import/alias/require
    _USE_RE = re.compile(r'^\s*use\s+([\w.]+)', re.MULTILINE)
    _IMPORT_RE = re.compile(r'^\s*import\s+([\w.]+)', re.MULTILINE)
    _ALIAS_RE = re.compile(r'^\s*alias\s+([\w.{}]+)', re.MULTILINE)
    _REQUIRE_RE = re.compile(r'^\s*require\s+([\w.]+)', re.MULTILINE)

    # Moduledoc
    _MODULEDOC_RE = re.compile(
        r'@moduledoc\s+"""(.*?)"""',
        re.DOTALL
    )

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract all type-level constructs from Elixir source."""
        modules = self._extract_modules(content, file_path)
        structs = self._extract_structs(content, file_path)
        protocols = self._extract_protocols(content, file_path)
        behaviours = self._extract_behaviours(content, file_path)
        typespecs = self._extract_typespecs(content, file_path)
        exceptions = self._extract_exceptions(content, file_path)

        return {
            "modules": modules,
            "structs": structs,
            "protocols": protocols,
            "behaviours": behaviours,
            "typespecs": typespecs,
            "exceptions": exceptions,
        }

    def _extract_modules(self, content: str, file_path: str) -> List[ElixirModuleInfo]:
        modules = []
        for m in self._MODULE_RE.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            uses = [u.group(1) for u in self._USE_RE.finditer(content)]
            imports = [i.group(1) for i in self._IMPORT_RE.finditer(content)]
            aliases = [a.group(1) for a in self._ALIAS_RE.finditer(content)]
            requires = [r.group(1) for r in self._REQUIRE_RE.finditer(content)]
            behaviours = [b.group(1) for b in self._BEHAVIOUR_RE.finditer(content)]

            has_struct = bool(self._STRUCT_RE.search(content))
            has_exception = bool(self._EXCEPTION_RE.search(content))

            doc = ""
            doc_m = self._MODULEDOC_RE.search(content)
            if doc_m:
                doc = doc_m.group(1).strip()[:200]

            modules.append(ElixirModuleInfo(
                name=name,
                file=file_path,
                line_number=line,
                is_nested='.' in name,
                parent_module='.'.join(name.split('.')[:-1]) if '.' in name else "",
                uses=uses[:20],
                imports=imports[:20],
                aliases=aliases[:20],
                requires=requires[:10],
                behaviours=behaviours[:10],
                has_struct=has_struct,
                has_exception=has_exception,
                doc=doc,
            ))
        return modules

    def _extract_structs(self, content: str, file_path: str) -> List[ElixirStructInfo]:
        structs = []
        # Get module name
        mod_m = self._MODULE_RE.search(content)
        mod_name = mod_m.group(1) if mod_m else ""

        for m in self._STRUCT_RE.finditer(content):
            line = content[:m.start()].count('\n') + 1
            raw = m.group(1).strip()

            # Extract field names from struct definition
            fields = re.findall(r':(\w+)', raw)

            # Enforced keys
            enforced = []
            ek_m = self._ENFORCE_KEYS_RE.search(content)
            if ek_m:
                enforced = re.findall(r':(\w+)', ek_m.group(1))

            # Derive
            derives = []
            for d in self._DERIVE_RE.finditer(content):
                if d.group(1):
                    derives.extend(x.strip() for x in d.group(1).split(','))
                elif d.group(2):
                    derives.append(d.group(2))

            structs.append(ElixirStructInfo(
                name=mod_name,
                file=file_path,
                line_number=line,
                fields=fields[:30],
                enforced_keys=enforced[:20],
                has_derive=bool(derives),
                derives=derives[:10],
            ))
        return structs

    def _extract_protocols(self, content: str, file_path: str) -> List[ElixirProtocolInfo]:
        protocols = []
        for m in self._PROTOCOL_RE.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            # Find function defs within protocol
            funcs = re.findall(r'def\s+(\w+)', content[m.start():])
            protocols.append(ElixirProtocolInfo(
                name=name,
                file=file_path,
                line_number=line,
                functions=funcs[:20],
            ))

        # Find implementations
        for m in self._IMPL_RE.finditer(content):
            protocol_name = m.group(1)
            for_types = m.group(2).strip()
            for p in protocols:
                if p.name == protocol_name:
                    p.implementations.append(for_types)

        return protocols

    def _extract_behaviours(self, content: str, file_path: str) -> List[ElixirBehaviourInfo]:
        behaviours = []
        seen = set()

        for m in self._BEHAVIOUR_RE.finditer(content):
            name = m.group(1)
            if name in seen:
                continue
            seen.add(name)
            line = content[:m.start()].count('\n') + 1

            callbacks = [c.group(1) for c in self._CALLBACK_RE.finditer(content)]
            optional = []
            for oc in self._OPTIONAL_CALLBACK_RE.finditer(content):
                optional.extend(re.findall(r'(\w+)', oc.group(1)))

            behaviours.append(ElixirBehaviourInfo(
                name=name,
                file=file_path,
                line_number=line,
                callbacks=callbacks[:20],
                optional_callbacks=optional[:10],
            ))
        return behaviours

    def _extract_typespecs(self, content: str, file_path: str) -> List[ElixirTypespecInfo]:
        specs = []
        for m in self._TYPE_RE.finditer(content):
            spec_type = m.group(1)
            name = m.group(2)
            line = content[:m.start()].count('\n') + 1
            # Get full line as definition
            line_end = content.find('\n', m.start())
            definition = content[m.start():line_end].strip() if line_end > 0 else ""
            specs.append(ElixirTypespecInfo(
                name=name, file=file_path, line_number=line,
                spec_type=spec_type, definition=definition[:200],
            ))

        for m in self._SPEC_RE.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            line_end = content.find('\n', m.start())
            definition = content[m.start():line_end].strip() if line_end > 0 else ""
            specs.append(ElixirTypespecInfo(
                name=name, file=file_path, line_number=line,
                spec_type="spec", definition=definition[:200],
            ))
        return specs

    def _extract_exceptions(self, content: str, file_path: str) -> List[ElixirExceptionInfo]:
        exceptions = []
        mod_m = self._MODULE_RE.search(content)
        mod_name = mod_m.group(1) if mod_m else ""

        for m in self._EXCEPTION_RE.finditer(content):
            line = content[:m.start()].count('\n') + 1
            raw = m.group(1).strip()
            fields = re.findall(r':(\w+)', raw)

            # Find @message attribute
            msg = ""
            msg_m = re.search(r'message:\s*"([^"]*)"', raw)
            if msg_m:
                msg = msg_m.group(1)

            exceptions.append(ElixirExceptionInfo(
                name=mod_name,
                file=file_path,
                line_number=line,
                fields=fields[:20],
                message=msg[:200],
            ))
        return exceptions
