"""
Tests for RustTypeExtractor — structs, enums, traits, type aliases, impl blocks.

Part of CodeTrellis v4.14 Rust Language Support.
"""

import pytest
from codetrellis.extractors.rust.type_extractor import RustTypeExtractor


@pytest.fixture
def extractor():
    return RustTypeExtractor()


# ===== STRUCT EXTRACTION =====

class TestStructExtraction:
    """Tests for Rust struct extraction."""

    def test_simple_pub_struct(self, extractor):
        code = '''
pub struct User {
    pub id: u64,
    pub name: String,
    pub email: String,
}
'''
        result = extractor.extract(code, "user.rs")
        assert len(result["structs"]) >= 1
        s = result["structs"][0]
        assert s.name == "User"
        assert s.visibility == "pub"
        assert len(s.fields) == 3
        assert s.fields[0].name == "id"
        assert s.fields[0].type == "u64"

    def test_struct_with_derives(self, extractor):
        code = '''
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub host: String,
    pub port: u16,
}
'''
        result = extractor.extract(code, "config.rs")
        assert len(result["structs"]) >= 1
        s = result["structs"][0]
        assert s.name == "Config"
        assert "Debug" in s.derives
        assert "Serialize" in s.derives

    def test_generic_struct(self, extractor):
        code = '''
pub struct Response<T> {
    pub data: T,
    pub status: u16,
}
'''
        result = extractor.extract(code, "response.rs")
        assert len(result["structs"]) >= 1
        s = result["structs"][0]
        assert s.name == "Response"
        assert "T" in s.generics

    def test_tuple_struct(self, extractor):
        code = '''
pub struct UserId(pub u64);
'''
        result = extractor.extract(code, "types.rs")
        assert len(result["structs"]) >= 1
        s = result["structs"][0]
        assert s.name == "UserId"
        assert s.is_tuple_struct is True

    def test_private_struct(self, extractor):
        code = '''
struct InternalState {
    counter: usize,
}
'''
        result = extractor.extract(code, "state.rs")
        assert len(result["structs"]) >= 1
        s = result["structs"][0]
        assert s.name == "InternalState"


# ===== ENUM EXTRACTION =====

class TestEnumExtraction:
    """Tests for Rust enum extraction."""

    def test_simple_enum(self, extractor):
        code = '''
pub enum Color {
    Red,
    Green,
    Blue,
}
'''
        result = extractor.extract(code, "color.rs")
        assert len(result["enums"]) >= 1
        e = result["enums"][0]
        assert e.name == "Color"
        assert len(e.variants) == 3
        assert e.variants[0].name == "Red"

    def test_enum_with_data(self, extractor):
        code = '''
pub enum Message {
    Quit,
    Echo(String),
    Move { x: i32, y: i32 },
    Color(u8, u8, u8),
}
'''
        result = extractor.extract(code, "message.rs")
        assert len(result["enums"]) >= 1
        e = result["enums"][0]
        assert e.name == "Message"
        assert len(e.variants) >= 3

    def test_enum_with_derives(self, extractor):
        code = '''
#[derive(Debug, Clone, PartialEq)]
pub enum Status {
    Active,
    Inactive,
    Suspended,
}
'''
        result = extractor.extract(code, "status.rs")
        assert len(result["enums"]) >= 1
        e = result["enums"][0]
        assert e.name == "Status"
        assert "Debug" in e.derives


# ===== TRAIT EXTRACTION =====

class TestTraitExtraction:
    """Tests for Rust trait extraction."""

    def test_simple_trait(self, extractor):
        code = '''
pub trait Repository {
    fn find_by_id(&self, id: u64) -> Option<Entity>;
    fn save(&mut self, entity: Entity) -> Result<(), Error>;
}
'''
        result = extractor.extract(code, "repo.rs")
        assert len(result["traits"]) >= 1
        t = result["traits"][0]
        assert t.name == "Repository"
        assert len(t.methods) >= 2

    def test_trait_with_supertrait(self, extractor):
        code = '''
pub trait Service: Send + Sync {
    fn execute(&self);
}
'''
        result = extractor.extract(code, "service.rs")
        assert len(result["traits"]) >= 1
        t = result["traits"][0]
        assert t.name == "Service"
        assert "Send" in t.super_traits
        assert "Sync" in t.super_traits

    def test_trait_with_default_methods(self, extractor):
        code = '''
pub trait Logger {
    fn log(&self, msg: &str);
    fn warn(&self, msg: &str) {
        self.log(&format!("WARN: {}", msg));
    }
}
'''
        result = extractor.extract(code, "logger.rs")
        assert len(result["traits"]) >= 1
        t = result["traits"][0]
        assert t.name == "Logger"

    def test_async_trait(self, extractor):
        code = '''
pub trait AsyncHandler {
    async fn handle(&self, req: Request) -> Response;
}
'''
        result = extractor.extract(code, "handler.rs")
        assert len(result["traits"]) >= 1
        t = result["traits"][0]
        assert t.name == "AsyncHandler"


# ===== TYPE ALIAS EXTRACTION =====

class TestTypeAliasExtraction:
    """Tests for Rust type alias extraction."""

    def test_simple_type_alias(self, extractor):
        code = '''
pub type Result<T> = std::result::Result<T, AppError>;
'''
        result = extractor.extract(code, "types.rs")
        assert len(result["type_aliases"]) >= 1
        a = result["type_aliases"][0]
        assert a.name == "Result"

    def test_type_alias_with_generics(self, extractor):
        code = '''
type BoxFuture<T> = Pin<Box<dyn Future<Output = T> + Send>>;
'''
        result = extractor.extract(code, "types.rs")
        assert len(result["type_aliases"]) >= 1


# ===== IMPL BLOCK EXTRACTION =====

class TestImplExtraction:
    """Tests for Rust impl block extraction."""

    def test_inherent_impl(self, extractor):
        code = '''
impl User {
    pub fn new(name: String) -> Self {
        Self { name, id: 0 }
    }

    pub fn greet(&self) -> String {
        format!("Hello, {}", self.name)
    }
}
'''
        result = extractor.extract(code, "user.rs")
        assert len(result["impls"]) >= 1
        imp = result["impls"][0]
        assert imp.target_type == "User"
        assert imp.trait_name is None

    def test_trait_impl(self, extractor):
        code = '''
impl Display for User {
    fn fmt(&self, f: &mut Formatter) -> fmt::Result {
        write!(f, "{}", self.name)
    }
}
'''
        result = extractor.extract(code, "user.rs")
        assert len(result["impls"]) >= 1
        imp = result["impls"][0]
        assert imp.target_type == "User"
        assert imp.trait_name == "Display"
