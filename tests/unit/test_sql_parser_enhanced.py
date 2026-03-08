"""
Tests for EnhancedSQLParser — full integration test of all SQL extractors.

Part of CodeTrellis v4.15 SQL Language Support.
"""

import pytest
from codetrellis.sql_parser_enhanced import EnhancedSQLParser


@pytest.fixture
def parser():
    return EnhancedSQLParser()


class TestSQLParserDialectDetection:
    """Tests for SQL dialect auto-detection."""

    def test_postgresql_detection(self, parser):
        code = '''
CREATE TABLE events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    data JSONB NOT NULL,
    tags TEXT[],
    created_at TIMESTAMPTZ DEFAULT now()
);
'''
        result = parser.parse(code, "events.sql")
        assert result.dialect == "postgresql"

    def test_mysql_detection(self, parser):
        code = '''
CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `status` ENUM('active', 'inactive') DEFAULT 'active'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''
        result = parser.parse(code, "users.sql")
        assert result.dialect == "mysql"

    def test_sqlserver_detection(self, parser):
        code = '''
CREATE TABLE [dbo].[Products] (
    [ProductID] INT IDENTITY(1,1) PRIMARY KEY,
    [Name] NVARCHAR(200) NOT NULL,
    [Price] MONEY NOT NULL
);
GO
'''
        result = parser.parse(code, "products.sql")
        assert result.dialect == "sqlserver"

    def test_sqlite_detection(self, parser):
        code = '''
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
) STRICT;
'''
        result = parser.parse(code, "users.sql")
        assert result.dialect == "sqlite"


class TestSQLParserFullParse:
    """Integration tests for full SQL file parsing."""

    def test_complete_schema(self, parser):
        code = '''
-- Schema for an e-commerce application

CREATE SCHEMA IF NOT EXISTS ecommerce;

CREATE TYPE order_status AS ENUM ('pending', 'confirmed', 'shipped', 'delivered');

CREATE SEQUENCE order_seq START WITH 1000;

CREATE TABLE ecommerce.users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE ecommerce.orders (
    id BIGINT DEFAULT nextval('order_seq') PRIMARY KEY,
    user_id BIGINT REFERENCES ecommerce.users(id) ON DELETE CASCADE,
    status order_status NOT NULL DEFAULT 'pending',
    total NUMERIC(12,2) NOT NULL CHECK (total >= 0),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_orders_user ON ecommerce.orders (user_id);
CREATE INDEX idx_orders_status ON ecommerce.orders (status) WHERE status != 'delivered';

CREATE VIEW ecommerce.active_orders AS
SELECT o.*, u.name AS user_name
FROM ecommerce.orders o
JOIN ecommerce.users u ON o.user_id = u.id
WHERE o.status IN ('pending', 'confirmed');

CREATE OR REPLACE FUNCTION ecommerce.update_modified()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_orders_updated
    BEFORE UPDATE ON ecommerce.orders
    FOR EACH ROW
    EXECUTE FUNCTION ecommerce.update_modified();

GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA ecommerce TO app_user;
'''
        result = parser.parse(code, "ecommerce_schema.sql")

        assert result.dialect == "postgresql"
        assert len(result.tables) >= 2
        assert len(result.views) >= 1
        assert len(result.indexes) >= 2
        assert len(result.functions) >= 1
        assert len(result.triggers) >= 1
        assert len(result.schemas) >= 1
        assert len(result.sequences) >= 1
        assert len(result.custom_types) >= 1
        assert len(result.grants) >= 1
        assert result.statement_count >= 5

    def test_empty_content(self, parser):
        result = parser.parse("", "empty.sql")
        assert result.file_type == "sql"
        assert len(result.tables) == 0

    def test_comments_only(self, parser):
        code = '''
-- This is a comment
/* Multi-line
   comment */
'''
        result = parser.parse(code, "comments.sql")
        assert len(result.comments) >= 1

    def test_dependencies_extraction(self, parser):
        code = '''
SELECT u.name, o.total
FROM users u
JOIN orders o ON u.id = o.user_id
LEFT JOIN products p ON o.product_id = p.id;
'''
        result = parser.parse(code, "query.sql")
        assert "users" in result.dependencies or "orders" in result.dependencies

    def test_framework_detection_postgis(self, parser):
        code = '''
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    geom GEOMETRY(Point, 4326) NOT NULL
);

CREATE INDEX idx_locations_geom ON locations USING GIST (geom);
'''
        result = parser.parse(code, "spatial.sql")
        assert "postgis" in result.detected_frameworks or "pg-ext:postgis" in result.detected_frameworks


class TestSQLParserMigration:
    """Tests for migration detection through the parser."""

    def test_migration_file(self, parser):
        code = '''
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(100),
    record_id BIGINT,
    old_data JSONB,
    new_data JSONB,
    performed_by BIGINT REFERENCES users(id),
    performed_at TIMESTAMPTZ DEFAULT now()
);
'''
        result = parser.parse(code, "V5__create_audit_log.sql")
        assert result.is_migration is True
        assert result.migration is not None
        assert result.migration.framework == "flyway"
        assert "audit_log" in result.migration.tables_created


class TestSQLParserProjectType:
    """Tests for SQL project type detection."""

    def test_migration_heavy_project(self):
        files = [
            "migrations/V1__init.sql",
            "migrations/V2__add_users.sql",
            "migrations/V3__add_orders.sql",
            "migrations/V4__add_products.sql",
            "schema/seed.sql",
        ]
        result = EnhancedSQLParser.detect_sql_project_type(files)
        assert result["migration_count"] >= 4
        assert result["migration_framework"] == "flyway"

    def test_golang_migrate_project(self):
        files = [
            "db/migrations/000001_init.up.sql",
            "db/migrations/000001_init.down.sql",
            "db/migrations/000002_users.up.sql",
            "db/migrations/000002_users.down.sql",
        ]
        result = EnhancedSQLParser.detect_sql_project_type(files)
        assert result["migration_framework"] == "golang-migrate"

    def test_schema_definition_project(self):
        files = [
            "schema/tables.sql",
            "schema/create_users.sql",
            "schema/init_database.sql",
        ]
        result = EnhancedSQLParser.detect_sql_project_type(files)
        assert result["schema_count"] >= 2
