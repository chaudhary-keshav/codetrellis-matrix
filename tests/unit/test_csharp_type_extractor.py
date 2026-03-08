"""
Tests for CSharpTypeExtractor — classes, interfaces, structs, records, delegates.

Part of CodeTrellis v4.13 C# Language Support.
"""

import pytest
from codetrellis.extractors.csharp.type_extractor import CSharpTypeExtractor


@pytest.fixture
def extractor():
    return CSharpTypeExtractor()


# ===== CLASS EXTRACTION =====

class TestClassExtraction:
    """Tests for C# class extraction."""

    def test_simple_public_class(self, extractor):
        code = '''
        namespace MyApp;

        public class HelloWorld
        {
            private string _name;
            public string GetName() { return _name; }
        }
        '''
        result = extractor.extract(code, "HelloWorld.cs")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "HelloWorld"

    def test_abstract_class(self, extractor):
        code = '''
        public abstract class BaseService
        {
            public abstract void Execute();
        }
        '''
        result = extractor.extract(code, "BaseService.cs")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "BaseService"
        assert cls.is_abstract is True

    def test_sealed_class(self, extractor):
        code = '''
        public sealed class UserService : BaseService
        {
            public override void Execute() { }
        }
        '''
        result = extractor.extract(code, "UserService.cs")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "UserService"
        assert cls.is_sealed is True

    def test_static_class(self, extractor):
        code = '''
        public static class StringExtensions
        {
            public static string Truncate(this string s, int len)
            {
                return s.Length > len ? s.Substring(0, len) : s;
            }
        }
        '''
        result = extractor.extract(code, "StringExtensions.cs")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "StringExtensions"
        assert cls.is_static is True

    def test_partial_class(self, extractor):
        code = '''
        public partial class UserService
        {
            public string GetName() { return "test"; }
        }
        '''
        result = extractor.extract(code, "UserService.cs")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "UserService"
        assert cls.is_partial is True

    def test_class_with_base_and_interfaces(self, extractor):
        code = '''
        public class OrderService : BaseService, IOrderService, IDisposable
        {
            public void Dispose() { }
        }
        '''
        result = extractor.extract(code, "OrderService.cs")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "OrderService"
        # Should detect base class and/or implements
        has_base = cls.base_class is not None
        has_impl = len(cls.implements) > 0
        assert has_base or has_impl

    def test_class_with_generic_params(self, extractor):
        code = '''
        public class Repository<T> where T : class, IEntity
        {
            public T GetById(int id) { return default; }
        }
        '''
        result = extractor.extract(code, "Repository.cs")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "Repository"

    def test_class_with_properties(self, extractor):
        code = '''
        public class User
        {
            public int Id { get; set; }
            public string Name { get; set; }
            public string? Email { get; init; }
            public required string Role { get; set; }
        }
        '''
        result = extractor.extract(code, "User.cs")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "User"
        assert len(cls.properties) >= 2  # Should find at least some properties

    def test_class_with_attributes(self, extractor):
        code = '''
        [ApiController]
        [Route("api/[controller]")]
        public class UsersController : ControllerBase
        {
            [HttpGet]
            public IActionResult Get() { return Ok(); }
        }
        '''
        result = extractor.extract(code, "UsersController.cs")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "UsersController"


# ===== INTERFACE EXTRACTION =====

class TestInterfaceExtraction:
    """Tests for C# interface extraction."""

    def test_simple_interface(self, extractor):
        code = '''
        public interface IOrderService
        {
            Task<Order> GetOrderAsync(int id);
            Task CreateOrderAsync(Order order);
        }
        '''
        result = extractor.extract(code, "IOrderService.cs")
        assert len(result["interfaces"]) >= 1
        iface = result["interfaces"][0]
        assert iface.name == "IOrderService"

    def test_interface_with_inheritance(self, extractor):
        code = '''
        public interface IRepository<T> : IReadRepository<T>, IWriteRepository<T>
            where T : class, IEntity
        {
        }
        '''
        result = extractor.extract(code, "IRepository.cs")
        assert len(result["interfaces"]) >= 1
        iface = result["interfaces"][0]
        assert iface.name == "IRepository"

    def test_interface_with_properties(self, extractor):
        code = '''
        public interface IUser
        {
            string? Id { get; }
            string Name { get; set; }
        }
        '''
        result = extractor.extract(code, "IUser.cs")
        assert len(result["interfaces"]) >= 1
        iface = result["interfaces"][0]
        assert iface.name == "IUser"


