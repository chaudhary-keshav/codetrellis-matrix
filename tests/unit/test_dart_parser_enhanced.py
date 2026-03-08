"""
Tests for EnhancedDartParser — full parse(), framework detection, pubspec parsing, imports.

Part of CodeTrellis v4.27 Dart Language Support.
"""

import pytest
from codetrellis.dart_parser_enhanced import EnhancedDartParser, DartParseResult


@pytest.fixture
def parser():
    return EnhancedDartParser()


# ===== BASIC PARSE =====

class TestBasicParse:
    """Tests for basic Dart parsing capabilities."""

    def test_parse_returns_result(self, parser):
        code = '''
class Hello {
  void greet() => print('Hello!');
}
'''
        result = parser.parse(code, "hello.dart")
        assert isinstance(result, DartParseResult)

    def test_parse_empty_file(self, parser):
        result = parser.parse("", "empty.dart")
        assert isinstance(result, DartParseResult)

    def test_parse_comment_only(self, parser):
        code = '''
// This is a comment-only file
/// Documentation comment
/* Block comment */
'''
        result = parser.parse(code, "comments.dart")
        assert isinstance(result, DartParseResult)


# ===== CLASS PARSING =====

class TestClassParsing:
    """Tests for class parsing through full parser."""

    def test_parse_simple_class(self, parser):
        code = '''
class UserModel {
  final String id;
  final String name;
  final String email;

  UserModel({required this.id, required this.name, required this.email});

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'email': email,
  };

  factory UserModel.fromJson(Map<String, dynamic> json) => UserModel(
    id: json['id'],
    name: json['name'],
    email: json['email'],
  );
}
'''
        result = parser.parse(code, "user_model.dart")
        assert len(result.classes) >= 1
        assert result.classes[0].name == "UserModel"

    def test_parse_sealed_class_hierarchy(self, parser):
        code = '''
sealed class Result<T> {}

class Success<T> extends Result<T> {
  final T data;
  Success(this.data);
}

class Failure<T> extends Result<T> {
  final Exception error;
  Failure(this.error);
}

class Loading<T> extends Result<T> {}
'''
        result = parser.parse(code, "result.dart")
        assert len(result.classes) >= 3
        sealed = [c for c in result.classes if c.is_sealed]
        assert len(sealed) >= 1

    def test_parse_abstract_class(self, parser):
        code = '''
abstract class Repository<T> {
  Future<T?> findById(String id);
  Future<List<T>> findAll();
  Future<void> save(T entity);
  Future<void> delete(String id);
}
'''
        result = parser.parse(code, "repository.dart")
        assert len(result.classes) >= 1
        assert result.classes[0].is_abstract is True


# ===== FUNCTION PARSING =====

class TestFunctionParsing:
    """Tests for function parsing through full parser."""

    def test_parse_top_level_functions(self, parser):
        code = '''
Future<void> main() async {
  runApp(const MyApp());
}

void setupLocator() {
  GetIt.I.registerSingleton<AuthService>(AuthServiceImpl());
}
'''
        result = parser.parse(code, "main.dart")
        assert len(result.functions) >= 1

    def test_parse_async_functions(self, parser):
        code = '''
Future<List<User>> fetchUsers() async {
  final response = await dio.get('/api/users');
  return (response.data as List).map((e) => User.fromJson(e)).toList();
}

Stream<int> countDown(int from) async* {
  for (var i = from; i >= 0; i--) {
    yield i;
    await Future.delayed(const Duration(seconds: 1));
  }
}
'''
        result = parser.parse(code, "api.dart")
        assert len(result.functions) >= 1


# ===== CONSTRUCTOR PARSING =====

class TestConstructorParsing:
    """Tests for constructor extraction through full parser."""

    def test_parse_constructors(self, parser):
        code = '''
class DatabaseConnection {
  final String url;
  final int port;

  DatabaseConnection(this.url, this.port);
  DatabaseConnection.localhost() : this('localhost', 5432);
  const DatabaseConnection.test() : url = 'test', port = 0;

  factory DatabaseConnection.fromEnv() {
    return DatabaseConnection(
      Platform.environment['DB_URL'] ?? 'localhost',
      int.parse(Platform.environment['DB_PORT'] ?? '5432'),
    );
  }
}
'''
        result = parser.parse(code, "db.dart")
        assert len(result.constructors) >= 2


# ===== MIXIN & ENUM PARSING =====

