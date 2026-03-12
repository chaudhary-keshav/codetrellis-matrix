"""
Enhanced Oban Parser for CodeTrellis

Self-contained framework parser for Oban (Elixir background job processing).
Detects and extracts:
- Worker definitions (queue, max_attempts, priority, tags, unique)
- Queue configuration
- Plugin usage (Pruner, Stager, Lifeline, Cron, Pro plugins)
- Crontab schedules
- Telemetry events
- Testing patterns (Oban.Testing)
- Pro features (Batch, Chunk, Workflow, Rate Limiter)

Oban versions: 2.0–2.17+ (detects based on features)

Reference pattern: Rails parser (self-contained framework file)

Part of CodeTrellis - Oban Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


# ── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class ObanWorkerInfo:
    """Information about an Oban Worker."""
    name: str
    queue: str = "default"
    max_attempts: int = 20
    priority: int = 0
    tags: List[str] = field(default_factory=list)
    unique: str = ""
    has_perform: bool = False
    has_timeout: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class ObanQueueInfo:
    """Information about an Oban queue configuration."""
    name: str
    limit: int = 0
    local_limit: int = 0
    rate_limit: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class ObanPluginInfo:
    """Information about an Oban plugin."""
    name: str
    options: str = ""
    is_pro: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class ObanCronInfo:
    """Information about an Oban cron schedule."""
    schedule: str
    worker: str = ""
    args: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class ObanTelemetryInfo:
    """Information about Oban telemetry events."""
    event: str
    handler: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class ObanProFeatureInfo:
    """Information about Oban Pro features."""
    feature: str  # batch, chunk, workflow, rate_limiter, smart_engine
    module: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class ObanParseResult:
    """Complete parse result for an Oban file."""
    file_path: str
    file_type: str = "elixir"

    # Workers
    workers: List[ObanWorkerInfo] = field(default_factory=list)

    # Queues
    queues: List[ObanQueueInfo] = field(default_factory=list)

    # Plugins
    plugins: List[ObanPluginInfo] = field(default_factory=list)

    # Cron schedules
    cron_schedules: List[ObanCronInfo] = field(default_factory=list)

    # Telemetry
    telemetry_events: List[ObanTelemetryInfo] = field(default_factory=list)

    # Pro features
    pro_features: List[ObanProFeatureInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    oban_version: str = ""
    has_pro: bool = False
    has_cron: bool = False
    has_testing: bool = False
    total_workers: int = 0
    total_queues: int = 0


# ── Parser ───────────────────────────────────────────────────────────────────

class EnhancedObanParser:
    """
    Enhanced Oban framework parser for CodeTrellis.

    Self-contained parser that extracts Oban-specific patterns from Elixir files.
    Only populates results if Oban framework is detected.
    """

    # Oban detection
    OBAN_REQUIRE = re.compile(
        r'use\s+Oban\.Worker|'
        r'use\s+Oban\.Pro\.\w+|'
        r'Oban\.Job|Oban\.insert|'
        r'Oban\.Testing|'
        r'\{Oban\s*,|'
        r'config\s+:\w+\s*,\s*Oban|'
        r':telemetry\.attach.*oban|'
        r'\[:oban\s*,|'
        r'@impl\s+Oban\.Worker',
        re.MULTILINE,
    )

    # ── Worker patterns ──────────────────────────────────────────────────

    WORKER_RE = re.compile(
        r'use\s+Oban\.Worker\s*(?:,\s*(.+?))?$',
        re.MULTILINE,
    )

    WORKER_QUEUE_RE = re.compile(r'queue:\s*:?(\w+)')
    WORKER_MAX_ATTEMPTS_RE = re.compile(r'max_attempts:\s*(\d+)')
    WORKER_PRIORITY_RE = re.compile(r'priority:\s*(\d+)')
    WORKER_TAGS_RE = re.compile(r'tags:\s*\[([^\]]*)\]')
    WORKER_UNIQUE_RE = re.compile(r'unique:\s*\[([^\]]*)\]')

    PERFORM_RE = re.compile(
        r'^\s*(?:@impl\s+(?:true|Oban\.Worker)\s*\n\s*)?def\s+perform\(',
        re.MULTILINE,
    )

    TIMEOUT_RE = re.compile(
        r'def\s+timeout\(',
        re.MULTILINE,
    )

    # ── Queue configuration patterns ─────────────────────────────────────

    QUEUE_CONFIG_RE = re.compile(
        r'queues:\s*\[([^\]]+)\]',
        re.MULTILINE,
    )

    QUEUE_ENTRY_RE = re.compile(
        r':?(\w+)(?::\s*|\s*,\s*)(\d+)',
    )

    # ── Plugin patterns ──────────────────────────────────────────────────

    PLUGIN_RE = re.compile(
        r'\{(Oban\.(?:Plugins\.)?[\w.]+|Oban\.Pro\.Plugins\.[\w.]+)\s*(?:,\s*(.+?))?\}',
        re.MULTILINE,
    )

    PLUGIN_SIMPLE_RE = re.compile(
        r'(Oban\.Plugins\.\w+|Oban\.Pro\.Plugins\.\w+)',
        re.MULTILINE,
    )

    # ── Cron patterns ────────────────────────────────────────────────────

    CRON_RE = re.compile(
        r'\{("(?:[^"]+)"|\~e\[.+?\])\s*,\s*([\w.]+)(?:\s*,\s*(.+?))?\}',
        re.MULTILINE,
    )

    CRONTAB_RE = re.compile(
        r'crontab:\s*\[',
        re.MULTILINE,
    )

    # ── Telemetry patterns ───────────────────────────────────────────────

    TELEMETRY_RE = re.compile(
        r':telemetry\.(?:attach|execute)\(\s*"([^"]+)"\s*,\s*\[([^\]]+)\]',
        re.MULTILINE,
    )

    OBAN_TELEMETRY_RE = re.compile(
        r'\[:oban\s*,\s*:(\w+)\s*(?:,\s*:(\w+))?\]',
        re.MULTILINE,
    )

    # ── Pro feature patterns ─────────────────────────────────────────────

    PRO_BATCH_RE = re.compile(r'use\s+Oban\.Pro\.Workers\.Batch|Oban\.Pro\.Batch', re.MULTILINE)
    PRO_CHUNK_RE = re.compile(r'use\s+Oban\.Pro\.Workers\.Chunk', re.MULTILINE)
    PRO_WORKFLOW_RE = re.compile(r'use\s+Oban\.Pro\.Workers\.Workflow|Oban\.Pro\.Workflow', re.MULTILINE)
    PRO_RATE_LIMIT_RE = re.compile(r'Oban\.Pro\.Plugins\.DynamicLifeline|rate_limit', re.MULTILINE)
    PRO_SMART_ENGINE_RE = re.compile(r'Oban\.Pro\.Engines\.Smart|engine:\s*Oban\.Pro', re.MULTILINE)

    # ── Insert patterns ──────────────────────────────────────────────────

    INSERT_RE = re.compile(
        r'Oban\.(insert!?|insert_all!?)\(',
        re.MULTILINE,
    )

    NEW_RE = re.compile(
        r'([\w.]+)\.new\(\s*(%\{[^}]*\}|\w+)',
        re.MULTILINE,
    )

    # ── Testing patterns ─────────────────────────────────────────────────

    TESTING_RE = re.compile(
        r'use\s+Oban\.Testing|Oban\.Testing\.\w+|assert_enqueued|refute_enqueued|perform_job',
        re.MULTILINE,
    )

    # ── Version detection ────────────────────────────────────────────────

    VERSION_FEATURES = [
        ('2.17', re.compile(r'Oban\.Notifiers\.PG|engine:\s*Oban\.Engines\.Lite', re.MULTILINE)),
        ('2.15', re.compile(r'Oban\.Engines\.\w+|Oban\.Notifiers\.\w+', re.MULTILINE)),
        ('2.13', re.compile(r'Oban\.Pro\.Engines\.Smart|Oban\.Pro\.Plugins', re.MULTILINE)),
        ('2.11', re.compile(r'unique:\s*\[|replace:\s*\[', re.MULTILINE)),
        ('2.9', re.compile(r'Oban\.Testing\.all_enqueued|perform_job', re.MULTILINE)),
        ('2.6', re.compile(r'Oban\.Plugins\.Pruner|Oban\.Plugins\.Stager', re.MULTILINE)),
        ('2.0', re.compile(r'use\s+Oban\.Worker|Oban\.insert', re.MULTILINE)),
    ]

    def parse(self, content: str, file_path: str = "") -> ObanParseResult:
        """Parse Elixir source code for Oban-specific patterns."""
        result = ObanParseResult(file_path=file_path)

        # Check if this file uses Oban
        if not self.OBAN_REQUIRE.search(content):
            return result

        # Detect version
        result.oban_version = self._detect_version(content)

        # Feature flags
        result.has_pro = bool(re.search(r'Oban\.Pro\.', content))
        result.has_cron = bool(self.CRONTAB_RE.search(content))
        result.has_testing = bool(self.TESTING_RE.search(content))

        # Extract all patterns
        self._extract_workers(content, file_path, result)
        self._extract_queues(content, file_path, result)
        self._extract_plugins(content, file_path, result)
        self._extract_cron_schedules(content, file_path, result)
        self._extract_telemetry(content, file_path, result)
        self._extract_pro_features(content, file_path, result)

        # Update totals
        result.total_workers = len(result.workers)
        result.total_queues = len(result.queues)

        return result

    def _detect_version(self, content: str) -> str:
        """Detect Oban version based on features used."""
        for version, pattern in self.VERSION_FEATURES:
            if pattern.search(content):
                return version
        return ""

    def _find_enclosing_module(self, content: str, pos: int) -> str:
        """Find the nearest enclosing defmodule name."""
        prefix = content[:pos]
        modules = re.findall(r'defmodule\s+([\w.]+)\s+do', prefix)
        return modules[-1] if modules else "Unknown"

    def _extract_workers(self, content: str, file_path: str, result: ObanParseResult):
        """Extract Oban Worker definitions."""
        for m in self.WORKER_RE.finditer(content):
            line = content[:m.start()].count('\n') + 1
            module = self._find_enclosing_module(content, m.start())
            options = m.group(1) or ""

            # Parse worker options
            queue = "default"
            queue_m = self.WORKER_QUEUE_RE.search(options)
            if queue_m:
                queue = queue_m.group(1)

            max_attempts = 20
            max_m = self.WORKER_MAX_ATTEMPTS_RE.search(options)
            if max_m:
                max_attempts = int(max_m.group(1))

            priority = 0
            prio_m = self.WORKER_PRIORITY_RE.search(options)
            if prio_m:
                priority = int(prio_m.group(1))

            tags = []
            tags_m = self.WORKER_TAGS_RE.search(options)
            if tags_m:
                tags = [t.strip().strip('"').lstrip(':') for t in tags_m.group(1).split(',') if t.strip()]

            unique = ""
            unique_m = self.WORKER_UNIQUE_RE.search(options)
            if unique_m:
                unique = unique_m.group(1).strip()

            has_perform = bool(self.PERFORM_RE.search(content))
            has_timeout = bool(self.TIMEOUT_RE.search(content))

            result.workers.append(ObanWorkerInfo(
                name=module,
                queue=queue,
                max_attempts=max_attempts,
                priority=priority,
                tags=tags[:10],
                unique=unique[:80],
                has_perform=has_perform,
                has_timeout=has_timeout,
                file=file_path,
                line_number=line,
            ))

    def _extract_queues(self, content: str, file_path: str, result: ObanParseResult):
        """Extract Oban queue configuration."""
        for m in self.QUEUE_CONFIG_RE.finditer(content):
            queue_list = m.group(1)
            base_line = content[:m.start()].count('\n') + 1

            for q_m in self.QUEUE_ENTRY_RE.finditer(queue_list):
                name = q_m.group(1)
                limit = int(q_m.group(2)) if q_m.group(2) else 0

                result.queues.append(ObanQueueInfo(
                    name=name,
                    limit=limit,
                    file=file_path,
                    line_number=base_line,
                ))

    def _extract_plugins(self, content: str, file_path: str, result: ObanParseResult):
        """Extract Oban plugin configuration."""
        for m in self.PLUGIN_RE.finditer(content):
            name = m.group(1)
            options = (m.group(2) or "").strip()
            line = content[:m.start()].count('\n') + 1
            is_pro = "Pro" in name

            result.plugins.append(ObanPluginInfo(
                name=name,
                options=options[:80],
                is_pro=is_pro,
                file=file_path,
                line_number=line,
            ))

    def _extract_cron_schedules(self, content: str, file_path: str, result: ObanParseResult):
        """Extract Oban cron schedules."""
        for m in self.CRON_RE.finditer(content):
            schedule = m.group(1).strip('"')
            worker = m.group(2)
            args = (m.group(3) or "").strip()
            line = content[:m.start()].count('\n') + 1

            result.cron_schedules.append(ObanCronInfo(
                schedule=schedule,
                worker=worker,
                args=args[:80],
                file=file_path,
                line_number=line,
            ))

    def _extract_telemetry(self, content: str, file_path: str, result: ObanParseResult):
        """Extract Oban telemetry events."""
        for m in self.OBAN_TELEMETRY_RE.finditer(content):
            event = m.group(1)
            sub_event = m.group(2) or ""
            line = content[:m.start()].count('\n') + 1

            full_event = f"oban:{event}"
            if sub_event:
                full_event += f":{sub_event}"

            result.telemetry_events.append(ObanTelemetryInfo(
                event=full_event,
                file=file_path,
                line_number=line,
            ))

    def _extract_pro_features(self, content: str, file_path: str, result: ObanParseResult):
        """Extract Oban Pro feature usage."""
        pro_checks = [
            (self.PRO_BATCH_RE, "batch"),
            (self.PRO_CHUNK_RE, "chunk"),
            (self.PRO_WORKFLOW_RE, "workflow"),
            (self.PRO_RATE_LIMIT_RE, "rate_limiter"),
            (self.PRO_SMART_ENGINE_RE, "smart_engine"),
        ]

        for pattern, feature in pro_checks:
            m = pattern.search(content)
            if m:
                line = content[:m.start()].count('\n') + 1
                module = self._find_enclosing_module(content, m.start())
                result.pro_features.append(ObanProFeatureInfo(
                    feature=feature,
                    module=module,
                    file=file_path,
                    line_number=line,
                ))
