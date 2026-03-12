"""
Tests for EnhancedElixirParser — full parser integration, framework detection,
OTP pattern detection, version detection.

Part of CodeTrellis v5.5 Elixir Language Support.
"""

import pytest
from codetrellis.elixir_parser_enhanced import (
    EnhancedElixirParser,
    ElixirParseResult,
)


@pytest.fixture
def parser():
    return EnhancedElixirParser()


class TestParserIntegration:
    """Tests for full parser integration."""

    def test_parse_empty_file(self, parser):
        result = parser.parse("", "empty.ex")
        assert isinstance(result, ElixirParseResult)
        assert result.file_path == "empty.ex"
        assert len(result.modules) == 0
        assert len(result.functions) == 0

    def test_parse_simple_module(self, parser):
        code = '''
defmodule MyApp.Hello do
  @moduledoc "A hello module."

  def greet(name) do
    "Hello, #{name}!"
  end

  defp internal_helper, do: :ok
end
'''
        result = parser.parse(code, "lib/my_app/hello.ex")
        assert len(result.modules) == 1
        assert result.modules[0].name == "MyApp.Hello"
        assert len(result.functions) == 2

    def test_parse_struct(self, parser):
        code = '''
defmodule MyApp.User do
  @enforce_keys [:email]
  defstruct [:email, :name, :age]
end
'''
        result = parser.parse(code, "lib/my_app/user.ex")
        assert len(result.structs) >= 1

    def test_parse_protocol(self, parser):
        code = '''
defprotocol MyApp.Printable do
  @doc "Converts to string"
  def to_string(data)
end

defimpl MyApp.Printable, for: Atom do
  def to_string(atom), do: Atom.to_string(atom)
end
'''
        result = parser.parse(code, "lib/my_app/printable.ex")
        assert len(result.protocols) >= 1

    def test_parse_behaviour(self, parser):
        code = '''
defmodule MyApp.Worker do
  @behaviour MyApp.JobRunner

  @impl MyApp.JobRunner
  def perform(args), do: :ok

  @impl true
  def retry_count, do: 3
end
'''
        result = parser.parse(code, "lib/my_app/worker.ex")
        assert len(result.callbacks) >= 1

    def test_parse_typespecs(self, parser):
        code = '''
defmodule MyApp.Math do
  @type result :: {:ok, number()} | {:error, String.t()}
  @typep internal :: atom()
  @opaque secret :: binary()

  @spec add(number(), number()) :: number()
  def add(a, b), do: a + b
end
'''
        result = parser.parse(code, "lib/my_app/math.ex")
        assert len(result.typespecs) >= 1
        assert len(result.functions) >= 1

    def test_parse_exception(self, parser):
        code = '''
defmodule MyApp.NotFoundError do
  defexception [:message, :resource]
end
'''
        result = parser.parse(code, "lib/my_app/not_found_error.ex")
        assert len(result.exceptions) >= 1

    def test_parse_macros(self, parser):
        code = '''
defmodule MyApp.DSL do
  defmacro define_route(path, handler) do
    quote do
      @routes {unquote(path), unquote(handler)}
    end
  end

  defmacrop internal_macro(x), do: quote(do: unquote(x) + 1)
end
'''
        result = parser.parse(code, "lib/my_app/dsl.ex")
        assert len(result.macros) >= 1

    def test_parse_guards(self, parser):
        code = '''
defmodule MyApp.Guards do
  defguard is_positive(x) when is_number(x) and x > 0
  defguardp is_valid_name(name) when is_binary(name) and byte_size(name) > 0
end
'''
        result = parser.parse(code, "lib/my_app/guards.ex")
        assert len(result.guards) >= 1

    def test_parse_genserver(self, parser):
        code = '''
defmodule MyApp.Counter do
  use GenServer

  def init(initial_count) do
    {:ok, initial_count}
  end

  def handle_call(:get, _from, count) do
    {:reply, count, count}
  end

  def handle_cast(:increment, count) do
    {:noreply, count + 1}
  end

  def handle_info(:tick, count) do
    {:noreply, count + 1}
  end
end
'''
        result = parser.parse(code, "lib/my_app/counter.ex")
        assert "genserver" in result.otp_patterns
        gs_fns = [f for f in result.functions if f.is_genserver_callback]
        assert len(gs_fns) >= 3

    def test_parse_supervisor(self, parser):
        code = '''
defmodule MyApp.Supervisor do
  use Supervisor

  def init(_opts) do
    children = [
      {MyApp.Counter, 0},
      MyApp.Worker
    ]
    Supervisor.init(children, strategy: :one_for_one)
  end
end
'''
        result = parser.parse(code, "lib/my_app/supervisor.ex")
        assert "supervisor" in result.otp_patterns

    def test_parse_use_import_alias_require(self, parser):
        code = '''
defmodule MyApp.Service do
  use GenServer
  import Ecto.Query
  alias MyApp.{Repo, User}
  require Logger
end
'''
        result = parser.parse(code, "lib/my_app/service.ex")
        assert len(result.modules) == 1
        mod = result.modules[0]
        assert "GenServer" in mod.uses
        assert "Ecto.Query" in mod.imports

    def test_parse_module_attributes(self, parser):
        code = '''
defmodule MyApp.Config do
  @timeout 5000
  @max_retries 3
  @moduledoc "Config module."

  def timeout, do: @timeout
end
'''
        result = parser.parse(code, "lib/my_app/config.ex")
        assert len(result.attributes) >= 1

    def test_parse_plug_pipeline(self, parser):
        code = '''
defmodule MyApp.Router do
  use Plug.Router
  plug :match
  plug :dispatch

  get "/hello" do
    send_resp(conn, 200, "world")
  end
end
'''
        result = parser.parse(code, "lib/my_app/router.ex")
        assert len(result.plugs) >= 1

    def test_parse_schema_changeset(self, parser):
        code = '''
defmodule MyApp.User do
  use Ecto.Schema
  import Ecto.Changeset

  schema "users" do
    field :email, :string
    field :name, :string
    timestamps()
  end

  def changeset(user, attrs) do
    user
    |> cast(attrs, [:email, :name])
    |> validate_required([:email])
  end
end
'''
        result = parser.parse(code, "lib/my_app/user.ex")
        assert len(result.schemas) >= 1
        assert len(result.changesets) >= 1

    def test_parse_elixir_script(self, parser):
        code = '''
defmodule MyApp.Seeds do
  alias MyApp.Repo
  alias MyApp.User

  Repo.insert!(%User{email: "admin@example.com", name: "Admin"})
end
'''
        result = parser.parse(code, "priv/repo/seeds.exs")
        assert isinstance(result, ElixirParseResult)


