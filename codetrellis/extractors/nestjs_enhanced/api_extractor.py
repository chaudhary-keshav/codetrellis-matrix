"""
NestJS API Extractor - Per-file extraction of Swagger/OpenAPI decorators and DTOs.

Supports:
- @ApiTags(), @ApiOperation(), @ApiResponse() Swagger decorators
- @ApiProperty(), @ApiPropertyOptional() DTO decorators
- @ApiParam(), @ApiQuery(), @ApiHeader(), @ApiBody() parameter decorators
- @ApiBearerAuth(), @ApiBasicAuth(), @ApiOAuth2() auth decorators
- DTO classes with class-validator decorators
- NestJS 7.x through 10.x patterns
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class NestSwaggerInfo:
    """Swagger/OpenAPI decorator information on a controller or method."""
    decorator: str  # ApiTags, ApiOperation, ApiResponse, etc.
    value: str = ""
    file: str = ""
    line_number: int = 0
    target: str = ""  # class or method name this applies to
    status_code: int = 0  # For @ApiResponse
    description: str = ""


@dataclass
class NestApiPropertyInfo:
    """An @ApiProperty() decorated field in a DTO."""
    name: str
    file: str = ""
    line_number: int = 0
    dto_class: str = ""
    property_type: str = ""
    is_optional: bool = False
    is_array: bool = False
    description: str = ""
    example: str = ""
    has_validation: bool = False
    validation_decorators: List[str] = field(default_factory=list)


@dataclass
class NestDtoInfo:
    """A DTO class with its properties."""
    class_name: str
    file: str = ""
    line_number: int = 0
    extends: str = ""
    properties: List[NestApiPropertyInfo] = field(default_factory=list)
    has_swagger: bool = False
    has_validation: bool = False
    total_properties: int = 0


@dataclass
class NestApiSummary:
    """Summary of NestJS API documentation patterns."""
    total_swagger_decorators: int = 0
    total_dtos: int = 0
    total_api_properties: int = 0
    has_swagger: bool = False
    has_tags: bool = False
    has_auth_decorators: bool = False
    has_validation: bool = False
    api_tags: List[str] = field(default_factory=list)


class NestApiExtractor:
    """Extracts NestJS API/Swagger information from a single file."""

    # Swagger decorators
    API_TAGS_PATTERN = re.compile(
        r"@ApiTags\s*\(\s*['\"`]([^'\"`]+)['\"`]"
    )

    API_OPERATION_PATTERN = re.compile(
        r'@ApiOperation\s*\(\s*\{([^}]*)\}\s*\)',
        re.DOTALL
    )

    API_RESPONSE_PATTERN = re.compile(
        r'@Api(?:Ok)?Response\s*\(\s*\{([^}]*)\}\s*\)',
        re.DOTALL
    )

    API_PROPERTY_PATTERN = re.compile(
        r'@ApiProperty(?:Optional)?\s*\(\s*(?:\{([^}]*)\})?\s*\)'
    )

    # Auth decorators
    API_AUTH_PATTERNS = [
        re.compile(r'@ApiBearerAuth\s*\('),
        re.compile(r'@ApiBasicAuth\s*\('),
        re.compile(r'@ApiOAuth2\s*\('),
        re.compile(r'@ApiSecurity\s*\('),
        re.compile(r'@ApiCookieAuth\s*\('),
    ]

    # DTO class pattern
    DTO_CLASS_PATTERN = re.compile(
        r'(?:export\s+)?class\s+(\w*(?:Dto|DTO|Input|Output|Request|Response)\w*)'
        r'(?:\s+extends\s+(\w+))?\s*\{'
    )

    # class-validator decorators
    VALIDATION_DECORATORS = re.compile(
        r'@(IsString|IsNumber|IsBoolean|IsEmail|IsNotEmpty|IsOptional|'
        r'IsEnum|IsArray|IsDate|IsInt|IsUUID|Min|Max|MinLength|MaxLength|'
        r'Matches|IsUrl|ValidateNested|Type|Transform|ArrayMinSize|ArrayMaxSize)\s*\('
    )

    # Property after @ApiProperty
    PROPERTY_LINE_PATTERN = re.compile(
        r'(\w+)\s*(?:\??\s*:\s*(\w[\w<>\[\]|,\s]*))?'
    )

    # Generic Swagger decorators
    SWAGGER_DECORATOR_PATTERN = re.compile(
        r'@Api(\w+)\s*\('
    )

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract API/Swagger information from a NestJS source file."""
        swagger_decorators: List[NestSwaggerInfo] = []
        api_properties: List[NestApiPropertyInfo] = []
        dtos: List[NestDtoInfo] = []
        lines = content.split('\n')

        # Collect API tags
        api_tags = []
        has_auth = False
        for match in self.API_TAGS_PATTERN.finditer(content):
            tag = match.group(1)
            api_tags.append(tag)
            line_num = content[:match.start()].count('\n') + 1
            swagger_decorators.append(NestSwaggerInfo(
                decorator='ApiTags',
                value=tag,
                file=file_path,
                line_number=line_num,
            ))

        # Collect @ApiOperation decorators
        for match in self.API_OPERATION_PATTERN.finditer(content):
            body = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            summary = ''
            desc = ''
            s_match = re.search(r"summary\s*:\s*['\"`]([^'\"`]+)['\"`]", body)
            d_match = re.search(r"description\s*:\s*['\"`]([^'\"`]+)['\"`]", body)
            if s_match:
                summary = s_match.group(1)
            if d_match:
                desc = d_match.group(1)
            swagger_decorators.append(NestSwaggerInfo(
                decorator='ApiOperation',
                value=summary,
                description=desc,
                file=file_path,
                line_number=line_num,
            ))

        # Collect @ApiResponse decorators
        for match in self.API_RESPONSE_PATTERN.finditer(content):
            body = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            status = 0
            desc = ''
            st_match = re.search(r'status\s*:\s*(\d+)', body)
            d_match = re.search(r"description\s*:\s*['\"`]([^'\"`]+)['\"`]", body)
            if st_match:
                status = int(st_match.group(1))
            if d_match:
                desc = d_match.group(1)
            swagger_decorators.append(NestSwaggerInfo(
                decorator='ApiResponse',
                description=desc,
                status_code=status,
                file=file_path,
                line_number=line_num,
            ))

        # Check auth decorators
        for pattern in self.API_AUTH_PATTERNS:
            if pattern.search(content):
                has_auth = True
                break

        # All Swagger decorators count
        total_swagger = len(list(self.SWAGGER_DECORATOR_PATTERN.finditer(content)))

        # Find DTOs
        for dto_match in self.DTO_CLASS_PATTERN.finditer(content):
            class_name = dto_match.group(1)
            extends = dto_match.group(2) or ''
            line_num = content[:dto_match.start()].count('\n') + 1

            # Extract class body
            body = self._extract_class_body(content, dto_match.end())
            props = self._extract_dto_properties(body, class_name, file_path, line_num)

            has_swagger = bool(self.API_PROPERTY_PATTERN.search(body))
            has_validation = bool(self.VALIDATION_DECORATORS.search(body))

            dtos.append(NestDtoInfo(
                class_name=class_name,
                file=file_path,
                line_number=line_num,
                extends=extends,
                properties=props,
                has_swagger=has_swagger,
                has_validation=has_validation,
                total_properties=len(props),
            ))
            api_properties.extend(props)

        # Build summary
        summary = NestApiSummary(
            total_swagger_decorators=total_swagger,
            total_dtos=len(dtos),
            total_api_properties=len(api_properties),
            has_swagger=total_swagger > 0,
            has_tags=bool(api_tags),
            has_auth_decorators=has_auth,
            has_validation=bool(self.VALIDATION_DECORATORS.search(content)),
            api_tags=api_tags,
        )

        return {
            "swagger_decorators": swagger_decorators,
            "api_properties": api_properties,
            "dtos": dtos,
            "summary": summary,
        }

    def _extract_class_body(self, content: str, start_idx: int) -> str:
        """Extract class body from after opening { to closing }.
        
        Note: start_idx should be right after the opening { of the class,
        so we begin with depth=1 already inside the class body.
        """
        depth = 1
        for i in range(start_idx, min(start_idx + 5000, len(content))):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth <= 0:
                    return content[start_idx:i + 1]
        return content[start_idx:start_idx + 5000]

    def _extract_dto_properties(
        self,
        body: str,
        dto_class: str,
        file_path: str,
        base_line: int,
    ) -> List[NestApiPropertyInfo]:
        """Extract properties from a DTO class body."""
        properties: List[NestApiPropertyInfo] = []
        lines = body.split('\n')

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Look for @ApiProperty or @ApiPropertyOptional
            api_match = self.API_PROPERTY_PATTERN.search(stripped)
            if api_match:
                opts = api_match.group(1) or ''
                is_optional = 'ApiPropertyOptional' in stripped

                # Get property name from next non-decorator line
                prop_name = ''
                prop_type = ''
                for j in range(i + 1, min(i + 5, len(lines))):
                    p_match = self.PROPERTY_LINE_PATTERN.search(lines[j].strip())
                    if p_match and not lines[j].strip().startswith('@'):
                        prop_name = p_match.group(1)
                        prop_type = (p_match.group(2) or '').strip()
                        break

                # Extract description and example from opts
                desc = ''
                example = ''
                d_match = re.search(r"description\s*:\s*['\"`]([^'\"`]+)['\"`]", opts)
                e_match = re.search(r"example\s*:\s*([^,}]+)", opts)
                if d_match:
                    desc = d_match.group(1)
                if e_match:
                    example = e_match.group(1).strip()

                is_array = 'isArray' in opts or '[]' in prop_type

                # Check for validation decorators around this property
                area = '\n'.join(lines[max(0, i - 3):i + 1])
                validation_decs = self.VALIDATION_DECORATORS.findall(area)

                properties.append(NestApiPropertyInfo(
                    name=prop_name,
                    file=file_path,
                    line_number=base_line + i,
                    dto_class=dto_class,
                    property_type=prop_type,
                    is_optional=is_optional or '?' in prop_name,
                    is_array=is_array,
                    description=desc,
                    example=example,
                    has_validation=bool(validation_decs),
                    validation_decorators=validation_decs,
                ))

        return properties
