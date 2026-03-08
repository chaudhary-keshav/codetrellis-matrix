"""
Tests for MatrixCompressor — Java and Kotlin compressed output sections.

Part of CodeTrellis v4.12 Java & Kotlin Language Support.
"""

import pytest
from types import SimpleNamespace
from codetrellis.compressor import MatrixCompressor


@pytest.fixture
def compressor():
    return MatrixCompressor()


def _make_matrix(**kwargs):
    """Create a minimal matrix-like object with the given attributes."""
    return SimpleNamespace(**kwargs)


# ===== JAVA_TYPES COMPRESSION =====

class TestJavaTypesCompression:
    """Tests for _compress_java_types output format."""

    def test_class_output(self, compressor):
        matrix = _make_matrix(
            java_classes=[{
                'name': 'UserService',
                'kind': 'class',
                'is_exported': True,
                'fields': [
                    {'name': 'name', 'type': 'String', 'annotations': []},
                    {'name': 'age', 'type': 'int', 'annotations': []},
                ],
                'extends': None,
                'implements': [],
                'annotations': ['Service'],
                'generic_params': [],
                'file': 'UserService.java',
            }],
            java_interfaces=[],
            java_records=[],
            java_enums=[],
            java_annotation_defs=[],
        )
        lines = compressor._compress_java_types(matrix)
        assert any("UserService" in l for l in lines)
        assert any("name:String" in l for l in lines)
        assert any("@Service" in l for l in lines)

    def test_non_exported_class_excluded(self, compressor):
        matrix = _make_matrix(
            java_classes=[{
                'name': 'InternalHelper',
                'kind': 'class',
                'is_exported': False,
                'fields': [],
                'extends': None,
                'implements': [],
                'annotations': [],
                'generic_params': [],
                'file': 'InternalHelper.java',
            }],
            java_interfaces=[],
            java_records=[],
            java_enums=[],
            java_annotation_defs=[],
        )
        lines = compressor._compress_java_types(matrix)
        assert not any("InternalHelper" in l for l in lines)

    def test_interface_output(self, compressor):
        matrix = _make_matrix(
            java_classes=[],
            java_interfaces=[{
                'name': 'UserRepository',
                'is_exported': True,
                'methods': ['findById', 'save', 'delete'],
                'extends': [],
                'is_functional': False,
                'is_sealed': False,
                'file': 'UserRepository.java',
            }],
            java_records=[],
            java_enums=[],
            java_annotation_defs=[],
        )
        lines = compressor._compress_java_types(matrix)
        assert any("UserRepository" in l for l in lines)
        assert any("findById" in l for l in lines)

    def test_record_output(self, compressor):
        matrix = _make_matrix(
            java_classes=[],
            java_interfaces=[],
            java_records=[{
                'name': 'Point',
                'is_exported': True,
                'components': [
                    {'name': 'x', 'type': 'int'},
                    {'name': 'y', 'type': 'int'},
                ],
                'implements': [],
                'annotations': [],
                'file': 'Point.java',
            }],
            java_enums=[],
            java_annotation_defs=[],
        )
        lines = compressor._compress_java_types(matrix)
        assert any("record Point" in l for l in lines)
        assert any("x:int" in l for l in lines)

    def test_enum_output(self, compressor):
        matrix = _make_matrix(
            java_classes=[],
            java_interfaces=[],
            java_records=[],
            java_enums=[{
                'name': 'Status',
                'is_exported': True,
                'constants': [
                    {'name': 'ACTIVE'},
                    {'name': 'INACTIVE'},
                    {'name': 'PENDING'},
                ],
                'methods': [],
                'file': 'Status.java',
            }],
            java_annotation_defs=[],
        )
        lines = compressor._compress_java_types(matrix)
        assert any("Status" in l for l in lines)
        assert any("ACTIVE" in l for l in lines)

    def test_annotation_def_output(self, compressor):
        matrix = _make_matrix(
            java_classes=[],
            java_interfaces=[],
            java_records=[],
            java_enums=[],
            java_annotation_defs=[{
                'name': 'MyAnnotation',
                'elements': [{'name': 'value', 'type': 'String'}],
                'retention': 'RUNTIME',
                'target': ['TYPE'],
                'file': 'MyAnnotation.java',
            }],
        )
        lines = compressor._compress_java_types(matrix)
        assert any("@interface MyAnnotation" in l for l in lines)

    def test_empty_java_types(self, compressor):
        matrix = _make_matrix()
        lines = compressor._compress_java_types(matrix)
        assert lines == []


# ===== JAVA API COMPRESSION =====

class TestJavaAPICompression:
    """Tests for _compress_java_api output format."""

    def test_endpoint_output(self, compressor):
        matrix = _make_matrix(
            java_endpoints=[{
                'method': 'GET',
                'path': '/api/users/{id}',
                'handler': 'getUser',
                'framework': 'spring',
                'consumes': '',
                'produces': '',
                'file': 'UserController.java',
            }],
            java_grpc_services=[],
            java_message_listeners=[],
        )
        lines = compressor._compress_java_api(matrix)
        assert any("GET:/api/users/{id}" in l for l in lines)
        assert any("getUser" in l for l in lines)

    def test_grpc_output(self, compressor):
        matrix = _make_matrix(
            java_endpoints=[],
            java_grpc_services=[{
                'name': 'GreeterServiceImpl',
                'base_class': 'GreeterGrpc.GreeterImplBase',
                'methods': ['sayHello'],
                'file': 'GreeterServiceImpl.java',
            }],
            java_message_listeners=[],
        )
        lines = compressor._compress_java_api(matrix)
        assert any("GreeterServiceImpl" in l for l in lines)
        assert any("sayHello" in l for l in lines)

    def test_message_listener_output(self, compressor):
        matrix = _make_matrix(
            java_endpoints=[],
            java_grpc_services=[],
            java_message_listeners=[{
                'type': 'kafka',
                'topic': 'user-events',
                'handler': 'handleUserEvent',
                'file': 'UserEventListener.java',
            }],
        )
        lines = compressor._compress_java_api(matrix)
        assert any("kafka" in l for l in lines)
        assert any("user-events" in l for l in lines)

    def test_empty_api(self, compressor):
        matrix = _make_matrix()
        lines = compressor._compress_java_api(matrix)
        assert lines == []


