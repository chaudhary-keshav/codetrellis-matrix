"""
Koa Context Extractor - Extracts Koa ctx usage patterns.

Supports:
- ctx.body, ctx.status, ctx.type — response shaping
- ctx.request.body, ctx.query, ctx.params — request data
- ctx.state — per-request state
- ctx.throw() — error throwing
- ctx.assert() — assertions
- ctx.cookies — cookie operations
- ctx.redirect() — redirects
- ctx.set() / ctx.get() — headers
- ctx.app — app-level context
- Custom context extensions: ctx.myProp via app.context.myProp
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class KoaContextUsageInfo:
    """A Koa ctx property/method usage."""
    property_path: str  # e.g., 'ctx.body', 'ctx.state.user', 'ctx.throw'
    usage_type: str  # 'response', 'request', 'state', 'error', 'cookie', 'header', 'custom'
    file: str = ""
    line_number: int = 0
    is_assignment: bool = False  # ctx.body = vs ctx.body


@dataclass
class KoaErrorThrowInfo:
    """A ctx.throw() or ctx.assert() call."""
    method: str  # 'throw' or 'assert'
    status_code: str = ""  # e.g., '404', '401'
    message: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class KoaCustomContextInfo:
    """Custom context extension via app.context.prop = value."""
    property_name: str
    file: str = ""
    line_number: int = 0


class KoaContextExtractor:
    """Extracts Koa ctx usage patterns from source code."""

    # ctx.throw(status, message) / ctx.throw(status)
    THROW_PATTERN = re.compile(
        r'ctx\s*\.\s*throw\s*\(\s*(\d{3})?\s*(?:,\s*[\'"`]([^\'"`]*)[\'"`])?',
    )

    # ctx.assert(condition, status, message)
    ASSERT_PATTERN = re.compile(
        r'ctx\s*\.\s*assert\s*\([^,]+,\s*(\d{3})?\s*(?:,\s*[\'"`]([^\'"`]*)[\'"`])?',
    )

    # app.context.prop = value  (custom context extension)
    CUSTOM_CTX_PATTERN = re.compile(
        r'(\w+)\s*\.\s*context\s*\.\s*(\w+)\s*=',
    )

    # ctx.body =, ctx.status =, ctx.type =, ctx.redirect()
    RESPONSE_PATTERNS = [
        re.compile(r'ctx\s*\.\s*(body)\s*='),
        re.compile(r'ctx\s*\.\s*(status)\s*='),
        re.compile(r'ctx\s*\.\s*(type)\s*='),
        re.compile(r'ctx\s*\.\s*(redirect)\s*\('),
        re.compile(r'ctx\s*\.\s*(attachment)\s*\('),
    ]

    # ctx.request.body, ctx.query, ctx.params, ctx.path, ctx.url
    REQUEST_PATTERNS = [
        re.compile(r'ctx\s*\.\s*request\s*\.\s*(body|query|params|headers|url|path|method|ip)'),
        re.compile(r'ctx\s*\.\s*(query|params|path|url|method|ip|hostname|headers)\b'),
    ]

    # ctx.state.user, ctx.state = {}, etc.
    STATE_PATTERN = re.compile(r'ctx\s*\.\s*state(?:\s*\.\s*(\w+))?')

    # ctx.cookies.get / ctx.cookies.set
    COOKIE_PATTERN = re.compile(r'ctx\s*\.\s*cookies\s*\.\s*(get|set)\s*\(')

    # ctx.set / ctx.get (headers)
    HEADER_PATTERN = re.compile(r'ctx\s*\.\s*(set|get|remove|append)\s*\(')

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Koa context usage patterns."""
        throws: List[KoaErrorThrowInfo] = []
        custom_ctx: List[KoaCustomContextInfo] = []
        context_usages: List[KoaContextUsageInfo] = []

        # ctx.throw()
        for match in self.THROW_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            throws.append(KoaErrorThrowInfo(
                method='throw',
                status_code=match.group(1) or '',
                message=match.group(2) or '',
                file=file_path,
                line_number=line_num,
            ))

        # ctx.assert()
        for match in self.ASSERT_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            throws.append(KoaErrorThrowInfo(
                method='assert',
                status_code=match.group(1) or '',
                message=match.group(2) or '',
                file=file_path,
                line_number=line_num,
            ))

        # Custom context extensions
        for match in self.CUSTOM_CTX_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            custom_ctx.append(KoaCustomContextInfo(
                property_name=match.group(2),
                file=file_path,
                line_number=line_num,
            ))

        # Response patterns
        for pattern in self.RESPONSE_PATTERNS:
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                context_usages.append(KoaContextUsageInfo(
                    property_path=f"ctx.{match.group(1)}",
                    usage_type='response',
                    file=file_path,
                    line_number=line_num,
                    is_assignment='=' in content[match.end():match.end()+5],
                ))

        # State patterns
        for match in self.STATE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            prop = match.group(1) or ''
            path = f"ctx.state.{prop}" if prop else "ctx.state"
            context_usages.append(KoaContextUsageInfo(
                property_path=path,
                usage_type='state',
                file=file_path,
                line_number=line_num,
            ))

        return {
            'throws': throws,
            'custom_context': custom_ctx,
            'context_usages': context_usages,
        }
