"""
SWR API Extractor for CodeTrellis

Extracts SWR API patterns, imports, integrations, and ecosystem usage:
- Import patterns (swr, swr/infinite, swr/mutation, swr/subscription,
  swr/immutable, swr/_internal)
- TypeScript types: SWRResponse, SWRConfiguration, SWRInfiniteResponse,
  SWRMutationResponse, SWRSubscriptionResponse, Key, Fetcher, Middleware,
  BareFetcher, MutatorCallback, MutatorOptions, Cache
- HTTP client integrations: fetch, axios, ky, got, ofetch, graphql-request
- Next.js integration (getServerSideProps, getStaticProps, ISR, SWR + SSR)
- React Native integration
- Testing patterns
- Version detection (v0.x, v1.x, v2.x)

Supports:
- swr v0.x (single swr package, initialData)
- swr v1.x (swr/infinite, SWRConfig, fallback, cache provider, middleware)
- swr v2.x (swr/mutation, swr/subscription, preload, keepPreviousData,
             optimisticData, throwOnError, React 18 concurrent)

Part of CodeTrellis v4.58 - SWR Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SWRImportInfo:
    """Information about SWR imports."""
    source: str  # swr, swr/infinite, swr/mutation, etc.
    file: str = ""
    line_number: int = 0
    imported_names: List[str] = field(default_factory=list)
    is_default: bool = False
    is_type_import: bool = False
    subpath: str = ""  # infinite, mutation, subscription, immutable, _internal


@dataclass
class SWRIntegrationInfo:
    """Information about SWR integration with other libraries."""
    integration_type: str  # http-client, nextjs, react-native, testing, graphql
    file: str = ""
    line_number: int = 0
    library: str = ""  # axios, fetch, ky, next, etc.
    pattern: str = ""  # Description of integration pattern


@dataclass
class SWRTypeInfo:
    """Information about SWR TypeScript type usage."""
    name: str
    file: str = ""
    line_number: int = 0
    type_category: str = ""  # response, configuration, key, fetcher, middleware, cache
    type_expression: str = ""


class SWRApiExtractor:
    """
    Extracts SWR API patterns, imports, integrations, and TypeScript types.

    Detects:
    - Import patterns across all SWR subpackages
    - HTTP client and data fetching integrations
    - Next.js integration patterns
    - React Native integration
    - Testing patterns
    - TypeScript utility type usage
    - Version-specific API usage
    """

    # ─── Import Patterns ──────────────────────────────────────────

    IMPORT_PATTERN = re.compile(
        r"(?:import\s+(?:type\s+)?(?:\{([^}]+)\}|(\w+))\s+from\s+['\"]"
        r"(swr(?:/[\w-]+)?)['\"]|"
        r"require\(['\"]"
        r"(swr(?:/[\w-]+)?)['\"]"
        r"\))",
        re.MULTILINE
    )

    # Type-only imports
    TYPE_IMPORT_PATTERN = re.compile(
        r"import\s+type\s+\{([^}]+)\}\s+from\s+['\"]"
        r"(swr(?:/[\w-]+)?)['\"]",
        re.MULTILINE
    )

    # ─── TypeScript Type Usage ────────────────────────────────────

    SWR_TYPE_PATTERN = re.compile(
        r'(?:type|interface)\s+(\w+)\s*=?\s*'
        r'(SWRResponse|SWRConfiguration|SWRInfiniteResponse|'
        r'SWRMutationResponse|SWRSubscriptionResponse|'
        r'Key|Fetcher|BareFetcher|Middleware|'
        r'MutatorCallback|MutatorOptions|Cache|'
        r'SWRInfiniteConfiguration|SWRMutationConfiguration)\s*(?:<([^>]*)>)?',
        re.MULTILINE
    )

    TS_TYPE_ANNOTATION_PATTERN = re.compile(
        r':\s*(SWRResponse|SWRConfiguration|SWRInfiniteResponse|'
        r'SWRMutationResponse|Key|Fetcher|Middleware|Cache)\s*(?:<([^>]*)>)?',
        re.MULTILINE
    )

    # ─── Integration Patterns ─────────────────────────────────────

    HTTP_CLIENT_PATTERNS = {
        'axios': re.compile(
            r"from\s+['\"]axios['\"]|require\(['\"]axios['\"]\)|"
            r"axios\s*\.\s*(?:get|post|put|patch|delete|request)\s*\(",
            re.MULTILINE
        ),
        'ky': re.compile(
            r"from\s+['\"]ky['\"]|ky\s*\.\s*(?:get|post|put|patch|delete)\s*\(",
            re.MULTILINE
        ),
        'fetch': re.compile(
            r'\bfetch\s*\(\s*[\'"`]|window\.fetch|globalThis\.fetch',
            re.MULTILINE
        ),
        'got': re.compile(
            r"from\s+['\"]got['\"]",
            re.MULTILINE
        ),
        'ofetch': re.compile(
            r"from\s+['\"]ofetch['\"]|\$fetch\s*\(",
            re.MULTILINE
        ),
    }

    # Next.js integration
    NEXTJS_PATTERNS = {
        'next-swr-ssr': re.compile(
            r"getServerSideProps.*(?:useSWR|SWRConfig|fallback)|"
            r"getStaticProps.*(?:useSWR|SWRConfig|fallback)",
            re.MULTILINE | re.DOTALL
        ),
        'next-api-route': re.compile(
            r"from\s+['\"]next[/'\"]",
            re.MULTILINE
        ),
    }

    # GraphQL integration
    GRAPHQL_PATTERNS = {
        'graphql-request': re.compile(
            r"from\s+['\"]graphql-request['\"]|new\s+GraphQLClient\s*\(",
            re.MULTILINE
        ),
        'graphql': re.compile(
            r"from\s+['\"]graphql['\"]|\bgql\s*`",
            re.MULTILINE
        ),
    }

    # Testing patterns
    TESTING_PATTERNS = {
        'testing-library': re.compile(
            r"from\s+['\"]@testing-library/react['\"]|renderHook\s*\(",
            re.MULTILINE
        ),
        'msw': re.compile(
            r"from\s+['\"]msw['\"]|setupServer\s*\(|setupWorker\s*\(",
            re.MULTILINE
        ),
        'jest': re.compile(
            r'\bdescribe\s*\(|it\s*\(|test\s*\(|expect\s*\(',
            re.MULTILINE
        ),
        'vitest': re.compile(
            r"from\s+['\"]vitest['\"]",
            re.MULTILINE
        ),
    }

    # React Native
    REACT_NATIVE_PATTERN = re.compile(
        r"from\s+['\"]react-native['\"]|from\s+['\"]@react-native",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract all SWR API patterns from source code."""
        result: Dict[str, Any] = {
            'imports': [],
            'integrations': [],
            'types': [],
        }

        # Extract imports
        for match in self.IMPORT_PATTERN.finditer(content):
            named_imports = match.group(1) or ""
            default_import = match.group(2) or ""
            source = match.group(3) or match.group(4) or ""
            line_num = content[:match.start()].count('\n') + 1

            imported_names = []
            if named_imports:
                imported_names = [n.strip().split(' as ')[0].strip()
                                  for n in named_imports.split(',') if n.strip()]

            subpath = ""
            if '/' in source:
                subpath = source.split('/', 1)[1]

            imp = SWRImportInfo(
                source=source,
                file=file_path,
                line_number=line_num,
                imported_names=imported_names,
                is_default=bool(default_import),
                subpath=subpath,
            )
            result['imports'].append(imp)

        # Extract type-only imports
        for match in self.TYPE_IMPORT_PATTERN.finditer(content):
            named_imports = match.group(1) or ""
            source = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1

            imported_names = [n.strip().split(' as ')[0].strip()
                              for n in named_imports.split(',') if n.strip()]

            subpath = ""
            if '/' in source:
                subpath = source.split('/', 1)[1]

            imp = SWRImportInfo(
                source=source,
                file=file_path,
                line_number=line_num,
                imported_names=imported_names,
                is_type_import=True,
                subpath=subpath,
            )
            result['imports'].append(imp)

        # Extract TypeScript type usage
        for match in self.SWR_TYPE_PATTERN.finditer(content):
            name = match.group(1)
            type_name = match.group(2)
            generics = match.group(3) or ""
            line_num = content[:match.start()].count('\n') + 1

            category = "response"
            if "Configuration" in type_name:
                category = "configuration"
            elif "Key" in type_name:
                category = "key"
            elif "Fetcher" in type_name:
                category = "fetcher"
            elif "Middleware" in type_name:
                category = "middleware"
            elif "Cache" in type_name:
                category = "cache"

            result['types'].append(SWRTypeInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                type_category=category,
                type_expression=f"{type_name}<{generics}>" if generics else type_name,
            ))

        for match in self.TS_TYPE_ANNOTATION_PATTERN.finditer(content):
            type_name = match.group(1)
            generics = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1

            category = "response"
            if "Configuration" in type_name:
                category = "configuration"
            elif "Key" in type_name:
                category = "key"
            elif "Fetcher" in type_name:
                category = "fetcher"
            elif "Middleware" in type_name:
                category = "middleware"

            result['types'].append(SWRTypeInfo(
                name=type_name,
                file=file_path,
                line_number=line_num,
                type_category=category,
                type_expression=f"{type_name}<{generics}>" if generics else type_name,
            ))

        # Extract integrations
        for name, pattern in self.HTTP_CLIENT_PATTERNS.items():
            if pattern.search(content):
                first_match = pattern.search(content)
                line_num = content[:first_match.start()].count('\n') + 1 if first_match else 0
                result['integrations'].append(SWRIntegrationInfo(
                    integration_type="http-client",
                    file=file_path,
                    line_number=line_num,
                    library=name,
                    pattern=f"{name} HTTP client",
                ))

        for name, pattern in self.NEXTJS_PATTERNS.items():
            if pattern.search(content):
                first_match = pattern.search(content)
                line_num = content[:first_match.start()].count('\n') + 1 if first_match else 0
                result['integrations'].append(SWRIntegrationInfo(
                    integration_type="nextjs",
                    file=file_path,
                    line_number=line_num,
                    library="next",
                    pattern=name,
                ))

        for name, pattern in self.GRAPHQL_PATTERNS.items():
            if pattern.search(content):
                first_match = pattern.search(content)
                line_num = content[:first_match.start()].count('\n') + 1 if first_match else 0
                result['integrations'].append(SWRIntegrationInfo(
                    integration_type="graphql",
                    file=file_path,
                    line_number=line_num,
                    library=name,
                    pattern=f"{name} GraphQL integration",
                ))

        for name, pattern in self.TESTING_PATTERNS.items():
            if pattern.search(content):
                first_match = pattern.search(content)
                line_num = content[:first_match.start()].count('\n') + 1 if first_match else 0
                result['integrations'].append(SWRIntegrationInfo(
                    integration_type="testing",
                    file=file_path,
                    line_number=line_num,
                    library=name,
                    pattern=f"{name} testing integration",
                ))

        if self.REACT_NATIVE_PATTERN.search(content):
            first_match = self.REACT_NATIVE_PATTERN.search(content)
            line_num = content[:first_match.start()].count('\n') + 1 if first_match else 0
            result['integrations'].append(SWRIntegrationInfo(
                integration_type="react-native",
                file=file_path,
                line_number=line_num,
                library="react-native",
                pattern="React Native integration",
            ))

        return result
