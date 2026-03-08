"""
Tests for Apache Camel extractors and EnhancedApacheCamelParser.

Part of CodeTrellis v4.95 Apache Camel Framework Support.
Tests cover:
- Route extraction (RouteBuilder, from/to, route IDs)
- Component extraction (60+ components, data formats)
- Processor extraction (Processor, bean refs, EIP patterns)
- Error handler extraction (deadLetterChannel, onException, retry)
- REST DSL extraction (rest(), HTTP verbs, OpenAPI)
- Parser integration (framework detection, version detection, is_apache_camel_file)
"""

import pytest
from codetrellis.apache_camel_parser_enhanced import EnhancedApacheCamelParser, ApacheCamelParseResult
from codetrellis.extractors.apache_camel import (
    CamelRouteExtractor,
    CamelComponentExtractor,
    CamelProcessorExtractor,
    CamelErrorHandlerExtractor,
    CamelRestDSLExtractor,
)


@pytest.fixture
def parser():
    return EnhancedApacheCamelParser()


@pytest.fixture
def route_extractor():
    return CamelRouteExtractor()


@pytest.fixture
def component_extractor():
    return CamelComponentExtractor()


@pytest.fixture
def processor_extractor():
    return CamelProcessorExtractor()


@pytest.fixture
def error_handler_extractor():
    return CamelErrorHandlerExtractor()


@pytest.fixture
def rest_dsl_extractor():
    return CamelRestDSLExtractor()


class TestCamelRouteExtractor:

    def test_extract_route_builder(self, route_extractor):
        content = """
import org.apache.camel.builder.RouteBuilder;

public class MyRoute extends RouteBuilder {
    @Override
    public void configure() {
        from("direct:start")
            .routeId("my-route")
            .to("log:output")
            .to("mock:result");
    }
}
"""
        result = route_extractor.extract(content)
        assert len(result['routes']) > 0
        assert len(result['endpoints']) > 0

    def test_extract_multiple_routes(self, route_extractor):
        content = """
public class OrderRoutes extends RouteBuilder {
    public void configure() {
        from("jms:queue:orders")
            .routeId("order-processor")
            .to("bean:orderService?method=process");

        from("timer:cleanup?period=3600000")
            .routeId("cleanup-job")
            .to("bean:cleanupService");
    }
}
"""
        result = route_extractor.extract(content)
        assert len(result['endpoints']) >= 2

    def test_extract_wiretap(self, route_extractor):
        content = """
from("direct:input")
    .wireTap("jms:queue:audit")
    .to("direct:process");
"""
        result = route_extractor.extract(content)
        assert len(result['endpoints']) > 0

    def test_empty_content(self, route_extractor):
        result = route_extractor.extract("")
        assert result['routes'] == []


class TestCamelComponentExtractor:

    def test_extract_components(self, component_extractor):
        content = """
from("jms:queue:orders")
    .to("kafka:processed-orders")
    .to("file:/tmp/output")
    .to("http://api.example.com/notify")
    .to("sql:SELECT * FROM orders");
"""
        result = component_extractor.extract(content)
        assert len(result['components']) > 0

    def test_extract_data_formats(self, component_extractor):
        content = """
from("direct:start")
    .marshal().json(JsonLibrary.Jackson)
    .unmarshal().xml()
    .marshal().csv();
"""
        result = component_extractor.extract(content)
        assert len(result['data_formats']) > 0


class TestCamelProcessorExtractor:

    def test_extract_processor(self, processor_extractor):
        content = """
public class OrderProcessor implements Processor {
    @Override
    public void process(Exchange exchange) throws Exception {
        Order order = exchange.getIn().getBody(Order.class);
        order.setProcessed(true);
        exchange.getIn().setBody(order);
    }
}
"""
        result = processor_extractor.extract(content)
        assert len(result['processors']) > 0

    def test_extract_eip_patterns(self, processor_extractor):
        content = """
from("direct:input")
    .split(body().tokenize(","))
    .filter(simple("${body.length} > 0"))
    .aggregate(constant(true), new StringAggregator())
    .multicast().to("direct:a", "direct:b")
    .recipientList(header("targets"))
    .circuitBreaker()
        .to("http://unstable-service");
"""
        result = processor_extractor.extract(content)
        assert len(result['eip_patterns']) > 0

    def test_extract_bean_refs(self, processor_extractor):
        content = """
from("direct:start")
    .bean("orderService", "validate")
    .bean(OrderProcessor.class)
    .process(new CustomProcessor());
"""
        result = processor_extractor.extract(content)
        assert len(result['processors']) > 0  # beans are captured as processors