# ===== STRUCT EXTRACTION =====

class TestStructExtraction:
    """Tests for C# struct extraction."""

    def test_simple_struct(self, extractor):
        code = '''
        public struct Point
        {
            public double X { get; }
            public double Y { get; }
            public Point(double x, double y) { X = x; Y = y; }
        }
        '''
        result = extractor.extract(code, "Point.cs")
        assert len(result["structs"]) >= 1
        s = result["structs"][0]
        assert s.name == "Point"

    def test_readonly_struct(self, extractor):
        code = '''
        public readonly struct Money
        {
            public decimal Amount { get; }
            public string Currency { get; }
        }
        '''
        result = extractor.extract(code, "Money.cs")
        assert len(result["structs"]) >= 1
        s = result["structs"][0]
        assert s.name == "Money"
        assert s.is_readonly is True


# ===== RECORD EXTRACTION =====

class TestRecordExtraction:
    """Tests for C# record extraction (C# 9+)."""

    def test_simple_record(self, extractor):
        code = '''
        public record UserDto(string Name, string Email);
        '''
        result = extractor.extract(code, "UserDto.cs")
        assert len(result["records"]) >= 1
        rec = result["records"][0]
        assert rec.name == "UserDto"

    def test_record_class(self, extractor):
        code = '''
        public record class OrderSummary(int OrderId, decimal Total, DateTime OrderDate);
        '''
        result = extractor.extract(code, "OrderSummary.cs")
        assert len(result["records"]) >= 1
        rec = result["records"][0]
        assert rec.name == "OrderSummary"

    def test_record_struct(self, extractor):
        code = '''
        public record struct Coordinate(double Lat, double Lon);
        '''
        result = extractor.extract(code, "Coordinate.cs")
        assert len(result["records"]) >= 1
        rec = result["records"][0]
        assert rec.name == "Coordinate"
        assert rec.is_struct is True


# ===== DELEGATE EXTRACTION =====

class TestDelegateExtraction:
    """Tests for C# delegate extraction."""

    def test_simple_delegate(self, extractor):
        code = '''
        public delegate void EventHandler(object sender, EventArgs e);
        '''
        result = extractor.extract(code, "Delegates.cs")
        assert len(result["delegates"]) >= 1
        dlg = result["delegates"][0]
        assert dlg.name == "EventHandler"
        assert dlg.return_type == "void"

    def test_generic_delegate(self, extractor):
        code = '''
        public delegate Task<TResult> AsyncOperation<TInput, TResult>(TInput input);
        '''
        result = extractor.extract(code, "Delegates.cs")
        assert len(result["delegates"]) >= 1
        dlg = result["delegates"][0]
        assert dlg.name == "AsyncOperation"


# ===== FILE-SCOPED NAMESPACE =====

class TestFileScopedNamespace:
    """Tests for C# 10 file-scoped namespaces."""

    def test_file_scoped_namespace_class(self, extractor):
        code = '''
        namespace MyApp.Services;

        public class UserService
        {
            public void DoWork() { }
        }
        '''
        result = extractor.extract(code, "UserService.cs")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "UserService"

    def test_traditional_namespace(self, extractor):
        code = '''
        namespace MyApp.Services
        {
            public class OrderService
            {
                public void Process() { }
            }
        }
        '''
        result = extractor.extract(code, "OrderService.cs")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "OrderService"


# ===== MULTIPLE TYPES IN ONE FILE =====

class TestMultipleTypes:
    """Tests for extracting multiple types from a single file."""

    def test_class_and_interface(self, extractor):
        code = '''
        namespace MyApp;

        public interface IUserService
        {
            Task<User> GetUserAsync(int id);
        }

        public class UserService : IUserService
        {
            public async Task<User> GetUserAsync(int id) { return null; }
        }
        '''
        result = extractor.extract(code, "UserService.cs")
        assert len(result["classes"]) >= 1
        assert len(result["interfaces"]) >= 1
