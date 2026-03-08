"""
Jakarta EE CDI Extractor v1.0 - CDI 4.0+ beans, producers, decorators, events.
Part of CodeTrellis v4.94 - Jakarta EE Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class JakartaCDIBeanInfo:
    """A Jakarta CDI managed bean."""
    name: str
    scope: str = ""  # application, request, session, dependent, conversation
    qualifiers: List[str] = field(default_factory=list)
    stereotypes: List[str] = field(default_factory=list)
    alternatives: bool = False
    injected_fields: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    namespace: str = ""  # jakarta or javax
    file: str = ""
    line_number: int = 0


@dataclass
class JakartaProducerInfo:
    """A CDI producer method or field."""
    name: str
    produced_type: str = ""
    scope: str = ""
    qualifiers: List[str] = field(default_factory=list)
    is_disposer: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class JakartaDecoratorInfo:
    """A CDI decorator."""
    name: str
    decorated_type: str = ""
    delegate_type: str = ""
    file: str = ""
    line_number: int = 0


class JakartaCDIExtractor:
    """Extracts Jakarta/Java EE CDI patterns (supports both jakarta.* and javax.* namespaces)."""

    SCOPE_PATTERN = re.compile(
        r'@(ApplicationScoped|RequestScoped|SessionScoped|Dependent|ConversationScoped)\s*\n'
        r'((?:@\w+(?:\([^)]*\))?\s*\n)*)'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    INJECT_PATTERN = re.compile(
        r'@Inject\s+(?:@\w+(?:\([^)]*\))?\s+)*'
        r'(?:(?:private|protected|public)\s+)?(?:final\s+)?([\w<>,?\[\]]+)\s+(\w+)\s*;',
        re.MULTILINE
    )

    PRODUCER_PATTERN = re.compile(
        r'@Produces\s*\n'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:public\s+)?([\w<>,?\[\]]+)\s+(\w+)\s*(?:\(|;)',
        re.MULTILINE
    )

    DISPOSER_PATTERN = re.compile(
        r'(?:public\s+)?void\s+(\w+)\s*\(\s*@Disposes\s+([\w<>,?]+)',
        re.MULTILINE
    )

    DECORATOR_PATTERN = re.compile(
        r'@Decorator\s*\n'
        r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    DELEGATE_PATTERN = re.compile(
        r'@Delegate\s+@Inject\s+(?:private\s+)?([\w<>,?]+)\s+(\w+)',
        re.MULTILINE
    )

    ALTERNATIVE_PATTERN = re.compile(r'@Alternative\b')

    QUALIFIER_PATTERN = re.compile(
        r'@(Named|Qualifier)\(\s*"?([^")\s]*)"?\s*\)',
        re.MULTILINE
    )

    OBSERVES_PATTERN = re.compile(
        r'(?:public\s+)?void\s+(\w+)\s*\(\s*@Observes(?:Async)?\s+([\w<>,?]+)',
        re.MULTILINE
    )

    NAMESPACE_PATTERN = re.compile(r'import\s+(jakarta|javax)\.enterprise\.')

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        result: Dict[str, Any] = {'beans': [], 'producers': [], 'decorators': [], 'event_observers': []}
        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        # Detect namespace
        ns_match = self.NAMESPACE_PATTERN.search(content)
        namespace = ns_match.group(1) if ns_match else ""

        # Extract scoped beans
        for match in self.SCOPE_PATTERN.finditer(content):
            scope = match.group(1).lower().replace('scoped', '')
            class_name = match.group(3)
            between = match.group(2) or ""

            injected = [m.group(1) for m in self.INJECT_PATTERN.finditer(content)]
            is_alternative = bool(self.ALTERNATIVE_PATTERN.search(between))
            qualifiers = [m.group(2) for m in self.QUALIFIER_PATTERN.finditer(between) if m.group(2)]
            annotations = re.findall(r'@(\w+)', between)
            annotations.insert(0, match.group(1))

            result['beans'].append(JakartaCDIBeanInfo(
                name=class_name, scope=scope,
                qualifiers=qualifiers, alternatives=is_alternative,
                injected_fields=injected, annotations=annotations,
                namespace=namespace,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Extract producers
        for match in self.PRODUCER_PATTERN.finditer(content):
            result['producers'].append(JakartaProducerInfo(
                name=match.group(2), produced_type=match.group(1),
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Extract disposers
        for match in self.DISPOSER_PATTERN.finditer(content):
            result['producers'].append(JakartaProducerInfo(
                name=match.group(1), produced_type=match.group(2),
                is_disposer=True,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Extract decorators
        for match in self.DECORATOR_PATTERN.finditer(content):
            decorator_name = match.group(1)
            delegate_match = self.DELEGATE_PATTERN.search(content)
            delegate_type = delegate_match.group(1) if delegate_match else ""

            result['decorators'].append(JakartaDecoratorInfo(
                name=decorator_name, delegate_type=delegate_type,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Extract event observers
        for match in self.OBSERVES_PATTERN.finditer(content):
            result['event_observers'].append({
                'method': match.group(1),
                'event_type': match.group(2),
                'file': file_path,
                'line_number': content[:match.start()].count('\n') + 1,
            })

        return result
