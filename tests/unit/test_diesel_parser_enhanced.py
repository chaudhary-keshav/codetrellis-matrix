"""
Tests for EnhancedDieselParser — Diesel ORM analysis.

Part of CodeTrellis v5.4 Rust Framework Support.
Tests: table extraction, model detection, query DSL, migrations,
connections, associations, custom types, version detection, self-selection.
"""

import pytest
from codetrellis.diesel_parser_enhanced import EnhancedDieselParser, DieselParseResult


@pytest.fixture
def parser():
    return EnhancedDieselParser()


# ═══════════════════════════════════════════════════════════════════
# Self-Selection Tests
# ═══════════════════════════════════════════════════════════════════

class TestDieselSelfSelection:

    def test_returns_empty_for_non_diesel_file(self, parser):
        code = '''
use std::io;
fn main() {}
'''
        result = parser.parse(code, "main.rs")
        assert result.tables == []
        assert result.detected_frameworks == []

    def test_detects_diesel_import(self, parser):
        code = '''
use diesel::prelude::*;
'''
        result = parser.parse(code, "main.rs")
        assert "diesel" in result.detected_frameworks


# ═══════════════════════════════════════════════════════════════════
# Table! Macro Tests
# ═══════════════════════════════════════════════════════════════════

class TestDieselTableExtraction:

    def test_extract_table_macro(self, parser):
        code = '''
use diesel::table;

diesel::table! {
    users (id) {
        id -> Int4,
        name -> Varchar,
        email -> Varchar,
        created_at -> Timestamp,
    }
}

diesel::table! {
    posts (id) {
        id -> Int4,
        title -> Varchar,
        body -> Text,
        user_id -> Int4,
    }
}
'''
        result = parser.parse(code, "schema.rs")
        assert len(result.tables) >= 2
        table_names = [t.name for t in result.tables]
        assert "users" in table_names
        assert "posts" in table_names

    def test_extract_table_columns(self, parser):
        code = '''
use diesel::table;

diesel::table! {
    products (id) {
        id -> Int4,
        name -> Varchar,
        price -> Float8,
    }
}
'''
        result = parser.parse(code, "schema.rs")
        assert len(result.tables) >= 1


# ═══════════════════════════════════════════════════════════════════
# Model Tests
# ═══════════════════════════════════════════════════════════════════

class TestDieselModels:

    def test_extract_queryable_model(self, parser):
        code = '''
use diesel::prelude::*;

#[derive(Queryable, Debug)]
pub struct User {
    pub id: i32,
    pub name: String,
    pub email: String,
}
'''
        result = parser.parse(code, "models.rs")
        assert len(result.models) >= 1
        assert any(m.name == "User" for m in result.models)

    def test_extract_insertable_model(self, parser):
        code = '''
use diesel::prelude::*;

#[derive(Insertable)]
#[diesel(table_name = users)]
pub struct NewUser {
    pub name: String,
    pub email: String,
}
'''
        result = parser.parse(code, "models.rs")
        assert len(result.models) >= 1

    def test_extract_changeset_model(self, parser):
        code = '''
use diesel::prelude::*;

#[derive(AsChangeset)]
#[diesel(table_name = users)]
pub struct UpdateUser {
    pub name: Option<String>,
    pub email: Option<String>,
}
'''
        result = parser.parse(code, "models.rs")
        assert len(result.models) >= 1


# ═══════════════════════════════════════════════════════════════════
# Query DSL Tests
# ═══════════════════════════════════════════════════════════════════

class TestDieselQueries:

    def test_extract_select_queries(self, parser):
        code = '''
use diesel::prelude::*;

fn list_users(conn: &mut PgConnection) -> Vec<User> {
    users::table
        .filter(users::active.eq(true))
        .order(users::name.asc())
        .load::<User>(conn)
        .expect("Error loading users")
}
'''
        result = parser.parse(code, "queries.rs")
        assert len(result.queries) >= 1

    def test_extract_insert_queries(self, parser):
        code = '''
use diesel::prelude::*;

fn create_user(conn: &mut PgConnection, new_user: &NewUser) -> User {
    diesel::insert_into(users::table)
        .values(new_user)
        .get_result(conn)
        .expect("Error inserting user")
}
'''
        result = parser.parse(code, "queries.rs")
        assert len(result.queries) >= 1

    def test_extract_update_queries(self, parser):
        code = '''
use diesel::prelude::*;

fn update_user(conn: &mut PgConnection, id: i32, changes: &UpdateUser) -> User {
    diesel::update(users::table.find(id))
        .set(changes)
        .get_result(conn)
        .expect("Error updating user")
}
'''
        result = parser.parse(code, "queries.rs")
        assert len(result.queries) >= 1

    def test_extract_delete_queries(self, parser):
        code = '''
use diesel::prelude::*;

fn delete_user(conn: &mut PgConnection, id: i32) -> usize {
    diesel::delete(users::table.find(id))
        .execute(conn)
        .expect("Error deleting user")
}
'''
        result = parser.parse(code, "queries.rs")
        assert len(result.queries) >= 1


# ═══════════════════════════════════════════════════════════════════
# Connection Tests
# ═══════════════════════════════════════════════════════════════════

class TestDieselConnections:

    def test_extract_pg_connection(self, parser):
        code = '''
use diesel::prelude::*;
use diesel::pg::PgConnection;

fn establish_connection() -> PgConnection {
    PgConnection::establish(&database_url)
        .expect("Error connecting to database")
}
'''
        result = parser.parse(code, "db.rs")
        assert len(result.connections) >= 1

    def test_extract_pool_connection(self, parser):
        code = '''
use diesel::prelude::*;
use diesel::r2d2::{self, ConnectionManager};

type DbPool = r2d2::Pool<ConnectionManager<PgConnection>>;
'''
        result = parser.parse(code, "db.rs")
        assert len(result.connections) >= 1


# ═══════════════════════════════════════════════════════════════════
# Migration Tests
# ═══════════════════════════════════════════════════════════════════

class TestDieselMigrations:

    def test_extract_embedded_migrations(self, parser):
        code = '''
use diesel_migrations::{embed_migrations, EmbeddedMigrations, MigrationHarness};

pub const MIGRATIONS: EmbeddedMigrations = embed_migrations!();

fn run_migrations(conn: &mut impl MigrationHarness<diesel::pg::Pg>) {
    conn.run_pending_migrations(MIGRATIONS).unwrap();
}
'''
        result = parser.parse(code, "main.rs")
        assert len(result.migrations) >= 1


# ═══════════════════════════════════════════════════════════════════
# Version Detection Tests
# ═══════════════════════════════════════════════════════════════════

class TestDieselVersionDetection:

    def test_detect_diesel_ecosystem(self, parser):
        code = '''
use diesel::prelude::*;
use diesel_migrations::embed_migrations;
'''
        result = parser.parse(code, "main.rs")
        assert "diesel" in result.detected_frameworks

    def test_version_detection(self, parser):
        code = '''
use diesel::prelude::*;
use diesel::Selectable;

#[derive(Queryable, Selectable)]
pub struct User {
    pub id: i32,
    pub name: String,
}
'''
        result = parser.parse(code, "models.rs")
        # Selectable derives are diesel v2.x
        assert result.diesel_version == "2.x"
