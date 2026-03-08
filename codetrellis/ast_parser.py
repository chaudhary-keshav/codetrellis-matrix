"""
CodeTrellis AST Parser - Tree-sitter based AST parsing
================================================

This module provides AST-based parsing using Tree-sitter for accurate
code extraction. This replaces regex-based parsing for better accuracy
and maintainability.

Version: 4.1.1
Created: 2 February 2026

Features:
- Python AST parsing (functions, classes, decorators, type hints)
- TypeScript AST parsing (interfaces, types, classes, functions)
- Unified extraction interface
- Error-resilient parsing
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator, Union
import logging

logger = logging.getLogger(__name__)

# Try to import tree-sitter - graceful fallback if not available
try:
    import tree_sitter
    from tree_sitter import Language, Parser
    import tree_sitter_python
    import tree_sitter_typescript
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    Language = None
    Parser = None
    logger.warning("Tree-sitter not available. Install with: pip install tree-sitter tree-sitter-python tree-sitter-typescript")


class LanguageType(Enum):
    """Supported languages for AST parsing."""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    TSX = "tsx"
    JAVASCRIPT = "javascript"


@dataclass
class ASTNode:
    """Represents an extracted AST node."""
    node_type: str  # function, class, interface, type, method, decorator
    name: str
    start_line: int
    end_line: int
    start_col: int = 0
    end_col: int = 0
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: Optional[str] = None
    parent: Optional[str] = None
    children: List['ASTNode'] = field(default_factory=list)
    modifiers: List[str] = field(default_factory=list)  # public, private, async, static
    extends: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    properties: List[Dict[str, Any]] = field(default_factory=list)
    body_preview: Optional[str] = None  # First few lines of body
    complexity: int = 0  # Cyclomatic complexity estimate

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'node_type': self.node_type,
            'name': self.name,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'docstring': self.docstring,
            'decorators': self.decorators,
            'parameters': self.parameters,
            'return_type': self.return_type,
            'parent': self.parent,
            'modifiers': self.modifiers,
            'extends': self.extends,
            'implements': self.implements,
            'properties': self.properties,
            'complexity': self.complexity,
        }


@dataclass
class ASTParseResult:
    """Result of AST parsing a file."""
    file_path: str
    language: LanguageType
    success: bool
    functions: List[ASTNode] = field(default_factory=list)
    classes: List[ASTNode] = field(default_factory=list)
    interfaces: List[ASTNode] = field(default_factory=list)
    types: List[ASTNode] = field(default_factory=list)
    imports: List[Dict[str, Any]] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    parse_time_ms: float = 0.0

    @property
    def total_nodes(self) -> int:
        """Total number of extracted nodes."""
        return len(self.functions) + len(self.classes) + len(self.interfaces) + len(self.types)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'file_path': self.file_path,
            'language': self.language.value,
            'success': self.success,
            'functions': [f.to_dict() for f in self.functions],
            'classes': [c.to_dict() for c in self.classes],
            'interfaces': [i.to_dict() for i in self.interfaces],
            'types': [t.to_dict() for t in self.types],
            'imports': self.imports,
            'exports': self.exports,
            'errors': self.errors,
            'parse_time_ms': self.parse_time_ms,
            'total_nodes': self.total_nodes,
        }


class BaseASTParser:
    """Base class for AST parsers."""

    def __init__(self):
        self.parser = None
        self.language = None

    def parse(self, content: str, file_path: str = "<unknown>") -> ASTParseResult:
        """Parse content and return AST result."""
        raise NotImplementedError

    def _get_node_text(self, node, source_bytes: bytes) -> str:
        """Extract text from a tree-sitter node."""
        return source_bytes[node.start_byte:node.end_byte].decode('utf-8', errors='replace')

    def _estimate_complexity(self, node, source_bytes: bytes) -> int:
        """Estimate cyclomatic complexity by counting control flow statements."""
        text = self._get_node_text(node, source_bytes)
        complexity = 1  # Base complexity

        # Count control flow keywords
        control_keywords = ['if', 'else', 'elif', 'for', 'while', 'try', 'except',
                          'catch', 'switch', 'case', '&&', '||', '?']
        for keyword in control_keywords:
            complexity += text.count(f' {keyword} ') + text.count(f'\n{keyword} ')

        return complexity


class PythonASTParser(BaseASTParser):
    """Tree-sitter based Python AST parser."""

    def __init__(self):
        super().__init__()
        if TREE_SITTER_AVAILABLE:
            # Wrap the language capsule with Language class
            py_lang = Language(tree_sitter_python.language())
            self.parser = Parser(py_lang)
        self.language = LanguageType.PYTHON

    def parse(self, content: str, file_path: str = "<unknown>") -> ASTParseResult:
        """Parse Python content using Tree-sitter."""
        import time
        start_time = time.perf_counter()

        result = ASTParseResult(
            file_path=file_path,
            language=self.language,
            success=False
        )

        if not TREE_SITTER_AVAILABLE:
            result.errors.append("Tree-sitter not available")
            return result

        try:
            source_bytes = content.encode('utf-8')
            tree = self.parser.parse(source_bytes)

            # Walk the AST
            self._walk_tree(tree.root_node, source_bytes, result)

            result.success = True
            result.parse_time_ms = (time.perf_counter() - start_time) * 1000

        except Exception as e:
            result.errors.append(f"Parse error: {str(e)}")
            logger.exception(f"Error parsing {file_path}")

        return result

    def _walk_tree(self, node, source_bytes: bytes, result: ASTParseResult, parent_name: str = None):
        """Recursively walk the AST and extract nodes."""

        if node.type == 'function_definition':
            func_node = self._extract_function(node, source_bytes, parent_name)
            if func_node:
                result.functions.append(func_node)
                # Check for nested functions
                for child in node.children:
                    if child.type == 'block':
                        self._walk_tree(child, source_bytes, result, func_node.name)

        elif node.type == 'class_definition':
            class_node = self._extract_class(node, source_bytes)
            if class_node:
                result.classes.append(class_node)
                # Extract methods
                for child in node.children:
                    if child.type == 'block':
                        self._walk_tree(child, source_bytes, result, class_node.name)

        elif node.type == 'import_statement' or node.type == 'import_from_statement':
            import_info = self._extract_import(node, source_bytes)
            if import_info:
                result.imports.append(import_info)

        else:
            # Recurse into children
            for child in node.children:
                self._walk_tree(child, source_bytes, result, parent_name)

    def _extract_function(self, node, source_bytes: bytes, parent_name: str = None) -> Optional[ASTNode]:
        """Extract function information from AST node."""
        name = None
        parameters = []
        return_type = None
        decorators = []
        docstring = None

        for child in node.children:
            if child.type == 'identifier':
                name = self._get_node_text(child, source_bytes)
            elif child.type == 'parameters':
                parameters = self._extract_parameters(child, source_bytes)
            elif child.type == 'type':
                return_type = self._get_node_text(child, source_bytes)
            elif child.type == 'block':
                # Check for docstring
                for block_child in child.children:
                    if block_child.type == 'expression_statement':
                        for expr_child in block_child.children:
                            if expr_child.type == 'string':
                                docstring = self._get_node_text(expr_child, source_bytes).strip('"""\'\'\'')
                                break
                        break

        # Get decorators from previous siblings
        prev = node.prev_named_sibling
        while prev and prev.type == 'decorator':
            dec_text = self._get_node_text(prev, source_bytes)
            decorators.insert(0, dec_text.lstrip('@'))
            prev = prev.prev_named_sibling

        if name:
            # Determine modifiers
            modifiers = []
            if name.startswith('_') and not name.startswith('__'):
                modifiers.append('private')
            if 'async' in self._get_node_text(node, source_bytes).split('\n')[0]:
                modifiers.append('async')
            if 'staticmethod' in decorators:
                modifiers.append('static')
            if 'classmethod' in decorators:
                modifiers.append('classmethod')

            return ASTNode(
                node_type='method' if parent_name else 'function',
                name=name,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                start_col=node.start_point[1],
                end_col=node.end_point[1],
                docstring=docstring,
                decorators=decorators,
                parameters=parameters,
                return_type=return_type,
                parent=parent_name,
                modifiers=modifiers,
                complexity=self._estimate_complexity(node, source_bytes)
            )
        return None

    def _extract_class(self, node, source_bytes: bytes) -> Optional[ASTNode]:
        """Extract class information from AST node."""
        name = None
        bases = []
        decorators = []
        docstring = None
        properties = []

        for child in node.children:
            if child.type == 'identifier':
                name = self._get_node_text(child, source_bytes)
            elif child.type == 'argument_list':
                # Base classes
                for arg in child.children:
                    if arg.type == 'identifier':
                        bases.append(self._get_node_text(arg, source_bytes))
            elif child.type == 'block':
                # Extract docstring and class-level attributes
                for block_child in child.children:
                    if block_child.type == 'expression_statement':
                        for expr_child in block_child.children:
                            if expr_child.type == 'string':
                                docstring = self._get_node_text(expr_child, source_bytes).strip('"""\'\'\'')
                                break
                    elif block_child.type == 'expression_statement':
                        # Class attribute assignment
                        text = self._get_node_text(block_child, source_bytes)
                        if ':' in text:
                            parts = text.split(':')
                            if len(parts) >= 2:
                                properties.append({
                                    'name': parts[0].strip(),
                                    'type': parts[1].split('=')[0].strip() if '=' in parts[1] else parts[1].strip()
                                })

        # Get decorators
        prev = node.prev_named_sibling
        while prev and prev.type == 'decorator':
            dec_text = self._get_node_text(prev, source_bytes)
            decorators.insert(0, dec_text.lstrip('@'))
            prev = prev.prev_named_sibling

        if name:
            return ASTNode(
                node_type='class',
                name=name,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                docstring=docstring,
                decorators=decorators,
                extends=bases[0] if bases else None,
                implements=bases[1:] if len(bases) > 1 else [],
                properties=properties,
                complexity=self._estimate_complexity(node, source_bytes)
            )
        return None

    def _extract_parameters(self, node, source_bytes: bytes) -> List[Dict[str, Any]]:
        """Extract function parameters."""
        params = []
        for child in node.children:
            if child.type in ('identifier', 'typed_parameter', 'default_parameter', 'typed_default_parameter'):
                param = {'name': '', 'type': None, 'default': None}

                if child.type == 'identifier':
                    param['name'] = self._get_node_text(child, source_bytes)
                else:
                    for sub in child.children:
                        if sub.type == 'identifier':
                            param['name'] = self._get_node_text(sub, source_bytes)
                        elif sub.type == 'type':
                            param['type'] = self._get_node_text(sub, source_bytes)

                if param['name'] and param['name'] not in ('self', 'cls'):
                    params.append(param)

        return params

    def _extract_import(self, node, source_bytes: bytes) -> Optional[Dict[str, Any]]:
        """Extract import information."""
        text = self._get_node_text(node, source_bytes)

        if node.type == 'import_statement':
            # import x, y, z
            return {'type': 'import', 'module': text.replace('import ', '').strip()}
        elif node.type == 'import_from_statement':
            # from x import y
            return {'type': 'from_import', 'statement': text}

        return None


