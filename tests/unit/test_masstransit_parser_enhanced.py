"""
Tests for MassTransit Enhanced Parser.

Tests consumer extraction, saga detection, message contracts, bus config.
Part of CodeTrellis v4.96 (Session 76)
"""

import pytest
from codetrellis.masstransit_parser_enhanced import EnhancedMassTransitParser, MassTransitParseResult


# ── Fixtures ─────────────────────────────────────────────

SAMPLE_CONSUMER = '''
using MassTransit;

public class OrderSubmittedConsumer : IConsumer<OrderSubmittedEvent>
{
    public async Task Consume(ConsumeContext<OrderSubmittedEvent> context)
    {
        var order = context.Message;
        // Process order
    }
}

public class OrderSubmittedConsumerDefinition : ConsumerDefinition<OrderSubmittedConsumer>
{
    protected override void ConfigureConsumer(IReceiveEndpointConfigurator endpointConfigurator,
        IConsumerConfigurator<OrderSubmittedConsumer> consumerConfigurator)
    {
        endpointConfigurator.UseMessageRetry(r => r.Interval(3, TimeSpan.FromSeconds(5)));
    }
}
'''

SAMPLE_BATCH_CONSUMER = '''
using MassTransit;

public class BatchOrderProcessor : IConsumer<Batch<ProcessOrderCommand>>
{
    public async Task Consume(ConsumeContext<Batch<ProcessOrderCommand>> context)
    {
        foreach (var msg in context.Message)
        {
            // Process batch
        }
    }
}
'''

SAMPLE_SAGA = '''
using MassTransit;

public class OrderState : SagaStateMachineInstance
{
    public Guid CorrelationId { get; set; }
    public string CurrentState { get; set; }
    public DateTime OrderDate { get; set; }
}

public class OrderStateMachine : MassTransitStateMachine<OrderState>
{
    public State Submitted { get; }
    public State Accepted { get; }
    public State Completed { get; }

    public Event<OrderSubmittedEvent> OrderSubmitted { get; }
    public Event<OrderAcceptedEvent> OrderAccepted { get; }
    public Event<OrderCompletedEvent> OrderCompleted { get; }

    public OrderStateMachine()
    {
        InstanceState(x => x.CurrentState);

        Event(() => OrderSubmitted, x => x.CorrelateById(m => m.Message.OrderId));

        Initially(
            When(OrderSubmitted)
                .TransitionTo(Submitted));
    }
}
'''

SAMPLE_MESSAGES = '''
using MassTransit;

public record OrderSubmittedEvent
{
    public Guid OrderId { get; init; }
    public decimal Total { get; init; }
}

public record ProcessOrderCommand
{
    public Guid OrderId { get; init; }
}

public record OrderStatusRequest
{
    public Guid OrderId { get; init; }
}

public record OrderStatusResponse
{
    public string Status { get; init; }
}
'''

SAMPLE_BUS_CONFIG = '''
using MassTransit;

builder.Services.AddMassTransit(x =>
{
    x.AddConsumersFromNamespaceContaining<OrderSubmittedConsumer>();

    x.UsingRabbitMq((context, cfg) =>
    {
        cfg.Host("rabbitmq://localhost");
        cfg.UseMessageRetry(r => r.Interval(3, TimeSpan.FromSeconds(5)));
        cfg.ConfigureEndpoints(context);
    });

    x.AddEntityFrameworkOutbox<AppDbContext>(o =>
    {
        o.UseSqlServer();
        o.UseBusOutbox();
    });
});
'''

SAMPLE_FILTER = '''
using MassTransit;

public class AuditConsumeFilter<T> : IConsumeFilter<T>
    where T : class
{
    public async Task Send(ConsumeContext<T> context, IPipe<ConsumeContext<T>> next)
    {
        await next.Send(context);
    }
}
'''


# ── Tests ────────────────────────────────────────────────

class TestEnhancedMassTransitParser:
    """Tests for EnhancedMassTransitParser."""

    def setup_method(self):
        self.parser = EnhancedMassTransitParser()

    def test_is_masstransit_file_consumer(self):
        assert self.parser.is_masstransit_file(SAMPLE_CONSUMER)

    def test_is_masstransit_file_saga(self):
        assert self.parser.is_masstransit_file(SAMPLE_SAGA)

    def test_is_masstransit_file_negative(self):
        assert not self.parser.is_masstransit_file("class Foo { }")
        assert not self.parser.is_masstransit_file("")

    def test_parse_consumers(self):
        result = self.parser.parse(SAMPLE_CONSUMER, "Consumers/OrderConsumer.cs")
        assert isinstance(result, MassTransitParseResult)
        assert result.total_consumers >= 1
        consumer = result.consumers[0]
        assert consumer.get('name') == 'OrderSubmittedConsumer'
        assert consumer.get('message_type') == 'OrderSubmittedEvent'

    def test_parse_batch_consumer(self):
        result = self.parser.parse(SAMPLE_BATCH_CONSUMER, "Consumers/BatchProcessor.cs")
        assert result.total_consumers >= 1
        consumer = result.consumers[0]
        assert consumer.get('consumer_type') == 'batch-consumer'

    def test_parse_saga(self):
        result = self.parser.parse(SAMPLE_SAGA, "Sagas/OrderStateMachine.cs")
        assert result.total_sagas >= 1
        saga = result.sagas[0]
        assert saga.get('saga_type') == 'state-machine'
        assert saga.get('state_type') == 'OrderState'

    def test_parse_saga_events(self):
        result = self.parser.parse(SAMPLE_SAGA, "Sagas/OrderStateMachine.cs")
        saga_machines = [s for s in result.sagas if s.get('saga_type') == 'state-machine']
        if saga_machines:
            assert len(saga_machines[0].get('events', [])) >= 1

    def test_parse_messages(self):
        result = self.parser.parse(SAMPLE_MESSAGES, "Contracts/OrderMessages.cs")
        assert result.total_messages >= 2

    def test_parse_message_kinds(self):
        result = self.parser.parse(SAMPLE_MESSAGES, "Contracts/OrderMessages.cs")
        kinds = [m.get('message_kind') for m in result.messages]
        assert "event" in kinds or "command" in kinds

    def test_parse_bus_config(self):
        result = self.parser.parse(SAMPLE_BUS_CONFIG, "Config/MassTransitConfig.cs")
        assert len(result.bus_configs) >= 1
        config = result.bus_configs[0]
        assert config.get('transport') == 'rabbitmq'

    def test_parse_outbox(self):
        result = self.parser.parse(SAMPLE_BUS_CONFIG, "Config/MassTransitConfig.cs")
        configs = result.bus_configs
        assert any(c.get('has_outbox') for c in configs)

    def test_parse_filter(self):
        result = self.parser.parse(SAMPLE_FILTER, "Filters/AuditFilter.cs")
        assert len(result.middleware) >= 1

    def test_framework_detection(self):
        result = self.parser.parse(SAMPLE_CONSUMER, "test.cs")
        assert len(result.detected_frameworks) > 0

    def test_empty_input(self):
        result = self.parser.parse("", "test.cs")
        assert result.total_consumers == 0
