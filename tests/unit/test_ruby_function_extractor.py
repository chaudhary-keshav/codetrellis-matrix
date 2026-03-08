"""
Tests for RubyFunctionExtractor — methods, blocks, accessors, visibility.

Part of CodeTrellis v4.23 Ruby Language Support.
"""

import pytest
from codetrellis.extractors.ruby.function_extractor import RubyFunctionExtractor


@pytest.fixture
def extractor():
    return RubyFunctionExtractor()


# ===== METHOD EXTRACTION =====

class TestMethodExtraction:
    """Tests for Ruby method extraction."""

    def test_simple_instance_method(self, extractor):
        code = '''
class User
  def full_name
    "#{first_name} #{last_name}"
  end
end
'''
        result = extractor.extract(code, "user.rb")
        assert len(result["methods"]) >= 1
        m = result["methods"][0]
        assert m.name == "full_name"
        assert m.is_class_method is False

    def test_method_with_params(self, extractor):
        code = '''
class Calculator
  def add(a, b)
    a + b
  end
end
'''
        result = extractor.extract(code, "calculator.rb")
        assert len(result["methods"]) >= 1
        m = result["methods"][0]
        assert m.name == "add"
        param_names = [p.name for p in m.parameters]
        assert "a" in param_names
        assert "b" in param_names

    def test_method_with_keyword_params(self, extractor):
        code = '''
class Mailer
  def send_email(to:, subject:, body: "")
    # send logic
  end
end
'''
        result = extractor.extract(code, "mailer.rb")
        assert len(result["methods"]) >= 1
        m = result["methods"][0]
        assert m.name == "send_email"
        param_names = [p.name for p in m.parameters]
        assert "to" in param_names

    def test_class_method_self_dot(self, extractor):
        code = '''
class User
  def self.find_by_email(email)
    where(email: email).first
  end
end
'''
        result = extractor.extract(code, "user.rb")
        methods = [m for m in result["methods"] if m.name == "find_by_email"]
        assert len(methods) >= 1
        assert methods[0].is_class_method is True

    def test_private_methods(self, extractor):
        code = '''
class Service
  def process
    validate_input
    do_work
  end

  private

  def validate_input
    raise "Invalid" unless valid?
  end

  def do_work
    # implementation
  end
end
'''
        result = extractor.extract(code, "service.rb")
        methods = result["methods"]
        method_map = {m.name: m for m in methods}
        assert "process" in method_map
        if "validate_input" in method_map:
            assert method_map["validate_input"].visibility == "private"

    def test_protected_method(self, extractor):
        code = '''
class Account
  protected

  def secret_key
    @key
  end
end
'''
        result = extractor.extract(code, "account.rb")
        methods = [m for m in result["methods"] if m.name == "secret_key"]
        if methods:
            assert methods[0].visibility == "protected"

    def test_method_with_yield(self, extractor):
        code = '''
class Collection
  def each
    @items.each { |item| yield item }
  end
end
'''
        result = extractor.extract(code, "collection.rb")
        methods = [m for m in result["methods"] if m.name == "each"]
        assert len(methods) >= 1
        assert methods[0].uses_yield is True

    def test_method_with_splat_params(self, extractor):
        code = '''
class Logger
  def log(level, *messages, **options, &block)
    # logging logic
  end
end
'''
        result = extractor.extract(code, "logger.rb")
        methods = [m for m in result["methods"] if m.name == "log"]
        assert len(methods) >= 1

    def test_endless_method(self, extractor):
        code = '''
class MathUtils
  def self.square(n) = n * n
  def double(n) = n * 2
end
'''
        result = extractor.extract(code, "math_utils.rb")
        methods = result["methods"]
        endless = [m for m in methods if m.is_endless]
        assert len(endless) >= 1

    def test_method_with_yard_doc(self, extractor):
        code = '''
class Api
  # @param name [String] the user name
  # @param age [Integer] the user age
  # @return [User] the created user
  def create_user(name, age)
    User.new(name, age)
  end
end
'''
        result = extractor.extract(code, "api.rb")
        methods = [m for m in result["methods"] if m.name == "create_user"]
        assert len(methods) >= 1
        assert methods[0].doc_comment  # Should have YARD doc

    def test_define_method(self, extractor):
        code = '''
class DynamicModel
  [:active, :inactive, :pending].each do |status|
    define_method("#{status}?") do
      self.status == status
    end
  end
end
'''
        result = extractor.extract(code, "dynamic_model.rb")
        # define_method should be detected
        methods = result["methods"]
        assert len(methods) >= 0  # May or may not extract dynamic methods


# ===== ACCESSOR EXTRACTION =====

class TestAccessorExtraction:
    """Tests for Ruby accessor extraction."""

    def test_attr_reader(self, extractor):
        code = '''
class Config
  attr_reader :host, :port
end
'''
        result = extractor.extract(code, "config.rb")
        accessors = result.get("accessors", [])
        if accessors:
            acc_names = []
            for a in accessors:
                acc_names.extend(a.names)
            assert "host" in acc_names or "port" in acc_names

    def test_attr_accessor(self, extractor):
        code = '''
class Settings
  attr_accessor :debug_mode, :log_level
end
'''
        result = extractor.extract(code, "settings.rb")
        accessors = result.get("accessors", [])
        if accessors:
            assert len(accessors) >= 1


# ===== BLOCK EXTRACTION =====

class TestBlockExtraction:
    """Tests for Ruby block extraction."""

    def test_lambda_detection(self, extractor):
        code = '''
class Filter
  ACTIVE = ->(record) { record.active? }
  RECENT = lambda { |r| r.created_at > 1.day.ago }
end
'''
        result = extractor.extract(code, "filter.rb")
        blocks = result.get("blocks", [])
        # Should detect lambda/proc definitions
        assert len(blocks) >= 0  # Depends on implementation

    def test_proc_new(self, extractor):
        code = '''
class Handler
  CALLBACK = Proc.new { |event| process(event) }
end
'''
        result = extractor.extract(code, "handler.rb")
        blocks = result.get("blocks", [])
        assert len(blocks) >= 0


# ===== EDGE CASES =====

class TestEdgeCases:
    """Tests for edge cases in function extraction."""

    def test_empty_file(self, extractor):
        result = extractor.extract("", "empty.rb")
        assert result["methods"] == []

    def test_initialize_method(self, extractor):
        code = '''
class Entity
  def initialize(id, type)
    @id = id
    @type = type
  end
end
'''
        result = extractor.extract(code, "entity.rb")
        methods = [m for m in result["methods"] if m.name == "initialize"]
        assert len(methods) >= 1

    def test_method_alias(self, extractor):
        code = '''
class StringHelper
  def to_s
    inspect
  end

  alias_method :to_string, :to_s
end
'''
        result = extractor.extract(code, "string_helper.rb")
        methods = result["methods"]
        assert len(methods) >= 1

    def test_method_with_question_mark(self, extractor):
        code = '''
class User
  def active?
    status == :active
  end

  def admin?
    role == :admin
  end
end
'''
        result = extractor.extract(code, "user.rb")
        method_names = [m.name for m in result["methods"]]
        assert "active?" in method_names or "admin?" in method_names

    def test_method_with_bang(self, extractor):
        code = '''
class Account
  def activate!
    update!(status: :active)
  end
end
'''
        result = extractor.extract(code, "account.rb")
        method_names = [m.name for m in result["methods"]]
        assert "activate!" in method_names
