"""
Tests for SQLIndexExtractor, SQLSecurityExtractor, SQLMigrationExtractor.

Part of CodeTrellis v4.15 SQL Language Support.
"""

import pytest
from codetrellis.extractors.sql.index_extractor import SQLIndexExtractor
from codetrellis.extractors.sql.security_extractor import SQLSecurityExtractor
from codetrellis.extractors.sql.migration_extractor import SQLMigrationExtractor


# ===== INDEX EXTRACTION =====

class TestIndexExtraction:
    """Tests for SQL index extraction."""

    @pytest.fixture
    def extractor(self):
        return SQLIndexExtractor()

    def test_simple_index(self, extractor):
        code = '''
CREATE INDEX idx_users_email ON users (email);
'''
        result = extractor.extract(code, "indexes.sql")
        assert len(result["indexes"]) >= 1
        idx = result["indexes"][0]
        assert idx.name == "idx_users_email"
        assert idx.table_name == "users"
        assert "email" in idx.columns

    def test_unique_index(self, extractor):
        code = '''
CREATE UNIQUE INDEX idx_users_username ON users (username);
'''
        result = extractor.extract(code, "indexes.sql")
        assert len(result["indexes"]) >= 1
        assert result["indexes"][0].is_unique is True

    def test_composite_index(self, extractor):
        code = '''
CREATE INDEX idx_orders_user_date ON orders (user_id, created_at DESC);
'''
        result = extractor.extract(code, "indexes.sql")
        assert len(result["indexes"]) >= 1
        idx = result["indexes"][0]
        assert len(idx.columns) >= 2

    def test_concurrent_index(self, extractor):
        code = '''
CREATE INDEX CONCURRENTLY idx_events_type ON events (event_type);
'''
        result = extractor.extract(code, "indexes.sql")
        assert len(result["indexes"]) >= 1
        assert result["indexes"][0].is_concurrent is True

    def test_gin_index(self, extractor):
        code = '''
CREATE INDEX idx_products_metadata ON products USING GIN (metadata);
'''
        result = extractor.extract(code, "indexes.sql")
        assert len(result["indexes"]) >= 1
        assert result["indexes"][0].method.lower() == "gin"

    def test_foreign_key(self, extractor):
        code = '''
ALTER TABLE order_items
    ADD CONSTRAINT fk_order_items_order
    FOREIGN KEY (order_id)
    REFERENCES orders(id)
    ON DELETE CASCADE;
'''
        result = extractor.extract(code, "fkeys.sql")
        assert len(result["foreign_keys"]) >= 1
        fk = result["foreign_keys"][0]
        assert fk.table_name == "order_items"
        assert fk.ref_table == "orders"
        assert fk.on_delete == "CASCADE"

    def test_partition(self, extractor):
        code = '''
CREATE TABLE measurements (
    id BIGINT,
    recorded_at DATE NOT NULL,
    value FLOAT
) PARTITION BY RANGE (recorded_at);
'''
        result = extractor.extract(code, "partitions.sql")
        partitions = result["partitions"]
        assert len(partitions) >= 1
        assert partitions[0].strategy == "RANGE"

    def test_constraint_extraction(self, extractor):
        code = '''
ALTER TABLE products
    ADD CONSTRAINT chk_price CHECK (price >= 0);

ALTER TABLE users
    ADD CONSTRAINT uq_users_email UNIQUE (email);
'''
        result = extractor.extract(code, "constraints.sql")
        constraints = result["constraints"]
        assert len(constraints) >= 2


# ===== SECURITY EXTRACTION =====

class TestSecurityExtraction:
    """Tests for SQL security extraction."""

    @pytest.fixture
    def extractor(self):
        return SQLSecurityExtractor()

    def test_create_role(self, extractor):
        code = '''
CREATE ROLE app_readonly WITH LOGIN PASSWORD 'secret' NOSUPERUSER;
'''
        result = extractor.extract(code, "security.sql")
        assert len(result["roles"]) >= 1
        r = result["roles"][0]
        assert r.name == "app_readonly"

    def test_grant_select(self, extractor):
        code = '''
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly;
'''
        result = extractor.extract(code, "security.sql")
        assert len(result["grants"]) >= 1
        g = result["grants"][0]
        assert "SELECT" in g.privileges
        assert g.grantee == "app_readonly"

    def test_revoke(self, extractor):
        code = '''
REVOKE INSERT, UPDATE ON users FROM public_user;
'''
        result = extractor.extract(code, "security.sql")
        grants = result["grants"]
        assert any(g.action == "REVOKE" for g in grants)

    def test_rls_policy(self, extractor):
        code = '''
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON documents
    USING (tenant_id = current_setting('app.tenant_id')::BIGINT);
'''
        result = extractor.extract(code, "rls.sql")
        policies = result["rls_policies"]
        assert len(policies) >= 1
        assert policies[0].name == "tenant_isolation"
        assert policies[0].table_name == "documents"


# ===== MIGRATION EXTRACTION =====

class TestMigrationExtraction:
    """Tests for SQL migration extraction."""

    @pytest.fixture
    def extractor(self):
        return SQLMigrationExtractor()

    def test_flyway_versioned(self, extractor):
        code = '''
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);
'''
        result = extractor.extract(code, "V1_0__create_users_table.sql")
        mig = result["migration"]
        assert mig is not None
        assert mig.framework == "flyway"
        assert mig.direction == "up"
        assert "users" in mig.tables_created

    def test_golang_migrate_up(self, extractor):
        code = '''
CREATE TABLE IF NOT EXISTS products (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE INDEX idx_products_name ON products (name);
'''
        result = extractor.extract(code, "000001_create_products.up.sql")
        mig = result["migration"]
        assert mig is not None
        assert mig.framework == "golang-migrate"
        assert mig.direction == "up"
        assert "products" in mig.tables_created
        assert mig.is_idempotent is True

    def test_golang_migrate_down(self, extractor):
        code = '''
DROP TABLE IF EXISTS products;
'''
        result = extractor.extract(code, "000001_create_products.down.sql")
        mig = result["migration"]
        assert mig is not None
        assert mig.framework == "golang-migrate"
        assert mig.direction == "down"
        assert "products" in mig.tables_dropped

    def test_dbmate_migration(self, extractor):
        code = '''
-- migrate:up
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT REFERENCES users(id),
    expires_at TIMESTAMPTZ NOT NULL
);

-- migrate:down
DROP TABLE sessions;
'''
        result = extractor.extract(code, "20240101120000_create_sessions.sql")
        mig = result["migration"]
        assert mig is not None
        assert mig.framework == "dbmate"

    def test_data_migration_detection(self, extractor):
        code = '''
INSERT INTO settings (key, value)
VALUES ('feature_flag', 'enabled');

UPDATE users SET role = 'member' WHERE role IS NULL;
'''
        result = extractor.extract(code, "V2_0__seed_data.sql")
        mig = result["migration"]
        assert mig is not None
        assert mig.has_data_migration is True
        assert mig.has_seed_data is True

    def test_transaction_detection(self, extractor):
        code = '''
BEGIN;
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
ALTER TABLE users ADD COLUMN address TEXT;
COMMIT;
'''
        result = extractor.extract(code, "V3_0__add_contact_info.sql")
        mig = result["migration"]
        assert mig is not None
        assert mig.has_transaction is True

    def test_non_migration_file(self, extractor):
        code = '''
SELECT * FROM users WHERE id = 1;
'''
        result = extractor.extract(code, "query.sql")
        assert result["migration"] is None
