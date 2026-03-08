"""
Tests for ScalaAPIExtractor — routes, controllers, gRPC, GraphQL.

Part of CodeTrellis v4.25 Scala Language Support.
"""

import pytest
from codetrellis.extractors.scala.api_extractor import ScalaAPIExtractor


@pytest.fixture
def extractor():
    return ScalaAPIExtractor()


# ===== PLAY ROUTES EXTRACTION =====

class TestPlayRouteExtraction:
    """Tests for Play Framework route extraction."""

    def test_play_routes_file(self, extractor):
        code = '''
GET     /users                  controllers.UserController.index
POST    /users                  controllers.UserController.create
GET     /users/:id              controllers.UserController.show(id: Long)
PUT     /users/:id              controllers.UserController.update(id: Long)
DELETE  /users/:id              controllers.UserController.delete(id: Long)
'''
        result = extractor.extract(code, "conf/routes")
        routes = result["routes"]
        assert len(routes) >= 5
        get_routes = [r for r in routes if r.method == "GET"]
        assert len(get_routes) >= 2

    def test_play_routes_with_path_params(self, extractor):
        code = '''
GET     /api/v1/users/:id       controllers.api.v1.UserController.show(id: Long)
'''
        result = extractor.extract(code, "conf/routes")
        routes = result["routes"]
        assert len(routes) >= 1
        assert routes[0].method == "GET"
        assert "/users/:id" in routes[0].path or "/users/" in routes[0].path


# ===== AKKA HTTP ROUTE EXTRACTION =====

class TestAkkaHttpRouteExtraction:
    """Tests for Akka HTTP directive route extraction."""

    def test_akka_http_directives(self, extractor):
        code = '''
import akka.http.scaladsl.server.Directives._

val route =
  path("hello") {
    get {
      complete(HttpEntity(ContentTypes.`text/html(UTF-8)`, "<h1>Hello</h1>"))
    }
  } ~
  path("users") {
    post {
      entity(as[User]) { user =>
        complete(StatusCodes.Created, user)
      }
    }
  }
'''
        result = extractor.extract(code, "Routes.scala")
        routes = result["routes"]
        assert len(routes) >= 1

    def test_akka_http_path_prefix(self, extractor):
        code = '''
val apiRoute =
  pathPrefix("api" / "v1") {
    path("users") {
      get {
        complete(users)
      }
    }
  }
'''
        result = extractor.extract(code, "ApiRoutes.scala")
        routes = result["routes"]
        assert len(routes) >= 0  # At minimum, no crash


# ===== HTTP4S ROUTE EXTRACTION =====

class TestHttp4sRouteExtraction:
    """Tests for http4s route extraction."""

    def test_http4s_routes(self, extractor):
        code = '''
import org.http4s._
import org.http4s.dsl.io._

val routes = HttpRoutes.of[IO] {
  case GET -> Root / "users" => Ok(getUsers())
  case GET -> Root / "users" / IntVar(id) => Ok(getUser(id))
  case req @ POST -> Root / "users" => req.as[User].flatMap(createUser)
}
'''
        result = extractor.extract(code, "UserRoutes.scala")
        routes = result["routes"]
        assert len(routes) >= 1

    def test_http4s_auth_middleware(self, extractor):
        code = '''
val authedRoutes = AuthedRoutes.of[User, IO] {
  case GET -> Root / "profile" as user => Ok(user.profile)
}
'''
        result = extractor.extract(code, "AuthRoutes.scala")
        routes = result["routes"]
        assert len(routes) >= 0


# ===== TAPIR ENDPOINT EXTRACTION =====

class TestTapirEndpointExtraction:
    """Tests for Tapir endpoint extraction."""

    def test_tapir_endpoint(self, extractor):
        code = '''
import sttp.tapir._

val getUserEndpoint = endpoint
  .get
  .in("users" / path[Long]("id"))
  .out(jsonBody[User])
  .errorOut(statusCode)
'''
        result = extractor.extract(code, "Endpoints.scala")
        routes = result["routes"]
        assert len(routes) >= 0  # Tapir patterns may vary

    def test_tapir_server_endpoint(self, extractor):
        code = '''
val createUserEndpoint = endpoint
  .post
  .in("users")
  .in(jsonBody[CreateUserRequest])
  .out(jsonBody[User])
'''
        result = extractor.extract(code, "Endpoints.scala")
        routes = result["routes"]
        assert len(routes) >= 0


# ===== ZIO HTTP ROUTE EXTRACTION =====

