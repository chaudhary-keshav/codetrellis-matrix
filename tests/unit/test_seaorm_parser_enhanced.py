"""
Tests for EnhancedSeaORMParser — SeaORM async ORM analysis.

Part of CodeTrellis v5.4 Rust Framework Support.
Tests: entity extraction, relation detection, query patterns,
migrations, connections, active models, version detection, self-selection.
"""

import pytest
from codetrellis.seaorm_parser_enhanced import EnhancedSeaORMParser, SeaORMParseResult


@pytest.fixture
def parser():
    return EnhancedSeaORMParser()


# ═══════════════════════════════════════════════════════════════════
# Self-Selection Tests
# ═══════════════════════════════════════════════════════════════════

class TestSeaORMSelfSelection:

    def test_returns_empty_for_non_seaorm_file(self, parser):
        code = '''
use std::collections::HashMap;
fn main() {}
'''
        result = parser.parse(code, "main.rs")
        assert result.entities == []
        assert result.detected_frameworks == []

    def test_detects_seaorm_import(self, parser):
        code = '''
use sea_orm::entity::prelude::*;
'''
        result = parser.parse(code, "entity.rs")
        assert "sea-orm" in result.detected_frameworks


# ═══════════════════════════════════════════════════════════════════
# Entity Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestSeaORMEntityExtraction:

    def test_extract_entity_model(self, parser):
        code = '''
use sea_orm::entity::prelude::*;

#[derive(Clone, Debug, PartialEq, Eq, DeriveEntityModel)]
#[sea_orm(table_name = "users")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub id: i32,
    pub name: String,
    pub email: String,
    #[sea_orm(nullable)]
    pub bio: Option<String>,
}
'''
        result = parser.parse(code, "users.rs")
        assert len(result.entities) >= 1

    def test_extract_multiple_entities(self, parser):
        code = '''
use sea_orm::entity::prelude::*;

#[derive(Clone, Debug, DeriveEntityModel)]
#[sea_orm(table_name = "posts")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub id: i32,
    pub title: String,
    pub user_id: i32,
}

#[derive(Clone, Debug, DeriveEntityModel)]
#[sea_orm(table_name = "comments")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub id: i32,
    pub body: String,
    pub post_id: i32,
}
'''
        result = parser.parse(code, "entities.rs")
        assert len(result.entities) >= 2


# ═══════════════════════════════════════════════════════════════════
# Relation Tests
# ═══════════════════════════════════════════════════════════════════

class TestSeaORMRelations:

    def test_extract_derive_relation(self, parser):
        code = '''
use sea_orm::entity::prelude::*;

#[derive(Copy, Clone, Debug, EnumIter, DeriveRelation)]
pub enum Relation {
    #[sea_orm(has_many = "super::post::Entity")]
    Post,
    #[sea_orm(has_one = "super::profile::Entity")]
    Profile,
}
'''
        result = parser.parse(code, "users.rs")
        assert len(result.relations) >= 2

    def test_extract_related_impl(self, parser):
        code = '''
use sea_orm::entity::prelude::*;

impl Related<super::post::Entity> for Entity {
    fn to() -> RelationDef {
        Relation::Post.def()
    }
}
'''
        result = parser.parse(code, "users.rs")
        assert len(result.relations) >= 1


# ═══════════════════════════════════════════════════════════════════
# Query Tests
# ═══════════════════════════════════════════════════════════════════

class TestSeaORMQueries:

    def test_extract_find_queries(self, parser):
        code = '''
use sea_orm::*;

async fn get_user(db: &DatabaseConnection, id: i32) -> Option<user::Model> {
    User::find_by_id(id)
        .one(db)
        .await
        .unwrap()
}

async fn list_users(db: &DatabaseConnection) -> Vec<user::Model> {
    User::find()
        .filter(user::Column::Active.eq(true))
        .all(db)
        .await
        .unwrap()
}
'''
        result = parser.parse(code, "queries.rs")
        assert len(result.queries) >= 1

    def test_extract_insert_queries(self, parser):
        code = '''
use sea_orm::*;

async fn create_user(db: &DatabaseConnection) -> user::Model {
    let user = user::ActiveModel {
        name: Set("John".to_string()),
        email: Set("john@example.com".to_string()),
        ..Default::default()
    };
    User::insert(user)
        .exec(db)
        .await
        .unwrap()
}
'''
        result = parser.parse(code, "queries.rs")
        assert len(result.queries) >= 1

    def test_extract_update_queries(self, parser):
        code = '''
use sea_orm::*;

async fn update_user(db: &DatabaseConnection, id: i32) {
    User::update(user::ActiveModel {
        id: Set(id),
        name: Set("Updated".to_string()),
        ..Default::default()
    })
    .exec(db)
    .await
    .unwrap();
}
'''
        result = parser.parse(code, "queries.rs")
        assert len(result.queries) >= 1


# ═══════════════════════════════════════════════════════════════════
# Migration Tests
# ═══════════════════════════════════════════════════════════════════

class TestSeaORMMigrations:

    def test_extract_migration_trait(self, parser):
        code = '''
use sea_orm_migration::prelude::*;

#[derive(DeriveMigrationName)]
pub struct Migration;

#[async_trait::async_trait]
impl MigrationTrait for Migration {
    async fn up(&self, manager: &SchemaManager) -> Result<(), DbErr> {
        manager.create_table(
            Table::create()
                .table(Users::Table)
                .col(ColumnDef::new(Users::Id).integer().primary_key().auto_increment())
                .col(ColumnDef::new(Users::Name).string().not_null())
                .to_owned()
        ).await
    }

    async fn down(&self, manager: &SchemaManager) -> Result<(), DbErr> {
        manager.drop_table(Table::drop().table(Users::Table).to_owned()).await
    }
}
'''
        result = parser.parse(code, "m20230101_000001_create_users.rs")
        assert len(result.migrations) >= 1


# ═══════════════════════════════════════════════════════════════════
# Connection Tests
# ═══════════════════════════════════════════════════════════════════

class TestSeaORMConnections:

    def test_extract_database_connect(self, parser):
        code = '''
use sea_orm::{Database, DatabaseConnection};

async fn establish_connection() -> DatabaseConnection {
    Database::connect("postgres://user:pass@localhost/db")
        .await
        .unwrap()
}
'''
        result = parser.parse(code, "db.rs")
        assert len(result.connections) >= 1


# ═══════════════════════════════════════════════════════════════════
# Version Detection Tests
# ═══════════════════════════════════════════════════════════════════

class TestSeaORMVersionDetection:

    def test_detect_seaorm_ecosystem(self, parser):
        code = '''
use sea_orm::entity::prelude::*;
use sea_orm_migration::prelude::*;
'''
        result = parser.parse(code, "lib.rs")
        assert "sea-orm" in result.detected_frameworks

    def test_version_detection(self, parser):
        code = '''
use sea_orm::entity::prelude::*;

#[derive(DeriveEntityModel)]
#[sea_orm(table_name = "users")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub id: i32,
}
'''
        result = parser.parse(code, "entity.rs")
        assert result.seaorm_version != "" or result.detected_frameworks
