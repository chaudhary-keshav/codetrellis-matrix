"""
EnhancedCeleryParser - Deep extraction for Celery task queue projects.

Extends the basic CeleryExtractor with:
- Task definitions (@shared_task, @app.task, @celery.task) with full options
- Beat schedule (crontab, timedelta, solar, crontab with timezone)
- Signals (task_prerun, task_postrun, task_failure, worker_ready, etc.)
- Canvas primitives (chain, group, chord, chunks, starmap)
- Result backend configuration
- Worker configuration (concurrency, prefetch, queues)
- Routing and queue definitions
- Task retry policies
- Rate limiting
- Priority queues
- Custom task base classes

Supports Celery 3.x through 5.x+ (latest).

Part of CodeTrellis v4.33 - Python Framework Support.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any

from codetrellis.extractors.python.celery_extractor import (
    CeleryExtractor,
    CeleryTaskInfo,
    CeleryBeatScheduleInfo,
)


# ═══════════════════════════════════════════════════════════════════
# Enhanced Dataclasses
# ═══════════════════════════════════════════════════════════════════

@dataclass
class CelerySignalHandlerInfo:
    """Information about a Celery signal handler."""
    signal_name: str  # task_prerun, task_postrun, task_failure, worker_ready, etc.
    handler: str
    is_async: bool = False
    line_number: int = 0


@dataclass
class CeleryCanvasUsageInfo:
    """Information about Celery canvas primitive usage."""
    canvas_type: str  # chain, group, chord, chunks, starmap, signature
    tasks: List[str] = field(default_factory=list)
    variable_name: str = ""
    line_number: int = 0


@dataclass
class CeleryResultBackendInfo:
    """Information about Celery result backend configuration."""
    backend_type: str  # redis, rpc, database, django-db, cache, mongodb, filesystem
    url: str = ""
    line_number: int = 0


@dataclass
class CeleryWorkerConfigInfo:
    """Information about Celery worker configuration."""
    setting: str
    value: str
    line_number: int = 0


@dataclass
class CeleryQueueInfo:
    """Information about a Celery queue definition."""
    name: str
    exchange: Optional[str] = None
    routing_key: Optional[str] = None
    line_number: int = 0


@dataclass
class CeleryRouteInfo:
    """Information about a Celery task route."""
    task_pattern: str
    queue: str
    exchange: Optional[str] = None
    routing_key: Optional[str] = None
    line_number: int = 0


@dataclass
class CeleryAppConfigInfo:
    """Information about Celery app configuration."""
    app_name: str
    broker_url: str = ""
    broker_type: str = ""  # redis, amqp, sqs, etc.
    line_number: int = 0


@dataclass
class CeleryParseResult:
    """Complete parse result for a Celery file."""
    file_path: str
    file_type: str = "module"  # app, task, config, beat, worker, test

    # From base extractor
    tasks: List[CeleryTaskInfo] = field(default_factory=list)
    schedules: List[CeleryBeatScheduleInfo] = field(default_factory=list)

    # Enhanced extraction
    signal_handlers: List[CelerySignalHandlerInfo] = field(default_factory=list)
    canvas_usages: List[CeleryCanvasUsageInfo] = field(default_factory=list)
    result_backends: List[CeleryResultBackendInfo] = field(default_factory=list)
    worker_configs: List[CeleryWorkerConfigInfo] = field(default_factory=list)
    queues: List[CeleryQueueInfo] = field(default_factory=list)
    routes: List[CeleryRouteInfo] = field(default_factory=list)
    app_configs: List[CeleryAppConfigInfo] = field(default_factory=list)

    # Aggregate
    detected_frameworks: List[str] = field(default_factory=list)
    celery_version: str = ""
    total_tasks: int = 0
    total_schedules: int = 0
    uses_canvas: bool = False


# ═══════════════════════════════════════════════════════════════════
# Parser
# ═══════════════════════════════════════════════════════════════════

class EnhancedCeleryParser:
    """
    Enhanced Celery parser v1.0 that extends the basic CeleryExtractor.

    Provides deep extraction for Celery 3.x through 5.x+ including
    tasks, beat schedules, signals, canvas primitives, result backends,
    worker config, routing, and queue definitions.
    """

    # ── Celery ecosystem detection patterns ───────────────────────
    FRAMEWORK_PATTERNS = {
        # Core Celery
        'celery': re.compile(
            r'from\s+celery\s+import|import\s+celery|from\s+celery\.',
            re.MULTILINE,
        ),
        'celery.app': re.compile(
            r'Celery\s*\(|from\s+celery\s+import\s+Celery',
            re.MULTILINE,
        ),
        'celery.shared_task': re.compile(
            r'from\s+celery\s+import\s+shared_task|@shared_task',
            re.MULTILINE,
        ),

        # Canvas
        'celery.canvas': re.compile(
            r'from\s+celery\s+import\s+[^;\n]*(?:chain|group|chord|chunks|starmap)|'
            r'from\s+celery\.canvas|chain\s*\(|group\s*\(|chord\s*\(',
            re.MULTILINE,
        ),

        # Signals
        'celery.signals': re.compile(
            r'from\s+celery\.signals|task_prerun|task_postrun|task_failure|'
            r'worker_ready|worker_shutdown|celeryd_after_setup',
            re.MULTILINE,
        ),

        # Beat
        'celery.beat': re.compile(
            r'from\s+celery\.schedules|beat_schedule|crontab\s*\(|'
            r'CELERYBEAT_SCHEDULE|CELERY_BEAT_SCHEDULE',
            re.MULTILINE,
        ),

        # Result backends
        'celery.result': re.compile(
            r'result_backend|CELERY_RESULT_BACKEND|AsyncResult\s*\(|GroupResult\s*\(',
            re.MULTILINE,
        ),

        # Kombu (messaging)
        'kombu': re.compile(
            r'from\s+kombu|import\s+kombu|Exchange\s*\(|Queue\s*\(',
            re.MULTILINE,
        ),

        # Django-Celery
        'django_celery': re.compile(
            r'from\s+django_celery_beat|django_celery_results|DJANGO_CELERY',
            re.MULTILINE,
        ),

        # Flask-Celery
        'flask_celery': re.compile(
            r'from\s+flask_celery|celery\.conf\.update\s*\(',
            re.MULTILINE,
        ),

        # Flower (monitoring)
        'flower': re.compile(
            r'from\s+flower|import\s+flower|flower',
            re.MULTILINE,
        ),

        # Redis as broker
        'redis_broker': re.compile(
            r'redis://|BROKER.*redis',
            re.MULTILINE,
        ),

        # RabbitMQ as broker
        'amqp_broker': re.compile(
            r'amqp://|pyamqp://|BROKER.*amqp|BROKER.*rabbit',
            re.MULTILINE,
        ),
    }

    # ── Celery app instantiation ──────────────────────────────────
    CELERY_APP_PATTERN = re.compile(
        r'(\w+)\s*=\s*Celery\s*\(\s*(?:["\']([^"\']+)["\'])?(?:\s*,\s*([^)]+))?\s*\)',
        re.MULTILINE,
    )

    # ── Signal handler patterns ───────────────────────────────────
    SIGNAL_CONNECT_PATTERN = re.compile(
        r'(task_prerun|task_postrun|task_failure|task_success|task_retry|'
        r'task_revoked|task_rejected|task_unknown|'
        r'worker_ready|worker_shutdown|worker_init|'
        r'worker_process_init|worker_process_shutdown|'
        r'celeryd_after_setup|celeryd_init|'
        r'before_task_publish|after_task_publish|'
        r'beat_init|beat_embedded_init|eventlet_pool_started|'
        r'setup_logging|after_setup_task_logger)\.connect\s*\(\s*(\w+)',
        re.MULTILINE,
    )

    SIGNAL_DECORATOR_PATTERN = re.compile(
        r'@(task_prerun|task_postrun|task_failure|task_success|task_retry|'
        r'task_revoked|task_rejected|'
        r'worker_ready|worker_shutdown|worker_init|'
        r'before_task_publish|after_task_publish|'
        r'beat_init)\.connect\s*(?:\(\s*\))?\s*\n'
        r'\s*(?:async\s+)?def\s+(\w+)',
        re.MULTILINE,
    )

    # ── Canvas patterns ───────────────────────────────────────────
    CANVAS_PATTERN = re.compile(
        r'(?:(\w+)\s*=\s*)?(chain|group|chord|chunks|starmap|signature|si)\s*\(\s*([^)]*(?:\([^)]*\)[^)]*)*)\s*\)',
        re.MULTILINE,
    )

    # ── Result backend pattern ────────────────────────────────────
    RESULT_BACKEND_PATTERN = re.compile(
        r'(?:result_backend|CELERY_RESULT_BACKEND)\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE,
    )

    # ── Broker URL pattern ────────────────────────────────────────
    BROKER_URL_PATTERN = re.compile(
        r'(?:broker_url|broker|BROKER_URL|CELERY_BROKER_URL)\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE,
    )

    # ── Queue definition pattern (Kombu) ──────────────────────────
    QUEUE_DEF_PATTERN = re.compile(
        r'Queue\s*\(\s*["\'](\w+)["\']\s*'
        r'(?:,\s*Exchange\s*\(\s*["\'](\w+)["\']\s*[^)]*\)\s*)?'
        r'(?:,\s*routing_key\s*=\s*["\']([^"\']+)["\'])?',
        re.MULTILINE,
    )

    # ── Route definition pattern ──────────────────────────────────
    ROUTE_PATTERN = re.compile(
        r'["\']([^"\']+)["\']\s*:\s*\{\s*["\']queue["\']\s*:\s*["\'](\w+)["\']'
        r'(?:\s*,\s*["\']exchange["\']\s*:\s*["\'](\w+)["\'])?'
        r'(?:\s*,\s*["\']routing_key["\']\s*:\s*["\']([^"\']+)["\'])?',
        re.MULTILINE,
    )

    # ── Worker config patterns ────────────────────────────────────
    WORKER_CONFIG_PATTERNS = {
        'worker_concurrency': re.compile(r'(?:worker_concurrency|CELERYD_CONCURRENCY)\s*=\s*(\d+)'),
        'worker_prefetch_multiplier': re.compile(r'(?:worker_prefetch_multiplier|CELERYD_PREFETCH_MULTIPLIER)\s*=\s*(\d+)'),
        'worker_max_tasks_per_child': re.compile(r'(?:worker_max_tasks_per_child|CELERYD_MAX_TASKS_PER_CHILD)\s*=\s*(\d+)'),
        'task_serializer': re.compile(r'(?:task_serializer|CELERY_TASK_SERIALIZER)\s*=\s*["\'](\w+)["\']'),
        'result_serializer': re.compile(r'(?:result_serializer|CELERY_RESULT_SERIALIZER)\s*=\s*["\'](\w+)["\']'),
        'accept_content': re.compile(r'(?:accept_content|CELERY_ACCEPT_CONTENT)\s*=\s*\[([^\]]+)\]'),
        'task_always_eager': re.compile(r'(?:task_always_eager|CELERY_ALWAYS_EAGER)\s*=\s*(True|False)'),
        'task_acks_late': re.compile(r'(?:task_acks_late|CELERY_ACKS_LATE)\s*=\s*(True|False)'),
        'task_track_started': re.compile(r'(?:task_track_started|CELERY_TRACK_STARTED)\s*=\s*(True|False)'),
        'task_time_limit': re.compile(r'(?:task_time_limit|CELERYD_TASK_TIME_LIMIT)\s*=\s*(\d+)'),
        'task_soft_time_limit': re.compile(r'(?:task_soft_time_limit|CELERYD_TASK_SOFT_TIME_LIMIT)\s*=\s*(\d+)'),
        'timezone': re.compile(r'(?:timezone|CELERY_TIMEZONE)\s*=\s*["\']([^"\']+)["\']'),
        'enable_utc': re.compile(r'(?:enable_utc|CELERY_ENABLE_UTC)\s*=\s*(True|False)'),
    }

    # ── Version feature detection ─────────────────────────────────
    CELERY_VERSION_FEATURES = {
        'shared_task': '3.1',
        'chain': '3.0',
        'group': '3.0',
        'chord': '3.0',
        'chunks': '3.0',
        'signature': '3.0',
        'canvas': '3.0',
        'crontab': '2.0',
        'beat_schedule': '4.0',
        'task_always_eager': '4.0',
        'task_acks_late': '4.0',
        'worker_concurrency': '4.0',
        'task_prerun': '3.0',
        'AsyncResult': '2.0',
        'Celery': '3.0',
    }

    def __init__(self):
        """Initialize the enhanced Celery parser."""
        self.base_extractor = CeleryExtractor()

    def parse(self, content: str, file_path: str = "") -> CeleryParseResult:
        """
        Parse Celery source code and extract all Celery-specific information.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            CeleryParseResult with all extracted information
        """
        result = CeleryParseResult(file_path=file_path)

        # Determine file type
        result.file_type = self._classify_file(file_path, content)

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # ── Tasks & Schedules (base extractor) ───────────────────
        base_result = self.base_extractor.extract(content)
        result.tasks = base_result.get('tasks', [])
        result.schedules = base_result.get('schedules', [])

        # ── Enhanced beat schedule extraction (fallback) ─────────
        if not result.schedules:
            self._extract_beat_schedules_enhanced(content, result)

        # ── App configuration ────────────────────────────────────
        self._extract_app_config(content, result)

        # ── Signal handlers ──────────────────────────────────────
        self._extract_signal_handlers(content, result)

        # ── Canvas primitives ────────────────────────────────────
        self._extract_canvas_usages(content, result)

        # ── Result backends ──────────────────────────────────────
        self._extract_result_backends(content, result)

        # ── Worker configuration ─────────────────────────────────
        self._extract_worker_configs(content, result)

        # ── Queues ───────────────────────────────────────────────
        self._extract_queues(content, result)

        # ── Routes ───────────────────────────────────────────────
        self._extract_routes(content, result)

        # Aggregates
        result.total_tasks = len(result.tasks)
        result.total_schedules = len(result.schedules)
        result.uses_canvas = len(result.canvas_usages) > 0
        result.celery_version = self._detect_celery_version(content)

        return result

    # ─── Extraction methods ───────────────────────────────────────

    def _extract_app_config(self, content: str, result: CeleryParseResult):
        """Extract Celery app instantiation."""
        for match in self.CELERY_APP_PATTERN.finditer(content):
            var_name = match.group(1)
            app_name = match.group(2) or var_name
            args_str = match.group(3) or ""

            # Extract broker URL
            broker_url = ""
            broker_match = re.search(r'broker\s*=\s*["\']([^"\']+)["\']', args_str)
            if broker_match:
                broker_url = broker_match.group(1)

            # Also check standalone broker_url
            if not broker_url:
                standalone = self.BROKER_URL_PATTERN.search(content)
                if standalone:
                    broker_url = standalone.group(1)

            # Determine broker type
            broker_type = ""
            if broker_url:
                if 'redis' in broker_url:
                    broker_type = "redis"
                elif 'amqp' in broker_url or 'rabbit' in broker_url:
                    broker_type = "amqp"
                elif 'sqs' in broker_url:
                    broker_type = "sqs"
                elif 'mongodb' in broker_url:
                    broker_type = "mongodb"

            result.app_configs.append(CeleryAppConfigInfo(
                app_name=app_name,
                broker_url=broker_url,
                broker_type=broker_type,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_beat_schedules_enhanced(self, content: str, result: CeleryParseResult):
        """Enhanced beat schedule extraction supporting hyphenated names and nested braces."""
        # Match beat_schedule / app.conf.beat_schedule / CELERYBEAT_SCHEDULE
        schedule_block_pattern = re.compile(
            r'(?:beat_schedule|CELERYBEAT_SCHEDULE|CELERY_BEAT_SCHEDULE)\s*=\s*\{',
            re.MULTILINE,
        )
        block_match = schedule_block_pattern.search(content)
        if not block_match:
            return

        # Find matching closing brace (handle nesting)
        start = block_match.end() - 1  # position of '{'
        depth = 0
        end = start
        for i in range(start, len(content)):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

        if depth != 0:
            return

        schedule_block = content[start + 1:end - 1]

        # Extract individual entries: 'name': { ... }
        entry_pattern = re.compile(
            r"""['"]([\w\-\.]+)['"]\s*:\s*\{([^}]+)\}""",
            re.MULTILINE,
        )

        for entry_match in entry_pattern.finditer(schedule_block):
            schedule_name = entry_match.group(1)
            entry_content = entry_match.group(2)

            # Extract task
            task_match = re.search(r"""['"]task['"]\s*:\s*['"]([^"']+)['"]""", entry_content)
            task = task_match.group(1) if task_match else "unknown"

            # Extract schedule string
            schedule_str = "unknown"
            crontab_match = re.search(r'crontab\s*\(\s*([^)]*)\s*\)', entry_content)
            timedelta_match = re.search(r'timedelta\s*\(\s*([^)]*)\s*\)', entry_content)
            seconds_match = re.search(r"""['"]schedule['"]\s*:\s*(\d+)""", entry_content)
            if crontab_match:
                schedule_str = f"crontab({crontab_match.group(1)})"
            elif timedelta_match:
                schedule_str = f"timedelta({timedelta_match.group(1)})"
            elif seconds_match:
                schedule_str = f"{seconds_match.group(1)}s"
            else:
                # Bare numeric schedule value
                bare_match = re.search(r"""['"]schedule['"]\s*:\s*(\d+(?:\.\d+)?)""", entry_content)
                if bare_match:
                    schedule_str = f"{bare_match.group(1)}s"

            # Extract args
            args: List[str] = []
            args_match = re.search(r"""['"]args['"]\s*:\s*\(([^)]*)\)""", entry_content)
            if args_match:
                args = [a.strip().strip("'\"") for a in args_match.group(1).split(',') if a.strip()]

            # Extract queue
            queue_match = re.search(r"""['"]queue['"]\s*:\s*['"]([^"']+)['"]""", entry_content)
            queue = queue_match.group(1) if queue_match else None

            from codetrellis.extractors.python.celery_extractor import CeleryBeatScheduleInfo
            result.schedules.append(CeleryBeatScheduleInfo(
                name=schedule_name,
                task=task,
                schedule=schedule_str,
                args=args,
                queue=queue,
            ))

    def _extract_signal_handlers(self, content: str, result: CeleryParseResult):
        """Extract signal handlers."""
        # signal.connect(handler) pattern
        for match in self.SIGNAL_CONNECT_PATTERN.finditer(content):
            result.signal_handlers.append(CelerySignalHandlerInfo(
                signal_name=match.group(1),
                handler=match.group(2),
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # @signal.connect decorator pattern
        for match in self.SIGNAL_DECORATOR_PATTERN.finditer(content):
            signal_name = match.group(1)
            handler = match.group(2)
            # Avoid duplicates
            if not any(s.signal_name == signal_name and s.handler == handler
                       for s in result.signal_handlers):
                result.signal_handlers.append(CelerySignalHandlerInfo(
                    signal_name=signal_name,
                    handler=handler,
                    line_number=content[:match.start()].count('\n') + 1,
                ))

    def _extract_canvas_usages(self, content: str, result: CeleryParseResult):
        """Extract canvas primitive usage."""
        for match in self.CANVAS_PATTERN.finditer(content):
            var_name = match.group(1) or ""
            canvas_type = match.group(2)
            args_str = match.group(3)

            # Extract task names from the canvas args
            tasks = re.findall(r'(\w+)\.s\(|(\w+)\.si\(|(\w+)\.signature\(', args_str)
            task_names = [t[0] or t[1] or t[2] for t in tasks if any(t)]

            # Also look for string task names
            str_tasks = re.findall(r'["\']([a-zA-Z_.]+)["\']', args_str)
            task_names.extend(str_tasks)

            result.canvas_usages.append(CeleryCanvasUsageInfo(
                canvas_type=canvas_type,
                tasks=task_names,
                variable_name=var_name,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_result_backends(self, content: str, result: CeleryParseResult):
        """Extract result backend configuration."""
        for match in self.RESULT_BACKEND_PATTERN.finditer(content):
            url = match.group(1)
            backend_type = ""
            if 'redis' in url:
                backend_type = "redis"
            elif 'rpc' in url:
                backend_type = "rpc"
            elif 'db+' in url or 'database' in url:
                backend_type = "database"
            elif 'django-db' in url:
                backend_type = "django-db"
            elif 'mongodb' in url:
                backend_type = "mongodb"
            elif 'cache' in url:
                backend_type = "cache"
            elif 'filesystem' in url:
                backend_type = "filesystem"

            result.result_backends.append(CeleryResultBackendInfo(
                backend_type=backend_type,
                url=url,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_worker_configs(self, content: str, result: CeleryParseResult):
        """Extract worker configuration settings."""
        for setting, pattern in self.WORKER_CONFIG_PATTERNS.items():
            match = pattern.search(content)
            if match:
                result.worker_configs.append(CeleryWorkerConfigInfo(
                    setting=setting,
                    value=match.group(1),
                    line_number=content[:match.start()].count('\n') + 1,
                ))

    def _extract_queues(self, content: str, result: CeleryParseResult):
        """Extract queue definitions."""
        for match in self.QUEUE_DEF_PATTERN.finditer(content):
            name = match.group(1)
            exchange = match.group(2)
            routing_key = match.group(3)

            result.queues.append(CeleryQueueInfo(
                name=name,
                exchange=exchange,
                routing_key=routing_key,
                line_number=content[:match.start()].count('\n') + 1,
            ))

    def _extract_routes(self, content: str, result: CeleryParseResult):
        """Extract task route definitions."""
        # Look for task_routes or CELERY_ROUTES dict
        routes_block = re.search(
            r'(?:task_routes|CELERY_ROUTES)\s*=\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}',
            content,
            re.MULTILINE,
        )
        if not routes_block:
            return

        block_content = routes_block.group(1)
        for match in self.ROUTE_PATTERN.finditer(block_content):
            result.routes.append(CeleryRouteInfo(
                task_pattern=match.group(1),
                queue=match.group(2),
                exchange=match.group(3),
                routing_key=match.group(4),
                line_number=content[:routes_block.start()].count('\n') + 1,
            ))

    # ─── Helper methods ───────────────────────────────────────────

    def _classify_file(self, file_path: str, content: str) -> str:
        """Classify a Celery file by its role."""
        normalized = file_path.replace('\\', '/').lower()
        basename = normalized.split('/')[-1] if normalized else ""

        if basename in ('celery.py', 'celeryconfig.py', 'celery_app.py'):
            return 'app'
        if basename.startswith('test') or basename.startswith('conftest'):
            return 'test'
        if 'task' in basename:
            return 'task'
        if 'config' in basename or 'settings' in basename:
            return 'config'
        if 'beat' in basename or 'schedule' in basename:
            return 'beat'
        if 'worker' in basename:
            return 'worker'

        if '/tasks/' in normalized:
            return 'task'
        if '/workers/' in normalized:
            return 'worker'

        # Check content
        if 'Celery(' in content:
            return 'app'
        if '@shared_task' in content or '@app.task' in content or '@celery.task' in content:
            return 'task'
        if 'beat_schedule' in content:
            return 'beat'

        return 'module'

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect Celery ecosystem frameworks."""
        frameworks = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(name)
        return frameworks

    def _detect_celery_version(self, content: str) -> str:
        """Detect minimum Celery version required."""
        max_version = '0.0'
        for feature, version in self.CELERY_VERSION_FEATURES.items():
            if feature in content:
                if self._version_compare(version, max_version) > 0:
                    max_version = version
        return max_version if max_version != '0.0' else ''

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings."""
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        for a, b in zip(parts1, parts2):
            if a != b:
                return a - b
        return len(parts1) - len(parts2)

    def is_celery_file(self, content: str, file_path: str = "") -> bool:
        """Determine if a file is a Celery-specific file."""
        # Direct celery imports
        if re.search(r'from\s+celery[\s.]|import\s+celery', content):
            return True
        # Task decorators
        if re.search(r'@shared_task|@\w+\.task\s*\(|@celery\.task', content):
            return True
        # Celery app instantiation
        if re.search(r'Celery\s*\(', content):
            return True
        # Beat schedule
        if re.search(r'beat_schedule|CELERYBEAT_SCHEDULE|CELERY_BEAT_SCHEDULE', content):
            return True
        # Celery config file
        normalized = file_path.replace('\\', '/').lower()
        if 'celery' in normalized.split('/')[-1]:
            return True
        return False

    def to_codetrellis_format(self, result: CeleryParseResult) -> str:
        """Convert parse result to CodeTrellis compressed format."""
        lines = []

        if result.file_path:
            lines.append(f"[FILE:{Path(result.file_path).name}|type:{result.file_type}]")
        if result.detected_frameworks:
            lines.append(f"[CELERY_ECOSYSTEM:{','.join(result.detected_frameworks)}]")
        if result.celery_version:
            lines.append(f"[CELERY_VERSION:>={result.celery_version}]")
        lines.append("")

        # App config
        if result.app_configs:
            lines.append("=== CELERY_APP ===")
            for ac in result.app_configs:
                broker_str = f"|broker:{ac.broker_type}" if ac.broker_type else ""
                lines.append(f"  {ac.app_name}{broker_str}")
            lines.append("")

        # Tasks
        if result.tasks:
            lines.append("=== CELERY_TASKS ===")
            for t in result.tasks:
                flags = []
                if t.bind:
                    flags.append("bind")
                if t.is_async:
                    flags.append("async")
                if t.ignore_result:
                    flags.append("no_result")
                flag_str = f"[{','.join(flags)}]" if flags else ""
                params_str = f"({','.join(t.parameters)})" if t.parameters else "()"
                opts = []
                if t.max_retries is not None:
                    opts.append(f"retries:{t.max_retries}")
                if t.rate_limit:
                    opts.append(f"rate:{t.rate_limit}")
                if t.time_limit:
                    opts.append(f"timeout:{t.time_limit}s")
                if t.queue:
                    opts.append(f"queue:{t.queue}")
                opts_str = f"|opts:{','.join(opts)}" if opts else ""
                return_str = f"|→{t.return_type}" if t.return_type else ""
                lines.append(f"  {t.name}{flag_str}{params_str}{opts_str}{return_str}")
            lines.append("")

        # Beat schedules
        if result.schedules:
            lines.append("=== CELERY_BEAT ===")
            for s in result.schedules:
                queue_str = f"|queue:{s.queue}" if s.queue else ""
                lines.append(f"  {s.name}|task:{s.task}|{s.schedule}{queue_str}")
            lines.append("")

        # Signals
        if result.signal_handlers:
            lines.append("=== CELERY_SIGNALS ===")
            for sh in result.signal_handlers:
                lines.append(f"  @{sh.signal_name} → {sh.handler}")
            lines.append("")

        # Canvas
        if result.canvas_usages:
            lines.append("=== CELERY_CANVAS ===")
            for cu in result.canvas_usages:
                tasks_str = f"|tasks:{','.join(cu.tasks)}" if cu.tasks else ""
                var_str = f"{cu.variable_name}=" if cu.variable_name else ""
                lines.append(f"  {var_str}{cu.canvas_type}{tasks_str}")
            lines.append("")

        # Queues
        if result.queues:
            lines.append("=== CELERY_QUEUES ===")
            for q in result.queues:
                exchange_str = f"|exchange:{q.exchange}" if q.exchange else ""
                lines.append(f"  {q.name}{exchange_str}")
            lines.append("")

        # Worker config
        if result.worker_configs:
            lines.append("=== CELERY_WORKER_CONFIG ===")
            for wc in result.worker_configs:
                lines.append(f"  {wc.setting}={wc.value}")
            lines.append("")

        # Result backend
        if result.result_backends:
            lines.append("=== CELERY_RESULT_BACKEND ===")
            for rb in result.result_backends:
                lines.append(f"  {rb.backend_type}|{rb.url}")
            lines.append("")

        return '\n'.join(lines)
