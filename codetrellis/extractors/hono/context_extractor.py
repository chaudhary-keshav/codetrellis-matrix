"""
Hono Context Extractor - Extracts Hono Context (c) usage patterns.

Detects:
- c.json() / c.text() / c.html() / c.redirect() / c.notFound() response helpers
- c.body() / c.header() / c.status()
- c.req.json() / c.req.text() / c.req.param() / c.req.query() / c.req.header()
- c.req.parseBody() / c.req.formData() / c.req.blob() / c.req.arrayBuffer()
- c.req.valid() (validator results)
- c.req.path / c.req.url / c.req.method / c.req.routePath / c.req.matchedRoutes
- c.var / c.set() / c.get() (context variables)
- c.env (Cloudflare Workers bindings)
- c.executionCtx (Cloudflare execution context)
- c.event (FetchEvent)
- c.error (error in onError handler)
- Hono JSX patterns: c.render(), c.setRenderer()
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class HonoContextUsageInfo:
    """A Hono context (c) property/method usage."""
    property_path: str  # e.g. 'c.json', 'c.req.param', 'c.env.DB'
    usage_type: str = ""  # response, request, variable, env, execution, jsx
    file: str = ""
    line_number: int = 0


@dataclass
class HonoResponseInfo:
    """A Hono response helper usage."""
    method: str  # json, text, html, redirect, notFound, body, newResponse
    status_code: str = ""
    content_type: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class HonoEnvBindingInfo:
    """A Cloudflare Workers environment binding accessed via c.env."""
    name: str
    binding_type: str = ""  # KV, D1, R2, DO, Service, Queue, AI, Vectorize, etc.
    file: str = ""
    line_number: int = 0


class HonoContextExtractor:
    """Extracts Hono context usage patterns from source code."""

    # Response helpers: c.json(), c.text(), c.html(), c.redirect()
    RESPONSE_PATTERNS = {
        'json': re.compile(r'\bc\s*\.\s*json\s*\('),
        'text': re.compile(r'\bc\s*\.\s*text\s*\('),
        'html': re.compile(r'\bc\s*\.\s*html\s*\('),
        'redirect': re.compile(r'\bc\s*\.\s*redirect\s*\('),
        'notFound': re.compile(r'\bc\s*\.\s*notFound\s*\('),
        'body': re.compile(r'\bc\s*\.\s*body\s*\('),
        'newResponse': re.compile(r'\bc\s*\.\s*newResponse\s*\('),
        'stream': re.compile(r'\bc\s*\.\s*stream\s*\('),
        'streamText': re.compile(r'\bc\s*\.\s*streamText\s*\('),
        'streamSSE': re.compile(r'\bc\s*\.\s*streamSSE\s*\('),
    }

    # Status: c.status(404), return c.json({}, 201)
    STATUS_PATTERN = re.compile(r'\bc\s*\.\s*status\s*\(\s*(\d+)\s*\)')

    # Request helpers
    REQUEST_PATTERNS = {
        'c.req.json': re.compile(r'\bc\s*\.\s*req\s*\.\s*json\s*\('),
        'c.req.text': re.compile(r'\bc\s*\.\s*req\s*\.\s*text\s*\('),
        'c.req.param': re.compile(r'\bc\s*\.\s*req\s*\.\s*param\s*\('),
        'c.req.query': re.compile(r'\bc\s*\.\s*req\s*\.\s*query\s*\('),
        'c.req.header': re.compile(r'\bc\s*\.\s*req\s*\.\s*header\s*\('),
        'c.req.parseBody': re.compile(r'\bc\s*\.\s*req\s*\.\s*parseBody\s*\('),
        'c.req.formData': re.compile(r'\bc\s*\.\s*req\s*\.\s*formData\s*\('),
        'c.req.blob': re.compile(r'\bc\s*\.\s*req\s*\.\s*blob\s*\('),
        'c.req.arrayBuffer': re.compile(r'\bc\s*\.\s*req\s*\.\s*arrayBuffer\s*\('),
        'c.req.valid': re.compile(r'\bc\s*\.\s*req\s*\.\s*valid\s*\('),
        'c.req.path': re.compile(r'\bc\s*\.\s*req\s*\.\s*path\b'),
        'c.req.url': re.compile(r'\bc\s*\.\s*req\s*\.\s*url\b'),
        'c.req.method': re.compile(r'\bc\s*\.\s*req\s*\.\s*method\b'),
        'c.req.routePath': re.compile(r'\bc\s*\.\s*req\s*\.\s*routePath\b'),
        'c.req.matchedRoutes': re.compile(r'\bc\s*\.\s*req\s*\.\s*matchedRoutes\b'),
        'c.req.raw': re.compile(r'\bc\s*\.\s*req\s*\.\s*raw\b'),
    }

    # Context variables: c.set(), c.get(), c.var
    VAR_SET_PATTERN = re.compile(r'\bc\s*\.\s*set\s*\(\s*[\'"`](\w+)[\'"`]')
    VAR_GET_PATTERN = re.compile(r'\bc\s*\.\s*get\s*\(\s*[\'"`](\w+)[\'"`]')
    VAR_ACCESS_PATTERN = re.compile(r'\bc\s*\.\s*var\s*\.\s*(\w+)')

    # Response header: c.header()
    HEADER_PATTERN = re.compile(r'\bc\s*\.\s*header\s*\(\s*[\'"`]([^\'"`]+)[\'"`]')

    # Cloudflare environment bindings: c.env.BINDING_NAME
    ENV_PATTERN = re.compile(r'\bc\s*\.\s*env\s*\.\s*(\w+)')

    # Execution context: c.executionCtx
    EXEC_CTX_PATTERN = re.compile(r'\bc\s*\.\s*executionCtx\b')

    # FetchEvent: c.event
    EVENT_PATTERN = re.compile(r'\bc\s*\.\s*event\b')

    # Error: c.error (in onError handler)
    ERROR_PATTERN = re.compile(r'\bc\s*\.\s*error\b')

    # JSX rendering: c.render(), c.setRenderer()
    RENDER_PATTERN = re.compile(r'\bc\s*\.\s*render\s*\(')
    SET_RENDERER_PATTERN = re.compile(r'\bc\s*\.\s*setRenderer\s*\(')

    # Known CF binding type hints
    CF_BINDING_TYPES = {
        'KV': 'KVNamespace',
        'D1': 'D1Database',
        'R2': 'R2Bucket',
        'DO': 'DurableObjectNamespace',
        'AI': 'Ai',
        'VECTORIZE': 'VectorizeIndex',
        'QUEUE': 'Queue',
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Hono context usage from source code."""
        context_usages: List[HonoContextUsageInfo] = []
        responses: List[HonoResponseInfo] = []
        env_bindings: List[HonoEnvBindingInfo] = []

        # Response helpers
        for method, pattern in self.RESPONSE_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                # Try to detect status code from second arg: c.json({}, 404)
                after = content[match.end():match.end()+100]
                status = ''
                status_match = re.search(r',\s*(\d{3})', after)
                if status_match:
                    status = status_match.group(1)

                responses.append(HonoResponseInfo(
                    method=method,
                    status_code=status,
                    file=file_path,
                    line_number=line_num,
                ))
                context_usages.append(HonoContextUsageInfo(
                    property_path=f'c.{method}',
                    usage_type='response',
                    file=file_path,
                    line_number=line_num,
                ))

        # Status
        for match in self.STATUS_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            context_usages.append(HonoContextUsageInfo(
                property_path='c.status',
                usage_type='response',
                file=file_path,
                line_number=line_num,
            ))

        # Request helpers
        for prop_path, pattern in self.REQUEST_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                context_usages.append(HonoContextUsageInfo(
                    property_path=prop_path,
                    usage_type='request',
                    file=file_path,
                    line_number=line_num,
                ))

        # Context variables
        for match in self.VAR_SET_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            context_usages.append(HonoContextUsageInfo(
                property_path=f'c.set({match.group(1)})',
                usage_type='variable',
                file=file_path,
                line_number=line_num,
            ))

        for match in self.VAR_GET_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            context_usages.append(HonoContextUsageInfo(
                property_path=f'c.get({match.group(1)})',
                usage_type='variable',
                file=file_path,
                line_number=line_num,
            ))

        for match in self.VAR_ACCESS_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            context_usages.append(HonoContextUsageInfo(
                property_path=f'c.var.{match.group(1)}',
                usage_type='variable',
                file=file_path,
                line_number=line_num,
            ))

        # Environment bindings
        seen_bindings = set()
        for match in self.ENV_PATTERN.finditer(content):
            binding_name = match.group(1)
            if binding_name in seen_bindings:
                continue
            seen_bindings.add(binding_name)
            line_num = content[:match.start()].count('\n') + 1

            # Try to detect binding type from name heuristics
            binding_type = ''
            upper = binding_name.upper()
            for hint, btype in self.CF_BINDING_TYPES.items():
                if hint in upper:
                    binding_type = btype
                    break

            env_bindings.append(HonoEnvBindingInfo(
                name=binding_name,
                binding_type=binding_type,
                file=file_path,
                line_number=line_num,
            ))
            context_usages.append(HonoContextUsageInfo(
                property_path=f'c.env.{binding_name}',
                usage_type='env',
                file=file_path,
                line_number=line_num,
            ))

        # Execution context
        if self.EXEC_CTX_PATTERN.search(content):
            context_usages.append(HonoContextUsageInfo(
                property_path='c.executionCtx',
                usage_type='execution',
                file=file_path,
            ))

        # Event
        if self.EVENT_PATTERN.search(content):
            context_usages.append(HonoContextUsageInfo(
                property_path='c.event',
                usage_type='execution',
                file=file_path,
            ))

        # Error
        if self.ERROR_PATTERN.search(content):
            context_usages.append(HonoContextUsageInfo(
                property_path='c.error',
                usage_type='error',
                file=file_path,
            ))

        # JSX
        if self.RENDER_PATTERN.search(content):
            context_usages.append(HonoContextUsageInfo(
                property_path='c.render',
                usage_type='jsx',
                file=file_path,
            ))
        if self.SET_RENDERER_PATTERN.search(content):
            context_usages.append(HonoContextUsageInfo(
                property_path='c.setRenderer',
                usage_type='jsx',
                file=file_path,
            ))

        # Response headers
        for match in self.HEADER_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            context_usages.append(HonoContextUsageInfo(
                property_path=f'c.header({match.group(1)})',
                usage_type='response',
                file=file_path,
                line_number=line_num,
            ))

        return {
            'context_usages': context_usages,
            'responses': responses,
            'env_bindings': env_bindings,
        }
