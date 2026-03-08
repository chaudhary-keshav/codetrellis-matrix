"""
Tests for Dapper Enhanced Parser.

Tests query extraction, repository detection, type handlers, multi-mapping.
Part of CodeTrellis v4.96 (Session 76)
"""

import pytest
from codetrellis.dapper_parser_enhanced import EnhancedDapperParser, DapperParseResult


# ── Fixtures ─────────────────────────────────────────────

SAMPLE_REPOSITORY = '''
using Dapper;
using System.Data;

public class ProductRepository : IProductRepository
{
    private readonly IDbConnection _connection;

    public ProductRepository(IDbConnection connection) => _connection = connection;

    public async Task<Product> GetByIdAsync(int id)
    {
        return await _connection.QueryFirstOrDefaultAsync<Product>(
            "SELECT * FROM Products WHERE Id = @Id",
            new { Id = id }
        );
    }

    public async Task<IEnumerable<Product>> GetAllAsync()
    {
        return await _connection.QueryAsync<Product>(
            "SELECT * FROM Products WHERE IsActive = 1"
        );
    }

    public async Task<int> CreateAsync(Product product)
    {
        return await _connection.ExecuteAsync(
            "INSERT INTO Products (Name, Price) VALUES (@Name, @Price)",
            product
        );
    }

    public async Task<int> DeleteAsync(int id)
    {
        return await _connection.ExecuteAsync(
            "DELETE FROM Products WHERE Id = @Id",
            new { Id = id }
        );
    }
}
'''

SAMPLE_STORED_PROC = '''
using Dapper;
using System.Data;

public class ReportRepository
{
    private readonly SqlConnection _conn;

    public async Task<Report> GetReportAsync(int year)
    {
        return await _conn.QueryFirstAsync<Report>(
            "sp_GetAnnualReport",
            new { Year = year },
            commandType: CommandType.StoredProcedure
        );
    }

    public async Task<int> GetCountAsync()
    {
        return await _conn.ExecuteScalarAsync<int>("SELECT COUNT(*) FROM Products");
    }
}
'''

SAMPLE_MULTI_MAPPING = '''
using Dapper;

public class OrderRepository
{
    private readonly IDbConnection _conn;

    public async Task<IEnumerable<Order>> GetOrdersWithCustomersAsync()
    {
        return await _conn.QueryAsync<Order, Customer, Order>(
            "SELECT o.*, c.* FROM Orders o INNER JOIN Customers c ON o.CustomerId = c.Id",
            (order, customer) => { order.Customer = customer; return order; },
            splitOn: "CustomerId"
        );
    }
}
'''

SAMPLE_TYPE_HANDLER = '''
using Dapper;

public class JsonTypeHandler<T> : SqlMapper.TypeHandler<T>
{
    public override void SetValue(IDbDataParameter parameter, T value)
    {
        parameter.Value = JsonSerializer.Serialize(value);
    }

    public override T Parse(object value)
    {
        return JsonSerializer.Deserialize<T>((string)value);
    }
}
'''

SAMPLE_QUERY_MULTIPLE = '''
using Dapper;

public class DashboardRepository
{
    private readonly IDbConnection _conn;

    public async Task<Dashboard> GetDashboardAsync()
    {
        using var multi = await _conn.QueryMultipleAsync(
            "SELECT COUNT(*) FROM Products; SELECT COUNT(*) FROM Orders;"
        );
        var productCount = await multi.ReadSingleAsync<int>();
        var orderCount = await multi.ReadSingleAsync<int>();
        return new Dashboard { ProductCount = productCount, OrderCount = orderCount };
    }
}
'''

SAMPLE_CONTRIB = '''
using Dapper;
using Dapper.Contrib.Extensions;

public class ProductContribRepository
{
    private readonly IDbConnection _conn;

    public async Task<Product> GetByIdAsync(int id)
    {
        return await _conn.Get<Product>(id);
    }

    public async Task<IEnumerable<Product>> GetAllAsync()
    {
        return await _conn.GetAll<Product>();
    }

    public async Task<long> InsertAsync(Product product)
    {
        return await _conn.Insert<Product>(product);
    }

    public async Task<bool> UpdateAsync(Product product)
    {
        return await _conn.Update<Product>(product);
    }

    public async Task<bool> DeleteAsync(Product product)
    {
        return await _conn.Delete<Product>(product);
    }
}
'''

