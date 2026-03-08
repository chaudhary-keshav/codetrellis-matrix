"""
Spring Boot Endpoint Extractor v1.0

Extracts Spring Boot REST controllers, WebFlux handlers, and actuator endpoints.

Extracts:
- @RestController / @Controller classes with @RequestMapping
- Handler methods: @GetMapping, @PostMapping, @PutMapping, @DeleteMapping, @PatchMapping
- WebFlux functional endpoints: RouterFunction, HandlerFunction
- Actuator endpoints: @Endpoint, @ReadOperation, @WriteOperation, health indicators
- Request/response body types, path variables, request params
- Content negotiation: consumes, produces
- Validation: @Valid, @Validated
- Exception handling: @ExceptionHandler, @ControllerAdvice, @RestControllerAdvice

Part of CodeTrellis v4.94 - Spring Boot Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class SpringBootControllerInfo:
    """A Spring Boot REST controller or controller class."""
    name: str
    controller_type: str = ""  # rest_controller, controller, controller_advice
    base_path: str = ""  # @RequestMapping at class level
    annotations: List[str] = field(default_factory=list)
    endpoints: List[str] = field(default_factory=list)  # method names
    cross_origin: bool = False
    produces: str = ""
    consumes: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SpringBootEndpointInfo:
    """A Spring Boot REST endpoint (handler method)."""
    method: str = ""  # GET, POST, PUT, DELETE, PATCH
    path: str = ""
    handler_method: str = ""
    controller_class: str = ""
    return_type: str = ""
    request_body_type: str = ""
    path_variables: List[str] = field(default_factory=list)
    request_params: List[str] = field(default_factory=list)
    has_validation: bool = False
    is_async: bool = False  # returns CompletableFuture, Mono, Flux
    is_reactive: bool = False  # WebFlux
    produces: str = ""
    consumes: str = ""
    response_status: str = ""
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class SpringBootActuatorInfo:
    """Spring Boot Actuator custom endpoint."""
    name: str
    endpoint_id: str = ""
    operations: List[str] = field(default_factory=list)  # read, write, delete
    is_web_only: bool = False
    is_jmx_only: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class SpringBootWebFluxHandlerInfo:
    """Spring WebFlux functional endpoint."""
    path: str = ""
    method: str = ""
    handler_function: str = ""
    handler_class: str = ""
    accept_type: str = ""
    content_type: str = ""
    is_nested: bool = False
    file: str = ""
    line_number: int = 0


class SpringBootEndpointExtractor:
    """Extracts Spring Boot REST endpoints, WebFlux handlers, and actuator endpoints."""

    # Controller class
    CONTROLLER_PATTERN = re.compile(
        r'[ \t]*@(RestController|Controller|RestControllerAdvice|ControllerAdvice)'
        r'(?:\([^)]*\))?\s*\n'
        r'((?:[ \t]*@\w+(?:\([^)]*\))?\s*\n)*)'
        r'[ \t]*(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    # Class-level @RequestMapping
    CLASS_REQUEST_MAPPING_PATTERN = re.compile(
        r'@RequestMapping\(\s*(?:value\s*=\s*)?(?:"([^"]*)"|\{[^}]*\})'
        r'(?:\s*,\s*produces\s*=\s*(?:"([^"]*)"|\{[^}]*\}))?'
        r'(?:\s*,\s*consumes\s*=\s*(?:"([^"]*)"|\{[^}]*\}))?'
        r'\s*\)',
        re.MULTILINE
    )

    # Handler methods
    HANDLER_PATTERN = re.compile(
        r'((?:[ \t]*@\w+(?:\([^)]*\))?\s*\n)*)'
        r'[ \t]*@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)'
        r'(?:\(\s*'
        r'(?:value\s*=\s*)?(?:"([^"]*)")?'
        r'(?:\s*,?\s*method\s*=\s*RequestMethod\.(\w+))?'
        r'(?:\s*,?\s*produces\s*=\s*(?:"([^"]*)"|\{[^}]*\}))?'
        r'(?:\s*,?\s*consumes\s*=\s*(?:"([^"]*)"|\{[^}]*\}))?'
        r'[^)]*\))?\s*\n'
        r'(?:[ \t]*@\w+(?:\([^)]*\))?\s*\n)*'
        r'[ \t]*(?:public\s+)?(\S+)\s+(\w+)\s*\(',
        re.MULTILINE
    )

    # @PathVariable
    PATH_VAR_PATTERN = re.compile(
        r'@PathVariable(?:\(\s*(?:value\s*=\s*)?(?:"(\w+)")?\s*\))?\s+\w+\s+(\w+)',
    )

    # @RequestParam
    REQUEST_PARAM_PATTERN = re.compile(
        r'@RequestParam(?:\(\s*(?:value\s*=\s*)?(?:"(\w+)")?\s*(?:,\s*required\s*=\s*(?:true|false))?\s*\))?\s+\w+\s+(\w+)',
    )

    # @RequestBody
    REQUEST_BODY_PATTERN = re.compile(
        r'@RequestBody\s+(?:@\w+(?:\([^)]*\))?\s+)*(?:final\s+)?([\w<>,?]+)\s+(\w+)',
    )

    # @Valid / @Validated
    VALIDATION_PATTERN = re.compile(r'@Valid(?:ated)?\b')

    # @ResponseStatus
    RESPONSE_STATUS_PATTERN = re.compile(
        r'@ResponseStatus\(\s*(?:HttpStatus\.)?(\w+)\s*\)',
    )

    # @CrossOrigin
    CROSS_ORIGIN_PATTERN = re.compile(r'@CrossOrigin')

    # Actuator @Endpoint
    ACTUATOR_ENDPOINT_PATTERN = re.compile(
        r'@Endpoint\(\s*id\s*=\s*"(\w+)"\s*\)\s*\n'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    # Actuator operations
    ACTUATOR_OP_PATTERN = re.compile(
        r'@(ReadOperation|WriteOperation|DeleteOperation)',
    )

    # WebFlux RouterFunction (classic style: route(GET("/path"), handler::method))
    ROUTER_FUNCTION_PATTERN = re.compile(
        r'route\(\s*(\w+)\(\s*"([^"]*)"\s*\)'
        r'(?:\.and\(\s*accept\(\s*(\w+)\s*\)\s*\))?\s*'
        r',\s*(?:(\w+)::(\w+)|\w+\s*->)',
        re.MULTILINE
    )

    # WebFlux RouterFunction builder style: .GET("/path", handler::method)
    ROUTER_BUILDER_PATTERN = re.compile(
        r'\.(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\(\s*"([^"]*)"\s*'
        r',\s*(?:(\w+)::(\w+)|\w+\s*->)',
        re.MULTILINE
    )

    MAPPING_TO_METHOD = {
        'GetMapping': 'GET',
        'PostMapping': 'POST',
        'PutMapping': 'PUT',
        'DeleteMapping': 'DELETE',
        'PatchMapping': 'PATCH',
        'RequestMapping': 'ANY',
    }

    REACTIVE_TYPES = {'Mono', 'Flux', 'ServerResponse', 'Publisher'}

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract all Spring Boot endpoints from Java source code."""
        result: Dict[str, Any] = {
            'controllers': [],
            'endpoints': [],
            'actuators': [],
            'webflux_handlers': [],
        }

        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        # Extract controllers
        for match in self.CONTROLLER_PATTERN.finditer(content):
            ctrl_type = match.group(1)
            between = match.group(2) or ""
            class_name = match.group(3)

            # Find class-level @RequestMapping
            context_start = max(0, match.start() - 300)
            context = content[context_start:match.end()]
            base_path = ""
            rm_match = self.CLASS_REQUEST_MAPPING_PATTERN.search(context)
            if rm_match:
                base_path = rm_match.group(1) or ""

            cross_origin = bool(self.CROSS_ORIGIN_PATTERN.search(context))

            type_map = {
                'RestController': 'rest_controller',
                'Controller': 'controller',
                'RestControllerAdvice': 'controller_advice',
                'ControllerAdvice': 'controller_advice',
            }

            result['controllers'].append(SpringBootControllerInfo(
                name=class_name,
                controller_type=type_map.get(ctrl_type, 'controller'),
                base_path=base_path,
                annotations=[ctrl_type],
                cross_origin=cross_origin,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Extract handler methods
        for match in self.HANDLER_PATTERN.finditer(content):
            preceding = match.group(1) or ""
            mapping_type = match.group(2)
            path = match.group(3) or ""
            explicit_method = match.group(4) or ""
            produces = match.group(5) or ""
            consumes = match.group(6) or ""
            return_type = match.group(7)
            method_name = match.group(8)

            http_method = self.MAPPING_TO_METHOD.get(mapping_type, 'ANY')
            if explicit_method:
                http_method = explicit_method

            # Look at method body for path vars, request params, body
            method_end = content.find('\n\n', match.end())
            if method_end == -1:
                method_end = min(match.end() + 500, len(content))
            method_text = content[match.start():method_end]

            path_vars = [m.group(1) or m.group(2) for m in self.PATH_VAR_PATTERN.finditer(method_text)]
            req_params = [m.group(1) or m.group(2) for m in self.REQUEST_PARAM_PATTERN.finditer(method_text)]
            body_match = self.REQUEST_BODY_PATTERN.search(method_text)
            request_body_type = body_match.group(1) if body_match else ""
            has_validation = bool(self.VALIDATION_PATTERN.search(method_text))

            # Check for reactive return types
            is_reactive = any(rt in return_type for rt in self.REACTIVE_TYPES)
            is_async = 'CompletableFuture' in return_type or is_reactive

            # @ResponseStatus
            status_match = self.RESPONSE_STATUS_PATTERN.search(method_text)
            response_status = status_match.group(1) if status_match else ""

            # Find enclosing controller
            controller_class = ""
            for ctrl in result['controllers']:
                ctrl_line = ctrl.line_number
                ep_line = content[:match.start()].count('\n') + 1
                if ep_line > ctrl_line:
                    controller_class = ctrl.name

            result['endpoints'].append(SpringBootEndpointInfo(
                method=http_method,
                path=path,
                handler_method=method_name,
                controller_class=controller_class,
                return_type=return_type,
                request_body_type=request_body_type,
                path_variables=path_vars,
                request_params=req_params,
                has_validation=has_validation,
                is_async=is_async,
                is_reactive=is_reactive,
                produces=produces,
                consumes=consumes,
                response_status=response_status,
                annotations=[mapping_type],
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Extract actuator endpoints
        for match in self.ACTUATOR_ENDPOINT_PATTERN.finditer(content):
            endpoint_id = match.group(1)
            class_name = match.group(2)

            # Find operations in this class
            class_end = content.find('\n}\n', match.end())
            if class_end == -1:
                class_end = len(content)
            class_body = content[match.end():class_end]
            operations = [m.group(1).replace('Operation', '').lower()
                         for m in self.ACTUATOR_OP_PATTERN.finditer(class_body)]

            result['actuators'].append(SpringBootActuatorInfo(
                name=class_name,
                endpoint_id=endpoint_id,
                operations=operations,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Extract WebFlux RouterFunction endpoints
        for match in self.ROUTER_FUNCTION_PATTERN.finditer(content):
            http_method = match.group(1).upper()
            path = match.group(2)
            accept = match.group(3) or ""
            handler_class = match.group(4) or ""
            handler_fn = match.group(5) or ""

            result['webflux_handlers'].append(SpringBootWebFluxHandlerInfo(
                path=path,
                method=http_method,
                handler_function=handler_fn,
                handler_class=handler_class,
                accept_type=accept,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Extract WebFlux builder-style routes: .GET("/path", handler::method)
        for match in self.ROUTER_BUILDER_PATTERN.finditer(content):
            http_method = match.group(1).upper()
            path = match.group(2)
            handler_class = match.group(3) or ""
            handler_fn = match.group(4) or ""

            result['webflux_handlers'].append(SpringBootWebFluxHandlerInfo(
                path=path,
                method=http_method,
                handler_function=handler_fn,
                handler_class=handler_class,
                accept_type="",
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return result
