"""
Framer Motion API and integration extractor for CodeTrellis.

Extracts API-level constructs:
- Import analysis (framer-motion, motion package, specific named imports)
- Hook usage (useMotionValue, useTransform, useSpring, useVelocity, useAnimate, etc.)
- TypeScript types (MotionProps, Variants, Transition, AnimationControls, etc.)
- Integration detection (React Spring bridge, Popmotion, mix/interpolate utilities)
- Version detection (framer-motion vs motion package name, API surface evolution)
- Motion component factory (motion.div, motion.create, motion())

Supports framer-motion v1-v10 and motion v11+.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set


@dataclass
class FramerImportInfo:
    """Import from framer-motion / motion package."""
    package_name: str = ""        # 'framer-motion' or 'motion'
    imported_names: List[str] = field(default_factory=list)
    is_namespace: bool = False     # import * as motion
    is_default: bool = False       # import motion from ...
    line_number: int = 0
    file_path: str = ""
    is_dynamic: bool = False       # dynamic import()


@dataclass
class FramerHookInfo:
    """Hook usage from framer-motion."""
    hook_name: str = ""
    variable_name: str = ""
    line_number: int = 0
    file_path: str = ""
    arguments: str = ""


@dataclass
class FramerTypeInfo:
    """TypeScript type from framer-motion."""
    type_name: str = ""
    usage_context: str = ""        # 'annotation', 'generic', 'interface_extends'
    line_number: int = 0
    file_path: str = ""


@dataclass
class FramerIntegrationInfo:
    """Integration with other libraries."""
    library_name: str = ""         # 'react-spring', 'popmotion', etc.
    integration_type: str = ""     # 'bridge', 'utility', 'compatible'
    line_number: int = 0
    file_path: str = ""


# ── Regex patterns ──────────────────────────────────────────────

# Named imports from framer-motion / motion
NAMED_IMPORT_PATTERN = re.compile(
    r"""import\s+\{([^}]+)\}\s+from\s+['"](?:framer-motion|motion)(?:/[^'"]*)?['"]""",
    re.MULTILINE
)

# Default / namespace imports
DEFAULT_IMPORT_PATTERN = re.compile(
    r"""import\s+(\w+)\s+from\s+['"](?:framer-motion|motion)['"]""",
    re.MULTILINE
)

NAMESPACE_IMPORT_PATTERN = re.compile(
    r"""import\s+\*\s+as\s+(\w+)\s+from\s+['"](?:framer-motion|motion)['"]""",
    re.MULTILINE
)

# Dynamic imports
DYNAMIC_IMPORT_PATTERN = re.compile(
    r"""(?:await\s+)?import\s*\(\s*['"](?:framer-motion|motion)(?:/[^'"]*)?['"]\s*\)""",
    re.MULTILINE
)

# Package name detection (framer-motion vs motion)
PACKAGE_NAME_PATTERN = re.compile(
    r"""['"](?P<pkg>framer-motion|motion)(?:/[^'"]*)?['"]""",
    re.MULTILINE
)

# Known hooks from framer-motion
FRAMER_HOOKS = {
    'useMotionValue', 'useTransform', 'useSpring', 'useVelocity',
    'useAnimate', 'useAnimation', 'useAnimationControls',
    'useScroll', 'useInView', 'useMotionValueEvent',
    'useMotionTemplate', 'useCycle', 'useReducedMotion',
    'useIsPresent', 'usePresence', 'useDragControls',
    'useTime', 'useWillChange', 'useAnimationFrame',
    'useInstantTransition', 'useInstantLayoutTransition',
}

HOOK_USAGE_PATTERN = re.compile(
    r"""(?:const|let|var)\s+(?:(\w+)|\{([^}]+)\}|\[([^\]]+)\])\s*=\s*(use(?:MotionValue|Transform|Spring|Velocity|Animate|Animation|AnimationControls|Scroll|InView|MotionValueEvent|MotionTemplate|Cycle|ReducedMotion|IsPresent|Presence|DragControls|Time|WillChange|AnimationFrame|InstantTransition|InstantLayoutTransition))\s*\(([^)]*)\)""",
    re.MULTILINE
)

# Known TypeScript types from framer-motion
FRAMER_TYPES = {
    'MotionProps', 'MotionValue', 'Variants', 'Transition',
    'AnimationControls', 'TargetAndTransition', 'AnimatePresenceProps',
    'MotionStyle', 'MotionConfig', 'DragControls', 'PanInfo',
    'TapInfo', 'HoverHandlers', 'FocusHandlers', 'LayoutProps',
    'AnimationDefinition', 'ResolvedValues', 'Spring', 'Inertia',
    'Keyframes', 'Orchestration', 'Tween', 'SVGMotionProps',
    'HTMLMotionProps', 'ForwardRefComponent', 'CustomDomComponent',
}

