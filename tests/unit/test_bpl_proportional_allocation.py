"""Tests for BPL proportional language allocation and dynamic language grouping."""

import pytest
from unittest.mock import MagicMock
from codetrellis.bpl.selector import PracticeSelector
from codetrellis.bpl.models import (
    BestPractice,
    PracticeCategory,
    PracticePriority,
    PracticeContent,
    ApplicabilityRule,
)


def _make_practice(
    id: str,
    category: PracticeCategory = PracticeCategory.CODE_STYLE,
    priority: PracticePriority = PracticePriority.HIGH,
    tags: tuple = (),
) -> BestPractice:
    """Create a minimal BestPractice for testing."""
    return BestPractice(
        id=id,
        title=f"Practice {id}",
        category=category,
        level="intermediate",
        priority=priority,
        content=PracticeContent(
            description=f"Description for {id}",
            good_examples=[],
            bad_examples=[],
            tags=tags,
        ),
        applicability=ApplicabilityRule(
            frameworks=[],
            patterns=[],
            has_dependencies=[],
        ),
    )


class TestDeriveLanguageMap:
    """Tests for _derive_prefix_language_map()."""

    def test_root_languages_detected(self):
        """Root language prefixes should resolve to their language."""
        lang_map = PracticeSelector._derive_prefix_language_map()
        assert lang_map["PY"] == "python"
        assert lang_map["GO"] == "golang"
        assert lang_map["RS"] == "rust"
        assert lang_map["JAVA"] == "java"
        assert lang_map["JS"] == "javascript"
        assert lang_map["TS"] == "typescript"

    def test_frameworks_resolve_to_parent(self):
        """Framework prefixes should resolve to their parent language."""
        lang_map = PracticeSelector._derive_prefix_language_map()
        assert lang_map["FLASK"] == "python"
        assert lang_map["DJANGO"] == "python"
        assert lang_map["GIN"] == "golang"
        assert lang_map["ACTIX"] == "rust"
        assert lang_map["RAILS"] == "ruby"

    def test_react_resolves_to_typescript(self):
        """React and its children should all resolve to typescript."""
        lang_map = PracticeSelector._derive_prefix_language_map()
        assert lang_map["REACT"] == "typescript"
        assert lang_map["MUI"] == "typescript"
        assert lang_map["SHADCN"] == "typescript"
        assert lang_map["NEXT"] == "typescript"
        assert lang_map["REDUX"] == "typescript"

    def test_solidjs_htmx_resolve_to_javascript(self):
        """Standalone JS-ecosystem frameworks should resolve to javascript."""
        lang_map = PracticeSelector._derive_prefix_language_map()
        assert lang_map["SOLIDJS"] == "javascript"
        assert lang_map["HTMX"] == "javascript"
        assert lang_map["ALPINE"] == "javascript"
        assert lang_map["LIT"] == "javascript"
        assert lang_map["PREACT"] == "javascript"
        assert lang_map["QWIK"] == "javascript"

    def test_generic_prefixes(self):
        """Empty-set prefixes should resolve to 'generic'."""
        lang_map = PracticeSelector._derive_prefix_language_map()
        assert lang_map["DP"] == "generic"
        assert lang_map["SOLID"] == "generic"

    def test_all_prefixes_mapped(self):
        """Every prefix in the auto-built map should have a language mapping."""
        lang_map = PracticeSelector._derive_prefix_language_map()
        pfm = PracticeSelector._get_prefix_framework_map()
        for prefix in pfm:
            assert prefix in lang_map, f"Prefix {prefix} not in language map"

    def test_caching(self):
        """Subsequent calls should return the cached result."""
        PracticeSelector._cached_language_map = None
        map1 = PracticeSelector._get_prefix_language_map()
        map2 = PracticeSelector._get_prefix_language_map()
        assert map1 is map2

    def test_css_ecosystem_resolves_to_css(self):
        """CSS sub-frameworks (SASS, LESS, PCSS) should resolve to css."""
        lang_map = PracticeSelector._derive_prefix_language_map()
        assert lang_map["SASS"] == "css"
        assert lang_map["LESS"] == "css"
        assert lang_map["PCSS"] == "css"
        assert lang_map["TW"] == "css"
        assert lang_map["BOOT"] == "css"

    def test_codeigniter_resolves_to_php(self):
        """CI prefix (CodeIgniter) should resolve to php, not generic."""
        lang_map = PracticeSelector._derive_prefix_language_map()
        assert lang_map["CI"] == "php"


