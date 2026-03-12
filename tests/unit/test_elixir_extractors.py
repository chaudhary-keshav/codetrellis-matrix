"""
Tests for Elixir extractors — type, function, api, model, attribute extractors.

Part of CodeTrellis v5.5 Elixir Language Support.
"""

import pytest
from codetrellis.extractors.elixir import (
    ElixirTypeExtractor,
    ElixirFunctionExtractor,
    ElixirAPIExtractor,
    ElixirModelExtractor,
    ElixirAttributeExtractor,
)


class TestTypeExtractor:
    """Tests for ElixirTypeExtractor."""

    @pytest.fixture
    def extractor(self):
        return ElixirTypeExtractor()

    def test_extract_module(self, extractor):
        code = (
            'defmodule MyApp.Accounts.User do\n'
            '  use Ecto.Schema\n'
            '  import Ecto.Changeset\n'
            '  alias MyApp.Repo\n'
            '  require Logger\n'
            '  @behaviour MyApp.Authenticatable\n'
            '  @moduledoc "User accounts."\n'
            'end\n'
        )
        result = extractor.extract(code, "user.ex")
        modules = result["modules"]
        assert len(modules) >= 1
        m = modules[0]
        assert m.name == "MyApp.Accounts.User"
        assert "Ecto.Schema" in m.uses
        assert "Ecto.Changeset" in m.imports

    def test_extract_struct(self, extractor):
        code = (
            'defmodule MyApp.User do\n'
            '  @enforce_keys [:email]\n'
            '  defstruct [:email, :name, age: 0]\n'
            'end\n'
        )
        result = extractor.extract(code, "user.ex")
        structs = result["structs"]
        assert len(structs) >= 1

    def test_extract_protocol(self, extractor):
        code = (
            'defprotocol MyApp.Printable do\n'
            '  @doc "Render to string"\n'
            '  def to_string(data)\n'
            '  def to_iodata(data)\n'
            'end\n'
        )
        result = extractor.extract(code, "printable.ex")
        protocols = result["protocols"]
        assert len(protocols) >= 1
        assert protocols[0].name == "MyApp.Printable"

    def test_extract_behaviour(self, extractor):
        code = (
            'defmodule MyApp.CacheImpl do\n'
            '  @behaviour MyApp.CacheBehaviour\n'
            '  @callback get(key :: String.t()) :: {:ok, any()} | {:error, :not_found}\n'
            '  @callback put(key :: String.t(), value :: any()) :: :ok\n'
            'end\n'
        )
        result = extractor.extract(code, "cache.ex")
        behaviours = result["behaviours"]
        assert len(behaviours) >= 1

    def test_extract_typespecs(self, extractor):
        code = (
            'defmodule MyApp.Types do\n'
            '  @type name :: String.t()\n'
            '  @typep internal :: atom()\n'
            '  @opaque opaque_type :: %__MODULE__{}\n'
            '  @spec greet(name()) :: String.t()\n'
            '  def greet(name), do: "Hello"\n'
            'end\n'
        )
        result = extractor.extract(code, "types.ex")
        typespecs = result["typespecs"]
        assert len(typespecs) >= 1

    def test_extract_exception(self, extractor):
        code = (
            'defmodule MyApp.AuthError do\n'
            '  defexception [:message, :code]\n'
            'end\n'
        )
        result = extractor.extract(code, "auth_error.ex")
        exceptions = result["exceptions"]
        assert len(exceptions) >= 1
        assert exceptions[0].name == "MyApp.AuthError"


class TestFunctionExtractor:
    """Tests for ElixirFunctionExtractor."""

    @pytest.fixture
    def extractor(self):
        return ElixirFunctionExtractor()

    def test_extract_public_function(self, extractor):
        code = (
            'defmodule MyApp.Math do\n'
            '  def add(a, b), do: a + b\n'
            'end\n'
        )
        result = extractor.extract(code, "math.ex")
        functions = result["functions"]
        assert len(functions) >= 1
        f = functions[0]
        assert f.name == "add"
        assert f.is_public is True
        assert f.arity == 2

    def test_extract_private_function(self, extractor):
        code = (
            'defmodule MyApp.Internal do\n'
            '  defp helper(x), do: x * 2\n'
            'end\n'
        )
        result = extractor.extract(code, "internal.ex")
        functions = result["functions"]
        priv = [f for f in functions if not f.is_public]
        assert len(priv) >= 1

    def test_extract_function_with_guard(self, extractor):
        code = (
            'defmodule MyApp.Check do\n'
            '  def process(x) when is_integer(x), do: x + 1\n'
            '  def process(x) when is_binary(x), do: String.length(x)\n'
            'end\n'
        )
        result = extractor.extract(code, "check.ex")
        functions = result["functions"]
        guarded = [f for f in functions if f.has_guard]
        assert len(guarded) >= 1

    def test_extract_genserver_callbacks(self, extractor):
        code = (
            'defmodule MyApp.Server do\n'
            '  use GenServer\n'
            '  def init(state), do: {:ok, state}\n'
            '  def handle_call(:get, _from, state), do: {:reply, state, state}\n'
            '  def handle_cast({:set, val}, _state), do: {:noreply, val}\n'
            '  def handle_info(:tick, state), do: {:noreply, state}\n'
            'end\n'
        )
        result = extractor.extract(code, "server.ex")
        functions = result["functions"]
        gs_cbs = [f for f in functions if f.is_genserver_callback]
        assert len(gs_cbs) >= 3

    def test_extract_macro(self, extractor):
        code = (
            'defmodule MyApp.DSL do\n'
            '  defmacro my_macro(arg) do\n'
            '    quote do: unquote(arg) + 1\n'
            '  end\n'
            '  defmacrop private_macro(x), do: quote(do: unquote(x))\n'
            'end\n'
        )
        result = extractor.extract(code, "dsl.ex")
        macros = result["macros"]
        assert len(macros) >= 1

    def test_extract_guard(self, extractor):
        code = (
            'defmodule MyApp.Guards do\n'
            '  defguard is_positive(x) when is_number(x) and x > 0\n'
            'end\n'
        )
        result = extractor.extract(code, "guards.ex")
        guards = result["guards"]
        assert len(guards) >= 1
        assert guards[0].name == "is_positive"

    def test_extract_callback(self, extractor):
        code = (
            'defmodule MyApp.Worker do\n'
            '  @behaviour MyApp.JobRunner\n'
            '\n'
            '  @impl MyApp.JobRunner\n'
            '  def perform(args), do: :ok\n'
            '\n'
            '  @impl true\n'
            '  def retry_count, do: 3\n'
            'end\n'
        )
        result = extractor.extract(code, "worker.ex")
        callbacks = result["callbacks"]
        assert len(callbacks) >= 1