class TestCamelErrorHandlerExtractor:

    def test_extract_dead_letter_channel(self, error_handler_extractor):
        content = """
public class ErrorRoutes extends RouteBuilder {
    public void configure() {
        errorHandler(deadLetterChannel("jms:queue:dead")
            .maximumRedeliveries(3)
            .redeliveryDelay(1000));
    }
}
"""
        result = error_handler_extractor.extract(content)
        assert len(result['error_handlers']) > 0

    def test_extract_on_exception(self, error_handler_extractor):
        content = """
onException(IOException.class)
    .maximumRedeliveries(5)
    .retryAttemptedLogLevel(LoggingLevel.WARN)
    .handled(true)
    .to("direct:error-handling");

onException(ValidationException.class)
    .handled(true)
    .to("direct:validation-error");
"""
        result = error_handler_extractor.extract(content)
        assert len(result['exception_clauses']) > 0


class TestCamelRestDslExtractor:

    def test_extract_rest_dsl(self, rest_dsl_extractor):
        content = """
rest("/api/users")
    .get().to("direct:getUsers")
    .get("/{id}").to("direct:getUser")
    .post().type(User.class).to("direct:createUser")
    .put("/{id}").type(User.class).to("direct:updateUser")
    .delete("/{id}").to("direct:deleteUser");
"""
        result = rest_dsl_extractor.extract(content)
        assert len(result['rest_definitions']) > 0

    def test_extract_rest_config(self, rest_dsl_extractor):
        content = """
restConfiguration()
    .component("jetty")
    .host("0.0.0.0")
    .port(8080)
    .bindingMode(RestBindingMode.json)
    .apiContextPath("/api-doc")
    .apiProperty("api.title", "User API")
    .apiProperty("api.version", "1.0");
"""
        result = rest_dsl_extractor.extract(content)
        assert result['rest_config']  # rest_config is a dict


class TestEnhancedApacheCamelParser:

    def test_is_apache_camel_file(self, parser):
        content = """
import org.apache.camel.builder.RouteBuilder;

public class MyRoute extends RouteBuilder {}
"""
        assert parser.is_camel_file(content) is True

    def test_is_not_apache_camel_file(self, parser):
        content = """
import java.util.List;
public class Main {}
"""
        assert parser.is_camel_file(content) is False

    def test_detect_frameworks(self, parser):
        content = """
import org.apache.camel.builder.RouteBuilder;
import org.apache.camel.component.kafka.KafkaComponent;
import org.apache.camel.model.rest.RestBindingMode;
"""
        frameworks = parser._detect_frameworks(content)
        assert 'camel_core' in frameworks

    def test_detect_version_4x(self, parser):
        content = """
import org.apache.camel.builder.endpoint.StaticEndpointBuilders;
"""
        version = parser._detect_version(content)
        assert '4.x' in version

    def test_parse_full(self, parser):
        content = """
import org.apache.camel.builder.RouteBuilder;

public class OrderRoute extends RouteBuilder {
    @Override
    public void configure() {
        errorHandler(deadLetterChannel("jms:queue:dead"));

        from("jms:queue:orders")
            .routeId("process-orders")
            .split(body())
            .to("bean:orderService?method=process")
            .to("kafka:processed");
    }
}
"""
        result = parser.parse(content)
        assert isinstance(result, ApacheCamelParseResult)
        assert len(result.routes) > 0

    def test_parse_empty(self, parser):
        result = parser.parse("")
        assert isinstance(result, ApacheCamelParseResult)
        assert result.routes == []
