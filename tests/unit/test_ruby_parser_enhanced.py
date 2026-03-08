"""
Tests for EnhancedRubyParser — full parser integration, framework detection, Gemfile parsing.

Part of CodeTrellis v4.23 Ruby Language Support.
"""

import pytest
from codetrellis.ruby_parser_enhanced import EnhancedRubyParser, RubyParseResult


@pytest.fixture
def parser():
    return EnhancedRubyParser()


# ===== BASIC PARSING =====

class TestBasicParsing:
    """Tests for basic Ruby file parsing."""

    def test_parse_empty_file(self, parser):
        result = parser.parse("", "empty.rb")
        assert isinstance(result, RubyParseResult)
        assert result.file_path == "empty.rb"
        assert result.classes == []
        assert result.methods == []

    def test_parse_simple_class(self, parser):
        code = '''
class User
  attr_accessor :name, :email

  def initialize(name, email)
    @name = name
    @email = email
  end

  def full_info
    "#{name} <#{email}>"
  end
end
'''
        result = parser.parse(code, "user.rb")
        assert len(result.classes) >= 1
        assert result.classes[0].name == "User"
        assert len(result.methods) >= 1

    def test_parse_module_with_methods(self, parser):
        code = '''
module Helpers
  def format_date(date)
    date.strftime("%Y-%m-%d")
  end

  def format_currency(amount)
    "$#{amount.round(2)}"
  end
end
'''
        result = parser.parse(code, "helpers.rb")
        assert len(result.modules) >= 1
        assert result.modules[0].name == "Helpers"
        assert len(result.methods) >= 1

    def test_parse_struct(self, parser):
        code = '''
Point = Struct.new(:x, :y)
Config = Struct.new(:host, :port, keyword_init: true)
'''
        result = parser.parse(code, "types.rb")
        assert len(result.structs) >= 2


# ===== FROZEN STRING LITERAL =====

class TestMagicComments:
    """Tests for magic comment detection."""

    def test_frozen_string_literal_true(self, parser):
        code = '''# frozen_string_literal: true

class App
end
'''
        result = parser.parse(code, "app.rb")
        assert result.frozen_string_literal is True

    def test_frozen_string_literal_false(self, parser):
        code = '''# frozen_string_literal: false

class App
end
'''
        result = parser.parse(code, "app.rb")
        assert result.frozen_string_literal is False

    def test_no_frozen_string_literal(self, parser):
        code = '''
class App
end
'''
        result = parser.parse(code, "app.rb")
        assert result.frozen_string_literal is None

    def test_sorbet_typed(self, parser):
        code = '''# typed: strict

class TypedClass
  extend T::Sig

  sig { params(name: String).returns(String) }
  def greet(name)
    "Hello #{name}"
  end
end
'''
        result = parser.parse(code, "typed_class.rb")
        assert result.sorbet_typed == "strict"


# ===== IMPORT EXTRACTION =====

class TestImportExtraction:
    """Tests for require/require_relative extraction."""

    def test_require(self, parser):
        code = '''
require 'json'
require 'net/http'
require 'active_record'
'''
        result = parser.parse(code, "app.rb")
        assert "json" in result.imports
        assert "net/http" in result.imports

    def test_require_relative(self, parser):
        code = '''
require_relative 'config'
require_relative '../models/user'
'''
        result = parser.parse(code, "app.rb")
        assert "config" in result.imports or "../models/user" in result.imports


# ===== FRAMEWORK DETECTION =====