class TestFrameworkDetection:
    """Tests for framework/library detection."""

    def test_detect_phoenix(self, parser):
        code = '''
defmodule MyAppWeb do
  use Phoenix.Router
end
'''
        result = parser.parse(code, "lib/my_app_web.ex")
        assert "phoenix" in result.detected_frameworks

    def test_detect_ecto(self, parser):
        code = '''
defmodule MyApp.User do
  use Ecto.Schema
end
'''
        result = parser.parse(code, "lib/my_app/user.ex")
        assert "ecto" in result.detected_frameworks

    def test_detect_oban(self, parser):
        code = '''
defmodule MyApp.EmailWorker do
  use Oban.Worker, queue: :mailers
  @impl Oban.Worker
  def perform(%Oban.Job{args: args}) do
    :ok
  end
end
'''
        result = parser.parse(code, "lib/my_app/email_worker.ex")
        assert "oban" in result.detected_frameworks

    def test_detect_absinthe(self, parser):
        code = '''
defmodule MyApp.Schema do
  use Absinthe.Schema
  query do
    field :hello, :string
  end
end
'''
        result = parser.parse(code, "lib/my_app/schema.ex")
        assert "absinthe" in result.detected_frameworks

    def test_detect_tesla_http(self, parser):
        code = '''
defmodule MyApp.Client do
  use Tesla
  plug Tesla.Middleware.JSON
end
'''
        result = parser.parse(code, "lib/my_app/client.ex")
        assert "tesla" in result.detected_frameworks

    def test_detect_broadway(self, parser):
        code = '''
defmodule MyApp.Pipeline do
  use Broadway
  def handle_message(_, message, _) do
    message
  end
end
'''
        result = parser.parse(code, "lib/my_app/pipeline.ex")
        assert "broadway" in result.detected_frameworks

    def test_detect_multiple_frameworks(self, parser):
        code = '''
defmodule MyApp.Context do
  use Ecto.Schema
  import Ecto.Query
  require Logger
  alias MyApp.Repo
end
'''
        result = parser.parse(code, "lib/my_app/context.ex")
        assert "ecto" in result.detected_frameworks


