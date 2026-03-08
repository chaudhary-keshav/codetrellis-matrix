"""
RustAttributeExtractor - Extracts Rust attributes and derive macros.

This extractor parses Rust source code and extracts:
- Derive macros (#[derive(...)])
- Custom proc macro attributes
- cfg/cfg_attr conditional compilation
- Feature flags
- serde attributes
- Crate-level attributes (#![...])
- Test/benchmark attributes
- Allow/deny/warn lint attributes

Part of CodeTrellis v4.14 - Rust Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RustDeriveInfo:
    """Information about a derive macro on a type."""
    struct_name: str
    derives: List[str] = field(default_factory=list)
    line_number: int = 0
    file: str = ""


@dataclass
class RustFeatureFlagInfo:
    """Information about a cfg feature flag."""
    feature: str
    kind: str = "feature"  # feature, target_os, target_arch, cfg_attr
    line_number: int = 0
    file: str = ""


@dataclass
class RustMacroUsageInfo:
    """Information about a proc macro attribute usage."""
    macro_name: str
    target_name: str = ""
    args: str = ""
    line_number: int = 0
    file: str = ""


@dataclass
class RustCrateAttributeInfo:
    """Information about a crate-level attribute."""
    attribute: str
    value: str = ""
    line_number: int = 0
    file: str = ""


class RustAttributeExtractor:
    """
    Extracts Rust attributes, derive macros, and feature flags from source code.

    Handles:
    - #[derive(Debug, Clone, Serialize)] derive macros
    - #[cfg(feature = "foo")] feature flags
    - #[cfg(target_os = "linux")] platform conditions
    - #[cfg_attr(feature = "serde", derive(Serialize))] conditional derives
    - #![allow(dead_code)] crate-level attributes
    - #[tokio::main] / #[actix_web::main] proc macro attributes
    - #[serde(rename_all = "camelCase")] serde attributes
    - #[test] / #[bench] test attributes
    - Custom proc macro attributes (#[route("/api")], etc.)
    """

    # Derive pattern
    DERIVE_PATTERN = re.compile(
        r'#\[derive\(([^)]+)\)\]',
        re.MULTILINE
    )

    # cfg feature pattern
    CFG_FEATURE = re.compile(
        r'#\[cfg\(\s*feature\s*=\s*"([^"]+)"\s*\)\]',
        re.MULTILINE
    )

    # cfg target_os pattern
    CFG_TARGET_OS = re.compile(
        r'#\[cfg\(\s*target_os\s*=\s*"([^"]+)"\s*\)\]',
        re.MULTILINE
    )

    # cfg_attr pattern
    CFG_ATTR = re.compile(
        r'#\[cfg_attr\(([^)]+)\)\]',
        re.MULTILINE
    )

    # Crate-level attribute pattern
    CRATE_ATTR = re.compile(
        r'^#!\[(\w+)(?:\(([^)]*)\))?\]',
        re.MULTILINE
    )

    # Proc macro attribute pattern (e.g. #[tokio::main], #[actix_web::main])
    PROC_MACRO = re.compile(
        r'#\[(\w+(?:::\w+)*)\s*(?:\(([^)]*)\))?\]\s*(?:pub\s+)?(?:async\s+)?(?:fn|struct|enum|impl)\s+(\w+)',
        re.MULTILINE
    )

    # Serde attribute pattern
    SERDE_ATTR = re.compile(
        r'#\[serde\(([^)]+)\)\]',
        re.MULTILINE
    )

    # Common proc macro entrypoints
    KNOWN_PROC_MACROS = {
        'tokio::main', 'tokio::test',
        'actix_web::main', 'actix_rt::main',
        'rocket::main', 'rocket::launch',
        'async_trait',
        'derive_more', 'derive_builder',
        'sqlx::test',
        'tracing::instrument',
        'clap::Parser', 'clap::Subcommand', 'clap::Args',
        'prost::Message',
        'tonic::async_trait',
    }

    # Known items to exclude from proc-macro detection
    BUILTIN_ATTRS = {
        'derive', 'cfg', 'cfg_attr', 'test', 'bench', 'allow', 'deny',
        'warn', 'forbid', 'deprecated', 'doc', 'inline', 'must_use',
        'repr', 'path', 'link', 'no_mangle', 'export_name',
        'global_allocator', 'panic_handler', 'non_exhaustive',
    }

    def __init__(self):
        """Initialize the Rust attribute extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all attribute/derive information from Rust source code.

        Args:
            content: Rust source code content
            file_path: Path to source file

        Returns:
            Dict with 'derives', 'features', 'proc_macros', 'crate_attrs' keys
        """
        return {
            'derives': self._extract_derives(content, file_path),
            'features': self._extract_features(content, file_path),
            'proc_macros': self._extract_proc_macros(content, file_path),
            'crate_attrs': self._extract_crate_attrs(content, file_path),
            'serde_attrs': self._extract_serde_attrs(content, file_path),
        }

    def _extract_derives(self, content: str, file_path: str) -> List[RustDeriveInfo]:
        """Extract derive macro information attached to structs/enums."""
        derives = []

        for match in self.DERIVE_PATTERN.finditer(content):
            derive_list = [d.strip() for d in match.group(1).split(',')]
            line_number = content[:match.start()].count('\n') + 1

            # Find the struct/enum name after this derive
            after = content[match.end():]
            struct_match = re.search(r'(?:pub\s+)?(?:struct|enum)\s+(\w+)', after)
            if struct_match and struct_match.start() < 200:
                derives.append(RustDeriveInfo(
                    struct_name=struct_match.group(1),
                    derives=derive_list,
                    line_number=line_number,
                    file=file_path,
                ))

        return derives

    def _extract_features(self, content: str, file_path: str) -> List[RustFeatureFlagInfo]:
        """Extract cfg feature flags and platform conditions."""
        features = []
        seen = set()

        # Feature flags
        for match in self.CFG_FEATURE.finditer(content):
            feat = match.group(1)
            if feat not in seen:
                seen.add(feat)
                features.append(RustFeatureFlagInfo(
                    feature=feat,
                    kind='feature',
                    line_number=content[:match.start()].count('\n') + 1,
                    file=file_path,
                ))

        # Target OS conditions
        for match in self.CFG_TARGET_OS.finditer(content):
            target = match.group(1)
            key = f"target_os:{target}"
            if key not in seen:
                seen.add(key)
                features.append(RustFeatureFlagInfo(
                    feature=target,
                    kind='target_os',
                    line_number=content[:match.start()].count('\n') + 1,
                    file=file_path,
                ))

        # cfg_attr
        for match in self.CFG_ATTR.finditer(content):
            attr_content = match.group(1)
            feat_match = re.search(r'feature\s*=\s*"([^"]+)"', attr_content)
            if feat_match:
                feat = feat_match.group(1)
                key = f"cfg_attr:{feat}"
                if key not in seen:
                    seen.add(key)
                    features.append(RustFeatureFlagInfo(
                        feature=feat,
                        kind='cfg_attr',
                        line_number=content[:match.start()].count('\n') + 1,
                        file=file_path,
                    ))

        return features

    def _extract_proc_macros(self, content: str, file_path: str) -> List[RustMacroUsageInfo]:
        """Extract proc macro attribute usages."""
        macros = []

        for match in self.PROC_MACRO.finditer(content):
            macro_name = match.group(1)
            args = match.group(2) or ''
            target = match.group(3)

            # Skip builtin attributes
            base = macro_name.split('::')[0]
            if base in self.BUILTIN_ATTRS:
                continue

            macros.append(RustMacroUsageInfo(
                macro_name=macro_name,
                target_name=target,
                args=args,
                line_number=content[:match.start()].count('\n') + 1,
                file=file_path,
            ))

        return macros

    def _extract_crate_attrs(self, content: str, file_path: str) -> List[RustCrateAttributeInfo]:
        """Extract crate-level attributes (#![...])."""
        attrs = []

        for match in self.CRATE_ATTR.finditer(content):
            attrs.append(RustCrateAttributeInfo(
                attribute=match.group(1),
                value=match.group(2) or '',
                line_number=content[:match.start()].count('\n') + 1,
                file=file_path,
            ))

        return attrs

    def _extract_serde_attrs(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract serde-specific attributes for data model analysis."""
        serde_attrs = []

        for match in self.SERDE_ATTR.finditer(content):
            attr_str = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            # Find the struct/enum this attribute is on
            after = content[match.end():]
            target_match = re.search(r'(?:#\[(?:derive|serde|doc)[^]]*\]\s*)*(?:pub\s+)?(?:struct|enum)\s+(\w+)', after)
            target_name = target_match.group(1) if target_match and target_match.start() < 300 else ''

            serde_attrs.append({
                'target': target_name,
                'attributes': attr_str,
                'line_number': line_number,
                'file': file_path,
            })

        return serde_attrs
