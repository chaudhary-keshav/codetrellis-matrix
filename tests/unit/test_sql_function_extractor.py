"""
Tests for SQLFunctionExtractor — functions, stored procedures, triggers, events.

Part of CodeTrellis v4.15 SQL Language Support.
"""

import pytest
from codetrellis.extractors.sql.function_extractor import SQLFunctionExtractor


@pytest.fixture
def extractor():
    return SQLFunctionExtractor()


# ===== FUNCTION EXTRACTION =====

class TestFunctionExtraction:
    """Tests for SQL function extraction."""

    def test_simple_function(self, extractor):
        code = '''
CREATE OR REPLACE FUNCTION calculate_total(order_id BIGINT)
RETURNS NUMERIC AS $$
BEGIN
    RETURN (SELECT SUM(quantity * price) FROM order_items WHERE order_items.order_id = calculate_total.order_id);
END;
$$ LANGUAGE plpgsql STABLE;
'''
        result = extractor.extract(code, "functions.sql")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "calculate_total"
        assert f.return_type == "NUMERIC"
        assert f.language == "plpgsql"
        assert len(f.parameters) >= 1
        assert f.parameters[0].name == "order_id"

    def test_function_returns_table(self, extractor):
        code = '''
CREATE FUNCTION get_user_orders(p_user_id INT)
RETURNS TABLE (order_id BIGINT, total NUMERIC, created_at TIMESTAMPTZ) AS $$
BEGIN
    RETURN QUERY SELECT o.id, o.total, o.created_at
    FROM orders o WHERE o.user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;
'''
        result = extractor.extract(code, "functions.sql")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "get_user_orders"

    def test_immutable_function(self, extractor):
        code = '''
CREATE FUNCTION full_name(first_name TEXT, last_name TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN first_name || ' ' || last_name;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
'''
        result = extractor.extract(code, "functions.sql")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "full_name"
        assert f.volatility == "IMMUTABLE"

    def test_sql_language_function(self, extractor):
        code = '''
CREATE FUNCTION user_count()
RETURNS INTEGER AS $$
    SELECT COUNT(*)::INTEGER FROM users;
$$ LANGUAGE SQL STABLE;
'''
        result = extractor.extract(code, "functions.sql")
        assert len(result["functions"]) >= 1


# ===== STORED PROCEDURE EXTRACTION =====

class TestStoredProcedureExtraction:
    """Tests for stored procedure extraction."""

    def test_postgresql_procedure(self, extractor):
        code = '''
CREATE OR REPLACE PROCEDURE transfer_funds(
    sender_id BIGINT,
    receiver_id BIGINT,
    amount NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE accounts SET balance = balance - amount WHERE id = sender_id;
    UPDATE accounts SET balance = balance + amount WHERE id = receiver_id;
    COMMIT;
END;
$$;
'''
        result = extractor.extract(code, "procedures.sql")
        assert len(result["procedures"]) >= 1
        p = result["procedures"][0]
        assert p.name == "transfer_funds"
        assert len(p.parameters) == 3

    def test_tsql_procedure(self, extractor):
        code = '''
CREATE PROCEDURE usp_GetOrdersByCustomer
    @CustomerId INT,
    @Status NVARCHAR(50) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    SELECT OrderID, OrderDate, Total
    FROM Orders
    WHERE CustomerID = @CustomerId
      AND (@Status IS NULL OR Status = @Status);
END;
GO
'''
        result = extractor.extract(code, "procedures.sql")
        assert len(result["procedures"]) >= 1
        p = result["procedures"][0]
        assert p.name == "usp_GetOrdersByCustomer"


# ===== TRIGGER EXTRACTION =====

class TestTriggerExtraction:
    """Tests for trigger extraction."""

    def test_simple_trigger(self, extractor):
        code = '''
CREATE TRIGGER update_timestamp
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();
'''
        result = extractor.extract(code, "triggers.sql")
        assert len(result["triggers"]) >= 1
        t = result["triggers"][0]
        assert t.name == "update_timestamp"
        assert t.table_name == "users"
        assert "UPDATE" in t.events
        assert t.timing == "BEFORE"

    def test_after_insert_trigger(self, extractor):
        code = '''
CREATE TRIGGER audit_orders
    AFTER INSERT OR UPDATE OR DELETE ON orders
    FOR EACH ROW
    EXECUTE PROCEDURE log_order_changes();
'''
        result = extractor.extract(code, "triggers.sql")
        assert len(result["triggers"]) >= 1
        t = result["triggers"][0]
        assert t.name == "audit_orders"
        assert "INSERT" in t.events


# ===== EVENT EXTRACTION =====

class TestEventExtraction:
    """Tests for MySQL event extraction."""

    def test_mysql_event(self, extractor):
        code = '''
CREATE EVENT cleanup_old_sessions
ON SCHEDULE EVERY 1 HOUR
DO
    DELETE FROM sessions WHERE expires_at < NOW();
'''
        result = extractor.extract(code, "events.sql")
        assert len(result["events"]) >= 1
        e = result["events"][0]
        assert e.name == "cleanup_old_sessions"
        assert "EVERY 1 HOUR" in e.schedule


# ===== CTE EXTRACTION =====

class TestCTEExtraction:
    """Tests for CTE extraction."""

    def test_simple_cte(self, extractor):
        code = '''
WITH active_users AS (
    SELECT id, name FROM users WHERE status = 'active'
),
user_orders AS (
    SELECT user_id, COUNT(*) AS order_count
    FROM orders
    GROUP BY user_id
)
SELECT au.name, COALESCE(uo.order_count, 0) AS orders
FROM active_users au
LEFT JOIN user_orders uo ON au.id = uo.user_id;
'''
        result = extractor.extract(code, "queries.sql")
        ctes = result.get("ctes", [])
        assert len(ctes) >= 2
        assert ctes[0]['name'] == "active_users"
        assert ctes[1]['name'] == "user_orders"

    def test_recursive_cte(self, extractor):
        code = '''
WITH RECURSIVE org_tree AS (
    SELECT id, name, parent_id, 0 AS depth
    FROM departments
    WHERE parent_id IS NULL
    UNION ALL
    SELECT d.id, d.name, d.parent_id, ot.depth + 1
    FROM departments d
    JOIN org_tree ot ON d.parent_id = ot.id
)
SELECT * FROM org_tree;
'''
        result = extractor.extract(code, "recursive.sql")
        ctes = result.get("ctes", [])
        assert len(ctes) >= 1
        assert ctes[0]['name'] == "org_tree"
