"""Best Practices Library (BPL) Core Models.

This module defines the core data models for the BPL system including:
- Practice categories and priorities
- Version constraints and applicability rules
- Best practice content and metadata
- SOLID principles and design patterns

All models follow Python best practices with:
- Type hints throughout
- Dataclasses for immutable data structures
- Enums for fixed categories
- Comprehensive docstrings

Example:
    >>> from codetrellis.bpl.models import BestPractice, PracticeCategory
    >>> practice = BestPractice(
    ...     id="PY001",
    ...     title="Use Type Hints",
    ...     category=PracticeCategory.TYPE_SAFETY
    ... )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set


class PracticeCategory(Enum):
    """Categories for organizing best practices.

    Each category represents a distinct area of software development
    best practices that can be filtered and selected.
    """

    # Code Quality Categories
    TYPE_SAFETY = "type_safety"
    ERROR_HANDLING = "error_handling"
    CODE_STYLE = "code_style"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    DEBUGGING = "debugging"
    BEST_PRACTICES = "best_practices"

    # Architecture Categories
    DESIGN_PATTERNS = "design_patterns"
    SOLID_PRINCIPLES = "solid_principles"
    API_DESIGN = "api_design"
    DATA_MODELING = "data_modeling"
    ARCHITECTURE = "architecture"
    STATE_MANAGEMENT = "state_management"
    PATTERNS = "patterns"  # Generic patterns category

    # Framework-Specific Categories
    FASTAPI = "fastapi"
    DJANGO = "django"
    FLASK = "flask"
    PYTORCH = "pytorch"
    PANDAS = "pandas"
    SQLALCHEMY = "sqlalchemy"
    PYDANTIC = "pydantic"
    CELERY = "celery"

    # Angular-Specific Categories
    COMPONENT_DESIGN = "component_design"
    SIGNAL_PATTERNS = "signal_patterns"
    SERVICE_PATTERNS = "service_patterns"
    LIFECYCLE = "lifecycle"
    ROUTING = "routing"
    FORMS = "forms"
    NETWORKING = "networking"

    # Domain Categories
    ASYNC_PATTERNS = "async_patterns"
    CONCURRENCY = "concurrency"
    DATABASE = "database"
    CACHING = "caching"
    LOGGING = "logging"
    CONFIGURATION = "configuration"

    # Design Pattern Categories (GoF)
    CREATIONAL = "creational"
    STRUCTURAL = "structural"
    BEHAVIORAL = "behavioral"
    ENTERPRISE = "enterprise"

    # NestJS-Specific Categories
    VALIDATION = "validation"
    MONITORING = "monitoring"
    RELIABILITY = "reliability"

    # Java-Specific Categories (v4.12)
    SPRING = "spring"
    JPA = "jpa"
    QUARKUS = "quarkus"
    MICRONAUT = "micronaut"
    MESSAGING = "messaging"
    PROJECT_STRUCTURE = "project_structure"

    # Go Framework-Specific Categories (v5.2)
    GIN = "gin"
    ECHO = "echo"
    FIBER = "fiber"
    CHI = "chi"
    GRPC_GO = "grpc_go"
    GORM = "gorm"
    SQLX_GO = "sqlx_go"
    COBRA = "cobra"

    # React-Specific Categories
    ACCESSIBILITY = "accessibility"
    USER_EXPERIENCE = "user_experience"

    # DevOps Categories
    AUTOMATION = "automation"
    CONTAINERS = "containers"
    DEPLOYMENT = "deployment"
    INFRASTRUCTURE = "infrastructure"

    # Rust-Specific Categories (v4.14)
    OWNERSHIP = "ownership"
    LIFETIMES = "lifetimes"
    MEMORY_SAFETY = "memory_safety"
    TRAIT_DESIGN = "trait_design"
    CARGO = "cargo"

    # SQL-Specific Categories (v4.15)
    QUERY_OPTIMIZATION = "query_optimization"
    SCHEMA_DESIGN = "schema_design"
    STORED_PROCEDURES = "stored_procedures"
    DATA_INTEGRITY = "data_integrity"
    INDEXING = "indexing"
    MIGRATION_PATTERNS = "migration_patterns"
    SQL_SECURITY = "sql_security"
    SQL_ANTI_PATTERNS = "sql_anti_patterns"

    # HTML-Specific Categories (v4.16)
    SEMANTIC_HTML = "semantic_html"
    HTML_FORMS = "html_forms"
    SEO = "seo"
    WEB_COMPONENTS = "web_components"
    TEMPLATE_ENGINES = "template_engines"
    HTML_PERFORMANCE = "html_performance"
    RESPONSIVE_DESIGN = "responsive_design"
    HTML_SECURITY = "html_security"

    # CSS-Specific Categories (v4.17)
    CSS_LAYOUT = "css_layout"
    CSS_VARIABLES = "css_variables"
    CSS_ANIMATIONS = "css_animations"
    CSS_PREPROCESSOR = "css_preprocessor"
    CSS_ARCHITECTURE = "css_architecture"
    CSS_NAMING = "css_naming"
    CSS_PERFORMANCE = "css_performance"
    CSS_RESPONSIVE = "css_responsive"

    # Sass/SCSS-Specific Categories (v4.44)
    SASS_VARIABLES = "sass_variables"
    SASS_MIXINS = "sass_mixins"
    SASS_FUNCTIONS = "sass_functions"
    SASS_MODULES = "sass_modules"
    SASS_NESTING = "sass_nesting"
    SASS_ARCHITECTURE = "sass_architecture"
    SASS_PERFORMANCE = "sass_performance"
    SASS_NAMING = "sass_naming"
    SASS_BEST_PRACTICES = "sass_best_practices"
    SASS_TOOLING = "sass_tooling"

    # Less CSS-Specific Categories (v4.45)
    LESS_VARIABLES = "less_variables"
    LESS_MIXINS = "less_mixins"
    LESS_FUNCTIONS = "less_functions"
    LESS_IMPORTS = "less_imports"
    LESS_EXTEND = "less_extend"
    LESS_ARCHITECTURE = "less_architecture"
    LESS_PERFORMANCE = "less_performance"
    LESS_NAMING = "less_naming"
    LESS_BEST_PRACTICES = "less_best_practices"
    LESS_TOOLING = "less_tooling"

    # PostCSS-Specific Categories (v4.46)
    POSTCSS_PLUGINS = "postcss_plugins"
    POSTCSS_CONFIG = "postcss_config"
    POSTCSS_TRANSFORMS = "postcss_transforms"
    POSTCSS_SYNTAX = "postcss_syntax"
    POSTCSS_API = "postcss_api"
    POSTCSS_ARCHITECTURE = "postcss_architecture"
    POSTCSS_PERFORMANCE = "postcss_performance"
    POSTCSS_BEST_PRACTICES = "postcss_best_practices"
    POSTCSS_TOOLING = "postcss_tooling"
    POSTCSS_MIGRATION = "postcss_migration"

    # Bash/Shell-Specific Categories (v4.18)
    SHELL_SCRIPTING = "shell_scripting"
    BASH_PATTERNS = "bash_patterns"
    POSIX_COMPLIANCE = "posix_compliance"
    BASH_SECURITY = "bash_security"
    BASH_ERROR_HANDLING = "bash_error_handling"
    BASH_PERFORMANCE = "bash_performance"
    BASH_PORTABILITY = "bash_portability"
    BASH_AUTOMATION = "bash_automation"

    # C-Specific Categories (v4.19)
    C_MEMORY_MANAGEMENT = "c_memory_management"
    C_POINTER_SAFETY = "c_pointer_safety"
    C_STANDARD_COMPLIANCE = "c_standard_compliance"
    C_PREPROCESSOR = "c_preprocessor"
    C_EMBEDDED = "c_embedded"
    C_CONCURRENCY = "c_concurrency"
    C_API_DESIGN = "c_api_design"
    C_ERROR_HANDLING = "c_error_handling"
    C_PERFORMANCE = "c_performance"
    C_SECURITY = "c_security"

    # C++-Specific Categories (v4.20)
    CPP_MEMORY_MANAGEMENT = "cpp_memory_management"
    CPP_SMART_POINTERS = "cpp_smart_pointers"
    CPP_RAII = "cpp_raii"
    CPP_TEMPLATES = "cpp_templates"
    CPP_MODERN_FEATURES = "cpp_modern_features"
    CPP_CONCURRENCY = "cpp_concurrency"
    CPP_STL_USAGE = "cpp_stl_usage"
    CPP_OOP_DESIGN = "cpp_oop_design"
    CPP_ERROR_HANDLING = "cpp_error_handling"
    CPP_PERFORMANCE = "cpp_performance"
    CPP_SECURITY = "cpp_security"
    CPP_API_DESIGN = "cpp_api_design"

    # Swift-Specific Categories (v4.22)
    SWIFT_CONCURRENCY = "swift_concurrency"
    SWIFT_PROTOCOL_DESIGN = "swift_protocol_design"
    SWIFT_VALUE_SEMANTICS = "swift_value_semantics"
    SWIFT_MEMORY_MANAGEMENT = "swift_memory_management"
    SWIFT_ERROR_HANDLING = "swift_error_handling"
    SWIFT_SWIFTUI = "swift_swiftui"
    SWIFT_COMBINE = "swift_combine"
    SWIFT_VAPOR = "swift_vapor"
    SWIFT_TESTING = "swift_testing"
    SWIFT_PERFORMANCE = "swift_performance"
    SWIFT_SAFETY = "swift_safety"
    SWIFT_API_DESIGN = "swift_api_design"

    # Ruby-Specific Categories (v4.23)
    STYLE = "style"
    TYPE_DESIGN = "type_design"
    METAPROGRAMMING = "metaprogramming"
    DEPENDENCIES = "dependencies"
    SAFETY = "safety"
    MODERN_RUBY = "modern_ruby"

    # PHP-Specific Categories (v4.24)
    DATA_ACCESS = "data_access"
    QUALITY = "quality"

    # Scala-Specific Categories (v4.25)
    SERIALIZATION = "serialization"
    BUILD = "build"
    INTEROP = "interop"
    TOOLING = "tooling"
    OBSERVABILITY = "observability"

    # Dart/Flutter-Specific Categories (v4.27)
    DART_NULL_SAFETY = "dart_null_safety"
    DART_IMMUTABILITY = "dart_immutability"
    DART_TYPE_SYSTEM = "dart_type_system"
    DART_PATTERNS = "dart_patterns"
    DART_ERROR_HANDLING = "dart_error_handling"
    DART_ASYNC = "dart_async"
    DART_CONCURRENCY = "dart_concurrency"
    DART_STATE_MANAGEMENT = "dart_state_management"
    DART_DATA = "dart_data"
    DART_DATABASE = "dart_database"
    DART_NETWORKING = "dart_networking"
    DART_SERVER = "dart_server"
    DART_TESTING = "dart_testing"
    DART_ARCHITECTURE = "dart_architecture"
    DART_CODEGEN = "dart_codegen"
    DART_PLATFORM = "dart_platform"
    DART_PERFORMANCE = "dart_performance"
    DART_SECURITY = "dart_security"
    DART_DOCUMENTATION = "dart_documentation"
    DART_STYLE = "dart_style"
    DART_QUALITY = "dart_quality"
    DART_DEPENDENCIES = "dart_dependencies"
    FLUTTER_WIDGETS = "flutter_widgets"
    FLUTTER_PERFORMANCE = "flutter_performance"
    FLUTTER_PLATFORM = "flutter_platform"

    # v4.28: Lua Categories
    LUA_TABLES = "lua_tables"
    LUA_METATABLES = "lua_metatables"
    LUA_MODULES = "lua_modules"
    LUA_FUNCTIONS = "lua_functions"
    LUA_COROUTINES = "lua_coroutines"
    LUA_ERROR_HANDLING = "lua_error_handling"
    LUA_OOP = "lua_oop"
    LUA_FFI = "lua_ffi"
    LUA_PERFORMANCE = "lua_performance"
    LUA_LOVE2D = "lua_love2d"
    LUA_OPENRESTY = "lua_openresty"
    LUA_LAPIS = "lua_lapis"
    LUA_TESTING = "lua_testing"
    LUA_SECURITY = "lua_security"
    LUA_STYLE = "lua_style"

    # v4.29: PowerShell Categories
    PS_CMDLET_DESIGN = "ps_cmdlet_design"
    PS_PIPELINE = "ps_pipeline"
    PS_DSC = "ps_dsc"
    PS_ERROR_HANDLING = "ps_error_handling"
    PS_MODULES = "ps_modules"
    PS_SECURITY = "ps_security"
    PS_REMOTING = "ps_remoting"
    PS_CLASSES = "ps_classes"
    PS_PESTER = "ps_pester"
    PS_PERFORMANCE = "ps_performance"
    PS_STYLE = "ps_style"
    PS_SCRIPTING = "ps_scripting"
    PS_CLOUD = "ps_cloud"
    PS_WEB = "ps_web"

    # v4.30: JavaScript Categories
    JS_MODERN_SYNTAX = "js_modern_syntax"
    JS_ASYNC_PATTERNS = "js_async_patterns"
    JS_ERROR_HANDLING = "js_error_handling"
    JS_MODULES = "js_modules"
    JS_CLASSES = "js_classes"
    JS_FUNCTIONS = "js_functions"
    JS_TYPE_SAFETY = "js_type_safety"
    JS_SECURITY = "js_security"
    JS_PERFORMANCE = "js_performance"
    JS_TESTING = "js_testing"
    JS_NODE = "js_node"
    JS_EXPRESS = "js_express"
    JS_REACT = "js_react"
    JS_REACT_NATIVE = "react-native"
    JS_API_DESIGN = "js_api_design"
    JS_DATA_MODELING = "js_data_modeling"
    JS_STATE_MANAGEMENT = "js_state_management"
    JS_BUILD_TOOLING = "js_build_tooling"
    JS_STYLE = "js_style"

    # v4.33: Next.js Categories
    NEXTJS_APP_ROUTER = "nextjs_app_router"
    NEXTJS_PAGES_ROUTER = "nextjs_pages_router"
    NEXTJS_DATA_FETCHING = "nextjs_data_fetching"
    NEXTJS_SERVER_ACTIONS = "nextjs_server_actions"
    NEXTJS_CACHING = "nextjs_caching"
    NEXTJS_ROUTING = "nextjs_routing"
    NEXTJS_MIDDLEWARE = "nextjs_middleware"
    NEXTJS_RENDERING = "nextjs_rendering"
    NEXTJS_PERFORMANCE = "nextjs_performance"
    NEXTJS_SECURITY = "nextjs_security"
    NEXTJS_DEPLOYMENT = "nextjs_deployment"
    NEXTJS_CONFIGURATION = "nextjs_configuration"
    NEXTJS_TESTING = "nextjs_testing"
    NEXTJS_METADATA = "nextjs_metadata"
    NEXTJS_IMAGE_OPTIMIZATION = "nextjs_image_optimization"

    # v4.34: Vue.js Categories
    VUE_COMPONENTS = "vue_components"
    VUE_COMPOSITION_API = "vue_composition_api"
    VUE_OPTIONS_API = "vue_options_api"
    VUE_SCRIPT_SETUP = "vue_script_setup"
    VUE_REACTIVITY = "vue_reactivity"
    VUE_COMPOSABLES = "vue_composables"
    VUE_DIRECTIVES = "vue_directives"
    VUE_ROUTING = "vue_routing"
    VUE_STATE_MANAGEMENT = "vue_state_management"
    VUE_PLUGINS = "vue_plugins"
    VUE_PERFORMANCE = "vue_performance"
    VUE_TESTING = "vue_testing"
    VUE_SECURITY = "vue_security"
    VUE_STYLE = "vue_style"
    VUE_TRANSITIONS = "vue_transitions"

    # v4.35: Svelte / SvelteKit Categories
    SVELTE_COMPONENTS = "svelte_components"
    SVELTE_RUNES = "svelte_runes"
    SVELTE_STORES = "svelte_stores"
    SVELTE_ROUTING = "svelte_routing"
    SVELTE_ACTIONS = "svelte_actions"
    SVELTE_LIFECYCLE = "svelte_lifecycle"
    SVELTE_PERFORMANCE = "svelte_performance"
    SVELTE_TESTING = "svelte_testing"
    SVELTE_SECURITY = "svelte_security"
    SVELTE_SVELTEKIT = "svelte_sveltekit"
    SVELTE_FORMS = "svelte_forms"
    SVELTE_ACCESSIBILITY = "svelte_accessibility"
    SVELTE_STATE = "svelte_state"
    SVELTE_TRANSITIONS = "svelte_transitions"
    SVELTE_TYPESCRIPT = "svelte_typescript"

    # v4.35: Tailwind CSS Categories
    TAILWIND_UTILITIES = "tailwind_utilities"
    TAILWIND_CONFIGURATION = "tailwind_configuration"
    TAILWIND_RESPONSIVE = "tailwind_responsive"
    TAILWIND_DARK_MODE = "tailwind_dark_mode"
    TAILWIND_COMPONENTS = "tailwind_components"
    TAILWIND_THEME = "tailwind_theme"
    TAILWIND_PLUGINS = "tailwind_plugins"
    TAILWIND_PERFORMANCE = "tailwind_performance"
    TAILWIND_V4 = "tailwind_v4"
    TAILWIND_ARCHITECTURE = "tailwind_architecture"

    # v4.36: Material UI (MUI) Categories
    MUI_COMPONENTS = "mui_components"
    MUI_THEME = "mui_theme"
    MUI_STYLING = "mui_styling"
    MUI_HOOKS = "mui_hooks"
    MUI_PERFORMANCE = "mui_performance"
    MUI_ACCESSIBILITY = "mui_accessibility"
    MUI_FORMS = "mui_forms"
    MUI_DATA_GRID = "mui_data_grid"
    MUI_NAVIGATION = "mui_navigation"
    MUI_MIGRATION = "mui_migration"

    # v4.37: Ant Design Categories
    ANTD_COMPONENTS = "antd_components"
    ANTD_THEME = "antd_theme"
    ANTD_STYLING = "antd_styling"
    ANTD_HOOKS = "antd_hooks"
    ANTD_PERFORMANCE = "antd_performance"
    ANTD_ACCESSIBILITY = "antd_accessibility"
    ANTD_FORMS = "antd_forms"
    ANTD_TABLE = "antd_table"
    ANTD_NAVIGATION = "antd_navigation"
    ANTD_MIGRATION = "antd_migration"

    # v4.38: Chakra UI Categories
    CHAKRA_COMPONENTS = "chakra_components"
    CHAKRA_THEME = "chakra_theme"
    CHAKRA_STYLING = "chakra_styling"
    CHAKRA_HOOKS = "chakra_hooks"
    CHAKRA_PERFORMANCE = "chakra_performance"
    CHAKRA_ACCESSIBILITY = "chakra_accessibility"
    CHAKRA_FORMS = "chakra_forms"
    CHAKRA_OVERLAY = "chakra_overlay"
    CHAKRA_NAVIGATION = "chakra_navigation"
    CHAKRA_MIGRATION = "chakra_migration"

    # v4.39: shadcn/ui Categories
    SHADCN_COMPONENTS = "shadcn_components"
    SHADCN_THEME = "shadcn_theme"
    SHADCN_STYLING = "shadcn_styling"
    SHADCN_HOOKS = "shadcn_hooks"
    SHADCN_PERFORMANCE = "shadcn_performance"
    SHADCN_ACCESSIBILITY = "shadcn_accessibility"
    SHADCN_FORMS = "shadcn_forms"
    SHADCN_DIALOG = "shadcn_dialog"
    SHADCN_DATA_TABLE = "shadcn_data_table"
    SHADCN_MIGRATION = "shadcn_migration"

    # v4.40: Bootstrap Categories
    BOOTSTRAP_COMPONENTS = "bootstrap_components"
    BOOTSTRAP_GRID = "bootstrap_grid"
    BOOTSTRAP_THEME = "bootstrap_theme"
    BOOTSTRAP_UTILITIES = "bootstrap_utilities"
    BOOTSTRAP_PLUGINS = "bootstrap_plugins"
    BOOTSTRAP_FORMS = "bootstrap_forms"
    BOOTSTRAP_RESPONSIVE = "bootstrap_responsive"
    BOOTSTRAP_ACCESSIBILITY = "bootstrap_accessibility"
    BOOTSTRAP_PERFORMANCE = "bootstrap_performance"
    BOOTSTRAP_MIGRATION = "bootstrap_migration"

    # v4.41: Radix UI Categories
    RADIX_COMPONENTS = "radix_components"
    RADIX_PRIMITIVES = "radix_primitives"
    RADIX_THEME = "radix_theme"
    RADIX_STYLING = "radix_styling"
    RADIX_COMPOSITION = "radix_composition"
    RADIX_ACCESSIBILITY = "radix_accessibility"
    RADIX_PERFORMANCE = "radix_performance"
    RADIX_ANIMATION = "radix_animation"
    RADIX_FORMS = "radix_forms"
    RADIX_MIGRATION = "radix_migration"

    # v4.42: Styled Components Categories
    SC_COMPONENTS = "sc_components"
    SC_THEME = "sc_theme"
    SC_STYLING = "sc_styling"
    SC_MIXINS = "sc_mixins"
    SC_PERFORMANCE = "sc_performance"
    SC_ACCESSIBILITY = "sc_accessibility"
    SC_SSR = "sc_ssr"
    SC_TESTING = "sc_testing"
    SC_PATTERNS = "sc_patterns"
    SC_MIGRATION = "sc_migration"

    # v4.43: Emotion CSS-in-JS Categories
    EM_COMPONENTS = "em_components"
    EM_CSS_PROP = "em_css_prop"
    EM_THEME = "em_theme"
    EM_STYLING = "em_styling"
    EM_PERFORMANCE = "em_performance"
    EM_ACCESSIBILITY = "em_accessibility"
    EM_SSR = "em_ssr"
    EM_TESTING = "em_testing"
    EM_PATTERNS = "em_patterns"
    EM_MIGRATION = "em_migration"

    # v4.47: Redux / Redux Toolkit Categories
    REDUX_STORE = "redux_store"
    REDUX_SLICES = "redux_slices"
    REDUX_MIDDLEWARE = "redux_middleware"
    REDUX_SELECTORS = "redux_selectors"
    REDUX_RTK_QUERY = "redux_rtk_query"
    REDUX_SAGAS = "redux_sagas"
    REDUX_PERFORMANCE = "redux_performance"
    REDUX_TESTING = "redux_testing"
    REDUX_TYPE_SAFETY = "redux_type_safety"
    REDUX_MIGRATION = "redux_migration"

    # v4.48: Zustand Categories
    ZUSTAND_STORE = "zustand_store"
    ZUSTAND_SELECTORS = "zustand_selectors"
    ZUSTAND_MIDDLEWARE = "zustand_middleware"
    ZUSTAND_ACTIONS = "zustand_actions"
    ZUSTAND_TYPESCRIPT = "zustand_typescript"
    ZUSTAND_PERFORMANCE = "zustand_performance"
    ZUSTAND_TESTING = "zustand_testing"
    ZUSTAND_SSR = "zustand_ssr"
    ZUSTAND_PATTERNS = "zustand_patterns"
    ZUSTAND_MIGRATION = "zustand_migration"

    # v4.49: Jotai Categories
    JOTAI_ATOMS = "jotai_atoms"
    JOTAI_SELECTORS = "jotai_selectors"
    JOTAI_MIDDLEWARE = "jotai_middleware"
    JOTAI_ACTIONS = "jotai_actions"
    JOTAI_TYPESCRIPT = "jotai_typescript"
    JOTAI_PERFORMANCE = "jotai_performance"
    JOTAI_TESTING = "jotai_testing"
    JOTAI_SSR = "jotai_ssr"
    JOTAI_PATTERNS = "jotai_patterns"
    JOTAI_MIGRATION = "jotai_migration"

    # v4.50: Recoil Categories
    RECOIL_ATOMS = "recoil_atoms"
    RECOIL_SELECTORS = "recoil_selectors"
    RECOIL_EFFECTS = "recoil_effects"
    RECOIL_HOOKS = "recoil_hooks"
    RECOIL_SNAPSHOT = "recoil_snapshot"
    RECOIL_TYPESCRIPT = "recoil_typescript"
    RECOIL_PERFORMANCE = "recoil_performance"
    RECOIL_TESTING = "recoil_testing"
    RECOIL_PATTERNS = "recoil_patterns"

    # v4.51: MobX Categories
    MOBX_OBSERVABLE = "mobx_observable"
    MOBX_ACTION = "mobx_action"
    MOBX_COMPUTED = "mobx_computed"
    MOBX_REACTION = "mobx_reaction"
    MOBX_CONFIG = "mobx_config"
    MOBX_REACT = "mobx_react"
    MOBX_TESTING = "mobx_testing"
    MOBX_ARCHITECTURE = "mobx_architecture"
    MOBX_MIGRATION = "mobx_migration"

    # v4.52: Pinia Categories
    PINIA_STORE = "pinia_store"
    PINIA_GETTER = "pinia_getter"
    PINIA_ACTION = "pinia_action"
    PINIA_PLUGIN = "pinia_plugin"
    PINIA_TYPESCRIPT = "pinia_typescript"
    PINIA_PERFORMANCE = "pinia_performance"
    PINIA_TESTING = "pinia_testing"
    PINIA_SSR = "pinia_ssr"
    PINIA_PATTERN = "pinia_pattern"

    # v4.53: NgRx Categories
    NGRX_STORE = "ngrx_store"
    NGRX_EFFECTS = "ngrx_effects"
    NGRX_SELECTORS = "ngrx_selectors"
    NGRX_ACTIONS = "ngrx_actions"
    NGRX_ENTITY = "ngrx_entity"
    NGRX_PERFORMANCE = "ngrx_performance"
    NGRX_TESTING = "ngrx_testing"
    NGRX_TYPE_SAFETY = "ngrx_type_safety"
    NGRX_MIGRATION = "ngrx_migration"
    NGRX_SIGNALS = "ngrx_signals"

    # v4.55: XState Categories
    XSTATE_MACHINE = "xstate_machine"
    XSTATE_STATES = "xstate_states"
    XSTATE_ACTIONS = "xstate_actions"
    XSTATE_GUARDS = "xstate_guards"
    XSTATE_ACTORS = "xstate_actors"
    XSTATE_TYPESCRIPT = "xstate_typescript"
    XSTATE_PERFORMANCE = "xstate_performance"
    XSTATE_TESTING = "xstate_testing"
    XSTATE_PATTERNS = "xstate_patterns"
    XSTATE_MIGRATION = "xstate_migration"

    # v4.56: Valtio Categories
    VALTIO_PROXY = "valtio_proxy"
    VALTIO_SNAPSHOT = "valtio_snapshot"
    VALTIO_SUBSCRIPTION = "valtio_subscription"
    VALTIO_ACTION = "valtio_action"
    VALTIO_TYPESCRIPT = "valtio_typescript"
    VALTIO_PERFORMANCE = "valtio_performance"
    VALTIO_TESTING = "valtio_testing"
    VALTIO_SSR = "valtio_ssr"
    VALTIO_PATTERNS = "valtio_patterns"
    VALTIO_MIGRATION = "valtio_migration"

    # v4.57: TanStack Query Categories
    TANSTACK_QUERY_QUERIES = "tanstack_query_queries"
    TANSTACK_QUERY_MUTATIONS = "tanstack_query_mutations"
    TANSTACK_QUERY_CACHE = "tanstack_query_cache"
    TANSTACK_QUERY_SSR = "tanstack_query_ssr"
    TANSTACK_QUERY_TYPESCRIPT = "tanstack_query_typescript"
    TANSTACK_QUERY_PERFORMANCE = "tanstack_query_performance"
    TANSTACK_QUERY_TESTING = "tanstack_query_testing"
    TANSTACK_QUERY_PATTERNS = "tanstack_query_patterns"
    TANSTACK_QUERY_MIGRATION = "tanstack_query_migration"
    TANSTACK_QUERY_INTEGRATION = "tanstack_query_integration"

    # v4.58: SWR Categories
    SWR_HOOKS = "swr_hooks"
    SWR_MUTATIONS = "swr_mutations"
    SWR_CACHE = "swr_cache"
    SWR_MIDDLEWARE = "swr_middleware"
    SWR_INFINITE = "swr_infinite"
    SWR_TYPESCRIPT = "swr_typescript"
    SWR_NEXTJS = "swr_nextjs"
    SWR_TESTING = "swr_testing"
    SWR_PATTERNS = "swr_patterns"
    SWR_MIGRATION = "swr_migration"

    # v4.59: Apollo Client Categories
    APOLLO_QUERIES = "apollo_queries"
    APOLLO_MUTATIONS = "apollo_mutations"
    APOLLO_CACHE = "apollo_cache"
    APOLLO_SUBSCRIPTIONS = "apollo_subscriptions"
    APOLLO_LINKS = "apollo_links"
    APOLLO_TYPESCRIPT = "apollo_typescript"
    APOLLO_TESTING = "apollo_testing"
    APOLLO_SSR = "apollo_ssr"
    APOLLO_PATTERNS = "apollo_patterns"
    APOLLO_MIGRATION = "apollo_migration"

    # v4.60: Astro Framework Categories
    ASTRO_COMPONENTS = "astro_components"
    ASTRO_ISLANDS = "astro_islands"
    ASTRO_ROUTING = "astro_routing"
    ASTRO_CONTENT = "astro_content"
    ASTRO_PERFORMANCE = "astro_performance"
    ASTRO_TYPESCRIPT = "astro_typescript"
    ASTRO_TESTING = "astro_testing"
    ASTRO_SECURITY = "astro_security"
    ASTRO_SSR = "astro_ssr"
    ASTRO_PATTERNS = "astro_patterns"

    # v4.61: Remix / React Router v7 Framework Categories
    REMIX_ROUTES = "remix_routes"
    REMIX_LOADERS = "remix_loaders"
    REMIX_ACTIONS = "remix_actions"
    REMIX_META = "remix_meta"
    REMIX_FORMS = "remix_forms"
    REMIX_ERROR_HANDLING = "remix_error_handling"
    REMIX_SESSION = "remix_session"
    REMIX_PERFORMANCE = "remix_performance"
    REMIX_TYPESCRIPT = "remix_typescript"
    REMIX_PATTERNS = "remix_patterns"

    # v4.62: Solid.js Framework Categories
    SOLIDJS_SIGNALS = "solidjs_signals"
    SOLIDJS_STORES = "solidjs_stores"
    SOLIDJS_COMPONENTS = "solidjs_components"
    SOLIDJS_RESOURCES = "solidjs_resources"
    SOLIDJS_ROUTING = "solidjs_routing"
    SOLIDJS_CONTEXT = "solidjs_context"
    SOLIDJS_LIFECYCLE = "solidjs_lifecycle"
    SOLIDJS_PERFORMANCE = "solidjs_performance"
    SOLIDJS_TYPESCRIPT = "solidjs_typescript"
    SOLIDJS_PATTERNS = "solidjs_patterns"

    # v4.63: Qwik Framework Categories
    QWIK_COMPONENTS = "qwik_components"
    QWIK_SIGNALS = "qwik_signals"
    QWIK_TASKS = "qwik_tasks"
    QWIK_ROUTING = "qwik_routing"
    QWIK_CONTEXT = "qwik_context"
    QWIK_PERFORMANCE = "qwik_performance"
    QWIK_SSR = "qwik_ssr"
    QWIK_TYPESCRIPT = "qwik_typescript"
    QWIK_PATTERNS = "qwik_patterns"
    QWIK_CITY = "qwik_city"

    # v4.64: Preact Framework Categories
    PREACT_COMPONENTS = "preact_components"
    PREACT_HOOKS = "preact_hooks"
    PREACT_SIGNALS = "preact_signals"
    PREACT_CONTEXT = "preact_context"
    PREACT_PERFORMANCE = "preact_performance"
    PREACT_SSR = "preact_ssr"
    PREACT_TYPESCRIPT = "preact_typescript"
    PREACT_PATTERNS = "preact_patterns"
    PREACT_COMPAT = "preact_compat"
    PREACT_ROUTING = "preact_routing"

    # v4.65: Lit / Web Components Framework Categories
    LIT_COMPONENTS = "lit_components"
    LIT_PROPERTIES = "lit_properties"
    LIT_TEMPLATES = "lit_templates"
    LIT_EVENTS = "lit_events"
    LIT_CSS = "lit_css"
    LIT_CONTEXT = "lit_context"
    LIT_SSR = "lit_ssr"
    LIT_PERFORMANCE = "lit_performance"
    LIT_PATTERNS = "lit_patterns"

    # v4.66: Alpine.js Framework Categories
    ALPINE_DIRECTIVES = "alpine_directives"
    ALPINE_COMPONENTS = "alpine_components"
    ALPINE_STORES = "alpine_stores"
    ALPINE_PLUGINS = "alpine_plugins"
    ALPINE_REACTIVITY = "alpine_reactivity"
    ALPINE_EVENTS = "alpine_events"
    ALPINE_TRANSITIONS = "alpine_transitions"
    ALPINE_PERFORMANCE = "alpine_performance"
    ALPINE_PATTERNS = "alpine_patterns"
    ALPINE_SECURITY = "alpine_security"

    # v4.67: HTMX Framework Categories
    HTMX_ATTRIBUTES = "htmx_attributes"
    HTMX_REQUESTS = "htmx_requests"
    HTMX_EVENTS = "htmx_events"
    HTMX_EXTENSIONS = "htmx_extensions"
    HTMX_SWAPPING = "htmx_swapping"
    HTMX_TRIGGERS = "htmx_triggers"
    HTMX_PERFORMANCE = "htmx_performance"
    HTMX_PATTERNS = "htmx_patterns"
    HTMX_SECURITY = "htmx_security"
    HTMX_TESTING = "htmx_testing"

    # v4.68: Stimulus Framework Categories
    STIMULUS_CONTROLLERS = "stimulus_controllers"
    STIMULUS_TARGETS = "stimulus_targets"
    STIMULUS_VALUES = "stimulus_values"
    STIMULUS_ACTIONS = "stimulus_actions"
    STIMULUS_OUTLETS = "stimulus_outlets"
    STIMULUS_PATTERNS = "stimulus_patterns"
    STIMULUS_LIFECYCLE = "stimulus_lifecycle"
    STIMULUS_PERFORMANCE = "stimulus_performance"
    STIMULUS_TESTING = "stimulus_testing"
    STIMULUS_TURBO = "stimulus_turbo"

    # v4.70: Storybook Framework Categories
    STORYBOOK_STORIES = "storybook_stories"
    STORYBOOK_COMPONENTS = "storybook_components"
    STORYBOOK_ADDONS = "storybook_addons"
    STORYBOOK_CONFIG = "storybook_config"
    STORYBOOK_TESTING = "storybook_testing"
    STORYBOOK_PATTERNS = "storybook_patterns"

    # v4.71: Three.js / React Three Fiber Categories
    THREEJS_SCENE = "threejs_scene"
    THREEJS_COMPONENTS = "threejs_components"
    THREEJS_MATERIALS = "threejs_materials"
    THREEJS_ANIMATION = "threejs_animation"
    THREEJS_INTERACTION = "threejs_interaction"
    THREEJS_PERFORMANCE = "threejs_performance"
    THREEJS_PHYSICS = "threejs_physics"
    THREEJS_POSTPROCESSING = "threejs_postprocessing"
    THREEJS_ADVANCED = "threejs_advanced"
    THREEJS_XR = "threejs_xr"

    # D3.js Data Visualization Categories (v4.72)
    D3JS_SELECTIONS = "d3js_selections"
    D3JS_DATA_JOINS = "d3js_data_joins"
    D3JS_SCALES = "d3js_scales"
    D3JS_AXES = "d3js_axes"
    D3JS_SHAPES = "d3js_shapes"
    D3JS_LAYOUTS = "d3js_layouts"
    D3JS_INTERACTION = "d3js_interaction"
    D3JS_PERFORMANCE = "d3js_performance"
    D3JS_ADVANCED = "d3js_advanced"
    D3JS_GEO = "d3js_geo"

    # Chart.js Charting Library Categories (v4.73)
    CHARTJS_CHART_CONFIG = "chartjs_chart_config"
    CHARTJS_DATASETS = "chartjs_datasets"
    CHARTJS_SCALES = "chartjs_scales"
    CHARTJS_PLUGINS = "chartjs_plugins"
    CHARTJS_ANIMATION = "chartjs_animation"
    CHARTJS_INTERACTION = "chartjs_interaction"
    CHARTJS_STYLING = "chartjs_styling"
    CHARTJS_PERFORMANCE = "chartjs_performance"
    CHARTJS_ADVANCED = "chartjs_advanced"
    CHARTJS_ECOSYSTEM = "chartjs_ecosystem"

    # Recharts Data Visualization Categories (v4.74)
    RECHARTS_COMPONENTS = "recharts_components"
    RECHARTS_SERIES = "recharts_series"
    RECHARTS_AXES = "recharts_axes"
    RECHARTS_TOOLTIP = "recharts_tooltip"
    RECHARTS_LEGEND = "recharts_legend"
    RECHARTS_ANIMATION = "recharts_animation"
    RECHARTS_STYLING = "recharts_styling"
    RECHARTS_PERFORMANCE = "recharts_performance"
    RECHARTS_ADVANCED = "recharts_advanced"
    RECHARTS_ECOSYSTEM = "recharts_ecosystem"

    # Leaflet/Mapbox Mapping Categories (v4.75)
    LEAFLET_MAPS = "leaflet_maps"
    LEAFLET_LAYERS = "leaflet_layers"
    LEAFLET_MARKERS = "leaflet_markers"
    LEAFLET_CONTROLS = "leaflet_controls"
    LEAFLET_POPUPS = "leaflet_popups"
    LEAFLET_EVENTS = "leaflet_events"
    LEAFLET_GEOJSON = "leaflet_geojson"
    LEAFLET_PLUGINS = "leaflet_plugins"
    LEAFLET_PERFORMANCE = "leaflet_performance"
    LEAFLET_ECOSYSTEM = "leaflet_ecosystem"

    # Framer Motion Animation Categories (v4.76)
    FRAMER_ANIMATIONS = "framer_animations"
    FRAMER_VARIANTS = "framer_variants"
    FRAMER_GESTURES = "framer_gestures"
    FRAMER_LAYOUT = "framer_layout"
    FRAMER_SCROLL = "framer_scroll"
    FRAMER_TRANSITIONS = "framer_transitions"
    FRAMER_PERFORMANCE = "framer_performance"
    FRAMER_ACCESSIBILITY = "framer_accessibility"
    FRAMER_HOOKS = "framer_hooks"
    FRAMER_ECOSYSTEM = "framer_ecosystem"

    # GSAP Animation Categories (v4.77)
    GSAP_ANIMATIONS = "gsap_animations"
    GSAP_TIMELINES = "gsap_timelines"
    GSAP_PLUGINS = "gsap_plugins"
    GSAP_SCROLL = "gsap_scroll"
    GSAP_PERFORMANCE = "gsap_performance"
    GSAP_CONTEXT = "gsap_context"
    GSAP_EASING = "gsap_easing"
    GSAP_STAGGER = "gsap_stagger"
    GSAP_INTEGRATION = "gsap_integration"
    GSAP_MIGRATION = "gsap_migration"

    # RxJS Reactive Programming Categories (v4.78)
    RXJS_OPERATORS = "rxjs_operators"
    RXJS_OBSERVABLES = "rxjs_observables"
    RXJS_SUBJECTS = "rxjs_subjects"
    RXJS_SCHEDULERS = "rxjs_schedulers"
    RXJS_PATTERNS = "rxjs_patterns"
    RXJS_ERROR_HANDLING = "rxjs_error_handling"
    RXJS_PERFORMANCE = "rxjs_performance"
    RXJS_TESTING = "rxjs_testing"
    RXJS_MULTICASTING = "rxjs_multicasting"
    RXJS_MIGRATION = "rxjs_migration"

    # DevOps Categories (cross-language)
    DEVOPS = "devops"


class PracticeLevel(Enum):
    """Expertise level for a practice.

    Used to filter practices based on developer experience level.
    """

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class PracticePriority(Enum):
    """Priority level for applying a practice.

    Higher priority practices should be applied first and are
    more critical for code quality.
    """

    CRITICAL = "critical"  # Must always follow
    HIGH = "high"  # Strongly recommended
    MEDIUM = "medium"  # Recommended
    LOW = "low"  # Nice to have
    OPTIONAL = "optional"  # Style preference


class SOLIDPrinciple(Enum):
    """The five SOLID principles of object-oriented design.

    Each principle is associated with specific best practices
    that help achieve better software design.
    """

    SRP = "single_responsibility"
    OCP = "open_closed"
    LSP = "liskov_substitution"
    ISP = "interface_segregation"
    DIP = "dependency_inversion"


class DesignPatternType(Enum):
    """Categories of design patterns.

    Patterns are organized by their primary purpose following
    the Gang of Four classification.
    """

    CREATIONAL = "creational"
    STRUCTURAL = "structural"
    BEHAVIORAL = "behavioral"
    ARCHITECTURAL = "architectural"
    CONCURRENCY = "concurrency"


@dataclass(frozen=True)
class VersionConstraint:
    """Version constraint for a practice applicability.

    Defines minimum and/or maximum version requirements for
    when a practice is applicable.

    Attributes:
        min_version: Minimum version (inclusive), e.g., "3.9".
        max_version: Maximum version (inclusive), e.g., "3.12".
        excluded_versions: Specific versions to exclude.

    Example:
        >>> constraint = VersionConstraint(min_version="3.9", max_version="3.12")
        >>> constraint.is_compatible("3.10")
        True
    """

    min_version: Optional[str] = None
    max_version: Optional[str] = None
    excluded_versions: tuple[str, ...] = field(default_factory=tuple)

    def is_compatible(self, version: str) -> bool:
        """Check if a version is compatible with this constraint.

        Args:
            version: The version string to check, e.g., "3.10".

        Returns:
            True if the version satisfies the constraint.
        """
        if version in self.excluded_versions:
            return False

        version_tuple = self._parse_version(version)

        if self.min_version:
            min_tuple = self._parse_version(self.min_version)
            if version_tuple < min_tuple:
                return False

        if self.max_version:
            max_tuple = self._parse_version(self.max_version)
            if version_tuple > max_tuple:
                return False

        return True

    @staticmethod
    def _parse_version(version: str) -> tuple[int, ...]:
        """Parse a version string into a comparable tuple.

        Args:
            version: Version string like "3.10" or "3.10.1".

        Returns:
            Tuple of integers for comparison.
        """
        parts = version.split(".")
        return tuple(int(p) for p in parts if p.isdigit())

    def to_string(self) -> str:
        """Convert constraint to a readable string.

        Returns:
            Human-readable version constraint string.
        """
        parts = []
        if self.min_version:
            parts.append(f">={self.min_version}")
        if self.max_version:
            parts.append(f"<={self.max_version}")
        if self.excluded_versions:
            excluded = ",".join(self.excluded_versions)
            parts.append(f"!={excluded}")
        return " ".join(parts) if parts else "any"


@dataclass(frozen=True)
class ApplicabilityRule:
    """Rule that determines when a practice applies.

    Used to match practices to specific project contexts based on
    detected frameworks, patterns, and project characteristics.

    Attributes:
        frameworks: Frameworks that must be detected.
        patterns: Architecture patterns that must be present.
        file_patterns: Glob patterns for applicable files.
        has_dependencies: Required package dependencies.
        project_types: Applicable project types.
        excluded_patterns: Patterns that exclude this rule.
        min_python: Minimum Python version required (e.g., "3.10").
        contexts: Usage contexts where this practice is most relevant
            (e.g., ["dispatch", "parsing", "state-machines"]).

    Example:
        >>> rule = ApplicabilityRule(
        ...     frameworks=["fastapi"],
        ...     has_dependencies=["pydantic"],
        ...     min_python="3.10",
        ...     contexts=("async", "concurrent-io"),
        ... )
    """

    frameworks: tuple[str, ...] = field(default_factory=tuple)
    patterns: tuple[str, ...] = field(default_factory=tuple)
    file_patterns: tuple[str, ...] = field(default_factory=tuple)
    has_dependencies: tuple[str, ...] = field(default_factory=tuple)
    project_types: tuple[str, ...] = field(default_factory=tuple)
    excluded_patterns: tuple[str, ...] = field(default_factory=tuple)
    min_python: Optional[str] = None
    contexts: tuple[str, ...] = field(default_factory=tuple)

    def matches(self, context: Dict[str, Any]) -> bool:
        """Check if this rule matches the given context.

        Args:
            context: Dictionary containing project context with keys:
                - frameworks: Set of detected framework names
                - patterns: Set of detected architecture patterns
                - dependencies: Set of package names
                - project_type: String of project type
                - file_path: Current file path (optional)

        Returns:
            True if all conditions in the rule are satisfied.
        """
        # Check frameworks
        if self.frameworks:
            ctx_frameworks = set(context.get("frameworks", []))
            if not any(f in ctx_frameworks for f in self.frameworks):
                return False

        # Check patterns
        if self.patterns:
            ctx_patterns = set(context.get("patterns", []))
            if not any(p in ctx_patterns for p in self.patterns):
                return False

        # Check dependencies
        if self.has_dependencies:
            ctx_deps = set(context.get("dependencies", []))
            if not all(d in ctx_deps for d in self.has_dependencies):
                return False

        # Check project type
        if self.project_types:
            ctx_type = context.get("project_type", "")
            if ctx_type not in self.project_types:
                return False

        # Check excluded patterns
        if self.excluded_patterns:
            ctx_patterns = set(context.get("patterns", []))
            if any(p in ctx_patterns for p in self.excluded_patterns):
                return False

        # Check minimum Python version
        if self.min_python:
            ctx_python = context.get("python_version", "")
            if ctx_python:
                try:
                    min_parts = tuple(int(p) for p in self.min_python.split(".") if p.isdigit())
                    ctx_parts = tuple(int(p) for p in ctx_python.split(".") if p.isdigit())
                    if ctx_parts < min_parts:
                        return False
                except (ValueError, TypeError):
                    pass  # Can't compare, assume compatible

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to a dictionary.

        Returns:
            Dictionary representation of the rule.
        """
        result: Dict[str, Any] = {}
        if self.frameworks:
            result["frameworks"] = list(self.frameworks)
        if self.patterns:
            result["patterns"] = list(self.patterns)
        if self.file_patterns:
            result["file_patterns"] = list(self.file_patterns)
        if self.has_dependencies:
            result["has_dependencies"] = list(self.has_dependencies)
        if self.project_types:
            result["project_types"] = list(self.project_types)
        if self.excluded_patterns:
            result["excluded_patterns"] = list(self.excluded_patterns)
        if self.min_python:
            result["min_python"] = self.min_python
        if self.contexts:
            result["contexts"] = list(self.contexts)
        return result


