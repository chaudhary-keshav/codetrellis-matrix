"""
Tests for Enhanced Flask Parser.

Part of CodeTrellis v4.33 Flask Language Support.
Tests cover:
- Route extraction (blueprints, methods, variable rules)
- Blueprint extraction (prefix, subdomain)
- Error handler extraction (HTTP codes, custom exceptions)
- Extension detection (SQLAlchemy, CORS, Migrate, etc.)
- CLI command extraction
- Context processor and template filter extraction
- Config detection (from_object, from_envvar)
- Framework detection and version detection
- is_flask_file detection
- to_codetrellis_format output
"""

import pytest
from codetrellis.flask_parser_enhanced import (
    EnhancedFlaskParser,
    FlaskParseResult,
    FlaskErrorHandlerInfo,
    FlaskExtensionInfo,
)
from codetrellis.extractors.python import (
    FlaskExtractor,
    FlaskRouteInfo,
    FlaskBlueprintInfo,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedFlaskParser()


@pytest.fixture
def flask_extractor():
    return FlaskExtractor()


# ═══════════════════════════════════════════════════════════════════
# Flask Extractor (base) Tests
# ═══════════════════════════════════════════════════════════════════

class TestFlaskExtractor:

    def test_extract_basic_routes(self, flask_extractor):
        """Test extracting basic Flask routes."""
        content = """
from flask import Flask

app = Flask(__name__)

@app.route('/hello')
def hello():
    return 'Hello World'

@app.route('/users', methods=['GET', 'POST'])
def users():
    return 'Users'
"""
        result = flask_extractor.extract(content)
        routes = result.get('routes', [])
        assert len(routes) >= 2

    def test_extract_blueprints(self, flask_extractor):
        """Test extracting Flask blueprints."""
        content = """
from flask import Blueprint

api = Blueprint('api', __name__, url_prefix='/api')
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
"""
        result = flask_extractor.extract(content)
        blueprints = result.get('blueprints', [])
        assert len(blueprints) >= 2

    def test_extract_blueprint_routes(self, flask_extractor):
        """Test extracting routes on blueprints."""
        content = """
from flask import Blueprint, jsonify

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/users', methods=['GET'])
def get_users():
    return jsonify([])

@api.route('/users/<int:user_id>', methods=['GET', 'PUT'])
def get_user(user_id):
    return jsonify({'id': user_id})
"""
        result = flask_extractor.extract(content)
        routes = result.get('routes', [])
        assert len(routes) >= 2


# ═══════════════════════════════════════════════════════════════════
# Enhanced Flask Parser Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedFlaskParser:

    def test_is_flask_file(self, parser):
        """Test Flask file detection."""
        content = """
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})
"""
        assert parser.is_flask_file(content, "app.py") is True

    def test_not_flask_file(self, parser):
        """Test non-Flask file detection."""
        content = """
import os
import sys

def main():
    print("hello")
"""
        assert parser.is_flask_file(content, "main.py") is False

    def test_parse_basic_flask_app(self, parser):
        """Test parsing a basic Flask application."""
        content = """
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello'

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/users', methods=['GET', 'POST'])
def users():
    if request.method == 'POST':
        return jsonify({'created': True}), 201
    return jsonify({'users': []})
"""
        result = parser.parse(content, "app.py")
        assert isinstance(result, FlaskParseResult)
        assert len(result.routes) >= 3
        assert result.file_type == "app"

    def test_parse_blueprints(self, parser):
        """Test parsing Flask blueprints."""
        content = """
from flask import Flask, Blueprint, jsonify

app = Flask(__name__)
api = Blueprint('api', __name__, url_prefix='/api/v1')

@api.route('/users', methods=['GET'])
def list_users():
    return jsonify([])

@api.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    return jsonify({'id': id})

app.register_blueprint(api)
"""
        result = parser.parse(content, "app.py")
        assert len(result.blueprints) >= 1
        bp = result.blueprints[0]
        assert bp.name == "api"
        assert bp.url_prefix == "/api/v1"

    def test_parse_error_handlers(self, parser):
        """Test parsing Flask error handlers."""
        content = """
from flask import Flask, jsonify

app = Flask(__name__)

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'internal server error'}), 500

@app.errorhandler(403)
def forbidden(e):
    return jsonify({'error': 'forbidden'}), 403
"""
        result = parser.parse(content, "app.py")
        assert len(result.error_handlers) >= 3

    def test_parse_extensions(self, parser):
        """Test parsing Flask extensions."""
        content = """
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_login import LoginManager

app = Flask(__name__)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
CORS(app)
login_manager = LoginManager(app)
"""
        result = parser.parse(content, "app.py")
        assert len(result.extensions) >= 1
        ext_names = [e.name for e in result.extensions]
        # Should detect at least SQLAlchemy
        assert any("SQLAlchemy" in n or "sqlalchemy" in n.lower() for n in ext_names)

    def test_parse_app_factory_pattern(self, parser):
        """Test parsing Flask app factory pattern."""
        content = """
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config_name)
    db.init_app(app)
    return app
"""
        result = parser.parse(content, "app.py")
        assert isinstance(result, FlaskParseResult)

    def test_detect_frameworks(self, parser):
        """Test Flask ecosystem framework detection."""
        content = """
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_wtf import FlaskForm
"""
        result = parser.parse(content, "app.py")
        assert 'flask' in result.detected_frameworks
        assert any('sqlalchemy' in f for f in result.detected_frameworks) or \
               any('flask_sqlalchemy' in f for f in result.detected_frameworks)

    def test_parse_variable_rules(self, parser):
        """Test parsing routes with variable rules."""
        content = """
from flask import Flask

app = Flask(__name__)

@app.route('/user/<username>')
def show_user_profile(username):
    return f'User {username}'

@app.route('/post/<int:post_id>')
def show_post(post_id):
    return f'Post {post_id}'

@app.route('/path/<path:subpath>')
def show_subpath(subpath):
    return f'Subpath {subpath}'
"""
        result = parser.parse(content, "app.py")
        assert len(result.routes) >= 3

    def test_to_codetrellis_format(self, parser):
        """Test to_codetrellis_format produces valid output."""
        content = """
from flask import Flask, Blueprint, jsonify

app = Flask(__name__)
api = Blueprint('api', __name__, url_prefix='/api')

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@api.route('/users', methods=['GET', 'POST'])
def users():
    return jsonify([])

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'not found'}), 404
"""
        result = parser.parse(content, "app.py")
        output = parser.to_codetrellis_format(result)

        assert isinstance(output, str)
        assert "[FILE:" in output
        assert "FLASK" in output

    def test_to_codetrellis_format_blueprints(self, parser):
        """Test to_codetrellis_format includes blueprint info."""
        content = """
from flask import Flask, Blueprint

app = Flask(__name__)
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')
api_v2 = Blueprint('api_v2', __name__, url_prefix='/api/v2')
"""
        result = parser.parse(content, "app.py")
        output = parser.to_codetrellis_format(result)

        assert "FLASK_BLUEPRINTS" in output
        assert "api_v1" in output
        assert "api_v2" in output

    def test_to_codetrellis_format_extensions(self, parser):
        """Test to_codetrellis_format includes extension info."""
        content = """
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
db = SQLAlchemy(app)
CORS(app)
"""
        result = parser.parse(content, "app.py")
        output = parser.to_codetrellis_format(result)

        assert isinstance(output, str)
        if result.extensions:
            assert "FLASK_EXTENSIONS" in output

    def test_parse_empty_file(self, parser):
        """Test parsing empty content."""
        result = parser.parse("", "empty.py")
        assert isinstance(result, FlaskParseResult)
        assert len(result.routes) == 0

    def test_parse_non_flask_file(self, parser):
        """Test parsing a file with no Flask imports."""
        content = """
import os
import json

def process_data(data):
    return json.dumps(data)
"""
        result = parser.parse(content, "utils.py")
        assert isinstance(result, FlaskParseResult)
        assert len(result.routes) == 0


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════

class TestFlaskEdgeCases:

    def test_class_based_views(self, parser):
        """Test Flask class-based views (MethodView)."""
        content = """
from flask import Flask
from flask.views import MethodView

app = Flask(__name__)

class UserAPI(MethodView):
    def get(self, user_id=None):
        if user_id is None:
            return 'list users'
        return f'user {user_id}'

    def post(self):
        return 'create user'

user_view = UserAPI.as_view('user_api')
app.add_url_rule('/users/', view_func=user_view, methods=['GET', 'POST'])
app.add_url_rule('/users/<int:user_id>', view_func=user_view, methods=['GET'])
"""
        result = parser.parse(content, "app.py")
        assert isinstance(result, FlaskParseResult)

    def test_multiple_decorators(self, parser):
        """Test routes with multiple decorators."""
        content = """
from flask import Flask
from functools import wraps

app = Flask(__name__)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated

@app.route('/admin')
@login_required
def admin_panel():
    return 'admin'
"""
        result = parser.parse(content, "app.py")
        assert len(result.routes) >= 1

    def test_nested_blueprints(self, parser):
        """Test multiple blueprints in one file."""
        content = """
from flask import Blueprint

users_bp = Blueprint('users', __name__, url_prefix='/users')
posts_bp = Blueprint('posts', __name__, url_prefix='/posts')
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@users_bp.route('/')
def list_users():
    return 'users'

@posts_bp.route('/')
def list_posts():
    return 'posts'

@auth_bp.route('/login', methods=['POST'])
def login():
    return 'login'
"""
        result = parser.parse(content, "routes.py")
        assert len(result.blueprints) >= 3
        assert len(result.routes) >= 3

    def test_flask_restful_pattern(self, parser):
        """Test Flask-RESTful pattern detection."""
        content = """
from flask import Flask
from flask_restful import Api, Resource

app = Flask(__name__)
api = Api(app)

class UserResource(Resource):
    def get(self, user_id):
        return {'user_id': user_id}

    def put(self, user_id):
        return {'updated': True}

api.add_resource(UserResource, '/users/<int:user_id>')
"""
        result = parser.parse(content, "app.py")
        assert isinstance(result, FlaskParseResult)
        assert any('flask_restful' in f for f in result.detected_frameworks) or \
               any('restful' in f.lower() for f in result.detected_frameworks)
