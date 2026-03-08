"""
Tests for RustFunctionExtractor — functions, methods, async/unsafe/const.

Part of CodeTrellis v4.14 Rust Language Support.
"""

import pytest
from codetrellis.extractors.rust.function_extractor import RustFunctionExtractor


@pytest.fixture
def extractor():
    return RustFunctionExtractor()


# ===== FUNCTION EXTRACTION =====

class TestFunctionExtraction:
    """Tests for Rust function extraction."""

    def test_simple_pub_function(self, extractor):
        code = '''
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}
'''
        result = extractor.extract(code, "math.rs")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "add"
        assert f.visibility == "pub"
        assert f.return_type == "i32"
        assert len(f.parameters) == 2
        assert f.parameters[0].name == "a"
        assert f.parameters[0].type == "i32"

    def test_async_function(self, extractor):
        code = '''
pub async fn fetch_data(url: &str) -> Result<Response, Error> {
    reqwest::get(url).await
}
'''
        result = extractor.extract(code, "http.rs")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "fetch_data"
        assert f.is_async is True

    def test_unsafe_function(self, extractor):
        code = '''
pub unsafe fn transmute_data(ptr: *const u8, len: usize) -> &[u8] {
    std::slice::from_raw_parts(ptr, len)
}
'''
        result = extractor.extract(code, "ffi.rs")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "transmute_data"
        assert f.is_unsafe is True

    def test_const_function(self, extractor):
        code = '''
pub const fn max_size() -> usize {
    1024
}
'''
        result = extractor.extract(code, "constants.rs")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "max_size"
        assert f.is_const is True

    def test_function_with_generics(self, extractor):
        code = '''
pub fn find<T: PartialEq>(items: &[T], target: &T) -> Option<usize> {
    items.iter().position(|x| x == target)
}
'''
        result = extractor.extract(code, "search.rs")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "find"

    def test_private_function(self, extractor):
        code = '''
fn helper_internal() -> bool {
    true
}
'''
        result = extractor.extract(code, "lib.rs")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "helper_internal"

    def test_function_no_return(self, extractor):
        code = '''
pub fn log_message(msg: &str) {
    println!("{}", msg);
}
'''
        result = extractor.extract(code, "log.rs")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "log_message"
        assert f.return_type is None

    def test_test_function(self, extractor):
        code = '''
#[test]
fn test_addition() {
    assert_eq!(add(2, 3), 5);
}
'''
        result = extractor.extract(code, "tests.rs")
        assert len(result["functions"]) >= 1
        f = result["functions"][0]
        assert f.name == "test_addition"
        assert f.is_test is True


# ===== METHOD EXTRACTION =====

class TestMethodExtraction:
    """Tests for Rust method extraction from impl blocks."""

    def test_methods_in_impl(self, extractor):
        code = '''
impl Server {
    pub fn new(port: u16) -> Self {
        Self { port }
    }

    pub fn start(&self) {
        println!("Starting on port {}", self.port);
    }

    pub fn stop(&mut self) {
        self.running = false;
    }
}
'''
        result = extractor.extract(code, "server.rs")
        assert len(result["methods"]) >= 2
        # Check we found methods with self params
        method_names = [m.name for m in result["methods"]]
        assert "start" in method_names or "stop" in method_names

    def test_async_method(self, extractor):
        code = '''
impl ApiClient {
    pub async fn get(&self, url: &str) -> Result<Response, Error> {
        self.client.get(url).send().await
    }
}
'''
        result = extractor.extract(code, "client.rs")
        assert len(result["methods"]) >= 1
        m = result["methods"][0]
        assert m.is_async is True
