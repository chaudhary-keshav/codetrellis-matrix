"""
JavaAPIExtractor - Extracts REST endpoints, gRPC services, and messaging handlers.

Supports:
- Spring MVC/WebFlux: @RestController, @GetMapping, @PostMapping, etc.
- JAX-RS: @Path, @GET, @POST, etc.
- Quarkus: @Path (JAX-RS based)
- Micronaut: @Controller, @Get, @Post, etc.
- gRPC-Java: Service implementation classes
- Messaging: @KafkaListener, @RabbitListener, @JmsListener

Part of CodeTrellis v4.12 - Java Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class JavaEndpointInfo:
    """Information about a Java REST/HTTP endpoint."""
    method: str  # GET, POST, PUT, DELETE, PATCH, etc.
    path: str
    handler_method: str
    framework: str  # spring, jaxrs, micronaut, quarkus
    produces: Optional[str] = None
    consumes: Optional[str] = None
    annotations: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)  # @PathVariable, @RequestParam, etc.
    return_type: Optional[str] = None
    controller_class: Optional[str] = None
    file: str = ""
    line_number: int = 0


@dataclass
class JavaGRPCServiceInfo:
    """Information about a Java gRPC service implementation."""
    name: str
    base_class: str  # extends *ImplBase
    methods: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class JavaMessageListenerInfo:
    """Information about a messaging listener (Kafka, RabbitMQ, JMS)."""
    type: str  # kafka, rabbitmq, jms
    topic_or_queue: str
    handler_method: str
    group_id: Optional[str] = None
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0
    class_name: Optional[str] = None


class JavaAPIExtractor:
    """
    Extracts API endpoints from Java source code.

    Detects:
    - Spring MVC/WebFlux controllers and handler methods
    - JAX-RS resources (used by Quarkus, Jersey, etc.)
    - Micronaut HTTP controllers
    - gRPC service implementations
    - Message listeners (Kafka, RabbitMQ, JMS)
    """

    # Spring controller detection
    SPRING_CONTROLLER = re.compile(
        r'@(?:RestController|Controller)\s*(?:\([^)]*\))?\s*'
        r'(?:@RequestMapping\s*\(\s*(?:value\s*=\s*)?["\']([^"\']*)["\'])?',
        re.MULTILINE
    )

    # Spring request mapping annotations
    # Handles: @GetMapping, @GetMapping(), @GetMapping("/path"), @GetMapping(value="/path"),
    #          @RequestMapping(method=RequestMethod.GET), etc.
    # Uses a two-phase approach: first find the annotation, then find the handler method nearby.
    SPRING_MAPPING_ANNOTATION = re.compile(
        r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)'
        r'(?:\s*\(([^)]*(?:\{[^}]*\}[^)]*)*)\))?',
        re.MULTILINE
    )

    # Pattern to extract method signature following a mapping annotation
    # Matches lines like: public List<User> getAllUsers(
    HANDLER_METHOD = re.compile(
        r'(?:@\w+\s*(?:\([^)]*\)\s*)?)*'  # skip any additional annotations
        r'(?:(?:public|protected|private)\s+)?'
        r'(?:(?:static|final|synchronized|default)\s+)*'
        r'(?:[\w<>\[\].,?\s]+?\s+)'
        r'(\w+)\s*\(',
        re.MULTILINE
    )

    # JAX-RS / Quarkus patterns
    JAXRS_RESOURCE = re.compile(
        r'@Path\s*\(\s*["\']([^"\']*)["\']',
        re.MULTILINE
    )

    JAXRS_METHOD = re.compile(
        r'@(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s*\n\s*'
        r'(?:@Path\s*\(\s*["\']([^"\']*)["\'].*?\)\s*)?'
        r'(?:@\w+\s*(?:\([^)]*\))?\s*)*'
        r'(?:public\s+)?(?:[\w<>\[\].,?\s]+?\s+)?'
        r'(\w+)\s*\(',
        re.MULTILINE | re.DOTALL
    )

    # Micronaut controller
    MICRONAUT_CONTROLLER = re.compile(
        r'@Controller\s*\(\s*["\']?([^"\')\s]*)',
        re.MULTILINE
    )

    MICRONAUT_METHOD = re.compile(
        r'@(Get|Post|Put|Delete|Patch|Head|Options)'
        r'\s*(?:\(\s*["\']([^"\']*)["\'])?'
        r'(?:[^)]*\))?\s*'
        r'(?:public\s+)?(?:[\w<>\[\].,?\s]+?\s+)?'
        r'(\w+)\s*\(',
        re.MULTILINE | re.DOTALL
    )

    # gRPC service implementation
    GRPC_SERVICE = re.compile(
        r'class\s+(\w+)\s+extends\s+(\w+(?:Grpc\.)?(\w+)ImplBase)',
        re.MULTILINE
    )

    GRPC_METHOD = re.compile(
        r'@Override\s*\n\s*'
        r'(?:public\s+)?void\s+(\w+)\s*\(',
        re.MULTILINE
    )

    # Messaging listeners
    KAFKA_LISTENER = re.compile(
        r'@KafkaListener\s*\('
        r'(?:[^)]*topics?\s*=\s*["\{]?["\']?([^"\'}\)]+)["\']?["\}]?)?'
        r'(?:[^)]*groupId\s*=\s*["\']([^"\']*)["\'])?'
        r'[^)]*\)\s*'
        r'(?:public\s+)?(?:[\w<>\[\].,?\s]+?\s+)?'
        r'(\w+)\s*\(',
        re.MULTILINE | re.DOTALL
    )

    RABBIT_LISTENER = re.compile(
        r'@RabbitListener\s*\('
        r'(?:[^)]*queues?\s*=\s*["\{]?["\']?([^"\'}\)]+)["\']?["\}]?)?'
        r'[^)]*\)\s*'
        r'(?:public\s+)?(?:[\w<>\[\].,?\s]+?\s+)?'
        r'(\w+)\s*\(',
        re.MULTILINE | re.DOTALL
    )

    JMS_LISTENER = re.compile(
        r'@JmsListener\s*\('
        r'(?:[^)]*destination\s*=\s*["\']([^"\']*)["\'])?'
        r'[^)]*\)\s*'
        r'(?:public\s+)?(?:[\w<>\[\].,?\s]+?\s+)?'
        r'(\w+)\s*\(',
        re.MULTILINE | re.DOTALL
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract API endpoints, gRPC services, and messaging listeners.

        Returns dict with keys: endpoints, grpc_services, message_listeners
        """
        result = {
            'endpoints': [],
            'grpc_services': [],
            'message_listeners': [],
        }

        # Detect controller type and base path
        controller_class = None
        base_path = ""
        framework = "spring"

        # Spring Controller
        spring_match = self.SPRING_CONTROLLER.search(content)
        if spring_match:
            base_path = spring_match.group(1) or ""
            framework = "spring"
            # Extract class name
            class_match = re.search(r'class\s+(\w+)', content)
            if class_match:
                controller_class = class_match.group(1)

        # Check for @RequestMapping at class level
        class_mapping = re.search(
            r'@RequestMapping\s*\(\s*(?:value\s*=\s*|path\s*=\s*)?["\']([^"\']*)["\']',
            content
        )
        if class_mapping:
            base_path = class_mapping.group(1)

        # JAX-RS / Quarkus resource
        jaxrs_match = self.JAXRS_RESOURCE.search(content)
        if jaxrs_match:
            base_path = jaxrs_match.group(1) or ""
            framework = "jaxrs"
            if '@io.quarkus' in content or 'quarkus' in content.lower():
                framework = "quarkus"
            class_match = re.search(r'class\s+(\w+)', content)
            if class_match:
                controller_class = class_match.group(1)

        # Micronaut controller
        micronaut_match = self.MICRONAUT_CONTROLLER.search(content)
        if micronaut_match:
            base_path = micronaut_match.group(1) or ""
            framework = "micronaut"
            class_match = re.search(r'class\s+(\w+)', content)
            if class_match:
                controller_class = class_match.group(1)

        # Extract Spring endpoints
        if spring_match or class_mapping:
            # Find class body start to skip class-level annotations
            class_body_start = 0
            class_body_match = re.search(r'class\s+\w+[^{]*\{', content)
            if class_body_match:
                class_body_start = class_body_match.end()

            for m in self.SPRING_MAPPING_ANNOTATION.finditer(content):
                # Skip class-level @RequestMapping — it's before the class body
                if m.start() < class_body_start:
                    continue

                mapping_type = m.group(1)
                annotation_args = m.group(2) or ""

                # Parse path from annotation args
                path = ""
                path_match = re.search(r'(?:value\s*=\s*|path\s*=\s*)?["\']([^"\']*)["\']', annotation_args)
                if path_match:
                    path = path_match.group(1)

                # Parse explicit method for @RequestMapping
                explicit_method = None
                method_match = re.search(r'method\s*=\s*RequestMethod\.(\w+)', annotation_args)
                if method_match:
                    explicit_method = method_match.group(1)

                # Find the handler method name after the annotation
                remaining = content[m.end():]
                handler_match = self.HANDLER_METHOD.match(remaining)
                if not handler_match:
                    continue
                handler_name = handler_match.group(1)

                # Skip if handler name looks like a class name (failsafe)
                if handler_name == controller_class:
                    continue

                # Determine HTTP method
                method_map = {
                    'GetMapping': 'GET',
                    'PostMapping': 'POST',
                    'PutMapping': 'PUT',
                    'DeleteMapping': 'DELETE',
                    'PatchMapping': 'PATCH',
                    'RequestMapping': explicit_method or 'GET',
                }
                http_method = method_map.get(mapping_type, 'GET')

                full_path = base_path.rstrip('/') + '/' + path.lstrip('/') if path else base_path
                if not full_path.startswith('/'):
                    full_path = '/' + full_path

                line_number = content[:m.start()].count('\n') + 1

                result['endpoints'].append(JavaEndpointInfo(
                    method=http_method,
                    path=full_path,
                    handler_method=handler_name,
                    framework=framework,
                    controller_class=controller_class,
                    file=file_path,
                    line_number=line_number,
                ))

        # Extract JAX-RS / Quarkus endpoints
        if jaxrs_match:
            for m in self.JAXRS_METHOD.finditer(content):
                http_method = m.group(1)
                path = m.group(2) or ""
                handler_name = m.group(3)

                full_path = base_path.rstrip('/') + '/' + path.lstrip('/') if path else base_path
                if not full_path.startswith('/'):
                    full_path = '/' + full_path

                line_number = content[:m.start()].count('\n') + 1

                result['endpoints'].append(JavaEndpointInfo(
                    method=http_method,
                    path=full_path,
                    handler_method=handler_name,
                    framework=framework,
                    controller_class=controller_class,
                    file=file_path,
                    line_number=line_number,
                ))

        # Extract Micronaut endpoints
        if micronaut_match:
            for m in self.MICRONAUT_METHOD.finditer(content):
                http_method = m.group(1).upper()
                path = m.group(2) or ""
                handler_name = m.group(3)

                full_path = base_path.rstrip('/') + '/' + path.lstrip('/') if path else base_path
                if not full_path.startswith('/'):
                    full_path = '/' + full_path

                line_number = content[:m.start()].count('\n') + 1

                result['endpoints'].append(JavaEndpointInfo(
                    method=http_method,
                    path=full_path,
                    handler_method=handler_name,
                    framework="micronaut",
                    controller_class=controller_class,
                    file=file_path,
                    line_number=line_number,
                ))

        # Extract gRPC services
        for m in self.GRPC_SERVICE.finditer(content):
            service_name = m.group(1)
            base_class = m.group(2)

            # Find gRPC methods
            methods = []
            brace_start = content.find('{', m.end())
            if brace_start >= 0:
                from .type_extractor import JavaTypeExtractor
                body = JavaTypeExtractor._extract_brace_body(content, brace_start)
                if body:
                    for method_match in self.GRPC_METHOD.finditer(body):
                        methods.append(method_match.group(1))

            line_number = content[:m.start()].count('\n') + 1

            result['grpc_services'].append(JavaGRPCServiceInfo(
                name=service_name,
                base_class=base_class,
                methods=methods,
                file=file_path,
                line_number=line_number,
            ))

        # Extract Kafka listeners
        for m in self.KAFKA_LISTENER.finditer(content):
            topic = m.group(1) or ""
            group_id = m.group(2)
            handler = m.group(3)
            line_number = content[:m.start()].count('\n') + 1

            result['message_listeners'].append(JavaMessageListenerInfo(
                type="kafka",
                topic_or_queue=topic.strip(),
                handler_method=handler,
                group_id=group_id,
                file=file_path,
                line_number=line_number,
            ))

        # Extract RabbitMQ listeners
        for m in self.RABBIT_LISTENER.finditer(content):
            queue = m.group(1) or ""
            handler = m.group(2)
            line_number = content[:m.start()].count('\n') + 1

            result['message_listeners'].append(JavaMessageListenerInfo(
                type="rabbitmq",
                topic_or_queue=queue.strip(),
                handler_method=handler,
                file=file_path,
                line_number=line_number,
            ))

        # Extract JMS listeners
        for m in self.JMS_LISTENER.finditer(content):
            destination = m.group(1) or ""
            handler = m.group(2)
            line_number = content[:m.start()].count('\n') + 1

            result['message_listeners'].append(JavaMessageListenerInfo(
                type="jms",
                topic_or_queue=destination.strip(),
                handler_method=handler,
                file=file_path,
                line_number=line_number,
            ))

        return result
