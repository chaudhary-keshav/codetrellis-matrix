"""
R API Extractor for CodeTrellis

Extracts API/web framework definitions from R source code:
- Plumber API routes (@get, @post, @put, @delete, @filter)
- Shiny server/UI definitions (shinyApp, shinyServer, renderUI)
- RestRserve endpoints
- OpenCPU API functions
- Ambiorix web framework routes
- Fiery web server routes
- httpuv handler functions

Supports: R 3.x through R 4.4+
Part of CodeTrellis v4.26 - R Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RRouteInfo:
    """Information about an R web API route."""
    method: str  # GET, POST, PUT, DELETE, etc.
    path: str
    handler: str
    framework: str = "plumber"
    description: str = ""
    parameters: List[str] = field(default_factory=list)
    response_type: str = ""  # From @serializer
    middleware: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class RShinyComponentInfo:
    """Information about a Shiny component."""
    name: str
    kind: str = "server"  # server, ui, module_server, module_ui, reactive, observer, output
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    reactive_values: List[str] = field(default_factory=list)
    observers: List[str] = field(default_factory=list)
    renders: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class RAPIEndpointInfo:
    """Information about a generic R API endpoint."""
    name: str
    framework: str  # restrserve, opencpu, ambiorix, fiery, httpuv
    method: str = "GET"
    path: str = ""
    handler: str = ""
    file: str = ""
    line_number: int = 0


class RAPIExtractor:
    """
    Extracts R API/web framework definitions.

    Frameworks detected:
    - Plumber (REST API)
    - Shiny (reactive web apps)
    - RestRserve
    - OpenCPU
    - Ambiorix
    - Fiery
    - httpuv
    - Golem (Shiny modules)
    - Rhino (Shiny enterprise framework)
    """

    # ===== Plumber Routes =====
    # Plumber decorators: #* @get /path or #* @post /path
    PLUMBER_ROUTE = re.compile(
        r"#\*\s*@(get|post|put|delete|patch|head|options)\s+(/[^\n]*)",
        re.IGNORECASE | re.MULTILINE
    )

    # Plumber filter: #* @filter name
    PLUMBER_FILTER = re.compile(
        r"#\*\s*@filter\s+(\w+)",
        re.MULTILINE
    )

    # Plumber serializer: #* @serializer json/csv/html
    PLUMBER_SERIALIZER = re.compile(
        r"#\*\s*@serializer\s+(\w+)",
        re.MULTILINE
    )

    # Plumber param: #* @param name type description
    PLUMBER_PARAM = re.compile(
        r"#\*\s*@param\s+(\w+)\s+(\w+)?\s*(.*)?",
        re.MULTILINE
    )

    # Plumber tag: #* @tag name
    PLUMBER_TAG = re.compile(
        r"#\*\s*@tag\s+(\w+)",
        re.MULTILINE
    )

    # Plumber programmatic: pr_get("/path", handler), pr_post(...), etc.
    PLUMBER_PROGRAMMATIC = re.compile(
        r'pr_(get|post|put|delete|patch|head)\s*\(\s*["\']([^"\']+)["\']\s*,\s*(\w+)',
        re.MULTILINE
    )

    # Plumber mount: pr_mount("/prefix", sub_api)
    PLUMBER_MOUNT = re.compile(
        r'pr_mount\s*\(\s*["\']([^"\']+)["\']\s*,\s*(\w+)',
        re.MULTILINE
    )

    # ===== Shiny =====
    # shinyApp(ui, server)
    SHINY_APP = re.compile(
        r'shinyApp\s*\(\s*(?:ui\s*=\s*)?(\w+)\s*,\s*(?:server\s*=\s*)?(\w+)',
        re.MULTILINE
    )

    # Server function: server <- function(input, output, session)
    SHINY_SERVER = re.compile(
        r'(\w+)\s*(?:<-|=)\s*function\s*\(\s*input\s*,\s*output(?:\s*,\s*session)?\s*\)',
        re.MULTILINE
    )

    # Shiny module server: moduleServer(id, function(input, output, session))
    SHINY_MODULE_SERVER = re.compile(
        r'(\w+)\s*(?:<-|=)\s*function\s*\(\s*id.*?\)\s*\{[^}]*?moduleServer\s*\(',
        re.DOTALL
    )

    # Shiny module UI: ns <- NS(id)
    SHINY_MODULE_UI = re.compile(
        r'(\w+)\s*(?:<-|=)\s*function\s*\(\s*id.*?\)\s*\{[^}]*?NS\s*\(',
        re.DOTALL
    )

    # Reactive values: reactiveValues(), reactiveVal(), reactive()
    SHINY_REACTIVE = re.compile(
        r'(\w+)\s*(?:<-|=)\s*(?:reactiveValues|reactiveVal|reactive)\s*\(',
        re.MULTILINE
    )

    # Observe/observeEvent
    SHINY_OBSERVER = re.compile(
        r'(?:observeEvent|observe)\s*\(\s*(?:input\$(\w+)|(\w+)\(\))',
        re.MULTILINE
    )

    # Render functions: renderText, renderPlot, renderTable, renderUI, renderDataTable
    SHINY_RENDER = re.compile(
        r'output\$(\w+)\s*(?:<-|=)\s*(render\w+)\s*\(',
        re.MULTILINE
    )

    # ===== RestRserve =====
    RESTRSERVE_ROUTE = re.compile(
        r'app\$add_(?:get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']\s*,\s*(\w+)',
        re.MULTILINE
    )

    # ===== Ambiorix =====
    AMBIORIX_ROUTE = re.compile(
        r'app\$(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']\s*,',
        re.MULTILINE
    )

    # ===== Fiery =====
    FIERY_ROUTE = re.compile(
        r'app\$on\s*\(\s*["\'](?:request|header|before-request|after-request|after-response)["\']',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract all R API definitions from source code."""
        result = {
            "routes": [],
            "shiny_components": [],
            "api_endpoints": [],
        }

        lines = content.split('\n')

        # Plumber routes
        result["routes"].extend(self._extract_plumber_routes(content, file_path, lines))
        result["routes"].extend(self._extract_plumber_programmatic(content, file_path))

        # Shiny components
        result["shiny_components"].extend(self._extract_shiny_components(content, file_path, lines))

        # RestRserve
        result["api_endpoints"].extend(self._extract_restrserve(content, file_path))

        # Ambiorix
        result["api_endpoints"].extend(self._extract_ambiorix(content, file_path))

        return result

    def _extract_plumber_routes(self, content: str, file_path: str, lines: List[str]) -> List[RRouteInfo]:
        """Extract Plumber decorator-based routes."""
        routes = []

        # Process line by line to associate decorators with handler functions
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check for plumber route decorator
            route_m = re.match(r"#\*\s*@(get|post|put|delete|patch|head|options)\s+(/[^\n]*)", line, re.IGNORECASE)
            if route_m:
                method = route_m.group(1).upper()
                path = route_m.group(2).strip()

                # Collect additional decorators
                params = []
                serializer = ""
                tags = []
                description = ""
                filters = []

                # Look backwards for description and other tags
                j = i - 1
                while j >= 0 and lines[j].strip().startswith('#*'):
                    tag_line = lines[j].strip()
                    param_m = self.PLUMBER_PARAM.match(tag_line)
                    if param_m:
                        params.append(param_m.group(1))
                    serial_m = self.PLUMBER_SERIALIZER.match(tag_line)
                    if serial_m:
                        serializer = serial_m.group(1)
                    tag_m = self.PLUMBER_TAG.match(tag_line)
                    if tag_m:
                        tags.append(tag_m.group(1))
                    filter_m = self.PLUMBER_FILTER.match(tag_line)
                    if filter_m:
                        filters.append(filter_m.group(1))
                    if not any([param_m, serial_m, tag_m, filter_m]):
                        desc_m = re.match(r'#\*\s+(.+)', tag_line)
                        if desc_m and not desc_m.group(1).startswith('@'):
                            description = desc_m.group(1)
                    j -= 1

                # Find handler function on next line(s)
                handler = ""
                k = i + 1
                while k < len(lines):
                    func_line = lines[k].strip()
                    if not func_line or func_line.startswith('#'):
                        k += 1
                        continue
                    func_m = re.match(r'(?:function|(\w+)\s*(?:<-|=)\s*function)\s*\(', func_line)
                    if func_m:
                        handler = func_m.group(1) or "anonymous"
                    break

                routes.append(RRouteInfo(
                    method=method,
                    path=path,
                    handler=handler,
                    framework="plumber",
                    description=description,
                    parameters=params,
                    response_type=serializer,
                    middleware=filters,
                    tags=tags,
                    file=file_path,
                    line_number=i + 1,
                ))
            i += 1

        return routes

    def _extract_plumber_programmatic(self, content: str, file_path: str) -> List[RRouteInfo]:
        """Extract Plumber programmatic routes (pr_get, pr_post, etc.)."""
        routes = []
        for m in self.PLUMBER_PROGRAMMATIC.finditer(content):
            method = m.group(1).upper()
            path = m.group(2)
            handler = m.group(3)
            line_num = content[:m.start()].count('\n') + 1

            routes.append(RRouteInfo(
                method=method,
                path=path,
                handler=handler,
                framework="plumber",
                file=file_path,
                line_number=line_num,
            ))
        return routes

    def _extract_shiny_components(self, content: str, file_path: str, lines: List[str]) -> List[RShinyComponentInfo]:
        """Extract Shiny application components."""
        components = []

        # Shiny server functions
        for m in self.SHINY_SERVER.finditer(content):
            name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1
            comp = RShinyComponentInfo(
                name=name,
                kind="server",
                file=file_path,
                line_number=line_num,
            )

            # Extract outputs and observers from server body
            body = self._get_block_body(content, m.end())
            if body:
                for render_m in self.SHINY_RENDER.finditer(body):
                    comp.outputs.append(render_m.group(1))
                    comp.renders.append(render_m.group(2))
                for obs_m in self.SHINY_OBSERVER.finditer(body):
                    inp = obs_m.group(1) or obs_m.group(2)
                    if inp:
                        comp.observers.append(inp)
                for react_m in self.SHINY_REACTIVE.finditer(body):
                    comp.reactive_values.append(react_m.group(1))

            components.append(comp)

        # Shiny module servers
        for m in self.SHINY_MODULE_SERVER.finditer(content):
            name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1
            components.append(RShinyComponentInfo(
                name=name,
                kind="module_server",
                file=file_path,
                line_number=line_num,
            ))

        # Shiny module UIs
        for m in self.SHINY_MODULE_UI.finditer(content):
            name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1
            # Don't add if already added as module_server
            if not any(c.name == name for c in components):
                components.append(RShinyComponentInfo(
                    name=name,
                    kind="module_ui",
                    file=file_path,
                    line_number=line_num,
                ))

        return components

    def _extract_restrserve(self, content: str, file_path: str) -> List[RAPIEndpointInfo]:
        """Extract RestRserve endpoints."""
        endpoints = []
        for m in self.RESTRSERVE_ROUTE.finditer(content):
            path = m.group(1)
            handler = m.group(2)
            line_num = content[:m.start()].count('\n') + 1

            # Determine method from function name
            method_m = re.search(r'add_(get|post|put|delete|patch)', content[m.start():m.start() + 30])
            method = method_m.group(1).upper() if method_m else "GET"

            endpoints.append(RAPIEndpointInfo(
                name=handler,
                framework="restrserve",
                method=method,
                path=path,
                handler=handler,
                file=file_path,
                line_number=line_num,
            ))
        return endpoints

    def _extract_ambiorix(self, content: str, file_path: str) -> List[RAPIEndpointInfo]:
        """Extract Ambiorix routes."""
        endpoints = []
        for m in self.AMBIORIX_ROUTE.finditer(content):
            method = m.group(1).upper()
            path = m.group(2)
            line_num = content[:m.start()].count('\n') + 1

            endpoints.append(RAPIEndpointInfo(
                name=f"{method} {path}",
                framework="ambiorix",
                method=method,
                path=path,
                file=file_path,
                line_number=line_num,
            ))
        return endpoints

    def _get_block_body(self, content: str, start: int) -> Optional[str]:
        """Get the body of a block starting from a position."""
        idx = content.find('{', start)
        if idx == -1:
            return None
        depth = 0
        i = idx
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return content[idx:i + 1]
            i += 1
        return None
