"""
EnhancedSidekiqParser v1.0 - Comprehensive Sidekiq background job parser.

Runs as a supplementary layer on top of the Ruby parser, extracting
Sidekiq-specific semantics.

Supports:
- Sidekiq 5.x (workers, queues, retries, scheduled jobs)
- Sidekiq 6.x (ActiveJob integration, batches, capsules)
- Sidekiq 7.x (embedded mode, capsules, strict_args, transactional push)

Sidekiq-specific extraction:
- Workers/Jobs: Sidekiq::Worker / Sidekiq::Job / ActiveJob
- Queues: queue configuration, weights, priorities
- Scheduling: perform_at, perform_in, cron patterns
- Batches: Sidekiq::Batch (Pro), on_complete/on_success callbacks
- Middleware: client & server middleware chains
- Error handling: sidekiq_retries_exhausted, retry configuration
- Redis config: redis connection pools, sentinels
- Rate limiting: Sidekiq::Limiter (Enterprise)
- Periodic jobs: Sidekiq::Periodic (Enterprise)
- Capsules: Sidekiq 7 capsule configuration

Framework detection (15+ Sidekiq ecosystem patterns):
- Core: sidekiq, sidekiq-pro, sidekiq-enterprise
- Scheduling: sidekiq-cron, sidekiq-scheduler, sidekiq-unique-jobs
- Monitoring: sidekiq-statistic, sidekiq-failures
- Extensions: sidekiq-throttled, sidekiq-limit_fetch, sidekiq-batch
- ActiveJob: activejob, sidekiq adapter

Part of CodeTrellis v5.2.0 - Ruby Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SidekiqWorkerInfo:
    """Information about a Sidekiq worker/job."""
    name: str
    queue: str = "default"
    retry_count: str = ""
    dead: bool = False
    backtrace: bool = False
    unique: bool = False
    lock: str = ""
    perform_params: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class SidekiqQueueInfo:
    """Information about a Sidekiq queue configuration."""
    name: str
    weight: int = 0
    strict: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class SidekiqScheduleInfo:
    """Information about a scheduled Sidekiq job."""
    worker: str
    schedule_type: str = ""  # cron, every, at, in
    schedule_value: str = ""
    args: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class SidekiqBatchInfo:
    """Information about a Sidekiq batch (Pro)."""
    name: str = ""
    on_complete: str = ""
    on_success: str = ""
    on_death: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SidekiqMiddlewareInfo:
    """Information about Sidekiq middleware."""
    name: str
    chain: str = ""  # client or server
    position: str = ""  # add, prepend, insert_before, insert_after
    file: str = ""
    line_number: int = 0


@dataclass
class SidekiqCallbackInfo:
    """Information about Sidekiq callbacks and hooks."""
    event: str  # retries_exhausted, death, startup, shutdown, heartbeat
    handler: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SidekiqConfigInfo:
    """Information about Sidekiq configuration."""
    key: str
    value: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SidekiqPeriodicInfo:
    """Information about Sidekiq periodic jobs (Enterprise)."""
    name: str
    cron: str = ""
    worker_class: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SidekiqParseResult:
    """Complete parse result for a Sidekiq file."""
    file_path: str
    file_type: str = "ruby"

    # Workers/Jobs
    workers: List[SidekiqWorkerInfo] = field(default_factory=list)

    # Queues
    queues: List[SidekiqQueueInfo] = field(default_factory=list)

    # Scheduling
    schedules: List[SidekiqScheduleInfo] = field(default_factory=list)

    # Batches
    batches: List[SidekiqBatchInfo] = field(default_factory=list)

    # Middleware
    middleware: List[SidekiqMiddlewareInfo] = field(default_factory=list)

    # Callbacks
    callbacks: List[SidekiqCallbackInfo] = field(default_factory=list)

    # Config
    configs: List[SidekiqConfigInfo] = field(default_factory=list)

    # Periodic jobs
    periodic_jobs: List[SidekiqPeriodicInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    sidekiq_version: str = ""
    has_pro: bool = False
    has_enterprise: bool = False
    total_workers: int = 0
    total_queues: int = 0


class EnhancedSidekiqParser:
    """
    Enhanced Sidekiq parser for background job framework extraction.

    Runs AFTER the Ruby parser when Sidekiq framework is detected.
    """

    # Sidekiq detection
    SIDEKIQ_REQUIRE = re.compile(
        r"require\s+['\"]sidekiq['\"]|"
        r"Sidekiq\.\w+|"
        r"include\s+Sidekiq::|"
        r"Sidekiq::Worker|Sidekiq::Job"
    )

    # Worker/Job patterns
    WORKER_INCLUDE = re.compile(
        r"include\s+Sidekiq::(?:Worker|Job)",
    )
    WORKER_CLASS = re.compile(
        r"class\s+(\w+)(?:\s*<\s*\w+)?\s*\n(?:.*\n)*?\s*include\s+Sidekiq::(?:Worker|Job)",
        re.MULTILINE,
    )
    WORKER_CLASS_SIMPLE = re.compile(
        r"class\s+(\w+).*\n.*include\s+Sidekiq::(?:Worker|Job)",
    )
    ACTIVEJOB_CLASS = re.compile(
        r"class\s+(\w+)\s*<\s*(?:ApplicationJob|ActiveJob::Base)",
    )
    PERFORM_METHOD = re.compile(
        r"def\s+perform\s*\(([^)]*)\)",
    )
    SIDEKIQ_OPTIONS = re.compile(
        r"sidekiq_options\s+(.+)",
    )
    SIDEKIQ_RETRY = re.compile(
        r"sidekiq_retry_in\s+",
    )

    # Queue patterns (from sidekiq.yml or config)
    QUEUE_CONFIG = re.compile(
        r"^\s*-\s+(?:\[?['\"]?)(\w+)(?:['\"]?\s*,\s*(\d+)\]?)?",
        re.MULTILINE,
    )
    QUEUE_OPTION = re.compile(
        r"queue:\s*['\"]?:?(\w+)['\"]?",
    )

    # Schedule patterns
    PERFORM_ASYNC = re.compile(
        r"(\w+)\.perform_async\b",
    )
    PERFORM_IN = re.compile(
        r"(\w+)\.perform_in\s*\(\s*(.+?)\s*[,)]",
    )
    PERFORM_AT = re.compile(
        r"(\w+)\.perform_at\s*\(\s*(.+?)\s*[,)]",
    )
    CRON_SCHEDULE = re.compile(
        r"['\"]cron['\"]?\s*(?:=>|:)\s*['\"]([^'\"]+)['\"]",
    )
    EVERY_SCHEDULE = re.compile(
        r"['\"]every['\"]?\s*(?:=>|:)\s*['\"]([^'\"]+)['\"]",
    )

    # Batch patterns (Pro)
    BATCH_NEW = re.compile(
        r"Sidekiq::Batch\.new",
    )
    BATCH_ON = re.compile(
        r"batch\.on\s*\(\s*:(\w+)\s*,\s*([A-Z][\w:]+)",
    )
    BATCH_CALLBACK = re.compile(
        r"def\s+on_(?:complete|success|death)\b",
    )

    # Middleware patterns
    MIDDLEWARE_CONFIG = re.compile(
        r"config\.(?:client|server)_middleware\s+do\s*\|(\w+)\|",
    )
    MIDDLEWARE_ADD = re.compile(
        r"(\w+)\.(?:add|prepend|insert_before|insert_after)\s+([A-Z][\w:]+)",
    )

    # Callback patterns
    RETRIES_EXHAUSTED = re.compile(
        r"sidekiq_retries_exhausted\s+do",
    )
    DEATH_HANDLER = re.compile(
        r"Sidekiq\.configure_server.*death_handlers",
        re.DOTALL,
    )

    # Config patterns
    CONFIGURE_SERVER = re.compile(
        r"Sidekiq\.configure_server\s+do",
    )
    CONFIGURE_CLIENT = re.compile(
        r"Sidekiq\.configure_client\s+do",
    )
    REDIS_CONFIG = re.compile(
        r"config\.redis\s*=\s*\{([^}]+)\}",
    )
    CONCURRENCY = re.compile(
        r"config\.(?:concurrency|options\[:concurrency\])\s*=\s*(\d+)",
    )

    # Periodic patterns (Enterprise)
    PERIODIC_REGISTER = re.compile(
        r"Sidekiq::Periodic\.register\b",
    )

    # Capsule patterns (Sidekiq 7)
    CAPSULE_DEF = re.compile(
        r"config\.capsule\s*\(\s*['\"](\w+)['\"]",
    )

    # Framework detection
    FRAMEWORK_PATTERNS = {
        'sidekiq': re.compile(r"require\s+['\"]sidekiq|Sidekiq::Worker|Sidekiq::Job"),
        'sidekiq-pro': re.compile(r"sidekiq-pro|Sidekiq::Batch|Sidekiq::Limiter"),
        'sidekiq-enterprise': re.compile(r"sidekiq-enterprise|Sidekiq::Periodic|Sidekiq::RateLimiter"),
        'sidekiq-cron': re.compile(r"sidekiq-cron|Sidekiq::Cron"),
        'sidekiq-scheduler': re.compile(r"sidekiq-scheduler|SidekiqScheduler"),
        'sidekiq-unique-jobs': re.compile(r"sidekiq-unique-jobs|SidekiqUniqueJobs"),
        'sidekiq-throttled': re.compile(r"sidekiq-throttled|Sidekiq::Throttled"),
        'sidekiq-limit_fetch': re.compile(r"sidekiq-limit_fetch"),
        'sidekiq-failures': re.compile(r"sidekiq-failures"),
        'sidekiq-statistic': re.compile(r"sidekiq-statistic"),
        'sidekiq-status': re.compile(r"sidekiq-status|Sidekiq::Status"),
        'sidekiq-batch': re.compile(r"sidekiq-batch"),
        'activejob': re.compile(r"ActiveJob|ApplicationJob|queue_adapter.*sidekiq"),
        'redis': re.compile(r"Redis\.new|redis-rb|Redis::"),
    }

    def __init__(self):
        """Initialize the Sidekiq parser."""
        pass

    def parse(self, content: str, file_path: str = "") -> SidekiqParseResult:
        """Parse Ruby source code for Sidekiq-specific patterns."""
        result = SidekiqParseResult(file_path=file_path)

        # Check if this file uses Sidekiq
        if not self.SIDEKIQ_REQUIRE.search(content):
            return result

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect version
        result.sidekiq_version = self._detect_version(content)

        # Pro/Enterprise flags
        result.has_pro = any(
            f in result.detected_frameworks
            for f in ('sidekiq-pro', 'sidekiq-batch')
        )
        result.has_enterprise = 'sidekiq-enterprise' in result.detected_frameworks

        # Extract all components
        self._extract_workers(content, file_path, result)
        self._extract_queues(content, file_path, result)
        self._extract_schedules(content, file_path, result)
        self._extract_batches(content, file_path, result)
        self._extract_middleware(content, file_path, result)
        self._extract_callbacks(content, file_path, result)
        self._extract_configs(content, file_path, result)
        self._extract_periodic_jobs(content, file_path, result)

        # Totals
        result.total_workers = len(result.workers)
        result.total_queues = len(result.queues)

        return result

    def _extract_workers(self, content: str, file_path: str, result: SidekiqParseResult):
        """Extract Sidekiq worker/job definitions."""
        lines = content.split('\n')
        current_class = None
        current_worker = None

        for i, line in enumerate(lines):
            # Check for class definition
            class_match = re.match(r'\s*class\s+(\w+)', line)
            if class_match:
                current_class = class_match.group(1)

            # Check for Sidekiq::Worker / Sidekiq::Job include
            if current_class and re.search(r'include\s+Sidekiq::(?:Worker|Job)', line):
                current_worker = SidekiqWorkerInfo(
                    name=current_class,
                    file=file_path,
                    line_number=i + 1,
                )
                result.workers.append(current_worker)

            # Check for ActiveJob class
            aj_match = self.ACTIVEJOB_CLASS.match(line.strip())
            if aj_match:
                current_worker = SidekiqWorkerInfo(
                    name=aj_match.group(1),
                    file=file_path,
                    line_number=i + 1,
                )
                result.workers.append(current_worker)

            # Extract sidekiq_options
            if current_worker:
                opt_match = self.SIDEKIQ_OPTIONS.search(line)
                if opt_match:
                    opts = opt_match.group(1)
                    q_match = re.search(r"queue:\s*['\"]?:?(\w+)", opts)
                    if q_match:
                        current_worker.queue = q_match.group(1)
                    r_match = re.search(r"retry:\s*(\w+)", opts)
                    if r_match:
                        current_worker.retry_count = r_match.group(1)
                    if re.search(r"dead:\s*true", opts):
                        current_worker.dead = True
                    if re.search(r"backtrace:\s*true", opts):
                        current_worker.backtrace = True

                # Extract perform method params
                perf_match = self.PERFORM_METHOD.search(line)
                if perf_match:
                    params = perf_match.group(1).strip()
                    if params:
                        current_worker.perform_params = [
                            p.strip() for p in params.split(',')
                        ]

    def _extract_queues(self, content: str, file_path: str, result: SidekiqParseResult):
        """Extract Sidekiq queue configurations."""
        # Extract from sidekiq.yml-style content
        queues_section = re.search(r":queues:\s*\n((?:\s+-\s+.+\n)+)", content)
        if queues_section:
            for m in self.QUEUE_CONFIG.finditer(queues_section.group(1)):
                result.queues.append(SidekiqQueueInfo(
                    name=m.group(1),
                    weight=int(m.group(2)) if m.group(2) else 0,
                    file=file_path,
                ))

        # Extract from configure block
        for m in self.QUEUE_OPTION.finditer(content):
            if not any(q.name == m.group(1) for q in result.queues):
                result.queues.append(SidekiqQueueInfo(
                    name=m.group(1),
                    file=file_path,
                    line_number=content[:m.start()].count('\n') + 1,
                ))

    def _extract_schedules(self, content: str, file_path: str, result: SidekiqParseResult):
        """Extract scheduled job definitions."""
        for m in self.PERFORM_IN.finditer(content):
            result.schedules.append(SidekiqScheduleInfo(
                worker=m.group(1),
                schedule_type="in",
                schedule_value=m.group(2),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))
        for m in self.PERFORM_AT.finditer(content):
            result.schedules.append(SidekiqScheduleInfo(
                worker=m.group(1),
                schedule_type="at",
                schedule_value=m.group(2),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))
        for m in self.CRON_SCHEDULE.finditer(content):
            result.schedules.append(SidekiqScheduleInfo(
                worker="",
                schedule_type="cron",
                schedule_value=m.group(1),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _extract_batches(self, content: str, file_path: str, result: SidekiqParseResult):
        """Extract Sidekiq batch definitions (Pro)."""
        for m in self.BATCH_NEW.finditer(content):
            batch = SidekiqBatchInfo(
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )
            # Look for callbacks nearby
            nearby = content[m.start():m.start() + 500]
            for cb in self.BATCH_ON.finditer(nearby):
                setattr(batch, f"on_{cb.group(1)}", cb.group(2))
            result.batches.append(batch)

    def _extract_middleware(self, content: str, file_path: str, result: SidekiqParseResult):
        """Extract Sidekiq middleware configurations."""
        for m in self.MIDDLEWARE_ADD.finditer(content):
            chain = ""
            # Determine chain from context
            before_ctx = content[:m.start()]
            if "client_middleware" in before_ctx[-200:]:
                chain = "client"
            elif "server_middleware" in before_ctx[-200:]:
                chain = "server"
            result.middleware.append(SidekiqMiddlewareInfo(
                name=m.group(2),
                chain=chain,
                position=m.group(1) if m.group(1) in ("add", "prepend") else "",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _extract_callbacks(self, content: str, file_path: str, result: SidekiqParseResult):
        """Extract Sidekiq callback definitions."""
        if self.RETRIES_EXHAUSTED.search(content):
            result.callbacks.append(SidekiqCallbackInfo(
                event="retries_exhausted",
                file=file_path,
            ))
        if self.DEATH_HANDLER.search(content):
            result.callbacks.append(SidekiqCallbackInfo(
                event="death",
                file=file_path,
            ))
        for event in ("startup", "shutdown", "heartbeat"):
            if re.search(rf"on\(:{event}\)", content):
                result.callbacks.append(SidekiqCallbackInfo(
                    event=event,
                    file=file_path,
                ))

    def _extract_configs(self, content: str, file_path: str, result: SidekiqParseResult):
        """Extract Sidekiq configuration."""
        # Redis config
        redis_m = self.REDIS_CONFIG.search(content)
        if redis_m:
            result.configs.append(SidekiqConfigInfo(
                key="redis",
                value=redis_m.group(1).strip(),
                file=file_path,
                line_number=content[:redis_m.start()].count('\n') + 1,
            ))

        # Concurrency
        conc_m = self.CONCURRENCY.search(content)
        if conc_m:
            result.configs.append(SidekiqConfigInfo(
                key="concurrency",
                value=conc_m.group(1),
                file=file_path,
                line_number=content[:conc_m.start()].count('\n') + 1,
            ))

        # Capsules (Sidekiq 7)
        for m in self.CAPSULE_DEF.finditer(content):
            result.configs.append(SidekiqConfigInfo(
                key="capsule",
                value=m.group(1),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _extract_periodic_jobs(self, content: str, file_path: str, result: SidekiqParseResult):
        """Extract Sidekiq periodic job definitions (Enterprise)."""
        if self.PERIODIC_REGISTER.search(content):
            # Look for cron entries after register
            for m in self.CRON_SCHEDULE.finditer(content):
                result.periodic_jobs.append(SidekiqPeriodicInfo(
                    name="periodic",
                    cron=m.group(1),
                    file=file_path,
                    line_number=content[:m.start()].count('\n') + 1,
                ))

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect Sidekiq ecosystem frameworks."""
        frameworks = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(name)
        return frameworks

    def _detect_version(self, content: str) -> str:
        """Detect Sidekiq version from usage patterns."""
        # Sidekiq 7.x indicators
        if re.search(r"Sidekiq::Job|capsule|strict_args|Sidekiq\.default_job_options", content):
            return "7.x"
        # Sidekiq 6.x indicators
        if re.search(r"Sidekiq::Worker.*Sidekiq::ServerMiddleware|embedded", content):
            return "6.x"
        # Sidekiq 5.x indicators
        if re.search(r"Sidekiq::Worker", content):
            return "5.x+"
        return ""
