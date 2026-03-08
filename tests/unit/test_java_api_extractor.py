"""
Tests for JavaAPIExtractor — Spring MVC, JAX-RS, Micronaut, gRPC, messaging.

Part of CodeTrellis v4.12 Java Language Support.
"""

import pytest
from codetrellis.extractors.java.api_extractor import JavaAPIExtractor


@pytest.fixture
def extractor():
    return JavaAPIExtractor()


# ===== SPRING MVC ENDPOINTS =====

class TestSpringEndpoints:
    """Tests for Spring MVC endpoint extraction."""

    def test_basic_crud_controller(self, extractor):
        """All 5 CRUD endpoints should be detected including bare @GetMapping/@PostMapping."""
        code = '''
        @RestController
        @RequestMapping("/api/users")
        public class UserController {
            @GetMapping
            public List<User> getAllUsers() { return null; }

            @PostMapping
            public User createUser(@RequestBody User user) { return null; }

            @GetMapping("/{id}")
            public User getUser(@PathVariable Long id) { return null; }

            @PutMapping("/{id}")
            public User updateUser(@PathVariable Long id, @RequestBody User user) { return null; }

            @DeleteMapping("/{id}")
            public void deleteUser(@PathVariable Long id) { }
        }
        '''
        result = extractor.extract(code, "UserController.java")
        endpoints = result["endpoints"]
        assert len(endpoints) == 5

        methods = {ep.handler_method: ep for ep in endpoints}

        # Bare @GetMapping (no parens)
        assert "getAllUsers" in methods
        assert methods["getAllUsers"].method == "GET"
        assert methods["getAllUsers"].path == "/api/users"

        # Bare @PostMapping (no parens)
        assert "createUser" in methods
        assert methods["createUser"].method == "POST"
        assert methods["createUser"].path == "/api/users"

        # @GetMapping with path
        assert "getUser" in methods
        assert methods["getUser"].method == "GET"
        assert methods["getUser"].path == "/api/users/{id}"

        # @PutMapping with path
        assert "updateUser" in methods
        assert methods["updateUser"].method == "PUT"
        assert methods["updateUser"].path == "/api/users/{id}"

        # @DeleteMapping with path
        assert "deleteUser" in methods
        assert methods["deleteUser"].method == "DELETE"
        assert methods["deleteUser"].path == "/api/users/{id}"

    def test_get_mapping_empty_parens(self, extractor):
        """@GetMapping() with empty parens should work."""
        code = '''
        @RestController
        @RequestMapping("/api/items")
        public class ItemController {
            @GetMapping()
            public List<Item> list() { return null; }
        }
        '''
        result = extractor.extract(code, "ItemController.java")
        assert len(result["endpoints"]) == 1
        assert result["endpoints"][0].method == "GET"
        assert result["endpoints"][0].path == "/api/items"

    def test_request_mapping_with_explicit_method(self, extractor):
        """@RequestMapping(value="/search", method=RequestMethod.POST) should extract correctly."""
        code = '''
        @RestController
        @RequestMapping("/api/legacy")
        public class LegacyController {
            @RequestMapping(value="/search", method=RequestMethod.POST)
            public Result search() { return null; }
        }
        '''
        result = extractor.extract(code, "LegacyController.java")
        assert len(result["endpoints"]) == 1
        ep = result["endpoints"][0]
        assert ep.method == "POST"
        assert ep.path == "/api/legacy/search"
        assert ep.handler_method == "search"

    def test_no_class_level_request_mapping_duplication(self, extractor):
        """Class-level @RequestMapping should NOT appear as an endpoint."""
        code = '''
        @RestController
        @RequestMapping("/api/legacy")
        public class LegacyController {
            @RequestMapping(value="/search", method=RequestMethod.POST)
            public Result search() { return null; }
        }
        '''
        result = extractor.extract(code, "LegacyController.java")
        # Should NOT have /api/legacy/api/legacy as a path
        for ep in result["endpoints"]:
            assert "/api/legacy/api/legacy" not in ep.path

    def test_multiple_annotations_on_handler(self, extractor):
        """Handler method with @PreAuthorize before @GetMapping should work."""
        code = '''
        @RestController
        @RequestMapping("/api/secure")
        public class SecureController {
            @PreAuthorize("hasRole('ADMIN')")
            @GetMapping("/admin")
            public String admin() { return null; }
        }
        '''
        result = extractor.extract(code, "SecureController.java")
        assert len(result["endpoints"]) == 1
        assert result["endpoints"][0].path == "/api/secure/admin"

    def test_no_class_level_mapping(self, extractor):
        """Controller without @RequestMapping should use root path."""
        code = '''
        @RestController
        public class RootController {
            @GetMapping("/health")
            public String health() { return "ok"; }

            @GetMapping
            public String root() { return "root"; }
        }
        '''
        result = extractor.extract(code, "RootController.java")
        assert len(result["endpoints"]) == 2
        methods = {ep.handler_method: ep for ep in result["endpoints"]}
        assert methods["health"].path == "/health"
        assert methods["root"].path == "/"

    def test_controller_class_name_captured(self, extractor):
        """Controller class name should be set on each endpoint."""
        code = '''
        @RestController
        @RequestMapping("/api/users")
        public class UserController {
            @GetMapping
            public List<User> list() { return null; }
        }
        '''
        result = extractor.extract(code, "UserController.java")
        assert result["endpoints"][0].controller_class == "UserController"

    def test_controller_annotation_also_works(self, extractor):
        """@Controller (not @RestController) should also detect endpoints."""
        code = '''
        @Controller
        @RequestMapping("/web")
        public class WebController {
            @GetMapping("/home")
            public String home() { return "home"; }
        }
        '''
        result = extractor.extract(code, "WebController.java")
        assert len(result["endpoints"]) == 1
        assert result["endpoints"][0].path == "/web/home"

    def test_framework_is_spring(self, extractor):
        """Spring endpoints should have framework='spring'."""
        code = '''
        @RestController
        @RequestMapping("/api")
        public class ApiController {
            @GetMapping("/test")
            public String test() { return "test"; }
        }
        '''
        result = extractor.extract(code, "ApiController.java")
        assert result["endpoints"][0].framework == "spring"

    def test_patch_mapping(self, extractor):
        """@PatchMapping should be detected."""
        code = '''
        @RestController
        @RequestMapping("/api/users")
        public class UserController {
            @PatchMapping("/{id}")
            public User patchUser(@PathVariable Long id) { return null; }
        }
        '''
        result = extractor.extract(code, "UserController.java")
        assert len(result["endpoints"]) == 1
        assert result["endpoints"][0].method == "PATCH"


