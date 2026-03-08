"""
TypeScript Parser - Extracts structure from .ts files
======================================================
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ParsedSchema:
    """Parsed schema information"""
    name: str
    collection: Optional[str] = None
    fields: List[Dict] = field(default_factory=list)
    enums: List[Dict] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)
    timestamps: bool = False


@dataclass
class ParsedDTO:
    """Parsed DTO information"""
    name: str
    fields: List[Dict] = field(default_factory=list)
    validators: List[str] = field(default_factory=list)


@dataclass
class ParsedController:
    """Parsed controller information"""
    name: str
    prefix: str = "/"
    routes: List[Dict] = field(default_factory=list)
    guards: List[str] = field(default_factory=list)


@dataclass
class ParsedService:
    """Parsed service information"""
    name: str
    methods: List[str] = field(default_factory=list)
    injections: List[str] = field(default_factory=list)


class TypeScriptParser:
    """
    Parser for TypeScript files (NestJS schemas, DTOs, controllers, services)
    """

    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse a TypeScript file and extract all structured data"""
        content = file_path.read_text()
        file_name = file_path.name

        result = {
            "path": str(file_path),
            "type": self._detect_file_type(file_name, content),
            "exports": [],
            "imports": [],
        }

        # Extract imports
        result["imports"] = self._extract_imports(content)

        # Extract based on file type
        if ".schema.ts" in file_name:
            result["schemas"] = self._parse_schemas(content)
            result["enums"] = self._parse_enums(content)

        elif ".dto.ts" in file_name:
            result["dtos"] = self._parse_dtos(content)

        elif ".controller.ts" in file_name:
            result["controllers"] = self._parse_controllers(content)

        elif ".service.ts" in file_name:
            result["services"] = self._parse_services(content)

        elif ".guard.ts" in file_name:
            result["guards"] = self._parse_guards(content)

        elif ".module.ts" in file_name:
            result["modules"] = self._parse_modules(content)

        return result

    def _detect_file_type(self, file_name: str, content: str) -> str:
        """Detect the type of TypeScript file"""
        if ".schema.ts" in file_name:
            return "schema"
        elif ".dto.ts" in file_name:
            return "dto"
        elif ".controller.ts" in file_name:
            return "controller"
        elif ".service.ts" in file_name:
            return "service"
        elif ".guard.ts" in file_name:
            return "guard"
        elif ".module.ts" in file_name:
            return "module"
        elif ".component.ts" in file_name:
            return "component"
        elif "@Schema" in content:
            return "schema"
        elif "@Controller" in content:
            return "controller"
        return "unknown"

    def _extract_imports(self, content: str) -> List[Dict]:
        """Extract import statements"""
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

    def _parse_schemas(self, content: str) -> List[ParsedSchema]:
        """Parse Mongoose/NestJS schemas"""
        schemas = []

        # Find @Schema decorated classes
        schema_pattern = r"@Schema\(([^)]*)\)\s*export\s+class\s+(\w+)"

        for match in re.finditer(schema_pattern, content):
            options = match.group(1)
            class_name = match.group(2)

            schema = ParsedSchema(name=class_name)

            # Check for timestamps
            if "timestamps: true" in options or "timestamps:true" in options:
                schema.timestamps = True

            # Extract collection name
            collection_match = re.search(r"collection:\s*['\"](\w+)['\"]", options)
            if collection_match:
                schema.collection = collection_match.group(1)

            # Find the class body and extract fields
            class_body = self._extract_class_body(content, class_name)
            if class_body:
                schema.fields = self._parse_schema_fields(class_body)

            schemas.append(schema)

        return schemas

    def _parse_schema_fields(self, class_body: str) -> List[Dict]:
        """Parse @Prop decorated fields"""
        fields = []

        # Pattern for @Prop with options
        prop_pattern = r"@Prop\(([^)]*)\)\s*(\w+)(\?)?:\s*([^;]+);"

        for match in re.finditer(prop_pattern, class_body):
            options = match.group(1)
            field_name = match.group(2)
            optional = match.group(3) == "?"
            field_type = match.group(4).strip()

            field = {
                "name": field_name,
                "type": field_type,
                "required": "required: true" in options or "required:true" in options,
                "unique": "unique: true" in options or "unique:true" in options,
                "optional": optional,
            }

            # Check for default value
            default_match = re.search(r"default:\s*([^,}]+)", options)
            if default_match:
                field["default"] = default_match.group(1).strip()

            # Check for index
            if "index: true" in options or "index:true" in options:
                field["indexed"] = True

            fields.append(field)

        return fields

    def _parse_enums(self, content: str) -> List[Dict]:
        """Parse enum definitions"""
        enums = []

        enum_pattern = r"export\s+enum\s+(\w+)\s*\{([^}]+)\}"

        for match in re.finditer(enum_pattern, content):
            enum_name = match.group(1)
            enum_body = match.group(2)

            # Extract enum values
            values = []
            value_pattern = r"(\w+)\s*=\s*['\"]([^'\"]+)['\"]"
            for value_match in re.finditer(value_pattern, enum_body):
                values.append(value_match.group(2))

            enums.append({
                "name": enum_name,
                "values": values
            })

        return enums

    def _parse_dtos(self, content: str) -> List[ParsedDTO]:
        """Parse DTO classes"""
        dtos = []

        # Find exported classes ending with Dto
        class_pattern = r"export\s+class\s+(\w+Dto)\s*\{"

        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)

            dto = ParsedDTO(name=class_name)

            # Extract class body
            class_body = self._extract_class_body(content, class_name)
            if class_body:
                dto.fields = self._parse_dto_fields(class_body)

            dtos.append(dto)

        return dtos

    def _parse_dto_fields(self, class_body: str) -> List[Dict]:
        """Parse DTO fields with validators"""
        fields = []

        # Pattern for fields with decorators
        # Matches: @IsEmail() @IsNotEmpty() email: string;
        field_pattern = r"((?:@\w+\([^)]*\)\s*)+)(\w+)(\?)?:\s*([^;]+);"

        for match in re.finditer(field_pattern, class_body):
            decorators = match.group(1)
            field_name = match.group(2)
            optional = match.group(3) == "?"
            field_type = match.group(4).strip()

            # Extract validator names
            validators = re.findall(r"@(\w+)", decorators)

            fields.append({
                "name": field_name,
                "type": field_type,
                "optional": optional,
                "validators": validators
            })

        return fields

    def _parse_controllers(self, content: str) -> List[ParsedController]:
        """Parse controller classes"""
        controllers = []

        # Find @Controller decorated classes
        ctrl_pattern = r"@Controller\(['\"]([^'\"]*)['\"]"

        for match in re.finditer(ctrl_pattern, content):
            prefix = match.group(1)

            # Find class name after decorator
            class_match = re.search(
                r"@Controller.*?export\s+class\s+(\w+)",
                content[match.start():],
                re.DOTALL
            )

            if class_match:
                class_name = class_match.group(1)

                controller = ParsedController(
                    name=class_name,
                    prefix=prefix
                )

                # Extract routes
                controller.routes = self._parse_routes(content)

                # Extract guards
                guard_pattern = r"@UseGuards\(([^)]+)\)"
                for guard_match in re.finditer(guard_pattern, content):
                    guards = guard_match.group(1).split(",")
                    controller.guards.extend([g.strip() for g in guards])

                controllers.append(controller)

        return controllers

    def _parse_routes(self, content: str) -> List[Dict]:
        """Parse route handlers"""
        routes = []

        # Pattern for route decorators
        route_pattern = r"@(Get|Post|Put|Delete|Patch)\(['\"]?([^'\")]*)['\"]?\)"

        for match in re.finditer(route_pattern, content):
            method = match.group(1).upper()
            path = match.group(2) or "/"

            # Try to find the method name
            method_match = re.search(
                r"@" + match.group(1) + r".*?\n\s*(?:async\s+)?(\w+)\s*\(",
                content[match.start():],
                re.DOTALL
            )

            handler = method_match.group(1) if method_match else "unknown"

            routes.append({
                "method": method,
                "path": path,
                "handler": handler
            })

        return routes

    def _parse_services(self, content: str) -> List[ParsedService]:
        """Parse service classes"""
        services = []

        # Find @Injectable decorated classes
        class_pattern = r"@Injectable\([^)]*\)\s*export\s+class\s+(\w+)"

        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)

            service = ParsedService(name=class_name)

            # Extract constructor injections
            ctor_pattern = r"constructor\s*\(([^)]+)\)"
            ctor_match = re.search(ctor_pattern, content)
            if ctor_match:
                params = ctor_match.group(1)
                # Extract parameter types
                param_pattern = r"(?:private|public|readonly)\s+\w+:\s*(\w+)"
                service.injections = re.findall(param_pattern, params)

            # Extract public methods
            method_pattern = r"(?:async\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{"
            for method_match in re.finditer(method_pattern, content):
                method_name = method_match.group(1)
                if method_name not in ["constructor", "if", "for", "while"]:
                    service.methods.append(method_name)

            services.append(service)

        return services

    def _parse_guards(self, content: str) -> List[Dict]:
        """Parse guard classes"""
        guards = []

        class_pattern = r"@Injectable\([^)]*\)\s*export\s+class\s+(\w+Guard)"

        for match in re.finditer(class_pattern, content):
            guards.append({
                "name": match.group(1)
            })

        return guards

    def _parse_modules(self, content: str) -> List[Dict]:
        """Parse NestJS modules"""
        modules = []

        # Find @Module decorated classes
        module_pattern = r"@Module\(\{([^}]+)\}\)"

        for match in re.finditer(module_pattern, content, re.DOTALL):
            module_body = match.group(1)

            # Find class name
            class_match = re.search(
                r"@Module.*?export\s+class\s+(\w+)",
                content,
                re.DOTALL
            )

            module = {
                "name": class_match.group(1) if class_match else "Unknown",
                "imports": [],
                "controllers": [],
                "providers": [],
                "exports": []
            }

            # Extract arrays
            for key in ["imports", "controllers", "providers", "exports"]:
                array_pattern = rf"{key}:\s*\[([^\]]+)\]"
                array_match = re.search(array_pattern, module_body)
                if array_match:
                    items = array_match.group(1)
                    module[key] = [i.strip() for i in items.split(",") if i.strip()]

            modules.append(module)

        return modules

    def _extract_class_body(self, content: str, class_name: str) -> Optional[str]:
        """Extract the body of a class"""
        # Find class definition
        pattern = rf"class\s+{class_name}\s*(?:extends\s+\w+\s*)?(?:implements\s+[\w,\s]+\s*)?\{{"
        match = re.search(pattern, content)

        if not match:
            return None

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
def parse_typescript(file_path: str) -> Dict:
    """Parse a TypeScript file"""
    parser = TypeScriptParser()
    return parser.parse(Path(file_path))
