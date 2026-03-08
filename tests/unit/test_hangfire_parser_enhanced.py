"""
Tests for Hangfire Enhanced Parser.

Tests background jobs, recurring jobs, filters, dashboard, storage detection.
Part of CodeTrellis v4.96 (Session 76)
"""

import pytest
from codetrellis.hangfire_parser_enhanced import EnhancedHangfireParser, HangfireParseResult


# ── Fixtures ─────────────────────────────────────────────

SAMPLE_JOBS = '''
using Hangfire;

public class JobService
{
    public void EnqueueEmailJob()
    {
        BackgroundJob.Enqueue<IEmailService>(svc => svc.SendWelcomeEmail("user@example.com"));
    }

    public void ScheduleReminder()
    {
        BackgroundJob.Schedule<IReminderService>(svc => svc.SendReminder(), TimeSpan.FromHours(24));
    }

    public void ContinueWithReport(string parentJobId)
    {
        BackgroundJob.ContinueJobWith<IReportService>(parentJobId, svc => svc.GenerateReport());
    }
}
'''

SAMPLE_RECURRING = '''
using Hangfire;

public static class RecurringJobSetup
{
    public static void Configure()
    {
        RecurringJob.AddOrUpdate<ICleanupService>(
            "daily-cleanup",
            svc => svc.CleanupOldData(),
            Cron.Daily()
        );

        RecurringJob.AddOrUpdate<IReportService>(
            "weekly-report",
            svc => svc.GenerateWeeklyReport(),
            "0 8 * * MON"
        );
    }
}
'''

SAMPLE_FILTER = '''
using Hangfire;
using Hangfire.Server;
using Hangfire.States;

public class LoggingJobFilter : IServerFilter
{
    public void OnPerforming(PerformingContext context) { }
    public void OnPerformed(PerformedContext context) { }
}

public class RetryJobFilter : IElectStateFilter
{
    public void OnStateElection(ElectStateContext context) { }
}
'''

SAMPLE_CONFIG = '''
using Hangfire;

builder.Services.AddHangfire(config =>
    config.UseSqlServerStorage(builder.Configuration.GetConnectionString("HangfireDb")));
builder.Services.AddHangfireServer();

app.UseHangfireDashboard("/hangfire", new DashboardOptions
{
    Authorization = new[] { new MyDashboardAuthFilter() }
});

public class MyDashboardAuthFilter : IDashboardAuthorizationFilter
{
    public bool Authorize(DashboardContext context) => true;
}
'''


# ── Tests ────────────────────────────────────────────────

class TestEnhancedHangfireParser:
    """Tests for EnhancedHangfireParser."""

    def setup_method(self):
        self.parser = EnhancedHangfireParser()

    def test_is_hangfire_file_jobs(self):
        assert self.parser.is_hangfire_file(SAMPLE_JOBS)

    def test_is_hangfire_file_config(self):
        assert self.parser.is_hangfire_file(SAMPLE_CONFIG)

    def test_is_hangfire_file_negative(self):
        assert not self.parser.is_hangfire_file("class Foo { }")
        assert not self.parser.is_hangfire_file("")

    def test_parse_background_jobs(self):
        result = self.parser.parse(SAMPLE_JOBS, "Services/JobService.cs")
        assert isinstance(result, HangfireParseResult)
        assert result.total_jobs >= 2  # Enqueue + Schedule + ContinueJobWith

    def test_parse_job_types(self):
        result = self.parser.parse(SAMPLE_JOBS, "Services/JobService.cs")
        job_types = [j.get('job_type') for j in result.jobs]
        assert "fire-and-forget" in job_types
        assert "delayed" in job_types

    def test_parse_recurring_jobs(self):
        result = self.parser.parse(SAMPLE_RECURRING, "Config/RecurringJobs.cs")
        assert result.total_recurring >= 2

    def test_parse_recurring_cron(self):
        result = self.parser.parse(SAMPLE_RECURRING, "Config/RecurringJobs.cs")
        assert len(result.recurring_jobs) >= 1

    def test_parse_job_filters(self):
        result = self.parser.parse(SAMPLE_FILTER, "Filters/LoggingFilter.cs")
        assert result.total_filters >= 1
        filter_types = [f.get('filter_type') for f in result.job_filters]
        assert "server" in filter_types or "elect-state" in filter_types

    def test_parse_dashboard(self):
        result = self.parser.parse(SAMPLE_CONFIG, "Startup.cs")
        assert len(result.dashboards) >= 1
        dash = result.dashboards[0]
        assert dash.get('path') == '/hangfire'

    def test_parse_storage(self):
        result = self.parser.parse(SAMPLE_CONFIG, "Startup.cs")
        assert len(result.storage) >= 1
        assert result.storage[0].get('storage_type') == 'sql-server'

    def test_framework_detection(self):
        result = self.parser.parse(SAMPLE_JOBS, "test.cs")
        assert len(result.detected_frameworks) > 0

    def test_file_classification(self):
        result = self.parser.parse(SAMPLE_JOBS, "Services/JobService.cs")
        assert result.file_type == "job-definition"

        result2 = self.parser.parse(SAMPLE_CONFIG, "Startup.cs")
        assert result2.file_type == "configuration"

    def test_empty_input(self):
        result = self.parser.parse("", "test.cs")
        assert result.total_jobs == 0