# ===== JAVA MODELS COMPRESSION =====

class TestJavaModelsCompression:
    """Tests for _compress_java_models output format."""

    def test_entity_output(self, compressor):
        matrix = _make_matrix(
            java_entities=[{
                'name': 'User',
                'table_name': 'users',
                'columns': [
                    {'name': 'id', 'type': 'Long', 'nullable': False, 'unique': False},
                    {'name': 'username', 'type': 'String', 'nullable': False, 'unique': True},
                    {'name': 'email', 'type': 'String', 'nullable': False, 'unique': False},
                ],
                'relationships': [],
            }],
            java_repositories=[],
        )
        lines = compressor._compress_java_models(matrix)
        assert any("User" in l for l in lines)
        assert any("table:users" in l for l in lines)
        assert any("id:Long" in l for l in lines)

    def test_entity_with_relationships(self, compressor):
        matrix = _make_matrix(
            java_entities=[{
                'name': 'Order',
                'table_name': 'orders',
                'columns': [
                    {'name': 'id', 'type': 'Long', 'nullable': False, 'unique': False},
                ],
                'relationships': [{
                    'type': 'ManyToOne',
                    'target': 'Customer',
                    'mapped_by': None,
                }],
            }],
            java_repositories=[],
        )
        lines = compressor._compress_java_models(matrix)
        assert any("rels:" in l for l in lines)
        assert any("ManyToOne" in l for l in lines)
        assert any("Customer" in l for l in lines)

    def test_repository_output(self, compressor):
        matrix = _make_matrix(
            java_entities=[],
            java_repositories=[{
                'name': 'UserRepository',
                'entity_type': 'User',
                'repo_type': 'JpaRepository',
                'custom_methods': ['findByEmail', 'findByName'],
            }],
        )
        lines = compressor._compress_java_models(matrix)
        assert any("UserRepository" in l for l in lines)
        assert any("JpaRepository" in l for l in lines)
        assert any("User" in l for l in lines)

    def test_empty_models(self, compressor):
        matrix = _make_matrix()
        lines = compressor._compress_java_models(matrix)
        assert lines == []


# ===== KOTLIN TYPES COMPRESSION =====

class TestKotlinTypesCompression:
    """Tests for _compress_kotlin_types output format."""

    def test_data_class_output(self, compressor):
        matrix = _make_matrix(
            kotlin_classes=[{
                'name': 'User',
                'kind': 'data_class',
                'is_exported': True,
                'primary_constructor': [
                    {'name': 'name', 'type': 'String', 'is_val': True},
                    {'name': 'email', 'type': 'String', 'is_val': True},
                ],
                'properties': [],
                'extends': None,
                'implements': [],
                'annotations': [],
                'generic_params': [],
                'companion_object': None,
                'file': 'User.kt',
            }],
            kotlin_objects=[],
            kotlin_interfaces=[],
            kotlin_enums=[],
        )
        lines = compressor._compress_kotlin_types(matrix)
        assert any("data" in l and "User" in l for l in lines)

    def test_object_output(self, compressor):
        matrix = _make_matrix(
            kotlin_classes=[],
            kotlin_objects=[{
                'name': 'AppConfig',
                'kind': 'object',
                'methods': ['init', 'configure'],
                'extends': None,
                'implements': [],
                'file': 'AppConfig.kt',
            }],
            kotlin_interfaces=[],
            kotlin_enums=[],
        )
        lines = compressor._compress_kotlin_types(matrix)
        assert any("AppConfig" in l for l in lines)

    def test_enum_class_output(self, compressor):
        matrix = _make_matrix(
            kotlin_classes=[],
            kotlin_objects=[],
            kotlin_interfaces=[],
            kotlin_enums=[{
                'name': 'Direction',
                'entries': ['NORTH', 'SOUTH', 'EAST', 'WEST'],
                'methods': [],
                'file': 'Direction.kt',
            }],
        )
        lines = compressor._compress_kotlin_types(matrix)
        assert any("Direction" in l for l in lines)
        assert any("NORTH" in l for l in lines)

    def test_empty_kotlin_types(self, compressor):
        matrix = _make_matrix()
        lines = compressor._compress_kotlin_types(matrix)
        assert lines == []


# ===== KOTLIN API COMPRESSION =====

class TestKotlinAPICompression:
    """Tests for _compress_kotlin_api output format."""

    def test_ktor_endpoint(self, compressor):
        matrix = _make_matrix(
            kotlin_endpoints=[{
                'method': 'GET',
                'path': '/api/hello',
                'handler': '',
                'framework': 'ktor',
                'consumes': '',
                'produces': '',
                'file': 'Routing.kt',
            }],
        )
        lines = compressor._compress_kotlin_api(matrix)
        assert any("GET:/api/hello" in l for l in lines)
        assert any("Ktor" in l for l in lines)

    def test_empty_kotlin_api(self, compressor):
        matrix = _make_matrix()
        lines = compressor._compress_kotlin_api(matrix)
        assert lines == []
