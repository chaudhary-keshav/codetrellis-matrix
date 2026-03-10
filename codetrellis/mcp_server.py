"""
CodeTrellis MCP Server — Model Context Protocol Integration (A5.2)
==================================================================

Exposes CodeTrellis Matrix sections as MCP resources and provides
search/query tools for any MCP-compatible AI tool.

Supported clients: Claude Desktop, Gemini CLI, Cursor, Cline, Continue

Architecture:
  Resources:
    - matrix://sections          → List all available sections
    - matrix://section/{name}    → Get a specific section
    - matrix://overview          → Project overview
    - matrix://types             → All type definitions
    - matrix://api               → All API endpoints
    - matrix://runbook           → Build/run/test commands
    - matrix://practices         → Best practices for the project

  Tools:
    - search_matrix(query)       → Full-text search across all sections
    - get_section(name)          → Get a specific section by name
    - get_sections(names)        → Batch-fetch multiple sections in one call
    - get_context_for_file(path) → Get relevant context for a file (JIT)
    - get_skills()               → List auto-generated skills
    - get_cache_stats()          → Get cache stats + matrix freshness info
    - get_filtered_logic(query)  → Filter IMPLEMENTATION_LOGIC by relevance

Protocol: MCP (Model Context Protocol) v1.0
Transport: stdio (default), SSE (optional)

Version: 1.0.0
Created: 20 February 2026
"""

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class MCPResource:
    """An MCP resource that can be read by AI tools."""
    uri: str
    name: str
    description: str
    mime_type: str = "text/plain"

    def to_dict(self) -> Dict[str, str]:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type,
        }


@dataclass
class MCPTool:
    """An MCP tool that can be called by AI tools."""
    name: str
    description: str
    input_schema: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


@dataclass
class MCPToolResult:
    """Result from an MCP tool call."""
    content: List[Dict[str, str]]
    is_error: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "isError": self.is_error,
        }


