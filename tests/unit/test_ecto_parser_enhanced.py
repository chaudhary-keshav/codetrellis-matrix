"""
Tests for EnhancedEctoParser — schemas, changesets, migrations, queries,
Repo calls, Multi transactions, custom types, version detection.

Part of CodeTrellis v5.5 Ecto Framework Support.
"""

import pytest
from codetrellis.ecto_parser_enhanced import (
    EnhancedEctoParser,
    EctoParseResult,
)


@pytest.fixture
def parser():
    return EnhancedEctoParser()


class TestSchemas:
    """Tests for Ecto schema extraction."""

    def test_parse_basic_schema(self, parser):
        code = '''
defmodule MyApp.User do
  use Ecto.Schema

  schema "users" do
    field :email, :string
    field :name, :string
    field :age, :integer
    timestamps()
  end
end
'''
        result = parser.parse(code, "lib/my_app/user.ex")
        assert len(result.schemas) >= 1
        s = result.schemas[0]
        assert s.table == "users"

    def test_parse_schema_with_associations(self, parser):
        code = '''
defmodule MyApp.Post do
  use Ecto.Schema

  schema "posts" do
    field :title, :string
    field :body, :text
    belongs_to :author, MyApp.User
    has_many :comments, MyApp.Comment
    has_one :metadata, MyApp.PostMetadata
    many_to_many :tags, MyApp.Tag, join_through: "posts_tags"
    timestamps()
  end
end
'''
        result = parser.parse(code, "lib/my_app/post.ex")
        assert len(result.schemas) >= 1

    def test_parse_embedded_schema(self, parser):
        code = '''
defmodule MyApp.Address do
  use Ecto.Schema

  embedded_schema do
    field :street, :string
    field :city, :string
    field :zip, :string
  end
end
'''
        result = parser.parse(code, "lib/my_app/address.ex")
        assert len(result.schemas) >= 1

    def test_parse_schema_with_embeds(self, parser):
        code = '''
defmodule MyApp.Order do
  use Ecto.Schema

  schema "orders" do
    field :total, :decimal
    embeds_one :shipping_address, MyApp.Address
    embeds_many :items, MyApp.OrderItem
    timestamps()
  end
end
'''
        result = parser.parse(code, "lib/my_app/order.ex")
        assert len(result.schemas) >= 1

    def test_parse_binary_id_schema(self, parser):
        code = '''
defmodule MyApp.Token do
  use Ecto.Schema

  @primary_key {:id, :binary_id, autogenerate: true}
  @foreign_key_type :binary_id

  schema "tokens" do
    field :value, :string
    timestamps()
  end
end
'''
        result = parser.parse(code, "lib/my_app/token.ex")
        assert len(result.schemas) >= 1


class TestChangesets:
    """Tests for Ecto changeset extraction."""

    def test_parse_basic_changeset(self, parser):
        code = '''
defmodule MyApp.User do
  use Ecto.Schema
  import Ecto.Changeset

  schema "users" do
    field :email, :string
    field :name, :string
  end

  def changeset(user, attrs) do
    user
    |> cast(attrs, [:email, :name])
    |> validate_required([:email])
    |> unique_constraint(:email)
  end
end
'''
        result = parser.parse(code, "lib/my_app/user.ex")
        assert len(result.changesets) >= 1

    def test_parse_multiple_changesets(self, parser):
        code = '''
defmodule MyApp.User do
  import Ecto.Changeset

  def registration_changeset(user, attrs) do
    user
    |> cast(attrs, [:email, :password])
    |> validate_required([:email, :password])
    |> validate_length(:password, min: 8)
    |> hash_password()
  end

  def profile_changeset(user, attrs) do
    user
    |> cast(attrs, [:name, :bio, :avatar])
    |> validate_length(:bio, max: 500)
  end
end
'''
        result = parser.parse(code, "lib/my_app/user.ex")
        assert len(result.changesets) >= 2


class TestMigrations:
    """Tests for Ecto migration extraction."""

    def test_parse_create_table(self, parser):
        code = '''
defmodule MyApp.Repo.Migrations.CreateUsers do
  use Ecto.Migration

  def change do
    create table(:users) do
      add :email, :string, null: false
      add :name, :string
      add :age, :integer
      timestamps()
    end

    create unique_index(:users, [:email])
  end
end
'''
        result = parser.parse(code, "priv/repo/migrations/20230101_create_users.exs")
        assert len(result.migrations) >= 1

    def test_parse_alter_table(self, parser):
        code = '''
defmodule MyApp.Repo.Migrations.AddRoleToUsers do
  use Ecto.Migration

  def change do
    alter table(:users) do
      add :role, :string, default: "user"
    end
  end
end
'''
        result = parser.parse(code, "priv/repo/migrations/20230201_add_role.exs")
        assert len(result.migrations) >= 1

    def test_parse_up_down_migration(self, parser):
        code = '''
defmodule MyApp.Repo.Migrations.AddIndex do
  use Ecto.Migration

  def up do
    create index(:posts, [:published_at])
  end

  def down do
    drop index(:posts, [:published_at])
  end
end
'''
        result = parser.parse(code, "priv/repo/migrations/20230301_add_index.exs")
        assert len(result.migrations) >= 1