class TestMixinEnumParsing:
    """Tests for mixin and enum parsing."""

    def test_parse_mixin(self, parser):
        code = '''
mixin Validator on FormField {
  String? validate(String? value) {
    if (value == null || value.isEmpty) return 'Required';
    return null;
  }
}
'''
        result = parser.parse(code, "validator.dart")
        assert len(result.mixins) >= 1

    def test_parse_enhanced_enum(self, parser):
        code = '''
enum HttpStatus {
  ok(200, 'OK'),
  notFound(404, 'Not Found'),
  serverError(500, 'Internal Server Error');

  const HttpStatus(this.code, this.message);
  final int code;
  final String message;

  bool get isSuccess => code >= 200 && code < 300;
  bool get isError => code >= 400;
}
'''
        result = parser.parse(code, "http_status.dart")
        assert len(result.enums) >= 1
        e = result.enums[0]
        assert e.name == "HttpStatus"
        assert e.has_members is True


# ===== EXTENSION & EXTENSION TYPE PARSING =====

class TestExtensionParsing:
    """Tests for extension and extension type parsing."""

    def test_parse_extension(self, parser):
        code = '''
extension DateTimeUtils on DateTime {
  String get formatted => '$year-${month.toString().padLeft(2, '0')}-${day.toString().padLeft(2, '0')}';
  bool get isToday {
    final now = DateTime.now();
    return year == now.year && month == now.month && day == now.day;
  }
}
'''
        result = parser.parse(code, "datetime_ext.dart")
        assert len(result.extensions) >= 1

    def test_parse_extension_type(self, parser):
        code = '''
extension type Email(String value) {
  Email.validated(String input)
    : assert(input.contains('@'), 'Invalid email'),
      value = input.toLowerCase();

  String get domain => value.split('@').last;
}
'''
        result = parser.parse(code, "email.dart")
        assert len(result.extension_types) >= 1


# ===== FRAMEWORK DETECTION =====

class TestFrameworkDetection:
    """Tests for automatic framework detection from imports."""

    def test_detect_flutter(self, parser):
        code = '''
import 'package:flutter/material.dart';
import 'package:flutter/widgets.dart';

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) => MaterialApp(home: Home());
}
'''
        result = parser.parse(code, "app.dart")
        assert result.is_flutter is True
        assert "flutter" in [f.lower() for f in result.detected_frameworks]

    def test_detect_riverpod(self, parser):
        code = '''
import 'package:flutter_riverpod/flutter_riverpod.dart';

final counterProvider = StateProvider<int>((ref) => 0);
'''
        result = parser.parse(code, "providers.dart")
        assert any("riverpod" in f.lower() for f in result.detected_frameworks)

    def test_detect_bloc(self, parser):
        code = '''
import 'package:flutter_bloc/flutter_bloc.dart';

class AppBloc extends Bloc<AppEvent, AppState> {
  AppBloc() : super(AppInitial());
}
'''
        result = parser.parse(code, "app_bloc.dart")
        assert any("bloc" in f.lower() for f in result.detected_frameworks)

    def test_detect_getx(self, parser):
        code = '''
import 'package:get/get.dart';

class MyController extends GetxController {
  var count = 0.obs;
}
'''
        result = parser.parse(code, "controller.dart")
        assert any("getx" in f.lower() for f in result.detected_frameworks)

    def test_detect_dio(self, parser):
        code = '''
import 'package:dio/dio.dart';

class ApiClient {
  final Dio _dio = Dio();
  Future<Response> get(String path) => _dio.get(path);
}
'''
        result = parser.parse(code, "client.dart")
        assert any("dio" in f.lower() for f in result.detected_frameworks)

    def test_detect_drift_database(self, parser):
        code = '''
import 'package:drift/drift.dart';

part 'database.g.dart';

class Users extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get name => text()();
}

@DriftDatabase(tables: [Users])
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(NativeDatabase.memory());
  @override
  int get schemaVersion => 1;
}
'''
        result = parser.parse(code, "database.dart")
        assert any("drift" in f.lower() for f in result.detected_frameworks)

    def test_detect_freezed(self, parser):
        code = '''
import 'package:freezed_annotation/freezed_annotation.dart';

part 'user.freezed.dart';
part 'user.g.dart';

@freezed
class User with _$User {
  const factory User({
    required String id,
    required String name,
    @Default('') String email,
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
}
'''
        result = parser.parse(code, "user.dart")
        assert any("freezed" in f.lower() for f in result.detected_frameworks)

    def test_detect_firebase(self, parser):
        code = '''
import 'package:firebase_core/firebase_core.dart';
import 'package:cloud_firestore/cloud_firestore.dart';

class FirestoreService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
}
'''
        result = parser.parse(code, "firestore.dart")
        assert any("firebase" in f.lower() for f in result.detected_frameworks)

    def test_detect_shelf(self, parser):
        code = '''
import 'package:shelf/shelf.dart';
import 'package:shelf/shelf_io.dart' as io;

Response _echoHandler(Request request) => Response.ok('Request for "${request.url}"');
'''
        result = parser.parse(code, "server.dart")
        assert any("shelf" in f.lower() for f in result.detected_frameworks)

    def test_detect_hive(self, parser):
        code = '''
import 'package:hive/hive.dart';

@HiveType(typeId: 0)
class Person extends HiveObject {
  @HiveField(0)
  late String name;
  @HiveField(1)
  late int age;
}
'''
        result = parser.parse(code, "person.dart")
        assert any("hive" in f.lower() for f in result.detected_frameworks)

    def test_detect_multiple_frameworks(self, parser):
        code = '''
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import 'package:go_router/go_router.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
'''
        result = parser.parse(code, "app.dart")
        assert result.is_flutter is True
        assert len(result.detected_frameworks) >= 3


