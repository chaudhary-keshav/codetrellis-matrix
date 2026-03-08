"""
Less Ruleset Extractor for CodeTrellis

Extracts Less :extend(), detached rulesets, nesting, parent selector (&),
and property merging (+ and +_).

Supports:
- :extend(.selector) — extend a selector
- :extend(.selector all) — extend with all keyword
- .selector:extend(.other) — inline extend syntax
- Detached rulesets: @ruleset: { ... }; @ruleset();
- Nesting depth analysis
- Parent selector & (concatenation, combinators, BEM patterns)
- Property merging: property+: value;  property+_: value;
- Each loops: each(@list, { ... }) (Less 3.7+)
- Recursive mixin loops with guard termination
- CSS guards: & when (condition) { }

Part of CodeTrellis v4.45 — Less CSS Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class LessExtendInfo:
    """Information about a Less :extend() usage."""
    target: str
    is_all: bool = False           # :extend(.selector all)
    is_inline: bool = False        # .selector:extend(.other) inline syntax
    file: str = ""
    line_number: int = 0


@dataclass
class LessDetachedRulesetInfo:
    """Information about a Less detached ruleset."""
    name: str
    body_lines: int = 0
    is_called: bool = False        # Whether @name() is invoked
    file: str = ""
    line_number: int = 0


@dataclass
class LessNestingInfo:
    """Information about Less nesting analysis."""
    selector: str
    depth: int = 0
    has_parent_selector: bool = False  # Uses &
    is_bem_pattern: bool = False       # &__element, &--modifier
    parent_usage: str = ""             # &-suffix, &.class, & + sibling
    file: str = ""
    line_number: int = 0


@dataclass
class LessPropertyMergeInfo:
    """Information about Less property merging."""
    property: str
    merge_type: str = "comma"      # comma (+) or space (+_)
    file: str = ""
    line_number: int = 0


class LessRulesetExtractor:
    """
    Extracts Less :extend(), detached rulesets, nesting analysis,
    parent selector patterns, and property merging.
    """

    # :extend(.selector) or :extend(.selector all)
    EXTEND_PATTERN = re.compile(
        r':extend\(\s*([^)]+?)\s*\)',
        re.MULTILINE
    )

    # Inline extend: .selector:extend(.other)
    INLINE_EXTEND_PATTERN = re.compile(
        r'([\w.#&>+~\[\]="\'\-:]+)\s*:extend\(\s*([^)]+?)\s*\)',
        re.MULTILINE
    )

    # Detached ruleset definition: @name: { ... };
    DETACHED_RULESET_DEF = re.compile(
        r'(@[\w-]+)\s*:\s*\{',
        re.MULTILINE
    )

    # Detached ruleset call: @name();
    DETACHED_RULESET_CALL = re.compile(
        r'(@[\w-]+)\s*\(\s*\)\s*;',
        re.MULTILINE
    )

    # Parent selector: &
    PARENT_SELECTOR_PATTERN = re.compile(
        r'&([\w._#>+~\[\]="\'\-]*)',
        re.MULTILINE
    )

    # BEM patterns: &__element, &--modifier
    BEM_PATTERN = re.compile(r'&(?:__|--)([\w-]+)')

    # Property merging: prop+: value; or prop+_: value;
    PROPERTY_MERGE_PATTERN = re.compile(
        r'([\w-]+)\+(_)?\s*:\s*[^;]+;',
        re.MULTILINE
    )

    # Each loop (Less 3.7+): each(@list, { })
    EACH_PATTERN = re.compile(r'each\s*\(', re.MULTILINE)

    # CSS guard: & when (condition) { }
    CSS_GUARD_PATTERN = re.compile(
        r'&\s*when\s*\([^)]+\)\s*\{',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Less :extend(), detached rulesets, nesting info,
        property merging, and parent selector patterns.

        Returns dict with 'extends', 'detached_rulesets', 'nesting',
        'property_merges', 'stats' keys.
        """
        if not content or not content.strip():
            return {'extends': [], 'detached_rulesets': [], 'nesting': [],
                    'property_merges': [], 'stats': {}}

        clean = self._strip_comments(content)

        extends = self._extract_extends(clean, file_path)
        detached = self._extract_detached_rulesets(clean, file_path)
        nesting = self._extract_nesting(clean, file_path)
        merges = self._extract_property_merges(clean, file_path)

        # Nesting depth analysis
        max_depth = max((n.depth for n in nesting), default=0)
        avg_depth = (sum(n.depth for n in nesting) / len(nesting)) if nesting else 0

        stats = {
            'total_extends': len(extends),
            'extend_all_count': sum(1 for e in extends if e.is_all),
            'inline_extends': sum(1 for e in extends if e.is_inline),
            'total_detached_rulesets': len(detached),
            'total_nesting': len(nesting),
            'max_nesting_depth': max_depth,
            'avg_nesting_depth': round(avg_depth, 1),
            'has_bem_patterns': any(n.is_bem_pattern for n in nesting),
            'has_parent_selector': any(n.has_parent_selector for n in nesting),
            'total_property_merges': len(merges),
            'has_each_loop': bool(self.EACH_PATTERN.search(clean)),
            'has_css_guards': bool(self.CSS_GUARD_PATTERN.search(clean)),
        }

        return {
            'extends': extends,
            'detached_rulesets': detached,
            'nesting': nesting,
            'property_merges': merges,
            'stats': stats,
        }

    def _strip_comments(self, content: str) -> str:
        """Strip comments preserving line structure."""
        result = re.sub(r'/\*.*?\*/', lambda m: '\n' * m.group().count('\n'), content, flags=re.DOTALL)
        result = re.sub(r'//[^\n]*', '', result)
        return result

    def _extract_extends(self, content: str, file_path: str) -> List[LessExtendInfo]:
        """Extract :extend() usages."""
        extends: List[LessExtendInfo] = []

        for match in self.EXTEND_PATTERN.finditer(content):
            target = match.group(1).strip()
            line_num = content[:match.start()].count('\n') + 1

            is_all = target.endswith(' all')
            if is_all:
                target = target[:-4].strip()

            # Detect inline extend
            before = content[max(0, match.start() - 50):match.start()]
            is_inline = not before.rstrip().endswith('{') and ':extend' not in before[-8:]

            extends.append(LessExtendInfo(
                target=target[:80],
                is_all=is_all,
                is_inline=bool(re.search(r'[\w.#&]', before[-10:])) if before else False,
                file=file_path,
                line_number=line_num,
            ))

        return extends

    def _extract_detached_rulesets(self, content: str, file_path: str) -> List[LessDetachedRulesetInfo]:
        """Extract detached ruleset definitions and calls."""
        rulesets: Dict[str, LessDetachedRulesetInfo] = {}

        # Definitions
        for match in self.DETACHED_RULESET_DEF.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Count body lines
            body_start = match.end()
            body_end = self._find_matching_brace(content, body_start - 1)
            body = content[body_start:body_end]
            body_lines = body.count('\n')

            rulesets[name] = LessDetachedRulesetInfo(
                name=name,
                body_lines=body_lines,
                file=file_path,
                line_number=line_num,
            )

        # Check for calls
        for match in self.DETACHED_RULESET_CALL.finditer(content):
            name = match.group(1)
            if name in rulesets:
                rulesets[name].is_called = True

        return list(rulesets.values())

    def _extract_nesting(self, content: str, file_path: str) -> List[LessNestingInfo]:
        """Extract nesting depth and parent selector patterns."""
        nesting: List[LessNestingInfo] = []
        lines = content.split('\n')
        depth = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            # Track depth
            open_count = stripped.count('{')
            close_count = stripped.count('}')

            if open_count > 0 and not stripped.startswith('@'):
                # This is a selector with opening brace
                selector = stripped.split('{')[0].strip()
                if selector and not selector.startswith('//'):
                    has_parent = '&' in selector
                    is_bem = bool(self.BEM_PATTERN.search(selector))

                    parent_usage = ""
                    parent_match = self.PARENT_SELECTOR_PATTERN.search(selector)
                    if parent_match:
                        suffix = parent_match.group(1)
                        if suffix:
                            parent_usage = f"&{suffix}"

                    nesting.append(LessNestingInfo(
                        selector=selector[:80],
                        depth=depth + 1,
                        has_parent_selector=has_parent,
                        is_bem_pattern=is_bem,
                        parent_usage=parent_usage,
                        file=file_path,
                        line_number=i + 1,
                    ))

            depth += open_count - close_count

        return nesting

    def _extract_property_merges(self, content: str, file_path: str) -> List[LessPropertyMergeInfo]:
        """Extract property merging usages (+ and +_)."""
        merges: List[LessPropertyMergeInfo] = []

        for match in self.PROPERTY_MERGE_PATTERN.finditer(content):
            prop = match.group(1)
            has_space = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            merges.append(LessPropertyMergeInfo(
                property=prop,
                merge_type="space" if has_space else "comma",
                file=file_path,
                line_number=line_num,
            ))

        return merges

    def _find_matching_brace(self, content: str, start: int) -> int:
        """Find matching closing brace."""
        depth = 0
        i = start
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return len(content)
