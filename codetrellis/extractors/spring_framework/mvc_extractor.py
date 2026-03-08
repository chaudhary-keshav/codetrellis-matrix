"""
Spring Framework MVC Extractor v1.0

Extracts Spring MVC / WebFlux infrastructure patterns.

Part of CodeTrellis v4.94 - Spring Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class SpringInterceptorInfo:
    """A HandlerInterceptor implementation."""
    name: str
    interceptor_type: str = ""  # handler, web_request, async
    methods: List[str] = field(default_factory=list)  # preHandle, postHandle, afterCompletion
    path_patterns: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class SpringConverterInfo:
    """A message converter, type converter, or formatter."""
    name: str
    converter_type: str = ""  # message, type, formatter, serializer
    source_type: str = ""
    target_type: str = ""
    media_type: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SpringResolverInfo:
    """A view resolver, argument resolver, or exception resolver."""
    name: str
    resolver_type: str = ""  # view, argument, exception, multipart
    handled_types: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


class SpringMVCExtractor:
    """Extracts Spring MVC infrastructure patterns."""

    INTERCEPTOR_PATTERN = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+(?:extends|implements)\s+'
        r'(HandlerInterceptor(?:Adapter)?|WebRequestInterceptor|AsyncHandlerInterceptor)',
        re.MULTILINE
    )

    CONFIGURER_PATTERN = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+implements\s+'
        r'(WebMvcConfigurer|WebFluxConfigurer|WebMvcRegistrations)',
        re.MULTILINE
    )

    CONVERTER_PATTERN = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+(?:extends|implements)\s+'
        r'(HttpMessageConverter|Converter|GenericConverter|Formatter|'
        r'JsonSerializer|JsonDeserializer)',
        re.MULTILINE
    )

    RESOLVER_PATTERN = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+(?:extends|implements)\s+'
        r'(ViewResolver|HandlerMethodArgumentResolver|'
        r'HandlerExceptionResolver|MultipartResolver)',
        re.MULTILINE
    )

    EXCEPTION_HANDLER_PATTERN = re.compile(
        r'@ExceptionHandler\(\s*(?:\{([^}]*)\}|(\w+)\.class)\s*\)\s*\n'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:public\s+)?(?:\w+\s+)?(\w+)\s+(\w+)\s*\(',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Spring MVC infrastructure patterns."""
        result: Dict[str, Any] = {
            'interceptors': [],
            'converters': [],
            'resolvers': [],
        }

        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        # Interceptors
        for match in self.INTERCEPTOR_PATTERN.finditer(content):
            result['interceptors'].append(SpringInterceptorInfo(
                name=match.group(1),
                interceptor_type='handler',
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Configurers (also act as MVC infrastructure)
        for match in self.CONFIGURER_PATTERN.finditer(content):
            result['interceptors'].append(SpringInterceptorInfo(
                name=match.group(1),
                interceptor_type='configurer',
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Converters
        for match in self.CONVERTER_PATTERN.finditer(content):
            type_map = {
                'HttpMessageConverter': 'message',
                'Converter': 'type',
                'GenericConverter': 'type',
                'Formatter': 'formatter',
                'JsonSerializer': 'serializer',
                'JsonDeserializer': 'serializer',
            }
            result['converters'].append(SpringConverterInfo(
                name=match.group(1),
                converter_type=type_map.get(match.group(2), 'other'),
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Resolvers
        for match in self.RESOLVER_PATTERN.finditer(content):
            type_map = {
                'ViewResolver': 'view',
                'HandlerMethodArgumentResolver': 'argument',
                'HandlerExceptionResolver': 'exception',
                'MultipartResolver': 'multipart',
            }
            result['resolvers'].append(SpringResolverInfo(
                name=match.group(1),
                resolver_type=type_map.get(match.group(2), 'other'),
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return result