class TypeScriptASTParser(BaseASTParser):
    """Tree-sitter based TypeScript AST parser."""

    def __init__(self, tsx: bool = False):
        super().__init__()
        if TREE_SITTER_AVAILABLE:
            lang_capsule = tree_sitter_typescript.language_tsx() if tsx else tree_sitter_typescript.language_typescript()
            ts_lang = Language(lang_capsule)
            self.parser = Parser(ts_lang)
        self.language = LanguageType.TSX if tsx else LanguageType.TYPESCRIPT

    def parse(self, content: str, file_path: str = "<unknown>") -> ASTParseResult:
        """Parse TypeScript content using Tree-sitter."""
        import time
        start_time = time.perf_counter()

        result = ASTParseResult(
            file_path=file_path,
            language=self.language,
            success=False
        )

        if not TREE_SITTER_AVAILABLE:
            result.errors.append("Tree-sitter not available")
            return result

        try:
            source_bytes = content.encode('utf-8')
            tree = self.parser.parse(source_bytes)

            # Walk the AST
            self._walk_tree(tree.root_node, source_bytes, result)

            result.success = True
            result.parse_time_ms = (time.perf_counter() - start_time) * 1000

        except Exception as e:
            result.errors.append(f"Parse error: {str(e)}")
            logger.exception(f"Error parsing {file_path}")

        return result

    def _walk_tree(self, node, source_bytes: bytes, result: ASTParseResult, parent_name: str = None):
        """Recursively walk the AST and extract nodes."""

        if node.type == 'function_declaration':
            func_node = self._extract_function(node, source_bytes, parent_name)
            if func_node:
                result.functions.append(func_node)

        elif node.type == 'arrow_function' and node.parent and node.parent.type == 'variable_declarator':
            # Named arrow function
            func_node = self._extract_arrow_function(node, source_bytes)
            if func_node:
                result.functions.append(func_node)

        elif node.type == 'class_declaration':
            class_node = self._extract_class(node, source_bytes)
            if class_node:
                result.classes.append(class_node)
                # Extract methods
                for child in node.children:
                    if child.type == 'class_body':
                        self._walk_tree(child, source_bytes, result, class_node.name)

        elif node.type == 'method_definition':
            method_node = self._extract_method(node, source_bytes, parent_name)
            if method_node:
                result.functions.append(method_node)

        elif node.type == 'interface_declaration':
            interface_node = self._extract_interface(node, source_bytes)
            if interface_node:
                result.interfaces.append(interface_node)

        elif node.type == 'type_alias_declaration':
            type_node = self._extract_type_alias(node, source_bytes)
            if type_node:
                result.types.append(type_node)

        elif node.type == 'import_statement':
            import_info = self._extract_import(node, source_bytes)
            if import_info:
                result.imports.append(import_info)

        elif node.type == 'export_statement':
            export_text = self._get_node_text(node, source_bytes)
            result.exports.append(export_text)
            # Collect decorators and modifiers from the export_statement level
            export_decorators = []
            for child in node.children:
                if child.type == 'decorator':
                    export_decorators.append(self._get_node_text(child, source_bytes).lstrip('@'))
            # Recurse into export children to extract interfaces, classes, functions
            for child in node.children:
                if child.type == 'class_declaration':
                    class_node = self._extract_class(child, source_bytes)
                    if class_node:
                        if 'export' not in class_node.modifiers:
                            class_node.modifiers.append('export')
                        class_node.decorators.extend(export_decorators)
                        result.classes.append(class_node)
                        for sub in child.children:
                            if sub.type == 'class_body':
                                self._walk_tree(sub, source_bytes, result, class_node.name)
                elif child.type == 'interface_declaration':
                    interface_node = self._extract_interface(child, source_bytes)
                    if interface_node:
                        if 'export' not in interface_node.modifiers:
                            interface_node.modifiers.append('export')
                        result.interfaces.append(interface_node)
                elif child.type == 'function_declaration':
                    func_node = self._extract_function(child, source_bytes, parent_name)
                    if func_node:
                        if 'export' not in func_node.modifiers:
                            func_node.modifiers.append('export')
                        result.functions.append(func_node)
                else:
                    self._walk_tree(child, source_bytes, result, parent_name)

        else:
            # Recurse into children
            for child in node.children:
                self._walk_tree(child, source_bytes, result, parent_name)

    def _extract_function(self, node, source_bytes: bytes, parent_name: str = None) -> Optional[ASTNode]:
        """Extract function declaration."""
        name = None
        parameters = []
        return_type = None
        modifiers = []

        for child in node.children:
            if child.type == 'identifier':
                name = self._get_node_text(child, source_bytes)
            elif child.type == 'formal_parameters':
                parameters = self._extract_parameters(child, source_bytes)
            elif child.type == 'type_annotation':
                return_type = self._get_node_text(child, source_bytes).lstrip(':').strip()
            elif child.type in ('async', 'export'):
                modifiers.append(child.type)

        if name:
            return ASTNode(
                node_type='function',
                name=name,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                parameters=parameters,
                return_type=return_type,
                parent=parent_name,
                modifiers=modifiers,
                complexity=self._estimate_complexity(node, source_bytes)
            )
        return None

    def _extract_arrow_function(self, node, source_bytes: bytes) -> Optional[ASTNode]:
        """Extract arrow function from variable declaration."""
        # Get the name from parent variable_declarator
        name = None
        if node.parent and node.parent.type == 'variable_declarator':
            for child in node.parent.children:
                if child.type == 'identifier':
                    name = self._get_node_text(child, source_bytes)
                    break

        parameters = []
        return_type = None

        for child in node.children:
            if child.type == 'formal_parameters':
                parameters = self._extract_parameters(child, source_bytes)
            elif child.type == 'type_annotation':
                return_type = self._get_node_text(child, source_bytes).lstrip(':').strip()

        if name:
            return ASTNode(
                node_type='function',
                name=name,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                parameters=parameters,
                return_type=return_type,
                modifiers=['arrow'],
                complexity=self._estimate_complexity(node, source_bytes)
            )
        return None

    def _extract_method(self, node, source_bytes: bytes, parent_name: str = None) -> Optional[ASTNode]:
        """Extract class method."""
        name = None
        parameters = []
        return_type = None
        modifiers = []
        decorators = []

        for child in node.children:
            if child.type == 'property_identifier':
                name = self._get_node_text(child, source_bytes)
            elif child.type == 'formal_parameters':
                parameters = self._extract_parameters(child, source_bytes)
            elif child.type == 'type_annotation':
                return_type = self._get_node_text(child, source_bytes).lstrip(':').strip()
            elif child.type == 'accessibility_modifier':
                modifiers.append(self._get_node_text(child, source_bytes))
            elif child.type in ('async', 'static', 'readonly'):
                modifiers.append(child.type)
            elif child.type == 'decorator':
                decorators.append(self._get_node_text(child, source_bytes).lstrip('@'))

        if name:
            return ASTNode(
                node_type='method',
                name=name,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                parameters=parameters,
                return_type=return_type,
                parent=parent_name,
                modifiers=modifiers,
                decorators=decorators,
                complexity=self._estimate_complexity(node, source_bytes)
            )
        return None

    def _extract_class(self, node, source_bytes: bytes) -> Optional[ASTNode]:
        """Extract class declaration."""
        name = None
        extends = None
        implements = []
        decorators = []
        modifiers = []
        properties = []

        for child in node.children:
            if child.type == 'type_identifier':
                name = self._get_node_text(child, source_bytes)
            elif child.type == 'class_heritage':
                # tree-sitter wraps extends/implements inside class_heritage
                for heritage_child in child.children:
                    if heritage_child.type == 'extends_clause':
                        for sub in heritage_child.children:
                            if sub.type == 'identifier' or sub.type == 'type_identifier':
                                extends = self._get_node_text(sub, source_bytes)
                                break
                    elif heritage_child.type == 'implements_clause':
                        for sub in heritage_child.children:
                            if sub.type == 'type_identifier':
                                implements.append(self._get_node_text(sub, source_bytes))
            elif child.type == 'extends_clause':
                for sub in child.children:
                    if sub.type == 'identifier' or sub.type == 'type_identifier':
                        extends = self._get_node_text(sub, source_bytes)
                        break
            elif child.type == 'implements_clause':
                for sub in child.children:
                    if sub.type == 'type_identifier':
                        implements.append(self._get_node_text(sub, source_bytes))
            elif child.type == 'decorator':
                decorators.append(self._get_node_text(child, source_bytes).lstrip('@'))
            elif child.type in ('export', 'abstract'):
                modifiers.append(child.type)
            elif child.type == 'class_body':
                # Extract properties
                for body_child in child.children:
                    if body_child.type == 'public_field_definition':
                        prop = self._extract_property(body_child, source_bytes)
                        if prop:
                            properties.append(prop)

        if name:
            return ASTNode(
                node_type='class',
                name=name,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                decorators=decorators,
                modifiers=modifiers,
                extends=extends,
                implements=implements,
                properties=properties,
                complexity=self._estimate_complexity(node, source_bytes)
            )
        return None

    def _extract_interface(self, node, source_bytes: bytes) -> Optional[ASTNode]:
        """Extract interface declaration."""
        name = None
        extends = []
        properties = []
        modifiers = []

        for child in node.children:
            if child.type == 'type_identifier':
                name = self._get_node_text(child, source_bytes)
            elif child.type == 'extends_type_clause':
                for sub in child.children:
                    if sub.type == 'type_identifier':
                        extends.append(self._get_node_text(sub, source_bytes))
            elif child.type == 'object_type' or child.type == 'interface_body':
                properties = self._extract_interface_properties(child, source_bytes)
            elif child.type == 'export':
                modifiers.append('export')

        if name:
            return ASTNode(
                node_type='interface',
                name=name,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                modifiers=modifiers,
                extends=extends[0] if extends else None,
                implements=extends[1:] if len(extends) > 1 else [],
                properties=properties
            )
        return None

    def _extract_type_alias(self, node, source_bytes: bytes) -> Optional[ASTNode]:
        """Extract type alias declaration."""
        name = None
        type_def = None
        modifiers = []

        for child in node.children:
            if child.type == 'type_identifier':
                name = self._get_node_text(child, source_bytes)
            elif child.type in ('union_type', 'intersection_type', 'type_identifier', 'object_type', 'literal_type'):
                type_def = self._get_node_text(child, source_bytes)
            elif child.type == 'export':
                modifiers.append('export')

        if name:
            return ASTNode(
                node_type='type',
                name=name,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                modifiers=modifiers,
                body_preview=type_def
            )
        return None

    def _extract_parameters(self, node, source_bytes: bytes) -> List[Dict[str, Any]]:
        """Extract function parameters."""
        params = []
        for child in node.children:
            if child.type in ('required_parameter', 'optional_parameter', 'rest_parameter'):
                param = {'name': '', 'type': None, 'optional': child.type == 'optional_parameter'}

                for sub in child.children:
                    if sub.type == 'identifier':
                        param['name'] = self._get_node_text(sub, source_bytes)
                    elif sub.type == 'type_annotation':
                        param['type'] = self._get_node_text(sub, source_bytes).lstrip(':').strip()

                if param['name']:
                    params.append(param)

        return params

    def _extract_interface_properties(self, node, source_bytes: bytes) -> List[Dict[str, Any]]:
        """Extract interface properties."""
        properties = []

        for child in node.children:
            if child.type == 'property_signature':
                prop = {'name': '', 'type': None, 'optional': False}

                for sub in child.children:
                    if sub.type == 'property_identifier':
                        prop['name'] = self._get_node_text(sub, source_bytes)
                    elif sub.type == 'type_annotation':
                        prop['type'] = self._get_node_text(sub, source_bytes).lstrip(':').strip()
                    elif sub.type == '?':
                        prop['optional'] = True

                if prop['name']:
                    properties.append(prop)

            elif child.type == 'method_signature':
                method = {'name': '', 'type': 'method', 'parameters': []}

                for sub in child.children:
                    if sub.type == 'property_identifier':
                        method['name'] = self._get_node_text(sub, source_bytes)
                    elif sub.type == 'formal_parameters':
                        method['parameters'] = self._extract_parameters(sub, source_bytes)
                    elif sub.type == 'type_annotation':
                        method['return_type'] = self._get_node_text(sub, source_bytes).lstrip(':').strip()

                if method['name']:
                    properties.append(method)

        return properties

    def _extract_property(self, node, source_bytes: bytes) -> Optional[Dict[str, Any]]:
        """Extract class property."""
        prop = {'name': '', 'type': None, 'modifiers': []}

        for child in node.children:
            if child.type == 'property_identifier':
                prop['name'] = self._get_node_text(child, source_bytes)
            elif child.type == 'type_annotation':
                prop['type'] = self._get_node_text(child, source_bytes).lstrip(':').strip()
            elif child.type == 'accessibility_modifier':
                prop['modifiers'].append(self._get_node_text(child, source_bytes))
            elif child.type in ('readonly', 'static'):
                prop['modifiers'].append(child.type)

        return prop if prop['name'] else None

    def _extract_import(self, node, source_bytes: bytes) -> Optional[Dict[str, Any]]:
        """Extract import information."""
        text = self._get_node_text(node, source_bytes)
        return {'type': 'import', 'statement': text}