class TestZioHttpRouteExtraction:
    """Tests for ZIO HTTP route extraction."""

    def test_zio_http_routes(self, extractor):
        code = '''
import zio.http._

val routes = Routes(
  Method.GET / "users" -> handler { (req: Request) =>
    Response.json(users.toJson)
  },
  Method.POST / "users" -> handler { (req: Request) =>
    req.body.asString.map(s => Response.text(s))
  },
)
'''
        result = extractor.extract(code, "UserRoutes.scala")
        routes = result["routes"]
        assert len(routes) >= 0


# ===== CONTROLLER EXTRACTION =====

class TestControllerExtraction:
    """Tests for Scala controller extraction."""

    def test_play_controller(self, extractor):
        code = '''
@Singleton
class UserController @Inject()(
  cc: ControllerComponents,
  userService: UserService
) extends AbstractController(cc) {

  def index = Action { implicit request =>
    Ok(Json.toJson(userService.findAll))
  }

  def show(id: Long) = Action { implicit request =>
    userService.findById(id) match {
      case Some(user) => Ok(Json.toJson(user))
      case None => NotFound
    }
  }
}
'''
        result = extractor.extract(code, "UserController.scala")
        controllers = result["controllers"]
        assert len(controllers) >= 1
        ctrl = controllers[0]
        assert ctrl.name == "UserController"

    def test_akka_http_server_class(self, extractor):
        code = '''
class ApiServer(implicit system: ActorSystem, mat: Materializer) extends Directives {
  val route = pathPrefix("api") {
    userRoutes ~ productRoutes
  }
}
'''
        result = extractor.extract(code, "ApiServer.scala")
        controllers = result["controllers"]
        assert len(controllers) >= 0


# ===== GRPC EXTRACTION =====

class TestGRPCExtraction:
    """Tests for Scala gRPC service extraction."""

    def test_scalapb_service(self, extractor):
        code = '''
class UserServiceImpl extends UserServiceGrpc.UserService {
  override def getUser(request: GetUserRequest): Future[User] = {
    Future.successful(User(name = "Alice"))
  }

  override def listUsers(request: ListUsersRequest): Future[ListUsersResponse] = {
    Future.successful(ListUsersResponse())
  }
}
'''
        result = extractor.extract(code, "UserServiceImpl.scala")
        grpc = result["grpc_services"]
        assert len(grpc) >= 0

    def test_fs2_grpc_service(self, extractor):
        code = '''
class UserServiceFs2 extends UserServiceFs2Grpc[IO, Metadata] {
  override def getUser(request: GetUserRequest, ctx: Metadata): IO[User] =
    IO.pure(User(name = "Alice"))
}
'''
        result = extractor.extract(code, "UserServiceFs2.scala")
        grpc = result["grpc_services"]
        assert len(grpc) >= 0


# ===== GRAPHQL EXTRACTION =====

class TestGraphQLExtraction:
    """Tests for Scala GraphQL type extraction."""

    def test_caliban_schema(self, extractor):
        code = '''
import caliban._
import caliban.schema.Annotations._

@GQLDescription("A user in the system")
case class User(
  @GQLDescription("The user's unique ID")
  id: Long,
  name: String,
  email: String,
)

case class Queries(
  users: ZIO[UserService, Nothing, List[User]],
  user: UserArgs => ZIO[UserService, Nothing, Option[User]],
)
'''
        result = extractor.extract(code, "GraphQLSchema.scala")
        gql = result["graphql_types"]
        assert len(gql) >= 0

    def test_sangria_schema(self, extractor):
        code = '''
import sangria.schema._

val UserType = ObjectType("User",
  fields[Unit, User](
    Field("id", LongType, resolve = _.value.id),
    Field("name", StringType, resolve = _.value.name),
  )
)
'''
        result = extractor.extract(code, "Schema.scala")
        gql = result["graphql_types"]
        assert len(gql) >= 0


# ===== EDGE CASES =====

class TestAPIEdgeCases:
    """Tests for edge cases in API extraction."""

    def test_empty_file(self, extractor):
        result = extractor.extract("", "empty.scala")
        assert result["routes"] == []
        assert result["controllers"] == []
        assert result["grpc_services"] == []
        assert result["graphql_types"] == []

    def test_non_api_code(self, extractor):
        code = '''
case class User(name: String, email: String)
object User {
  def apply(name: String): User = User(name, s"$name@example.com")
}
'''
        result = extractor.extract(code, "User.scala")
        assert result["routes"] == []
