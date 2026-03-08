"""
KafkaExtractor - Extracts Kafka messaging components.

This extractor parses Python code using Kafka and extracts:
- Kafka producers
- Kafka consumers
- Topic configurations
- Consumer groups
- Schema registry usage
- Avro/JSON schema definitions

Part of CodeTrellis v2.0 - Python Data Engineering Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class KafkaProducerInfo:
    """Information about a Kafka producer."""
    name: str
    bootstrap_servers_env: Optional[str] = None
    topics: List[str] = field(default_factory=list)
    key_serializer: Optional[str] = None
    value_serializer: Optional[str] = None
    acks: Optional[str] = None  # 0, 1, all
    is_async: bool = False


@dataclass
class KafkaConsumerInfo:
    """Information about a Kafka consumer."""
    name: str
    topics: List[str] = field(default_factory=list)
    group_id: Optional[str] = None
    auto_offset_reset: Optional[str] = None  # earliest, latest
    key_deserializer: Optional[str] = None
    value_deserializer: Optional[str] = None
    is_async: bool = False


@dataclass
class KafkaTopicInfo:
    """Information about a Kafka topic."""
    name: str
    partitions: Optional[int] = None
    replication_factor: Optional[int] = None
    retention_ms: Optional[int] = None
    cleanup_policy: Optional[str] = None


@dataclass
class KafkaSchemaInfo:
    """Information about a schema used with Kafka."""
    name: str
    schema_type: str  # avro, json, protobuf
    subject: Optional[str] = None
    fields: List[str] = field(default_factory=list)


@dataclass
class KafkaStreamInfo:
    """Information about Kafka Streams usage (Faust)."""
    name: str
    input_topics: List[str] = field(default_factory=list)
    output_topics: List[str] = field(default_factory=list)
    processor_type: str = "stream"  # stream, table, agent


class KafkaExtractor:
    """
    Extracts Kafka-related components from Python source code.

    Handles:
    - kafka-python Producer/Consumer
    - aiokafka async Producer/Consumer
    - confluent-kafka clients
    - Faust streaming
    - Schema registry and Avro schemas
    """

    # kafka-python patterns
    KAFKA_PRODUCER_PATTERN = re.compile(
        r'(\w+)\s*=\s*(?:Aio)?KafkaProducer\s*\(',
        re.MULTILINE
    )

    KAFKA_CONSUMER_PATTERN = re.compile(
        r'(\w+)\s*=\s*(?:Aio)?KafkaConsumer\s*\(',
        re.MULTILINE
    )

    # confluent-kafka patterns
    CONFLUENT_PRODUCER_PATTERN = re.compile(
        r'(\w+)\s*=\s*(?:Producer|SerializingProducer)\s*\(',
        re.MULTILINE
    )

    CONFLUENT_CONSUMER_PATTERN = re.compile(
        r'(\w+)\s*=\s*(?:Consumer|DeserializingConsumer)\s*\(',
        re.MULTILINE
    )

    # Topic patterns
    TOPIC_SEND_PATTERN = re.compile(
        r'\.send\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    TOPIC_PRODUCE_PATTERN = re.compile(
        r'\.produce\s*\(\s*(?:topic\s*=\s*)?[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    TOPIC_SUBSCRIBE_PATTERN = re.compile(
        r'\.subscribe\s*\(\s*\[\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    # Consumer instantiation with topics
    CONSUMER_TOPICS_PATTERN = re.compile(
        r'KafkaConsumer\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    # Configuration patterns
    BOOTSTRAP_SERVERS_PATTERN = re.compile(
        r'bootstrap[_.]servers\s*[=:]\s*([^\n,)]+)',
        re.IGNORECASE
    )

    GROUP_ID_PATTERN = re.compile(
        r'group[_.]id\s*[=:]\s*[\'"]([^"\']+)[\'"]',
        re.IGNORECASE
    )

    # Faust patterns
    FAUST_APP_PATTERN = re.compile(
        r'(\w+)\s*=\s*faust\.App\s*\(',
        re.MULTILINE
    )

    FAUST_AGENT_PATTERN = re.compile(
        r'@(\w+)\.agent\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    FAUST_TOPIC_PATTERN = re.compile(
        r'(\w+)\s*=\s*\w+\.topic\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    # Schema patterns
    AVRO_SCHEMA_PATTERN = re.compile(
        r'(\w+)\s*=\s*(?:avro\.)?(?:parse|schema\.Parse)\s*\(',
        re.MULTILINE
    )

    SCHEMA_REGISTRY_PATTERN = re.compile(
        r'SchemaRegistryClient\s*\(\s*\{\s*[\'"]url[\'"]\s*:\s*([^\}]+)',
        re.MULTILINE
    )

    # AdminClient for topic management
    ADMIN_CREATE_TOPIC_PATTERN = re.compile(
        r'NewTopic\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the Kafka extractor."""
        pass

    def extract(self, content: str) -> Dict[str, Any]:
        """
        Extract all Kafka components from Python content.

        Args:
            content: Python source code

        Returns:
            Dict with producers, consumers, topics, schemas, streams
        """
        producers = self._extract_producers(content)
        consumers = self._extract_consumers(content)
        topics = self._extract_topics(content)
        schemas = self._extract_schemas(content)
        streams = self._extract_streams(content)

        return {
            'producers': producers,
            'consumers': consumers,
            'topics': topics,
            'schemas': schemas,
            'streams': streams
        }

    def _extract_producers(self, content: str) -> List[KafkaProducerInfo]:
        """Extract Kafka producer configurations."""
        producers = []

        # kafka-python producers
        for match in self.KAFKA_PRODUCER_PATTERN.finditer(content):
            var_name = match.group(1)
            context = content[match.start():match.start()+500]

            is_async = 'Aio' in match.group(0)

            # Find topics this producer sends to
            topics = []
            for send_match in self.TOPIC_SEND_PATTERN.finditer(content):
                # Check if this send is related to this producer
                send_context = content[max(0, send_match.start()-50):send_match.start()]
                if var_name in send_context or 'producer' in send_context.lower():
                    topics.append(send_match.group(1))

            # Get bootstrap servers env
            bootstrap_env = None
            bs_match = self.BOOTSTRAP_SERVERS_PATTERN.search(context)
            if bs_match:
                bs_value = bs_match.group(1)
                env_match = re.search(r'os\.(?:environ|getenv)\s*\[[\'"](\w+)[\'"]', bs_value)
                if env_match:
                    bootstrap_env = env_match.group(1)

            producers.append(KafkaProducerInfo(
                name=var_name,
                bootstrap_servers_env=bootstrap_env,
                topics=list(set(topics)),
                is_async=is_async
            ))

        # confluent-kafka producers
        for match in self.CONFLUENT_PRODUCER_PATTERN.finditer(content):
            var_name = match.group(1)

            topics = []
            for prod_match in self.TOPIC_PRODUCE_PATTERN.finditer(content):
                context = content[max(0, prod_match.start()-50):prod_match.start()]
                if var_name in context:
                    topics.append(prod_match.group(1))

            producers.append(KafkaProducerInfo(
                name=var_name,
                topics=list(set(topics)),
                is_async=False
            ))

        return producers

    def _extract_consumers(self, content: str) -> List[KafkaConsumerInfo]:
        """Extract Kafka consumer configurations."""
        consumers = []

        # kafka-python consumers
        for match in self.KAFKA_CONSUMER_PATTERN.finditer(content):
            var_name = match.group(1)
            context = content[match.start():match.start()+500]

            is_async = 'Aio' in match.group(0)

            # Topics from constructor
            topics = []
            topics_match = self.CONSUMER_TOPICS_PATTERN.search(context)
            if topics_match:
                topics.append(topics_match.group(1))

            # Topics from subscribe
            for sub_match in self.TOPIC_SUBSCRIBE_PATTERN.finditer(content):
                topics.append(sub_match.group(1))

            # Group ID
            group_id = None
            gid_match = self.GROUP_ID_PATTERN.search(context)
            if gid_match:
                group_id = gid_match.group(1)

            # Auto offset reset
            auto_offset = None
            offset_match = re.search(r'auto_offset_reset\s*=\s*[\'"](\w+)[\'"]', context)
            if offset_match:
                auto_offset = offset_match.group(1)

            consumers.append(KafkaConsumerInfo(
                name=var_name,
                topics=list(set(topics)),
                group_id=group_id,
                auto_offset_reset=auto_offset,
                is_async=is_async
            ))

        # confluent-kafka consumers
        for match in self.CONFLUENT_CONSUMER_PATTERN.finditer(content):
            var_name = match.group(1)
            context = content[match.start():match.start()+500]

            group_id = None
            gid_match = re.search(r'[\'"]group\.id[\'"]\s*:\s*[\'"]([^"\']+)[\'"]', context)
            if gid_match:
                group_id = gid_match.group(1)

            consumers.append(KafkaConsumerInfo(
                name=var_name,
                group_id=group_id,
                topics=[]
            ))

        return consumers

    def _extract_topics(self, content: str) -> List[KafkaTopicInfo]:
        """Extract Kafka topic definitions."""
        topics = []
        seen = set()

        # From NewTopic (AdminClient)
        for match in self.ADMIN_CREATE_TOPIC_PATTERN.finditer(content):
            topic_name = match.group(1)
            context = content[match.start():match.start()+200]

            if topic_name not in seen:
                seen.add(topic_name)

                partitions = None
                part_match = re.search(r'num_partitions\s*=\s*(\d+)', context)
                if part_match:
                    partitions = int(part_match.group(1))

                replication = None
                rep_match = re.search(r'replication_factor\s*=\s*(\d+)', context)
                if rep_match:
                    replication = int(rep_match.group(1))

                topics.append(KafkaTopicInfo(
                    name=topic_name,
                    partitions=partitions,
                    replication_factor=replication
                ))

        # From Faust topics
        for match in self.FAUST_TOPIC_PATTERN.finditer(content):
            topic_name = match.group(2)
            if topic_name not in seen:
                seen.add(topic_name)
                topics.append(KafkaTopicInfo(name=topic_name))

        return topics

    def _extract_schemas(self, content: str) -> List[KafkaSchemaInfo]:
        """Extract schema definitions used with Kafka."""
        schemas = []

        # Avro schemas
        for match in self.AVRO_SCHEMA_PATTERN.finditer(content):
            var_name = match.group(1)
            schemas.append(KafkaSchemaInfo(
                name=var_name,
                schema_type="avro"
            ))

        # Check for schema registry usage
        sr_match = self.SCHEMA_REGISTRY_PATTERN.search(content)
        if sr_match:
            # Check for JSON schema
            if 'JSONSerializer' in content or 'JSONDeserializer' in content:
                schemas.append(KafkaSchemaInfo(
                    name="json_schema",
                    schema_type="json"
                ))

            # Check for Protobuf
            if 'ProtobufSerializer' in content or 'ProtobufDeserializer' in content:
                schemas.append(KafkaSchemaInfo(
                    name="protobuf_schema",
                    schema_type="protobuf"
                ))

        return schemas

    def _extract_streams(self, content: str) -> List[KafkaStreamInfo]:
        """Extract Faust stream processing definitions."""
        streams = []

        # Faust agents
        for match in self.FAUST_AGENT_PATTERN.finditer(content):
            app_var = match.group(1)
            input_topic = match.group(2)

            streams.append(KafkaStreamInfo(
                name=f"agent_{input_topic}",
                input_topics=[input_topic],
                processor_type="agent"
            ))

        return streams

    def to_codetrellis_format(self, result: Dict[str, Any]) -> str:
        """Convert extracted Kafka data to CodeTrellis format."""
        lines = []

        # Producers
        producers = result.get('producers', [])
        if producers:
            lines.append("[KAFKA_PRODUCERS]")
            for prod in producers:
                parts = [prod.name]
                if prod.is_async:
                    parts.append("async")
                if prod.topics:
                    parts.append(f"topics:[{','.join(prod.topics[:5])}]")
                if prod.bootstrap_servers_env:
                    parts.append(f"bootstrap_env:{prod.bootstrap_servers_env}")
                lines.append("|".join(parts))
            lines.append("")

        # Consumers
        consumers = result.get('consumers', [])
        if consumers:
            lines.append("[KAFKA_CONSUMERS]")
            for cons in consumers:
                parts = [cons.name]
                if cons.group_id:
                    parts.append(f"group:{cons.group_id}")
                if cons.topics:
                    parts.append(f"topics:[{','.join(cons.topics[:5])}]")
                if cons.auto_offset_reset:
                    parts.append(f"offset:{cons.auto_offset_reset}")
                if cons.is_async:
                    parts.append("async")
                lines.append("|".join(parts))
            lines.append("")

        # Topics
        topics = result.get('topics', [])
        if topics:
            lines.append("[KAFKA_TOPICS]")
            for topic in topics:
                parts = [topic.name]
                if topic.partitions:
                    parts.append(f"partitions:{topic.partitions}")
                if topic.replication_factor:
                    parts.append(f"replication:{topic.replication_factor}")
                lines.append("|".join(parts))
            lines.append("")

        # Schemas
        schemas = result.get('schemas', [])
        if schemas:
            lines.append("[KAFKA_SCHEMAS]")
            for schema in schemas:
                lines.append(f"{schema.name}|type:{schema.schema_type}")
            lines.append("")

        # Streams
        streams = result.get('streams', [])
        if streams:
            lines.append("[KAFKA_STREAMS]")
            for stream in streams:
                parts = [stream.name, f"type:{stream.processor_type}"]
                if stream.input_topics:
                    parts.append(f"in:[{','.join(stream.input_topics)}]")
                if stream.output_topics:
                    parts.append(f"out:[{','.join(stream.output_topics)}]")
                lines.append("|".join(parts))

        return "\n".join(lines)


# Convenience function
def extract_kafka(content: str) -> Dict[str, Any]:
    """Extract Kafka components from Python content."""
    extractor = KafkaExtractor()
    return extractor.extract(content)