class UnifiedASTParser:
    """
    Unified AST parser that automatically selects the appropriate
    language parser based on file extension.
    """

    def __init__(self):
        self._parsers: Dict[str, BaseASTParser] = {}

        # Initialize parsers lazily
        self._extension_map = {
            '.py': 'python',
            '.pyi': 'python',
            '.ts': 'typescript',
            '.tsx': 'tsx',
            '.js': 'typescript',  # Use TS parser for JS (superset)
            '.jsx': 'tsx',
        }

    def _get_parser(self, extension: str) -> Optional[BaseASTParser]:
        """Get or create parser for file extension."""
        parser_type = self._extension_map.get(extension.lower())

        if not parser_type:
            return None

        if parser_type not in self._parsers:
            if parser_type == 'python':
                self._parsers[parser_type] = PythonASTParser()
            elif parser_type == 'typescript':
                self._parsers[parser_type] = TypeScriptASTParser(tsx=False)
            elif parser_type == 'tsx':
                self._parsers[parser_type] = TypeScriptASTParser(tsx=True)

        return self._parsers.get(parser_type)

    def parse_file(self, file_path: Path) -> ASTParseResult:
        """Parse a file using the appropriate parser."""
        parser = self._get_parser(file_path.suffix)

        if not parser:
            return ASTParseResult(
                file_path=str(file_path),
                language=LanguageType.PYTHON,  # Default
                success=False,
                errors=[f"Unsupported file extension: {file_path.suffix}"]
            )

        try:
            content = file_path.read_text(encoding='utf-8')
            return parser.parse(content, str(file_path))
        except Exception as e:
            return ASTParseResult(
                file_path=str(file_path),
                language=parser.language,
                success=False,
                errors=[f"File read error: {str(e)}"]
            )

    def parse_content(self, content: str, file_path: str) -> ASTParseResult:
        """Parse content with explicit file path for language detection."""
        extension = Path(file_path).suffix
        parser = self._get_parser(extension)

        if not parser:
            return ASTParseResult(
                file_path=file_path,
                language=LanguageType.PYTHON,
                success=False,
                errors=[f"Unsupported file extension: {extension}"]
            )

        return parser.parse(content, file_path)

    @property
    def is_available(self) -> bool:
        """Check if Tree-sitter is available."""
        return TREE_SITTER_AVAILABLE


# Convenience function
def parse_file(file_path: Union[str, Path]) -> ASTParseResult:
    """Parse a file using the unified AST parser."""
    parser = UnifiedASTParser()
    return parser.parse_file(Path(file_path))


def parse_content(content: str, file_path: str) -> ASTParseResult:
    """Parse content using the unified AST parser."""
    parser = UnifiedASTParser()
    return parser.parse_content(content, file_path)
