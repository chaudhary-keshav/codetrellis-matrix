"""
Tests for EnhancedRustParser — full integration of all Rust extractors.

Part of CodeTrellis v4.14 Rust Language Support.
"""

import pytest
from codetrellis.rust_parser_enhanced import EnhancedRustParser


@pytest.fixture
def parser():
    return EnhancedRustParser()


class TestRustParserBasic:
    """Tests for basic Rust parsing capabilities."""

    def test_parse_simple_rust_file(self, parser):
        code = '''
use std::collections::HashMap;

pub struct Config {
    pub host: String,
    pub port: u16,
}

impl Config {
    pub fn new() -> Self {
        Self { host: "localhost".to_string(), port: 8080 }
    }
}

pub fn main() {
    let config = Config::new();
    println!("{}:{}", config.host, config.port);
}
'''
        result = parser.parse(code, "main.rs")
        assert result.file_type == "rust"
        assert len(result.structs) >= 1
        assert result.structs[0].name == "Config"
        assert len(result.impls) >= 1
        assert len(result.functions) >= 1
        assert len(result.imports) >= 1

    def test_detect_frameworks(self, parser):
        code = '''
use actix_web::{get, web, App, HttpServer, Responder};
use serde::{Deserialize, Serialize};
use tokio;
'''
        result = parser.parse(code, "main.rs")
        assert "actix-web" in result.detected_frameworks
        assert "serde" in result.detected_frameworks
        assert "tokio" in result.detected_frameworks

    def test_extract_imports(self, parser):
        code = '''
use std::io;
use std::collections::HashMap;
use crate::models::User;
'''
        result = parser.parse(code, "lib.rs")
        assert len(result.imports) == 3

    def test_extract_extern_crates(self, parser):
        code = '''
extern crate serde;
extern crate diesel;
'''
        result = parser.parse(code, "lib.rs")
        assert "serde" in result.extern_crates
        assert "diesel" in result.extern_crates

    def test_extract_macro_definitions(self, parser):
        code = '''
macro_rules! create_function {
    ($func_name:ident) => {
        fn $func_name() {
            println!("Function: {:?}", stringify!($func_name));
        }
    };
}
'''
        result = parser.parse(code, "macros.rs")
        assert "create_function" in result.macros_defined

    def test_module_name_from_path(self, parser):
        result = parser.parse("", "src/models/user.rs")
        assert result.module_name == "user"

    def test_module_name_from_mod_rs(self, parser):
        result = parser.parse("", "src/models/mod.rs")
        assert result.module_name == "models"


class TestRustParserIntegration:
    """Tests for integrated parsing of complex Rust code."""

    def test_full_actix_handler(self, parser):
        code = '''
use actix_web::{get, post, web, App, HttpServer, Responder, HttpResponse};
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct User {
    pub id: u64,
    pub name: String,
}

#[get("/api/users")]
async fn list_users(db: web::Data<Pool>) -> impl Responder {
    HttpResponse::Ok().json(vec![])
}

#[post("/api/users")]
async fn create_user(body: web::Json<User>) -> impl Responder {
    HttpResponse::Created().json(body.into_inner())
}
'''
        result = parser.parse(code, "handlers.rs")
        assert len(result.structs) >= 1
        assert result.structs[0].name == "User"
        assert len(result.routes) >= 2
        assert any(r.method == "GET" for r in result.routes)
        assert any(r.method == "POST" for r in result.routes)
        assert "actix-web" in result.detected_frameworks
        assert "serde" in result.detected_frameworks

    def test_diesel_model(self, parser):
        code = '''
use diesel::prelude::*;

#[derive(Queryable, Insertable, Debug)]
#[diesel(table_name = "users")]
pub struct User {
    pub id: i32,
    pub name: String,
    pub email: String,
}
'''
        result = parser.parse(code, "models.rs")
        assert len(result.structs) >= 1
        assert len(result.models) >= 1
        model = result.models[0]
        assert model.name == "User"
        assert model.orm == "diesel"

    def test_trait_and_impl(self, parser):
        code = '''
pub trait Repository {
    fn find_by_id(&self, id: u64) -> Option<Entity>;
    fn save(&mut self, entity: Entity) -> Result<(), Error>;
}

impl Repository for PostgresRepo {
    fn find_by_id(&self, id: u64) -> Option<Entity> {
        todo!()
    }

    fn save(&mut self, entity: Entity) -> Result<(), Error> {
        todo!()
    }
}
'''
        result = parser.parse(code, "repo.rs")
        assert len(result.traits) >= 1
        assert result.traits[0].name == "Repository"
        assert len(result.impls) >= 1
        assert result.impls[0].trait_name == "Repository"
        assert result.impls[0].target_type == "PostgresRepo"


class TestCargoTomlParsing:
    """Tests for Cargo.toml parsing."""

    def test_parse_simple_cargo_toml(self, parser):
        content = '''
[package]
name = "my-app"
version = "0.1.0"
edition = "2021"

[dependencies]
actix-web = "4"
serde = { version = "1", features = ["derive"] }
tokio = { version = "1", features = ["full"] }

[dev-dependencies]
reqwest = "0.11"
'''
        result = EnhancedRustParser.parse_cargo_toml(content)
        assert result['name'] == "my-app"
        assert result['version'] == "0.1.0"
        assert result['edition'] == "2021"
        assert len(result['dependencies']) >= 3
        dep_names = [d['name'] for d in result['dependencies']]
        assert "actix-web" in dep_names
        assert "serde" in dep_names
        assert "tokio" in dep_names
        assert len(result['dev_dependencies']) >= 1

    def test_parse_workspace_cargo_toml(self, parser):
        content = '''
[workspace]
members = [
    "crate-a",
    "crate-b",
    "crate-c",
]
'''
        result = EnhancedRustParser.parse_cargo_toml(content)
        assert len(result['workspace_members']) >= 3

    def test_parse_features(self, parser):
        content = '''
[package]
name = "my-lib"
version = "0.1.0"

[features]
default = ["std"]
std = ["serde/std"]
full = ["std", "extra"]
'''
        result = EnhancedRustParser.parse_cargo_toml(content)
        assert "default" in result['features']
        assert "std" in result['features']
