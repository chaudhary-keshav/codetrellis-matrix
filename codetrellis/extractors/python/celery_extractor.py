"""
CeleryExtractor - Extracts Celery task definitions from Python source code.

This extractor parses Celery tasks and extracts:
- @celery.task and @shared_task decorators
- Task names and bindings
- Task options (retry, rate_limit, etc.)
- Periodic tasks (beat schedule)
- Task queues

Part of CodeTrellis v2.0 - Python Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class CeleryTaskInfo:
    """Information about a Celery task."""
    name: str
    task_name: Optional[str] = None  # Explicit task name
    bind: bool = False
    base: Optional[str] = None
    max_retries: Optional[int] = None
    default_retry_delay: Optional[int] = None
    rate_limit: Optional[str] = None
    time_limit: Optional[int] = None
    soft_time_limit: Optional[int] = None
    ignore_result: bool = False
    queue: Optional[str] = None
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    is_async: bool = False
    line_number: int = 0


@dataclass
class CeleryBeatScheduleInfo:
    """Information about a periodic/beat task schedule."""
    name: str
    task: str
    schedule: str  # crontab, timedelta representation
    args: List[str] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    queue: Optional[str] = None


class CeleryExtractor:
    """
    Extracts Celery task definitions from source code.

    Handles:
    - @celery.task decorator
    - @app.task decorator
    - @shared_task decorator
    - Task options (bind, name, retry, etc.)
    - celery_beat_schedule definitions
    - Task signatures
    """

    # Task decorator patterns
    TASK_DECORATOR_PATTERN = re.compile(
        r'@(?:celery\.task|app\.task|shared_task)\s*(?:\(\s*([^)]*)\s*\))?',
        re.MULTILINE
    )

    # Function definition following decorator
    FUNCTION_PATTERN = re.compile(
        r'(async\s+)?def\s+(\w+)\s*\(\s*([^)]*)\s*\)(?:\s*->\s*([^:]+))?\s*:',
        re.MULTILINE
    )

    # Beat schedule pattern
    BEAT_SCHEDULE_PATTERN = re.compile(
        r'[\'"](\w+)[\'"]\s*:\s*\{([^}]+)\}',
        re.MULTILINE
    )

    # Crontab pattern
    CRONTAB_PATTERN = re.compile(
        r'crontab\s*\(\s*([^)]*)\s*\)'
    )

    # Timedelta pattern
    TIMEDELTA_PATTERN = re.compile(
        r'timedelta\s*\(\s*([^)]*)\s*\)'
    )

    def __init__(self):
        """Initialize the Celery extractor."""
        pass

    def extract(self, content: str) -> Dict[str, Any]:
        """
        Extract all Celery tasks and schedules from Python content.

        Args:
            content: Python source code

        Returns:
            Dict containing 'tasks' and 'schedules'
        """
        tasks = self._extract_tasks(content)
        schedules = self._extract_beat_schedules(content)

        return {
            'tasks': tasks,
            'schedules': schedules
        }

    def _extract_tasks(self, content: str) -> List[CeleryTaskInfo]:
        """Extract task definitions."""
        tasks = []

        for decorator_match in self.TASK_DECORATOR_PATTERN.finditer(content):
            decorator_args = decorator_match.group(1) or ""

            # Find the function definition after the decorator
            remaining_content = content[decorator_match.end():]
            func_match = self.FUNCTION_PATTERN.search(remaining_content)

            if not func_match:
                continue

            is_async = func_match.group(1) is not None
            func_name = func_match.group(2)
            params_str = func_match.group(3)
            return_type = func_match.group(4)

            # Parse task options from decorator
            task_name = self._extract_string_option(decorator_args, 'name')
            bind = self._extract_bool_option(decorator_args, 'bind')
            base = self._extract_string_option(decorator_args, 'base')
            max_retries = self._extract_int_option(decorator_args, 'max_retries')
            default_retry_delay = self._extract_int_option(decorator_args, 'default_retry_delay')
            rate_limit = self._extract_string_option(decorator_args, 'rate_limit')
            time_limit = self._extract_int_option(decorator_args, 'time_limit')
            soft_time_limit = self._extract_int_option(decorator_args, 'soft_time_limit')
            ignore_result = self._extract_bool_option(decorator_args, 'ignore_result')
            queue = self._extract_string_option(decorator_args, 'queue')

            # Parse parameters
            parameters = self._parse_parameters(params_str, bind)

            # Calculate line number
            line_number = content[:decorator_match.start()].count('\n') + 1

            task = CeleryTaskInfo(
                name=func_name,
                task_name=task_name,
                bind=bind,
                base=base,
                max_retries=max_retries,
                default_retry_delay=default_retry_delay,
                rate_limit=rate_limit,
                time_limit=time_limit,
                soft_time_limit=soft_time_limit,
                ignore_result=ignore_result,
                queue=queue,
                parameters=parameters,
                return_type=return_type.strip() if return_type else None,
                is_async=is_async,
                line_number=line_number
            )

            tasks.append(task)

        return tasks

    def _extract_beat_schedules(self, content: str) -> List[CeleryBeatScheduleInfo]:
        """Extract celery beat schedule definitions."""
        schedules = []

        # Look for beat_schedule or CELERYBEAT_SCHEDULE
        schedule_match = re.search(
            r'(?:beat_schedule|CELERYBEAT_SCHEDULE|CELERY_BEAT_SCHEDULE)\s*=\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}',
            content,
            re.MULTILINE
        )

        if not schedule_match:
            return schedules

        schedule_content = schedule_match.group(1)

        # Find each schedule entry
        for entry_match in self.BEAT_SCHEDULE_PATTERN.finditer(schedule_content):
            schedule_name = entry_match.group(1)
            entry_content = entry_match.group(2)

            # Extract task name
            task_match = re.search(r'[\'"]task[\'"]\s*:\s*[\'"]([^"\']+)[\'"]', entry_content)
            task = task_match.group(1) if task_match else "unknown"

            # Extract schedule
            schedule_str = self._extract_schedule(entry_content)

            # Extract args
            args_match = re.search(r'[\'"]args[\'"]\s*:\s*\(([^)]*)\)', entry_content)
            args = []
            if args_match:
                args = [a.strip().strip('"\'') for a in args_match.group(1).split(',') if a.strip()]

            # Extract queue
            queue_match = re.search(r'[\'"]queue[\'"]\s*:\s*[\'"]([^"\']+)[\'"]', entry_content)
            queue = queue_match.group(1) if queue_match else None

            schedule_info = CeleryBeatScheduleInfo(
                name=schedule_name,
                task=task,
                schedule=schedule_str,
                args=args,
                queue=queue
            )

            schedules.append(schedule_info)

        return schedules

    def _extract_schedule(self, entry_content: str) -> str:
        """Extract schedule representation from entry."""
        # Check for crontab
        crontab_match = self.CRONTAB_PATTERN.search(entry_content)
        if crontab_match:
            return f"crontab({crontab_match.group(1)})"

        # Check for timedelta
        timedelta_match = self.TIMEDELTA_PATTERN.search(entry_content)
        if timedelta_match:
            return f"timedelta({timedelta_match.group(1)})"

        # Check for numeric seconds
        seconds_match = re.search(r'[\'"]schedule[\'"]\s*:\s*(\d+)', entry_content)
        if seconds_match:
            return f"{seconds_match.group(1)}s"

        return "unknown"

    def _extract_string_option(self, args: str, option: str) -> Optional[str]:
        """Extract a string option from decorator arguments."""
        match = re.search(rf'{option}\s*=\s*[\'"]([^"\']+)[\'"]', args)
        if match:
            return match.group(1)
        return None

    def _extract_bool_option(self, args: str, option: str) -> bool:
        """Extract a boolean option from decorator arguments."""
        return f'{option}=True' in args or f'{option} = True' in args

    def _extract_int_option(self, args: str, option: str) -> Optional[int]:
        """Extract an integer option from decorator arguments."""
        match = re.search(rf'{option}\s*=\s*(\d+)', args)
        if match:
            return int(match.group(1))
        return None

    def _parse_parameters(self, params_str: str, bind: bool) -> List[str]:
        """Parse function parameters."""
        params = []

        for part in params_str.split(','):
            part = part.strip()
            if not part:
                continue

            # Skip self if bound task
            if bind and part == 'self':
                continue

            # Get parameter name
            if ':' in part:
                name = part.split(':')[0].strip()
            elif '=' in part:
                name = part.split('=')[0].strip()
            else:
                name = part

            params.append(name)

        return params

    def to_codetrellis_format(self, result: Dict[str, Any]) -> str:
        """
        Convert extracted Celery data to CodeTrellis format.

        Args:
            result: Dict with 'tasks' and 'schedules'

        Returns:
            CodeTrellis formatted string
        """
        lines = []

        # Add tasks
        tasks = result.get('tasks', [])
        if tasks:
            lines.append("[CELERY_TASKS]")

            for task in tasks:
                parts = [task.name]

                # Add task name if explicit
                if task.task_name:
                    parts.append(f"name:{task.task_name}")

                # Add flags
                flags = []
                if task.bind:
                    flags.append("bind")
                if task.is_async:
                    flags.append("async")
                if task.ignore_result:
                    flags.append("no_result")

                if flags:
                    parts.append(f"[{','.join(flags)}]")

                # Add parameters
                if task.parameters:
                    parts.append(f"({','.join(task.parameters)})")

                # Add return type
                if task.return_type:
                    parts.append(f"→{task.return_type}")

                # Add options
                opts = []
                if task.max_retries is not None:
                    opts.append(f"retries:{task.max_retries}")
                if task.rate_limit:
                    opts.append(f"rate:{task.rate_limit}")
                if task.time_limit:
                    opts.append(f"timeout:{task.time_limit}s")
                if task.queue:
                    opts.append(f"queue:{task.queue}")

                if opts:
                    parts.append(f"opts:[{','.join(opts)}]")

                lines.append("|".join(parts))

            lines.append("")

        # Add schedules
        schedules = result.get('schedules', [])
        if schedules:
            lines.append("[CELERY_BEAT_SCHEDULES]")

            for sched in schedules:
                parts = [
                    sched.name,
                    f"task:{sched.task}",
                    f"schedule:{sched.schedule}"
                ]

                if sched.args:
                    parts.append(f"args:({','.join(sched.args)})")

                if sched.queue:
                    parts.append(f"queue:{sched.queue}")

                lines.append("|".join(parts))

        return "\n".join(lines)


# Convenience function
def extract_celery_tasks(content: str) -> Dict[str, Any]:
    """Extract Celery tasks and schedules from Python content."""
    extractor = CeleryExtractor()
    return extractor.extract(content)
