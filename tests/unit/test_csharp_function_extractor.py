"""
Tests for CSharpFunctionExtractor — methods, constructors, events.

Part of CodeTrellis v4.13 C# Language Support.
"""

import pytest
from codetrellis.extractors.csharp.function_extractor import CSharpFunctionExtractor


@pytest.fixture
def extractor():
    return CSharpFunctionExtractor()


# ===== METHOD EXTRACTION =====

class TestMethodExtraction:
    """Tests for C# method extraction."""

    def test_simple_public_method(self, extractor):
        code = '''
        public class UserService
        {
            public string GetName()
            {
                return "test";
            }
        }
        '''
        result = extractor.extract(code, "UserService.cs")
        methods = [m for m in result["methods"] if m.name == "GetName"]
        assert len(methods) >= 1
        method = methods[0]
        assert method.return_type is not None

    def test_async_method(self, extractor):
        code = '''
        public class OrderService
        {
            public async Task<Order> GetOrderAsync(int orderId)
            {
                return await _repo.FindAsync(orderId);
            }
        }
        '''
        result = extractor.extract(code, "OrderService.cs")
        methods = [m for m in result["methods"] if m.name == "GetOrderAsync"]
        assert len(methods) >= 1
        method = methods[0]
        assert method.is_async is True

    def test_static_method(self, extractor):
        code = '''
        public static class MathHelper
        {
            public static int Add(int a, int b)
            {
                return a + b;
            }
        }
        '''
        result = extractor.extract(code, "MathHelper.cs")
        methods = [m for m in result["methods"] if m.name == "Add"]
        assert len(methods) >= 1
        method = methods[0]
        assert method.is_static is True

    def test_virtual_method(self, extractor):
        code = '''
        public class BaseService
        {
            public virtual void Process()
            {
            }
        }
        '''
        result = extractor.extract(code, "BaseService.cs")
        methods = [m for m in result["methods"] if m.name == "Process"]
        assert len(methods) >= 1
        method = methods[0]
        assert method.is_virtual is True

    def test_override_method(self, extractor):
        code = '''
        public class UserService : BaseService
        {
            public override void Process()
            {
                base.Process();
            }
        }
        '''
        result = extractor.extract(code, "UserService.cs")
        methods = [m for m in result["methods"] if m.name == "Process"]
        assert len(methods) >= 1
        method = methods[0]
        assert method.is_override is True

    def test_method_with_parameters(self, extractor):
        code = '''
        public class Calculator
        {
            public decimal Calculate(decimal amount, decimal rate, int years)
            {
                return amount * rate * years;
            }
        }
        '''
        result = extractor.extract(code, "Calculator.cs")
        methods = [m for m in result["methods"] if m.name == "Calculate"]
        assert len(methods) >= 1
        method = methods[0]
        assert len(method.parameters) >= 2

    def test_expression_bodied_method(self, extractor):
        code = '''
        public class Person
        {
            private string _name;
            public string GetName() => _name;
        }
        '''
        result = extractor.extract(code, "Person.cs")
        methods = [m for m in result["methods"] if m.name == "GetName"]
        assert len(methods) >= 1

    def test_method_with_generic_return(self, extractor):
        code = '''
        public class Repository<T>
        {
            public Task<IEnumerable<T>> GetAllAsync()
            {
                return Task.FromResult(Enumerable.Empty<T>());
            }
        }
        '''
        result = extractor.extract(code, "Repository.cs")
        methods = [m for m in result["methods"] if m.name == "GetAllAsync"]
        assert len(methods) >= 1


# ===== CONSTRUCTOR EXTRACTION =====

class TestConstructorExtraction:
    """Tests for C# constructor extraction."""

    def test_simple_constructor(self, extractor):
        code = '''
        public class UserService
        {
            private readonly ILogger _logger;

            public UserService(ILogger<UserService> logger)
            {
                _logger = logger;
            }
        }
        '''
        result = extractor.extract(code, "UserService.cs")
        assert len(result["constructors"]) >= 1
        ctor = result["constructors"][0]
        assert ctor.class_name == "UserService"
        assert len(ctor.parameters) >= 1

    def test_constructor_with_base_call(self, extractor):
        code = '''
        public class AdminService : BaseService
        {
            public AdminService(ILogger logger) : base(logger)
            {
            }
        }
        '''
        result = extractor.extract(code, "AdminService.cs")
        assert len(result["constructors"]) >= 1
        ctor = result["constructors"][0]
        assert ctor.class_name == "AdminService"
        assert ctor.calls_base is True


# ===== EVENT EXTRACTION =====

class TestEventExtraction:
    """Tests for C# event extraction."""

    def test_simple_event(self, extractor):
        code = '''
        public class EventBus
        {
            public event EventHandler<OrderCreatedArgs> OrderCreated;
            public event EventHandler ConnectionLost;
        }
        '''
        result = extractor.extract(code, "EventBus.cs")
        assert len(result["events"]) >= 1
