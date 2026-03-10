"""
Tests for Ruby framework enhanced parsers — Rails, Sinatra, Hanami, Grape, Sidekiq.

Part of CodeTrellis v5.2 Ruby Framework Support.
"""

import pytest
from codetrellis.rails_parser_enhanced import EnhancedRailsParser, RailsParseResult
from codetrellis.sinatra_parser_enhanced import EnhancedSinatraParser, SinatraParseResult
from codetrellis.hanami_parser_enhanced import EnhancedHanamiParser, HanamiParseResult
from codetrellis.grape_parser_enhanced import EnhancedGrapeParser, GrapeParseResult
from codetrellis.sidekiq_parser_enhanced import EnhancedSidekiqParser, SidekiqParseResult


# ===== FIXTURES =====

@pytest.fixture
def rails_parser():
    return EnhancedRailsParser()


@pytest.fixture
def sinatra_parser():
    return EnhancedSinatraParser()


@pytest.fixture
def hanami_parser():
    return EnhancedHanamiParser()


@pytest.fixture
def grape_parser():
    return EnhancedGrapeParser()


@pytest.fixture
def sidekiq_parser():
    return EnhancedSidekiqParser()


# ===== RAILS TESTS =====

class TestRailsParser:
    """Tests for EnhancedRailsParser."""

    def test_parse_empty_file(self, rails_parser):
        result = rails_parser.parse("", "empty.rb")
        assert isinstance(result, RailsParseResult)
        assert result.routes == []
        assert result.controllers == []

    def test_parse_non_rails_file(self, rails_parser):
        code = "class Foo; def bar; end; end"
        result = rails_parser.parse(code, "foo.rb")
        assert result.detected_frameworks == []

    def test_parse_routes(self, rails_parser):
        code = '''
Rails.application.routes.draw do
  root 'home#index'
  get '/about', to: 'pages#about'
  post '/users', to: 'users#create'
  resources :articles
  namespace :admin do
    resources :users
  end
end
'''
        result = rails_parser.parse(code, "config/routes.rb")
        assert len(result.routes) >= 3
        assert any(r.method == "root" for r in result.routes)
        assert any(r.path == "/about" for r in result.routes)
        assert 'rails' in result.detected_frameworks

    def test_parse_controller(self, rails_parser):
        code = '''
class UsersController < ApplicationController
  before_action :authenticate_user!
  before_action :set_user, only: [:show, :edit, :update]

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

  def user_params
    params.require(:user).permit(:name, :email)
  end
end
'''
        result = rails_parser.parse(code, "app/controllers/users_controller.rb")
        assert len(result.controllers) >= 1
        assert result.controllers[0].name == "UsersController"

    def test_parse_model(self, rails_parser):
        code = '''
class User < ApplicationRecord
  has_many :posts
  belongs_to :team
  has_one :profile

  validates :email, presence: true, uniqueness: true
  validates :name, presence: true

  scope :active, -> { where(active: true) }
  scope :admins, -> { where(role: :admin) }

  enum role: { member: 0, admin: 1 }

  before_save :normalize_email
end
'''
        result = rails_parser.parse(code, "app/models/user.rb")
        assert len(result.models) >= 1
        assert result.models[0].name == "User"
        assert any(a.get('type') == 'has_many' for a in result.models[0].associations)

    def test_parse_migration(self, rails_parser):
        code = '''
class CreateUsers < ActiveRecord::Migration[7.1]
  def change
    create_table :users do |t|
      t.string :name, null: false
      t.string :email, null: false
      t.timestamps
    end
    add_index :users, :email, unique: true
  end
end
'''
        result = rails_parser.parse(code, "db/migrate/20240101_create_users.rb")
        assert len(result.migrations) >= 1

    def test_parse_active_job(self, rails_parser):
        code = '''
class SendWelcomeEmailJob < ApplicationJob
  queue_as :mailers

  def perform(user_id)
    user = User.find(user_id)
    UserMailer.welcome(user).deliver_now
  end
end
'''
        result = rails_parser.parse(code, "app/jobs/send_welcome_email_job.rb")
        assert len(result.jobs) >= 1
        assert result.jobs[0].name == "SendWelcomeEmailJob"

    def test_detect_version_rails7(self, rails_parser):
        code = '''
Rails.application.routes.draw do
  root 'home#index'
end

class User < ApplicationRecord
  enum :role, { member: 0, admin: 1 }
  normalizes :email, with: -> { _1.strip.downcase }
end
'''
        result = rails_parser.parse(code, "app.rb")
        assert result.rails_version in ("7.x", "7.1+")

    def test_framework_detection(self, rails_parser):
        code = '''
require 'rails'
gem 'devise'
gem 'pundit'
gem 'sidekiq'
gem 'turbo-rails'
'''
        result = rails_parser.parse(code, "Gemfile")
        assert 'rails' in result.detected_frameworks


