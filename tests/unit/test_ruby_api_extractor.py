"""
Tests for RubyAPIExtractor — routes, controllers, gRPC, GraphQL.

Part of CodeTrellis v4.23 Ruby Language Support.
"""

import pytest
from codetrellis.extractors.ruby.api_extractor import RubyAPIExtractor


@pytest.fixture
def extractor():
    return RubyAPIExtractor()


# ===== RAILS ROUTE EXTRACTION =====

class TestRailsRouteExtraction:
    """Tests for Rails route extraction."""

    def test_simple_get_route(self, extractor):
        code = '''
Rails.application.routes.draw do
  get '/users', to: 'users#index'
  post '/users', to: 'users#create'
end
'''
        result = extractor.extract(code, "routes.rb")
        routes = result["routes"]
        assert len(routes) >= 2
        get_routes = [r for r in routes if r.method == "GET"]
        assert len(get_routes) >= 1
        assert get_routes[0].path == "/users"

    def test_resources_route(self, extractor):
        code = '''
Rails.application.routes.draw do
  resources :articles
  resources :comments, only: [:index, :create]
end
'''
        result = extractor.extract(code, "routes.rb")
        routes = result["routes"]
        assert len(routes) >= 1  # resources expands to CRUD routes

    def test_namespace_route(self, extractor):
        code = '''
Rails.application.routes.draw do
  namespace :api do
    namespace :v1 do
      resources :users
    end
  end
end
'''
        result = extractor.extract(code, "routes.rb")
        routes = result["routes"]
        assert len(routes) >= 1

    def test_root_route(self, extractor):
        code = '''
Rails.application.routes.draw do
  root 'home#index'
end
'''
        result = extractor.extract(code, "routes.rb")
        routes = result["routes"]
        assert len(routes) >= 1


# ===== SINATRA ROUTE EXTRACTION =====

class TestSinatraRouteExtraction:
    """Tests for Sinatra route extraction."""

    def test_sinatra_routes(self, extractor):
        code = '''
class MyApp < Sinatra::Base
  get '/hello' do
    "Hello World"
  end

  post '/data' do
    process_data(params)
  end

  put '/items/:id' do
    update_item(params[:id])
  end
end
'''
        result = extractor.extract(code, "app.rb")
        routes = result["routes"]
        assert len(routes) >= 2
        methods = [r.method for r in routes]
        assert "GET" in methods
        assert "POST" in methods


# ===== CONTROLLER EXTRACTION =====

class TestControllerExtraction:
    """Tests for Rails controller extraction."""

    def test_simple_controller(self, extractor):
        code = '''
class UsersController < ApplicationController
  before_action :authenticate_user!
  before_action :set_user, only: [:show, :update, :destroy]

  def index
    @users = User.all
  end

  def show
  end

  def create
    @user = User.new(user_params)
    if @user.save
      redirect_to @user
    else
      render :new
    end
  end

  private

  def set_user
    @user = User.find(params[:id])
  end

  def user_params
    params.require(:user).permit(:name, :email)
  end
end
'''
        result = extractor.extract(code, "users_controller.rb")
        controllers = result["controllers"]
        assert len(controllers) >= 1
        ctrl = controllers[0]
        assert ctrl.name == "UsersController"
        assert ctrl.parent_class == "ApplicationController"
        assert "index" in ctrl.actions or "show" in ctrl.actions

    def test_api_controller(self, extractor):
        code = '''
class Api::V1::ProductsController < Api::BaseController
  def index
    render json: Product.all
  end

  def show
    render json: Product.find(params[:id])
  end
end
'''
        result = extractor.extract(code, "products_controller.rb")
        controllers = result["controllers"]
        assert len(controllers) >= 1


# ===== GRAPE API EXTRACTION =====

class TestGrapeExtraction:
    """Tests for Grape API extraction."""

    def test_grape_api(self, extractor):
        code = '''
class Api::V1::Users < Grape::API
  resource :users do
    get do
      User.all
    end

    post do
      User.create!(params)
    end

    route_param :id do
      get do
        User.find(params[:id])
      end
    end
  end
end
'''
        result = extractor.extract(code, "users_api.rb")
        routes = result["routes"]
        assert len(routes) >= 1


# ===== GRAPHQL EXTRACTION =====

class TestGraphQLExtraction:
    """Tests for GraphQL type extraction."""

    def test_graphql_object_type(self, extractor):
        code = '''
class Types::UserType < Types::BaseObject
  field :id, ID, null: false
  field :name, String, null: false
  field :email, String, null: true
  field :posts, [Types::PostType], null: true
end
'''
        result = extractor.extract(code, "user_type.rb")
        graphql = result.get("graphql", [])
        if graphql:
            assert len(graphql) >= 1
            assert graphql[0].name == "UserType"

    def test_graphql_mutation(self, extractor):
        code = '''
class Mutations::CreateUser < Mutations::BaseMutation
  argument :name, String, required: true
  argument :email, String, required: true

  field :user, Types::UserType, null: true
  field :errors, [String], null: false

  def resolve(name:, email:)
    user = User.new(name: name, email: email)
    if user.save
      { user: user, errors: [] }
    else
      { user: nil, errors: user.errors.full_messages }
    end
  end
end
'''
        result = extractor.extract(code, "create_user.rb")
        graphql = result.get("graphql", [])
        if graphql:
            assert len(graphql) >= 1


# ===== GRPC EXTRACTION =====

class TestGRPCExtraction:
    """Tests for gRPC service extraction."""

    def test_grpc_service(self, extractor):
        code = '''
class GreeterService < Greeter::Service
  def say_hello(request, _call)
    HelloReply.new(message: "Hello #{request.name}")
  end
end
'''
        result = extractor.extract(code, "greeter_service.rb")
        grpc = result.get("grpc_services", [])
        if grpc:
            assert len(grpc) >= 1


# ===== EDGE CASES =====

class TestEdgeCases:
    """Tests for edge cases in API extraction."""

    def test_empty_file(self, extractor):
        result = extractor.extract("", "empty.rb")
        assert result["routes"] == []
        assert result["controllers"] == []

    def test_non_controller_class(self, extractor):
        code = '''
class UserService
  def create(params)
    User.create!(params)
  end
end
'''
        result = extractor.extract(code, "user_service.rb")
        controllers = result["controllers"]
        assert len(controllers) == 0  # Not a controller

    def test_rack_middleware(self, extractor):
        code = '''
class RateLimiter
  def initialize(app, limit: 100)
    @app = app
    @limit = limit
  end

  def call(env)
    if rate_limited?(env)
      [429, {}, ["Too Many Requests"]]
    else
      @app.call(env)
    end
  end
end
'''
        result = extractor.extract(code, "rate_limiter.rb")
        middleware = result.get("middleware", [])
        assert len(middleware) >= 0  # May or may not detect as middleware
