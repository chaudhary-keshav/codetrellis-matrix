"""
JavaFunctionExtractor - Extracts Java methods, constructors, and function-like patterns.

Extracts:
- Instance methods with full signatures
- Static methods
- Constructors
- Abstract methods
- Default interface methods
- Lambda expressions (detected)
- Method references (detected)

Part of CodeTrellis v4.12 - Java Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class JavaParameterInfo:
    """Information about a Java method parameter."""
    name: str
    type: str
    annotations: List[str] = field(default_factory=list)
    is_varargs: bool = False
    is_final: bool = False


@dataclass
class JavaMethodInfo:
    """Information about a Java method."""
    name: str
    return_type: str = "void"
    parameters: List[JavaParameterInfo] = field(default_factory=list)
    modifiers: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    throws: List[str] = field(default_factory=list)
    generic_params: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_exported: bool = True
    is_static: bool = False
    is_abstract: bool = False
    is_synchronized: bool = False
    is_default: bool = False  # interface default method
    is_override: bool = False
    class_name: Optional[str] = None  # containing class
    javadoc: Optional[str] = None


@dataclass
class JavaConstructorInfo:
    """Information about a Java constructor."""
    class_name: str
    parameters: List[JavaParameterInfo] = field(default_factory=list)
    modifiers: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    throws: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    is_exported: bool = True


class JavaFunctionExtractor:
    """
    Extracts Java method and constructor definitions from source code.

    Handles:
    - Full method signatures with generics, throws clauses
    - Access modifiers (public, protected, private, package-private)
    - Static, abstract, synchronized, default, native methods
    - @Override detection
    - Constructors (name matches class name)
    - Parameter annotations (@RequestBody, @PathVariable, etc.)
    - Varargs parameters
    """

    # Method pattern (comprehensive)
    METHOD_PATTERN = re.compile(
        r'(?:(/\*\*.*?\*/)\s*)?'                     # Optional javadoc
        r'((?:@\w+(?:\([^)]*\))?[\s\n]*)*)'          # Annotations
        r'((?:public|protected|private|static|final|abstract|synchronized|native|default|strictfp)\s+)*'  # Modifiers
        r'(?:<([^>]+)>\s+)?'                          # Optional generic type params
        r'([\w<>\[\].,?\s]+?)\s+'                     # Return type
        r'(\w+)\s*'                                   # Method name
        r'\(([^)]*)\)'                                # Parameters
        r'(?:\s+throws\s+([\w,\s.]+))?'               # Optional throws
        r'\s*(?:\{|;)',                                # Body start or semicolon (abstract)
        re.MULTILINE | re.DOTALL
    )

    # Constructor pattern
    CONSTRUCTOR_PATTERN = re.compile(
        r'((?:@\w+(?:\([^)]*\))?[\s\n]*)*)'          # Annotations
        r'((?:public|protected|private)\s+)?'          # Modifier
        r'(\w+)\s*'                                    # Class name
        r'\(([^)]*)\)'                                # Parameters
        r'(?:\s+throws\s+([\w,\s.]+))?'               # Optional throws
        r'\s*\{',                                      # Body start
        re.MULTILINE | re.DOTALL
    )

    # Lambda detection pattern
    LAMBDA_PATTERN = re.compile(
        r'(?:\(([^)]*)\)|(\w+))\s*->\s*(?:\{|[^;{]+)',
        re.MULTILINE
    )

    # Method reference pattern
    METHOD_REF_PATTERN = re.compile(
        r'([\w.]+)::([\w<>]+)',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def _parse_parameters(self, params_str: str) -> List[JavaParameterInfo]:
        """Parse method parameters into structured info."""
        if not params_str or not params_str.strip():
            return []

        params = []
        # Split on commas respecting generics depth
        parts = self._split_params(params_str)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            annotations = []
            is_final = False
            is_varargs = False

            # Extract annotations
            while part.startswith('@'):
                ann_match = re.match(r'@(\w+(?:\([^)]*\))?)\s*', part)
                if ann_match:
                    annotations.append(ann_match.group(1))
                    part = part[ann_match.end():]
                else:
                    break

            # Check final
            if part.startswith('final '):
                is_final = True
                part = part[6:]

            # Check varargs
            if '...' in part:
                is_varargs = True
                part = part.replace('...', '')

            # Split type and name
            parts_split = part.rsplit(None, 1)
            if len(parts_split) == 2:
                param_type, param_name = parts_split
                params.append(JavaParameterInfo(
                    name=param_name.strip(),
                    type=param_type.strip(),
                    annotations=annotations,
                    is_varargs=is_varargs,
                    is_final=is_final,
                ))
            elif len(parts_split) == 1:
                # Might just be a type in an interface declaration
                params.append(JavaParameterInfo(
                    name="",
                    type=parts_split[0].strip(),
                ))

        return params

    def _split_params(self, params_str: str) -> List[str]:
        """Split parameter list respecting generic brackets."""
        params = []
        depth = 0
        current = ""
        for ch in params_str:
            if ch in ('<', '(', '['):
                depth += 1
                current += ch
            elif ch in ('>', ')', ']'):
                depth -= 1
                current += ch
            elif ch == ',' and depth == 0:
                params.append(current.strip())
                current = ""
            else:
                current += ch
        if current.strip():
            params.append(current.strip())
        return params

    def extract(self, content: str, file_path: str = "", class_names: List[str] = None) -> Dict[str, Any]:
        """
        Extract methods and constructors from Java source code.

        Args:
            content: Java source code
            file_path: Path to the file
            class_names: List of class names in the file (for constructor detection)

        Returns:
            Dict with 'methods', 'constructors', 'lambda_count', 'method_ref_count'
        """
        if class_names is None:
            # Auto-detect class names
            class_names = re.findall(r'class\s+(\w+)', content)

        methods = []
        constructors = []

        # Control flow keywords to exclude
        KEYWORDS = {'if', 'for', 'while', 'switch', 'try', 'catch', 'return',
                     'throw', 'new', 'super', 'this', 'else', 'do', 'assert',
                     'case', 'break', 'continue', 'finally', 'class', 'interface',
                     'enum', 'import', 'package', 'var', 'yield'}

        for match in self.METHOD_PATTERN.finditer(content):
            javadoc = match.group(1)
            annotations_str = match.group(2) or ""
            modifiers_str = match.group(3) or ""
            generic_params_str = match.group(4)
            return_type = match.group(5).strip()
            method_name = match.group(6)
            params_str = match.group(7)
            throws_str = match.group(8)

            # Skip keywords and constructors
            if method_name in KEYWORDS:
                continue
            if return_type in KEYWORDS:
                continue

            # Check if this is a constructor (return type matches class name)
            if method_name in class_names and return_type == method_name:
                continue  # Will be caught by constructor pattern

            modifiers = modifiers_str.split() if modifiers_str else []
            annotations = re.findall(r'@(\w+(?:\([^)]*\))?)', annotations_str)
            parameters = self._parse_parameters(params_str)
            throws = [t.strip() for t in throws_str.split(',')] if throws_str else []
            generic_params = [g.strip() for g in generic_params_str.split(',')] if generic_params_str else []

            is_override = any(a.startswith('Override') for a in annotations)

            javadoc_text = None
            if javadoc:
                cleaned = re.sub(r'/\*\*|\*/|\*', '', javadoc).strip()
                lines = [l.strip() for l in cleaned.split('\n') if l.strip() and not l.strip().startswith('@')]
                if lines:
                    javadoc_text = lines[0][:200]

            line_number = content[:match.start()].count('\n') + 1

            # Determine containing class
            containing_class = None
            for cn in class_names:
                class_decl = re.search(rf'class\s+{re.escape(cn)}\b', content)
                if class_decl and class_decl.start() < match.start():
                    containing_class = cn

            methods.append(JavaMethodInfo(
                name=method_name,
                return_type=return_type,
                parameters=parameters,
                modifiers=modifiers,
                annotations=annotations,
                throws=throws,
                generic_params=generic_params,
                file=file_path,
                line_number=line_number,
                is_exported='public' in modifiers or 'protected' in modifiers,
                is_static='static' in modifiers,
                is_abstract='abstract' in modifiers,
                is_synchronized='synchronized' in modifiers,
                is_default='default' in modifiers,
                is_override=is_override,
                class_name=containing_class,
                javadoc=javadoc_text,
            ))

        # Extract constructors
        for cn in class_names:
            # Find constructors specifically for each class
            ctor_pattern = re.compile(
                rf'((?:@\w+(?:\([^)]*\))?[\s\n]*)*)'
                rf'((?:public|protected|private)\s+)?'
                rf'{re.escape(cn)}\s*'
                rf'\(([^)]*)\)'
                rf'(?:\s+throws\s+([\w,\s.]+))?'
                rf'\s*\{{',
                re.MULTILINE | re.DOTALL
            )
            for match in ctor_pattern.finditer(content):
                annotations_str = match.group(1) or ""
                modifiers_str = match.group(2) or ""
                params_str = match.group(3)
                throws_str = match.group(4)

                modifiers = modifiers_str.split() if modifiers_str else []
                annotations = re.findall(r'@(\w+(?:\([^)]*\))?)', annotations_str)
                parameters = self._parse_parameters(params_str)
                throws = [t.strip() for t in throws_str.split(',')] if throws_str else []

                line_number = content[:match.start()].count('\n') + 1

                constructors.append(JavaConstructorInfo(
                    class_name=cn,
                    parameters=parameters,
                    modifiers=modifiers,
                    annotations=annotations,
                    throws=throws,
                    file=file_path,
                    line_number=line_number,
                    is_exported='public' in modifiers or 'protected' in modifiers,
                ))

        # Count lambdas and method references
        lambda_count = len(self.LAMBDA_PATTERN.findall(content))
        method_ref_count = len(self.METHOD_REF_PATTERN.findall(content))

        return {
            'methods': methods,
            'constructors': constructors,
            'lambda_count': lambda_count,
            'method_ref_count': method_ref_count,
        }
