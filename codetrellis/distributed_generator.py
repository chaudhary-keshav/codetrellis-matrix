"""
CodeTrellis Distributed Generator
===========================

Creates .codetrellis files inside each component/module folder.
This allows AI to read local context on-demand instead of loading everything.

Structure:
  /src/app/components/
    dashboard/
      dashboard.component.ts
      .codetrellis  <-- Generated file with component summary
    live-trading/
      live-trading.component.ts
      .codetrellis  <-- Generated file with component summary
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ComponentSummary:
    """Summary of an Angular component or NestJS module"""
    name: str
    type: str  # component, service, module, controller
    folder: str

    # Angular specific
    inputs: List[str] = None
    outputs: List[str] = None
    signals: List[str] = None

    # Common
    methods: List[str] = None
    interfaces: List[Dict] = None
    imports: List[str] = None

    # NestJS specific
    routes: List[Dict] = None
    injections: List[str] = None

    def __post_init__(self):
        self.inputs = self.inputs or []
        self.outputs = self.outputs or []
        self.signals = self.signals or []
        self.methods = self.methods or []
        self.interfaces = self.interfaces or []
        self.imports = self.imports or []
        self.routes = self.routes or []
        self.injections = self.injections or []


class DistributedCodeTrellisGenerator:
    """
    Generates .codetrellis files in each component/module folder.

    Usage:
        generator = DistributedCodeTrellisGenerator()
        generator.generate("/path/to/angular-project")
    """

    def __init__(self):
        self.stats = {
            "components": 0,
            "services": 0,
            "modules": 0,
            "total_files": 0,
        }

    def generate(self, project_path: str) -> Dict[str, int]:
        """
        Generate .codetrellis files throughout the project.

        Args:
            project_path: Root path of the project

        Returns:
            Statistics about generated files
        """
        root = Path(project_path)

        # Find src directory
        src_path = root / "src"
        if not src_path.exists():
            src_path = root

        print(f"[CodeTrellis] Generating distributed .codetrellis files in: {src_path}")

        # Walk through all directories
        for dirpath, dirnames, filenames in os.walk(src_path):
            # Skip ignored directories
            dirnames[:] = [d for d in dirnames if d not in {
                'node_modules', 'dist', '.angular', '.git', '__pycache__'
            }]

            dir_path = Path(dirpath)

            # Check if this folder has TypeScript files
            ts_files = [f for f in filenames if f.endswith('.ts') and not f.endswith('.spec.ts')]

            if ts_files:
                # Analyze and generate .codetrellis for this folder
                ct_content = self._analyze_folder(dir_path, ts_files)

                if ct_content:
                    codetrellis_file = dir_path / ".codetrellis"
                    codetrellis_file.write_text(ct_content, encoding="utf-8")
                    self.stats["total_files"] += 1
                    print(f"  ✓ {dir_path.relative_to(root)}")

        print(f"\n[CodeTrellis] Generated {self.stats['total_files']} .codetrellis files")
        return self.stats

    def _analyze_folder(self, folder: Path, ts_files: List[str]) -> Optional[str]:
        """Analyze a folder and generate .codetrellis content"""
        lines = []
        folder_name = folder.name

        # Detect folder type
        has_component = any('.component.ts' in f for f in ts_files)
        has_service = any('.service.ts' in f for f in ts_files)
        has_module = any('.module.ts' in f for f in ts_files)
        has_controller = any('.controller.ts' in f for f in ts_files)

        if has_component:
            lines.extend(self._analyze_angular_component(folder, ts_files))
            self.stats["components"] += 1

        if has_service:
            lines.extend(self._analyze_service(folder, ts_files))
            self.stats["services"] += 1

        if has_module:
            lines.extend(self._analyze_module(folder, ts_files))
            self.stats["modules"] += 1

        if has_controller:
            lines.extend(self._analyze_controller(folder, ts_files))

        if not lines:
            return None

        return '\n'.join(lines)

    def _analyze_angular_component(self, folder: Path, ts_files: List[str]) -> List[str]:
        """Analyze Angular component files"""
        lines = []

        for filename in ts_files:
            if '.component.ts' not in filename:
                continue

            file_path = folder / filename
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            # Extract component name
            name_match = re.search(r'export\s+class\s+(\w+Component)', content)
            if not name_match:
                continue

            component_name = name_match.group(1)
            lines.append(f"# {component_name}")

            # Detect features
            features = []
            if 'standalone: true' in content or 'standalone:true' in content:
                features.append('standalone')
            if 'OnPush' in content:
                features.append('OnPush')
            if 'signal(' in content or 'computed(' in content:
                features.append('signals')

            lines.append(f"type=component|{','.join(features)}" if features else "type=component")

            # Extract inputs (both @Input and input())
            inputs = []

            # Old style @Input()
            old_inputs = re.findall(r'@Input\(\)\s*(\w+)', content)
            inputs.extend(old_inputs)

            # New style input<T>() or input()
            new_inputs = re.findall(r'readonly\s+(\w+)\s*=\s*input(?:<[^>]+>)?\(', content)
            inputs.extend(new_inputs)

            if inputs:
                lines.append(f"inputs:{','.join(inputs)}")

            # Extract outputs
            outputs = []
            old_outputs = re.findall(r'@Output\(\)\s*(\w+)', content)
            outputs.extend(old_outputs)
            new_outputs = re.findall(r'readonly\s+(\w+)\s*=\s*output(?:<[^>]+>)?\(', content)
            outputs.extend(new_outputs)

            if outputs:
                lines.append(f"outputs:{','.join(outputs)}")

            # Extract signals (computed, signal)
            signals = re.findall(r'readonly\s+(\w+)\s*=\s*(?:computed|signal)\(', content)
            if signals:
                lines.append(f"signals:{','.join(signals)}")

            # Extract public methods (simplified)
            methods = re.findall(r'(?:public\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{', content)
            # Filter out lifecycle hooks and common patterns
            methods = [m for m in methods if m not in [
                'constructor', 'ngOnInit', 'ngOnDestroy', 'ngOnChanges',
                'ngAfterViewInit', 'if', 'for', 'while', 'switch'
            ]]
            if methods:
                lines.append(f"methods:{','.join(methods[:10])}")  # Limit to 10

            # Extract interfaces defined in this file
            interfaces = self._extract_interfaces(content)
            if interfaces:
                lines.append(f"interfaces:{interfaces}")

            lines.append("")  # Empty line between components

        return lines

    def _analyze_service(self, folder: Path, ts_files: List[str]) -> List[str]:
        """Analyze service files"""
        lines = []

        for filename in ts_files:
            if '.service.ts' not in filename:
                continue

            file_path = folder / filename
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            # Extract service name
            name_match = re.search(r'export\s+class\s+(\w+Service)', content)
            if not name_match:
                continue

            service_name = name_match.group(1)
            lines.append(f"# {service_name}")
            lines.append("type=service|injectable")

            # Extract injected dependencies
            ctor_match = re.search(r'constructor\s*\(([^)]+)\)', content, re.DOTALL)
            if ctor_match:
                ctor_body = ctor_match.group(1)
                deps = re.findall(r'(?:private|public|readonly)\s+\w+:\s*(\w+)', ctor_body)
                if deps:
                    lines.append(f"deps:{','.join(deps)}")

            # Extract public methods
            methods = re.findall(r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{', content)
            methods = [m for m in methods if m not in ['constructor', 'if', 'for', 'while']]
            if methods:
                lines.append(f"methods:{','.join(methods[:15])}")

            lines.append("")

        return lines

    def _analyze_module(self, folder: Path, ts_files: List[str]) -> List[str]:
        """Analyze Angular/NestJS module files"""
        lines = []

        for filename in ts_files:
            if '.module.ts' not in filename:
                continue

            file_path = folder / filename
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            # Extract module name
            name_match = re.search(r'export\s+class\s+(\w+Module)', content)
            if not name_match:
                continue

            module_name = name_match.group(1)
            lines.append(f"# {module_name}")
            lines.append("type=module")

            # Extract imports
            imports_match = re.search(r'imports:\s*\[([^\]]+)\]', content, re.DOTALL)
            if imports_match:
                imports = re.findall(r'(\w+)', imports_match.group(1))
                if imports:
                    lines.append(f"imports:{','.join(imports[:10])}")

            # Extract exports
            exports_match = re.search(r'exports:\s*\[([^\]]+)\]', content, re.DOTALL)
            if exports_match:
                exports = re.findall(r'(\w+)', exports_match.group(1))
                if exports:
                    lines.append(f"exports:{','.join(exports[:10])}")

            # Extract providers (NestJS)
            providers_match = re.search(r'providers:\s*\[([^\]]+)\]', content, re.DOTALL)
            if providers_match:
                providers = re.findall(r'(\w+)', providers_match.group(1))
                if providers:
                    lines.append(f"providers:{','.join(providers[:10])}")

            lines.append("")

        return lines

    def _analyze_controller(self, folder: Path, ts_files: List[str]) -> List[str]:
        """Analyze NestJS controller files"""
        lines = []

        for filename in ts_files:
            if '.controller.ts' not in filename:
                continue

            file_path = folder / filename
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            # Extract controller name and prefix
            ctrl_match = re.search(r"@Controller\(['\"]([^'\"]*)['\"]", content)
            prefix = ctrl_match.group(1) if ctrl_match else '/'

            name_match = re.search(r'export\s+class\s+(\w+Controller)', content)
            if not name_match:
                continue

            ctrl_name = name_match.group(1)
            lines.append(f"# {ctrl_name}")
            lines.append(f"type=controller|prefix:{prefix}")

            # Extract routes
            routes = []
            for method in ['Get', 'Post', 'Put', 'Delete', 'Patch']:
                matches = re.findall(rf'@{method}\([\'"]?([^\'")\s]*)[\'"]?\)', content)
                for path in matches:
                    routes.append(f"{method.upper()}:{path or '/'}")

            if routes:
                lines.append(f"routes:{';'.join(routes[:10])}")

            lines.append("")

        return lines

    def _extract_interfaces(self, content: str) -> str:
        """Extract interface definitions in compact format"""
        interfaces = []

        # Find interface definitions
        interface_pattern = r'(?:export\s+)?interface\s+(\w+)\s*\{([^}]+)\}'
        matches = re.findall(interface_pattern, content, re.DOTALL)

        for name, body in matches[:3]:  # Limit to 3 interfaces
            # Extract field names
            fields = re.findall(r'(?:readonly\s+)?(\w+)(?:\?)?:', body)
            if fields:
                interfaces.append(f"{name}{{{','.join(fields[:5])}}}")  # Limit to 5 fields

        return ','.join(interfaces)


def generate_distributed(project_path: str) -> Dict[str, int]:
    """Generate distributed .codetrellis files for a project"""
    generator = DistributedCodeTrellisGenerator()
    return generator.generate(project_path)


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    stats = generate_distributed(path)
    print(f"\nStats: {stats}")
