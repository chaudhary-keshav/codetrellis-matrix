"""
Micronaut DI Extractor v1.0 - Bean definitions, factories, qualifiers, scopes.
Part of CodeTrellis v4.94 - Micronaut Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class MicronautBeanInfo:
    """A Micronaut-managed bean."""
    name: str
    scope: str = ""  # singleton, prototype, request, refreshable, thread_local
    qualifiers: List[str] = field(default_factory=list)
    requires: List[str] = field(default_factory=list)  # @Requires conditions
    injected_fields: List[str] = field(default_factory=list)
    is_primary: bool = False
    is_replaceable: bool = False
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class MicronautFactoryInfo:
    """A @Factory bean producer."""
    name: str
    produced_beans: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class MicronautQualifierInfo:
    """A custom qualifier."""
    name: str
    file: str = ""
    line_number: int = 0


class MicronautDIExtractor:
    """Extracts Micronaut DI patterns."""

    SCOPE_PATTERN = re.compile(
        r'@(Singleton|Prototype|RequestScope|Refreshable|ThreadLocal|Context|Infrastructure)\s*\n'
        r'((?:@\w+(?:\([^)]*\))?\s*\n)*)'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    INJECT_PATTERN = re.compile(
        r'@(?:Inject|Value)\s+(?:@\w+(?:\([^)]*\))?\s+)*'
        r'(?:(?:private|protected|public)\s+)?(?:final\s+)?([\w<>,?\[\]]+)\s+(\w+)\s*;',
        re.MULTILINE
    )

    CONSTRUCTOR_INJECT_PATTERN = re.compile(
        r'(?:public\s+)?(\w+)\s*\(\s*'
        r'((?:@?\w+(?:\([^)]*\))?\s+)*[\w<>,?\[\]]+\s+\w+(?:\s*,\s*(?:@?\w+(?:\([^)]*\))?\s+)*[\w<>,?\[\]]+\s+\w+)*)\s*\)',
        re.MULTILINE
    )

    FACTORY_PATTERN = re.compile(
        r'@Factory\s*\n(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    FACTORY_BEAN_PATTERN = re.compile(
        r'@(?:Singleton|Prototype|Bean|Context)\s*\n'
        r'(?:public\s+)?([\w<>,?\[\]]+)\s+(\w+)\s*\(',
        re.MULTILINE
    )

    REQUIRES_PATTERN = re.compile(
        r'@Requires\(\s*(?:property\s*=\s*"([^"]+)"'
        r'|beans\s*=\s*(\w+)\.class'
        r'|classes\s*=\s*(\w+)\.class'
        r'|env\s*=\s*"([^"]+)"'
        r'|missingBeans\s*=\s*(\w+)\.class)',
        re.MULTILINE
    )

    PRIMARY_PATTERN = re.compile(r'@Primary\b')
    REPLACEABLE_PATTERN = re.compile(r'@Replaces\(\s*(\w+)\.class\s*\)')

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        result: Dict[str, Any] = {'beans': [], 'factories': [], 'qualifiers': []}
        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        # Extract scoped beans
        for match in self.SCOPE_PATTERN.finditer(content):
            scope = match.group(1).lower()
            class_name = match.group(3)
            between = match.group(2) or ""

            injected = [m.group(1) for m in self.INJECT_PATTERN.finditer(content)]
            requires = []
            for rm in self.REQUIRES_PATTERN.finditer(content):
                req = rm.group(1) or rm.group(2) or rm.group(3) or rm.group(4) or rm.group(5)
                if req:
                    requires.append(req)

            is_primary = bool(self.PRIMARY_PATTERN.search(between))
            replaces_match = self.REPLACEABLE_PATTERN.search(between)
            is_replaceable = bool(replaces_match)

            annotations = re.findall(r'@(\w+)', between)
            annotations.insert(0, match.group(1))

            result['beans'].append(MicronautBeanInfo(
                name=class_name, scope=scope,
                injected_fields=injected, requires=requires,
                is_primary=is_primary, is_replaceable=is_replaceable,
                annotations=annotations,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Extract factories
        for match in self.FACTORY_PATTERN.finditer(content):
            factory_name = match.group(1)
            factory_start = match.end()
            produced_beans = [m.group(2) for m in self.FACTORY_BEAN_PATTERN.finditer(content[factory_start:])]

            result['factories'].append(MicronautFactoryInfo(
                name=factory_name, produced_beans=produced_beans,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        return result
