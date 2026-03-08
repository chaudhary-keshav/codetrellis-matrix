"""
Astro Frontmatter Extractor v1.0

Extracts information from Astro frontmatter (--- fenced code blocks):
- Import statements (component, library, utility, content collection imports)
- Variable declarations (const/let with types)
- Data fetching patterns (fetch, Astro.glob, getCollection, getEntry, getEntries)
- Content collections (defineCollection, z schema, config.ts)
- Exported values (for getStaticPaths, API endpoints)
- Astro global API usage (Astro.redirect, Astro.url, Astro.cookies, Astro.response)
- TypeScript type definitions in frontmatter

Part of CodeTrellis v4.60 - Astro Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class AstroDataFetchInfo:
    """Information about data fetching in Astro frontmatter."""
    method: str = ""  # fetch, Astro.glob, getCollection, getEntry, getEntries
    line_number: int = 0
    target: str = ""  # URL or glob pattern or collection name
    has_await: bool = False
    is_static: bool = False  # Used in getStaticPaths


@dataclass
class AstroCollectionInfo:
    """Information about content collection usage."""
    name: str = ""  # Collection name
    line_number: int = 0
    schema_type: str = ""  # The zod schema type
    collection_type: str = "content"  # content, data
    has_references: bool = False  # z.reference()


@dataclass
class AstroFrontmatterInfo:
    """Information extracted from Astro frontmatter."""
    file_path: str = ""
    line_number: int = 1

    # Imports
    imports: List[Dict[str, Any]] = field(default_factory=list)
    has_typescript: bool = False

    # Variables
    variables: List[Dict[str, Any]] = field(default_factory=list)

    # Data fetching
    data_fetches: List[AstroDataFetchInfo] = field(default_factory=list)

    # Content collections
    collections: List[AstroCollectionInfo] = field(default_factory=list)
    is_collection_config: bool = False  # src/content/config.ts

    # Astro API
    uses_astro_redirect: bool = False
    uses_astro_url: bool = False
    uses_astro_cookies: bool = False
    uses_astro_response: bool = False
    uses_astro_request: bool = False
    uses_astro_params: bool = False
    uses_astro_slots: bool = False
    uses_astro_glob: bool = False
    uses_astro_locals: bool = False
    uses_astro_preferred_locale: bool = False
    uses_astro_current_locale: bool = False
    uses_image: bool = False
    uses_get_image: bool = False

    # Static paths
    has_get_static_paths: bool = False
    has_paginate: bool = False

    # Content
    has_content_render: bool = False  # entry.render()
    has_markdown_content: bool = False


class AstroFrontmatterExtractor:
    """Extracts frontmatter information from Astro files."""

    # Frontmatter delimiter
    FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---', re.DOTALL)

    # Import patterns
    IMPORT_NAMED = re.compile(
        r"import\s+\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )
    IMPORT_DEFAULT = re.compile(
        r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )
    IMPORT_SIDE_EFFECT = re.compile(
        r"import\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )
    IMPORT_TYPE = re.compile(
        r"import\s+type\s+\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )

    # Variable patterns
    VARIABLE_CONST = re.compile(
        r'(?:export\s+)?const\s+(\w+)(?:\s*:\s*([^=]+))?\s*=',
        re.MULTILINE
    )
    VARIABLE_LET = re.compile(
        r'let\s+(\w+)(?:\s*:\s*([^=]+))?\s*=',
        re.MULTILINE
    )

    # Data fetching patterns
    FETCH_PATTERN = re.compile(
        r'(?:await\s+)?fetch\s*\(\s*[`"\']([^`"\']+)',
        re.MULTILINE
    )
    ASTRO_GLOB = re.compile(
        r'Astro\.glob\s*(?:<[^>]*>)?\s*\(\s*[`"\']([^`"\']+)',
        re.MULTILINE
    )
    GET_COLLECTION = re.compile(
        r'(?:await\s+)?getCollection\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )
    GET_ENTRY = re.compile(
        r'(?:await\s+)?getEntry\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )
    GET_ENTRIES = re.compile(
        r'(?:await\s+)?getEntries\s*\(',
        re.MULTILINE
    )

    # Content collection config
    DEFINE_COLLECTION = re.compile(
        r'defineCollection\s*\(\s*\{',
        re.MULTILINE
    )
    Z_SCHEMA = re.compile(
        r'schema\s*:\s*z\.object\s*\(\s*\{',
        re.MULTILINE
    )
    COLLECTION_TYPE = re.compile(
        r"type\s*:\s*['\"](\w+)['\"]",
        re.MULTILINE
    )

    # Astro API patterns
    ASTRO_REDIRECT = re.compile(r'Astro\.redirect\s*\(', re.MULTILINE)
    ASTRO_URL = re.compile(r'Astro\.url\b', re.MULTILINE)
    ASTRO_COOKIES = re.compile(r'Astro\.cookies\b', re.MULTILINE)
    ASTRO_RESPONSE = re.compile(r'Astro\.response\b', re.MULTILINE)
    ASTRO_REQUEST = re.compile(r'Astro\.request\b', re.MULTILINE)
    ASTRO_PARAMS = re.compile(r'Astro\.params\b', re.MULTILINE)
    ASTRO_SLOTS_API = re.compile(r'Astro\.slots\b', re.MULTILINE)
    ASTRO_LOCALS = re.compile(r'Astro\.locals\b', re.MULTILINE)
    ASTRO_PREFERRED_LOCALE = re.compile(r'Astro\.preferredLocale\b', re.MULTILINE)
    ASTRO_CURRENT_LOCALE = re.compile(r'Astro\.currentLocale\b', re.MULTILINE)
    IMAGE_IMPORT = re.compile(r"from\s+['\"]astro:assets['\"]", re.MULTILINE)
    GET_IMAGE_CALL = re.compile(r'getImage\s*\(', re.MULTILINE)

    # Static paths
    GET_STATIC_PATHS = re.compile(
        r'(?:export\s+)?(?:async\s+)?function\s+getStaticPaths\b|'
        r'export\s+const\s+getStaticPaths\b',
        re.MULTILINE
    )
    PAGINATE_PATTERN = re.compile(r'paginate\s*\(', re.MULTILINE)

    # Content render
    CONTENT_RENDER = re.compile(r'\.render\s*\(\s*\)', re.MULTILINE)

    # TypeScript detection
    TS_PATTERN = re.compile(
        r':\s*(?:string|number|boolean|any|void|never|unknown|Record|Array|Promise)\b|'
        r'(?:interface|type)\s+\w+\s*[{=<]|'
        r'<\w+(?:,\s*\w+)*>',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract frontmatter information from an Astro file.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with frontmatter information
        """
        result = AstroFrontmatterInfo(file_path=file_path)

        # Extract frontmatter
        fm_match = self.FRONTMATTER_PATTERN.search(content)
        if not fm_match:
            # Could be a .ts config file (content/config.ts)
            if file_path.endswith('.ts') or file_path.endswith('.js'):
                frontmatter = content
            else:
                return {"frontmatter": result}
        else:
            frontmatter = fm_match.group(1)

        # Check for TypeScript
        result.has_typescript = bool(self.TS_PATTERN.search(frontmatter))

        # Collection config detection
        if 'config' in file_path and ('content/' in file_path or 'content\\' in file_path):
            result.is_collection_config = True
            self._extract_collections(frontmatter, result)

        # Imports
        self._extract_imports(frontmatter, result)

        # Variables
        self._extract_variables(frontmatter, result)

        # Data fetching
        self._extract_data_fetches(frontmatter, result)

        # Astro API usage
        result.uses_astro_redirect = bool(self.ASTRO_REDIRECT.search(frontmatter))
        result.uses_astro_url = bool(self.ASTRO_URL.search(frontmatter))
        result.uses_astro_cookies = bool(self.ASTRO_COOKIES.search(frontmatter))
        result.uses_astro_response = bool(self.ASTRO_RESPONSE.search(frontmatter))
        result.uses_astro_request = bool(self.ASTRO_REQUEST.search(frontmatter))
        result.uses_astro_params = bool(self.ASTRO_PARAMS.search(frontmatter))
        result.uses_astro_slots = bool(self.ASTRO_SLOTS_API.search(frontmatter))
        result.uses_astro_locals = bool(self.ASTRO_LOCALS.search(frontmatter))
        result.uses_astro_preferred_locale = bool(self.ASTRO_PREFERRED_LOCALE.search(frontmatter))
        result.uses_astro_current_locale = bool(self.ASTRO_CURRENT_LOCALE.search(frontmatter))
        result.uses_image = bool(self.IMAGE_IMPORT.search(frontmatter))
        result.uses_get_image = bool(self.GET_IMAGE_CALL.search(frontmatter))

        # Static paths
        result.has_get_static_paths = bool(self.GET_STATIC_PATHS.search(frontmatter))
        result.has_paginate = bool(self.PAGINATE_PATTERN.search(frontmatter))

        # Content render
        result.has_content_render = bool(self.CONTENT_RENDER.search(frontmatter))

        # Astro.glob
        result.uses_astro_glob = bool(self.ASTRO_GLOB.search(frontmatter))

        return {"frontmatter": result}

    def _extract_imports(self, frontmatter: str, result: AstroFrontmatterInfo) -> None:
        """Extract import statements from frontmatter."""
        for m in self.IMPORT_TYPE.finditer(frontmatter):
            names = [n.strip() for n in m.group(1).split(',') if n.strip()]
            line = frontmatter[:m.start()].count('\n') + 1
            result.imports.append({
                "source": m.group(2),
                "named_imports": names,
                "is_type_import": True,
                "is_default_import": False,
                "line": line,
            })

        for m in self.IMPORT_NAMED.finditer(frontmatter):
            # Skip type imports already captured
            full_match = m.group(0)
            if 'import type' in full_match:
                continue
            names = [n.strip() for n in m.group(1).split(',') if n.strip()]
            line = frontmatter[:m.start()].count('\n') + 1
            result.imports.append({
                "source": m.group(2),
                "named_imports": names,
                "is_type_import": False,
                "is_default_import": False,
                "line": line,
            })

        for m in self.IMPORT_DEFAULT.finditer(frontmatter):
            # Skip named imports already captured
            full_match = m.group(0)
            if '{' in full_match or 'import type' in full_match:
                continue
            line = frontmatter[:m.start()].count('\n') + 1
            result.imports.append({
                "source": m.group(2),
                "named_imports": [m.group(1)],
                "is_type_import": False,
                "is_default_import": True,
                "line": line,
            })

    def _extract_variables(self, frontmatter: str, result: AstroFrontmatterInfo) -> None:
        """Extract variable declarations from frontmatter."""
        for m in self.VARIABLE_CONST.finditer(frontmatter):
            name = m.group(1)
            type_ann = m.group(2).strip() if m.group(2) else ""
            line = frontmatter[:m.start()].count('\n') + 1
            result.variables.append({
                "name": name,
                "type": type_ann[:60],
                "kind": "const",
                "is_exported": m.group(0).startswith('export'),
                "line": line,
            })

        for m in self.VARIABLE_LET.finditer(frontmatter):
            name = m.group(1)
            type_ann = m.group(2).strip() if m.group(2) else ""
            line = frontmatter[:m.start()].count('\n') + 1
            result.variables.append({
                "name": name,
                "type": type_ann[:60],
                "kind": "let",
                "is_exported": False,
                "line": line,
            })

    def _extract_data_fetches(self, frontmatter: str, result: AstroFrontmatterInfo) -> None:
        """Extract data fetching patterns from frontmatter."""
        for m in self.FETCH_PATTERN.finditer(frontmatter):
            line = frontmatter[:m.start()].count('\n') + 1
            result.data_fetches.append(AstroDataFetchInfo(
                method="fetch",
                line_number=line,
                target=m.group(1)[:80],
                has_await='await' in frontmatter[max(0, m.start() - 10):m.start()],
            ))

        for m in self.ASTRO_GLOB.finditer(frontmatter):
            line = frontmatter[:m.start()].count('\n') + 1
            result.data_fetches.append(AstroDataFetchInfo(
                method="Astro.glob",
                line_number=line,
                target=m.group(1)[:80],
                is_static=True,
            ))

        for m in self.GET_COLLECTION.finditer(frontmatter):
            line = frontmatter[:m.start()].count('\n') + 1
            result.data_fetches.append(AstroDataFetchInfo(
                method="getCollection",
                line_number=line,
                target=m.group(1),
                has_await='await' in frontmatter[max(0, m.start() - 10):m.start()],
            ))

        for m in self.GET_ENTRY.finditer(frontmatter):
            line = frontmatter[:m.start()].count('\n') + 1
            result.data_fetches.append(AstroDataFetchInfo(
                method="getEntry",
                line_number=line,
                target=m.group(1),
                has_await='await' in frontmatter[max(0, m.start() - 10):m.start()],
            ))

        for m in self.GET_ENTRIES.finditer(frontmatter):
            line = frontmatter[:m.start()].count('\n') + 1
            result.data_fetches.append(AstroDataFetchInfo(
                method="getEntries",
                line_number=line,
                has_await='await' in frontmatter[max(0, m.start() - 10):m.start()],
            ))

    def _extract_collections(self, content: str, result: AstroFrontmatterInfo) -> None:
        """Extract content collection definitions from config files."""
        # Look for defineCollection calls
        pattern = re.compile(
            r"(\w+)\s*:\s*defineCollection\s*\(\s*\{",
            re.MULTILINE
        )
        for m in pattern.finditer(content):
            name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            # Determine collection type
            col_type = "content"
            block_start = m.end()
            block = content[block_start:block_start + 200]
            type_match = self.COLLECTION_TYPE.search(block)
            if type_match:
                col_type = type_match.group(1)

            has_refs = 'reference(' in block

            result.collections.append(AstroCollectionInfo(
                name=name,
                line_number=line,
                collection_type=col_type,
                has_references=has_refs,
            ))
