"""
CSS Selector Extractor for CodeTrellis

Extracts CSS selectors, specificity, rule blocks, nesting (CSS Nesting spec),
and selector complexity from CSS/SCSS/Less source code.

Supports:
- CSS1-CSS3 selectors (element, class, ID, attribute, pseudo)
- CSS4 selectors (:is(), :where(), :has(), :not())
- Combinators (descendant, child, sibling, general sibling)
- CSS Nesting (& parent selector, @nest)
- SCSS/Less nesting
- @scope rules (CSS Scoping)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CSSSelectorInfo:
    """Information about a CSS selector."""
    selector: str
    file: str = ""
    line_number: int = 0
    specificity: tuple = (0, 0, 0)  # (id, class, element)
    selector_type: str = ""  # class, id, element, pseudo, attribute, combinator
    is_nested: bool = False
    parent_selector: str = ""
    property_count: int = 0


@dataclass
class CSSRuleInfo:
    """Information about a CSS rule block."""
    selectors: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    property_count: int = 0
    has_nesting: bool = False
    nested_rules: int = 0
    is_at_rule: bool = False
    at_rule_type: str = ""  # media, keyframes, supports, layer, scope, etc.


class CSSSelectorExtractor:
    """
    Extracts CSS selectors and rule blocks from CSS/SCSS/Less source code.

    Detects:
    - All CSS selector types (class, ID, element, pseudo, attribute)
    - CSS4 functional selectors (:is, :where, :has, :not)
    - Nesting patterns (CSS Nesting, SCSS, Less)
    - @-rules (media, keyframes, supports, layer, scope, container)
    - Selector specificity calculation
    """

    # Pattern to match CSS rule blocks (selector { ... })
    # Handles both formatted and minified CSS by matching after }, newline, or start
    RULE_PATTERN = re.compile(
        r'(?:^|[};])\s*([^{@/;][^{]*?)\s*\{',
        re.MULTILINE
    )

    # Pattern to match @-rules
    AT_RULE_PATTERN = re.compile(
        r'^(\s*@(\w[\w-]*)\s*[^{;]*?)\s*\{',
        re.MULTILINE
    )

    # CSS4 functional pseudo selectors
    FUNCTIONAL_PSEUDO = re.compile(r':(?:is|where|has|not|matches|nth-child|nth-of-type)\s*\(')

    # Nesting indicator
    NESTING_PATTERN = re.compile(r'&\s*[.#\[:>\+~\w-]|@nest\s')

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all selectors and rules from CSS source code.

        Returns dict with:
          - selectors: List[CSSSelectorInfo]
          - rules: List[CSSRuleInfo]
          - stats: Dict with selector counts by type
        """
        selectors: List[CSSSelectorInfo] = []
        rules: List[CSSRuleInfo] = []
        stats = {
            "total_rules": 0,
            "total_selectors": 0,
            "class_selectors": 0,
            "id_selectors": 0,
            "element_selectors": 0,
            "pseudo_selectors": 0,
            "pseudo_class_selectors": 0,
            "pseudo_element_selectors": 0,
            "attribute_selectors": 0,
            "css4_functional": 0,
            "nested_rules": 0,
            "has_nesting": False,
            "at_rules": 0,
        }

        # Remove comments
        clean = self._remove_comments(content)

        # Extract @-rules
        for match in self.AT_RULE_PATTERN.finditer(clean):
            at_rule = match.group(1).strip()
            at_type = match.group(2).strip()
            line_num = clean[:match.start()].count('\n') + 1

            rule_info = CSSRuleInfo(
                selectors=[at_rule],
                file=file_path,
                line_number=line_num,
                is_at_rule=True,
                at_rule_type=at_type,
            )
            rules.append(rule_info)
            stats["at_rules"] += 1

        # Extract regular rules
        for match in self.RULE_PATTERN.finditer(clean):
            selector_text = match.group(1).strip()
            line_num = clean[:match.start()].count('\n') + 1

            # Skip if it's inside an @-rule body (we handle those separately)
            if selector_text.startswith('@'):
                continue

            # Split comma-separated selectors
            parts = [s.strip() for s in selector_text.split(',') if s.strip()]

            has_nesting = bool(self.NESTING_PATTERN.search(selector_text))
            if has_nesting:
                stats["nested_rules"] += 1
                stats["has_nesting"] = True

            # Count properties in block
            body_start = match.end()
            prop_count = self._count_properties(clean, body_start)

            rule_info = CSSRuleInfo(
                selectors=parts,
                file=file_path,
                line_number=line_num,
                property_count=prop_count,
                has_nesting=has_nesting,
            )
            rules.append(rule_info)
            stats["total_rules"] += 1

            for sel in parts:
                specificity = self._calculate_specificity(sel)
                sel_type = self._classify_selector(sel)

                selector_info = CSSSelectorInfo(
                    selector=sel,
                    file=file_path,
                    line_number=line_num,
                    specificity=specificity,
                    selector_type=sel_type,
                    is_nested=has_nesting,
                    property_count=prop_count,
                )
                selectors.append(selector_info)

                # Update stats
                stats["total_selectors"] += 1
                if sel_type == "class":
                    stats["class_selectors"] += 1
                elif sel_type == "id":
                    stats["id_selectors"] += 1
                elif sel_type == "element":
                    stats["element_selectors"] += 1
                elif sel_type == "pseudo_class":
                    stats["pseudo_selectors"] += 1
                    stats["pseudo_class_selectors"] += 1
                elif sel_type == "pseudo_element":
                    stats["pseudo_selectors"] += 1
                    stats["pseudo_element_selectors"] += 1
                elif sel_type == "attribute":
                    stats["attribute_selectors"] += 1

                if self.FUNCTIONAL_PSEUDO.search(sel):
                    stats["css4_functional"] += 1

        return {
            "selectors": selectors,
            "rules": rules,
            "stats": stats,
        }

    def _remove_comments(self, content: str) -> str:
        """Remove CSS comments (/* ... */) and // line comments (SCSS/Less)."""
        # Block comments
        result = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        # Line comments (SCSS/Less)
        result = re.sub(r'//[^\n]*', '', result)
        return result

    def _count_properties(self, content: str, start: int) -> int:
        """Count properties in a CSS rule block starting at position."""
        depth = 1
        pos = start
        count = 0
        while pos < len(content) and depth > 0:
            ch = content[pos]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
            elif ch == ';' and depth == 1:
                count += 1
            pos += 1
        return count

    def _calculate_specificity(self, selector: str) -> tuple:
        """Calculate CSS specificity (id, class, element) for a selector."""
        # Remove :not() content for specificity (contents count, not :not itself)
        s = re.sub(r':not\(([^)]*)\)', r'\1', selector)
        # Remove :is() and :where() (different specificity rules)
        s = re.sub(r':where\([^)]*\)', '', s)

        ids = len(re.findall(r'#[\w-]+', s))
        classes = len(re.findall(r'\.[\w-]+', s))
        classes += len(re.findall(r'\[[\w-]+', s))  # attribute selectors
        classes += len(re.findall(r':(?!:)[\w-]+(?!\()', s))  # pseudo-classes (not pseudo-elements)
        elements = len(re.findall(r'(?:^|[\s>+~])[\w][\w-]*', s))
        elements += len(re.findall(r'::[\w-]+', s))  # pseudo-elements

        return (ids, classes, elements)

    def _classify_selector(self, selector: str) -> str:
        """Classify a selector by its primary type.

        Priority order handles compound selectors like 'a:hover' or 'p::first-line':
        - pseudo_element (::) takes priority
        - pseudo_class (:) next (but not :: which is pseudo_element)
        - attribute ([...]) next
        - id (#) next
        - class (.) next
        - nested (&) next
        - element (bare tag name) is default
        """
        s = selector.strip()

        # Check for pseudo-element anywhere in selector (::before, ::after, etc.)
        if '::' in s:
            return "pseudo_element"

        # Check for pseudo-class anywhere in selector (:hover, :focus, :nth-child, etc.)
        # but not :: (already handled above)
        if re.search(r':(?!:)[\w-]', s):
            return "pseudo_class"

        # Check for attribute selector anywhere
        if '[' in s:
            return "attribute"

        # Check start-based types
        if s.startswith('#'):
            return "id"
        if s.startswith('.'):
            return "class"
        if re.match(r'^&', s):
            return "nested"
        if re.match(r'^[\w]', s):
            if '.' in s or '#' in s:
                return "combined"
            return "element"
        return "complex"
