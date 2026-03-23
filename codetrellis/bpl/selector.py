"""Practice Selector for context-aware best practice selection.

This module provides the PracticeSelector class for selecting best practices
based on project context extracted from ProjectMatrix.

The selector analyzes:
- Detected frameworks and dependencies
- Architecture patterns in use
- Python version requirements
- Project type and structure

Example:
    >>> from codetrellis.bpl.selector import PracticeSelector
    >>> from codetrellis.scanner import ProjectMatrix
    >>>
    >>> selector = PracticeSelector()
    >>> matrix = ProjectMatrix(...)  # From CodeTrellis scan
    >>> practices = selector.select_for_project(matrix)
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

from .models import (
    BestPractice,
    BPLOutput,
    PracticeCategory,
    PracticeLevel,
    PracticePriority,
)
from .repository import BestPracticesRepository, get_repository

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# Token Estimation with tiktoken (optional, with fallback)
# ═══════════════════════════════════════════════════════════════════════════

# Try to import tiktoken for accurate token counting
_tiktoken_encoder: Optional[Any] = None
_use_tiktoken: bool = False

try:
    import tiktoken

    # Use cl100k_base encoding (GPT-4, GPT-3.5-turbo)
    _tiktoken_encoder = tiktoken.get_encoding("cl100k_base")
    _use_tiktoken = True
    logger.debug("tiktoken available - using accurate token counting")
except ImportError:
    logger.debug("tiktoken not installed - using char/4 heuristic for token estimation")


def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken if available, else char/4 heuristic.

    Args:
        text: The text to count tokens for.

    Returns:
        Estimated or actual token count.
    """
    if _use_tiktoken and _tiktoken_encoder is not None:
        return len(_tiktoken_encoder.encode(text))
    # Fallback: ~4 characters per token (GPT-style heuristic)
    return max(1, len(text) // 4)


def is_tiktoken_available() -> bool:
    """Check if tiktoken is available for accurate token counting."""
    return _use_tiktoken


# ═══════════════════════════════════════════════════════════════════════════
# Dynamic Format Selection (P3-06)
# ═══════════════════════════════════════════════════════════════════════════


class OutputFormat:
    """Output format tiers with different token costs.

    Formats are listed in order of detail (highest to lowest):
    - full: Complete details with all metadata
    - prompt: Balanced output for AI prompts (default)
    - compact: Minimal output with essential info only
    - minimal: Bare minimum (ID + title only)
    """

    FULL = "full"
    PROMPT = "prompt"
    COMPACT = "compact"
    MINIMAL = "minimal"

    # Format priority (higher detail to lower)
    _PRIORITY = [FULL, PROMPT, COMPACT, MINIMAL]

    @classmethod
    def select_format_for_budget(
        cls,
        practices: List[BestPractice],
        max_tokens: int,
        preferred_format: str = PROMPT,
    ) -> str:
        """Select the best format that fits within a token budget.

        Progressively downgrades format until practices fit the budget.

        Args:
            practices: List of practices to format.
            max_tokens: Maximum token budget.
            preferred_format: Preferred format to try first.

        Returns:
            Format string that fits the budget, or MINIMAL if none fit.
        """
        # Get formats from preferred to minimal
        start_idx = cls._PRIORITY.index(preferred_format)
        formats_to_try = cls._PRIORITY[start_idx:]

        for fmt in formats_to_try:
            estimated = cls._estimate_format_tokens(practices, fmt)
            if estimated <= max_tokens:
                return fmt

        # If nothing fits, return minimal
        return cls.MINIMAL

    @classmethod
    def _estimate_format_tokens(
        cls, practices: List[BestPractice], format_tier: str
    ) -> int:
        """Estimate total tokens for a list of practices in a given format.

        Args:
            practices: List of practices.
            format_tier: Format tier to estimate.

        Returns:
            Estimated token count.
        """
        compact = format_tier in (cls.COMPACT, cls.MINIMAL)
        total = 0

        # Add header overhead
        if format_tier == cls.FULL:
            total += 30  # Headers, timestamps, etc.
        elif format_tier == cls.PROMPT:
            total += 20  # Category headers
        else:
            total += 5  # Minimal header

        for practice in practices:
            if format_tier == cls.MINIMAL:
                # ID + title only
                text = f"{practice.id}|{practice.title}"
                total += count_tokens(text)
            else:
                text = practice.to_codetrellis_format(compact=compact)
                total += count_tokens(text)

        return total


@dataclass
class SelectionCriteria:
    """Criteria for filtering practices during selection.

    Attributes:
        categories: Categories to include. If empty, include all.
        levels: Expertise levels to include. If empty, include all.
        min_priority: Minimum priority level to include.
        frameworks: Frameworks to filter for. If empty, auto-detect.
        include_generic: Whether to include generic (non-framework) practices.
        max_practices: Maximum number of practices to return.
        python_version: Python version for compatibility check.
    """

    categories: List[PracticeCategory] = field(default_factory=list)
    levels: List[PracticeLevel] = field(default_factory=list)
    min_priority: PracticePriority = PracticePriority.LOW
    frameworks: List[str] = field(default_factory=list)
    include_generic: bool = True
    max_practices: int = 50
    python_version: Optional[str] = None
    max_tokens: Optional[int] = None


@dataclass
class ProjectContext:
    """Extracted context from a project for practice selection.

    This is built from ProjectMatrix or other project analysis.

    Attributes:
        project_name: Name of the project.
        project_type: Type of project (e.g., "FASTAPI", "DJANGO").
        python_version: Detected Python version.
        frameworks: Set of detected framework names.
        dependencies: Set of package dependencies.
        patterns: Set of detected architecture patterns.
        has_tests: Whether the project has tests.
        has_async: Whether the project uses async code.
        file_types: Set of file types present in the project.
    """

    project_name: str = ""
    project_type: str = "UNKNOWN"
    python_version: str = "3.9"
    frameworks: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)
    patterns: Set[str] = field(default_factory=set)
    has_tests: bool = False
    has_async: bool = False
    file_types: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for applicability matching.

        Returns:
            Dictionary suitable for ApplicabilityRule.matches().
        """
        return {
            "frameworks": self.frameworks,
            "patterns": self.patterns,
            "dependencies": self.dependencies,
            "project_type": self.project_type,
        }

    @classmethod
    def from_matrix(cls, matrix: Any) -> "ProjectContext":
        """Build context from a ProjectMatrix.

        Uses a weighted approach to detect the dominant language/framework
        based on the number of artifacts found.

        Args:
            matrix: ProjectMatrix from CodeTrellis scanner.

        Returns:
            Extracted ProjectContext.
        """
        context = cls()

        # Extract basic info
        context.project_name = getattr(matrix, "name", "")
        # v4.9 fix: project_type is not a direct field — read from overview dict
        project_type = "UNKNOWN"
        if hasattr(matrix, "overview") and matrix.overview:
            if isinstance(matrix.overview, dict):
                project_type = matrix.overview.get("type", matrix.overview.get("project_type", "UNKNOWN"))
            elif hasattr(matrix.overview, "project_type"):
                project_type = str(getattr(matrix.overview, "project_type", "UNKNOWN"))
        # Fallback: check direct project_type attribute on matrix
        if project_type == "UNKNOWN" and hasattr(matrix, "project_type") and matrix.project_type:
            project_type = str(matrix.project_type)
        context.project_type = str(project_type)

        # Extract Python version from pyproject.toml or setup.py
        context.python_version = "3.9"  # Default

        # Collect dependencies from multiple sources
        deps = set()
        dev_deps = set()

        # From package_info if available (legacy)
        if hasattr(matrix, "package_info") and matrix.package_info:
            pkg_info = matrix.package_info
            if hasattr(pkg_info, "dependencies"):
                deps.update(pkg_info.dependencies.keys())
            if hasattr(pkg_info, "dev_dependencies"):
                dev_deps.update(pkg_info.dev_dependencies.keys())

        # From matrix.dependencies (JS/TS from package.json)
        if hasattr(matrix, "dependencies") and matrix.dependencies:
            deps.update(matrix.dependencies.keys())

        # From matrix.python_dependencies
        if hasattr(matrix, "python_dependencies") and matrix.python_dependencies:
            deps.update(matrix.python_dependencies.keys())

        context.dependencies = deps | dev_deps

        # ==== COUNT ARTIFACTS BY LANGUAGE ====
        # This determines the DOMINANT language(s) for the project

        # Python artifact counts
        python_count = 0
        python_artifacts = [
            "python_dataclasses", "python_pydantic_models", "python_fastapi_endpoints",
            "python_flask_routes", "python_functions", "python_ml_models",
            "python_typed_dicts", "python_protocols", "python_type_aliases",
            "python_enums", "python_celery_tasks", "python_sqlalchemy_models"
        ]
        for attr in python_artifacts:
            if hasattr(matrix, attr):
                python_count += len(getattr(matrix, attr, []))

        # TypeScript/JavaScript artifact counts
        ts_count = 0
        ts_artifacts = [
            "interfaces", "types", "components", "angular_services",
            "stores", "controllers", "dtos", "schemas"
        ]
        for attr in ts_artifacts:
            if hasattr(matrix, attr):
                ts_count += len(getattr(matrix, attr, []))

        # Angular-specific count (subset of TS)
        angular_count = 0
        angular_artifacts = ["components", "angular_services", "stores"]
        for attr in angular_artifacts:
            if hasattr(matrix, attr):
                angular_count += len(getattr(matrix, attr, []))

        # NestJS-specific count
        nestjs_count = 0
        if hasattr(matrix, "controllers") and matrix.controllers:
            for ctrl in matrix.controllers:
                if ctrl.get("decorators") or "@Controller" in str(ctrl.get("source", "")):
                    nestjs_count += 1

        logger.debug(f"Artifact counts - Python: {python_count}, TS: {ts_count}, Angular: {angular_count}, NestJS: {nestjs_count}")

        # ==== DETERMINE DOMINANT LANGUAGE ====
        # Use both absolute threshold AND relative proportion
        SIGNIFICANCE_THRESHOLD = 5  # At least 5 artifacts to be considered
        DOMINANCE_RATIO = 0.1  # Must be at least 10% of the dominant count

        total_count = python_count + ts_count
        dominant_count = max(python_count, ts_count)

        # Detect Python if it has significant presence AND is meaningful proportion
        python_is_significant = (
            python_count >= SIGNIFICANCE_THRESHOLD and
            (ts_count == 0 or python_count >= ts_count * DOMINANCE_RATIO)
        )
        if python_is_significant:
            context.frameworks.add("python")

        # Detect TypeScript if it has significant presence AND is meaningful proportion
        # Also require it to be proportionally significant compared to Python
        ts_is_significant = (
            ts_count >= SIGNIFICANCE_THRESHOLD and
            (python_count == 0 or ts_count >= python_count * 0.3)  # Must be at least 30% of Python count
        )
        if ts_is_significant:
            context.frameworks.add("typescript")

        # Detect Angular if it has significant presence AND is the dominant frontend
        # Angular count must be significant compared to total TS count
        angular_is_significant = (
            angular_count >= SIGNIFICANCE_THRESHOLD and
            (ts_count == 0 or angular_count >= ts_count * 0.3)  # Must be 30%+ of TS count
        )
        if angular_is_significant:
            context.frameworks.add("angular")
            context.frameworks.add("typescript")

        # Detect NestJS if controllers are decorated with NestJS decorators
        if nestjs_count > 0:
            context.frameworks.add("nestjs")
            context.frameworks.add("typescript")

        # ==== Go artifact counts (v4.5 / G-17) ====
        go_count = 0
        go_artifacts = [
            "go_structs", "go_interfaces", "go_functions",
            "go_methods", "go_routes", "go_grpc_services",
            "go_const_blocks", "go_type_aliases"
        ]
        for attr in go_artifacts:
            if hasattr(matrix, attr):
                go_count += len(getattr(matrix, attr, []))

        go_is_significant = (
            go_count >= SIGNIFICANCE_THRESHOLD and
            (python_count == 0 or go_count >= python_count * DOMINANCE_RATIO) and
            (ts_count == 0 or go_count >= ts_count * DOMINANCE_RATIO)
        )
        if go_is_significant:
            context.frameworks.add("golang")

        # Detect Go frameworks from detected_frameworks lists (v5.2)
        if go_is_significant:
            go_fw_mapping = {
                'gin': 'gin',
                'echo': 'echo',
                'fiber': 'fiber',
                'chi': 'chi',
                'grpc-go': 'grpc_go',
                'gorm': 'gorm',
                'gorm_v2': 'gorm',
                'gorm_v1': 'gorm',
                'sqlx': 'sqlx_go',
                'cobra': 'cobra',
            }
            go_fw_attrs = [
                'go_gin_detected_frameworks', 'go_echo_detected_frameworks',
                'go_fiber_detected_frameworks', 'go_chi_detected_frameworks',
                'go_grpc_detected_frameworks', 'go_gorm_detected_frameworks',
                'go_sqlx_detected_frameworks', 'go_cobra_detected_frameworks',
            ]
            for attr in go_fw_attrs:
                for fw in getattr(matrix, attr, []):
                    mapped = go_fw_mapping.get(fw)
                    if mapped:
                        context.frameworks.add(mapped)

        # ==== Java artifact counts (v4.12) ====
        java_count = 0
        java_artifacts = [
            "java_classes", "java_interfaces", "java_records",
            "java_enums", "java_methods", "java_constructors",
            "java_endpoints", "java_entities", "java_repositories",
            "java_grpc_services", "java_message_listeners",
        ]
        for attr in java_artifacts:
            if hasattr(matrix, attr):
                java_count += len(getattr(matrix, attr, []))

        java_is_significant = (
            java_count >= SIGNIFICANCE_THRESHOLD and
            (python_count == 0 or java_count >= python_count * DOMINANCE_RATIO) and
            (ts_count == 0 or java_count >= ts_count * DOMINANCE_RATIO)
        )
        if java_is_significant:
            context.frameworks.add("java")

        # Detect Java frameworks from detected_frameworks list
        java_frameworks = getattr(matrix, 'java_detected_frameworks', [])
        if java_is_significant and java_frameworks:
            java_fw_mapping = {
                'spring_boot': 'spring',
                'spring_mvc': 'spring',
                'spring_webflux': 'spring',
                'spring_data': 'spring',
                'spring_security': 'spring',
                'spring_cloud': 'spring',
                'quarkus': 'quarkus',
                'micronaut': 'micronaut',
                'jpa': 'jpa',
                'hibernate': 'hibernate',
                'junit5': 'junit',
                'junit4': 'junit',
                'kafka': 'kafka',
                'grpc': 'grpc',
            }
            for fw in java_frameworks:
                mapped = java_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # ==== C# artifact counts (v4.13) ====
        csharp_count = 0
        csharp_artifacts = [
            "csharp_classes", "csharp_interfaces", "csharp_structs",
            "csharp_records", "csharp_enums", "csharp_methods",
            "csharp_constructors", "csharp_endpoints", "csharp_entities",
            "csharp_repositories", "csharp_grpc_services", "csharp_signalr_hubs",
            "csharp_db_contexts", "csharp_dtos",
        ]
        for attr in csharp_artifacts:
            if hasattr(matrix, attr):
                csharp_count += len(getattr(matrix, attr, []))

        csharp_is_significant = (
            csharp_count >= SIGNIFICANCE_THRESHOLD and
            (python_count == 0 or csharp_count >= python_count * DOMINANCE_RATIO) and
            (ts_count == 0 or csharp_count >= ts_count * DOMINANCE_RATIO)
        )
        if csharp_is_significant:
            context.frameworks.add("csharp")

        # Detect C# frameworks from detected_frameworks list
        csharp_frameworks = getattr(matrix, 'csharp_detected_frameworks', [])
        if csharp_is_significant and csharp_frameworks:
            csharp_fw_mapping = {
                'aspnet_core': 'aspnet',
                'aspnet_mvc': 'aspnet',
                'blazor': 'blazor',
                'ef_core': 'efcore',
                'signalr': 'signalr',
                'grpc': 'grpc',
                'xunit': 'xunit',
                'nunit': 'nunit',
                'mediatr': 'mediatr',
                'masstransit': 'masstransit',
                'identity': 'identity',
                'serilog': 'serilog',
                'fluentvalidation': 'fluentvalidation',
                'automapper': 'automapper',
                'azure_functions': 'azure_functions',
                'maui': 'maui',
            }
            for fw in csharp_frameworks:
                mapped = csharp_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # ==== Rust artifact counts (v4.14) ====
        rust_count = 0
        rust_artifacts = [
            "rust_structs", "rust_enums", "rust_traits",
            "rust_type_aliases", "rust_impls", "rust_functions",
            "rust_methods", "rust_routes", "rust_grpc_services",
            "rust_graphql_types", "rust_models", "rust_schemas",
        ]
        for attr in rust_artifacts:
            if hasattr(matrix, attr):
                rust_count += len(getattr(matrix, attr, []))

        rust_is_significant = (
            rust_count >= SIGNIFICANCE_THRESHOLD and
            (python_count == 0 or rust_count >= python_count * DOMINANCE_RATIO) and
            (ts_count == 0 or rust_count >= ts_count * DOMINANCE_RATIO)
        )
        if rust_is_significant:
            context.frameworks.add("rust")

        # Detect Rust frameworks from detected_frameworks list
        rust_frameworks = getattr(matrix, 'rust_detected_frameworks', [])
        if rust_is_significant and rust_frameworks:
            rust_fw_mapping = {
                'actix-web': 'actix',
                'rocket': 'rocket',
                'axum': 'axum',
                'warp': 'warp',
                'tide': 'tide',
                'tokio': 'tokio',
                'tonic': 'tonic',
                'diesel': 'diesel',
                'sea-orm': 'sea_orm',
                'sqlx': 'sqlx',
                'serde': 'serde',
                'clap': 'clap',
                'async-graphql': 'async_graphql',
                'tower': 'tower',
                'hyper': 'hyper',
                'tracing': 'tracing',
                'tauri': 'tauri',
            }
            for fw in rust_frameworks:
                mapped = rust_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # v5.4: Detect Rust frameworks from framework-specific detected_frameworks lists
        if rust_is_significant:
            rust_fw_fields = {
                'actix_detected_frameworks': 'actix',
                'axum_detected_frameworks': 'axum',
                'rocket_detected_frameworks': 'rocket',
                'warp_detected_frameworks': 'warp',
                'diesel_detected_frameworks': 'diesel',
                'seaorm_detected_frameworks': 'sea_orm',
                'tauri_detected_frameworks': 'tauri',
            }
            for field, bpl_name in rust_fw_fields.items():
                if getattr(matrix, field, []):
                    context.frameworks.add(bpl_name)

        logger.debug(f"Artifact counts - Python: {python_count}, TS: {ts_count}, Angular: {angular_count}, NestJS: {nestjs_count}, Go: {go_count}, Java: {java_count}, C#: {csharp_count}, Rust: {rust_count}")

        # ==== HTML artifact counts (v4.16) ====
        html_count = 0
        html_artifacts = [
            "html_documents", "html_forms", "html_semantic_elements",
            "html_custom_elements", "html_scripts", "html_styles",
            "html_templates",
        ]
        for attr in html_artifacts:
            if hasattr(matrix, attr):
                html_count += len(getattr(matrix, attr, []))

        html_is_significant = (
            html_count >= SIGNIFICANCE_THRESHOLD
        )
        if html_is_significant:
            context.frameworks.add("html")

        # Detect HTML frameworks from detected_frameworks list
        html_frameworks = getattr(matrix, 'html_detected_frameworks', [])
        if html_is_significant and html_frameworks:
            html_fw_mapping = {
                'bootstrap': 'bootstrap',
                'tailwind': 'tailwind',
                'htmx': 'htmx',
                'alpine.js': 'alpine',
                'stimulus': 'stimulus',
                'turbo': 'turbo',
                'lit': 'lit',
                'jquery': 'jquery',
                'bulma': 'bulma',
                'foundation': 'foundation',
                'materialize': 'materialize',
                'd3': 'd3',
                'three.js': 'threejs',
                'chart.js': 'chartjs',
                'recharts': 'recharts',
                'leaflet': 'leaflet',
                'mapbox-gl': 'mapbox-gl',
            }
            for fw in html_frameworks:
                mapped = html_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect HTML template engines
        html_template_engines = getattr(matrix, 'html_template_engines', [])
        if html_is_significant and html_template_engines:
            tmpl_mapping = {
                'jinja2': 'jinja2',
                'django': 'django',
                'nunjucks': 'nunjucks',
                'ejs': 'ejs',
                'handlebars': 'handlebars',
                'mustache': 'mustache',
                'blade': 'blade',
                'thymeleaf': 'thymeleaf',
                'erb': 'erb',
                'razor': 'razor',
            }
            for engine in html_template_engines:
                mapped = tmpl_mapping.get(engine)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"HTML artifact count: {html_count}")

        # ==== CSS artifact counts (v4.17) ====
        css_count = 0
        css_artifacts = [
            "css_selectors", "css_variables", "css_media_queries",
            "css_keyframes", "css_flexbox", "css_grid",
            "css_mixins", "css_functions",
        ]
        for attr in css_artifacts:
            if hasattr(matrix, attr):
                css_count += len(getattr(matrix, attr, []))

        css_is_significant = (
            css_count >= SIGNIFICANCE_THRESHOLD
        )
        if css_is_significant:
            context.frameworks.add("css")

        # Detect CSS features as sub-frameworks
        css_features = getattr(matrix, 'css_detected_features', [])
        if css_is_significant and css_features:
            css_feat_mapping = {
                'tailwind': 'tailwind',
                'postcss': 'postcss',
                'css_modules': 'css_modules',
                'css_houdini': 'css_houdini',
                'BEM': 'BEM',
                'ITCSS': 'ITCSS',
                'SMACSS': 'SMACSS',
            }
            for feat in css_features:
                mapped = css_feat_mapping.get(feat)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect CSS preprocessors
        css_preprocessors = getattr(matrix, 'css_detected_preprocessors', [])
        if css_is_significant and css_preprocessors:
            for pp in css_preprocessors:
                if pp in ('scss', 'sass'):
                    context.frameworks.add('scss')
                elif pp == 'less':
                    context.frameworks.add('less')
                elif pp == 'stylus':
                    context.frameworks.add('stylus')

        logger.debug(f"CSS artifact count: {css_count}")

        # ==== Sass/SCSS artifact counts (v4.44) ====
        sass_count = 0
        sass_artifacts = [
            "sass_variables", "sass_maps", "sass_lists",
            "sass_mixin_definitions", "sass_mixin_usages",
            "sass_function_definitions", "sass_function_calls",
            "sass_uses", "sass_forwards", "sass_imports",
            "sass_extends", "sass_placeholders", "sass_nesting",
            "sass_at_roots",
        ]
        for attr in sass_artifacts:
            if hasattr(matrix, attr):
                sass_count += len(getattr(matrix, attr, []))

        sass_is_significant = sass_count >= SIGNIFICANCE_THRESHOLD
        if sass_is_significant:
            context.frameworks.add("sass")

        # Detect Sass module system
        sass_module_sys = getattr(matrix, 'sass_module_system', '')
        if sass_is_significant and sass_module_sys:
            if sass_module_sys == 'dart_sass':
                context.frameworks.add('dart_sass')
            elif sass_module_sys == 'legacy':
                context.frameworks.add('sass_legacy')

        # Detect Sass frameworks
        sass_frameworks = getattr(matrix, 'sass_detected_frameworks', [])
        if sass_is_significant and sass_frameworks:
            sass_fw_mapping = {
                'bootstrap': 'bootstrap',
                'foundation': 'foundation',
                'bulma': 'bulma',
                'materialize': 'materialize',
            }
            for fw in sass_frameworks:
                mapped = sass_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect Sass libraries
        sass_libraries = getattr(matrix, 'sass_detected_libraries', [])
        if sass_is_significant and sass_libraries:
            sass_lib_mapping = {
                'bourbon': 'bourbon',
                'compass': 'compass',
                'susy': 'susy',
                'include_media': 'include_media',
                'sass_mq': 'sass_mq',
                'rfs': 'rfs',
            }
            for lib in sass_libraries:
                mapped = sass_lib_mapping.get(lib)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"Sass artifact count: {sass_count}")

        # ==== Less CSS artifact counts (v4.45) ====
        less_count = 0
        less_artifacts = [
            "less_variables", "less_mixin_definitions", "less_mixin_calls",
            "less_guards", "less_namespaces", "less_function_calls",
            "less_plugins", "less_imports", "less_extends",
            "less_detached_rulesets", "less_nesting", "less_property_merges",
        ]
        for attr in less_artifacts:
            if hasattr(matrix, attr):
                less_count += len(getattr(matrix, attr, []))

        less_is_significant = less_count >= SIGNIFICANCE_THRESHOLD
        if less_is_significant:
            context.frameworks.add("less")

        # Detect Less frameworks
        less_frameworks = getattr(matrix, 'less_detected_frameworks', [])
        if less_is_significant and less_frameworks:
            less_fw_mapping = {
                'bootstrap': 'bootstrap',
                'ant_design': 'ant_design',
                'semantic_ui': 'semantic_ui',
                'element_ui': 'element_ui',
                'iview': 'iview',
            }
            for fw in less_frameworks:
                mapped = less_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect Less libraries
        less_libraries = getattr(matrix, 'less_detected_libraries', [])
        if less_is_significant and less_libraries:
            less_lib_mapping = {
                'less_hat': 'less_hat',
                'lesslie': 'lesslie',
                'less_elements': 'less_elements',
                '3l': '3l',
                'preboot': 'preboot',
                'lessmore': 'lessmore',
            }
            for lib in less_libraries:
                mapped = less_lib_mapping.get(lib)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"Less artifact count: {less_count}")

        # ==== PostCSS artifact counts (v4.46) ====
        postcss_count = 0
        postcss_artifacts = [
            "postcss_plugins", "postcss_config", "postcss_transforms",
            "postcss_syntaxes", "postcss_api_usages",
        ]
        for attr in postcss_artifacts:
            if hasattr(matrix, attr):
                postcss_count += len(getattr(matrix, attr, []))

        postcss_is_significant = postcss_count >= SIGNIFICANCE_THRESHOLD
        if postcss_is_significant:
            context.frameworks.add("postcss")

        # Detect PostCSS ecosystem frameworks
        postcss_frameworks = getattr(matrix, 'postcss_detected_frameworks', [])
        if postcss_is_significant and postcss_frameworks:
            postcss_fw_mapping = {
                'vite': 'vite',
                'webpack': 'webpack',
                'next': 'next',
                'nuxt': 'nuxt',
                'gatsby': 'gatsby',
                'remix': 'remix',
                'astro': 'astro',
                'svelte': 'svelte',
                'tailwindcss': 'tailwind',
            }
            for fw in postcss_frameworks:
                mapped = postcss_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect PostCSS tools
        postcss_tools = getattr(matrix, 'postcss_detected_tools', [])
        if postcss_is_significant and postcss_tools:
            postcss_tool_mapping = {
                'stylelint': 'stylelint',
                'postcss_cli': 'postcss_cli',
                'postcss_loader': 'postcss_loader',
                'tailwindcss': 'tailwind',
                'css_modules': 'css_modules',
            }
            for tool in postcss_tools:
                mapped = postcss_tool_mapping.get(tool)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"PostCSS artifact count: {postcss_count}")

        # ==== Tailwind CSS artifact counts (v4.35) ====
        tailwind_count = 0
        tailwind_artifacts = [
            "tailwind_apply_directives", "tailwind_arbitrary_values",
            "tailwind_directives", "tailwind_components", "tailwind_layers",
            "tailwind_config", "tailwind_theme_tokens", "tailwind_colors",
            "tailwind_screens", "tailwind_plugins", "tailwind_custom_utilities",
            "tailwind_custom_variants", "tailwind_v4_features",
        ]
        for attr in tailwind_artifacts:
            if hasattr(matrix, attr):
                tailwind_count += len(getattr(matrix, attr, []))

        tailwind_is_significant = tailwind_count >= SIGNIFICANCE_THRESHOLD
        if tailwind_is_significant:
            context.frameworks.add("tailwind")

        # Detect Tailwind ecosystem frameworks
        tw_frameworks = getattr(matrix, 'tailwind_detected_frameworks', [])
        if tailwind_is_significant and tw_frameworks:
            tw_fw_mapping = {
                'tailwind': 'tailwind',
                'daisyui': 'daisyui',
                'tailwind_ui': 'tailwind_ui',
                'headlessui': 'headlessui',
                'flowbite': 'flowbite',
                'preline': 'preline',
                'nextui': 'nextui',
                'shadcn': 'shadcn',
                'twin_macro': 'twin_macro',
                'radix_tailwind': 'radix_tailwind',
                'tailwind_animate': 'tailwind_animate',
                'tailwind_merge': 'tailwind_merge',
                'tailwind_variants': 'tailwind_variants',
                'cva': 'cva',
            }
            for fw in tw_frameworks:
                mapped = tw_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect Tailwind version
        tw_version = getattr(matrix, 'tailwind_version', '')
        if tw_version:
            context.frameworks.add(f"tailwind_{tw_version}")

        logger.debug(f"Tailwind artifact count: {tailwind_count}")

        # ==== Bash/Shell artifact counts (v4.18) ====
        bash_count = 0
        bash_artifacts = [
            "bash_functions", "bash_variables", "bash_arrays",
            "bash_exports", "bash_aliases", "bash_sources",
            "bash_pipelines", "bash_traps", "bash_heredocs",
            "bash_http_calls", "bash_services",
        ]
        for attr in bash_artifacts:
            if hasattr(matrix, attr):
                bash_count += len(getattr(matrix, attr, []))

        bash_is_significant = (
            bash_count >= SIGNIFICANCE_THRESHOLD
        )
        if bash_is_significant:
            context.frameworks.add("bash")

        # Detect Bash frameworks (docker, kubernetes, terraform, etc.)
        bash_frameworks = getattr(matrix, 'bash_detected_frameworks', [])
        if bash_is_significant and bash_frameworks:
            bash_fw_mapping = {
                'docker': 'docker',
                'kubernetes': 'kubernetes',
                'terraform': 'terraform',
                'ansible': 'ansible',
                'aws_cli': 'aws',
                'gcloud': 'gcloud',
                'azure_cli': 'azure',
                'git': 'git',
                'systemd': 'systemd',
                'ci_cd': 'ci_cd',
                'nginx': 'nginx',
            }
            for fw in bash_frameworks:
                mapped = bash_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect shell types
        bash_shells = getattr(matrix, 'bash_detected_shells', [])
        if bash_is_significant and bash_shells:
            for shell in bash_shells:
                if shell in ('sh', 'dash', 'ash'):
                    context.frameworks.add('posix_shell')
                elif shell == 'zsh':
                    context.frameworks.add('zsh')
                elif shell == 'ksh':
                    context.frameworks.add('ksh')
                elif shell == 'fish':
                    context.frameworks.add('fish')

        logger.debug(f"Bash artifact count: {bash_count}")

        # ==== C artifact counts (v4.19) ====
        c_count = 0
        c_artifacts = [
            "c_structs", "c_unions", "c_enums", "c_typedefs",
            "c_functions", "c_function_pointers", "c_socket_apis",
            "c_signal_handlers", "c_ipc", "c_callbacks",
            "c_data_structures", "c_global_vars", "c_constants",
            "c_macros", "c_includes",
        ]
        for attr in c_artifacts:
            if hasattr(matrix, attr):
                c_count += len(getattr(matrix, attr, []))

        c_is_significant = (
            c_count >= SIGNIFICANCE_THRESHOLD
        )
        if c_is_significant:
            context.frameworks.add("c")

        # Detect C frameworks (posix, openssl, libuv, etc.)
        c_frameworks = getattr(matrix, 'c_detected_frameworks', [])
        if c_is_significant and c_frameworks:
            c_fw_mapping = {
                'posix': 'posix',
                'linux_kernel': 'linux_kernel',
                'pthreads': 'pthreads',
                'openssl': 'openssl',
                'libcurl': 'libcurl',
                'libevent': 'libevent',
                'libuv': 'libuv',
                'sqlite3': 'sqlite3',
                'glib': 'glib',
                'gtk': 'gtk',
                'ncurses': 'ncurses',
                'io_uring': 'io_uring',
                'bpf': 'bpf',
                'mongoose': 'mongoose',
                'libpcap': 'libpcap',
            }
            for fw in c_frameworks:
                mapped = c_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect C standard
        c_standard = getattr(matrix, 'c_c_standard', '')
        if c_is_significant and c_standard:
            context.frameworks.add(c_standard)  # e.g. 'c99', 'c11'

        logger.debug(f"C artifact count: {c_count}")

        # ==== C++ artifact counts (v4.20) ====
        cpp_count = 0
        cpp_artifacts = [
            "cpp_classes", "cpp_unions", "cpp_enums", "cpp_type_aliases",
            "cpp_concepts", "cpp_namespaces", "cpp_methods", "cpp_lambdas",
            "cpp_endpoints", "cpp_grpc_services", "cpp_signals_slots",
            "cpp_callbacks", "cpp_networking", "cpp_ipc",
            "cpp_containers", "cpp_smart_pointers", "cpp_raii",
            "cpp_global_vars", "cpp_constants", "cpp_design_patterns",
            "cpp_macros", "cpp_includes", "cpp_modules",
        ]
        for attr in cpp_artifacts:
            if hasattr(matrix, attr):
                cpp_count += len(getattr(matrix, attr, []))

        cpp_is_significant = (
            cpp_count >= SIGNIFICANCE_THRESHOLD
        )
        if cpp_is_significant:
            context.frameworks.add("cpp")

        # Detect C++ frameworks
        cpp_frameworks = getattr(matrix, 'cpp_detected_frameworks', [])
        if cpp_is_significant and cpp_frameworks:
            cpp_fw_mapping = {
                'stl': 'stl',
                'boost': 'boost',
                'boost_asio': 'boost_asio',
                'boost_beast': 'boost_beast',
                'boost_spirit': 'boost_spirit',
                'qt': 'qt',
                'qml': 'qml',
                'poco': 'poco',
                'grpc': 'grpc',
                'protobuf': 'protobuf',
                'crow': 'crow',
                'pistache': 'pistache',
                'httplib': 'httplib',
                'drogon': 'drogon',
                'nlohmann_json': 'nlohmann_json',
                'rapidjson': 'rapidjson',
                'opencv': 'opencv',
                'eigen': 'eigen',
                'spdlog': 'spdlog',
                'fmt': 'fmt',
                'gtest': 'gtest',
                'catch2': 'catch2',
                'doctest': 'doctest',
                'llvm': 'llvm',
                'clang': 'clang',
                'abseil': 'abseil',
                'folly': 'folly',
                'pybind11': 'pybind11',
                'vulkan': 'vulkan',
                'opengl': 'opengl',
                'cuda': 'cuda',
                'tbb': 'tbb',
                'openmp': 'openmp',
                'ros': 'ros',
                'ros2': 'ros2',
                'unreal': 'unreal',
                'wxwidgets': 'wxwidgets',
                'sfml': 'sfml',
                'sqlite': 'sqlite',
                'libcurl': 'libcurl',
            }
            for fw in cpp_frameworks:
                mapped = cpp_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect C++ standard
        cpp_standard = getattr(matrix, 'cpp_cpp_standard', '')
        if cpp_is_significant and cpp_standard:
            context.frameworks.add(cpp_standard)  # e.g. 'c++17', 'c++20'

        logger.debug(f"C++ artifact count: {cpp_count}")

        # ==== Kotlin artifact counts (v4.21) ====
        kotlin_count = 0
        kotlin_artifacts = [
            "kotlin_classes", "kotlin_objects", "kotlin_interfaces",
            "kotlin_enums", "kotlin_functions", "kotlin_endpoints",
            "kotlin_entities", "kotlin_repositories", "kotlin_exposed_tables",
            "kotlin_serializables", "kotlin_dtos", "kotlin_annotation_defs",
            "kotlin_annotation_usages", "kotlin_delegations", "kotlin_di_bindings",
            "kotlin_multiplatform_decls", "kotlin_context_receivers",
            "kotlin_contracts", "kotlin_websockets", "kotlin_grpc_services",
            "kotlin_graphql", "kotlin_dsl_markers", "kotlin_type_aliases",
        ]
        for attr in kotlin_artifacts:
            if hasattr(matrix, attr):
                kotlin_count += len(getattr(matrix, attr, []))

        kotlin_is_significant = (
            kotlin_count >= SIGNIFICANCE_THRESHOLD and
            (python_count == 0 or kotlin_count >= python_count * DOMINANCE_RATIO) and
            (ts_count == 0 or kotlin_count >= ts_count * DOMINANCE_RATIO)
        )
        if kotlin_is_significant:
            context.frameworks.add("kotlin")

        # Detect Kotlin frameworks from detected_frameworks list
        kotlin_frameworks = getattr(matrix, 'kotlin_detected_frameworks', [])
        if kotlin_is_significant and kotlin_frameworks:
            kotlin_fw_mapping = {
                'spring_boot': 'spring',
                'spring_mvc': 'spring',
                'spring_webflux': 'spring',
                'spring_data': 'spring',
                'spring_security': 'spring',
                'ktor_server': 'ktor',
                'ktor_client': 'ktor',
                'ktor': 'ktor',
                'compose': 'compose',
                'compose_multiplatform': 'compose',
                'koin': 'koin',
                'dagger': 'dagger',
                'hilt': 'hilt',
                'room': 'room',
                'exposed': 'exposed',
                'kotlinx_serialization': 'kotlinx_serialization',
                'kotlinx_coroutines': 'kotlinx_coroutines',
                'arrow': 'arrow',
                'kmm': 'kmm',
                'retrofit': 'retrofit',
                'okhttp': 'okhttp',
                'grpc': 'grpc',
                'graphql': 'graphql',
                'kotest': 'kotest',
                'mockk': 'mockk',
                'junit5': 'junit',
            }
            for fw in kotlin_frameworks:
                mapped = kotlin_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect Kotlin multiplatform
        kotlin_features = getattr(matrix, 'kotlin_features', [])
        if kotlin_is_significant and 'multiplatform' in kotlin_features:
            context.frameworks.add("kmm")

        logger.debug(f"Kotlin artifact count: {kotlin_count}")

        # ==== Swift artifact counts (v4.22) ====
        swift_count = 0
        swift_artifacts = [
            "swift_classes", "swift_structs", "swift_enums",
            "swift_protocols", "swift_actors", "swift_extensions",
            "swift_functions", "swift_inits", "swift_routes",
            "swift_views", "swift_publishers", "swift_grpc_services",
            "swift_models", "swift_codables", "swift_property_wrappers",
            "swift_macros", "swift_concurrency",
        ]
        for attr in swift_artifacts:
            if hasattr(matrix, attr):
                swift_count += len(getattr(matrix, attr, []))

        swift_is_significant = (
            swift_count >= SIGNIFICANCE_THRESHOLD
        )
        if swift_is_significant:
            context.frameworks.add("swift")

        # Detect Swift frameworks from detected_frameworks list
        swift_frameworks = getattr(matrix, 'swift_detected_frameworks', [])
        if swift_is_significant and swift_frameworks:
            swift_fw_mapping = {
                'swiftui': 'swiftui',
                'uikit': 'uikit',
                'appkit': 'appkit',
                'combine': 'combine',
                'core_data': 'core_data',
                'swift_data': 'swift_data',
                'vapor': 'vapor',
                'hummingbird': 'hummingbird',
                'kitura': 'kitura',
                'perfect': 'perfect',
                'swiftnio': 'swiftnio',
                'fluent': 'fluent',
                'alamofire': 'alamofire',
                'grdb': 'grdb',
                'realm': 'realm',
                'xctest': 'xctest',
                'swift_testing': 'swift_testing',
                'quick_nimble': 'quick_nimble',
                'tca': 'tca',
                'rxswift': 'rxswift',
                'swinject': 'swinject',
                'arkit': 'arkit',
                'realitykit': 'realitykit',
                'coreml': 'coreml',
                'cloudkit': 'cloudkit',
                'storekit': 'storekit',
                'widgetkit': 'widgetkit',
                'grpc_swift': 'grpc_swift',
            }
            for fw in swift_frameworks:
                mapped = swift_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"Swift artifact count: {swift_count}")

        # ==== Ruby artifact counts (v4.23) ====
        ruby_count = 0
        ruby_artifacts = [
            "ruby_classes", "ruby_modules", "ruby_structs",
            "ruby_methods", "ruby_accessors", "ruby_routes",
            "ruby_controllers", "ruby_grpc_services", "ruby_graphql_types",
            "ruby_channels", "ruby_models", "ruby_migrations",
            "ruby_concerns", "ruby_workers", "ruby_rake_tasks",
            "ruby_callbacks", "ruby_metaprogramming",
        ]
        for attr in ruby_artifacts:
            if hasattr(matrix, attr):
                ruby_count += len(getattr(matrix, attr, []))

        ruby_is_significant = (
            ruby_count >= SIGNIFICANCE_THRESHOLD
        )
        if ruby_is_significant:
            context.frameworks.add("ruby")

        # Detect Ruby frameworks from detected_frameworks list
        ruby_frameworks = getattr(matrix, 'ruby_detected_frameworks', [])
        if ruby_is_significant and ruby_frameworks:
            ruby_fw_mapping = {
                'rails': 'rails',
                'sinatra': 'sinatra',
                'grape': 'grape',
                'hanami': 'hanami',
                'roda': 'roda',
                'padrino': 'padrino',
                'activerecord': 'activerecord',
                'sequel': 'sequel',
                'mongoid': 'mongoid',
                'rom': 'rom',
                'graphql-ruby': 'graphql',
                'grpc': 'grpc',
                'sidekiq': 'sidekiq',
                'resque': 'resque',
                'delayed_job': 'delayed_job',
                'activejob': 'activejob',
                'rspec': 'rspec',
                'minitest': 'minitest',
                'devise': 'devise',
                'pundit': 'pundit',
                'cancancan': 'cancancan',
                'sorbet': 'sorbet',
                'dry-rb': 'dry_rb',
                'turbo': 'turbo',
                'hotwire': 'hotwire',
                'stimulus': 'stimulus',
                'view_component': 'view_component',
                'action_cable': 'action_cable',
                'factory_bot': 'factory_bot',
            }
            for fw in ruby_frameworks:
                mapped = ruby_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"Ruby artifact count: {ruby_count}")

        # ==== PHP artifact counts (v4.24) ====
        php_count = 0
        php_artifacts = [
            "php_classes", "php_interfaces", "php_traits", "php_enums",
            "php_abstract_classes", "php_functions", "php_methods",
            "php_closures", "php_routes", "php_controllers",
            "php_middleware", "php_grpc_services", "php_graphql_types",
            "php_models", "php_migrations", "php_repositories",
            "php_attributes_php8", "php_annotations",
            "php_di_bindings", "php_event_listeners",
        ]
        for attr in php_artifacts:
            if hasattr(matrix, attr):
                php_count += len(getattr(matrix, attr, []))

        php_is_significant = (
            php_count >= SIGNIFICANCE_THRESHOLD
        )
        if php_is_significant:
            context.frameworks.add("php")

        # Detect PHP frameworks from detected_frameworks list
        php_frameworks = getattr(matrix, 'php_detected_frameworks', [])
        if php_is_significant and php_frameworks:
            php_fw_mapping = {
                'laravel': 'laravel',
                'symfony': 'symfony',
                'codeigniter': 'codeigniter',
                'slim': 'slim',
                'cakephp': 'cakephp',
                'lumen': 'lumen',
                'yii': 'yii',
                'phalcon': 'phalcon',
                'wordpress': 'wordpress',
                'drupal': 'drupal',
                'magento': 'magento',
                'doctrine': 'doctrine',
                'eloquent': 'eloquent',
                'phpunit': 'phpunit',
                'pest': 'pest',
                'livewire': 'livewire',
                'inertia': 'inertia',
                'filament': 'filament',
                'nova': 'nova',
                'sanctum': 'sanctum',
                'passport': 'passport',
                'jetstream': 'jetstream',
                'breeze': 'breeze',
                'horizon': 'horizon',
                'vapor': 'vapor',
                'octane': 'octane',
                'telescope': 'telescope',
                'dusk': 'dusk',
                'spatie': 'spatie',
                'api-platform': 'api_platform',
            }
            for fw in php_frameworks:
                mapped = php_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # v5.3: Also detect frameworks from framework-specific detected lists
        for fw_prefix, fw_name in [
            ('laravel', 'laravel'), ('symfony', 'symfony'),
            ('codeigniter', 'codeigniter'), ('slim', 'slim'),
            ('wordpress', 'wordpress'),
        ]:
            fw_detected = getattr(matrix, f'{fw_prefix}_detected_frameworks', [])
            if fw_detected:
                context.frameworks.add(fw_name)
                for fw in fw_detected:
                    mapped = php_fw_mapping.get(fw)
                    if mapped:
                        context.frameworks.add(mapped)

        logger.debug(f"PHP artifact count: {php_count}")

        # ==== Scala artifact counts (v4.25) ====
        scala_count = 0
        scala_artifacts = [
            "scala_classes", "scala_traits", "scala_objects",
            "scala_case_classes", "scala_enums", "scala_type_aliases",
            "scala_givens", "scala_methods", "scala_extension_methods",
            "scala_routes", "scala_controllers", "scala_grpc_services",
            "scala_graphql_types", "scala_models", "scala_migrations",
            "scala_codecs", "scala_annotations", "scala_implicits",
            "scala_macros",
        ]
        for attr in scala_artifacts:
            if hasattr(matrix, attr):
                scala_count += len(getattr(matrix, attr, []))

        scala_is_significant = (
            scala_count >= SIGNIFICANCE_THRESHOLD
        )
        if scala_is_significant:
            context.frameworks.add("scala")

        # Detect Scala frameworks from detected_frameworks list
        scala_frameworks = getattr(matrix, 'scala_detected_frameworks', [])
        if scala_is_significant and scala_frameworks:
            scala_fw_mapping = {
                'play': 'play',
                'akka': 'akka',
                'akka-http': 'akka_http',
                'pekko': 'pekko',
                'http4s': 'http4s',
                'zio': 'zio',
                'zio-http': 'zio_http',
                'cats': 'cats',
                'cats-effect': 'cats_effect',
                'fs2': 'fs2',
                'tapir': 'tapir',
                'circe': 'circe',
                'doobie': 'doobie',
                'skunk': 'skunk',
                'slick': 'slick',
                'quill': 'quill',
                'scalikejdbc': 'scalikejdbc',
                'spark': 'spark',
                'flink': 'flink',
                'finch': 'finch',
                'scalatra': 'scalatra',
                'sangria': 'sangria',
                'caliban': 'caliban',
                'scalatest': 'scalatest',
                'munit': 'munit',
                'specs2': 'specs2',
                'scalacheck': 'scalacheck',
                'monix': 'monix',
            }
            for fw in scala_frameworks:
                mapped = scala_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"Scala artifact count: {scala_count}")

        # ==== R artifact counts (v4.26) ====
        r_count = 0
        r_artifacts = [
            "r_classes", "r_generics", "r_s4_methods", "r_environments",
            "r_functions", "r_pipe_chains", "r_routes",
            "r_shiny_components", "r_api_endpoints",
            "r_data_models", "r_db_connections", "r_db_queries",
            "r_data_pipelines", "r_exports", "r_lifecycle_hooks",
        ]
        for attr in r_artifacts:
            if hasattr(matrix, attr):
                r_count += len(getattr(matrix, attr, []))

        r_is_significant = (
            r_count >= SIGNIFICANCE_THRESHOLD
        )
        if r_is_significant:
            context.frameworks.add("rlang")

        # Detect R frameworks from detected_frameworks list
        r_frameworks = getattr(matrix, 'r_detected_frameworks', [])
        if r_is_significant and r_frameworks:
            r_fw_mapping = {
                'shiny': 'shiny',
                'plumber': 'plumber',
                'golem': 'golem',
                'rhino': 'rhino',
                'restrserve': 'restrserve',
                'ambiorix': 'ambiorix',
                'tidyverse': 'tidyverse',
                'dplyr': 'tidyverse',
                'ggplot2': 'ggplot2',
                'data.table': 'data_table',
                'R6': 'r6',
                'R7': 'r7',
                'Rcpp': 'rcpp',
                'DBI': 'dbi',
                'dbplyr': 'dbplyr',
                'sparklyr': 'sparklyr',
                'arrow': 'arrow',
                'tidymodels': 'tidymodels',
                'caret': 'caret',
                'mlr3': 'mlr3',
                'testthat': 'testthat',
                'targets': 'targets',
                'rmarkdown': 'rmarkdown',
                'quarto': 'quarto',
                'reticulate': 'reticulate',
                'sf': 'sf',
                'terra': 'terra',
                'bioconductor': 'bioconductor',
                'renv': 'renv',
                'devtools': 'devtools',
                'roxygen2': 'roxygen2',
                'future': 'future',
                'torch': 'torch',
                'tensorflow': 'tensorflow',
                'brms': 'brms',
                'rstan': 'rstan',
            }
            for fw in r_frameworks:
                mapped = r_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"R artifact count: {r_count}")

        # ==== Dart artifact counts (v4.27) ====
        dart_count = 0
        dart_artifacts = [
            "dart_classes", "dart_mixins", "dart_enums",
            "dart_extensions", "dart_extension_types", "dart_typedefs",
            "dart_functions", "dart_constructors",
            "dart_getters", "dart_setters", "dart_exports",
            "dart_widgets", "dart_routes", "dart_state_managers",
            "dart_grpc_services", "dart_flutter_routes",
            "dart_models", "dart_data_classes", "dart_migrations",
            "dart_annotations", "dart_isolates", "dart_platform_channels",
        ]
        for attr in dart_artifacts:
            if hasattr(matrix, attr):
                dart_count += len(getattr(matrix, attr, []))

        dart_is_significant = (
            dart_count >= SIGNIFICANCE_THRESHOLD
        )
        if dart_is_significant:
            context.frameworks.add("dart")

        # Detect if Flutter project
        if getattr(matrix, 'dart_is_flutter', False) and dart_is_significant:
            context.frameworks.add("flutter")

        # Detect Dart frameworks from detected_frameworks list
        dart_frameworks = getattr(matrix, 'dart_detected_frameworks', [])
        if dart_is_significant and dart_frameworks:
            dart_fw_mapping = {
                'flutter': 'flutter',
                'flutter_material': 'flutter',
                'flutter_cupertino': 'flutter',
                'riverpod': 'riverpod',
                'bloc': 'bloc',
                'getx': 'getx',
                'provider': 'provider',
                'mobx': 'mobx',
                'redux': 'redux',
                'dio': 'dio',
                'drift': 'drift',
                'floor': 'floor',
                'isar': 'isar',
                'hive': 'hive',
                'objectbox': 'objectbox',
                'freezed': 'freezed',
                'json_serializable': 'json_serializable',
                'get_it': 'get_it',
                'injectable': 'injectable',
                'go_router': 'go_router',
                'auto_route': 'auto_route',
                'shelf': 'shelf',
                'dart_frog': 'dart_frog',
                'serverpod': 'serverpod',
                'conduit': 'conduit',
                'grpc': 'grpc',
                'firebase_core': 'firebase',
                'cloud_firestore': 'firebase',
                'firebase_auth': 'firebase',
                'supabase': 'supabase',
                'flutter_test': 'flutter_test',
                'mockito': 'mockito',
                'bloc_test': 'bloc_test',
                'patrol': 'patrol',
            }
            for fw in dart_frameworks:
                mapped = dart_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"Dart artifact count: {dart_count}")

        # ==== Lua artifact counts (v4.28) ====
        lua_count = 0
        lua_artifacts = [
            "lua_functions", "lua_tables", "lua_classes",
            "lua_modules", "lua_metatables", "lua_coroutines",
            "lua_routes", "lua_middleware",
        ]
        for attr in lua_artifacts:
            if hasattr(matrix, attr):
                lua_count += len(getattr(matrix, attr, []))

        lua_is_significant = lua_count >= SIGNIFICANCE_THRESHOLD
        if lua_is_significant:
            context.frameworks.add("lua")

        # Detect Lua frameworks from detected_frameworks list
        lua_frameworks = getattr(matrix, 'lua_detected_frameworks', [])
        if lua_is_significant and lua_frameworks:
            lua_fw_mapping = {
                'love2d': 'love2d', 'openresty': 'openresty',
                'lapis': 'lapis', 'tarantool': 'tarantool',
                'corona': 'corona', 'solar2d': 'solar2d',
                'defold': 'defold', 'busted': 'busted',
            }
            for fw in lua_frameworks:
                mapped = lua_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"Lua artifact count: {lua_count}")

        # ==== PowerShell artifact counts (v4.29) ====
        ps_count = 0
        ps_artifacts = [
            "ps_classes", "ps_enums", "ps_interfaces", "ps_dsc_resources",
            "ps_functions", "ps_script_blocks", "ps_pipelines",
            "ps_routes", "ps_cmdlet_bindings", "ps_dsc_configs",
            "ps_pester_tests", "ps_module_manifests", "ps_data_models",
            "ps_registry_ops", "ps_dsc_nodes",
            "ps_imports", "ps_usings", "ps_requires", "ps_dot_sources",
        ]
        for attr in ps_artifacts:
            if hasattr(matrix, attr):
                ps_count += len(getattr(matrix, attr, []))

        ps_is_significant = ps_count >= SIGNIFICANCE_THRESHOLD
        if ps_is_significant:
            context.frameworks.add("powershell")

        # Detect PowerShell frameworks from detected_frameworks list
        ps_frameworks = getattr(matrix, 'ps_detected_frameworks', [])
        if ps_is_significant and ps_frameworks:
            ps_fw_mapping = {
                'pode': 'pode', 'polaris': 'polaris',
                'universaldashboard': 'universaldashboard',
                'pester': 'pester', 'dsc': 'dsc',
                'azure': 'azure', 'azuread': 'azuread',
                'aws': 'aws', 'gcp': 'gcp',
                'msgraph': 'msgraph', 'exchange': 'exchange',
                'activedirectory': 'activedirectory',
                'psake': 'psake', 'invokebuild': 'invokebuild',
                'plaster': 'plaster', 'psgallery': 'psgallery',
                'secretmanagement': 'secretmanagement',
                'dbatools': 'dbatools', 'sqlserver': 'sqlserver',
                'psframework': 'psframework',
            }
            for fw in ps_frameworks:
                mapped = ps_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"PowerShell artifact count: {ps_count}")

        # ==== JavaScript artifact counts (v4.30) ====
        js_count = 0
        js_artifacts = [
            "js_classes", "js_prototypes", "js_constants", "js_symbols",
            "js_functions", "js_arrow_functions", "js_generators",
            "js_routes", "js_middleware", "js_websockets", "js_graphql_resolvers",
            "js_models", "js_migrations", "js_relationships",
            "js_imports", "js_exports", "js_jsdoc", "js_decorators",
            "js_dynamic_imports",
        ]
        for attr in js_artifacts:
            if hasattr(matrix, attr):
                js_count += len(getattr(matrix, attr, []))

        js_is_significant = js_count >= SIGNIFICANCE_THRESHOLD
        if js_is_significant:
            context.frameworks.add("javascript")

        # Detect JavaScript frameworks from detected_frameworks list
        js_frameworks = getattr(matrix, 'js_detected_frameworks', [])
        if js_is_significant and js_frameworks:
            js_fw_mapping = {
                'express': 'express', 'fastify': 'fastify',
                'koa': 'koa', 'hapi': 'hapi',
                'restify': 'restify', 'polka': 'polka',
                'micro': 'micro',
                'react': 'react', 'vue': 'vue',
                'svelte': 'svelte', 'preact': 'preact',
                'solid': 'solid', 'lit': 'lit',
                'nextjs': 'nextjs', 'nuxt': 'nuxt',
                'gatsby': 'gatsby', 'remix': 'remix',
                'astro': 'astro',
                'jest': 'jest', 'mocha': 'mocha',
                'vitest': 'vitest', 'jasmine': 'jasmine',
                'ava': 'ava', 'cypress': 'cypress',
                'playwright': 'playwright',
                'mongoose': 'mongoose', 'sequelize': 'sequelize',
                'prisma': 'prisma', 'knex': 'knex',
                'typeorm': 'typeorm', 'objection': 'objection',
                'drizzle': 'drizzle',
                'passport': 'passport', 'jsonwebtoken': 'jsonwebtoken',
                'auth0': 'auth0',
                'socketio': 'socketio', 'ws': 'ws',
                'apollo': 'apollo', 'graphql_yoga': 'graphql_yoga',
                'mercurius': 'mercurius',
                'joi': 'joi', 'zod': 'zod', 'yup': 'yup',
                'bull': 'bull', 'bullmq': 'bullmq', 'agenda': 'agenda',
                'winston': 'winston', 'pino': 'pino', 'bunyan': 'bunyan',
                'redux': 'redux', 'mobx': 'mobx',
                'zustand': 'zustand', 'jotai': 'jotai', 'recoil': 'recoil',
                'webpack': 'webpack', 'vite': 'vite',
                'rollup': 'rollup', 'esbuild': 'esbuild',
                'electron': 'electron', 'pm2': 'pm2',
            }
            for fw in js_frameworks:
                mapped = js_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"JavaScript artifact count: {js_count}")

        # ==== TypeScript artifact counts (v4.31) ====
        ts_count = 0
        ts_artifacts = [
            "ts_classes", "ts_interfaces", "ts_type_aliases", "ts_enums",
            "ts_functions", "ts_overloads",
            "ts_routes", "ts_middleware", "ts_websockets", "ts_graphql_resolvers",
            "ts_trpc_routers",
            "ts_models", "ts_migrations", "ts_relationships", "ts_dtos",
            "ts_imports", "ts_exports", "ts_decorators", "ts_namespaces",
            "ts_triple_slash_directives", "ts_tsdoc",
        ]
        for attr in ts_artifacts:
            if hasattr(matrix, attr):
                ts_count += len(getattr(matrix, attr, []))

        ts_is_significant = ts_count >= SIGNIFICANCE_THRESHOLD
        if ts_is_significant:
            context.frameworks.add("typescript")

        # Detect TypeScript frameworks from detected_frameworks list
        ts_frameworks = getattr(matrix, 'ts_detected_frameworks', [])
        if ts_is_significant and ts_frameworks:
            ts_fw_mapping = {
                'nestjs': 'nestjs', 'angular': 'angular',
                'express': 'express', 'fastify': 'fastify',
                'koa': 'koa', 'hapi': 'hapi', 'hono': 'hono',
                'react': 'react', 'vue': 'vue',
                'svelte': 'svelte', 'solid': 'solid',
                'lit': 'lit', 'qwik': 'qwik', 'preact': 'preact',
                'nextjs': 'nextjs', 'nuxt': 'nuxt',
                'remix': 'remix', 'astro': 'astro',
                'sveltekit': 'sveltekit', 'analog': 'analog',
                'trpc': 'trpc',
                'graphql_typegraphql': 'type-graphql',
                'apollo': 'apollo', 'pothos': 'pothos',
                'grpc': 'grpc',
                'typeorm': 'typeorm', 'mikroorm': 'mikroorm',
                'prisma': 'prisma', 'drizzle': 'drizzle',
                'sequelize_ts': 'sequelize', 'kysely': 'kysely',
                'mongoose_ts': 'mongoose',
                'zod': 'zod', 'class_validator': 'class-validator',
                'io_ts': 'io-ts', 'arktype': 'arktype', 'valibot': 'valibot',
                'jest': 'jest', 'vitest': 'vitest',
                'playwright': 'playwright', 'cypress': 'cypress',
                'testing_library': 'testing-library',
                'ngrx': 'ngrx', 'redux_toolkit': 'redux-toolkit',
                'zustand': 'zustand', 'jotai': 'jotai',
                'mobx': 'mobx', 'pinia': 'pinia',
                'tanstack_query': 'tanstack-query',
                'swr': 'swr',
                'passport': 'passport', 'nextauth': 'nextauth',
                'lucia': 'lucia',
                'socketio': 'socketio', 'ws': 'ws',
                'inversify': 'inversify', 'tsyringe': 'tsyringe',
                'rxjs': 'rxjs', 'fp_ts': 'fp-ts', 'effect': 'effect',
                'webpack': 'webpack', 'vite': 'vite',
                'esbuild': 'esbuild', 'swc': 'swc',
                'electron': 'electron', 'tauri': 'tauri',
                'nx': 'nx', 'turborepo': 'turborepo',
            }
            for fw in ts_frameworks:
                mapped = ts_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"TypeScript artifact count: {ts_count}")

        # ==== React artifact counts (v4.32) ====
        react_count = 0
        react_artifacts = [
            "react_components", "react_hocs", "react_forward_refs",
            "react_memos", "react_lazy_components", "react_error_boundaries",
            "react_providers", "react_hook_usages", "react_custom_hooks",
            "react_hook_dependencies", "react_contexts", "react_context_consumers",
            "react_stores", "react_slices", "react_atoms", "react_queries",
            "react_routes", "react_layouts", "react_pages",
        ]
        for attr in react_artifacts:
            if hasattr(matrix, attr):
                react_count += len(getattr(matrix, attr, []))

        if react_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("react")

        # Detect React ecosystem frameworks from detected_frameworks list
        react_frameworks = getattr(matrix, 'react_detected_frameworks', [])
        if react_count >= SIGNIFICANCE_THRESHOLD and react_frameworks:
            react_fw_mapping = {
                'react': 'react', 'react-dom': 'react',
                'react-native': 'react-native',
                'nextjs': 'nextjs', 'remix': 'remix',
                'gatsby': 'gatsby', 'expo': 'expo',
                'material-ui': 'material-ui', 'chakra-ui': 'chakra-ui',
                'ant-design': 'ant-design', 'mantine': 'mantine',
                'shadcn-ui': 'shadcn-ui', 'radix-ui': 'radix-ui',
                'headless-ui': 'headless-ui',
                'react-hook-form': 'react-hook-form',
                'formik': 'formik', 'final-form': 'final-form',
                'framer-motion': 'framer-motion',
                'react-spring': 'react-spring',
                'tanstack-query': 'tanstack-query',
                'swr': 'swr', 'apollo-client': 'apollo',
                'urql': 'urql', 'relay': 'relay',
                'redux': 'redux', 'zustand': 'zustand',
                'jotai': 'jotai', 'recoil': 'recoil',
                'mobx-react': 'mobx', 'valtio': 'valtio',
                'xstate-react': 'xstate',
                'react-router': 'react-router',
                'tanstack-router': 'tanstack-router',
                'testing-library': 'testing-library',
                'enzyme': 'enzyme',
                'styled-components': 'styled-components',
                'emotion': 'emotion',
                'tailwind-react': 'tailwind',
                'css-modules': 'css-modules',
                'recharts': 'recharts', 'victory': 'victory',
                'nivo': 'nivo', 'visx': 'visx',
                'leaflet': 'leaflet', 'react-leaflet': 'react-leaflet',
                'mapbox-gl': 'mapbox-gl', 'react-map-gl': 'react-map-gl',
                'react-helmet': 'react-helmet',
                'react-i18next': 'react-i18next',
                'react-dnd': 'react-dnd',
                'react-window': 'react-window',
            }
            for fw in react_frameworks:
                mapped = react_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"React artifact count: {react_count}")

        # ==== Material UI (MUI) artifact counts (v4.36) ====
        mui_count = 0
        mui_artifacts = [
            "mui_components", "mui_custom_components", "mui_slots",
            "mui_themes", "mui_palettes", "mui_typography_configs",
            "mui_breakpoints", "mui_component_overrides",
            "mui_hook_usages", "mui_custom_hooks",
            "mui_sx_usages", "mui_styled_components", "mui_make_styles",
            "mui_data_grids", "mui_forms", "mui_dialogs", "mui_navigations",
        ]
        for attr in mui_artifacts:
            if hasattr(matrix, attr):
                mui_count += len(getattr(matrix, attr, []))

        if mui_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("mui")

        # Detect MUI ecosystem frameworks from detected_frameworks list
        mui_frameworks = getattr(matrix, 'mui_detected_frameworks', [])
        if mui_count >= SIGNIFICANCE_THRESHOLD and mui_frameworks:
            mui_fw_mapping = {
                'mui-material': 'mui', 'mui-system': 'mui',
                'mui-base': 'mui-base', 'mui-joy': 'mui-joy',
                'mui-x-data-grid': 'mui-x-data-grid',
                'mui-x-date-pickers': 'mui-x-date-pickers',
                'mui-x-tree-view': 'mui-x-tree-view',
                'mui-x-charts': 'mui-x-charts',
                'mui-icons': 'mui-icons',
                'mui-lab': 'mui-lab',
                'emotion-react': 'emotion',
                'tss-react': 'tss-react',
                'pigment-css': 'pigment-css',
                'material-ui-core': 'material-ui',
                'material-ui-styles': 'material-ui',
                'notistack': 'notistack',
                'mui-datatables': 'mui-datatables',
            }
            for fw in mui_frameworks:
                mapped = mui_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"MUI artifact count: {mui_count}")

        # ==== Ant Design artifact counts (v4.37) ====
        antd_count = 0
        antd_artifacts = [
            "antd_components", "antd_custom_components", "antd_pro_components",
            "antd_themes", "antd_tokens", "antd_less_variables",
            "antd_component_tokens",
            "antd_hook_usages", "antd_custom_hooks",
            "antd_css_in_js", "antd_less_styles", "antd_style_overrides",
            "antd_tables", "antd_forms", "antd_modals", "antd_menus",
        ]
        for attr in antd_artifacts:
            if hasattr(matrix, attr):
                antd_count += len(getattr(matrix, attr, []))

        if antd_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("antd")

        # Detect Ant Design ecosystem frameworks from detected_frameworks list
        antd_frameworks = getattr(matrix, 'antd_detected_frameworks', [])
        if antd_count >= SIGNIFICANCE_THRESHOLD and antd_frameworks:
            antd_fw_mapping = {
                'antd': 'antd',
                'antd-icons': 'antd-icons',
                'antd-cssinjs': 'antd-cssinjs',
                'antd-pro-components': 'antd-pro',
                'antd-pro-table': 'antd-pro',
                'antd-pro-form': 'antd-pro',
                'antd-pro-layout': 'antd-pro',
                'antd-charts': 'antd-charts',
                'antd-plots': 'antd-plots',
                'antd-mobile': 'antd-mobile',
                'antd-style': 'antd-style',
                'antd-compatible': 'antd-compat',
                'umi': 'umi',
                'dumi': 'dumi',
                'ahooks': 'ahooks',
            }
            for fw in antd_frameworks:
                mapped = antd_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"Ant Design artifact count: {antd_count}")

        # ==== Chakra UI artifact counts (v4.38) ====
        chakra_count = 0
        chakra_artifacts = [
            "chakra_components", "chakra_custom_components",
            "chakra_themes", "chakra_tokens", "chakra_semantic_tokens",
            "chakra_component_styles",
            "chakra_hook_usages", "chakra_custom_hooks",
            "chakra_style_props", "chakra_sx_usages", "chakra_responsive_patterns",
            "chakra_forms", "chakra_modals", "chakra_toasts", "chakra_menus",
        ]
        for attr in chakra_artifacts:
            if hasattr(matrix, attr):
                chakra_count += len(getattr(matrix, attr, []))

        if chakra_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("chakra-ui")

        # Detect Chakra UI ecosystem frameworks from detected_frameworks list
        chakra_frameworks = getattr(matrix, 'chakra_detected_frameworks', [])
        if chakra_count >= SIGNIFICANCE_THRESHOLD and chakra_frameworks:
            chakra_fw_mapping = {
                'chakra-ui': 'chakra-ui',
                'chakra-icons': 'chakra-icons',
                'chakra-theme-tools': 'chakra-theme-tools',
                'chakra-pro-theme': 'chakra-pro',
                'saas-ui': 'saas-ui',
                'ark-ui': 'ark-ui',
                'panda-css': 'panda-css',
                'framer-motion': 'framer-motion',
                'emotion-react': 'emotion',
                'emotion-styled': 'emotion',
                'chakra-react-select': 'chakra-react-select',
                'react-hook-form': 'react-hook-form',
                'formik': 'formik',
            }
            for fw in chakra_frameworks:
                mapped = chakra_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"Chakra UI artifact count: {chakra_count}")

        # ==== shadcn/ui artifact counts (v4.39) ====
        shadcn_count = 0
        shadcn_artifacts = [
            "shadcn_components", "shadcn_registry_components",
            "shadcn_themes", "shadcn_css_variables",
            "shadcn_hook_usages", "shadcn_custom_hooks",
            "shadcn_cn_usages", "shadcn_cva_definitions", "shadcn_tailwind_patterns",
            "shadcn_forms", "shadcn_dialogs", "shadcn_toasts", "shadcn_data_tables",
        ]
        for attr in shadcn_artifacts:
            if hasattr(matrix, attr):
                shadcn_count += len(getattr(matrix, attr, []))

        # Also count components_json as 1 if present
        if hasattr(matrix, 'shadcn_components_json') and matrix.shadcn_components_json:
            shadcn_count += 1

        if shadcn_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("shadcn-ui")

        # Detect shadcn/ui ecosystem frameworks from detected_frameworks list
        shadcn_frameworks = getattr(matrix, 'shadcn_detected_frameworks', [])
        if shadcn_count >= SIGNIFICANCE_THRESHOLD and shadcn_frameworks:
            shadcn_fw_mapping = {
                'shadcn-ui': 'shadcn-ui',
                'radix-ui': 'radix-ui',
                'tailwind-merge': 'tailwind-merge',
                'clsx': 'clsx',
                'class-variance-authority': 'class-variance-authority',
                'react-hook-form': 'react-hook-form',
                'zod': 'zod',
                'tanstack-react-table': 'tanstack-react-table',
                'sonner': 'sonner',
                'lucide-react': 'lucide-react',
                'next-themes': 'next-themes',
                'vaul': 'vaul',
                'cmdk': 'cmdk',
                'react-day-picker': 'react-day-picker',
                'date-fns': 'date-fns',
                'embla-carousel': 'embla-carousel',
                'recharts': 'recharts',
                'leaflet': 'leaflet',
                'input-otp': 'input-otp',
                'react-resizable-panels': 'react-resizable-panels',
            }
            for fw in shadcn_frameworks:
                mapped = shadcn_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"shadcn/ui artifact count: {shadcn_count}")

        # ==== Bootstrap artifact counts (v4.40) ====
        bootstrap_count = 0
        bootstrap_artifacts = [
            "bootstrap_components", "bootstrap_custom_components",
            "bootstrap_grids", "bootstrap_breakpoints",
            "bootstrap_themes", "bootstrap_variables", "bootstrap_color_modes",
            "bootstrap_utilities", "bootstrap_utility_summary",
            "bootstrap_plugins", "bootstrap_events", "bootstrap_cdn_includes",
        ]
        for attr in bootstrap_artifacts:
            if hasattr(matrix, attr):
                bootstrap_count += len(getattr(matrix, attr, []))

        if bootstrap_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("bootstrap")

        # Detect Bootstrap ecosystem frameworks from detected_frameworks list
        bootstrap_frameworks = getattr(matrix, 'bootstrap_detected_frameworks', [])
        if bootstrap_count >= SIGNIFICANCE_THRESHOLD and bootstrap_frameworks:
            bootstrap_fw_mapping = {
                'bootstrap': 'bootstrap',
                'react-bootstrap': 'react-bootstrap',
                'reactstrap': 'reactstrap',
                'ng-bootstrap': 'ng-bootstrap',
                'ngx-bootstrap': 'ngx-bootstrap',
                'bootstrap-vue': 'bootstrap-vue',
                'bootstrap-vue-next': 'bootstrap-vue-next',
                'bootswatch': 'bootswatch',
                'bootstrap-icons': 'bootstrap-icons',
                'popper': 'popper',
                'jquery': 'jquery',
                'bootstrap-table': 'bootstrap-table',
                'bootstrap-select': 'bootstrap-select',
                'bootstrap-datepicker': 'bootstrap-datepicker',
                'datatables': 'datatables',
                'bootstrap-sass': 'bootstrap-sass',
            }
            for fw in bootstrap_frameworks:
                mapped = bootstrap_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"Bootstrap artifact count: {bootstrap_count}")

        # ==== Radix UI artifact counts (v4.41) ====
        radix_count = 0
        radix_artifacts = [
            "radix_components", "radix_themes_components",
            "radix_primitives", "radix_slots",
            "radix_theme_configs", "radix_color_scales",
            "radix_style_patterns", "radix_data_attributes",
            "radix_compositions", "radix_controlled_patterns",
            "radix_portal_patterns",
        ]
        for attr in radix_artifacts:
            if hasattr(matrix, attr):
                radix_count += len(getattr(matrix, attr, []))

        if radix_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("radix-ui")

        # Detect Radix UI ecosystem frameworks from detected_frameworks list
        radix_frameworks = getattr(matrix, 'radix_detected_frameworks', [])
        if radix_count >= SIGNIFICANCE_THRESHOLD and radix_frameworks:
            radix_fw_mapping = {
                'radix-primitives': 'radix-ui',
                'radix-themes': 'radix-themes',
                'radix-themes-css': 'radix-themes',
                'radix-colors': 'radix-colors',
                'radix-icons': 'radix-icons',
                'stitches': 'stitches',
                'tailwind-merge': 'tailwind-merge',
                'clsx': 'clsx',
                'class-variance-authority': 'class-variance-authority',
                'vanilla-extract': 'vanilla-extract',
                'framer-motion': 'framer-motion',
                'react-spring': 'react-spring',
            }
            for fw in radix_frameworks:
                mapped = radix_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"Radix UI artifact count: {radix_count}")

        # ==== Styled Components artifact counts (v4.42) ====
        sc_count = 0
        sc_artifacts = [
            "sc_components", "sc_extended_components",
            "sc_providers", "sc_global_styles", "sc_theme_usages",
            "sc_css_helpers", "sc_keyframes", "sc_mixins",
            "sc_style_patterns", "sc_dynamic_props", "sc_media_queries",
            "sc_ssr_patterns", "sc_config_patterns", "sc_test_patterns",
        ]
        for attr in sc_artifacts:
            if hasattr(matrix, attr):
                sc_count += len(getattr(matrix, attr, []))

        if sc_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("styled-components")

        # Detect styled-components ecosystem frameworks from detected_frameworks list
        sc_frameworks = getattr(matrix, 'sc_detected_frameworks', [])
        if sc_count >= SIGNIFICANCE_THRESHOLD and sc_frameworks:
            sc_fw_mapping = {
                'styled-components': 'styled-components',
                '@emotion/styled': '@emotion/styled',
                'emotion': '@emotion/styled',
                'linaria': 'linaria',
                'goober': 'goober',
                'stitches': 'stitches',
                'polished': 'polished',
                'styled-system': 'styled-system',
                'rebass': 'rebass',
                'xstyled': 'xstyled',
                'styled-media-query': 'styled-media-query',
                'styled-breakpoints': 'styled-breakpoints',
                'babel-plugin-styled-components': 'babel-plugin-styled-components',
                '@swc/plugin-styled-components': '@swc/plugin-styled-components',
                'jest-styled-components': 'jest-styled-components',
                'styled-normalize': 'styled-normalize',
            }
            for fw in sc_frameworks:
                mapped = sc_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Set CSS-in-JS library if detected
        sc_library = getattr(matrix, 'sc_css_in_js_library', '')
        if sc_library:
            context.frameworks.add(sc_library)

        logger.debug(f"Styled Components artifact count: {sc_count}")

        # ==== Emotion CSS-in-JS artifact counts (v4.43) ====
        em_count = 0
        em_artifacts = [
            "em_components", "em_extended_components",
            "em_providers", "em_global_styles", "em_theme_usages",
            "em_css_props", "em_css_functions", "em_classnames",
            "em_style_patterns", "em_dynamic_props", "em_media_queries",
            "em_keyframes", "em_animation_usages",
            "em_caches", "em_ssr_patterns", "em_babel_configs", "em_test_patterns",
        ]
        for attr in em_artifacts:
            if hasattr(matrix, attr):
                em_count += len(getattr(matrix, attr, []))

        if em_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("emotion")

        # Detect Emotion ecosystem frameworks from detected_frameworks list
        em_frameworks = getattr(matrix, 'em_detected_frameworks', [])
        if em_count >= SIGNIFICANCE_THRESHOLD and em_frameworks:
            em_fw_mapping = {
                'emotion-react': '@emotion/react',
                'emotion-styled': '@emotion/styled',
                'emotion-css': '@emotion/css',
                'emotion-cache': '@emotion/cache',
                'emotion-server': '@emotion/server',
                'emotion-jest': '@emotion/jest',
                'emotion-legacy': 'emotion',
                'react-emotion': 'react-emotion',
                'emotion-theming': 'emotion-theming',
                'emotion-core': '@emotion/core',
                'emotion-babel-plugin': '@emotion/babel-plugin',
                'swc-plugin-emotion': '@swc/plugin-emotion',
                'facepaint': 'facepaint',
                'polished': 'polished',
                'twin-macro': 'twin.macro',
                'emotion-reset': 'emotion-reset',
            }
            for fw in em_frameworks:
                mapped = em_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect Emotion packages
        em_packages = getattr(matrix, 'em_packages', [])
        for pkg in em_packages:
            context.frameworks.add(pkg)

        logger.debug(f"Emotion artifact count: {em_count}")

        # ==== Redux / Redux Toolkit artifact counts (v4.47) ====
        redux_count = 0
        redux_artifacts = [
            "redux_stores", "redux_reducer_compositions", "redux_persist_configs",
            "redux_slices", "redux_entity_adapters", "redux_action_creators",
            "redux_async_thunks", "redux_sagas", "redux_epics",
            "redux_listeners", "redux_custom_middleware",
            "redux_selectors", "redux_typed_hooks",
            "redux_rtk_query_apis", "redux_rtk_query_endpoints", "redux_cache_tags",
        ]
        for attr in redux_artifacts:
            if hasattr(matrix, attr):
                redux_count += len(getattr(matrix, attr, []))

        if redux_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("redux")

        # Detect Redux ecosystem frameworks from detected_frameworks list
        redux_frameworks = getattr(matrix, 'redux_detected_frameworks', [])
        if redux_count >= SIGNIFICANCE_THRESHOLD and redux_frameworks:
            redux_fw_mapping = {
                'redux': 'redux',
                'react-redux': 'react-redux',
                'reduxjs-toolkit': 'redux-toolkit',
                'rtk-query': 'rtk-query',
                'redux-saga': 'redux-saga',
                'redux-observable': 'redux-observable',
                'redux-thunk': 'redux-thunk',
                'redux-persist': 'redux-persist',
                'redux-devtools': 'redux-devtools',
                'redux-logger': 'redux-logger',
                'redux-promise': 'redux-promise',
                'reselect': 'reselect',
                'immer': 'immer',
                'normalizr': 'normalizr',
                'redux-actions': 'redux-actions',
                'typesafe-actions': 'typesafe-actions',
                'redux-mock-store': 'redux-mock-store',
                'msw': 'msw',
                'redux-form': 'redux-form',
                'connected-react-router': 'connected-react-router',
            }
            for fw in redux_frameworks:
                mapped = redux_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect Redux version
        redux_version = getattr(matrix, 'redux_version', '')
        if redux_version:
            if redux_version == 'rtk-v2':
                context.frameworks.add('redux-toolkit-v2')
            elif redux_version == 'rtk-v1':
                context.frameworks.add('redux-toolkit-v1')
            elif redux_version == 'legacy':
                context.frameworks.add('redux-legacy')

        logger.debug(f"Redux artifact count: {redux_count}")

        # ==== Zustand State Management artifact counts (v4.48) ====
        zustand_count = 0
        zustand_artifacts = [
            "zustand_stores", "zustand_slices", "zustand_context_stores",
            "zustand_selectors", "zustand_hook_usages",
            "zustand_persist_configs", "zustand_devtools_configs",
            "zustand_custom_middleware", "zustand_actions",
            "zustand_subscriptions", "zustand_imperative_usages",
            "zustand_imports", "zustand_integrations", "zustand_types",
        ]
        for attr in zustand_artifacts:
            if hasattr(matrix, attr):
                zustand_count += len(getattr(matrix, attr, []))

        if zustand_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("zustand")

        # Detect Zustand ecosystem frameworks from detected_frameworks list
        zustand_frameworks = getattr(matrix, 'zustand_detected_frameworks', [])
        if zustand_count >= SIGNIFICANCE_THRESHOLD and zustand_frameworks:
            zustand_fw_mapping = {
                'zustand': 'zustand',
                'zustand-middleware': 'zustand-middleware',
                'zustand-persist': 'zustand-persist',
                'zustand-devtools': 'zustand-devtools',
                'zustand-immer': 'zustand-immer',
                'zustand-subscribeWithSelector': 'zustand-subscribe',
                'zustand-shallow': 'zustand-shallow',
                'zustand-vanilla': 'zustand-vanilla',
                'zustand-context': 'zustand-context',
                'zundo': 'zundo',
                'zustand-computed': 'zustand-computed',
                'zustand-broadcast': 'zustand-broadcast',
                'react-query': 'react-query',
                'react-hook-form': 'react-hook-form',
                'immer': 'immer',
            }
            for fw in zustand_frameworks:
                mapped = zustand_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect Zustand version
        zustand_version = getattr(matrix, 'zustand_version', '')
        if zustand_version:
            if zustand_version == 'v5':
                context.frameworks.add('zustand-v5')
            elif zustand_version == 'v4':
                context.frameworks.add('zustand-v4')
            elif zustand_version == 'v3':
                context.frameworks.add('zustand-v3')
            elif zustand_version in ('v1', 'v2'):
                context.frameworks.add('zustand-legacy')

        logger.debug(f"Zustand artifact count: {zustand_count}")

        # ==== Jotai Atomic State Management artifact counts (v4.49) ====
        jotai_count = 0
        jotai_artifacts = [
            "jotai_atoms", "jotai_atom_families", "jotai_resettable_atoms",
            "jotai_derived_atoms", "jotai_select_atoms", "jotai_focus_atoms",
            "jotai_storage_atoms", "jotai_effects", "jotai_machine_atoms",
            "jotai_hook_usages", "jotai_write_fns", "jotai_store_usages",
            "jotai_imports", "jotai_integrations", "jotai_types",
        ]
        for attr in jotai_artifacts:
            if hasattr(matrix, attr):
                jotai_count += len(getattr(matrix, attr, []))

        if jotai_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("jotai")

        # Detect Jotai ecosystem frameworks from detected_frameworks list
        jotai_frameworks = getattr(matrix, 'jotai_detected_frameworks', [])
        if jotai_count >= SIGNIFICANCE_THRESHOLD and jotai_frameworks:
            jotai_fw_mapping = {
                'jotai': 'jotai',
                'jotai-utils': 'jotai-utils',
                'jotai-vanilla': 'jotai-vanilla',
                'jotai-devtools': 'jotai-devtools',
                'jotai-immer': 'jotai-immer',
                'jotai-optics': 'jotai-optics',
                'jotai-xstate': 'jotai-xstate',
                'jotai-effect': 'jotai-effect',
                'jotai-tanstack-query': 'jotai-tanstack-query',
                'jotai-trpc': 'jotai-trpc',
                'jotai-molecules': 'jotai-molecules',
                'jotai-scope': 'jotai-scope',
                'jotai-location': 'jotai-location',
                'jotai-valtio': 'jotai-valtio',
                'immer': 'immer',
                'xstate': 'xstate',
                'rxjs': 'rxjs',
                'react-query': 'react-query',
                'react-hook-form': 'react-hook-form',
            }
            for fw in jotai_frameworks:
                mapped = jotai_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect Jotai version
        jotai_version = getattr(matrix, 'jotai_version', '')
        if jotai_version:
            if jotai_version == 'v2':
                context.frameworks.add('jotai-v2')
            elif jotai_version == 'v1':
                context.frameworks.add('jotai-v1')

        logger.debug(f"Jotai artifact count: {jotai_count}")

        # ==== Recoil State Management artifact counts (v4.50) ====
        recoil_count = 0
        recoil_artifacts = [
            "recoil_atoms", "recoil_atom_families",
            "recoil_selectors", "recoil_selector_families",
            "recoil_effects", "recoil_hook_usages", "recoil_callbacks",
            "recoil_imports", "recoil_snapshot_usages", "recoil_types",
        ]
        for attr in recoil_artifacts:
            if hasattr(matrix, attr):
                recoil_count += len(getattr(matrix, attr, []))

        if recoil_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("recoil")

        # Detect Recoil ecosystem frameworks from detected_frameworks list
        recoil_frameworks = getattr(matrix, 'recoil_detected_frameworks', [])
        if recoil_count >= SIGNIFICANCE_THRESHOLD and recoil_frameworks:
            recoil_fw_mapping = {
                'recoil': 'recoil',
                'recoil-sync': 'recoil-sync',
                'recoil-relay': 'recoil-relay',
                'recoil-nexus': 'recoil-nexus',
                'recoil-persist': 'recoil-persist',
                '@recoiljs/refine': 'recoiljs-refine',
                'react': 'react',
                'react-native': 'react-native',
                'relay': 'relay',
            }
            for fw in recoil_frameworks:
                mapped = recoil_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect Recoil version
        recoil_version = getattr(matrix, 'recoil_version', '')
        if recoil_version:
            context.frameworks.add(f'recoil-{recoil_version}')

        logger.debug(f"Recoil artifact count: {recoil_count}")

        # ==== MobX State Management artifact counts (v4.51) ====
        mobx_count = 0
        mobx_artifacts = [
            "mobx_observables", "mobx_auto_observables",
            "mobx_decorator_observables", "mobx_computeds",
            "mobx_actions", "mobx_flows", "mobx_reactions",
            "mobx_imports", "mobx_configures",
            "mobx_integrations", "mobx_types",
        ]
        for attr in mobx_artifacts:
            if hasattr(matrix, attr):
                mobx_count += len(getattr(matrix, attr, []))

        if mobx_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("mobx")

        # Detect MobX ecosystem frameworks from detected_frameworks list
        mobx_frameworks = getattr(matrix, 'mobx_detected_frameworks', [])
        if mobx_count >= SIGNIFICANCE_THRESHOLD and mobx_frameworks:
            mobx_fw_mapping = {
                'mobx': 'mobx',
                'mobx-react': 'mobx-react',
                'mobx-react-lite': 'mobx-react-lite',
                'mobx-state-tree': 'mobx-state-tree',
                'mobx-keystone': 'mobx-keystone',
                'mobx-utils': 'mobx-utils',
                'mobx-persist': 'mobx-persist',
                'mobx-persist-store': 'mobx-persist-store',
                'react': 'react',
                'react-native': 'react-native',
            }
            for fw in mobx_frameworks:
                mapped = mobx_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect MobX version
        mobx_version = getattr(matrix, 'mobx_version', '')
        if mobx_version:
            context.frameworks.add(f'mobx-{mobx_version}')

        logger.debug(f"MobX artifact count: {mobx_count}")

        # ==== Pinia State Management artifact counts (v4.52) ====
        pinia_count = 0
        pinia_artifacts = [
            "pinia_stores", "pinia_getters", "pinia_store_to_refs",
            "pinia_actions", "pinia_patches", "pinia_subscriptions",
            "pinia_plugins", "pinia_instances",
            "pinia_imports", "pinia_integrations", "pinia_types",
        ]
        for attr in pinia_artifacts:
            if hasattr(matrix, attr):
                pinia_count += len(getattr(matrix, attr, []))

        if pinia_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("pinia")

        # Detect Pinia ecosystem frameworks from detected_frameworks list
        pinia_frameworks = getattr(matrix, 'pinia_detected_frameworks', [])
        if pinia_count >= SIGNIFICANCE_THRESHOLD and pinia_frameworks:
            pinia_fw_mapping = {
                'pinia': 'pinia',
                '@pinia/nuxt': 'pinia-nuxt',
                '@pinia/testing': 'pinia-testing',
                'pinia-plugin-persistedstate': 'pinia-plugin-persistedstate',
                'pinia-plugin-debounce': 'pinia-plugin-debounce',
                'pinia-orm': 'pinia-orm',
                'vue': 'vue',
                'nuxt': 'nuxt',
                'vue-router': 'vue-router',
                'vue-i18n': 'vue-i18n',
            }
            for fw in pinia_frameworks:
                mapped = pinia_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect Pinia version
        pinia_version = getattr(matrix, 'pinia_version', '')
        if pinia_version:
            context.frameworks.add(f'pinia-{pinia_version}')

        logger.debug(f"Pinia artifact count: {pinia_count}")

        # ==== NgRx State Management artifact counts (v4.53) ====
        ngrx_count = 0
        ngrx_artifacts = [
            "ngrx_stores", "ngrx_component_stores", "ngrx_signal_stores",
            "ngrx_actions", "ngrx_action_groups",
            "ngrx_effects", "ngrx_component_store_effects",
            "ngrx_selectors", "ngrx_feature_selectors",
            "ngrx_entities", "ngrx_router_stores",
        ]
        for attr in ngrx_artifacts:
            if hasattr(matrix, attr):
                ngrx_count += len(getattr(matrix, attr, []))

        if ngrx_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("ngrx")

        # Detect NgRx ecosystem frameworks from detected_frameworks list
        ngrx_frameworks = getattr(matrix, 'ngrx_detected_frameworks', [])
        if ngrx_count >= SIGNIFICANCE_THRESHOLD and ngrx_frameworks:
            ngrx_fw_mapping = {
                'ngrx-store': 'ngrx-store',
                'ngrx-effects': 'ngrx-effects',
                'ngrx-entity': 'ngrx-entity',
                'ngrx-store-devtools': 'ngrx-store-devtools',
                'ngrx-router-store': 'ngrx-router-store',
                'ngrx-component-store': 'ngrx-component-store',
                'ngrx-signals': 'ngrx-signals',
                'ngrx-operators': 'ngrx-operators',
                'ngrx-schematics': 'ngrx-schematics',
                'ngrx-eslint-plugin': 'ngrx-eslint-plugin',
                'ngrx-store-freeze': 'ngrx-store-freeze',
                'ngrx-forms': 'ngrx-forms',
                'ngrx-entity-relationship': 'ngrx-entity-relationship',
                'ngrx-store-localstorage': 'ngrx-store-localstorage',
                'ngrx-store-logger': 'ngrx-store-logger',
                'angular': 'angular',
                'rxjs': 'rxjs',
            }
            for fw in ngrx_frameworks:
                mapped = ngrx_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect NgRx version
        ngrx_version = getattr(matrix, 'ngrx_version', '')
        if ngrx_version:
            context.frameworks.add(f'ngrx-{ngrx_version}')

        logger.debug(f"NgRx artifact count: {ngrx_count}")

        # ==== XState State Machine artifact counts (v4.55) ====
        xstate_count = 0
        xstate_artifacts = [
            "xstate_machines", "xstate_state_nodes", "xstate_transitions",
            "xstate_invokes", "xstate_actions", "xstate_guards",
            "xstate_imports", "xstate_actors", "xstate_typegens",
        ]
        for attr in xstate_artifacts:
            if hasattr(matrix, attr):
                xstate_count += len(getattr(matrix, attr, []))

        if xstate_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("xstate")

        # Detect XState ecosystem frameworks from detected_frameworks list
        xstate_frameworks = getattr(matrix, 'xstate_detected_frameworks', [])
        if xstate_count >= SIGNIFICANCE_THRESHOLD and xstate_frameworks:
            xstate_fw_mapping = {
                'xstate': 'xstate',
                'xstate-v5': 'xstate-v5',
                '@xstate/react': 'xstate-react',
                '@xstate/vue': 'xstate-vue',
                '@xstate/svelte': 'xstate-svelte',
                '@xstate/solid': 'xstate-solid',
                '@xstate/inspect': 'xstate-inspect',
                '@xstate/test': 'xstate-test',
                '@xstate/graph': 'xstate-graph',
                '@xstate/store': 'xstate-store',
                '@xstate/immer': 'xstate-immer',
                '@stately/inspect': 'stately-inspect',
                'react': 'react',
                'vue': 'vue',
                'svelte': 'svelte',
            }
            for fw in xstate_frameworks:
                mapped = xstate_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect XState version
        xstate_version = getattr(matrix, 'xstate_version', '')
        if xstate_version:
            context.frameworks.add(f'xstate-{xstate_version}')

        logger.debug(f"XState artifact count: {xstate_count}")

        # ==== Valtio Proxy State Management artifact counts (v4.56) ====
        valtio_count = 0
        valtio_artifacts = [
            "valtio_proxies", "valtio_refs", "valtio_collections",
            "valtio_snapshots", "valtio_use_proxies",
            "valtio_subscribes", "valtio_subscribe_keys", "valtio_watches",
            "valtio_actions", "valtio_devtools",
            "valtio_imports", "valtio_integrations", "valtio_types",
        ]
        for attr in valtio_artifacts:
            if hasattr(matrix, attr):
                valtio_count += len(getattr(matrix, attr, []))

        if valtio_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("valtio")

        # Detect Valtio ecosystem frameworks from detected_frameworks list
        valtio_frameworks = getattr(matrix, 'valtio_detected_frameworks', [])
        if valtio_count >= SIGNIFICANCE_THRESHOLD and valtio_frameworks:
            valtio_fw_mapping = {
                'valtio': 'valtio',
                'valtio-vanilla': 'valtio-vanilla',
                'valtio-react': 'valtio-react',
                'valtio-utils': 'valtio-utils',
                'derive-valtio': 'derive-valtio',
                'valtio-reactive': 'valtio-reactive',
                'use-valtio': 'use-valtio',
                'eslint-plugin-valtio': 'eslint-plugin-valtio',
                'proxy-compare': 'proxy-compare',
                'react': 'react',
                'next': 'next',
            }
            for fw in valtio_frameworks:
                mapped = valtio_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect Valtio version
        valtio_version = getattr(matrix, 'valtio_version', '')
        if valtio_version:
            context.frameworks.add(f'valtio-{valtio_version}')

        logger.debug(f"Valtio artifact count: {valtio_count}")

        # ==== TanStack Query Data Fetching artifact counts (v4.57) ====
        tanstack_query_count = 0
        tanstack_query_artifacts = [
            "tanstack_query_queries", "tanstack_query_infinite_queries",
            "tanstack_query_parallel_queries", "tanstack_query_query_options",
            "tanstack_query_key_factories", "tanstack_query_mutations",
            "tanstack_query_clients", "tanstack_query_cache_operations",
            "tanstack_query_providers", "tanstack_query_prefetches",
            "tanstack_query_hydrations", "tanstack_query_imports",
            "tanstack_query_integrations", "tanstack_query_types",
        ]
        for attr in tanstack_query_artifacts:
            if hasattr(matrix, attr):
                tanstack_query_count += len(getattr(matrix, attr, []))

        if tanstack_query_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("tanstack-query")

        # Detect TanStack Query ecosystem frameworks from detected_frameworks list
        tsq_frameworks = getattr(matrix, 'tanstack_query_detected_frameworks', [])
        if tanstack_query_count >= SIGNIFICANCE_THRESHOLD and tsq_frameworks:
            tsq_fw_mapping = {
                'tanstack-react-query': 'tanstack-query',
                'tanstack-vue-query': 'tanstack-query',
                'tanstack-svelte-query': 'tanstack-query',
                'tanstack-solid-query': 'tanstack-query',
                'tanstack-angular-query': 'tanstack-query',
                'react-query-legacy': 'tanstack-query',
                'tanstack-devtools': 'tanstack-query',
                'tanstack-persist': 'tanstack-query',
                'trpc': 'trpc',
                'axios': 'axios',
                'ky': 'ky',
                'graphql-request': 'graphql',
                'react': 'react',
                'next': 'next',
                'msw': 'msw',
            }
            for fw in tsq_frameworks:
                mapped = tsq_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect TanStack Query version
        tsq_version = getattr(matrix, 'tanstack_query_version', '')
        if tsq_version:
            context.frameworks.add(f'tanstack-query-{tsq_version}')

        logger.debug(f"TanStack Query artifact count: {tanstack_query_count}")

        # ==== SWR Data Fetching artifact counts (v4.58) ====
        swr_count = 0
        swr_artifacts = [
            "swr_hooks", "swr_infinite_hooks",
            "swr_subscription_hooks", "swr_mutation_hooks",
            "swr_optimistic_updates", "swr_configs",
            "swr_mutate_calls", "swr_preloads",
            "swr_middlewares", "swr_imports",
            "swr_integrations", "swr_types",
        ]
        for attr in swr_artifacts:
            if hasattr(matrix, attr):
                swr_count += len(getattr(matrix, attr, []))

        if swr_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("swr")

        # Detect SWR ecosystem frameworks from detected_frameworks list
        swr_frameworks = getattr(matrix, 'swr_detected_frameworks', [])
        if swr_count >= SIGNIFICANCE_THRESHOLD and swr_frameworks:
            swr_fw_mapping = {
                'swr': 'swr',
                'swr-infinite': 'swr',
                'swr-mutation': 'swr',
                'swr-subscription': 'swr',
                'swr-immutable': 'swr',
                'axios': 'axios',
                'ky': 'ky',
                'graphql-request': 'graphql',
                'react': 'react',
                'next': 'next',
                'react-native': 'react-native',
                'msw': 'msw',
            }
            for fw in swr_frameworks:
                mapped = swr_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect SWR version
        swr_version = getattr(matrix, 'swr_version', '')
        if swr_version:
            context.frameworks.add(f'swr-{swr_version}')

        logger.debug(f"SWR artifact count: {swr_count}")

        # ==== Apollo Client GraphQL artifact counts (v4.59) ====
        apollo_count = 0
        apollo_artifacts = [
            "apollo_queries", "apollo_lazy_queries",
            "apollo_gql_tags", "apollo_mutations",
            "apollo_optimistic_responses", "apollo_cache_configs",
            "apollo_type_policies", "apollo_reactive_vars",
            "apollo_cache_operations", "apollo_subscriptions",
            "apollo_subscribe_to_more", "apollo_imports",
            "apollo_links", "apollo_client_configs",
            "apollo_integrations", "apollo_types",
        ]
        for attr in apollo_artifacts:
            if hasattr(matrix, attr):
                apollo_count += len(getattr(matrix, attr, []))

        if apollo_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("apollo")
            context.frameworks.add("graphql")

        # Detect Apollo ecosystem frameworks from detected_frameworks list
        apollo_frameworks = getattr(matrix, 'apollo_detected_frameworks', [])
        if apollo_count >= SIGNIFICANCE_THRESHOLD and apollo_frameworks:
            apollo_fw_mapping = {
                'apollo-client-v3': 'apollo',
                'apollo-client-v1': 'apollo',
                'apollo-boost': 'apollo',
                'react-apollo': 'apollo',
                'apollo-react-hooks': 'apollo',
                'apollo-link-http': 'apollo',
                'apollo-link-error': 'apollo',
                'apollo-link-ws': 'apollo',
                'apollo-link-rest': 'apollo',
                'apollo-link-retry': 'apollo',
                'apollo-link-context': 'apollo',
                'apollo-link-persisted-queries': 'apollo',
                'apollo-link-batch-http': 'apollo',
                'graphql-tag': 'graphql',
                'graphql': 'graphql',
                'graphql-ws': 'graphql',
                'subscriptions-transport-ws': 'graphql',
                'graphql-codegen': 'graphql',
                'react': 'react',
                'next': 'next',
                'react-native': 'react-native',
            }
            for fw in apollo_frameworks:
                mapped = apollo_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect Apollo Client version
        apollo_version = getattr(matrix, 'apollo_version', '')
        if apollo_version:
            context.frameworks.add(f'apollo-{apollo_version}')

        logger.debug(f"Apollo artifact count: {apollo_count}")

        # ==== Astro artifact counts (v4.60) ====
        astro_count = 0
        astro_artifacts = [
            "astro_components", "astro_frontmatter",
            "astro_islands", "astro_routes",
            "astro_endpoints", "astro_middleware",
            "astro_collections", "astro_data_fetches",
            "astro_imports", "astro_integrations",
            "astro_config", "astro_types",
        ]
        for attr in astro_artifacts:
            if hasattr(matrix, attr):
                astro_count += len(getattr(matrix, attr, []))

        if astro_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("astro")

        # Detect Astro ecosystem frameworks from detected_frameworks list
        astro_frameworks = getattr(matrix, 'astro_detected_frameworks', [])
        if astro_count >= SIGNIFICANCE_THRESHOLD and astro_frameworks:
            astro_fw_mapping = {
                'astro': 'astro',
                'astro-content': 'astro',
                'astro-assets': 'astro',
                'astro-transitions': 'astro',
                'astro-middleware': 'astro',
                'astro-i18n': 'astro',
                'astro-env': 'astro',
                'astro-db': 'astro',
                'astro-actions': 'astro',
                'astro-react': 'react',
                'astro-vue': 'vue',
                'astro-svelte': 'svelte',
                'astro-solid': 'solid',
                'astro-preact': 'preact',
                'astro-lit': 'lit',
                'astro-alpinejs': 'alpine',
                'astro-tailwind': 'tailwind',
                'astro-mdx': 'mdx',
                'astro-markdoc': 'markdoc',
                'starlight': 'starlight',
                'astro-node': 'node',
                'astro-vercel': 'vercel',
                'astro-netlify': 'netlify',
                'astro-cloudflare': 'cloudflare',
                'astro-sitemap': 'astro',
                'astro-rss': 'astro',
                'astro-partytown': 'astro',
            }
            for fw in astro_frameworks:
                mapped = astro_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect Astro version
        astro_version = getattr(matrix, 'astro_version', '')
        if astro_version:
            context.frameworks.add(f'astro-{astro_version}')

        logger.debug(f"Astro artifact count: {astro_count}")

        # ==== Remix / React Router v7 artifact counts (v4.61) ====
        remix_count = 0
        remix_artifacts = [
            "remix_routes", "remix_layouts",
            "remix_loaders", "remix_client_loaders",
            "remix_actions", "remix_client_actions",
            "remix_forms", "remix_fetchers",
            "remix_meta", "remix_error_boundaries",
            "remix_imports", "remix_adapters",
            "remix_config", "remix_types",
        ]
        for attr in remix_artifacts:
            if hasattr(matrix, attr):
                remix_count += len(getattr(matrix, attr, []))

        if remix_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("remix")

        # Detect Remix ecosystem frameworks from detected_frameworks list
        remix_frameworks = getattr(matrix, 'remix_detected_frameworks', [])
        if remix_count >= SIGNIFICANCE_THRESHOLD and remix_frameworks:
            remix_fw_mapping = {
                'remix': 'remix',
                'remix-react': 'remix',
                'remix-node': 'remix',
                'react-router': 'react-router',
                'remix-express': 'express',
                'remix-cloudflare': 'cloudflare',
                'remix-vercel': 'vercel',
                'remix-netlify': 'netlify',
                'remix-architect': 'architect',
                'remix-deno': 'deno',
                'prisma': 'prisma',
                'drizzle': 'drizzle',
                'supabase': 'supabase',
                'remix-auth': 'remix-auth',
                'clerk': 'clerk',
                'conform': 'conform',
                'remix-validated-form': 'remix-validated-form',
                'zod': 'zod',
                'tailwind': 'tailwind',
                'shadcn': 'shadcn',
                'remix-utils': 'remix-utils',
                'remix-i18next': 'remix-i18next',
                'remix-flat-routes': 'remix-flat-routes',
                'epic-stack': 'epic-stack',
                'sentry': 'sentry',
                'fly-io': 'fly-io',
            }
            for fw in remix_frameworks:
                mapped = remix_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect Remix version
        remix_version = getattr(matrix, 'remix_version', '')
        if remix_version:
            context.frameworks.add(f'remix-{remix_version}')

        logger.debug(f"Remix artifact count: {remix_count}")

        # ==== Solid.js artifact counts (v4.62) ====
        solidjs_count = 0
        solidjs_artifacts = [
            "solidjs_components", "solidjs_control_flows",
            "solidjs_signals", "solidjs_memos",
            "solidjs_effects", "solidjs_reactive_utils",
            "solidjs_stores", "solidjs_store_updates",
            "solidjs_resources", "solidjs_server_functions",
            "solidjs_route_data", "solidjs_routes",
            "solidjs_router_hooks", "solidjs_imports",
            "solidjs_contexts", "solidjs_lifecycles",
            "solidjs_integrations", "solidjs_types",
        ]
        for attr in solidjs_artifacts:
            if hasattr(matrix, attr):
                solidjs_count += len(getattr(matrix, attr, []))

        if solidjs_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("solidjs")

        # Detect Solid.js ecosystem frameworks from detected_frameworks list
        solidjs_frameworks = getattr(matrix, 'solidjs_detected_frameworks', [])
        if solidjs_count >= SIGNIFICANCE_THRESHOLD and solidjs_frameworks:
            solidjs_fw_mapping = {
                'solid-js': 'solidjs',
                'solid-js-store': 'solidjs',
                'solid-js-web': 'solidjs',
                'solid-js-html': 'solidjs',
                'solidjs-router': 'solidjs-router',
                'solid-app-router': 'solidjs-router',
                'solid-start': 'solid-start',
                'vinxi': 'solid-start',
                'solidjs-testing': 'solidjs',
                'solid-primitives': 'solid-primitives',
                'kobalte': 'kobalte',
                'ark-ui-solid': 'ark-ui',
                'solid-headless': 'solidjs',
                'tanstack-solid-query': 'tanstack-query',
                'tanstack-solid-table': 'tanstack-table',
                'solid-styled-components': 'styled-components',
                'solid-styled': 'solidjs',
                'solid-transition-group': 'solidjs',
                'motionone-solid': 'motion',
                'solid-meta': 'solidjs',
                'vite-plugin-solid': 'vite',
                'solid-devtools': 'solidjs',
                'solid-markdown': 'solidjs',
                'solid-icons': 'solidjs',
                'solid-toast': 'solidjs',
                'solid-i18n': 'solidjs',
            }
            for fw in solidjs_frameworks:
                mapped = solidjs_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect Solid.js version
        solidjs_version = getattr(matrix, 'solidjs_version', '')
        if solidjs_version:
            context.frameworks.add(f'solidjs-{solidjs_version}')

        logger.debug(f"Solid.js artifact count: {solidjs_count}")

        # ==== Qwik artifact counts (v4.63) ====
        qwik_count = 0
        qwik_artifacts = [
            "qwik_components", "qwik_slots",
            "qwik_signals", "qwik_stores",
            "qwik_computeds", "qwik_tasks",
            "qwik_resources", "qwik_route_loaders",
            "qwik_route_actions", "qwik_server_functions",
            "qwik_middleware", "qwik_nav_hooks",
            "qwik_contexts", "qwik_no_serializes",
            "qwik_imports", "qwik_event_handlers",
            "qwik_styles", "qwik_integrations",
            "qwik_types",
        ]
        for attr in qwik_artifacts:
            if hasattr(matrix, attr):
                qwik_count += len(getattr(matrix, attr, []))

        if qwik_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("qwik")

        # Detect Qwik ecosystem frameworks from detected_frameworks list
        qwik_frameworks = getattr(matrix, 'qwik_detected_frameworks', [])
        if qwik_count >= SIGNIFICANCE_THRESHOLD and qwik_frameworks:
            qwik_fw_mapping = {
                'qwik': 'qwik',
                'qwik-city': 'qwik-city',
                'qwik-build': 'qwik',
                'qwik-server': 'qwik',
                'qwik-optimizer': 'qwik',
                'qwik-testing': 'qwik',
                'qwik-ui-headless': 'qwik-ui',
                'qwik-ui-styled': 'qwik-ui',
                'qwik-ui': 'qwik-ui',
                'modular-forms': 'modular-forms',
                'qwik-speak': 'qwik-speak',
                'qwik-auth': 'qwik-auth',
                'unpic-qwik': 'unpic',
                'zod': 'zod',
                'valibot': 'valibot',
                'qwik-icon': 'qwik',
                'vite': 'vite',
            }
            for fw in qwik_frameworks:
                mapped = qwik_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect Qwik version
        qwik_version = getattr(matrix, 'qwik_version', '')
        if qwik_version:
            context.frameworks.add(f'qwik-{qwik_version}')

        # Detect Qwik City usage
        if getattr(matrix, 'qwik_has_city', False):
            context.frameworks.add('qwik-city')

        logger.debug(f"Qwik artifact count: {qwik_count}")

        # ==== Preact artifact counts (v4.64) ====
        preact_count = 0
        preact_artifacts = [
            "preact_components", "preact_class_components",
            "preact_memos", "preact_lazies",
            "preact_forward_refs", "preact_error_boundaries",
            "preact_hook_usages", "preact_custom_hooks",
            "preact_hook_dependencies",
            "preact_signals", "preact_computeds",
            "preact_effects", "preact_batches",
            "preact_contexts", "preact_context_consumers",
            "preact_imports", "preact_integrations",
            "preact_types", "preact_ssr_patterns",
        ]
        for attr in preact_artifacts:
            if hasattr(matrix, attr):
                preact_count += len(getattr(matrix, attr, []))

        if preact_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("preact")

        # Detect Preact ecosystem frameworks from detected_frameworks list
        preact_frameworks = getattr(matrix, 'preact_detected_frameworks', [])
        if preact_count >= SIGNIFICANCE_THRESHOLD and preact_frameworks:
            preact_fw_mapping = {
                'preact': 'preact',
                'preact-hooks': 'preact',
                'preact-compat': 'preact-compat',
                'preact-signals': 'preact-signals',
                'preact-signals-core': 'preact-signals',
                'preact-router': 'preact-router',
                'wouter-preact': 'wouter',
                'preact-render-to-string': 'preact-ssr',
                'preact-iso': 'preact-iso',
                'htm': 'htm',
                'goober': 'goober',
                'fresh': 'fresh',
                'astro-preact': 'astro',
                'preact-cli': 'preact-cli',
                'wmr': 'wmr',
                'vite-preact': 'vite',
                'testing-library-preact': 'testing-library',
                'preact-custom-element': 'web-components',
                'preact-debug': 'preact',
                'preact-devtools': 'preact',
                'preact-i18n': 'preact-i18n',
            }
            for fw in preact_frameworks:
                mapped = preact_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect Preact version
        preact_version = getattr(matrix, 'preact_version', '')
        if preact_version:
            context.frameworks.add(f'preact-{preact_version}')

        # Detect Preact signals / compat / SSR usage
        if getattr(matrix, 'preact_has_signals', False):
            context.frameworks.add('preact-signals')
        if getattr(matrix, 'preact_has_compat', False):
            context.frameworks.add('preact-compat')
        if getattr(matrix, 'preact_has_ssr', False):
            context.frameworks.add('preact-ssr')

        logger.debug(f"Preact artifact count: {preact_count}")

        # ==== Lit / Web Components artifact counts (v4.65) ====
        lit_count = 0
        lit_artifacts = [
            "lit_components", "lit_mixins", "lit_controllers",
            "lit_properties", "lit_states",
            "lit_events", "lit_event_listeners",
            "lit_templates", "lit_directive_usages", "lit_css_info",
            "lit_imports", "lit_integrations",
            "lit_types", "lit_ssr_patterns",
        ]
        for attr in lit_artifacts:
            if hasattr(matrix, attr):
                lit_count += len(getattr(matrix, attr, []))

        if lit_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("lit")

        # Detect Lit ecosystem frameworks from detected_frameworks list
        lit_frameworks = getattr(matrix, 'lit_detected_frameworks', [])
        if lit_count >= SIGNIFICANCE_THRESHOLD and lit_frameworks:
            lit_fw_mapping = {
                'lit': 'lit',
                'lit-element': 'lit',
                'lit-html': 'lit',
                'lit-decorators': 'lit',
                'lit-directives': 'lit',
                'reactive-element': 'lit',
                'lit-static-html': 'lit',
                'lit-task': 'lit-task',
                'lit-context': 'lit-context',
                'lit-localize': 'lit-localize',
                'lit-labs-ssr': 'lit-ssr',
                'lit-labs-ssr-client': 'lit-ssr',
                'lit-labs-router': 'lit-router',
                'lit-labs-motion': 'lit-motion',
                'lit-labs-task': 'lit-task',
                'lit-labs-context': 'lit-context',
                'lit-labs-observers': 'lit-observers',
                'lit-labs-virtualizer': 'lit-virtualizer',
                'lit-labs-react': 'lit-react',
                'lit-labs-scoped-registry': 'lit-scoped-registry',
                'vaadin': 'vaadin',
                'shoelace': 'shoelace',
                'spectrum-web-components': 'spectrum',
                'lion': 'lion',
                'material-web': 'material-web',
                'open-wc-testing': 'open-wc',
                'open-wc-scoped-elements': 'open-wc',
                'web-dev-server': 'web-dev-server',
                'web-test-runner': 'web-test-runner',
                'storybook-wc': 'storybook',
                'polymer': 'polymer',
                'polymer-legacy': 'polymer',
                'fast-element': 'fast',
                'stencil': 'stencil',
            }
            for fw in lit_frameworks:
                mapped = lit_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect Lit version
        lit_version = getattr(matrix, 'lit_version', '')
        if lit_version:
            context.frameworks.add(f'lit-{lit_version}')

        # Detect Lit feature flags
        if getattr(matrix, 'lit_has_shadow_dom', False):
            context.frameworks.add('shadow-dom')
        if getattr(matrix, 'lit_has_controllers', False):
            context.frameworks.add('reactive-controllers')
        if getattr(matrix, 'lit_has_ssr', False):
            context.frameworks.add('lit-ssr')
        if getattr(matrix, 'lit_has_context', False):
            context.frameworks.add('lit-context')
        if getattr(matrix, 'lit_has_decorators', False):
            context.frameworks.add('lit-decorators')

        logger.debug(f"Lit artifact count: {lit_count}")

        # ==== Alpine.js artifact counts (v4.66) ====
        alpine_count = 0
        alpine_artifacts = [
            "alpine_directives", "alpine_components", "alpine_methods",
            "alpine_stores", "alpine_plugins",
            "alpine_custom_directives", "alpine_custom_magics",
            "alpine_imports", "alpine_integrations",
            "alpine_types", "alpine_cdns",
        ]
        for attr in alpine_artifacts:
            if hasattr(matrix, attr):
                alpine_count += len(getattr(matrix, attr, []))

        if alpine_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("alpine")

        # Detect Alpine.js ecosystem frameworks from detected_frameworks list
        alpine_frameworks = getattr(matrix, 'alpine_detected_frameworks', [])
        if alpine_count >= SIGNIFICANCE_THRESHOLD and alpine_frameworks:
            alpine_fw_mapping = {
                'alpinejs': 'alpine',
                'alpine-csp': 'alpine-csp',
                'alpine-mask': 'alpine-mask',
                'alpine-intersect': 'alpine-intersect',
                'alpine-persist': 'alpine-persist',
                'alpine-morph': 'alpine-morph',
                'alpine-focus': 'alpine-focus',
                'alpine-collapse': 'alpine-collapse',
                'alpine-anchor': 'alpine-anchor',
                'alpine-sort': 'alpine-sort',
                'alpine-ui': 'alpine-ui',
                'alpine-resize': 'alpine-resize',
                'alpine-clipboard': 'alpine-clipboard',
                'alpine-tooltip': 'alpine-tooltip',
                'alpine-turbo-drive': 'alpine-turbo-drive',
                'htmx': 'htmx',
                'livewire': 'livewire',
                'turbo': 'turbo',
                'stimulus': 'stimulus',
                'tailwind': 'tailwind',
            }
            for fw in alpine_frameworks:
                mapped = alpine_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect Alpine.js version
        alpine_version = getattr(matrix, 'alpine_version', '')
        if alpine_version:
            context.frameworks.add(f'alpine-{alpine_version}')

        # Detect Alpine.js feature flags
        if getattr(matrix, 'alpine_has_stores', False):
            context.frameworks.add('alpine-stores')
        if getattr(matrix, 'alpine_has_plugins', False):
            context.frameworks.add('alpine-plugins')
        if getattr(matrix, 'alpine_has_cdn', False):
            context.frameworks.add('alpine-cdn')

        logger.debug(f"Alpine.js artifact count: {alpine_count}")

        # ==== HTMX artifact counts (v4.67) ====
        htmx_count = 0
        htmx_artifacts = [
            "htmx_attributes", "htmx_requests",
            "htmx_events", "htmx_extensions",
            "htmx_imports", "htmx_integrations",
            "htmx_configs", "htmx_cdns",
        ]
        for attr in htmx_artifacts:
            if hasattr(matrix, attr):
                htmx_count += len(getattr(matrix, attr, []))

        if htmx_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("htmx")

        # Detect HTMX ecosystem frameworks from detected_frameworks list
        htmx_frameworks = getattr(matrix, 'htmx_detected_frameworks', [])
        if htmx_count >= SIGNIFICANCE_THRESHOLD and htmx_frameworks:
            htmx_fw_mapping = {
                'htmx': 'htmx',
                'hyperscript': 'hyperscript',
                'alpinejs': 'alpine',
                'django': 'django',
                'flask': 'flask',
                'rails': 'rails',
                'laravel': 'laravel',
                'fastapi': 'fastapi',
                'go_templ': 'go-templ',
                'aspnet': 'aspnet',
                'spring': 'spring',
                'phoenix': 'phoenix',
                'tailwind': 'tailwind',
                'htmx-sse': 'htmx-sse',
                'htmx-ws': 'htmx-ws',
                'htmx-json-enc': 'htmx-json-enc',
                'htmx-response-targets': 'htmx-response-targets',
                'htmx-preload': 'htmx-preload',
                'htmx-idiomorph': 'htmx-idiomorph',
            }
            for fw in htmx_frameworks:
                mapped = htmx_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect HTMX version
        htmx_version = getattr(matrix, 'htmx_version', '')
        if htmx_version:
            context.frameworks.add(f'htmx-{htmx_version}')

        # Detect HTMX feature flags
        if getattr(matrix, 'htmx_has_sse', False):
            context.frameworks.add('htmx-sse')
        if getattr(matrix, 'htmx_has_ws', False):
            context.frameworks.add('htmx-ws')
        if getattr(matrix, 'htmx_has_extensions', False):
            context.frameworks.add('htmx-extensions')
        if getattr(matrix, 'htmx_has_boost', False):
            context.frameworks.add('htmx-boost')
        if getattr(matrix, 'htmx_has_cdn', False):
            context.frameworks.add('htmx-cdn')

        logger.debug(f"HTMX artifact count: {htmx_count}")

        # ==== Stimulus / Hotwire artifact counts (v4.68) ====
        stimulus_count = 0
        stimulus_artifacts = [
            "stimulus_controllers", "stimulus_targets",
            "stimulus_actions", "stimulus_values",
            "stimulus_imports", "stimulus_integrations",
            "stimulus_configs", "stimulus_cdns",
        ]
        for attr in stimulus_artifacts:
            if hasattr(matrix, attr):
                stimulus_count += len(getattr(matrix, attr, []))

        if stimulus_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("stimulus")

        # Detect Stimulus ecosystem frameworks from detected_frameworks list
        stimulus_frameworks = getattr(matrix, 'stimulus_detected_frameworks', [])
        if stimulus_count >= SIGNIFICANCE_THRESHOLD and stimulus_frameworks:
            stim_fw_mapping = {
                'stimulus': 'stimulus',
                'turbo': 'turbo',
                'turbo-rails': 'turbo-rails',
                'strada': 'strada',
                'stimulus-use': 'stimulus-use',
                'stimulus-components': 'stimulus-components',
                'stimulus-webpack-helpers': 'stimulus-webpack',
                'stimulus-vite-helpers': 'stimulus-vite',
                'stimulus-loading': 'stimulus-loading',
                'rails': 'rails',
                'laravel': 'laravel',
                'django': 'django',
                'phoenix': 'phoenix',
                'alpinejs': 'alpine',
                'htmx': 'htmx',
                'tailwind': 'tailwind',
            }
            for fw in stimulus_frameworks:
                mapped = stim_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect Stimulus version
        stimulus_version = getattr(matrix, 'stimulus_version', '')
        if stimulus_version:
            context.frameworks.add(f'stimulus-{stimulus_version}')

        # Detect Stimulus feature flags
        if getattr(matrix, 'stimulus_has_turbo', False):
            context.frameworks.add('turbo')
        if getattr(matrix, 'stimulus_has_strada', False):
            context.frameworks.add('strada')
        if getattr(matrix, 'stimulus_has_turbo_frames', False):
            context.frameworks.add('turbo-frames')
        if getattr(matrix, 'stimulus_has_turbo_streams', False):
            context.frameworks.add('turbo-streams')
        if getattr(matrix, 'stimulus_has_cdn', False):
            context.frameworks.add('stimulus-cdn')
        if getattr(matrix, 'stimulus_has_outlets', False):
            context.frameworks.add('stimulus-outlets')

        logger.debug(f"Stimulus artifact count: {stimulus_count}")

        # ==== Storybook artifact counts (v4.70) ====
        storybook_count = 0
        storybook_artifacts = [
            "storybook_stories", "storybook_components",
            "storybook_addons", "storybook_configs",
            "storybook_imports", "storybook_testing",
        ]
        for attr in storybook_artifacts:
            if hasattr(matrix, attr):
                storybook_count += len(getattr(matrix, attr, []))

        if storybook_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("storybook")

        # Detect Storybook ecosystem frameworks
        storybook_frameworks = getattr(matrix, 'storybook_detected_frameworks', [])
        if storybook_count >= SIGNIFICANCE_THRESHOLD and storybook_frameworks:
            sb_fw_mapping = {
                '@storybook/react': 'storybook-react',
                '@storybook/vue3': 'storybook-vue3',
                '@storybook/angular': 'storybook-angular',
                '@storybook/svelte': 'storybook-svelte',
                '@storybook/web-components': 'storybook-wc',
                '@storybook/nextjs': 'storybook-nextjs',
                '@storybook/react-vite': 'storybook-react-vite',
                '@storybook/react-webpack5': 'storybook-react-webpack5',
                'chromatic': 'chromatic',
                '@storybook/test': 'storybook-test',
                '@storybook/addon-interactions': 'storybook-interactions',
                '@storybook/addon-a11y': 'storybook-a11y',
            }
            for fw in storybook_frameworks:
                mapped = sb_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect Storybook version
        storybook_version = getattr(matrix, 'storybook_version', '')
        if storybook_version:
            context.frameworks.add(f'storybook-{storybook_version}')

        # Detect Storybook feature flags
        if getattr(matrix, 'storybook_has_play_functions', False):
            context.frameworks.add('storybook-play')
        if getattr(matrix, 'storybook_has_interaction_testing', False):
            context.frameworks.add('storybook-interactions')
        if getattr(matrix, 'storybook_has_portable_stories', False):
            context.frameworks.add('storybook-portable')
        if getattr(matrix, 'storybook_has_chromatic', False):
            context.frameworks.add('chromatic')
        if getattr(matrix, 'storybook_has_autodocs', False):
            context.frameworks.add('storybook-autodocs')

        logger.debug(f"Storybook artifact count: {storybook_count}")

        # ==== Three.js / React Three Fiber artifact counts (v4.71) ====
        threejs_count = 0
        threejs_artifacts = [
            "threejs_canvases", "threejs_cameras", "threejs_renderers",
            "threejs_controls", "threejs_lights", "threejs_post_processing",
            "threejs_physics", "threejs_meshes", "threejs_groups",
            "threejs_instanced_meshes", "threejs_drei_components",
            "threejs_custom_components", "threejs_models",
            "threejs_materials", "threejs_shaders", "threejs_textures",
            "threejs_uniforms", "threejs_use_frames",
            "threejs_animation_mixers", "threejs_spring_animations",
            "threejs_tweens", "threejs_morph_targets",
            "threejs_imports", "threejs_integrations", "threejs_types",
        ]
        for attr in threejs_artifacts:
            if hasattr(matrix, attr):
                threejs_count += len(getattr(matrix, attr, []))

        if threejs_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("threejs")

        # Detect R3F vs vanilla Three.js from matrix flags
        if getattr(matrix, 'threejs_is_r3f', False):
            context.frameworks.add("r3f")

        # Detect R3F ecosystem from detected_frameworks list
        threejs_frameworks = getattr(matrix, 'threejs_detected_frameworks', [])
        if threejs_count >= SIGNIFICANCE_THRESHOLD and threejs_frameworks:
            threejs_fw_mapping = {
                '@react-three/fiber': 'r3f',
                '@react-three/drei': 'drei',
                '@react-three/postprocessing': 'r3f-postprocessing',
                '@react-three/rapier': 'rapier',
                '@react-three/xr': 'r3f-xr',
                '@react-three/a11y': 'r3f-a11y',
                '@react-three/flex': 'r3f-flex',
                'three-stdlib': 'three-stdlib',
                'lamina': 'lamina',
                'leva': 'leva',
                'theatre': 'theatre',
                'gsap': 'gsap',
                '@react-spring/three': 'react-spring-three',
                'cannon-es': 'cannon',
                'ammo.js': 'ammo',
                'oimo': 'oimo',
            }
            for fw in threejs_frameworks:
                mapped = threejs_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Detect Three.js version
        threejs_version = getattr(matrix, 'threejs_version', '')
        if threejs_version:
            context.frameworks.add(f'threejs-{threejs_version}')

        r3f_version = getattr(matrix, 'threejs_r3f_version', '')
        if r3f_version:
            context.frameworks.add(f'r3f-{r3f_version}')

        logger.debug(f"Three.js artifact count: {threejs_count}")

        # ==== D3.js Data Visualization artifact counts (v4.72) ====
        d3js_count = 0
        d3js_artifacts = [
            "d3js_selections", "d3js_data_joins", "d3js_shapes",
            "d3js_layouts", "d3js_svg_elements", "d3js_scales",
            "d3js_color_scales", "d3js_axes", "d3js_brushes",
            "d3js_zooms", "d3js_events", "d3js_drags",
            "d3js_transitions", "d3js_tooltips",
            "d3js_imports", "d3js_integrations", "d3js_types",
            "d3js_data_loaders",
        ]
        for attr in d3js_artifacts:
            if hasattr(matrix, attr):
                d3js_count += len(getattr(matrix, attr, []))

        if d3js_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("d3js")

        # Detect D3.js version from matrix
        d3js_version = getattr(matrix, 'd3js_version', '')
        if d3js_version:
            context.frameworks.add(f'd3js-{d3js_version}')

        # Detect modular vs monolithic
        if getattr(matrix, 'd3js_is_modular', False):
            context.frameworks.add("d3js-modular")
        if getattr(matrix, 'd3js_is_monolithic', False):
            context.frameworks.add("d3js-monolithic")

        # Detect Observable notebook
        if getattr(matrix, 'd3js_is_observable', False):
            context.frameworks.add("d3js-observable")

        # Detect geo/map features
        if getattr(matrix, 'd3js_has_geo', False):
            context.frameworks.add("d3js-geo")

        # Detect D3.js ecosystem frameworks
        d3js_frameworks = getattr(matrix, 'd3js_detected_frameworks', [])
        if d3js_count >= SIGNIFICANCE_THRESHOLD and d3js_frameworks:
            d3js_fw_mapping = {
                'd3-force': 'd3-force',
                'd3-hierarchy': 'd3-hierarchy',
                'd3-geo': 'd3-geo',
                'd3-zoom': 'd3-zoom',
                'd3-brush': 'd3-brush',
                'd3-drag': 'd3-drag',
                'd3-transition': 'd3-transition',
                'd3-scale-chromatic': 'd3-chromatic',
                'topojson': 'topojson',
                'visx': 'visx',
                'nivo': 'nivo',
                'recharts': 'recharts',
                'leaflet': 'leaflet',
                'mapbox-gl': 'mapbox-gl',
                'observable': 'observable',
                'vega': 'vega',
                'd3-annotation': 'd3-annotation',
                'd3-tip': 'd3-tip',
                'd3-cloud': 'd3-cloud',
                'd3-sankey': 'd3-sankey',
            }
            for fw in d3js_frameworks:
                mapped = d3js_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"D3.js artifact count: {d3js_count}")

        # ==== Chart.js Charting Library artifact counts (v4.73) ====
        chartjs_count = 0
        chartjs_artifacts = [
            "chartjs_instances", "chartjs_chart_types", "chartjs_configs",
            "chartjs_defaults", "chartjs_datasets", "chartjs_data_points",
            "chartjs_scales", "chartjs_axis_features",
            "chartjs_plugins", "chartjs_registrations",
            "chartjs_imports", "chartjs_integrations", "chartjs_types",
            "chartjs_animations", "chartjs_interactions",
        ]
        for attr in chartjs_artifacts:
            if hasattr(matrix, attr):
                chartjs_count += len(getattr(matrix, attr, []))

        if chartjs_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("chartjs")

        # Detect Chart.js version from matrix
        chartjs_version = getattr(matrix, 'chartjs_version', '')
        if chartjs_version:
            context.frameworks.add(f'chartjs-{chartjs_version}')

        # Detect tree-shakeable vs auto
        if getattr(matrix, 'chartjs_is_tree_shakeable', False):
            context.frameworks.add("chartjs-tree-shakeable")
        if getattr(matrix, 'chartjs_is_auto', False):
            context.frameworks.add("chartjs-auto")

        # Detect features
        if getattr(matrix, 'chartjs_has_animation', False):
            context.frameworks.add("chartjs-animation")
        if getattr(matrix, 'chartjs_has_interaction', False):
            context.frameworks.add("chartjs-interaction")
        if getattr(matrix, 'chartjs_has_typescript', False):
            context.frameworks.add("chartjs-typescript")

        # Detect Chart.js ecosystem frameworks
        chartjs_frameworks = getattr(matrix, 'chartjs_detected_frameworks', [])
        if chartjs_count >= SIGNIFICANCE_THRESHOLD and chartjs_frameworks:
            chartjs_fw_mapping = {
                'react-chartjs-2': 'react-chartjs-2',
                'vue-chartjs': 'vue-chartjs',
                'ng2-charts': 'ng2-charts',
                'angular-chart.js': 'angular-chartjs',
                'svelte-chartjs': 'svelte-chartjs',
                'chartjs-plugin-datalabels': 'chartjs-datalabels',
                'chartjs-plugin-zoom': 'chartjs-zoom',
                'chartjs-plugin-annotation': 'chartjs-annotation',
                'chartjs-plugin-streaming': 'chartjs-streaming',
                'chartjs-adapter-date-fns': 'chartjs-date-fns',
                'chartjs-adapter-luxon': 'chartjs-luxon',
                'chartjs-adapter-moment': 'chartjs-moment',
                'chartjs-adapter-dayjs': 'chartjs-dayjs',
            }
            for fw in chartjs_frameworks:
                mapped = chartjs_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"Chart.js artifact count: {chartjs_count}")

        # ==== Recharts Charting Library artifact counts (v4.74) ====
        recharts_count = 0
        recharts_artifacts = [
            "recharts_components", "recharts_responsive_containers",
            "recharts_series", "recharts_data_keys", "recharts_cells",
            "recharts_axes", "recharts_grids", "recharts_polar_axes",
            "recharts_tooltips", "recharts_legends", "recharts_references",
            "recharts_brushes", "recharts_events", "recharts_animations",
            "recharts_labels", "recharts_imports", "recharts_integrations",
            "recharts_types",
        ]
        for attr in recharts_artifacts:
            if hasattr(matrix, attr):
                recharts_count += len(getattr(matrix, attr, []))

        if recharts_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("recharts")

        # Detect Recharts version from matrix
        recharts_version = getattr(matrix, 'recharts_version', '')
        if recharts_version:
            context.frameworks.add(f'recharts-{recharts_version}')

        # Detect tree-shakeable imports
        if getattr(matrix, 'recharts_is_tree_shakeable', False):
            context.frameworks.add("recharts-tree-shakeable")

        # Detect features
        if getattr(matrix, 'recharts_has_animation', False):
            context.frameworks.add("recharts-animation")
        if getattr(matrix, 'recharts_has_typescript', False):
            context.frameworks.add("recharts-typescript")
        if getattr(matrix, 'recharts_has_responsive', False):
            context.frameworks.add("recharts-responsive")

        # Detect Recharts ecosystem frameworks
        recharts_frameworks = getattr(matrix, 'recharts_detected_frameworks', [])
        if recharts_count >= SIGNIFICANCE_THRESHOLD and recharts_frameworks:
            recharts_fw_mapping = {
                'recharts': 'recharts',
                'recharts-scale': 'recharts-scale',
                'recharts-to-png': 'recharts-to-png',
                'd3-scale': 'd3-scale',
                'd3-shape': 'd3-shape',
                'd3-format': 'd3-format',
                'd3-time-format': 'd3-time-format',
                'd3-interpolate': 'd3-interpolate',
                'd3-color': 'd3-color',
            }
            for fw in recharts_frameworks:
                mapped = recharts_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"Recharts artifact count: {recharts_count}")

        # ==== Leaflet/Mapbox Mapping Framework artifact counts (v4.75) ====
        leaflet_count = 0
        leaflet_artifacts = [
            "leaflet_maps", "leaflet_tile_layers",
            "leaflet_markers", "leaflet_shapes", "leaflet_geojson",
            "leaflet_layer_groups", "leaflet_sources",
            "leaflet_controls", "leaflet_popups", "leaflet_tooltips",
            "leaflet_events", "leaflet_drawings", "leaflet_animations",
            "leaflet_imports", "leaflet_integrations", "leaflet_types",
            "leaflet_plugins",
        ]
        for attr in leaflet_artifacts:
            if hasattr(matrix, attr):
                leaflet_count += len(getattr(matrix, attr, []))

        if leaflet_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("leaflet")

        # Detect Leaflet/Mapbox versions from matrix
        leaflet_version = getattr(matrix, 'leaflet_version', '')
        if leaflet_version:
            context.frameworks.add(f'leaflet-{leaflet_version}')
        mapbox_version = getattr(matrix, 'mapbox_version', '')
        if mapbox_version:
            context.frameworks.add(f'mapbox-gl-{mapbox_version}')

        # Detect feature flags
        if getattr(matrix, 'leaflet_has_react_leaflet', False):
            context.frameworks.add("react-leaflet")
        if getattr(matrix, 'leaflet_has_mapbox', False):
            context.frameworks.add("mapbox-gl")
        if getattr(matrix, 'leaflet_has_maplibre', False):
            context.frameworks.add("maplibre-gl")
        if getattr(matrix, 'leaflet_has_typescript', False):
            context.frameworks.add("leaflet-typescript")
        if getattr(matrix, 'leaflet_has_clustering', False):
            context.frameworks.add("leaflet-clustering")
        if getattr(matrix, 'leaflet_has_drawing', False):
            context.frameworks.add("leaflet-drawing")

        # Detect Leaflet ecosystem frameworks
        leaflet_frameworks = getattr(matrix, 'leaflet_detected_frameworks', [])
        if leaflet_count >= SIGNIFICANCE_THRESHOLD and leaflet_frameworks:
            leaflet_fw_mapping = {
                'leaflet': 'leaflet',
                'mapbox-gl': 'mapbox-gl',
                'maplibre-gl': 'maplibre-gl',
                'react-leaflet': 'react-leaflet',
                'vue-leaflet': 'vue-leaflet',
                'react-map-gl': 'react-map-gl',
                'deck.gl': 'deck-gl',
                'leaflet-draw': 'leaflet-draw',
                'leaflet-markercluster': 'leaflet-markercluster',
                'leaflet-heat': 'leaflet-heat',
                'leaflet-routing': 'leaflet-routing',
                'mapbox-draw': 'mapbox-draw',
                'mapbox-geocoder': 'mapbox-geocoder',
                'turf': 'turf',
                'topojson': 'topojson',
                'proj4': 'proj4',
                'supercluster': 'supercluster',
                'leaflet-geoman': 'leaflet-geoman',
                'leaflet-geosearch': 'leaflet-geosearch',
            }
            for fw in leaflet_frameworks:
                mapped = leaflet_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"Leaflet artifact count: {leaflet_count}")

        # ==== Framer Motion Animation Framework artifact counts (v4.76) ====
        framer_count = 0
        framer_artifacts = [
            "framer_motion_variants", "framer_motion_keyframes",
            "framer_motion_transitions", "framer_motion_animate_presences",
            "framer_motion_animation_controls", "framer_motion_motion_components",
            "framer_motion_drags", "framer_motion_hovers", "framer_motion_taps",
            "framer_motion_gestures", "framer_motion_layout_anims",
            "framer_motion_shared_layouts", "framer_motion_exit_anims",
            "framer_motion_scrolls", "framer_motion_in_views",
            "framer_motion_parallaxes", "framer_motion_imports",
            "framer_motion_hooks", "framer_motion_types",
            "framer_motion_integrations", "framer_motion_motion_elements",
        ]
        for attr in framer_artifacts:
            if hasattr(matrix, attr):
                framer_count += len(getattr(matrix, attr, []))

        if framer_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("framer-motion")

        # Detect Framer Motion version
        framer_version = getattr(matrix, 'framer_motion_version', '')
        if framer_version:
            context.frameworks.add(f'framer-motion-{framer_version}')

        # Detect feature flags
        if getattr(matrix, 'framer_motion_has_typescript', False):
            context.frameworks.add("framer-motion-typescript")
        if getattr(matrix, 'framer_motion_has_variants', False):
            context.frameworks.add("framer-motion-variants")
        if getattr(matrix, 'framer_motion_has_gestures', False):
            context.frameworks.add("framer-motion-gestures")
        if getattr(matrix, 'framer_motion_has_layout_animations', False):
            context.frameworks.add("framer-motion-layout")
        if getattr(matrix, 'framer_motion_has_scroll_animations', False):
            context.frameworks.add("framer-motion-scroll")
        if getattr(matrix, 'framer_motion_has_animate_presence', False):
            context.frameworks.add("framer-motion-animate-presence")
        if getattr(matrix, 'framer_motion_has_drag', False):
            context.frameworks.add("framer-motion-drag")

        # Detect Framer Motion ecosystem frameworks
        framer_frameworks = getattr(matrix, 'framer_motion_detected_frameworks', [])
        if framer_count >= SIGNIFICANCE_THRESHOLD and framer_frameworks:
            framer_fw_mapping = {
                'framer-motion': 'framer-motion',
                'motion': 'motion',
                'motion-subpath': 'framer-motion',
                'animate-presence': 'framer-motion',
                'lazy-motion': 'framer-motion',
                'motion-config': 'framer-motion',
                'layout-group': 'framer-motion',
                'reorder': 'framer-motion',
                'popmotion': 'popmotion',
                'react-spring-bridge': 'react-spring',
                'framer': 'framer',
                'motion-dom': 'framer-motion',
                'motion-three': 'framer-motion-3d',
            }
            for fw in framer_frameworks:
                mapped = framer_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"Framer Motion artifact count: {framer_count}")

        # ==== GSAP Animation Library artifact counts (v4.77) ====
        gsap_count = 0
        gsap_artifacts = [
            "gsap_tweens", "gsap_sets", "gsap_staggers", "gsap_eases",
            "gsap_timelines", "gsap_labels", "gsap_callbacks",
            "gsap_nested_timelines", "gsap_plugins", "gsap_registrations",
            "gsap_effects", "gsap_utilities", "gsap_scroll_triggers",
            "gsap_scroll_smoothers", "gsap_observers", "gsap_scroll_batches",
            "gsap_imports", "gsap_integrations", "gsap_types",
            "gsap_contexts", "gsap_match_medias",
        ]
        for attr in gsap_artifacts:
            if hasattr(matrix, attr):
                gsap_count += len(getattr(matrix, attr, []))

        if gsap_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("gsap")

        # Detect GSAP version
        gsap_version = getattr(matrix, 'gsap_version', '')
        if gsap_version:
            context.frameworks.add(f'gsap-{gsap_version}')

        # Detect GSAP feature flags
        if getattr(matrix, 'gsap_has_typescript', False):
            context.frameworks.add("gsap-typescript")
        if getattr(matrix, 'gsap_has_scroll_trigger', False):
            context.frameworks.add("gsap-scrolltrigger")
        if getattr(matrix, 'gsap_has_scroll_smoother', False):
            context.frameworks.add("gsap-scrollsmoother")
        if getattr(matrix, 'gsap_has_timelines', False):
            context.frameworks.add("gsap-timelines")
        if getattr(matrix, 'gsap_has_plugins', False):
            context.frameworks.add("gsap-plugins")
        if getattr(matrix, 'gsap_has_staggers', False):
            context.frameworks.add("gsap-staggers")
        if getattr(matrix, 'gsap_has_context', False):
            context.frameworks.add("gsap-context")
        if getattr(matrix, 'gsap_has_match_media', False):
            context.frameworks.add("gsap-matchmedia")
        if getattr(matrix, 'gsap_has_club_plugins', False):
            context.frameworks.add("gsap-club")

        # Detect GSAP ecosystem frameworks
        gsap_frameworks = getattr(matrix, 'gsap_detected_frameworks', [])
        if gsap_count >= SIGNIFICANCE_THRESHOLD and gsap_frameworks:
            gsap_fw_mapping = {
                'gsap': 'gsap',
                'gsap-core': 'gsap',
                'ScrollTrigger': 'gsap-scrolltrigger',
                'ScrollSmoother': 'gsap-scrollsmoother',
                'Draggable': 'gsap-draggable',
                'MotionPathPlugin': 'gsap-motionpath',
                'MorphSVGPlugin': 'gsap-morphsvg',
                'DrawSVGPlugin': 'gsap-drawsvg',
                'SplitText': 'gsap-splittext',
                'Flip': 'gsap-flip',
                'Observer': 'gsap-observer',
                'react-gsap': 'gsap-react',
                'vue-gsap': 'gsap-vue',
                'angular-gsap': 'gsap-angular',
            }
            for fw in gsap_frameworks:
                mapped = gsap_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"GSAP artifact count: {gsap_count}")

        # ==== RxJS Reactive Programming artifact counts (v4.78) ====
        rxjs_count = 0
        rxjs_artifacts = [
            "rxjs_operators", "rxjs_custom_operators", "rxjs_pipes",
            "rxjs_observables", "rxjs_subscriptions", "rxjs_conversions",
            "rxjs_subscription_mgmt", "rxjs_subjects", "rxjs_emissions",
            "rxjs_schedulers", "rxjs_testing", "rxjs_marbles",
            "rxjs_imports", "rxjs_integrations", "rxjs_types",
            "rxjs_deprecations",
        ]
        for attr in rxjs_artifacts:
            if hasattr(matrix, attr):
                rxjs_count += len(getattr(matrix, attr, []))

        if rxjs_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("rxjs")

        # Detect RxJS version
        rxjs_version = getattr(matrix, 'rxjs_version', '')
        if rxjs_version:
            context.frameworks.add(f'rxjs-{rxjs_version}')

        # Detect RxJS feature flags
        if getattr(matrix, 'rxjs_has_typescript', False):
            context.frameworks.add("rxjs-typescript")
        if getattr(matrix, 'rxjs_has_operators', False):
            context.frameworks.add("rxjs-operators")
        if getattr(matrix, 'rxjs_has_subjects', False):
            context.frameworks.add("rxjs-subjects")
        if getattr(matrix, 'rxjs_has_pipes', False):
            context.frameworks.add("rxjs-pipes")
        if getattr(matrix, 'rxjs_has_schedulers', False):
            context.frameworks.add("rxjs-schedulers")
        if getattr(matrix, 'rxjs_has_testing', False):
            context.frameworks.add("rxjs-testing")
        if getattr(matrix, 'rxjs_has_higher_order', False):
            context.frameworks.add("rxjs-higher-order")
        if getattr(matrix, 'rxjs_has_error_handling', False):
            context.frameworks.add("rxjs-error-handling")
        if getattr(matrix, 'rxjs_has_multicasting', False):
            context.frameworks.add("rxjs-multicasting")
        if getattr(matrix, 'rxjs_has_deprecations', False):
            context.frameworks.add("rxjs-deprecations")

        # Detect RxJS ecosystem frameworks
        rxjs_frameworks = getattr(matrix, 'rxjs_detected_frameworks', [])
        if rxjs_count >= SIGNIFICANCE_THRESHOLD and rxjs_frameworks:
            rxjs_fw_mapping = {
                'rxjs': 'rxjs',
                'rxjs-compat': 'rxjs-compat',
                'rxjs-marbles': 'rxjs-testing',
                'ngrx': 'ngrx',
                'ngxs': 'ngxs',
                'redux-observable': 'redux-observable',
                'rx-angular': 'rx-angular',
                'nestjs-rxjs': 'nestjs',
                'angular-rxjs': 'angular',
                'rxjs-websocket': 'rxjs-websocket',
                'rxjs-for-await': 'rxjs',
            }
            for fw in rxjs_frameworks:
                mapped = rxjs_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"RxJS artifact count: {rxjs_count}")

        # ==== Next.js artifact counts (v4.33) ====
        nextjs_count = 0
        nextjs_artifacts = [
            "nextjs_pages", "nextjs_layouts", "nextjs_loadings",
            "nextjs_errors", "nextjs_templates", "nextjs_metadata",
            "nextjs_segment_configs", "nextjs_route_handlers",
            "nextjs_api_routes", "nextjs_middleware",
            "nextjs_server_actions", "nextjs_form_actions",
            "nextjs_fetch_calls", "nextjs_caches", "nextjs_static_params",
        ]
        for attr in nextjs_artifacts:
            if hasattr(matrix, attr):
                nextjs_count += len(getattr(matrix, attr, []))

        # Also count config as an artifact
        if getattr(matrix, 'nextjs_config', None):
            nextjs_count += 1

        if nextjs_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("nextjs")

        # Detect Next.js ecosystem frameworks from detected_frameworks list
        nextjs_frameworks = getattr(matrix, 'nextjs_detected_frameworks', [])
        if nextjs_count >= SIGNIFICANCE_THRESHOLD and nextjs_frameworks:
            nextjs_fw_mapping = {
                'next': 'nextjs', 'next-server': 'nextjs',
                'next-navigation': 'nextjs', 'next-headers': 'nextjs',
                'next-cache': 'nextjs', 'next-router-pages': 'nextjs',
                'next-link': 'nextjs', 'next-image': 'nextjs',
                'next-script': 'nextjs', 'next-font': 'nextjs',
                'next-dynamic': 'nextjs', 'next-og': 'nextjs',
                'nextauth': 'nextauth', 'clerk': 'clerk',
                'supabase-auth': 'supabase', 'lucia': 'lucia',
                'kinde': 'kinde',
                'contentful': 'contentful', 'sanity': 'sanity',
                'strapi': 'strapi', 'payload': 'payload',
                'directus': 'directus',
                'prisma': 'prisma', 'drizzle': 'drizzle',
                'supabase': 'supabase', 'planetscale': 'planetscale',
                'neon': 'neon', 'vercel-postgres': 'vercel-postgres',
                'vercel-kv': 'vercel-kv', 'vercel-blob': 'vercel-blob',
                'upstash': 'upstash',
                'vercel': 'vercel',
                'vercel-analytics': 'vercel-analytics',
                'vercel-speed-insights': 'vercel-speed-insights',
                'posthog': 'posthog',
                'trpc': 'trpc',
                'react-email': 'react-email', 'resend': 'resend',
                'sentry': 'sentry', 'mdx': 'mdx',
                'next-intl': 'next-intl', 'next-i18next': 'next-i18next',
            }
            for fw in nextjs_frameworks:
                mapped = nextjs_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"Next.js artifact count: {nextjs_count}")

        # ==== Vue.js artifact counts (v4.34) ====
        vue_count = 0
        vue_artifacts = [
            "vue_components", "vue_async_components", "vue_custom_elements",
            "vue_composables", "vue_refs", "vue_computeds",
            "vue_watchers", "vue_lifecycle_hooks",
            "vue_directives", "vue_transitions",
            "vue_plugins", "vue_global_registrations",
            "vue_routes", "vue_guards", "vue_router_views",
        ]
        for attr in vue_artifacts:
            if hasattr(matrix, attr):
                vue_count += len(getattr(matrix, attr, []))

        if vue_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("vue")

        # Detect Vue ecosystem frameworks from detected_frameworks list
        vue_frameworks = getattr(matrix, 'vue_detected_frameworks', [])
        if vue_count >= SIGNIFICANCE_THRESHOLD and vue_frameworks:
            vue_fw_mapping = {
                'vue': 'vue', 'vue-router': 'vue-router',
                'pinia': 'pinia', 'vuex': 'vuex',
                'nuxt': 'nuxt', 'nuxt3': 'nuxt',
                'quasar': 'quasar', 'vuetify': 'vuetify',
                'element-plus': 'element-plus', 'element-ui': 'element-ui',
                'primevue': 'primevue', 'naive-ui': 'naive-ui',
                'ant-design-vue': 'ant-design-vue',
                'vueuse': 'vueuse', 'vue-i18n': 'vue-i18n',
                'vee-validate': 'vee-validate', 'formkit': 'formkit',
                'vue-query': 'tanstack-query',
                'vitest': 'vitest', 'vue-test-utils': 'vue-test-utils',
                'cypress': 'cypress',
                'tailwindcss': 'tailwind',
                'unocss': 'unocss', 'windicss': 'windicss',
                'vue-apollo': 'apollo', 'urql': 'urql',
                'swrv': 'swrv',
                'vite': 'vite',
                'webpack': 'webpack',
                'capacitor': 'capacitor', 'ionic-vue': 'ionic',
                'electron-vue': 'electron',
                'tauri': 'tauri',
                'storybook': 'storybook',
            }
            for fw in vue_frameworks:
                mapped = vue_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        logger.debug(f"Vue.js artifact count: {vue_count}")

        # ==== Svelte / SvelteKit artifact counts (v4.35) ====
        svelte_count = 0
        svelte_artifacts = [
            "svelte_components", "svelte_stores", "svelte_store_subscriptions",
            "svelte_actions", "svelte_routes", "svelte_load_functions",
            "svelte_form_actions", "svelte_hooks", "svelte_param_matchers",
            "svelte_lifecycle_hooks", "svelte_contexts", "svelte_runes",
        ]
        for attr in svelte_artifacts:
            if hasattr(matrix, attr):
                svelte_count += len(getattr(matrix, attr, []))

        if svelte_count >= SIGNIFICANCE_THRESHOLD:
            context.frameworks.add("svelte")

        # Detect Svelte ecosystem frameworks from detected_frameworks list
        svelte_frameworks = getattr(matrix, 'svelte_detected_frameworks', [])
        if svelte_count >= SIGNIFICANCE_THRESHOLD and svelte_frameworks:
            svelte_fw_mapping = {
                'svelte': 'svelte', 'sveltekit': 'sveltekit',
                'skeleton': 'skeleton-ui', 'shadcn-svelte': 'shadcn-svelte',
                'flowbite-svelte': 'flowbite-svelte', 'daisyui': 'daisyui',
                'melt-ui': 'melt-ui', 'bits-ui': 'bits-ui',
                'superforms': 'superforms', 'formsnap': 'formsnap',
                'lucia': 'lucia-auth', 'authjs': 'authjs',
                'houdini': 'houdini', 'urql': 'urql',
                'tanstack-query': 'tanstack-query', 'svelte-query': 'tanstack-query',
                'trpc-svelte': 'trpc',
                'threlte': 'threlte', 'svelte-cubed': 'svelte-cubed',
                'motion': 'svelte-motion', 'svelte-motion': 'svelte-motion',
                'svelte-i18n': 'svelte-i18n', 'paraglide': 'paraglide',
                'inlang': 'inlang',
                'vitest': 'vitest', 'playwright': 'playwright',
                'testing-library': 'testing-library',
                'svelte-check': 'svelte-check',
                'tailwindcss': 'tailwind', 'unocss': 'unocss',
                'postcss': 'postcss',
                'mdsvex': 'mdsvex',
                'vite': 'vite',
                'drizzle': 'drizzle', 'prisma': 'prisma',
                'supabase': 'supabase',
                'tauri': 'tauri', 'capacitor': 'capacitor',
                'storybook': 'storybook',
                'histoire': 'histoire',
            }
            for fw in svelte_frameworks:
                mapped = svelte_fw_mapping.get(fw)
                if mapped:
                    context.frameworks.add(mapped)

        # Check SvelteKit specifically
        if getattr(matrix, 'sveltekit_version', None):
            context.frameworks.add("sveltekit")

        logger.debug(f"Svelte artifact count: {svelte_count}")

        # ==== DETECT FRAMEWORKS FROM DEPENDENCIES ====
        python_framework_mapping = {
            "fastapi": "fastapi",
            "django": "django",
            "flask": "flask",
            "pytorch": "torch",
            "tensorflow": "tensorflow",
            "pandas": "pandas",
            "sqlalchemy": "sqlalchemy",
            "pydantic": "pydantic",
            "celery": "celery",
            "pytest": "pytest",
            "numpy": "numpy",
            "scipy": "scipy",
            "sklearn": "scikit-learn",
            "langchain": "langchain",
            "transformers": "transformers",
        }

        for framework, dep_name in python_framework_mapping.items():
            if dep_name in context.dependencies:
                context.frameworks.add(framework)

        js_framework_mapping = {
            # Frontend Frameworks
            "angular": ["@angular/core", "@angular/common", "@angular/router"],
            "react": ["react", "react-dom"],
            "vue": ["vue"],
            "svelte": ["svelte"],
            "nextjs": ["next"],
            # Backend Frameworks
            "nestjs": ["@nestjs/core", "@nestjs/common"],
            "express": ["express"],
            "fastify": ["fastify"],
            "koa": ["koa"],
            # State Management
            "ngrx": ["@ngrx/store", "@ngrx/effects"],
            "redux": ["redux", "@reduxjs/toolkit"],
            "mobx": ["mobx"],
            "zustand": ["zustand"],
            # TypeScript
            "typescript": ["typescript"],
            # Testing
            "jest": ["jest", "@jest/core"],
            "vitest": ["vitest"],
            "cypress": ["cypress"],
            "playwright": ["@playwright/test", "playwright"],
            # Build Tools
            "vite": ["vite"],
            "webpack": ["webpack"],
            # GraphQL
            "graphql": ["graphql", "@apollo/client", "apollo-server"],
            # ORM/Database
            "prisma": ["@prisma/client", "prisma"],
            "typeorm": ["typeorm"],
            "mongoose": ["mongoose"],
            # Real-time
            "socketio": ["socket.io", "socket.io-client"],
            # Animation
            "gsap": ["gsap"],
            # Reactive
            "rxjs": ["rxjs"],
        }

        for framework, dep_names in js_framework_mapping.items():
            if any(dep in context.dependencies for dep in dep_names):
                context.frameworks.add(framework)

        # ==== DETECT SPECIFIC PYTHON FRAMEWORKS FROM ARTIFACTS ====
        if hasattr(matrix, "python_fastapi_endpoints") and matrix.python_fastapi_endpoints:
            context.frameworks.add("fastapi")
            context.frameworks.add("python")

        if hasattr(matrix, "python_flask_routes") and matrix.python_flask_routes:
            context.frameworks.add("flask")
            context.frameworks.add("python")

        # ==== FALLBACK: If no frameworks detected, use raw presence ====
        if not context.frameworks:
            if python_count > 0:
                context.frameworks.add("python")
            if ts_count > 0:
                context.frameworks.add("typescript")

        # Detect patterns from matrix
        if hasattr(matrix, "patterns"):
            context.patterns = set(matrix.patterns)

        # Check for tests
        if hasattr(matrix, "tests") and matrix.tests:
            context.has_tests = True
        if "pytest" in context.dependencies or "jest" in context.frameworks:
            context.has_tests = True

        # Check for async usage
        if hasattr(matrix, "async_patterns") and matrix.async_patterns:
            context.has_async = True
        if "fastapi" in context.frameworks or "aiohttp" in context.dependencies:
            context.has_async = True
        if "nestjs" in context.frameworks:
            context.has_async = True

        # Extract file types
        if hasattr(matrix, "file_types"):
            context.file_types = set(matrix.file_types)

        return context


class PracticeSelector:
    """Selects best practices based on project context.

    The selector uses the project context to determine which practices
    are applicable and prioritizes them based on relevance.

    Attributes:
        repository: The practices repository to select from.

    Example:
        >>> selector = PracticeSelector()
        >>> criteria = SelectionCriteria(
        ...     categories=[PracticeCategory.TYPE_SAFETY],
        ...     min_priority=PracticePriority.HIGH
        ... )
        >>> practices = selector.select(context, criteria)
    """

    def __init__(self, repository: Optional[BestPracticesRepository] = None) -> None:
        """Initialize the selector.

        Args:
            repository: Repository to select from. Uses default if None.
        """
        self._repository = repository

    @property
    def repository(self) -> BestPracticesRepository:
        """Get the repository, loading default if needed."""
        if self._repository is None:
            self._repository = get_repository()
        return self._repository

    def select(
        self,
        context: ProjectContext,
        criteria: Optional[SelectionCriteria] = None,
    ) -> BPLOutput:
        """Select practices based on context and criteria.

        Args:
            context: The project context.
            criteria: Selection criteria. Uses defaults if None.

        Returns:
            BPLOutput with selected practices.
        """
        if criteria is None:
            criteria = SelectionCriteria()

        t_start = time.perf_counter()

        # Get all practices
        all_practices = list(self.repository.iter_practices())
        total_available = len(all_practices)

        # Filter by applicability
        applicable = self._filter_applicable(all_practices, context, criteria)
        logger.debug(
            f"Filter stage 1 (applicability): {total_available} → {len(applicable)} practices"
        )

        # Filter by criteria
        filtered = self._filter_by_criteria(applicable, criteria)
        logger.debug(
            f"Filter stage 2 (criteria): {len(applicable)} → {len(filtered)} practices"
        )

        # Score and sort
        scored = self._score_practices(filtered, context, criteria)

        # v4.8: Limit generic practices when language-specific ones exist.
        # Generic practices (DP*, SOLID*, DB*, DEVOPS*) use Python code examples
        # which are misleading for non-Python projects. Cap generic practices to
        # at most 30% of the output, preferring language-specific ones.
        language_specific = [p for p in scored if self._get_practice_frameworks(p)]
        generic = [p for p in scored if not self._get_practice_frameworks(p)]

        if language_specific and generic:
            max_generic = max(3, len(language_specific) // 3)  # At most 1/3 of language-specific count
            scored = language_specific + generic[:max_generic]

        # Limit results
        limited = scored[: criteria.max_practices]

        # Enforce token budget if set
        if criteria.max_tokens is not None:
            limited = self._enforce_token_budget(limited, criteria.max_tokens)

        logger.debug(
            f"Filter stage 3 (limit): {len(scored)} → {len(limited)} practices"
        )

        t_elapsed = time.perf_counter() - t_start
        logger.info(
            f"Selected {len(limited)}/{total_available} practices in {t_elapsed:.3f}s "
            f"(context: {self._summarize_context(context)})"
        )

        # Build output
        return BPLOutput(
            practices=limited,
            total_available=total_available,
            filters_applied=self._describe_filters(criteria),
            context_summary=self._summarize_context(context),
        )

    def select_for_project(
        self,
        matrix: Any,
        criteria: Optional[SelectionCriteria] = None,
    ) -> BPLOutput:
        """Select practices for a project based on its matrix.

        Convenience method that builds context from ProjectMatrix.

        Args:
            matrix: ProjectMatrix from CodeTrellis scanner.
            criteria: Selection criteria.

        Returns:
            BPLOutput with selected practices.
        """
        context = ProjectContext.from_matrix(matrix)
        return self.select(context, criteria)

    def _get_practice_frameworks(self, practice: BestPractice) -> Set[str]:
        """Determine which frameworks a practice applies to from its ID prefix.

        Practice ID prefixes map to frameworks:
        - NG* -> angular, typescript
        - TS* -> typescript
        - PY*, PYE* -> python
        - DP* -> generic (design patterns apply to all)
        - NEST* -> nestjs, typescript
        - REACT* -> react, typescript

        Args:
            practice: The practice to check.

        Returns:
            Set of framework names this practice applies to.
        """
        practice_id = practice.id.upper()

        # Map of ID prefixes to required frameworks
        prefix_framework_map = {
            "NG": {"angular", "typescript"},
            "TS": {"typescript"},
            "PY": {"python"},
            "PYE": {"python"},  # Python expanded
            "DP": set(),  # Design patterns are generic
            "SOLID": set(),  # SOLID patterns are generic
            "NEST": {"nestjs", "typescript"},
            "REACT": {"react", "typescript"},
            "FLASK": {"flask", "python"},
            "DJANGO": {"django", "python"},
            "FAST": {"fastapi", "python"},
            "DB": set(),  # Database practices are generic
            "DEVOPS": set(),  # DevOps practices are generic
            "GORM": {"gorm", "golang"},    # GORM ORM (v5.2) — must precede GO
            "GRPCGO": {"grpc_go", "golang"},  # gRPC-Go framework (v5.2)
            "GO": {"golang"},  # Go language practices (G-17)
            "GIN": {"gin", "golang"},  # Gin framework
            "ECHO": {"echo", "golang"},  # Echo framework
            "FIBER": {"fiber", "golang"},  # Fiber framework (v5.2)
            "CHI": {"chi", "golang"},      # Chi router (v5.2)
            "COBRA": {"cobra", "golang"},  # Cobra CLI framework (v5.2)
            "JAVA": {"java"},  # Java language practices (v4.12)
            "SPRING": {"spring", "java"},  # Spring framework
            "JPA": {"jpa", "java"},  # JPA/Hibernate practices
            "QUARKUS": {"quarkus", "java"},  # Quarkus framework
            "MICRONAUT": {"micronaut", "java"},  # Micronaut framework
            "CS": {"csharp"},              # C# language practices (v4.13)
            "ASPNET": {"aspnet", "csharp"},  # ASP.NET Core
            "EF": {"efcore", "csharp"},    # Entity Framework Core
            "BLAZOR": {"blazor", "csharp"},  # Blazor framework
            "SIGNALR": {"signalr", "csharp"},  # SignalR
            "MAUI": {"maui", "csharp"},    # MAUI
            "RS": {"rust"},                # Rust language practices (v4.14)
            "ACTIX": {"actix", "rust"},    # actix-web framework
            "ROCKET": {"rocket", "rust"},  # Rocket framework
            "AXUM": {"axum", "rust"},      # Axum framework
            "WARP": {"warp", "rust"},      # Warp framework
            "TOKIO": {"tokio", "rust"},    # Tokio async runtime
            "DIESEL": {"diesel", "rust"},  # Diesel ORM
            "SEAORM": {"sea_orm", "rust"},  # SeaORM async ORM (v5.4)
            "TAURI": {"tauri", "rust"},     # Tauri desktop framework (v5.4)
            "TONIC": {"tonic", "rust"},    # Tonic gRPC
            "SQLX": {"sqlx_go", "golang"},   # sqlx Go SQL extensions (v5.2) — must precede SQL
            "SQL": {"sql"},                # SQL language practices (v4.15)
            "PG": {"postgresql", "sql"},   # PostgreSQL-specific
            "MYSQL": {"mysql", "sql"},     # MySQL-specific
            "TSQL": {"sqlserver", "sql"},  # SQL Server / T-SQL
            "ORA": {"oracle", "sql"},      # Oracle / PL/SQL
            "SQLITE": {"sqlite", "sql"},   # SQLite-specific
            "HTML": {"html"},              # HTML language practices (v4.16)
            "A11Y": {"html"},              # Accessibility practices
            "SEO": {"html"},               # SEO practices
            "TMPL": {"html"},              # Template engine practices
            "CSS": {"css"},                # CSS language practices (v4.17)
            "SASS": {"sass"},              # Sass/SCSS language practices (v4.44)
            "LESS": {"less"},              # Less CSS language practices (v4.45)
            "PCSS": {"postcss"},           # PostCSS language practices (v4.46)
            "BASH": {"bash"},              # Bash/Shell language practices (v4.18)
            "SH": {"bash"},                # POSIX shell practices
            "ZSH": {"zsh", "bash"},        # Zsh-specific practices
            "KSH": {"ksh", "bash"},        # Ksh-specific practices
            "C": {"c"},                    # C language practices (v4.19)
            "POSIX": {"posix", "c"},       # POSIX C practices
            "GLIB": {"glib", "c"},         # GLib framework practices
            "OPENSSL": {"openssl", "c"},   # OpenSSL practices
            "CPP": {"cpp"},                # C++ language practices (v4.20)
            "QT": {"qt", "cpp"},           # Qt framework practices
            "BOOST": {"boost", "cpp"},     # Boost library practices
            "CUDA": {"cuda", "cpp"},       # CUDA practices
            "SWIFT": {"swift"},              # Swift language practices (v4.22)
            "VAPOR": {"vapor", "swift"},     # Vapor framework
            "SWIFTUI": {"swiftui", "swift"}, # SwiftUI framework
            "COMBINE": {"combine", "swift"}, # Combine framework
            "RB": {"ruby"},                  # Ruby language practices (v4.23)
            "RAILS": {"rails", "ruby"},      # Rails framework
            "SINATRA": {"sinatra", "ruby"},  # Sinatra framework
            "GRAPE": {"grape", "ruby"},      # Grape API framework
            "HANAMI": {"hanami", "ruby"},    # Hanami framework
            "SCALA": {"scala"},                  # Scala language practices (v4.25)
            "PLAY": {"play", "scala"},           # Play Framework
            "AKKA": {"akka", "scala"},           # Akka toolkit
            "ZIO": {"zio", "scala"},             # ZIO effect system
            "HTTP4S": {"http4s", "scala"},       # http4s server
            "TAPIR": {"tapir", "scala"},         # Tapir endpoints
            "R": {"rlang"},                          # R language practices (v4.26)
            "SHINY": {"shiny", "rlang"},             # Shiny framework
            "PLUMBER": {"plumber", "rlang"},         # Plumber REST API
            "GOLEM": {"golem", "rlang"},             # Golem framework
            "TIDY": {"tidyverse", "rlang"},          # tidyverse practices
            "DART": {"dart"},                            # Dart language practices (v4.27)
            "FLUTTER": {"flutter", "dart"},              # Flutter framework
            "RIVERPOD": {"riverpod", "dart"},            # Riverpod state management
            "BLOC": {"bloc", "dart"},                    # Bloc state management
            "SHELF": {"shelf", "dart"},                  # Shelf server framework
            "DART_FROG": {"dart_frog", "dart"},          # Dart Frog server framework
            "SERVERPOD": {"serverpod", "dart"},          # Serverpod server framework
            "LUA": {"lua"},                                  # Lua language practices (v4.28)
            "LOVE": {"love2d", "lua"},                       # LÖVE2D game framework
            "OPENRESTY": {"openresty", "lua"},               # OpenResty/nginx-lua
            "LAPIS": {"lapis", "lua"},                       # Lapis web framework
            "TARANTOOL": {"tarantool", "lua"},               # Tarantool database
            "PS": {"powershell"},                                # PowerShell practices (v4.29)
            "PODE": {"pode", "powershell"},                      # Pode web framework
            "DSC": {"dsc", "powershell"},                        # DSC configuration
            "PESTER": {"pester", "powershell"},                  # Pester testing
            "AZURE": {"azure", "powershell"},                    # Azure PowerShell
            "JS": {"javascript"},                                    # JavaScript practices (v4.30)
            "EXPRESS": {"express", "javascript"},                    # Express.js framework
            "MONGOOSE": {"mongoose", "javascript"},                  # Mongoose ODM
            "NODE": {"node", "javascript"},                          # Node.js platform
            "NESTJS": {"nestjs", "typescript"},                          # NestJS framework
            "ANGULAR": {"angular", "typescript"},                        # Angular framework
            "TRPC": {"trpc", "typescript"},                              # tRPC API framework
            "TYPEORM": {"typeorm", "typescript"},                        # TypeORM ORM
            "PRISMA_TS": {"prisma", "typescript"},                       # Prisma with TypeScript
            "DRIZZLE": {"drizzle", "typescript"},                        # Drizzle ORM
            "ZOD": {"zod", "typescript"},                                # Zod validation
            "VUE": {"vue"},                                                      # Vue.js practices (v4.34)
            "NUXT": {"nuxt", "vue"},                                             # Nuxt framework
            "PINIA": {"pinia", "vue"},                                           # Pinia state management
            "VUEX": {"vuex", "vue"},                                             # Vuex state management
            "VUETIFY": {"vuetify", "vue"},                                       # Vuetify UI framework
            "QUASAR": {"quasar", "vue"},                                         # Quasar framework
            "MUI": {"mui", "react"},                                                     # Material UI practices (v4.36)
            "ANTD": {"antd", "react"},                                                   # Ant Design practices (v4.37)
            "CHAKRA": {"chakra-ui", "react"},                                              # Chakra UI practices (v4.38)
            "RADIX": {"radix-ui", "react"},                                                # Radix UI practices (v4.41)
            "REDUX": {"redux", "react"},                                                       # Redux / RTK practices (v4.47)
            "ZUSTAND": {"zustand", "react"},                                                   # Zustand practices (v4.48)
            "JOTAI": {"jotai", "react"},                                                       # Jotai practices (v4.49)
            "RECOIL": {"recoil", "react"},                                                     # Recoil practices (v4.50)
            "SOLIDJS": {"solidjs"},                                                                # Solid.js practices (v4.62)
            "HTMX": {"htmx"},                                                                          # HTMX practices (v4.67)
            "STIM": {"stimulus"},                                                                        # Stimulus / Hotwire practices (v4.68)
            "SB": {"storybook"},                                                                             # Storybook practices (v4.70)
            "GSAP": {"gsap"},                                                                                # GSAP animation library (v4.77)
            "RXJS": {"rxjs"},                                                                                # RxJS reactive programming (v4.78)
        }

        # Check explicit applicability first
        if practice.applicability.frameworks:
            return set(practice.applicability.frameworks)

        # Determine from prefix
        for prefix, frameworks in prefix_framework_map.items():
            if practice_id.startswith(prefix):
                return frameworks

        # Default: generic practice
        return set()

    def _filter_applicable(
        self,
        practices: List[BestPractice],
        context: ProjectContext,
        criteria: SelectionCriteria,
    ) -> List[BestPractice]:
        """Filter practices by applicability to context.

        Uses a smart filtering approach:
        1. Practices with explicit applicability.frameworks are checked against context
        2. Practices with framework-specific ID prefixes (NG*, TS*, PY*) are filtered by prefix
        3. Generic practices (DP*) are always included if include_generic is True

        Args:
            practices: All practices to filter.
            context: The project context.
            criteria: Selection criteria.

        Returns:
            List of applicable practices.
        """
        result = []
        context_dict = context.to_dict()
        python_version = criteria.python_version or context.python_version
        context_frameworks = context.frameworks

        # Determine which language families are in use
        has_python = any(f in context_frameworks for f in ["python", "fastapi", "django", "flask", "pytorch", "pandas"])
        # v4.30 fix: Only detect TypeScript when 'typescript' is explicitly present
        # OR when TS-only frameworks (angular, nestjs) are present. Don't trigger
        # on react/vue/nextjs alone — those can be pure JavaScript projects.
        has_typescript = (
            "typescript" in context_frameworks
            or "angular" in context_frameworks
            or "nestjs" in context_frameworks
        )
        has_angular = "angular" in context_frameworks
        has_nestjs = "nestjs" in context_frameworks
        has_react = "react" in context_frameworks
        has_golang = any(f in context_frameworks for f in ["golang", "gin", "echo", "fiber", "chi", "grpc_go", "gorm", "sqlx_go", "cobra"])
        has_java = any(f in context_frameworks for f in ["java", "spring", "quarkus", "micronaut", "jpa", "hibernate"])
        has_csharp = any(f in context_frameworks for f in ["csharp", "aspnet", "efcore", "blazor", "signalr", "maui"])
        has_rust = any(f in context_frameworks for f in ["rust", "actix", "rocket", "axum", "warp", "tokio", "tonic", "diesel", "sea_orm", "sqlx", "tauri"])
        has_c = "c" in context_frameworks
        has_cpp = any(f in context_frameworks for f in ["cpp", "qt", "boost", "boost_asio", "crow", "pistache", "drogon", "cuda", "opengl", "vulkan", "unreal"])
        has_swift = any(f in context_frameworks for f in ["swift", "swiftui", "vapor", "combine", "core_data", "swift_data", "hummingbird", "alamofire", "tca"])
        has_ruby = any(f in context_frameworks for f in ["ruby", "rails", "sinatra", "grape", "hanami", "roda", "sidekiq", "activerecord", "sequel", "mongoid"])
        has_php = any(f in context_frameworks for f in ["php", "laravel", "symfony", "codeigniter", "slim", "cakephp", "wordpress", "drupal"])
        has_scala = any(f in context_frameworks for f in ["scala", "play", "akka", "akka_http", "zio", "zio_http", "http4s", "cats", "cats_effect", "tapir", "spark", "slick", "doobie"])
        has_r = any(f in context_frameworks for f in ["rlang", "shiny", "plumber", "golem", "rhino", "tidyverse", "data_table", "r6", "r7", "dbi", "sparklyr", "arrow", "tidymodels", "caret", "rcpp", "targets", "rmarkdown", "quarto"])
        has_dart = any(f in context_frameworks for f in ["dart", "flutter", "riverpod", "bloc", "getx", "provider", "shelf", "dart_frog", "serverpod", "drift", "freezed", "dio", "firebase"])
        has_lua = any(f in context_frameworks for f in ["lua", "love2d", "openresty", "lapis", "lor", "tarantool", "luajit", "corona", "solar2d", "defold", "busted", "pgmoon", "turbo"])
        has_powershell = any(f in context_frameworks for f in ["powershell", "pode", "polaris", "universaldashboard", "dsc", "pester", "azure", "aws", "msgraph", "psake", "invokebuild", "secretmanagement", "dbatools", "psframework"])
        has_javascript = any(f in context_frameworks for f in ["javascript", "express", "fastify", "koa", "hapi", "react", "vue", "svelte", "nextjs", "nuxt", "gatsby", "remix", "astro", "solidjs", "mongoose", "sequelize", "prisma", "jest", "mocha", "vitest", "socketio", "apollo", "redux", "zustand", "electron", "mui"])
        has_vue = any(f in context_frameworks for f in ["vue", "nuxt", "pinia", "vuex", "vuetify", "quasar", "element-plus", "primevue", "naive-ui", "vueuse"])
        has_mui = any(f in context_frameworks for f in ["mui", "mui-base", "mui-joy", "mui-x-data-grid", "mui-x-date-pickers", "material-ui", "pigment-css"])
        has_antd = any(f in context_frameworks for f in ["antd", "antd-pro", "antd-mobile", "antd-icons", "antd-charts", "antd-style", "umi", "ahooks"])
        has_radix = any(f in context_frameworks for f in ["radix-ui", "radix-themes", "radix-colors", "radix-icons"])
        has_redux = any(f in context_frameworks for f in ["redux", "redux-toolkit", "redux-toolkit-v1", "redux-toolkit-v2", "redux-legacy", "react-redux", "rtk-query", "redux-saga", "redux-observable", "redux-persist"])
        has_zustand = any(f in context_frameworks for f in ["zustand", "zustand-v3", "zustand-v4", "zustand-v5", "zustand-legacy", "zustand-middleware", "zustand-persist", "zustand-devtools", "zustand-immer", "zundo"])
        has_jotai = any(f in context_frameworks for f in ["jotai", "jotai-v1", "jotai-v2", "jotai-utils", "jotai-vanilla", "jotai-devtools", "jotai-immer", "jotai-optics", "jotai-xstate", "jotai-effect", "jotai-tanstack-query", "jotai-trpc", "jotai-molecules", "jotai-scope", "jotai-location", "jotai-valtio"])
        has_recoil = any(f in context_frameworks for f in ["recoil", "recoil-0.0", "recoil-0.1", "recoil-0.2", "recoil-0.3", "recoil-0.4", "recoil-0.5", "recoil-0.6", "recoil-0.7", "recoil-sync", "recoil-relay", "recoil-nexus", "recoil-persist", "recoiljs-refine"])
        has_xstate = any(f in context_frameworks for f in ["xstate", "xstate-v3", "xstate-v4", "xstate-v5", "xstate-react", "xstate-vue", "xstate-svelte", "xstate-solid", "xstate-inspect", "xstate-test", "xstate-graph", "xstate-store", "xstate-immer", "stately-inspect"])
        has_solidjs = any(f in context_frameworks for f in ["solidjs", "solid-js", "solid-start", "solidjs-router", "solid-app-router", "@solidjs/router", "@solidjs/start", "vinxi", "kobalte", "solid-primitives"])
        has_stimulus = any(f in context_frameworks for f in ["stimulus", "turbo", "turbo-rails", "strada", "hotwire", "stimulus-use", "stimulus-components", "stimulus-webpack", "stimulus-vite", "stimulus-loading"])
        has_gsap = any(f in context_frameworks for f in ["gsap", "gsap-scrolltrigger", "gsap-scrollsmoother", "gsap-draggable", "gsap-flip", "gsap-observer", "gsap-plugins", "gsap-context", "gsap-matchmedia", "gsap-react", "gsap-club"])
        has_rxjs = any(f in context_frameworks for f in ["rxjs", "rxjs-operators", "rxjs-subjects", "rxjs-pipes", "rxjs-schedulers", "rxjs-testing", "rxjs-higher-order", "rxjs-error-handling", "rxjs-multicasting"])

        logger.debug(f"Context frameworks: {context_frameworks}")
        logger.debug(f"Has Python: {has_python}, Has TypeScript: {has_typescript}, Has Angular: {has_angular}, Has Go: {has_golang}, Has Java: {has_java}, Has C#: {has_csharp}, Has Rust: {has_rust}, Has C: {has_c}, Has C++: {has_cpp}, Has Swift: {has_swift}, Has Ruby: {has_ruby}, Has PHP: {has_php}, Has Scala: {has_scala}, Has R: {has_r}, Has Dart: {has_dart}, Has Lua: {has_lua}, Has PowerShell: {has_powershell}, Has JavaScript: {has_javascript}, Has Redux: {has_redux}, Has Zustand: {has_zustand}, Has Jotai: {has_jotai}, Has Recoil: {has_recoil}, Has SolidJS: {has_solidjs}, Has Stimulus: {has_stimulus}, Has GSAP: {has_gsap}, Has RxJS: {has_rxjs}")

        for practice in practices:
            # Skip deprecated
            if practice.deprecated:
                continue

            # Check Python version compatibility (skip for non-Python practices)
            practice_id = practice.id.upper()
            is_python_practice = practice_id.startswith("PY")
            if is_python_practice and not practice.python_version.is_compatible(python_version):
                continue

            # Get frameworks this practice applies to
            practice_frameworks = self._get_practice_frameworks(practice)

            # If practice has no framework requirements, it's generic
            if not practice_frameworks:
                if criteria.include_generic:
                    result.append(practice)
                continue

            # Check if practice's required frameworks match context
            # Angular practices: require angular in context
            if "angular" in practice_frameworks:
                if has_angular:
                    result.append(practice)
                continue

            # NestJS practices: require nestjs in context
            if "nestjs" in practice_frameworks:
                if has_nestjs:
                    result.append(practice)
                continue

            # React practices: require react in context
            # NOTE: More-specific React-based frameworks (MUI, ANTD, Radix, Chakra)
            # must be checked BEFORE the generic React check, because their
            # prefix_framework_map includes "react" in the set.
            if "react" in practice_frameworks:
                # Radix UI practices: require radix-ui in context (v4.41)
                if "radix-ui" in practice_frameworks:
                    if has_radix:
                        result.append(practice)
                    continue

                # MUI practices: require mui in context (v4.36)
                if "mui" in practice_frameworks:
                    if has_mui:
                        result.append(practice)
                    continue

                # Ant Design practices: require antd in context (v4.37)
                if "antd" in practice_frameworks:
                    if has_antd:
                        result.append(practice)
                    continue

                # Chakra UI practices: require chakra-ui in context (v4.38)
                if "chakra-ui" in practice_frameworks:
                    if any(f in context_frameworks for f in ["chakra-ui", "chakra-icons", "chakra-theme-tools"]):
                        result.append(practice)
                    continue

                # Redux / RTK practices: require redux in context (v4.47)
                if "redux" in practice_frameworks:
                    if has_redux:
                        result.append(practice)
                    continue

                # Zustand practices: require zustand in context (v4.48)
                if "zustand" in practice_frameworks:
                    if has_zustand:
                        result.append(practice)
                    continue

                # Jotai practices: require jotai in context (v4.49)
                if "jotai" in practice_frameworks:
                    if has_jotai:
                        result.append(practice)
                    continue

                # Recoil practices: require recoil in context (v4.50)
                if "recoil" in practice_frameworks:
                    if has_recoil:
                        result.append(practice)
                    continue

                # XState practices: require xstate in context (v4.55)
                if "xstate" in practice_frameworks:
                    if has_xstate:
                        result.append(practice)
                    continue

                # Generic React practices
                if has_react:
                    result.append(practice)
                continue

            # XState practices (standalone, without react): require xstate in context (v4.55)
            if "xstate" in practice_frameworks and "react" not in practice_frameworks:
                if has_xstate:
                    result.append(practice)
                continue

            # Solid.js practices: require solidjs in context (v4.62)
            if "solidjs" in practice_frameworks:
                if has_solidjs:
                    result.append(practice)
                continue

            # Stimulus / Hotwire practices: require stimulus in context (v4.68)
            if "stimulus" in practice_frameworks:
                if has_stimulus:
                    result.append(practice)
                continue

            # GSAP animation library practices: require gsap in context (v4.77)
            if "gsap" in practice_frameworks:
                if has_gsap:
                    result.append(practice)
                continue

            # RxJS reactive programming practices: require rxjs in context (v4.78)
            if "rxjs" in practice_frameworks:
                if has_rxjs:
                    result.append(practice)
                continue

            # Vue.js practices: require vue in context (v4.34)
            # Sub-framework checks: Nuxt, Pinia, Vuex, Vuetify, Quasar
            if "vue" in practice_frameworks:
                if not has_vue:
                    continue
                # Nuxt-specific practices
                if "nuxt" in practice_frameworks:
                    if "nuxt" not in context_frameworks:
                        continue
                # Pinia-specific practices
                if "pinia" in practice_frameworks:
                    if "pinia" not in context_frameworks:
                        continue
                # Vuex-specific practices
                if "vuex" in practice_frameworks:
                    if "vuex" not in context_frameworks:
                        continue
                # Vuetify-specific practices
                if "vuetify" in practice_frameworks:
                    if "vuetify" not in context_frameworks:
                        continue
                # Quasar-specific practices
                if "quasar" in practice_frameworks:
                    if "quasar" not in context_frameworks:
                        continue
                result.append(practice)
                continue

            # Python practices: require python/python-framework in context
            if "python" in practice_frameworks:
                if has_python:
                    result.append(practice)
                continue

            # Go practices: require golang in context (G-17)
            if "golang" in practice_frameworks:
                if has_golang:
                    result.append(practice)
                continue

            # Java practices: require java in context (v4.12)
            if "java" in practice_frameworks:
                if has_java:
                    result.append(practice)
                continue

            # C# practices: require csharp in context (v4.13)
            if "csharp" in practice_frameworks:
                if has_csharp:
                    result.append(practice)
                continue

            # Rust practices: require rust in context (v4.14)
            if "rust" in practice_frameworks:
                if has_rust:
                    result.append(practice)
                continue

            # C practices: require c in context (v4.19)
            if "c" in practice_frameworks and "cpp" not in practice_frameworks:
                if has_c:
                    result.append(practice)
                continue

            # C++ practices: require cpp in context (v4.20)
            if "cpp" in practice_frameworks:
                if has_cpp:
                    result.append(practice)
                continue

            # Swift practices: require swift in context (v4.22)
            # Sub-framework checks: Vapor, SwiftUI, Combine require specific framework
            if "swift" in practice_frameworks:
                if not has_swift:
                    continue
                # Vapor-specific practices: only include if vapor is in context
                if "vapor" in practice_frameworks:
                    if "vapor" not in context_frameworks:
                        continue
                # SwiftUI-specific practices: only include if swiftui is in context
                if "swiftui" in practice_frameworks:
                    if "swiftui" not in context_frameworks:
                        continue
                # Combine-specific practices: only include if combine is in context
                if "combine" in practice_frameworks:
                    if "combine" not in context_frameworks:
                        continue
                result.append(practice)
                continue

            # Ruby practices: require ruby in context (v4.23)
            # Sub-framework checks: Rails, Sinatra, Grape, Hanami
            if "ruby" in practice_frameworks:
                if not has_ruby:
                    continue
                # Rails-specific practices: only include if rails is in context
                if "rails" in practice_frameworks:
                    if "rails" not in context_frameworks:
                        continue
                # Sinatra-specific practices: only include if sinatra is in context
                if "sinatra" in practice_frameworks:
                    if "sinatra" not in context_frameworks:
                        continue
                # Grape-specific practices: only include if grape is in context
                if "grape" in practice_frameworks:
                    if "grape" not in context_frameworks:
                        continue
                # Hanami-specific practices: only include if hanami is in context
                if "hanami" in practice_frameworks:
                    if "hanami" not in context_frameworks:
                        continue
                result.append(practice)
                continue

            # PHP practices: require php in context (v4.24)
            # Sub-framework checks: Laravel, Symfony, CodeIgniter, Slim, WordPress (v5.3)
            if "php" in practice_frameworks:
                if not has_php:
                    continue
                if "laravel" in practice_frameworks:
                    if "laravel" not in context_frameworks:
                        continue
                if "symfony" in practice_frameworks:
                    if "symfony" not in context_frameworks:
                        continue
                if "codeigniter" in practice_frameworks:
                    if "codeigniter" not in context_frameworks:
                        continue
                if "slim" in practice_frameworks:
                    if "slim" not in context_frameworks:
                        continue
                if "wordpress" in practice_frameworks:
                    if "wordpress" not in context_frameworks:
                        continue
                result.append(practice)
                continue

            # Scala practices: require scala in context (v4.25)
            # Sub-framework checks: Play, Akka, ZIO, http4s, Tapir
            if "scala" in practice_frameworks:
                if not has_scala:
                    continue
                if "play" in practice_frameworks:
                    if "play" not in context_frameworks:
                        continue
                if "akka" in practice_frameworks:
                    if "akka" not in context_frameworks:
                        continue
                if "zio" in practice_frameworks:
                    if "zio" not in context_frameworks:
                        continue
                if "http4s" in practice_frameworks:
                    if "http4s" not in context_frameworks:
                        continue
                if "tapir" in practice_frameworks:
                    if "tapir" not in context_frameworks:
                        continue
                result.append(practice)
                continue

            # R practices: require rlang in context (v4.26)
            # Sub-framework checks: Shiny, Plumber, Golem, tidyverse
            if "rlang" in practice_frameworks:
                if not has_r:
                    continue
                # Shiny-specific practices: only include if shiny is in context
                if "shiny" in practice_frameworks:
                    if "shiny" not in context_frameworks:
                        continue
                # Plumber-specific practices: only include if plumber is in context
                if "plumber" in practice_frameworks:
                    if "plumber" not in context_frameworks:
                        continue
                # Golem-specific practices: only include if golem is in context
                if "golem" in practice_frameworks:
                    if "golem" not in context_frameworks:
                        continue
                # tidyverse-specific practices: only include if tidyverse is in context
                if "tidyverse" in practice_frameworks:
                    if "tidyverse" not in context_frameworks:
                        continue
                result.append(practice)
                continue

            # Dart practices: require dart in context (v4.27)
            # Sub-framework checks: Flutter, Riverpod, Bloc, Shelf, Dart Frog, Serverpod
            if "dart" in practice_frameworks:
                if not has_dart:
                    continue
                # Flutter-specific practices: only include if flutter is in context
                if "flutter" in practice_frameworks:
                    if "flutter" not in context_frameworks:
                        continue
                # Riverpod-specific practices
                if "riverpod" in practice_frameworks:
                    if "riverpod" not in context_frameworks:
                        continue
                # Bloc-specific practices
                if "bloc" in practice_frameworks:
                    if "bloc" not in context_frameworks:
                        continue
                # Shelf-specific practices
                if "shelf" in practice_frameworks:
                    if "shelf" not in context_frameworks:
                        continue
                # Dart Frog-specific practices
                if "dart_frog" in practice_frameworks:
                    if "dart_frog" not in context_frameworks:
                        continue
                # Serverpod-specific practices
                if "serverpod" in practice_frameworks:
                    if "serverpod" not in context_frameworks:
                        continue
                result.append(practice)
                continue

            # Lua practices: require lua in context (v4.28)
            # Sub-framework checks: LÖVE2D, OpenResty, Lapis, Tarantool
            if "lua" in practice_frameworks:
                if not has_lua:
                    continue
                # LÖVE2D-specific practices
                if "love2d" in practice_frameworks:
                    if "love2d" not in context_frameworks:
                        continue
                # OpenResty-specific practices
                if "openresty" in practice_frameworks:
                    if "openresty" not in context_frameworks:
                        continue
                # Lapis-specific practices
                if "lapis" in practice_frameworks:
                    if "lapis" not in context_frameworks:
                        continue
                # Tarantool-specific practices
                if "tarantool" in practice_frameworks:
                    if "tarantool" not in context_frameworks:
                        continue
                result.append(practice)
                continue

            # PowerShell practices: require powershell in context (v4.29)
            # Sub-framework checks: Pode, DSC, Pester, Azure
            if "powershell" in practice_frameworks:
                if not has_powershell:
                    continue
                # Pode-specific practices
                if "pode" in practice_frameworks:
                    if "pode" not in context_frameworks:
                        continue
                # DSC-specific practices
                if "dsc" in practice_frameworks:
                    if "dsc" not in context_frameworks:
                        continue
                # Pester-specific practices
                if "pester" in practice_frameworks:
                    if "pester" not in context_frameworks:
                        continue
                # Azure-specific practices
                if "azure" in practice_frameworks:
                    if "azure" not in context_frameworks:
                        continue
                result.append(practice)
                continue

            # JavaScript practices: require javascript in context (v4.30)
            # Sub-framework checks: Express, React, Mongoose, Node
            if "javascript" in practice_frameworks:
                if not has_javascript:
                    continue
                # Express-specific practices
                if "express" in practice_frameworks:
                    if "express" not in context_frameworks:
                        continue
                # React-specific practices
                if "react" in practice_frameworks:
                    if "react" not in context_frameworks:
                        continue
                # Mongoose-specific practices
                if "mongoose" in practice_frameworks:
                    if "mongoose" not in context_frameworks:
                        continue
                # Node-specific practices
                if "node" in practice_frameworks:
                    if "node" not in context_frameworks:
                        continue
                result.append(practice)
                continue

            # TypeScript-only practices (not Angular/NestJS/React specific)
            if practice_frameworks == {"typescript"}:
                if has_typescript:
                    result.append(practice)
                continue

            # Fallback: use applicability.matches if set
            if practice.applicability.frameworks:
                if practice.applicability.matches(context_dict):
                    result.append(practice)
                continue

            # Last resort: if generic requested, include
            if criteria.include_generic:
                result.append(practice)

        logger.debug(f"Filtered {len(result)} applicable practices from {len(practices)}")
        return result

    def _filter_by_criteria(
        self,
        practices: List[BestPractice],
        criteria: SelectionCriteria,
    ) -> List[BestPractice]:
        """Filter practices by selection criteria.

        Args:
            practices: Practices to filter.
            criteria: Selection criteria.

        Returns:
            Filtered list of practices.
        """
        result = []
        priority_order = list(PracticePriority)
        min_priority_index = priority_order.index(criteria.min_priority)

        for practice in practices:
            # Filter by category
            if criteria.categories:
                if practice.category not in criteria.categories:
                    continue

            # Filter by level
            if criteria.levels:
                if practice.level not in criteria.levels:
                    continue

            # Filter by priority
            practice_priority_index = priority_order.index(practice.priority)
            if practice_priority_index > min_priority_index:
                continue

            # Filter by frameworks if specified
            if criteria.frameworks:
                practice_frameworks = set(practice.applicability.frameworks)
                if practice_frameworks and not practice_frameworks.intersection(
                    set(f.lower() for f in criteria.frameworks)
                ):
                    continue

            result.append(practice)

        return result

    def _score_practices(
        self,
        practices: List[BestPractice],
        context: ProjectContext,
        criteria: SelectionCriteria,
    ) -> List[BestPractice]:
        """Score and sort practices by relevance.

        Higher scores are better. Considers:
        - Priority level
        - Framework match
        - Pattern match
        - Dependencies match

        Args:
            practices: Practices to score.
            context: Project context.
            criteria: Selection criteria.

        Returns:
            Practices sorted by score (highest first).
        """

        def score(practice: BestPractice) -> tuple:
            """Calculate score for a practice.

            Returns tuple for stable sorting:
            (priority_score, framework_match, pattern_match, id)
            """
            # Priority score (higher priority = higher score)
            priority_order = list(PracticePriority)
            priority_score = len(priority_order) - priority_order.index(practice.priority)

            # Framework match score
            practice_frameworks = set(practice.applicability.frameworks)
            framework_match = len(practice_frameworks.intersection(context.frameworks))

            # Pattern match score
            practice_patterns = set(practice.applicability.patterns)
            pattern_match = len(practice_patterns.intersection(context.patterns))

            # Dependency match score
            practice_deps = set(practice.applicability.has_dependencies)
            dep_match = len(practice_deps.intersection(context.dependencies))

            # Combined score
            total_match = framework_match + pattern_match + dep_match

            return (priority_score, total_match, practice.id)

        return sorted(practices, key=score, reverse=True)

    @staticmethod
    def _estimate_tokens(practice: BestPractice, compact: bool = False) -> int:
        """Estimate the token count for a practice's output.

        Uses tiktoken (cl100k_base encoding) if available for accurate GPT-4
        token counting, otherwise falls back to char/4 heuristic.

        Args:
            practice: The practice to estimate.
            compact: Whether compact format will be used.

        Returns:
            Estimated token count.
        """
        text = practice.to_codetrellis_format(compact=compact)
        return count_tokens(text)

    def _enforce_token_budget(
        self,
        practices: List[BestPractice],
        max_tokens: int,
    ) -> List[BestPractice]:
        """Trim practices list to fit within a token budget.

        Practices are already sorted by relevance score (highest first),
        so we greedily include practices until the budget is exhausted.

        Args:
            practices: Sorted list of practices to trim.
            max_tokens: Maximum total tokens allowed.

        Returns:
            Subset of practices fitting the budget.
        """
        result: List[BestPractice] = []
        used_tokens = 0

        for practice in practices:
            tokens = self._estimate_tokens(practice)
            if used_tokens + tokens > max_tokens:
                break
            result.append(practice)
            used_tokens += tokens

        if len(result) < len(practices):
            logger.debug(
                f"Token budget {max_tokens}: kept {len(result)}/{len(practices)} "
                f"practices (~{used_tokens} tokens used)"
            )

        return result

    def _describe_filters(self, criteria: SelectionCriteria) -> Dict[str, Any]:
        """Create a description of applied filters.

        Args:
            criteria: The selection criteria used.

        Returns:
            Dictionary describing the filters.
        """
        filters: Dict[str, Any] = {}

        if criteria.categories:
            filters["categories"] = [c.value for c in criteria.categories]

        if criteria.levels:
            filters["levels"] = [l.value for l in criteria.levels]

        filters["min_priority"] = criteria.min_priority.value

        if criteria.frameworks:
            filters["frameworks"] = criteria.frameworks

        filters["include_generic"] = criteria.include_generic
        filters["max_practices"] = criteria.max_practices

        if criteria.python_version:
            filters["python_version"] = criteria.python_version

        if criteria.max_tokens is not None:
            filters["max_tokens"] = criteria.max_tokens

        return filters

    def _summarize_context(self, context: ProjectContext) -> str:
        """Create a summary of the project context.

        Args:
            context: The project context.

        Returns:
            Human-readable summary string.
        """
        parts = []

        if context.project_name:
            parts.append(context.project_name)

        parts.append(f"type={context.project_type}")

        if context.frameworks:
            frameworks = ", ".join(sorted(context.frameworks)[:5])
            parts.append(f"frameworks=[{frameworks}]")

        if context.has_async:
            parts.append("async")

        if context.has_tests:
            parts.append("tests")

        return " | ".join(parts)

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    def get_for_framework(
        self,
        framework: str,
        level: Optional[PracticeLevel] = None,
    ) -> List[BestPractice]:
        """Get practices for a specific framework.

        Args:
            framework: Framework name (e.g., "fastapi", "django").
            level: Optional level filter.

        Returns:
            List of practices for that framework.
        """
        practices = self.repository.get_by_framework(framework.lower())

        if level is not None:
            practices = [p for p in practices if p.level == level]

        return practices

    def get_for_category(
        self,
        category: PracticeCategory,
        min_priority: PracticePriority = PracticePriority.OPTIONAL,
    ) -> List[BestPractice]:
        """Get practices for a specific category.

        Args:
            category: The category to get.
            min_priority: Minimum priority to include.

        Returns:
            List of practices in that category.
        """
        practices = self.repository.get_by_category(category)
        priority_order = list(PracticePriority)
        min_index = priority_order.index(min_priority)

        return [
            p
            for p in practices
            if priority_order.index(p.priority) <= min_index
        ]

    def get_critical(self) -> List[BestPractice]:
        """Get all critical priority practices.

        Returns:
            List of critical practices.
        """
        return self.repository.get_by_priority(PracticePriority.CRITICAL)

    def search(self, query: str) -> List[BestPractice]:
        """Search practices by text query.

        Args:
            query: Search query.

        Returns:
            Matching practices.
        """
        return self.repository.search(query)


# Module-level selector for convenience
_default_selector: Optional[PracticeSelector] = None


def get_selector() -> PracticeSelector:
    """Get the default selector instance.

    Returns:
        The default PracticeSelector.
    """
    global _default_selector

    if _default_selector is None:
        _default_selector = PracticeSelector()

    return _default_selector


def select_practices(
    context: Optional[ProjectContext] = None,
    matrix: Optional[Any] = None,
    categories: Optional[List[PracticeCategory]] = None,
    levels: Optional[List[PracticeLevel]] = None,
    min_priority: PracticePriority = PracticePriority.LOW,
    frameworks: Optional[List[str]] = None,
    max_practices: int = 50,
) -> BPLOutput:
    """Convenience function for selecting practices.

    Args:
        context: Project context (or provide matrix).
        matrix: ProjectMatrix (alternative to context).
        categories: Categories to include.
        levels: Levels to include.
        min_priority: Minimum priority.
        frameworks: Frameworks to filter for.
        max_practices: Maximum practices to return.

    Returns:
        BPLOutput with selected practices.

    Raises:
        ValueError: If neither context nor matrix is provided.
    """
    if context is None and matrix is None:
        raise ValueError("Must provide either context or matrix")

    if context is None:
        context = ProjectContext.from_matrix(matrix)

    criteria = SelectionCriteria(
        categories=categories or [],
        levels=levels or [],
        min_priority=min_priority,
        frameworks=frameworks or [],
        max_practices=max_practices,
    )

    selector = get_selector()
    return selector.select(context, criteria)
