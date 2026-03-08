"""
Tests for EnhancedCSharpParser — integrated parsing across all extractors.

Part of CodeTrellis v4.13 C# Language Support.
"""

import pytest
from codetrellis.csharp_parser_enhanced import EnhancedCSharpParser


@pytest.fixture
def parser():
    return EnhancedCSharpParser()


# ===== BASIC PARSING =====

class TestBasicParsing:
    """Tests for basic C# file parsing."""

    def test_empty_content(self, parser):
        result = parser.parse("", "empty.cs")
        assert len(result.classes) == 0
        assert len(result.methods) == 0

    def test_whitespace_only(self, parser):
        result = parser.parse("   \n  \n  ", "whitespace.cs")
        assert len(result.classes) == 0

    def test_namespace_extraction(self, parser):
        code = '''
        namespace MyApp.Services;

        public class UserService { }
        '''
        result = parser.parse(code, "UserService.cs")
        assert result.namespace == "MyApp.Services"

    def test_traditional_namespace(self, parser):
        code = '''
        namespace MyApp.Services
        {
            public class OrderService { }
        }
        '''
        result = parser.parse(code, "OrderService.cs")
        assert result.namespace == "MyApp.Services"

    def test_using_extraction(self, parser):
        code = '''
        using System;
        using System.Collections.Generic;
        using Microsoft.AspNetCore.Mvc;

        namespace MyApp.Controllers;

        public class TestController : ControllerBase { }
        '''
        result = parser.parse(code, "TestController.cs")
        assert "System" in result.usings
        assert "System.Collections.Generic" in result.usings
        assert "Microsoft.AspNetCore.Mvc" in result.usings


# ===== FRAMEWORK DETECTION =====

class TestFrameworkDetection:
    """Tests for framework detection."""

    def test_aspnet_core_detection(self, parser):
        code = '''
        using Microsoft.AspNetCore.Mvc;

        [ApiController]
        [Route("api/[controller]")]
        public class TestController : ControllerBase
        {
            [HttpGet]
            public IActionResult Get() => Ok();
        }
        '''
        result = parser.parse(code, "TestController.cs")
        assert "aspnet_core" in result.detected_frameworks

    def test_ef_core_detection(self, parser):
        code = '''
        using Microsoft.EntityFrameworkCore;

        public class AppDbContext : DbContext
        {
            public DbSet<User> Users { get; set; }
        }
        '''
        result = parser.parse(code, "AppDbContext.cs")
        assert "ef_core" in result.detected_frameworks

    def test_blazor_detection(self, parser):
        code = '''
        @page "/counter"

        using Microsoft.AspNetCore.Components;

        public partial class Counter : ComponentBase
        {
            private int currentCount = 0;
            private void IncrementCount() { currentCount++; }
        }
        '''
        result = parser.parse(code, "Counter.razor.cs")
        assert "blazor" in result.detected_frameworks


# ===== VERSION FEATURE DETECTION =====

class TestVersionFeatureDetection:
    """Tests for C# version feature detection."""

    def test_file_scoped_namespace(self, parser):
        code = '''
        namespace MyApp.Models;

        public class User { }
        '''
        result = parser.parse(code, "User.cs")
        assert "file_scoped_namespace" in result.csharp_version_features

    def test_record_detection(self, parser):
        code = '''
        public record UserDto(string Name, string Email);
        '''
        result = parser.parse(code, "UserDto.cs")
        assert "records" in result.csharp_version_features


# ===== INTEGRATED EXTRACTION =====