# ===== SINATRA TESTS =====

class TestSinatraParser:
    """Tests for EnhancedSinatraParser."""

    def test_parse_empty_file(self, sinatra_parser):
        result = sinatra_parser.parse("", "empty.rb")
        assert isinstance(result, SinatraParseResult)
        assert result.routes == []

    def test_parse_non_sinatra_file(self, sinatra_parser):
        code = "class Foo; def bar; end; end"
        result = sinatra_parser.parse(code, "foo.rb")
        assert result.detected_frameworks == []

    def test_parse_classic_app(self, sinatra_parser):
        code = '''
require 'sinatra'

get '/' do
  'Hello World'
end

post '/users' do
  content_type :json
  { user: params[:name] }.to_json
end

put '/users/:id' do
  "Update user #{params[:id]}"
end

delete '/users/:id' do
  "Delete user #{params[:id]}"
end
'''
        result = sinatra_parser.parse(code, "app.rb")
        assert len(result.routes) >= 4
        assert any(r.method == "GET" for r in result.routes)
        assert any(r.method == "POST" for r in result.routes)
        assert 'sinatra' in result.detected_frameworks

    def test_parse_modular_app(self, sinatra_parser):
        code = '''
require 'sinatra/base'

class MyApp < Sinatra::Base
  set :views, 'templates'
  enable :sessions

  get '/' do
    erb :index
  end

  post '/api/data' do
    json data: process(params)
  end
end
'''
        result = sinatra_parser.parse(code, "app.rb")
        assert len(result.routes) >= 2
        assert len(result.settings) >= 1

    def test_parse_filters(self, sinatra_parser):
        code = '''
require 'sinatra'

before do
  content_type :json
end

before '/admin/*' do
  authenticate!
end

after do
  logger.info "Request completed"
end

get '/' do
  'hello'
end
'''
        result = sinatra_parser.parse(code, "app.rb")
        assert len(result.filters) >= 2

    def test_parse_error_handlers(self, sinatra_parser):
        code = '''
require 'sinatra'

not_found do
  'Not Found'
end

error 500 do
  'Internal Error'
end

error ArgumentError do
  'Bad Arguments'
end

get '/' do
  'ok'
end
'''
        result = sinatra_parser.parse(code, "app.rb")
        assert len(result.error_handlers) >= 2

    def test_parse_helpers(self, sinatra_parser):
        code = '''
require 'sinatra'

helpers do
  def current_user
    @user ||= User.find(session[:user_id])
  end

  def authenticate!
    halt 401 unless current_user
  end
end

get '/' do
  'hello'
end
'''
        result = sinatra_parser.parse(code, "app.rb")
        assert len(result.helpers) >= 1


# ===== HANAMI TESTS =====

class TestHanamiParser:
    """Tests for EnhancedHanamiParser."""

    def test_parse_empty_file(self, hanami_parser):
        result = hanami_parser.parse("", "empty.rb")
        assert isinstance(result, HanamiParseResult)
        assert result.actions == []

    def test_parse_non_hanami_file(self, hanami_parser):
        code = "class Foo; def bar; end; end"
        result = hanami_parser.parse(code, "foo.rb")
        assert result.detected_frameworks == []

    def test_parse_action_v2(self, hanami_parser):
        code = '''
require 'hanami'

module Main
  module Actions
    module Users
      class Index < Main::Action
        def handle(request, response)
          users = user_repo.all
          response.body = users.to_json
        end
      end
    end
  end
end
'''
        result = hanami_parser.parse(code, "app/actions/users/index.rb")
        assert len(result.actions) >= 1
        assert result.actions[0].has_handle_method

    def test_parse_routes(self, hanami_parser):
        code = '''
require 'hanami'

Hanami.app.routes do
  root to: 'home.index'
  get '/users', to: 'users.index'
  post '/users', to: 'users.create'
  get '/users/:id', to: 'users.show'
end
'''
        result = hanami_parser.parse(code, "config/routes.rb")
        assert len(result.routes) >= 3

    def test_parse_entity(self, hanami_parser):
        code = '''
require 'hanami'

class User < Hanami::Entity
  attribute :name
  attribute :email
  attribute :age
end
'''
        result = hanami_parser.parse(code, "lib/entities/user.rb")
        assert len(result.entities) >= 1
        assert result.entities[0].name == "User"
        assert 'name' in result.entities[0].attributes

    def test_parse_repository(self, hanami_parser):
        code = '''
require 'hanami'

class UserRepository < Hanami::Repository
  relations :users

  def find_by_email(email)
    users.where(email: email).one
  end
end
'''
        result = hanami_parser.parse(code, "lib/repos/user_repository.rb")
        assert len(result.repositories) >= 1
        assert result.repositories[0].name == "UserRepository"

    def test_parse_slice(self, hanami_parser):
        code = '''
require 'hanami'

module Admin
  class Slice < Hanami::Slice
  end
end
'''
        result = hanami_parser.parse(code, "slices/admin/slice.rb")
        assert len(result.slices) >= 1
        assert result.has_slices

    def test_detect_version_2x(self, hanami_parser):
        code = '''
require 'hanami'
Hanami.app.register('persistence', MyPersistence)
include Deps['repos.users']
'''
        result = hanami_parser.parse(code, "app.rb")
        assert result.hanami_version in ("2.x", "2.1+")