TYPE_ANNOTATION_PATTERN = re.compile(
    r""":\s*(""" + '|'.join(FRAMER_TYPES) + r""")(?:\s*[<>\[\],;=\)])""",
    re.MULTILINE
)

TYPE_GENERIC_PATTERN = re.compile(
    r"""<\s*(""" + '|'.join(FRAMER_TYPES) + r""")[\s,>]""",
    re.MULTILINE
)

# motion.div, motion.span, etc.
MOTION_ELEMENT_PATTERN = re.compile(
    r"""<motion\.(\w+)""",
    re.MULTILINE
)

# motion() custom component
MOTION_FACTORY_PATTERN = re.compile(
    r"""motion\(\s*(\w+)""",
    re.MULTILINE
)

# Integration patterns
REACT_SPRING_BRIDGE_PATTERN = re.compile(
    r"""from\s+['"]@react-spring/framer-motion['"]""",
    re.MULTILINE
)

POPMOTION_IMPORT_PATTERN = re.compile(
    r"""from\s+['"]popmotion['"]""",
    re.MULTILINE
)

MIX_INTERPOLATE_PATTERN = re.compile(
    r"""(?:from\s+['"]framer-motion['"].*?)?\b(?:mix|interpolate)\s*\(""",
    re.MULTILINE
)


