"""
PowerShell API Extractor for CodeTrellis

Extracts API and framework patterns from PowerShell source code:
- REST API endpoints (Invoke-RestMethod, Invoke-WebRequest, Pode, Polaris)
- DSC configurations and resources
- Pester test definitions
- Module commands and exports
- Remoting patterns (Enter-PSSession, Invoke-Command)
- Azure/AWS/GCP cmdlets
- Graph API calls

Supports PowerShell 1.0 through 7.4+ (PowerShell Core / pwsh).
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PSRouteInfo:
    """Information about a PowerShell REST API route."""
    method: str
    path: str
    handler: Optional[str] = None
    framework: str = ""
    file: str = ""
    line_number: int = 0
    middleware: List[str] = field(default_factory=list)


@dataclass
class PSCmdletBindingInfo:
    """Information about a cmdlet binding / command pattern."""
    name: str
    verb: str = ""
    noun: str = ""
    module: str = ""
    file: str = ""
    line_number: int = 0
    category: str = ""  # azure, aws, gcp, exchange, ad, graph


@dataclass
class PSDSCConfigInfo:
    """Information about a DSC configuration."""
    name: str
    file: str = ""
    line_number: int = 0
    resources: List[str] = field(default_factory=list)
    nodes: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)


@dataclass
class PSPesterTestInfo:
    """Information about a Pester test definition."""
    name: str
    file: str = ""
    line_number: int = 0
    test_type: str = ""  # Describe, Context, It, BeforeAll, AfterAll
    parent: Optional[str] = None
    tags: List[str] = field(default_factory=list)


class PowerShellAPIExtractor:
    """
    Extracts API and framework patterns from PowerShell source code.

    Detects:
    - Pode web server routes (Add-PodeRoute)
    - Polaris web server routes
    - REST API calls (Invoke-RestMethod)
    - DSC configurations
    - Pester test blocks
    - Azure/AWS/GCP cmdlet patterns
    - Microsoft Graph API
    - Remoting sessions
    """

    # Pode routes
    PODE_ROUTE_PATTERN = re.compile(
        r"Add-PodeRoute\s+"
        r"(?:-Method\s+['\"]?(\w+)['\"]?\s+)?"
        r"(?:-Path\s+['\"]([^'\"]+)['\"]?\s+)?"
        r"(?:-ScriptBlock\s+\{)?",
        re.IGNORECASE | re.MULTILINE
    )

    # Pode route alternative syntax
    PODE_ROUTE_ALT = re.compile(
        r"Add-PodeRoute\s+-Method\s+(\w+)\s+-Path\s+'([^']+)'",
        re.IGNORECASE
    )

    # Polaris routes
    POLARIS_ROUTE_PATTERN = re.compile(
        r"New-PolarisRoute\s+-Path\s+['\"]([^'\"]+)['\"]"
        r"\s+-Method\s+['\"]?(\w+)['\"]?",
        re.IGNORECASE
    )

    # Invoke-RestMethod / Invoke-WebRequest
    REST_CALL_PATTERN = re.compile(
        r"(Invoke-(?:Rest|Web)(?:Method|Request))"
        r"(?:\s+-Method\s+['\"]?(\w+)['\"]?)?"
        r"(?:\s+-Uri\s+['\"]([^'\"]+)['\"]?)?",
        re.IGNORECASE
    )

    # DSC Configuration
    DSC_CONFIG_PATTERN = re.compile(
        r'^\s*Configuration\s+(\w+)\s*(?:\(([^)]*)\))?\s*\{',
        re.MULTILINE | re.IGNORECASE
    )

    # DSC Node
    DSC_NODE_PATTERN = re.compile(
        r'^\s*Node\s+(?:\$(\w+)|["\']([^"\']+)["\'])\s*\{',
        re.MULTILINE | re.IGNORECASE
    )

    # DSC Resource usage
    DSC_RESOURCE_USAGE = re.compile(
        r'^\s+(\w+)\s+["\']?(\w+)["\']?\s*\{',
        re.MULTILINE
    )

    # Pester Describe/Context/It
    PESTER_DESCRIBE = re.compile(
        r"^\s*Describe\s+['\"]([^'\"]+)['\"]"
        r"(?:\s+-Tag\s+['\"]([^'\"]+)['\"])?",
        re.MULTILINE | re.IGNORECASE
    )

    PESTER_CONTEXT = re.compile(
        r"^\s*Context\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE | re.IGNORECASE
    )

    PESTER_IT = re.compile(
        r"^\s*It\s+['\"]([^'\"]+)['\"]"
        r"(?:\s+-Tag\s+['\"]([^'\"]+)['\"])?",
        re.MULTILINE | re.IGNORECASE
    )

    # Azure cmdlet patterns
    AZURE_CMDLET = re.compile(
        r'\b((?:Get|Set|New|Remove|Start|Stop|Restart|Update)-Az\w+)',
        re.IGNORECASE
    )

    # AWS cmdlet patterns
    AWS_CMDLET = re.compile(
        r'\b((?:Get|Set|New|Remove|Start|Stop|Write|Read)-(?:EC2|S3|IAM|Lambda|SNS|SQS|DDB|CF|ECS|EKS|RDS|CW)\w*)',
        re.IGNORECASE
    )

    # Graph API patterns
    GRAPH_PATTERN = re.compile(
        r'\b((?:Get|New|Set|Remove|Update|Invoke)-Mg\w+)',
        re.IGNORECASE
    )

    # Polaris / Pode middleware
    MIDDLEWARE_PATTERN = re.compile(
        r'Add-PodeMiddleware\s+-Name\s+["\'](\w+)["\']',
        re.IGNORECASE
    )

    # Universal Dashboard routes
    UD_ROUTE_PATTERN = re.compile(
        r"New-UDEndpoint\s+-Url\s+['\"]([^'\"]+)['\"]"
        r"(?:\s+-Method\s+['\"]?(\w+)['\"]?)?",
        re.IGNORECASE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract all API patterns from PowerShell source code.

        Returns dict with keys: routes, cmdlet_bindings, dsc_configs, pester_tests
        """
        routes = self._extract_routes(content, file_path)
        cmdlet_bindings = self._extract_cmdlet_bindings(content, file_path)
        dsc_configs = self._extract_dsc_configs(content, file_path)
        pester_tests = self._extract_pester_tests(content, file_path)

        return {
            'routes': routes,
            'cmdlet_bindings': cmdlet_bindings,
            'dsc_configs': dsc_configs,
            'pester_tests': pester_tests,
        }

    def _extract_routes(self, content: str, file_path: str) -> List[PSRouteInfo]:
        """Extract REST API routes from web frameworks."""
        routes = []

        # Pode routes
        for match in self.PODE_ROUTE_PATTERN.finditer(content):
            method = (match.group(1) or 'GET').upper()
            path = match.group(2) or '/'
            line_num = content[:match.start()].count('\n') + 1

            routes.append(PSRouteInfo(
                method=method,
                path=path,
                framework='pode',
                file=file_path,
                line_number=line_num,
            ))

        # Pode alternative syntax
        for match in self.PODE_ROUTE_ALT.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            # Avoid duplicates
            if not any(r.method == method and r.path == path for r in routes):
                routes.append(PSRouteInfo(
                    method=method,
                    path=path,
                    framework='pode',
                    file=file_path,
                    line_number=line_num,
                ))

        # Polaris routes
        for match in self.POLARIS_ROUTE_PATTERN.finditer(content):
            path = match.group(1)
            method = match.group(2).upper()
            line_num = content[:match.start()].count('\n') + 1

            routes.append(PSRouteInfo(
                method=method,
                path=path,
                framework='polaris',
                file=file_path,
                line_number=line_num,
            ))

        # Universal Dashboard endpoints
        for match in self.UD_ROUTE_PATTERN.finditer(content):
            path = match.group(1)
            method = (match.group(2) or 'GET').upper()
            line_num = content[:match.start()].count('\n') + 1

            routes.append(PSRouteInfo(
                method=method,
                path=path,
                framework='universaldashboard',
                file=file_path,
                line_number=line_num,
            ))

        # REST API calls
        for match in self.REST_CALL_PATTERN.finditer(content):
            cmdlet = match.group(1)
            method = (match.group(2) or 'GET').upper()
            uri = match.group(3) or ''
            line_num = content[:match.start()].count('\n') + 1

            if uri:
                routes.append(PSRouteInfo(
                    method=method,
                    path=uri,
                    handler=cmdlet,
                    framework='rest_call',
                    file=file_path,
                    line_number=line_num,
                ))

        return routes

    def _extract_cmdlet_bindings(self, content: str, file_path: str) -> List[PSCmdletBindingInfo]:
        """Extract cloud and platform cmdlet usage patterns."""
        bindings = []
        seen = set()

        # Azure cmdlets
        for match in self.AZURE_CMDLET.finditer(content):
            name = match.group(1)
            if name in seen:
                continue
            seen.add(name)
            line_num = content[:match.start()].count('\n') + 1
            vn = name.split('-', 1)
            bindings.append(PSCmdletBindingInfo(
                name=name,
                verb=vn[0] if len(vn) > 1 else '',
                noun=vn[1] if len(vn) > 1 else name,
                module='Az',
                file=file_path,
                line_number=line_num,
                category='azure',
            ))

        # AWS cmdlets
        for match in self.AWS_CMDLET.finditer(content):
            name = match.group(1)
            if name in seen:
                continue
            seen.add(name)
            line_num = content[:match.start()].count('\n') + 1
            vn = name.split('-', 1)
            bindings.append(PSCmdletBindingInfo(
                name=name,
                verb=vn[0] if len(vn) > 1 else '',
                noun=vn[1] if len(vn) > 1 else name,
                module='AWS',
                file=file_path,
                line_number=line_num,
                category='aws',
            ))

        # Microsoft Graph
        for match in self.GRAPH_PATTERN.finditer(content):
            name = match.group(1)
            if name in seen:
                continue
            seen.add(name)
            line_num = content[:match.start()].count('\n') + 1
            vn = name.split('-', 1)
            bindings.append(PSCmdletBindingInfo(
                name=name,
                verb=vn[0] if len(vn) > 1 else '',
                noun=vn[1] if len(vn) > 1 else name,
                module='Microsoft.Graph',
                file=file_path,
                line_number=line_num,
                category='graph',
            ))

        return bindings

    def _extract_dsc_configs(self, content: str, file_path: str) -> List[PSDSCConfigInfo]:
        """Extract DSC configurations."""
        configs = []

        for match in self.DSC_CONFIG_PATTERN.finditer(content):
            name = match.group(1)
            params_str = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1

            # Extract parameters
            parameters = []
            if params_str:
                param_names = re.findall(r'\$(\w+)', params_str)
                parameters = param_names

            # Extract body
            body_start = match.end() - 1
            body = self._extract_brace_block(content, body_start)

            resources = []
            nodes = []
            depends = []

            if body:
                # Find Node declarations
                for node_match in self.DSC_NODE_PATTERN.finditer(body):
                    node_name = node_match.group(1) or node_match.group(2)
                    nodes.append(node_name)

                # Find resource usage
                for res_match in self.DSC_RESOURCE_USAGE.finditer(body):
                    res_type = res_match.group(1)
                    if res_type not in ('Node', 'if', 'else', 'foreach', 'switch', 'param', 'Import'):
                        if res_type not in resources:
                            resources.append(res_type)

                # Find DependsOn
                depends_matches = re.findall(r"DependsOn\s*=\s*['\"]?\[(\w+)\](\w+)['\"]?", body)
                depends = [f"[{d[0]}]{d[1]}" for d in depends_matches]

            configs.append(PSDSCConfigInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                resources=resources,
                nodes=nodes,
                parameters=parameters,
                depends_on=depends,
            ))

        return configs

    def _extract_pester_tests(self, content: str, file_path: str) -> List[PSPesterTestInfo]:
        """Extract Pester test definitions."""
        tests = []

        for match in self.PESTER_DESCRIBE.finditer(content):
            name = match.group(1)
            tags_str = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1
            tags = [t.strip() for t in tags_str.split(',')] if tags_str else []

            tests.append(PSPesterTestInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                test_type='Describe',
                tags=tags,
            ))

        for match in self.PESTER_CONTEXT.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            tests.append(PSPesterTestInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                test_type='Context',
            ))

        for match in self.PESTER_IT.finditer(content):
            name = match.group(1)
            tags_str = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1
            tags = [t.strip() for t in tags_str.split(',')] if tags_str else []

            tests.append(PSPesterTestInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                test_type='It',
                tags=tags,
            ))

        return tests

    def _extract_brace_block(self, content: str, start_pos: int) -> Optional[str]:
        """Extract content within balanced braces."""
        if start_pos >= len(content) or content[start_pos] != '{':
            return None
        depth = 0
        i = start_pos
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return content[start_pos + 1:i]
            i += 1
        return content[start_pos + 1:]
