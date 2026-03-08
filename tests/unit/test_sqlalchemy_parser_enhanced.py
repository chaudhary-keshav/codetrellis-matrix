"""
Tests for Enhanced SQLAlchemy Parser.

Part of CodeTrellis v4.33 SQLAlchemy Framework Support.
Tests cover:
- ORM model extraction (SQLAlchemy 1.x and 2.0 style)
- Core Table() extraction
- Engine configuration extraction (create_engine, create_async_engine)
- Session configuration extraction (sessionmaker, scoped_session, async)
- Alembic migration extraction
- Event listener extraction (@event.listens_for, event.listen)
- Hybrid property extraction
- Framework detection
- Version detection
- is_sqlalchemy_file detection
- to_codetrellis_format output
"""

import pytest
from codetrellis.sqlalchemy_parser_enhanced import (
    EnhancedSQLAlchemyParser,
    SQLAlchemyParseResult,
    SQLAlchemyCoreTableInfo,
    SQLAlchemyEngineInfo,
    SQLAlchemySessionInfo,
    SQLAlchemyMigrationInfo,
    SQLAlchemyEventListenerInfo,
    SQLAlchemyHybridPropertyInfo,
)
from codetrellis.extractors.python.sqlalchemy_extractor import (
    SQLAlchemyModelInfo,
    SQLAlchemyColumnInfo,
    SQLAlchemyRelationshipInfo,
    RelationshipType,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedSQLAlchemyParser()


# ═══════════════════════════════════════════════════════════════════
# ORM Model Extraction Tests (via base extractor)
# ═══════════════════════════════════════════════════════════════════

class TestSQLAlchemyModels:

    def test_extract_basic_model(self, parser):
        """Test extracting a basic SQLAlchemy model."""
        content = """
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True)
"""
        result = parser.parse(content, "models.py")
        assert len(result.models) >= 1
        user_model = result.models[0]
        assert user_model.name == "User"
        assert user_model.table_name == "users"

    def test_extract_model_with_relationships(self, parser):
        """Test extracting model with relationships."""
        content = """
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    posts = relationship("Post", back_populates="author")

class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    author = relationship("User", back_populates="posts")
"""
        result = parser.parse(content, "models.py")
        assert len(result.models) >= 2
        assert result.total_models >= 2

    def test_extract_sqlalchemy_2_0_model(self, parser):
        """Test extracting SQLAlchemy 2.0 Mapped[] style models."""
        content = """
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
"""
        result = parser.parse(content)
        assert len(result.models) >= 1
        assert "sqlalchemy_2_0" in result.detected_frameworks


# ═══════════════════════════════════════════════════════════════════
# Core Table Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestSQLAlchemyCoreTables:

    def test_extract_core_table(self, parser):
        """Test Core Table() extraction."""
        content = """
from sqlalchemy import Table, Column, Integer, String, MetaData

metadata = MetaData()

users_table = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(100)),
    Column('email', String(255)),
)
"""
        result = parser.parse(content)
        assert len(result.core_tables) >= 1
        tbl = result.core_tables[0]
        assert tbl.name == "users"
        assert tbl.variable_name == "users_table"
        assert len(tbl.columns) >= 2

    def test_extract_association_table(self, parser):
        """Test association table extraction."""
        content = """
from sqlalchemy import Table, Column, Integer, ForeignKey, MetaData

metadata = MetaData()

user_roles = Table('user_roles', metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('role_id', Integer, ForeignKey('roles.id')),
)
"""
        result = parser.parse(content)
        assert len(result.core_tables) >= 1
        assert result.core_tables[0].name == "user_roles"


# ═══════════════════════════════════════════════════════════════════
# Engine Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestSQLAlchemyEngines:

    def test_extract_engine(self, parser):
        """Test create_engine extraction."""
        content = """
from sqlalchemy import create_engine

engine = create_engine("postgresql://user:pass@localhost/db", pool_size=10, echo=True)
"""
        result = parser.parse(content)
        assert len(result.engines) >= 1
        eng = result.engines[0]
        assert eng.variable_name == "engine"
        assert eng.url_pattern == "postgresql"
        assert eng.pool_size == 10
        assert eng.echo is True
        assert eng.is_async is False

    def test_extract_async_engine(self, parser):
        """Test create_async_engine extraction."""
        content = """
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
"""
        result = parser.parse(content)
        assert len(result.engines) >= 1
        assert result.engines[0].is_async is True
        assert result.uses_async is True

    def test_extract_sqlite_engine(self, parser):
        """Test SQLite engine extraction."""
        content = """
from sqlalchemy import create_engine

engine = create_engine("sqlite:///./test.db")
"""
        result = parser.parse(content)
        assert len(result.engines) >= 1
        assert result.engines[0].url_pattern == "sqlite"


# ═══════════════════════════════════════════════════════════════════
# Session Extraction Tests
# ═══════════════════════════════════════════════════════════════════

class TestSQLAlchemySessions:

    def test_extract_sessionmaker(self, parser):
        """Test sessionmaker extraction."""
        content = """
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
"""
        result = parser.parse(content)
        assert len(result.sessions) >= 1
        sess = result.sessions[0]
        assert sess.variable_name == "SessionLocal"
        assert sess.session_type == "sessionmaker"
        assert sess.bind == "engine"
        assert sess.expire_on_commit is False

    def test_extract_scoped_session(self, parser):
        """Test scoped_session extraction."""
        content = """
from sqlalchemy.orm import sessionmaker, scoped_session

Session = scoped_session(sessionmaker(bind=engine))
"""
        result = parser.parse(content)
        assert len(result.sessions) >= 1
        assert result.sessions[0].session_type == "scoped_session"

    def test_extract_async_session(self, parser):
        """Test async_sessionmaker extraction."""
        content = """
from sqlalchemy.ext.asyncio import async_sessionmaker

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
"""
        result = parser.parse(content)
        assert len(result.sessions) >= 1
        assert result.sessions[0].session_type == "async_sessionmaker"


# ═══════════════════════════════════════════════════════════════════
# Alembic Migration Tests
# ═══════════════════════════════════════════════════════════════════

class TestSQLAlchemyMigrations:

    def test_extract_migration(self, parser):
        """Test Alembic migration extraction."""
        content = '''"""create users table

Revision ID: abc123
"""

revision = 'abc123'
down_revision = 'def456'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100)),
    )
    op.create_index('ix_users_name', 'users', ['name'])


def downgrade():
    op.drop_index('ix_users_name')
    op.drop_table('users')
'''
        result = parser.parse(content, "versions/abc123_create_users.py")
        assert len(result.migrations) >= 1
        mig = result.migrations[0]
        assert mig.revision == "abc123"
        assert mig.down_revision == "def456"
        assert "create_table" in mig.operations
        assert "create_index" in mig.operations
        assert result.file_type == "migration"


# ═══════════════════════════════════════════════════════════════════
# Event Listener Tests
# ═══════════════════════════════════════════════════════════════════

class TestSQLAlchemyEvents:

    def test_event_listener_decorator(self, parser):
        """Test @event.listens_for decorator extraction."""
        content = """
from sqlalchemy import event

@event.listens_for(User, 'before_insert')
def set_created_at(mapper, connection, target):
    target.created_at = datetime.utcnow()
"""
        result = parser.parse(content)
        assert len(result.event_listeners) >= 1
        ev = result.event_listeners[0]
        assert ev.target == "User"
        assert ev.event_name == "before_insert"
        assert ev.handler == "set_created_at"

    def test_event_listen_call(self, parser):
        """Test event.listen() call extraction."""
        content = """
from sqlalchemy import event

def receive_after_flush(session, flush_context):
    pass

event.listen(Session, 'after_flush', receive_after_flush)
"""
        result = parser.parse(content)
        assert len(result.event_listeners) >= 1
        ev = result.event_listeners[0]
        assert ev.target == "Session"
        assert ev.event_name == "after_flush"


# ═══════════════════════════════════════════════════════════════════
# Hybrid Property Tests
# ═══════════════════════════════════════════════════════════════════

class TestSQLAlchemyHybridProperties:

    def test_hybrid_property(self, parser):
        """Test hybrid property extraction."""
        content = """
from sqlalchemy.ext.hybrid import hybrid_property

class User(Base):
    __tablename__ = 'users'
    first_name = Column(String(50))
    last_name = Column(String(50))

    @hybrid_property
    def full_name(self):
        return self.first_name + " " + self.last_name
"""
        result = parser.parse(content)
        assert len(result.hybrid_properties) >= 1
        hp = result.hybrid_properties[0]
        assert hp.name == "full_name"

    def test_hybrid_property_with_setter_and_expression(self, parser):
        """Test hybrid property with setter and expression."""
        content = """
from sqlalchemy.ext.hybrid import hybrid_property

class User(Base):
    __tablename__ = 'users'
    _price = Column(Integer)

    @hybrid_property
    def price(self):
        return self._price / 100

    @price.setter
    def price(self, value):
        self._price = int(value * 100)

    @price.expression
    def price(cls):
        return cls._price / 100
"""
        result = parser.parse(content)
        assert len(result.hybrid_properties) >= 1
        hp = result.hybrid_properties[0]
        assert hp.name == "price"
        assert hp.has_setter is True
        assert hp.has_expression is True


# ═══════════════════════════════════════════════════════════════════
# Framework Detection & Version Tests
# ═══════════════════════════════════════════════════════════════════

class TestSQLAlchemyDetection:

    def test_detect_frameworks(self, parser):
        """Test framework detection."""
        content = """
from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import event
"""
        result = parser.parse(content)
        assert "sqlalchemy" in result.detected_frameworks
        assert "sqlalchemy.orm" in result.detected_frameworks
        assert "sqlalchemy.event" in result.detected_frameworks

    def test_detect_async(self, parser):
        """Test async framework detection."""
        content = """
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
"""
        result = parser.parse(content)
        assert "sqlalchemy_async" in result.detected_frameworks
        assert result.uses_async is True

    def test_detect_alembic(self, parser):
        """Test Alembic detection."""
        content = """
from alembic import op
import sqlalchemy as sa

revision = 'abc123'
"""
        result = parser.parse(content)
        assert "alembic" in result.detected_frameworks

    def test_detect_sqlmodel(self, parser):
        """Test SQLModel detection."""
        content = """
from sqlmodel import SQLModel, Field
"""
        result = parser.parse(content)
        assert "sqlmodel" in result.detected_frameworks

    def test_version_detection_2_0(self, parser):
        """Test version detection for SQLAlchemy 2.0."""
        content = """
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
"""
        result = parser.parse(content)
        assert result.sqlalchemy_version == "2.0"

    def test_version_detection_1_4(self, parser):
        """Test version detection for SQLAlchemy 1.4 (async)."""
        content = """
from sqlalchemy.ext.asyncio import create_async_engine
"""
        result = parser.parse(content)
        assert result.sqlalchemy_version == "1.4"

    def test_is_sqlalchemy_file(self, parser):
        """Test SQLAlchemy file detection."""
        content = """
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
"""
        assert parser.is_sqlalchemy_file(content) is True

    def test_not_sqlalchemy_file(self, parser):
        """Test non-SQLAlchemy file."""
        content = """
def hello():
    print("Hello")
"""
        assert parser.is_sqlalchemy_file(content) is False

    def test_alembic_is_sqlalchemy_file(self, parser):
        """Test Alembic migration detected as SQLAlchemy."""
        content = """
from alembic import op
op.create_table('users')
"""
        assert parser.is_sqlalchemy_file(content) is True


# ═══════════════════════════════════════════════════════════════════
# File Classification Tests
# ═══════════════════════════════════════════════════════════════════

class TestSQLAlchemyClassification:

    def test_classify_model(self, parser):
        """Test model file classification."""
        result = parser.parse("class User(Base): pass", "models.py")
        assert result.file_type == "model"

    def test_classify_migration(self, parser):
        """Test migration file classification."""
        content = "revision = 'abc'\nop.create_table('t')"
        result = parser.parse(content, "migrations/versions/abc_init.py")
        assert result.file_type == "migration"

    def test_classify_config(self, parser):
        """Test config file classification."""
        result = parser.parse("engine = create_engine()", "database.py")
        assert result.file_type == "config"

    def test_classify_repository(self, parser):
        """Test repository file classification."""
        result = parser.parse("def get_user(): pass", "user_repository.py")
        assert result.file_type == "repository"


# ═══════════════════════════════════════════════════════════════════
# CodeTrellis Format Tests
# ═══════════════════════════════════════════════════════════════════

class TestSQLAlchemyFormat:

    def test_to_codetrellis_format_models(self, parser):
        """Test CodeTrellis format includes ORM models."""
        content = """
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
"""
        result = parser.parse(content, "models.py")
        output = parser.to_codetrellis_format(result)
        assert "SQLALCHEMY_ORM_MODELS" in output
        assert "User" in output

    def test_to_codetrellis_format_engines(self, parser):
        """Test CodeTrellis format includes engines."""
        content = """
from sqlalchemy import create_engine
engine = create_engine("postgresql://localhost/db", pool_size=5)
"""
        result = parser.parse(content)
        output = parser.to_codetrellis_format(result)
        assert "SQLALCHEMY_ENGINES" in output

    def test_to_codetrellis_format_empty(self, parser):
        """Test CodeTrellis format for empty file."""
        result = parser.parse("x = 1")
        output = parser.to_codetrellis_format(result)
        assert "SQLALCHEMY_ORM_MODELS" not in output

    def test_parse_empty(self, parser):
        """Test parsing empty content."""
        result = parser.parse("")
        assert result.total_models == 0
        assert result.total_tables == 0


# ═══════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestSQLAlchemyIntegration:

    def test_full_sqlalchemy_project(self, parser):
        """Test parsing a full SQLAlchemy project file."""
        content = """
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table, event
from sqlalchemy.orm import sessionmaker, relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property

engine = create_engine("postgresql://user:pass@localhost/mydb", pool_size=10, echo=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

user_roles = Table('user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('role_id', Integer, ForeignKey('roles.id')),
)

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    posts = relationship("Post", back_populates="author")

    @hybrid_property
    def display_name(self):
        return self.name.upper()

class Post(Base):
    __tablename__ = 'posts'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    author = relationship("User", back_populates="posts")

@event.listens_for(User, 'before_insert')
def set_defaults(mapper, connection, target):
    pass
"""
        result = parser.parse(content, "models.py")

        # Models
        assert result.total_models >= 2
        # Core tables
        assert result.total_tables >= 1
        # Engine
        assert len(result.engines) >= 1
        assert result.engines[0].url_pattern == "postgresql"
        # Sessions
        assert len(result.sessions) >= 1
        # Event listeners
        assert len(result.event_listeners) >= 1
        # Hybrid properties
        assert len(result.hybrid_properties) >= 1
        # Version
        assert result.sqlalchemy_version == "2.0"
        # File type
        assert result.file_type == "model"

        # Format
        output = parser.to_codetrellis_format(result)
        assert "SQLALCHEMY_ORM_MODELS" in output
        assert "SQLALCHEMY_ENGINES" in output
        assert "SQLALCHEMY_SESSIONS" in output
        assert "SQLALCHEMY_EVENTS" in output
        assert "SQLALCHEMY_HYBRID_PROPS" in output
