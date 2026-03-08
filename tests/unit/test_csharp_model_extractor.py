"""
Tests for CSharpModelExtractor — EF Core entities, DbContext, repositories, DTOs.

Part of CodeTrellis v4.13 C# Language Support.
"""

import pytest
from codetrellis.extractors.csharp.model_extractor import CSharpModelExtractor


@pytest.fixture
def extractor():
    return CSharpModelExtractor()


# ===== DBCONTEXT EXTRACTION =====

class TestDbContextExtraction:
    """Tests for EF Core DbContext extraction."""

    def test_simple_dbcontext(self, extractor):
        code = '''
        public class AppDbContext : DbContext
        {
            public DbSet<User> Users { get; set; }
            public DbSet<Order> Orders { get; set; }
            public DbSet<Product> Products { get; set; }
        }
        '''
        result = extractor.extract(code, "AppDbContext.cs")
        assert len(result["db_contexts"]) >= 1
        ctx = result["db_contexts"][0]
        assert ctx.name == "AppDbContext"
        assert len(ctx.db_sets) >= 2

    def test_identity_dbcontext(self, extractor):
        code = '''
        public class ApplicationDbContext : IdentityDbContext<ApplicationUser>
        {
            public DbSet<TodoItem> TodoItems { get; set; }

            protected override void OnModelCreating(ModelBuilder builder)
            {
                base.OnModelCreating(builder);
                builder.Entity<TodoItem>().HasIndex(t => t.Title);
            }
        }
        '''
        result = extractor.extract(code, "ApplicationDbContext.cs")
        assert len(result["db_contexts"]) >= 1
        ctx = result["db_contexts"][0]
        assert ctx.name == "ApplicationDbContext"
        assert ctx.has_on_model_creating is True


# ===== ENTITY EXTRACTION =====

class TestEntityExtraction:
    """Tests for EF Core entity/model extraction."""

    def test_entity_with_annotations(self, extractor):
        code = '''
        [Table("orders")]
        public class Order
        {
            [Key]
            public int Id { get; set; }

            [Required]
            public string Description { get; set; }

            public DateTime OrderDate { get; set; }

            public int BuyerId { get; set; }
            public Buyer Buyer { get; set; }
        }
        '''
        result = extractor.extract(code, "Order.cs")
        assert len(result["entities"]) >= 1
        entity = result["entities"][0]
        assert entity.name == "Order"

    def test_keyless_entity(self, extractor):
        code = '''
        [Keyless]
        public class OrderSummary
        {
            public int TotalOrders { get; set; }
            public decimal TotalRevenue { get; set; }
        }
        '''
        result = extractor.extract(code, "OrderSummary.cs")
        assert len(result["entities"]) >= 1
        entity = result["entities"][0]
        assert entity.name == "OrderSummary"
        assert entity.is_keyless is True


# ===== DTO/VIEWMODEL EXTRACTION =====

class TestDtoExtraction:
    """Tests for DTO/ViewModel extraction."""

    def test_dto_class(self, extractor):
        code = '''
        public class UserDto
        {
            public int Id { get; set; }
            public string Name { get; set; }
            public string Email { get; set; }
        }
        '''
        result = extractor.extract(code, "UserDto.cs")
        assert len(result["dtos"]) >= 1
        dto = result["dtos"][0]
        assert dto.name == "UserDto"
        assert dto.kind == "dto"

    def test_viewmodel_class(self, extractor):
        code = '''
        public class LoginViewModel
        {
            public string Email { get; set; }
            public string Password { get; set; }
            public bool RememberMe { get; set; }
        }
        '''
        result = extractor.extract(code, "LoginViewModel.cs")
        assert len(result["dtos"]) >= 1
        dto = result["dtos"][0]
        assert dto.name == "LoginViewModel"
        assert dto.kind == "viewmodel"

    def test_request_class(self, extractor):
        code = '''
        public class CreateOrderRequest
        {
            public string ProductId { get; set; }
            public int Quantity { get; set; }
        }
        '''
        result = extractor.extract(code, "CreateOrderRequest.cs")
        assert len(result["dtos"]) >= 1
        dto = result["dtos"][0]
        assert dto.name == "CreateOrderRequest"
        assert dto.kind == "request"

    def test_response_class(self, extractor):
        code = '''
        public class OrderResponse
        {
            public int OrderId { get; set; }
            public string Status { get; set; }
        }
        '''
        result = extractor.extract(code, "OrderResponse.cs")
        assert len(result["dtos"]) >= 1
        dto = result["dtos"][0]
        assert dto.name == "OrderResponse"
        assert dto.kind == "response"

    def test_command_class(self, extractor):
        code = '''
        public class CancelOrderCommand
        {
            public int OrderNumber { get; set; }
        }
        '''
        result = extractor.extract(code, "CancelOrderCommand.cs")
        assert len(result["dtos"]) >= 1
        dto = result["dtos"][0]
        assert dto.name == "CancelOrderCommand"
        assert dto.kind == "command"

    def test_query_class(self, extractor):
        code = '''
        public class GetOrdersQuery
        {
            public int UserId { get; set; }
            public int Page { get; set; }
        }
        '''
        result = extractor.extract(code, "GetOrdersQuery.cs")
        assert len(result["dtos"]) >= 1
        dto = result["dtos"][0]
        assert dto.name == "GetOrdersQuery"
        assert dto.kind == "query"

    def test_record_dto(self, extractor):
        code = '''
        public record OrderItemDto(int ProductId, string ProductName, decimal UnitPrice, int Quantity);
        '''
        result = extractor.extract(code, "OrderItemDto.cs")
        assert len(result["dtos"]) >= 1
        dto = result["dtos"][0]
        assert dto.name == "OrderItemDto"
        assert dto.is_record is True


# ===== REPOSITORY EXTRACTION =====

class TestRepositoryExtraction:
    """Tests for repository pattern extraction."""

    def test_repository_interface(self, extractor):
        code = '''
        public interface IOrderRepository : IRepository<Order>
        {
            Task<Order> GetAsync(int orderId);
            Order Add(Order order);
            void Update(Order order);
        }
        '''
        result = extractor.extract(code, "IOrderRepository.cs")
        assert len(result["repositories"]) >= 1
        repo = result["repositories"][0]
        assert repo.name == "IOrderRepository"

    def test_repository_class(self, extractor):
        code = '''
        public class OrderRepository : IOrderRepository
        {
            private readonly AppDbContext _context;

            public OrderRepository(AppDbContext context)
            {
                _context = context;
            }

            public async Task<Order> GetAsync(int orderId)
            {
                return await _context.Orders.FindAsync(orderId);
            }

            public Order Add(Order order)
            {
                return _context.Orders.Add(order).Entity;
            }

            public void Update(Order order)
            {
                _context.Entry(order).State = EntityState.Modified;
            }
        }
        '''
        result = extractor.extract(code, "OrderRepository.cs")
        assert len(result["repositories"]) >= 1
        repo = result["repositories"][0]
        assert repo.name == "OrderRepository"
