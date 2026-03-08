"""
Tests for SQLTypeExtractor — tables, views, materialized views, custom types, domains, sequences, schemas.

Part of CodeTrellis v4.15 SQL Language Support.
"""

import pytest
from codetrellis.extractors.sql.type_extractor import SQLTypeExtractor


@pytest.fixture
def extractor():
    return SQLTypeExtractor()


# ===== TABLE EXTRACTION =====

class TestTableExtraction:
    """Tests for SQL table extraction."""

    def test_simple_create_table(self, extractor):
        code = '''
CREATE TABLE users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
'''
        result = extractor.extract(code, "schema.sql")
        assert len(result["tables"]) >= 1
        t = result["tables"][0]
        assert t.name == "users"
        assert len(t.columns) == 4
        assert t.columns[0].name == "id"
        assert t.columns[0].is_primary_key is True

    def test_table_with_schema(self, extractor):
        code = '''
CREATE TABLE public.orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    total NUMERIC(10,2) NOT NULL
);
'''
        result = extractor.extract(code, "orders.sql")
        tables = result["tables"]
        assert len(tables) >= 1
        assert tables[0].name == "orders"

    def test_if_not_exists(self, extractor):
        code = '''
CREATE TABLE IF NOT EXISTS products (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    price DECIMAL(10,2)
);
'''
        result = extractor.extract(code, "products.sql")
        assert len(result["tables"]) >= 1
        assert result["tables"][0].name == "products"

    def test_temporary_table(self, extractor):
        code = '''
CREATE TEMPORARY TABLE temp_results (
    id INT,
    score FLOAT
);
'''
        result = extractor.extract(code, "temp.sql")
        tables = result["tables"]
        assert len(tables) >= 1
        assert tables[0].is_temporary is True

    def test_mysql_table(self, extractor):
        code = '''
CREATE TABLE `products` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `price` DECIMAL(10,2) DEFAULT 0.00,
    `category_id` INT,
    KEY `idx_category` (`category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''
        result = extractor.extract(code, "products.sql")
        tables = result["tables"]
        assert len(tables) >= 1
        t = tables[0]
        assert t.name == "products"

    def test_sqlserver_table(self, extractor):
        code = '''
CREATE TABLE [dbo].[Orders] (
    [OrderID] INT IDENTITY(1,1) PRIMARY KEY,
    [CustomerName] NVARCHAR(200) NOT NULL,
    [OrderDate] DATETIME2 DEFAULT GETDATE(),
    [Total] MONEY NOT NULL
);
GO
'''
        result = extractor.extract(code, "orders.sql")
        tables = result["tables"]
        assert len(tables) >= 1

    def test_multiple_tables(self, extractor):
        code = '''
CREATE TABLE roles (
    id INT PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

CREATE TABLE user_roles (
    user_id INT REFERENCES users(id),
    role_id INT REFERENCES roles(id),
    PRIMARY KEY (user_id, role_id)
);
'''
        result = extractor.extract(code, "roles.sql")
        assert len(result["tables"]) >= 2


# ===== VIEW EXTRACTION =====

class TestViewExtraction:
    """Tests for SQL view extraction."""

    def test_simple_view(self, extractor):
        code = '''
CREATE VIEW active_users AS
SELECT id, name, email
FROM users
WHERE status = 'active';
'''
        result = extractor.extract(code, "views.sql")
        assert len(result["views"]) >= 1
        v = result["views"][0]
        assert v.name == "active_users"

    def test_view_or_replace(self, extractor):
        code = '''
CREATE OR REPLACE VIEW order_summary AS
SELECT u.name, COUNT(o.id) as order_count, SUM(o.total) as total_spent
FROM users u
JOIN orders o ON u.id = o.user_id
GROUP BY u.name;
'''
        result = extractor.extract(code, "views.sql")
        assert len(result["views"]) >= 1
        assert result["views"][0].name == "order_summary"


# ===== MATERIALIZED VIEW EXTRACTION =====

class TestMaterializedViewExtraction:
    """Tests for materialized view extraction."""

    def test_materialized_view(self, extractor):
        code = '''
CREATE MATERIALIZED VIEW monthly_revenue AS
SELECT date_trunc('month', created_at) AS month,
       SUM(total) AS revenue,
       COUNT(*) AS order_count
FROM orders
GROUP BY 1
WITH DATA;
'''
        result = extractor.extract(code, "matviews.sql")
        assert len(result["materialized_views"]) >= 1
        mv = result["materialized_views"][0]
        assert mv.name == "monthly_revenue"


# ===== CUSTOM TYPE EXTRACTION =====

class TestCustomTypeExtraction:
    """Tests for custom type extraction."""

    def test_enum_type(self, extractor):
        code = '''
CREATE TYPE order_status AS ENUM ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled');
'''
        result = extractor.extract(code, "types.sql")
        assert len(result["custom_types"]) >= 1
        ct = result["custom_types"][0]
        assert ct.name == "order_status"
        assert "pending" in ct.values

    def test_composite_type(self, extractor):
        code = '''
CREATE TYPE address AS (
    street TEXT,
    city TEXT,
    state VARCHAR(2),
    zip VARCHAR(10)
);
'''
        result = extractor.extract(code, "types.sql")
        assert len(result["custom_types"]) >= 1
        assert result["custom_types"][0].name == "address"


# ===== DOMAIN EXTRACTION =====

class TestDomainExtraction:
    """Tests for domain extraction."""

    def test_domain(self, extractor):
        code = '''
CREATE DOMAIN email_address AS VARCHAR(255)
    CHECK (VALUE ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$');
'''
        result = extractor.extract(code, "domains.sql")
        assert len(result["domains"]) >= 1
        d = result["domains"][0]
        assert d.name == "email_address"
        assert d.base_type == "VARCHAR(255)"


# ===== SEQUENCE EXTRACTION =====

class TestSequenceExtraction:
    """Tests for sequence extraction."""

    def test_sequence(self, extractor):
        code = '''
CREATE SEQUENCE order_seq
    START WITH 1000
    INCREMENT BY 1
    NO MAXVALUE
    CACHE 10;
'''
        result = extractor.extract(code, "sequences.sql")
        assert len(result["sequences"]) >= 1
        s = result["sequences"][0]
        assert s.name == "order_seq"


# ===== SCHEMA EXTRACTION =====

class TestSchemaExtraction:
    """Tests for schema extraction."""

    def test_create_schema(self, extractor):
        code = '''
CREATE SCHEMA IF NOT EXISTS analytics AUTHORIZATION admin_user;
'''
        result = extractor.extract(code, "schemas.sql")
        assert len(result["schemas"]) >= 1
        s = result["schemas"][0]
        assert s.name == "analytics"


# ===== DIALECT DETECTION =====

class TestDialectDetection:
    """Tests for SQL dialect auto-detection."""

    def test_postgresql_dialect(self, extractor):
        code = '''
CREATE TABLE events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_events_data ON events USING GIN (data);
'''
        result = extractor.extract(code, "events.sql")
        tables = result["tables"]
        assert len(tables) >= 1
        assert tables[0].dialect == "postgresql"

    def test_mysql_dialect(self, extractor):
        code = '''
CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''
        result = extractor.extract(code, "users.sql")
        tables = result["tables"]
        assert len(tables) >= 1
        assert tables[0].dialect == "mysql"
