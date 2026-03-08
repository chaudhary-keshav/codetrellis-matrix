"""
NestJS Config Extractor - Per-file extraction of @nestjs/config patterns.

Supports:
- ConfigModule.forRoot() detection
- ConfigService usage
- @nestjs/config environment variable extraction
- .env file references
- Custom configuration factories
- Configuration namespaces
- Joi/class-validator validation schemas
- NestJS 7.x through 10.x patterns
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class NestConfigModuleInfo:
    """ConfigModule.forRoot() configuration."""
    file: str = ""
    line_number: int = 0
    is_global: bool = False
    env_file_path: str = ""
    has_validation: bool = False
    validation_schema: str = ""
    config_factories: List[str] = field(default_factory=list)
    expand_variables: bool = False


@dataclass
class NestEnvVarInfo:
    """An environment variable referenced via ConfigService or process.env."""
    name: str
    file: str = ""
    line_number: int = 0
    source: str = ""  # configService.get, process.env
    default_value: str = ""
    type_hint: str = ""  # string, number, boolean
    is_required: bool = False


@dataclass
class NestConfigServiceUsageInfo:
    """A ConfigService.get() or ConfigService.getOrThrow() usage."""
    key: str
    file: str = ""
    line_number: int = 0
    method: str = "get"  # get, getOrThrow
    type_param: str = ""  # Generic type param <string>, <number>
    has_default: bool = False
    namespace: str = ""  # Namespace prefix for config keys


class NestConfigExtractor:
    """Extracts NestJS configuration information from a single file."""

    # ConfigModule.forRoot() pattern
    CONFIG_MODULE_PATTERN = re.compile(
        r'ConfigModule\s*\.\s*(forRoot|forRootAsync)\s*\(\s*(\{[^}]*(?:\{[^}]*\}[^}]*)*\})?\s*\)',
        re.DOTALL
    )

    # ConfigService.get() / ConfigService.getOrThrow()
    CONFIG_GET_PATTERN = re.compile(
        r'(?:configService|this\.configService|config)\s*\.\s*(get|getOrThrow)\s*'
        r'(?:<(\w+)>)?\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'
        r'(?:\s*,\s*([^)]+))?\s*\)',
    )

    # process.env references
    PROCESS_ENV_PATTERN = re.compile(
        r'process\.env\.(\w+)(?:\s*\|\|\s*([^\s;,\)]+))?'
    )

    # registerAs() config factory
    REGISTER_AS_PATTERN = re.compile(
        r"registerAs\s*\(\s*['\"`](\w+)['\"`]"
    )

    # Joi validation schema
    JOI_SCHEMA_PATTERN = re.compile(
        r'Joi\.\w+\(\)\s*\.(?:keys|object)\s*\(\s*\{'
    )

    # .env file reference
    ENV_FILE_PATTERN = re.compile(
        r"envFilePath\s*:\s*['\"`]([^'\"`]+)['\"`]"
    )

    # isGlobal
    IS_GLOBAL_PATTERN = re.compile(r'isGlobal\s*:\s*true')

    # expandVariables
    EXPAND_VARS_PATTERN = re.compile(r'expandVariables\s*:\s*true')

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract configuration information from a NestJS source file."""
        config_modules: List[NestConfigModuleInfo] = []
        env_vars: List[NestEnvVarInfo] = []
        config_usages: List[NestConfigServiceUsageInfo] = []

        # ConfigModule.forRoot()
        for match in self.CONFIG_MODULE_PATTERN.finditer(content):
            method = match.group(1)
            options = match.group(2) or ''
            line_num = content[:match.start()].count('\n') + 1

            env_file = ''
            ef_match = self.ENV_FILE_PATTERN.search(options)
            if ef_match:
                env_file = ef_match.group(1)

            config_factories = []
            for cf_match in self.REGISTER_AS_PATTERN.finditer(content):
                config_factories.append(cf_match.group(1))

            config_modules.append(NestConfigModuleInfo(
                file=file_path,
                line_number=line_num,
                is_global=bool(self.IS_GLOBAL_PATTERN.search(options)),
                env_file_path=env_file,
                has_validation=bool(self.JOI_SCHEMA_PATTERN.search(content)),
                validation_schema='Joi' if self.JOI_SCHEMA_PATTERN.search(content) else '',
                config_factories=config_factories,
                expand_variables=bool(self.EXPAND_VARS_PATTERN.search(options)),
            ))

        # ConfigService.get() / getOrThrow()
        for match in self.CONFIG_GET_PATTERN.finditer(content):
            method = match.group(1)
            type_param = match.group(2) or ''
            key = match.group(3)
            default_val = (match.group(4) or '').strip()
            line_num = content[:match.start()].count('\n') + 1

            namespace = ''
            if '.' in key:
                namespace = key.split('.')[0]

            config_usages.append(NestConfigServiceUsageInfo(
                key=key,
                file=file_path,
                line_number=line_num,
                method=method,
                type_param=type_param,
                has_default=bool(default_val),
                namespace=namespace,
            ))

            env_vars.append(NestEnvVarInfo(
                name=key,
                file=file_path,
                line_number=line_num,
                source='configService.' + method,
                default_value=default_val.strip("'\"` "),
                type_hint=type_param.lower() if type_param else '',
                is_required=method == 'getOrThrow',
            ))

        # process.env references
        for match in self.PROCESS_ENV_PATTERN.finditer(content):
            var_name = match.group(1)
            default_val = match.group(2) or ''
            line_num = content[:match.start()].count('\n') + 1

            env_vars.append(NestEnvVarInfo(
                name=var_name,
                file=file_path,
                line_number=line_num,
                source='process.env',
                default_value=default_val.strip("'\"` "),
                is_required=not bool(default_val),
            ))

        return {
            "config_modules": config_modules,
            "env_vars": env_vars,
            "config_usages": config_usages,
        }