class TestQueries:
    """Tests for Ecto query extraction."""

    def test_parse_from_query(self, parser):
        code = '''
defmodule MyApp.Accounts do
  import Ecto.Query

  def list_active_users do
    from(u in "users", where: u.active == true, order_by: u.name)
    |> Repo.all()
  end
end
'''
        result = parser.parse(code, "lib/my_app/accounts.ex")
        assert len(result.queries) >= 1

    def test_parse_repo_calls(self, parser):
        code = '''
defmodule MyApp.Accounts do
  alias MyApp.Repo

  def get_user!(id), do: Repo.get!(User, id)
  def list_users, do: Repo.all(User)
  def create_user(attrs), do: %User{} |> User.changeset(attrs) |> Repo.insert()
  def update_user(user, attrs), do: user |> User.changeset(attrs) |> Repo.update()
  def delete_user(user), do: Repo.delete(user)
end
'''
        result = parser.parse(code, "lib/my_app/accounts.ex")
        assert len(result.repo_calls) >= 4

    def test_parse_multi(self, parser):
        code = '''
defmodule MyApp.Accounts do
  alias Ecto.Multi

  def transfer(from, to, amount) do
    Multi.new()
    |> Multi.update(:debit, debit_changeset(from, amount))
    |> Multi.update(:credit, credit_changeset(to, amount))
    |> Multi.insert(:log, transfer_log(from, to, amount))
    |> Repo.transaction()
  end
end
'''
        result = parser.parse(code, "lib/my_app/accounts.ex")
        assert len(result.multis) >= 1


class TestCustomTypes:
    """Tests for Ecto custom type extraction."""

    def test_parse_custom_type(self, parser):
        code = '''
defmodule MyApp.Encrypted do
  @behaviour Ecto.Type

  def type, do: :binary

  def cast(value) when is_binary(value), do: {:ok, value}
  def cast(_), do: :error

  def dump(value), do: {:ok, encrypt(value)}
  def load(value), do: {:ok, decrypt(value)}
end
'''
        result = parser.parse(code, "lib/my_app/encrypted.ex")
        assert len(result.custom_types) >= 1


class TestVersionDetection:
    """Tests for Ecto version detection."""

    def test_detect_ecto_3(self, parser):
        code = '''
defmodule MyApp.User do
  use Ecto.Schema
  schema "users" do
    field :email, :string
  end
end
'''
        result = parser.parse(code, "lib/user.ex")
        # Should detect some version
        assert result.detected_frameworks or result.schemas


class TestEdgeCases:
    """Tests for edge cases."""

    def test_parse_empty_file(self, parser):
        result = parser.parse("", "empty.ex")
        assert isinstance(result, EctoParseResult)
        assert len(result.schemas) == 0

    def test_non_ecto_file(self, parser):
        code = '''
defmodule MyApp.Math do
  def add(a, b), do: a + b
end
'''
        result = parser.parse(code, "lib/math.ex")
        assert len(result.schemas) == 0
        assert len(result.migrations) == 0

    def test_complex_schema_with_everything(self, parser):
        code = '''
defmodule MyApp.Product do
  use Ecto.Schema
  import Ecto.Changeset
  import Ecto.Query

  @primary_key {:id, :binary_id, autogenerate: true}
  @derive {Phoenix.Param, key: :slug}

  schema "products" do
    field :name, :string
    field :slug, :string
    field :price, :decimal
    field :quantity, :integer, default: 0
    field :metadata, :map
    belongs_to :category, MyApp.Category
    has_many :reviews, MyApp.Review
    many_to_many :tags, MyApp.Tag, join_through: "products_tags"
    embeds_one :dimensions, MyApp.Dimensions
    timestamps()
  end

  def changeset(product, attrs) do
    product
    |> cast(attrs, [:name, :price, :quantity, :metadata])
    |> validate_required([:name, :price])
    |> validate_number(:price, greater_than: 0)
    |> validate_number(:quantity, greater_than_or_equal_to: 0)
    |> generate_slug()
    |> unique_constraint(:slug)
  end

  def by_category(query, category_id) do
    from p in query, where: p.category_id == ^category_id
  end
end
'''
        result = parser.parse(code, "lib/my_app/product.ex")
        assert len(result.schemas) >= 1
        assert len(result.changesets) >= 1
        assert len(result.queries) >= 1