class MatrixMCPServer:
    """
    MCP Server that exposes CodeTrellis Matrix as resources and tools.

    The server loads a matrix.prompt file and makes its sections available
    as individual MCP resources that AI tools can query.

    Usage:
        server = MatrixMCPServer(project_root="/path/to/project")
        server.load_matrix()

        # Get a specific section
        content = server.get_section("PYTHON_TYPES")

        # Search across all sections
        results = server.search_matrix("FastAPI routes")

        # Get context for a specific file
        context = server.get_context_for_file("src/api/routes.py")
    """

    # Section aliases: map common/documented names to actual section names
    # This allows users to request e.g. "TYPESCRIPT_TYPES" even though
    # the compressor emits "TS_TYPES".
    SECTION_ALIASES = {
        "TYPESCRIPT_TYPES": "TS_TYPES",
        "TYPESCRIPT_API": "TS_API",
        "TYPESCRIPT_FUNCTIONS": "TS_FUNCTIONS",
        "TYPESCRIPT_MODELS": "TS_MODELS",
        "TYPESCRIPT_DEPENDENCIES": "TS_DEPENDENCIES",
        "JAVASCRIPT_TYPES": "JS_TYPES",
        "JAVASCRIPT_API": "JS_API",
        "JAVASCRIPT_FUNCTIONS": "JS_FUNCTIONS",
        "JAVASCRIPT_MODELS": "JS_MODELS",
        "JAVASCRIPT_DEPENDENCIES": "JS_DEPENDENCIES",
        "ROUTES_SEMANTIC": "ROUTES",
    }

    # Aggregate resource URIs that combine multiple sections
    AGGREGATE_RESOURCES = {
        "types": [
            "PYTHON_TYPES", "SCHEMAS", "INTERFACES", "TYPES", "ENUMS",
            "GO_TYPES", "JAVA_TYPES", "KOTLIN_TYPES", "CSHARP_TYPES",
            "RUST_TYPES", "SWIFT_TYPES", "RUBY_TYPES", "PHP_TYPES",
            "SCALA_TYPES", "TS_TYPES", "JS_TYPES", "DART_TYPES",
            "R_TYPES", "LUA_TYPES", "C_TYPES", "CPP_TYPES",
            "SQL_TABLES", "POWERSHELL_TYPES",
        ],
        "api": [
            # Core language APIs
            "PYTHON_API", "HTTP_API", "ROUTES", "ROUTES_SEMANTIC",
            "GO_API", "JAVA_API", "KOTLIN_API", "CSHARP_API",
            "RUST_API", "SWIFT_API", "RUBY_API", "PHP_API",
            "SCALA_API", "TS_API", "JS_API", "DART_API",
            "R_API", "LUA_API", "C_API", "CPP_API",
            "BASH_API", "POWERSHELL_API", "GRAPHQL", "OPENAPI",
            "WEBSOCKET_EVENTS", "SERVICE_MAP",
            # Framework APIs
            "ALPINE_API", "ANTD_API", "APOLLO_API", "ASTRO_API",
            "CHAKRA_API", "EM_API", "HTMX_API", "JOTAI_API",
            "LIT_API", "MOBX_API", "MUI_API", "NGRX_API",
            "PINIA_API", "PREACT_API", "QWIK_API", "RADIX_API",
            "RECOIL_API", "REMIX_API", "SC_API", "SHADCN_API",
            "SOLIDJS_API", "STIMULUS_API", "STORYBOOK_API", "SWR_API", "TANSTACK_QUERY_API",
            "VALTIO_API", "XSTATE_API", "ZUSTAND_API",
            # Go framework APIs (v5.2)
            "GO_GIN", "GO_ECHO", "GO_FIBER", "GO_CHI",
            "GO_GRPC", "GO_GORM", "GO_SQLX", "GO_COBRA",
        ],
        "overview": [
            "PROJECT", "OVERVIEW", "PROJECT_STRUCTURE", "PROJECT_PROFILE",
            "BUSINESS_DOMAIN", "DATA_FLOWS",
        ],
        "state": [
            "STORES", "REACT_STATE", "REACT_CONTEXT",
            "REDUX_STORES", "REDUX_SLICES", "REDUX_SELECTORS",
            "ZUSTAND_STORES", "ZUSTAND_SELECTORS",
            "JOTAI_ATOMS", "JOTAI_SELECTORS",
            "RECOIL_ATOMS", "RECOIL_SELECTORS",
            "MOBX_OBSERVABLES", "MOBX_COMPUTEDS",
            "PINIA_STORES", "PINIA_GETTERS",
            "NGRX_STORES", "NGRX_SELECTORS",
            "VALTIO_PROXIES", "VALTIO_SNAPSHOTS",
            "XSTATE_MACHINES", "XSTATE_STATES",
            "SVELTE_STORES", "SOLIDJS_SIGNALS", "SOLIDJS_STORES",
            "QWIK_SIGNALS", "PREACT_SIGNALS",
        ],
        "infrastructure": [
            "INFRASTRUCTURE", "DATABASE", "SECURITY",
            "CONFIG_VARIABLES", "ENV_GAPS",
        ],
        "components": [
            "COMPONENTS", "REACT_COMPONENTS", "VUE_COMPONENTS",
            "SVELTE_COMPONENTS", "ASTRO_COMPONENTS", "LIT_COMPONENTS",
            "SOLIDJS_COMPONENTS", "QWIK_COMPONENTS", "PREACT_COMPONENTS",
            "ALPINE_COMPONENTS", "SC_COMPONENTS", "EM_COMPONENTS",
            "MUI_COMPONENTS", "ANTD_COMPONENTS", "CHAKRA_COMPONENTS",
            "SHADCN_COMPONENTS", "BOOTSTRAP_COMPONENTS", "RADIX_COMPONENTS",
            "HTMX_ATTRIBUTES", "STIMULUS_CONTROLLERS",
            "STORYBOOK_STORIES", "STORYBOOK_COMPONENTS",
        ],
        "styling": [
            "CSS_SELECTORS", "CSS_VARIABLES", "CSS_LAYOUT", "CSS_MEDIA",
            "CSS_ANIMATIONS", "CSS_PREPROCESSOR",
            "SASS_VARIABLES", "SASS_MIXINS", "SASS_FUNCTIONS", "SASS_MODULES",
            "LESS_VARIABLES", "LESS_MIXINS", "LESS_FUNCTIONS",
            "TAILWIND_UTILITIES", "TAILWIND_COMPONENTS", "TAILWIND_CONFIG",
            "POSTCSS_PLUGINS", "POSTCSS_CONFIG",
            "SC_STYLES", "SC_THEME", "EM_STYLES", "EM_THEME",
            "MUI_THEME", "MUI_STYLES", "ANTD_THEME", "ANTD_STYLES",
            "CHAKRA_THEME", "CHAKRA_STYLES", "SHADCN_STYLES", "SHADCN_THEME",
            "BOOTSTRAP_THEME", "BOOTSTRAP_UTILITIES", "RADIX_STYLES",
        ],
        "routing": [
            "ROUTES", "ROUTES_SEMANTIC", "HTTP_API",
            "REACT_ROUTING", "VUE_ROUTING", "SVELTEKIT_ROUTING",
            "NEXT_ROUTES", "NEXT_PAGES", "REMIX_ROUTES",
            "ASTRO_ROUTING", "QWIK_ROUTES", "HTMX_REQUESTS",
            "STIMULUS_ACTIONS",
        ],
    }

    def __init__(self, project_root: str, matrix_path: Optional[str] = None) -> None:
        """
        Initialize the MCP server.

        Args:
            project_root: Path to the project root directory
            matrix_path: Optional explicit path to matrix.prompt file.
                        If not provided, looks in .codetrellis/cache/
        """
        self._project_root = Path(project_root).resolve()
        self._matrix_path = Path(matrix_path) if matrix_path else None
        self._raw_prompt: str = ""
        self._sections: Dict[str, str] = {}
        self._loaded: bool = False
        self._matrix_mtime: float = 0.0  # Track file modification time for auto-reload
        self._matrix_file_path: Optional[Path] = None  # Cached resolved path

    @property
    def is_loaded(self) -> bool:
        """Whether a matrix has been loaded."""
        return self._loaded

    def load_matrix(self, force: bool = False) -> bool:
        """
        Load the matrix.prompt file and parse it into sections.

        Args:
            force: Force reload even if already loaded

        Returns:
            True if matrix was loaded successfully
        """
        if self._loaded and not force:
            return True

        matrix_file = self._find_matrix_file()
        if not matrix_file or not matrix_file.exists():
            return False

        self._raw_prompt = matrix_file.read_text(encoding="utf-8")
        self._sections = self._parse_into_sections(self._raw_prompt)
        self._loaded = True
        self._matrix_file_path = matrix_file
        try:
            self._matrix_mtime = matrix_file.stat().st_mtime
        except OSError:
            self._matrix_mtime = 0.0
        return True

    def _reload_if_stale(self) -> None:
        """Auto-reload matrix.prompt if the file has changed on disk.

        This is called before every tool/resource request so the MCP server
        always serves the latest matrix without requiring a process restart.
        """
        if not self._loaded:
            self.load_matrix()
            return

        # Resolve path if we don't have it cached
        matrix_file = self._matrix_file_path or self._find_matrix_file()
        if not matrix_file or not matrix_file.exists():
            return

        try:
            current_mtime = matrix_file.stat().st_mtime
        except OSError:
            return

        if current_mtime > self._matrix_mtime:
            import sys as _sys
            _sys.stderr.write(
                f"[CodeTrellis] Matrix file changed on disk, reloading "
                f"({len(self._sections)} → "
            )
            _sys.stderr.flush()
            self.load_matrix(force=True)
            _sys.stderr.write(f"{len(self._sections)} sections)\n")
            _sys.stderr.flush()

    def _find_matrix_file(self) -> Optional[Path]:
        """Find the matrix.prompt file in the project."""
        if self._matrix_path and self._matrix_path.exists():
            return self._matrix_path

        cache_dir = self._project_root / ".codetrellis" / "cache"
        if not cache_dir.exists():
            return None

        # Find the latest version directory
        version_dirs = sorted(cache_dir.iterdir(), reverse=True)
        for vdir in version_dirs:
            if vdir.is_dir():
                for project_dir in vdir.iterdir():
                    if project_dir.is_dir():
                        prompt_file = project_dir / "matrix.prompt"
                        if prompt_file.exists():
                            return prompt_file
        return None

    def _parse_into_sections(self, raw: str) -> Dict[str, str]:
        """Parse raw matrix.prompt into named sections."""
        sections: Dict[str, str] = {}

        pattern = re.compile(r'^\[([A-Z][A-Z0-9_]*(?::[^\]]+)?)\]', re.MULTILINE)
        matches = list(pattern.finditer(raw))

        # Preamble
        if matches:
            preamble = raw[:matches[0].start()].strip()
            if preamble:
                sections["_PREAMBLE"] = preamble

        for i, match in enumerate(matches):
            section_name = match.group(1)
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
            sections[section_name] = raw[start:end].rstrip()

        return sections

    # =========================================================================
    # Resources
    # =========================================================================

    def list_resources(self) -> List[MCPResource]:
        """List all available MCP resources."""
        if not self._loaded:
            self.load_matrix()

        resources: List[MCPResource] = []

        # Section list resource
        resources.append(MCPResource(
            uri="matrix://sections",
            name="Matrix Section List",
            description="List of all available CodeTrellis Matrix sections",
        ))

        # Full matrix
        resources.append(MCPResource(
            uri="matrix://full",
            name="Full Matrix",
            description="Complete CodeTrellis Matrix prompt",
        ))

        # Aggregate resources
        for agg_name, _sections in self.AGGREGATE_RESOURCES.items():
            resources.append(MCPResource(
                uri=f"matrix://{agg_name}",
                name=f"Matrix {agg_name.title()}",
                description=f"Aggregated {agg_name} sections from the matrix",
            ))

        # Individual sections
        for section_name in self._sections:
            if section_name == "_PREAMBLE":
                continue
            resources.append(MCPResource(
                uri=f"matrix://section/{section_name}",
                name=section_name,
                description=f"Matrix section: {section_name}",
            ))

        return resources

    def read_resource(self, uri: str) -> Optional[str]:
        """
        Read a specific MCP resource by URI.

        Args:
            uri: Resource URI (e.g., "matrix://section/PYTHON_TYPES")

        Returns:
            Resource content or None if not found
        """
        if not self._loaded:
            self.load_matrix()

        if uri == "matrix://sections":
            return self._get_section_list()
        elif uri == "matrix://full":
            return self._raw_prompt
        elif uri.startswith("matrix://section/"):
            section_name = uri.split("matrix://section/", 1)[1]
            return self._sections.get(section_name)
        elif uri.startswith("matrix://"):
            # Aggregate resources
            agg_name = uri.split("matrix://", 1)[1]
            if agg_name in self.AGGREGATE_RESOURCES:
                return self._get_aggregate(agg_name)
        return None

    def _get_section_list(self) -> str:
        """Get a formatted list of all sections with token counts."""
        lines = ["# CodeTrellis Matrix Sections", ""]
        for name, content in self._sections.items():
            if name == "_PREAMBLE":
                continue
            tokens = len(content) // 4
            lines.append(f"  {name}: ~{tokens} tokens")
        lines.append("")
        lines.append(f"Total sections: {len(self._sections) - (1 if '_PREAMBLE' in self._sections else 0)}")
        lines.append(f"Total tokens: ~{len(self._raw_prompt) // 4}")
        return "\n".join(lines)

    def _get_aggregate(self, name: str) -> str:
        """Get an aggregate of multiple sections."""
        section_names = self.AGGREGATE_RESOURCES.get(name, [])
        parts = []
        for sname in section_names:
            if sname in self._sections:
                parts.append(self._sections[sname])
        return "\n\n".join(parts) if parts else f"No {name} sections found in matrix."

    # =========================================================================
    # Tools
    # =========================================================================

    def list_tools(self) -> List[MCPTool]:
        """List all available MCP tools."""
        return [
            MCPTool(
                name="search_matrix",
                description=(
                    "Search across all CodeTrellis Matrix sections for relevant context. "
                    "Returns matching sections and lines containing the search query."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query — text to find in the matrix",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of matching sections to return",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            ),
            MCPTool(
                name="get_section",
                description="Get a specific named section from the CodeTrellis Matrix.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Section name (e.g., PYTHON_TYPES, RUNBOOK, BEST_PRACTICES)",
                        },
                    },
                    "required": ["name"],
                },
            ),
            MCPTool(
                name="get_context_for_file",
                description=(
                    "Get relevant matrix context for a specific file path. "
                    "Returns type definitions, API endpoints, dependencies, and "
                    "other context relevant to the given file."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Relative file path to get context for",
                        },
                    },
                    "required": ["file_path"],
                },
            ),
            MCPTool(
                name="get_skills",
                description="List auto-generated skills based on project analysis.",
                input_schema={
                    "type": "object",
                    "properties": {},
                },
            ),
            MCPTool(
                name="get_cache_stats",
                description="Get prompt caching optimization statistics.",
                input_schema={
                    "type": "object",
                    "properties": {},
                },
            ),
            MCPTool(
                name="get_sections",
                description=(
                    "Batch-fetch multiple named sections from the CodeTrellis Matrix "
                    "in a single call. Returns a JSON object mapping section names to "
                    "their content. More efficient than calling get_section repeatedly."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "List of section names to fetch "
                                "(e.g., ['PYTHON_TYPES', 'RUNBOOK', 'BEST_PRACTICES'])"
                            ),
                        },
                    },
                    "required": ["names"],
                },
            ),
            MCPTool(
                name="get_filtered_logic",
                description=(
                    "Search the IMPLEMENTATION_LOGIC section for snippets relevant "
                    "to a query. Returns the top matching snippets ranked by relevance. "
                    "Use this instead of fetching the entire IMPLEMENTATION_LOGIC section "
                    "when you only need context for specific files or functions."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query — file name, function name, or concept",
                        },
                        "max_snippets": {
                            "type": "integer",
                            "description": "Maximum number of snippets to return (default: 20)",
                            "default": 20,
                        },
                    },
                    "required": ["query"],
                },
            ),
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> MCPToolResult:
        """
        Call an MCP tool by name.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            MCPToolResult with the tool output
        """
        if not self._loaded:
            self.load_matrix()

        try:
            if name == "search_matrix":
                return self._tool_search(
                    arguments.get("query", ""),
                    arguments.get("max_results", 5),
                )
            elif name == "get_section":
                return self._tool_get_section(arguments.get("name", ""))
            elif name == "get_context_for_file":
                return self._tool_get_context_for_file(arguments.get("file_path", ""))
            elif name == "get_skills":
                return self._tool_get_skills()
            elif name == "get_cache_stats":
                return self._tool_get_cache_stats()
            elif name == "get_sections":
                return self._tool_get_sections(arguments.get("names", []))
            elif name == "get_filtered_logic":
                return self._tool_get_filtered_logic(
                    arguments.get("query", ""),
                    arguments.get("max_snippets", 20),
                )
            else:
                return MCPToolResult(
                    content=[{"type": "text", "text": f"Unknown tool: {name}"}],
                    is_error=True,
                )
        except Exception as e:
            return MCPToolResult(
                content=[{"type": "text", "text": f"Error: {str(e)}"}],
                is_error=True,
            )

    def _tool_search(self, query: str, max_results: int = 5) -> MCPToolResult:
        """Search across all matrix sections."""
        results = self.search_matrix(query, max_results)
        if not results:
            return MCPToolResult(
                content=[{"type": "text", "text": f"No results found for: {query}"}],
            )

        text_parts = [f"# Search results for: {query}\n"]
        for section_name, matches in results:
            text_parts.append(f"\n## [{section_name}]")
            for line in matches[:10]:
                text_parts.append(f"  {line.strip()}")

        return MCPToolResult(
            content=[{"type": "text", "text": "\n".join(text_parts)}],
        )

    def _tool_get_section(self, name: str) -> MCPToolResult:
        """Get a specific section."""
        content = self.get_section(name)
        if content is None:
            available = [s for s in self._sections if s != "_PREAMBLE"]
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": f"Section '{name}' not found. Available: {', '.join(available[:20])}",
                }],
                is_error=True,
            )
        return MCPToolResult(
            content=[{"type": "text", "text": content}],
        )

    def _tool_get_context_for_file(self, file_path: str) -> MCPToolResult:
        """Get JIT context for a file."""
        # Path traversal protection: reject paths outside project root
        resolved = (self._project_root / file_path).resolve()
        if not str(resolved).startswith(str(self._project_root)):
            return MCPToolResult(
                content=[{"type": "text", "text": f"Rejected: path '{file_path}' resolves outside the project root"}],
                is_error=True,
            )

        from codetrellis.jit_context import JITContextProvider

        provider = JITContextProvider(self._sections)
        context = provider.get_context_for_file(file_path)

        if not context:
            return MCPToolResult(
                content=[{"type": "text", "text": f"No relevant context found for: {file_path}"}],
            )

        return MCPToolResult(
            content=[{"type": "text", "text": context}],
        )

    def _tool_get_skills(self) -> MCPToolResult:
        """Get auto-generated skills."""
        from codetrellis.skills_generator import SkillsGenerator

        generator = SkillsGenerator(self._sections)
        skills = generator.generate()

        text_parts = ["# Auto-Generated Skills\n"]
        for skill in skills:
            text_parts.append(f"## {skill.name}")
            text_parts.append(f"  Description: {skill.description}")
            text_parts.append(f"  Trigger: {skill.trigger}")
            text_parts.append(f"  Context sections: {', '.join(skill.context_sections)}")
            text_parts.append("")

        return MCPToolResult(
            content=[{"type": "text", "text": "\n".join(text_parts)}],
        )

    def _tool_get_cache_stats(self) -> MCPToolResult:
        """Get cache optimization statistics."""
        from codetrellis.cache_optimizer import optimize_matrix_prompt

        result = optimize_matrix_prompt(self._raw_prompt)
        stats = dict(result.stats)

        # ── MOTA enrichment: matrix freshness info ──
        stats["matrix_mtime"] = self._matrix_mtime
        stats["matrix_mtime_iso"] = ""
        if self._matrix_mtime > 0:
            import datetime
            stats["matrix_mtime_iso"] = (
                datetime.datetime.fromtimestamp(self._matrix_mtime)
                .isoformat(timespec="seconds")
            )

        # Count source files newer than the matrix
        source_files_newer_count = 0
        if self._matrix_mtime > 0:
            source_files_newer_count = self._count_source_files_newer_than(
                self._matrix_mtime
            )
        stats["source_files_newer_count"] = source_files_newer_count
        stats["matrix_is_fresh"] = source_files_newer_count == 0

        stats_text = json.dumps(stats, indent=2, default=str)
        return MCPToolResult(
            content=[{"type": "text", "text": f"# Cache Optimization Stats\n\n{stats_text}"}],
        )

    def _tool_get_sections(self, names: List[str]) -> MCPToolResult:
        """Batch-fetch multiple sections in a single call."""
        if not names:
            return MCPToolResult(
                content=[{"type": "text", "text": "Error: 'names' list is empty."}],
                is_error=True,
            )

        result_map: Dict[str, Optional[str]] = {}
        found_count = 0
        for name in names:
            content = self.get_section(name)
            if content is not None:
                result_map[name] = content
                found_count += 1
            else:
                result_map[name] = None

        # Build response: JSON object with section contents
        text_parts = [f"# Batch Sections ({found_count}/{len(names)} found)\n"]
        for name in names:
            content = result_map[name]
            if content is not None:
                text_parts.append(f"\n## [{name}]")
                text_parts.append(content)
            else:
                text_parts.append(f"\n## [{name}] — NOT FOUND")

        return MCPToolResult(
            content=[{"type": "text", "text": "\n".join(text_parts)}],
        )

    def _tool_get_filtered_logic(
        self, query: str, max_snippets: int = 20
    ) -> MCPToolResult:
        """Filter IMPLEMENTATION_LOGIC snippets by relevance to a query."""
        # Gather all IMPLEMENTATION_LOGIC sections (may be split across keys)
        logic_sections: List[str] = []
        for section_name, content in self._sections.items():
            if "IMPLEMENTATION_LOGIC" in section_name:
                logic_sections.append(content)

        if not logic_sections:
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": "No IMPLEMENTATION_LOGIC section found in matrix.",
                }],
            )

        # Parse into individual snippets (split on "## " which starts each file block)
        all_snippets: List[str] = []
        for section_text in logic_sections:
            parts = re.split(r'(?=^## )', section_text, flags=re.MULTILINE)
            for part in parts:
                stripped = part.strip()
                if stripped and not stripped.startswith("[IMPLEMENTATION_LOGIC"):
                    all_snippets.append(stripped)

        if not all_snippets:
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": f"No IMPLEMENTATION_LOGIC snippets found for: {query}",
                }],
            )

        # Score each snippet by relevance to query
        query_lower = query.lower()
        query_words = query_lower.split()
        scored: List[tuple] = []
        for snippet in all_snippets:
            snippet_lower = snippet.lower()
            # Exact query match scores highest
            score = snippet_lower.count(query_lower) * 10
            # Individual word matches
            score += sum(snippet_lower.count(w) for w in query_words)
            if score > 0:
                scored.append((snippet, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:max_snippets]

        if not top:
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": f"No matching IMPLEMENTATION_LOGIC snippets for: {query}",
                }],
            )

        text_parts = [
            f"# Filtered IMPLEMENTATION_LOGIC ({len(top)}/{len(all_snippets)} snippets)\n"
            f"Query: {query}\n"
        ]
        for snippet, _score in top:
            text_parts.append(snippet)
            text_parts.append("")

        return MCPToolResult(
            content=[{"type": "text", "text": "\n".join(text_parts)}],
        )

    def _count_source_files_newer_than(self, threshold: float) -> int:
        """Count project source files modified after the given timestamp."""
        count = 0
        # Common source extensions to check
        source_extensions = {
            ".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".kt", ".go",
            ".rs", ".cs", ".swift", ".rb", ".php", ".scala", ".dart",
            ".vue", ".svelte", ".astro", ".lua", ".r", ".c", ".cpp", ".h",
            ".sql", ".sh", ".ps1", ".html", ".css", ".scss", ".sass", ".less",
        }
        try:
            for item in self._project_root.rglob("*"):
                if not item.is_file():
                    continue
                if item.suffix.lower() not in source_extensions:
                    continue
                # Skip hidden dirs, node_modules, .codetrellis, etc.
                parts = item.relative_to(self._project_root).parts
                if any(
                    p.startswith(".") or p in ("node_modules", "__pycache__", "dist", "build", "venv", ".venv")
                    for p in parts
                ):
                    continue
                try:
                    if item.stat().st_mtime > threshold:
                        count += 1
                except OSError:
                    continue
        except OSError:
            pass
        return count

    # =========================================================================
    # Core query methods
    # =========================================================================

    def get_section(self, name: str) -> Optional[str]:
        """Get a specific section by name."""
        if not self._loaded:
            self.load_matrix()
        # Try exact match first, then case-insensitive
        if name in self._sections:
            return self._sections[name]
        name_upper = name.upper()
        if name_upper in self._sections:
            return self._sections[name_upper]
        # Try aliases (e.g. TYPESCRIPT_TYPES -> TS_TYPES)
        alias_target = self.SECTION_ALIASES.get(name_upper)
        if alias_target and alias_target in self._sections:
            return self._sections[alias_target]
        return None

    def search_matrix(self, query: str, max_results: int = 5) -> List[tuple]:
        """
        Search across all sections for matching content.

        Args:
            query: Search query string
            max_results: Maximum sections to return

        Returns:
            List of (section_name, matching_lines) tuples, ranked by relevance
        """
        if not self._loaded:
            self.load_matrix()

        query_lower = query.lower()
        query_words = query_lower.split()
        results: List[tuple] = []

        for section_name, content in self._sections.items():
            if section_name == "_PREAMBLE":
                continue

            content_lower = content.lower()
            # Score: count of query word occurrences
            score = sum(content_lower.count(w) for w in query_words)

            if score > 0:
                # Get matching lines
                matching_lines = []
                for line in content.split("\n"):
                    if any(w in line.lower() for w in query_words):
                        matching_lines.append(line)

                results.append((section_name, matching_lines, score))

        # Sort by score descending
        results.sort(key=lambda x: x[2], reverse=True)
        return [(name, lines) for name, lines, _ in results[:max_results]]

    # =========================================================================
    # MCP Protocol Handler (stdio transport)
    # =========================================================================

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a single MCP JSON-RPC request.

        Args:
            request: JSON-RPC 2.0 request object

        Returns:
            JSON-RPC 2.0 response object
        """
        method = request.get("method", "")
        req_id = request.get("id")
        params = request.get("params", {})

        # Auto-reload matrix if the file has changed on disk
        self._reload_if_stale()

        try:
            if method == "initialize":
                result = self._handle_initialize(params)
            elif method == "resources/list":
                result = {"resources": [r.to_dict() for r in self.list_resources()]}
            elif method == "resources/read":
                uri = params.get("uri", "")
                content = self.read_resource(uri)
                if content is not None:
                    result = {
                        "contents": [{
                            "uri": uri,
                            "mimeType": "text/plain",
                            "text": content,
                        }]
                    }
                else:
                    return self._error_response(req_id, -32602, f"Resource not found: {uri}")
            elif method == "tools/list":
                result = {"tools": [t.to_dict() for t in self.list_tools()]}
            elif method == "tools/call":
                tool_name = params.get("name", "")
                tool_args = params.get("arguments", {})
                tool_result = self.call_tool(tool_name, tool_args)
                result = tool_result.to_dict()
            elif method == "notifications/initialized":
                # Client notification, no response needed
                return None
            else:
                return self._error_response(req_id, -32601, f"Method not found: {method}")

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result,
            }

        except Exception as e:
            return self._error_response(req_id, -32603, str(e))

    def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the initialize request."""
        self.load_matrix()
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "resources": {"listChanged": False},
                "tools": {},
            },
            "serverInfo": {
                "name": "codetrellis-matrix",
                "version": "1.0.0",
            },
        }

    def _error_response(self, req_id: Any, code: int, message: str) -> Dict[str, Any]:
        """Create a JSON-RPC error response."""
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": code,
                "message": message,
            },
        }

    def run_stdio(self) -> None:
        """
        Run the MCP server using stdio transport.

        Reads JSON-RPC requests from stdin and writes responses to stdout.
        """
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                request = json.loads(line)
                response = self.handle_request(request)

                if response is not None:
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()

            except json.JSONDecodeError:
                error = self._error_response(None, -32700, "Parse error")
                sys.stdout.write(json.dumps(error) + "\n")
                sys.stdout.flush()
            except KeyboardInterrupt:
                break
            except Exception:
                pass


def create_mcp_server(project_root: str, matrix_path: Optional[str] = None) -> MatrixMCPServer:
    """
    Factory function to create and initialize an MCP server.

    Args:
        project_root: Path to the project root
        matrix_path: Optional explicit path to matrix.prompt

    Returns:
        Initialized MatrixMCPServer
    """
    server = MatrixMCPServer(project_root, matrix_path)
    server.load_matrix()
    return server
