"""
Fastify Hook Extractor - Extracts lifecycle hooks and their usage.

Supports:
- Request/Reply lifecycle hooks: onRequest, preParsing, preValidation,
  preHandler, preSerialization, onSend, onResponse, onTimeout, onError
- Application hooks: onRoute, onRegister, onReady, onListen, onClose
- Hook ordering and layering
- Async hook patterns
- Fastify 3.x through 5.x hook patterns
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class FastifyHookInfo:
    """A single Fastify lifecycle hook registration."""
    hook_name: str  # onRequest, preHandler, onSend, etc.
    file: str = ""
    line_number: int = 0
    hook_category: str = ""  # request-lifecycle, application
    is_async: bool = False
    handler_name: str = ""
    is_route_level: bool = False  # Set on route options vs global


@dataclass
class FastifyHookSummary:
    """Summary of Fastify hook usage."""
    total_hooks: int = 0
    request_lifecycle_hooks: int = 0
    application_hooks: int = 0
    has_on_request: bool = False
    has_pre_handler: bool = False
    has_pre_validation: bool = False
    has_pre_serialization: bool = False
    has_on_send: bool = False
    has_on_response: bool = False
    has_on_error: bool = False
    has_on_close: bool = False
    has_on_ready: bool = False
    has_on_route: bool = False


class FastifyHookExtractor:
    """Extracts Fastify lifecycle hook information from source code."""

    # Request/Reply lifecycle hooks
    REQUEST_HOOKS = {
        'onRequest', 'preParsing', 'preValidation', 'preHandler',
        'preSerialization', 'onSend', 'onResponse', 'onTimeout', 'onError',
        'onRequestAbort',
    }

    # Application hooks
    APP_HOOKS = {
        'onRoute', 'onRegister', 'onReady', 'onListen', 'onClose',
    }

    ALL_HOOKS = REQUEST_HOOKS | APP_HOOKS

    # fastify.addHook('hookName', handler)
    ADD_HOOK_PATTERN = re.compile(
        r"(\w+)\s*\.\s*addHook\s*\(\s*['\"`](\w+)['\"`]"
    )

    # Inline hooks in route options: { preHandler: ... }
    INLINE_HOOK_PATTERN = re.compile(
        r'(onRequest|preParsing|preValidation|preHandler|preSerialization|'
        r'onSend|onResponse|onTimeout|onError|onRequestAbort)\s*:'
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract hook information from Fastify source code."""
        hooks: List[FastifyHookInfo] = []
        lines = content.split('\n')

        # Global hooks via addHook()
        for match in self.ADD_HOOK_PATTERN.finditer(content):
            hook_name = match.group(2)
            if hook_name not in self.ALL_HOOKS:
                continue

            line_num = content[:match.start()].count('\n') + 1
            category = 'request-lifecycle' if hook_name in self.REQUEST_HOOKS else 'application'

            # Check if async
            after = content[match.end():match.end() + 100]
            is_async = 'async' in after[:50]

            # Try to find handler name
            handler_name = ''
            h_match = re.search(r',\s*(\w+)\s*[,)]', after[:80])
            if h_match and h_match.group(1) not in ('async', 'function'):
                handler_name = h_match.group(1)

            hooks.append(FastifyHookInfo(
                hook_name=hook_name,
                file=file_path,
                line_number=line_num,
                hook_category=category,
                is_async=is_async,
                handler_name=handler_name,
                is_route_level=False,
            ))

        # Inline hooks in route options
        for match in self.INLINE_HOOK_PATTERN.finditer(content):
            hook_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Check if this is inside a route options object (not addHook)
            before = content[max(0, match.start() - 200):match.start()]
            if 'addHook' not in before and ('.route(' in before or '.get(' in before or
                '.post(' in before or '.put(' in before or '.delete(' in before):
                hooks.append(FastifyHookInfo(
                    hook_name=hook_name,
                    file=file_path,
                    line_number=line_num,
                    hook_category='request-lifecycle',
                    is_route_level=True,
                ))

        # Build summary
        summary = self._build_summary(hooks)

        return {
            "hooks": hooks,
            "summary": summary,
        }

    def _build_summary(self, hooks: List[FastifyHookInfo]) -> FastifyHookSummary:
        """Build hook usage summary."""
        summary = FastifyHookSummary()
        summary.total_hooks = len(hooks)

        hook_names = {h.hook_name for h in hooks}

        for h in hooks:
            if h.hook_category == 'request-lifecycle':
                summary.request_lifecycle_hooks += 1
            else:
                summary.application_hooks += 1

        summary.has_on_request = 'onRequest' in hook_names
        summary.has_pre_handler = 'preHandler' in hook_names
        summary.has_pre_validation = 'preValidation' in hook_names
        summary.has_pre_serialization = 'preSerialization' in hook_names
        summary.has_on_send = 'onSend' in hook_names
        summary.has_on_response = 'onResponse' in hook_names
        summary.has_on_error = 'onError' in hook_names
        summary.has_on_close = 'onClose' in hook_names
        summary.has_on_ready = 'onReady' in hook_names
        summary.has_on_route = 'onRoute' in hook_names

        return summary
