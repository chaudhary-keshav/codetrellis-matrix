"""
CodeTrellis Business Domain Extractor
================================

Extracts high-level business domain context that helps AI understand:
- What the application DOES (business purpose)
- How data FLOWS through the system
- WHY certain architectural decisions were made
- Key domain entities and their relationships

This complements the technical matrix with semantic understanding.

Part of CodeTrellis v3.1 - Semantic Context Enrichment
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class DomainCategory(Enum):
    """Detected business domain categories"""
    TRADING = "Trading/Finance"
    ECOMMERCE = "E-Commerce"
    CRM = "Customer Relationship Management"
    HEALTHCARE = "Healthcare"
    EDUCATION = "Education/E-Learning"
    SOCIAL = "Social Media"
    PRODUCTIVITY = "Productivity/SaaS"
    IOT = "IoT/Device Management"
    LOGISTICS = "Logistics/Supply Chain"
    ANALYTICS = "Analytics/BI"
    CONTENT = "Content Management"
    GAMING = "Gaming"
    COMMUNICATION = "Communication/Messaging"
    AI_ML = "AI/ML Platform"
    DEVTOOLS = "Developer Tools"
    INFRASTRUCTURE = "Infrastructure/BaaS"
    MEDIA_PHOTO = "Media/Photo Management"
    WEB_SERVER = "Web Server/Proxy"
    WEB_FRAMEWORK = "Web Framework/Library"
    ERP_HRM = "Business Management (ERP/CRM/HRM)"
    BLOGGING = "Content/Blogging Platform"
    SCHEDULING = "Scheduling/Calendar"
    TASK_ORCHESTRATION = "Task Orchestration/Workflow Engine"
    VERSION_CONTROL = "Version Control/SCM"
    UNKNOWN = "General Application"


class DataFlowPattern(Enum):
    """Common data flow patterns"""
    REAL_TIME_STREAMING = "Real-time Streaming"
    REQUEST_RESPONSE = "Request-Response"
    EVENT_DRIVEN = "Event-Driven"
    POLLING = "Polling"
    CQRS = "Command Query Separation"
    SAGA = "Saga/Orchestration"
    PUB_SUB = "Publish-Subscribe"


@dataclass
class DomainEntity:
    """A key entity in the business domain"""
    name: str
    category: str  # e.g., "Core", "Supporting", "Reference"
    description: str = ""
    relationships: List[str] = field(default_factory=list)  # Related entity names
    interfaces: List[str] = field(default_factory=list)  # Related interfaces
    operations: List[str] = field(default_factory=list)  # CRUD + domain operations

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "relationships": self.relationships,
            "interfaces": self.interfaces,
            "operations": self.operations,
        }


@dataclass
class DataFlow:
    """A data flow path in the system"""
    name: str
    source: str
    destination: str
    pattern: DataFlowPattern
    events: List[str] = field(default_factory=list)
    data_types: List[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "source": self.source,
            "destination": self.destination,
            "pattern": self.pattern.value,
            "events": self.events,
            "dataTypes": self.data_types,
            "description": self.description,
        }


@dataclass
class ArchitecturalDecision:
    """A detected architectural decision"""
    title: str
    decision: str
    rationale: str = ""
    evidence: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "decision": self.decision,
            "rationale": self.rationale,
            "evidence": self.evidence,
            "alternatives": self.alternatives,
        }


@dataclass
class UserJourney:
    """A key user journey/workflow"""
    name: str
    steps: List[str]
    components_involved: List[str] = field(default_factory=list)
    entry_point: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "steps": self.steps,
            "componentsInvolved": self.components_involved,
            "entryPoint": self.entry_point,
        }


@dataclass
class BusinessDomainContext:
    """Complete business domain context for the project"""
    project_name: str
    domain_category: DomainCategory = DomainCategory.UNKNOWN
    domain_description: str = ""
    # Phase 1: Confidence scoring
    domain_confidence: float = 0.0
    domain_runner_up: Optional[str] = None  # "CRM (0.24)" format
    domain_runner_up_confidence: float = 0.0

    # Core domain knowledge
    entities: List[DomainEntity] = field(default_factory=list)
    domain_vocabulary: Dict[str, str] = field(default_factory=dict)  # Term -> Definition

    # Data flows
    data_flows: List[DataFlow] = field(default_factory=list)
    primary_data_pattern: DataFlowPattern = DataFlowPattern.REQUEST_RESPONSE

    # Architectural decisions
    decisions: List[ArchitecturalDecision] = field(default_factory=list)

    # User journeys
    user_journeys: List[UserJourney] = field(default_factory=list)

    # System boundaries
    external_systems: List[str] = field(default_factory=list)
    api_consumers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "projectName": self.project_name,
            "domainCategory": self.domain_category.value,
            "domainDescription": self.domain_description,
            "entities": [e.to_dict() for e in self.entities],
            "domainVocabulary": self.domain_vocabulary,
            "dataFlows": [f.to_dict() for f in self.data_flows],
            "primaryDataPattern": self.primary_data_pattern.value,
            "decisions": [d.to_dict() for d in self.decisions],
            "userJourneys": [j.to_dict() for j in self.user_journeys],
            "externalSystems": self.external_systems,
            "apiConsumers": self.api_consumers,
        }

    def to_codetrellis_format(self) -> str:
        """Convert to compact CodeTrellis format for prompt injection"""
        lines = []

        # Domain summary with confidence
        domain_line = f"domain:{self.domain_category.value}"
        if self.domain_confidence > 0:
            domain_line += f" (confidence={self.domain_confidence}"
            if self.domain_runner_up:
                domain_line += f", runner_up={self.domain_runner_up}"
            domain_line += ")"
        lines.append(domain_line)
        if self.domain_description:
            desc = self.domain_description[:150] + "..." if len(self.domain_description) > 150 else self.domain_description
            lines.append(f"purpose:{desc}")

        # Core entities
        if self.entities:
            core_entities = [e.name for e in self.entities if e.category == "Core"][:5]
            if core_entities:
                lines.append(f"core-entities:{','.join(core_entities)}")

        # Primary data flow
        lines.append(f"data-pattern:{self.primary_data_pattern.value}")

        # Key flows
        if self.data_flows:
            flow_summaries = [f"{f.source}→{f.destination}" for f in self.data_flows[:4]]
            lines.append(f"flows:{','.join(flow_summaries)}")

        # External systems
        if self.external_systems:
            lines.append(f"external:{','.join(self.external_systems[:5])}")

        return '\n'.join(lines)


class BusinessDomainExtractor:
    """
    Extracts business domain context from a project.

    Analyzes:
    - Interface names and structures for domain entities
    - Service names for domain operations
    - WebSocket/HTTP events for data flows
    - Route structures for user journeys
    - Comments and docs for domain vocabulary
    """

    # ── Domain indicators — Weighted tier system (Phase 1 systemic improvement) ──
    # Each domain has three tiers of indicator keywords:
    #   high   (weight=3): Very specific to this domain, low cross-domain overlap
    #   medium (weight=2): Moderately specific, some overlap with other domains
    #   low    (weight=1): Generic words that appear across many domains
    #
    # Inspired by Wappalyzer's confidence scoring with implies/excludes.
    DOMAIN_INDICATORS = {
        DomainCategory.TRADING: {
            "high": [
                "trade", "trading", "stock", "portfolio", "position", "ticker",
                "quote", "pnl", "broker", "hedge", "arbitrage", "forex", "crypto",
                "nifty", "bse", "nse", "intraday", "swing", "delivery", "stoploss",
                "backtest", "scalping", "vwap",
            ],
            "medium": [
                "market", "price", "profit", "loss", "execution",
                "margin", "target", "regime", "bull", "bear", "vix",
                "ema", "rsi", "macd", "atr", "momentum", "breakout",
            ],
            "low": [
                "signal", "risk",
            ],
        },
        DomainCategory.ECOMMERCE: {
            "high": [
                "checkout", "cart", "sku", "storefront", "ecommerce",
                "commerce", "marketplace", "wishlist", "coupon", "promo",
                "giftcard", "gift_card", "merchant", "seller", "buyer",
                "medusa", "medusajs", "saleor", "shopify", "woocommerce",
                "magento", "bigcommerce", "prestashop", "spree",
                "fulfillment", "pricing", "promotion", "sales_channel",
            ],
            "medium": [
                "product", "order", "payment", "shipping", "catalog",
                "inventory", "customer", "discount", "refund", "return",
                "variant", "warehouse", "invoice", "shop",
            ],
            "low": [],
        },
        DomainCategory.CRM: {
            "high": [
                "lead", "opportunity", "pipeline", "deal", "prospect",
                "funnel", "conversion", "engagement",
            ],
            "medium": [
                "contact", "account", "campaign", "customer", "sales",
            ],
            "low": [],
        },
        DomainCategory.HEALTHCARE: {
            "high": [
                "patient", "diagnosis", "prescription", "medical",
                "clinic", "hospital", "treatment", "ehr", "symptom",
                "condition",
            ],
            "medium": [
                "doctor", "appointment", "health",
            ],
            "low": [],
        },
        DomainCategory.EDUCATION: {
            "high": [
                "course", "lesson", "student", "teacher", "enrollment",
                "quiz", "assignment", "curriculum", "assessment",
            ],
            "medium": [
                "grade", "module", "learning", "progress",
            ],
            "low": [],
        },
        DomainCategory.ANALYTICS: {
            "high": [
                "dashboard", "kpi", "visualization", "analytics",
                "cohort", "segment", "forecast", "datawarehouse", "olap",
                "cube", "dimension", "tableau", "grafana", "prometheus",
                "datadog", "mixpanel", "amplitude", "posthog_analytics",
            ],
            "medium": [
                "metric", "insight", "funnel", "trend",
            ],
            "low": [],
        },
        DomainCategory.COMMUNICATION: {
            "high": [
                "chat", "inbox", "conversation", "thread",
                "mention", "reaction", "sms", "smtp", "imap",
                "slack", "discord", "matrix", "xmpp", "jabber",
                "gotify", "ntfy", "pushover",
            ],
            "medium": [
                "message", "websocket", "realtime",
            ],
            "low": [],
        },
        DomainCategory.AI_ML: {
            "high": [
                "inference", "embedding", "llm", "training",
                "transformer", "neural", "tensor", "epoch",
                "classification", "regression", "rag", "retrieval",
                "langchain", "openai", "huggingface", "ollama",
                "pytorch", "tensorflow", "qdrant", "pinecone",
                "weaviate", "chromadb", "faiss", "embedding_model",
                "perplexity", "generation", "nlp", "sentiment",
            ],
            "medium": [
                "vector", "fine", "tuning", "prompt", "completion",
                "prediction", "semantic", "similarity",
                "brain", "cognitive", "agent",
            ],
            "low": [],
        },
        DomainCategory.DEVTOOLS: {
            "high": [
                "extractor", "scanner", "parser", "compiler", "linter",
                "formatter", "analyzer", "generator", "bundler", "transpiler",
                "lint", "minif", "sourcemap", "ast", "syntax", "lexer",
                "tokenizer", "debugger", "profiler", "benchmark",
                "devtool", "devtools", "sdk", "toolchain", "tooling",
            ],
            "medium": [],
            "low": [],
        },
        DomainCategory.INFRASTRUCTURE: {
            "high": [
                "ratelimit", "superuser", "tenant", "multitenancy",
                "firewall", "certificate", "dns",
                "baas", "paas", "saas", "serverless",
                "registry", "artifact", "deploy", "provision",
                "infra", "cluster", "loadbalance",
                "pocketbase", "supabase", "firebase", "appwrite",
            ],
            "medium": [
                "gateway",
            ],
            "low": [],
        },
        DomainCategory.MEDIA_PHOTO: {
            "high": [
                "photo", "album", "gallery", "thumbnail", "camera",
                "lens", "exif", "portrait", "picture", "slideshow",
                "originals", "sidecar", "webdav", "classify", "nsfw",
                "jpeg", "heif", "photoprism", "immich", "librephotos",
            ],
            "medium": [],
            "low": [],
        },
        DomainCategory.WEB_SERVER: {
            "high": [
                "reverse", "proxy", "loadbalance", "load_balancer",
                "upstream", "vhost", "virtualhost", "listen", "binding",
                "acme", "letsencrypt", "certmagic", "caddyfile", "caddy",
                "nginx", "apache", "traefik", "envoy", "http2", "http3",
                "quic", "webserver",
            ],
            "medium": [],
            "low": [],
        },
        DomainCategory.WEB_FRAMEWORK: {
            "high": [
                "framework", "fastapi", "flask", "django", "express",
                "starlette", "openapi", "swagger", "asgi", "wsgi",
                "uvicorn",
            ],
            "medium": [
                "middleware", "router", "route", "endpoint",
                "request", "response", "handler", "decorator",
                "dependency", "injection", "serializer", "deserializer",
            ],
            "low": [],
        },
        DomainCategory.ERP_HRM: {
            "high": [
                "employee", "payroll", "salary", "timesheet", "attendance",
                "leave", "department", "organization", "expense",
                "accounting", "billing", "recruitment", "applicant",
                "onboarding", "performance", "appraisal", "benefits",
                "erp", "hrm", "ats", "hris",
            ],
            "medium": [
                "invoice", "vendor", "purchase", "supply",
                "inventory", "warehouse",
            ],
            "low": [
                "crm",
            ],
        },
        DomainCategory.BLOGGING: {
            "high": [
                "blog", "article", "author", "publish", "draft",
                "slug", "archive", "feed", "rss", "atom",
                "conduit", "realworld", "blogging",
            ],
            "medium": [
                "post", "comment", "content", "editor", "category",
            ],
            "low": [],
        },
        DomainCategory.SCHEDULING: {
            "high": [
                "calendar", "booking", "appointment", "schedule",
                "scheduling", "availability", "timeslot", "slot",
                "event_type", "eventtype", "reschedule", "recurring",
                "attendee", "invitee", "calendly", "calcom", "cal.com",
                "ical", "icalendar", "caldav", "webcal", "recurrence",
            ],
            "medium": [
                "timezone", "cron",
            ],
            "low": [],
        },
        DomainCategory.TASK_ORCHESTRATION: {
            "high": [
                "workflow", "orchestrat", "taskqueue", "task_queue",
                "durable", "step_function", "stepfunction", "dag",
                "celery", "bullmq", "sidekiq", "temporal", "hatchet",
                "airflow", "prefect", "dagster", "conductor",
                "dispatcher", "fanout", "idempoten", "deadletter",
                "backoff",
            ],
            "medium": [
                "worker", "retry",
            ],
            "low": [],
        },
        DomainCategory.PRODUCTIVITY: {
            "high": [
                "issue", "sprint", "kanban", "backlog", "milestone",
                "epic", "board", "assignee", "cycle", "roadmap",
                "agile", "scrum", "jira", "linear", "trello", "asana",
                "plane", "notion", "project_management", "taskboard",
                "storypoint", "burndown", "velocity",
            ],
            "medium": [
                "priority", "label", "estimate", "module",
            ],
            "low": [],
        },
        DomainCategory.CONTENT: {
            "high": [
                "note", "memo", "bookmark", "snippet", "wiki",
                "knowledge", "notebook", "journal", "annotation",
                "highlight", "obsidian", "logseq", "joplin", "memos",
                "tiddlywiki", "zettelkasten", "pkm",
                "headless", "strapi", "contentful", "sanity", "cms",
                "content_type", "content_manager", "content_builder",
                "i18n", "localization",
            ],
            "medium": [
                "archive", "markdown", "content", "plugin",
            ],
            "low": [],
        },
        DomainCategory.VERSION_CONTROL: {
            "high": [
                "gitea", "gitlab", "github", "gogs", "bitbucket",
                "repository", "commit", "branch", "merge", "pullrequest",
                "pull_request", "clone", "fetch", "rebase", "cherry",
                "forgejo", "sourcehut", "gerrit", "phabricator",
                "diff", "blame", "stash", "worktree", "submodule",
                "self-hosted", "hosted",
            ],
            "medium": [
                "push", "hook", "webhook", "fork", "issue",
                "release", "milestone", "review",
            ],
            "low": [],
        },
    }

    # Entity category patterns
    CORE_ENTITY_PATTERNS = [
        r'(Trade|Order|Signal|Position|Portfolio)',  # Trading
        r'(Product|Order|Cart|Customer)',  # E-commerce
        r'(User|Account|Profile)',  # Generic
    ]

    # Operation patterns from method/function names
    OPERATION_PATTERNS = {
        "create": ["create", "add", "new", "insert", "register", "submit"],
        "read": ["get", "fetch", "load", "find", "search", "list", "query"],
        "update": ["update", "edit", "modify", "patch", "change", "set"],
        "delete": ["delete", "remove", "cancel", "clear", "revoke"],
        "execute": ["execute", "run", "process", "trigger", "invoke", "apply"],
        "validate": ["validate", "verify", "check", "ensure", "confirm"],
        "transform": ["transform", "convert", "map", "parse", "format"],
    }

    def __init__(self):
        self._project_root: Optional[Path] = None
        self._interfaces: List[Dict] = []
        self._services: List[Dict] = []
        self._stores: List[Dict] = []
        self._websocket_events: List[Dict] = []
        self._http_apis: List[Dict] = []
        self._routes: List[Dict] = []
        self._components: List[Dict] = []
        # Phase 1: confidence scoring metadata
        self._domain_confidence: float = 0.0
        self._domain_runner_up: Optional[Tuple[DomainCategory, float]] = None

    def extract(
        self,
        project_path: str,
        interfaces: List[Dict] = None,
        services: List[Dict] = None,
        stores: List[Dict] = None,
        websocket_events: List[Dict] = None,
        http_apis: List[Dict] = None,
        routes: List[Dict] = None,
        components: List[Dict] = None,
        discovery_result=None,
    ) -> BusinessDomainContext:
        """
        Extract business domain context from project data.

        Args:
            project_path: Path to project root
            interfaces: Extracted interfaces from InterfaceExtractor
            services: Extracted services from ServiceExtractor
            stores: Extracted stores from StoreExtractor
            websocket_events: Extracted WS events from WebSocketExtractor
            http_apis: Extracted HTTP APIs from HttpApiExtractor
            routes: Extracted routes from RouteExtractor
            components: Extracted components

        Returns:
            BusinessDomainContext with inferred domain knowledge
        """
        self._project_root = Path(project_path)
        self._interfaces = interfaces or []
        self._services = services or []
        self._stores = stores or []
        self._websocket_events = websocket_events or []
        self._http_apis = http_apis or []
        self._routes = routes or []
        self._components = components or []
        self._discovery_result = discovery_result  # v5.0: from DiscoveryExtractor

        context = BusinessDomainContext(project_name=self._project_root.name)

        # 1. Detect domain category
        context.domain_category = self._detect_domain_category()
        context.domain_description = self._generate_domain_description(context.domain_category)

        # Phase 1: Populate confidence + runner-up from detection metadata
        context.domain_confidence = self._domain_confidence
        if self._domain_runner_up:
            ru_domain, ru_conf = self._domain_runner_up
            context.domain_runner_up = f"{ru_domain.value}:{ru_conf}"
            context.domain_runner_up_confidence = ru_conf

        # 2. Extract domain entities from interfaces
        context.entities = self._extract_entities()

        # 3. Build domain vocabulary
        context.domain_vocabulary = self._build_vocabulary(context.domain_category)

        # 4. Analyze data flows
        context.data_flows = self._extract_data_flows()
        context.primary_data_pattern = self._detect_primary_pattern()

        # 5. Infer architectural decisions
        context.decisions = self._infer_decisions()

        # 6. Extract user journeys from routes
        context.user_journeys = self._extract_user_journeys()

        # 7. Identify external systems
        context.external_systems = self._identify_external_systems()

        return context

    def _detect_domain_category(self) -> DomainCategory:
        """
        Detect the primary business domain from code artifacts.
        Phase A (WS-5 / G-12): Enhanced to also scan Python file names,
        directory names, and README content for domain signals. Previously
        only used TypeScript interface/service/store/component names which
        yielded ~20% accuracy on Python-heavy or mixed projects.

        Phase E fix: Source-weighted scoring to prevent data/fixture files
        from inflating scores for wrong domains. Code artifact names get 3x
        weight, README words get 1x weight. Also skips known data directories
        like bpl/practices, tests/fixtures, and data/ from name collection.
        """
        domain_scores: Dict[DomainCategory, int] = defaultdict(int)

        # Phase E: Separate name pools with different weights
        code_names = set()    # From source code artifacts: weight 3x
        fs_names = set()      # From file/directory names: weight 2x
        readme_names = set()  # From README content: weight 1x
        pkg_json_names = set()  # From package.json/README title: weight 4x

        # Directories to skip during file system scanning (Phase E)
        FS_IGNORE_SEGMENTS = {
            'tests', 'test', '__tests__', 'fixtures', '__fixtures__',
            'node_modules', 'dist', 'build', '.git', '__pycache__',
            '.pytest_cache', '.venv', 'venv', 'env', 'site-packages',
            'coverage', '.tox', '.mypy_cache', '.ruff_cache', 'htmlcov',
            'practices', 'bpl', 'data', 'docs', '.codetrellis', '.egg-info',
            'codetrellis.egg-info', 'best_practices',
        }

        # From interfaces (code artifacts)
        for iface in self._interfaces:
            name = iface.get("name", "")
            code_names.add(name.lower())
            for prop in iface.get("properties", []):
                code_names.add(prop.get("name", "").lower())

        # From services (code artifacts)
        for svc in self._services:
            code_names.add(svc.get("name", "").lower())
            for method in svc.get("methods", []):
                if isinstance(method, str):
                    code_names.add(method.lower())
                elif isinstance(method, dict):
                    code_names.add(method.get("name", "").lower())

        # From stores (code artifacts)
        for store in self._stores:
            code_names.add(store.get("name", "").lower())
            for state_key in store.get("state", []):
                if isinstance(state_key, str):
                    code_names.add(state_key.lower())

        # From components (code artifacts)
        for comp in self._components:
            code_names.add(comp.get("name", "").lower())

        # Phase A (WS-5 / G-12): Scan file system for additional domain signals
        if self._project_root and self._project_root.is_dir():
            # Scan directory names (1 level deep under key dirs)
            # Also scan the main package directory (e.g., saleor/ in a project named saleor)
            scan_dirs = [self._project_root, self._project_root / 'src',
                         self._project_root / 'services',
                         self._project_root / 'ai',
                         self._project_root / 'apps',
                         self._project_root / 'packages',
                         self._project_root / 'internal',
                         self._project_root / 'pkg',
                         self._project_root / 'cmd']
            # Auto-detect main package dirs: directories with __init__.py or go files
            try:
                for item in self._project_root.iterdir():
                    if (item.is_dir() and not item.name.startswith('.')
                            and item.name.lower() not in FS_IGNORE_SEGMENTS
                            and item not in scan_dirs):
                        # Check if it's a Python package or Go/TS source dir
                        has_init = (item / '__init__.py').exists()
                        has_go = any(item.glob('*.go'))
                        has_ts = any(item.glob('*.ts'))
                        if has_init or has_go or has_ts:
                            scan_dirs.append(item)
            except PermissionError:
                pass

            for scan_dir in scan_dirs:
                if scan_dir.is_dir():
                    try:
                        for item in scan_dir.iterdir():
                            if item.is_dir() and not item.name.startswith('.'):
                                # Phase E: Skip ignored directories
                                if item.name.lower() in FS_IGNORE_SEGMENTS:
                                    continue
                                parts = re.split(r'[-_]', item.name.lower())
                                fs_names.update(parts)
                                fs_names.add(item.name.lower())
                    except PermissionError:
                        pass

            # Scan Python file names (top-level and src/)
            py_scan_dirs = [self._project_root, self._project_root / 'src']
            for scan_dir in py_scan_dirs:
                if scan_dir.is_dir():
                    for py_file in scan_dir.glob('*.py'):
                        stem = py_file.stem.lower()
                        parts = re.split(r'[-_]', stem)
                        fs_names.update(parts)
                        fs_names.add(stem)

            # Phase E: Also scan Python files recursively in codetrellis/ or src/
            # subdirectories (skipping ignored dirs) to pick up extractor,
            # scanner, parser names that indicate DEVTOOLS
            for pkg_dir in [self._project_root / 'codetrellis',
                            self._project_root / 'src',
                            self._project_root / self._project_root.name]:
                if pkg_dir.is_dir():
                    for py_file in pkg_dir.rglob('*.py'):
                        # Skip files inside ignored directories
                        skip = False
                        for part in py_file.relative_to(self._project_root).parts:
                            if part.lower() in FS_IGNORE_SEGMENTS:
                                skip = True
                                break
                        if skip:
                            continue
                        stem = py_file.stem.lower()
                        parts = re.split(r'[-_]', stem)
                        fs_names.update(parts)

            # Scan README for domain keywords (fast first-paragraph scan)
            for readme_name in ['README.md', 'readme.md', 'README.rst']:
                readme_path = self._project_root / readme_name
                if readme_path.exists():
                    try:
                        raw_content = readme_path.read_text(encoding='utf-8')[:2000]
                        # Strip HTML tags and markdown image/link syntax to avoid
                        # badge URLs polluting domain signals (e.g. "goreportcard",
                        # "shields.io" would otherwise produce false matches)
                        content = re.sub(r'<[^>]+>', ' ', raw_content).lower()
                        content = re.sub(r'!\[.*?\]\(.*?\)', ' ', content)
                        content = re.sub(r'\[.*?\]\(.*?\)', ' ', content)
                        words = re.findall(r'\b[a-z]{4,}\b', content)
                        readme_names.update(words[:100])
                        # GAP-6: Boost README first paragraph words with extra weight
                        # The project tagline (text before first ## heading) is the
                        # strongest natural-language domain signal
                        first_section = content.split('## ')[0] if '## ' in content else content[:500]
                        first_words = set(re.findall(r'\b[a-z]{4,}\b', first_section))
                        # Filter out project name words — they appear in every README
                        # but are not domain signals (e.g. "server" in "gotify/server")
                        proj_name_parts = set(re.split(r'[-_/\s]', self._project_root.name.lower()))
                        first_words -= proj_name_parts
                        # Add first-section words to pkg_json_names pool (4x weight)
                        # to compete with code artifact signals
                        pkg_json_names.update(first_words)
                    except Exception:
                        pass
                    break

            # GAP-16: Scan package.json description field for domain signals
            # The "description" field is often the strongest single-line domain
            # signal (e.g. "AI-Powered Photos App"). Weight 4x (higher than README).
            for pkg_path in [
                self._project_root / 'package.json',
                self._project_root / 'frontend' / 'package.json',
                self._project_root / 'ui' / 'package.json',
                self._project_root / 'web' / 'package.json',
                self._project_root / 'client' / 'package.json',
            ]:
                if pkg_path.exists():
                    try:
                        import json
                        pkg_data = json.loads(pkg_path.read_text(encoding='utf-8'))
                        desc = pkg_data.get('description', '')
                        if desc:
                            desc_words = re.findall(r'\b[a-z]{3,}\b', desc.lower())
                            pkg_json_names.update(desc_words)
                        # Also check "keywords" array
                        keywords = pkg_data.get('keywords', [])
                        for kw in keywords:
                            if isinstance(kw, str) and len(kw) >= 3:
                                pkg_json_names.add(kw.lower())
                    except Exception:
                        pass

            # GAP-C2: Also parse pyproject.toml [project] description for Python projects
            pyproject_path = self._project_root / 'pyproject.toml'
            if pyproject_path.exists():
                try:
                    content = pyproject_path.read_text(encoding='utf-8')
                    # Simple TOML parsing for description field
                    desc_match = re.search(r'^description\s*=\s*["\'](.+?)["\']', content, re.MULTILINE)
                    if desc_match:
                        desc_words = re.findall(r'\b[a-z]{3,}\b', desc_match.group(1).lower())
                        pkg_json_names.update(desc_words)
                    # Parse classifiers for domain signals
                    for classifier_match in re.finditer(r'"Topic :: (.+?)"', content):
                        topic_words = re.findall(r'\b[a-z]{3,}\b', classifier_match.group(1).lower())
                        pkg_json_names.update(topic_words)
                    # Parse keywords
                    kw_match = re.search(r'keywords\s*=\s*\[([^\]]+)\]', content)
                    if kw_match:
                        for kw in re.findall(r'["\']([^"\']+)["\']', kw_match.group(1)):
                            if len(kw) >= 3:
                                pkg_json_names.add(kw.lower())
                except Exception:
                    pass

        # Discard empty/short noise from all pools
        for pool in (code_names, fs_names, readme_names, pkg_json_names):
            pool.discard('')
            pool -= {n for n in pool if len(n) < 3}

        # v5.0: Inject discovery_result signals (readme_summary + package_description)
        # These are strong domain signals already extracted by DiscoveryExtractor
        if self._discovery_result:
            dr = self._discovery_result
            # readme_summary → pkg_json_names pool (4x weight)
            if hasattr(dr, 'readme_summary') and dr.readme_summary:
                words = re.findall(r'\b[a-z]{4,}\b', dr.readme_summary.lower())
                pkg_json_names.update(words)
            # package_description → pkg_json_names pool (4x weight)
            if hasattr(dr, 'package_description') and dr.package_description:
                words = re.findall(r'\b[a-z]{4,}\b', dr.package_description.lower())
                pkg_json_names.update(words)

        # Phase 1 (systemic): Weighted tier scoring across all pools
        # Each indicator word has a tier weight (high=3, medium=2, low=1)
        # and each pool has a source weight (pkg_json=4, code=3, fs=2, readme=1).
        # Final score = sum(tier_weight * source_weight) for all matches.
        TIER_WEIGHTS = {"high": 3, "medium": 2, "low": 1}
        SOURCE_WEIGHTS = [
            (code_names, 3),     # Code artifacts
            (fs_names, 2),       # File system names
            (readme_names, 1),   # README words
            (pkg_json_names, 4), # package.json description/keywords
        ]

        # Pre-compute max possible score per domain for confidence normalization
        max_possible: Dict[DomainCategory, int] = {}
        for domain, tiers in self.DOMAIN_INDICATORS.items():
            total_indicators = sum(len(tiers.get(t, [])) for t in ("high", "medium", "low"))
            # Max source weight (4) * max tier weight (3) * number of indicators
            max_possible[domain] = total_indicators * 4 * 3 if total_indicators > 0 else 1

        for domain, tiers in self.DOMAIN_INDICATORS.items():
            for tier_name, tier_weight in TIER_WEIGHTS.items():
                indicators = tiers.get(tier_name, [])
                for indicator in indicators:
                    for pool, source_weight in SOURCE_WEIGHTS:
                        for name in pool:
                            # R4 fix: Use word-boundary matching for short indicators
                            # to prevent false positives (e.g., "ema" inside "schema",
                            # "bse" inside "ctBseSessionContextValue", "nse" inside "license")
                            if len(indicator) <= 4:
                                # Short indicators: require exact match or word boundary
                                if name == indicator or re.search(r'(?:^|[-_\s])' + re.escape(indicator) + r'(?:$|[-_\s])', name):
                                    domain_scores[domain] += tier_weight * source_weight
                            else:
                                # Longer indicators: substring match is acceptable
                                if indicator in name:
                                    domain_scores[domain] += tier_weight * source_weight

        # Return highest scoring domain with confidence threshold
        if domain_scores:
            sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
            best_domain, best_score = sorted_domains[0]
            # Compute confidence as proportion of max possible for this domain
            confidence = best_score / max_possible.get(best_domain, 1)
            # Require at least 3 weighted indicator hits to avoid false positives
            if best_score >= 3:
                # Store confidence + runner-up for output enrichment
                self._domain_confidence = round(min(confidence, 1.0), 2)
                if len(sorted_domains) > 1:
                    runner_up_domain, runner_up_score = sorted_domains[1]
                    runner_up_conf = round(runner_up_score / max_possible.get(runner_up_domain, 1), 2)
                    self._domain_runner_up = (runner_up_domain, min(runner_up_conf, 1.0))
                else:
                    self._domain_runner_up = None
                return best_domain
        self._domain_confidence = 0.0
        self._domain_runner_up = None
        return DomainCategory.UNKNOWN

    def _generate_domain_description(self, category: DomainCategory) -> str:
        """Generate a description based on detected domain"""
        descriptions = {
            DomainCategory.TRADING: (
                "A trading/financial application that handles market data, "
                "trade execution, portfolio management, and risk analysis. "
                "Likely supports real-time price feeds, order management, "
                "and automated trading strategies."
            ),
            DomainCategory.ECOMMERCE: (
                "An e-commerce application managing product catalogs, "
                "shopping carts, checkout flows, and order fulfillment. "
                "Handles customer accounts, payments, and inventory."
            ),
            DomainCategory.CRM: (
                "A customer relationship management system tracking leads, "
                "contacts, sales pipelines, and customer interactions. "
                "Supports sales workflows and engagement tracking."
            ),
            DomainCategory.HEALTHCARE: (
                "A healthcare application managing patient records, "
                "appointments, medical histories, and clinical workflows. "
                "Handles sensitive medical data with compliance requirements."
            ),
            DomainCategory.ANALYTICS: (
                "An analytics/BI application providing dashboards, reports, "
                "and data visualizations. Tracks KPIs, metrics, and trends "
                "to support data-driven decisions."
            ),
            DomainCategory.UNKNOWN: (
                "A general-purpose application. Domain specifics should be "
                "inferred from the interface and service structures."
            ),
            DomainCategory.AI_ML: (
                "An AI/ML platform handling model inference, embeddings, "
                "LLM serving, RAG pipelines, and/or ML model training. "
                "May include vector stores, prompt engineering, and multi-tenant "
                "model management."
            ),
            DomainCategory.DEVTOOLS: (
                "A developer tools application for code analysis, project scanning, "
                "or build/development tooling. Provides utilities for development "
                "workflow automation and code intelligence."
            ),
            DomainCategory.INFRASTRUCTURE: (
                "A backend-as-a-service or infrastructure platform providing API "
                "management, authentication, data collections, real-time subscriptions, "
                "file storage, webhooks, and admin interfaces. Acts as a self-hosted "
                "backend framework with extensible hooks and middleware."
            ),
            DomainCategory.MEDIA_PHOTO: (
                "A media/photo management application handling photo libraries, "
                "albums, image indexing, facial recognition, and AI-powered "
                "classification. Supports RAW conversion, metadata extraction, "
                "WebDAV access, and sharing. May include video management."
            ),
            DomainCategory.WEB_SERVER: (
                "A web server, reverse proxy, or load balancer handling HTTP/HTTPS "
                "traffic routing, TLS termination, automatic certificate management "
                "(ACME/Let's Encrypt), and virtual hosting. May support HTTP/2, "
                "HTTP/3/QUIC, and a modular middleware/handler architecture."
            ),
            DomainCategory.WEB_FRAMEWORK: (
                "A web framework or library providing HTTP routing, middleware, "
                "request/response handling, and API endpoint definition. Designed "
                "for building web applications and APIs, with features like "
                "dependency injection, serialization, and OpenAPI integration."
            ),
            DomainCategory.ERP_HRM: (
                "A business management platform encompassing ERP, CRM, and/or HRM "
                "capabilities. Handles employee management, payroll, invoicing, "
                "expense tracking, time management, recruitment, and organizational "
                "structure. Supports multi-tenant enterprise workflows."
            ),
            DomainCategory.BLOGGING: (
                "A content/blogging platform for publishing articles, managing "
                "comments, user profiles, and content feeds. Supports features "
                "like tagging, favoriting, following authors, and content discovery."
            ),
            DomainCategory.SCHEDULING: (
                "A scheduling and calendar management platform handling bookings, "
                "appointments, availability, time slots, and event types. Supports "
                "calendar integrations, timezone management, recurring events, "
                "and attendee coordination."
            ),
            DomainCategory.TASK_ORCHESTRATION: (
                "A task orchestration and workflow engine for running background "
                "tasks, durable workflows, job queues, and distributed work. "
                "Provides task scheduling, retry logic, observability, and "
                "multi-language SDK support."
            ),
            DomainCategory.PRODUCTIVITY: (
                "A productivity and project management application for tracking "
                "issues, sprints, milestones, and project roadmaps. Supports "
                "Kanban boards, backlogs, team collaboration, and agile/scrum "
                "workflows."
            ),
            DomainCategory.CONTENT: (
                "A content management and note-taking application for organizing "
                "notes, memos, bookmarks, and knowledge. Supports tagging, search, "
                "archiving, and markdown-based editing."
            ),
            DomainCategory.VERSION_CONTROL: (
                "A version control and source code management platform providing "
                "Git repository hosting, pull requests, code review, issue tracking, "
                "CI/CD integration, and collaboration features. Supports self-hosted "
                "deployment with web UI and API access."
            ),
        }
        return descriptions.get(category, descriptions[DomainCategory.UNKNOWN])

    def _extract_entities(self) -> List[DomainEntity]:
        """Extract domain entities from interfaces"""
        entities = []
        entity_names = set()

        # Find core entities from interfaces
        for iface in self._interfaces:
            name = iface.get("name", "")
            if not name:
                continue

            # Skip utility/helper interfaces
            if any(skip in name.lower() for skip in ["config", "options", "params", "state", "props"]):
                continue

            # Determine category
            category = "Supporting"
            name_lower = name.lower()

            # Core entities are main domain objects
            if any(core in name_lower for core in [
                "trade", "order", "position", "signal", "portfolio",  # Trading
                "product", "cart", "customer",  # E-commerce
                "user", "account", "session",  # Generic
            ]):
                category = "Core"
            elif any(ref in name_lower for ref in ["status", "type", "config", "settings"]):
                category = "Reference"

            # Extract relationships from property types
            relationships = []
            operations = []
            for prop in iface.get("properties", []):
                prop_type = prop.get("type", "")
                # If type references another interface
                for other_iface in self._interfaces:
                    other_name = other_iface.get("name", "")
                    if other_name and other_name in prop_type and other_name != name:
                        relationships.append(other_name)

            entity = DomainEntity(
                name=name,
                category=category,
                relationships=list(set(relationships)),
                interfaces=[name],
                operations=operations,
            )
            entities.append(entity)
            entity_names.add(name)

        # Sort: Core first, then by name
        category_order = {"Core": 0, "Supporting": 1, "Reference": 2}
        entities.sort(key=lambda e: (category_order.get(e.category, 99), e.name))

        return entities[:30]  # Limit to top 30

    def _build_vocabulary(self, category: DomainCategory) -> Dict[str, str]:
        """Build domain-specific vocabulary"""
        # Base vocabulary per domain
        vocabularies = {
            DomainCategory.TRADING: {
                "PnL": "Profit and Loss - the difference between gains and losses",
                "Position": "An open trade - a holding of a security",
                "Signal": "A trading recommendation (BUY/SELL/HOLD)",
                "StopLoss": "Price level to exit a losing trade automatically",
                "Regime": "Market condition (Bull/Bear/Sideways)",
                "Intraday": "Same-day trading, positions closed by market end",
                "Swing": "Multi-day trading strategy",
                "VWAP": "Volume Weighted Average Price",
                "ATR": "Average True Range - volatility indicator",
                "RSI": "Relative Strength Index - momentum indicator",
            },
            DomainCategory.ECOMMERCE: {
                "SKU": "Stock Keeping Unit - unique product identifier",
                "Cart": "Collection of items selected for purchase",
                "Checkout": "Process of completing a purchase",
                "Inventory": "Stock levels and availability",
            },
        }

        return vocabularies.get(category, {})

    def _extract_data_flows(self) -> List[DataFlow]:
        """Extract data flow patterns from events and APIs"""
        flows = []

        # WebSocket flows (real-time)
        ws_in_events = []
        ws_out_events = []
        for ws in self._websocket_events:
            for event in ws.get("events", []):
                event_name = event.get("name", "")
                if event.get("direction") == "in" or event.get("type") == "subscribe":
                    ws_in_events.append(event_name)
                else:
                    ws_out_events.append(event_name)

        if ws_in_events:
            flows.append(DataFlow(
                name="Real-time Updates",
                source="Backend/WebSocket Server",
                destination="Frontend State",
                pattern=DataFlowPattern.REAL_TIME_STREAMING,
                events=ws_in_events[:10],
                description="Server pushes real-time updates to client via WebSocket",
            ))

        # HTTP API flows
        http_methods = {"GET": [], "POST": [], "PUT": [], "DELETE": []}
        for api in self._http_apis:
            for endpoint in api.get("endpoints", []):
                method = endpoint.get("method", "GET")
                path = endpoint.get("path", "")
                if method in http_methods:
                    http_methods[method].append(path)

        if http_methods["GET"]:
            flows.append(DataFlow(
                name="Data Fetching",
                source="Frontend",
                destination="Backend API",
                pattern=DataFlowPattern.REQUEST_RESPONSE,
                events=http_methods["GET"][:5],
                description="Client requests data from REST API endpoints",
            ))

        if http_methods["POST"]:
            flows.append(DataFlow(
                name="Data Submission",
                source="Frontend Forms",
                destination="Backend API",
                pattern=DataFlowPattern.REQUEST_RESPONSE,
                events=http_methods["POST"][:5],
                description="Client submits data through POST requests",
            ))

        return flows

    def _detect_primary_pattern(self) -> DataFlowPattern:
        """Detect the primary data flow pattern"""
        # If we have WebSocket events, likely real-time
        total_ws_events = sum(
            len(ws.get("events", []))
            for ws in self._websocket_events
        )
        if total_ws_events > 10:
            return DataFlowPattern.REAL_TIME_STREAMING

        # If we have stores with computed properties, likely event-driven
        if self._stores:
            return DataFlowPattern.EVENT_DRIVEN

        return DataFlowPattern.REQUEST_RESPONSE

    def _infer_decisions(self) -> List[ArchitecturalDecision]:
        """Infer architectural decisions from code patterns"""
        decisions = []

        # Check for signal stores
        if self._stores:
            store_names = [s.get("name", "") for s in self._stores]
            decisions.append(ArchitecturalDecision(
                title="State Management",
                decision="NgRx Signal Store for reactive state management",
                rationale="Provides fine-grained reactivity, better performance with OnPush, and cleaner signal-based APIs",
                evidence=store_names[:5],
                alternatives=["NgRx Store (classic)", "Akita", "Component state", "Services with BehaviorSubject"],
            ))

        # Check for WebSocket usage
        if self._websocket_events:
            decisions.append(ArchitecturalDecision(
                title="Real-time Communication",
                decision="WebSocket for real-time data streaming",
                rationale="Enables server-push for live updates without polling, critical for real-time applications",
                evidence=["WebSocket events detected in services"],
                alternatives=["Server-Sent Events", "Long Polling", "GraphQL Subscriptions"],
            ))

        # Check for OnPush components
        onpush_count = sum(
            1 for c in self._components
            if c.get("changeDetection") == "OnPush"
        )
        if onpush_count > 5:
            decisions.append(ArchitecturalDecision(
                title="Change Detection Strategy",
                decision="OnPush change detection for performance",
                rationale="Reduces unnecessary change detection cycles, works well with signals and immutable data",
                evidence=[f"{onpush_count} components use OnPush"],
                alternatives=["Default change detection"],
            ))

        # Check for standalone components
        standalone_count = sum(
            1 for c in self._components
            if c.get("standalone", False)
        )
        if standalone_count > 5:
            decisions.append(ArchitecturalDecision(
                title="Component Architecture",
                decision="Standalone components (no NgModules)",
                rationale="Simpler dependency management, better tree-shaking, modern Angular patterns",
                evidence=[f"{standalone_count} standalone components"],
                alternatives=["NgModule-based components"],
            ))

        return decisions

    def _extract_user_journeys(self) -> List[UserJourney]:
        """Extract user journeys from routes"""
        journeys = []

        # Group routes by feature area
        route_groups: Dict[str, List[str]] = defaultdict(list)
        for route_file in self._routes:
            for route in route_file.get("routes", []):
                path = route.get("path", "")
                if not path or path == "**":
                    continue

                # Extract first segment as feature area
                segments = path.strip("/").split("/")
                if segments:
                    feature = segments[0]
                    route_groups[feature].append(path)

        # Create journeys for key feature areas
        for feature, paths in route_groups.items():
            if len(paths) >= 2:  # At least 2 routes to be interesting
                journey = UserJourney(
                    name=f"{feature.title()} Journey",
                    steps=paths[:5],
                    entry_point=f"/{feature}",
                )
                journeys.append(journey)

        return journeys[:5]  # Limit to top 5

    def _identify_external_systems(self) -> List[str]:
        """Identify external systems from API calls and configurations"""
        systems = set()

        # From HTTP APIs - look for base URLs
        for api in self._http_apis:
            base_url = api.get("baseUrl", "")
            if base_url:
                # Extract service name from URL
                if "localhost" in base_url:
                    # Local service - extract port-based name
                    import re
                    port_match = re.search(r':(\d+)', base_url)
                    if port_match:
                        systems.add(f"Local Service (:{port_match.group(1)})")
                else:
                    parts = base_url.split("/")
                    systems.add(parts[2] if len(parts) > 2 else base_url)

        # Common patterns
        for iface in self._interfaces:
            name = iface.get("name", "").lower()
            if "broker" in name:
                systems.add("Broker API")
            if "groww" in name:
                systems.add("Groww Trading API")
            if "yahoo" in name:
                systems.add("Yahoo Finance API")

        return list(systems)[:10]

    def to_dict(self, context: BusinessDomainContext) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return context.to_dict()

    def to_codetrellis_format(self, context: BusinessDomainContext) -> str:
        """Convert to CodeTrellis compact format"""
        return context.to_codetrellis_format()