# ===== GRAPE TESTS =====

class TestGrapeParser:
    """Tests for EnhancedGrapeParser."""

    def test_parse_empty_file(self, grape_parser):
        result = grape_parser.parse("", "empty.rb")
        assert isinstance(result, GrapeParseResult)
        assert result.endpoints == []

    def test_parse_non_grape_file(self, grape_parser):
        code = "class Foo; def bar; end; end"
        result = grape_parser.parse(code, "foo.rb")
        assert result.detected_frameworks == []

    def test_parse_basic_api(self, grape_parser):
        code = '''
class UsersAPI < Grape::API
  version 'v1', using: :path
  format :json

  resource :users do
    desc 'List all users'
    get do
      User.all
    end

    desc 'Create a user'
    params do
      requires :name, type: String
      requires :email, type: String
      optional :role, type: String, default: 'member'
    end
    post do
      User.create!(declared(params))
    end

    route_param :id do
      desc 'Get a user'
      get do
        User.find(params[:id])
      end

      desc 'Update a user'
      put do
        User.find(params[:id]).update!(declared(params))
      end

      desc 'Delete a user'
      delete do
        User.find(params[:id]).destroy
      end
    end
  end
end
'''
        result = grape_parser.parse(code, "app/api/users.rb")
        assert len(result.endpoints) >= 4
        assert len(result.resources) >= 1
        assert any(ep.method == "GET" for ep in result.endpoints)
        assert any(ep.method == "POST" for ep in result.endpoints)
        assert 'grape' in result.detected_frameworks

    def test_parse_params(self, grape_parser):
        code = '''
class API < Grape::API
  params do
    requires :name, type: String
    requires :age, type: Integer
    optional :email, type: String
  end
  post '/users' do
    create_user(declared(params))
  end
end
'''
        result = grape_parser.parse(code, "api.rb")
        assert len(result.params) >= 3
        required_params = [p for p in result.params if p.required]
        assert len(required_params) >= 2

    def test_parse_entity(self, grape_parser):
        code = '''
class UserEntity < Grape::Entity
  root 'users'
  expose :id
  expose :name
  expose :email
  expose :created_at
end
'''
        result = grape_parser.parse(code, "app/entities/user_entity.rb")
        assert len(result.entities) >= 1
        assert result.entities[0].name == "UserEntity"
        assert len(result.entities[0].exposures) >= 3

    def test_parse_mount(self, grape_parser):
        code = '''
class RootAPI < Grape::API
  mount UsersAPI
  mount ArticlesAPI
  mount Admin::API
end
'''
        result = grape_parser.parse(code, "app/api/root.rb")
        assert len(result.mounts) >= 3

    def test_parse_error_handling(self, grape_parser):
        code = '''
class API < Grape::API
  rescue_from ActiveRecord::RecordNotFound
  rescue_from Grape::Exceptions::ValidationErrors
  rescue_from :all

  get '/test' do
    'ok'
  end
end
'''
        result = grape_parser.parse(code, "api.rb")
        assert len(result.error_handlers) >= 2

    def test_parse_versioning(self, grape_parser):
        code = '''
class API < Grape::API
  version 'v2', using: :header
  format :json

  get '/status' do
    { status: 'ok' }
  end
end
'''
        result = grape_parser.parse(code, "api.rb")
        assert result.versioning_strategy == "header"


# ===== SIDEKIQ TESTS =====

