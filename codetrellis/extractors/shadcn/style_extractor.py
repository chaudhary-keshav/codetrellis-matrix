"""
shadcn/ui Style Extractor for CodeTrellis

Extracts styling patterns specific to shadcn/ui:
- cn() utility usage (clsx + tailwind-merge composition)
- CVA (class-variance-authority) variant definitions
- Tailwind CSS utility patterns in component context
- CSS variable references in component styles
- Responsive patterns in shadcn/ui components
- Dark mode class-based patterns

cn() is the central utility in shadcn/ui for merging Tailwind classes
safely. It combines clsx() for conditional classes with twMerge() for
deduplication. Defined in lib/utils.ts as:
  import { type ClassValue, clsx } from "clsx";
  import { twMerge } from "tailwind-merge";
  export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
  }

CVA (class-variance-authority) is used extensively in shadcn/ui to
create type-safe component variants. Pattern:
  const buttonVariants = cva("inline-flex items-center...", {
    variants: { variant: { default: "...", destructive: "..." } },
    defaultVariants: { variant: "default", size: "default" },
  });

Part of CodeTrellis v4.39 - shadcn/ui Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ShadcnCnUsageInfo:
    """Information about cn() utility usage."""
    file: str = ""
    line_number: int = 0
    component: str = ""          # Component where cn() is used
    class_count: int = 0         # Number of class arguments
    has_conditional: bool = False  # Uses conditional logic
    has_dark_mode: bool = False  # Contains dark: prefix
    has_responsive: bool = False  # Contains responsive prefixes (sm:, md:, etc.)


@dataclass
class ShadcnCvaInfo:
    """Information about a CVA (class-variance-authority) definition."""
    name: str                    # e.g., buttonVariants
    file: str = ""
    line_number: int = 0
    base_classes: str = ""       # Base CSS classes
    variant_names: List[str] = field(default_factory=list)
    variant_values: Dict[str, List[str]] = field(default_factory=dict)
    default_variant: str = ""
    default_size: str = ""
    has_compound_variants: bool = False


@dataclass
class ShadcnTailwindPatternInfo:
    """Information about Tailwind CSS patterns in shadcn/ui context."""
    file: str = ""
    line_number: int = 0
    pattern_type: str = ""       # responsive, dark-mode, state, animation, group
    classes: List[str] = field(default_factory=list)
    component: str = ""


class ShadcnStyleExtractor:
    """
    Extracts shadcn/ui styling patterns from React/TypeScript code.

    Detects:
    - cn() utility usage and patterns
    - CVA variant definitions
    - Tailwind utility class patterns in shadcn context
    - CSS variable references
    - Responsive patterns
    - Dark mode patterns
    """

    # cn() usage detection
    CN_USAGE_RE = re.compile(
        r"""cn\s*\(([^)]*(?:\([^)]*\)[^)]*)*)\)""",
        re.DOTALL,
    )

    # cn() import detection
    CN_IMPORT_RE = re.compile(
        r"""import\s+\{[^}]*\bcn\b[^}]*\}\s+from\s+['"]([^'"]+)['"]""",
        re.MULTILINE,
    )

    # CVA definition detection
    CVA_DEF_RE = re.compile(
        r"""(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*cva\s*\(\s*""",
        re.MULTILINE,
    )

    # CVA import detection
    CVA_IMPORT_RE = re.compile(
        r"""from\s+['"]class-variance-authority['"]""",
        re.MULTILINE,
    )

    # Tailwind responsive prefixes
    RESPONSIVE_PREFIXES = ['sm:', 'md:', 'lg:', 'xl:', '2xl:']

    # Tailwind dark mode
    DARK_MODE_PREFIX = 'dark:'

    # Tailwind state variants
    STATE_PREFIXES = [
        'hover:', 'focus:', 'active:', 'disabled:',
        'focus-visible:', 'focus-within:', 'group-hover:',
        'data-[state=open]:', 'data-[state=closed]:',
        'data-[state=checked]:', 'data-[state=unchecked]:',
        'data-[side=', 'data-[disabled]:',
        'aria-selected:', 'aria-disabled:',
    ]

    # CSS variable reference in Tailwind
    CSS_VAR_REF_RE = re.compile(
        r"""(?:bg|text|border|ring|shadow|fill|stroke)-\[(?:hsl\()?var\(--[\w-]+\)""",
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract shadcn/ui styling information from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'cn_usages', 'cva_definitions', 'tailwind_patterns'
        """
        result: Dict[str, Any] = {
            'cn_usages': [],
            'cva_definitions': [],
            'tailwind_patterns': [],
        }

        if not content or not content.strip():
            return result

        # Extract cn() usages
        result['cn_usages'] = self._extract_cn_usages(content, file_path)

        # Extract CVA definitions
        result['cva_definitions'] = self._extract_cva_definitions(
            content, file_path
        )

        # Extract Tailwind patterns in shadcn context
        result['tailwind_patterns'] = self._extract_tailwind_patterns(
            content, file_path
        )

        return result

    def _extract_cn_usages(
        self, content: str, file_path: str
    ) -> List[ShadcnCnUsageInfo]:
        """Extract cn() utility usages."""
        usages: List[ShadcnCnUsageInfo] = []

        # Verify cn is imported or defined
        has_cn = (
            'cn(' in content and (
                self.CN_IMPORT_RE.search(content) is not None or
                'function cn(' in content or
                'const cn = ' in content
            )
        )

        if not has_cn:
            return usages

        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for match in self.CN_USAGE_RE.finditer(line):
                args = match.group(1)

                # Count class arguments
                class_count = len([
                    a for a in args.split(',')
                    if a.strip() and not a.strip().startswith('//')
                ])

                # Detect patterns
                has_conditional = (
                    '&&' in args or '?' in args or
                    'true' in args or 'false' in args
                )
                has_dark = self.DARK_MODE_PREFIX in args
                has_responsive = any(
                    prefix in args for prefix in self.RESPONSIVE_PREFIXES
                )

                # Try to determine component context
                component = self._find_component_context(lines, line_num - 1)

                usages.append(ShadcnCnUsageInfo(
                    file=file_path,
                    line_number=line_num,
                    component=component,
                    class_count=class_count,
                    has_conditional=has_conditional,
                    has_dark_mode=has_dark,
                    has_responsive=has_responsive,
                ))

        return usages

    def _extract_cva_definitions(
        self, content: str, file_path: str
    ) -> List[ShadcnCvaInfo]:
        """Extract CVA (class-variance-authority) definitions."""
        definitions: List[ShadcnCvaInfo] = []

        if not self.CVA_IMPORT_RE.search(content) and 'cva(' not in content:
            return definitions

        for match in self.CVA_DEF_RE.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            start = match.end()

            info = ShadcnCvaInfo(
                name=name,
                file=file_path,
                line_number=line_num,
            )

            # Extract CVA body using brace counting
            body = self._extract_balanced_block(content, start - 1)

            # Extract base classes (first string argument)
            base_match = re.search(
                r"""['"]((?:[^'"\n]|\\['"])*?)['"]""", body
            )
            if base_match:
                info.base_classes = base_match.group(1)

            # Extract variants block
            variants_match = re.search(
                r'variants\s*:\s*\{', body
            )
            if variants_match:
                variants_body = self._extract_balanced_block(
                    body, variants_match.end() - 1
                )
                # Extract variant names and their values
                variant_key_re = re.compile(
                    r'(\w+)\s*:\s*\{([^}]+)\}'
                )
                for vm in variant_key_re.finditer(variants_body):
                    variant_key = vm.group(1)
                    variant_values_str = vm.group(2)
                    values = re.findall(r'(\w+)\s*:', variant_values_str)
                    info.variant_names.append(variant_key)
                    info.variant_values[variant_key] = values

            # Extract default variants
            default_match = re.search(
                r'defaultVariants\s*:\s*\{([^}]+)\}', body
            )
            if default_match:
                defaults = default_match.group(1)
                variant_default = re.search(
                    r"""variant\s*:\s*['"](\w+)['"]""", defaults
                )
                if variant_default:
                    info.default_variant = variant_default.group(1)
                size_default = re.search(
                    r"""size\s*:\s*['"](\w+)['"]""", defaults
                )
                if size_default:
                    info.default_size = size_default.group(1)

            # Compound variants
            info.has_compound_variants = 'compoundVariants' in body

            definitions.append(info)

        return definitions

    def _extract_tailwind_patterns(
        self, content: str, file_path: str
    ) -> List[ShadcnTailwindPatternInfo]:
        """Extract significant Tailwind CSS patterns in shadcn/ui context."""
        patterns: List[ShadcnTailwindPatternInfo] = []
        seen: set = set()

        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            # Responsive patterns
            for prefix in self.RESPONSIVE_PREFIXES:
                if prefix in line:
                    key = f"responsive:{line_num}"
                    if key not in seen:
                        seen.add(key)
                        classes = re.findall(
                            rf'{re.escape(prefix)}[\w\[\]-]+', line
                        )
                        if classes:
                            component = self._find_component_context(
                                lines, line_num - 1
                            )
                            patterns.append(ShadcnTailwindPatternInfo(
                                file=file_path,
                                line_number=line_num,
                                pattern_type='responsive',
                                classes=classes[:10],
                                component=component,
                            ))
                    break  # Only record once per line

            # Dark mode patterns
            if self.DARK_MODE_PREFIX in line:
                key = f"dark:{line_num}"
                if key not in seen:
                    seen.add(key)
                    classes = re.findall(r'dark:[\w\[\]-]+', line)
                    if classes:
                        component = self._find_component_context(
                            lines, line_num - 1
                        )
                        patterns.append(ShadcnTailwindPatternInfo(
                            file=file_path,
                            line_number=line_num,
                            pattern_type='dark-mode',
                            classes=classes[:10],
                            component=component,
                        ))

            # Data attribute state patterns (Radix UI)
            if 'data-[' in line:
                key = f"data-state:{line_num}"
                if key not in seen:
                    seen.add(key)
                    classes = re.findall(r'data-\[[^\]]+\]:[\w\[\]-]+', line)
                    if classes:
                        component = self._find_component_context(
                            lines, line_num - 1
                        )
                        patterns.append(ShadcnTailwindPatternInfo(
                            file=file_path,
                            line_number=line_num,
                            pattern_type='data-state',
                            classes=classes[:10],
                            component=component,
                        ))

            # Animation patterns (transition, animate)
            if re.search(r'\b(?:transition-|animate-|duration-)', line):
                key = f"animation:{line_num}"
                if key not in seen:
                    seen.add(key)
                    classes = re.findall(
                        r'(?:transition|animate|duration)-[\w\[\]-]+', line
                    )
                    if classes:
                        component = self._find_component_context(
                            lines, line_num - 1
                        )
                        patterns.append(ShadcnTailwindPatternInfo(
                            file=file_path,
                            line_number=line_num,
                            pattern_type='animation',
                            classes=classes[:10],
                            component=component,
                        ))

        return patterns

    def _find_component_context(
        self, lines: List[str], current_index: int
    ) -> str:
        """Find the enclosing component name for a line."""
        # Search backward for component function definition
        for i in range(current_index, max(-1, current_index - 30), -1):
            line = lines[i]
            # React component patterns
            comp_match = re.search(
                r"""(?:function|const|export\s+(?:default\s+)?function)\s+([A-Z]\w*)""",
                line,
            )
            if comp_match:
                return comp_match.group(1)
            # forwardRef pattern
            ref_match = re.search(
                r"""(?:const|let)\s+([A-Z]\w*)\s*=\s*(?:React\.)?forwardRef""",
                line,
            )
            if ref_match:
                return ref_match.group(1)
        return ""

    def _extract_balanced_block(self, content: str, start: int) -> str:
        """Extract content within balanced braces/parens starting at start."""
        if start < 0 or start >= len(content):
            return ""

        # Find the opening brace/paren
        idx = start
        while idx < len(content) and content[idx] not in ('{', '('):
            idx += 1

        if idx >= len(content):
            return ""

        opener = content[idx]
        closer = '}' if opener == '{' else ')'
        depth = 1
        idx += 1
        body_start = idx

        while idx < len(content) and depth > 0:
            ch = content[idx]
            if ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
            elif ch in ('"', "'", '`'):
                # Skip strings
                quote = ch
                idx += 1
                while idx < len(content):
                    if content[idx] == '\\':
                        idx += 1
                    elif content[idx] == quote:
                        break
                    idx += 1
            idx += 1

        return content[body_start:idx - 1]
