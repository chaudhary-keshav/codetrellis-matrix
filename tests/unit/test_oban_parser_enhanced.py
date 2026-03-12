"""
Tests for EnhancedObanParser — workers, queues, plugins, cron schedules,
telemetry events, Pro features, version detection.

Part of CodeTrellis v5.5 Oban Framework Support.
"""

import pytest
from codetrellis.oban_parser_enhanced import (
    EnhancedObanParser,
    ObanParseResult,
)


@pytest.fixture
def parser():
    return EnhancedObanParser()


class TestWorkers:
    """Tests for Oban worker extraction."""

    def test_parse_basic_worker(self, parser):
        code = '''
defmodule MyApp.Workers.EmailWorker do
  use Oban.Worker, queue: :mailers, max_attempts: 5

  @impl Oban.Worker
  def perform(%Oban.Job{args: %{"to" => to, "subject" => subject}}) do
    MyApp.Mailer.send(to, subject)
    :ok
  end
end
'''
        result = parser.parse(code, "lib/my_app/workers/email_worker.ex")
        assert len(result.workers) >= 1
        w = result.workers[0]
        assert "EmailWorker" in w.name

    def test_parse_worker_with_options(self, parser):
        code = '''
defmodule MyApp.Workers.ImportWorker do
  use Oban.Worker,
    queue: :imports,
    max_attempts: 3,
    priority: 1,
    unique: [period: 300],
    tags: ["import", "heavy"]

  @impl Oban.Worker
  def perform(%Oban.Job{args: args}) do
    MyApp.Importer.run(args)
  end

  @impl Oban.Worker
  def timeout(%Oban.Job{}), do: :timer.minutes(30)
end
'''
        result = parser.parse(code, "lib/my_app/workers/import_worker.ex")
        assert len(result.workers) >= 1

    def test_parse_worker_with_unique(self, parser):
        code = '''
defmodule MyApp.Workers.DedupWorker do
  use Oban.Worker,
    queue: :default,
    unique: [period: 60, fields: [:args, :queue], states: [:available, :scheduled]]

  @impl Oban.Worker
  def perform(%Oban.Job{args: args}) do
    :ok
  end
end
'''
        result = parser.parse(code, "lib/my_app/workers/dedup_worker.ex")
        assert len(result.workers) >= 1

    def test_parse_multiple_workers(self, parser):
        code = '''
defmodule MyApp.Workers.NotificationWorker do
  use Oban.Worker, queue: :notifications

  @impl Oban.Worker
  def perform(%Oban.Job{args: %{"type" => "push"} = args}) do
    MyApp.Push.send(args)
  end

  def perform(%Oban.Job{args: %{"type" => "sms"} = args}) do
    MyApp.SMS.send(args)
  end
end
'''
        result = parser.parse(code, "lib/my_app/workers/notification_worker.ex")
        assert len(result.workers) >= 1


class TestQueues:
    """Tests for Oban queue configuration extraction."""

    def test_parse_queue_config(self, parser):
        code = '''
defmodule MyApp.Application do
  def start(_type, _args) do
    children = [
      {Oban, queues: [default: 10, mailers: 5, imports: 2, heavy: 1]}
    ]
    Supervisor.start_link(children, strategy: :one_for_one)
  end
end
'''
        result = parser.parse(code, "lib/my_app/application.ex")
        assert len(result.queues) >= 1

    def test_parse_runtime_config(self, parser):
        code = '''
# config/runtime.exs
import Config

config :my_app, Oban,
  repo: MyApp.Repo,
  queues: [default: 10, mailers: 5, events: 20],
  plugins: [
    {Oban.Plugins.Pruner, max_age: 60 * 60 * 24 * 7},
    Oban.Plugins.Stager
  ]
'''
        result = parser.parse(code, "config/runtime.exs")
        assert len(result.queues) >= 1 or len(result.plugins) >= 1


class TestPlugins:
    """Tests for Oban plugin extraction."""

    def test_parse_plugins(self, parser):
        code = '''
defmodule MyApp.Application do
  def start(_type, _args) do
    children = [
      {Oban,
       repo: MyApp.Repo,
       plugins: [
         {Oban.Plugins.Pruner, max_age: 60 * 60 * 24 * 14},
         Oban.Plugins.Stager,
         {Oban.Plugins.Lifeline, rescue_after: :timer.minutes(30)}
       ]}
    ]
    Supervisor.start_link(children, strategy: :one_for_one)
  end
end
'''
        result = parser.parse(code, "lib/my_app/application.ex")
        assert len(result.plugins) >= 1


