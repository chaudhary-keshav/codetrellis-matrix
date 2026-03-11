"""
CodeTrellis JIT Context Discovery (A5.3)
========================================

When AI accesses any file, auto-inject the relevant matrix slices:
  - Language-specific type definitions
  - Related API endpoints
  - Dependency information
  - TODOs and actionable items for that file
  - Best practices for the detected language/framework

The JIT provider maps file paths → relevant matrix sections by analyzing:
  1. File extension → language → language-specific sections
  2. File path patterns → framework-specific sections
  3. File name mentioned in matrix content → specific sections
  4. Project structure → architectural sections

Version: 1.0.0
Created: 20 February 2026
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class JITContextResult:
    """Result of JIT context resolution for a file."""
    file_path: str
    sections_included: List[str]
    context: str
    token_estimate: int
    relevance_scores: Dict[str, float] = field(default_factory=dict)


# Maps file extensions to relevant matrix section prefixes
EXTENSION_TO_SECTIONS: Dict[str, List[str]] = {
    # ---- Core Languages ----
    # Python
    ".py": ["PYTHON_TYPES", "PYTHON_API", "PYTHON_FUNCTIONS", "PYTHON_ML",
            "PYTHON_INFRA", "PYTHON_DATA"],
    # TypeScript
    ".ts": ["TS_TYPES", "TS_FUNCTIONS", "TS_API", "TS_MODELS", "TS_DEPENDENCIES",
            "INTERFACES", "TYPES"],
    ".tsx": ["TS_TYPES", "TS_FUNCTIONS", "TS_API", "TS_MODELS",
             "REACT_COMPONENTS", "REACT_HOOKS", "REACT_CONTEXT", "REACT_STATE",
             # State management libraries commonly used with TSX
             "REDUX_STORES", "REDUX_SLICES", "ZUSTAND_STORES",
             "JOTAI_ATOMS", "RECOIL_ATOMS", "MOBX_OBSERVABLES",
             # Data fetching commonly used with TSX
             "TANSTACK_QUERIES", "SWR_HOOKS", "APOLLO_QUERIES",
             # UI libraries commonly used with TSX
             "MUI_COMPONENTS", "ANTD_COMPONENTS", "CHAKRA_COMPONENTS",
             "SHADCN_COMPONENTS", "RADIX_COMPONENTS",
             "SC_COMPONENTS", "EM_COMPONENTS"],
    # JavaScript
    ".js": ["JS_TYPES", "JS_FUNCTIONS", "JS_API", "JS_MODELS", "JS_DEPENDENCIES"],
    ".jsx": ["JS_TYPES", "JS_FUNCTIONS", "JS_API",
             "REACT_COMPONENTS", "REACT_HOOKS", "REACT_CONTEXT", "REACT_STATE",
             "REDUX_STORES", "REDUX_SLICES", "ZUSTAND_STORES",
             "JOTAI_ATOMS", "RECOIL_ATOMS", "MOBX_OBSERVABLES",
             "TANSTACK_QUERIES", "SWR_HOOKS", "APOLLO_QUERIES",
             "MUI_COMPONENTS", "ANTD_COMPONENTS", "CHAKRA_COMPONENTS",
             "SHADCN_COMPONENTS", "RADIX_COMPONENTS",
             "SC_COMPONENTS", "EM_COMPONENTS"],
    ".mjs": ["JS_TYPES", "JS_FUNCTIONS", "JS_API", "JS_MODELS"],
    ".cjs": ["JS_TYPES", "JS_FUNCTIONS", "JS_API", "JS_MODELS"],
    # Go
    ".go": ["GO_TYPES", "GO_API", "GO_FUNCTIONS", "GO_DEPENDENCIES",
            "GO_GIN", "GO_ECHO", "GO_FIBER", "GO_CHI",
            "GO_GRPC", "GO_GORM", "GO_SQLX", "GO_COBRA"],
    # Java
    ".java": ["JAVA_TYPES", "JAVA_API", "JAVA_FUNCTIONS", "JAVA_MODELS",
              "JAVA_DEPENDENCIES"],
    # Kotlin
    ".kt": ["KOTLIN_TYPES", "KOTLIN_FUNCTIONS", "KOTLIN_API", "KOTLIN_MODELS",
            "KOTLIN_REPOSITORIES", "KOTLIN_DI", "KOTLIN_EXTENSIONS",
            "KOTLIN_COROUTINES"],
    ".kts": ["KOTLIN_TYPES", "KOTLIN_FUNCTIONS", "KOTLIN_API"],
    # C#
    ".cs": ["CSHARP_TYPES", "CSHARP_API", "CSHARP_FUNCTIONS", "CSHARP_MODELS",
            "CSHARP_DEPENDENCIES"],
    # Rust
    ".rs": ["RUST_TYPES", "RUST_API", "RUST_FUNCTIONS", "RUST_MODELS",
            "RUST_DEPENDENCIES",
            "ACTIX_WEB", "AXUM", "ROCKET", "WARP", "DIESEL", "SEAORM", "TAURI"],
    # Swift
    ".swift": ["SWIFT_TYPES", "SWIFT_FUNCTIONS", "SWIFT_API", "SWIFT_MODELS",
               "SWIFT_DEPENDENCIES"],
    # Ruby
    ".rb": ["RUBY_TYPES", "RUBY_FUNCTIONS", "RUBY_API", "RUBY_MODELS",
            "RUBY_DEPENDENCIES"],
    # PHP
    ".php": ["PHP_TYPES", "PHP_FUNCTIONS", "PHP_API", "PHP_MODELS",
             "PHP_DEPENDENCIES"],
    # Scala
    ".scala": ["SCALA_TYPES", "SCALA_FUNCTIONS", "SCALA_API", "SCALA_MODELS",
               "SCALA_DEPENDENCIES"],
    # R
    ".r": ["R_TYPES", "R_FUNCTIONS", "R_API", "R_MODELS", "R_DEPENDENCIES"],
    ".R": ["R_TYPES", "R_FUNCTIONS", "R_API", "R_MODELS", "R_DEPENDENCIES"],
    # Dart
    ".dart": ["DART_TYPES", "DART_FUNCTIONS", "DART_API", "DART_MODELS",
              "DART_DEPENDENCIES"],
    # Lua
    ".lua": ["LUA_TYPES", "LUA_FUNCTIONS", "LUA_API", "LUA_MODELS",
             "LUA_DEPENDENCIES"],
    # C
    ".c": ["C_TYPES", "C_FUNCTIONS", "C_API", "C_MODELS", "C_DEPENDENCIES"],
    ".h": ["C_TYPES", "C_FUNCTIONS", "C_API", "C_DEPENDENCIES"],
    # C++
    ".cpp": ["CPP_TYPES", "CPP_FUNCTIONS", "CPP_API", "CPP_MODELS", "CPP_DEPENDENCIES"],
    ".hpp": ["CPP_TYPES", "CPP_FUNCTIONS", "CPP_API", "CPP_DEPENDENCIES"],
    ".cc": ["CPP_TYPES", "CPP_FUNCTIONS", "CPP_API", "CPP_MODELS"],
    ".cxx": ["CPP_TYPES", "CPP_FUNCTIONS", "CPP_API", "CPP_MODELS"],
    ".hxx": ["CPP_TYPES", "CPP_FUNCTIONS", "CPP_API", "CPP_DEPENDENCIES"],
    # PowerShell
    ".ps1": ["POWERSHELL_TYPES", "POWERSHELL_FUNCTIONS", "POWERSHELL_API",
             "POWERSHELL_MODELS", "POWERSHELL_DEPENDENCIES"],
    ".psm1": ["POWERSHELL_TYPES", "POWERSHELL_FUNCTIONS", "POWERSHELL_API"],
    ".psd1": ["POWERSHELL_TYPES", "POWERSHELL_FUNCTIONS"],
    # Shell / Bash
    ".sh": ["BASH_FUNCTIONS", "BASH_VARIABLES", "BASH_API", "BASH_COMMANDS",
            "BASH_DEPENDENCIES"],
    ".bash": ["BASH_FUNCTIONS", "BASH_VARIABLES", "BASH_API", "BASH_COMMANDS"],
    ".zsh": ["BASH_FUNCTIONS", "BASH_VARIABLES", "BASH_API", "BASH_COMMANDS"],

    # ---- Data / Query Languages ----
    ".sql": ["SQL_TABLES", "SQL_VIEWS", "SQL_FUNCTIONS", "SQL_INDEXES",
             "SQL_SECURITY", "SQL_MIGRATIONS", "SQL_DEPENDENCIES"],

    # ---- Markup ----
    ".html": ["HTML_STRUCTURE", "HTML_FORMS", "HTML_META", "HTML_ACCESSIBILITY",
              "HTML_ASSETS", "HTML_COMPONENTS", "HTML_TEMPLATES",
              "HTMX_ATTRIBUTES", "HTMX_REQUESTS", "HTMX_EVENTS",
              "ALPINE_DIRECTIVES", "ALPINE_COMPONENTS",
              "STIMULUS_CONTROLLERS", "STIMULUS_TARGETS", "STIMULUS_ACTIONS",
              "STIMULUS_VALUES",
              "BOOTSTRAP_COMPONENTS", "BOOTSTRAP_GRID"],
    ".htm": ["HTML_STRUCTURE", "HTML_FORMS", "HTML_META",
             "HTMX_ATTRIBUTES", "ALPINE_DIRECTIVES",
             "STIMULUS_CONTROLLERS", "STIMULUS_TARGETS"],

    # ---- Stylesheets ----
    ".css": ["CSS_SELECTORS", "CSS_VARIABLES", "CSS_LAYOUT", "CSS_MEDIA",
             "CSS_ANIMATIONS", "CSS_PREPROCESSOR",
             "TAILWIND_CONFIG", "TAILWIND_UTILITIES", "TAILWIND_COMPONENTS"],
    ".scss": ["SASS_VARIABLES", "SASS_MIXINS", "SASS_FUNCTIONS", "SASS_MODULES",
              "SASS_NESTING", "SASS_DEPENDENCIES"],
    ".sass": ["SASS_VARIABLES", "SASS_MIXINS", "SASS_FUNCTIONS", "SASS_MODULES",
              "SASS_NESTING"],
    ".less": ["LESS_VARIABLES", "LESS_MIXINS", "LESS_FUNCTIONS", "LESS_IMPORTS",
              "LESS_RULESETS", "LESS_DEPENDENCIES"],
    ".pcss": ["POSTCSS_PLUGINS", "POSTCSS_CONFIG", "POSTCSS_TRANSFORMS",
              "POSTCSS_SYNTAX", "POSTCSS_DEPENDENCIES"],
    ".styl": ["CSS_SELECTORS", "CSS_VARIABLES", "CSS_LAYOUT"],

    # ---- Frontend Frameworks ----
    # Vue
    ".vue": ["VUE_COMPONENTS", "VUE_COMPOSABLES", "VUE_DIRECTIVES",
             "VUE_PLUGINS", "VUE_ROUTING",
             "PINIA_STORES", "PINIA_GETTERS", "PINIA_ACTIONS"],
    # Svelte
    ".svelte": ["SVELTE_COMPONENTS", "SVELTE_STORES", "SVELTE_ACTIONS",
                "SVELTEKIT_ROUTING", "SVELTE_RUNES"],
    # Astro
    ".astro": ["ASTRO_COMPONENTS", "ASTRO_ISLANDS", "ASTRO_ROUTING",
               "ASTRO_CONTENT", "ASTRO_API"],
    # SolidJS (uses .tsx/.jsx but detected via path patterns)
    # Qwik (uses .tsx but detected via path patterns)
    # Preact (uses .tsx/.jsx but detected via path patterns)
    # Lit (uses .ts/.js but detected via path patterns)
    # MDX
    ".mdx": ["REACT_COMPONENTS", "REACT_HOOKS",
             "ASTRO_COMPONENTS", "NEXT_PAGES"],

    # ---- Config files ----
    ".json": ["CONFIG_VARIABLES", "RUNBOOK"],
    ".yaml": ["INFRASTRUCTURE", "CONFIG_VARIABLES", "RUNBOOK"],
    ".yml": ["INFRASTRUCTURE", "CONFIG_VARIABLES", "RUNBOOK"],
    ".toml": ["CONFIG_VARIABLES", "RUNBOOK"],
    ".env": ["CONFIG_VARIABLES", "ENV_GAPS"],
    ".ini": ["CONFIG_VARIABLES"],

    # ---- API definition files ----
    ".proto": ["GRPC"],
    ".graphql": ["GRAPHQL"],
    ".gql": ["GRAPHQL"],
}

# Path patterns that indicate framework-specific context
PATH_PATTERN_SECTIONS: Dict[str, List[str]] = {
    # ---- Routing ----
    r"(route|router|routing)": [
        "ROUTES", "ROUTES_SEMANTIC", "HTTP_API",
        "VUE_ROUTING", "SVELTEKIT_ROUTING", "ASTRO_ROUTING",
        "NEXT_ROUTES", "REMIX_ROUTES", "QWIK_ROUTES",
    ],
    # ---- Controllers / Handlers ----
    r"(controller|ctrl)": ["CONTROLLERS", "HTTP_API"],
    # ---- Services / Providers ----
    r"(service|provider)": ["SERVICES", "ANGULAR_SERVICES"],
    # ---- Components ----
    r"(component|widget)": [
        "COMPONENTS", "REACT_COMPONENTS",
        "VUE_COMPONENTS", "SVELTE_COMPONENTS", "ASTRO_COMPONENTS",
        "SOLIDJS_COMPONENTS", "QWIK_COMPONENTS", "PREACT_COMPONENTS",
        "LIT_COMPONENTS", "ALPINE_COMPONENTS", "HTMX_ATTRIBUTES",
        "STIMULUS_CONTROLLERS",
        "BOOTSTRAP_COMPONENTS", "MUI_COMPONENTS", "ANTD_COMPONENTS",
        "CHAKRA_COMPONENTS", "SHADCN_COMPONENTS", "RADIX_COMPONENTS",
        "SC_COMPONENTS", "EM_COMPONENTS",
    ],
    # ---- State Management ----
    r"(store|state|redux|zustand|jotai|recoil|mobx|pinia|ngrx|xstate|valtio)": [
        "STORES", "REACT_STATE",
        "REDUX_STORES", "REDUX_SLICES", "REDUX_SELECTORS", "REDUX_MIDDLEWARE",
        "ZUSTAND_STORES", "ZUSTAND_SELECTORS", "ZUSTAND_ACTIONS",
        "JOTAI_ATOMS", "JOTAI_SELECTORS",
        "RECOIL_ATOMS", "RECOIL_SELECTORS",
        "MOBX_OBSERVABLES", "MOBX_COMPUTEDS", "MOBX_ACTIONS",
        "PINIA_STORES", "PINIA_GETTERS", "PINIA_ACTIONS",
        "NGRX_STORES", "NGRX_ACTIONS", "NGRX_EFFECTS", "NGRX_SELECTORS",
        "XSTATE_MACHINES", "XSTATE_STATES", "XSTATE_ACTIONS",
        "VALTIO_PROXIES", "VALTIO_SNAPSHOTS", "VALTIO_ACTIONS",
        "SVELTE_STORES", "SOLIDJS_STORES", "SOLIDJS_SIGNALS",
        "QWIK_SIGNALS", "PREACT_SIGNALS",
    ],
    # ---- Models / Entities ----
    r"(model|entity|schema)": ["SCHEMAS", "DATABASE"],
    r"(dto|transfer)": ["SCHEMAS"],
    # ---- Hooks / Composables ----
    r"(hook)": [
        "HOOKS", "REACT_HOOKS", "VUE_COMPOSABLES",
        "PREACT_HOOKS", "MUI_HOOKS", "ANTD_HOOKS",
        "CHAKRA_HOOKS", "SHADCN_HOOKS",
        "SWR_HOOKS", "RECOIL_HOOKS",
    ],
    # ---- Middleware ----
    r"(middleware|interceptor|guard|pipe)": [
        "MIDDLEWARE", "NESTJS_MODULES",
        "REDUX_MIDDLEWARE", "ZUSTAND_MIDDLEWARE",
        "JOTAI_MIDDLEWARE", "SWR_MIDDLEWARE",
    ],
    # ---- Testing ----
    r"(test|spec|__test__|__spec__)": ["RUNBOOK"],
    # ---- Storybook ----
    r"\.stories\.(ts|tsx|js|jsx|mdx)$": [
        "STORYBOOK_STORIES", "STORYBOOK_COMPONENTS", "STORYBOOK_API",
    ],
    r"\.storybook/": [
        "STORYBOOK_CONFIG", "STORYBOOK_ADDONS", "STORYBOOK_API",
    ],
    # ---- Infrastructure ----
    r"(docker|compose)": ["INFRASTRUCTURE"],
    r"(terraform|tf)": ["INFRASTRUCTURE"],
    r"(\.github|ci|cd|pipeline|workflow)": ["INFRASTRUCTURE"],
    # ---- Config ----
    r"(config|settings|env)": ["CONFIG_VARIABLES", "ENV_GAPS", "RUNBOOK",
                                "TAILWIND_CONFIG", "NEXT_CONFIG", "POSTCSS_CONFIG"],
    # ---- Database ----
    r"(migration|migrate)": ["DATABASE", "SQL_MIGRATIONS"],
    # ---- API ----
    r"(api|endpoint)": ["HTTP_API", "OPENAPI"],
    r"(websocket|ws|socket)": ["WEBSOCKET_EVENTS"],
    r"(grpc|proto)": ["GRPC"],
    r"(graphql|gql|resolver|mutation|query)": ["GRAPHQL",
                                                "APOLLO_QUERIES", "APOLLO_MUTATIONS"],
    # ---- Security ----
    r"(auth|login|jwt|oauth|session)": ["SECURITY"],
    # ---- ML / AI ----
    r"(ml|model|train|predict|inference)": ["PYTHON_ML"],
    # ---- Next.js ----
    r"(pages|app)/(api|route)": ["NEXT_PAGES", "NEXT_ROUTES", "NEXT_SERVER_ACTIONS"],
    r"(next\.config|next-env)": ["NEXT_CONFIG"],
    # ---- Remix ----
    r"(loader|action)s?\.(ts|js|tsx|jsx)": ["REMIX_LOADERS", "REMIX_ACTIONS", "REMIX_ROUTES"],
    # ---- SolidJS ----
    r"(solid|createSignal|createStore|createResource)": [
        "SOLIDJS_COMPONENTS", "SOLIDJS_SIGNALS", "SOLIDJS_STORES",
        "SOLIDJS_RESOURCES", "SOLIDJS_API",
    ],
    # ---- Qwik ----
    r"(qwik|useSignal|useStore|useTask)": [
        "QWIK_COMPONENTS", "QWIK_SIGNALS", "QWIK_TASKS",
        "QWIK_ROUTES", "QWIK_API",
    ],
    # ---- Preact ----
    r"(preact|preact-iso)": [
        "PREACT_COMPONENTS", "PREACT_HOOKS", "PREACT_SIGNALS",
        "PREACT_CONTEXTS", "PREACT_API",
    ],
    # ---- Lit ----
    r"(lit-element|lit-html|@lit)": [
        "LIT_COMPONENTS", "LIT_PROPERTIES", "LIT_TEMPLATES",
        "LIT_EVENTS", "LIT_API",
    ],
    # ---- Styling (path-based) ----
    r"(theme|styled|styles)": [
        "SC_THEME", "EM_THEME", "MUI_THEME", "ANTD_THEME",
        "CHAKRA_THEME", "SHADCN_THEME", "BOOTSTRAP_THEME",
        "RADIX_THEME", "TAILWIND_THEME",
        "CSS_VARIABLES", "CSS_LAYOUT",
    ],
    # ---- Data Fetching ----
    r"(tanstack|react-query)": [
        "TANSTACK_QUERIES", "TANSTACK_MUTATIONS", "TANSTACK_CACHE",
        "TANSTACK_PREFETCH", "TANSTACK_QUERY_API",
    ],
    r"(swr|useSWR)": ["SWR_HOOKS", "SWR_MUTATIONS", "SWR_CACHE", "SWR_API"],
    r"(apollo|useQuery|useMutation)": [
        "APOLLO_QUERIES", "APOLLO_MUTATIONS", "APOLLO_CACHE",
        "APOLLO_SUBSCRIPTIONS", "APOLLO_API",
    ],
}

# Sections that are always included regardless of file type
UNIVERSAL_SECTIONS = ["PROJECT", "BEST_PRACTICES", "RUNBOOK"]

# Max token budget for JIT context to prevent overwhelming the AI
DEFAULT_MAX_TOKENS = 30000


class JITContextProvider:
    """
    Provides Just-In-Time context from the matrix for a given file.

    When AI tools access a file, this provider determines which matrix
    sections are most relevant and returns them in priority order,
    respecting a token budget.
    """

    def __init__(
        self,
        sections: Dict[str, str],
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        """
        Initialize the JIT context provider.

        Args:
            sections: Parsed matrix sections {name: content}
            max_tokens: Maximum token budget for returned context
        """
        self._sections = sections
        self._max_tokens = max_tokens

    def get_context_for_file(
        self,
        file_path: str,
        include_universal: bool = True,
    ) -> str:
        """
        Get relevant matrix context for a specific file.

        Args:
            file_path: Relative or absolute file path
            include_universal: Whether to include universal sections (PROJECT, etc.)

        Returns:
            Formatted context string with relevant matrix slices
        """
        result = self.resolve_context(file_path, include_universal)
        return result.context

    def resolve_context(
        self,
        file_path: str,
        include_universal: bool = True,
    ) -> JITContextResult:
        """
        Resolve which matrix sections are relevant for a file.

        Args:
            file_path: Relative or absolute file path
            include_universal: Whether to include universal sections

        Returns:
            JITContextResult with resolved context and metadata
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        file_name = path.name.lower()
        path_str = str(path).lower()

        # Collect candidate sections with relevance scores
        candidates: Dict[str, float] = {}

        # 1. Extension-based sections (highest relevance for language match)
        ext_sections = EXTENSION_TO_SECTIONS.get(extension, [])
        for section_name in ext_sections:
            candidates[section_name] = candidates.get(section_name, 0) + 3.0

        # 2. Path pattern matching
        for pattern, sections in PATH_PATTERN_SECTIONS.items():
            if re.search(pattern, path_str, re.IGNORECASE):
                for section_name in sections:
                    candidates[section_name] = candidates.get(section_name, 0) + 2.0

        # 3. File name mentioned in matrix sections (very specific)
        for section_name, content in self._sections.items():
            if section_name == "_PREAMBLE":
                continue
            if file_name in content.lower() or path.stem.lower() in content.lower():
                candidates[section_name] = candidates.get(section_name, 0) + 4.0

        # 3b. Dependency-graph boosting: find sections containing files
        #     that co-occur with the target file in IMPLEMENTATION_LOGIC.
        #     Files that appear near each other in logic sections are likely
        #     import-related; boost those sections so the AI sees full context.
        co_occurring = self._find_co_occurring_files(file_name, path.stem.lower())
        if co_occurring:
            for section_name, content in self._sections.items():
                if section_name == "_PREAMBLE":
                    continue
                content_lower = content.lower()
                for co_file in co_occurring:
                    if co_file in content_lower:
                        candidates[section_name] = candidates.get(section_name, 0) + 2.0
                        break  # One co-occurrence per section is enough

        # 4. Universal sections
        if include_universal:
            for section_name in UNIVERSAL_SECTIONS:
                candidates[section_name] = candidates.get(section_name, 0) + 1.0

        # Sort by relevance score (descending)
        sorted_candidates = sorted(
            candidates.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        # Assemble context within token budget
        included_sections: List[str] = []
        parts: List[str] = []
        total_tokens = 0
        relevance_scores: Dict[str, float] = {}

        parts.append(f"# JIT Context for: {file_path}")
        parts.append("# Sections selected by relevance to file type and path\n")

        for section_name, score in sorted_candidates:
            if section_name not in self._sections:
                continue

            content = self._sections[section_name]
            section_tokens = len(content) // 4

            if total_tokens + section_tokens > self._max_tokens:
                # Try to include a truncated version
                remaining_tokens = self._max_tokens - total_tokens
                if remaining_tokens > 200:
                    # Include first N chars to fit budget
                    truncated = content[:remaining_tokens * 4]
                    last_newline = truncated.rfind("\n")
                    if last_newline > 0:
                        truncated = truncated[:last_newline]
                    truncated += f"\n# ... truncated ({section_tokens} tokens total)"
                    parts.append(truncated)
                    included_sections.append(section_name)
                    relevance_scores[section_name] = score
                    total_tokens += remaining_tokens
                break

            parts.append(content)
            included_sections.append(section_name)
            relevance_scores[section_name] = score
            total_tokens += section_tokens

        context_text = "\n\n".join(parts)

        return JITContextResult(
            file_path=file_path,
            sections_included=included_sections,
            context=context_text,
            token_estimate=total_tokens,
            relevance_scores=relevance_scores,
        )

    def get_sections_for_extension(self, extension: str) -> List[str]:
        """
        Get the list of relevant section names for a file extension.

        Args:
            extension: File extension (e.g., ".py", ".ts")

        Returns:
            List of section names
        """
        ext = extension.lower() if extension.startswith(".") else f".{extension.lower()}"
        return EXTENSION_TO_SECTIONS.get(ext, [])

    def get_available_sections(self) -> List[str]:
        """Get list of all available section names."""
        return [s for s in self._sections if s != "_PREAMBLE"]

    def _find_co_occurring_files(
        self, file_name: str, stem: str, max_results: int = 8,
    ) -> Set[str]:
        """
        Find file names that co-occur with the target in IMPLEMENTATION_LOGIC.

        Implementation logic sections list files as ``# filename.ext (...)``
        headers. If the target file appears in a block, other files listed
        nearby are likely import-related. We collect those neighbours.
        """
        logic = self._sections.get("IMPLEMENTATION_LOGIC", "")
        if not logic:
            return set()

        # Split into per-file blocks (lines starting with ``# filename``)
        blocks: List[List[str]] = []
        current: List[str] = []
        for line in logic.splitlines():
            if line.startswith("# ") and "(" in line:
                if current:
                    blocks.append(current)
                current = [line]
            else:
                current.append(line)
        if current:
            blocks.append(current)

        # Find blocks that reference the target file
        target_blocks: List[int] = []
        fn_lower = file_name.lower()
        for idx, block in enumerate(blocks):
            header = block[0].lower() if block else ""
            if fn_lower in header or stem in header:
                target_blocks.append(idx)

        if not target_blocks:
            return set()

        # Collect neighbour file names (±3 blocks around target)
        neighbours: Set[str] = set()
        for tidx in target_blocks:
            for offset in range(-3, 4):
                nidx = tidx + offset
                if 0 <= nidx < len(blocks) and nidx != tidx:
                    header = blocks[nidx][0]
                    # Extract filename from ``# filename.ext (...)``
                    if header.startswith("# "):
                        fname = header[2:].split("(")[0].strip().lower()
                        if fname:
                            neighbours.add(fname)
                            if len(neighbours) >= max_results:
                                return neighbours
        return neighbours
