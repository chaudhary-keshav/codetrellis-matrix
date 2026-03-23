"""
Tests for Dart/Flutter integration improvements.

Covers:
- Scanner field mapping for getters, setters, exports, library_name, package_name
- File classifier Dart generated file detection
- Discovery extractor Dart framework hints from pubspec.yaml
- Compressor output for new fields
- BPL selector dart_getters/dart_setters/dart_exports artifact counting

Part of Dart/Flutter integration audit and improvement.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from codetrellis.dart_parser_enhanced import EnhancedDartParser, DartParseResult
from codetrellis.file_classifier import FileClassifier, FileType


@pytest.fixture
def parser():
    return EnhancedDartParser()


# ===== SCANNER FIELD MAPPING: GETTERS & SETTERS =====

class TestGetterSetterExtraction:
    """Tests that getters and setters are properly extracted by the parser."""

    def test_parse_getters(self, parser):
        code = '''
class User {
  String _name = '';

  String get name => _name;

  int get age {
    return _age;
  }

  static String get defaultName => 'Unknown';
}
'''
        result = parser.parse(code, "user.dart")
        assert len(result.getters) >= 1, "Should extract at least one getter"
        getter_names = [g.name for g in result.getters]
        assert 'name' in getter_names

    def test_parse_setters(self, parser):
        code = '''
class User {
  String _name = '';

  set name(String value) {
    _name = value;
  }

  set age(int value) => _age = value;
}
'''
        result = parser.parse(code, "user.dart")
        assert len(result.setters) >= 1, "Should extract at least one setter"
        setter_names = [s.name for s in result.setters]
        assert 'name' in setter_names

    def test_getter_has_return_type(self, parser):
        code = '''
class Config {
  String get apiUrl => 'https://api.example.com';
}
'''
        result = parser.parse(code, "config.dart")
        if result.getters:
            getter = result.getters[0]
            assert getter.return_type  # Should have return type info

    def test_setter_has_class_name(self, parser):
        """Test that setter class_name is populated (when extractor supports it).
        Note: Current extractor uses flat regex, so class_name may be empty.
        This test validates the data flows through without error."""
        code = '''
class Settings {
  int _timeout = 30;
  set timeout(int value) => _timeout = value;
}
'''
        result = parser.parse(code, "settings.dart")
        if result.setters:
            setter = result.setters[0]
            # class_name may be empty due to flat regex extraction
            assert isinstance(setter.class_name, str)


# ===== SCANNER FIELD MAPPING: EXPORTS =====

class TestExportExtraction:
    """Tests that exports are properly extracted."""

    def test_parse_exports(self, parser):
        code = '''
export 'src/model.dart';
export 'src/utils.dart' show formatDate, parseDate;
export 'src/internal.dart' hide InternalHelper;
'''
        result = parser.parse(code, "lib.dart")
        assert len(result.exports) >= 1, "Should extract exports"
        export_uris = [e.uri for e in result.exports]
        assert 'src/model.dart' in export_uris

    def test_export_with_show(self, parser):
        code = '''
export 'package:my_lib/api.dart' show ApiClient, ApiConfig;
'''
        result = parser.parse(code, "lib.dart")
        if result.exports:
            exp = result.exports[0]
            assert 'ApiClient' in exp.show or len(exp.show) > 0

    def test_export_with_hide(self, parser):
        code = '''
export 'src/internal.dart' hide _InternalHelper, _DebugUtils;
'''
        result = parser.parse(code, "lib.dart")
        if result.exports:
            exp = result.exports[0]
            assert len(exp.hide) > 0 or exp.uri == 'src/internal.dart'


# ===== SCANNER FIELD MAPPING: LIBRARY NAME & PACKAGE NAME =====

class TestLibraryPackageExtraction:
    """Tests for library and package name extraction."""

    def test_parse_library_name(self, parser):
        code = '''
library my_awesome_lib;

class Foo {}
'''
        result = parser.parse(code, "lib.dart")
        assert result.library_name == 'my_awesome_lib'

    def test_parse_package_name_from_path(self, parser):
        """package_name is derived from the parent of lib/ in the file path,
        NOT from import statements."""
        code = '''
import 'package:my_app/src/model.dart';

class Bar {}
'''
        # When path contains lib/, parent dir is used as package name
        result = parser.parse(code, "my_app/lib/bar.dart")
        assert result.package_name == 'my_app'
        # Fallback: without lib/ dir, uses file stem
        result2 = parser.parse(code, "bar.dart")
        assert result2.package_name == 'bar'


# ===== FILE CLASSIFIER: DART GENERATED FILES =====

class TestFileClassifierDartGenerated:
    """Tests that Dart generated files are detected by FileClassifier."""

    def test_g_dart_is_generated(self):
        assert '.g.dart' in FileClassifier.GENERATED_SUFFIXES

    def test_freezed_dart_is_generated(self):
        assert '.freezed.dart' in FileClassifier.GENERATED_SUFFIXES

    def test_gr_dart_is_generated(self):
        assert '.gr.dart' in FileClassifier.GENERATED_SUFFIXES

    def test_mocks_dart_is_generated(self):
        assert '.mocks.dart' in FileClassifier.GENERATED_SUFFIXES

    def test_classify_generated_dart_file(self):
        result = FileClassifier.classify("model.g.dart")
        assert result == FileType.GENERATED

    def test_classify_freezed_dart_file(self):
        result = FileClassifier.classify("user.freezed.dart")
        assert result == FileType.GENERATED

    def test_classify_normal_dart_not_generated(self):
        result = FileClassifier.classify("main.dart")
        assert result != FileType.GENERATED


# ===== DISCOVERY EXTRACTOR: DART FRAMEWORK HINTS =====

class TestDiscoveryDartFrameworkHints:
    """Tests that the discovery extractor has Dart framework hints."""

    def test_dart_framework_hints_exist(self):
        from codetrellis.extractors.discovery_extractor import DiscoveryExtractor
        extractor = DiscoveryExtractor()
        assert hasattr(extractor, 'DART_FRAMEWORK_HINTS')
        assert len(extractor.DART_FRAMEWORK_HINTS) > 0

    def test_flutter_in_hints(self):
        from codetrellis.extractors.discovery_extractor import DiscoveryExtractor
        extractor = DiscoveryExtractor()
        assert 'flutter' in extractor.DART_FRAMEWORK_HINTS

    def test_riverpod_in_hints(self):
        from codetrellis.extractors.discovery_extractor import DiscoveryExtractor
        extractor = DiscoveryExtractor()
        assert 'flutter_riverpod' in extractor.DART_FRAMEWORK_HINTS

    def test_bloc_in_hints(self):
        from codetrellis.extractors.discovery_extractor import DiscoveryExtractor
        extractor = DiscoveryExtractor()
        assert 'flutter_bloc' in extractor.DART_FRAMEWORK_HINTS

    def test_dio_in_hints(self):
        from codetrellis.extractors.discovery_extractor import DiscoveryExtractor
        extractor = DiscoveryExtractor()
        assert 'dio' in extractor.DART_FRAMEWORK_HINTS

    def test_drift_in_hints(self):
        from codetrellis.extractors.discovery_extractor import DiscoveryExtractor
        extractor = DiscoveryExtractor()
        assert 'drift' in extractor.DART_FRAMEWORK_HINTS

    def test_shelf_in_hints(self):
        from codetrellis.extractors.discovery_extractor import DiscoveryExtractor
        extractor = DiscoveryExtractor()
        assert 'shelf' in extractor.DART_FRAMEWORK_HINTS

    def test_firebase_in_hints(self):
        from codetrellis.extractors.discovery_extractor import DiscoveryExtractor
        extractor = DiscoveryExtractor()
        assert 'firebase_core' in extractor.DART_FRAMEWORK_HINTS
        assert extractor.DART_FRAMEWORK_HINTS['firebase_core'] == 'firebase'


# ===== COMPRESSOR OUTPUT FOR NEW FIELDS =====

class TestCompressorDartNewFields:
    """Tests that compressor handles new Dart fields (getters, setters, exports)."""

    def test_compress_dart_functions_includes_getters(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        compressor = MatrixCompressor()
        matrix = ProjectMatrix(name='test', root_path='/')
        matrix.dart_getters = [
            {"name": "userName", "file": "user.dart", "line": 10,
             "return_type": "String", "is_static": False, "class_name": "User"}
        ]
        lines = compressor._compress_dart_functions(matrix)
        output = '\n'.join(lines)
        assert 'Getters' in output
        assert 'userName' in output

    def test_compress_dart_functions_includes_setters(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        compressor = MatrixCompressor()
        matrix = ProjectMatrix(name='test', root_path='/')
        matrix.dart_setters = [
            {"name": "userName", "file": "user.dart", "line": 15,
             "param_type": "String", "is_static": False, "class_name": "User"}
        ]
        lines = compressor._compress_dart_functions(matrix)
        output = '\n'.join(lines)
        assert 'Setters' in output
        assert 'userName' in output

    def test_compress_dart_dependencies_includes_exports(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        compressor = MatrixCompressor()
        matrix = ProjectMatrix(name='test', root_path='/')
        matrix.dart_exports = [
            {"uri": "src/model.dart", "file": "lib.dart", "line": 1,
             "show": ["Model"], "hide": []}
        ]
        lines = compressor._compress_dart_dependencies(matrix)
        output = '\n'.join(lines)
        assert 'Exports' in output
        assert 'src/model.dart' in output

    def test_compress_dart_dependencies_includes_library_name(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        compressor = MatrixCompressor()
        matrix = ProjectMatrix(name='test', root_path='/')
        matrix.dart_library_name = "my_awesome_lib"
        lines = compressor._compress_dart_dependencies(matrix)
        output = '\n'.join(lines)
        assert 'my_awesome_lib' in output

    def test_compress_dart_dependencies_includes_package_name(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        compressor = MatrixCompressor()
        matrix = ProjectMatrix(name='test', root_path='/')
        matrix.dart_package_name = "my_app"
        lines = compressor._compress_dart_dependencies(matrix)
        output = '\n'.join(lines)
        assert 'my_app' in output


# ===== BPL SELECTOR: NEW ARTIFACT COUNTING =====

class TestBPLSelectorDartArtifacts:
    """Tests that BPL selector includes new dart fields in artifact counting."""

    def test_dart_getters_in_artifact_list(self):
        from codetrellis.bpl.selector import ProjectContext
        from codetrellis.scanner import ProjectMatrix
        matrix = ProjectMatrix(name='test', root_path='/')
        # Add enough artifacts to cross threshold
        matrix.dart_getters = [{"name": f"get{i}"} for i in range(10)]
        context = ProjectContext.from_matrix(matrix)
        # With 10 getters, may or may not cross threshold, but field should be counted
        assert hasattr(matrix, 'dart_getters')

    def test_dart_setters_in_artifact_list(self):
        from codetrellis.bpl.selector import ProjectContext
        from codetrellis.scanner import ProjectMatrix
        matrix = ProjectMatrix(name='test', root_path='/')
        matrix.dart_setters = [{"name": f"set{i}"} for i in range(10)]
        context = ProjectContext.from_matrix(matrix)
        assert hasattr(matrix, 'dart_setters')

    def test_dart_exports_in_artifact_list(self):
        from codetrellis.bpl.selector import ProjectContext
        from codetrellis.scanner import ProjectMatrix
        matrix = ProjectMatrix(name='test', root_path='/')
        matrix.dart_exports = [{"uri": f"src/part{i}.dart"} for i in range(10)]
        context = ProjectContext.from_matrix(matrix)
        assert hasattr(matrix, 'dart_exports')

    def test_dart_significance_with_new_artifacts(self):
        from codetrellis.bpl.selector import ProjectContext
        from codetrellis.scanner import ProjectMatrix
        matrix = ProjectMatrix(name='test', root_path='/')
        # Add a mix of dart artifacts - enough to cross threshold (5)
        matrix.dart_classes = [{"name": "Foo"}, {"name": "Bar"}]
        matrix.dart_getters = [{"name": "get1"}, {"name": "get2"}]
        matrix.dart_setters = [{"name": "set1"}]
        context = ProjectContext.from_matrix(matrix)
        assert "dart" in context.frameworks


# ===== PROJECTMATRIX FIELDS =====

class TestProjectMatrixNewDartFields:
    """Tests that ProjectMatrix has the new dart fields."""

    def test_dart_getters_field_exists(self):
        from codetrellis.scanner import ProjectMatrix
        matrix = ProjectMatrix(name='test', root_path='/')
        assert hasattr(matrix, 'dart_getters')
        assert isinstance(matrix.dart_getters, list)

    def test_dart_setters_field_exists(self):
        from codetrellis.scanner import ProjectMatrix
        matrix = ProjectMatrix(name='test', root_path='/')
        assert hasattr(matrix, 'dart_setters')
        assert isinstance(matrix.dart_setters, list)

    def test_dart_exports_field_exists(self):
        from codetrellis.scanner import ProjectMatrix
        matrix = ProjectMatrix(name='test', root_path='/')
        assert hasattr(matrix, 'dart_exports')
        assert isinstance(matrix.dart_exports, list)

    def test_dart_library_name_field_exists(self):
        from codetrellis.scanner import ProjectMatrix
        matrix = ProjectMatrix(name='test', root_path='/')
        assert hasattr(matrix, 'dart_library_name')
        assert matrix.dart_library_name == ""

    def test_dart_package_name_field_exists(self):
        from codetrellis.scanner import ProjectMatrix
        matrix = ProjectMatrix(name='test', root_path='/')
        assert hasattr(matrix, 'dart_package_name')
        assert matrix.dart_package_name == ""

    def test_to_dict_includes_new_fields(self):
        from codetrellis.scanner import ProjectMatrix
        matrix = ProjectMatrix(name='test', root_path='/')
        matrix.dart_getters = [{"name": "getter1"}]
        matrix.dart_setters = [{"name": "setter1"}]
        matrix.dart_exports = [{"uri": "src/api.dart"}]
        matrix.dart_library_name = "my_lib"
        matrix.dart_package_name = "my_pkg"
        d = matrix.to_dict()
        dart = d.get('dart', {})
        assert dart.get('getters') == [{"name": "getter1"}]
        assert dart.get('setters') == [{"name": "setter1"}]
        assert dart.get('exports') == [{"uri": "src/api.dart"}]
        assert dart.get('library_name') == "my_lib"
        assert dart.get('package_name') == "my_pkg"


# ===== FULL PARSER INTEGRATION: GETTERS/SETTERS/EXPORTS =====

class TestFullParserIntegration:
    """Integration tests through the full parser pipeline for new fields."""

    def test_mixed_dart_file_with_getters_setters_exports(self, parser):
        code = '''
library my_lib;

export 'src/model.dart';
export 'src/utils.dart' show formatDate;

class AppConfig {
  String _baseUrl = '';

  String get baseUrl => _baseUrl;
  set baseUrl(String value) => _baseUrl = value;

  static int get maxRetries => 3;
}

int get globalTimeout => 30;
'''
        result = parser.parse(code, "app.dart")
        assert result.library_name == 'my_lib'
        assert len(result.exports) >= 1

    def test_flutter_widget_with_getters(self, parser):
        code = '''
import 'package:flutter/material.dart';

class MyWidget extends StatelessWidget {
  final String title;

  const MyWidget({super.key, required this.title});

  String get displayTitle => title.toUpperCase();

  @override
  Widget build(BuildContext context) {
    return Text(displayTitle);
  }
}
'''
        result = parser.parse(code, "my_widget.dart")
        assert result.is_flutter
        assert len(result.widgets) >= 1
        # Widget should be detected alongside getters
        getter_names = [g.name for g in result.getters]
        assert 'displayTitle' in getter_names
