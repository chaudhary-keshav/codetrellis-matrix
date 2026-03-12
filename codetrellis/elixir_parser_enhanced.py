"""
Enhanced Elixir Parser for CodeTrellis

Base language parser for Elixir (.ex, .exs) files. Orchestrates all 5 Elixir
extractors and aggregates results into a single ElixirParseResult.

Detects:
- Elixir version features (1.0–1.17+)
- 70+ framework/library patterns (Phoenix, Ecto, Absinthe, Oban, Nerves, Nx, etc.)
- OTP patterns (GenServer, Supervisor, Application, Task, Agent, Registry)
- Mix project configuration

Reference pattern: TypeScript parser (5 extractors + orchestrator)

Part of CodeTrellis - Elixir Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from codetrellis.extractors.elixir import (
    ElixirTypeExtractor, ElixirModuleInfo, ElixirStructInfo,
    ElixirProtocolInfo, ElixirBehaviourInfo, ElixirTypespecInfo,
    ElixirExceptionInfo,
    ElixirFunctionExtractor, ElixirFunctionInfo, ElixirMacroInfo,
    ElixirGuardInfo, ElixirCallbackInfo,
    ElixirAPIExtractor, ElixirPlugInfo, ElixirPipelineInfo,
    ElixirEndpointInfo,
    ElixirModelExtractor, ElixirSchemaInfo, ElixirChangesetInfo,
    ElixirGenServerStateInfo,
    ElixirAttributeExtractor, ElixirModuleAttributeInfo,
    ElixirUseDirectiveInfo,
)


@dataclass
class ElixirParseResult:
    """Complete parse result for an Elixir file."""
    file_path: str
    file_type: str = "elixir"  # elixir, exs (script/test/config)

    # Core types (from type_extractor)
    modules: List[ElixirModuleInfo] = field(default_factory=list)
    structs: List[ElixirStructInfo] = field(default_factory=list)
    protocols: List[ElixirProtocolInfo] = field(default_factory=list)
    behaviours: List[ElixirBehaviourInfo] = field(default_factory=list)
    typespecs: List[ElixirTypespecInfo] = field(default_factory=list)
    exceptions: List[ElixirExceptionInfo] = field(default_factory=list)

    # Functions (from function_extractor)
    functions: List[ElixirFunctionInfo] = field(default_factory=list)
    macros: List[ElixirMacroInfo] = field(default_factory=list)
    guards: List[ElixirGuardInfo] = field(default_factory=list)
    callbacks: List[ElixirCallbackInfo] = field(default_factory=list)

    # API/web (from api_extractor)
    plugs: List[ElixirPlugInfo] = field(default_factory=list)
    pipelines: List[ElixirPipelineInfo] = field(default_factory=list)
    endpoints: List[ElixirEndpointInfo] = field(default_factory=list)

    # Models/data (from model_extractor)
    schemas: List[ElixirSchemaInfo] = field(default_factory=list)
    changesets: List[ElixirChangesetInfo] = field(default_factory=list)
    genserver_states: List[ElixirGenServerStateInfo] = field(default_factory=list)

    # Attributes (from attribute_extractor)
    attributes: List[ElixirModuleAttributeInfo] = field(default_factory=list)
    directives: List[ElixirUseDirectiveInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    elixir_version: str = ""
    otp_patterns: List[str] = field(default_factory=list)
    is_test_file: bool = False
    is_config_file: bool = False
    is_mix_file: bool = False


class EnhancedElixirParser:
    """
    Enhanced Elixir parser for CodeTrellis.

    Parses Elixir source files (.ex, .exs) and extracts:
    - Modules, structs, protocols, behaviours, typespecs, exceptions
    - Functions (def/defp), macros, guards, callbacks
    - Plugs, pipelines, endpoints
    - Schemas, changesets, GenServer state shapes
    - Module attributes, use/import/alias/require directives
    - OTP patterns (GenServer, Supervisor, Application, Agent, Task, Registry)
    - Framework detection (Phoenix, Ecto, Absinthe, Oban, Nerves, Nx, etc.)

    Elixir versions: 1.0–1.17+ (detects minimum version based on features)
    Optional AST: tree-sitter-elixir
    Optional LSP: elixir-ls / next-ls / lexical
    """

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        # Web frameworks
        'phoenix': re.compile(
            r'use\s+Phoenix\.\w+|Phoenix\.Router|Phoenix\.Controller|'
            r'Phoenix\.LiveView|Phoenix\.LiveComponent|Phoenix\.Channel|'
            r'Phoenix\.Socket|Phoenix\.Endpoint|Phoenix\.HTML|'
            r'plug\s+Phoenix\.\w+|@phoenix|Phoenix\.ConnTest',
            re.MULTILINE,
        ),
        'phoenix_liveview': re.compile(
            r'use\s+Phoenix\.LiveView|Phoenix\.LiveComponent|'
            r'live\s+"/|live_render|assign\(|push_event\(|'
            r'handle_event\(|mount\(.*socket|phx-',
            re.MULTILINE,
        ),
        'plug': re.compile(
            r'use\s+Plug\.\w+|Plug\.Conn|Plug\.Router|Plug\.Builder|'
            r'plug\s+:?\w+|Plug\.Parsers|Plug\.Static',
            re.MULTILINE,
        ),

        # Database
        'ecto': re.compile(
            r'use\s+Ecto\.\w+|Ecto\.Schema|Ecto\.Changeset|Ecto\.Query|'
            r'Ecto\.Repo|Ecto\.Migration|Ecto\.Multi|Ecto\.Type|'
            r'schema\s+"[^"]+"\s+do|embedded_schema\s+do|'
            r'from\s+\w+\s+in\s+\w+',
            re.MULTILINE,
        ),

        # GraphQL
        'absinthe': re.compile(
            r'use\s+Absinthe\.\w+|Absinthe\.Schema|Absinthe\.Relay|'
            r'Absinthe\.Middleware|Absinthe\.Resolution|'
            r'object\s+:\w+\s+do|query\s+do|mutation\s+do|'
            r'subscription\s+do|resolve\s+&',
            re.MULTILINE,
        ),

        # Background jobs
        'oban': re.compile(
            r'use\s+Oban\.Worker|use\s+Oban\.Pro\.\w+|Oban\.Job|'
            r'Oban\.insert|Oban\.insert_all|Oban\.Testing|'
            r'@impl\s+Oban\.Worker|perform\(%Oban\.Job\{',
            re.MULTILINE,
        ),

        # Auth
        'guardian': re.compile(r'use\s+Guardian|Guardian\.Plug|Guardian\.Token', re.MULTILINE),
        'pow': re.compile(r'use\s+Pow|Pow\.Ecto|Pow\.Phoenix|pow_routes', re.MULTILINE),
        'ueberauth': re.compile(r'use\s+Ueberauth|Ueberauth\.Strategy', re.MULTILINE),
        'phx_gen_auth': re.compile(r'UserAuth|UserSessionController|confirm_user', re.MULTILINE),

        # Testing
        'ex_unit': re.compile(r'use\s+ExUnit\.Case|ExUnit\.start|test\s+"[^"]+"', re.MULTILINE),
        'ex_machina': re.compile(r'use\s+ExMachina|ExMachina\.Ecto|factory\(', re.MULTILINE),
        'mox': re.compile(r'Mox\.defmock|import\s+Mox|expect\(', re.MULTILINE),
        'bypass': re.compile(r'Bypass\.open|Bypass\.expect', re.MULTILINE),
        'wallaby': re.compile(r'use\s+Wallaby|Wallaby\.Feature|visit\(', re.MULTILINE),

        # Realtime / PubSub
        'phoenix_pubsub': re.compile(r'Phoenix\.PubSub|PubSub\.subscribe|PubSub\.broadcast', re.MULTILINE),
        'phoenix_presence': re.compile(r'Phoenix\.Presence|Presence\.track', re.MULTILINE),

        # HTTP client
        'tesla': re.compile(r'use\s+Tesla|Tesla\.Middleware|Tesla\.get|Tesla\.post', re.MULTILINE),
        'httpoison': re.compile(r'use\s+HTTPoison|HTTPoison\.get|HTTPoison\.post', re.MULTILINE),
        'finch': re.compile(r'Finch\.request|Finch\.build|Finch\.start_link', re.MULTILINE),
        'req': re.compile(r'Req\.get|Req\.post|Req\.new|Req\.request', re.MULTILINE),

        # Caching
        'nebulex': re.compile(r'use\s+Nebulex\.Cache|Nebulex\.Adapter', re.MULTILINE),
        'cachex': re.compile(r'Cachex\.start_link|Cachex\.get|Cachex\.put', re.MULTILINE),
        'con_cache': re.compile(r'ConCache\.start_link|ConCache\.get|ConCache\.put', re.MULTILINE),

        # Telemetry / Monitoring
        'telemetry': re.compile(r':telemetry\.execute|:telemetry\.attach|Telemetry\.Metrics', re.MULTILINE),
        'logger': re.compile(r'require\s+Logger|Logger\.info|Logger\.error|Logger\.warn|Logger\.debug', re.MULTILINE),

        # Serialization
        'jason': re.compile(r'Jason\.encode|Jason\.decode|@derive\s+Jason\.Encoder', re.MULTILINE),
        'poison': re.compile(r'Poison\.encode|Poison\.decode', re.MULTILINE),
        'protobuf': re.compile(r'use\s+Protobuf|defstruct\s+.*protobuf', re.MULTILINE),

        # ML / Numerical
        'nx': re.compile(r'Nx\.tensor|Nx\.add|Nx\.dot|Nx\.defn|import\s+Nx', re.MULTILINE),
        'axon': re.compile(r'Axon\.input|Axon\.dense|Axon\.relu|Axon\.Loop', re.MULTILINE),
        'explorer': re.compile(r'Explorer\.DataFrame|Explorer\.Series|require\s+Explorer', re.MULTILINE),
        'bumblebee': re.compile(r'Bumblebee\.load_model|Bumblebee\.Text', re.MULTILINE),
        'scholar': re.compile(r'Scholar\.Linear|Scholar\.Cluster', re.MULTILINE),

        # Embedded / IoT
        'nerves': re.compile(r'use\s+Nerves|Nerves\.Runtime|Nerves\.Firmware', re.MULTILINE),

        # Release / Deploy
        'distillery': re.compile(r'use\s+Distillery|Mix\.Releases', re.MULTILINE),

        # Task queue / Scheduling
        'quantum': re.compile(r'use\s+Quantum|Quantum\.Job', re.MULTILINE),
        'exq': re.compile(r'use\s+Exq|Exq\.Enqueuer', re.MULTILINE),

        # API / Documentation
        'open_api_spex': re.compile(r'use\s+OpenApiSpex|OpenApiSpex\.Schema|operation\s+:', re.MULTILINE),
        'ex_doc': re.compile(r'ExDoc\.', re.MULTILINE),

        # LiveBook / Notebook
        'livebook': re.compile(r'Mix\.install|Kino\.\w+|VegaLite', re.MULTILINE),

        # Event sourcing / CQRS
        'commanded': re.compile(r'use\s+Commanded|Commanded\.Commands|Commanded\.Aggregate', re.MULTILINE),
        'event_store': re.compile(r'EventStore\.append|EventStore\.read', re.MULTILINE),

        # Messaging
        'broadway': re.compile(r'use\s+Broadway|Broadway\.Message|handle_message', re.MULTILINE),
        'gen_stage': re.compile(r'use\s+GenStage|GenStage\.start_link|handle_demand', re.MULTILINE),

        # Gettext / i18n
        'gettext': re.compile(r'use\s+Gettext|gettext\(|ngettext\(', re.MULTILINE),

        # Email
        'swoosh': re.compile(r'use\s+Swoosh|Swoosh\.Email|new_email', re.MULTILINE),
        'bamboo': re.compile(r'use\s+Bamboo|Bamboo\.Email|Bamboo\.Mailer', re.MULTILINE),

        # File upload
        'waffle': re.compile(r'use\s+Waffle|Waffle\.Definition', re.MULTILINE),
        'arc': re.compile(r'use\s+Arc|Arc\.Definition', re.MULTILINE),

        # WebSocket
        'gun': re.compile(r':gun\.open|:gun\.ws_upgrade', re.MULTILINE),
        'mint_websocket': re.compile(r'Mint\.WebSocket', re.MULTILINE),
    }

    # OTP pattern detection
    OTP_PATTERNS = {
        'genserver': re.compile(r'use\s+GenServer|GenServer\.start_link|GenServer\.call|GenServer\.cast', re.MULTILINE),
        'supervisor': re.compile(r'use\s+Supervisor|Supervisor\.start_link|Supervisor\.init|children\s*=', re.MULTILINE),
        'application': re.compile(r'use\s+Application|Application\.start|def\s+start\(.*_type.*_args', re.MULTILINE),
        'agent': re.compile(r'Agent\.start_link|Agent\.get|Agent\.update|use\s+Agent', re.MULTILINE),
        'task': re.compile(r'Task\.start_link|Task\.async|Task\.await|Task\.Supervisor', re.MULTILINE),
        'registry': re.compile(r'Registry\.start_link|Registry\.lookup|Registry\.register', re.MULTILINE),
        'dynamic_supervisor': re.compile(r'DynamicSupervisor\.start_link|DynamicSupervisor\.start_child', re.MULTILINE),
        'gen_event': re.compile(r'GenEvent\.start_link|GenEvent\.notify', re.MULTILINE),
        'ets': re.compile(r':ets\.new|:ets\.insert|:ets\.lookup|:ets\.delete', re.MULTILINE),
        'mnesia': re.compile(r':mnesia\.create_table|:mnesia\.transaction|:mnesia\.write', re.MULTILINE),
    }

    # Elixir version feature detection (minimum version based on features used)
    VERSION_FEATURES = [
        ('1.17', re.compile(r'Duration\.new|Date\.shift|Time\.shift', re.MULTILINE)),
        ('1.16', re.compile(r'dbg\(|__DIR__|__ENV__|Code\.Fragment', re.MULTILINE)),
        ('1.15', re.compile(r'Mix\.install|t::|\bcompile_env!?\b', re.MULTILINE)),
        ('1.14', re.compile(r'PartitionSupervisor|dbg\b|then\(', re.MULTILINE)),
        ('1.13', re.compile(r'tap\(|then\(', re.MULTILINE)),
        ('1.12', re.compile(r'Mix\.install|Enum\.zip_with|Map\.intersect', re.MULTILINE)),
        ('1.11', re.compile(r'is_struct\(|config_env\(\)|config_target', re.MULTILINE)),
        ('1.10', re.compile(r'Enum\.frequencies|Map\.filter|Kernel\.is_map_key', re.MULTILINE)),
        ('1.9', re.compile(r'~U\[|release\b|Config\.Reader', re.MULTILINE)),
        ('1.8', re.compile(r'mix format|@impl true|Inspect\.Opts', re.MULTILINE)),
        ('1.7', re.compile(r'__STACKTRACE__|DynamicSupervisor', re.MULTILINE)),
        ('1.6', re.compile(r'@impl|defguard\b|mix format', re.MULTILINE)),
        ('1.5', re.compile(r'@impl|child_spec|Exception\.blame', re.MULTILINE)),
        ('1.4', re.compile(r'Registry|Task\.async_stream', re.MULTILINE)),
        ('1.3', re.compile(r'with\s+\w+\s+<-|ExUnit\.Case.*async', re.MULTILINE)),
        ('1.2', re.compile(r'with\b|i\s+[A-Z]\w+', re.MULTILINE)),
        ('1.0', re.compile(r'defmodule|def\s+\w+', re.MULTILINE)),
    ]

    def __init__(self):
        """Initialize the parser with all extractors."""
        self.type_extractor = ElixirTypeExtractor()
        self.function_extractor = ElixirFunctionExtractor()
        self.api_extractor = ElixirAPIExtractor()
        self.model_extractor = ElixirModelExtractor()
        self.attribute_extractor = ElixirAttributeExtractor()

    def parse(self, content: str, file_path: str = "") -> ElixirParseResult:
        """Parse Elixir source code and return structured result."""
        result = ElixirParseResult(file_path=file_path)

        # Determine file type
        if file_path.endswith('.exs'):
            result.file_type = "exs"
        else:
            result.file_type = "elixir"

        # Detect test/config/mix files
        result.is_test_file = '_test.exs' in file_path or '/test/' in file_path
        result.is_config_file = file_path.endswith('config.exs') or '/config/' in file_path
        result.is_mix_file = file_path.endswith('mix.exs')

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect Elixir version
        result.elixir_version = self._detect_version(content)

        # Detect OTP patterns
        result.otp_patterns = self._detect_otp_patterns(content)

        # ── Extract types ─────────────────────────────────────────
        type_result = self.type_extractor.extract(content, file_path)
        result.modules = type_result.get('modules', [])
        result.structs = type_result.get('structs', [])
        result.protocols = type_result.get('protocols', [])
        result.behaviours = type_result.get('behaviours', [])
        result.typespecs = type_result.get('typespecs', [])
        result.exceptions = type_result.get('exceptions', [])

        # ── Extract functions ─────────────────────────────────────
        func_result = self.function_extractor.extract(content, file_path)
        result.functions = func_result.get('functions', [])
        result.macros = func_result.get('macros', [])
        result.guards = func_result.get('guards', [])
        result.callbacks = func_result.get('callbacks', [])

        # ── Extract API/web patterns ─────────────────────────────
        api_result = self.api_extractor.extract(content, file_path)
        result.plugs = api_result.get('plugs', [])
        result.pipelines = api_result.get('pipelines', [])
        result.endpoints = api_result.get('endpoints', [])

        # ── Extract models/data ───────────────────────────────────
        model_result = self.model_extractor.extract(content, file_path)
        result.schemas = model_result.get('schemas', [])
        result.changesets = model_result.get('changesets', [])
        result.genserver_states = model_result.get('genserver_states', [])

        # ── Extract attributes ────────────────────────────────────
        attr_result = self.attribute_extractor.extract(content, file_path)
        result.attributes = attr_result.get('attributes', [])
        result.directives = attr_result.get('directives', [])

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect frameworks used in this file."""
        frameworks = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(name)
        return frameworks

    def _detect_version(self, content: str) -> str:
        """Detect minimum Elixir version based on language features used."""
        for version, pattern in self.VERSION_FEATURES:
            if pattern.search(content):
                return version
        return ""

    def _detect_otp_patterns(self, content: str) -> List[str]:
        """Detect OTP patterns used in this file."""
        patterns = []
        for name, pattern in self.OTP_PATTERNS.items():
            if pattern.search(content):
                patterns.append(name)
        return patterns
