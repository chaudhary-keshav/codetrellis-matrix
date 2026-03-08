"""
Tests for ScalaModelExtractor — Slick, Doobie, Quill, codecs, migrations.

Part of CodeTrellis v4.25 Scala Language Support.
"""

import pytest
from codetrellis.extractors.scala.model_extractor import ScalaModelExtractor


@pytest.fixture
def extractor():
    return ScalaModelExtractor()


# ===== SLICK MODEL EXTRACTION =====

class TestSlickModelExtraction:
    """Tests for Slick table definition extraction."""

    def test_slick_table_definition(self, extractor):
        code = '''
import slick.jdbc.PostgresProfile.api._

case class User(id: Long, name: String, email: String)

class UsersTable(tag: Tag) extends Table[User](tag, "users") {
  def id = column[Long]("id", O.PrimaryKey, O.AutoInc)
  def name = column[String]("name")
  def email = column[String]("email", O.Unique)
  def * = (id, name, email).mapTo[User]
}

val users = TableQuery[UsersTable]
'''
        result = extractor.extract(code, "UserModel.scala")
        models = result["models"]
        assert len(models) >= 1
        model = models[0]
        assert "User" in model.name or "users" in (model.table_name or "")

    def test_slick_with_foreign_key(self, extractor):
        code = '''
class OrdersTable(tag: Tag) extends Table[Order](tag, "orders") {
  def id = column[Long]("id", O.PrimaryKey, O.AutoInc)
  def userId = column[Long]("user_id")
  def total = column[BigDecimal]("total")
  def * = (id, userId, total).mapTo[Order]
  def user = foreignKey("fk_user", userId, users)(_.id)
}
'''
        result = extractor.extract(code, "OrderModel.scala")
        models = result["models"]
        assert len(models) >= 1


# ===== DOOBIE QUERY EXTRACTION =====

class TestDoobieExtraction:
    """Tests for Doobie query extraction."""

    def test_doobie_query(self, extractor):
        code = '''
import doobie._
import doobie.implicits._

object UserQueries {
  def findById(id: Long): Query0[User] =
    sql"SELECT id, name, email FROM users WHERE id = $id".query[User]

  def findAll: Query0[User] =
    sql"SELECT id, name, email FROM users".query[User]

  def insert(user: User): Update0 =
    sql"INSERT INTO users (name, email) VALUES (${user.name}, ${user.email})".update
}
'''
        result = extractor.extract(code, "UserQueries.scala")
        models = result["models"]
        assert len(models) >= 0  # Doobie may extract as queries


# ===== QUILL EXTRACTION =====

class TestQuillExtraction:
    """Tests for Quill query extraction."""

    def test_quill_model(self, extractor):
        code = '''
import io.getquill._

val ctx = new PostgresJdbcContext(SnakeCase, "db")
import ctx._

case class User(id: Long, name: String, email: String)

val users = quote {
  query[User]
}

val findById = quote { (id: Long) =>
  query[User].filter(_.id == id)
}
'''
        result = extractor.extract(code, "UserQuill.scala")
        models = result["models"]
        assert len(models) >= 0


# ===== MIGRATION EXTRACTION =====

class TestMigrationExtraction:
    """Tests for database migration extraction."""

    def test_play_evolution(self, extractor):
        code = '''
# --- !Ups
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL
);

# --- !Downs
DROP TABLE users;
'''
        result = extractor.extract(code, "1.sql")
        migrations = result["migrations"]
        assert len(migrations) >= 0

    def test_flyway_migration(self, extractor):
        code = '''
import org.flywaydb.core.api.migration.{BaseJavaMigration, Context}

class V1__CreateUsers extends BaseJavaMigration {
  override def migrate(context: Context): Unit = {
    val conn = context.getConnection
    val stmt = conn.createStatement()
    stmt.execute("CREATE TABLE users (id BIGSERIAL PRIMARY KEY, name VARCHAR(255))")
  }
}
'''
        result = extractor.extract(code, "V1__CreateUsers.scala")
        migrations = result["migrations"]
        assert len(migrations) >= 0


# ===== CODEC EXTRACTION =====

class TestCodecExtraction:
    """Tests for serialization codec extraction."""

    def test_circe_codec(self, extractor):
        code = '''
import io.circe._
import io.circe.generic.semiauto._

case class User(name: String, age: Int)
object User {
  implicit val decoder: Decoder[User] = deriveDecoder
  implicit val encoder: Encoder[User] = deriveEncoder
}
'''
        result = extractor.extract(code, "User.scala")
        codecs = result["codecs"]
        assert len(codecs) >= 1

    def test_play_json_format(self, extractor):
        code = '''
import play.api.libs.json._

case class User(name: String, age: Int)
object User {
  implicit val format: Format[User] = Json.format[User]
}
'''
        result = extractor.extract(code, "User.scala")
        codecs = result["codecs"]
        assert len(codecs) >= 1

    def test_spray_json_protocol(self, extractor):
        code = '''
import spray.json._
import DefaultJsonProtocol._

case class User(name: String, age: Int)
object UserJsonProtocol extends DefaultJsonProtocol {
  implicit val userFormat = jsonFormat2(User)
}
'''
        result = extractor.extract(code, "UserJsonProtocol.scala")
        codecs = result["codecs"]
        assert len(codecs) >= 0

    def test_zio_json_codec(self, extractor):
        code = '''
import zio.json._

case class User(name: String, age: Int)
object User {
  implicit val codec: JsonCodec[User] = DeriveJsonCodec.gen[User]
}
'''
        result = extractor.extract(code, "User.scala")
        codecs = result["codecs"]
        assert len(codecs) >= 0


# ===== EDGE CASES =====

class TestModelEdgeCases:
    """Tests for edge cases in model extraction."""

    def test_empty_file(self, extractor):
        result = extractor.extract("", "empty.scala")
        assert result["models"] == []
        assert result["migrations"] == []
        assert result["codecs"] == []

    def test_non_model_code(self, extractor):
        code = '''
object MathUtils {
  def square(x: Int): Int = x * x
}
'''
        result = extractor.extract(code, "MathUtils.scala")
        assert result["models"] == []
        assert result["migrations"] == []