class FramerAPIExtractor:
    """Extract Framer Motion API-level constructs."""

    def extract(self, content: str, file_path: str = "") -> Dict:
        """
        Extract all API-level constructs.

        Returns dict with keys: imports, hooks, types, integrations,
        motion_elements, version_info.
        """
        result = {
            'imports': [],
            'hooks': [],
            'types': [],
            'integrations': [],
            'motion_elements': [],
            'version_info': {},
        }

        if not content.strip():
            return result

        result['imports'] = self._extract_imports(content, file_path)
        result['hooks'] = self._extract_hooks(content, file_path)
        result['types'] = self._extract_types(content, file_path)
        result['integrations'] = self._extract_integrations(content, file_path)
        result['motion_elements'] = self._extract_motion_elements(content, file_path)
        result['version_info'] = self._detect_version_info(content)

        return result

    def _extract_imports(self, content: str, file_path: str) -> List[FramerImportInfo]:
        """Extract all framer-motion / motion imports."""
        imports = []

        # Named imports
        for m in NAMED_IMPORT_PATTERN.finditer(content):
            raw_names = m.group(1)
            line_num = content[:m.start()].count('\n') + 1

            # Parse names, handling 'as' aliases
            names = []
            for part in raw_names.split(','):
                part = part.strip()
                if not part:
                    continue
                if ' as ' in part:
                    original = part.split(' as ')[0].strip()
                    names.append(original)
                else:
                    names.append(part)

            # Detect package name
            pkg = self._detect_package(content[m.start():m.end()])

            imports.append(FramerImportInfo(
                package_name=pkg,
                imported_names=names,
                line_number=line_num,
                file_path=file_path,
            ))

        # Default imports
        for m in DEFAULT_IMPORT_PATTERN.finditer(content):
            name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1
            pkg = self._detect_package(content[m.start():m.end()])

            imports.append(FramerImportInfo(
                package_name=pkg,
                imported_names=[name],
                is_default=True,
                line_number=line_num,
                file_path=file_path,
            ))

        # Namespace imports
        for m in NAMESPACE_IMPORT_PATTERN.finditer(content):
            name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1
            pkg = self._detect_package(content[m.start():m.end()])

            imports.append(FramerImportInfo(
                package_name=pkg,
                imported_names=[name],
                is_namespace=True,
                line_number=line_num,
                file_path=file_path,
            ))

        # Dynamic imports
        for m in DYNAMIC_IMPORT_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            pkg = self._detect_package(content[m.start():m.end()])

            imports.append(FramerImportInfo(
                package_name=pkg,
                is_dynamic=True,
                line_number=line_num,
                file_path=file_path,
            ))

        return imports[:30]

    def _extract_hooks(self, content: str, file_path: str) -> List[FramerHookInfo]:
        """Extract framer-motion hook usage."""
        hooks = []
        for m in HOOK_USAGE_PATTERN.finditer(content):
            var_single = m.group(1) or ""
            var_destructured = m.group(2) or ""
            var_array = m.group(3) or ""
            hook_name = m.group(4)
            arguments = m.group(5) or ""
            line_num = content[:m.start()].count('\n') + 1

            variable = var_single if var_single else (var_destructured.strip() if var_destructured else var_array.strip())

            hooks.append(FramerHookInfo(
                hook_name=hook_name,
                variable_name=variable,
                line_number=line_num,
                file_path=file_path,
                arguments=arguments.strip(),
            ))

        return hooks[:30]

    def _extract_types(self, content: str, file_path: str) -> List[FramerTypeInfo]:
        """Extract TypeScript type usage from framer-motion."""
        types = []
        seen = set()

        for m in TYPE_ANNOTATION_PATTERN.finditer(content):
            type_name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1
            key = (type_name, line_num)
            if key not in seen:
                seen.add(key)
                types.append(FramerTypeInfo(
                    type_name=type_name,
                    usage_context='annotation',
                    line_number=line_num,
                    file_path=file_path,
                ))

        for m in TYPE_GENERIC_PATTERN.finditer(content):
            type_name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1
            key = (type_name, line_num)
            if key not in seen:
                seen.add(key)
                types.append(FramerTypeInfo(
                    type_name=type_name,
                    usage_context='generic',
                    line_number=line_num,
                    file_path=file_path,
                ))

        return types[:30]

    def _extract_integrations(self, content: str, file_path: str) -> List[FramerIntegrationInfo]:
        """Detect integrations with other animation/UI libraries."""
        integrations = []

        for m in REACT_SPRING_BRIDGE_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            integrations.append(FramerIntegrationInfo(
                library_name='react-spring',
                integration_type='bridge',
                line_number=line_num,
                file_path=file_path,
            ))

        for m in POPMOTION_IMPORT_PATTERN.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            integrations.append(FramerIntegrationInfo(
                library_name='popmotion',
                integration_type='utility',
                line_number=line_num,
                file_path=file_path,
            ))

        return integrations[:10]

    def _extract_motion_elements(self, content: str, file_path: str) -> List[Dict]:
        """Extract motion.* element usage and motion() factory calls."""
        elements = []
        seen_elements: Dict[str, int] = {}

        # motion.div, motion.span, etc.
        for m in MOTION_ELEMENT_PATTERN.finditer(content):
            tag = m.group(1)
            if tag in seen_elements:
                seen_elements[tag] += 1
            else:
                seen_elements[tag] = 1

        for tag, count in seen_elements.items():
            elements.append({
                'element': f'motion.{tag}',
                'count': count,
                'file': file_path,
            })

        # motion() factory
        for m in MOTION_FACTORY_PATTERN.finditer(content):
            component = m.group(1)
            line_num = content[:m.start()].count('\n') + 1
            elements.append({
                'element': f'motion({component})',
                'count': 1,
                'line': line_num,
                'file': file_path,
            })

        return elements[:30]

    def _detect_version_info(self, content: str) -> Dict:
        """Detect framer-motion version indicators from API usage."""
        info = {
            'package': 'unknown',
            'api_hints': [],
        }

        # Package name detection
        if re.search(r"""['"]motion(?:/[^'"]*)?['"]""", content):
            # Check for exact "motion" (not "framer-motion")
            if re.search(r"""['"]motion['"]""", content) and not re.search(r"""['"]framer-motion['"]""", content):
                info['package'] = 'motion'
                info['api_hints'].append('v11+_motion_package')
            elif re.search(r"""['"]framer-motion['"]""", content):
                info['package'] = 'framer-motion'
        elif re.search(r"""['"]framer-motion['"]""", content):
            info['package'] = 'framer-motion'

        # API surface hints
        if 'useAnimate' in content:
            info['api_hints'].append('v10+_useAnimate')
        if 'useScroll' in content:
            info['api_hints'].append('v6+_useScroll')
        if 'useInView' in content:
            info['api_hints'].append('v7+_useInView')
        if 'useWillChange' in content:
            info['api_hints'].append('v10+_useWillChange')
        if 'AnimatePresence' in content:
            info['api_hints'].append('v2+_AnimatePresence')
        if 'LazyMotion' in content:
            info['api_hints'].append('v4+_LazyMotion')
        if 'useMotionValueEvent' in content:
            info['api_hints'].append('v10+_useMotionValueEvent')
        if 'layout' in content and re.search(r"""\blayout\s*[=\s]""", content):
            info['api_hints'].append('v5+_layout_animations')
        if 'useAnimationFrame' in content:
            info['api_hints'].append('v11+_useAnimationFrame')

        return info

    # ── Helpers ──────────────────────────────────────────────────

    def _detect_package(self, snippet: str) -> str:
        """Detect whether import is from 'framer-motion' or 'motion'."""
        # Check for 'framer-motion' first (more specific)
        if 'framer-motion' in snippet:
            return 'framer-motion'
        if re.search(r"""['"]motion(?:/|['"])""", snippet):
            return 'motion'
        return 'framer-motion'
