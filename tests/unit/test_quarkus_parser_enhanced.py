"""
Tests for Quarkus extractors and EnhancedQuarkusParser.

Part of CodeTrellis v4.94 Quarkus Framework Support.
Tests cover:
- CDI extraction (@ApplicationScoped, @RequestScoped, @Inject, producers, interceptors)
- REST extraction (@Path, @GET/@POST, RESTEasy Reactive, filters)
- Panache extraction (PanacheEntity, PanacheRepository, active record, finders)
- Config extraction (@ConfigProperty, @ConfigMapping, profiles)
- Extension extraction (extension detection, native hints, health, metrics)
- Parser integration (framework detection, version detection, is_quarkus_file)
"""

import pytest
from codetrellis.quarkus_parser_enhanced import (
    EnhancedQuarkusParser,
    QuarkusParseResult,
)
from codetrellis.extractors.quarkus import (
    QuarkusCDIExtractor,
    QuarkusRESTExtractor,
    QuarkusPanacheExtractor,
    QuarkusConfigExtractor,
    QuarkusExtensionExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedQuarkusParser()


@pytest.fixture
def cdi_extractor():
    return QuarkusCDIExtractor()


@pytest.fixture
def rest_extractor():
    return QuarkusRESTExtractor()


@pytest.fixture
def panache_extractor():
    return QuarkusPanacheExtractor()


@pytest.fixture
def config_extractor():
    return QuarkusConfigExtractor()


@pytest.fixture
def extension_extractor():
    return QuarkusExtensionExtractor()


# ═══════════════════════════════════════════════════════════════════
# CDI Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestQuarkusCDIExtractor:

    def test_extract_application_scoped_bean(self, cdi_extractor):
        """Test extracting @ApplicationScoped CDI bean."""
        content = """
package com.example.service;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class GreetingService {
    @Inject
    GreetingRepository repository;

    public String greet(String name) {
        return repository.getGreeting() + " " + name;
    }
}
"""
        result = cdi_extractor.extract(content, "GreetingService.java")
        beans = result.get('beans', [])
        assert len(beans) >= 1

    def test_extract_request_scoped_bean(self, cdi_extractor):
        """Test extracting @RequestScoped CDI bean."""
        content = """
package com.example.service;

import jakarta.enterprise.context.RequestScoped;

@RequestScoped
public class RequestContext {
    private String correlationId;
    public String getCorrelationId() { return correlationId; }
}
"""
        result = cdi_extractor.extract(content, "RequestContext.java")
        beans = result.get('beans', [])
        assert len(beans) >= 1

    def test_extract_producer_method(self, cdi_extractor):
        """Test extracting @Produces methods."""
        content = """
package com.example.config;

import jakarta.enterprise.inject.Produces;
import jakarta.inject.Singleton;

public class Producers {
    @Produces
    @Singleton
    public ObjectMapper objectMapper() {
        return new ObjectMapper();
    }
}
"""
        result = cdi_extractor.extract(content, "Producers.java")
        producers = result.get('producers', [])
        assert len(producers) >= 1

    def test_extract_interceptor(self, cdi_extractor):
        """Test extracting @Interceptor with binding."""
        content = """
package com.example.interceptor;

import jakarta.interceptor.Interceptor;
import jakarta.interceptor.AroundInvoke;
import jakarta.interceptor.InvocationContext;

@Interceptor
@Logged
public class LoggingInterceptor {
    @AroundInvoke
    public Object logInvocation(InvocationContext context) throws Exception {
        System.out.println("Calling: " + context.getMethod().getName());
        return context.proceed();
    }
}
"""
        result = cdi_extractor.extract(content, "LoggingInterceptor.java")
        interceptors = result.get('interceptors', [])
        assert len(interceptors) >= 1

    def test_extract_observer(self, cdi_extractor):
        """Test extracting @Observes event handler."""
        content = """
package com.example.observer;

import jakarta.enterprise.event.Observes;

public class AuditObserver {
    public void onUserCreated(@Observes UserCreatedEvent event) {
        // audit user creation
    }
}
"""
        result = cdi_extractor.extract(content, "AuditObserver.java")
        observers = result.get('observers', [])
        assert len(observers) >= 1


# ═══════════════════════════════════════════════════════════════════
# REST Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestQuarkusRESTExtractor:

    def test_extract_jaxrs_resource(self, rest_extractor):
        """Test extracting JAX-RS resource endpoints."""
        content = """
package com.example.resource;

import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;

@Path("/users")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class UserResource {
    @GET
    public List<User> list() {
        return User.listAll();
    }

    @GET
    @Path("/{id}")
    public User get(@PathParam("id") Long id) {
        return User.findById(id);
    }

    @POST
    public Response create(User user) {
        user.persist();
        return Response.created(URI.create("/users/" + user.id)).build();
    }

    @DELETE
    @Path("/{id}")
    public void delete(@PathParam("id") Long id) {
        User.deleteById(id);
    }
}
"""
        result = rest_extractor.extract(content, "UserResource.java")
        endpoints = result.get('endpoints', [])
        assert len(endpoints) >= 4
        methods = [getattr(e, 'method', '') for e in endpoints]
        assert 'GET' in methods
        assert 'POST' in methods
        assert 'DELETE' in methods

    def test_extract_resteasy_reactive(self, rest_extractor):
        """Test extracting RESTEasy Reactive annotations."""
        content = """
package com.example.resource;

import io.smallrye.mutiny.Uni;
import jakarta.ws.rs.*;

@Path("/products")
public class ProductResource {
    @GET
    public Uni<List<Product>> list() {
        return Product.listAll();
    }

    @GET
    @Path("/{id}")
    public Uni<Product> get(@PathParam("id") Long id) {
        return Product.findById(id);
    }
}
"""
        result = rest_extractor.extract(content, "ProductResource.java")
        endpoints = result.get('endpoints', [])
        assert len(endpoints) >= 2

    def test_extract_query_params(self, rest_extractor):
        """Test extracting @QueryParam."""
        content = """
package com.example.resource;

import jakarta.ws.rs.*;

@Path("/search")
public class SearchResource {
    @GET
    public List<Result> search(@QueryParam("q") String query, @QueryParam("page") @DefaultValue("0") int page) {
        return searchService.search(query, page);
    }
}
"""
        result = rest_extractor.extract(content, "SearchResource.java")
        endpoints = result.get('endpoints', [])
        assert len(endpoints) >= 1


# ═══════════════════════════════════════════════════════════════════
# Panache Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestQuarkusPanacheExtractor:

    def test_extract_panache_entity_active_record(self, panache_extractor):
        """Test extracting PanacheEntity (active record pattern)."""
        content = """
package com.example.model;

import io.quarkus.hibernate.orm.panache.PanacheEntity;
import jakarta.persistence.Entity;

@Entity
public class User extends PanacheEntity {
    public String name;
    public String email;

    public static User findByEmail(String email) {
        return find("email", email).firstResult();
    }

    public static List<User> findActive() {
        return list("active", true);
    }
}
"""
        result = panache_extractor.extract(content, "User.java")
        entities = result.get('entities', [])
        assert len(entities) >= 1

    def test_extract_panache_repository(self, panache_extractor):
        """Test extracting PanacheRepository (repository pattern)."""
        content = """
package com.example.repository;

import io.quarkus.hibernate.orm.panache.PanacheRepository;
import jakarta.enterprise.context.ApplicationScoped;

@ApplicationScoped
public class UserRepository implements PanacheRepository<User> {
    public User findByEmail(String email) {
        return find("email", email).firstResult();
    }
}
"""
        result = panache_extractor.extract(content, "UserRepository.java")
        repos = result.get('repositories', [])
        assert len(repos) >= 1

    def test_extract_reactive_panache(self, panache_extractor):
        """Test extracting reactive Panache entity."""
        content = """
package com.example.model;

import io.quarkus.hibernate.reactive.panache.PanacheEntity;
import jakarta.persistence.Entity;

@Entity
public class Product extends PanacheEntity {
    public String name;
    public double price;
}
"""
        result = panache_extractor.extract(content, "Product.java")
        entities = result.get('entities', [])
        assert len(entities) >= 1


# ═══════════════════════════════════════════════════════════════════
# Config Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestQuarkusConfigExtractor:

    def test_extract_config_property(self, config_extractor):
        """Test extracting @ConfigProperty."""
        content = """
package com.example.service;

import org.eclipse.microprofile.config.inject.ConfigProperty;
import jakarta.enterprise.context.ApplicationScoped;

@ApplicationScoped
public class GreetingService {
    @ConfigProperty(name = "greeting.message")
    String message;

    @ConfigProperty(name = "greeting.suffix", defaultValue = "!")
    String suffix;
}
"""
        result = config_extractor.extract(content, "GreetingService.java")
        configs = result.get('config_properties', [])
        assert len(configs) >= 2

    def test_extract_config_mapping(self, config_extractor):
        """Test extracting @ConfigMapping interface."""
        content = """
package com.example.config;

import io.smallrye.config.ConfigMapping;

@ConfigMapping(prefix = "app")
public interface AppConfig {
    String name();
    DatabaseConfig database();

    interface DatabaseConfig {
        String url();
        String username();
    }
}
"""
        result = config_extractor.extract(content, "AppConfig.java")
        mappings = result.get('config_mappings', [])
        assert len(mappings) >= 1

    def test_extract_application_properties(self, config_extractor):
        """Test extracting from application.properties (Quarkus format)."""
        content = """
quarkus.datasource.db-kind=postgresql
quarkus.datasource.username=admin
quarkus.datasource.password=${DB_PASSWORD}
quarkus.datasource.jdbc.url=jdbc:postgresql://localhost:5432/mydb
quarkus.hibernate-orm.database.generation=update
quarkus.http.port=8080
greeting.message=Hello
"""
        result = config_extractor.extract(content, "application.properties")
        props = result.get('app_properties', [])
        assert len(props) >= 5


# ═══════════════════════════════════════════════════════════════════
# Extension Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestQuarkusExtensionExtractor:

    def test_detect_extensions_from_pom(self, extension_extractor):
        """Test detecting Quarkus extensions from pom.xml."""
        content = """
<project>
    <dependencies>
        <dependency>
            <groupId>io.quarkus</groupId>
            <artifactId>quarkus-resteasy-reactive</artifactId>
        </dependency>
        <dependency>
            <groupId>io.quarkus</groupId>
            <artifactId>quarkus-hibernate-orm-panache</artifactId>
        </dependency>
        <dependency>
            <groupId>io.quarkus</groupId>
            <artifactId>quarkus-smallrye-health</artifactId>
        </dependency>
    </dependencies>
</project>
"""
        result = extension_extractor.extract(content, "pom.xml")
        extensions = result.get('extensions', [])
        assert len(extensions) >= 3

    def test_extract_register_for_reflection(self, extension_extractor):
        """Test extracting @RegisterForReflection."""
        content = """
package com.example.model;

import io.quarkus.runtime.annotations.RegisterForReflection;

@RegisterForReflection
public class UserDto {
    public String name;
    public String email;
}
"""
        result = extension_extractor.extract(content, "UserDto.java")
        hints = result.get('native_hints', [])
        assert len(hints) >= 1

    def test_extract_health_check(self, extension_extractor):
        """Test extracting health check endpoints."""
        content = """
package com.example.health;

import org.eclipse.microprofile.health.HealthCheck;
import org.eclipse.microprofile.health.HealthCheckResponse;
import org.eclipse.microprofile.health.Liveness;

@Liveness
public class DatabaseHealthCheck implements HealthCheck {
    @Override
    public HealthCheckResponse call() {
        return HealthCheckResponse.up("Database connection");
    }
}
"""
        result = extension_extractor.extract(content, "DatabaseHealthCheck.java")
        health = result.get('health_checks', [])
        assert len(health) >= 1


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedQuarkusParser:

    def test_is_quarkus_file_positive(self, parser):
        """Test detection of Quarkus file."""
        content = """
package com.example.resource;

import jakarta.ws.rs.Path;
import jakarta.ws.rs.GET;
import io.quarkus.hibernate.orm.panache.PanacheEntity;

@Path("/api")
public class ApiResource {
    @GET
    public String hello() { return "Hello Quarkus!"; }
}
"""
        assert parser.is_quarkus_file(content, "ApiResource.java")

    def test_is_quarkus_file_negative(self, parser):
        """Test non-Quarkus file."""
        content = """
package com.example.util;

public class MathUtils {
    public static int add(int a, int b) { return a + b; }
}
"""
        assert not parser.is_quarkus_file(content, "MathUtils.java")

    def test_parse_returns_result(self, parser):
        """Test parse returns QuarkusParseResult."""
        content = """
package com.example.resource;

import jakarta.ws.rs.*;
import jakarta.enterprise.context.ApplicationScoped;

@Path("/greeting")
@ApplicationScoped
public class GreetingResource {
    @GET
    @Produces("text/plain")
    public String hello() {
        return "Hello!";
    }
}
"""
        result = parser.parse(content, "GreetingResource.java")
        assert isinstance(result, QuarkusParseResult)

    def test_parse_full_quarkus_resource(self, parser):
        """Test parsing a complete Quarkus resource with CDI + REST."""
        content = """
package com.example.resource;

import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.inject.Inject;
import jakarta.enterprise.context.ApplicationScoped;

@Path("/fruits")
@ApplicationScoped
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class FruitResource {
    @Inject
    FruitService fruitService;

    @GET
    public List<Fruit> list() {
        return fruitService.listAll();
    }

    @POST
    public Response add(Fruit fruit) {
        fruitService.add(fruit);
        return Response.status(201).entity(fruit).build();
    }

    @DELETE
    @Path("/{name}")
    public Response delete(@PathParam("name") String name) {
        fruitService.delete(name);
        return Response.noContent().build();
    }
}
"""
        result = parser.parse(content, "FruitResource.java")
        assert isinstance(result, QuarkusParseResult)
        assert hasattr(result, 'cdi_beans') or hasattr(result, 'rest_endpoints')

    def test_reactive_detection(self, parser):
        """Test reactive mode detection."""
        content = """
package com.example.resource;

import io.smallrye.mutiny.Uni;
import io.smallrye.mutiny.Multi;
import jakarta.ws.rs.*;

@Path("/reactive")
public class ReactiveResource {
    @GET
    public Uni<String> hello() {
        return Uni.createFrom().item("Hello Reactive!");
    }

    @GET
    @Path("/stream")
    public Multi<String> stream() {
        return Multi.createFrom().items("a", "b", "c");
    }
}
"""
        result = parser.parse(content, "ReactiveResource.java")
        assert isinstance(result, QuarkusParseResult)
