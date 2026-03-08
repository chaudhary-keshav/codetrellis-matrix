"""
Tests for MediatR Enhanced Parser.

Tests request, handler, notification, behavior, stream extraction.
Part of CodeTrellis v4.96 (Session 76)
"""

import pytest
from codetrellis.mediatr_parser_enhanced import EnhancedMediatRParser, MediatRParseResult


# ── Fixtures ─────────────────────────────────────────────

SAMPLE_REQUEST = '''
using MediatR;

public class GetProductQuery : IRequest<ProductDto>
{
    public int ProductId { get; set; }
}

public class CreateProductCommand : IRequest<int>
{
    public string Name { get; set; }
    public decimal Price { get; set; }
}

public class DeleteProductCommand : IRequest
{
    public int ProductId { get; set; }
}
'''

SAMPLE_HANDLER = '''
using MediatR;

public class GetProductQueryHandler : IRequestHandler<GetProductQuery, ProductDto>
{
    private readonly IProductRepository _repo;

    public GetProductQueryHandler(IProductRepository repo) => _repo = repo;

    public async Task<ProductDto> Handle(GetProductQuery request, CancellationToken ct)
    {
        return await _repo.GetByIdAsync(request.ProductId, ct);
    }
}

public class CreateProductCommandHandler : IRequestHandler<CreateProductCommand, int>
{
    public async Task<int> Handle(CreateProductCommand request, CancellationToken ct)
    {
        return 1;
    }
}
'''

SAMPLE_NOTIFICATION = '''
using MediatR;

public class ProductCreatedNotification : INotification
{
    public int ProductId { get; set; }
    public string ProductName { get; set; }
}

public class ProductCreatedHandler : INotificationHandler<ProductCreatedNotification>
{
    public Task Handle(ProductCreatedNotification notification, CancellationToken ct)
    {
        return Task.CompletedTask;
    }
}
'''

SAMPLE_BEHAVIOR = '''
using MediatR;
using FluentValidation;

public class ValidationBehavior<TRequest, TResponse> : IPipelineBehavior<TRequest, TResponse>
    where TRequest : IRequest<TResponse>
{
    private readonly IEnumerable<IValidator<TRequest>> _validators;

    public ValidationBehavior(IEnumerable<IValidator<TRequest>> validators) => _validators = validators;

    public async Task<TResponse> Handle(TRequest request, RequestHandlerDelegate<TResponse> next, CancellationToken ct)
    {
        var failures = _validators.SelectMany(v => v.Validate(request).Errors).ToList();
        if (failures.Any()) throw new ValidationException(failures);
        return await next();
    }
}

public class LoggingBehavior<TRequest, TResponse> : IPipelineBehavior<TRequest, TResponse>
{
    public async Task<TResponse> Handle(TRequest request, RequestHandlerDelegate<TResponse> next, CancellationToken ct)
    {
        return await next();
    }
}
'''

SAMPLE_STREAM = '''
using MediatR;

public class GetProductsStreamRequest : IStreamRequest<ProductDto>
{
    public string Category { get; set; }
}
'''


# ── Tests ────────────────────────────────────────────────

class TestEnhancedMediatRParser:
    """Tests for EnhancedMediatRParser."""

    def setup_method(self):
        self.parser = EnhancedMediatRParser()

    def test_is_mediatr_file_request(self):
        assert self.parser.is_mediatr_file(SAMPLE_REQUEST)

    def test_is_mediatr_file_handler(self):
        assert self.parser.is_mediatr_file(SAMPLE_HANDLER)

    def test_is_mediatr_file_negative(self):
        assert not self.parser.is_mediatr_file("class Foo { }")
        assert not self.parser.is_mediatr_file("")

    def test_parse_requests(self):
        result = self.parser.parse(SAMPLE_REQUEST, "Commands/CreateProductCommand.cs")
        assert isinstance(result, MediatRParseResult)
        assert len(result.requests) >= 2  # GetProductQuery + CreateProductCommand

    def test_parse_handlers(self):
        result = self.parser.parse(SAMPLE_HANDLER, "Handlers/ProductHandlers.cs")
        assert len(result.handlers) >= 1

    def test_parse_notifications(self):
        result = self.parser.parse(SAMPLE_NOTIFICATION, "Notifications/ProductCreated.cs")
        assert len(result.notifications) >= 1

    def test_parse_behaviors(self):
        result = self.parser.parse(SAMPLE_BEHAVIOR, "Behaviors/ValidationBehavior.cs")
        assert len(result.behaviors) >= 1

    def test_parse_stream_requests(self):
        result = self.parser.parse(SAMPLE_STREAM, "Queries/GetProductsStream.cs")
        assert len(result.stream_requests) >= 1

    def test_framework_detection(self):
        result = self.parser.parse(SAMPLE_REQUEST, "test.cs")
        assert len(result.detected_frameworks) > 0

    def test_empty_input(self):
        result = self.parser.parse("", "test.cs")
        assert len(result.requests) == 0

    def test_cqrs_detection(self):
        combined = SAMPLE_REQUEST + SAMPLE_HANDLER
        result = self.parser.parse(combined, "Features/Products.cs")
        assert result.total_requests > 0
        assert result.total_handlers > 0
