"""
Valtio API Extractor for CodeTrellis

Extracts Valtio API-level metadata:
- Import analysis: valtio, valtio/vanilla, valtio/utils, valtio/vanilla/utils, valtio/react
- Version detection: v1.x vs v2.x indicators
- TypeScript type usage: Snapshot<T>, INTERNAL_Snapshot
- Integration detection: derive-valtio, valtio-reactive, use-valtio,
  eslint-plugin-valtio, proxy-compare, React, Next.js
- Deprecated API usage: watch(), derive(), underive(), proxyWithComputed()
- Ecosystem plugin detection

Supports:
- Valtio v1.x (valtio, valtio/utils)
- Valtio v2.x (valtio/vanilla, valtio/vanilla/utils, valtio/react, valtio/react/utils)

Part of CodeTrellis v4.56 - Valtio Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ValtioImportInfo:
    """Information about a Valtio import statement."""
    file: str = ""
    line_number: int = 0
    source: str = ""  # e.g., 'valtio', 'valtio/vanilla', 'valtio/utils'
    imported_names: List[str] = field(default_factory=list)
    is_default_import: bool = False
    is_namespace_import: bool = False  # import * as valtio from 'valtio'
    is_dynamic_import: bool = False  # import('valtio')
    is_require: bool = False  # require('valtio')


@dataclass
class ValtioIntegrationInfo:
    """Information about Valtio ecosystem integration."""
    file: str = ""
    line_number: int = 0
    integration: str = ""  # 'derive-valtio', 'valtio-reactive', 'react', etc.
    imported_names: List[str] = field(default_factory=list)


@dataclass
class ValtioTypeInfo:
    """Information about Valtio TypeScript type usage."""
    file: str = ""
    line_number: int = 0
    type_name: str = ""  # e.g., 'Snapshot', 'INTERNAL_Snapshot'
    generic_param: str = ""  # The T in Snapshot<T>
    context: str = ""  # 'type_annotation', 'type_alias', 'generic_constraint'


class ValtioApiExtractor:
    """
    Extracts Valtio API-level metadata from source code.

    Detects:
    - Import statements from all Valtio subpaths
    - Version indicators (v1 vs v2)
    - TypeScript type usage
    - Ecosystem integrations
    - Deprecated API usage
    """

    # Named import: import { x, y } from 'valtio...'
    NAMED_IMPORT_PATTERN = re.compile(
        r'''import\s*\{([^}]+)\}\s*from\s*['"](valtio(?:/[\w-]+)*)['"]''',
        re.MULTILINE
    )

    # Default import: import valtio from 'valtio'
    DEFAULT_IMPORT_PATTERN = re.compile(
        r'''import\s+(\w+)\s+from\s*['"](valtio(?:/[\w-]+)*)['"]''',
        re.MULTILINE
    )

    # Namespace import: import * as valtio from 'valtio'
    NAMESPACE_IMPORT_PATTERN = re.compile(
        r'''import\s+\*\s+as\s+(\w+)\s+from\s*['"](valtio(?:/[\w-]+)*)['"]''',
        re.MULTILINE
    )

    # Dynamic import: import('valtio...')
    DYNAMIC_IMPORT_PATTERN = re.compile(
        r'''import\s*\(\s*['"](valtio(?:/[\w-]+)*)['"]''',
        re.MULTILINE
    )

    # require('valtio...')
    REQUIRE_PATTERN = re.compile(
        r'''require\s*\(\s*['"](valtio(?:/[\w-]+)*)['"]''',
        re.MULTILINE
    )

    # Ecosystem packages
    ECOSYSTEM_IMPORT_PATTERN = re.compile(
        r'''(?:import\s+(?:\{[^}]+\}|\*\s+as\s+\w+|\w+)\s+from|require\s*\()\s*'''
        r'''['"](derive-valtio|valtio-reactive|use-valtio|eslint-plugin-valtio|proxy-compare)['"]''',
        re.MULTILINE
    )

    # Snapshot<T> type usage
    SNAPSHOT_TYPE_PATTERN = re.compile(
        r'(?:Snapshot|INTERNAL_Snapshot)\s*<\s*([^>]+)\s*>',
        re.MULTILINE
    )

    # Type alias/annotation with Snapshot
    SNAPSHOT_TYPE_ALIAS_PATTERN = re.compile(
        r'(?:type\s+(\w+)\s*=\s*(?:Snapshot|INTERNAL_Snapshot)\s*<([^>]+)>|'
        r':\s*(?:Snapshot|INTERNAL_Snapshot)\s*<([^>]+)>)',
        re.MULTILINE
    )

    # Deprecated APIs
    DEPRECATED_DERIVE_PATTERN = re.compile(
        r'''(?:derive|underive)\s*\(''',
        re.MULTILINE
    )

    DEPRECATED_PROXY_WITH_COMPUTED = re.compile(
        r'proxyWithComputed\s*\(',
        re.MULTILINE
    )

    DEPRECATED_ADD_COMPUTED = re.compile(
        r'addComputed\s*\(',
        re.MULTILINE
    )

    # V2 indicators
    V2_VANILLA_IMPORT = re.compile(
        r'''from\s*['"]valtio/vanilla(?:/utils)?['"]''',
        re.MULTILINE
    )

    V2_REACT_IMPORT = re.compile(
        r'''from\s*['"]valtio/react(?:/utils)?['"]''',
        re.MULTILINE
    )

    V2_UNSTABLE_PATTERN = re.compile(
        r'unstable_(?:enableOp|deepProxy|getInternalStates|replaceInternalFunction)',
        re.MULTILINE
    )

    V2_IS_PROXY_PATTERN = re.compile(
        r'isProxy(?:Map|Set)\s*\(',
        re.MULTILINE
    )

    # V1 indicators
    V1_DERIVE_FROM_UTILS = re.compile(
        r'''import\s*\{[^}]*(?:derive|underive|addComputed|proxyWithComputed)[^}]*\}\s*'''
        r'''from\s*['"]valtio/utils['"]''',
        re.MULTILINE
    )

    def __init__(self) -> None:
        """Initialize the API extractor."""

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Valtio API metadata from source code.

        Args:
            content: Source code content.
            file_path: Path to source file.

        Returns:
            Dictionary with 'imports', 'integrations', 'types',
            'detected_version', 'deprecated_apis', and 'detected_features'.
        """
        imports: List[ValtioImportInfo] = []
        integrations: List[ValtioIntegrationInfo] = []
        types: List[ValtioTypeInfo] = []

        # Extract named imports
        for match in self.NAMED_IMPORT_PATTERN.finditer(content):
            names_str = match.group(1)
            source = match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            names = [n.strip().split(' as ')[0].strip()
                     for n in names_str.split(',') if n.strip()]

            imports.append(ValtioImportInfo(
                file=file_path,
                line_number=line_num,
                source=source,
                imported_names=names,
            ))

        # Extract default imports
        for match in self.DEFAULT_IMPORT_PATTERN.finditer(content):
            name = match.group(1)
            source = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            imports.append(ValtioImportInfo(
                file=file_path,
                line_number=line_num,
                source=source,
                imported_names=[name],
                is_default_import=True,
            ))

        # Extract namespace imports
        for match in self.NAMESPACE_IMPORT_PATTERN.finditer(content):
            name = match.group(1)
            source = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            imports.append(ValtioImportInfo(
                file=file_path,
                line_number=line_num,
                source=source,
                imported_names=[name],
                is_namespace_import=True,
            ))

        # Extract dynamic imports
        for match in self.DYNAMIC_IMPORT_PATTERN.finditer(content):
            source = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            imports.append(ValtioImportInfo(
                file=file_path,
                line_number=line_num,
                source=source,
                is_dynamic_import=True,
            ))

        # Extract require() calls
        for match in self.REQUIRE_PATTERN.finditer(content):
            source = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            imports.append(ValtioImportInfo(
                file=file_path,
                line_number=line_num,
                source=source,
                is_require=True,
            ))

        # Extract ecosystem integrations
        for match in self.ECOSYSTEM_IMPORT_PATTERN.finditer(content):
            pkg = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Re-parse to get imported names
            import_names = []
            line_text = content.split('\n')[line_num - 1]
            brace_match = re.search(r'\{([^}]+)\}', line_text)
            if brace_match:
                import_names = [n.strip().split(' as ')[0].strip()
                                for n in brace_match.group(1).split(',')
                                if n.strip()]

            integrations.append(ValtioIntegrationInfo(
                file=file_path,
                line_number=line_num,
                integration=pkg,
                imported_names=import_names,
            ))

        # Detect React integration (useSnapshot implies React)
        if re.search(r'useSnapshot\s*\(', content):
            # Only add if not already in integrations
            if not any(i.integration == 'react' for i in integrations):
                integrations.append(ValtioIntegrationInfo(
                    file=file_path,
                    line_number=0,
                    integration='react',
                    imported_names=['useSnapshot'],
                ))

        # Extract TypeScript type usage
        for match in self.SNAPSHOT_TYPE_ALIAS_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            alias_name = match.group(1) or ""
            param = match.group(2) or match.group(3) or ""

            type_name_match = re.search(
                r'(INTERNAL_Snapshot|Snapshot)',
                content[match.start():match.end()]
            )
            type_name = type_name_match.group(1) if type_name_match else "Snapshot"

            context = 'type_alias' if alias_name else 'type_annotation'

            types.append(ValtioTypeInfo(
                file=file_path,
                line_number=line_num,
                type_name=type_name,
                generic_param=param.strip(),
                context=context,
            ))

        # Detect version
        detected_version = self._detect_version(content)

        # Detect deprecated APIs
        deprecated_apis = []
        if self.DEPRECATED_DERIVE_PATTERN.search(content):
            deprecated_apis.append('derive/underive')
        if self.DEPRECATED_PROXY_WITH_COMPUTED.search(content):
            deprecated_apis.append('proxyWithComputed')
        if self.DEPRECATED_ADD_COMPUTED.search(content):
            deprecated_apis.append('addComputed')

        # Detect features used
        detected_features = self._detect_features(content)

        return {
            'imports': imports,
            'integrations': integrations,
            'types': types,
            'detected_version': detected_version,
            'deprecated_apis': deprecated_apis,
            'detected_features': detected_features,
        }

    def _detect_version(self, content: str) -> str:
        """Detect Valtio version from import patterns and API usage.

        Returns:
            'v2' if v2 indicators found, 'v1' if v1-only indicators,
            'unknown' otherwise.
        """
        v2_signals = 0
        v1_signals = 0

        if self.V2_VANILLA_IMPORT.search(content):
            v2_signals += 2
        if self.V2_REACT_IMPORT.search(content):
            v2_signals += 2
        if self.V2_UNSTABLE_PATTERN.search(content):
            v2_signals += 1
        if self.V2_IS_PROXY_PATTERN.search(content):
            v2_signals += 1
        if self.V1_DERIVE_FROM_UTILS.search(content):
            v1_signals += 2
        if self.DEPRECATED_PROXY_WITH_COMPUTED.search(content):
            v1_signals += 1
        if self.DEPRECATED_ADD_COMPUTED.search(content):
            v1_signals += 1

        if v2_signals > 0 and v2_signals > v1_signals:
            return 'v2'
        if v1_signals > 0:
            return 'v1'
        return 'unknown'

    @staticmethod
    def _detect_features(content: str) -> List[str]:
        """Detect which Valtio features are used."""
        features = []
        feature_checks = [
            (r'proxy\s*\(', 'proxy'),
            (r'useSnapshot\s*\(', 'useSnapshot'),
            (r'subscribe\s*\(', 'subscribe'),
            (r'snapshot\s*\(', 'snapshot'),
            (r'ref\s*\(', 'ref'),
            (r'subscribeKey\s*\(', 'subscribeKey'),
            (r'watch\s*\(', 'watch'),
            (r'devtools\s*\(', 'devtools'),
            (r'proxyMap\s*\(', 'proxyMap'),
            (r'proxySet\s*\(', 'proxySet'),
            (r'useProxy\s*\(', 'useProxy'),
            (r'deepClone\s*\(', 'deepClone'),
            (r'getVersion\s*\(', 'getVersion'),
            (r'unstable_deepProxy\s*\(', 'deepProxy'),
            (r'unstable_enableOp\s*\(', 'enableOp'),
            (r'derive\s*\(', 'derive'),
            (r'underive\s*\(', 'underive'),
        ]
        for pattern, feature in feature_checks:
            if re.search(pattern, content):
                features.append(feature)
        return features
