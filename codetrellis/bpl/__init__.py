"""Best Practices Library (BPL) for CodeTrellis.

The BPL module provides version-aware, context-sensitive best practices
injection for AI code generation. It integrates with CodeTrellis to enhance
AI prompts with relevant coding standards and patterns.

Key Components:
    - models: Core data models (BestPractice, PracticeCategory, etc.)
    - repository: Loading and managing practices from YAML files
    - selector: Context-aware practice selection based on project analysis

Basic Usage:
    >>> from codetrellis.bpl import PracticeSelector, BestPracticesRepository
    >>>
    >>> # Load practices
    >>> repo = BestPracticesRepository()
    >>> repo.load_all()
    >>>
    >>> # Get practices for a framework
    >>> fastapi_practices = repo.get_by_framework("fastapi")
    >>>
    >>> # Or use selector with project context
    >>> selector = PracticeSelector()
    >>> output = selector.select_for_project(project_matrix)
    >>> print(output.to_codetrellis_format())

Integration with CodeTrellis:
    The BPL output can be integrated into CodeTrellis matrix output by adding
    the [BEST_PRACTICES] section to the generated prompt.

Example:
    >>> # In cli.py scan command
    >>> from codetrellis.bpl import select_practices
    >>>
    >>> # After scanning project
    >>> bpl_output = select_practices(
    ...     matrix=project_matrix,
    ...     categories=[PracticeCategory.TYPE_SAFETY],
    ...     min_priority=PracticePriority.HIGH
    ... )
    >>>
    >>> # Add to output
    >>> output += "\\n" + bpl_output.to_codetrellis_format(tier="prompt")
"""

from __future__ import annotations

__version__ = "1.0.0"
__all__ = [
    # Models
    "BestPractice",
    "PracticeCategory",
    "PracticeContent",
    "PracticeLevel",
    "PracticePriority",
    "VersionConstraint",
    "ApplicabilityRule",
    "SOLIDPrinciple",
    "DesignPatternType",
    "DesignPattern",
    "PracticeSet",
    "BPLOutput",
    # Repository
    "BestPracticesRepository",
    "get_repository",
    "reload_repository",
    "PracticeLoadError",
    "PracticeValidationError",
    # Selector
    "PracticeSelector",
    "ProjectContext",
    "SelectionCriteria",
    "get_selector",
    "select_practices",
    # Token utilities (P3-05, P3-06)
    "count_tokens",
    "is_tiktoken_available",
    "OutputFormat",
]


# Lazy imports for better performance
def __getattr__(name: str):
    """Lazy import module components."""
    if name in (
        "BestPractice",
        "PracticeCategory",
        "PracticeContent",
        "PracticeLevel",
        "PracticePriority",
        "VersionConstraint",
        "ApplicabilityRule",
        "SOLIDPrinciple",
        "DesignPatternType",
        "DesignPattern",
        "PracticeSet",
        "BPLOutput",
    ):
        from .models import (
            ApplicabilityRule,
            BestPractice,
            BPLOutput,
            DesignPattern,
            DesignPatternType,
            PracticeCategory,
            PracticeContent,
            PracticeLevel,
            PracticePriority,
            PracticeSet,
            SOLIDPrinciple,
            VersionConstraint,
        )

        return {
            "BestPractice": BestPractice,
            "PracticeCategory": PracticeCategory,
            "PracticeContent": PracticeContent,
            "PracticeLevel": PracticeLevel,
            "PracticePriority": PracticePriority,
            "VersionConstraint": VersionConstraint,
            "ApplicabilityRule": ApplicabilityRule,
            "SOLIDPrinciple": SOLIDPrinciple,
            "DesignPatternType": DesignPatternType,
            "DesignPattern": DesignPattern,
            "PracticeSet": PracticeSet,
            "BPLOutput": BPLOutput,
        }[name]

    elif name in (
        "BestPracticesRepository",
        "get_repository",
        "reload_repository",
        "PracticeLoadError",
        "PracticeValidationError",
    ):
        from .repository import (
            BestPracticesRepository,
            PracticeLoadError,
            PracticeValidationError,
            get_repository,
            reload_repository,
        )

        return {
            "BestPracticesRepository": BestPracticesRepository,
            "get_repository": get_repository,
            "reload_repository": reload_repository,
            "PracticeLoadError": PracticeLoadError,
            "PracticeValidationError": PracticeValidationError,
        }[name]

    elif name in (
        "PracticeSelector",
        "ProjectContext",
        "SelectionCriteria",
        "get_selector",
        "select_practices",
        "count_tokens",
        "is_tiktoken_available",
        "OutputFormat",
    ):
        from .selector import (
            OutputFormat,
            PracticeSelector,
            ProjectContext,
            SelectionCriteria,
            count_tokens,
            get_selector,
            is_tiktoken_available,
            select_practices,
        )

        return {
            "PracticeSelector": PracticeSelector,
            "ProjectContext": ProjectContext,
            "SelectionCriteria": SelectionCriteria,
            "get_selector": get_selector,
            "select_practices": select_practices,
            "count_tokens": count_tokens,
            "is_tiktoken_available": is_tiktoken_available,
            "OutputFormat": OutputFormat,
        }[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
