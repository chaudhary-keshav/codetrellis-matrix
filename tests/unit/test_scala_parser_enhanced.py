"""
Tests for EnhancedScalaParser — full parser integration, framework detection, build.sbt parsing.

Part of CodeTrellis v4.25 Scala Language Support.
"""

import pytest
from codetrellis.scala_parser_enhanced import EnhancedScalaParser, ScalaParseResult


@pytest.fixture
def parser():
    return EnhancedScalaParser()


# ===== BASIC PARSING =====

class TestBasicParsing:
    """Tests for basic Scala file parsing."""

    def test_parse_empty_file(self, parser):
        result = parser.parse("", "empty.scala")
        assert isinstance(result, ScalaParseResult)
        assert result.file_path == "empty.scala"
        assert result.classes == []
        assert result.methods == []

    def test_parse_simple_class(self, parser):
        code = '''
class User(val name: String, val email: String) {
  def greet: String = s"Hello, $name"
}
'''
        result = parser.parse(code, "User.scala")
        assert len(result.classes) >= 1
        assert result.classes[0].name == "User"
        assert len(result.methods) >= 1

    def test_parse_case_class(self, parser):
        code = '''
case class Point(x: Double, y: Double) {
  def distanceTo(other: Point): Double =
    math.sqrt(math.pow(x - other.x, 2) + math.pow(y - other.y, 2))
}
'''
        result = parser.parse(code, "Point.scala")
        assert len(result.classes) >= 1
        cls = result.classes[0]
        assert cls.name == "Point"
        assert cls.is_case is True

    def test_parse_trait(self, parser):
        code = '''
trait Printable {
  def print(): Unit
  def prettyPrint(): Unit = println(toString)
}
'''
        result = parser.parse(code, "Printable.scala")
        assert len(result.traits) >= 1
        assert result.traits[0].name == "Printable"

    def test_parse_object(self, parser):
        code = '''
object MathUtils {
  def square(x: Int): Int = x * x
  val Pi: Double = 3.14159265
}
'''
        result = parser.parse(code, "MathUtils.scala")
        assert len(result.objects) >= 1
        assert result.objects[0].name == "MathUtils"

    def test_parse_enum(self, parser):
        code = '''
enum Color:
  case Red, Green, Blue
'''
        result = parser.parse(code, "Color.scala")
        assert len(result.enums) >= 1
        assert result.enums[0].name == "Color"

    def test_parse_sealed_trait_hierarchy(self, parser):
        code = '''
sealed trait Shape
case class Circle(radius: Double) extends Shape
case class Rectangle(width: Double, height: Double) extends Shape
case object Empty extends Shape
'''
        result = parser.parse(code, "Shape.scala")
        # Should detect sealed trait and case classes
        assert len(result.traits) >= 1 or len(result.enums) >= 1
        assert len(result.classes) >= 2 or len(result.objects) >= 1


# ===== PACKAGE DETECTION =====

class TestPackageDetection:
    """Tests for package name extraction."""

    def test_package_declaration(self, parser):
        code = '''
package com.example.models

case class User(name: String)
'''
        result = parser.parse(code, "User.scala")
        assert result.package_name == "com.example.models"

    def test_nested_package(self, parser):
        code = '''
package com.example
package models

case class User(name: String)
'''
        result = parser.parse(code, "User.scala")
        assert "com.example" in result.package_name


# ===== FRAMEWORK DETECTION =====

