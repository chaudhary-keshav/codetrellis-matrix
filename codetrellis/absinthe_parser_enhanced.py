"""
Enhanced Absinthe Parser for CodeTrellis

Self-contained framework parser for Absinthe (Elixir GraphQL toolkit).
Detects and extracts:
- Schema types (object, input_object, enum, union, interface, scalar)
- Queries, mutations, subscriptions
- Fields with resolvers
- Middleware chains
- Dataloader sources
- Relay connections
- Subscription triggers

Absinthe versions: 1.0–1.7+ (detects based on features)

Reference pattern: Rails parser (self-contained framework file)

Part of CodeTrellis - Absinthe Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


# ── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class AbsintheTypeInfo:
    """Information about an Absinthe type definition."""
    name: str
    type_kind: str = "object"  # object, input_object, enum, union, interface, scalar
    fields: List[str] = field(default_factory=list)
    description: str = ""
    interfaces: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class AbsintheFieldInfo:
    """Information about a GraphQL field."""
    name: str
    parent_type: str = ""
    return_type: str = ""
    args: List[str] = field(default_factory=list)
    has_resolver: bool = False
    resolver_module: str = ""
    middleware: List[str] = field(default_factory=list)
    description: str = ""
    is_deprecated: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class AbsintheQueryInfo:
    """Information about a query/mutation/subscription root field."""
    name: str
    operation: str = "query"  # query, mutation, subscription
    return_type: str = ""
    args: List[str] = field(default_factory=list)
    resolver: str = ""
    description: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class AbsintheResolverInfo:
    """Information about a resolver module."""
    name: str
    functions: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class AbsintheMiddlewareInfo:
    """Information about Absinthe middleware."""
    name: str
    applied_to: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class AbsintheDataloaderInfo:
    """Information about a Dataloader source."""
    name: str
    source_module: str = ""
    repo: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class AbsintheSubscriptionInfo:
    """Information about a subscription with trigger."""
    name: str
    topic: str = ""
    trigger_mutations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class AbsintheParseResult:
    """Complete parse result for an Absinthe file."""
    file_path: str
    file_type: str = "elixir"

    # Types
    types: List[AbsintheTypeInfo] = field(default_factory=list)

    # Fields
    fields: List[AbsintheFieldInfo] = field(default_factory=list)

    # Operations
    queries: List[AbsintheQueryInfo] = field(default_factory=list)

    # Resolvers
    resolvers: List[AbsintheResolverInfo] = field(default_factory=list)

    # Middleware
    middleware: List[AbsintheMiddlewareInfo] = field(default_factory=list)

    # Dataloader
    dataloaders: List[AbsintheDataloaderInfo] = field(default_factory=list)

    # Subscriptions with triggers
    subscriptions: List[AbsintheSubscriptionInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    absinthe_version: str = ""
    has_relay: bool = False
    has_dataloader: bool = False
    has_subscriptions: bool = False
    total_types: int = 0
    total_queries: int = 0
    total_mutations: int = 0


# ── Parser ───────────────────────────────────────────────────────────────────

class EnhancedAbsintheParser:
    """
    Enhanced Absinthe framework parser for CodeTrellis.

    Self-contained parser that extracts Absinthe-specific patterns from Elixir files.
    Only populates results if Absinthe framework is detected.
    """

    # Absinthe detection
    ABSINTHE_REQUIRE = re.compile(
        r'use\s+Absinthe\.\w+|'
        r'Absinthe\.Schema|Absinthe\.Relay|'
        r'Absinthe\.Middleware|Absinthe\.Resolution|'
        r'@behaviour\s+Absinthe\.\w+|'
        r'object\s+:\w+\s+do|'
        r'query\s+do|mutation\s+do|subscription\s+do|'
        r'import_types\b|'
        r'Dataloader\.new|Dataloader\.add_source|'
        r'Resolvers?\.',
        re.MULTILINE,
    )

    # ── Type definition patterns ─────────────────────────────────────────

    OBJECT_RE = re.compile(
        r'^\s*object\s+:(\w+)(?:\s+do)?\b',
        re.MULTILINE,
    )

    INPUT_OBJECT_RE = re.compile(
        r'^\s*input_object\s+:(\w+)(?:\s+do)?\b',
        re.MULTILINE,
    )

    ENUM_RE = re.compile(
        r'^\s*enum\s+:(\w+)\s+do\b',
        re.MULTILINE,
    )

    UNION_RE = re.compile(
        r'^\s*union\s+:(\w+)\s+do\b',
        re.MULTILINE,
    )

    INTERFACE_RE = re.compile(
        r'^\s*interface\s+:(\w+)\s+do\b',
        re.MULTILINE,
    )

    SCALAR_RE = re.compile(
        r'^\s*scalar\s+:(\w+)',
        re.MULTILINE,
    )

    # ── Field patterns ───────────────────────────────────────────────────

    FIELD_RE = re.compile(
        r'^\s*field\s+:(\w+)\s*,?\s*(?::?(\w[\w.!]*))?',
        re.MULTILINE,
    )

    ARG_RE = re.compile(
        r'^\s*arg\s+:(\w+)\s*,\s*(?::?non_null\(\s*)?:?(\w+)',
        re.MULTILINE,
    )

    RESOLVE_RE = re.compile(
        r'resolve\s+(?:&([\w.]+)/\d+|fn\s|&)',
        re.MULTILINE,
    )

    # ── Operation patterns ───────────────────────────────────────────────

    QUERY_DO_RE = re.compile(r'^\s*query\s+do\b', re.MULTILINE)
    MUTATION_DO_RE = re.compile(r'^\s*mutation\s+do\b', re.MULTILINE)
    SUBSCRIPTION_DO_RE = re.compile(r'^\s*subscription\s+do\b', re.MULTILINE)

    # ── Middleware patterns ───────────────────────────────────────────────

    MIDDLEWARE_RE = re.compile(
        r'middleware\s+([\w.]+)',
        re.MULTILINE,
    )

    # ── Dataloader patterns ──────────────────────────────────────────────

    DATALOADER_SOURCE_RE = re.compile(
        r'Dataloader\.(?:Ecto|KV)\.new\(\s*([\w.]+)|'
        r'Dataloader\.add_source\(\s*([\w.]+)',
        re.MULTILINE,
    )

    DATALOADER_ADD_RE = re.compile(
        r'Dataloader\.add_source\(\s*\w+\s*,\s*:?(\w+)',
        re.MULTILINE,
    )

    # ── Subscription trigger patterns ────────────────────────────────────

    TRIGGER_RE = re.compile(
        r'config\s+fn.*?topic:\s*(?:\[([^\]]+)\]|"([^"]+)")',
        re.MULTILINE | re.DOTALL,
    )

    # ── Import types ─────────────────────────────────────────────────────

    IMPORT_TYPES_RE = re.compile(
        r'import_types\s+([\w.]+)',
        re.MULTILINE,
    )

    # ── Relay patterns ───────────────────────────────────────────────────

    CONNECTION_RE = re.compile(r'connection\s+node_type:\s*:(\w+)', re.MULTILINE)
    NODE_RE = re.compile(r'node\s+interface', re.MULTILINE)

    # ── Version detection ────────────────────────────────────────────────

    VERSION_FEATURES = [
        ('1.7', re.compile(r'Absinthe\.Relay\.Node\.IDTranslation|async_phase', re.MULTILINE)),
        ('1.6', re.compile(r'Absinthe\.Subscription|trigger\b|PubSub', re.MULTILINE)),
        ('1.5', re.compile(r'Dataloader|Absinthe\.Middleware\.Dataloader', re.MULTILINE)),
        ('1.4', re.compile(r'import_types|Absinthe\.Schema\.Notation', re.MULTILINE)),
        ('1.3', re.compile(r'Absinthe\.Relay|connection|node\s+interface', re.MULTILINE)),
        ('1.0', re.compile(r'Absinthe\.Schema|object\s+:', re.MULTILINE)),
    ]

    def parse(self, content: str, file_path: str = "") -> AbsintheParseResult:
        """Parse Elixir source code for Absinthe-specific patterns."""
        result = AbsintheParseResult(file_path=file_path)

        # Check if this file uses Absinthe
        if not self.ABSINTHE_REQUIRE.search(content):
            return result

        # Detect version
        result.absinthe_version = self._detect_version(content)

        # Feature flags
        result.has_relay = bool(self.CONNECTION_RE.search(content) or self.NODE_RE.search(content))
        result.has_dataloader = bool(self.DATALOADER_SOURCE_RE.search(content))
        result.has_subscriptions = bool(self.SUBSCRIPTION_DO_RE.search(content))

        # Extract all patterns
        self._extract_types(content, file_path, result)
        self._extract_operations(content, file_path, result)
        self._extract_resolvers(content, file_path, result)
        self._extract_middleware(content, file_path, result)
        self._extract_dataloaders(content, file_path, result)
        self._extract_subscriptions(content, file_path, result)

        # Update totals
        result.total_types = len(result.types)
        result.total_queries = len([q for q in result.queries if q.operation == "query"])
        result.total_mutations = len([q for q in result.queries if q.operation == "mutation"])

        return result

    def _detect_version(self, content: str) -> str:
        """Detect Absinthe version based on features used."""
        for version, pattern in self.VERSION_FEATURES:
            if pattern.search(content):
                return version
        return ""

    def _extract_block(self, content: str, start: int) -> str:
        """Extract content up to matching end keyword."""
        depth = 1
        pos = start
        while pos < len(content) and depth > 0:
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
        return content[start:min(start + 1000, len(content))]

    def _extract_types(self, content: str, file_path: str, result: AbsintheParseResult):
        """Extract Absinthe type definitions."""
        type_patterns = [
            (self.OBJECT_RE, "object"),
            (self.INPUT_OBJECT_RE, "input_object"),
            (self.ENUM_RE, "enum"),
            (self.UNION_RE, "union"),
            (self.INTERFACE_RE, "interface"),
            (self.SCALAR_RE, "scalar"),
        ]

        for pattern, type_kind in type_patterns:
            for m in pattern.finditer(content):
                name = m.group(1)
                line = content[:m.start()].count('\n') + 1

                # Extract fields within the type block
                fields = []
                if type_kind != "scalar":
                    block = self._extract_block(content, m.end())
                    fields = [f.group(1) for f in self.FIELD_RE.finditer(block)]

                # Check for description
                desc = ""
                pre_context = content[max(0, m.start() - 80):m.start()]
                desc_match = re.search(r'@desc\s+"([^"]+)"', pre_context)
                if desc_match:
                    desc = desc_match.group(1)

                result.types.append(AbsintheTypeInfo(
                    name=name,
                    type_kind=type_kind,
                    fields=fields[:30],
                    description=desc[:120],
                    file=file_path,
                    line_number=line,
                ))

    def _extract_operations(self, content: str, file_path: str, result: AbsintheParseResult):
        """Extract query/mutation/subscription root fields."""
        operation_blocks = [
            (self.QUERY_DO_RE, "query"),
            (self.MUTATION_DO_RE, "mutation"),
            (self.SUBSCRIPTION_DO_RE, "subscription"),
        ]

        for block_re, op_type in operation_blocks:
            for m in block_re.finditer(content):
                block = self._extract_block(content, m.end())
                base_line = content[:m.start()].count('\n') + 1

                for field_m in self.FIELD_RE.finditer(block):
                    name = field_m.group(1)
                    return_type = field_m.group(2) or ""
                    field_line = base_line + block[:field_m.start()].count('\n')

                    # Find args for this field
                    field_block = self._extract_block(block, field_m.end())
                    args = [a.group(1) for a in self.ARG_RE.finditer(field_block)]

                    # Find resolver for this field
                    resolver = ""
                    resolve_m = self.RESOLVE_RE.search(field_block)
                    if resolve_m:
                        resolver = resolve_m.group(1) or "inline"

                    result.queries.append(AbsintheQueryInfo(
                        name=name,
                        operation=op_type,
                        return_type=return_type,
                        args=args[:10],
                        resolver=resolver,
                        file=file_path,
                        line_number=field_line,
                    ))

    def _extract_resolvers(self, content: str, file_path: str, result: AbsintheParseResult):
        """Extract resolver modules."""
        # Look for modules that define resolve functions
        resolve_funcs = re.findall(
            r'def\s+(resolve_\w+|create_\w+|update_\w+|delete_\w+|list_\w+|get_\w+)\s*\(',
            content,
        )
        if resolve_funcs:
            module = self._find_enclosing_module(content, 0)
            result.resolvers.append(AbsintheResolverInfo(
                name=module,
                functions=resolve_funcs[:20],
                file=file_path,
                line_number=1,
            ))

    def _extract_middleware(self, content: str, file_path: str, result: AbsintheParseResult):
        """Extract Absinthe middleware usage and definitions."""
        # Middleware usage: middleware MyApp.Something
        for m in self.MIDDLEWARE_RE.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1
            result.middleware.append(AbsintheMiddlewareInfo(
                name=name,
                file=file_path,
                line_number=line,
            ))

        # Middleware definitions: @behaviour Absinthe.Middleware + def call
        if re.search(r'@behaviour\s+Absinthe\.Middleware', content) and re.search(r'def\s+call\(', content):
            module = self._find_enclosing_module(content, 0)
            line = 1
            m = re.search(r'@behaviour\s+Absinthe\.Middleware', content)
            if m:
                line = content[:m.start()].count('\n') + 1
            result.middleware.append(AbsintheMiddlewareInfo(
                name=module,
                file=file_path,
                line_number=line,
            ))

        # Schema-level middleware: def middleware(...) do
        if re.search(r'def\s+middleware\s*\(\s*middleware\s*,', content):
            module = self._find_enclosing_module(content, 0)
            m = re.search(r'def\s+middleware\s*\(\s*middleware\s*,', content)
            line = content[:m.start()].count('\n') + 1 if m else 1
            result.middleware.append(AbsintheMiddlewareInfo(
                name=f"{module}.middleware/3",
                file=file_path,
                line_number=line,
            ))

    def _extract_dataloaders(self, content: str, file_path: str, result: AbsintheParseResult):
        """Extract Dataloader sources."""
        for m in self.DATALOADER_SOURCE_RE.finditer(content):
            source = m.group(1) or m.group(2)
            line = content[:m.start()].count('\n') + 1
            result.dataloaders.append(AbsintheDataloaderInfo(
                name=source,
                source_module=source,
                file=file_path,
                line_number=line,
            ))

    def _extract_subscriptions(self, content: str, file_path: str, result: AbsintheParseResult):
        """Extract subscription definitions with triggers."""
        sub_m = self.SUBSCRIPTION_DO_RE.search(content)
        if not sub_m:
            return

        block = self._extract_block(content, sub_m.end())
        base_line = content[:sub_m.start()].count('\n') + 1

        for field_m in self.FIELD_RE.finditer(block):
            name = field_m.group(1)
            field_line = base_line + block[:field_m.start()].count('\n')

            # Find trigger mutations
            field_block = self._extract_block(block, field_m.end())
            triggers = re.findall(r':(\w+)', field_block[:200])

            result.subscriptions.append(AbsintheSubscriptionInfo(
                name=name,
                trigger_mutations=triggers[:10],
                file=file_path,
                line_number=field_line,
            ))

    def _find_enclosing_module(self, content: str, pos: int) -> str:
        """Find the nearest enclosing defmodule name."""
        prefix = content[:max(pos, len(content))]
        modules = re.findall(r'defmodule\s+([\w.]+)\s+do', prefix)
        return modules[-1] if modules else "Unknown"