@dataclass
class PracticeContent:
    """The actual content of a best practice.

    Contains all the instructional content including description,
    examples, rationale, and anti-patterns.

    Attributes:
        description: Full description of the practice.
        rationale: Why this practice is important.
        good_examples: List of code examples showing correct usage.
        bad_examples: List of anti-pattern examples.
        references: External reference links.
        related_practices: IDs of related practices.
        tags: Additional searchable tags.
    """

    description: str
    rationale: str = ""
    good_examples: List[str] = field(default_factory=list)
    bad_examples: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    related_practices: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert content to a dictionary.

        Returns:
            Dictionary representation of the content.
        """
        return {
            "description": self.description,
            "rationale": self.rationale,
            "good_examples": self.good_examples,
            "bad_examples": self.bad_examples,
            "references": self.references,
            "related_practices": self.related_practices,
            "tags": self.tags,
        }

    def to_compressed(self, max_length: int = 500) -> str:
        """Get a compressed version for token-efficient output.

        Args:
            max_length: Maximum length of the compressed output.

        Returns:
            Compressed string representation.
        """
        parts = [self.description[:max_length]]
        if self.good_examples:
            parts.append(f"Example: {self.good_examples[0][:200]}")
        return " | ".join(parts)


@dataclass
class DesignPattern:
    """A software design pattern.

    Represents a reusable solution to a commonly occurring problem
    in software design.

    Attributes:
        name: Pattern name (e.g., "Factory", "Observer").
        pattern_type: Category of the pattern.
        description: What the pattern does.
        when_to_use: Situations where this pattern is appropriate.
        structure: Code structure or template.
        python_example: Python implementation example.
        related_patterns: Names of related patterns.
    """

    name: str
    pattern_type: DesignPatternType
    description: str
    when_to_use: List[str] = field(default_factory=list)
    structure: str = ""
    python_example: str = ""
    related_patterns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to a dictionary.

        Returns:
            Dictionary representation of the pattern.
        """
        return {
            "name": self.name,
            "pattern_type": self.pattern_type.value,
            "description": self.description,
            "when_to_use": self.when_to_use,
            "structure": self.structure,
            "python_example": self.python_example,
            "related_patterns": self.related_patterns,
        }

    def to_codetrellis_format(self) -> str:
        """Format pattern for CodeTrellis output.

        Returns:
            CodeTrellis-formatted string representation.
        """
        parts = [f"{self.name}|type:{self.pattern_type.value}"]
        if self.when_to_use:
            use_cases = ";".join(self.when_to_use[:3])
            parts.append(f"use:{use_cases}")
        return "|".join(parts)


