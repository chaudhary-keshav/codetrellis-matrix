"""
NestJS Module Extractor - Per-file extraction of @Module() decorators and DI graph.

Supports:
- @Module() decorator parsing (imports, providers, controllers, exports)
- @Global() module detection
- Dynamic module patterns (forRoot, forRootAsync, forFeature, register, registerAsync)
- Module re-exports
- Custom provider definitions in module
- NestJS 7.x through 10.x module patterns
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class NestModuleDecoratorInfo:
    """A @Module() decorator definition found in a file."""
    class_name: str
    file: str = ""
    line_number: int = 0
    imports: List[str] = field(default_factory=list)
    providers: List[str] = field(default_factory=list)
    controllers: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    is_global: bool = False
    is_dynamic: bool = False


@dataclass
class NestProviderInfo:
    """A provider definition within a module."""
    name: str
    file: str = ""
    line_number: int = 0
    provide_token: str = ""  # { provide: TOKEN, ... }
    use_class: str = ""
    use_value: str = ""
    use_factory: str = ""
    use_existing: str = ""
    is_custom: bool = False


@dataclass
class NestDynamicModuleInfo:
    """A dynamic module method (forRoot, forFeature, etc.)."""
    method_name: str
    module_class: str = ""
    file: str = ""
    line_number: int = 0
    is_async: bool = False
    has_options: bool = False


class NestModuleExtractor:
    """Extracts NestJS module information from a single file."""

    # @Module() decorator
    MODULE_DECORATOR = re.compile(
        r'@Module\s*\(\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}\s*\)',
        re.DOTALL
    )

    # @Global() decorator
    GLOBAL_DECORATOR = re.compile(r'@Global\s*\(\s*\)')

    # Class definition after decorator
    CLASS_AFTER_DECORATOR = re.compile(
        r'(?:export\s+)?class\s+(\w+)'
    )

    # Module property patterns
    IMPORTS_PATTERN = re.compile(r'imports\s*:\s*\[([^\]]*)\]', re.DOTALL)
    PROVIDERS_PATTERN = re.compile(r'providers\s*:\s*\[([^\]]*)\]', re.DOTALL)
    CONTROLLERS_PATTERN = re.compile(r'controllers\s*:\s*\[([^\]]*)\]', re.DOTALL)
    EXPORTS_PATTERN = re.compile(r'exports\s*:\s*\[([^\]]*)\]', re.DOTALL)

    # Dynamic module methods
    DYNAMIC_MODULE_PATTERN = re.compile(
        r'(?:static\s+)?(?:async\s+)?(forRoot|forRootAsync|forFeature|forFeatureAsync|'
        r'register|registerAsync|forChild|forChildAsync)\s*\(',
    )

    # Custom provider patterns
    CUSTOM_PROVIDER_PATTERN = re.compile(
        r'\{\s*provide\s*:\s*(\w+(?:\.\w+)?|[\'"`][^\'"`]+[\'"`])\s*,'
        r'(?:\s*useClass\s*:\s*(\w+))?'
        r'(?:\s*useValue\s*:\s*([^,}]+))?'
        r'(?:\s*useFactory\s*:\s*([^,}]+))?'
        r'(?:\s*useExisting\s*:\s*(\w+))?',
        re.DOTALL
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract module information from a NestJS source file."""
        modules: List[NestModuleDecoratorInfo] = []
        providers: List[NestProviderInfo] = []
        dynamic_modules: List[NestDynamicModuleInfo] = []
        lines = content.split('\n')

        # Check for @Global() decorator
        has_global = bool(self.GLOBAL_DECORATOR.search(content))

        # Find @Module() decorators
        for match in self.MODULE_DECORATOR.finditer(content):
            module_body = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Find class name after decorator
            rest = content[match.end():]
            class_match = self.CLASS_AFTER_DECORATOR.search(rest)
            class_name = class_match.group(1) if class_match else 'UnknownModule'

            # Extract arrays
            imports = self._extract_array_items(self.IMPORTS_PATTERN, module_body)
            providers_list = self._extract_array_items(self.PROVIDERS_PATTERN, module_body)
            controllers = self._extract_array_items(self.CONTROLLERS_PATTERN, module_body)
            exports = self._extract_array_items(self.EXPORTS_PATTERN, module_body)

            modules.append(NestModuleDecoratorInfo(
                class_name=class_name,
                file=file_path,
                line_number=line_num,
                imports=imports,
                providers=providers_list,
                controllers=controllers,
                exports=exports,
                is_global=has_global,
                is_dynamic=bool(self.DYNAMIC_MODULE_PATTERN.search(content)),
            ))

            # Extract custom providers
            for cp_match in self.CUSTOM_PROVIDER_PATTERN.finditer(module_body):
                token = cp_match.group(1).strip("'\"` ")
                providers.append(NestProviderInfo(
                    name=token,
                    file=file_path,
                    line_number=line_num,
                    provide_token=token,
                    use_class=cp_match.group(2) or '',
                    use_value=(cp_match.group(3) or '').strip(),
                    use_factory=(cp_match.group(4) or '').strip(),
                    use_existing=cp_match.group(5) or '',
                    is_custom=True,
                ))

        # Find dynamic module methods
        for match in self.DYNAMIC_MODULE_PATTERN.finditer(content):
            method_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Find surrounding class
            before = content[:match.start()]
            class_match = re.search(r'class\s+(\w+)', before)
            module_class = ''
            if class_match:
                # Get last class before this method
                all_classes = re.findall(r'class\s+(\w+)', before)
                module_class = all_classes[-1] if all_classes else ''

            dynamic_modules.append(NestDynamicModuleInfo(
                method_name=method_name,
                module_class=module_class,
                file=file_path,
                line_number=line_num,
                is_async='Async' in method_name or 'async' in content[max(0, match.start()-20):match.start()],
                has_options='options' in content[match.start():match.start()+100].lower(),
            ))

        return {
            "modules": modules,
            "providers": providers,
            "dynamic_modules": dynamic_modules,
        }

    def _extract_array_items(self, pattern: re.Pattern, text: str) -> List[str]:
        """Extract items from a decorated array like imports: [A, B, C]."""
        match = pattern.search(text)
        if not match:
            return []
        items_str = match.group(1)
        # Split by comma, handle method calls like TypeOrmModule.forRoot(...)
        items = []
        depth = 0
        current = ''
        for ch in items_str:
            if ch in ('(', '[', '{'):
                depth += 1
                current += ch
            elif ch in (')', ']', '}'):
                depth -= 1
                current += ch
            elif ch == ',' and depth == 0:
                item = current.strip()
                if item:
                    items.append(item)
                current = ''
            else:
                current += ch
        item = current.strip()
        if item:
            items.append(item)
        return items
