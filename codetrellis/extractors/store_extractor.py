"""
StoreExtractor - Extracts NgRx SignalStore definitions from TypeScript source code.

This extractor parses NgRx signalStore() definitions and extracts:
- Store name and configuration
- Initial state shape
- Computed properties (withComputed)
- Methods/actions (withMethods)
- Store feature composition
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class StoreStateProperty:
    """Represents a property in the store's initial state."""
    name: str
    type: str
    initial_value: str = ""
    readonly: bool = True


@dataclass
class StoreComputedProperty:
    """Represents a computed property in the store."""
    name: str
    description: str = ""


@dataclass
class StoreMethod:
    """Represents a method/action in the store."""
    name: str
    parameters: List[Dict[str, str]] = field(default_factory=list)
    description: str = ""


@dataclass
class StoreInfo:
    """Complete information about an NgRx SignalStore."""
    name: str
    provided_in: str = "root"
    is_exported: bool = True
    state_properties: List[StoreStateProperty] = field(default_factory=list)
    computed_properties: List[StoreComputedProperty] = field(default_factory=list)
    methods: List[StoreMethod] = field(default_factory=list)
    features: List[str] = field(default_factory=list)  # withState, withComputed, withMethods, etc.
    description: str = ""
    line_number: int = 0


class StoreExtractor:
    """
    Extracts NgRx SignalStore definitions from TypeScript source code.

    Handles:
    - signalStore() factory function
    - withState() for initial state
    - withComputed() for selectors
    - withMethods() for actions
    - Store type exports
    """

    def __init__(self):
        # Pattern for signalStore definition
        self.store_pattern = re.compile(
            r'export\s+const\s+(\w+Store)\s*=\s*signalStore\s*\(',
            re.MULTILINE
        )
        # Pattern for store type export
        self.store_type_pattern = re.compile(
            r'export\s+type\s+(\w+StoreType)\s*=\s*InstanceType<typeof\s+(\w+Store)>',
            re.MULTILINE
        )
        # Pattern for initial state interface
        self.state_interface_pattern = re.compile(
            r'interface\s+(\w+State)\s*\{([^}]+)\}',
            re.MULTILINE | re.DOTALL
        )
        # Pattern for withState
        self.with_state_pattern = re.compile(
            r'withState\s*\(\s*(\w+)\s*\)',
            re.MULTILINE
        )
        # Pattern for withComputed
        self.with_computed_pattern = re.compile(
            r'withComputed\s*\(\s*\([^)]*\)\s*=>\s*\(\{([^}]+)\}\)',
            re.MULTILINE | re.DOTALL
        )
        # Pattern for withMethods
        self.with_methods_pattern = re.compile(
            r'withMethods\s*\(\s*\([^)]*\)\s*=>\s*\(\{([^}]+)\}\)',
            re.MULTILINE | re.DOTALL
        )
        # Pattern for providedIn in signalStore config
        self.provided_in_pattern = re.compile(
            r"\{\s*providedIn\s*:\s*['\"](\w+)['\"]",
            re.MULTILINE
        )

    def extract(self, content: str) -> List[StoreInfo]:
        """
        Extract all NgRx SignalStores from the given content.

        Args:
            content: TypeScript source code

        Returns:
            List of StoreInfo objects
        """
        stores = []

        # Find all signalStore definitions
        for store_match in self.store_pattern.finditer(content):
            store_name = store_match.group(1)
            store_start = store_match.end()

            # Find the complete signalStore call
            store_body = self._extract_store_body(content, store_start - 1)

            if store_body:
                store = StoreInfo(
                    name=store_name,
                    line_number=content[:store_match.start()].count('\n') + 1,
                )

                # Extract providedIn
                provided_in_match = self.provided_in_pattern.search(store_body)
                if provided_in_match:
                    store.provided_in = provided_in_match.group(1)

                # Extract features used
                store.features = self._extract_features(store_body)

                # Extract state properties from associated interface
                store.state_properties = self._extract_state_properties(content, store_name)

                # Extract computed properties
                store.computed_properties = self._extract_computed_properties(store_body)

                # Extract methods
                store.methods = self._extract_methods(store_body)

                stores.append(store)

        return stores

    def _extract_store_body(self, content: str, start_paren: int) -> Optional[str]:
        """Extract the signalStore() call body by matching parentheses."""
        # Find the opening parenthesis
        while start_paren < len(content) and content[start_paren] != '(':
            start_paren += 1

        if start_paren >= len(content):
            return None

        paren_count = 1
        pos = start_paren + 1

        while pos < len(content) and paren_count > 0:
            if content[pos] == '(':
                paren_count += 1
            elif content[pos] == ')':
                paren_count -= 1
            pos += 1

        return content[start_paren + 1:pos - 1]

    def _extract_features(self, store_body: str) -> List[str]:
        """Extract the features used in the store (withState, withComputed, etc.)."""
        features = []

        feature_patterns = [
            ('withState', r'withState\s*\('),
            ('withComputed', r'withComputed\s*\('),
            ('withMethods', r'withMethods\s*\('),
            ('withEntities', r'withEntities\s*\('),
            ('withHooks', r'withHooks\s*\('),
            ('withCallState', r'withCallState\s*\('),
        ]

        for name, pattern in feature_patterns:
            if re.search(pattern, store_body):
                features.append(name)

        return features

    def _extract_state_properties(self, content: str, store_name: str) -> List[StoreStateProperty]:
        """Extract state properties from the state interface."""
        properties = []

        # Look for state interface (e.g., WorkerTileState for WorkerTileStore)
        state_name = store_name.replace('Store', 'State')

        # Find the interface
        interface_pattern = re.compile(
            rf'interface\s+{state_name}\s*\{{([^}}]+)\}}',
            re.MULTILINE | re.DOTALL
        )

        match = interface_pattern.search(content)
        if match:
            body = match.group(1)

            # Extract properties
            prop_pattern = re.compile(
                r'(?:readonly\s+)?(\w+)(\?)?:\s*([^;]+);',
                re.MULTILINE
            )

            for prop_match in prop_pattern.finditer(body):
                properties.append(StoreStateProperty(
                    name=prop_match.group(1),
                    type=prop_match.group(3).strip(),
                    readonly=True
                ))

        return properties

    def _extract_computed_properties(self, store_body: str) -> List[StoreComputedProperty]:
        """Extract computed properties from withComputed."""
        computed = []

        # Find withComputed block
        match = self.with_computed_pattern.search(store_body)
        if match:
            computed_body = match.group(1)

            # Extract property names
            prop_pattern = re.compile(r'(\w+)\s*:\s*computed\s*\(', re.MULTILINE)

            for prop_match in prop_pattern.finditer(computed_body):
                computed.append(StoreComputedProperty(
                    name=prop_match.group(1)
                ))

        return computed

    def _extract_methods(self, store_body: str) -> List[StoreMethod]:
        """Extract methods from withMethods."""
        methods = []

        # Find withMethods block
        match = self.with_methods_pattern.search(store_body)
        if match:
            methods_body = match.group(1)

            # Extract method names (simplified - looks for method: patterns)
            method_pattern = re.compile(r'(\w+)\s*(?:\([^)]*\))?\s*[:{]', re.MULTILINE)

            seen_methods = set()
            for method_match in method_pattern.finditer(methods_body):
                name = method_match.group(1)
                # Skip common keywords
                if name in ('return', 'if', 'else', 'const', 'let', 'var', 'function', 'patchState'):
                    continue
                if name not in seen_methods:
                    seen_methods.add(name)
                    methods.append(StoreMethod(name=name))

        return methods

    def to_codetrellis_format(self, stores: List[StoreInfo]) -> str:
        """
        Convert extracted stores to CodeTrellis format.

        Args:
            stores: List of extracted stores

        Returns:
            CodeTrellis formatted string
        """
        if not stores:
            return ""

        lines = ["[STORES]"]

        for store in stores:
            # Store header
            lines.append(f"  signalStore {store.name} (providedIn: '{store.provided_in}'):")

            # Features
            if store.features:
                lines.append(f"    features: [{', '.join(store.features)}]")

            # State properties (first 5)
            if store.state_properties:
                state_props = [f"{p.name}:{p.type[:20]}..." if len(p.type) > 20 else f"{p.name}:{p.type}"
                              for p in store.state_properties[:5]]
                state_str = ', '.join(state_props)
                if len(store.state_properties) > 5:
                    state_str += f", +{len(store.state_properties) - 5}more"
                lines.append(f"    state: [{state_str}]")

            # Computed properties
            if store.computed_properties:
                computed_str = ', '.join([c.name for c in store.computed_properties[:5]])
                if len(store.computed_properties) > 5:
                    computed_str += f", +{len(store.computed_properties) - 5}more"
                lines.append(f"    computed: [{computed_str}]")

            # Methods
            if store.methods:
                methods_str = ', '.join([m.name for m in store.methods[:8]])
                if len(store.methods) > 8:
                    methods_str += f", +{len(store.methods) - 8}more"
                lines.append(f"    methods: [{methods_str}]")

            lines.append("")

        return '\n'.join(lines)


# Convenience function
def extract_stores(content: str) -> List[StoreInfo]:
    """
    Convenience function to extract stores from content.

    Args:
        content: TypeScript source code

    Returns:
        List of StoreInfo objects
    """
    extractor = StoreExtractor()
    return extractor.extract(content)