# ===== PUBSPEC PARSING =====

class TestPubspecParsing:
    """Tests for pubspec.yaml parsing."""

    def test_parse_pubspec(self, parser):
        pubspec = '''
name: my_app
description: A Flutter application
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'
  flutter: '>=3.10.0'

dependencies:
  flutter:
    sdk: flutter
  flutter_riverpod: ^2.4.0
  dio: ^5.3.3
  go_router: ^12.1.0
  freezed_annotation: ^2.4.1
  json_annotation: ^4.8.1

dev_dependencies:
  flutter_test:
    sdk: flutter
  build_runner: ^2.4.7
  freezed: ^2.4.5
  json_serializable: ^6.7.1
  flutter_lints: ^2.0.0
'''
        result = parser.parse_pubspec(pubspec)
        assert result is not None
        assert "name" in result
        assert result["name"] == "my_app"

    def test_detect_frameworks_from_pubspec(self, parser):
        pubspec = '''
name: bloc_app
dependencies:
  flutter:
    sdk: flutter
  flutter_bloc: ^8.1.3
  equatable: ^2.0.5
'''
        result = parser.parse_pubspec(pubspec)
        assert result is not None


# ===== IMPORT EXTRACTION =====

class TestImportExtraction:
    """Tests for Dart import/export/part extraction."""

    def test_parse_imports(self, parser):
        code = '''
import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../models/user.dart';
import 'utils.dart' show formatDate, parseJson;
import 'legacy.dart' hide deprecatedMethod;
'''
        result = parser.parse(code, "main.dart")
        assert len(result.imports) >= 3

    def test_parse_exports(self, parser):
        code = '''
export 'src/models.dart';
export 'src/services.dart' show AuthService;
export 'src/utils.dart' hide internalHelper;
'''
        result = parser.parse(code, "lib.dart")
        assert len(result.exports) >= 1

    def test_parse_parts(self, parser):
        code = '''
part of 'database.dart';

class Users extends Table {
  IntColumn get id => integer().autoIncrement()();
}
'''
        result = parser.parse(code, "users.dart")
        assert len(result.parts) >= 1


# ===== ANNOTATION EXTRACTION =====

class TestAnnotationExtraction:
    """Tests for annotation extraction."""

    def test_parse_annotations(self, parser):
        code = '''
@immutable
class AppState {
  final int count;
  const AppState(this.count);
}

@deprecated
void oldMethod() {}

@override
String toString() => 'AppState';

@JsonSerializable()
class User {
  @JsonKey(name: 'user_name')
  final String userName;
  User(this.userName);
}
'''
        result = parser.parse(code, "app_state.dart")
        assert len(result.annotations) >= 1


# ===== NULL SAFETY =====

class TestNullSafety:
    """Tests for null safety analysis."""

    def test_null_safety_detection(self, parser):
        code = '''
String? nullableString;
late String lateString;
int nonNullable = 42;

void process(String? input) {
  final value = input ?? 'default';
  final length = input?.length;
  final exclaimed = input!.toUpperCase();
}
'''
        result = parser.parse(code, "null_safety.dart")
        ns = result.null_safety
        assert ns is not None


# ===== DART 3 FEATURES =====

