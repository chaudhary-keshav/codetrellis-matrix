"""
Tests for EnhancedPhoenixParser — routes, controllers, LiveView, channels,
components, sockets, framework detection, version detection.

Part of CodeTrellis v5.5 Phoenix Framework Support.
"""

import pytest
from codetrellis.phoenix_parser_enhanced import (
    EnhancedPhoenixParser,
    PhoenixParseResult,
)


@pytest.fixture
def parser():
    return EnhancedPhoenixParser()


class TestRoutes:
    """Tests for Phoenix route extraction."""

    def test_parse_get_route(self, parser):
        code = '''
defmodule MyAppWeb.Router do
  use MyAppWeb, :router
  scope "/", MyAppWeb do
    get "/", PageController, :index
  end
end
'''
        result = parser.parse(code, "lib/my_app_web/router.ex")
        assert len(result.routes) >= 1
        r = result.routes[0]
        assert r.method == "GET"
        assert r.path == "/"

    def test_parse_post_route(self, parser):
        code = '''
defmodule MyAppWeb.Router do
  use MyAppWeb, :router
  scope "/api" do
    post "/users", UserController, :create
  end
end
'''
        result = parser.parse(code, "lib/my_app_web/router.ex")
        post_routes = [r for r in result.routes if r.method == "POST"]
        assert len(post_routes) >= 1

    def test_parse_live_route(self, parser):
        code = '''
defmodule MyAppWeb.Router do
  use MyAppWeb, :router
  scope "/" do
    live "/dashboard", DashboardLive
    live "/users/:id/edit", UserLive.Edit, :edit
  end
end
'''
        result = parser.parse(code, "lib/my_app_web/router.ex")
        live_routes = [r for r in result.routes if r.method == "live"]
        assert len(live_routes) >= 1

    def test_parse_resources(self, parser):
        code = '''
defmodule MyAppWeb.Router do
  use MyAppWeb, :router
  scope "/api" do
    resources "/posts", PostController
    resources "/comments", CommentController, only: [:index, :show]
  end
end
'''
        result = parser.parse(code, "lib/my_app_web/router.ex")
        res_routes = [r for r in result.routes if r.method == "resources"]
        assert len(res_routes) >= 1

    def test_parse_pipeline(self, parser):
        code = '''
defmodule MyAppWeb.Router do
  use MyAppWeb, :router
  pipeline :api do
    plug :accepts, ["json"]
    plug MyAppWeb.Auth
  end
  scope "/api", MyAppWeb do
    pipe_through :api
    get "/users", UserController, :index
  end
end
'''
        result = parser.parse(code, "lib/my_app_web/router.ex")
        assert len(result.routes) >= 1

    def test_parse_forward(self, parser):
        code = '''
defmodule MyAppWeb.Router do
  use MyAppWeb, :router
  forward "/health", MyAppWeb.HealthPlug
end
'''
        result = parser.parse(code, "lib/my_app_web/router.ex")
        fwd = [r for r in result.routes if r.method == "forward"]
        assert len(fwd) >= 1


class TestControllers:
    """Tests for Phoenix controller extraction."""

    def test_parse_controller(self, parser):
        code = '''
defmodule MyAppWeb.UserController do
  use MyAppWeb, :controller

  plug :authenticate when action in [:edit, :update]

  def index(conn, _params) do
    users = Accounts.list_users()
    render(conn, :index, users: users)
  end

  def show(conn, %{"id" => id}) do
    user = Accounts.get_user!(id)
    render(conn, :show, user: user)
  end

  def create(conn, %{"user" => user_params}) do
    case Accounts.create_user(user_params) do
      {:ok, user} -> redirect(conn, to: ~p"/users/#{user}")
      {:error, changeset} -> render(conn, :new, changeset: changeset)
    end
  end
end
'''
        result = parser.parse(code, "lib/my_app_web/controllers/user_controller.ex")
        assert len(result.controllers) >= 1
        ctrl = result.controllers[0]
        assert "UserController" in ctrl.name
        assert len(ctrl.actions) >= 3

    def test_controller_with_plugs(self, parser):
        code = '''
defmodule MyAppWeb.AdminController do
  use MyAppWeb, :controller
  use Phoenix.Controller
  plug :require_admin
  plug MyAppWeb.RateLimiter

  def dashboard(conn, _params) do
    render(conn, :dashboard)
  end
end
'''
        result = parser.parse(code, "lib/controller.ex")
        assert len(result.controllers) >= 1


class TestLiveView:
    """Tests for Phoenix LiveView extraction."""

    def test_parse_live_view(self, parser):
        code = '''
defmodule MyAppWeb.DashboardLive do
  use MyAppWeb, :live_view

  def mount(_params, _session, socket) do
    {:ok, assign(socket, count: 0, title: "Dashboard")}
  end

  def handle_event("increment", _, socket) do
    {:noreply, update(socket, :count, &(&1 + 1))}
  end

  def handle_event("decrement", _, socket) do
    {:noreply, update(socket, :count, &(&1 - 1))}
  end

  def handle_info({:tick, val}, socket) do
    {:noreply, assign(socket, count: val)}
  end

  def handle_params(%{"id" => id}, _uri, socket) do
    {:noreply, assign(socket, id: id)}
  end

  def render(assigns) do
    ~H\"\"\"
    <div><%= @count %></div>
    \"\"\"
  end
end
'''
        result = parser.parse(code, "lib/my_app_web/live/dashboard_live.ex")
        assert len(result.live_views) >= 1
        lv = result.live_views[0]
        assert "DashboardLive" in lv.name
        assert len(lv.handle_events) >= 2

    def test_parse_live_component(self, parser):
        code = '''
defmodule MyAppWeb.ModalComponent do
  use MyAppWeb, :live_component

  def update(assigns, socket) do
    {:ok, assign(socket, assigns)}
  end

  def handle_event("close", _, socket) do
    {:noreply, push_patch(socket, to: socket.assigns.return_to)}
  end

  def render(assigns) do
    ~H\"\"\"
    <div class="modal"><%= @inner_content %></div>
    \"\"\"
  end
end
'''
        result = parser.parse(code, "lib/my_app_web/live/modal_component.ex")
        assert len(result.live_components) >= 1


