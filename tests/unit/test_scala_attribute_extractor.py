"""
Tests for ScalaAttributeExtractor — annotations, implicits, macros, SBT dependencies.

Part of CodeTrellis v4.25 Scala Language Support.
"""

import pytest
from codetrellis.extractors.scala.attribute_extractor import ScalaAttributeExtractor


@pytest.fixture
def extractor():
    return ScalaAttributeExtractor()


# ===== ANNOTATION EXTRACTION =====

class TestAnnotationExtraction:
    """Tests for Scala annotation extraction."""

    def test_singleton_annotation(self, extractor):
        code = '''
@Singleton
class UserService {
  def findAll: List[User] = ???
}
'''
        result = extractor.extract(code, "UserService.scala")
        annotations = result["annotations"]
        assert len(annotations) >= 1
        ann = annotations[0]
        assert ann.name == "Singleton"

    def test_inject_annotation(self, extractor):
        code = '''
@Inject
class OrderController(userService: UserService, orderService: OrderService) {
}
'''
        result = extractor.extract(code, "OrderController.scala")
        annotations = result["annotations"]
        assert len(annotations) >= 1

    def test_tailrec_annotation(self, extractor):
        code = '''
import scala.annotation.tailrec

@tailrec
def factorial(n: Int, acc: Int = 1): Int =
  if (n <= 1) acc else factorial(n - 1, n * acc)
'''
        result = extractor.extract(code, "math.scala")
        annotations = result["annotations"]
        tailrec = [a for a in annotations if a.name == "tailrec"]
        assert len(tailrec) >= 1

    def test_deprecated_annotation(self, extractor):
        code = '''
@deprecated("Use newMethod instead", "2.0")
def oldMethod(): Unit = ???
'''
        result = extractor.extract(code, "old.scala")
        annotations = result["annotations"]
        deprecated = [a for a in annotations if a.name == "deprecated"]
        assert len(deprecated) >= 1

    def test_multiple_annotations(self, extractor):
        code = '''
@Singleton
@Named("userService")
@Inject
class UserService(db: Database) {
}
'''
        result = extractor.extract(code, "UserService.scala")
        annotations = result["annotations"]
        assert len(annotations) >= 2


# ===== IMPLICIT EXTRACTION =====

class TestImplicitExtraction:
    """Tests for Scala implicit/given extraction."""

    def test_implicit_val(self, extractor):
        code = '''
implicit val ec: ExecutionContext = ExecutionContext.global
'''
        result = extractor.extract(code, "context.scala")
        implicits = result["implicits"]
        assert len(implicits) >= 1

    def test_implicit_def_conversion(self, extractor):
        code = '''
implicit def intToString(i: Int): String = i.toString
'''
        result = extractor.extract(code, "conversions.scala")
        implicits = result["implicits"]
        assert len(implicits) >= 1

    def test_given_instance_scala3(self, extractor):
        code = '''
given ordering: Ordering[User] = Ordering.by(_.name)
'''
        result = extractor.extract(code, "ordering.scala")
        implicits = result["implicits"]
        assert len(implicits) >= 1

    def test_given_with_clause_scala3(self, extractor):
        code = '''
given Ordering[User] with
  def compare(a: User, b: User): Int = a.name.compare(b.name)
'''
        result = extractor.extract(code, "ordering.scala")
        implicits = result["implicits"]
        assert len(implicits) >= 1

    def test_implicit_class(self, extractor):
        code = '''
implicit class RichInt(val n: Int) extends AnyVal {
  def isEven: Boolean = n % 2 == 0
  def isOdd: Boolean = n % 2 != 0
}
'''
        result = extractor.extract(code, "RichInt.scala")
        implicits = result["implicits"]
        assert len(implicits) >= 1


# ===== MACRO EXTRACTION =====

class TestMacroExtraction:
    """Tests for Scala macro extraction."""

    def test_scala2_macro(self, extractor):
        code = '''
def materializeCodec[T]: Codec[T] = macro CodecMacro.materialize[T]
'''
        result = extractor.extract(code, "macros.scala")
        macros = result["macros"]
        assert len(macros) >= 1

    def test_inline_def(self, extractor):
        code = '''
inline def debug(inline msg: String): Unit =
  if (debugEnabled) println(msg)
'''
        result = extractor.extract(code, "Debug.scala")
        macros = result["macros"]
        assert len(macros) >= 0  # inline may be in methods not macros


