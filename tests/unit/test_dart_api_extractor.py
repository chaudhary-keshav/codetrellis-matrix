"""
Tests for DartAPIExtractor — widgets, routes, state managers, gRPC services.

Part of CodeTrellis v4.27 Dart Language Support.
"""

import pytest
from codetrellis.extractors.dart.api_extractor import DartAPIExtractor


@pytest.fixture
def extractor():
    return DartAPIExtractor()


# ===== FLUTTER WIDGET EXTRACTION =====

class TestWidgetExtraction:
    """Tests for Flutter widget extraction."""

    def test_stateless_widget(self, extractor):
        code = '''
class GreetingWidget extends StatelessWidget {
  final String name;
  const GreetingWidget({super.key, required this.name});

  @override
  Widget build(BuildContext context) {
    return Text('Hello, $name!');
  }
}
'''
        result = extractor.extract(code, "greeting.dart")
        assert len(result["widgets"]) >= 1
        w = result["widgets"][0]
        assert w.name == "GreetingWidget"
        assert w.widget_type == "stateless"

    def test_stateful_widget(self, extractor):
        code = '''
class CounterWidget extends StatefulWidget {
  const CounterWidget({super.key});

  @override
  State<CounterWidget> createState() => _CounterWidgetState();
}

class _CounterWidgetState extends State<CounterWidget> {
  int _count = 0;

  @override
  Widget build(BuildContext context) {
    return Text('$_count');
  }
}
'''
        result = extractor.extract(code, "counter.dart")
        widgets = result["widgets"]
        stateful = [w for w in widgets if w.widget_type == "stateful"]
        assert len(stateful) >= 1
        assert stateful[0].name == "CounterWidget"

    def test_inherited_widget(self, extractor):
        code = '''
class ThemeProvider extends InheritedWidget {
  final ThemeData theme;

  const ThemeProvider({
    super.key,
    required this.theme,
    required super.child,
  });

  static ThemeProvider of(BuildContext context) {
    return context.dependOnInheritedWidgetOfExactType<ThemeProvider>()!;
  }

  @override
  bool updateShouldNotify(ThemeProvider oldWidget) => theme != oldWidget.theme;
}
'''
        result = extractor.extract(code, "theme_provider.dart")
        widgets = result["widgets"]
        inherited = [w for w in widgets if w.widget_type == "inherited"]
        assert len(inherited) >= 1

    def test_render_object_widget(self, extractor):
        code = '''
class CustomPaint extends SingleChildRenderObjectWidget {
  final CustomPainter painter;

  const CustomPaint({super.key, required this.painter, super.child});

  @override
  RenderCustomPaint createRenderObject(BuildContext context) {
    return RenderCustomPaint(painter: painter);
  }
}
'''
        result = extractor.extract(code, "custom_paint.dart")
        widgets = result["widgets"]
        assert len(widgets) >= 1


# ===== ROUTE EXTRACTION =====

class TestRouteExtraction:
    """Tests for HTTP route extraction (Shelf, Dart Frog, Serverpod)."""

    def test_shelf_route(self, extractor):
        code = '''
import 'package:shelf/shelf.dart';
import 'package:shelf_router/shelf_router.dart';

class Api {
  Router get router {
    final router = Router();

    router.get('/users', _getUsers);
    router.post('/users', _createUser);
    router.get('/users/<id>', _getUserById);
    router.put('/users/<id>', _updateUser);
    router.delete('/users/<id>', _deleteUser);

    return router;
  }

  Response _getUsers(Request request) => Response.ok('users');
  Response _createUser(Request request) => Response.ok('created');
  Response _getUserById(Request request, String id) => Response.ok('user $id');
  Response _updateUser(Request request, String id) => Response.ok('updated $id');
  Response _deleteUser(Request request, String id) => Response.ok('deleted $id');
}
'''
        result = extractor.extract(code, "api.dart")
        assert len(result["routes"]) >= 1

    def test_dart_frog_route(self, extractor):
        code = '''
import 'package:dart_frog/dart_frog.dart';

Response onRequest(RequestContext context) {
  return switch (context.request.method) {
    HttpMethod.get => _get(context),
    HttpMethod.post => _post(context),
    _ => Response(statusCode: HttpStatus.methodNotAllowed),
  };
}

Response _get(RequestContext context) {
  return Response.json(body: {'message': 'Hello'});
}

Response _post(RequestContext context) {
  return Response.json(body: {'created': true});
}
'''
        result = extractor.extract(code, "routes/index.dart")
        assert len(result["routes"]) >= 1

    def test_serverpod_endpoint(self, extractor):
        code = '''
import 'package:serverpod/serverpod.dart';

class UserEndpoint extends Endpoint {
  Future<User> getUser(Session session, int id) async {
    return await User.db.findById(session, id) ?? User(name: 'Unknown');
  }

  Future<void> createUser(Session session, User user) async {
    await User.db.insertRow(session, user);
  }
}
'''
        result = extractor.extract(code, "user_endpoint.dart")
        assert len(result["routes"]) >= 1


# ===== STATE MANAGEMENT EXTRACTION =====

