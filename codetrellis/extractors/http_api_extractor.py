"""
HTTP API Extractor for Angular/TypeScript

Extracts HTTP API calls from Angular services using HttpClient.
Supports:
- HttpClient.get/post/put/patch/delete calls
- API endpoint URLs
- Request/Response types
- API base URL detection

Part of CodeTrellis v2.0 - Phase 3 Implementation
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class HttpApiCall:
    """Information about a single HTTP API call"""
    method: str  # GET, POST, PUT, PATCH, DELETE
    url: str  # Full URL or path
    url_template: bool = False  # True if URL contains template variables
    response_type: Optional[str] = None
    request_body_type: Optional[str] = None
    function_name: Optional[str] = None  # Method name that makes this call
    line_number: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            'method': self.method,
            'url': self.url,
            'urlTemplate': self.url_template,
        }
        if self.response_type:
            result['responseType'] = self.response_type
        if self.request_body_type:
            result['requestBodyType'] = self.request_body_type
        if self.function_name:
            result['function'] = self.function_name
        return result

    def to_codetrellis_format(self) -> str:
        """Convert to CodeTrellis output format"""
        parts = [f"{self.method} {self.url}"]

        if self.response_type:
            parts.append(f"→ {self.response_type}")

        if self.request_body_type:
            parts.append(f"body: {self.request_body_type}")

        return ' | '.join(parts)


@dataclass
class HttpApiFileInfo:
    """Information about HTTP API usage in a file"""
    file_path: str
    base_url: Optional[str] = None  # Detected API base URL
    base_url_variable: Optional[str] = None  # Variable name for base URL
    api_calls: List[HttpApiCall] = field(default_factory=list)

    # Stats
    get_count: int = 0
    post_count: int = 0
    put_count: int = 0
    patch_count: int = 0
    delete_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            'filePath': self.file_path,
            'apiCalls': [c.to_dict() for c in self.api_calls],
            'stats': {
                'total': len(self.api_calls),
                'GET': self.get_count,
                'POST': self.post_count,
                'PUT': self.put_count,
                'PATCH': self.patch_count,
                'DELETE': self.delete_count,
            }
        }
        if self.base_url:
            result['baseUrl'] = self.base_url
        if self.base_url_variable:
            result['baseUrlVariable'] = self.base_url_variable
        return result


class HttpApiExtractor:
    """
    Extracts HTTP API calls from Angular TypeScript services.

    Supports Angular HttpClient patterns.
    """

    # Pattern to detect HttpClient import
    HTTP_CLIENT_IMPORT_PATTERN = re.compile(
        r"import\s*\{[^}]*HttpClient[^}]*\}\s*from\s*['\"]@angular/common/http['\"]",
        re.MULTILINE
    )

    # Pattern to detect HttpClient injection
    HTTP_CLIENT_INJECT_PATTERN = re.compile(
        r'(?:private|readonly)\s+(?:readonly\s+)?(\w+)\s*(?:=\s*inject\(HttpClient\)|:\s*HttpClient)',
        re.MULTILINE
    )

    # Pattern to detect API base URL
    BASE_URL_PATTERN = re.compile(
        r'(?:private|readonly|const)\s+(?:readonly\s+)?(\w*(?:API|BASE|URL|ENDPOINT)\w*)\s*=\s*[\'"]([^\'"]+)[\'"]',
        re.IGNORECASE
    )

    # Pattern for HTTP method calls with generic type
    HTTP_CALL_TYPED_PATTERN = re.compile(
        r'this\.(\w+)\.(get|post|put|patch|delete)\s*<([^>]+)>\s*\(\s*([^,)]+)',
        re.MULTILINE
    )

    # Pattern for HTTP method calls without generic type
    HTTP_CALL_UNTYPED_PATTERN = re.compile(
        r'this\.(\w+)\.(get|post|put|patch|delete)\s*\(\s*([^,)]+)',
        re.MULTILINE
    )

    # Pattern for HTTP POST/PUT/PATCH with body
    HTTP_CALL_WITH_BODY_PATTERN = re.compile(
        r'this\.(\w+)\.(post|put|patch)\s*<([^>]+)>\s*\(\s*([^,]+)\s*,\s*([^,)]+)',
        re.MULTILINE
    )

    # HTTP methods
    HTTP_METHODS = {'get', 'post', 'put', 'patch', 'delete'}

    def __init__(self):
        self.files_info: List[HttpApiFileInfo] = []

    def can_extract(self, file_path: str, content: str) -> bool:
        """Check if this file contains HTTP API calls"""
        # Check for HttpClient import
        if not self.HTTP_CLIENT_IMPORT_PATTERN.search(content):
            return False

        # Check for HTTP method calls
        if any(f'.{method}(' in content or f'.{method}<' in content
               for method in self.HTTP_METHODS):
            return True

        return False

    def extract(self, file_path: str, content: str) -> Optional[HttpApiFileInfo]:
        """Extract HTTP API calls from a file"""
        if not self.can_extract(file_path, content):
            return None

        file_info = HttpApiFileInfo(file_path=file_path)

        # Find HttpClient variable name
        http_var_match = self.HTTP_CLIENT_INJECT_PATTERN.search(content)
        http_var = http_var_match.group(1) if http_var_match else 'http'

        # Find base URL
        base_url_match = self.BASE_URL_PATTERN.search(content)
        if base_url_match:
            file_info.base_url_variable = base_url_match.group(1)
            file_info.base_url = base_url_match.group(2)

        # Extract API calls
        api_calls = self._extract_api_calls(content, http_var)
        file_info.api_calls = api_calls

        # Calculate stats
        file_info.get_count = sum(1 for c in api_calls if c.method == 'GET')
        file_info.post_count = sum(1 for c in api_calls if c.method == 'POST')
        file_info.put_count = sum(1 for c in api_calls if c.method == 'PUT')
        file_info.patch_count = sum(1 for c in api_calls if c.method == 'PATCH')
        file_info.delete_count = sum(1 for c in api_calls if c.method == 'DELETE')

        if api_calls:
            self.files_info.append(file_info)
            return file_info

        return None

    def _extract_api_calls(self, content: str, http_var: str) -> List[HttpApiCall]:
        """Extract all HTTP API calls"""
        calls = []
        seen_urls = set()

        # Normalize content - handle line continuations
        normalized = content.replace('\n      .', '.')
        normalized = normalized.replace('\n    .', '.')
        normalized = normalized.replace('\n  .', '.')
        normalized = normalized.replace('\n.', '.')

        # Escape http_var for regex
        escaped_var = re.escape(http_var)

        # Pattern for typed calls: this.http.get<Type>(url) or return this.http.post<Type>(url
        typed_pattern = re.compile(
            rf'(?:return\s+)?this\.{escaped_var}\.(get|post|put|patch|delete)\s*<([^>]+)>\s*\(\s*([^,)]+)',
            re.MULTILINE | re.DOTALL
        )

        for match in typed_pattern.finditer(normalized):
            method = match.group(1).upper()
            response_type = match.group(2).strip()
            url = self._clean_url(match.group(3))

            url_key = f"{method}_{url}"
            if url_key not in seen_urls:
                seen_urls.add(url_key)
                calls.append(HttpApiCall(
                    method=method,
                    url=url,
                    url_template='${' in match.group(3) or '`' in match.group(3),
                    response_type=response_type,
                    line_number=content[:match.start()].count('\n') + 1
                ))

        # Pattern for untyped calls: this.http.get(url)
        untyped_pattern = re.compile(
            rf'(?:return\s+)?this\.{escaped_var}\.(get|post|put|patch|delete)\s*\(\s*([^,)<]+)',
            re.MULTILINE | re.DOTALL
        )

        for match in untyped_pattern.finditer(normalized):
            method = match.group(1).upper()
            url = self._clean_url(match.group(2))

            url_key = f"{method}_{url}"
            if url_key not in seen_urls:
                seen_urls.add(url_key)
                calls.append(HttpApiCall(
                    method=method,
                    url=url,
                    url_template='${' in match.group(2) or '`' in match.group(2),
                    line_number=content[:match.start()].count('\n') + 1
                ))

        # Extract function context for each call
        calls = self._add_function_context(content, calls)

        return calls

    def _clean_url(self, url_str: str) -> str:
        """Clean and normalize URL string"""
        url = url_str.strip()

        # Remove quotes
        url = url.strip('"\'`')

        # Handle template literals
        if url.startswith('`'):
            url = url[1:]
        if url.endswith('`'):
            url = url[:-1]

        # Keep variable references readable
        if url.startswith('this.'):
            # Extract just the variable reference
            parts = url.split('/')
            if len(parts) > 1:
                url = f"${{{parts[0]}}}/" + '/'.join(parts[1:])

        # Handle string concatenation
        url = url.replace(' + ', '')
        url = url.replace("' + '", '')
        url = url.replace('" + "', '')

        # Clean up template expressions
        url = re.sub(r'\$\{([^}]+)\}', r'{\1}', url)

        # Limit length
        if len(url) > 100:
            url = url[:97] + '...'

        return url

    def _add_function_context(self, content: str, calls: List[HttpApiCall]) -> List[HttpApiCall]:
        """Add function name context to each API call"""
        # Find all function definitions with their line numbers
        function_pattern = re.compile(
            r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{',
            re.MULTILINE
        )

        functions = []
        for match in function_pattern.finditer(content):
            func_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            functions.append((func_name, line_num))

        # Assign function names to calls based on line numbers
        for call in calls:
            for func_name, func_line in reversed(functions):
                if func_line < call.line_number:
                    call.function_name = func_name
                    break

        return calls

    def get_all_files(self) -> List[HttpApiFileInfo]:
        """Get all extracted HTTP API info"""
        return self.files_info

    def get_endpoints_summary(self) -> Dict[str, List[str]]:
        """Get summary of all endpoints grouped by method"""
        summary = {
            'GET': [],
            'POST': [],
            'PUT': [],
            'PATCH': [],
            'DELETE': [],
        }

        for file_info in self.files_info:
            for call in file_info.api_calls:
                if call.url not in summary[call.method]:
                    summary[call.method].append(call.url)

        return summary

    def clear(self):
        """Clear all extracted API info"""
        self.files_info = []
