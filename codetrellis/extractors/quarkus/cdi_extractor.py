"""
Quarkus CDI Extractor v1.0 - CDI beans, producers, interceptors, decorators.
Part of CodeTrellis v4.94 - Quarkus Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class QuarkusCDIBeanInfo:
    """A CDI-managed bean."""
    name: str
    scope: str = ""  # application, request, session, dependent, singleton
    qualifiers: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    stereotypes: List[str] = field(default_factory=list)
    injected_fields: List[str] = field(default_factory=list)
    observed_events: List[str] = field(default_factory=list)
    is_unremovable: bool = False
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class QuarkusProducerInfo:
    """A CDI producer method or field."""
    name: str
    produced_type: str = ""
    scope: str = ""
    qualifiers: List[str] = field(default_factory=list)
    is_method: bool = True  # True=@Produces method, False=@Produces field
    file: str = ""
    line_number: int = 0


@dataclass
class QuarkusInterceptorInfo:
    """A CDI interceptor."""
    name: str
    binding_annotation: str = ""
    priority: int = 0
    file: str = ""
    line_number: int = 0


class QuarkusCDIExtractor:
    """Extracts Quarkus CDI patterns."""

    SCOPE_PATTERN = re.compile(
        r'@(ApplicationScoped|RequestScoped|SessionScoped|Dependent|Singleton)\s*\n'
        r'((?:@\w+(?:\([^)]*\))?\s*\n)*)'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    INJECT_PATTERN = re.compile(
        r'@Inject\s+(?:@\w+(?:\([^)]*\))?\s+)*'
        r'(?:(?:private|protected|public)\s+)?(?:final\s+)?([\w<>,?]+)\s+(\w+)\s*;',
        re.MULTILINE
    )

    PRODUCER_PATTERN = re.compile(
        r'@Produces\s*\n'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:public\s+)?([\w<>,?]+)\s+(\w+)\s*(?:\(|;)',
        re.MULTILINE
    )

    INTERCEPTOR_PATTERN = re.compile(
        r'@Interceptor\s*\n'
        r'(?:@Priority\(\s*(\d+)\s*\)\s*\n)?'
        r'(?:@(\w+)\s*\n)?'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    UNREMOVABLE_PATTERN = re.compile(r'@Unremovable\b')

    OBSERVES_PATTERN = re.compile(
        r'(?:public\s+)?void\s+(\w+)\s*\(\s*@Observes(?:Async)?\s+([\w<>,?]+)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        result: Dict[str, Any] = {'beans': [], 'producers': [], 'interceptors': [], 'observers': []}
        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        for match in self.SCOPE_PATTERN.finditer(content):
            scope = match.group(1).lower().replace('scoped', '')
            if scope == 'application':
                scope = 'application'
            class_name = match.group(3)
            between = match.group(2) or ""

            injected = [m.group(1) for m in self.INJECT_PATTERN.finditer(content)]
            observed = [m.group(2) for m in self.OBSERVES_PATTERN.finditer(content)]
            is_unremovable = bool(self.UNREMOVABLE_PATTERN.search(between))

            result['beans'].append(QuarkusCDIBeanInfo(
                name=class_name, scope=scope,
                injected_fields=injected, observed_events=observed,
                is_unremovable=is_unremovable,
                annotations=[match.group(1)],
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        for match in self.PRODUCER_PATTERN.finditer(content):
            is_method = '(' in content[match.end()-1:match.end()]
            result['producers'].append(QuarkusProducerInfo(
                name=match.group(2), produced_type=match.group(1),
                is_method=is_method,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        for match in self.INTERCEPTOR_PATTERN.finditer(content):
            result['interceptors'].append(QuarkusInterceptorInfo(
                name=match.group(3),
                priority=int(match.group(1)) if match.group(1) else 0,
                binding_annotation=match.group(2) or "",
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Standalone observer methods
        for match in self.OBSERVES_PATTERN.finditer(content):
            result['observers'].append({
                'method_name': match.group(1),
                'event_type': match.group(2),
                'file': file_path,
                'line_number': content[:match.start()].count('\n') + 1,
            })

        return result