class TestOTPPatternDetection:
    """Tests for OTP pattern detection."""

    def test_detect_genserver(self, parser):
        code = "defmodule MyApp.Server do\n  use GenServer\nend"
        result = parser.parse(code, "lib/server.ex")
        assert "genserver" in result.otp_patterns

    def test_detect_supervisor(self, parser):
        code = "defmodule MyApp.Sup do\n  use Supervisor\nend"
        result = parser.parse(code, "lib/sup.ex")
        assert "supervisor" in result.otp_patterns

    def test_detect_application(self, parser):
        code = "defmodule MyApp.Application do\n  use Application\nend"
        result = parser.parse(code, "lib/application.ex")
        assert "application" in result.otp_patterns

    def test_detect_agent(self, parser):
        code = "defmodule MyApp.Store do\n  use Agent\nend"
        result = parser.parse(code, "lib/store.ex")
        assert "agent" in result.otp_patterns

    def test_detect_task(self, parser):
        code = "defmodule MyApp.AsyncWorker do\n  def run do\n    Task.async(fn -> :work end)\n    Task.await(task)\n  end\nend"
        result = parser.parse(code, "lib/async.ex")
        assert "task" in result.otp_patterns


class TestVersionDetection:
    """Tests for Elixir version feature detection."""

    def test_detect_with_clause(self, parser):
        code = '''
defmodule MyApp.Auth do
  def authenticate(user, pass) do
    with {:ok, user} <- find_user(user),
         {:ok, _} <- check_password(user, pass) do
      {:ok, user}
    end
  end
end
'''
        result = parser.parse(code, "lib/auth.ex")
        # with was introduced in Elixir 1.2
        assert result.elixir_version is not None


class TestEdgeCases:
    """Tests for edge cases and robustness."""

    def test_parse_empty_module(self, parser):
        code = "defmodule MyApp.Empty do\nend"
        result = parser.parse(code, "lib/empty.ex")
        assert len(result.modules) == 1

    def test_parse_nested_modules(self, parser):
        code = '''
defmodule MyApp.Outer do
  defmodule Inner do
    def hello, do: :world
  end
end
'''
        result = parser.parse(code, "lib/outer.ex")
        assert len(result.modules) >= 2

    def test_parse_multiclause_function(self, parser):
        code = '''
defmodule MyApp.Fib do
  def fib(0), do: 0
  def fib(1), do: 1
  def fib(n), do: fib(n - 1) + fib(n - 2)
end
'''
        result = parser.parse(code, "lib/fib.ex")
        fib_fns = [f for f in result.functions if f.name == "fib"]
        assert len(fib_fns) >= 1

    def test_parse_function_with_guard(self, parser):
        code = '''
defmodule MyApp.Math do
  def abs(x) when x >= 0, do: x
  def abs(x) when x < 0, do: -x
end
'''
        result = parser.parse(code, "lib/math.ex")
        guarded = [f for f in result.functions if f.has_guard]
        assert len(guarded) >= 1

    def test_parse_unicode_file(self, parser):
        code = '''
defmodule MyApp.Grüße do
  @moduledoc "Unicode module name"
  def grüßen, do: "Hallo Welt!"
end
'''
        result = parser.parse(code, "lib/grüße.ex")
        assert isinstance(result, ElixirParseResult)

    def test_parse_large_module(self, parser):
        """Test parsing a module with many functions."""
        functions = "\n".join(
            f"  def func_{i}(x), do: x + {i}" for i in range(50)
        )
        code = f"defmodule MyApp.Big do\n{functions}\nend"
        result = parser.parse(code, "lib/big.ex")
        assert len(result.functions) >= 50
