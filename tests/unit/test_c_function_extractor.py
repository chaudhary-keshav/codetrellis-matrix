"""
Tests for C function extractor — functions, function pointers, parameter parsing.

Part of CodeTrellis v4.19 C Language Support.
"""

import pytest
from codetrellis.extractors.c.function_extractor import (
    CFunctionExtractor, CFunctionInfo, CFunctionPointerInfo, CParameterInfo,
)


@pytest.fixture
def extractor():
    return CFunctionExtractor()


class TestCFunctionExtraction:
    """Tests for C function extraction."""

    def test_basic_function(self, extractor):
        code = '''
int add(int a, int b) {
    return a + b;
}
'''
        result = extractor.extract(code)
        assert len(result['functions']) >= 1
        f = result['functions'][0]
        assert f.name == 'add'
        assert f.return_type == 'int'
        assert len(f.parameters) == 2

    def test_void_function(self, extractor):
        code = '''
void print_message(const char *msg) {
    printf("%s\\n", msg);
}
'''
        result = extractor.extract(code)
        assert len(result['functions']) >= 1
        f = result['functions'][0]
        assert f.name == 'print_message'
        assert f.return_type == 'void'

    def test_static_function(self, extractor):
        code = '''
static int helper(int x) {
    return x * 2;
}
'''
        result = extractor.extract(code)
        assert len(result['functions']) >= 1
        f = result['functions'][0]
        assert f.is_static is True

    def test_inline_function(self, extractor):
        code = '''
static inline int max(int a, int b) {
    return a > b ? a : b;
}
'''
        result = extractor.extract(code)
        assert len(result['functions']) >= 1
        f = result['functions'][0]
        assert f.is_inline is True

    def test_extern_function(self, extractor):
        code = '''
extern int global_init(void);
'''
        result = extractor.extract(code)
        funcs = result['functions']
        # May or may not extract declarations — at least no crash
        assert isinstance(funcs, list)

    def test_variadic_function(self, extractor):
        code = '''
int log_msg(const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    int ret = vprintf(fmt, args);
    va_end(args);
    return ret;
}
'''
        result = extractor.extract(code)
        assert len(result['functions']) >= 1
        f = result['functions'][0]
        assert f.is_variadic is True

    def test_pointer_return_function(self, extractor):
        code = '''
char *strdup_safe(const char *s) {
    if (!s) return NULL;
    size_t len = strlen(s) + 1;
    char *dup = malloc(len);
    if (dup) memcpy(dup, s, len);
    return dup;
}
'''
        result = extractor.extract(code)
        assert len(result['functions']) >= 1
        f = result['functions'][0]
        assert 'char' in f.return_type

    def test_complexity_estimation(self, extractor):
        code = '''
int complex_func(int x) {
    if (x > 10) {
        if (x > 20) {
            for (int i = 0; i < x; i++) {
                if (i % 2 == 0) {
                    continue;
                }
            }
        }
    } else if (x < 0) {
        while (x < 0) {
            x++;
        }
    }
    return x;
}
'''
        result = extractor.extract(code)
        assert len(result['functions']) >= 1
        f = result['functions'][0]
        assert f.complexity >= 3  # Multiple branches

    def test_noreturn_function(self, extractor):
        code = '''
_Noreturn void fatal_error(const char *msg) {
    fprintf(stderr, "FATAL: %s\\n", msg);
    abort();
}
'''
        result = extractor.extract(code)
        funcs = result['functions']
        assert len(funcs) >= 1


class TestCFunctionPointerExtraction:
    """Tests for C function pointer extraction."""

    def test_function_pointer_variable(self, extractor):
        code = '''
int (*compare)(const void *, const void *);
void (*signal_handler)(int);
'''
        result = extractor.extract(code)
        fps = result['function_pointers']
        assert len(fps) >= 1

    def test_function_pointer_in_struct(self, extractor):
        code = '''
struct operations {
    int (*read)(void *buf, size_t len);
    int (*write)(const void *buf, size_t len);
    void (*close)(void);
};
'''
        result = extractor.extract(code)
        fps = result['function_pointers']
        assert len(fps) >= 1
