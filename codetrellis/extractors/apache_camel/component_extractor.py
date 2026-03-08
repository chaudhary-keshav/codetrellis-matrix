"""
Apache Camel Component Extractor - Extracts component usage and data formats.

Extracts:
- Component URIs and their categories (messaging, file, http, cloud, database)
- Data format usage (JSON, XML, CSV, Avro, Protobuf, YAML)
- Type converters
- Component configuration properties
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class CamelComponentInfo:
    """Information about a Camel component."""
    name: str = ""
    category: str = ""  # messaging, file, http, database, cloud, timer, direct, seda
    uri_count: int = 0
    uris: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class CamelDataFormatInfo:
    """Information about a Camel data format."""
    format_name: str = ""  # json, xml, csv, avro, protobuf, yaml
    library: str = ""  # jackson, gson, jaxb, xstream, etc.
    marshal_count: int = 0
    unmarshal_count: int = 0
    line_number: int = 0


class CamelComponentExtractor:
    """Extracts Camel component usage and data format information."""

    # Component categories mapping
    COMPONENT_CATEGORIES = {
        # Messaging
        'jms': 'messaging', 'activemq': 'messaging', 'kafka': 'messaging',
        'amqp': 'messaging', 'rabbitmq': 'messaging', 'aws-sqs': 'messaging',
        'aws-sns': 'messaging', 'google-pubsub': 'messaging', 'azure-servicebus': 'messaging',
        'paho': 'messaging', 'mqtt': 'messaging', 'stomp': 'messaging',
        'nats': 'messaging',
        # File
        'file': 'file', 'ftp': 'file', 'sftp': 'file', 'ftps': 'file',
        'aws-s3': 'file', 'google-storage': 'file', 'minio': 'file',
        # HTTP
        'http': 'http', 'https': 'http', 'http4': 'http', 'netty-http': 'http',
        'jetty': 'http', 'undertow': 'http', 'servlet': 'http',
        'rest': 'http', 'rest-api': 'http', 'platform-http': 'http',
        'cxf': 'http', 'cxfrs': 'http',
        # Database
        'jdbc': 'database', 'sql': 'database', 'jpa': 'database',
        'mongodb': 'database', 'couchdb': 'database', 'cassandra': 'database',
        'elasticsearch': 'database', 'infinispan': 'database', 'redis': 'database',
        # Cloud
        'aws-lambda': 'cloud', 'aws-ec2': 'cloud', 'aws-ecs': 'cloud',
        'google-functions': 'cloud', 'azure-functions': 'cloud',
        'kubernetes': 'cloud', 'docker': 'cloud',
        # Internal
        'direct': 'direct', 'direct-vm': 'direct',
        'seda': 'seda', 'vm': 'seda',
        'timer': 'timer', 'quartz': 'timer', 'cron': 'timer', 'scheduler': 'timer',
        # Other
        'bean': 'bean', 'class': 'bean', 'method': 'bean',
        'log': 'log', 'mock': 'test', 'dataset': 'test',
        'mail': 'mail', 'smtp': 'mail', 'imap': 'mail', 'pop3': 'mail',
        'exec': 'process', 'process': 'process',
        'velocity': 'template', 'freemarker': 'template', 'thymeleaf': 'template',
    }

    # Endpoint URI pattern (from, to, toD)
    ENDPOINT_URI_PATTERN = re.compile(
        r'(?:from|\.to|\.toD|\.toF|\.wireTap|\.enrich|\.pollEnrich)\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # Marshal/Unmarshal
    MARSHAL_PATTERN = re.compile(
        r'\.marshal\s*\(\s*\)\s*\.\s*(\w+)\s*\(|'
        r'\.marshal\s*\(\s*(?:new\s+)?(\w+)',
        re.MULTILINE
    )

    UNMARSHAL_PATTERN = re.compile(
        r'\.unmarshal\s*\(\s*\)\s*\.\s*(\w+)\s*\(|'
        r'\.unmarshal\s*\(\s*(?:new\s+)?(\w+)',
        re.MULTILINE
    )

    # Data format DSL
    DATA_FORMAT_DSL_PATTERN = re.compile(
        r'\.(?:json|xml|csv|avro|protobuf|yaml|jacksonXml|jaxb|'
        r'xstream|bindy|hl7|fhirJson|fhirXml|asn1|cbor|'
        r'flatpack|ical|lzf|pgp|tarFile|zipFile|gzipDeflater|'
        r'syslog|mimeMultipart|rss)\s*\(',
        re.MULTILINE
    )

    # Jackson JSON
    JACKSON_PATTERN = re.compile(
        r'JacksonDataFormat|jacksonxml|import\s+org\.apache\.camel\.component\.jackson\b',
        re.MULTILINE
    )

    # Type converter
    TYPE_CONVERTER_PATTERN = re.compile(
        r'@Converter(?:\s*\(\s*(?:generateLoader|generateBulkLoader)\s*=\s*true\s*\))?\s*'
        r'(?:public\s+)?(?:static\s+)?(?:class|(?:\w+(?:<[^>]+>)?)\s+\w+\s*\()',
        re.DOTALL
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract component and data format information."""
        components: Dict[str, CamelComponentInfo] = {}
        data_formats: List[CamelDataFormatInfo] = []
        has_type_converters = False

        if not content or not content.strip():
            return {
                'components': list(components.values()),
                'data_formats': data_formats,
                'has_type_converters': has_type_converters,
            }

        # Extract all endpoint URIs and categorize
        for match in self.ENDPOINT_URI_PATTERN.finditer(content):
            uri = match.group(1)
            if ':' in uri:
                comp_name = uri.split(':')[0].strip()
            else:
                comp_name = uri.strip()

            if comp_name not in components:
                components[comp_name] = CamelComponentInfo(
                    name=comp_name,
                    category=self.COMPONENT_CATEGORIES.get(comp_name, 'other'),
                    line_number=content[:match.start()].count('\n') + 1,
                )
            components[comp_name].uri_count += 1
            components[comp_name].uris.append(uri)

        # Marshal data formats
        marshal_formats: Dict[str, int] = {}
        for match in self.MARSHAL_PATTERN.finditer(content):
            fmt = match.group(1) or match.group(2) or ""
            fmt = fmt.lower().replace('dataformat', '').strip()
            if fmt:
                marshal_formats[fmt] = marshal_formats.get(fmt, 0) + 1

        # Unmarshal data formats
        unmarshal_formats: Dict[str, int] = {}
        for match in self.UNMARSHAL_PATTERN.finditer(content):
            fmt = match.group(1) or match.group(2) or ""
            fmt = fmt.lower().replace('dataformat', '').strip()
            if fmt:
                unmarshal_formats[fmt] = unmarshal_formats.get(fmt, 0) + 1

        # Combine into data format info
        all_fmts = set(list(marshal_formats.keys()) + list(unmarshal_formats.keys()))
        for fmt in all_fmts:
            library = ""
            if 'jackson' in fmt.lower() or self.JACKSON_PATTERN.search(content):
                library = "jackson"
            df = CamelDataFormatInfo(
                format_name=fmt,
                library=library,
                marshal_count=marshal_formats.get(fmt, 0),
                unmarshal_count=unmarshal_formats.get(fmt, 0),
            )
            data_formats.append(df)

        # Type converters
        has_type_converters = bool(self.TYPE_CONVERTER_PATTERN.search(content))

        return {
            'components': list(components.values()),
            'data_formats': data_formats,
            'has_type_converters': has_type_converters,
        }
