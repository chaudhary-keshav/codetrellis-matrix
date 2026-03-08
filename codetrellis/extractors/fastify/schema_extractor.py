"""
Fastify Schema Extractor - Extracts JSON Schema validation and type provider patterns.

Supports:
- Inline route schemas (body, querystring, params, headers, response)
- Shared schemas via fastify.addSchema()
- $ref schema references
- Type providers: TypeBox, Zod, JSON Schema to TypeScript
- Fluent-json-schema usage
- Fastify 3.x through 5.x schema patterns
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class FastifySchemaInfo:
    """A schema definition or usage."""
    schema_id: str = ""
    file: str = ""
    line_number: int = 0
    schema_type: str = ""  # inline, shared, ref
    target: str = ""  # body, querystring, params, headers, response
    has_required: bool = False
    has_properties: bool = False
    property_count: int = 0
    uses_ref: bool = False
    ref_ids: List[str] = field(default_factory=list)


@dataclass
class FastifyTypeProviderInfo:
    """Type provider configuration."""
    provider: str = ""  # typebox, zod, json-schema-to-ts, fluent-json-schema
    file: str = ""
    line_number: int = 0


class FastifySchemaExtractor:
    """Extracts Fastify schema information from source code."""

    # fastify.addSchema()
    ADD_SCHEMA_PATTERN = re.compile(
        r'(\w+)\s*\.\s*addSchema\s*\(\s*(\{)',
    )

    # $id in schema
    SCHEMA_ID_PATTERN = re.compile(
        r"\$id\s*:\s*['\"`]([^'\"`]+)['\"`]"
    )

    # $ref in schema
    SCHEMA_REF_PATTERN = re.compile(
        r"\$ref\s*:\s*['\"`]([^'\"`]+)['\"`]"
    )

    # Schema sections in route options
    SCHEMA_SECTION_PATTERN = re.compile(
        r'schema\s*:\s*\{'
    )

    # Schema targets
    SCHEMA_TARGET_PATTERN = re.compile(
        r'(body|querystring|params|headers|response)\s*:'
    )

    # Type providers
    TYPE_PROVIDER_PATTERNS = {
        'typebox': re.compile(
            r"from\s+['\"]@sinclair/typebox['\"]|Type\.\w+\(|TypeBox",
            re.MULTILINE
        ),
        'zod': re.compile(
            r"from\s+['\"]zod['\"]|z\.\w+\(|ZodTypeProvider|serializerCompiler.*zod",
            re.MULTILINE
        ),
        'json-schema-to-ts': re.compile(
            r"from\s+['\"]json-schema-to-ts['\"]|FromSchema|JsonSchemaToTsProvider",
            re.MULTILINE
        ),
        'fluent-json-schema': re.compile(
            r"from\s+['\"]fluent-json-schema['\"]|require\(['\"]fluent-json-schema['\"]\)|"
            r"S\.object|S\.string|S\.number|S\.array",
            re.MULTILINE
        ),
        'fluent-schema': re.compile(
            r"from\s+['\"]fluent-schema['\"]|FluentSchema",
            re.MULTILINE
        ),
    }

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract schema information from Fastify source code."""
        schemas: List[FastifySchemaInfo] = []
        type_providers: List[FastifyTypeProviderInfo] = []

        # Detect type providers
        for provider, pattern in self.TYPE_PROVIDER_PATTERNS.items():
            match = pattern.search(content)
            if match:
                line_num = content[:match.start()].count('\n') + 1
                type_providers.append(FastifyTypeProviderInfo(
                    provider=provider,
                    file=file_path,
                    line_number=line_num,
                ))

        # Find addSchema() calls
        for match in self.ADD_SCHEMA_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            block = self._extract_block(content, match.start())

            schema_id = ''
            id_match = self.SCHEMA_ID_PATTERN.search(block)
            if id_match:
                schema_id = id_match.group(1)

            refs = self.SCHEMA_REF_PATTERN.findall(block)
            props = re.findall(r'properties\s*:', block)

            schemas.append(FastifySchemaInfo(
                schema_id=schema_id,
                file=file_path,
                line_number=line_num,
                schema_type='shared',
                has_required='required' in block,
                has_properties=bool(props),
                property_count=block.count(':') // 2,  # rough estimate
                uses_ref=bool(refs),
                ref_ids=refs,
            ))

        # Find inline schemas in route options
        for match in self.SCHEMA_SECTION_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            block = self._extract_block(content, match.start())

            # Find which targets are defined
            for target_match in self.SCHEMA_TARGET_PATTERN.finditer(block):
                target = target_match.group(1)
                refs = self.SCHEMA_REF_PATTERN.findall(block)

                schemas.append(FastifySchemaInfo(
                    file=file_path,
                    line_number=line_num,
                    schema_type='inline',
                    target=target,
                    has_required='required' in block,
                    has_properties='properties' in block,
                    uses_ref=bool(refs),
                    ref_ids=refs,
                ))

        return {
            "schemas": schemas,
            "type_providers": type_providers,
        }

    def _extract_block(self, content: str, start: int, max_chars: int = 2000) -> str:
        """Extract a braced block from content."""
        depth = 0
        started = False
        end = min(start + max_chars, len(content))
        for i in range(start, end):
            if content[i] == '{':
                depth += 1
                started = True
            elif content[i] == '}':
                depth -= 1
                if started and depth <= 0:
                    return content[start:i + 1]
        return content[start:end]