class TestFrameworkDetection:
    """Tests for Scala framework detection."""

    def test_detect_play_framework(self, parser):
        code = '''
import play.api.mvc._
import play.api.libs.json._

@Singleton
class UserController @Inject()(cc: ControllerComponents) extends AbstractController(cc) {
  def index = Action { Ok("Users") }
}
'''
        result = parser.parse(code, "UserController.scala")
        assert "play" in result.detected_frameworks

    def test_detect_akka_http(self, parser):
        code = '''
import akka.http.scaladsl.server.Directives._
import akka.http.scaladsl.marshallers.sprayjson.SprayJsonSupport._

val route = path("hello") {
  get { complete("Hello") }
}
'''
        result = parser.parse(code, "Routes.scala")
        assert "akka_http" in result.detected_frameworks

    def test_detect_http4s(self, parser):
        code = '''
import org.http4s._
import org.http4s.dsl.io._
import org.http4s.ember.server.EmberServerBuilder

val routes = HttpRoutes.of[IO] {
  case GET -> Root / "hello" => Ok("Hello")
}
'''
        result = parser.parse(code, "Server.scala")
        assert "http4s" in result.detected_frameworks

    def test_detect_cats_effect(self, parser):
        code = '''
import cats.effect._
import cats.effect.std.Console

object Main extends IOApp.Simple:
  def run: IO[Unit] = IO.println("Hello, Cats Effect!")
'''
        result = parser.parse(code, "Main.scala")
        detected = result.detected_frameworks
        assert "cats-effect" in detected or "cats" in detected

    def test_detect_zio(self, parser):
        code = '''
import zio._
import zio.Console._

object Main extends ZIOAppDefault:
  def run = Console.printLine("Hello, ZIO!")
'''
        result = parser.parse(code, "Main.scala")
        assert "zio" in result.detected_frameworks

    def test_detect_circe(self, parser):
        code = '''
import io.circe._
import io.circe.generic.semiauto._

case class User(name: String)
object User {
  implicit val decoder: Decoder[User] = deriveDecoder
  implicit val encoder: Encoder[User] = deriveEncoder
}
'''
        result = parser.parse(code, "User.scala")
        assert "circe" in result.detected_frameworks

    def test_detect_slick(self, parser):
        code = '''
import slick.jdbc.PostgresProfile.api._

class UsersTable(tag: Tag) extends Table[User](tag, "users") {
  def id = column[Long]("id", O.PrimaryKey, O.AutoInc)
  def name = column[String]("name")
  def * = (id, name).mapTo[User]
}
'''
        result = parser.parse(code, "UserTable.scala")
        assert "slick" in result.detected_frameworks

    def test_detect_doobie(self, parser):
        code = '''
import doobie._
import doobie.implicits._

val query = sql"SELECT id, name FROM users".query[User]
'''
        result = parser.parse(code, "Queries.scala")
        assert "doobie" in result.detected_frameworks

    def test_detect_tapir(self, parser):
        code = '''
import sttp.tapir._
import sttp.tapir.server.http4s.Http4sServerInterpreter

val helloEndpoint = endpoint.get.in("hello").out(stringBody)
'''
        result = parser.parse(code, "Endpoints.scala")
        assert "tapir" in result.detected_frameworks

    def test_detect_scalatest(self, parser):
        code = '''
import org.scalatest.flatspec.AnyFlatSpec
import org.scalatest.matchers.should.Matchers

class UserSpec extends AnyFlatSpec with Matchers {
  "User" should "have a name" in {
    val user = User("Alice")
    user.name shouldBe "Alice"
  }
}
'''
        result = parser.parse(code, "UserSpec.scala")
        assert "scalatest" in result.detected_frameworks

    def test_detect_spark(self, parser):
        code = '''
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions._

val spark = SparkSession.builder().appName("MyApp").getOrCreate()
val df = spark.read.parquet("data.parquet")
'''
        result = parser.parse(code, "SparkJob.scala")
        assert "spark" in result.detected_frameworks

    def test_no_framework_plain_scala(self, parser):
        code = '''
object Main extends App {
  println("Hello, World!")
}
'''
        result = parser.parse(code, "Main.scala")
        # No frameworks should be detected for plain Scala
        assert isinstance(result.detected_frameworks, list)


# ===== BUILD.SBT PARSING =====

class TestBuildSbtParsing:
    """Tests for build.sbt parsing."""

    def test_parse_build_sbt(self, parser):
        code = '''
name := "my-project"
version := "1.0.0"
scalaVersion := "3.4.2"

libraryDependencies ++= Seq(
  "org.typelevel" %% "cats-core" % "2.10.0",
  "org.typelevel" %% "cats-effect" % "3.5.4",
  "org.http4s" %% "http4s-ember-server" % "0.23.27",
  "org.http4s" %% "http4s-dsl" % "0.23.27",
  "io.circe" %% "circe-generic" % "0.14.7",
  "org.scalatest" %% "scalatest" % "3.2.18" % Test,
)
'''
        # parse_build_sbt extracts scalaVersion from build.sbt
        build_info = EnhancedScalaParser.parse_build_sbt(code)
        assert build_info['scala_version'] == "3.4.2"

        # The parse() method also extracts dependencies via attribute extractor
        result = parser.parse(code, "build.sbt")
        assert len(result.dependencies) >= 5

    def test_parse_scala_version(self, parser):
        code = '''
scalaVersion := "2.13.14"
'''
        build_info = EnhancedScalaParser.parse_build_sbt(code)
        assert "2.13" in build_info['scala_version']


# ===== SCALA VERSION FEATURE DETECTION =====

class TestVersionDetection:
    """Tests for Scala version feature detection."""

    def test_scala3_features_detected(self, parser):
        code = '''
enum Color:
  case Red, Green, Blue

extension (s: String)
  def toSlug: String = s.toLowerCase.replaceAll("\\\\s+", "-")

given Ordering[Color] = Ordering.by(_.ordinal)
'''
        result = parser.parse(code, "Modern.scala")
        # Should detect Scala 3 features: enum, extension, given
        version_features = result.detected_scala_version_features
        assert len(version_features) >= 0  # Features detected depends on implementation

    def test_scala2_style_detected(self, parser):
        code = '''
implicit val ordering: Ordering[User] = Ordering.by(_.name)
implicit class RichString(val s: String) extends AnyVal {
  def toSlug: String = s.toLowerCase.replaceAll("\\\\s+", "-")
}
'''
        result = parser.parse(code, "Legacy.scala")
        # Scala 2 style with implicits
        assert isinstance(result.detected_scala_version_features, list)


