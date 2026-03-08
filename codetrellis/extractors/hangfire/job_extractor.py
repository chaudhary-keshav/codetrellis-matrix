"""
Hangfire Job Extractor.

Extracts background job definitions, recurring jobs, continuations,
job filters, dashboard configs, and storage configurations.

Supports Hangfire 1.7 through 1.8+.
Part of CodeTrellis v4.96
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class HangfireJobInfo:
    """Information about a Hangfire background job."""
    name: str = ""
    job_type: str = ""  # fire-and-forget, delayed, recurring, continuation, batch
    method_name: str = ""
    queue: str = ""
    retry_count: int = 0
    has_timeout: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class HangfireRecurringJobInfo:
    """Information about a recurring job."""
    job_id: str = ""
    cron_expression: str = ""
    method_name: str = ""
    queue: str = ""
    time_zone: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class HangfireJobFilterInfo:
    """Information about a job filter."""
    name: str = ""
    filter_type: str = ""  # client, server, elect-state, apply-state
    file: str = ""
    line_number: int = 0


@dataclass
class HangfireDashboardInfo:
    """Dashboard configuration."""
    path: str = ""
    has_authorization: bool = False
    authorization_filter: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class HangfireStorageInfo:
    """Storage backend configuration."""
    storage_type: str = ""  # sql-server, redis, postgresql, memory, mongo
    connection_string_ref: str = ""
    file: str = ""
    line_number: int = 0


class HangfireJobExtractor:
    """Extracts Hangfire job definitions and configurations."""

    # Fire-and-forget
    ENQUEUE_PATTERN = re.compile(
        r'BackgroundJob\.Enqueue\s*(?:<\s*(\w+)\s*>)?\s*\(\s*(?:\w+\s*=>\s*\w+\.)?(\w+)',
        re.MULTILINE
    )

    # Delayed jobs
    SCHEDULE_PATTERN = re.compile(
        r'BackgroundJob\.Schedule\s*(?:<\s*(\w+)\s*>)?\s*\(',
        re.MULTILINE
    )

    # Continuations
    CONTINUE_PATTERN = re.compile(
        r'BackgroundJob\.ContinueJobWith\s*(?:<\s*(\w+)\s*>)?\s*\(',
        re.MULTILINE
    )

    # Recurring jobs
    RECURRING_PATTERN = re.compile(
        r'RecurringJob\.AddOrUpdate\s*(?:<\s*(\w+)\s*>)?\s*\(\s*'
        r'(?:"([^"]*)")?\s*,',
        re.MULTILINE
    )

    # Cron expression in recurring job
    CRON_PATTERN = re.compile(
        r'(?:Cron\.(\w+)\s*\(\s*\)|"([^"]*\s+[^"]*\s+[^"]*)")',
        re.MULTILINE
    )

    # Queue attribute
    QUEUE_PATTERN = re.compile(
        r'\[Queue\s*\(\s*"([^"]*)"\s*\)\]',
        re.MULTILINE
    )

    # AutomaticRetry attribute
    RETRY_PATTERN = re.compile(
        r'\[AutomaticRetry\s*\(\s*Attempts\s*=\s*(\d+)',
        re.MULTILINE
    )

    # Job filter classes
    JOB_FILTER_PATTERN = re.compile(
        r'class\s+(\w+)\s*:\s*(IClientFilter|IServerFilter|IElectStateFilter|IApplyStateFilter|JobFilterAttribute)\b',
        re.MULTILINE
    )

    FILTER_TYPE_MAP = {
        'IClientFilter': 'client',
        'IServerFilter': 'server',
        'IElectStateFilter': 'elect-state',
        'IApplyStateFilter': 'apply-state',
        'JobFilterAttribute': 'attribute',
    }

    # Dashboard
    DASHBOARD_PATTERN = re.compile(
        r'\.UseHangfireDashboard\s*\(\s*(?:"([^"]*)")?',
        re.MULTILINE
    )

    # Dashboard authorization filter
    DASHBOARD_AUTH_PATTERN = re.compile(
        r'class\s+(\w+)\s*:\s*IDashboardAuthorizationFilter\b',
        re.MULTILINE
    )

    # Storage patterns
    STORAGE_PATTERNS = {
        'sql-server': re.compile(r'\.UseSqlServerStorage\s*\(', re.MULTILINE),
        'redis': re.compile(r'\.UseRedisStorage\s*\(', re.MULTILINE),
        'postgresql': re.compile(r'\.UsePostgreSqlStorage\s*\(', re.MULTILINE),
        'memory': re.compile(r'\.UseMemoryStorage\s*\(', re.MULTILINE),
        'mongo': re.compile(r'\.UseMongoStorage\s*\(', re.MULTILINE),
    }

    # Hangfire server config
    SERVER_PATTERN = re.compile(
        r'\.UseHangfireServer\s*\(',
        re.MULTILINE
    )

    # Batch jobs (Hangfire.Pro)
    BATCH_PATTERN = re.compile(
        r'BatchJob\.Start\w*\s*\(',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Hangfire jobs and configurations."""
        result: Dict[str, Any] = {
            'jobs': [],
            'recurring_jobs': [],
            'job_filters': [],
            'dashboards': [],
            'storage': [],
        }

        if not content or not content.strip():
            return result

        # Fire-and-forget jobs
        for match in self.ENQUEUE_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['jobs'].append(HangfireJobInfo(
                name=match.group(1) or "",
                job_type="fire-and-forget",
                method_name=match.group(2) or "",
                file=file_path,
                line_number=line,
            ))

        # Delayed jobs
        for match in self.SCHEDULE_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['jobs'].append(HangfireJobInfo(
                name=match.group(1) or "",
                job_type="delayed",
                file=file_path,
                line_number=line,
            ))

        # Continuation jobs
        for match in self.CONTINUE_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['jobs'].append(HangfireJobInfo(
                name=match.group(1) or "",
                job_type="continuation",
                file=file_path,
                line_number=line,
            ))

        # Batch jobs
        for match in self.BATCH_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            result['jobs'].append(HangfireJobInfo(
                job_type="batch",
                file=file_path,
                line_number=line,
            ))

        # Recurring jobs
        for match in self.RECURRING_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            job_id = match.group(2) or ""
            # Try to find cron expression nearby
            after = content[match.end():match.end() + 300]
            cron_match = self.CRON_PATTERN.search(after)
            cron = ""
            if cron_match:
                cron = cron_match.group(1) or cron_match.group(2) or ""

            result['recurring_jobs'].append(HangfireRecurringJobInfo(
                job_id=job_id,
                cron_expression=cron,
                file=file_path,
                line_number=line,
            ))

        # Job filters
        for match in self.JOB_FILTER_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            base_type = match.group(2)
            result['job_filters'].append(HangfireJobFilterInfo(
                name=match.group(1),
                filter_type=self.FILTER_TYPE_MAP.get(base_type, 'unknown'),
                file=file_path,
                line_number=line,
            ))

        # Dashboard
        for match in self.DASHBOARD_PATTERN.finditer(content):
            line = content[:match.start()].count('\n') + 1
            path = match.group(1) or "/hangfire"
            # Check for authorization
            has_auth = bool(self.DASHBOARD_AUTH_PATTERN.search(content))
            auth_filter = ""
            auth_match = self.DASHBOARD_AUTH_PATTERN.search(content)
            if auth_match:
                auth_filter = auth_match.group(1)

            result['dashboards'].append(HangfireDashboardInfo(
                path=path,
                has_authorization=has_auth,
                authorization_filter=auth_filter,
                file=file_path,
                line_number=line,
            ))

        # Storage
        for storage_type, pattern in self.STORAGE_PATTERNS.items():
            match = pattern.search(content)
            if match:
                line = content[:match.start()].count('\n') + 1
                result['storage'].append(HangfireStorageInfo(
                    storage_type=storage_type,
                    file=file_path,
                    line_number=line,
                ))

        return result
