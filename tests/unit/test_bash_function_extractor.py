"""
Tests for BashFunctionExtractor — function definitions, cross-calls, complexity.

Part of CodeTrellis v4.18 Bash Language Support.
"""

import pytest
from codetrellis.extractors.bash.function_extractor import BashFunctionExtractor


@pytest.fixture
def extractor():
    return BashFunctionExtractor()


def _get_functions(extractor, code):
    """Helper to extract functions list from extractor result."""
    result = extractor.extract(code, "test.sh")
    return result.get("functions", [])


# ===== FUNCTION SYNTAX EXTRACTION =====

class TestFunctionSyntax:
    """Tests for various Bash function definition syntaxes."""

    def test_posix_function(self, extractor):
        code = '''
my_func() {
    echo "hello"
}
'''
        funcs = _get_functions(extractor, code)
        assert len(funcs) >= 1
        f = funcs[0]
        assert f.name == "my_func"
        assert f.syntax == "posix"

    def test_bash_keyword_function(self, extractor):
        code = '''
function my_func {
    echo "hello"
}
'''
        funcs = _get_functions(extractor, code)
        assert len(funcs) >= 1
        f = funcs[0]
        assert f.name == "my_func"
        assert f.syntax == "bash_keyword"

    def test_combined_syntax_function(self, extractor):
        code = '''
function my_func() {
    echo "hello"
}
'''
        funcs = _get_functions(extractor, code)
        assert len(funcs) >= 1
        f = funcs[0]
        assert f.name == "my_func"
        assert f.syntax == "combined"

    def test_multiple_functions(self, extractor):
        code = '''
setup() {
    echo "setup"
}

teardown() {
    echo "teardown"
}

main() {
    setup
    teardown
}
'''
        funcs = _get_functions(extractor, code)
        assert len(funcs) >= 3
        names = [f.name for f in funcs]
        assert "setup" in names
        assert "teardown" in names
        assert "main" in names

    def test_function_with_hyphens_in_name(self, extractor):
        code = '''
my-func() {
    echo "hyphenated"
}
'''
        funcs = _get_functions(extractor, code)
        assert len(funcs) >= 1
        assert funcs[0].name == "my-func"


# ===== FUNCTION BODY ANALYSIS =====

class TestFunctionBody:
    """Tests for function body analysis (complexity, calls, etc.)."""

    def test_local_variables_detection(self, extractor):
        code = '''
process() {
    local name="test"
    local -i count=0
    local result
    echo "$name $count"
}
'''
        funcs = _get_functions(extractor, code)
        assert len(funcs) >= 1
        f = funcs[0]
        assert "name" in f.local_variables or len(f.local_variables) >= 1

    def test_cross_function_calls(self, extractor):
        code = '''
helper() {
    echo "helping"
}

main() {
    helper
    echo "done"
}
'''
        funcs = _get_functions(extractor, code)
        main_func = [f for f in funcs if f.name == "main"]
        assert len(main_func) >= 1
        assert "helper" in main_func[0].calls_functions

    def test_docstring_extraction(self, extractor):
        code = '''
# This is a helper function
# It does important things
# Args: $1 = name
helper() {
    echo "$1"
}
'''
        funcs = _get_functions(extractor, code)
        assert len(funcs) >= 1
        f = funcs[0]
        assert f.docstring != ""

    def test_complexity_estimation(self, extractor):
        code = '''
complex() {
    if [[ -n "$1" ]]; then
        for f in *.txt; do
            if [[ -f "$f" ]]; then
                while IFS= read -r line; do
                    case "$line" in
                        start*) echo "start" ;;
                        stop*)  echo "stop" ;;
                        *)      echo "other" ;;
                    esac
                done < "$f"
            fi
        done
    fi
}
'''
        funcs = _get_functions(extractor, code)
        assert len(funcs) >= 1
        f = funcs[0]
        assert f.complexity > 1  # Should detect multiple branches

    def test_return_codes_extraction(self, extractor):
        code = '''
check_status() {
    if [[ -f "$1" ]]; then
        return 0
    else
        return 1
    fi
}
'''
        funcs = _get_functions(extractor, code)
        assert len(funcs) >= 1
        f = funcs[0]
        assert 0 in f.return_codes or 1 in f.return_codes

    def test_empty_function(self, extractor):
        code = '''
noop() {
    :
}
'''
        funcs = _get_functions(extractor, code)
        assert len(funcs) >= 1
        assert funcs[0].name == "noop"
        assert funcs[0].body_lines <= 5  # includes braces

    def test_exported_function(self, extractor):
        code = '''
my_func() {
    echo "exported"
}
export -f my_func
'''
        funcs = _get_functions(extractor, code)
        assert len(funcs) >= 1
        f = funcs[0]
        assert f.is_exported is True


# ===== PARAMETER EXTRACTION =====

class TestParameterExtraction:
    """Tests for function parameter detection."""

    def test_positional_params(self, extractor):
        code = '''
greet() {
    local name="$1"
    local greeting="$2"
    echo "$greeting, $name!"
}
'''
        funcs = _get_functions(extractor, code)
        assert len(funcs) >= 1
        f = funcs[0]
        # Should detect $1, $2 usage
        assert len(f.parameters) >= 1 or len(f.local_variables) >= 1

    def test_special_params(self, extractor):
        code = '''
log_all() {
    echo "Args: $@"
    echo "Count: $#"
}
'''
        funcs = _get_functions(extractor, code)
        assert len(funcs) >= 1


# ===== EDGE CASES =====

class TestEdgeCases:
    """Tests for edge cases and tricky patterns."""

    def test_nested_braces(self, extractor):
        code = '''
outer() {
    if true; then
        {
            echo "nested braces"
        }
    fi
}

after() {
    echo "after"
}
'''
        funcs = _get_functions(extractor, code)
        names = [f.name for f in funcs]
        assert "outer" in names
        assert "after" in names

    def test_function_with_pipe_in_body(self, extractor):
        code = '''
find_files() {
    find . -name "*.txt" | grep -v "test" | sort
}
'''
        funcs = _get_functions(extractor, code)
        assert len(funcs) >= 1
        f = funcs[0]
        assert f.has_pipe is True

    def test_function_with_subshell(self, extractor):
        code = '''
get_version() {
    local ver=$(cat VERSION)
    echo "$ver"
}
'''
        funcs = _get_functions(extractor, code)
        assert len(funcs) >= 1
        f = funcs[0]
        assert f.has_subshell is True

    def test_empty_script(self, extractor):
        code = '''#!/bin/bash
# Just a comment
'''
        funcs = _get_functions(extractor, code)
        assert len(funcs) == 0

    def test_indented_function(self, extractor):
        code = '''
    setup_env() {
        export PATH="/usr/local/bin:$PATH"
    }
'''
        funcs = _get_functions(extractor, code)
        assert len(funcs) >= 1
        assert funcs[0].name == "setup_env"