class TestIsSecurityPractice:
    """Tests for _is_security_practice()."""

    def test_security_category(self):
        p = _make_practice("SEC001", category=PracticeCategory.SECURITY)
        assert PracticeSelector._is_security_practice(p) is True

    def test_security_tag(self):
        p = _make_practice("PY001", tags=("security", "core"))
        assert PracticeSelector._is_security_practice(p) is True

    def test_non_security(self):
        p = _make_practice("PY001", tags=("performance",))
        assert PracticeSelector._is_security_practice(p) is False


class TestGetPracticeLanguage:
    """Tests for get_practice_language() (public API)."""

    def test_public_api_matches_private(self):
        selector = PracticeSelector()
        p = _make_practice("FLASK001")
        assert selector.get_practice_language(p) == selector._get_practice_language(p)

    def test_longest_prefix_match(self):
        selector = PracticeSelector()
        # GRPCGO should match before GO
        p = _make_practice("GRPCGO001")
        assert selector.get_practice_language(p) == "golang"

    def test_unknown_prefix_returns_generic(self):
        selector = PracticeSelector()
        p = _make_practice("UNKNOWN999")
        assert selector.get_practice_language(p) == "generic"

    def test_framework_fallback_for_unknown_prefix(self):
        """Unknown prefixes should resolve via applicability.frameworks."""
        selector = PracticeSelector()
        p = BestPractice(
            id="SPRING001",
            title="Spring Practice",
            category=PracticeCategory.CODE_STYLE,
            level="intermediate",
            priority="medium",
            content=PracticeContent(description="test"),
            applicability=ApplicabilityRule(frameworks=("spring", "java")),
        )
        assert selector.get_practice_language(p) == "java"


class TestAllocateProportionalSlots:
    """Tests for _allocate_proportional_slots()."""

    def _make_context(self):
        ctx = MagicMock()
        ctx.frameworks = set()
        return ctx

    def test_budget_filled(self):
        """Result should contain exactly max_practices items."""
        selector = PracticeSelector()
        practices = [_make_practice(f"PY{i:03d}") for i in range(20)]
        practices += [_make_practice(f"GO{i:03d}") for i in range(10)]
        result = selector._allocate_proportional_slots(
            practices, self._make_context(), max_practices=15
        )
        assert len(result) == 15

    def test_proportional_distribution(self):
        """Larger groups should get more slots."""
        selector = PracticeSelector()
        py_practices = [_make_practice(f"PY{i:03d}") for i in range(20)]
        go_practices = [_make_practice(f"GO{i:03d}") for i in range(5)]
        all_practices = py_practices + go_practices
        result = selector._allocate_proportional_slots(
            all_practices, self._make_context(), max_practices=10
        )
        py_count = sum(1 for p in result if p.id.startswith("PY"))
        go_count = sum(1 for p in result if p.id.startswith("GO"))
        # Python (20/25 = 80%) should get more than Go (5/25 = 20%)
        assert py_count > go_count

    def test_security_priority(self):
        """Security practices should be included even in small allocations."""
        selector = PracticeSelector()
        practices = [
            _make_practice("PY001"),
            _make_practice("PY002"),
            _make_practice(
                "PY003", category=PracticeCategory.SECURITY
            ),
            _make_practice("GO001"),
            _make_practice("GO002"),
        ]
        result = selector._allocate_proportional_slots(
            practices, self._make_context(), max_practices=4
        )
        ids = {p.id for p in result}
        assert "PY003" in ids, "Security practice should be prioritized"

    def test_many_groups_exceeding_budget(self):
        """When num_groups > max_practices, should not exceed budget."""
        selector = PracticeSelector()
        # Create 10 groups with 2 practices each
        practices = []
        for prefix in ["PY", "GO", "RS", "JAVA", "CS", "RB", "SCALA", "DART", "LUA", "SWIFT"]:
            for i in range(2):
                practices.append(_make_practice(f"{prefix}{i:03d}"))
        result = selector._allocate_proportional_slots(
            practices, self._make_context(), max_practices=5
        )
        assert len(result) <= 5

    def test_slot_redistribution(self):
        """Unused slots from small groups should be redistributed."""
        selector = PracticeSelector()
        # Large group (10 practices) + tiny group (1 practice)
        practices = [_make_practice(f"PY{i:03d}") for i in range(10)]
        practices.append(_make_practice("GO001"))
        result = selector._allocate_proportional_slots(
            practices, self._make_context(), max_practices=8
        )
        # With redistribution, we should get 8 total even though
        # Go only has 1 practice (unused slots go back to Python)
        assert len(result) == 8

    def test_returns_all_when_under_budget(self):
        """When scored <= max_practices, return all."""
        selector = PracticeSelector()
        practices = [_make_practice(f"PY{i:03d}") for i in range(3)]
        result = selector._allocate_proportional_slots(
            practices, self._make_context(), max_practices=10
        )
        assert len(result) == 3
