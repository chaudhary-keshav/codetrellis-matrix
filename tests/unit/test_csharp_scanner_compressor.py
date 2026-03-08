"""
Tests for C# scanner and compressor integration.

Verifies that C# files are correctly detected, parsed, and compressed
into the matrix.prompt output format.

Part of CodeTrellis v4.13 C# Language Support.
"""

import pytest
from codetrellis.scanner import ProjectScanner, ProjectMatrix


@pytest.fixture
def scanner():
    return ProjectScanner()


@pytest.fixture
def matrix():
    return ProjectMatrix(name="test_csharp", root_path="/test")


# ===== FILE TYPE DETECTION =====

class TestFileTypeDetection:
    """Tests that C# file extensions map correctly."""

    def test_cs_extension(self, scanner):
        assert ".cs" in scanner.FILE_TYPES
        assert scanner.FILE_TYPES[".cs"] == "csharp"

    def test_file_type_priority(self, scanner):
        """Ensure .cs doesn't conflict with .ts, .tsx, or other extensions."""
        # .cs should map to csharp, not anything else
        # Iterate FILE_TYPES and ensure .cs matches correctly
        from pathlib import Path
        test_path = Path("/test/Models/User.cs")
        file_type = "unknown"
        for pattern, ftype in scanner.FILE_TYPES.items():
            if test_path.name.endswith(pattern):
                file_type = ftype
                break
        assert file_type == "csharp"

    def test_csx_extension(self, scanner):
        """C# script files should also be classified as csharp."""
        # Check if .csx is in FILE_TYPES
        if ".csx" in scanner.FILE_TYPES:
            assert scanner.FILE_TYPES[".csx"] == "csharp"


# ===== PARSE DISPATCH =====

class TestParseDispatch:
    """Tests that _parse_csharp is called and populates matrix correctly."""

    def test_parse_simple_class(self, scanner, matrix, tmp_path):
        cs_file = tmp_path / "User.cs"
        cs_file.write_text('''
        namespace MyApp.Models;

        public class User
        {
            public int Id { get; set; }
            public string Name { get; set; }
            public string Email { get; set; }
        }
        ''')
        scanner._parse_csharp(cs_file, matrix)
        assert len(matrix.csharp_classes) >= 1
        assert matrix.csharp_classes[0]["name"] == "User"

    def test_parse_controller(self, scanner, matrix, tmp_path):
        cs_file = tmp_path / "ProductsController.cs"
        cs_file.write_text('''
        using Microsoft.AspNetCore.Mvc;

        namespace MyApp.Controllers;

        [ApiController]
        [Route("api/products")]
        public class ProductsController : ControllerBase
        {
            [HttpGet]
            public IActionResult GetAll() => Ok();

            [HttpGet("{id}")]
            public IActionResult GetById(int id) => Ok();
        }
        ''')
        scanner._parse_csharp(cs_file, matrix)
        assert len(matrix.csharp_classes) >= 1
        assert len(matrix.csharp_endpoints) >= 2

    def test_parse_ef_dbcontext(self, scanner, matrix, tmp_path):
        cs_file = tmp_path / "AppDbContext.cs"
        cs_file.write_text('''
        using Microsoft.EntityFrameworkCore;

        public class AppDbContext : DbContext
        {
            public DbSet<User> Users { get; set; }
            public DbSet<Order> Orders { get; set; }
        }
        ''')
        scanner._parse_csharp(cs_file, matrix)
        assert len(matrix.csharp_db_contexts) >= 1

    def test_parse_minimal_api(self, scanner, matrix, tmp_path):
        cs_file = tmp_path / "OrdersApi.cs"
        cs_file.write_text('''
        public static class OrdersApi
        {
            public static void MapEndpoints(IEndpointRouteBuilder app)
            {
                app.MapGet("/api/orders", GetAllOrders);
                app.MapPost("/api/orders", CreateOrder);
                app.MapDelete("/api/orders/{id}", DeleteOrder);
            }
        }
        ''')
        scanner._parse_csharp(cs_file, matrix)
        assert len(matrix.csharp_endpoints) >= 3

    def test_parse_enum(self, scanner, matrix, tmp_path):
        cs_file = tmp_path / "OrderStatus.cs"
        cs_file.write_text('''
        namespace MyApp.Models;

        public enum OrderStatus
        {
            Pending = 0,
            Confirmed = 1,
            Shipped = 2,
            Delivered = 3,
            Cancelled = 4
        }
        ''')
        scanner._parse_csharp(cs_file, matrix)
        assert len(matrix.csharp_enums) >= 1
        enum_data = matrix.csharp_enums[0]
        assert enum_data["name"] == "OrderStatus"
        assert len(enum_data["members"]) >= 4

    def test_parse_record(self, scanner, matrix, tmp_path):
        cs_file = tmp_path / "OrderDto.cs"
        cs_file.write_text('''
        namespace MyApp.DTOs;

        public record OrderDto(int Id, string Description, decimal Total, DateTime CreatedAt);
        public record OrderItemDto(int ProductId, string Name, decimal Price, int Quantity);
        ''')
        scanner._parse_csharp(cs_file, matrix)
        assert len(matrix.csharp_records) >= 2

    def test_parse_interface(self, scanner, matrix, tmp_path):
        cs_file = tmp_path / "IOrderService.cs"
        cs_file.write_text('''
        namespace MyApp.Services;

        public interface IOrderService
        {
            Task<Order> GetOrderAsync(int id);
            Task<IEnumerable<Order>> GetAllOrdersAsync();
            Task<int> CreateOrderAsync(Order order);
        }
        ''')
        scanner._parse_csharp(cs_file, matrix)
        assert len(matrix.csharp_interfaces) >= 1
        assert matrix.csharp_interfaces[0]["name"] == "IOrderService"

    def test_skip_test_files(self, scanner, matrix, tmp_path):
        cs_file = tmp_path / "OrderServiceTest.cs"
        cs_file.write_text('''
        public class OrderServiceTest
        {
            [Fact]
            public void Should_CreateOrder()
            {
            }
        }
        ''')
        scanner._parse_csharp(cs_file, matrix)
        # Test files should be skipped
        assert len(matrix.csharp_classes) == 0

    def test_skip_designer_files(self, scanner, matrix, tmp_path):
        cs_file = tmp_path / "Form1.Designer.cs"
        cs_file.write_text('''
        partial class Form1
        {
            private void InitializeComponent() { }
        }
        ''')
        scanner._parse_csharp(cs_file, matrix)
        # Designer files should be skipped
        assert len(matrix.csharp_classes) == 0

    def test_namespace_tracking(self, scanner, matrix, tmp_path):
        cs_file = tmp_path / "Service.cs"
        cs_file.write_text('''
        namespace MyApp.Services;

        public class TestService { }
        ''')
        scanner._parse_csharp(cs_file, matrix)
        assert "MyApp.Services" in matrix.csharp_namespaces