class TestStateManagementExtraction:
    """Tests for state management extraction (Riverpod, Bloc, GetX, MobX)."""

    def test_riverpod_provider(self, extractor):
        code = '''
import 'package:flutter_riverpod/flutter_riverpod.dart';

final userProvider = StateNotifierProvider<UserNotifier, UserState>((ref) {
  return UserNotifier(ref.watch(repositoryProvider));
});

class UserNotifier extends StateNotifier<UserState> {
  final UserRepository _repository;
  UserNotifier(this._repository) : super(const UserState.initial());

  Future<void> fetchUsers() async {
    state = const UserState.loading();
    final users = await _repository.getAll();
    state = UserState.loaded(users);
  }
}
'''
        result = extractor.extract(code, "user_provider.dart")
        assert len(result["state_managers"]) >= 1
        sm = result["state_managers"][0]
        assert "riverpod" in sm.pattern.lower()

    def test_bloc_pattern(self, extractor):
        code = '''
import 'package:flutter_bloc/flutter_bloc.dart';

class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final AuthRepository _authRepository;

  AuthBloc(this._authRepository) : super(const AuthInitial()) {
    on<LoginRequested>(_onLoginRequested);
    on<LogoutRequested>(_onLogoutRequested);
  }

  Future<void> _onLoginRequested(LoginRequested event, Emitter<AuthState> emit) async {
    emit(const AuthLoading());
    try {
      final user = await _authRepository.login(event.email, event.password);
      emit(AuthAuthenticated(user));
    } catch (e) {
      emit(AuthError(e.toString()));
    }
  }

  Future<void> _onLogoutRequested(LogoutRequested event, Emitter<AuthState> emit) async {
    await _authRepository.logout();
    emit(const AuthInitial());
  }
}
'''
        result = extractor.extract(code, "auth_bloc.dart")
        assert len(result["state_managers"]) >= 1
        sm = result["state_managers"][0]
        assert "bloc" in sm.pattern.lower()

    def test_cubit_pattern(self, extractor):
        code = '''
import 'package:flutter_bloc/flutter_bloc.dart';

class CounterCubit extends Cubit<int> {
  CounterCubit() : super(0);

  void increment() => emit(state + 1);
  void decrement() => emit(state - 1);
}
'''
        result = extractor.extract(code, "counter_cubit.dart")
        assert len(result["state_managers"]) >= 1

    def test_getx_controller(self, extractor):
        code = '''
import 'package:get/get.dart';

class HomeController extends GetxController {
  final count = 0.obs;
  final items = <String>[].obs;

  void increment() => count.value++;
  void addItem(String item) => items.add(item);

  @override
  void onInit() {
    super.onInit();
    fetchItems();
  }
}
'''
        result = extractor.extract(code, "home_controller.dart")
        assert len(result["state_managers"]) >= 1
        sm = result["state_managers"][0]
        assert "getx" in sm.pattern.lower()

    def test_mobx_store(self, extractor):
        code = '''
import 'package:mobx/mobx.dart';

part 'todo_store.g.dart';

class TodoStore extends _TodoStoreBase with _$TodoStore {
  TodoStore() : super();
}

abstract class _TodoStoreBase with Store {
  @observable
  ObservableList<Todo> todos = ObservableList<Todo>();

  @computed
  int get completedCount => todos.where((t) => t.done).length;

  @action
  void addTodo(String title) {
    todos.add(Todo(title: title));
  }
}
'''
        result = extractor.extract(code, "todo_store.dart")
        assert len(result["state_managers"]) >= 1


# ===== gRPC SERVICE EXTRACTION =====

class TestGRPCExtraction:
    """Tests for gRPC service extraction."""

    def test_grpc_service(self, extractor):
        code = '''
import 'package:grpc/grpc.dart';

class GreeterService extends GreeterServiceBase {
  @override
  Future<HelloReply> sayHello(ServiceCall call, HelloRequest request) async {
    return HelloReply()..message = 'Hello, ${request.name}!';
  }

  @override
  Future<HelloReply> sayHelloAgain(ServiceCall call, HelloRequest request) async {
    return HelloReply()..message = 'Hello again, ${request.name}!';
  }
}
'''
        result = extractor.extract(code, "greeter_service.dart")
        assert len(result["grpc_services"]) >= 1


# ===== FLUTTER NAVIGATION EXTRACTION =====

class TestFlutterNavigationExtraction:
    """Tests for Flutter route/navigation extraction."""

    def test_go_router(self, extractor):
        code = '''
import 'package:go_router/go_router.dart';

final router = GoRouter(
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const HomeScreen(),
      routes: [
        GoRoute(
          path: 'details/:id',
          builder: (context, state) => DetailScreen(id: state.pathParameters['id']!),
        ),
      ],
    ),
    GoRoute(
      path: '/settings',
      builder: (context, state) => const SettingsScreen(),
    ),
  ],
);
'''
        result = extractor.extract(code, "router.dart")
        assert len(result["flutter_routes"]) >= 1

    def test_auto_route(self, extractor):
        code = '''
import 'package:auto_route/auto_route.dart';

@MaterialRoute(page: HomePage)
class HomeRoute {}

@CupertinoRoute(page: SettingsPage)
class SettingsRoute {}
'''
        result = extractor.extract(code, "app_router.dart")
        assert len(result["flutter_routes"]) >= 1
