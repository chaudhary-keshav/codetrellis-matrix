"""
Less Mixin Extractor for CodeTrellis

Extracts Less mixin definitions, parametric mixins, guards, and namespaces.

Supports:
- .mixin() definitions (class-selector style)
- #mixin() definitions (ID-selector style)
- Parametric mixins with default values
- @arguments and @rest (Less 1.4+)
- Mixin guards: when (condition) { }
- Guard operators: and, not, or (comma = or)
- Type-checking guards: iscolor(), isnumber(), isstring(), iskeyword(), isurl(),
  ispixel(), isem(), ispercentage(), isunit()
- Mixin namespaces: #bundle > .mixin() or #bundle.mixin()
- !important keyword propagation in mixin calls
- Conditional mixins (parameterless vs with parens)
- Pattern matching mixins (overloading by args)
- Mixin as function (return value via variable)
- Recursive mixins with guards (loops)

Part of CodeTrellis v4.45 — Less CSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class LessMixinDefInfo:
    """Information about a Less mixin definition."""
    name: str
    parameters: List[str] = field(default_factory=list)
    has_defaults: bool = False
    has_rest_args: bool = False     # @rest... or ... syntax
    has_arguments: bool = False     # @arguments usage
    has_guard: bool = False         # when clause
    guard_expression: str = ""     # Guard condition text
    body_lines: int = 0
    is_parametric: bool = False    # Has () even if no params
    is_pattern_matched: bool = False  # Multiple defs with same name
    namespace: str = ""            # #bundle or #namespace
    file: str = ""
    line_number: int = 0


@dataclass
class LessMixinCallInfo:
    """Information about a Less mixin call/include."""
    name: str
    arguments: List[str] = field(default_factory=list)
    has_important: bool = False    # !important keyword
    namespace: str = ""            # #bundle > .mixin() or #bundle.mixin()
    file: str = ""
    line_number: int = 0


@dataclass
class LessGuardInfo:
    """Information about a Less guard condition."""
    expression: str
    guard_type: str = "mixin"     # mixin, css (CSS guard)
    type_checks: List[str] = field(default_factory=list)  # iscolor, isnumber etc
    operators: List[str] = field(default_factory=list)     # and, not, or
    file: str = ""
    line_number: int = 0


@dataclass
class LessNamespaceInfo:
    """Information about a Less mixin namespace."""
    name: str
    members: List[str] = field(default_factory=list)
    access_pattern: str = ""       # > or . access
    file: str = ""
    line_number: int = 0


class LessMixinExtractor:
    """
    Extracts Less mixin definitions, calls, guards, and namespaces.

    Less mixins use class/ID selector syntax: .mixin() { } or #mixin() { }
    Guards provide conditional execution: .mixin() when (condition) { }
    """

    # Mixin definition: .name() { or .name(@param) { or .name when (...) {
    MIXIN_DEF_PATTERN = re.compile(
        r'^[ \t]*([.#][\w-]+)\s*'            # name (.class or #id)
        r'(\([^)]*\))?\s*'                    # optional params
        r'(?:when\s*\(([^)]+)\))?\s*'         # optional guard
        r'\{',
        re.MULTILINE
    )

    # Mixin call: .mixin(); or .mixin(args);
    MIXIN_CALL_PATTERN = re.compile(
        r'^[ \t]*'
        r'(?:(#[\w-]+)\s*(?:>|\.)\s*)?'       # optional namespace
        r'([.#][\w-]+)\s*'                     # mixin name
        r'\(([^)]*)\)\s*'                      # args (including empty)
        r'(!important)?\s*;',                  # optional !important
        re.MULTILINE
    )

    # Parameterless mixin call: .mixin;  (no parens)
    MIXIN_CALL_NO_PARENS = re.compile(
        r'^[ \t]*([.#][\w-]+)\s*;',
        re.MULTILINE
    )

    # Guard-only mixins: & when (condition) { }
    CSS_GUARD_PATTERN = re.compile(
        r'&\s*when\s*\(([^)]+)\)\s*\{',
        re.MULTILINE
    )

    # Namespace access: #ns > .mixin() or #ns.mixin()
    NAMESPACE_PATTERN = re.compile(
        r'(#[\w-]+)\s*(?:>|\.)\s*([.#][\w-]+)',
        re.MULTILINE
    )

    # @arguments usage
    ARGUMENTS_PATTERN = re.compile(r'@arguments\b')

    # @rest usage
    REST_PATTERN = re.compile(r'(?:@rest\b|\.\.\.)')

    # Guard type-checking functions
    GUARD_TYPE_FUNCS = re.compile(
        r'(iscolor|isnumber|isstring|iskeyword|isurl|ispixel|isem|'
        r'ispercentage|isunit|isruleset|isdefined)\s*\(',
        re.IGNORECASE
    )

    # Guard operators
    GUARD_OPERATORS = re.compile(r'\b(and|not|or)\b', re.IGNORECASE)

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Less mixin definitions, calls, guards, and namespaces.

        Returns dict with 'definitions', 'calls', 'guards', 'namespaces', 'stats'.
        """
        if not content or not content.strip():
            return {'definitions': [], 'calls': [], 'guards': [],
                    'namespaces': [], 'stats': {}}

        # Strip comments
        clean = self._strip_comments(content)

        definitions = self._extract_definitions(clean, file_path)
        calls = self._extract_calls(clean, file_path)
        guards = self._extract_guards(clean, file_path)
        namespaces = self._extract_namespaces(clean, file_path)

        # Detect pattern matching (multiple defs with same name)
        name_counts: Dict[str, int] = {}
        for d in definitions:
            name_counts[d.name] = name_counts.get(d.name, 0) + 1
        for d in definitions:
            if name_counts.get(d.name, 0) > 1:
                d.is_pattern_matched = True

        stats = {
            'total_definitions': len(definitions),
            'total_calls': len(calls),
            'total_guards': len(guards),
            'total_namespaces': len(namespaces),
            'has_parametric': any(d.is_parametric for d in definitions),
            'has_guards': any(d.has_guard for d in definitions),
            'has_pattern_matching': any(d.is_pattern_matched for d in definitions),
            'has_rest_args': any(d.has_rest_args for d in definitions),
            'has_arguments': any(d.has_arguments for d in definitions),
            'has_namespaces': len(namespaces) > 0,
            'has_important_calls': any(c.has_important for c in calls),
        }

        return {
            'definitions': definitions,
            'calls': calls,
            'guards': guards,
            'namespaces': namespaces,
            'stats': stats,
        }

    def _strip_comments(self, content: str) -> str:
        """Strip Less comments (// and /* */) preserving line structure."""
        result = re.sub(r'/\*.*?\*/', lambda m: '\n' * m.group().count('\n'), content, flags=re.DOTALL)
        result = re.sub(r'//[^\n]*', '', result)
        return result

    def _extract_definitions(self, content: str, file_path: str) -> List[LessMixinDefInfo]:
        """Extract mixin definitions."""
        definitions: List[LessMixinDefInfo] = []

        for match in self.MIXIN_DEF_PATTERN.finditer(content):
            name = match.group(1)
            params_str = match.group(2) or ""
            guard_str = match.group(3) or ""

            line_num = content[:match.start()].count('\n') + 1

            # Parse parameters
            parameters = []
            has_defaults = False
            has_rest = False
            has_arguments = False

            if params_str:
                # Remove outer parens
                inner = params_str.strip('()')
                if inner.strip():
                    for param in re.split(r'[,;]', inner):
                        param = param.strip()
                        if param:
                            if ':' in param:
                                has_defaults = True
                            if '...' in param or param == '@rest':
                                has_rest = True
                            # Extract param name
                            pname = param.split(':')[0].strip().split('...')[0].strip()
                            if pname:
                                parameters.append(pname)

            # Check for @arguments in body
            body_start = match.end()
            body_end = self._find_matching_brace(content, body_start - 1)
            body = content[body_start:body_end] if body_end > body_start else ""

            if self.ARGUMENTS_PATTERN.search(body):
                has_arguments = True
            if self.REST_PATTERN.search(params_str + body):
                has_rest = True

            body_lines = body.count('\n')

            # Detect namespace
            namespace = ""
            before = content[:match.start()].rstrip()
            if before.endswith('>'):
                ns_match = re.search(r'(#[\w-]+)\s*>', before[-50:])
                if ns_match:
                    namespace = ns_match.group(1)

            definitions.append(LessMixinDefInfo(
                name=name,
                parameters=parameters,
                has_defaults=has_defaults,
                has_rest_args=has_rest,
                has_arguments=has_arguments,
                has_guard=bool(guard_str),
                guard_expression=guard_str,
                body_lines=body_lines,
                is_parametric=bool(params_str),
                namespace=namespace,
                file=file_path,
                line_number=line_num,
            ))

        return definitions

    def _extract_calls(self, content: str, file_path: str) -> List[LessMixinCallInfo]:
        """Extract mixin calls."""
        calls: List[LessMixinCallInfo] = []

        for match in self.MIXIN_CALL_PATTERN.finditer(content):
            namespace = match.group(1) or ""
            name = match.group(2)
            args_str = match.group(3) or ""
            has_important = bool(match.group(4))

            line_num = content[:match.start()].count('\n') + 1

            # Parse arguments
            arguments = []
            if args_str.strip():
                for arg in re.split(r'[,;]', args_str):
                    arg = arg.strip()
                    if arg:
                        arguments.append(arg[:50])  # truncate long args

            calls.append(LessMixinCallInfo(
                name=name,
                arguments=arguments,
                has_important=has_important,
                namespace=namespace,
                file=file_path,
                line_number=line_num,
            ))

        return calls

    def _extract_guards(self, content: str, file_path: str) -> List[LessGuardInfo]:
        """Extract guard expressions from mixins and CSS guards."""
        guards: List[LessGuardInfo] = []

        # Mixin guards: when (condition)
        for match in re.finditer(r'when\s*\(([^)]+)\)', content):
            expr = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Detect guard type
            before = content[:match.start()].rstrip()
            guard_type = "css" if before.endswith('&') else "mixin"

            # Detect type-checking functions
            type_checks = [m.group(1).lower() for m in self.GUARD_TYPE_FUNCS.finditer(expr)]

            # Detect operators
            operators = [m.group(1).lower() for m in self.GUARD_OPERATORS.finditer(expr)]

            guards.append(LessGuardInfo(
                expression=expr.strip()[:100],
                guard_type=guard_type,
                type_checks=type_checks,
                operators=operators,
                file=file_path,
                line_number=line_num,
            ))

        return guards

    def _extract_namespaces(self, content: str, file_path: str) -> List[LessNamespaceInfo]:
        """Extract mixin namespace usages."""
        namespaces: Dict[str, LessNamespaceInfo] = {}

        for match in self.NAMESPACE_PATTERN.finditer(content):
            ns_name = match.group(1)
            member = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            # Detect access pattern
            between = content[match.start() + len(ns_name):match.start() + len(ns_name) + 5]
            access = '>' if '>' in between else '.'

            if ns_name not in namespaces:
                namespaces[ns_name] = LessNamespaceInfo(
                    name=ns_name,
                    members=[],
                    access_pattern=access,
                    file=file_path,
                    line_number=line_num,
                )
            if member not in namespaces[ns_name].members:
                namespaces[ns_name].members.append(member)

        return list(namespaces.values())

    def _find_matching_brace(self, content: str, start: int) -> int:
        """Find the matching closing brace for an opening brace at 'start'."""
        depth = 0
        i = start
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return len(content)