class TestFrameworkDetection:
    """Tests for Ruby framework detection."""

    def test_detect_rails(self, parser):
        code = '''
class UsersController < ApplicationController
  def index
    @users = User.all
  end
end
'''
        result = parser.parse(code, "users_controller.rb")
        assert "rails" in result.detected_frameworks or "activerecord" in result.detected_frameworks

    def test_detect_sinatra(self, parser):
        code = '''
class MyApp < Sinatra::Base
  get '/hello' do
    "Hello World"
  end
end
'''
        result = parser.parse(code, "app.rb")
        assert "sinatra" in result.detected_frameworks

    def test_detect_rspec(self, parser):
        code = '''
RSpec.describe User do
  describe '#full_name' do
    it 'returns full name' do
      user = User.new(first: "John", last: "Doe")
      expect(user.full_name).to eq("John Doe")
    end
  end
end
'''
        result = parser.parse(code, "user_spec.rb")
        assert "rspec" in result.detected_frameworks

    def test_detect_sidekiq(self, parser):
        code = '''
class HardWorker
  include Sidekiq::Worker

  def perform(name, count)
    puts "Working hard on #{name} #{count} times"
  end
end
'''
        result = parser.parse(code, "hard_worker.rb")
        assert "sidekiq" in result.detected_frameworks

    def test_detect_sorbet(self, parser):
        code = '''
# typed: strict
class MyService
  extend T::Sig

  sig { params(id: Integer).returns(T.nilable(User)) }
  def find(id)
    User.find_by(id: id)
  end
end
'''
        result = parser.parse(code, "my_service.rb")
        assert "sorbet" in result.detected_frameworks

    def test_detect_grape(self, parser):
        code = '''
class API < Grape::API
  resource :users do
    get do
      User.all
    end
  end
end
'''
        result = parser.parse(code, "api.rb")
        assert "grape" in result.detected_frameworks

    def test_detect_activerecord(self, parser):
        code = '''
class User < ActiveRecord::Base
  has_many :posts
  validates :name, presence: true
end
'''
        result = parser.parse(code, "user.rb")
        assert "activerecord" in result.detected_frameworks


# ===== RAILS MODELS =====

class TestRailsModels:
    """Tests for Rails model extraction via parser."""

    def test_model_with_associations(self, parser):
        code = '''
class Article < ApplicationRecord
  belongs_to :author, class_name: 'User'
  has_many :comments, dependent: :destroy
  has_many :tags, through: :article_tags
  has_one :featured_image

  validates :title, presence: true
  validates :body, length: { minimum: 10 }

  scope :published, -> { where(published: true) }
  scope :recent, -> { order(created_at: :desc) }

  enum status: { draft: 0, published: 1, archived: 2 }
end
'''
        result = parser.parse(code, "article.rb")
        assert len(result.models) >= 1
        model = result.models[0]
        assert model.name == "Article"
        assert len(model.associations) >= 3


# ===== GEMFILE PARSING =====

class TestGemfileParsing:
    """Tests for Gemfile parsing."""

    def test_parse_simple_gemfile(self, parser):
        gemfile = '''
source 'https://rubygems.org'

ruby '3.2.0'

gem 'rails', '~> 7.1'
gem 'pg', '~> 1.5'
gem 'puma', '>= 5.0'

group :development, :test do
  gem 'rspec-rails'
  gem 'factory_bot_rails'
end

group :development do
  gem 'rubocop', require: false
end
'''
        result = EnhancedRubyParser.parse_gemfile(gemfile)
        assert result.get('ruby_version') == '3.2.0'
        gems = result.get('gems', [])
        gem_names = [g['name'] for g in gems]
        assert 'rails' in gem_names
        assert 'pg' in gem_names

    def test_parse_gemfile_with_git_source(self, parser):
        gemfile = '''
source 'https://rubygems.org'

gem 'my_gem', git: 'https://github.com/user/my_gem.git'
gem 'another', github: 'user/another'
'''
        result = EnhancedRubyParser.parse_gemfile(gemfile)
        gems = result.get('gems', [])
        assert len(gems) >= 2


# ===== GEMSPEC PARSING =====

class TestGemspecParsing:
    """Tests for .gemspec parsing."""

    def test_parse_gemspec(self, parser):
        gemspec = '''
Gem::Specification.new do |spec|
  spec.name = "my_gem"
  spec.version = "1.0.0"
  spec.summary = "A great gem"
  spec.homepage = "https://github.com/user/my_gem"
  spec.license = "MIT"

  spec.add_dependency "activesupport", "~> 7.0"
  spec.add_development_dependency "rspec", "~> 3.12"
end
'''
        result = EnhancedRubyParser.parse_gemspec(gemspec)
        assert result['name'] == "my_gem"
        assert result['version'] == "1.0.0"
        assert result['license'] == "MIT"
        assert len(result['dependencies']) >= 1
        assert len(result['dev_dependencies']) >= 1


