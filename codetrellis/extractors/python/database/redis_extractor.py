"""
RedisExtractor - Extracts Redis components for caching and data structures.

This extractor parses Python code using Redis and extracts:
- Redis client configurations
- Cache operations (get/set)
- Pub/Sub channels
- Data structures (lists, sets, sorted sets, hashes)
- Redis streams
- Lua scripts

Part of CodeTrellis v2.0 - Python Data Engineering Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RedisClientInfo:
    """Information about a Redis client configuration."""
    name: str
    host_env: Optional[str] = None  # Environment variable for host
    port: Optional[int] = None
    db: Optional[int] = None
    is_async: bool = False
    is_cluster: bool = False
    password_env: Optional[str] = None


@dataclass
class RedisCacheInfo:
    """Information about Redis caching patterns."""
    key_pattern: str
    ttl: Optional[int] = None
    operation: str = "get/set"  # get, set, getex, setex
    serializer: Optional[str] = None  # json, pickle, msgpack


@dataclass
class RedisPubSubInfo:
    """Information about Redis Pub/Sub channels."""
    channel_pattern: str
    is_pattern: bool = False  # psubscribe vs subscribe
    handler_function: Optional[str] = None


@dataclass
class RedisDataStructureInfo:
    """Information about Redis data structure usage."""
    name: str
    structure_type: str  # list, set, sorted_set, hash, stream
    operations: List[str] = field(default_factory=list)


@dataclass
class RedisStreamInfo:
    """Information about Redis Streams usage."""
    stream_name: str
    consumer_group: Optional[str] = None
    operations: List[str] = field(default_factory=list)  # xadd, xread, xreadgroup


class RedisExtractor:
    """
    Extracts Redis-related components from Python source code.

    Handles:
    - Redis/aioredis client configurations
    - Caching patterns and TTLs
    - Pub/Sub channels and handlers
    - Data structure operations
    - Redis Streams
    - Lua script registrations
    """

    # Redis client patterns
    REDIS_CLIENT_PATTERN = re.compile(
        r'(\w+)\s*=\s*(?:aio)?[Rr]edis(?:\.from_url)?\s*\(',
        re.MULTILINE
    )

    REDIS_CLUSTER_PATTERN = re.compile(
        r'(\w+)\s*=\s*RedisCluster\s*\(',
        re.MULTILINE
    )

    # Cache operations
    CACHE_GET_PATTERN = re.compile(
        r'\.get\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    CACHE_SET_PATTERN = re.compile(
        r'\.set(?:ex)?\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    # TTL patterns
    TTL_PATTERN = re.compile(
        r'(?:ttl|ex|expire|timeout)\s*=\s*(\d+)',
        re.IGNORECASE
    )

    # Pub/Sub patterns
    SUBSCRIBE_PATTERN = re.compile(
        r'\.p?subscribe\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    PUBLISH_PATTERN = re.compile(
        r'\.publish\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    # List operations
    LIST_OPS_PATTERN = re.compile(
        r'\.(lpush|rpush|lpop|rpop|lrange|llen|lindex)\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    # Set operations
    SET_OPS_PATTERN = re.compile(
        r'\.(sadd|srem|smembers|sismember|scard|sunion|sinter)\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    # Sorted set operations
    ZSET_OPS_PATTERN = re.compile(
        r'\.(zadd|zrem|zrange|zrangebyscore|zscore|zcard)\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    # Hash operations
    HASH_OPS_PATTERN = re.compile(
        r'\.(hset|hget|hgetall|hdel|hexists|hkeys|hvals)\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    # Stream operations
    STREAM_OPS_PATTERN = re.compile(
        r'\.(xadd|xread|xreadgroup|xrange|xlen|xinfo)\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    # Consumer group
    CONSUMER_GROUP_PATTERN = re.compile(
        r'xgroup_create\s*\([^,]+,\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the Redis extractor."""
        pass

    def extract(self, content: str) -> Dict[str, Any]:
        """
        Extract all Redis components from Python content.

        Args:
            content: Python source code

        Returns:
            Dict with clients, caches, pubsub, data_structures, streams
        """
        clients = self._extract_clients(content)
        caches = self._extract_caches(content)
        pubsub = self._extract_pubsub(content)
        data_structures = self._extract_data_structures(content)
        streams = self._extract_streams(content)

        return {
            'clients': clients,
            'caches': caches,
            'pubsub': pubsub,
            'data_structures': data_structures,
            'streams': streams
        }

    def _extract_clients(self, content: str) -> List[RedisClientInfo]:
        """Extract Redis client configurations."""
        clients = []

        for match in self.REDIS_CLIENT_PATTERN.finditer(content):
            var_name = match.group(1)
            context = content[match.start():match.start()+300]

            is_async = 'aioredis' in context or 'aio' in match.group(0).lower()

            # Check for environment variable usage
            host_env = None
            env_match = re.search(r'host\s*=\s*os\.(?:environ|getenv)\s*\[[\'"](\w+)[\'"]', context)
            if env_match:
                host_env = env_match.group(1)

            # Check for password
            password_env = None
            pwd_match = re.search(r'password\s*=\s*os\.(?:environ|getenv)\s*\[[\'"](\w+)[\'"]', context)
            if pwd_match:
                password_env = pwd_match.group(1)

            # Check for db number
            db = None
            db_match = re.search(r'db\s*=\s*(\d+)', context)
            if db_match:
                db = int(db_match.group(1))

            clients.append(RedisClientInfo(
                name=var_name,
                host_env=host_env,
                is_async=is_async,
                password_env=password_env,
                db=db
            ))

        # Cluster clients
        for match in self.REDIS_CLUSTER_PATTERN.finditer(content):
            var_name = match.group(1)
            clients.append(RedisClientInfo(
                name=var_name,
                is_cluster=True
            ))

        return clients

    def _extract_caches(self, content: str) -> List[RedisCacheInfo]:
        """Extract caching patterns."""
        caches = []
        seen_patterns = set()

        # Get operations
        for match in self.CACHE_GET_PATTERN.finditer(content):
            key_pattern = match.group(1)
            if key_pattern not in seen_patterns:
                seen_patterns.add(key_pattern)
                caches.append(RedisCacheInfo(
                    key_pattern=key_pattern,
                    operation="get"
                ))

        # Set operations
        for match in self.CACHE_SET_PATTERN.finditer(content):
            key_pattern = match.group(1)
            context = content[match.start():match.start()+150]

            ttl = None
            ttl_match = self.TTL_PATTERN.search(context)
            if ttl_match:
                ttl = int(ttl_match.group(1))

            # Check if we already have this key from get
            existing = next((c for c in caches if c.key_pattern == key_pattern), None)
            if existing:
                existing.operation = "get/set"
                existing.ttl = ttl
            elif key_pattern not in seen_patterns:
                seen_patterns.add(key_pattern)
                caches.append(RedisCacheInfo(
                    key_pattern=key_pattern,
                    operation="set",
                    ttl=ttl
                ))

        return caches

    def _extract_pubsub(self, content: str) -> List[RedisPubSubInfo]:
        """Extract Pub/Sub channel patterns."""
        pubsub = []
        seen_channels = set()

        for match in self.SUBSCRIBE_PATTERN.finditer(content):
            channel = match.group(1)
            is_pattern = 'psubscribe' in match.group(0)

            if channel not in seen_channels:
                seen_channels.add(channel)
                pubsub.append(RedisPubSubInfo(
                    channel_pattern=channel,
                    is_pattern=is_pattern
                ))

        for match in self.PUBLISH_PATTERN.finditer(content):
            channel = match.group(1)
            if channel not in seen_channels:
                seen_channels.add(channel)
                pubsub.append(RedisPubSubInfo(
                    channel_pattern=channel,
                    is_pattern=False
                ))

        return pubsub

    def _extract_data_structures(self, content: str) -> List[RedisDataStructureInfo]:
        """Extract Redis data structure usage."""
        structures = {}

        # Lists
        for match in self.LIST_OPS_PATTERN.finditer(content):
            op = match.group(1)
            key = match.group(2)
            if key not in structures:
                structures[key] = RedisDataStructureInfo(
                    name=key,
                    structure_type="list",
                    operations=[]
                )
            if op not in structures[key].operations:
                structures[key].operations.append(op)

        # Sets
        for match in self.SET_OPS_PATTERN.finditer(content):
            op = match.group(1)
            key = match.group(2)
            if key not in structures:
                structures[key] = RedisDataStructureInfo(
                    name=key,
                    structure_type="set",
                    operations=[]
                )
            if op not in structures[key].operations:
                structures[key].operations.append(op)

        # Sorted sets
        for match in self.ZSET_OPS_PATTERN.finditer(content):
            op = match.group(1)
            key = match.group(2)
            if key not in structures:
                structures[key] = RedisDataStructureInfo(
                    name=key,
                    structure_type="sorted_set",
                    operations=[]
                )
            if op not in structures[key].operations:
                structures[key].operations.append(op)

        # Hashes
        for match in self.HASH_OPS_PATTERN.finditer(content):
            op = match.group(1)
            key = match.group(2)
            if key not in structures:
                structures[key] = RedisDataStructureInfo(
                    name=key,
                    structure_type="hash",
                    operations=[]
                )
            if op not in structures[key].operations:
                structures[key].operations.append(op)

        return list(structures.values())

    def _extract_streams(self, content: str) -> List[RedisStreamInfo]:
        """Extract Redis Streams usage."""
        streams = {}

        for match in self.STREAM_OPS_PATTERN.finditer(content):
            op = match.group(1)
            stream_name = match.group(2)

            if stream_name not in streams:
                streams[stream_name] = RedisStreamInfo(
                    stream_name=stream_name,
                    operations=[]
                )
            if op not in streams[stream_name].operations:
                streams[stream_name].operations.append(op)

        # Consumer groups
        for match in self.CONSUMER_GROUP_PATTERN.finditer(content):
            group_name = match.group(1)
            # Try to associate with a stream
            for stream in streams.values():
                if not stream.consumer_group:
                    stream.consumer_group = group_name
                    break

        return list(streams.values())

    def to_codetrellis_format(self, result: Dict[str, Any]) -> str:
        """Convert extracted Redis data to CodeTrellis format."""
        lines = []

        # Clients
        clients = result.get('clients', [])
        if clients:
            lines.append("[REDIS_CLIENTS]")
            for client in clients:
                parts = [client.name]
                if client.is_cluster:
                    parts.append("cluster")
                if client.is_async:
                    parts.append("async")
                if client.host_env:
                    parts.append(f"host_env:{client.host_env}")
                if client.db is not None:
                    parts.append(f"db:{client.db}")
                lines.append("|".join(parts))
            lines.append("")

        # Caches
        caches = result.get('caches', [])
        if caches:
            lines.append("[REDIS_CACHE_KEYS]")
            for cache in caches:
                parts = [cache.key_pattern, f"op:{cache.operation}"]
                if cache.ttl:
                    parts.append(f"ttl:{cache.ttl}s")
                lines.append("|".join(parts))
            lines.append("")

        # Pub/Sub
        pubsub = result.get('pubsub', [])
        if pubsub:
            lines.append("[REDIS_PUBSUB]")
            for ps in pubsub:
                pattern_marker = "*" if ps.is_pattern else ""
                lines.append(f"{ps.channel_pattern}{pattern_marker}")
            lines.append("")

        # Data structures
        data_structures = result.get('data_structures', [])
        if data_structures:
            lines.append("[REDIS_DATA_STRUCTURES]")
            for ds in data_structures:
                ops_str = ','.join(ds.operations[:5])
                lines.append(f"{ds.name}|type:{ds.structure_type}|ops:[{ops_str}]")
            lines.append("")

        # Streams
        streams = result.get('streams', [])
        if streams:
            lines.append("[REDIS_STREAMS]")
            for stream in streams:
                parts = [stream.stream_name]
                if stream.consumer_group:
                    parts.append(f"group:{stream.consumer_group}")
                ops_str = ','.join(stream.operations)
                parts.append(f"ops:[{ops_str}]")
                lines.append("|".join(parts))

        return "\n".join(lines)


# Convenience function
def extract_redis(content: str) -> Dict[str, Any]:
    """Extract Redis components from Python content."""
    extractor = RedisExtractor()
    return extractor.extract(content)
