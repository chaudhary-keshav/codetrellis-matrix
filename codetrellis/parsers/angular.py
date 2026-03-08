"""
Angular Parser - Extracts structure from Angular component files
=================================================================
"""

import re
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class ParsedComponent:
    """Parsed Angular component"""
    name: str
    selector: str = ""
    standalone: bool = False
    inputs: List[Dict] = field(default_factory=list)
    outputs: List[Dict] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    template_url: str = ""
    style_urls: List[str] = field(default_factory=list)


@dataclass
class ParsedService:
    """Parsed Angular service"""
    name: str
    provided_in: str = "root"
    methods: List[Dict] = field(default_factory=list)
    injections: List[str] = field(default_factory=list)


class AngularParser:
    """
    Parser for Angular component and service files
    Supports Angular 17+ features (signals, new control flow, standalone)
    """

    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse an Angular file"""
        content = file_path.read_text()
        file_name = file_path.name

        result = {
            "path": str(file_path),
            "type": self._detect_file_type(file_name, content),
            "imports": self._parse_imports(content),
        }

        if ".component.ts" in file_name:
            result["components"] = self._parse_components(content)
        elif ".service.ts" in file_name:
            result["services"] = self._parse_services(content)
        elif ".module.ts" in file_name:
            result["modules"] = self._parse_modules(content)
        elif ".directive.ts" in file_name:
            result["directives"] = self._parse_directives(content)
        elif ".pipe.ts" in file_name:
            result["pipes"] = self._parse_pipes(content)

        return result

    def _detect_file_type(self, file_name: str, content: str) -> str:
        """Detect Angular file type"""
        if ".component.ts" in file_name:
            return "component"
        elif ".service.ts" in file_name:
            return "service"
        elif ".module.ts" in file_name:
            return "module"
        elif ".directive.ts" in file_name:
            return "directive"
        elif ".pipe.ts" in file_name:
            return "pipe"
        elif ".guard.ts" in file_name:
            return "guard"
        elif ".interceptor.ts" in file_name:
            return "interceptor"
        return "unknown"

    def _parse_imports(self, content: str) -> List[Dict]:
        """Parse import statements"""
        imports = []
        pattern = r"import\s+\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]"

        for match in re.finditer(pattern, content):
            items = [i.strip() for i in match.group(1).split(",")]
            source = match.group(2)
            imports.append({
                "items": items,
                "source": source
            })

        return imports

    def _parse_components(self, content: str) -> List[ParsedComponent]:
        """Parse Angular components"""
        components = []

        # Find @Component decorator
        component_pattern = r"@Component\(\{([^}]+(?:\{[^}]*\}[^}]*)*)\}\)"

        for match in re.finditer(component_pattern, content, re.DOTALL):
            decorator_body = match.group(1)

            component = ParsedComponent(name="Unknown")

            # Extract selector
            selector_match = re.search(r"selector:\s*['\"]([^'\"]+)['\"]", decorator_body)
            if selector_match:
                component.selector = selector_match.group(1)

            # Check standalone
            if "standalone: true" in decorator_body or "standalone:true" in decorator_body:
                component.standalone = True

            # Extract templateUrl
            template_match = re.search(r"templateUrl:\s*['\"]([^'\"]+)['\"]", decorator_body)
            if template_match:
                component.template_url = template_match.group(1)

            # Extract styleUrls
            style_match = re.search(r"styleUrls:\s*\[([^\]]+)\]", decorator_body)
            if style_match:
                component.style_urls = re.findall(r"['\"]([^'\"]+)['\"]", style_match.group(1))

            # Extract imports (for standalone components)
            imports_match = re.search(r"imports:\s*\[([^\]]+)\]", decorator_body)
            if imports_match:
                component.imports = [i.strip() for i in imports_match.group(1).split(",") if i.strip()]

            # Find class name
            class_match = re.search(
                r"@Component.*?export\s+class\s+(\w+)",
                content[match.start():],
                re.DOTALL
            )
            if class_match:
                component.name = class_match.group(1)

            # Extract class body
            class_body = self._extract_class_body(content, component.name)
            if class_body:
                # Parse inputs (both decorator and signal syntax)
                component.inputs = self._parse_inputs(class_body)
                # Parse outputs
                component.outputs = self._parse_outputs(class_body)

            components.append(component)

        return components

    def _parse_inputs(self, class_body: str) -> List[Dict]:
        """Parse component inputs (both @Input and input() signal)"""
        inputs = []

        # Traditional @Input decorator
        input_pattern = r"@Input\(([^)]*)\)\s*(\w+)(?:\?)?:\s*([^;=]+)"

        for match in re.finditer(input_pattern, class_body):
            options = match.group(1)
            name = match.group(2)
            input_type = match.group(3).strip()

            input_info = {
                "name": name,
                "type": input_type,
                "syntax": "decorator"
            }

            # Check for required
            if "required: true" in options:
                input_info["required"] = True

            # Check for alias
            alias_match = re.search(r"['\"](\w+)['\"]", options)
            if alias_match:
                input_info["alias"] = alias_match.group(1)

            inputs.append(input_info)

        # Angular 17+ signal input syntax: name = input<Type>()
        signal_pattern = r"(\w+)\s*=\s*input(?:\.required)?<([^>]*)>\s*\("

        for match in re.finditer(signal_pattern, class_body):
            name = match.group(1)
            input_type = match.group(2)
            required = ".required" in class_body[match.start():match.end()+20]

            inputs.append({
                "name": name,
                "type": input_type,
                "syntax": "signal",
                "required": required
            })

        return inputs

    def _parse_outputs(self, class_body: str) -> List[Dict]:
        """Parse component outputs (both @Output and output() signal)"""
        outputs = []

        # Traditional @Output decorator
        output_pattern = r"@Output\(([^)]*)\)\s*(\w+)\s*=\s*new\s*EventEmitter<([^>]*)>"

        for match in re.finditer(output_pattern, class_body):
            name = match.group(2)
            event_type = match.group(3)

            outputs.append({
                "name": name,
                "type": event_type,
                "syntax": "decorator"
            })

        # Angular 17+ signal output syntax: name = output<Type>()
        signal_output_pattern = r"(\w+)\s*=\s*output<([^>]*)>\s*\("

        for match in re.finditer(signal_output_pattern, class_body):
            name = match.group(1)
            event_type = match.group(2)

            outputs.append({
                "name": name,
                "type": event_type,
                "syntax": "signal"
            })

        return outputs

    def _parse_services(self, content: str) -> List[ParsedService]:
        """Parse Angular services"""
        services = []

        # Find @Injectable decorator
        injectable_pattern = r"@Injectable\(\{([^}]*)\}\)"

        for match in re.finditer(injectable_pattern, content):
            decorator_body = match.group(1)

            service = ParsedService(name="Unknown")

            # Extract providedIn
            provided_match = re.search(r"providedIn:\s*['\"](\w+)['\"]", decorator_body)
            if provided_match:
                service.provided_in = provided_match.group(1)

            # Find class name
            class_match = re.search(
                r"@Injectable.*?export\s+class\s+(\w+)",
                content[match.start():],
                re.DOTALL
            )
            if class_match:
                service.name = class_match.group(1)

            # Extract class body
            class_body = self._extract_class_body(content, service.name)
            if class_body:
                # Parse constructor injections
                service.injections = self._parse_injections(class_body)
                # Parse methods
                service.methods = self._parse_methods(class_body)

            services.append(service)

        return services

    def _parse_injections(self, class_body: str) -> List[str]:
        """Parse constructor injections"""
        injections = []

        # Find constructor
        ctor_pattern = r"constructor\s*\(([^)]+)\)"
        ctor_match = re.search(ctor_pattern, class_body)

        if ctor_match:
            params = ctor_match.group(1)
            # Extract parameter types
            param_pattern = r"(?:private|public|readonly)\s+\w+:\s*(\w+)"
            injections = re.findall(param_pattern, params)

        # Also check for inject() function (Angular 14+)
        inject_pattern = r"=\s*inject\((\w+)\)"
        inject_matches = re.findall(inject_pattern, class_body)
        injections.extend(inject_matches)

        return injections

    def _parse_methods(self, class_body: str) -> List[Dict]:
        """Parse service methods"""
        methods = []

        method_pattern = r"(?:async\s+)?(\w+)\s*\(([^)]*)\)(?:\s*:\s*([^{]+))?\s*\{"

        for match in re.finditer(method_pattern, class_body):
            method_name = match.group(1)
            params = match.group(2)
            return_type = match.group(3)

            if method_name not in ["constructor", "if", "for", "while", "switch"]:
                methods.append({
                    "name": method_name,
                    "params": params.strip() if params else "",
                    "return_type": return_type.strip() if return_type else None
                })

        return methods

    def _parse_modules(self, content: str) -> List[Dict]:
        """Parse Angular modules"""
        modules = []

        module_pattern = r"@NgModule\(\{([^}]+(?:\{[^}]*\}[^}]*)*)\}\)"

        for match in re.finditer(module_pattern, content, re.DOTALL):
            module_body = match.group(1)

            module = {
                "declarations": [],
                "imports": [],
                "exports": [],
                "providers": []
            }

            # Find class name
            class_match = re.search(
                r"@NgModule.*?export\s+class\s+(\w+)",
                content[match.start():],
                re.DOTALL
            )
            if class_match:
                module["name"] = class_match.group(1)

            # Extract arrays
            for key in ["declarations", "imports", "exports", "providers"]:
                array_pattern = rf"{key}:\s*\[([^\]]+)\]"
                array_match = re.search(array_pattern, module_body)
                if array_match:
                    items = array_match.group(1)
                    module[key] = [i.strip() for i in items.split(",") if i.strip()]

            modules.append(module)

        return modules

    def _parse_directives(self, content: str) -> List[Dict]:
        """Parse Angular directives"""
        directives = []

        directive_pattern = r"@Directive\(\{([^}]+)\}\)"

        for match in re.finditer(directive_pattern, content):
            decorator_body = match.group(1)

            directive = {}

            # Extract selector
            selector_match = re.search(r"selector:\s*['\"]([^'\"]+)['\"]", decorator_body)
            if selector_match:
                directive["selector"] = selector_match.group(1)

            # Find class name
            class_match = re.search(
                r"@Directive.*?export\s+class\s+(\w+)",
                content[match.start():],
                re.DOTALL
            )
            if class_match:
                directive["name"] = class_match.group(1)

            directives.append(directive)

        return directives

    def _parse_pipes(self, content: str) -> List[Dict]:
        """Parse Angular pipes"""
        pipes = []

        pipe_pattern = r"@Pipe\(\{([^}]+)\}\)"

        for match in re.finditer(pipe_pattern, content):
            decorator_body = match.group(1)

            pipe = {}

            # Extract name
            name_match = re.search(r"name:\s*['\"]([^'\"]+)['\"]", decorator_body)
            if name_match:
                pipe["pipe_name"] = name_match.group(1)

            # Find class name
            class_match = re.search(
                r"@Pipe.*?export\s+class\s+(\w+)",
                content[match.start():],
                re.DOTALL
            )
            if class_match:
                pipe["class_name"] = class_match.group(1)

            pipes.append(pipe)

        return pipes

    def _extract_class_body(self, content: str, class_name: str) -> str:
        """Extract class body"""
        pattern = rf"class\s+{class_name}\s*(?:extends\s+\w+\s*)?(?:implements\s+[\w,\s]+\s*)?\{{"
        match = re.search(pattern, content)

        if not match:
            return ""

        start = match.end()
        brace_count = 1
        end = start

        while end < len(content) and brace_count > 0:
            if content[end] == "{":
                brace_count += 1
            elif content[end] == "}":
                brace_count -= 1
            end += 1

        return content[start:end-1]


# Convenience function
def parse_angular(file_path: str) -> Dict:
    """Parse an Angular file"""
    parser = AngularParser()
    return parser.parse(Path(file_path))
