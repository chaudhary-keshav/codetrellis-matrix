"""
Radix UI Primitive Extractor for CodeTrellis

Extracts low-level Radix UI primitive usage patterns — Slot/Compose,
asChild forwarding, Presence animations, FocusScope, VisuallyHidden,
Portal, DismissableLayer, Popper, Arrow, Collection utilities.

These primitives are the building blocks used by both Radix Primitives
and Radix Themes. They enable composition, accessibility, and
animation patterns.

Primitives:
- Slot: Polymorphic component rendering via asChild
- Presence: Animation lifecycle management (enter/exit)
- FocusScope: Focus trapping and management
- VisuallyHidden: Accessible hidden content
- Portal: Render content in a separate DOM node
- DismissableLayer: Click outside / Escape handling
- Direction: RTL/LTR support
- Collection: Item collection management
- Compose: Ref composition utility
- Id: Accessible ID generation

Part of CodeTrellis v4.41 - Radix UI Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RadixPrimitiveInfo:
    """Information about a Radix UI low-level primitive usage."""
    name: str
    file: str = ""
    line_number: int = 0
    primitive_type: str = ""     # slot, presence, focus-scope, portal, etc.
    import_source: str = ""      # @radix-ui/react-slot, @radix-ui/react-presence, etc.
    usage_context: str = ""      # animation, accessibility, composition, layout
    is_internal: bool = False    # Used internally by other Radix components
    configuration: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RadixSlotInfo:
    """Information about Radix Slot / asChild usage."""
    name: str
    file: str = ""
    line_number: int = 0
    parent_component: str = ""   # Component wrapping the Slot
    merged_props: List[str] = field(default_factory=list)  # Props being merged
    has_slottable: bool = False  # Uses Slottable for mixed content
    forwarded_ref: bool = False  # Uses forwardRef


class RadixPrimitiveExtractor:
    """
    Extracts low-level Radix UI primitive usage patterns.

    Detects:
    - Slot and asChild composition pattern
    - Presence for enter/exit animations
    - FocusScope for focus trapping
    - VisuallyHidden for accessible hidden content
    - Portal for DOM rendering outside component tree
    - DismissableLayer for click outside / Escape handling
    - Direction for RTL/LTR support
    - Collection for item management
    """

    # Primitive import patterns
    PRIMITIVE_PATTERNS = {
        'slot': {
            'import': re.compile(
                r"""from\s+['"]@radix-ui/react-slot['"]""",
                re.MULTILINE,
            ),
            'usage': re.compile(
                r'(?:<Slot\b|asChild)',
                re.MULTILINE,
            ),
            'context': 'composition',
        },
        'presence': {
            'import': re.compile(
                r"""from\s+['"]@radix-ui/react-presence['"]""",
                re.MULTILINE,
            ),
            'usage': re.compile(
                r'<Presence\b',
                re.MULTILINE,
            ),
            'context': 'animation',
        },
        'focus-scope': {
            'import': re.compile(
                r"""from\s+['"]@radix-ui/react-focus-scope['"]""",
                re.MULTILINE,
            ),
            'usage': re.compile(
                r'<FocusScope\b',
                re.MULTILINE,
            ),
            'context': 'accessibility',
        },
        'visually-hidden': {
            'import': re.compile(
                r"""from\s+['"]@radix-ui/react-visually-hidden['"]""",
                re.MULTILINE,
            ),
            'usage': re.compile(
                r'<VisuallyHidden\b',
                re.MULTILINE,
            ),
            'context': 'accessibility',
        },
        'portal': {
            'import': re.compile(
                r"""from\s+['"]@radix-ui/react-portal['"]""",
                re.MULTILINE,
            ),
            'usage': re.compile(
                r'<Portal\b|\.Portal\b',
                re.MULTILINE,
            ),
            'context': 'layout',
        },
        'dismissable-layer': {
            'import': re.compile(
                r"""from\s+['"]@radix-ui/react-dismissable-layer['"]""",
                re.MULTILINE,
            ),
            'usage': re.compile(
                r'<DismissableLayer\b|onDismiss|onEscapeKeyDown|onPointerDownOutside',
                re.MULTILINE,
            ),
            'context': 'interaction',
        },
        'direction': {
            'import': re.compile(
                r"""from\s+['"]@radix-ui/react-direction['"]""",
                re.MULTILINE,
            ),
            'usage': re.compile(
                r'<DirectionProvider\b|useDirection',
                re.MULTILINE,
            ),
            'context': 'accessibility',
        },
        'collection': {
            'import': re.compile(
                r"""from\s+['"]@radix-ui/react-collection['"]""",
                re.MULTILINE,
            ),
            'usage': re.compile(
                r'createCollection|useCollection',
                re.MULTILINE,
            ),
            'context': 'composition',
        },
        'compose-refs': {
            'import': re.compile(
                r"""from\s+['"]@radix-ui/react-compose-refs['"]""",
                re.MULTILINE,
            ),
            'usage': re.compile(
                r'composeRefs|useComposedRefs',
                re.MULTILINE,
            ),
            'context': 'composition',
        },
        'id': {
            'import': re.compile(
                r"""from\s+['"]@radix-ui/react-id['"]""",
                re.MULTILINE,
            ),
            'usage': re.compile(
                r'useId',
                re.MULTILINE,
            ),
            'context': 'accessibility',
        },
        'use-callback-ref': {
            'import': re.compile(
                r"""from\s+['"]@radix-ui/react-use-callback-ref['"]""",
                re.MULTILINE,
            ),
            'usage': re.compile(
                r'useCallbackRef',
                re.MULTILINE,
            ),
            'context': 'composition',
        },
        'use-controllable-state': {
            'import': re.compile(
                r"""from\s+['"]@radix-ui/react-use-controllable-state['"]""",
                re.MULTILINE,
            ),
            'usage': re.compile(
                r'useControllableState',
                re.MULTILINE,
            ),
            'context': 'composition',
        },
        'use-escape-keydown': {
            'import': re.compile(
                r"""from\s+['"]@radix-ui/react-use-escape-keydown['"]""",
                re.MULTILINE,
            ),
            'usage': re.compile(
                r'useEscapeKeydown',
                re.MULTILINE,
            ),
            'context': 'interaction',
        },
        'use-layout-effect': {
            'import': re.compile(
                r"""from\s+['"]@radix-ui/react-use-layout-effect['"]""",
                re.MULTILINE,
            ),
            'usage': re.compile(
                r'useLayoutEffect',
                re.MULTILINE,
            ),
            'context': 'composition',
        },
        'use-previous': {
            'import': re.compile(
                r"""from\s+['"]@radix-ui/react-use-previous['"]""",
                re.MULTILINE,
            ),
            'usage': re.compile(
                r'usePrevious',
                re.MULTILINE,
            ),
            'context': 'composition',
        },
        'use-size': {
            'import': re.compile(
                r"""from\s+['"]@radix-ui/react-use-size['"]""",
                re.MULTILINE,
            ),
            'usage': re.compile(
                r'useSize',
                re.MULTILINE,
            ),
            'context': 'layout',
        },
        'use-rect': {
            'import': re.compile(
                r"""from\s+['"]@radix-ui/react-use-rect['"]""",
                re.MULTILINE,
            ),
            'usage': re.compile(
                r'useRect',
                re.MULTILINE,
            ),
            'context': 'layout',
        },
        'roving-focus': {
            'import': re.compile(
                r"""from\s+['"]@radix-ui/react-roving-focus['"]""",
                re.MULTILINE,
            ),
            'usage': re.compile(
                r'RovingFocusGroup|useRovingFocus',
                re.MULTILINE,
            ),
            'context': 'accessibility',
        },
        'focus-guards': {
            'import': re.compile(
                r"""from\s+['"]@radix-ui/react-focus-guards['"]""",
                re.MULTILINE,
            ),
            'usage': re.compile(
                r'FocusGuards|useFocusGuards',
                re.MULTILINE,
            ),
            'context': 'accessibility',
        },
        'popper': {
            'import': re.compile(
                r"""from\s+['"]@radix-ui/react-popper['"]""",
                re.MULTILINE,
            ),
            'usage': re.compile(
                r'<Popper\b|PopperContent|PopperAnchor|PopperArrow',
                re.MULTILINE,
            ),
            'context': 'layout',
        },
        'arrow': {
            'import': re.compile(
                r"""from\s+['"]@radix-ui/react-arrow['"]""",
                re.MULTILINE,
            ),
            'usage': re.compile(
                r'<Arrow\b|\.Arrow\b',
                re.MULTILINE,
            ),
            'context': 'layout',
        },
        'primitive': {
            'import': re.compile(
                r"""from\s+['"]@radix-ui/react-primitive['"]""",
                re.MULTILINE,
            ),
            'usage': re.compile(
                r'<Primitive\b|Primitive\.',
                re.MULTILINE,
            ),
            'context': 'composition',
        },
    }

    # Slot-specific patterns
    SLOT_IMPORT_PATTERN = re.compile(
        r"""import\s*\{([^}]*(?:Slot|Slottable)[^}]*)\}\s*from\s*['"]@radix-ui/react-slot['"]""",
        re.MULTILINE,
    )

    FORWARD_REF_SLOT_PATTERN = re.compile(
        r'(?:React\.)?forwardRef.*?<Slot\b',
        re.DOTALL,
    )

    AS_CHILD_PROP_PATTERN = re.compile(
        r'asChild\s*(?:\??\s*:\s*boolean)?',
        re.MULTILINE,
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Radix UI primitive usage patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dictionary with 'primitives' and 'slots' lists
        """
        result = {
            'primitives': [],
            'slots': [],
        }

        if not content or not content.strip():
            return result

        # Extract primitive usages
        for prim_name, patterns in self.PRIMITIVE_PATTERNS.items():
            import_match = patterns['import'].search(content)
            usage_match = patterns['usage'].search(content)

            if import_match or usage_match:
                match = import_match or usage_match
                line_number = content[:match.start()].count('\n') + 1

                prim = RadixPrimitiveInfo(
                    name=prim_name,
                    file=file_path,
                    line_number=line_number,
                    primitive_type=prim_name,
                    import_source=f"@radix-ui/react-{prim_name}",
                    usage_context=patterns['context'],
                    is_internal=prim_name in (
                        'compose-refs', 'use-callback-ref', 'use-layout-effect',
                        'use-previous', 'use-size', 'use-rect', 'collection',
                        'focus-guards', 'popper', 'arrow', 'primitive',
                    ),
                )
                result['primitives'].append(prim)

        # Extract Slot usage details
        slots = self._extract_slots(content, file_path)
        result['slots'].extend(slots)

        return result

    def _extract_slots(self, content: str, file_path: str) -> List[RadixSlotInfo]:
        """Extract detailed Slot/asChild usage patterns."""
        slots = []

        for match in self.SLOT_IMPORT_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            imports_str = match.group(1)
            has_slottable = 'Slottable' in imports_str
            forwarded_ref = bool(self.FORWARD_REF_SLOT_PATTERN.search(content))

            slot = RadixSlotInfo(
                name='Slot',
                file=file_path,
                line_number=line_number,
                has_slottable=has_slottable,
                forwarded_ref=forwarded_ref,
            )
            slots.append(slot)

        return slots
