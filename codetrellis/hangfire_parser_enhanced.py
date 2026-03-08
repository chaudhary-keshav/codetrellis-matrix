"""
Enhanced Hangfire Parser for CodeTrellis.

Extracts Hangfire-specific concepts: background jobs, recurring jobs,
job filters, dashboard configurations, storage backends.

Supports Hangfire 1.7 through 1.8+.
Part of CodeTrellis v4.96 (Session 76)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path

from codetrellis.extractors.hangfire import HangfireJobExtractor


@dataclass
class HangfireParseResult:
    """Result of Hangfire-enhanced parsing."""
    # Jobs
    jobs: List[Dict[str, Any]] = field(default_factory=list)
    recurring_jobs: List[Dict[str, Any]] = field(default_factory=list)

    # Filters
    job_filters: List[Dict[str, Any]] = field(default_factory=list)

    # Config
    dashboards: List[Dict[str, Any]] = field(default_factory=list)
    storage: List[Dict[str, Any]] = field(default_factory=list)

    # Aggregates
    total_jobs: int = 0
    total_recurring: int = 0
    total_filters: int = 0

    # Framework metadata
    detected_frameworks: List[str] = field(default_factory=list)
    detected_version: str = ""
    file_type: str = ""  # job-definition, configuration, filter


class EnhancedHangfireParser:
    """Parser for Hangfire concepts in C# files."""

    FRAMEWORK_PATTERNS: Dict[str, str] = {
        # Core
        'hangfire': r'using\s+Hangfire\b',
        'hangfire_core': r'using\s+Hangfire\.Core\b',
        'hangfire_server': r'using\s+Hangfire\.Server\b',
        'hangfire_dashboard': r'using\s+Hangfire\.Dashboard\b',
        'hangfire_states': r'using\s+Hangfire\.States\b',
        'hangfire_annotations': r'using\s+Hangfire\.Annotations\b',

        # Storage
        'hangfire_sqlserver': r'using\s+Hangfire\.SqlServer\b',
        'hangfire_redis': r'using\s+Hangfire\.Pro\.Redis\b',
        'hangfire_postgresql': r'using\s+Hangfire\.PostgreSql\b',
        'hangfire_mongo': r'using\s+Hangfire\.Mongo\b',

        # Job types
        'background_job': r'\bBackgroundJob\.(Enqueue|Schedule|ContinueJobWith|Delete)\b',
        'recurring_job': r'\bRecurringJob\.(AddOrUpdate|RemoveIfExists|TriggerJob)\b',
        'batch_job': r'\bBatchJob\.Start\w*\b',

        # Configuration
        'use_hangfire': r'\.UseHangfire\w*\(',
        'add_hangfire': r'\.AddHangfire\s*\(',
        'add_hangfire_server': r'\.AddHangfireServer\s*\(',

        # Filters
        'automatic_retry': r'\[AutomaticRetry\b',
        'queue_attribute': r'\[Queue\s*\(',
        'disable_concurrent': r'\[DisableConcurrentExecution\b',
    }

    VERSION_FEATURES: Dict[str, List[str]] = {
        '1.7': ['BackgroundJob', 'RecurringJob', 'IServerFilter', 'SqlServerStorage'],
        '1.7.25': ['AsyncFilters', 'DisableConcurrentExecution'],
        '1.8': ['AddHangfire', 'AddHangfireServer', 'UseRecommendedSerializerSettings'],
    }

    def __init__(self):
        """Initialize extractors."""
        self.job_extractor = HangfireJobExtractor()

    def is_hangfire_file(self, content: str, file_path: str = "") -> bool:
        """Check if file contains Hangfire code."""
        if not content:
            return False
        indicators = [
            r'using\s+Hangfire\b',
            r'\bBackgroundJob\.',
            r'\bRecurringJob\.',
            r'\.AddHangfire\s*\(',
            r'\.UseHangfireDashboard\s*\(',
            r'\bIServerFilter\b',
            r'\bIClientFilter\b',
            r'\bJobFilterAttribute\b',
        ]
        return any(re.search(p, content) for p in indicators)

    def parse(self, content: str, file_path: str = "") -> HangfireParseResult:
        """Parse Hangfire concepts from C# file."""
        result = HangfireParseResult()

        if not content or not self.is_hangfire_file(content, file_path):
            return result

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)
        result.detected_version = self._detect_version(content)
        result.file_type = self._classify_file(content, file_path)

        # Extract with job extractor
        job_data = self.job_extractor.extract(content, file_path)

        result.jobs = [self._job_to_dict(j) for j in job_data.get('jobs', [])]
        result.recurring_jobs = [self._recurring_to_dict(r) for r in job_data.get('recurring_jobs', [])]
        result.job_filters = [self._filter_to_dict(f) for f in job_data.get('job_filters', [])]
        result.dashboards = [self._dashboard_to_dict(d) for d in job_data.get('dashboards', [])]
        result.storage = [self._storage_to_dict(s) for s in job_data.get('storage', [])]

        # Aggregates
        result.total_jobs = len(result.jobs)
        result.total_recurring = len(result.recurring_jobs)
        result.total_filters = len(result.job_filters)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect Hangfire-related frameworks."""
        found = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if re.search(pattern, content):
                found.append(name)
        return found

    def _detect_version(self, content: str) -> str:
        """Detect Hangfire version from usage patterns."""
        if re.search(r'\.AddHangfireServer\s*\(', content):
            return "1.8"
        if re.search(r'\[DisableConcurrentExecution\b', content):
            return "1.7.25"
        return "1.7"

    def _classify_file(self, content: str, file_path: str) -> str:
        """Classify file type."""
        if re.search(r'\.AddHangfire\s*\(|\.UseHangfire', content):
            return "configuration"
        if re.search(r'class\s+\w+\s*:\s*(IServerFilter|IClientFilter|JobFilterAttribute)', content):
            return "filter"
        if re.search(r'\bBackgroundJob\.|RecurringJob\.', content):
            return "job-definition"
        return "usage"

    def _job_to_dict(self, j) -> Dict[str, Any]:
        return {
            'name': j.name, 'job_type': j.job_type, 'method_name': j.method_name,
            'queue': j.queue, 'file': j.file, 'line': j.line_number,
        }

    def _recurring_to_dict(self, r) -> Dict[str, Any]:
        return {
            'job_id': r.job_id, 'cron_expression': r.cron_expression,
            'queue': r.queue, 'file': r.file, 'line': r.line_number,
        }

    def _filter_to_dict(self, f) -> Dict[str, Any]:
        return {
            'name': f.name, 'filter_type': f.filter_type,
            'file': f.file, 'line': f.line_number,
        }

    def _dashboard_to_dict(self, d) -> Dict[str, Any]:
        return {
            'path': d.path, 'has_authorization': d.has_authorization,
            'authorization_filter': d.authorization_filter,
            'file': d.file, 'line': d.line_number,
        }

    def _storage_to_dict(self, s) -> Dict[str, Any]:
        return {
            'storage_type': s.storage_type,
            'file': s.file, 'line': s.line_number,
        }