class TestCronSchedules:
    """Tests for Oban cron schedule extraction."""

    def test_parse_cron(self, parser):
        code = '''
config :my_app, Oban,
  repo: MyApp.Repo,
  plugins: [
    {Oban.Plugins.Cron,
     crontab: [
       {"0 * * * *", MyApp.Workers.HourlySync},
       {"0 0 * * *", MyApp.Workers.DailyReport},
       {"*/5 * * * *", MyApp.Workers.HealthCheck, args: %{type: "basic"}},
       {"@daily", MyApp.Workers.Cleanup}
     ]}
  ]
'''
        result = parser.parse(code, "config/config.exs")
        assert len(result.cron_schedules) >= 1

    def test_parse_cron_with_options(self, parser):
        code = '''
config :my_app, Oban,
  plugins: [
    {Oban.Plugins.Cron,
     crontab: [
       {"0 2 * * *", MyApp.Workers.NightlyJob, queue: :heavy, max_attempts: 1}
     ]}
  ]
'''
        result = parser.parse(code, "config/config.exs")
        assert len(result.cron_schedules) >= 1


class TestTelemetry:
    """Tests for Oban telemetry event extraction."""

    def test_parse_telemetry_handler(self, parser):
        code = '''
defmodule MyApp.ObanTelemetry do
  def attach do
    :telemetry.attach_many(
      "oban-logger",
      [
        [:oban, :job, :start],
        [:oban, :job, :stop],
        [:oban, :job, :exception]
      ],
      &handle_event/4,
      nil
    )
  end

  def handle_event([:oban, :job, :stop], measure, meta, _) do
    Logger.info("Job #{meta.worker} completed in #{measure.duration}")
  end

  def handle_event([:oban, :job, :exception], _measure, meta, _) do
    Logger.error("Job #{meta.worker} failed: #{inspect(meta.error)}")
  end
end
'''
        result = parser.parse(code, "lib/my_app/oban_telemetry.ex")
        assert len(result.telemetry_events) >= 1


class TestProFeatures:
    """Tests for Oban Pro feature extraction."""

    def test_parse_batch_worker(self, parser):
        code = '''
defmodule MyApp.Workers.BatchImport do
  use Oban.Pro.Workers.Batch

  @impl true
  def process(%Job{args: args}) do
    :ok
  end
end
'''
        result = parser.parse(code, "lib/workers/batch_import.ex")
        assert len(result.pro_features) >= 1

    def test_parse_workflow(self, parser):
        code = '''
defmodule MyApp.Workflows.Onboarding do
  use Oban.Pro.Workers.Workflow

  def new_workflow(user_id) do
    new()
    |> add(:welcome, MyApp.Workers.SendWelcome.new(%{user_id: user_id}))
    |> add(:setup, MyApp.Workers.SetupAccount.new(%{user_id: user_id}), deps: [:welcome])
    |> add(:notify, MyApp.Workers.NotifyTeam.new(%{user_id: user_id}), deps: [:setup])
  end
end
'''
        result = parser.parse(code, "lib/workflows/onboarding.ex")
        assert len(result.pro_features) >= 1

    def test_parse_chunk_worker(self, parser):
        code = '''
defmodule MyApp.Workers.BulkNotify do
  use Oban.Pro.Workers.Chunk, size: 100, timeout: 1000

  @impl true
  def process(jobs) do
    jobs
    |> Enum.map(& &1.args)
    |> MyApp.Notifications.send_batch()
    :ok
  end
end
'''
        result = parser.parse(code, "lib/workers/bulk_notify.ex")
        assert len(result.pro_features) >= 1


class TestVersionDetection:
    """Tests for Oban version detection."""

    def test_detect_oban(self, parser):
        code = '''
defmodule MyApp.Worker do
  use Oban.Worker
  def perform(%Oban.Job{}), do: :ok
end
'''
        result = parser.parse(code, "lib/worker.ex")
        assert result.detected_frameworks or result.workers


class TestEdgeCases:
    """Tests for edge cases."""

    def test_parse_empty_file(self, parser):
        result = parser.parse("", "empty.ex")
        assert isinstance(result, ObanParseResult)
        assert len(result.workers) == 0

    def test_non_oban_file(self, parser):
        code = '''
defmodule MyApp.Math do
  def add(a, b), do: a + b
end
'''
        result = parser.parse(code, "lib/math.ex")
        assert len(result.workers) == 0
        assert len(result.queues) == 0

    def test_complex_oban_setup(self, parser):
        code = '''
defmodule MyApp.Application do
  use Application

  def start(_type, _args) do
    children = [
      MyApp.Repo,
      {Oban,
       repo: MyApp.Repo,
       queues: [default: 10, mailers: 5, imports: 2],
       plugins: [
         {Oban.Plugins.Pruner, max_age: 60 * 60 * 24 * 7},
         {Oban.Plugins.Cron,
          crontab: [
            {"@hourly", MyApp.Workers.SyncWorker},
            {"@daily", MyApp.Workers.ReportWorker}
          ]},
         Oban.Plugins.Stager,
         {Oban.Plugins.Lifeline, rescue_after: :timer.minutes(60)}
       ]}
    ]

    opts = [strategy: :one_for_one, name: MyApp.Supervisor]
    Supervisor.start_link(children, opts)
  end
end
'''
        result = parser.parse(code, "lib/my_app/application.ex")
        assert len(result.queues) >= 1 or len(result.plugins) >= 1
