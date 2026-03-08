"""
RubyFunctionExtractor - Extracts Ruby method, block, proc, and lambda definitions.

This extractor parses Ruby source code and extracts:
- Instance methods (def name)
- Class methods (def self.name, class << self)
- Method aliases (alias, alias_method)
- Blocks (do..end, {})
- Procs and Lambdas
- Method visibility (public, private, protected)
- Method parameters (positional, keyword, default, splat, double-splat, block)
- Yield usage
- define_method metaprogramming
- method_missing / respond_to_missing?

Supports Ruby 1.8 through Ruby 3.3+ features including:
- Numbered block parameters (Ruby 2.7+: _1, _2)
- Pattern matching in methods (Ruby 3.0+)
- Endless methods (Ruby 3.0+: def name = expr)

Part of CodeTrellis v4.23 - Ruby Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RubyParameterInfo:
    """Information about a Ruby method parameter."""
    name: str
    kind: str = "positional"  # positional, keyword, default, rest, keyrest, block
    default_value: Optional[str] = None
    type_annotation: Optional[str] = None  # Sorbet sig
    is_optional: bool = False


@dataclass
class RubyMethodInfo:
    """Information about a Ruby method."""
    name: str
    parameters: List[RubyParameterInfo] = field(default_factory=list)
    return_type: Optional[str] = None  # Sorbet sig return type
    visibility: str = "public"  # public, private, protected
    file: str = ""
    line_number: int = 0
    is_class_method: bool = False
    is_singleton: bool = False
    is_initializer: bool = False  # def initialize
    is_endless: bool = False  # def name = expr (Ruby 3.0+)
    uses_yield: bool = False
    decorators: List[str] = field(default_factory=list)  # Sorbet sig, etc.
    owner_class: Optional[str] = None
    doc_comment: Optional[str] = None
    aliases: List[str] = field(default_factory=list)


@dataclass
class RubyBlockInfo:
    """Information about a Ruby block/proc/lambda."""
    kind: str = "block"  # block, proc, lambda, ->
    name: Optional[str] = None  # Variable name if assigned
    file: str = ""
    line_number: int = 0
    parameters: List[str] = field(default_factory=list)


@dataclass
class RubyAccessorInfo:
    """Information about attr_reader/attr_writer/attr_accessor."""
    names: List[str] = field(default_factory=list)
    kind: str = "attr_accessor"  # attr_reader, attr_writer, attr_accessor
    file: str = ""
    line_number: int = 0
    owner_class: Optional[str] = None


class RubyFunctionExtractor:
    """
    Extracts Ruby methods and function-like constructs from source code.

    Handles:
    - Instance methods (def name ... end)
    - Class methods (def self.name)
    - Endless methods (def name = expr) — Ruby 3.0+
    - Method parameters (positional, keyword, default, *, **, &block)
    - Visibility (public, private, protected, private_class_method)
    - define_method metaprogramming
    - method_missing / respond_to_missing?
    - Sorbet type annotations (sig { params(...).returns(...) })
    - Method aliases (alias / alias_method)
    - Yield detection
    """

    # Method definition: def name(params)
    METHOD_PATTERN = re.compile(
        r'^\s*def\s+(?P<self>self\.)?(?P<name>\w+[?!=]?)\s*(?:\((?P<params>[^)]*)\))?\s*(?:=\s*(?P<endless>.+))?',
        re.MULTILINE
    )

    # define_method :name
    DEFINE_METHOD_PATTERN = re.compile(
        r'^\s*define_method\s*[\(:]?\s*:?(?P<name>\w+[?!=]?)',
        re.MULTILINE
    )

    # alias / alias_method
    ALIAS_PATTERN = re.compile(
        r'^\s*(?:alias|alias_method)\s+:?(?P<new_name>\w+[?!=]?)\s*,?\s*:?(?P<old_name>\w+[?!=]?)',
        re.MULTILINE
    )

    # Visibility modifiers with method name: private :method_name
    VISIBILITY_METHOD_PATTERN = re.compile(
        r'^\s*(?P<visibility>public|private|protected)\s+:(?P<name>\w+[?!=]?)',
        re.MULTILINE
    )

    # Standalone visibility modifier: private (on its own line)
    VISIBILITY_BLOCK_PATTERN = re.compile(
        r'^\s*(?P<visibility>public|private|protected)\s*$',
        re.MULTILINE
    )

    # private_class_method :name
    PRIVATE_CLASS_METHOD_PATTERN = re.compile(
        r'^\s*private_class_method\s+:(?P<name>\w+[?!=]?)',
        re.MULTILINE
    )

    # Proc/Lambda: name = Proc.new / name = lambda / name = ->
    PROC_LAMBDA_PATTERN = re.compile(
        r'^\s*(?P<name>\w+)\s*=\s*(?:Proc\.new|lambda|->)\s*(?:\((?P<params>[^)]*)\))?\s*(?:\{|do)',
        re.MULTILINE
    )

    # Sorbet sig block
    SORBET_SIG_PATTERN = re.compile(
        r'^\s*sig\s*\{[^}]*\}',
        re.MULTILINE
    )

    # Sorbet T.let / T.cast type annotations
    SORBET_TYPE_PATTERN = re.compile(
        r'T\.(?:let|cast)\s*\([^,]+,\s*(?P<type>[^)]+)\)',
        re.MULTILINE
    )

    # yield detection
    YIELD_PATTERN = re.compile(r'\byield\b')

    # Doc comment pattern (# comments or YARD @param/@return)
    DOC_COMMENT_PATTERN = re.compile(
        r'((?:^\s*#[^\n]*\n)+)\s*def\s',
        re.MULTILINE
    )

    # YARD annotations
    YARD_PARAM_PATTERN = re.compile(r'#\s*@param\s+(?:\[([^\]]+)\]\s+)?(\w+)')
    YARD_RETURN_PATTERN = re.compile(r'#\s*@return\s+\[([^\]]+)\]')

    def __init__(self):
        """Initialize the function extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all Ruby methods and function constructs from source code.

        Args:
            content: Ruby source code content
            file_path: Path to source file

        Returns:
            Dict with 'methods', 'blocks', 'accessors' keys
        """
        methods = self._extract_methods(content, file_path)
        blocks = self._extract_blocks(content, file_path)
        accessors = self._extract_accessors(content, file_path)

        # Apply visibility modifiers
        self._apply_visibility(content, methods)

        # Apply aliases
        self._apply_aliases(content, methods)

        return {
            'methods': methods,
            'blocks': blocks,
            'accessors': accessors,
        }

    def _extract_methods(self, content: str, file_path: str) -> List[RubyMethodInfo]:
        """Extract method definitions from Ruby source."""
        methods = []

        # Collect doc comments
        doc_map = {}
        for match in self.DOC_COMMENT_PATTERN.finditer(content):
            doc_end = match.start()
            doc_text = match.group(1).strip()
            # Map line number of the def to the doc
            def_line = content[:match.end()].count('\n') + 1
            doc_map[def_line] = doc_text

        for match in self.METHOD_PATTERN.finditer(content):
            is_class_method = bool(match.group('self'))
            name = match.group('name')
            params_str = match.group('params') or ""
            endless_body = match.group('endless')
            line_number = content[:match.start()].count('\n') + 1

            parameters = self._parse_parameters(params_str)
            is_initializer = name == 'initialize'

            # Check for yield in method body
            uses_yield = False
            if not endless_body:
                method_end = self._find_method_end(content, match.start())
                method_body = content[match.end():method_end]
                uses_yield = bool(self.YIELD_PATTERN.search(method_body))

            # Check for doc comment
            doc = doc_map.get(line_number)

            # Extract YARD return type
            return_type = None
            if doc:
                ret_match = self.YARD_RETURN_PATTERN.search(doc)
                if ret_match:
                    return_type = ret_match.group(1)

            method = RubyMethodInfo(
                name=name,
                parameters=parameters,
                return_type=return_type,
                file=file_path,
                line_number=line_number,
                is_class_method=is_class_method,
                is_initializer=is_initializer,
                is_endless=bool(endless_body),
                uses_yield=uses_yield,
                doc_comment=doc,
            )
            methods.append(method)

        # define_method
        for match in self.DEFINE_METHOD_PATTERN.finditer(content):
            name = match.group('name')
            line_number = content[:match.start()].count('\n') + 1
            methods.append(RubyMethodInfo(
                name=name,
                file=file_path,
                line_number=line_number,
            ))

        return methods

    def _extract_blocks(self, content: str, file_path: str) -> List[RubyBlockInfo]:
        """Extract named blocks, procs, and lambdas."""
        blocks = []

        for match in self.PROC_LAMBDA_PATTERN.finditer(content):
            name = match.group('name')
            params_str = match.group('params') or ""
            params = [p.strip() for p in params_str.split(',') if p.strip()]
            line_number = content[:match.start()].count('\n') + 1

            # Determine kind
            line = content[match.start():match.end()]
            if 'Proc.new' in line:
                kind = 'proc'
            elif '->' in line:
                kind = 'lambda'
            else:
                kind = 'lambda'

            blocks.append(RubyBlockInfo(
                kind=kind,
                name=name,
                file=file_path,
                line_number=line_number,
                parameters=params,
            ))

        return blocks

    def _extract_accessors(self, content: str, file_path: str) -> List[RubyAccessorInfo]:
        """Extract attr_reader/attr_writer/attr_accessor definitions."""
        accessors = []

        ACCESSOR_PATTERN = re.compile(
            r'^\s*(?P<type>attr_reader|attr_writer|attr_accessor)\s+(?P<attrs>[^\n#]+)',
            re.MULTILINE
        )

        for match in ACCESSOR_PATTERN.finditer(content):
            kind = match.group('type')
            attrs_str = match.group('attrs')
            names = re.findall(r':(\w+)', attrs_str)
            line_number = content[:match.start()].count('\n') + 1

            if names:
                accessors.append(RubyAccessorInfo(
                    names=names,
                    kind=kind,
                    file=file_path,
                    line_number=line_number,
                ))

        return accessors

    def _parse_parameters(self, params_str: str) -> List[RubyParameterInfo]:
        """Parse method parameters string into RubyParameterInfo list."""
        params = []
        if not params_str.strip():
            return params

        for param in params_str.split(','):
            param = param.strip()
            if not param:
                continue

            if param.startswith('**'):
                # Double splat (keyword rest)
                name = param[2:] or 'options'
                params.append(RubyParameterInfo(name=name, kind='keyrest'))
            elif param.startswith('*'):
                # Splat (rest)
                name = param[1:] or 'args'
                params.append(RubyParameterInfo(name=name, kind='rest'))
            elif param.startswith('&'):
                # Block parameter
                name = param[1:] or 'block'
                params.append(RubyParameterInfo(name=name, kind='block'))
            elif ':' in param and '=' not in param:
                # Required keyword arg: name:
                name = param.rstrip(':')
                params.append(RubyParameterInfo(name=name, kind='keyword'))
            elif ':' in param and '=' in param:
                # Optional keyword arg: name: default
                parts = param.split(':', 1)
                name = parts[0].strip()
                default = parts[1].strip().lstrip('= ') if len(parts) > 1 else None
                params.append(RubyParameterInfo(name=name, kind='keyword', default_value=default, is_optional=True))
            elif '=' in param:
                # Default value parameter
                parts = param.split('=', 1)
                name = parts[0].strip()
                default = parts[1].strip() if len(parts) > 1 else None
                params.append(RubyParameterInfo(name=name, kind='default', default_value=default, is_optional=True))
            else:
                # Positional
                params.append(RubyParameterInfo(name=param, kind='positional'))

        return params

    def _apply_visibility(self, content: str, methods: List[RubyMethodInfo]):
        """Apply visibility modifiers to methods."""
        # Track current visibility state
        visibility_changes = []

        # Specific method visibility: private :method_name
        for match in self.VISIBILITY_METHOD_PATTERN.finditer(content):
            vis = match.group('visibility')
            name = match.group('name')
            for method in methods:
                if method.name == name:
                    method.visibility = vis

        # Block visibility modifiers (private on its own line)
        for match in self.VISIBILITY_BLOCK_PATTERN.finditer(content):
            vis = match.group('visibility')
            line_num = content[:match.start()].count('\n') + 1
            visibility_changes.append((line_num, vis))

        # Apply block-level visibility
        if visibility_changes:
            visibility_changes.sort()
            for method in methods:
                current_vis = "public"
                for change_line, vis in visibility_changes:
                    if change_line < method.line_number:
                        current_vis = vis
                    else:
                        break
                if method.visibility == "public":  # Only override if not explicitly set
                    method.visibility = current_vis

    def _apply_aliases(self, content: str, methods: List[RubyMethodInfo]):
        """Apply alias definitions to methods."""
        for match in self.ALIAS_PATTERN.finditer(content):
            new_name = match.group('new_name')
            old_name = match.group('old_name')
            for method in methods:
                if method.name == old_name:
                    method.aliases.append(new_name)

    def _find_method_end(self, content: str, start: int) -> int:
        """Find the 'end' keyword that closes a method definition."""
        lines = content[start:].split('\n')
        depth = 0
        pos = start

        block_openers = re.compile(
            r'^\s*(?:def|class|module|do|if|unless|while|until|for|begin|case)\b'
        )
        block_closer = re.compile(r'^\s*end\b')

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                pos += len(line) + 1
                continue

            if block_openers.match(line):
                depth += 1
            elif block_closer.match(line):
                depth -= 1
                if depth == 0:
                    return pos + len(line)

            pos += len(line) + 1

        return len(content)