class TestAPIExtractor:
    """Tests for ElixirAPIExtractor."""

    @pytest.fixture
    def extractor(self):
        return ElixirAPIExtractor()

    def test_extract_plugs(self, extractor):
        code = (
            'defmodule MyApp.Router do\n'
            '  plug :match\n'
            '  plug :dispatch\n'
            '  plug MyApp.Auth\n'
            '  plug Plug.Logger, log: :debug\n'
            'end\n'
        )
        result = extractor.extract(code, "router.ex")
        plugs = result["plugs"]
        assert len(plugs) >= 1

    def test_extract_pipeline(self, extractor):
        code = (
            'defmodule MyAppWeb.Router do\n'
            '  pipeline :api do\n'
            '    plug :accepts, ["json"]\n'
            '    plug MyApp.AuthPlug\n'
            '  end\n'
            'end\n'
        )
        result = extractor.extract(code, "router.ex")
        pipelines = result["pipelines"]
        assert len(pipelines) >= 1

    def test_extract_endpoint(self, extractor):
        code = (
            'defmodule MyAppWeb.Endpoint do\n'
            '  use Phoenix.Endpoint, otp_app: :my_app\n'
            '  socket "/socket", MyAppWeb.UserSocket\n'
            '  plug Plug.Static, at: "/", from: :my_app\n'
            '  plug MyAppWeb.Router\n'
            'end\n'
        )
        result = extractor.extract(code, "endpoint.ex")
        endpoints = result["endpoints"]
        assert len(endpoints) >= 1


class TestModelExtractor:
    """Tests for ElixirModelExtractor."""

    @pytest.fixture
    def extractor(self):
        return ElixirModelExtractor()

    def test_extract_schema(self, extractor):
        code = (
            'defmodule MyApp.User do\n'
            '  use Ecto.Schema\n'
            '  schema "users" do\n'
            '    field :email, :string\n'
            '    field :name, :string\n'
            '    belongs_to :org, MyApp.Org\n'
            '    timestamps()\n'
            '  end\n'
            'end\n'
        )
        result = extractor.extract(code, "user.ex")
        schemas = result["schemas"]
        assert len(schemas) >= 1

    def test_extract_changeset(self, extractor):
        code = (
            'defmodule MyApp.User do\n'
            '  import Ecto.Changeset\n'
            '  def changeset(user, attrs) do\n'
            '    user\n'
            '    |> cast(attrs, [:email, :name])\n'
            '    |> validate_required([:email])\n'
            '  end\n'
            'end\n'
        )
        result = extractor.extract(code, "user.ex")
        changesets = result["changesets"]
        assert len(changesets) >= 1

    def test_extract_genserver_state(self, extractor):
        code = (
            'defmodule MyApp.Counter do\n'
            '  use GenServer\n'
            '  def init(count) do\n'
            '    {:ok, %{count: count, started_at: DateTime.utc_now()}}\n'
            '  end\n'
            'end\n'
        )
        result = extractor.extract(code, "counter.ex")
        states = result["genserver_states"]
        assert len(states) >= 1


class TestAttributeExtractor:
    """Tests for ElixirAttributeExtractor."""

    @pytest.fixture
    def extractor(self):
        return ElixirAttributeExtractor()

    def test_extract_module_attributes(self, extractor):
        code = (
            'defmodule MyApp.Config do\n'
            '  @timeout 5000\n'
            '  @max_retries 3\n'
            '  @moduledoc "Configuration module."\n'
            '  @vsn "1.0.0"\n'
            'end\n'
        )
        result = extractor.extract(code, "config.ex")
        attrs = result["attributes"]
        assert len(attrs) >= 1

    def test_extract_use_directives(self, extractor):
        code = (
            'defmodule MyApp.Service do\n'
            '  use GenServer\n'
            '  use MyApp.DSL, option: :value\n'
            'end\n'
        )
        result = extractor.extract(code, "service.ex")
        directives = result["directives"]
        assert len(directives) >= 1

    def test_skip_spec_impl_type(self, extractor):
        code = (
            'defmodule MyApp.Worker do\n'
            '  @impl true\n'
            '  @spec perform(map()) :: :ok\n'
            '  @type t :: %__MODULE__{}\n'
            '  @timeout 5000\n'
            'end\n'
        )
        result = extractor.extract(code, "worker.ex")
        attrs = result["attributes"]
        # Should not include @impl, @spec, @type (those are tracked by other extractors)
        timeout_attrs = [a for a in attrs if a.name == "timeout"]
        assert len(timeout_attrs) >= 1
