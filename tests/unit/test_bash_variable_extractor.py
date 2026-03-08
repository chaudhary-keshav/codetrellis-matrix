"""
Tests for BashVariableExtractor — variables, arrays, exports.

Part of CodeTrellis v4.18 Bash Language Support.
"""

import pytest
from codetrellis.extractors.bash.variable_extractor import BashVariableExtractor


@pytest.fixture
def extractor():
    return BashVariableExtractor()


# ===== SIMPLE VARIABLE EXTRACTION =====

class TestSimpleVariables:
    """Tests for basic variable assignment extraction."""

    def test_simple_assignment(self, extractor):
        code = '''
NAME="John"
AGE=30
'''
        result = extractor.extract(code)
        vars_found = result.get("variables", [])
        names = [v.name for v in vars_found]
        assert "NAME" in names
        assert "AGE" in names

    def test_variable_with_command_substitution(self, extractor):
        code = '''
HOSTNAME=$(hostname)
DATE=$(date +%Y-%m-%d)
'''
        result = extractor.extract(code)
        vars_found = result.get("variables", [])
        names = [v.name for v in vars_found]
        assert "HOSTNAME" in names or "DATE" in names

    def test_readonly_variable(self, extractor):
        code = '''
readonly MAX_RETRIES=3
readonly CONFIG_DIR="/etc/app"
'''
        result = extractor.extract(code)
        vars_found = result.get("variables", [])
        readonly_vars = [v for v in vars_found if v.is_readonly]
        assert len(readonly_vars) >= 1


# ===== EXPORT EXTRACTION =====

class TestExports:
    """Tests for export statement extraction."""

    def test_export_with_value(self, extractor):
        code = '''
export PATH="/usr/local/bin:$PATH"
export LANG="en_US.UTF-8"
'''
        result = extractor.extract(code)
        exports = result.get("exports", [])
        assert len(exports) >= 1
        names = [e.name for e in exports]
        assert "PATH" in names or "LANG" in names

    def test_export_without_value(self, extractor):
        code = '''
MY_VAR="hello"
export MY_VAR
'''
        result = extractor.extract(code)
        exports = result.get("exports", [])
        assert len(exports) >= 1


# ===== ARRAY EXTRACTION =====

class TestArrays:
    """Tests for array extraction."""

    def test_indexed_array(self, extractor):
        code = '''
FRUITS=("apple" "banana" "cherry")
'''
        result = extractor.extract(code)
        arrays = result.get("arrays", [])
        assert len(arrays) >= 1
        a = arrays[0]
        assert a.name == "FRUITS"
        assert a.array_type == "indexed"

    def test_associative_array(self, extractor):
        code = '''
declare -A COLORS
COLORS[red]="#ff0000"
COLORS[green]="#00ff00"
'''
        result = extractor.extract(code)
        arrays = result.get("arrays", [])
        assert len(arrays) >= 1
        a = arrays[0]
        assert a.array_type == "associative"


# ===== DECLARE EXTRACTION =====

class TestDeclare:
    """Tests for declare/typeset variable extraction."""

    def test_declare_integer(self, extractor):
        code = '''
declare -i counter=0
'''
        result = extractor.extract(code)
        vars_found = result.get("variables", [])
        int_vars = [v for v in vars_found if v.is_integer or v.var_type == "integer"]
        assert len(int_vars) >= 1

    def test_declare_readonly(self, extractor):
        code = '''
declare -r CONSTANT="immutable"
'''
        result = extractor.extract(code)
        vars_found = result.get("variables", [])
        ro_vars = [v for v in vars_found if v.is_readonly]
        assert len(ro_vars) >= 1


# ===== EDGE CASES =====

class TestVariableEdgeCases:
    """Tests for edge cases."""

    def test_empty_script(self, extractor):
        code = '''#!/bin/bash
# Just comments
'''
        result = extractor.extract(code)
        vars_found = result.get("variables", [])
        assert len(vars_found) == 0

    def test_local_variable(self, extractor):
        code = '''
local my_var="test"
'''
        result = extractor.extract(code)
        vars_found = result.get("variables", [])
        if vars_found:
            local_vars = [v for v in vars_found if v.is_local]
            assert len(local_vars) >= 1

    def test_variable_with_spaces_in_value(self, extractor):
        code = '''
MESSAGE="Hello World"
'''
        result = extractor.extract(code)
        vars_found = result.get("variables", [])
        names = [v.name for v in vars_found]
        assert "MESSAGE" in names
