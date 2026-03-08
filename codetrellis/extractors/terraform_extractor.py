"""
CodeTrellis Terraform / IaC Extractor
================================

Phase C (WS-6 / G-14): Extracts infrastructure-as-code context from
Terraform (.tf) files.

Extracts:
- Provider declarations (aws, gcp, azure)
- Resource definitions (type, name)
- Variable definitions (name, type, default, description)
- Output definitions
- Module references
- Backend configuration
- Required provider versions

Output feeds into:
- [INFRASTRUCTURE] section in matrix.prompt
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TerraformVariable:
    """A Terraform variable definition"""
    name: str
    var_type: str = "string"
    default: Optional[str] = None
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"name": self.name, "type": self.var_type}
        if self.description:
            result["description"] = self.description
        if self.default is not None:
            result["default"] = self.default
        return result


@dataclass
class TerraformResource:
    """A Terraform resource or data source"""
    resource_type: str  # e.g., "aws_ecs_service", "aws_rds_instance"
    name: str
    provider: str = ""  # Derived from resource_type prefix
    file_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.resource_type,
            "name": self.name,
            "provider": self.provider,
            "file": self.file_path,
        }


@dataclass
class TerraformOutput:
    """A Terraform output value"""
    name: str
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"name": self.name}
        if self.description:
            result["description"] = self.description
        return result


@dataclass
class TerraformModule:
    """A Terraform module reference"""
    name: str
    source: str
    file_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "source": self.source, "file": self.file_path}


@dataclass
class TerraformInfo:
    """Complete Terraform/IaC project information"""
    providers: List[str] = field(default_factory=list)
    required_version: Optional[str] = None
    backend: Optional[str] = None
    resources: List[TerraformResource] = field(default_factory=list)
    data_sources: List[TerraformResource] = field(default_factory=list)
    variables: List[TerraformVariable] = field(default_factory=list)
    outputs: List[TerraformOutput] = field(default_factory=list)
    modules: List[TerraformModule] = field(default_factory=list)
    files_scanned: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "providers": self.providers,
            "required_version": self.required_version,
            "backend": self.backend,
            "resources": [r.to_dict() for r in self.resources],
            "data_sources": [d.to_dict() for d in self.data_sources],
            "variables": [v.to_dict() for v in self.variables],
            "outputs": [o.to_dict() for o in self.outputs],
            "modules": [m.to_dict() for m in self.modules],
            "files_scanned": self.files_scanned,
        }


class TerraformExtractor:
    """
    Extracts Terraform/IaC infrastructure context from a project.

    Parses .tf files for:
    - Providers, resources, data sources
    - Variables, outputs, modules
    - Backend configuration

    Used by: scanner.py → compressor.py → [INFRASTRUCTURE] section
    """

    def extract(self, root_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract all Terraform information from a project.

        Args:
            root_path: Path to project root

        Returns:
            Dict with Terraform info, or None if no .tf files found
        """
        root = Path(root_path)
        tf_files = self._find_tf_files(root)

        if not tf_files:
            return None

        info = TerraformInfo(files_scanned=len(tf_files))

        for tf_file in tf_files:
            try:
                self._parse_tf_file(tf_file, root, info)
            except Exception:
                pass

        # Deduplicate providers
        info.providers = sorted(set(info.providers))

        return info.to_dict()

    def _find_tf_files(self, root: Path) -> List[Path]:
        """Find all .tf files, excluding hidden directories and vendor."""
        tf_files = []
        ignore_dirs = {'node_modules', '.git', '_archive', '.terraform', 'vendor',
                       '__pycache__', '.venv', 'venv', 'dist', 'build'}

        for dirpath, dirnames, filenames in __import__('os').walk(root):
            dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
            for f in filenames:
                if f.endswith('.tf'):
                    tf_files.append(Path(dirpath) / f)
        return tf_files

    def _parse_tf_file(self, file_path: Path, root: Path, info: TerraformInfo):
        """Parse a single .tf file."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return

        try:
            rel_path = str(file_path.relative_to(root))
        except ValueError:
            rel_path = str(file_path)

        # Terraform block (version, backend)
        terraform_match = re.search(
            r'terraform\s*\{(.*?)\n\}',
            content, re.DOTALL
        )
        if terraform_match:
            block = terraform_match.group(1)
            version_match = re.search(r'required_version\s*=\s*"([^"]+)"', block)
            if version_match:
                info.required_version = version_match.group(1)

            backend_match = re.search(r'backend\s+"(\w+)"', block)
            if backend_match:
                info.backend = backend_match.group(1)

        # Provider blocks
        for provider_match in re.finditer(r'provider\s+"(\w+)"', content):
            info.providers.append(provider_match.group(1))

        # Required providers
        for prov_match in re.finditer(
            r'(\w+)\s*=\s*\{[^}]*source\s*=\s*"([^"]+)"',
            content
        ):
            provider_name = prov_match.group(1)
            if provider_name not in info.providers:
                info.providers.append(provider_name)

        # Resource blocks
        for res_match in re.finditer(
            r'resource\s+"(\w+)"\s+"(\w+)"', content
        ):
            res_type = res_match.group(1)
            res_name = res_match.group(2)
            provider = res_type.split('_')[0] if '_' in res_type else ''
            info.resources.append(TerraformResource(
                resource_type=res_type,
                name=res_name,
                provider=provider,
                file_path=rel_path,
            ))

        # Data source blocks
        for data_match in re.finditer(
            r'data\s+"(\w+)"\s+"(\w+)"', content
        ):
            info.data_sources.append(TerraformResource(
                resource_type=data_match.group(1),
                name=data_match.group(2),
                provider=data_match.group(1).split('_')[0],
                file_path=rel_path,
            ))

        # Variable blocks
        for var_match in re.finditer(
            r'variable\s+"(\w+)"\s*\{(.*?)\n\}',
            content, re.DOTALL
        ):
            var_name = var_match.group(1)
            var_body = var_match.group(2)

            var_type = "string"
            type_match = re.search(r'type\s*=\s*(\S+)', var_body)
            if type_match:
                var_type = type_match.group(1)

            description = ""
            desc_match = re.search(r'description\s*=\s*"([^"]*)"', var_body)
            if desc_match:
                description = desc_match.group(1)

            default = None
            default_match = re.search(r'default\s*=\s*"([^"]*)"', var_body)
            if default_match:
                default = default_match.group(1)
            else:
                default_match = re.search(r'default\s*=\s*(\S+)', var_body)
                if default_match:
                    val = default_match.group(1)
                    if val not in ('{', '['):  # Skip complex defaults
                        default = val

            info.variables.append(TerraformVariable(
                name=var_name,
                var_type=var_type,
                default=default,
                description=description,
            ))

        # Output blocks
        for out_match in re.finditer(
            r'output\s+"(\w+)"\s*\{(.*?)\n\}',
            content, re.DOTALL
        ):
            out_name = out_match.group(1)
            out_body = out_match.group(2)
            description = ""
            desc_match = re.search(r'description\s*=\s*"([^"]*)"', out_body)
            if desc_match:
                description = desc_match.group(1)
            info.outputs.append(TerraformOutput(
                name=out_name,
                description=description,
            ))

        # Module blocks
        for mod_match in re.finditer(
            r'module\s+"(\w+)"\s*\{(.*?)\n\}',
            content, re.DOTALL
        ):
            mod_name = mod_match.group(1)
            mod_body = mod_match.group(2)
            source = ""
            src_match = re.search(r'source\s*=\s*"([^"]*)"', mod_body)
            if src_match:
                source = src_match.group(1)
            info.modules.append(TerraformModule(
                name=mod_name,
                source=source,
                file_path=rel_path,
            ))
