"""
Tests for EnhancedAbsintheParser — types, queries, mutations, subscriptions,
resolvers, middleware, dataloaders, version detection.

Part of CodeTrellis v5.5 Absinthe Framework Support.
"""

import pytest
from codetrellis.absinthe_parser_enhanced import (
    EnhancedAbsintheParser,
    AbsintheParseResult,
)


@pytest.fixture
def parser():
    return EnhancedAbsintheParser()


class TestTypes:
    """Tests for Absinthe type extraction."""

    def test_parse_object_type(self, parser):
        code = '''
defmodule MyApp.Schema.Types do
  use Absinthe.Schema.Notation

  object :user do
    field :id, non_null(:id)
    field :email, non_null(:string)
    field :name, :string
    field :posts, list_of(:post)
  end
end
'''
        result = parser.parse(code, "lib/my_app/schema/types.ex")
        assert len(result.types) >= 1
        t = result.types[0]
        assert t.name == "user"

    def test_parse_input_object(self, parser):
        code = '''
defmodule MyApp.Schema.Types do
  use Absinthe.Schema.Notation

  input_object :create_user_input do
    field :email, non_null(:string)
    field :name, :string
    field :role, :role_enum
  end
end
'''
        result = parser.parse(code, "lib/schema/types.ex")
        inputs = [t for t in result.types if t.type_kind == "input_object"]
        assert len(inputs) >= 1

    def test_parse_enum_type(self, parser):
        code = '''
defmodule MyApp.Schema.Enums do
  use Absinthe.Schema.Notation

  enum :role do
    value :admin
    value :moderator
    value :user
  end
end
'''
        result = parser.parse(code, "lib/schema/enums.ex")
        enums = [t for t in result.types if t.type_kind == "enum"]
        assert len(enums) >= 1

    def test_parse_union_type(self, parser):
        code = '''
defmodule MyApp.Schema.Types do
  use Absinthe.Schema.Notation

  union :search_result do
    types [:user, :post, :comment]
    resolve_type fn
      %MyApp.User{}, _ -> :user
      %MyApp.Post{}, _ -> :post
      %MyApp.Comment{}, _ -> :comment
    end
  end
end
'''
        result = parser.parse(code, "lib/schema/types.ex")
        unions = [t for t in result.types if t.type_kind == "union"]
        assert len(unions) >= 1

    def test_parse_interface_type(self, parser):
        code = '''
defmodule MyApp.Schema.Types do
  use Absinthe.Schema.Notation

  interface :node do
    field :id, non_null(:id)
    resolve_type fn
      %MyApp.User{}, _ -> :user
      %MyApp.Post{}, _ -> :post
    end
  end
end
'''
        result = parser.parse(code, "lib/schema/types.ex")
        interfaces = [t for t in result.types if t.type_kind == "interface"]
        assert len(interfaces) >= 1

    def test_parse_scalar_type(self, parser):
        code = '''
defmodule MyApp.Schema.Scalars do
  use Absinthe.Schema.Notation

  scalar :datetime, name: "DateTime" do
    serialize &DateTime.to_iso8601/1
    parse &parse_datetime/1
  end
end
'''
        result = parser.parse(code, "lib/schema/scalars.ex")
        scalars = [t for t in result.types if t.type_kind == "scalar"]
        assert len(scalars) >= 1


class TestQueriesAndMutations:
    """Tests for Absinthe query/mutation extraction."""

    def test_parse_query(self, parser):
        code = '''
defmodule MyApp.Schema do
  use Absinthe.Schema

  query do
    field :user, :user do
      arg :id, non_null(:id)
      resolve &MyApp.Resolvers.Users.get_user/3
    end

    field :users, list_of(:user) do
      resolve &MyApp.Resolvers.Users.list_users/3
    end
  end
end
'''
        result = parser.parse(code, "lib/my_app/schema.ex")
        assert len(result.queries) >= 1

    def test_parse_mutation(self, parser):
        code = '''
defmodule MyApp.Schema do
  use Absinthe.Schema

  mutation do
    field :create_user, :user do
      arg :input, non_null(:create_user_input)
      resolve &MyApp.Resolvers.Users.create_user/3
    end

    field :delete_user, :user do
      arg :id, non_null(:id)
      resolve &MyApp.Resolvers.Users.delete_user/3
    end
  end
end
'''
        result = parser.parse(code, "lib/my_app/schema.ex")
        mutations = [q for q in result.queries if q.operation == "mutation"]
        assert len(mutations) >= 1

    def test_parse_subscription(self, parser):
        code = '''
defmodule MyApp.Schema do
  use Absinthe.Schema

  subscription do
    field :new_message, :message do
      config fn _args, _info ->
        {:ok, topic: "messages"}
      end
    end
  end
end
'''
        result = parser.parse(code, "lib/my_app/schema.ex")
        assert len(result.subscriptions) >= 1


