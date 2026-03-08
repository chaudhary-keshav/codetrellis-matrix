"""
Tests for RubyTypeExtractor — classes, modules, structs, Data.define.

Part of CodeTrellis v4.23 Ruby Language Support.
"""

import pytest
from codetrellis.extractors.ruby.type_extractor import RubyTypeExtractor


@pytest.fixture
def extractor():
    return RubyTypeExtractor()


# ===== CLASS EXTRACTION =====

class TestClassExtraction:
    """Tests for Ruby class extraction."""

    def test_simple_class(self, extractor):
        code = '''
class User
  attr_accessor :name, :email

  def initialize(name, email)
    @name = name
    @email = email
  end
end
'''
        result = extractor.extract(code, "user.rb")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "User"

    def test_class_with_superclass(self, extractor):
        code = '''
class Admin < User
  def admin?
    true
  end
end
'''
        result = extractor.extract(code, "admin.rb")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "Admin"
        assert cls.parent_class == "User"

    def test_class_with_namespace(self, extractor):
        code = '''
class Api::V2::UsersController < ApplicationController
  def index
  end
end
'''
        result = extractor.extract(code, "users_controller.rb")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert "UsersController" in cls.name
        assert "Api::V2" in cls.namespace or "Api::V2" in cls.name

    def test_class_with_mixins(self, extractor):
        code = '''
class Order
  include Comparable
  extend Forwardable
  prepend MyModule

  def initialize(total)
    @total = total
  end
end
'''
        result = extractor.extract(code, "order.rb")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "Order"
        mixin_names = [m.name for m in cls.mixins]
        assert "Comparable" in mixin_names

    def test_class_with_attr_accessors(self, extractor):
        code = '''
class Product
  attr_reader :id
  attr_writer :price
  attr_accessor :name, :description

  def initialize(id, name)
    @id = id
    @name = name
  end
end
'''
        result = extractor.extract(code, "product.rb")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "Product"
        field_names = [f.name for f in cls.fields]
        assert "id" in field_names or "name" in field_names

    def test_class_with_constants(self, extractor):
        code = '''
class Config
  MAX_RETRIES = 3
  DEFAULT_TIMEOUT = 30
  VALID_STATUSES = [:active, :inactive].freeze
end
'''
        result = extractor.extract(code, "config.rb")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "Config"
        assert "MAX_RETRIES" in cls.constants or len(cls.constants) > 0

    def test_nested_class(self, extractor):
        code = '''
module Payments
  class Processor
    class Error < StandardError; end

    def process(amount)
    end
  end
end
'''
        result = extractor.extract(code, "processor.rb")
        classes = result["classes"]
        class_names = [c.name for c in classes]
        assert "Processor" in class_names

    def test_class_with_doc_comment(self, extractor):
        code = '''
# Represents a user account in the system.
# Handles authentication and authorization.
class UserAccount
  def login(password)
  end
end
'''
        result = extractor.extract(code, "user_account.rb")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "UserAccount"
        assert cls.doc_comment  # Should have doc comment

    def test_application_record(self, extractor):
        code = '''
class ApplicationRecord < ActiveRecord::Base
  self.abstract_class = true
end
'''
        result = extractor.extract(code, "application_record.rb")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "ApplicationRecord"
        assert "ActiveRecord::Base" in cls.parent_class


# ===== MODULE EXTRACTION =====

class TestModuleExtraction:
    """Tests for Ruby module extraction."""

    def test_simple_module(self, extractor):
        code = '''
module Authenticatable
  def authenticate(token)
    verify_token(token)
  end
end
'''
        result = extractor.extract(code, "authenticatable.rb")
        assert len(result["modules"]) >= 1
        mod = result["modules"][0]
        assert mod.name == "Authenticatable"

    def test_concern_module(self, extractor):
        code = '''
module Searchable
  extend ActiveSupport::Concern

  included do
    scope :search, ->(term) { where("name LIKE ?", "%#{term}%") }
  end

  class_methods do
    def find_by_query(q)
    end
  end
end
'''
        result = extractor.extract(code, "searchable.rb")
        assert len(result["modules"]) >= 1
        mod = result["modules"][0]
        assert mod.name == "Searchable"
        assert mod.is_concern is True

    def test_namespaced_module(self, extractor):
        code = '''
module Api
  module V2
    module Helpers
      def format_response(data)
      end
    end
  end
end
'''
        result = extractor.extract(code, "helpers.rb")
        modules = result["modules"]
        mod_names = [m.name for m in modules]
        assert "Api" in mod_names or "V2" in mod_names or "Helpers" in mod_names

    def test_module_with_constants(self, extractor):
        code = '''
module Constants
  VERSION = "1.0.0"
  API_BASE = "https://api.example.com"
end
'''
        result = extractor.extract(code, "constants.rb")
        assert len(result["modules"]) >= 1
        mod = result["modules"][0]
        assert mod.name == "Constants"


# ===== STRUCT EXTRACTION =====

class TestStructExtraction:
    """Tests for Ruby Struct and Data extraction."""

    def test_struct_new(self, extractor):
        code = '''
Point = Struct.new(:x, :y)
'''
        result = extractor.extract(code, "point.rb")
        assert len(result["structs"]) >= 1
        s = result["structs"][0]
        assert s.name == "Point"
        assert "x" in s.members
        assert "y" in s.members

    def test_struct_keyword_init(self, extractor):
        code = '''
Address = Struct.new(:street, :city, :zip, keyword_init: true)
'''
        result = extractor.extract(code, "address.rb")
        assert len(result["structs"]) >= 1
        s = result["structs"][0]
        assert s.name == "Address"
        assert s.keyword_init is True

    def test_struct_with_block(self, extractor):
        code = '''
Person = Struct.new(:name, :age) do
  def greeting
    "Hi, I'm #{name}"
  end
end
'''
        result = extractor.extract(code, "person.rb")
        assert len(result["structs"]) >= 1
        s = result["structs"][0]
        assert s.name == "Person"

    def test_data_define(self, extractor):
        code = '''
Measure = Data.define(:amount, :unit)
'''
        result = extractor.extract(code, "measure.rb")
        assert len(result["structs"]) >= 1
        s = result["structs"][0]
        assert s.name == "Measure"
        assert s.kind == "Data"
        assert "amount" in s.members


# ===== EDGE CASES =====

class TestEdgeCases:
    """Tests for edge cases in type extraction."""

    def test_empty_file(self, extractor):
        result = extractor.extract("", "empty.rb")
        assert result["classes"] == []
        assert result["modules"] == []
        assert result["structs"] == []

    def test_comment_only_file(self, extractor):
        code = '''
# This file is intentionally left blank.
# It serves as a placeholder.
'''
        result = extractor.extract(code, "comment.rb")
        assert result["classes"] == []

    def test_class_with_eigenclass(self, extractor):
        code = '''
class Singleton
  class << self
    def instance
      @instance ||= new
    end
  end
end
'''
        result = extractor.extract(code, "singleton.rb")
        assert len(result["classes"]) >= 1
        cls = result["classes"][0]
        assert cls.name == "Singleton"

    def test_one_liner_class(self, extractor):
        code = '''
class NotFoundError < StandardError; end
class ForbiddenError < StandardError; end
'''
        result = extractor.extract(code, "errors.rb")
        assert len(result["classes"]) >= 2
        names = [c.name for c in result["classes"]]
        assert "NotFoundError" in names
        assert "ForbiddenError" in names
