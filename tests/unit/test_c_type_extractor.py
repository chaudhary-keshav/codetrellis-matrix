"""
Tests for C type extractor — structs, unions, enums, typedefs, forward declarations.

Part of CodeTrellis v4.19 C Language Support.
"""

import pytest
from codetrellis.extractors.c.type_extractor import (
    CTypeExtractor, CStructInfo, CUnionInfo, CEnumInfo,
    CTypedefInfo, CForwardDeclInfo,
)


@pytest.fixture
def extractor():
    return CTypeExtractor()


class TestCStructExtraction:
    """Tests for C struct extraction."""

    def test_basic_struct(self, extractor):
        code = '''
struct point {
    int x;
    int y;
};
'''
        result = extractor.extract(code)
        assert len(result['structs']) >= 1
        s = result['structs'][0]
        assert s.name == 'point'
        assert len(s.fields) == 2

    def test_typedef_struct(self, extractor):
        code = '''
typedef struct {
    char name[64];
    int age;
} Person;
'''
        result = extractor.extract(code)
        # Should detect either in structs or typedefs
        structs = result['structs']
        typedefs = result['typedefs']
        assert len(structs) + len(typedefs) >= 1

    def test_named_typedef_struct(self, extractor):
        code = '''
typedef struct node {
    int value;
    struct node *next;
} Node;
'''
        result = extractor.extract(code)
        assert len(result['structs']) >= 1

    def test_struct_with_bitfields(self, extractor):
        code = '''
struct flags {
    unsigned int read : 1;
    unsigned int write : 1;
    unsigned int execute : 1;
};
'''
        result = extractor.extract(code)
        assert len(result['structs']) >= 1

    def test_packed_struct(self, extractor):
        code = '''
struct __attribute__((packed)) header {
    uint8_t version;
    uint16_t length;
    uint32_t checksum;
};
'''
        result = extractor.extract(code)
        structs = result['structs']
        assert len(structs) >= 1


class TestCUnionExtraction:
    """Tests for C union extraction."""

    def test_basic_union(self, extractor):
        code = '''
union value {
    int i;
    float f;
    char *s;
};
'''
        result = extractor.extract(code)
        assert len(result['unions']) >= 1
        u = result['unions'][0]
        assert u.name == 'value'
        assert len(u.fields) >= 2


class TestCEnumExtraction:
    """Tests for C enum extraction."""

    def test_basic_enum(self, extractor):
        code = '''
enum color {
    RED,
    GREEN,
    BLUE
};
'''
        result = extractor.extract(code)
        assert len(result['enums']) >= 1
        e = result['enums'][0]
        assert e.name == 'color'
        assert len(e.constants) == 3

    def test_enum_with_values(self, extractor):
        code = '''
enum http_status {
    HTTP_OK = 200,
    HTTP_NOT_FOUND = 404,
    HTTP_SERVER_ERROR = 500
};
'''
        result = extractor.extract(code)
        assert len(result['enums']) >= 1
        e = result['enums'][0]
        assert any(c.name == 'HTTP_OK' for c in e.constants)

    def test_typedef_enum(self, extractor):
        code = '''
typedef enum {
    LOG_DEBUG,
    LOG_INFO,
    LOG_WARN,
    LOG_ERROR
} LogLevel;
'''
        result = extractor.extract(code)
        assert len(result['enums']) >= 1


class TestCTypedefExtraction:
    """Tests for C typedef extraction."""

    def test_simple_typedef(self, extractor):
        code = '''
typedef unsigned long size_t;
typedef int (*compare_fn)(const void *, const void *);
'''
        result = extractor.extract(code)
        assert len(result['typedefs']) >= 1

    def test_function_pointer_typedef(self, extractor):
        code = '''
typedef void (*callback_t)(int status, void *data);
typedef int (*handler_fn)(const char *path, void *ctx);
'''
        result = extractor.extract(code)
        typedefs = result['typedefs']
        assert len(typedefs) >= 1


class TestCForwardDeclarations:
    """Tests for C forward declarations."""

    def test_forward_struct_decl(self, extractor):
        code = '''
struct node;
struct tree;
'''
        result = extractor.extract(code)
        assert len(result['forward_decls']) >= 1
