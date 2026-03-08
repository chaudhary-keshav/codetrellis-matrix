"""
CodeTrellis v4.1 Extractors Module

Provides specialized extractors for TypeScript/Angular code elements:
- InterfaceExtractor: TypeScript interfaces
- TypeExtractor: TypeScript type aliases
- ServiceExtractor: Angular @Injectable services
- StoreExtractor: NgRx SignalStore definitions
- RouteExtractor: Angular route definitions
- WebSocketExtractor: WebSocket event patterns
- HttpApiExtractor: HTTP API calls

Phase 2 Context Enrichment:
- JSDocExtractor: JSDoc documentation comments
- ReadmeExtractor: README documentation files
- ConfigExtractor: Project configuration files
- ErrorExtractor: Error handling patterns (NEW in v3.0)
- TodoExtractor: TODO/FIXME comments (NEW in v3.0)

Phase 2.1 Progress & Overview:
- ProgressExtractor: Project progress tracking (TODOs, completion, blockers)
- ArchitectureExtractor: Project overview for onboarding

Phase 3 LSP Integration:
- LSPExtractor: TypeScript Language Server Protocol extraction

Phase 4.1 Implementation Logic (NEW):
- LogicExtractor: Extracts implementation details and code logic
  - Function bodies (compressed to key logic)
  - Control flow patterns
  - API calls and data transformations
  - Addresses: "AI can't see specific code logic" limitation
"""

from .interface_extractor import InterfaceExtractor
from .type_extractor import TypeExtractor
from .service_extractor import ServiceExtractor
from .store_extractor import StoreExtractor
from .route_extractor import RouteExtractor
from .websocket_extractor import WebSocketExtractor
from .http_api_extractor import HttpApiExtractor

# Phase 2: Context enrichment extractors
from .jsdoc_extractor import JSDocExtractor, extract_jsdoc
from .readme_extractor import ReadmeExtractor, extract_readme, extract_project_readmes
from .config_extractor import ConfigExtractor, extract_project_config

# Phase 2.5: Error and TODO extractors (NEW in v3.0)
from .error_extractor import (
    ErrorExtractor,
    ErrorFileInfo,
    TryCatchBlock,
    ErrorClass,
    HttpErrorHandler,
    ErrorBoundary,
    extract_errors,
    extract_project_errors,
)
from .todo_extractor import (
    TodoExtractor,
    TodoFileInfo,
    TodoComment,
    TodoSummary,
    TodoType,
    Priority,
    extract_todos,
    extract_project_todos,
)

# Phase 2.1: Progress & Overview extractors (NEW in v2.1)
from .progress_extractor import (
    ProgressExtractor,
    ProgressMarker,
    PlaceholderImplementation,
    FileProgress,
    ProjectProgress,
    ProgressStatus,
    MarkerType,
)
from .architecture_extractor import (
    ArchitectureExtractor,
    ProjectOverview,
    ProjectType,
    ArchPattern,
    DependencyInfo,
    DirectoryInfo,
    EntryPointInfo,
    ApiConnectionInfo,
)
from .business_domain_extractor import (
    BusinessDomainExtractor,
    BusinessDomainContext,
    DomainCategory,
    DataFlowPattern,
    DomainEntity,
    DataFlow,
    ArchitecturalDecision,
    UserJourney,
)

# Phase 3: LSP-based type extraction
from .lsp_extractor import LSPExtractor, EnhancedInterfaceInfo, LSPExtractionStats

# Phase 4.1: Implementation Logic extraction (NEW)
from .logic_extractor import LogicExtractor, LogicSnippet, LogicFileInfo

# Phase A: Runbook extraction (NEW in v4.2 - WS-1)
from .runbook_extractor import (
    RunbookExtractor,
    RunbookContext,
    CommandInfo,
    CICDPipeline,
    EnvVariable,
    DockerInfo,
    ComposeInfo,
    ComposeService,
)

# Phase C: Infrastructure & NestJS extractors (NEW in v4.4 - WS-6)
from .docker_extractor import (
    DockerExtractor,
    DockerfileInfo,
    DockerStage,
    ComposeServiceInfo,
    ComposeFileInfo,
)
from .terraform_extractor import (
    TerraformExtractor,
    TerraformInfo,
    TerraformResource,
    TerraformVariable,
    TerraformOutput,
    TerraformModule,
)
from .cicd_extractor import (
    CICDExtractor,
    CICDPipelineInfo,
    CICDJob,
)
from .nestjs_extractor import (
    NestJSExtractor,
    NestJSInfo,
    NestJSModule,
    NestJSGuard,
    NestJSInterceptor,
    NestJSPipe,
    NestJSMiddleware,
    NestJSGateway,
    NestJSGatewayEvent,
)