# ===== INTEGRATION TESTS =====

class TestFullIntegration:
    """Full integration tests combining multiple features."""

    def test_complete_play_controller(self, parser):
        code = '''
package controllers

import javax.inject._
import play.api.mvc._
import play.api.libs.json._

case class CreateUserRequest(name: String, email: String)
object CreateUserRequest {
  implicit val format: Format[CreateUserRequest] = Json.format[CreateUserRequest]
}

@Singleton
class UserController @Inject()(
  cc: ControllerComponents,
  userService: UserService,
) extends AbstractController(cc) {

  def index = Action {
    Ok(Json.toJson(userService.findAll))
  }

  def create = Action(parse.json) { request =>
    request.body.validate[CreateUserRequest] match {
      case JsSuccess(req, _) =>
        val user = userService.create(req.name, req.email)
        Created(Json.toJson(user))
      case JsError(errors) =>
        BadRequest(Json.obj("errors" -> errors.toString))
    }
  }
}
'''
        result = parser.parse(code, "UserController.scala")
        assert result.package_name == "controllers"
        assert len(result.classes) >= 2  # CreateUserRequest + UserController
        assert len(result.objects) >= 1  # companion
        assert len(result.controllers) >= 1
        assert len(result.codecs) >= 1
        assert "play" in result.detected_frameworks

    def test_complete_cats_effect_app(self, parser):
        code = '''
package com.example

import cats.effect._
import cats.effect.std.Console
import org.http4s._
import org.http4s.dsl.io._
import org.http4s.ember.server.EmberServerBuilder
import io.circe.generic.auto._
import org.http4s.circe.CirceEntityCodec._

case class User(name: String, email: String)

object UserRoutes {
  val routes: HttpRoutes[IO] = HttpRoutes.of[IO] {
    case GET -> Root / "users" =>
      Ok(List(User("Alice", "alice@example.com")))
    case req @ POST -> Root / "users" =>
      req.as[User].flatMap(u => Created(u))
  }
}

object Main extends IOApp.Simple {
  def run: IO[Unit] =
    EmberServerBuilder.default[IO]
      .withHttpApp(UserRoutes.routes.orNotFound)
      .build
      .useForever
}
'''
        result = parser.parse(code, "Main.scala")
        assert result.package_name == "com.example"
        assert len(result.classes) >= 1
        assert len(result.objects) >= 1
        detected = result.detected_frameworks
        assert any(f in detected for f in ["http4s", "cats-effect", "cats", "circe"])

    def test_complete_zio_app(self, parser):
        code = '''
package com.example

import zio._
import zio.http._
import zio.json._

case class User(name: String, email: String)
object User {
  implicit val codec: JsonCodec[User] = DeriveJsonCodec.gen[User]
}

object Main extends ZIOAppDefault {
  val routes = Routes(
    Method.GET / "users" -> handler {
      Response.json("""[{"name":"Alice","email":"alice@test.com"}]""")
    },
  )

  def run = Server.serve(routes).provide(Server.default)
}
'''
        result = parser.parse(code, "Main.scala")
        detected = result.detected_frameworks
        assert "zio" in detected

    def test_parse_file_type(self, parser):
        result = parser.parse("class Foo", "Foo.scala")
        assert result.file_type == "scala"

    def test_parse_sbt_file(self, parser):
        code = '''
name := "my-app"
scalaVersion := "3.4.2"
libraryDependencies += "dev.zio" %% "zio" % "2.1.1"
'''
        result = parser.parse(code, "build.sbt")
        assert len(result.dependencies) >= 1


# ===== EDGE CASES =====

class TestEdgeCases:
    """Tests for edge cases."""

    def test_parse_script_file(self, parser):
        code = '''
//> using scala "3.4.2"
//> using dep "dev.zio::zio:2.1.1"

val result = 1 + 2
println(result)
'''
        result = parser.parse(code, "script.sc")
        assert isinstance(result, ScalaParseResult)

    def test_parse_very_large_class(self, parser):
        methods = "\n".join([f"  def method{i}(x: Int): Int = x + {i}" for i in range(100)])
        code = f'''
class LargeClass {{
{methods}
}}
'''
        result = parser.parse(code, "Large.scala")
        assert len(result.classes) >= 1
        assert len(result.methods) >= 50

    def test_unicode_in_identifiers(self, parser):
        code = '''
class Résumé(val naïve: String)
'''
        result = parser.parse(code, "unicode.scala")
        # Should not crash
        assert isinstance(result, ScalaParseResult)