# ===== COMPRESSOR INTEGRATION =====

class TestCompressorIntegration:
    """Tests that C# data compresses correctly."""

    def test_compress_classes(self):
        from codetrellis.compressor import MatrixCompressor
        compressor = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/test")
        matrix.csharp_classes = [
            {
                "name": "UserService",
                "file": "/test/Services/UserService.cs",
                "line": 10,
                "fields": [],
                "properties": [{"name": "Logger", "type": "ILogger", "getter": True, "setter": False, "init": False}],
                "methods": ["GetUser", "CreateUser"],
                "extends": "BaseService",
                "implements": ["IUserService"],
                "attributes": ["Injectable"],
                "generic_params": [],
                "is_abstract": False,
                "is_sealed": False,
                "is_static": False,
                "is_partial": False,
            }
        ]
        lines = compressor._compress_csharp_types(matrix)
        assert len(lines) >= 1
        output = "\n".join(lines)
        assert "UserService" in output

    def test_compress_endpoints(self):
        from codetrellis.compressor import MatrixCompressor
        compressor = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/test")
        matrix.csharp_endpoints = [
            {
                "method": "GET",
                "path": "/api/orders",
                "handler": "GetAllOrders",
                "framework": "minimal_api",
                "file": "/test/OrdersApi.cs",
                "line": 5,
                "controller": "",
                "is_authorized": False,
            }
        ]
        lines = compressor._compress_csharp_api(matrix)
        assert len(lines) >= 1
        output = "\n".join(lines)
        assert "GET" in output
        assert "/api/orders" in output

    def test_compress_models(self):
        from codetrellis.compressor import MatrixCompressor
        compressor = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/test")
        matrix.csharp_db_contexts = [
            {
                "name": "AppDbContext",
                "base_class": "DbContext",
                "file": "/test/AppDbContext.cs",
                "line": 5,
                "db_sets": [{"property_name": "Users", "entity_type": "User"}],
                "has_on_model_creating": True,
                "uses_fluent_api": False,
            }
        ]
        lines = compressor._compress_csharp_models(matrix)
        assert len(lines) >= 1
        output = "\n".join(lines)
        assert "AppDbContext" in output

    def test_compress_dependencies(self):
        from codetrellis.compressor import MatrixCompressor
        compressor = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/test")
        matrix.csharp_detected_frameworks = ["aspnet_core", "ef_core", "blazor"]
        matrix.csharp_namespaces = ["MyApp.Models", "MyApp.Services", "MyApp.Controllers"]
        lines = compressor._compress_csharp_dependencies(matrix)
        assert len(lines) >= 1
        output = "\n".join(lines)
        assert "aspnet_core" in output


# ===== MATRIX TO_DICT =====

class TestMatrixToDict:
    """Tests that C# data appears in matrix.to_dict() output."""

    def test_csharp_in_stats(self):
        matrix = ProjectMatrix(name="test", root_path="/test")
        matrix.csharp_classes = [{"name": "Test", "file": "Test.cs"}]
        matrix.csharp_methods = [{"name": "DoWork", "file": "Test.cs"}]
        d = matrix.to_dict()
        assert d["stats"]["csharp_classes"] == 1
        assert d["stats"]["csharp_methods"] == 1

    def test_csharp_data_section(self):
        matrix = ProjectMatrix(name="test", root_path="/test")
        matrix.csharp_classes = [{"name": "UserService", "file": "UserService.cs"}]
        matrix.csharp_interfaces = [{"name": "IUserService", "file": "IUserService.cs"}]
        d = matrix.to_dict()
        assert "csharp" in d
        assert d["csharp"]["classes"] == matrix.csharp_classes
        assert d["csharp"]["interfaces"] == matrix.csharp_interfaces
