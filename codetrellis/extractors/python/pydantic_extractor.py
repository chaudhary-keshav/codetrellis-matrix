"""
PydanticExtractor - Extracts Pydantic BaseModel definitions from source code.

This extractor parses Pydantic model declarations and extracts:
- Model name and inheritance
- Fields with types, defaults, and Field() options
- Validators (@field_validator, @model_validator)
- Computed fields (@computed_field)
- Model configuration (model_config)
- Pydantic v1 and v2 syntax support

Part of CodeTrellis v2.0 - Python Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class PydanticFieldInfo:
    """Information about a Pydantic model field."""
    name: str
    type: str
    required: bool = True
    default: Optional[str] = None
    alias: Optional[str] = None
    description: Optional[str] = None
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PydanticValidatorInfo:
    """Information about a Pydantic validator."""
    name: str
    fields: List[str]
    mode: str = "after"  # before, after, wrap, plain
    is_class_method: bool = True


@dataclass
class PydanticComputedFieldInfo:
    """Information about a computed field."""
    name: str
    return_type: str
    cached: bool = False


@dataclass
class PydanticModelInfo:
    """Complete information about a Pydantic model."""
    name: str
    fields: List[PydanticFieldInfo] = field(default_factory=list)
    validators: List[PydanticValidatorInfo] = field(default_factory=list)
    computed_fields: List[PydanticComputedFieldInfo] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    is_exported: bool = True
    line_number: int = 0


class PydanticExtractor:
    """
    Extracts Pydantic BaseModel definitions from source code.

    Handles:
    - Pydantic v1 and v2 syntax
    - Field() with constraints (min_length, max_length, gt, lt, etc.)
    - Default values and factories
    - @field_validator and @model_validator decorators
    - @computed_field decorated properties
    - model_config / Config class
    - Generic models
    """

    # Patterns to detect Pydantic models
    PYDANTIC_CLASS_PATTERN = re.compile(
        r'class\s+(\w+)\s*\(([^)]*(?:BaseModel|BaseSettings|GenericModel)[^)]*)\):',
        re.MULTILINE
    )

    FIELD_PATTERN = re.compile(
        r'^\s+(\w+)\s*:\s*([^=\n]+?)(?:\s*=\s*(.+?))?$',
        re.MULTILINE
    )

    FIELD_CALL_PATTERN = re.compile(
        r'Field\s*\(\s*([^)]*)\s*\)'
    )

    VALIDATOR_PATTERN = re.compile(
        r'@(?:field_validator|validator)\s*\(\s*([^)]+)\s*\)(?:.*?)?\n\s+'
        r'(?:@classmethod\s+)?'
        r'def\s+(\w+)',
        re.MULTILINE | re.DOTALL
    )

    MODEL_VALIDATOR_PATTERN = re.compile(
        r'@model_validator\s*\(\s*mode\s*=\s*[\'"](\w+)[\'"]\s*\).*?\n\s+'
        r'(?:@classmethod\s+)?'
        r'def\s+(\w+)',
        re.MULTILINE | re.DOTALL
    )

    COMPUTED_FIELD_PATTERN = re.compile(
        r'@computed_field(?:\(cached=(\w+)\))?\s*\n\s+'
        r'@property\s*\n\s+'
        r'def\s+(\w+)\s*\([^)]*\)\s*->\s*([^:]+):',
        re.MULTILINE
    )

    CONFIG_PATTERN = re.compile(
        r'model_config\s*=\s*ConfigDict\s*\(\s*([^)]+)\s*\)',
        re.MULTILINE
    )

    CONFIG_CLASS_PATTERN = re.compile(
        r'class\s+Config\s*:\s*\n((?:\s+.+\n)+)',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the Pydantic extractor."""
        pass

    def extract(self, content: str) -> List[PydanticModelInfo]:
        """
        Extract all Pydantic models from Python content.

        Args:
            content: Python source code

        Returns:
            List of PydanticModelInfo objects
        """
        models = []

        for match in self.PYDANTIC_CLASS_PATTERN.finditer(content):
            model_name = match.group(1)
            bases_str = match.group(2)

            # Parse bases
            bases = [b.strip() for b in bases_str.split(',') if b.strip()]

            # Calculate line number
            line_number = content[:match.start()].count('\n') + 1

            # Extract class body
            class_body_start = match.end()
            class_body = self._extract_class_body(content, class_body_start)

            if class_body is None:
                continue

            # Parse fields
            fields = self._parse_fields(class_body)

            # Parse validators
            validators = self._parse_validators(class_body)

            # Parse model validators
            model_validators = self._parse_model_validators(class_body)
            validators.extend(model_validators)

            # Parse computed fields
            computed_fields = self._parse_computed_fields(class_body)

            # Parse config
            config = self._parse_config(class_body)

            model_info = PydanticModelInfo(
                name=model_name,
                fields=fields,
                validators=validators,
                computed_fields=computed_fields,
                bases=bases,
                config=config,
                line_number=line_number
            )

            models.append(model_info)

        return models

    def _extract_class_body(self, content: str, start_pos: int) -> Optional[str]:
        """Extract the body of a class by indentation."""
        lines = content[start_pos:].split('\n')

        if not lines:
            return None

        body_lines = []
        base_indent = None

        for line in lines:
            if not line.strip():
                if base_indent is not None:
                    body_lines.append('')
                continue

            current_indent = len(line) - len(line.lstrip())

            if base_indent is None:
                base_indent = current_indent
                body_lines.append(line)
                continue

            if current_indent < base_indent and line.strip():
                break

            body_lines.append(line)

        return '\n'.join(body_lines)

    def _parse_fields(self, class_body: str) -> List[PydanticFieldInfo]:
        """Parse Pydantic fields from class body."""
        fields = []

        for match in self.FIELD_PATTERN.finditer(class_body):
            field_name = match.group(1)
            field_type = match.group(2).strip()
            default_value = match.group(3)

            # Skip class methods, Config class, etc.
            if field_name in ['def', 'class', 'model_config', 'Config']:
                continue

            # Skip ClassVar
            if 'ClassVar' in field_type:
                continue

            # Determine if required
            required = True
            default = None
            alias = None
            description = None
            constraints = {}

            # Check for Optional or union with None
            if 'Optional' in field_type or '| None' in field_type or 'None |' in field_type:
                required = False

            if default_value:
                default_value = default_value.strip()
                required = False

                # Check if it's a Field() call
                field_match = self.FIELD_CALL_PATTERN.search(default_value)
                if field_match:
                    field_args = field_match.group(1)

                    # Extract alias
                    alias_match = re.search(r'alias\s*=\s*[\'"](\w+)[\'"]', field_args)
                    if alias_match:
                        alias = alias_match.group(1)

                    # Extract description
                    desc_match = re.search(r'description\s*=\s*[\'"]([^"\']+)[\'"]', field_args)
                    if desc_match:
                        description = desc_match.group(1)

                    # Extract constraints
                    constraint_patterns = {
                        'min_length': r'min_length\s*=\s*(\d+)',
                        'max_length': r'max_length\s*=\s*(\d+)',
                        'gt': r'gt\s*=\s*([^,)]+)',
                        'ge': r'ge\s*=\s*([^,)]+)',
                        'lt': r'lt\s*=\s*([^,)]+)',
                        'le': r'le\s*=\s*([^,)]+)',
                        'regex': r'regex\s*=\s*[\'"]([^"\']+)[\'"]',
                        'pattern': r'pattern\s*=\s*[\'"]([^"\']+)[\'"]',
                    }

                    for constraint_name, pattern in constraint_patterns.items():
                        constraint_match = re.search(pattern, field_args)
                        if constraint_match:
                            constraints[constraint_name] = constraint_match.group(1)

                    # Check if required (Field(...) or Field(default=...))
                    if '...' in field_args and 'default' not in field_args:
                        required = True
                    elif 'default=' in field_args:
                        default_match = re.search(r'default\s*=\s*([^,)]+)', field_args)
                        if default_match:
                            default = default_match.group(1).strip()

                elif default_value != 'None':
                    default = default_value

            field_info = PydanticFieldInfo(
                name=field_name,
                type=field_type,
                required=required,
                default=default,
                alias=alias,
                description=description,
                constraints=constraints
            )

            fields.append(field_info)

        return fields

    def _parse_validators(self, class_body: str) -> List[PydanticValidatorInfo]:
        """Parse field validators."""
        validators = []

        for match in self.VALIDATOR_PATTERN.finditer(class_body):
            fields_str = match.group(1)
            validator_name = match.group(2)

            # Extract field names
            fields = re.findall(r'[\'"](\w+)[\'"]', fields_str)

            # Determine mode
            mode = "after"
            if 'mode=' in class_body[match.start():match.end()+50]:
                mode_match = re.search(r'mode\s*=\s*[\'"](\w+)[\'"]',
                                       class_body[match.start():match.end()+50])
                if mode_match:
                    mode = mode_match.group(1)

            validators.append(PydanticValidatorInfo(
                name=validator_name,
                fields=fields,
                mode=mode
            ))

        return validators

    def _parse_model_validators(self, class_body: str) -> List[PydanticValidatorInfo]:
        """Parse model validators."""
        validators = []

        for match in self.MODEL_VALIDATOR_PATTERN.finditer(class_body):
            mode = match.group(1)
            validator_name = match.group(2)

            validators.append(PydanticValidatorInfo(
                name=validator_name,
                fields=['__all__'],  # Model validators apply to all fields
                mode=mode
            ))

        return validators

    def _parse_computed_fields(self, class_body: str) -> List[PydanticComputedFieldInfo]:
        """Parse computed fields."""
        computed_fields = []

        for match in self.COMPUTED_FIELD_PATTERN.finditer(class_body):
            cached_str = match.group(1)
            field_name = match.group(2)
            return_type = match.group(3).strip()

            cached = cached_str == 'True' if cached_str else False

            computed_fields.append(PydanticComputedFieldInfo(
                name=field_name,
                return_type=return_type,
                cached=cached
            ))

        return computed_fields

    def _parse_config(self, class_body: str) -> Dict[str, Any]:
        """Parse model configuration."""
        config = {}

        # Check for model_config = ConfigDict(...)
        config_match = self.CONFIG_PATTERN.search(class_body)
        if config_match:
            config_str = config_match.group(1)

            config_options = {
                'from_attributes': r'from_attributes\s*=\s*(True|False)',
                'validate_assignment': r'validate_assignment\s*=\s*(True|False)',
                'extra': r'extra\s*=\s*[\'"](\w+)[\'"]',
                'frozen': r'frozen\s*=\s*(True|False)',
                'str_strip_whitespace': r'str_strip_whitespace\s*=\s*(True|False)',
                'use_enum_values': r'use_enum_values\s*=\s*(True|False)',
            }

            for opt_name, pattern in config_options.items():
                opt_match = re.search(pattern, config_str)
                if opt_match:
                    value = opt_match.group(1)
                    if value in ('True', 'False'):
                        config[opt_name] = value == 'True'
                    else:
                        config[opt_name] = value

        # Check for legacy Config class
        config_class_match = self.CONFIG_CLASS_PATTERN.search(class_body)
        if config_class_match:
            config_body = config_class_match.group(1)

            legacy_options = {
                'orm_mode': r'orm_mode\s*=\s*(True|False)',
                'validate_assignment': r'validate_assignment\s*=\s*(True|False)',
                'extra': r'extra\s*=\s*[\'"](\w+)[\'"]',
            }

            for opt_name, pattern in legacy_options.items():
                opt_match = re.search(pattern, config_body)
                if opt_match:
                    value = opt_match.group(1)
                    # Map orm_mode to from_attributes
                    if opt_name == 'orm_mode':
                        config['from_attributes'] = value == 'True'
                    elif value in ('True', 'False'):
                        config[opt_name] = value == 'True'
                    else:
                        config[opt_name] = value

        return config

    def to_codetrellis_format(self, models: List[PydanticModelInfo]) -> str:
        """
        Convert extracted Pydantic models to CodeTrellis format.

        Args:
            models: List of PydanticModelInfo objects

        Returns:
            CodeTrellis formatted string
        """
        if not models:
            return ""

        lines = ["[PYDANTIC_MODELS]"]

        for model in models:
            parts = [model.name]

            # Add bases
            if model.bases:
                parts.append(f"extends:{','.join(model.bases)}")

            # Add fields
            field_strs = []
            for f in model.fields:
                field_str = f"{f.name}:{f.type}"
                if f.required:
                    field_str += "!"
                elif f.default:
                    field_str += f"={f.default}"
                if f.constraints:
                    constraint_str = ','.join(f"{k}={v}" for k, v in f.constraints.items())
                    field_str += f"[{constraint_str}]"
                field_strs.append(field_str)

            if field_strs:
                parts.append(f"fields:[{','.join(field_strs)}]")

            # Add validators
            if model.validators:
                validator_strs = [f"{v.name}→{','.join(v.fields)}" for v in model.validators]
                parts.append(f"validators:[{';'.join(validator_strs)}]")

            # Add computed fields
            if model.computed_fields:
                computed_strs = [f"{c.name}:{c.return_type}" for c in model.computed_fields]
                parts.append(f"computed:[{','.join(computed_strs)}]")

            # Add config
            if model.config:
                config_strs = [f"{k}={v}" for k, v in model.config.items()]
                parts.append(f"config:[{','.join(config_strs)}]")

            lines.append("|".join(parts))

        return "\n".join(lines)


# Convenience function
def extract_pydantic_models(content: str) -> List[PydanticModelInfo]:
    """Extract Pydantic models from Python content."""
    extractor = PydanticExtractor()
    return extractor.extract(content)