class TestChannels:
    """Tests for Phoenix Channel extraction."""

    def test_parse_channel(self, parser):
        code = '''
defmodule MyAppWeb.RoomChannel do
  use MyAppWeb, :channel

  def join("room:" <> room_id, _params, socket) do
    {:ok, assign(socket, :room_id, room_id)}
  end

  def handle_in("new_msg", %{"body" => body}, socket) do
    broadcast!(socket, "new_msg", %{body: body})
    {:noreply, socket}
  end

  def handle_in("ping", _payload, socket) do
    {:reply, :ok, socket}
  end

  def handle_out("new_msg", payload, socket) do
    push(socket, "new_msg", payload)
    {:noreply, socket}
  end
end
'''
        result = parser.parse(code, "lib/my_app_web/channels/room_channel.ex")
        assert len(result.channels) >= 1

    def test_parse_socket(self, parser):
        code = '''
defmodule MyAppWeb.UserSocket do
  use Phoenix.Socket

  channel "room:*", MyAppWeb.RoomChannel
  channel "notifications:*", MyAppWeb.NotificationChannel

  def connect(%{"token" => token}, socket, _connect_info) do
    case verify_token(token) do
      {:ok, user_id} -> {:ok, assign(socket, :user_id, user_id)}
      {:error, _} -> :error
    end
  end

  def id(socket), do: "users_socket:#{socket.assigns.user_id}"
end
'''
        result = parser.parse(code, "lib/my_app_web/channels/user_socket.ex")
        assert len(result.sockets) >= 1


class TestComponents:
    """Tests for Phoenix function component extraction."""

    def test_parse_function_component(self, parser):
        code = '''
defmodule MyAppWeb.CoreComponents do
  use Phoenix.Component

  attr :type, :string, default: "button"
  attr :class, :string, default: nil
  slot :inner_block, required: true

  def button(assigns) do
    ~H\"\"\"
    <button type={@type} class={@class}><%= render_slot(@inner_block) %></button>
    \"\"\"
  end

  attr :flash, :map, required: true
  attr :kind, :atom

  def flash_group(assigns) do
    ~H\"\"\"
    <div><%= render_slot(@inner_block) %></div>
    \"\"\"
  end
end
'''
        result = parser.parse(code, "lib/my_app_web/components/core_components.ex")
        assert len(result.components) >= 1


class TestVersionDetection:
    """Tests for Phoenix version detection."""

    def test_detect_phoenix_1_7_verified_routes(self, parser):
        code = '''
defmodule MyAppWeb.Router do
  use Phoenix.VerifiedRoutes
  def home_path, do: ~p"/home"
end
'''
        result = parser.parse(code, "lib/router.ex")
        # Phoenix 1.7+ uses verified routes
        assert result.phoenix_version is not None

    def test_detect_phoenix_live_view(self, parser):
        code = '''
defmodule MyAppWeb.HomeLive do
  use Phoenix.LiveView
  def mount(_, _, socket), do: {:ok, socket}
end
'''
        result = parser.parse(code, "lib/home_live.ex")
        assert "phoenix_live_view" in result.detected_frameworks or result.live_views


class TestEdgeCases:
    """Tests for edge cases."""

    def test_parse_empty_file(self, parser):
        result = parser.parse("", "empty.ex")
        assert isinstance(result, PhoenixParseResult)
        assert len(result.routes) == 0

    def test_non_phoenix_file(self, parser):
        code = '''
defmodule MyApp.Math do
  def add(a, b), do: a + b
end
'''
        result = parser.parse(code, "lib/math.ex")
        assert len(result.routes) == 0
        assert len(result.controllers) == 0

    def test_complex_router(self, parser):
        code = '''
defmodule MyAppWeb.Router do
  use MyAppWeb, :router

  pipeline :browser do
    plug :accepts, ["html"]
    plug :fetch_session
    plug :protect_from_forgery
  end

  pipeline :api do
    plug :accepts, ["json"]
  end

  scope "/", MyAppWeb do
    pipe_through :browser
    get "/", PageController, :index
    get "/about", PageController, :about
    live "/dashboard", DashboardLive
  end

  scope "/api/v1", MyAppWeb.API.V1 do
    pipe_through :api
    resources "/users", UserController
    resources "/posts", PostController, only: [:index, :show]
    get "/health", HealthController, :check
  end

  scope "/admin", MyAppWeb.Admin, as: :admin do
    pipe_through [:browser, :require_admin]
    live "/", AdminDashboardLive
  end
end
'''
        result = parser.parse(code, "lib/my_app_web/router.ex")
        assert len(result.routes) >= 5