class TestDart3Features:
    """Tests for Dart 3.x feature detection."""

    def test_records(self, parser):
        code = '''
(int, String) getUser() => (1, 'Alice');

({int id, String name}) getNamedUser() => (id: 1, name: 'Alice');

void process() {
  var (id, name) = getUser();
  var (:id2, :name2) = getNamedUser();
}
'''
        result = parser.parse(code, "records.dart")
        assert result.dart3_features is not None

    def test_patterns(self, parser):
        code = '''
String describe(Object obj) {
  return switch (obj) {
    int n when n > 0 => 'positive int',
    String s when s.isNotEmpty => 'non-empty string',
    List l when l.isNotEmpty => 'non-empty list',
    _ => 'something else',
  };
}
'''
        result = parser.parse(code, "patterns.dart")
        assert result.dart3_features is not None

    def test_class_modifiers(self, parser):
        code = '''
sealed class Shape {}
base class Circle extends Shape { final double r; Circle(this.r); }
interface class Drawable { void draw(); }
final class Config { final String k; Config(this.k); }
base mixin class Loggable { void log(String m) => print(m); }
'''
        result = parser.parse(code, "modifiers.dart")
        assert len(result.classes) >= 3


# ===== ISOLATE DETECTION =====

class TestIsolateDetection:
    """Tests for isolate and compute detection."""

    def test_isolate_spawn(self, parser):
        code = '''
import 'dart:isolate';

void heavyComputation(SendPort sendPort) {
  final result = fibonacci(40);
  sendPort.send(result);
}

Future<int> runInIsolate() async {
  final receivePort = ReceivePort();
  await Isolate.spawn(heavyComputation, receivePort.sendPort);
  return await receivePort.first as int;
}
'''
        result = parser.parse(code, "isolate.dart")
        assert len(result.isolates) >= 1

    def test_compute_function(self, parser):
        code = '''
import 'package:flutter/foundation.dart';

Future<List<Product>> parseProducts(String json) async {
  return await compute(_parseInBackground, json);
}

List<Product> _parseInBackground(String json) {
  return (jsonDecode(json) as List).map((e) => Product.fromJson(e)).toList();
}
'''
        result = parser.parse(code, "compute.dart")
        assert len(result.isolates) >= 1


# ===== PLATFORM CHANNEL DETECTION =====

class TestPlatformChannelDetection:
    """Tests for platform channel detection."""

    def test_method_channel(self, parser):
        code = '''
import 'package:flutter/services.dart';

class BatteryPlugin {
  static const platform = MethodChannel('com.example/battery');

  Future<int> getBatteryLevel() async {
    final int level = await platform.invokeMethod('getBatteryLevel');
    return level;
  }
}
'''
        result = parser.parse(code, "battery_plugin.dart")
        assert len(result.platform_channels) >= 1

    def test_event_channel(self, parser):
        code = '''
import 'package:flutter/services.dart';

class SensorPlugin {
  static const eventChannel = EventChannel('com.example/sensors');

  Stream<double> get sensorStream {
    return eventChannel.receiveBroadcastStream().map((event) => event as double);
  }
}
'''
        result = parser.parse(code, "sensor_plugin.dart")
        assert len(result.platform_channels) >= 1


# ===== DART PARSE RESULT =====

class TestDartParseResult:
    """Tests for DartParseResult dataclass."""

    def test_default_values(self):
        result = DartParseResult(file_path="test.dart")
        assert result.classes == []
        assert result.functions == []
        assert result.mixins == []
        assert result.enums == []
        assert result.extensions == []
        assert result.extension_types == []
        assert result.typedefs == []
        assert result.constructors == []
        assert result.getters == []
        assert result.setters == []
        assert result.widgets == []
        assert result.routes == []
        assert result.state_managers == []
        assert result.grpc_services == []
        assert result.flutter_routes == []
        assert result.models == []
        assert result.data_classes == []
        assert result.migrations == []
        assert result.annotations == []
        assert result.imports == []
        assert result.exports == []
        assert result.parts == []
        assert result.isolates == []
        assert result.platform_channels == []
        assert result.detected_frameworks == []
        assert result.is_flutter is False

    def test_result_with_data(self):
        result = DartParseResult(
            file_path="app.dart",
            is_flutter=True,
            detected_frameworks=["flutter", "riverpod", "dio"],
            dart_version="3.0.0",
            flutter_version="3.10.0",
        )
        assert result.is_flutter is True
        assert len(result.detected_frameworks) == 3
        assert result.dart_version == "3.0.0"
        assert result.flutter_version == "3.10.0"
