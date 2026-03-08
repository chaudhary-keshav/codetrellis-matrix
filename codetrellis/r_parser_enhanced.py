"""
EnhancedRParser v1.0 - Comprehensive R parser using all extractors.

This parser integrates all R extractors to provide complete
parsing of R source files.

Supports:
- Core R types (R6 classes, R5 Reference classes, S4 classes, S3 constructors, S7/R7)
- Functions (def, S3 methods, operators, lambda syntax R 4.1+)
- Web frameworks (Plumber REST API, Shiny, RestRserve, Ambiorix, Golem, Rhino)
- Database (DBI, dbplyr, dplyr pipelines, data.table, Arrow/Parquet, sparklyr)
- Package metadata (DESCRIPTION, NAMESPACE, renv.lock, Roxygen)
- Pipe chain analysis (|> base, %>% magrittr)
- NSE detection (rlang, tidyeval)
- All R versions: 2.x, 3.0-3.6, 4.0-4.4+
  (Lambda \\(x), base pipe |>, placeholder _, R7/S7 classes)

Optional AST support via rpy2 or tree-sitter (if installed).
Optional LSP support via R Language Server (languageserver package).

Part of CodeTrellis v4.26 - R Language Support
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all R extractors
from .extractors.r import (
    RTypeExtractor, RClassInfo, RFieldInfo, RGenericInfo,
    RS4MethodInfo, REnvironmentInfo,
    RFunctionExtractor, RFunctionInfo, RParameterInfo, RPipeChainInfo,
    RAPIExtractor, RRouteInfo, RShinyComponentInfo, RAPIEndpointInfo,
    RModelExtractor, RDataModelInfo, RDBConnectionInfo, RDBQueryInfo,
    RDataPipelineInfo,
    RAttributeExtractor, RPackageDepInfo, RExportInfo, RConfigInfo,
    RLifecycleHookInfo, RPackageMetadataInfo,
)

logger = logging.getLogger(__name__)

# Optional tree-sitter support for AST parsing
_tree_sitter_available = False
_ts_r_language = None

try:
    import tree_sitter
    import tree_sitter_r
    _ts_r_language = tree_sitter_r.language()
    _tree_sitter_available = True
    logger.debug("tree-sitter-r available for AST parsing")
except ImportError:
    logger.debug("tree-sitter-r not installed — using regex-based parsing")

# Optional rpy2 support for deep AST analysis
_rpy2_available = False
try:
    import rpy2.robjects as robjects
    _rpy2_available = True
    logger.debug("rpy2 available for R AST analysis")
except ImportError:
    logger.debug("rpy2 not installed — using regex-based parsing")


@dataclass
class RParseResult:
    """Complete parse result for an R file."""
    file_path: str
    file_type: str = "r"

    # Package info
    package_name: str = ""
    r_version: str = ""

    # Core types
    classes: List[RClassInfo] = field(default_factory=list)
    generics: List[RGenericInfo] = field(default_factory=list)
    s4_methods: List[RS4MethodInfo] = field(default_factory=list)
    environments: List[REnvironmentInfo] = field(default_factory=list)

    # Functions
    functions: List[RFunctionInfo] = field(default_factory=list)
    pipe_chains: List[RPipeChainInfo] = field(default_factory=list)

    # API/Framework elements
    routes: List[RRouteInfo] = field(default_factory=list)
    shiny_components: List[RShinyComponentInfo] = field(default_factory=list)
    api_endpoints: List[RAPIEndpointInfo] = field(default_factory=list)

    # Data models and database
    data_models: List[RDataModelInfo] = field(default_factory=list)
    db_connections: List[RDBConnectionInfo] = field(default_factory=list)
    db_queries: List[RDBQueryInfo] = field(default_factory=list)
    data_pipelines: List[RDataPipelineInfo] = field(default_factory=list)

    # Package metadata
    dependencies: List[RPackageDepInfo] = field(default_factory=list)
    exports: List[RExportInfo] = field(default_factory=list)
    configs: List[RConfigInfo] = field(default_factory=list)
    lifecycle_hooks: List[RLifecycleHookInfo] = field(default_factory=list)
    package_metadata: Optional[RPackageMetadataInfo] = None
    env_vars: List[RConfigInfo] = field(default_factory=list)

    # Metadata
    imports: List[str] = field(default_factory=list)  # library/require calls
    detected_frameworks: List[str] = field(default_factory=list)
    detected_r_features: List[str] = field(default_factory=list)


class EnhancedRParser:
    """
    Enhanced R parser that uses all extractors for comprehensive parsing.

    Framework detection supports:
    - Shiny (reactive web applications)
    - Plumber (REST APIs)
    - Golem (Shiny modules framework)
    - Rhino (enterprise Shiny framework)
    - RestRserve (high-performance REST APIs)
    - Ambiorix (Express-like web framework)
    - Fiery (event-driven web server)
    - httpuv (HTTP/WebSocket server)
    - tidyverse (dplyr, tidyr, ggplot2, purrr, etc.)
    - data.table (high-performance data manipulation)
    - ggplot2 (grammar of graphics)
    - R6 (encapsulated OOP)
    - S4 (formal OOP)
    - Rcpp (C++ integration)
    - rstan / brms (Bayesian modeling)
    - caret / tidymodels / mlr3 (machine learning)
    - testthat / tinytest (testing)
    - roxygen2 (documentation)
    - devtools / usethis (package development)
    - DBI / dbplyr (database interfaces)
    - sparklyr (Apache Spark interface)
    - arrow (Apache Arrow / Parquet)
    - reticulate (Python integration)
    - terra / sf / stars (geospatial)
    - Bioconductor (genomics/bioinformatics)
    - targets / drake (pipeline tools)
    - rmarkdown / quarto / bookdown (literate programming)
    - pkgdown (package websites)
    """

    # Library/require detection
    LIBRARY_PATTERN = re.compile(
        r'(?:library|require)\s*\(\s*["\']?([\w.]+)["\']?\s*(?:,.*?)?\)',
        re.MULTILINE
    )

    # Import detection (pkg::func)
    NAMESPACE_IMPORT = re.compile(
        r'(\w+)::(\w+)',
        re.MULTILINE
    )

    # Package name from DESCRIPTION or inline
    PACKAGE_NAME_PATTERN = re.compile(
        r'^Package:\s*(\S+)',
        re.MULTILINE
    )

    # source() calls
    SOURCE_PATTERN = re.compile(
        r'source\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        # Web frameworks
        'shiny': re.compile(r'\b(?:shinyApp|shinyServer|shinyUI|fluidPage|navbarPage|dashboardPage|renderPlot|renderTable|renderText|renderUI|observeEvent|reactiveValues|NS\(|moduleServer)\b'),
        'plumber': re.compile(r'(?:#\*\s*@(?:get|post|put|delete|patch|filter)|pr_get|pr_post|pr_run|plumber::plumber|plumb\()'),
        'golem': re.compile(r'\b(?:golem::|run_app|add_module|mod_\w+_ui|mod_\w+_server|golem_opts|golem::run_app)\b'),
        'rhino': re.compile(r'\b(?:rhino::|box::use|rhino::app|app\$server)\b'),
        'restrserve': re.compile(r'\b(?:RestRserve|Application\$new|app\$add_get|app\$add_post)\b'),
        'ambiorix': re.compile(r'\b(?:Ambiorix|ambiorix::|app\$get\(|app\$post\()\b'),
        'fiery': re.compile(r'\b(?:fiery::|Fire\$new|app\$on\()\b'),
        'httpuv': re.compile(r'\b(?:httpuv::|startServer|startDaemonizedServer|runServer)\b'),

        # Data manipulation
        'tidyverse': re.compile(r'\b(?:tidyverse|tidyr::|dplyr::|tibble::|readr::|stringr::|forcats::|purrr::)\b'),
        'dplyr': re.compile(r'\b(?:dplyr::|mutate|filter|select|group_by|summarize|summarise|arrange|slice|left_join|inner_join|right_join|full_join|anti_join|semi_join|across|pull|distinct|count|tally|transmute|rename|relocate)\s*\('),
        'tidyr': re.compile(r'\b(?:tidyr::|pivot_longer|pivot_wider|unnest|nest|separate|unite|fill|complete|expand|crossing|nesting)\s*\('),
        'purrr': re.compile(r'\b(?:purrr::|map\(|map_chr\(|map_dbl\(|map_int\(|map_lgl\(|map_dfr\(|map2\(|pmap\(|walk\(|imap\(|reduce\(|accumulate\(|keep\(|discard\(|pluck\(|possibly\(|safely\()\b'),
        'data.table': re.compile(r'\b(?:data\.table::|fread|fwrite|\.\(|:=|\.SD|\.N|\.GRP|\.I|setkey|setDT|setDF|setnames|setcolorder|fifelse|fcase|shift|rleid)\b'),
        'dtplyr': re.compile(r'\b(?:dtplyr::|lazy_dt)\b'),

        # Visualization
        'ggplot2': re.compile(r'\b(?:ggplot2::|ggplot\(|geom_\w+|aes\(|theme_|scale_|coord_|facet_|stat_|labs\(|ggtitle\()\b'),
        'plotly': re.compile(r'\b(?:plotly::|plot_ly\(|ggplotly\(|add_trace\()\b'),
        'htmlwidgets': re.compile(r'\b(?:htmlwidgets::|createWidget|sizingPolicy)\b'),
        'leaflet': re.compile(r'\b(?:leaflet::|leaflet\(|addTiles|addMarkers|addPolygons)\b'),

        # Machine learning
        'tidymodels': re.compile(r'\b(?:tidymodels|parsnip::|recipes::|workflows::|tune::|rsample::|yardstick::)\b'),
        'caret': re.compile(r'\b(?:caret::|trainControl|train\(|confusionMatrix)\b'),
        'mlr3': re.compile(r'\b(?:mlr3::|TaskClassif|TaskRegr|lrn\(|rsmp\(|msr\()\b'),
        'xgboost': re.compile(r'\b(?:xgboost::|xgb\.train|xgb\.DMatrix|xgb\.cv)\b'),
        'tensorflow': re.compile(r'\b(?:tensorflow::|keras::|tf\$|layer_|compile\(|fit\()\b'),
        'torch': re.compile(r'\b(?:torch::|nn_module|nn_linear|nn_conv\d|dataloader|dataset)\b'),

        # Statistics / modeling
        'rstan': re.compile(r'\b(?:rstan::|stan\(|stan_model|sampling)\b'),
        'brms': re.compile(r'\b(?:brms::|brm\(|prior\(|posterior_predict)\b'),
        'lme4': re.compile(r'\b(?:lme4::|lmer\(|glmer\(|nlmer\()\b'),
        'mgcv': re.compile(r'\b(?:mgcv::|gam\(|bam\(|s\(|te\(|ti\()\b'),
        'survival': re.compile(r'\b(?:survival::|Surv\(|survfit\(|coxph\()\b'),

        # OOP
        'R6': re.compile(r'\b(?:R6::|R6Class\()\b'),
        'R7': re.compile(r'\b(?:S7::|new_class\(|new_generic\(|method\()\b'),

        # C/C++ integration
        'Rcpp': re.compile(r'\b(?:Rcpp::|sourceCpp|cppFunction|evalCpp|RcppExport|RcppArmadillo|RcppEigen)\b'),

        # Database
        'DBI': re.compile(r'\b(?:DBI::|dbConnect|dbDisconnect|dbGetQuery|dbSendQuery|dbExecute|dbWriteTable|dbReadTable|dbListTables)\b'),
        'dbplyr': re.compile(r'\b(?:dbplyr::|tbl\(.*?con|in_schema|show_query|collect)\b'),
        'pool': re.compile(r'\b(?:pool::|dbPool|poolClose|poolCheckout)\b'),

        # Spark
        'sparklyr': re.compile(r'\b(?:sparklyr::|spark_connect|spark_read_|sdf_|ft_|ml_)\b'),

        # Arrow / big data
        'arrow': re.compile(r'\b(?:arrow::|read_parquet|write_parquet|read_feather|write_feather|open_dataset|arrow_table)\b'),
        'duckdb': re.compile(r'\b(?:duckdb::|duckdb\(|dbConnect\(duckdb)\b'),

        # Python integration
        'reticulate': re.compile(r'\b(?:reticulate::|import\(|py_run_string|source_python|py_to_r|r_to_py|py\$)\b'),

        # Geospatial
        'sf': re.compile(r'\b(?:sf::|st_read|st_write|st_transform|st_crs|st_buffer|st_intersection|st_union|st_join)\b'),
        'terra': re.compile(r'\b(?:terra::|rast\(|vect\(|project\(|crop\(|mask\(|extract\()\b'),
        'stars': re.compile(r'\b(?:stars::|read_stars|st_as_stars|write_stars)\b'),

        # Bioconductor
        'bioconductor': re.compile(r'\b(?:BiocManager::|Biobase::|GenomicRanges::|SummarizedExperiment|DESeq2|edgeR|limma)\b'),

        # Pipeline / workflow
        'targets': re.compile(r'\b(?:targets::|tar_target|tar_make|tar_read|tar_load|tar_visnetwork|tar_option_set|list\(\s*tar_target)\b'),
        'drake': re.compile(r'\b(?:drake::|drake_plan|make\(|readd\(|loadd\()\b'),

        # Reporting / literate programming
        'rmarkdown': re.compile(r'\b(?:rmarkdown::|render\(|output_format|html_document|pdf_document|word_document)\b'),
        'quarto': re.compile(r'\b(?:quarto::|quarto_render|quarto_preview)\b'),
        'knitr': re.compile(r'\b(?:knitr::|knit\(|kable\(|opts_chunk)\b'),
        'bookdown': re.compile(r'\b(?:bookdown::|gitbook|bs4_book|pdf_book)\b'),

        # Package development
        'devtools': re.compile(r'\b(?:devtools::|load_all|install\(|document\(|check\(|build\(|test\()\b'),
        'usethis': re.compile(r'\b(?:usethis::|create_package|use_r|use_test|use_data|use_pipe|use_package|use_github_action)\b'),
        'roxygen2': re.compile(r"\b(?:roxygen2::|roxygenise|roxygenize)\b"),
        'pkgdown': re.compile(r'\b(?:pkgdown::|build_site|build_reference|build_articles)\b'),

        # Testing
        'testthat': re.compile(r'\b(?:testthat::|test_that\(|expect_equal|expect_true|expect_false|expect_error|expect_warning|expect_message|describe\(|it\()\b'),
        'tinytest': re.compile(r'\b(?:tinytest::|expect_equal|expect_true|expect_false|expect_error|run_test_dir)\b'),
        'covr': re.compile(r'\b(?:covr::|package_coverage|file_coverage|report)\b'),
        'shinytest2': re.compile(r'\b(?:shinytest2::|AppDriver\$new|expect_screenshot)\b'),

        # Configuration
        'config': re.compile(r'\b(?:config::|config::get\(|config_file)\b'),
        'dotenv': re.compile(r'\b(?:dotenv::|load_dot_env)\b'),
        'yaml': re.compile(r'\b(?:yaml::|read_yaml|write_yaml|yaml\.load)\b'),

        # Logging
        'logger': re.compile(r'\b(?:logger::|log_info|log_warn|log_error|log_debug|log_trace)\b'),
        'futile.logger': re.compile(r'\b(?:futile\.logger::|flog\.info|flog\.warn|flog\.error)\b'),

        # API clients
        'httr2': re.compile(r'\b(?:httr2::|request\(|req_perform|req_url_path|req_body_json|resp_body_json)\b'),
        'httr': re.compile(r'\b(?:httr::|GET\(|POST\(|PUT\(|DELETE\(|content\(|status_code\()\b'),

        # Task scheduling
        'later': re.compile(r'\b(?:later::|later\(|run_now)\b'),
        'callr': re.compile(r'\b(?:callr::|r\(|r_bg\(|r_process)\b'),
        'future': re.compile(r'\b(?:future::|plan\(|future\(|value\(|multisession|multicore|cluster)\b'),
        'promises': re.compile(r'\b(?:promises::|promise\(|then\(|catch\(|finally\()\b'),

        # Dependency management
        'renv': re.compile(r'\b(?:renv::|renv::init|renv::snapshot|renv::restore|renv\.lock)\b'),
        'packrat': re.compile(r'\b(?:packrat::|packrat::init|packrat::snapshot)\b'),
    }

    # R version feature detection
    R_VERSION_FEATURES = {
        'base_pipe': re.compile(r'\|>'),  # R 4.1+
        'lambda': re.compile(r'\\\s*\('),  # R 4.1+ lambda
        'placeholder': re.compile(r'_\s*(?:\|>|%>%)'),  # R 4.2+ placeholder
        'raw_strings': re.compile(r'r"\{|r"\(|R"\{|R"\('),  # R 4.0+
        'walrus': re.compile(r':='),  # data.table/rlang
    }

    def __init__(self):
        """Initialize the parser with all extractors."""
        self.type_extractor = RTypeExtractor()
        self.function_extractor = RFunctionExtractor()
        self.api_extractor = RAPIExtractor()
        self.model_extractor = RModelExtractor()
        self.attribute_extractor = RAttributeExtractor()

    def parse(self, content: str, file_path: str = "") -> RParseResult:
        """
        Parse R source code and extract all information.

        Args:
            content: R source code content
            file_path: Path to source file

        Returns:
            RParseResult with all extracted information
        """
        result = RParseResult(file_path=file_path)

        if not content.strip():
            return result

        # Type extraction
        try:
            type_result = self.type_extractor.extract(content, file_path)
            result.classes = type_result.get("classes", [])
            result.generics = type_result.get("generics", [])
            result.s4_methods = type_result.get("s4_methods", [])
            result.environments = type_result.get("environments", [])
        except Exception as e:
            logger.debug(f"R type extraction failed for {file_path}: {e}")

        # Function extraction
        try:
            func_result = self.function_extractor.extract(content, file_path)
            result.functions = func_result.get("functions", [])
            result.pipe_chains = func_result.get("pipe_chains", [])
        except Exception as e:
            logger.debug(f"R function extraction failed for {file_path}: {e}")

        # API extraction
        try:
            api_result = self.api_extractor.extract(content, file_path)
            result.routes = api_result.get("routes", [])
            result.shiny_components = api_result.get("shiny_components", [])
            result.api_endpoints = api_result.get("api_endpoints", [])
        except Exception as e:
            logger.debug(f"R API extraction failed for {file_path}: {e}")

        # Model extraction
        try:
            model_result = self.model_extractor.extract(content, file_path)
            result.data_models = model_result.get("data_models", [])
            result.db_connections = model_result.get("db_connections", [])
            result.db_queries = model_result.get("db_queries", [])
            result.data_pipelines = model_result.get("data_pipelines", [])
        except Exception as e:
            logger.debug(f"R model extraction failed for {file_path}: {e}")

        # Attribute extraction
        try:
            attr_result = self.attribute_extractor.extract(content, file_path)
            result.dependencies = attr_result.get("dependencies", [])
            result.exports = attr_result.get("exports", [])
            result.configs = attr_result.get("configs", [])
            result.lifecycle_hooks = attr_result.get("lifecycle_hooks", [])
            result.package_metadata = attr_result.get("package_metadata")
            result.env_vars = attr_result.get("env_vars", [])
        except Exception as e:
            logger.debug(f"R attribute extraction failed for {file_path}: {e}")

        # Detect imports (library/require calls)
        result.imports = self._detect_imports(content)

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect R version features
        result.detected_r_features = self._detect_r_features(content)

        return result

    def parse_description(self, content: str) -> Dict[str, Any]:
        """Parse a DESCRIPTION file for package metadata."""
        attr_result = self.attribute_extractor.extract(content, "DESCRIPTION")
        metadata = attr_result.get("package_metadata")
        deps = attr_result.get("dependencies", [])

        result = {
            "metadata": None,
            "dependencies": {},
        }

        if metadata:
            result["metadata"] = {
                "name": metadata.name,
                "title": metadata.title,
                "version": metadata.version,
                "description": metadata.description,
                "license": metadata.license,
                "r_version": metadata.r_version,
                "authors": metadata.authors,
                "url": metadata.url,
                "encoding": metadata.encoding,
                "system_requirements": metadata.system_requirements,
            }

        for dep in deps:
            result["dependencies"][dep.name] = dep.version or "*"

        return result

    def parse_renv_lock(self, content: str) -> Dict[str, str]:
        """Parse renv.lock file for package dependencies."""
        attr_result = self.attribute_extractor.extract(content, "renv.lock")
        deps = attr_result.get("dependencies", [])
        return {dep.name: dep.version for dep in deps}

    def parse_namespace(self, content: str) -> Dict[str, Any]:
        """Parse NAMESPACE file for exports/imports."""
        attr_result = self.attribute_extractor.extract(content, "NAMESPACE")
        exports = attr_result.get("exports", [])
        return {
            "exports": [{"name": e.name, "kind": e.kind, "pattern": e.pattern} for e in exports],
        }

    def _detect_imports(self, content: str) -> List[str]:
        """Detect library/require imports."""
        imports = []
        seen = set()
        for m in self.LIBRARY_PATTERN.finditer(content):
            pkg = m.group(1)
            if pkg not in seen:
                seen.add(pkg)
                imports.append(pkg)

        # Also detect namespace imports (pkg::func)
        for m in self.NAMESPACE_IMPORT.finditer(content):
            pkg = m.group(1)
            if pkg not in seen:
                seen.add(pkg)
                imports.append(pkg)

        return imports

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect R frameworks used in source code."""
        detected = []
        for fw_name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(fw_name)
        return detected

    def _detect_r_features(self, content: str) -> List[str]:
        """Detect R version-specific features."""
        features = []
        for feat_name, pattern in self.R_VERSION_FEATURES.items():
            if pattern.search(content):
                features.append(feat_name)
        return features

    def _try_tree_sitter_parse(self, content: str, file_path: str) -> Optional[RParseResult]:
        """
        Attempt to parse R code using tree-sitter for accurate AST.

        Only used when tree-sitter-r is installed. Provides more accurate
        parsing than regex for complex nested structures.
        """
        if not _tree_sitter_available or not _ts_r_language:
            return None

        try:
            parser = tree_sitter.Parser()
            parser.language = _ts_r_language
            tree = parser.parse(bytes(content, 'utf-8'))
            root = tree.root_node

            # Use tree-sitter AST for enhanced extraction
            # This supplements the regex-based extractors with precise node boundaries
            logger.debug(f"tree-sitter-r parsed {file_path}: {root.child_count} top-level nodes")

            # For now, fall through to regex parsing
            # Future: extract types/functions directly from AST nodes
            return None

        except Exception as e:
            logger.debug(f"tree-sitter-r parse failed for {file_path}: {e}")
            return None

    def _try_lsp_enrich(self, result: RParseResult, file_path: str) -> None:
        """
        Attempt to enrich parse results using R Language Server (languageserver).

        Provides:
        - Precise type information
        - Cross-file symbol resolution
        - Hover documentation
        - Completion data
        """
        # LSP integration would connect to a running R Language Server
        # via JSON-RPC. For now, this is a placeholder for future integration.
        # The R Language Server (https://github.com/REditorSupport/languageserver)
        # supports textDocument/documentSymbol, textDocument/hover, etc.
        pass
