"""
Tests for Entity Framework Core Enhanced Parser.

Tests DbContext extraction, entity detection, relationships,
migrations, query filters, interceptors.
Part of CodeTrellis v4.96 (Session 76)
"""

import pytest
from codetrellis.efcore_parser_enhanced import EnhancedEFCoreParser, EFCoreParseResult


# ── Fixtures ─────────────────────────────────────────────

SAMPLE_DB_CONTEXT = '''
using Microsoft.EntityFrameworkCore;

public class AppDbContext : DbContext
{
    public DbSet<Product> Products { get; set; }
    public DbSet<Order> Orders { get; set; }
    public DbSet<Customer> Customers { get; set; }

    protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
    {
        optionsBuilder.UseSqlServer("Server=.;Database=MyApp;");
    }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Product>()
            .HasOne(p => p.Category)
            .WithMany(c => c.Products)
            .HasForeignKey(p => p.CategoryId);

        modelBuilder.Entity<Order>()
            .HasMany(o => o.Items)
            .WithOne(i => i.Order);

        modelBuilder.Entity<Product>()
            .HasQueryFilter(p => !p.IsDeleted);

        modelBuilder.Entity<Product>()
            .HasData(new Product { Id = 1, Name = "Seed Product" });
    }
}
'''

SAMPLE_ENTITY_CONFIG = '''
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

public class ProductConfiguration : IEntityTypeConfiguration<Product>
{
    public void Configure(EntityTypeBuilder<Product> builder)
    {
        builder.HasKey(p => p.Id);
        builder.Property(p => p.Name).IsRequired().HasMaxLength(200);
        builder.HasIndex(p => p.Sku).IsUnique();
        builder.OwnsOne(p => p.Price);
    }
}

public class OrderConfiguration : IEntityTypeConfiguration<Order>
{
    public void Configure(EntityTypeBuilder<Order> builder)
    {
        builder.HasOne(o => o.Customer).WithMany(c => c.Orders);
    }
}
'''

SAMPLE_MIGRATION = '''
using Microsoft.EntityFrameworkCore.Migrations;

[DbContext(typeof(AppDbContext))]
[Migration("20240101_InitialCreate")]
public partial class InitialCreate : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.CreateTable("Products", table => new { });
    }

    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropTable("Products");
    }
}
'''

SAMPLE_INTERCEPTOR = '''
using Microsoft.EntityFrameworkCore.Diagnostics;

public class AuditSaveChangesInterceptor : SaveChangesInterceptor
{
    public override InterceptionResult<int> SavingChanges(DbContextEventData eventData, InterceptionResult<int> result)
    {
        return base.SavingChanges(eventData, result);
    }
}

public class SlowQueryInterceptor : DbCommandInterceptor
{
    public override DbCommand CommandCreated(CommandEndEventData eventData, DbCommand result)
    {
        return base.CommandCreated(eventData, result);
    }
}
'''

SAMPLE_COMPILED_QUERY = '''
using Microsoft.EntityFrameworkCore;

public static class ProductQueries
{
    public static readonly Func<AppDbContext, int, Product> GetById =
        EF.CompileQuery((AppDbContext ctx, int id) => ctx.Products.First(p => p.Id == id));

    public static IQueryable<ProductDto> GetProjected(AppDbContext ctx) =>
        ctx.Products.AsNoTracking().AsSplitQuery().Select(p => new ProductDto { Name = p.Name });

    public static async Task RawSql(AppDbContext ctx) =>
        await ctx.Products.FromSqlRaw("SELECT * FROM Products WHERE Active = 1").ToListAsync();
}
'''


# ── Tests ────────────────────────────────────────────────

class TestEnhancedEFCoreParser:
    """Tests for EnhancedEFCoreParser."""

    def setup_method(self):
        self.parser = EnhancedEFCoreParser()

    def test_is_efcore_file_context(self):
        assert self.parser.is_efcore_file(SAMPLE_DB_CONTEXT)

    def test_is_efcore_file_config(self):
        assert self.parser.is_efcore_file(SAMPLE_ENTITY_CONFIG)

    def test_is_efcore_file_negative(self):
        assert not self.parser.is_efcore_file("class Foo { }")
        assert not self.parser.is_efcore_file("")

    def test_parse_db_context(self):
        result = self.parser.parse(SAMPLE_DB_CONTEXT, "Data/AppDbContext.cs")
        assert isinstance(result, EFCoreParseResult)
        assert len(result.db_contexts) > 0
        assert result.total_db_sets >= 3  # Products, Orders, Customers

    def test_parse_relationships(self):
        result = self.parser.parse(SAMPLE_DB_CONTEXT, "Data/AppDbContext.cs")
        assert len(result.relationships) >= 1  # HasOne/WithMany, HasMany/WithOne

    def test_parse_entity_configuration(self):
        result = self.parser.parse(SAMPLE_ENTITY_CONFIG, "Config/ProductConfiguration.cs")
        assert len(result.entity_configs) >= 1

    def test_parse_migration(self):
        result = self.parser.parse(SAMPLE_MIGRATION, "Migrations/InitialCreate.cs")
        assert len(result.migrations) >= 1

    def test_parse_interceptors(self):
        result = self.parser.parse(SAMPLE_INTERCEPTOR, "Interceptors/AuditInterceptor.cs")
        assert len(result.interceptors) >= 1

    def test_parse_query_filters(self):
        result = self.parser.parse(SAMPLE_DB_CONTEXT, "Data/AppDbContext.cs")
        assert len(result.query_filters) >= 1  # HasQueryFilter

    def test_framework_detection(self):
        result = self.parser.parse(SAMPLE_DB_CONTEXT, "Data/AppDbContext.cs")
        assert len(result.detected_frameworks) > 0

    def test_empty_input(self):
        result = self.parser.parse("", "test.cs")
        assert len(result.db_contexts) == 0

    def test_non_efcore_file(self):
        result = self.parser.parse("public class Foo { void Bar() { } }", "Foo.cs")
        assert len(result.db_contexts) == 0