# ===== FULL INTEGRATION =====

class TestFullIntegration:
    """Tests for full parser integration with complex files."""

    def test_rails_controller_full(self, parser):
        code = '''# frozen_string_literal: true

require 'json'

class Api::V1::OrdersController < ApplicationController
  before_action :authenticate_user!
  before_action :set_order, only: [:show, :update]

  # @return [Array<Order>] list of user orders
  def index
    @orders = current_user.orders.includes(:items).page(params[:page])
    render json: OrderSerializer.new(@orders)
  end

  def show
    render json: OrderSerializer.new(@order)
  end

  def create
    @order = current_user.orders.build(order_params)
    if @order.save
      OrderMailer.confirmation(@order).deliver_later
      render json: OrderSerializer.new(@order), status: :created
    else
      render json: { errors: @order.errors }, status: :unprocessable_entity
    end
  end

  private

  def set_order
    @order = current_user.orders.find(params[:id])
  end

  def order_params
    params.require(:order).permit(:address_id, items: [:product_id, :quantity])
  end
end
'''
        result = parser.parse(code, "orders_controller.rb")
        assert result.frozen_string_literal is True
        assert "json" in result.imports
        assert len(result.classes) >= 1 or len(result.controllers) >= 1
        assert len(result.methods) >= 3
        assert any(fw in result.detected_frameworks for fw in ["rails", "activerecord"])

    def test_concern_module_full(self, parser):
        code = '''
module Auditable
  extend ActiveSupport::Concern

  included do
    has_many :audit_logs, as: :auditable
    after_create :log_creation
    after_update :log_update
  end

  class_methods do
    def audited_fields(*fields)
      @audited_fields = fields
    end
  end

  private

  def log_creation
    audit_logs.create!(action: 'create', changes: attributes)
  end

  def log_update
    audit_logs.create!(action: 'update', changes: saved_changes)
  end
end
'''
        result = parser.parse(code, "auditable.rb")
        assert len(result.modules) >= 1
        mod = result.modules[0]
        assert mod.name == "Auditable"
        assert mod.is_concern is True
        assert len(result.callbacks) >= 1 or len(result.methods) >= 1

    def test_sidekiq_worker(self, parser):
        code = '''
class ReportGeneratorWorker
  include Sidekiq::Worker
  sidekiq_options queue: :reports, retry: 3

  def perform(report_id, format)
    report = Report.find(report_id)
    generator = ReportGenerator.new(report)
    generator.generate(format: format)
    ReportMailer.completed(report).deliver_later
  end
end
'''
        result = parser.parse(code, "report_generator_worker.rb")
        assert "sidekiq" in result.detected_frameworks
        assert len(result.classes) >= 1
        assert len(result.workers) >= 1 or len(result.methods) >= 1

    def test_complex_activerecord_model(self, parser):
        code = '''
class User < ApplicationRecord
  include Searchable
  include Auditable

  has_secure_password

  has_many :posts, dependent: :destroy
  has_many :comments
  has_one :profile
  belongs_to :organization
  has_and_belongs_to_many :roles

  validates :email, presence: true, uniqueness: true, format: { with: URI::MailTo::EMAIL_REGEXP }
  validates :username, presence: true, length: { in: 3..50 }

  scope :active, -> { where(active: true) }
  scope :admins, -> { joins(:roles).where(roles: { name: 'admin' }) }
  scope :created_after, ->(date) { where("created_at > ?", date) }

  enum role_type: { member: 0, moderator: 1, admin: 2 }

  before_save :normalize_email
  after_create :send_welcome_email

  def full_name
    "#{first_name} #{last_name}"
  end

  private

  def normalize_email
    self.email = email.downcase.strip
  end

  def send_welcome_email
    UserMailer.welcome(self).deliver_later
  end
end
'''
        result = parser.parse(code, "user.rb")
        assert len(result.models) >= 1
        user_model = result.models[0]
        assert user_model.name == "User"
        assert len(user_model.associations) >= 4
        assert len(user_model.validations) >= 2
        assert len(result.callbacks) >= 1 or len(user_model.callbacks) >= 1
