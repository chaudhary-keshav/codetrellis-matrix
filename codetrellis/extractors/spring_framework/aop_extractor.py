"""
Spring Framework AOP Extractor v1.0

Extracts Spring AOP patterns: aspects, advices, and pointcut definitions.

Part of CodeTrellis v4.94 - Spring Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class SpringAspectInfo:
    """An @Aspect class."""
    name: str
    advices: List[str] = field(default_factory=list)
    pointcuts: List[str] = field(default_factory=list)
    order: int = 0
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class SpringAdviceInfo:
    """An AOP advice method."""
    name: str
    advice_type: str = ""  # before, after, around, afterReturning, afterThrowing
    pointcut_expression: str = ""
    pointcut_ref: str = ""
    aspect_class: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SpringPointcutInfo:
    """A named pointcut definition."""
    name: str
    expression: str = ""
    aspect_class: str = ""
    file: str = ""
    line_number: int = 0


class SpringAOPExtractor:
    """Extracts Spring AOP patterns."""

    ASPECT_PATTERN = re.compile(
        r'@Aspect\s*\n'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:@Order\(\s*(\d+)\s*\)\s*\n)?'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    ADVICE_PATTERN = re.compile(
        r'@(Before|After|Around|AfterReturning|AfterThrowing)'
        r'\(\s*(?:(?:value|pointcut)\s*=\s*)?'
        r'(?:"([^"]*)"|(\w+)\(\))'
        r'[^)]*\)\s*\n'
        r'(?:(?:public|protected|private)\s+)?'
        r'(?:static\s+)?(?:final\s+)?'
        r'(\w[\w<>,\s]*?)\s+(\w+)\s*\(',
        re.MULTILINE
    )

    POINTCUT_PATTERN = re.compile(
        r'@Pointcut\(\s*"([^"]*)"\s*\)\s*\n'
        r'(?:public|private|protected)?\s*void\s+(\w+)\s*\(\s*\)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Spring AOP patterns."""
        result: Dict[str, Any] = {
            'aspects': [],
            'advices': [],
            'pointcuts': [],
        }

        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        # Aspects
        for match in self.ASPECT_PATTERN.finditer(content):
            order = int(match.group(1)) if match.group(1) else 0
            class_name = match.group(2)
            result['aspects'].append(SpringAspectInfo(
                name=class_name,
                order=order,
                annotations=['Aspect'],
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Advices
        for match in self.ADVICE_PATTERN.finditer(content):
            advice_type = match.group(1).lower()
            if advice_type == 'afterreturning':
                advice_type = 'after_returning'
            elif advice_type == 'afterthrowing':
                advice_type = 'after_throwing'

            pointcut_expr = match.group(2) or ""
            pointcut_ref = match.group(3) or ""
            method_name = match.group(5)

            result['advices'].append(SpringAdviceInfo(
                name=method_name,
                advice_type=advice_type,
                pointcut_expression=pointcut_expr,
                pointcut_ref=pointcut_ref,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Pointcuts
        for match in self.POINTCUT_PATTERN.finditer(content):
            result['pointcuts'].append(SpringPointcutInfo(
                name=match.group(2),
                expression=match.group(1),
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return result
