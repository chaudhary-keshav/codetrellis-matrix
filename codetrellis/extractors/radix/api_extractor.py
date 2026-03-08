"""
Radix UI API / Composition Extractor for CodeTrellis

Extracts Radix UI composition patterns — controlled/uncontrolled state,
onOpenChange/onValueChange callbacks, asChild prop forwarding,
portal usage, animation integration (framer-motion, react-spring),
keyboard navigation, focus management.

Composition Patterns:
- Controlled state: <Dialog open={open} onOpenChange={setOpen}>
- Uncontrolled state: <Dialog defaultOpen={true}>
- asChild forwarding: <Button asChild><Link href="/...">
- Portal rendering: <Dialog.Portal container={containerRef}>
- Animation integration: framer-motion AnimatePresence + Radix Presence
- Keyboard navigation: Arrow keys, Home/End, Enter/Space
- Focus management: FocusScope, auto-focus, return-focus

Part of CodeTrellis v4.41 - Radix UI Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RadixCompositionPatternInfo:
    """Information about a Radix UI composition pattern."""
    name: str
    file: str = ""
    line_number: int = 0
    pattern_type: str = ""        # controlled, uncontrolled, forwarded, compound
    component: str = ""           # Which Radix component is being composed
    sub_components_used: List[str] = field(default_factory=list)
    props_forwarded: List[str] = field(default_factory=list)
    has_as_child: bool = False
    has_forward_ref: bool = False
    wrapping_element: str = ""    # What element wraps the Radix component


@dataclass
class RadixControlledPatternInfo:
    """Information about controlled/uncontrolled component usage."""
    component: str
    file: str = ""
    line_number: int = 0
    is_controlled: bool = False
    state_prop: str = ""          # open, value, checked, pressed
    change_handler: str = ""      # onOpenChange, onValueChange, etc.
    default_prop: str = ""        # defaultOpen, defaultValue, etc.
    state_source: str = ""        # useState, useReducer, zustand, etc.


@dataclass
class RadixPortalPatternInfo:
    """Information about portal usage in Radix UI."""
    component: str
    file: str = ""
    line_number: int = 0
    has_container_ref: bool = False  # Uses container prop
    has_force_mount: bool = False    # Uses forceMount for animations
    animation_library: str = ""      # framer-motion, react-spring, etc.


class RadixApiExtractor:
    """
    Extracts Radix UI composition and API patterns.

    Detects:
    - Controlled vs uncontrolled component state
    - asChild prop forwarding patterns
    - Portal usage with container refs
    - Animation integration (framer-motion, react-spring, CSS)
    - Compound component patterns
    - Forward ref wrapping
    - Focus management patterns
    """

    # Controlled state patterns
    CONTROLLED_PATTERN = re.compile(
        r'<(\w+)(?:\.Root)?\s[^>]*\b(open|value|checked|pressed)\s*=\s*\{',
        re.MULTILINE,
    )

    # Uncontrolled (default*) state patterns
    UNCONTROLLED_PATTERN = re.compile(
        r'<(\w+)(?:\.Root)?\s[^>]*\b(defaultOpen|defaultValue|defaultChecked|defaultPressed)\s*=',
        re.MULTILINE,
    )

    # State change handler patterns
    CHANGE_HANDLER_PATTERN = re.compile(
        r'<(\w+)(?:\.Root)?\s[^>]*\b(onOpenChange|onValueChange|onCheckedChange|onPressedChange)\s*=\s*\{',
        re.MULTILINE,
    )

    # asChild usage pattern
    AS_CHILD_PATTERN = re.compile(
        r'<(\w+(?:\.\w+)?)\s[^>]*\basChild\b',
        re.MULTILINE,
    )

    # forwardRef wrapping pattern
    FORWARD_REF_PATTERN = re.compile(
        r'(?:React\.)?forwardRef\s*(?:<[^>]+>)?\s*\(\s*\(',
        re.MULTILINE,
    )

    # Portal with container or forceMount
    PORTAL_PATTERN = re.compile(
        r'<(\w+)\.Portal\b([^>]*?)>',
        re.MULTILINE | re.DOTALL,
    )

    # forceMount prop for animation support
    FORCE_MOUNT_PATTERN = re.compile(
        r'\bforceMount\b',
        re.MULTILINE,
    )

    # Animation library imports
    ANIMATION_PATTERNS = {
        'framer-motion': re.compile(
            r"""from\s+['"]framer-motion['"]""",
            re.MULTILINE,
        ),
        'react-spring': re.compile(
            r"""from\s+['"]@react-spring/web['"]|from\s+['"]react-spring['"]""",
            re.MULTILINE,
        ),
        'motion': re.compile(
            r"""from\s+['"]motion['"]""",
            re.MULTILINE,
        ),
    }

    # Compound component creation pattern
    COMPOUND_PATTERN = re.compile(
        r'(\w+)\.(Root|Trigger|Content|Portal|Overlay|Close|Item|Header|Footer|Title|Description)\b',
        re.MULTILINE,
    )

    # State management source detection
    STATE_SOURCE_PATTERN = re.compile(
        r'(?:const|let)\s+\[(\w+),\s*set\w+\]\s*=\s*(useState|useReducer|useAtom|useStore|useSignal)',
        re.MULTILINE,
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Radix UI composition and API patterns.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dictionary with 'compositions', 'controlled_patterns', 'portal_patterns' lists
        """
        result = {
            'compositions': [],
            'controlled_patterns': [],
            'portal_patterns': [],
        }

        if not content or not content.strip():
            return result

        # Extract controlled/uncontrolled patterns
        controlled = self._extract_controlled_patterns(content, file_path)
        result['controlled_patterns'].extend(controlled)

        # Extract portal patterns
        portals = self._extract_portal_patterns(content, file_path)
        result['portal_patterns'].extend(portals)

        # Extract composition patterns
        compositions = self._extract_composition_patterns(content, file_path)
        result['compositions'].extend(compositions)

        return result

    def _extract_controlled_patterns(
        self, content: str, file_path: str
    ) -> List[RadixControlledPatternInfo]:
        """Extract controlled/uncontrolled state patterns."""
        patterns = []
        seen = set()

        # Controlled patterns
        for match in self.CONTROLLED_PATTERN.finditer(content):
            component = match.group(1)
            state_prop = match.group(2)
            line_number = content[:match.start()].count('\n') + 1
            key = (component, state_prop, file_path)
            if key in seen:
                continue
            seen.add(key)

            # Find corresponding change handler
            change_handler = ''
            handler_map = {
                'open': 'onOpenChange',
                'value': 'onValueChange',
                'checked': 'onCheckedChange',
                'pressed': 'onPressedChange',
            }
            expected_handler = handler_map.get(state_prop, '')
            if expected_handler and expected_handler in content:
                change_handler = expected_handler

            # Detect state management source
            state_source = ''
            for src_match in self.STATE_SOURCE_PATTERN.finditer(content):
                state_source = src_match.group(2)
                break

            patterns.append(RadixControlledPatternInfo(
                component=component,
                file=file_path,
                line_number=line_number,
                is_controlled=True,
                state_prop=state_prop,
                change_handler=change_handler,
                state_source=state_source,
            ))

        # Uncontrolled patterns
        for match in self.UNCONTROLLED_PATTERN.finditer(content):
            component = match.group(1)
            default_prop = match.group(2)
            line_number = content[:match.start()].count('\n') + 1
            key = (component, 'default', file_path)
            if key in seen:
                continue
            seen.add(key)

            patterns.append(RadixControlledPatternInfo(
                component=component,
                file=file_path,
                line_number=line_number,
                is_controlled=False,
                default_prop=default_prop,
            ))

        return patterns

    def _extract_portal_patterns(
        self, content: str, file_path: str
    ) -> List[RadixPortalPatternInfo]:
        """Extract Portal usage patterns."""
        patterns = []

        for match in self.PORTAL_PATTERN.finditer(content):
            component = match.group(1)
            props_str = match.group(2) or ""
            line_number = content[:match.start()].count('\n') + 1

            has_container = 'container' in props_str
            has_force_mount = 'forceMount' in props_str

            # Detect animation library
            anim_library = ''
            for lib, pattern in self.ANIMATION_PATTERNS.items():
                if pattern.search(content):
                    anim_library = lib
                    break

            patterns.append(RadixPortalPatternInfo(
                component=component,
                file=file_path,
                line_number=line_number,
                has_container_ref=has_container,
                has_force_mount=has_force_mount,
                animation_library=anim_library,
            ))

        return patterns

    def _extract_composition_patterns(
        self, content: str, file_path: str
    ) -> List[RadixCompositionPatternInfo]:
        """Extract compound component composition patterns."""
        patterns = []
        seen_components = set()

        # Find all compound component usages
        for match in self.COMPOUND_PATTERN.finditer(content):
            base_component = match.group(1)
            sub_component = match.group(2)

            if base_component in seen_components:
                # Add sub-component to existing pattern
                for p in patterns:
                    if p.component == base_component:
                        if sub_component not in p.sub_components_used:
                            p.sub_components_used.append(sub_component)
                continue

            seen_components.add(base_component)
            line_number = content[:match.start()].count('\n') + 1

            # Detect pattern type
            has_as_child = bool(re.search(
                rf'<{re.escape(base_component)}(?:\.\w+)?\s[^>]*\basChild\b',
                content,
            ))
            has_forward_ref = bool(self.FORWARD_REF_PATTERN.search(content))

            # Determine pattern type
            is_controlled = bool(re.search(
                rf'<{re.escape(base_component)}(?:\.Root)?\s[^>]*\b(?:open|value|checked|pressed)\s*=\s*\{{',
                content,
            ))
            pattern_type = 'controlled' if is_controlled else 'compound'

            # Find all sub-components used
            sub_comps = []
            for sub_match in re.finditer(
                rf'{re.escape(base_component)}\.(\w+)', content
            ):
                sub = sub_match.group(1)
                if sub not in sub_comps:
                    sub_comps.append(sub)

            patterns.append(RadixCompositionPatternInfo(
                name=f"{base_component}_composition",
                file=file_path,
                line_number=line_number,
                pattern_type=pattern_type,
                component=base_component,
                sub_components_used=sub_comps[:15],
                has_as_child=has_as_child,
                has_forward_ref=has_forward_ref,
            ))

        return patterns