SAMPLE_TRANSACTION = '''
using Dapper;
using System.Data;

public class OrderService
{
    private readonly IDbConnection _conn;

    public async Task<int> CreateOrderWithItemsAsync(Order order, List<OrderItem> items)
    {
        using var transaction = _conn.BeginTransaction();
        try
        {
            var orderId = await _conn.ExecuteScalarAsync<int>(
                "INSERT INTO Orders (CustomerId, Total) VALUES (@CustomerId, @Total); SELECT SCOPE_IDENTITY();",
                order,
                transaction: transaction
            );

            foreach (var item in items)
            {
                item.OrderId = orderId;
                await _conn.ExecuteAsync(
                    "INSERT INTO OrderItems (OrderId, ProductId, Quantity) VALUES (@OrderId, @ProductId, @Quantity)",
                    item,
                    transaction: transaction
                );
            }

            transaction.Commit();
            return orderId;
        }
        catch
        {
            transaction.Rollback();
            throw;
        }
    }
}
'''


# ── Tests ────────────────────────────────────────────────

class TestEnhancedDapperParser:
    """Tests for EnhancedDapperParser."""

    def setup_method(self):
        self.parser = EnhancedDapperParser()

    def test_is_dapper_file_repository(self):
        assert self.parser.is_dapper_file(SAMPLE_REPOSITORY)

    def test_is_dapper_file_stored_proc(self):
        assert self.parser.is_dapper_file(SAMPLE_STORED_PROC)

    def test_is_dapper_file_negative(self):
        assert not self.parser.is_dapper_file("class Foo { }")
        assert not self.parser.is_dapper_file("")

    def test_parse_queries(self):
        result = self.parser.parse(SAMPLE_REPOSITORY, "Repositories/ProductRepository.cs")
        assert isinstance(result, DapperParseResult)
        assert result.total_queries >= 3  # Query + QueryFirstOrDefault + Execute x2

    def test_parse_async_queries(self):
        result = self.parser.parse(SAMPLE_REPOSITORY, "Repositories/ProductRepository.cs")
        assert result.total_async_queries >= 2

    def test_parse_stored_procedures(self):
        result = self.parser.parse(SAMPLE_STORED_PROC, "Repositories/ReportRepository.cs")
        assert result.total_stored_procs >= 1

    def test_parse_repository(self):
        result = self.parser.parse(SAMPLE_REPOSITORY, "Repositories/ProductRepository.cs")
        assert result.total_repositories >= 1
        repo = result.repositories[0]
        assert repo.get('name') == 'ProductRepository'
        assert repo.get('interface_name') == 'IProductRepository'

    def test_parse_multi_mapping(self):
        result = self.parser.parse(SAMPLE_MULTI_MAPPING, "Repositories/OrderRepository.cs")
        assert len(result.multi_mappings) >= 1
        mm = result.multi_mappings[0]
        assert 'Order' in mm.get('types', []) or 'Customer' in mm.get('types', [])
        assert mm.get('split_on') == 'CustomerId'

    def test_parse_type_handler(self):
        result = self.parser.parse(SAMPLE_TYPE_HANDLER, "Handlers/JsonTypeHandler.cs")
        assert len(result.type_handlers) >= 1

    def test_parse_query_multiple(self):
        result = self.parser.parse(SAMPLE_QUERY_MULTIPLE, "Repositories/DashboardRepository.cs")
        assert result.total_queries >= 1
        query_types = [q.get('query_type') for q in result.queries]
        assert "query-multiple" in query_types

    def test_parse_contrib(self):
        result = self.parser.parse(SAMPLE_CONTRIB, "Repositories/ProductContribRepository.cs")
        assert result.total_queries >= 3  # Get, GetAll, Insert, Update, Delete

    def test_parse_transaction(self):
        result = self.parser.parse(SAMPLE_TRANSACTION, "Services/OrderService.cs")
        assert result.total_queries >= 2
        assert any(q.get('has_transaction') for q in result.queries)

    def test_framework_detection(self):
        result = self.parser.parse(SAMPLE_REPOSITORY, "test.cs")
        assert len(result.detected_frameworks) > 0

    def test_file_classification(self):
        result = self.parser.parse(SAMPLE_REPOSITORY, "Repositories/ProductRepository.cs")
        assert result.file_type == "repository"

    def test_empty_input(self):
        result = self.parser.parse("", "test.cs")
        assert result.total_queries == 0