class TestIntegratedExtraction:
    """Tests for full file parsing with all extractors."""

    def test_aspnet_controller_full(self, parser):
        code = '''
        using Microsoft.AspNetCore.Mvc;
        using Microsoft.AspNetCore.Authorization;

        namespace MyApp.Controllers;

        [ApiController]
        [Route("api/[controller]")]
        [Authorize]
        public class OrdersController : ControllerBase
        {
            private readonly IOrderService _orderService;

            public OrdersController(IOrderService orderService)
            {
                _orderService = orderService;
            }

            [HttpGet]
            public async Task<IActionResult> GetAllOrders()
            {
                var orders = await _orderService.GetAllAsync();
                return Ok(orders);
            }

            [HttpGet("{id}")]
            public async Task<IActionResult> GetOrder(int id)
            {
                var order = await _orderService.GetByIdAsync(id);
                return Ok(order);
            }

            [HttpPost]
            public async Task<IActionResult> CreateOrder([FromBody] CreateOrderDto dto)
            {
                var order = await _orderService.CreateAsync(dto);
                return CreatedAtAction(nameof(GetOrder), new { id = order.Id }, order);
            }
        }
        '''
        result = parser.parse(code, "OrdersController.cs")
        assert len(result.classes) >= 1
        assert result.classes[0].name == "OrdersController"
        assert len(result.endpoints) >= 3
        assert len(result.constructors) >= 1
        assert "aspnet_core" in result.detected_frameworks

    def test_ef_entity_full(self, parser):
        code = '''
        using System.ComponentModel.DataAnnotations;
        using System.ComponentModel.DataAnnotations.Schema;

        namespace MyApp.Models;

        [Table("orders")]
        public class Order
        {
            [Key]
            public int Id { get; set; }

            [Required]
            [StringLength(200)]
            public string Description { get; set; }

            public DateTime OrderDate { get; set; }
            public decimal Total { get; set; }

            public int BuyerId { get; set; }
            public Buyer Buyer { get; set; }

            public ICollection<OrderItem> Items { get; set; }
        }
        '''
        result = parser.parse(code, "Order.cs")
        assert result.namespace == "MyApp.Models"
        assert len(result.classes) >= 1
        assert result.classes[0].name == "Order"
        assert len(result.entities) >= 1
        assert result.entities[0].name == "Order"

    def test_minimal_api_file(self, parser):
        code = '''
        using Microsoft.AspNetCore.Http.HttpResults;

        public static class OrdersApi
        {
            public static RouteGroupBuilder MapOrdersApiV1(IEndpointRouteBuilder app)
            {
                var api = app.MapGroup("api/orders");
                api.MapGet("/", GetAllOrders);
                api.MapGet("/{id:int}", GetOrderById);
                api.MapPost("/", CreateOrder);
                api.MapPut("/{id:int}", UpdateOrder);
                api.MapDelete("/{id:int}", DeleteOrder);
                return api;
            }

            public static async Task<Ok<List<Order>>> GetAllOrders()
            {
                return TypedResults.Ok(new List<Order>());
            }
        }
        '''
        result = parser.parse(code, "OrdersApi.cs")
        assert len(result.classes) >= 1
        assert len(result.endpoints) >= 5
        assert all(ep.framework == "minimal_api" for ep in result.endpoints)

    def test_grpc_service_file(self, parser):
        code = '''
        using Grpc.Core;

        public class BasketService : Basket.BasketBase
        {
            public override async Task<CustomerBasketResponse> GetBasket(
                GetBasketRequest request, ServerCallContext context)
            {
                return new CustomerBasketResponse();
            }

            public override async Task<CustomerBasketResponse> UpdateBasket(
                UpdateBasketRequest request, ServerCallContext context)
            {
                return new CustomerBasketResponse();
            }
        }
        '''
        result = parser.parse(code, "BasketService.cs")
        assert len(result.grpc_services) >= 1
        assert result.grpc_services[0].name == "BasketService"

    def test_signalr_hub_file(self, parser):
        code = '''
        using Microsoft.AspNetCore.SignalR;

        namespace MyApp.Hubs;

        public class ChatHub : Hub
        {
            public async Task SendMessage(string user, string message)
            {
                await Clients.All.SendAsync("ReceiveMessage", user, message);
            }

            public async Task JoinGroup(string groupName)
            {
                await Groups.AddToGroupAsync(Context.ConnectionId, groupName);
            }
        }
        '''
        result = parser.parse(code, "ChatHub.cs")
        assert len(result.signalr_hubs) >= 1
        assert result.signalr_hubs[0].name == "ChatHub"

    def test_cqrs_pattern(self, parser):
        code = '''
        namespace MyApp.Application.Commands;

        public class CreateOrderCommand
        {
            public int ProductId { get; set; }
            public int Quantity { get; set; }
        }

        public class CreateOrderCommandHandler : IRequestHandler<CreateOrderCommand, int>
        {
            private readonly IOrderRepository _repository;

            public CreateOrderCommandHandler(IOrderRepository repository)
            {
                _repository = repository;
            }

            public async Task<int> Handle(CreateOrderCommand request, CancellationToken cancellationToken)
            {
                var order = new Order(request.ProductId, request.Quantity);
                return await _repository.AddAsync(order);
            }
        }
        '''
        result = parser.parse(code, "CreateOrderCommand.cs")
        assert len(result.classes) >= 2  # Command + Handler
        assert len(result.dtos) >= 1  # Command detected as DTO
        assert result.dtos[0].kind == "command"


# ===== CSPROJ PARSING =====

class TestCsprojParsing:
    """Tests for .csproj file parsing."""

    def test_parse_csproj(self, parser, tmp_path):
        csproj = tmp_path / "MyApp.csproj"
        csproj.write_text('''
        <Project Sdk="Microsoft.NET.Sdk.Web">
          <PropertyGroup>
            <TargetFramework>net8.0</TargetFramework>
            <Nullable>enable</Nullable>
          </PropertyGroup>
          <ItemGroup>
            <PackageReference Include="Microsoft.EntityFrameworkCore" Version="8.0.0" />
            <PackageReference Include="MediatR" Version="12.0.0" />
          </ItemGroup>
        </Project>
        ''')
        result = EnhancedCSharpParser.parse_csproj(str(csproj))
        assert result["sdk"] == "Microsoft.NET.Sdk.Web"
        assert result["target_framework"] == "net8.0"
        assert len(result["dependencies"]) >= 2

    def test_parse_csproj_class_library(self, parser, tmp_path):
        csproj = tmp_path / "MyLib.csproj"
        csproj.write_text('''
        <Project Sdk="Microsoft.NET.Sdk">
          <PropertyGroup>
            <TargetFramework>netstandard2.1</TargetFramework>
          </PropertyGroup>
        </Project>
        ''')
        result = EnhancedCSharpParser.parse_csproj(str(csproj))
        assert result["sdk"] == "Microsoft.NET.Sdk"
        assert result["target_framework"] == "netstandard2.1"


# ===== SLN PARSING =====

class TestSlnParsing:
    """Tests for .sln file parsing."""

    def test_parse_sln(self, parser, tmp_path):
        sln = tmp_path / "MyApp.sln"
        sln.write_text('''
Microsoft Visual Studio Solution File, Format Version 12.00
# Visual Studio Version 17
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "MyApp.Web", "src\\MyApp.Web\\MyApp.Web.csproj", "{GUID1}"
EndProject
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "MyApp.Core", "src\\MyApp.Core\\MyApp.Core.csproj", "{GUID2}"
EndProject
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "MyApp.Tests", "tests\\MyApp.Tests\\MyApp.Tests.csproj", "{GUID3}"
EndProject
        ''')
        result = EnhancedCSharpParser.parse_sln(str(sln))
        assert len(result["projects"]) >= 2