# Phase G-17: Go Language Extractors (NEW in v4.5)
from .go import (
    GoTypeExtractor, GoStructInfo, GoInterfaceInfo, GoTypeAliasInfo, GoFieldInfo,
    GoFunctionExtractor, GoFunctionInfo, GoMethodInfo, GoParameterInfo,
    GoEnumExtractor, GoConstBlockInfo, GoConstValueInfo,
    GoAPIExtractor, GoRouteInfo, GoGRPCServiceInfo, GoHandlerInfo,
)

# Phase v4.6: Semantic Extractors (Generic language-agnostic)
from .semantic_extractor import (
    SemanticExtractor,
    SemanticResult,
    HookInfo,
    MiddlewareInfo,
    GenericRouteInfo,
    PluginInfo,
    LifecycleInfo,
)

# Phase v5.0: Universal Scanner Extractors
from .discovery_extractor import (
    DiscoveryExtractor,
    ProjectDiscoveryResult,
    SubProjectInfo,
    SpecFileInfo,
    ConfigTemplateInfo,
    LanguageBreakdown,
)
from .architecture_extractor import ProjectProfile
from .openapi_extractor import (
    OpenAPIExtractor,
    OpenAPIInfo,
    OpenAPIEndpoint,
    OpenAPISecurityScheme,
    OpenAPIModel,
)
from .graphql_schema_extractor import (
    GraphQLSchemaExtractor,
    GraphQLSchemaInfo,
    GraphQLType,
    GraphQLField,
    GraphQLOperation,
)
from .config_template_extractor import (
    ConfigTemplateExtractor,
    ConfigTemplateResult,
    ConfigTemplate,
    ConfigVariable,
)
from .env_inference_extractor import (
    EnvInferenceExtractor,
    EnvInferenceResult,
    InferredEnvVar,
)
from .security_extractor import (
    SecurityExtractor,
    SecurityResult,
    AuthMechanism,
    AuthzPattern,
    SecurityFlag,
)
from .database_architecture_extractor import (
    DatabaseArchitectureExtractor,
    DatabaseArchitectureResult,
    DatabaseInfo,
    DatabaseModel,
    MigrationInfo,
)
from .sub_project_extractor import (
    SubProjectExtractor,
    SubProjectResult,
    SubProjectAnalysis,
    SubProjectDependency,
)
from .generic_language_extractor import (
    GenericLanguageExtractor,
    GenericLanguageResult,
    GenericFileResult,
    GenericFunction,
    GenericType,
    GenericImport,
)

# Phase v4.16: HTML Language Extractors (NEW)
from .html import (
    HTMLStructureExtractor, HTMLDocumentInfo, HTMLSectionInfo,
    HTMLHeadingInfo, HTMLLandmarkInfo,
    HTMLSemanticExtractor, HTMLSemanticElementInfo, HTMLMicrodataInfo,
    HTMLFormExtractor, HTMLFormInfo, HTMLInputInfo, HTMLFieldsetInfo,
    HTMLMetaExtractor, HTMLMetaInfo, HTMLLinkInfo,
    HTMLOpenGraphInfo, HTMLJsonLdInfo,
    HTMLAccessibilityExtractor, HTMLAriaInfo, HTMLA11yIssue,
    HTMLTemplateExtractor, HTMLTemplateInfo, HTMLTemplateBlockInfo,
    HTMLAssetExtractor, HTMLScriptInfo, HTMLStyleInfo, HTMLPreloadInfo,
    HTMLComponentExtractor, HTMLCustomElementInfo, HTMLSlotInfo,
)

