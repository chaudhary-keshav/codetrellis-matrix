"""
Vert.x Data Extractor v1.0

Extracts Vert.x data access patterns: SQL clients, Mongo, Redis, reactive drivers.
Covers Vert.x 2.x through 4.x.

Part of CodeTrellis v4.95 - Vert.x Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class VertxSQLClientInfo:
    """A Vert.x SQL client usage."""
    client_type: str = ""  # pg, mysql, mssql, oracle, db2, jdbc
    variable_name: str = ""
    is_pool: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class VertxMongoClientInfo:
    """A Vert.x Mongo client usage."""
    variable_name: str = ""
    collection: str = ""
    operation: str = ""  # find, save, insert, update, delete, aggregate
    file: str = ""
    line_number: int = 0


@dataclass
class VertxRedisClientInfo:
    """A Vert.x Redis client usage."""
    variable_name: str = ""
    connection_string: str = ""
    file: str = ""
    line_number: int = 0


class VertxDataExtractor:
    """Extracts Vert.x data access patterns."""

    # SQL client creation: PgPool.pool(), MySQLPool.pool(), JDBCPool.pool()
    SQL_POOL_PATTERN = re.compile(
        r'(PgPool|MySQLPool|MSSQLPool|OraclePool|DB2Pool|JDBCPool)\s*\.\s*pool\s*\(',
        re.MULTILINE
    )

    # Reactive SQL client: PgConnectOptions, MySQLConnectOptions
    SQL_CONNECT_PATTERN = re.compile(
        r'(PgConnect|MySQLConnect|MSSQLConnect|OracleConnect|DB2Connect)Options',
        re.MULTILINE
    )

    # SQL operations: client.query("SELECT..."), client.preparedQuery("...")
    SQL_QUERY_PATTERN = re.compile(
        r'(\w+)\s*\.\s*(query|preparedQuery)\s*\(\s*"([^"]{1,200})"',
        re.MULTILINE
    )

    # Mongo client: MongoClient.create / MongoClient.createShared
    MONGO_CLIENT_PATTERN = re.compile(
        r'MongoClient\s*\.\s*(create|createShared)\s*\(',
        re.MULTILINE
    )

    # Mongo operations
    MONGO_OP_PATTERN = re.compile(
        r'(\w+)\s*\.\s*(find|findOne|save|insert|insertOne|updateCollection|removeDocuments|aggregate|createCollection)\s*\(\s*"([^"]+)"',
        re.MULTILINE
    )

    # Redis client
    REDIS_CLIENT_PATTERN = re.compile(
        r'Redis\s*\.\s*createClient\s*\(|RedisAPI\s*\.\s*api\s*\(',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Vert.x data access patterns."""
        result = {
            'sql_clients': [],
            'mongo_clients': [],
            'redis_clients': [],
        }

        if not content:
            return result

        # SQL pools
        for m in self.SQL_POOL_PATTERN.finditer(content):
            pool_type = m.group(1)
            line = content[:m.start()].count('\n') + 1
            client_map = {
                'PgPool': 'pg', 'MySQLPool': 'mysql', 'MSSQLPool': 'mssql',
                'OraclePool': 'oracle', 'DB2Pool': 'db2', 'JDBCPool': 'jdbc',
            }
            result['sql_clients'].append(VertxSQLClientInfo(
                client_type=client_map.get(pool_type, pool_type.lower()),
                is_pool=True,
                file=file_path,
                line_number=line,
            ))

        # Mongo clients
        for m in self.MONGO_CLIENT_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            result['mongo_clients'].append(VertxMongoClientInfo(
                file=file_path, line_number=line,
            ))

        # Mongo operations
        for m in self.MONGO_OP_PATTERN.finditer(content):
            operation = m.group(2)
            collection = m.group(3)
            line = content[:m.start()].count('\n') + 1
            result['mongo_clients'].append(VertxMongoClientInfo(
                variable_name=m.group(1),
                collection=collection,
                operation=operation,
                file=file_path,
                line_number=line,
            ))

        # Redis clients
        for m in self.REDIS_CLIENT_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            result['redis_clients'].append(VertxRedisClientInfo(
                file=file_path, line_number=line,
            ))

        return result
