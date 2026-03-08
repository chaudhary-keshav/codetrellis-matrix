"""
Tests for Enhanced Celery Parser.

Part of CodeTrellis v4.33 Celery Framework Support.
Tests cover:
- Task extraction (@shared_task, @app.task, @celery.task)
- Beat schedule extraction (crontab, timedelta)
- Signal handler extraction (task_prerun, task_postrun, worker_ready, etc.)
- Canvas primitive extraction (chain, group, chord, chunks)
- Result backend extraction
- Worker configuration extraction
- Queue definition extraction
- Route definition extraction
- App configuration extraction
- Framework detection
- Version detection
- is_celery_file detection
- to_codetrellis_format output
"""

import pytest
from codetrellis.celery_parser_enhanced import (
    EnhancedCeleryParser,
    CeleryParseResult,
    CelerySignalHandlerInfo,
    CeleryCanvasUsageInfo,
    CeleryResultBackendInfo,
    CeleryWorkerConfigInfo,
    CeleryQueueInfo,
    CeleryRouteInfo,
    CeleryAppConfigInfo,
)
from codetrellis.extractors.python.celery_extractor import (
    CeleryTaskInfo,
    CeleryBeatScheduleInfo,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedCeleryParser()


# ═══════════════════════════════════════════════════════════════════
# Task Extraction Tests (via base extractor)
# ═══════════════════════════════════════════════════════════════════

class TestCeleryTasks:

    def test_extract_shared_task(self, parser):
        """Test @shared_task extraction."""
        content = """
from celery import shared_task

@shared_task
def send_email(to, subject, body):
    pass
"""
        result = parser.parse(content, "tasks.py")
        assert len(result.tasks) >= 1
        assert result.tasks[0].name == "send_email"

    def test_extract_app_task(self, parser):
        """Test @app.task extraction."""
        content = """
from celery import Celery

app = Celery('myapp')

@app.task(bind=True, max_retries=3, rate_limit='10/m')
def process_data(self, data_id):
    pass
"""
        result = parser.parse(content, "tasks.py")
        assert len(result.tasks) >= 1
        task = result.tasks[0]
        assert task.name == "process_data"
        assert task.bind is True
        assert task.max_retries == 3

    def test_extract_async_task(self, parser):
        """Test async task extraction."""
        content = """
from celery import shared_task

@shared_task
async def async_process(data):
    pass
"""
        result = parser.parse(content)
        assert len(result.tasks) >= 1
        assert result.tasks[0].is_async is True

    def test_extract_task_with_options(self, parser):
        """Test task with all options."""
        content = """
from celery import shared_task

@shared_task(name='myapp.send_email', queue='email', time_limit=300, ignore_result=True)
def send_email(to, subject):
    pass
"""
        result = parser.parse(content)
        assert len(result.tasks) >= 1
        task = result.tasks[0]
        assert task.task_name == "myapp.send_email"
        assert task.queue == "email"
        assert task.time_limit == 300
        assert task.ignore_result is True


# ═══════════════════════════════════════════════════════════════════
# Beat Schedule Tests
# ═══════════════════════════════════════════════════════════════════

class TestCeleryBeat:

    def test_extract_beat_schedule(self, parser):
        """Test beat schedule extraction."""
        content = """
from celery.schedules import crontab

app.conf.beat_schedule = {
    'cleanup-every-night': {
        'task': 'myapp.tasks.cleanup',
        'schedule': crontab(hour=0, minute=0),
    },
    'report-every-hour': {
        'task': 'myapp.tasks.report',
        'schedule': 3600,
    },
}
"""
        result = parser.parse(content)
        assert len(result.schedules) >= 1
        assert result.total_schedules >= 1


# ═══════════════════════════════════════════════════════════════════
# Signal Handler Tests
# ═══════════════════════════════════════════════════════════════════

class TestCelerySignals:

    def test_signal_connect(self, parser):
        """Test signal.connect() extraction."""
        content = """
from celery.signals import task_prerun, task_postrun, worker_ready

def on_task_prerun(sender, **kwargs):
    print(f"Task {sender} starting")

task_prerun.connect(on_task_prerun)
worker_ready.connect(on_worker_ready)
"""
        result = parser.parse(content)
        assert len(result.signal_handlers) >= 2
        signals = {sh.signal_name for sh in result.signal_handlers}
        assert "task_prerun" in signals
        assert "worker_ready" in signals

    def test_signal_decorator(self, parser):
        """Test @signal.connect decorator."""
        content = """
from celery.signals import task_failure, task_success

@task_failure.connect
def handle_failure(sender, **kwargs):
    pass

@task_success.connect
def handle_success(sender, **kwargs):
    pass
"""
        result = parser.parse(content)
        assert len(result.signal_handlers) >= 2
        signals = {sh.signal_name for sh in result.signal_handlers}
        assert "task_failure" in signals
        assert "task_success" in signals


# ═══════════════════════════════════════════════════════════════════
# Canvas Tests
# ═══════════════════════════════════════════════════════════════════

class TestCeleryCanvas:

    def test_extract_chain(self, parser):
        """Test chain() extraction."""
        content = """
from celery import chain

workflow = chain(fetch_data.s(url), process_data.s(), save_results.s())
"""
        result = parser.parse(content)
        assert len(result.canvas_usages) >= 1
        cu = result.canvas_usages[0]
        assert cu.canvas_type == "chain"
        assert result.uses_canvas is True

    def test_extract_group(self, parser):
        """Test group() extraction."""
        content = """
from celery import group

batch = group(process_item.s(i) for i in range(10))
"""
        result = parser.parse(content)
        assert len(result.canvas_usages) >= 1
        assert result.canvas_usages[0].canvas_type == "group"

    def test_extract_chord(self, parser):
        """Test chord() extraction."""
        content = """
from celery import chord

result = chord(process_item.s(i) for i in items)(combine.s())
"""
        result = parser.parse(content)
        assert len(result.canvas_usages) >= 1
        assert result.canvas_usages[0].canvas_type == "chord"


# ═══════════════════════════════════════════════════════════════════
# Result Backend Tests
# ═══════════════════════════════════════════════════════════════════

class TestCeleryResultBackend:

    def test_extract_redis_backend(self, parser):
        """Test Redis result backend extraction."""
        content = """
app.conf.result_backend = 'redis://localhost:6379/0'
"""
        result = parser.parse(content)
        assert len(result.result_backends) >= 1
        rb = result.result_backends[0]
        assert rb.backend_type == "redis"

    def test_extract_database_backend(self, parser):
        """Test database result backend extraction."""
        content = """
CELERY_RESULT_BACKEND = 'db+postgresql://user:pass@localhost/celery_results'
"""
        result = parser.parse(content)
        assert len(result.result_backends) >= 1
        assert result.result_backends[0].backend_type == "database"

    def test_extract_rpc_backend(self, parser):
        """Test RPC result backend extraction."""
        content = """
app.conf.result_backend = 'rpc://'
"""
        result = parser.parse(content)
        assert len(result.result_backends) >= 1
        assert result.result_backends[0].backend_type == "rpc"


# ═══════════════════════════════════════════════════════════════════
# Worker Config Tests
# ═══════════════════════════════════════════════════════════════════

class TestCeleryWorkerConfig:

    def test_extract_worker_settings(self, parser):
        """Test worker configuration extraction."""
        content = """
app.conf.worker_concurrency = 4
app.conf.worker_prefetch_multiplier = 1
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.task_acks_late = True
app.conf.timezone = 'UTC'
"""
        result = parser.parse(content)
        settings = {wc.setting for wc in result.worker_configs}
        assert "worker_concurrency" in settings
        assert "worker_prefetch_multiplier" in settings
        assert "task_serializer" in settings
        assert "task_acks_late" in settings
        assert "timezone" in settings

    def test_extract_legacy_settings(self, parser):
        """Test legacy CELERY_ prefix settings."""
        content = """
CELERYD_CONCURRENCY = 8
CELERY_TASK_SERIALIZER = 'json'
CELERY_ALWAYS_EAGER = True
"""
        result = parser.parse(content)
        settings = {wc.setting for wc in result.worker_configs}
        assert "worker_concurrency" in settings
        assert "task_serializer" in settings
        assert "task_always_eager" in settings


# ═══════════════════════════════════════════════════════════════════
# Queue Tests
# ═══════════════════════════════════════════════════════════════════

class TestCeleryQueues:

    def test_extract_queues(self, parser):
        """Test queue definition extraction."""
        content = """
from kombu import Exchange, Queue

task_queues = [
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('priority', Exchange('priority'), routing_key='priority.#'),
]
"""
        result = parser.parse(content)
        assert len(result.queues) >= 2
        names = [q.name for q in result.queues]
        assert "default" in names
        assert "priority" in names


# ═══════════════════════════════════════════════════════════════════
# App Config Tests
# ═══════════════════════════════════════════════════════════════════

class TestCeleryAppConfig:

    def test_extract_app_config(self, parser):
        """Test Celery app instantiation extraction."""
        content = """
from celery import Celery

app = Celery('myapp', broker='redis://localhost:6379/0')
"""
        result = parser.parse(content)
        assert len(result.app_configs) >= 1
        ac = result.app_configs[0]
        assert ac.app_name == "myapp"
        assert ac.broker_type == "redis"

    def test_extract_app_with_amqp(self, parser):
        """Test Celery app with AMQP broker."""
        content = """
from celery import Celery

celery_app = Celery('tasks', broker='amqp://guest:guest@localhost//')
"""
        result = parser.parse(content)
        assert len(result.app_configs) >= 1
        assert result.app_configs[0].broker_type == "amqp"

    def test_extract_standalone_broker_url(self, parser):
        """Test standalone broker_url configuration."""
        content = """
from celery import Celery

app = Celery('myapp')
app.conf.broker_url = 'redis://localhost:6379/0'
"""
        result = parser.parse(content)
        assert len(result.app_configs) >= 1


# ═══════════════════════════════════════════════════════════════════
# Framework Detection & Version Tests
# ═══════════════════════════════════════════════════════════════════

class TestCeleryDetection:

    def test_detect_frameworks(self, parser):
        """Test framework detection."""
        content = """
from celery import Celery, chain, group
from celery.signals import task_prerun
from celery.schedules import crontab
"""
        result = parser.parse(content)
        assert "celery" in result.detected_frameworks
        assert "celery.canvas" in result.detected_frameworks
        assert "celery.signals" in result.detected_frameworks
        assert "celery.beat" in result.detected_frameworks

    def test_detect_kombu(self, parser):
        """Test Kombu detection."""
        content = """
from kombu import Exchange, Queue
"""
        result = parser.parse(content)
        assert "kombu" in result.detected_frameworks

    def test_detect_django_celery(self, parser):
        """Test Django-Celery detection."""
        content = """
from django_celery_beat.models import PeriodicTask
"""
        result = parser.parse(content)
        assert "django_celery" in result.detected_frameworks

    def test_version_detection(self, parser):
        """Test version feature detection."""
        content = """
from celery import Celery, shared_task, chain, group
"""
        result = parser.parse(content)
        # shared_task = 3.1, chain/group = 3.0
        assert result.celery_version == "3.1"

    def test_is_celery_file(self, parser):
        """Test Celery file detection."""
        content = """
from celery import shared_task

@shared_task
def my_task():
    pass
"""
        assert parser.is_celery_file(content) is True

    def test_not_celery_file(self, parser):
        """Test non-Celery file."""
        content = """
def hello():
    print("Hello")
"""
        assert parser.is_celery_file(content) is False

    def test_celery_config_file(self, parser):
        """Test Celery config file by name."""
        content = "BROKER_URL = 'redis://'"
        assert parser.is_celery_file(content, "celery.py") is True

    def test_beat_schedule_file(self, parser):
        """Test beat schedule file detection."""
        content = """
beat_schedule = {
    'task-1': {'task': 'do_something'},
}
"""
        assert parser.is_celery_file(content) is True


# ═══════════════════════════════════════════════════════════════════
# File Classification Tests
# ═══════════════════════════════════════════════════════════════════

class TestCeleryClassification:

    def test_classify_app(self, parser):
        """Test app file classification."""
        content = "app = Celery('myapp')"
        result = parser.parse(content, "celery.py")
        assert result.file_type == "app"

    def test_classify_task(self, parser):
        """Test task file classification."""
        content = "@shared_task\ndef my_task(): pass"
        result = parser.parse(content, "tasks.py")
        assert result.file_type == "task"

    def test_classify_config(self, parser):
        """Test config file classification."""
        result = parser.parse("BROKER_URL = 'redis://'", "celeryconfig.py")
        assert result.file_type == "app"

    def test_classify_test(self, parser):
        """Test test file classification."""
        result = parser.parse("def test_task(): pass", "test_tasks.py")
        assert result.file_type == "test"


# ═══════════════════════════════════════════════════════════════════
# CodeTrellis Format Tests
# ═══════════════════════════════════════════════════════════════════

class TestCeleryFormat:

    def test_to_codetrellis_format_tasks(self, parser):
        """Test CodeTrellis format includes tasks."""
        content = """
from celery import shared_task

@shared_task
def my_task(data):
    pass
"""
        result = parser.parse(content, "tasks.py")
        output = parser.to_codetrellis_format(result)
        assert "CELERY_TASKS" in output

    def test_to_codetrellis_format_signals(self, parser):
        """Test CodeTrellis format includes signals."""
        content = """
from celery.signals import task_prerun

task_prerun.connect(on_prerun)
"""
        result = parser.parse(content)
        output = parser.to_codetrellis_format(result)
        assert "CELERY_SIGNALS" in output

    def test_to_codetrellis_format_empty(self, parser):
        """Test CodeTrellis format for empty file."""
        result = parser.parse("x = 1")
        output = parser.to_codetrellis_format(result)
        assert "CELERY_TASKS" not in output

    def test_parse_empty(self, parser):
        """Test parsing empty content."""
        result = parser.parse("")
        assert result.total_tasks == 0
        assert result.total_schedules == 0


# ═══════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestCeleryIntegration:

    def test_full_celery_project(self, parser):
        """Test parsing a full Celery project file."""
        content = """
from celery import Celery, chain, group, shared_task
from celery.signals import task_prerun, task_failure, worker_ready
from celery.schedules import crontab
from kombu import Exchange, Queue

app = Celery('myapp', broker='redis://localhost:6379/0')

app.conf.result_backend = 'redis://localhost:6379/1'
app.conf.worker_concurrency = 4
app.conf.task_serializer = 'json'
app.conf.timezone = 'UTC'
app.conf.task_acks_late = True

task_queues = [
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('high_priority', Exchange('high_priority'), routing_key='high.#'),
]

app.conf.beat_schedule = {
    'cleanup-every-night': {
        'task': 'myapp.tasks.cleanup',
        'schedule': crontab(hour=0, minute=0),
    },
}

@shared_task(bind=True, max_retries=3)
def process_data(self, data_id):
    pass

@shared_task
def send_notification(user_id, message):
    pass

workflow = chain(process_data.s(1), send_notification.s("done"))

task_prerun.connect(on_prerun)
task_failure.connect(on_failure)
worker_ready.connect(on_ready)
"""
        result = parser.parse(content, "celery_app.py")

        # Tasks
        assert result.total_tasks >= 2
        # Beat
        assert result.total_schedules >= 1
        # Signals
        assert len(result.signal_handlers) >= 3
        # Canvas
        assert len(result.canvas_usages) >= 1
        assert result.uses_canvas is True
        # Result backend
        assert len(result.result_backends) >= 1
        # Worker config
        assert len(result.worker_configs) >= 3
        # Queues
        assert len(result.queues) >= 2
        # App config
        assert len(result.app_configs) >= 1
        assert result.app_configs[0].broker_type == "redis"
        # File type
        assert result.file_type == "app"
        # Version
        assert result.celery_version != ""

        # Format
        output = parser.to_codetrellis_format(result)
        assert "CELERY_TASKS" in output
        assert "CELERY_SIGNALS" in output
        assert "CELERY_CANVAS" in output
        assert "CELERY_APP" in output
