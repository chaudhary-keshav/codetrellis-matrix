"""
Jakarta EE Servlet Extractor v1.0 - Servlets, filters, listeners.
Part of CodeTrellis v4.94 - Jakarta EE Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class JakartaServletInfo:
    """A Jakarta Servlet."""
    name: str
    url_patterns: List[str] = field(default_factory=list)
    servlet_type: str = ""  # http_servlet, generic_servlet, async_servlet
    is_async: bool = False
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class JakartaFilterInfo:
    """A Servlet filter."""
    name: str
    url_patterns: List[str] = field(default_factory=list)
    dispatcher_types: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class JakartaListenerInfo:
    """A Servlet listener."""
    name: str
    listener_type: str = ""  # context, session, request, attribute
    file: str = ""
    line_number: int = 0


class JakartaServletExtractor:
    """Extracts Jakarta Servlet patterns."""

    SERVLET_ANNOTATION_PATTERN = re.compile(
        r'@WebServlet\(\s*(?:(?:name\s*=\s*"[^"]*"\s*,\s*)?'
        r'(?:urlPatterns\s*=\s*\{([^}]+)\}|value\s*=\s*\{?([^})]+)\}?|"([^"]+)"))'
        r'(?:\s*,\s*asyncSupported\s*=\s*(true|false))?\s*\)\s*\n'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    SERVLET_EXTENDS_PATTERN = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+extends\s+(HttpServlet|GenericServlet)',
        re.MULTILINE
    )

    FILTER_PATTERN = re.compile(
        r'@WebFilter\(\s*(?:urlPatterns\s*=\s*\{([^}]+)\}|value\s*=\s*\{?([^})]+)\}?|"([^"]+)")'
        r'(?:\s*,\s*dispatcherTypes\s*=\s*\{([^}]+)\})?\s*\)\s*\n'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    FILTER_IMPL_PATTERN = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+implements\s+(?:jakarta\.servlet\.)?Filter\b',
        re.MULTILINE
    )

    LISTENER_PATTERNS = {
        'context': re.compile(r'class\s+(\w+)\s+implements\s+(?:\w+\.)*ServletContextListener', re.MULTILINE),
        'session': re.compile(r'class\s+(\w+)\s+implements\s+(?:\w+\.)*HttpSessionListener', re.MULTILINE),
        'request': re.compile(r'class\s+(\w+)\s+implements\s+(?:\w+\.)*ServletRequestListener', re.MULTILINE),
        'attribute': re.compile(r'class\s+(\w+)\s+implements\s+(?:\w+\.)*(?:ServletContext|HttpSession|ServletRequest)AttributeListener', re.MULTILINE),
    }

    LISTENER_ANNOTATION_PATTERN = re.compile(
        r'@WebListener\s*(?:\(\s*"?([^")*]*)"?\s*\))?\s*\n'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        result: Dict[str, Any] = {'servlets': [], 'filters': [], 'listeners': []}
        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        # Extract annotated servlets
        for match in self.SERVLET_ANNOTATION_PATTERN.finditer(content):
            url_patterns_raw = match.group(1) or match.group(2) or match.group(3) or ""
            url_patterns = [p.strip().strip('"\'') for p in url_patterns_raw.split(',') if p.strip()]
            is_async = match.group(4) == 'true' if match.group(4) else False
            class_name = match.group(5)

            result['servlets'].append(JakartaServletInfo(
                name=class_name, url_patterns=url_patterns,
                servlet_type='async_servlet' if is_async else 'http_servlet',
                is_async=is_async,
                annotations=['WebServlet'],
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Extract non-annotated servlets (extends HttpServlet)
        for match in self.SERVLET_EXTENDS_PATTERN.finditer(content):
            class_name = match.group(1)
            # Skip if already found by annotation pattern
            if any(s.name == class_name for s in [JakartaServletInfo(**s) if isinstance(s, dict) else s for s in result['servlets']]):
                continue
            servlet_type = 'http_servlet' if match.group(2) == 'HttpServlet' else 'generic_servlet'
            result['servlets'].append(JakartaServletInfo(
                name=class_name, servlet_type=servlet_type,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Extract filters
        for match in self.FILTER_PATTERN.finditer(content):
            url_patterns_raw = match.group(1) or match.group(2) or match.group(3) or ""
            url_patterns = [p.strip().strip('"\'') for p in url_patterns_raw.split(',') if p.strip()]
            dispatchers_raw = match.group(4) or ""
            dispatchers = [d.strip() for d in dispatchers_raw.split(',') if d.strip()]

            result['filters'].append(JakartaFilterInfo(
                name=match.group(5), url_patterns=url_patterns,
                dispatcher_types=dispatchers,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        for match in self.FILTER_IMPL_PATTERN.finditer(content):
            name = match.group(1)
            if not any(f.name == name for f in [JakartaFilterInfo(**f) if isinstance(f, dict) else f for f in result['filters']]):
                result['filters'].append(JakartaFilterInfo(
                    name=name,
                    file=file_path, line_number=content[:match.start()].count('\n') + 1,
                ))

        # Extract listeners
        for listener_type, pattern in self.LISTENER_PATTERNS.items():
            for match in pattern.finditer(content):
                result['listeners'].append(JakartaListenerInfo(
                    name=match.group(1), listener_type=listener_type,
                    file=file_path, line_number=content[:match.start()].count('\n') + 1,
                ))

        for match in self.LISTENER_ANNOTATION_PATTERN.finditer(content):
            name = match.group(2)
            if not any(l.name == name for l in [JakartaListenerInfo(**l) if isinstance(l, dict) else l for l in result['listeners']]):
                result['listeners'].append(JakartaListenerInfo(
                    name=name, listener_type='annotated',
                    file=file_path, line_number=content[:match.start()].count('\n') + 1,
                ))

        return result
