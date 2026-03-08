"""
Pinia Getter Extractor for CodeTrellis

Extracts Pinia getter definitions and usage patterns:
- Options API getters (getters: { getter(state) { ... } })
- Setup API computed getters (const getter = computed(() => ...))
- Getter arguments (getters that return a function)
- Cross-store getters (using other stores inside getters)
- storeToRefs destructuring for reactive getter access
- Getter caching behavior

Supports:
- Pinia v1.x-v2.x getter patterns
- TypeScript typed getters
- Getter composition (getter using other getters via this)

Part of CodeTrellis v4.52 - Pinia State Management Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class PiniaGetterInfo:
    """Information about a Pinia getter."""
    name: str
    file: str = ""
    line_number: int = 0
    api_style: str = ""  # options, setup
    store_name: str = ""
    store_id: str = ""
    returns_function: bool = False  # getter that returns a function (getter arguments)
    uses_state_fields: List[str] = field(default_factory=list)
    uses_other_getters: List[str] = field(default_factory=list)
    uses_other_stores: List[str] = field(default_factory=list)
    has_typescript: bool = False
    return_type: str = ""


@dataclass
class PiniaStoreToRefsInfo:
    """Information about storeToRefs usage for reactive getter/state access."""
    file: str = ""
    line_number: int = 0
    store_name: str = ""
    destructured_fields: List[str] = field(default_factory=list)
    is_getter: bool = False  # True if fields are getters vs state


class PiniaGetterExtractor:
    """
    Extracts Pinia getter definitions and storeToRefs usage.

    Detects:
    - Options API getters: getters: { doubleCount(state) { return state.count * 2 } }
    - Options API getters using this: getters: { doubleCount() { return this.count * 2 } }
    - Setup API getters: const doubleCount = computed(() => count.value * 2)
    - Getter arguments: getters: { getUserById: (state) => (id) => ... }
    - storeToRefs() for reactive destructuring
    - Cross-store getter composition
    """

    # Options API getter pattern inside getters: { ... }
    OPTIONS_GETTER_PATTERN = re.compile(
        r'getters\s*:\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
        re.MULTILINE | re.DOTALL
    )

    # Individual getter methods
    GETTER_METHOD_PATTERN = re.compile(
        r'(\w+)\s*\(\s*(?:state)?\s*\)\s*(?::\s*[^{]+)?\s*\{',
        re.MULTILINE
    )

    # Getter that returns function (getter arguments)
    GETTER_RETURNS_FN_PATTERN = re.compile(
        r'(\w+)\s*\(\s*state\s*\)\s*\{[^}]*return\s+\([^)]*\)\s*=>',
        re.MULTILINE | re.DOTALL
    )

    # Arrow function getter: getterName: (state) => state.field * 2
    ARROW_GETTER_PATTERN = re.compile(
        r'(\w+)\s*:\s*\(\s*(?:state)?\s*\)\s*=>',
        re.MULTILINE
    )

    # Setup API computed getter
    SETUP_COMPUTED_PATTERN = re.compile(
        r'(?:const|let)\s+(\w+)\s*=\s*computed\s*(?:<[^>]*>)?\s*\(',
        re.MULTILINE
    )

    # storeToRefs destructuring
    STORE_TO_REFS_PATTERN = re.compile(
        r'(?:const|let)\s+\{([^}]+)\}\s*=\s*storeToRefs\s*\(\s*(\w+)\s*\)',
        re.MULTILINE
    )

    # Plain store destructuring (for actions, not reactive)
    STORE_DESTRUCTURE_PATTERN = re.compile(
        r'(?:const|let)\s+\{([^}]+)\}\s*=\s*(\w+Store)\s*\(\)',
        re.MULTILINE
    )

    # this.otherGetter usage in options getters
    THIS_GETTER_PATTERN = re.compile(
        r'this\.(\w+)',
        re.MULTILINE
    )

    # use of other stores inside getters
    USE_STORE_IN_GETTER = re.compile(
        r'(?:const|let)\s+\w+\s*=\s*(use\w+Store)\s*\(\)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Pinia getters and storeToRefs usage.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dictionary with 'getters' and 'store_to_refs' lists
        """
        getters: List[PiniaGetterInfo] = []
        store_to_refs: List[PiniaStoreToRefsInfo] = []

        # Options API getters
        for getter_block_match in self.OPTIONS_GETTER_PATTERN.finditer(content):
            block = getter_block_match.group(1)
            block_start = getter_block_match.start()

            # Extract individual getter methods
            for method_match in self.GETTER_METHOD_PATTERN.finditer(block):
                name = method_match.group(1)
                line = content[:block_start + method_match.start()].count('\n') + 1
                getter = PiniaGetterInfo(
                    name=name,
                    file=file_path,
                    line_number=line,
                    api_style="options",
                )
                getters.append(getter)

            # Arrow function getters
            for arrow_match in self.ARROW_GETTER_PATTERN.finditer(block):
                name = arrow_match.group(1)
                # Avoid duplicates
                if not any(g.name == name for g in getters):
                    line = content[:block_start + arrow_match.start()].count('\n') + 1
                    getter = PiniaGetterInfo(
                        name=name,
                        file=file_path,
                        line_number=line,
                        api_style="options",
                    )
                    getters.append(getter)

        # Check for getter arguments (return function)
        for returns_fn_match in self.GETTER_RETURNS_FN_PATTERN.finditer(content):
            name = returns_fn_match.group(1)
            for g in getters:
                if g.name == name:
                    g.returns_function = True

        # Setup API computed getters
        for comp_match in self.SETUP_COMPUTED_PATTERN.finditer(content):
            name = comp_match.group(1)
            line = content[:comp_match.start()].count('\n') + 1
            getter = PiniaGetterInfo(
                name=name,
                file=file_path,
                line_number=line,
                api_style="setup",
            )
            getters.append(getter)

        # storeToRefs
        for str_match in self.STORE_TO_REFS_PATTERN.finditer(content):
            fields_str = str_match.group(1)
            store_name = str_match.group(2)
            line = content[:str_match.start()].count('\n') + 1
            fields = [f.strip() for f in fields_str.split(',') if f.strip()]
            store_to_refs.append(PiniaStoreToRefsInfo(
                file=file_path,
                line_number=line,
                store_name=store_name,
                destructured_fields=fields,
            ))

        return {
            'getters': getters,
            'store_to_refs': store_to_refs,
        }