@dataclass
class BestPractice:
    """A complete best practice definition.

    The main model representing a single best practice with all
    its metadata, content, and applicability rules.

    Attributes:
        id: Unique identifier (e.g., "PY001", "FAST001").
        title: Short descriptive title.
        category: Primary category of the practice.
        level: Expertise level required.
        priority: Importance/priority level.
        content: The actual practice content.
        python_version: Version constraint for Python.
        applicability: Rules for when this practice applies.
        solid_principles: Related SOLID principles.
        design_patterns: Related design patterns.
        complexity_score: Implementation complexity (1-10 scale).
            1-3: Simple, quick to implement
            4-6: Moderate, requires some refactoring
            7-10: Complex, significant architectural changes
        anti_pattern_id: ID of the related anti-pattern practice
            for cross-referencing good vs bad patterns.
        created_at: When the practice was created.
        updated_at: When the practice was last updated.
        deprecated: Whether this practice is deprecated.
        superseded_by: ID of practice that supersedes this one.

    Example:
        >>> practice = BestPractice(
        ...     id="PY001",
        ...     title="Use Type Hints",
        ...     category=PracticeCategory.TYPE_SAFETY,
        ...     level=PracticeLevel.BEGINNER,
        ...     priority=PracticePriority.HIGH,
        ...     content=PracticeContent(
        ...         description="Always use type hints for function parameters and return values."
        ...     )
        ... )
    """

    id: str
    title: str
    category: PracticeCategory
    level: PracticeLevel = PracticeLevel.INTERMEDIATE
    priority: PracticePriority = PracticePriority.MEDIUM
    content: PracticeContent = field(default_factory=lambda: PracticeContent(""))
    python_version: VersionConstraint = field(default_factory=VersionConstraint)
    applicability: ApplicabilityRule = field(default_factory=ApplicabilityRule)
    solid_principles: List[SOLIDPrinciple] = field(default_factory=list)
    design_patterns: List[str] = field(default_factory=list)
    complexity_score: Optional[int] = None  # 1-10 scale: 1-3 simple, 4-6 moderate, 7-10 complex
    anti_pattern_id: Optional[str] = None  # Cross-reference to related anti-pattern
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deprecated: bool = False
    superseded_by: Optional[str] = None

    def is_applicable(
        self,
        context: Dict[str, Any],
        python_version: Optional[str] = None,
    ) -> bool:
        """Check if this practice is applicable to the given context.

        Args:
            context: Project context dictionary.
            python_version: Optional Python version to check against.

        Returns:
            True if the practice is applicable.
        """
        if self.deprecated:
            return False

        if python_version and not self.python_version.is_compatible(python_version):
            return False

        return self.applicability.matches(context)

    def to_dict(self) -> Dict[str, Any]:
        """Convert practice to a dictionary.

        Returns:
            Complete dictionary representation.
        """
        result = {
            "id": self.id,
            "title": self.title,
            "category": self.category.value,
            "level": self.level.value,
            "priority": self.priority.value,
            "content": self.content.to_dict(),
            "python_version": {
                "min_version": self.python_version.min_version,
                "max_version": self.python_version.max_version,
                "excluded_versions": list(self.python_version.excluded_versions),
            },
            "applicability": self.applicability.to_dict(),
            "solid_principles": [p.value for p in self.solid_principles],
            "design_patterns": self.design_patterns,
            "deprecated": self.deprecated,
            "superseded_by": self.superseded_by,
        }
        # Add optional fields only if set
        if self.complexity_score is not None:
            result["complexity_score"] = self.complexity_score
        if self.anti_pattern_id is not None:
            result["anti_pattern_id"] = self.anti_pattern_id
        return result

    def to_codetrellis_format(self, compact: bool = False) -> str:
        """Format practice for CodeTrellis output.

        Args:
            compact: If True, return minimal output for token efficiency.

        Returns:
            CodeTrellis-formatted string representation.
        """
        if compact:
            return f"{self.id}|{self.title}|{self.category.value}|{self.priority.value}"

        parts = [
            f"[{self.id}] {self.title}",
            f"  Category: {self.category.value}",
            f"  Level: {self.level.value}",
            f"  Priority: {self.priority.value}",
        ]

        if self.content.description:
            desc = self.content.description[:300]
            parts.append(f"  Description: {desc}")

        if self.content.good_examples:
            parts.append(f"  Example: {self.content.good_examples[0][:200]}")

        if self.solid_principles:
            principles = ", ".join(p.value for p in self.solid_principles)
            parts.append(f"  SOLID: {principles}")

        return "\n".join(parts)


