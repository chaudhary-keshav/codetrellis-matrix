"""
Tests for ASP.NET Core Enhanced Parser.

Tests controller extraction, minimal API detection, middleware,
dependency injection, configuration binding, and authentication.
Part of CodeTrellis v4.96 (Session 76)
"""

import pytest
from codetrellis.aspnetcore_parser_enhanced import EnhancedASPNetCoreParser, ASPNetCoreParseResult


# ── Fixtures ─────────────────────────────────────────────

SAMPLE_CONTROLLER = '''
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Authorization;

namespace MyApp.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class ProductsController : ControllerBase
{
    [HttpGet]
    public async Task<IActionResult> GetAll()
    {
        return Ok(await _service.GetAllAsync());
    }

    [HttpGet("{id}")]
    public async Task<IActionResult> GetById(int id)
    {
        return Ok(await _service.GetByIdAsync(id));
    }

    [HttpPost]
    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> Create([FromBody] CreateProductDto dto)
    {
        return Created("", await _service.CreateAsync(dto));
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> Update(int id, [FromBody] UpdateProductDto dto)
    {
        return Ok(await _service.UpdateAsync(id, dto));
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(int id)
    {
        await _service.DeleteAsync(id);
        return NoContent();
    }
}
'''

SAMPLE_MINIMAL_API = '''
using Microsoft.AspNetCore.Builder;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapGet("/api/products", async (IProductService svc) => await svc.GetAllAsync());
app.MapGet("/api/products/{id}", async (int id, IProductService svc) => await svc.GetByIdAsync(id));
app.MapPost("/api/products", async (CreateProductDto dto, IProductService svc) => await svc.CreateAsync(dto));
app.MapDelete("/api/products/{id}", async (int id, IProductService svc) => await svc.DeleteAsync(id));
app.MapGroup("/api/orders").WithTags("Orders");

app.Run();
'''

SAMPLE_MIDDLEWARE = '''
using Microsoft.AspNetCore.Http;

public class RequestLoggingMiddleware : IMiddleware
{
    public async Task InvokeAsync(HttpContext context, RequestDelegate next)
    {
        Console.WriteLine($"Request: {context.Request.Path}");
        await next(context);
    }
}

// Startup
app.UseAuthentication();
app.UseAuthorization();
app.UseCors("AllowAll");
app.UseMiddleware<RequestLoggingMiddleware>();
app.UseResponseCaching();
'''

SAMPLE_DI = '''
using Microsoft.Extensions.DependencyInjection;

builder.Services.AddScoped<IProductService, ProductService>();
builder.Services.AddSingleton<ICacheService, RedisCacheService>();
builder.Services.AddTransient<IEmailService, SmtpEmailService>();
builder.Services.AddDbContext<AppDbContext>(options => options.UseSqlServer(connStr));
builder.Services.AddHttpClient<IExternalApiService, ExternalApiService>();
builder.Services.AddKeyedSingleton<INotifier>("sms", new SmsNotifier());
'''

SAMPLE_AUTH = '''
using Microsoft.AspNetCore.Authentication.JwtBearer;

builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters { ... };
    })
    .AddCookie("Cookies", options =>
    {
        options.LoginPath = "/login";
    });

builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("AdminOnly", policy => policy.RequireRole("Admin"));
    options.AddPolicy("PremiumUser", policy => policy.RequireClaim("subscription", "premium"));
});
'''

SAMPLE_CONFIG = '''
using Microsoft.Extensions.Options;

builder.Services.Configure<SmtpSettings>(builder.Configuration.GetSection("Smtp"));
builder.Services.AddOptions<DatabaseSettings>().Bind(builder.Configuration.GetSection("Database"));

var connString = builder.Configuration.GetSection("ConnectionStrings:Default").Value;
'''


# ── Tests ────────────────────────────────────────────────

class TestEnhancedASPNetCoreParser:
    """Tests for EnhancedASPNetCoreParser."""

    def setup_method(self):
        self.parser = EnhancedASPNetCoreParser()

    def test_is_aspnetcore_file_controller(self):
        assert self.parser.is_aspnetcore_file(SAMPLE_CONTROLLER)

    def test_is_aspnetcore_file_minimal_api(self):
        assert self.parser.is_aspnetcore_file(SAMPLE_MINIMAL_API)

    def test_is_aspnetcore_file_negative(self):
        assert not self.parser.is_aspnetcore_file("class Foo { }")
        assert not self.parser.is_aspnetcore_file("")

    def test_parse_controller(self):
        result = self.parser.parse(SAMPLE_CONTROLLER, "Controllers/ProductsController.cs")
        assert isinstance(result, ASPNetCoreParseResult)
        assert len(result.controllers) > 0
        ctrl = result.controllers[0]
        # Controllers are AspNetControllerInfo dataclass objects
        assert ctrl.name == 'ProductsController' or 'Products' in str(ctrl.name)
        assert len(result.detected_frameworks) > 0

    def test_parse_controller_endpoints(self):
        result = self.parser.parse(SAMPLE_CONTROLLER, "Controllers/ProductsController.cs")
        assert result.total_endpoints >= 3  # GET/id, PUT, DELETE (extracted per action method)

    def test_parse_minimal_apis(self):
        result = self.parser.parse(SAMPLE_MINIMAL_API, "Program.cs")
        assert len(result.minimal_apis) >= 3  # MapGet x2, MapPost, MapDelete

    def test_parse_middleware(self):
        result = self.parser.parse(SAMPLE_MIDDLEWARE, "Middleware/RequestLogging.cs")
        assert len(result.middlewares) > 0

    def test_parse_di_registrations(self):
        result = self.parser.parse(SAMPLE_DI, "Startup.cs")
        assert len(result.di_registrations) >= 3  # scoped + singleton + transient

    def test_parse_auth(self):
        result = self.parser.parse(SAMPLE_AUTH, "Startup.cs")
        assert len(result.auth_schemes) >= 1  # JWT at minimum
        assert len(result.auth_policies) >= 1  # AdminOnly

    def test_parse_config(self):
        result = self.parser.parse(SAMPLE_CONFIG, "Startup.cs")
        assert len(result.config_bindings) >= 1 or len(result.options_patterns) >= 1

    def test_framework_detection(self):
        result = self.parser.parse(SAMPLE_CONTROLLER, "ProductsController.cs")
        assert any('aspnet' in f or 'mvc' in f or 'api_controller' in f for f in result.detected_frameworks)

    def test_version_detection(self):
        result = self.parser.parse(SAMPLE_MINIMAL_API, "Program.cs")
        assert result.aspnetcore_version  # Should detect some version

    def test_file_classification(self):
        result = self.parser.parse(SAMPLE_CONTROLLER, "Controllers/ProductsController.cs")
        assert result.file_type in ("controller", "api", "service", "startup")

    def test_empty_input(self):
        result = self.parser.parse("", "test.cs")
        assert len(result.controllers) == 0
        assert result.total_endpoints == 0

    def test_non_aspnetcore_file(self):
        result = self.parser.parse("public class Foo { void Bar() { } }", "Foo.cs")
        assert len(result.controllers) == 0
