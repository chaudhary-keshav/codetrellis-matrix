"""
MongoDBExtractor - Extracts MongoDB/PyMongo/Motor/Beanie components.

This extractor parses Python code using MongoDB and extracts:
- Beanie Document models (ODM)
- PyMongo collection operations
- Motor async operations
- Index definitions
- Aggregation pipelines
- Connection configurations

Part of CodeTrellis v2.0 - Python Data Engineering Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class BeanieDocumentInfo:
    """Information about a Beanie Document model."""
    name: str
    collection_name: Optional[str] = None
    fields: List[Dict[str, Any]] = field(default_factory=list)
    indexes: List[Dict[str, Any]] = field(default_factory=list)
    validators: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)  # Document references
    settings_class: Optional[str] = None
    line_number: int = 0


@dataclass
class MongoCollectionInfo:
    """Information about a MongoDB collection usage."""
    name: str
    variable_name: str
    database: Optional[str] = None
    operations: List[str] = field(default_factory=list)  # find, insert, update, etc.


@dataclass
class MongoIndexInfo:
    """Information about a MongoDB index definition."""
    collection: str
    fields: List[str] = field(default_factory=list)
    unique: bool = False
    sparse: bool = False
    index_type: str = "ascending"  # ascending, descending, text, geo2d, etc.


@dataclass
class MongoAggregationInfo:
    """Information about a MongoDB aggregation pipeline."""
    name: str
    collection: Optional[str] = None
    stages: List[str] = field(default_factory=list)  # $match, $group, $project, etc.
    line_number: int = 0


@dataclass
class MongoConnectionInfo:
    """Information about MongoDB connection configuration."""
    name: str
    uri_env: Optional[str] = None  # Environment variable name
    database: Optional[str] = None
    is_async: bool = False
    driver: str = "pymongo"  # pymongo, motor, beanie


class MongoDBExtractor:
    """
    Extracts MongoDB-related components from Python source code.

    Handles:
    - Beanie ODM Document classes
    - PyMongo collection operations
    - Motor async operations
    - Index definitions
    - Aggregation pipelines
    - Connection strings and configurations
    """

    # Beanie Document pattern
    BEANIE_DOCUMENT_PATTERN = re.compile(
        r'class\s+(\w+)\s*\(\s*(?:Document|BaseDocument)\s*\)\s*:',
        re.MULTILINE
    )

    # Settings class in Beanie
    BEANIE_SETTINGS_PATTERN = re.compile(
        r'class\s+Settings\s*:.*?collection\s*=\s*[\'"](\w+)[\'"]',
        re.MULTILINE | re.DOTALL
    )

    # Beanie field with Link
    BEANIE_LINK_PATTERN = re.compile(
        r'(\w+)\s*:\s*(?:Optional\[)?(?:Link|BackLink)\s*\[\s*[\'"]?(\w+)[\'"]?\s*\]'
    )

    # PyMongo/Motor client
    MONGO_CLIENT_PATTERN = re.compile(
        r'(\w+)\s*=\s*(Motor)?(?:Async)?Client\s*\(\s*([^)]*)\s*\)',
        re.MULTILINE
    )

    # Collection access
    COLLECTION_PATTERN = re.compile(
        r'(\w+)\s*=\s*(\w+)\s*\[\s*[\'"](\w+)[\'"]\s*\]\s*\[\s*[\'"](\w+)[\'"]\s*\]',
        re.MULTILINE
    )

    # Alternative collection access
    COLLECTION_ALT_PATTERN = re.compile(
        r'(\w+)\s*=\s*(\w+)\.(\w+)\.(\w+)',
        re.MULTILINE
    )

    # Index creation
    INDEX_PATTERN = re.compile(
        r'\.create_index\s*\(\s*\[?\s*\(\s*[\'"](\w+)[\'"]',
        re.MULTILINE
    )

    # Aggregation pipeline
    AGGREGATION_PATTERN = re.compile(
        r'(\w+)\s*=\s*\[\s*(\{\s*[\'"]?\$\w+[\'"]?\s*:.*?\})\s*(?:,\s*\{[^]]*\})*\s*\]',
        re.MULTILINE | re.DOTALL
    )

    # Aggregate method call
    AGGREGATE_CALL_PATTERN = re.compile(
        r'\.aggregate\s*\(\s*(\w+)\s*\)',
        re.MULTILINE
    )

    # Common operations
    OPERATION_PATTERNS = {
        'find': re.compile(r'\.find(?:_one)?\s*\('),
        'insert': re.compile(r'\.insert_(?:one|many)\s*\('),
        'update': re.compile(r'\.update_(?:one|many)\s*\('),
        'delete': re.compile(r'\.delete_(?:one|many)\s*\('),
        'aggregate': re.compile(r'\.aggregate\s*\('),
        'count': re.compile(r'\.count_documents\s*\('),
        'distinct': re.compile(r'\.distinct\s*\('),
        'bulk_write': re.compile(r'\.bulk_write\s*\('),
    }

    def __init__(self):
        """Initialize the MongoDB extractor."""
        pass

    def extract(self, content: str) -> Dict[str, Any]:
        """
        Extract all MongoDB components from Python content.

        Args:
            content: Python source code

        Returns:
            Dict with documents, collections, indexes, aggregations
        """
        documents = self._extract_beanie_documents(content)
        collections = self._extract_collections(content)
        indexes = self._extract_indexes(content)
        aggregations = self._extract_aggregations(content)
        connections = self._extract_connections(content)

        return {
            'documents': documents,
            'collections': collections,
            'indexes': indexes,
            'aggregations': aggregations,
            'connections': connections
        }

    def _extract_beanie_documents(self, content: str) -> List[BeanieDocumentInfo]:
        """Extract Beanie Document model definitions."""
        documents = []

        for match in self.BEANIE_DOCUMENT_PATTERN.finditer(content):
            doc_name = match.group(1)
            class_start = match.end()
            class_body = self._extract_class_body(content, class_start)

            # Extract collection name from Settings
            settings_match = self.BEANIE_SETTINGS_PATTERN.search(class_body)
            collection_name = settings_match.group(1) if settings_match else doc_name.lower() + 's'

            # Extract fields
            fields = self._extract_document_fields(class_body)

            # Extract links (references)
            links = []
            for link_match in self.BEANIE_LINK_PATTERN.finditer(class_body):
                links.append(f"{link_match.group(1)}→{link_match.group(2)}")

            # Extract indexes from Settings
            indexes = self._extract_beanie_indexes(class_body)

            documents.append(BeanieDocumentInfo(
                name=doc_name,
                collection_name=collection_name,
                fields=fields,
                indexes=indexes,
                links=links,
                line_number=content[:match.start()].count('\n') + 1
            ))

        return documents

    def _extract_document_fields(self, class_body: str) -> List[Dict[str, Any]]:
        """Extract field definitions from a Beanie Document."""
        fields = []

        # Pattern for typed fields
        field_pattern = re.compile(
            r'^\s+(\w+)\s*:\s*([^=\n]+)(?:\s*=\s*(.+))?$',
            re.MULTILINE
        )

        for match in field_pattern.finditer(class_body):
            field_name = match.group(1)
            field_type = match.group(2).strip()
            default = match.group(3)

            # Skip class-level methods and Settings
            if field_name in ('Settings', 'Config') or field_name.startswith('_'):
                continue

            # Skip if it looks like a method definition
            if 'def ' in field_type or 'class ' in field_type:
                continue

            field_info = {
                'name': field_name,
                'type': field_type,
                'required': default is None and 'Optional' not in field_type
            }

            if default:
                field_info['default'] = default.strip()

            # Check for Indexed
            if 'Indexed' in field_type:
                field_info['indexed'] = True

            fields.append(field_info)

        return fields

    def _extract_beanie_indexes(self, class_body: str) -> List[Dict[str, Any]]:
        """Extract index definitions from Beanie Settings."""
        indexes = []

        # Look for indexes in Settings class
        indexes_match = re.search(r'indexes\s*=\s*\[([^\]]+)\]', class_body, re.DOTALL)
        if indexes_match:
            indexes_str = indexes_match.group(1)

            # Simple pattern for index definitions
            index_items = re.findall(r'Index\s*\(\s*[\'"]([^"\']+)[\'"]', indexes_str)
            for idx_field in index_items:
                indexes.append({'fields': [idx_field], 'type': 'single'})

            # Compound indexes
            compound = re.findall(r'\[\s*\(\s*[\'"](\w+)[\'"].*?\),\s*\(\s*[\'"](\w+)[\'"]', indexes_str)
            for fields in compound:
                indexes.append({'fields': list(fields), 'type': 'compound'})

        return indexes

    def _extract_collections(self, content: str) -> List[MongoCollectionInfo]:
        """Extract MongoDB collection usages."""
        collections = []
        seen = set()

        # Pattern 1: db["database"]["collection"]
        for match in self.COLLECTION_PATTERN.finditer(content):
            var_name = match.group(1)
            db_name = match.group(3)
            coll_name = match.group(4)

            if var_name not in seen:
                seen.add(var_name)
                collections.append(MongoCollectionInfo(
                    name=coll_name,
                    variable_name=var_name,
                    database=db_name
                ))

        # Pattern 2: client.database.collection
        for match in self.COLLECTION_ALT_PATTERN.finditer(content):
            var_name = match.group(1)
            db_name = match.group(3)
            coll_name = match.group(4)

            if var_name not in seen:
                seen.add(var_name)
                collections.append(MongoCollectionInfo(
                    name=coll_name,
                    variable_name=var_name,
                    database=db_name
                ))

        # Detect operations for each collection
        for coll in collections:
            coll.operations = self._detect_operations(content, coll.variable_name)

        return collections

    def _detect_operations(self, content: str, var_name: str) -> List[str]:
        """Detect what operations are performed on a collection."""
        operations = []

        for op_name, pattern in self.OPERATION_PATTERNS.items():
            # Check if operation is called on this variable
            if re.search(rf'{var_name}\s*{pattern.pattern}', content):
                operations.append(op_name)

        return operations

    def _extract_indexes(self, content: str) -> List[MongoIndexInfo]:
        """Extract index creation statements."""
        indexes = []

        # create_index calls
        for match in self.INDEX_PATTERN.finditer(content):
            field = match.group(1)

            # Try to find the collection
            context = content[max(0, match.start()-100):match.start()]
            coll_match = re.search(r'(\w+)\.create_index', context)
            collection = coll_match.group(1) if coll_match else "unknown"

            unique = 'unique=True' in content[match.start():match.start()+200]

            indexes.append(MongoIndexInfo(
                collection=collection,
                fields=[field],
                unique=unique
            ))

        return indexes

    def _extract_aggregations(self, content: str) -> List[MongoAggregationInfo]:
        """Extract aggregation pipeline definitions."""
        aggregations = []

        # Find pipeline variables
        for match in self.AGGREGATION_PATTERN.finditer(content):
            var_name = match.group(1)
            pipeline_content = match.group(2)

            # Extract stages
            stages = re.findall(r'\$(\w+)', pipeline_content)
            stages = list(dict.fromkeys(stages))  # Remove duplicates, preserve order

            aggregations.append(MongoAggregationInfo(
                name=var_name,
                stages=stages,
                line_number=content[:match.start()].count('\n') + 1
            ))

        return aggregations

    def _extract_connections(self, content: str) -> List[MongoConnectionInfo]:
        """Extract MongoDB connection configurations."""
        connections = []

        for match in self.MONGO_CLIENT_PATTERN.finditer(content):
            var_name = match.group(1)
            is_motor = match.group(2) is not None
            conn_args = match.group(3)

            # Check for URI from environment
            uri_env = None
            env_match = re.search(r'os\.(?:environ|getenv)\s*\[\s*[\'"](\w+)[\'"]', conn_args)
            if env_match:
                uri_env = env_match.group(1)

            connections.append(MongoConnectionInfo(
                name=var_name,
                uri_env=uri_env,
                is_async=is_motor,
                driver="motor" if is_motor else "pymongo"
            ))

        return connections

    def _extract_class_body(self, content: str, start: int) -> str:
        """Extract class body starting from position."""
        lines = content[start:].split('\n')
        body_lines = []
        indent = None

        for line in lines:
            if not line.strip():
                body_lines.append(line)
                continue

            current_spaces = len(line) - len(line.lstrip())

            if indent is None:
                if current_spaces > 0:
                    indent = current_spaces
                else:
                    break

            if line.strip() and current_spaces < indent:
                break

            body_lines.append(line)

        return '\n'.join(body_lines)

    def to_codetrellis_format(self, result: Dict[str, Any]) -> str:
        """Convert extracted MongoDB data to CodeTrellis format."""
        lines = []

        # Beanie Documents
        documents = result.get('documents', [])
        if documents:
            lines.append("[MONGODB_DOCUMENTS]")
            for doc in documents:
                parts = [f"{doc.name}|collection:{doc.collection_name}"]

                # Fields summary
                if doc.fields:
                    field_strs = []
                    for f in doc.fields[:5]:  # Limit to 5 fields
                        req = '!' if f.get('required') else '?'
                        idx = '+idx' if f.get('indexed') else ''
                        field_strs.append(f"{f['name']}:{f['type']}{req}{idx}")
                    suffix = f"...+{len(doc.fields)-5}" if len(doc.fields) > 5 else ""
                    parts.append(f"fields:[{','.join(field_strs)}{suffix}]")

                # Links
                if doc.links:
                    parts.append(f"refs:[{','.join(doc.links)}]")

                # Indexes
                if doc.indexes:
                    idx_strs = []
                    for idx in doc.indexes:
                        idx_strs.append('+'.join(idx['fields']))
                    parts.append(f"indexes:[{','.join(idx_strs)}]")

                lines.append("|".join(parts))
            lines.append("")

        # Collections
        collections = result.get('collections', [])
        if collections:
            lines.append("[MONGODB_COLLECTIONS]")
            for coll in collections:
                parts = [f"{coll.variable_name}|db:{coll.database}|coll:{coll.name}"]
                if coll.operations:
                    parts.append(f"ops:[{','.join(coll.operations)}]")
                lines.append("|".join(parts))
            lines.append("")

        # Aggregations
        aggregations = result.get('aggregations', [])
        if aggregations:
            lines.append("[MONGODB_AGGREGATIONS]")
            for agg in aggregations:
                stages_str = '→'.join(f"${s}" for s in agg.stages)
                lines.append(f"{agg.name}|pipeline:[{stages_str}]")
            lines.append("")

        # Connections
        connections = result.get('connections', [])
        if connections:
            lines.append("[MONGODB_CONNECTIONS]")
            for conn in connections:
                parts = [conn.name, f"driver:{conn.driver}"]
                if conn.uri_env:
                    parts.append(f"uri_env:{conn.uri_env}")
                if conn.is_async:
                    parts.append("async")
                lines.append("|".join(parts))

        return "\n".join(lines)


# Convenience function
def extract_mongodb(content: str) -> Dict[str, Any]:
    """Extract MongoDB components from Python content."""
    extractor = MongoDBExtractor()
    return extractor.extract(content)