__all__ = [
    # Phase 1: Code structure extractors
    'InterfaceExtractor',
    'TypeExtractor',
    'ServiceExtractor',
    'StoreExtractor',
    'RouteExtractor',
    'WebSocketExtractor',
    'HttpApiExtractor',
    # Phase 2: Context enrichment extractors
    'JSDocExtractor',
    'ReadmeExtractor',
    'ConfigExtractor',
    'extract_jsdoc',
    'extract_readme',
    'extract_project_readmes',
    'extract_project_config',
    # Phase 2.5: Error and TODO extractors (NEW in v3.0)
    'ErrorExtractor',
    'ErrorFileInfo',
    'TryCatchBlock',
    'ErrorClass',
    'HttpErrorHandler',
    'ErrorBoundary',
    'extract_errors',
    'extract_project_errors',
    'TodoExtractor',
    'TodoFileInfo',
    'TodoComment',
    'TodoSummary',
    'TodoType',
    'Priority',
    'extract_todos',
    'extract_project_todos',
    # Phase 2.1: Progress & Overview extractors (NEW in v2.1)
    'ProgressExtractor',
    'ProgressMarker',
    'PlaceholderImplementation',
    'FileProgress',
    'ProjectProgress',
    'ProgressStatus',
    'MarkerType',
    'ArchitectureExtractor',
    'ProjectOverview',
    'ProjectType',
    'ArchPattern',
    'DependencyInfo',
    'DirectoryInfo',
    'EntryPointInfo',
    'ApiConnectionInfo',
    # Phase 3.1: Business Domain extractors (NEW in v3.1)
    'BusinessDomainExtractor',
    'BusinessDomainContext',
    'DomainCategory',
    'DataFlowPattern',
    'DomainEntity',
    'DataFlow',
    'ArchitecturalDecision',
    'UserJourney',
    # Phase 3: LSP extractors
    'LSPExtractor',
    'EnhancedInterfaceInfo',
    'LSPExtractionStats',
    # Phase 4.1: Implementation Logic extractors (NEW)
    'LogicExtractor',
    'LogicSnippet',
    'LogicFileInfo',
    # Phase A: Runbook extractors (NEW in v4.2 - WS-1)
    'RunbookExtractor',
    'RunbookContext',
    'CommandInfo',
    'CICDPipeline',
    'EnvVariable',
    'DockerInfo',
    'ComposeInfo',
    'ComposeService',
    # Phase C: Infrastructure & NestJS extractors (NEW in v4.4 - WS-6)
    'DockerExtractor',
    'DockerfileInfo',
    'DockerStage',
    'ComposeServiceInfo',
    'ComposeFileInfo',
    'TerraformExtractor',
    'TerraformInfo',
    'TerraformResource',
    'TerraformVariable',
    'TerraformOutput',
    'TerraformModule',
    'CICDExtractor',
    'CICDPipelineInfo',
    'CICDJob',
    'NestJSExtractor',
    'NestJSInfo',
    'NestJSModule',
    'NestJSGuard',
    'NestJSInterceptor',
    'NestJSPipe',
    'NestJSMiddleware',
    'NestJSGateway',
    'NestJSGatewayEvent',
    # Phase G-17: Go Language Extractors (NEW in v4.5)
    'GoTypeExtractor', 'GoStructInfo', 'GoInterfaceInfo', 'GoTypeAliasInfo', 'GoFieldInfo',
    'GoFunctionExtractor', 'GoFunctionInfo', 'GoMethodInfo', 'GoParameterInfo',
    'GoEnumExtractor', 'GoConstBlockInfo', 'GoConstValueInfo',
    'GoAPIExtractor', 'GoRouteInfo', 'GoGRPCServiceInfo', 'GoHandlerInfo',
    # Phase v4.6: Semantic Extractors
    'SemanticExtractor', 'SemanticResult', 'HookInfo', 'MiddlewareInfo',
    'GenericRouteInfo', 'PluginInfo', 'LifecycleInfo',
    # Phase v5.0: Universal Scanner Extractors
    'DiscoveryExtractor', 'ProjectDiscoveryResult', 'SubProjectInfo',
    'SpecFileInfo', 'ConfigTemplateInfo', 'LanguageBreakdown',
    'ProjectProfile',
    'OpenAPIExtractor', 'OpenAPIInfo', 'OpenAPIEndpoint',
    'OpenAPISecurityScheme', 'OpenAPIModel',
    'GraphQLSchemaExtractor', 'GraphQLSchemaInfo', 'GraphQLType',
    'GraphQLField', 'GraphQLOperation',
    'ConfigTemplateExtractor', 'ConfigTemplateResult', 'ConfigTemplate', 'ConfigVariable',
    'EnvInferenceExtractor', 'EnvInferenceResult', 'InferredEnvVar',
    'SecurityExtractor', 'SecurityResult', 'AuthMechanism', 'AuthzPattern', 'SecurityFlag',
    'DatabaseArchitectureExtractor', 'DatabaseArchitectureResult',
    'DatabaseInfo', 'DatabaseModel', 'MigrationInfo',
    'SubProjectExtractor', 'SubProjectResult', 'SubProjectAnalysis', 'SubProjectDependency',
    'GenericLanguageExtractor', 'GenericLanguageResult', 'GenericFileResult',
    'GenericFunction', 'GenericType', 'GenericImport',
    # Phase v4.16: HTML Language Extractors (NEW)
    'HTMLStructureExtractor', 'HTMLDocumentInfo', 'HTMLSectionInfo',
    'HTMLHeadingInfo', 'HTMLLandmarkInfo',
    'HTMLSemanticExtractor', 'HTMLSemanticElementInfo', 'HTMLMicrodataInfo',
    'HTMLFormExtractor', 'HTMLFormInfo', 'HTMLInputInfo', 'HTMLFieldsetInfo',
    'HTMLMetaExtractor', 'HTMLMetaInfo', 'HTMLLinkInfo',
    'HTMLOpenGraphInfo', 'HTMLJsonLdInfo',
    'HTMLAccessibilityExtractor', 'HTMLAriaInfo', 'HTMLA11yIssue',
    'HTMLTemplateExtractor', 'HTMLTemplateInfo', 'HTMLTemplateBlockInfo',
    'HTMLAssetExtractor', 'HTMLScriptInfo', 'HTMLStyleInfo', 'HTMLPreloadInfo',
    'HTMLComponentExtractor', 'HTMLCustomElementInfo', 'HTMLSlotInfo',
]