# ===== JAX-RS ENDPOINTS =====

class TestJaxRsEndpoints:
    """Tests for JAX-RS/Quarkus endpoint extraction."""

    def test_jaxrs_resource(self, extractor):
        code = '''
        @Path("/api/items")
        public class ItemResource {
            @GET
            @Path("/{id}")
            public Item getItem(@PathParam("id") Long id) { return null; }

            @POST
            public Item createItem(Item item) { return null; }
        }
        '''
        result = extractor.extract(code, "ItemResource.java")
        assert len(result["endpoints"]) == 2
        methods = {ep.handler_method: ep for ep in result["endpoints"]}
        assert methods["getItem"].method == "GET"
        assert methods["createItem"].method == "POST"
        assert result["endpoints"][0].framework == "jaxrs"


# ===== MICRONAUT ENDPOINTS =====

class TestMicronautEndpoints:
    """Tests for Micronaut endpoint extraction."""

    def test_micronaut_controller(self, extractor):
        code = '''
        @Controller("/api/items")
        public class ItemController {
            @Get("/{id}")
            public Item getItem(Long id) { return null; }

            @Post
            public Item create(Item item) { return null; }
        }
        '''
        result = extractor.extract(code, "ItemController.java")
        assert len(result["endpoints"]) >= 1
        assert result["endpoints"][0].framework == "micronaut"


# ===== GRPC SERVICES =====

class TestGrpcServices:
    """Tests for gRPC service extraction."""

    def test_grpc_service(self, extractor):
        code = '''
        public class GreeterServiceImpl extends GreeterGrpc.GreeterImplBase {
            @Override
            public void sayHello(HelloRequest request, StreamObserver<HelloReply> responseObserver) {
                responseObserver.onNext(HelloReply.newBuilder().setMessage("Hello").build());
                responseObserver.onCompleted();
            }
        }
        '''
        result = extractor.extract(code, "GreeterServiceImpl.java")
        assert len(result["grpc_services"]) == 1
        svc = result["grpc_services"][0]
        assert svc.name == "GreeterServiceImpl"
        assert "sayHello" in svc.methods


# ===== MESSAGE LISTENERS =====

class TestMessageListeners:
    """Tests for Kafka/RabbitMQ/JMS listener extraction."""

    def test_kafka_listener(self, extractor):
        code = '''
        @Service
        public class OrderConsumer {
            @KafkaListener(topics = "orders", groupId = "order-group")
            public void consume(String message) {
                System.out.println(message);
            }
        }
        '''
        result = extractor.extract(code, "OrderConsumer.java")
        assert len(result["message_listeners"]) == 1
        listener = result["message_listeners"][0]
        assert listener.type == "kafka"
        assert "orders" in listener.topic_or_queue
        assert listener.handler_method == "consume"

    def test_rabbit_listener(self, extractor):
        code = '''
        @Service
        public class NotificationConsumer {
            @RabbitListener(queues = "notifications")
            public void receive(String message) {}
        }
        '''
        result = extractor.extract(code, "NotificationConsumer.java")
        assert len(result["message_listeners"]) == 1
        assert result["message_listeners"][0].type == "rabbitmq"

    def test_jms_listener(self, extractor):
        code = '''
        @Component
        public class JmsConsumer {
            @JmsListener(destination = "queue.orders")
            public void onMessage(String msg) {}
        }
        '''
        result = extractor.extract(code, "JmsConsumer.java")
        assert len(result["message_listeners"]) == 1
        assert result["message_listeners"][0].type == "jms"


# ===== NO ENDPOINTS =====

class TestNoEndpoints:
    """Tests for files that should NOT produce endpoints."""

    def test_plain_class_no_endpoints(self, extractor):
        code = '''
        public class Utils {
            public static String format(String text) { return text.trim(); }
        }
        '''
        result = extractor.extract(code, "Utils.java")
        assert len(result["endpoints"]) == 0
        assert len(result["grpc_services"]) == 0
        assert len(result["message_listeners"]) == 0

    def test_service_class_no_endpoints(self, extractor):
        code = '''
        @Service
        public class UserService {
            public User findById(Long id) { return null; }
        }
        '''
        result = extractor.extract(code, "UserService.java")
        assert len(result["endpoints"]) == 0