class TestSidekiqParser:
    """Tests for EnhancedSidekiqParser."""

    def test_parse_empty_file(self, sidekiq_parser):
        result = sidekiq_parser.parse("", "empty.rb")
        assert isinstance(result, SidekiqParseResult)
        assert result.workers == []

    def test_parse_non_sidekiq_file(self, sidekiq_parser):
        code = "class Foo; def bar; end; end"
        result = sidekiq_parser.parse(code, "foo.rb")
        assert result.detected_frameworks == []

    def test_parse_worker(self, sidekiq_parser):
        code = '''
require 'sidekiq'

class HardWorker
  include Sidekiq::Worker
  sidekiq_options queue: 'critical', retry: 5

  def perform(user_id, action)
    user = User.find(user_id)
    user.process(action)
  end
end
'''
        result = sidekiq_parser.parse(code, "app/workers/hard_worker.rb")
        assert len(result.workers) >= 1
        assert result.workers[0].name == "HardWorker"
        assert result.workers[0].queue == "critical"
        assert result.workers[0].retry_count == "5"
        assert len(result.workers[0].perform_params) >= 2
        assert 'sidekiq' in result.detected_frameworks

    def test_parse_job_v7(self, sidekiq_parser):
        code = '''
require 'sidekiq'

class ProcessOrderJob
  include Sidekiq::Job
  sidekiq_options queue: 'orders', retry: 3

  def perform(order_id)
    Order.find(order_id).process!
  end
end
'''
        result = sidekiq_parser.parse(code, "app/jobs/process_order_job.rb")
        assert len(result.workers) >= 1
        assert result.workers[0].name == "ProcessOrderJob"
        assert result.sidekiq_version == "7.x"

    def test_parse_activejob_worker(self, sidekiq_parser):
        code = '''
require 'sidekiq'

class SendEmailJob < ApplicationJob
  queue_as :mailers

  def perform(user_id)
    UserMailer.welcome(User.find(user_id)).deliver_now
  end
end
'''
        result = sidekiq_parser.parse(code, "app/jobs/send_email_job.rb")
        assert len(result.workers) >= 1

    def test_parse_scheduled_jobs(self, sidekiq_parser):
        code = '''
require 'sidekiq'

class CleanupJob
  include Sidekiq::Worker

  def perform
    OldRecord.where('created_at < ?', 30.days.ago).delete_all
  end
end

# Schedule it
CleanupJob.perform_in(1.hour)
CleanupJob.perform_at(Time.now + 86400)
'''
        result = sidekiq_parser.parse(code, "app/workers/cleanup.rb")
        assert len(result.schedules) >= 2

    def test_parse_batch(self, sidekiq_parser):
        code = '''
require 'sidekiq'

class BatchProcessor
  include Sidekiq::Worker

  def perform
    batch = Sidekiq::Batch.new
    batch.on(:complete, BatchCallback, bid: batch.bid)
    batch.on(:success, SuccessCallback)
    batch.jobs do
      100.times { |i| ItemWorker.perform_async(i) }
    end
  end
end
'''
        result = sidekiq_parser.parse(code, "app/workers/batch.rb")
        assert len(result.batches) >= 1
        assert result.has_pro

    def test_parse_middleware(self, sidekiq_parser):
        code = '''
require 'sidekiq'

Sidekiq.configure_server do |config|
  config.server_middleware do |chain|
    chain.add LoggingMiddleware
    chain.add MetricsMiddleware
  end
end
'''
        result = sidekiq_parser.parse(code, "config/sidekiq.rb")
        assert len(result.middleware) >= 2

    def test_parse_config(self, sidekiq_parser):
        code = '''
require 'sidekiq'

Sidekiq.configure_server do |config|
  config.redis = { url: ENV['REDIS_URL'], pool_size: 25 }
  config.concurrency = 15
end

Sidekiq.configure_client do |config|
  config.redis = { url: ENV['REDIS_URL'], pool_size: 5 }
end
'''
        result = sidekiq_parser.parse(code, "config/sidekiq.rb")
        assert any(c.key == "concurrency" for c in result.configs)

    def test_parse_retries_exhausted(self, sidekiq_parser):
        code = '''
require 'sidekiq'

class ImportantWorker
  include Sidekiq::Worker

  sidekiq_retries_exhausted do |msg, ex|
    Notifier.alert("Job failed permanently: #{msg['class']}")
  end

  def perform(data)
    process(data)
  end
end
'''
        result = sidekiq_parser.parse(code, "app/workers/important.rb")
        assert any(c.event == "retries_exhausted" for c in result.callbacks)
