"""
ConfigExtractor - Extracts configuration patterns (Hydra, OmegaConf, Pydantic Settings).

This extractor parses Python code using configuration libraries and extracts:
- Hydra config groups and overrides
- OmegaConf structured configs
- Pydantic BaseSettings
- Environment variable usage
- Config file references

Part of CodeTrellis v2.0 - Python MLOps Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class HydraConfigInfo:
    """Information about Hydra configuration."""
    config_path: Optional[str] = None
    config_name: Optional[str] = None
    version_base: Optional[str] = None
    config_groups: List[str] = field(default_factory=list)
    overrides: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class StructuredConfigInfo:
    """Information about a structured config class."""
    name: str
    fields: List[Dict[str, Any]] = field(default_factory=list)
    defaults: List[str] = field(default_factory=list)
    is_dataclass: bool = True
    line_number: int = 0


@dataclass
class PydanticSettingsInfo:
    """Information about Pydantic BaseSettings class."""
    name: str
    fields: List[Dict[str, Any]] = field(default_factory=list)
    env_prefix: Optional[str] = None
    env_file: Optional[str] = None
    line_number: int = 0


@dataclass
class EnvVarInfo:
    """Information about environment variable usage."""
    name: str
    default: Optional[str] = None
    required: bool = False
    used_in: Optional[str] = None  # Function or class where used


@dataclass
class ConfigFileInfo:
    """Information about a config file reference."""
    path: str
    format: str  # yaml, json, toml, ini
    loader: str  # hydra, omegaconf, pyyaml, json, toml


class ConfigExtractor:
    """
    Extracts configuration-related components from Python source code.

    Handles:
    - Hydra decorators and config loading
    - OmegaConf structured configs
    - Pydantic BaseSettings
    - Environment variables (os.environ, os.getenv)
    - Config file loading patterns
    """

    # Hydra patterns
    HYDRA_MAIN_PATTERN = re.compile(
        r'@hydra\.main\s*\(',
        re.MULTILINE
    )

    HYDRA_CONFIG_PATH_PATTERN = re.compile(
        r'config_path\s*=\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    HYDRA_CONFIG_NAME_PATTERN = re.compile(
        r'config_name\s*=\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    HYDRA_VERSION_BASE_PATTERN = re.compile(
        r'version_base\s*=\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    # Hydra compose API
    HYDRA_COMPOSE_PATTERN = re.compile(
        r'compose\s*\(\s*config_name\s*=\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    HYDRA_OVERRIDES_PATTERN = re.compile(
        r'overrides\s*=\s*\[([^\]]+)\]',
        re.MULTILINE
    )

    # OmegaConf patterns
    OMEGACONF_LOAD_PATTERN = re.compile(
        r'OmegaConf\.load\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    OMEGACONF_CREATE_PATTERN = re.compile(
        r'OmegaConf\.create\s*\(',
        re.MULTILINE
    )

    OMEGACONF_STRUCTURED_PATTERN = re.compile(
        r'OmegaConf\.structured\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # Structured config class (dataclass with config fields)
    STRUCTURED_CONFIG_PATTERN = re.compile(
        r'@dataclass\s*\n\s*class\s+(\w+)(?:Config)?\s*:',
        re.MULTILINE
    )

    # Pydantic BaseSettings
    PYDANTIC_SETTINGS_PATTERN = re.compile(
        r'class\s+(\w+)\s*\(\s*(?:Base)?Settings\s*\)\s*:',
        re.MULTILINE
    )

    PYDANTIC_V2_SETTINGS_PATTERN = re.compile(
        r'class\s+(\w+)\s*\(\s*(?:pydantic_settings\.)?BaseSettings\s*\)\s*:',
        re.MULTILINE
    )

    # Environment variables
    ENVIRON_GET_PATTERN = re.compile(
        r'os\.environ(?:\.get)?\s*\[\s*[\'"](\w+)[\'"]',
        re.MULTILINE
    )

    GETENV_PATTERN = re.compile(
        r'os\.getenv\s*\(\s*[\'"](\w+)[\'"](?:\s*,\s*([^)]+))?',
        re.MULTILINE
    )

    # dotenv
    DOTENV_LOAD_PATTERN = re.compile(
        r'load_dotenv\s*\(',
        re.MULTILINE
    )

    # Config file loading
    YAML_LOAD_PATTERN = re.compile(
        r'yaml\.(?:safe_)?load\s*\(\s*(?:open\s*\(\s*)?[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    JSON_LOAD_PATTERN = re.compile(
        r'json\.load\s*\(\s*open\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    TOML_LOAD_PATTERN = re.compile(
        r'toml\.load\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the config extractor."""
        pass

    def extract(self, content: str) -> Dict[str, Any]:
        """
        Extract all configuration components from Python content.

        Args:
            content: Python source code

        Returns:
            Dict with hydra, structured_configs, pydantic_settings, env_vars, config_files
        """
        hydra = self._extract_hydra(content)
        structured_configs = self._extract_structured_configs(content)
        pydantic_settings = self._extract_pydantic_settings(content)
        env_vars = self._extract_env_vars(content)
        config_files = self._extract_config_files(content)

        return {
            'hydra': hydra,
            'structured_configs': structured_configs,
            'pydantic_settings': pydantic_settings,
            'env_vars': env_vars,
            'config_files': config_files
        }

    def _extract_hydra(self, content: str) -> List[HydraConfigInfo]:
        """Extract Hydra configuration patterns."""
        hydra_configs = []

        for match in self.HYDRA_MAIN_PATTERN.finditer(content):
            context = content[match.start():match.start()+300]

            config_path = None
            path_match = self.HYDRA_CONFIG_PATH_PATTERN.search(context)
            if path_match:
                config_path = path_match.group(1)

            config_name = None
            name_match = self.HYDRA_CONFIG_NAME_PATTERN.search(context)
            if name_match:
                config_name = name_match.group(1)

            version_base = None
            version_match = self.HYDRA_VERSION_BASE_PATTERN.search(context)
            if version_match:
                version_base = version_match.group(1)

            hydra_configs.append(HydraConfigInfo(
                config_path=config_path,
                config_name=config_name,
                version_base=version_base,
                line_number=content[:match.start()].count('\n') + 1
            ))

        # Compose API
        for match in self.HYDRA_COMPOSE_PATTERN.finditer(content):
            config_name = match.group(1)
            context = content[match.start():match.start()+300]

            overrides = []
            ovr_match = self.HYDRA_OVERRIDES_PATTERN.search(context)
            if ovr_match:
                ovr_str = ovr_match.group(1)
                overrides = [o.strip().strip('"\'') for o in ovr_str.split(',')]

            hydra_configs.append(HydraConfigInfo(
                config_name=config_name,
                overrides=overrides,
                line_number=content[:match.start()].count('\n') + 1
            ))

        return hydra_configs

    def _extract_structured_configs(self, content: str) -> List[StructuredConfigInfo]:
        """Extract structured config classes."""
        configs = []

        for match in self.STRUCTURED_CONFIG_PATTERN.finditer(content):
            class_name = match.group(1)
            class_body = self._extract_class_body(content, match.end())

            # Extract fields
            fields = self._extract_dataclass_fields(class_body)

            # Check for defaults list
            defaults = []
            defaults_match = re.search(r'defaults\s*:\s*List\[Any\]\s*=\s*field\s*\([^)]*default_factory\s*=\s*lambda:\s*\[([^\]]+)\]', class_body)
            if defaults_match:
                defaults_str = defaults_match.group(1)
                defaults = [d.strip().strip('"\'') for d in defaults_str.split(',')]

            configs.append(StructuredConfigInfo(
                name=class_name,
                fields=fields,
                defaults=defaults,
                line_number=content[:match.start()].count('\n') + 1
            ))

        return configs

    def _extract_pydantic_settings(self, content: str) -> List[PydanticSettingsInfo]:
        """Extract Pydantic BaseSettings classes."""
        settings = []

        # V1 style
        for match in self.PYDANTIC_SETTINGS_PATTERN.finditer(content):
            class_name = match.group(1)
            class_body = self._extract_class_body(content, match.end())

            fields = self._extract_pydantic_fields(class_body)

            # Config class
            env_prefix = None
            env_file = None

            config_match = re.search(r'class\s+Config\s*:', class_body)
            if config_match:
                config_body = class_body[config_match.end():config_match.end()+200]

                prefix_match = re.search(r'env_prefix\s*=\s*[\'"]([^"\']+)[\'"]', config_body)
                if prefix_match:
                    env_prefix = prefix_match.group(1)

                file_match = re.search(r'env_file\s*=\s*[\'"]([^"\']+)[\'"]', config_body)
                if file_match:
                    env_file = file_match.group(1)

            settings.append(PydanticSettingsInfo(
                name=class_name,
                fields=fields,
                env_prefix=env_prefix,
                env_file=env_file,
                line_number=content[:match.start()].count('\n') + 1
            ))

        # V2 style
        for match in self.PYDANTIC_V2_SETTINGS_PATTERN.finditer(content):
            class_name = match.group(1)
            class_body = self._extract_class_body(content, match.end())

            fields = self._extract_pydantic_fields(class_body)

            # model_config
            env_prefix = None
            env_file = None

            config_match = re.search(r'model_config\s*=\s*SettingsConfigDict\s*\(([^)]+)\)', class_body)
            if config_match:
                config_str = config_match.group(1)

                prefix_match = re.search(r'env_prefix\s*=\s*[\'"]([^"\']+)[\'"]', config_str)
                if prefix_match:
                    env_prefix = prefix_match.group(1)

                file_match = re.search(r'env_file\s*=\s*[\'"]([^"\']+)[\'"]', config_str)
                if file_match:
                    env_file = file_match.group(1)

            settings.append(PydanticSettingsInfo(
                name=class_name,
                fields=fields,
                env_prefix=env_prefix,
                env_file=env_file,
                line_number=content[:match.start()].count('\n') + 1
            ))

        return settings

    def _extract_env_vars(self, content: str) -> List[EnvVarInfo]:
        """Extract environment variable usage."""
        env_vars = []
        seen = set()

        # os.environ['VAR']
        for match in self.ENVIRON_GET_PATTERN.finditer(content):
            var_name = match.group(1)
            if var_name not in seen:
                seen.add(var_name)
                env_vars.append(EnvVarInfo(
                    name=var_name,
                    required=True
                ))

        # os.getenv('VAR', default)
        for match in self.GETENV_PATTERN.finditer(content):
            var_name = match.group(1)
            default = match.group(2)

            if var_name not in seen:
                seen.add(var_name)
                env_vars.append(EnvVarInfo(
                    name=var_name,
                    default=default.strip() if default else None,
                    required=default is None
                ))

        return env_vars

    def _extract_config_files(self, content: str) -> List[ConfigFileInfo]:
        """Extract config file loading patterns."""
        config_files = []

        # OmegaConf.load
        for match in self.OMEGACONF_LOAD_PATTERN.finditer(content):
            path = match.group(1)
            config_files.append(ConfigFileInfo(
                path=path,
                format="yaml",
                loader="omegaconf"
            ))

        # yaml.load
        for match in self.YAML_LOAD_PATTERN.finditer(content):
            path = match.group(1)
            config_files.append(ConfigFileInfo(
                path=path,
                format="yaml",
                loader="pyyaml"
            ))

        # json.load
        for match in self.JSON_LOAD_PATTERN.finditer(content):
            path = match.group(1)
            config_files.append(ConfigFileInfo(
                path=path,
                format="json",
                loader="json"
            ))

        # toml.load
        for match in self.TOML_LOAD_PATTERN.finditer(content):
            path = match.group(1)
            config_files.append(ConfigFileInfo(
                path=path,
                format="toml",
                loader="toml"
            ))

        return config_files

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

    def _extract_dataclass_fields(self, class_body: str) -> List[Dict[str, Any]]:
        """Extract fields from a dataclass."""
        fields = []

        field_pattern = re.compile(
            r'^\s+(\w+)\s*:\s*([^=\n]+)(?:\s*=\s*(.+))?$',
            re.MULTILINE
        )

        for match in field_pattern.finditer(class_body):
            field_name = match.group(1)
            field_type = match.group(2).strip()
            default = match.group(3)

            if field_name.startswith('_') or field_name in ('Config', 'model_config'):
                continue

            fields.append({
                'name': field_name,
                'type': field_type,
                'default': default.strip() if default else None
            })

        return fields

    def _extract_pydantic_fields(self, class_body: str) -> List[Dict[str, Any]]:
        """Extract fields from a Pydantic model."""
        return self._extract_dataclass_fields(class_body)

    def to_codetrellis_format(self, result: Dict[str, Any]) -> str:
        """Convert extracted config data to CodeTrellis format."""
        lines = []

        # Hydra configs
        hydra = result.get('hydra', [])
        if hydra:
            lines.append("[HYDRA_CONFIG]")
            for h in hydra:
                parts = []
                if h.config_name:
                    parts.append(f"name:{h.config_name}")
                if h.config_path:
                    parts.append(f"path:{h.config_path}")
                if h.overrides:
                    parts.append(f"overrides:[{','.join(h.overrides[:5])}]")
                lines.append("|".join(parts) if parts else "hydra.main")
            lines.append("")

        # Structured configs
        structured = result.get('structured_configs', [])
        if structured:
            lines.append("[STRUCTURED_CONFIGS]")
            for cfg in structured:
                field_names = [f['name'] for f in cfg.fields[:5]]
                suffix = f"...+{len(cfg.fields)-5}" if len(cfg.fields) > 5 else ""
                lines.append(f"{cfg.name}|fields:[{','.join(field_names)}{suffix}]")
            lines.append("")

        # Pydantic settings
        pydantic = result.get('pydantic_settings', [])
        if pydantic:
            lines.append("[PYDANTIC_SETTINGS]")
            for settings in pydantic:
                parts = [settings.name]
                if settings.env_prefix:
                    parts.append(f"prefix:{settings.env_prefix}")
                if settings.env_file:
                    parts.append(f"env_file:{settings.env_file}")
                field_count = len(settings.fields)
                parts.append(f"fields:{field_count}")
                lines.append("|".join(parts))
            lines.append("")

        # Environment variables
        env_vars = result.get('env_vars', [])
        if env_vars:
            lines.append("[ENV_VARS]")
            required = [v.name for v in env_vars if v.required]
            optional = [v.name for v in env_vars if not v.required]

            if required:
                lines.append(f"required:[{','.join(required[:10])}]")
            if optional:
                lines.append(f"optional:[{','.join(optional[:10])}]")
            lines.append("")

        # Config files
        config_files = result.get('config_files', [])
        if config_files:
            lines.append("[CONFIG_FILES]")
            for cf in config_files:
                lines.append(f"{cf.path}|format:{cf.format}|loader:{cf.loader}")

        return "\n".join(lines)


# Convenience function
def extract_config(content: str) -> Dict[str, Any]:
    """Extract configuration components from Python content."""
    extractor = ConfigExtractor()
    return extractor.extract(content)