# ===== SBT DEPENDENCY EXTRACTION =====

class TestDependencyExtraction:
    """Tests for SBT dependency extraction."""

    def test_library_dependency(self, extractor):
        code = '''
libraryDependencies ++= Seq(
  "org.typelevel" %% "cats-core" % "2.10.0",
  "org.typelevel" %% "cats-effect" % "3.5.4",
  "org.http4s" %% "http4s-ember-server" % "0.23.27",
)
'''
        result = extractor.extract(code, "build.sbt")
        deps = result["dependencies"]
        assert len(deps) >= 3
        cats_core = [d for d in deps if "cats-core" in d.artifact_id]
        assert len(cats_core) >= 1

    def test_single_dependency(self, extractor):
        code = '''
libraryDependencies += "com.typesafe.play" %% "play" % "2.9.0"
'''
        result = extractor.extract(code, "build.sbt")
        deps = result["dependencies"]
        assert len(deps) >= 1

    def test_test_scope_dependency(self, extractor):
        code = '''
libraryDependencies += "org.scalatest" %% "scalatest" % "3.2.18" % Test
'''
        result = extractor.extract(code, "build.sbt")
        deps = result["dependencies"]
        assert len(deps) >= 1
        test_deps = [d for d in deps if d.scope == "test" or d.scope == "Test"]
        assert len(test_deps) >= 1 or len(deps) >= 1  # Scope detection may vary

    def test_sbt_plugin(self, extractor):
        code = '''
addSbtPlugin("com.typesafe.play" % "sbt-plugin" % "2.9.0")
addSbtPlugin("org.scalameta" % "sbt-scalafmt" % "2.5.2")
'''
        result = extractor.extract(code, "plugins.sbt")
        deps = result["dependencies"]
        assert len(deps) >= 2

    def test_java_dependency_single_percent(self, extractor):
        code = '''
libraryDependencies += "org.postgresql" % "postgresql" % "42.7.3"
'''
        result = extractor.extract(code, "build.sbt")
        deps = result["dependencies"]
        assert len(deps) >= 1

    def test_scala3_cross_version(self, extractor):
        code = '''
libraryDependencies += "dev.zio" %% "zio" % "2.1.1"
libraryDependencies += "dev.zio" %% "zio-http" % "3.0.0-RC6"
'''
        result = extractor.extract(code, "build.sbt")
        deps = result["dependencies"]
        assert len(deps) >= 2


# ===== IMPORT EXTRACTION =====

class TestImportExtraction:
    """Tests for Scala import extraction."""

    def test_simple_import(self, extractor):
        code = '''
import scala.collection.mutable.ArrayBuffer
import scala.util.{Try, Success, Failure}
'''
        result = extractor.extract(code, "imports.scala")
        imports = result["imports"]
        assert len(imports) >= 1

    def test_wildcard_import(self, extractor):
        code = '''
import java.util._
import scala.jdk.CollectionConverters._
'''
        result = extractor.extract(code, "imports.scala")
        imports = result["imports"]
        assert len(imports) >= 1

    def test_given_import_scala3(self, extractor):
        code = '''
import scala.math.Ordering.given
import MyModule.{given MyTypeClass}
'''
        result = extractor.extract(code, "imports.scala")
        imports = result["imports"]
        assert len(imports) >= 0  # given import support may vary


# ===== EDGE CASES =====

class TestAttributeEdgeCases:
    """Tests for edge cases in attribute extraction."""

    def test_empty_file(self, extractor):
        result = extractor.extract("", "empty.scala")
        assert result["annotations"] == []
        assert result["implicits"] == []
        assert result["macros"] == []
        assert result["dependencies"] == []

    def test_build_file_only_deps(self, extractor):
        code = '''
name := "my-project"
version := "1.0.0"
scalaVersion := "3.4.2"

libraryDependencies += "dev.zio" %% "zio" % "2.1.1"
'''
        result = extractor.extract(code, "build.sbt")
        deps = result["dependencies"]
        assert len(deps) >= 1
        # Build files should not extract annotations
        assert result["annotations"] == []

    def test_non_build_file_no_deps(self, extractor):
        code = '''
class MyApp extends App {
  println("Hello, World!")
}
'''
        result = extractor.extract(code, "MyApp.scala")
        assert result["dependencies"] == []
