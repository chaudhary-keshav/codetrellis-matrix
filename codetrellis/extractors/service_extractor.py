"""
ServiceExtractor - Extracts Angular services from TypeScript source code.

This extractor parses Angular @Injectable() decorated classes and extracts:
- Service name and provided configuration
- Injected dependencies (via constructor or inject())
- Public methods with their signatures
- Signal properties (state management)
- Computed properties
- Implements interfaces
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class InjectedDependency:
    """Represents an injected dependency in a service."""
    name: str
    type: str
    access_modifier: str = "private"  # private, public, protected, readonly


@dataclass
class MethodInfo:
    """Represents a method in a service."""
    name: str
    parameters: List[Dict[str, str]] = field(default_factory=list)
    return_type: str = "void"
    is_async: bool = False
    is_private: bool = False
    description: str = ""


@dataclass
class SignalProperty:
    """Represents a signal property in an Angular service."""
    name: str
    type: str
    initial_value: str = ""
    signal_type: str = "signal"  # signal, computed, effect


@dataclass
class ServiceInfo:
    """Complete information about an Angular service."""
    name: str
    provided_in: str = "root"
    is_exported: bool = True
    implements: List[str] = field(default_factory=list)
    dependencies: List[InjectedDependency] = field(default_factory=list)
    methods: List[MethodInfo] = field(default_factory=list)
    signals: List[SignalProperty] = field(default_factory=list)
    description: str = ""
    line_number: int = 0


class ServiceExtractor:
    """
    Extracts Angular service definitions from TypeScript source code.

    Handles:
    - @Injectable() decorated classes
    - Constructor injection
    - inject() function injection (Angular 14+)
    - Signal properties (Angular 16+)
    - Computed properties
    - Public and private methods
    """

    def __init__(self):
        # Patterns for service extraction
        self.injectable_pattern = re.compile(
            r'@Injectable\s*\(\s*\{([^}]*)\}\s*\)',
            re.MULTILINE | re.DOTALL
        )
        self.class_pattern = re.compile(
            r'export\s+class\s+(\w+)(?:\s+implements\s+([^{]+))?\s*\{',
            re.MULTILINE
        )
        self.constructor_pattern = re.compile(
            r'constructor\s*\(([^)]*)\)',
            re.MULTILINE | re.DOTALL
        )
        self.inject_pattern = re.compile(
            r'(?:private|public|protected|readonly)?\s*(\w+)\s*=\s*inject\s*\(\s*(\w+)\s*\)',
            re.MULTILINE
        )
        self.signal_pattern = re.compile(
            r'(?:private|public|protected|readonly)?\s*(\w+)\s*=\s*signal\s*<([^>]+)>\s*\(([^)]*)\)',
            re.MULTILINE
        )
        self.computed_pattern = re.compile(
            r'(?:private|public|protected|readonly)?\s*(\w+)\s*=\s*computed\s*\(\s*\(\)\s*=>',
            re.MULTILINE
        )
        self.method_pattern = re.compile(
            r'(?:async\s+)?(private\s+)?(\w+)\s*(?:<[^>]*>)?\s*\(([^)]*)\)(?:\s*:\s*([^{]+))?\s*\{',
            re.MULTILINE
        )

    def extract(self, content: str) -> List[ServiceInfo]:
        """
        Extract all Angular services from the given content.

        Args:
            content: TypeScript source code

        Returns:
            List of ServiceInfo objects
        """
        services = []

        # Find all @Injectable decorators and their positions
        injectable_matches = list(self.injectable_pattern.finditer(content))

        for injectable_match in injectable_matches:
            # Parse providedIn from decorator
            decorator_content = injectable_match.group(1)
            provided_in = self._extract_provided_in(decorator_content)

            # Find the class definition after the decorator
            class_start = injectable_match.end()
            class_match = self.class_pattern.search(content, class_start)

            if class_match and class_match.start() - class_start < 100:
                class_name = class_match.group(1)
                implements = self._parse_implements(class_match.group(2))

                # Extract class body
                class_body = self._extract_class_body(content, class_match.end() - 1)

                if class_body:
                    service = ServiceInfo(
                        name=class_name,
                        provided_in=provided_in,
                        implements=implements,
                        line_number=content[:injectable_match.start()].count('\n') + 1,
                    )

                    # Extract dependencies
                    service.dependencies = self._extract_dependencies(class_body, content[:class_match.start()])

                    # Extract signals
                    service.signals = self._extract_signals(class_body)

                    # Extract methods
                    service.methods = self._extract_methods(class_body)

                    services.append(service)

        return services

    def _extract_provided_in(self, decorator_content: str) -> str:
        """Extract providedIn value from decorator content."""
        match = re.search(r"providedIn\s*:\s*['\"](\w+)['\"]", decorator_content)
        if match:
            return match.group(1)
        return "root"

    def _parse_implements(self, implements_str: Optional[str]) -> List[str]:
        """Parse the implements clause."""
        if not implements_str:
            return []

        # Split by comma and clean up
        interfaces = [i.strip() for i in implements_str.split(',')]
        return [i for i in interfaces if i]

    def _extract_class_body(self, content: str, start_brace: int) -> Optional[str]:
        """Extract the class body by matching braces."""
        if content[start_brace] != '{':
            return None

        brace_count = 1
        pos = start_brace + 1

        while pos < len(content) and brace_count > 0:
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
            pos += 1

        return content[start_brace + 1:pos - 1]

    def _extract_dependencies(self, class_body: str, before_class: str) -> List[InjectedDependency]:
        """Extract injected dependencies from constructor and inject() calls."""
        dependencies = []

        # Method 1: Constructor injection
        constructor_match = self.constructor_pattern.search(class_body)
        if constructor_match:
            params = constructor_match.group(1)
            dependencies.extend(self._parse_constructor_params(params))

        # Method 2: inject() function (Angular 14+)
        for match in self.inject_pattern.finditer(class_body):
            name = match.group(1)
            dep_type = match.group(2)
            dependencies.append(InjectedDependency(
                name=name,
                type=dep_type,
                access_modifier="private"
            ))

        return dependencies

    def _parse_constructor_params(self, params: str) -> List[InjectedDependency]:
        """Parse constructor parameters for dependencies."""
        dependencies = []

        # Clean up the params
        params = params.strip()
        if not params:
            return dependencies

        # Pattern: (private|public|protected|readonly)? name: Type
        param_pattern = re.compile(
            r'(private|public|protected|readonly)?\s*(\w+)\s*:\s*(\w+(?:<[^>]+>)?)',
            re.MULTILINE
        )

        for match in param_pattern.finditer(params):
            access = match.group(1) or "private"
            name = match.group(2)
            dep_type = match.group(3)

            dependencies.append(InjectedDependency(
                name=name,
                type=dep_type,
                access_modifier=access
            ))

        return dependencies

    def _extract_signals(self, class_body: str) -> List[SignalProperty]:
        """Extract signal and computed properties."""
        signals = []

        # Signal properties
        for match in self.signal_pattern.finditer(class_body):
            signals.append(SignalProperty(
                name=match.group(1),
                type=match.group(2),
                initial_value=match.group(3).strip(),
                signal_type="signal"
            ))

        # Computed properties
        for match in self.computed_pattern.finditer(class_body):
            signals.append(SignalProperty(
                name=match.group(1),
                type="computed",
                signal_type="computed"
            ))

        return signals

    def _extract_methods(self, class_body: str) -> List[MethodInfo]:
        """Extract public and private methods."""
        methods = []

        # Skip constructor and lifecycle hooks
        skip_methods = {'constructor', 'ngOnInit', 'ngOnDestroy', 'ngOnChanges',
                        'ngAfterViewInit', 'ngAfterContentInit'}

        for match in self.method_pattern.finditer(class_body):
            is_private = match.group(1) is not None
            method_name = match.group(2)
            params_str = match.group(3)
            return_type = match.group(4).strip() if match.group(4) else "void"

            if method_name in skip_methods:
                continue

            # Skip getter/setter syntax
            if method_name in ('get', 'set'):
                continue

            # Check if async
            is_async = 'async' in match.group(0)

            # Parse parameters
            params = self._parse_method_params(params_str)

            methods.append(MethodInfo(
                name=method_name,
                parameters=params,
                return_type=return_type.strip(),
                is_async=is_async,
                is_private=is_private
            ))

        return methods

    def _parse_method_params(self, params_str: str) -> List[Dict[str, str]]:
        """Parse method parameters."""
        params = []

        params_str = params_str.strip()
        if not params_str:
            return params

        # Simple parameter extraction
        param_pattern = re.compile(r'(\w+)(?:\?)?:\s*([^,]+)')

        for match in param_pattern.finditer(params_str):
            params.append({
                'name': match.group(1),
                'type': match.group(2).strip()
            })

        return params

    def to_codetrellis_format(self, services: List[ServiceInfo]) -> str:
        """
        Convert extracted services to CodeTrellis format.

        Args:
            services: List of extracted services

        Returns:
            CodeTrellis formatted string
        """
        if not services:
            return ""

        lines = ["[SERVICES]"]

        for service in services:
            # Service header
            implements_str = f" implements {', '.join(service.implements)}" if service.implements else ""
            lines.append(f"  @Injectable({{providedIn: '{service.provided_in}'}}) class {service.name}{implements_str}:")

            # Dependencies
            if service.dependencies:
                deps = [f"{d.name}:{d.type}" for d in service.dependencies[:5]]
                deps_str = ', '.join(deps)
                if len(service.dependencies) > 5:
                    deps_str += f", +{len(service.dependencies) - 5}more"
                lines.append(f"    inject: [{deps_str}]")

            # Signals
            if service.signals:
                signals_str = ', '.join([f"{s.name}:{s.signal_type}" for s in service.signals[:5]])
                if len(service.signals) > 5:
                    signals_str += f", +{len(service.signals) - 5}more"
                lines.append(f"    signals: [{signals_str}]")

            # Public methods (skip private)
            public_methods = [m for m in service.methods if not m.is_private]
            if public_methods:
                methods_str = ', '.join([m.name for m in public_methods[:8]])
                if len(public_methods) > 8:
                    methods_str += f", +{len(public_methods) - 8}more"
                lines.append(f"    methods: [{methods_str}]")

            lines.append("")

        return '\n'.join(lines)


# Convenience function
def extract_services(content: str) -> List[ServiceInfo]:
    """
    Convenience function to extract services from content.

    Args:
        content: TypeScript source code

    Returns:
        List of ServiceInfo objects
    """
    extractor = ServiceExtractor()
    return extractor.extract(content)