class TestResolvers:
    """Tests for Absinthe resolver extraction."""

    def test_parse_resolver_module(self, parser):
        code = '''
defmodule MyApp.Resolvers.Users do
  alias MyApp.Accounts

  def list_users(_parent, _args, _resolution) do
    {:ok, Accounts.list_users()}
  end

  def get_user(_parent, %{id: id}, _resolution) do
    case Accounts.get_user(id) do
      nil -> {:error, "User not found"}
      user -> {:ok, user}
    end
  end

  def create_user(_parent, %{input: input}, _resolution) do
    Accounts.create_user(input)
  end
end
'''
        result = parser.parse(code, "lib/my_app/resolvers/users.ex")
        assert len(result.resolvers) >= 1


class TestMiddleware:
    """Tests for Absinthe middleware extraction."""

    def test_parse_middleware(self, parser):
        code = '''
defmodule MyApp.Middleware.Auth do
  @behaviour Absinthe.Middleware

  def call(resolution, _config) do
    case resolution.context do
      %{current_user: _} -> resolution
      _ -> Absinthe.Resolution.put_result(resolution, {:error, "Unauthorized"})
    end
  end
end
'''
        result = parser.parse(code, "lib/my_app/middleware/auth.ex")
        assert len(result.middleware) >= 1

    def test_parse_middleware_in_schema(self, parser):
        code = '''
defmodule MyApp.Schema do
  use Absinthe.Schema

  def middleware(middleware, _field, %{identifier: :mutation}) do
    [MyApp.Middleware.Auth | middleware] ++ [MyApp.Middleware.ErrorHandler]
  end
  def middleware(middleware, _field, _object), do: middleware
end
'''
        result = parser.parse(code, "lib/my_app/schema.ex")
        assert len(result.middleware) >= 1


class TestDataloaders:
    """Tests for Absinthe Dataloader extraction."""

    def test_parse_dataloader(self, parser):
        code = '''
defmodule MyApp.Schema do
  use Absinthe.Schema

  def context(ctx) do
    loader =
      Dataloader.new()
      |> Dataloader.add_source(MyApp.Accounts, MyApp.Accounts.data())
      |> Dataloader.add_source(MyApp.Blog, MyApp.Blog.data())
    Map.put(ctx, :loader, loader)
  end

  def plugins do
    [Absinthe.Middleware.Dataloader | Absinthe.Plugin.defaults()]
  end
end
'''
        result = parser.parse(code, "lib/my_app/schema.ex")
        assert len(result.dataloaders) >= 1


class TestVersionDetection:
    """Tests for Absinthe version detection."""

    def test_detect_absinthe(self, parser):
        code = '''
defmodule MyApp.Schema do
  use Absinthe.Schema
  query do
    field :hello, :string
  end
end
'''
        result = parser.parse(code, "lib/schema.ex")
        assert result.detected_frameworks or result.types or result.queries


class TestEdgeCases:
    """Tests for edge cases."""

    def test_parse_empty_file(self, parser):
        result = parser.parse("", "empty.ex")
        assert isinstance(result, AbsintheParseResult)
        assert len(result.types) == 0

    def test_non_absinthe_file(self, parser):
        code = '''
defmodule MyApp.Math do
  def add(a, b), do: a + b
end
'''
        result = parser.parse(code, "lib/math.ex")
        assert len(result.types) == 0
        assert len(result.queries) == 0

    def test_complex_schema(self, parser):
        code = '''
defmodule MyApp.Schema do
  use Absinthe.Schema

  import_types MyApp.Schema.Types
  import_types MyApp.Schema.Enums
  import_types Absinthe.Type.Custom

  query do
    field :users, list_of(:user) do
      arg :filter, :user_filter
      arg :limit, :integer
      middleware MyApp.Middleware.Auth
      resolve &MyApp.Resolvers.Users.list/3
    end
  end

  mutation do
    field :create_user, :user do
      arg :input, non_null(:create_user_input)
      resolve &MyApp.Resolvers.Users.create/3
    end
  end

  subscription do
    field :user_created, :user do
      config fn _, _ -> {:ok, topic: "users"} end
    end
  end
end
'''
        result = parser.parse(code, "lib/my_app/schema.ex")
        assert len(result.queries) >= 1
        assert len(result.subscriptions) >= 1
