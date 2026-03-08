"""
Python Parser - Extracts structure from .py files
==================================================
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ParsedClass:
    """Parsed Python class"""
    name: str
    bases: List[str] = field(default_factory=list)
    methods: List[Dict] = field(default_factory=list)
    attributes: List[Dict] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)


@dataclass
class ParsedFunction:
    """Parsed Python function"""
    name: str
    args: List[Dict] = field(default_factory=list)
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False


@dataclass
class ParsedRoute:
    """Parsed Flask/FastAPI route"""
    method: str
    path: str
    handler: str


class PythonParser:
    """
    Parser for Python files (Flask, FastAPI, classes, functions)
    """

    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse a Python file"""
        content = file_path.read_text()

        result = {
            "path": str(file_path),
            "type": self._detect_file_type(content),
            "imports": self._parse_imports(content),
            "classes": self._parse_classes(content),
            "functions": self._parse_functions(content),
            "routes": self._parse_routes(content),
            "exports": [],
        }

        return result

    def _detect_file_type(self, content: str) -> str:
        """Detect the type of Python file"""
        if "from flask" in content.lower() or "Flask(" in content:
            return "flask"
        elif "from fastapi" in content.lower() or "FastAPI(" in content:
            return "fastapi"
        elif "@dataclass" in content:
            return "dataclass"
        elif "class " in content:
            return "class"
        return "script"

    def _parse_imports(self, content: str) -> List[Dict]:
        """Parse import statements"""
        imports = []

        # from X import Y
        from_pattern = r"from\s+([\w.]+)\s+import\s+(.+)"
        for match in re.finditer(from_pattern, content):
            module = match.group(1)
            items = [i.strip() for i in match.group(2).split(",")]
            imports.append({
                "module": module,
                "items": items
            })

        # import X
        import_pattern = r"^import\s+([\w.]+)"
        for match in re.finditer(import_pattern, content, re.MULTILINE):
            imports.append({
                "module": match.group(1),
                "items": []
            })

        return imports

    def _parse_classes(self, content: str) -> List[ParsedClass]:
        """Parse class definitions"""
        classes = []

        # Pattern for class with optional decorators
        class_pattern = r"(?:@(\w+)(?:\([^)]*\))?\s*\n)*class\s+(\w+)(?:\(([^)]*)\))?"

        for match in re.finditer(class_pattern, content):
            decorator = match.group(1)
            class_name = match.group(2)
            bases = match.group(3)

            parsed_class = ParsedClass(name=class_name)

            if decorator:
                parsed_class.decorators.append(decorator)

            if bases:
                parsed_class.bases = [b.strip() for b in bases.split(",")]

            # Extract class body
            class_body = self._extract_body(content, match.end())
            if class_body:
                parsed_class.methods = self._parse_methods(class_body)
                parsed_class.attributes = self._parse_attributes(class_body)

            classes.append(parsed_class)

        return classes

    def _parse_methods(self, class_body: str) -> List[Dict]:
        """Parse class methods"""
        methods = []

        # Pattern for method definitions
        method_pattern = r"(?:@(\w+)(?:\([^)]*\))?\s*\n\s*)*(async\s+)?def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^:]+))?"

        for match in re.finditer(method_pattern, class_body):
            decorator = match.group(1)
            is_async = match.group(2) is not None
            method_name = match.group(3)
            args = match.group(4)
            return_type = match.group(5)

            # Parse arguments
            parsed_args = []
            if args:
                for arg in args.split(","):
                    arg = arg.strip()
                    if arg and arg != "self" and arg != "cls":
                        # Handle type annotations
                        if ":" in arg:
                            name, type_hint = arg.split(":", 1)
                            parsed_args.append({
                                "name": name.strip(),
                                "type": type_hint.strip()
                            })
                        else:
                            parsed_args.append({"name": arg})

            methods.append({
                "name": method_name,
                "args": parsed_args,
                "return_type": return_type.strip() if return_type else None,
                "is_async": is_async,
                "decorator": decorator
            })

        return methods

    def _parse_attributes(self, class_body: str) -> List[Dict]:
        """Parse class attributes"""
        attributes = []

        # Pattern for type-annotated attributes
        attr_pattern = r"^\s+(\w+):\s*([^=\n]+)(?:\s*=\s*(.+))?"

        for match in re.finditer(attr_pattern, class_body, re.MULTILINE):
            attr_name = match.group(1)
            attr_type = match.group(2).strip()
            default = match.group(3)

            if attr_name not in ["self", "cls"]:
                attributes.append({
                    "name": attr_name,
                    "type": attr_type,
                    "default": default.strip() if default else None
                })

        return attributes

    def _parse_functions(self, content: str) -> List[ParsedFunction]:
        """Parse top-level functions"""
        functions = []

        # Pattern for function definitions (not inside classes)
        func_pattern = r"^(?:@(\w+)(?:\([^)]*\))?\s*\n)*(async\s+)?def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^:]+))?"

        for match in re.finditer(func_pattern, content, re.MULTILINE):
            decorator = match.group(1)
            is_async = match.group(2) is not None
            func_name = match.group(3)
            args = match.group(4)
            return_type = match.group(5)

            func = ParsedFunction(
                name=func_name,
                is_async=is_async,
                return_type=return_type.strip() if return_type else None
            )

            if decorator:
                func.decorators.append(decorator)

            # Parse arguments
            if args:
                for arg in args.split(","):
                    arg = arg.strip()
                    if arg:
                        if ":" in arg:
                            name, type_hint = arg.split(":", 1)
                            func.args.append({
                                "name": name.strip(),
                                "type": type_hint.split("=")[0].strip()
                            })
                        else:
                            func.args.append({"name": arg.split("=")[0].strip()})

            functions.append(func)

        return functions

    def _parse_routes(self, content: str) -> List[ParsedRoute]:
        """Parse Flask/FastAPI routes"""
        routes = []

        # Flask pattern: @app.route('/path', methods=['GET'])
        flask_pattern = r"@\w+\.route\(['\"]([^'\"]+)['\"](?:,\s*methods=\[([^\]]+)\])?\)"

        for match in re.finditer(flask_pattern, content):
            path = match.group(1)
            methods = match.group(2)

            if methods:
                method_list = re.findall(r"['\"](\w+)['\"]", methods)
            else:
                method_list = ["GET"]

            # Find handler function name
            handler_match = re.search(
                r"@\w+\.route.*?\ndef\s+(\w+)",
                content[match.start():],
                re.DOTALL
            )
            handler = handler_match.group(1) if handler_match else "unknown"

            for method in method_list:
                routes.append(ParsedRoute(
                    method=method,
                    path=path,
                    handler=handler
                ))

        # FastAPI pattern: @app.get('/path')
        fastapi_pattern = r"@\w+\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]"

        for match in re.finditer(fastapi_pattern, content, re.IGNORECASE):
            method = match.group(1).upper()
            path = match.group(2)

            handler_match = re.search(
                r"@\w+\.\w+.*?\ndef\s+(\w+)",
                content[match.start():],
                re.DOTALL
            )
            handler = handler_match.group(1) if handler_match else "unknown"

            routes.append(ParsedRoute(
                method=method,
                path=path,
                handler=handler
            ))

        return routes

    def _extract_body(self, content: str, start_pos: int) -> Optional[str]:
        """Extract indented body after a definition"""
        # Find the colon and newline
        colon_pos = content.find(":", start_pos)
        if colon_pos == -1:
            return None

        newline_pos = content.find("\n", colon_pos)
        if newline_pos == -1:
            return None

        # Find the next line with content
        lines = content[newline_pos:].split("\n")
        if len(lines) < 2:
            return None

        # Get base indentation
        first_line = lines[1]
        if not first_line.strip():
            if len(lines) < 3:
                return None
            first_line = lines[2]

        base_indent = len(first_line) - len(first_line.lstrip())

        # Collect body lines
        body_lines = []
        for line in lines[1:]:
            if line.strip() == "":
                body_lines.append("")
            elif len(line) - len(line.lstrip()) >= base_indent:
                body_lines.append(line)
            else:
                break

        return "\n".join(body_lines)


# Convenience function
def parse_python(file_path: str) -> Dict:
    """Parse a Python file"""
    parser = PythonParser()
    return parser.parse(Path(file_path))