@dataclass
class PracticeSet:
    """A collection of related practices.

    Used to group practices by theme, framework, or use case
    for easier selection and application.

    Attributes:
        name: Name of the practice set.
        description: What this set covers.
        practices: List of practice IDs in this set.
        order: Recommended order to apply practices.
        prerequisites: Other practice sets that should be applied first.
    """

    name: str
    description: str
    practices: List[str] = field(default_factory=list)
    order: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert practice set to a dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "name": self.name,
            "description": self.description,
            "practices": self.practices,
            "order": self.order,
            "prerequisites": self.prerequisites,
        }


@dataclass
class BPLOutput:
    """Output container for BPL results.

    Contains selected practices and metadata about the selection
    process for integration with CodeTrellis output.

    Attributes:
        practices: Selected practices.
        total_available: Total practices in repository.
        filters_applied: Description of filters used.
        context_summary: Summary of the project context used.
        generated_at: When this output was generated.
    """

    practices: List[BestPractice] = field(default_factory=list)
    total_available: int = 0
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    context_summary: str = ""
    generated_at: datetime = field(default_factory=datetime.now)

    def to_codetrellis_format(self, tier: str = "prompt") -> str:
        """Format BPL output for CodeTrellis integration.

        Args:
            tier: Output tier (minimal, compact, prompt, full).

        Returns:
            CodeTrellis-formatted string for the specified tier.
        """
        lines = ["[BEST_PRACTICES]"]

        if tier == "minimal":
            # Bare minimum: ID + title only
            for practice in self.practices:
                lines.append(f"{practice.id}|{practice.title}")
        elif tier == "compact":
            # Minimal output
            for practice in self.practices:
                lines.append(practice.to_codetrellis_format(compact=True))
        elif tier == "prompt":
            # Balanced output for AI prompts
            lines.append(f"# {len(self.practices)} practices selected")
            if self.context_summary:
                lines.append(f"# Context: {self.context_summary}")

            # Group by category
            by_category: Dict[str, List[BestPractice]] = {}
            for practice in self.practices:
                cat = practice.category.value
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(practice)

            for category, practices in by_category.items():
                lines.append(f"\n## {category.upper()}")
                for practice in practices:
                    lines.append(practice.to_codetrellis_format(compact=False))
        else:
            # Full output with all details
            lines.append(f"# Total: {len(self.practices)} / {self.total_available}")
            lines.append(f"# Generated: {self.generated_at.isoformat()}")
            if self.filters_applied:
                filters_str = ", ".join(
                    f"{k}={v}" for k, v in self.filters_applied.items()
                )
                lines.append(f"# Filters: {filters_str}")

            for practice in self.practices:
                lines.append("")
                lines.append(practice.to_codetrellis_format(compact=False))

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert output to a dictionary.

        Returns:
            Complete dictionary representation.
        """
        return {
            "practices": [p.to_dict() for p in self.practices],
            "total_available": self.total_available,
            "filters_applied": self.filters_applied,
            "context_summary": self.context_summary,
            "generated_at": self.generated_at.isoformat(),
        }
