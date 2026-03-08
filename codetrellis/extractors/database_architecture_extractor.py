"""
CodeTrellis Database Architecture Extractor — Phase 5 of v5.0 Universal Scanner
==================================================================================

Extracts database-related patterns from source code:
- Database type detection (PostgreSQL, MySQL, MongoDB, SQLite, Redis, etc.)
- ORM / query builder detection (GORM, SQLAlchemy, Prisma, TypeORM, etc.)
- Migration patterns
- Schema/model definitions from ORM code
- Connection pool configuration
- Database access patterns (repository, DAO, direct queries)

Language-agnostic with enhanced Go, Python, TypeScript/JS support.

Part of CodeTrellis v5.0 — Universal Scanner
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from codetrellis.file_classifier import FileClassifier, GitignoreFilter


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class DatabaseInfo:
    """A detected database system."""
    db_type: str             # "postgresql", "mysql", "mongodb", "sqlite", "redis", etc.
    orm: Optional[str] = None  # "gorm", "sqlalchemy", "prisma", "typeorm", etc.
    evidence_files: List[str] = field(default_factory=list)
    connection_env_var: Optional[str] = None  # e.g. "DATABASE_URL"
    sub_project: Optional[str] = None  # Phase 3: which sub-project this belongs to

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "db_type": self.db_type,
            "orm": self.orm,
            "evidence_files": self.evidence_files[:5],
            "connection_env_var": self.connection_env_var,
        }
        if self.sub_project:
            d["sub_project"] = self.sub_project
        return d


@dataclass
class DatabaseModel:
    """A database model/table detected from ORM code."""
    name: str
    source_file: str = ""
    fields: List[Dict[str, str]] = field(default_factory=list)
    orm: str = ""
    table_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "source_file": self.source_file,
            "fields": self.fields[:20],
            "orm": self.orm,
            "table_name": self.table_name,
        }


@dataclass
class MigrationInfo:
    """Migration framework detection."""
    framework: str           # "alembic", "goose", "prisma-migrate", "typeorm", "knex", "flyway"
    migration_dir: Optional[str] = None
    migration_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "framework": self.framework,
            "migration_dir": self.migration_dir,
            "migration_count": self.migration_count,
        }


@dataclass
class DatabaseArchitectureResult:
    """Complete database architecture analysis."""
    databases: List[DatabaseInfo] = field(default_factory=list)
    models: List[DatabaseModel] = field(default_factory=list)
    migrations: List[MigrationInfo] = field(default_factory=list)
    access_pattern: Optional[str] = None  # "repository", "dao", "active_record", "direct"
    message_queues: List[str] = field(default_factory=list)  # "rabbitmq", "kafka", "sqs", etc.

    def to_dict(self) -> Dict[str, Any]:
        return {
            "databases": [d.to_dict() for d in self.databases],
            "models": [m.to_dict() for m in self.models],
            "migrations": [m.to_dict() for m in self.migrations],
            "access_pattern": self.access_pattern,
            "message_queues": self.message_queues,
        }

    def to_codetrellis_format(self) -> str:
        """Convert to compact CodeTrellis format."""
        lines = []
        lines.append("# Database Architecture")

        # Databases
        if self.databases:
            for db in self.databases:
                orm_str = f" via {db.orm}" if db.orm else ""
                env_str = f" (env: {db.connection_env_var})" if db.connection_env_var else ""
                sub_str = f" [{db.sub_project}]" if db.sub_project else ""
                lines.append(f"db: {db.db_type}{orm_str}{env_str}{sub_str}")
        else:
            lines.append("db: NONE DETECTED")

        # Access pattern
        if self.access_pattern:
            lines.append(f"pattern: {self.access_pattern}")

        # Models
        if self.models:
            lines.append(f"## Models ({len(self.models)})")
            for model in self.models[:20]:
                field_str = ', '.join(
                    f"{f['name']}:{f.get('type', '?')}" for f in model.fields[:8]
                )
                more = f",+{len(model.fields) - 8}" if len(model.fields) > 8 else ""
                table = f" -> {model.table_name}" if model.table_name else ""
                lines.append(f"  {model.name}{table}: {field_str}{more}")

        # Migrations
        if self.migrations:
            for mig in self.migrations:
                lines.append(f"migrations: {mig.framework} ({mig.migration_count} files)")

        # Message queues
        if self.message_queues:
            lines.append(f"message_queues: {', '.join(sorted(self.message_queues))}")

        return '\n'.join(lines)


# =============================================================================
# Phase 3 — Improvement 6: ORM-DB Affinity Graph
# =============================================================================

@dataclass
class ORMEvidence:
    """
    Evidence of an ORM detection with provenance.
    Instead of flat orm_name→files, we track WHERE each ORM was found
    and what DB it's associated with, enabling per-sub-project attribution.
    """
    orm: str                           # e.g., "prisma", "django_orm"
    db_type: Optional[str] = None      # From ORM_DETECTION assoc_db or inferred
    file_path: str = ""                # First evidence file
    sub_project: Optional[str] = None  # Which sub-project directory
    confidence: float = 1.0            # Detection confidence (from multi-signal)
    all_files: List[str] = field(default_factory=list)  # All evidence files


# =============================================================================
# Detection Patterns
# =============================================================================

# Database type detection: (pattern, db_type)
# Legacy flat list — used by model extraction and backwards-compat paths.
DB_TYPE_PATTERNS = [
    (re.compile(r'postgres|pgx|pq|psycopg|asyncpg|pg-promise|lib/pq', re.I), 'postgresql'),
    (re.compile(r'mysql|go-sql-driver/mysql|PyMySQL|mysqlclient', re.I), 'mysql'),
    (re.compile(r'mongodb|mongo-go-driver|pymongo|mongoose|mongoclient', re.I), 'mongodb'),
    (re.compile(r'sqlite|mattn/go-sqlite3|sqlite3', re.I), 'sqlite'),
    (re.compile(r'redis|go-redis|aioredis|ioredis|redis-py', re.I), 'redis'),
    (re.compile(r'elasticsearch|opensearch|olivere/elastic', re.I), 'elasticsearch'),
    (re.compile(r'cassandra|gocql|datastax', re.I), 'cassandra'),
    (re.compile(r'dynamodb|aws-sdk.*dynamodb', re.I), 'dynamodb'),
    (re.compile(r'clickhouse', re.I), 'clickhouse'),
    (re.compile(r'cockroachdb/cockroach|cockroach_dsn|COCKROACH_DB|COCKROACH_HOST', re.I), 'cockroachdb'),
    (re.compile(r'neo4j', re.I), 'neo4j'),
    (re.compile(r'firestore|firebase.*database', re.I), 'firestore'),
]

# =============================================================================
# Multi-Signal DB Detection (Phase 2 — Improvement 3)
# =============================================================================
# Same tiered approach as ORM_DETECTION:
#   strong (1 hit = confirmed), medium (2+ = confirmed), anti (file rejection)
# Prevents false positives like `cockroachdb/errors` being treated as CockroachDB usage.

DB_DETECTION: Dict[str, Dict] = {
    'postgresql': {
        'strong': [r'psycopg[23]', r'asyncpg', r'pg-promise', r'lib/pq', r'DATABASE_URL.*postgres'],
        'medium': [r'postgres', r'pgx', r'pq\.Open\(', r'PostgreSQL'],
        'weak':   [r'pg', r'sql'],
        'anti':   [],
    },
    'mysql': {
        'strong': [r'go-sql-driver/mysql', r'PyMySQL', r'mysqlclient', r'mysql2'],
        'medium': [r'mysql', r'MySQL', r'MariaDB'],
        'weak':   [],
        'anti':   [],
    },
    'mongodb': {
        'strong': [r'mongo-go-driver', r'pymongo', r'mongoose\.connect', r'MongoClient\('],
        'medium': [r'mongodb', r'mongoclient', r'mongoose'],
        'weak':   [r'mongo'],
        'anti':   [],
    },
    'sqlite': {
        'strong': [r'mattn/go-sqlite3', r'sqlite3\.connect', r'better-sqlite3'],
        'medium': [r'sqlite', r'sqlite3', r'SQLite'],
        'weak':   [],
        'anti':   [],
    },
    'redis': {
        'strong': [r'go-redis', r'aioredis', r'ioredis', r'redis-py', r'@upstash/redis', r'RedisClient\('],
        'medium': [r'redis', r'Redis', r'REDIS_URL'],
        'weak':   [],
        'anti':   [],
    },
    'elasticsearch': {
        'strong': [r'olivere/elastic', r'elasticsearch-py', r'@elastic/elasticsearch'],
        'medium': [r'elasticsearch', r'opensearch', r'ElasticSearch'],
        'weak':   [],
        'anti':   [],
    },
    'cassandra': {
        'strong': [r'gocql', r'datastax.*cassandra', r'cassandra-driver'],
        'medium': [r'cassandra', r'Cassandra'],
        'weak':   [],
        'anti':   [],
    },
    'dynamodb': {
        'strong': [r'aws-sdk.*dynamodb', r'DynamoDBClient\(', r'boto3.*dynamodb'],
        'medium': [r'dynamodb', r'DynamoDB'],
        'weak':   [],
        'anti':   [],
    },
    'clickhouse': {
        'strong': [r'clickhouse-go', r'clickhouse-driver', r'ClickHouse\('],
        'medium': [r'clickhouse', r'ClickHouse'],
        'weak':   [],
        'anti':   [],
    },
    'cockroachdb': {
        # cockroachdb/errors is NOT a DB usage — it's an error handling library.
        # Only strong signals (actual connection/DSN references) confirm CockroachDB.
        'strong': [r'cockroach_dsn', r'COCKROACH_DB', r'COCKROACH_HOST', r'cockroachdb.*dialect'],
        'medium': [r'cockroachdb/cockroach', r'cockroach'],
        'weak':   [],
        'anti':   [],
    },
    'neo4j': {
        'strong': [r'neo4j-go-driver', r'neo4j\.GraphDatabase', r'from\s+neo4j\s+import'],
        'medium': [r'neo4j', r'Neo4j'],
        'weak':   [],
        'anti':   [],
    },
    'firestore': {
        'strong': [r'firebase.*firestore', r'cloud\.google.*firestore', r'FirestoreClient'],
        'medium': [r'firestore', r'firebase.*database'],
        'weak':   [],
        'anti':   [],
    },
}

# =============================================================================
# Multi-Signal ORM Detection (Phase 2 — Improvement 3)
# =============================================================================
# Instead of single-regex = confirmed, we use tiered signals:
#   strong: 1 hit = confirmed (e.g., import statement, decorator with args)
#   medium: 2+ hits = confirmed (e.g., generic class name + config reference)
#   weak:   ignored alone (e.g., "Repository", "Entity" — too generic)
#   anti:   file extension patterns that reject this ORM immediately
#   assoc_db: associated database type (if known)
#
# Inspired by Linguist's progressive-narrowing + Bayesian fallback strategy.

ORM_DETECTION: Dict[str, Dict] = {
    'gorm': {
        'strong': [r'gorm\.io/gorm', r'gorm\.Model', r'gorm\.Open\(', r'gorm\.DB'],
        'medium': [r'AutoMigrate\(', r'gorm:"', r'GORM'],
        'weak':   [],
        'anti':   [r'\.py$', r'\.ts$', r'\.js$', r'\.rs$'],
        'assoc_db': 'postgresql',
    },
    'sqlalchemy': {
        'strong': [r'from\s+sqlalchemy', r'import\s+sqlalchemy', r'declarative_base\(\)', r'mapped_column\('],
        'medium': [r'SQLAlchemy', r'sessionmaker', r'create_engine\(', r'Column\('],
        'weak':   [r'Base', r'Session', r'engine'],
        'anti':   [r'\.go$', r'\.ts$', r'\.js$', r'\.rs$'],
        'assoc_db': None,
    },
    'django_orm': {
        'strong': [r'from\s+django\.db\s+import\s+models', r'models\.CharField\(', r'models\.ForeignKey\('],
        'medium': [r'models\.Model', r'django\.db', r'models\.IntegerField\(', r'models\.TextField\('],
        'weak':   [r'makemigrations', r'migrate'],
        'anti':   [r'\.go$', r'\.ts$', r'\.js$', r'\.rs$'],
        'assoc_db': None,
    },
    'tortoise': {
        'strong': [r'tortoise-orm', r'from\s+tortoise\.models', r'tortoise\.fields'],
        'medium': [r'tortoise', r'Tortoise\.init'],
        'weak':   [],
        'anti':   [r'\.go$', r'\.ts$', r'\.js$', r'\.rs$'],
        'assoc_db': None,
    },
    'peewee': {
        'strong': [r'from\s+peewee\s+import', r'peewee\.Model', r'peewee\.SqliteDatabase'],
        'medium': [r'peewee', r'CharField\(', r'IntegerField\('],
        'weak':   [],
        'anti':   [r'\.go$', r'\.ts$', r'\.js$', r'\.rs$'],
        'assoc_db': None,
    },
    'prisma': {
        'strong': [r'@prisma/client', r'PrismaClient', r'prisma\.\$connect'],
        'medium': [r'prisma\.schema', r'prisma', r'PrismaModule'],
        'weak':   [r'model\s+\w+\s*\{'],
        'anti':   [r'\.go$', r'\.py$', r'\.rs$'],
        'assoc_db': None,
    },
    'typeorm': {
        'strong': [r'TypeOrmModule', r'createConnection.*typeorm', r'@Entity\(\).*@Column\(\)'],
        'medium': [r'getRepository\(', r'@PrimaryGeneratedColumn', r'typeorm', r'TypeORM'],
        'weak':   [r'Repository', r'Entity', r'Column'],
        'anti':   [r'\.go$', r'\.py$', r'\.rs$'],
        'assoc_db': None,
    },
    'sequelize': {
        'strong': [r'new\s+Sequelize\(', r'sequelize\.define\(', r'from\s+.sequelize.'],
        'medium': [r'Sequelize', r'sequelize'],
        'weak':   [r'DataTypes'],
        'anti':   [r'\.go$', r'\.py$', r'\.rs$'],
        'assoc_db': None,
    },
    'knex': {
        'strong': [r'require\(.knex.\)', r'knex\.migrate', r'knex\('],
        'medium': [r'knex', r'Knex'],
        'weak':   [],
        'anti':   [r'\.go$', r'\.py$', r'\.rs$'],
        'assoc_db': None,
    },
    'drizzle': {
        'strong': [r'drizzle-orm', r'from\s+.drizzle-orm.', r'drizzle\('],
        'medium': [r'drizzle', r'pgTable\(', r'sqliteTable\('],
        'weak':   [],
        'anti':   [r'\.go$', r'\.py$', r'\.rs$'],
        'assoc_db': None,
    },
    'mongoose': {
        'strong': [r'mongoose\.model\(', r'mongoose\.connect\(', r'mongoose\.Schema\('],
        'medium': [r'mongoose', r'Schema\(\{'],
        'weak':   [r'schema', r'model'],
        'anti':   [r'\.go$', r'\.py$', r'\.rs$'],
        'assoc_db': 'mongodb',
    },
    'ent': {
        'strong': [r'ent\.Schema', r'entgo\.io', r'ent\.Fields\('],
        'medium': [r'ent\.Mixin', r'ent\.Edge'],
        'weak':   [],
        'anti':   [r'\.py$', r'\.ts$', r'\.js$', r'\.rs$'],
        'assoc_db': None,
    },
    'sqlx': {
        'strong': [r'jmoiron/sqlx', r'sqlx\.Connect\(', r'sqlx\.DB'],
        'medium': [r'sqlx', r'sqlx\.Named'],
        'weak':   [],
        'anti':   [r'\.py$', r'\.ts$', r'\.js$'],
        'assoc_db': None,
    },
    'sqlc': {
        'strong': [r'sqlc\.yaml', r'sqlc\.json', r'sqlc generate'],
        'medium': [r'sqlc', r'-- name:.*:one'],
        'weak':   [],
        'anti':   [r'\.py$', r'\.ts$', r'\.js$', r'\.rs$'],
        'assoc_db': None,
    },
    'diesel': {
        'strong': [r'diesel\.rs', r'diesel::prelude', r'diesel::RunQueryDsl'],
        'medium': [r'diesel', r'#\[derive\(.*Queryable'],
        'weak':   [],
        'anti':   [r'\.py$', r'\.ts$', r'\.js$', r'\.go$'],
        'assoc_db': None,
    },
    'sea_orm': {
        'strong': [r'sea-orm', r'sea_orm::entity', r'sea_orm::prelude'],
        'medium': [r'sea_orm', r'DeriveEntityModel'],
        'weak':   [],
        'anti':   [r'\.py$', r'\.ts$', r'\.js$', r'\.go$'],
        'assoc_db': None,
    },
    'active_record': {
        'strong': [r'ActiveRecord::Base', r'ActiveRecord::Migration', r'ApplicationRecord'],
        'medium': [r'ActiveRecord', r'active_record', r'has_many\s+:'],
        'weak':   [r'belongs_to', r'validates'],
        'anti':   [r'\.go$', r'\.ts$', r'\.js$', r'\.rs$'],
        'assoc_db': None,
    },
    'pgx': {
        'strong': [r'jackc/pgx', r'pgx\.Connect\(', r'pgxpool\.New\('],
        'medium': [r'pgxpool', r'pgx\.Conn'],
        'weak':   [r'pgx'],
        'anti':   [r'\.py$', r'\.ts$', r'\.js$', r'\.rs$'],
        'assoc_db': 'postgresql',
    },
    'kysely': {
        'strong': [r'from\s+.kysely.', r'new\s+Kysely\(', r'Kysely<'],
        'medium': [r'kysely', r'Kysely'],
        'weak':   [],
        'anti':   [r'\.go$', r'\.py$', r'\.rs$'],
        'assoc_db': None,
    },
}

# Legacy flat list for backward compatibility (derived from ORM_DETECTION)
# Used by callers that still expect (pattern, orm_name, assoc_db) tuples.
ORM_PATTERNS = [
    (re.compile('|'.join(signals['strong'] + signals['medium']), re.I), orm_name, signals.get('assoc_db'))
    for orm_name, signals in ORM_DETECTION.items()
]

# Migration framework detection: (pattern, framework_name)
MIGRATION_PATTERNS = [
    (re.compile(r'alembic', re.I), 'alembic'),
    (re.compile(r'goose|pressly/goose', re.I), 'goose'),
    (re.compile(r'golang-migrate|migrate\.Up', re.I), 'golang-migrate'),
    (re.compile(r'prisma.*migrate|npx prisma migrate', re.I), 'prisma-migrate'),
    (re.compile(r'typeorm.*migration|MigrationInterface', re.I), 'typeorm'),
    (re.compile(r'knex.*migrate|exports\.up', re.I), 'knex'),
    (re.compile(r'flyway', re.I), 'flyway'),
    (re.compile(r'liquibase', re.I), 'liquibase'),
    (re.compile(r'django.*migrate|makemigrations', re.I), 'django'),
    (re.compile(r'dbmate', re.I), 'dbmate'),
]

# Migration directory patterns
MIGRATION_DIRS = {
    'migrations', 'migration', 'db/migrations', 'db/migrate',
    'alembic/versions', 'prisma/migrations',
}

# Access pattern detection
ACCESS_PATTERNS = [
    (re.compile(r'Repository|repository|RepositoryInterface', re.I), 'repository'),
    (re.compile(r'DAO|DataAccessObject|dao\.', re.I), 'dao'),
    (re.compile(r'ActiveRecord|active_record', re.I), 'active_record'),
]

# Connection env var patterns
CONN_ENV_PATTERNS = [
    re.compile(r'(?:DATABASE_URL|DB_URL|MONGO_URI|MONGODB_URI|REDIS_URL|'
               r'POSTGRES_DSN|MYSQL_DSN|DB_HOST|DB_CONNECTION_STRING)'),
]

# GORM model field patterns (Go)
GORM_FIELD_PATTERN = re.compile(
    r'(\w+)\s+(\S+)\s+`[^`]*gorm:"([^"]*)"[^`]*`'
)

# Message queue detection: (pattern, queue_type)
# Legacy flat list — kept for backwards compatibility.
MESSAGE_QUEUE_PATTERNS = [
    (re.compile(r'rabbitmq|amqp091|amqp\.Dial|amqplib', re.I), 'rabbitmq'),
    (re.compile(r'kafka|confluent-kafka|sarama|segmentio/kafka|kafkajs', re.I), 'kafka'),
    (re.compile(r'nats\.go|nats-io|nats\.connect', re.I), 'nats'),
    (re.compile(r'celery|kombu', re.I), 'celery'),
    (re.compile(r'bullmq|bull\.', re.I), 'bullmq'),
    (re.compile(r'aws.*sqs|sqs\.SendMessage|SQSClient', re.I), 'sqs'),
    (re.compile(r'google.*pubsub|cloud\.google.*pubsub|PubSubClient', re.I), 'google_pubsub'),
    (re.compile(r'azure.*servicebus|ServiceBusClient', re.I), 'azure_servicebus'),
    (re.compile(r'pulsar-client|apache.*pulsar', re.I), 'pulsar'),
    (re.compile(r'zeromq|zmq\.', re.I), 'zeromq'),
]

# =============================================================================
# Multi-Signal MQ Detection (Phase 2 — Improvement 3)
# =============================================================================

MQ_DETECTION: Dict[str, Dict] = {
    'rabbitmq': {
        'strong': [r'amqp091', r'amqp\.Dial\(', r'amqplib', r'amqp://'],
        'medium': [r'rabbitmq', r'RabbitMQ', r'amqp'],
        'weak':   [r'queue', r'exchange'],
        'anti':   [],
    },
    'kafka': {
        'strong': [r'confluent-kafka', r'sarama', r'segmentio/kafka', r'kafkajs', r'KafkaClient\('],
        'medium': [r'kafka', r'Kafka', r'KafkaProducer', r'KafkaConsumer'],
        'weak':   [r'topic', r'partition', r'broker'],
        'anti':   [],
    },
    'nats': {
        'strong': [r'nats\.go', r'nats-io', r'nats\.connect\(', r'nats://'],
        'medium': [r'nats', r'NATS', r'JetStream'],
        'weak':   [],
        'anti':   [],
    },
    'celery': {
        'strong': [r'from\s+celery\s+import', r'celery\.task', r'@shared_task', r'Celery\('],
        'medium': [r'celery', r'kombu', r'CELERY_BROKER'],
        'weak':   [r'task', r'worker'],
        'anti':   [r'\.go$', r'\.ts$', r'\.js$'],
    },
    'bullmq': {
        'strong': [r'from\s+.bullmq.', r'new\s+Queue\(.*bullmq', r'BullModule'],
        'medium': [r'bullmq', r'bull\.process'],
        'weak':   [r'Queue', r'Worker'],
        'anti':   [r'\.go$', r'\.py$'],
    },
    'sqs': {
        'strong': [r'sqs\.SendMessage', r'SQSClient\(', r'aws.*sqs.*send'],
        'medium': [r'aws.*sqs', r'SQS', r'sqs_queue'],
        'weak':   [r'queue'],
        'anti':   [],
    },
    'google_pubsub': {
        'strong': [r'cloud\.google.*pubsub', r'PubSubClient\(', r'pubsub\.NewClient\('],
        'medium': [r'google.*pubsub', r'PubSub'],
        'weak':   [r'topic', r'subscription'],
        'anti':   [],
    },
    'azure_servicebus': {
        'strong': [r'ServiceBusClient\(', r'azure.*servicebus', r'ServiceBusSender'],
        'medium': [r'servicebus', r'ServiceBus'],
        'weak':   [],
        'anti':   [],
    },
    'pulsar': {
        'strong': [r'pulsar-client', r'apache.*pulsar', r'pulsar\.Client\('],
        'medium': [r'pulsar', r'Pulsar'],
        'weak':   [],
        'anti':   [],
    },
    'zeromq': {
        'strong': [r'zmq\.Context\(', r'pyzmq', r'zeromq'],
        'medium': [r'zmq\.', r'ZeroMQ', r'zeromq'],
        'weak':   [],
        'anti':   [],
    },
}

# SQLAlchemy/Django field patterns (Python)
PY_ORM_FIELD_PATTERN = re.compile(
    r'(\w+)\s*=\s*(?:Column|mapped_column|models\.)\s*\(\s*(\w+)'
)


# =============================================================================
# Multi-Signal Detection Helpers (Phase 2 — Improvement 3)
# =============================================================================

def detect_orms_multi_signal(
    file_path: str, content: str
) -> List[Tuple[str, Optional[str]]]:
    """
    Detect ORMs using multi-signal tiered matching.

    Returns list of (orm_name, assoc_db) tuples for confirmed detections.
    Requires:
      - 1+ strong signal hit, OR
      - 2+ medium signal hits
    Anti-patterns (file extension mismatches) reject immediately.
    """
    results: List[Tuple[str, Optional[str]]] = []

    for orm_name, signals in ORM_DETECTION.items():
        # Anti-patterns: skip if file extension doesn't match this ORM's language
        anti_patterns = signals.get('anti', [])
        if any(re.search(p, file_path) for p in anti_patterns):
            continue

        # Count strong hits
        strong_hits = sum(
            1 for p in signals.get('strong', [])
            if re.search(p, content, re.I)
        )
        if strong_hits >= 1:
            results.append((orm_name, signals.get('assoc_db')))
            continue

        # Count medium hits
        medium_hits = sum(
            1 for p in signals.get('medium', [])
            if re.search(p, content, re.I)
        )
        if medium_hits >= 2:
            results.append((orm_name, signals.get('assoc_db')))

    return results


def detect_dbs_multi_signal(
    file_path: str, content: str
) -> List[str]:
    """
    Detect database types using multi-signal tiered matching.

    Returns list of db_type strings for confirmed detections.
    Uses DB_DETECTION if available, falls back to DB_TYPE_PATTERNS.
    """
    results: List[str] = []

    for db_type, signals in DB_DETECTION.items():
        # Anti-patterns: skip if file extension doesn't match
        anti_patterns = signals.get('anti', [])
        if any(re.search(p, file_path) for p in anti_patterns):
            continue

        # Count strong hits
        strong_hits = sum(
            1 for p in signals.get('strong', [])
            if re.search(p, content, re.I)
        )
        if strong_hits >= 1:
            results.append(db_type)
            continue

        # Count medium hits
        medium_hits = sum(
            1 for p in signals.get('medium', [])
            if re.search(p, content, re.I)
        )
        if medium_hits >= 2:
            results.append(db_type)

    return results


def detect_mqs_multi_signal(
    file_path: str, content: str
) -> List[str]:
    """
    Detect message queues using multi-signal tiered matching.

    Returns list of queue_type strings for confirmed detections.
    Uses MQ_DETECTION if available, falls back to MESSAGE_QUEUE_PATTERNS.
    """
    results: List[str] = []

    for mq_type, signals in MQ_DETECTION.items():
        # Anti-patterns: skip if file extension doesn't match
        anti_patterns = signals.get('anti', [])
        if any(re.search(p, file_path) for p in anti_patterns):
            continue

        # Count strong hits
        strong_hits = sum(
            1 for p in signals.get('strong', [])
            if re.search(p, content, re.I)
        )
        if strong_hits >= 1:
            results.append(mq_type)
            continue

        # Count medium hits
        medium_hits = sum(
            1 for p in signals.get('medium', [])
            if re.search(p, content, re.I)
        )
        if medium_hits >= 2:
            results.append(mq_type)

    return results


# =============================================================================
# Database Architecture Extractor
# =============================================================================

class DatabaseArchitectureExtractor:
    """
    Extract database architecture from source code and config files.
    """

    IGNORE_DIRS = {
        'node_modules', '.git', 'dist', 'build', '__pycache__',
        'vendor', '.next', 'coverage', 'venv', '.venv',
    }

    # Directories whose content should be treated as examples, not app code (GAP-C4)
    # Now delegates to unified FileClassifier (Phase 1 systemic improvement).
    EXAMPLE_DIRS = FileClassifier.EXAMPLE_DIRS

    SOURCE_EXTENSIONS = {
        '.go', '.py', '.ts', '.js', '.tsx', '.jsx',
        '.java', '.kt', '.rs', '.rb',
        '.prisma', '.sql',
    }

    MANIFEST_FILES = {
        'package.json', 'go.mod', 'requirements.txt', 'pyproject.toml',
        'Cargo.toml', 'Gemfile', 'pom.xml', 'build.gradle',
    }

    def extract_from_directory(self, root_dir: Path,
                              discovery_result=None,
                              gitignore_filter: Optional[GitignoreFilter] = None,
                              ) -> Optional[DatabaseArchitectureResult]:
        """
        Scan project for database patterns.

        Phase 3 — Improvement 6: Uses ORMEvidence affinity graph for precise
        ORM-DB attribution with per-sub-project provenance.

        Args:
            root_dir: Root directory to scan
            discovery_result: Optional discovery result with sub_projects

        Returns:
            DatabaseArchitectureResult or None if nothing found
        """
        result = DatabaseArchitectureResult()
        db_evidence: Dict[str, Set[str]] = {}   # db_type → files
        orm_evidence_list: List[ORMEvidence] = []  # Phase 3: structured evidence
        orm_files: Dict[str, Set[str]] = {}   # orm_name → files (for model extraction compat)
        orm_db_map: Dict[str, Optional[str]] = {}  # orm_name → db_type

        # Phase 3: Build sub-project lookup from discovery result
        # Maps relative directory prefixes to sub-project names
        sub_project_map: Dict[str, str] = {}  # dir_prefix → sub_project_name
        if discovery_result:
            sub_projects = (
                discovery_result.get("sub_projects", [])
                if isinstance(discovery_result, dict)
                else [sp.to_dict() for sp in getattr(discovery_result, 'sub_projects', [])]
            )
            for sp in sub_projects:
                sp_path = sp.get("path", "") if isinstance(sp, dict) else ""
                sp_name = sp.get("name", "") or sp_path
                if sp_path:
                    sub_project_map[sp_path.rstrip('/')] = sp_name

        def _infer_sub_project(file_path_str: str) -> Optional[str]:
            """Infer which sub-project a file belongs to based on path prefix."""
            try:
                rel = str(Path(file_path_str).relative_to(root_dir))
            except ValueError:
                return None
            for prefix, name in sub_project_map.items():
                if rel.startswith(prefix):
                    return name
            return None

        gi = gitignore_filter

        for root, dirs, files in _walk_compat(root_dir):
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS
                       and not (gi and not gi.is_empty and gi.should_ignore(
                           os.path.relpath(os.path.join(str(root), d), str(root_dir)),
                           is_dir=True))]

            # GAP-C4: Track if we're inside an example/vendor/generated directory
            # Uses unified FileClassifier (Phase 1 systemic improvement)
            rel_path = str(root.relative_to(root_dir)) if root != root_dir else ''
            in_example_dir = FileClassifier.should_skip_for_detection(rel_path) if rel_path else False

            # Check for migration directories (skip example dirs)
            if not in_example_dir:
                for d in dirs:
                    if d.lower() in ('migrations', 'migration', 'migrate'):
                        mig_path = root / d
                        count = sum(1 for f in mig_path.iterdir()
                                    if f.is_file() and f.suffix in ('.sql', '.py', '.go', '.ts', '.js'))
                        if count > 0:
                            result.migrations.append(MigrationInfo(
                                framework='detected',
                                migration_dir=str(mig_path),
                                migration_count=count,
                            ))

            for f in files:
                fp = root / f
                ext = fp.suffix.lower()
                name = fp.name.lower()

                if ext not in self.SOURCE_EXTENSIONS and name not in self.MANIFEST_FILES:
                    continue

                try:
                    content = fp.read_text(encoding='utf-8')
                except (OSError, UnicodeDecodeError):
                    continue

                file_str = str(fp)

                # GAP-C4: Skip example/docs files for DB/ORM detection
                # to avoid false positives from tutorial code
                if not in_example_dir:
                    # Phase 2: Multi-signal DB detection (Improvement 3)
                    file_rel_path = str(fp.relative_to(root_dir)) if root_dir in fp.parents or fp.parent == root_dir else name
                    for db_type in detect_dbs_multi_signal(file_rel_path, content):
                        if db_type not in db_evidence:
                            db_evidence[db_type] = set()
                        db_evidence[db_type].add(file_str)

                    # Phase 2+3: Multi-signal ORM detection → ORMEvidence
                    for orm_name, assoc_db in detect_orms_multi_signal(file_rel_path, content):
                        sub_proj = _infer_sub_project(file_str)
                        orm_evidence_list.append(ORMEvidence(
                            orm=orm_name,
                            db_type=assoc_db,
                            file_path=file_str,
                            sub_project=sub_proj,
                            all_files=[file_str],
                        ))
                        # Maintain backwards-compat flat maps
                        if orm_name not in orm_files:
                            orm_files[orm_name] = set()
                        orm_files[orm_name].add(file_str)
                        if assoc_db:
                            orm_db_map[orm_name] = assoc_db

                # Detect migration frameworks
                for pattern, framework in MIGRATION_PATTERNS:
                    if pattern.search(content):
                        existing = [m for m in result.migrations if m.framework == framework]
                        if not existing:
                            result.migrations.append(MigrationInfo(framework=framework))

                # Detect access patterns
                for pattern, pattern_name in ACCESS_PATTERNS:
                    if pattern.search(content):
                        if not result.access_pattern:
                            result.access_pattern = pattern_name

                # Phase 2: Multi-signal MQ detection (Improvement 3)
                file_rel_path_mq = str(fp.relative_to(root_dir)) if root_dir in fp.parents or fp.parent == root_dir else name
                is_generated = FileClassifier.is_generated_file(file_rel_path_mq)
                if not in_example_dir and not is_generated:
                    for queue_type in detect_mqs_multi_signal(file_rel_path_mq, content):
                        if queue_type not in result.message_queues:
                            result.message_queues.append(queue_type)

                # Detect connection env vars
                conn_env = None
                for pattern in CONN_ENV_PATTERNS:
                    m = pattern.search(content)
                    if m:
                        conn_env = m.group(0)
                        break

                # Extract ORM models (skip example/docs directories)
                if not in_example_dir:
                    if ext == '.go':
                        self._extract_gorm_models(content, file_str, result)
                    elif ext == '.py':
                        self._extract_python_models(content, file_str, result)
                    elif ext == '.prisma':
                        self._extract_prisma_models(content, file_str, result)

        # =====================================================================
        # Phase 3 — Improvement 6: ORM-DB Affinity Graph Attribution
        # =====================================================================
        # Build evidence graph: group ORM evidence by (orm, sub_project) to
        # create precise ORM-DB associations with provenance.
        # Replaces the old 3-phase heuristic with relationship-aware logic.

        # Consolidate ORM evidence by (orm_name, sub_project)
        consolidated: Dict[Tuple[str, Optional[str]], ORMEvidence] = {}
        for ev in orm_evidence_list:
            key = (ev.orm, ev.sub_project)
            if key in consolidated:
                consolidated[key].all_files.append(ev.file_path)
            else:
                consolidated[key] = ORMEvidence(
                    orm=ev.orm,
                    db_type=ev.db_type,
                    file_path=ev.file_path,
                    sub_project=ev.sub_project,
                    all_files=[ev.file_path],
                )

        # For each ORM evidence, resolve DB type using affinity:
        # Priority 1: ORM has explicit assoc_db (e.g., mongoose→mongodb)
        # Priority 2: Co-located DB evidence (DB detected in same sub-project)
        # Priority 3: Any relational DB detected in the project
        relational_dbs = {'postgresql', 'mysql', 'sqlite', 'cockroachdb'}

        # Build per-sub-project DB evidence for co-location matching
        sub_project_dbs: Dict[Optional[str], Set[str]] = {}  # sub_project → {db_types}
        for db_type, files in db_evidence.items():
            for fpath in files:
                sp = _infer_sub_project(fpath)
                if sp not in sub_project_dbs:
                    sub_project_dbs[sp] = set()
                sub_project_dbs[sp].add(db_type)

        seen_pairs: Set[Tuple[str, str, Optional[str]]] = set()  # (orm, db, sub_project)
        seen_dbs: Set[str] = set()

        # Sort consolidated items by key to ensure determinism
        sorted_consolidated = sorted(consolidated.items(), key=lambda x: (x[0][0], x[0][1] or ""))

        for (orm_name, sub_proj), evidence in sorted_consolidated:
            db_type = evidence.db_type or orm_db_map.get(orm_name)

            if not db_type:
                # Try co-located DB: prefer relational DBs in the same sub-project
                co_located = sorted(list(sub_project_dbs.get(sub_proj, set())))
                for candidate in co_located:
                    if candidate in relational_dbs:
                        db_type = candidate
                        break
                # Fallback: any relational DB in the entire project
                if not db_type:
                    for candidate in sorted(list(db_evidence.keys())):
                        if candidate in relational_dbs:
                            db_type = candidate
                            break

            if db_type:
                triple = (orm_name, db_type, sub_proj)
                if triple not in seen_pairs:
                    seen_pairs.add(triple)
                    seen_dbs.add(db_type)
                    result.databases.append(DatabaseInfo(
                        db_type=db_type,
                        orm=orm_name,
                        evidence_files=sorted(evidence.all_files)[:5],
                        sub_project=sub_proj,
                    ))

        # Add remaining databases without ORM attribution
        # (redis via ioredis, elasticsearch via client, etc.)
        for db_type in sorted(list(db_evidence.keys())):
            files = db_evidence[db_type]
            if db_type not in seen_dbs:
                # Determine sub-project for standalone DBs
                sub_proj = None
                sorted_files = sorted(list(files))
                for fpath in sorted_files:
                    sp = _infer_sub_project(fpath)
                    if sp:
                        sub_proj = sp
                        break
                result.databases.append(DatabaseInfo(
                    db_type=db_type,
                    evidence_files=sorted_files[:5],
                    sub_project=sub_proj,
                ))

        return result if (result.databases or result.models or result.migrations or result.message_queues) else None

    def _extract_gorm_models(self, content: str, file_path: str, result: DatabaseArchitectureResult) -> None:
        """Extract GORM model structs."""
        # Find structs with gorm.Model embedded
        struct_pattern = re.compile(
            r'type\s+(\w+)\s+struct\s*\{([^}]+)\}', re.DOTALL
        )
        for m in struct_pattern.finditer(content):
            name = m.group(1)
            body = m.group(2)

            if 'gorm.Model' not in body and 'gorm:' not in body:
                continue

            fields = []
            for fm in GORM_FIELD_PATTERN.finditer(body):
                fields.append({
                    "name": fm.group(1),
                    "type": fm.group(2),
                    "gorm_tag": fm.group(3),
                })

            # Table name
            table_name = None
            table_match = re.search(
                rf'func\s*\(\s*\w*\s*\*?{name}\s*\)\s*TableName\s*\(\)\s*string\s*\{{\s*return\s*"(\w+)"',
                content
            )
            if table_match:
                table_name = table_match.group(1)

            result.models.append(DatabaseModel(
                name=name,
                source_file=file_path,
                fields=fields,
                orm='gorm',
                table_name=table_name,
            ))

    def _extract_python_models(self, content: str, file_path: str, result: DatabaseArchitectureResult) -> None:
        """Extract SQLAlchemy/Django model classes (not Pydantic/dataclass)."""
        # Match classes inheriting from known ORM base classes
        class_pattern = re.compile(
            r'class\s+(\w+)\s*\(([^)]+)\)\s*:', re.I
        )
        # Only these base classes indicate real ORM models
        ORM_BASES = {
            'models.model', 'db.model', 'base', 'declarativebase',
            'abstractuser', 'abstractbaseuser', 'model',
        }
        # Bases that should be EXCLUDED (Pydantic, generic "Base*" names)
        NON_ORM_BASES = {
            'basemodel', 'baseschema', 'basesettings', 'baseclient',
            'baserestclient', 'baseworkflow', 'baseclass', 'baseobject',
            'baseplugin', 'baseexception', 'baseexporter', 'baseinput',
            'baseoutput', 'basesource', 'baseprocessor', 'baseprovider',
            'baseservice', 'basehandler', 'basemixin', 'baseconfig',
            'baseparser', 'basemanager', 'io.iobase', 'iobase',
            'genericmodel', 'msgspecstruct',
        }
        for cm in class_pattern.finditer(content):
            name = cm.group(1)
            bases_str = cm.group(2)
            bases_lower = bases_str.lower().replace(' ', '')

            # Skip if any non-ORM base is present
            if any(nb in bases_lower for nb in NON_ORM_BASES):
                continue

            # Must have at least one known ORM base
            bases_parts = [b.strip().lower() for b in bases_str.split(',')]
            has_orm_base = any(
                b in ORM_BASES or b.endswith('.model') or b == 'base'
                for b in bases_parts
            )
            if not has_orm_base:
                continue

            # Find lines after class def that look like field definitions
            start = cm.end()
            rest = content[start:start + 2000]
            fields = []

            for fm in PY_ORM_FIELD_PATTERN.finditer(rest):
                fields.append({
                    "name": fm.group(1),
                    "type": fm.group(2),
                })

            # Table name
            table_name = None
            table_match = re.search(r'__tablename__\s*=\s*["\'](\w+)["\']', rest)
            if table_match:
                table_name = table_match.group(1)

            orm_type = 'django_orm' if 'models.' in content[:start] else 'sqlalchemy'

            result.models.append(DatabaseModel(
                name=name,
                source_file=file_path,
                fields=fields,
                orm=orm_type,
                table_name=table_name,
            ))

    def _extract_prisma_models(self, content: str, file_path: str, result: DatabaseArchitectureResult) -> None:
        """Extract Prisma schema models."""
        model_pattern = re.compile(
            r'model\s+(\w+)\s*\{([^}]+)\}', re.DOTALL
        )
        for m in model_pattern.finditer(content):
            name = m.group(1)
            body = m.group(2)
            fields = []

            for line in body.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith('//') or stripped.startswith('@@'):
                    continue
                parts = stripped.split()
                if len(parts) >= 2:
                    fields.append({
                        "name": parts[0],
                        "type": parts[1],
                    })

            result.models.append(DatabaseModel(
                name=name,
                source_file=file_path,
                fields=fields,
                orm='prisma',
            ))


# =============================================================================
# Compatibility helper
# =============================================================================

def _walk_compat(root: Path):
    """os.walk wrapper that yields (Path, dirs, files)."""
    import os
    for dirpath, dirs, files in os.walk(root):
        yield Path(dirpath), dirs, files
