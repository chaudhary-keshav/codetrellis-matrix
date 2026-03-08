"""
Database Extractors for Python.

This module provides extractors for various database and messaging systems:
- MongoDB (PyMongo, Motor, Beanie ODM)
- Vector Databases (Pinecone, ChromaDB, Qdrant, FAISS, Weaviate, Milvus)
- Redis (Caching, Pub/Sub, Data Structures, Streams)
- Kafka (Producers, Consumers, Streams, Schema Registry)

Part of CodeTrellis v2.0 - Python Data Engineering Support
"""

from .mongodb_extractor import MongoDBExtractor, extract_mongodb
from .vectordb_extractor import VectorDBExtractor, extract_vectordb
from .redis_extractor import RedisExtractor, extract_redis
from .kafka_extractor import KafkaExtractor, extract_kafka

__all__ = [
    # MongoDB
    'MongoDBExtractor',
    'extract_mongodb',

    # Vector Databases
    'VectorDBExtractor',
    'extract_vectordb',

    # Redis
    'RedisExtractor',
    'extract_redis',

    # Kafka
    'KafkaExtractor',
    'extract_kafka',
]
