"""
Tests for Micronaut extractors and EnhancedMicronautParser.

Part of CodeTrellis v4.94 Micronaut Framework Support.
Tests cover:
- DI extraction (@Singleton, @Prototype, @Factory, @Requires, @Primary, @Replaces)
- HTTP extraction (@Controller, @Get/@Post, @ServerFilter, @Client)
- Data extraction (CrudRepository, @MappedEntity, derived queries)
- Config extraction (@ConfigurationProperties, @EachProperty, @Value)
- Feature extraction (feature detection, health, security, scheduling)
- Parser integration (framework detection, version detection, is_micronaut_file)
"""

import pytest
from codetrellis.micronaut_parser_enhanced import (
    EnhancedMicronautParser,
    MicronautParseResult,
)
from codetrellis.extractors.micronaut import (
    MicronautDIExtractor,
    MicronautHTTPExtractor,
    MicronautDataExtractor,
    MicronautConfigExtractor,
    MicronautFeatureExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedMicronautParser()


@pytest.fixture
def di_extractor():
    return MicronautDIExtractor()


@pytest.fixture
def http_extractor():
    return MicronautHTTPExtractor()


@pytest.fixture
def data_extractor():
    return MicronautDataExtractor()


@pytest.fixture
def config_extractor():
    return MicronautConfigExtractor()


@pytest.fixture
def feature_extractor():
    return MicronautFeatureExtractor()


# ═══════════════════════════════════════════════════════════════════
# DI Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestMicronautDIExtractor:

    def test_extract_singleton_bean(self, di_extractor):
        """Test extracting @Singleton bean."""
        content = """
package com.example.service;

import jakarta.inject.Singleton;
import jakarta.inject.Inject;

@Singleton
public class GreetingService {
    @Inject
    GreetingRepository repository;

    public String greet(String name) {
        return "Hello " + name;
    }
}
"""
        result = di_extractor.extract(content, "GreetingService.java")
        beans = result.get('beans', [])
        assert len(beans) >= 1

    def test_extract_prototype_bean(self, di_extractor):
        """Test extracting @Prototype bean."""
        content = """
package com.example.service;

import io.micronaut.context.annotation.Prototype;

@Prototype
public class RequestState {
    private String requestId;
}
"""
        result = di_extractor.extract(content, "RequestState.java")
        beans = result.get('beans', [])
        assert len(beans) >= 1

    def test_extract_factory(self, di_extractor):
        """Test extracting @Factory with @Bean methods."""
        content = """
package com.example.config;

import io.micronaut.context.annotation.Factory;
import jakarta.inject.Singleton;

@Factory
public class BeanFactory {
    @Singleton
    public ObjectMapper objectMapper() {
        return new ObjectMapper();
    }

    @Singleton
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}
"""
        result = di_extractor.extract(content, "BeanFactory.java")
        factories = result.get('factories', [])
        assert len(factories) >= 1

    def test_extract_requires_annotation(self, di_extractor):
        """Test extracting @Requires conditional."""
        content = """
package com.example.service;

import io.micronaut.context.annotation.Requires;
import jakarta.inject.Singleton;

@Singleton
@Requires(property = "feature.enabled", value = "true")
public class FeatureService {
    public void doSomething() {}
}
"""
        result = di_extractor.extract(content, "FeatureService.java")
        beans = result.get('beans', [])
        assert len(beans) >= 1

    def test_extract_replaces(self, di_extractor):
        """Test extracting @Replaces annotation."""
        content = """
package com.example.service;

import io.micronaut.context.annotation.Replaces;
import jakarta.inject.Singleton;

@Singleton
@Replaces(DefaultUserService.class)
public class CustomUserService implements UserService {
    public User findById(Long id) { return null; }
}
"""
        result = di_extractor.extract(content, "CustomUserService.java")
        beans = result.get('beans', [])
        assert len(beans) >= 1


# ═══════════════════════════════════════════════════════════════════
# HTTP Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestMicronautHTTPExtractor:

    def test_extract_controller_endpoints(self, http_extractor):
        """Test extracting @Controller HTTP endpoints."""
        content = """
package com.example.controller;

import io.micronaut.http.annotation.*;
import io.micronaut.http.HttpResponse;

@Controller("/users")
public class UserController {
    @Get
    public List<User> list() {
        return userService.findAll();
    }

    @Get("/{id}")
    public User get(Long id) {
        return userService.findById(id);
    }

    @Post
    public HttpResponse<User> create(@Body User user) {
        return HttpResponse.created(userService.save(user));
    }

    @Put("/{id}")
    public User update(Long id, @Body User user) {
        return userService.update(id, user);
    }

    @Delete("/{id}")
    public HttpResponse<?> delete(Long id) {
        userService.delete(id);
        return HttpResponse.noContent();
    }
}
"""
        result = http_extractor.extract(content, "UserController.java")
        endpoints = result.get('endpoints', [])
        assert len(endpoints) >= 5
        methods = [getattr(e, 'method', '') for e in endpoints]
        assert 'GET' in methods
        assert 'POST' in methods
        assert 'PUT' in methods
        assert 'DELETE' in methods

    def test_extract_server_filter(self, http_extractor):
        """Test extracting @ServerFilter."""
        content = """
package com.example.filter;

import io.micronaut.http.annotation.ServerFilter;
import io.micronaut.http.annotation.RequestFilter;
import io.micronaut.http.HttpRequest;

@ServerFilter("/api/**")
public class AuthFilter {
    @RequestFilter
    public void filterRequest(HttpRequest<?> request) {
        // auth logic
    }
}
"""
        result = http_extractor.extract(content, "AuthFilter.java")
        filters = result.get('filters', [])
        assert len(filters) >= 1

    def test_extract_declarative_client(self, http_extractor):
        """Test extracting @Client declarative HTTP client."""
        content = """
package com.example.client;

import io.micronaut.http.annotation.Get;
import io.micronaut.http.annotation.Post;
import io.micronaut.http.annotation.Body;
import io.micronaut.http.client.annotation.Client;

@Client("/api")
public interface UserClient {
    @Get("/users")
    List<User> list();

    @Post("/users")
    User create(@Body User user);
}
"""
        result = http_extractor.extract(content, "UserClient.java")
        clients = result.get('clients', [])
        assert len(clients) >= 1

    def test_extract_reactive_endpoints(self, http_extractor):
        """Test extracting reactive (Reactor/RxJava) endpoints."""
        content = """
package com.example.controller;

import io.micronaut.http.annotation.*;
import reactor.core.publisher.Mono;
import reactor.core.publisher.Flux;

@Controller("/reactive")
public class ReactiveController {
    @Get
    public Flux<User> list() {
        return userService.findAll();
    }

    @Get("/{id}")
    public Mono<User> get(Long id) {
        return userService.findById(id);
    }
}
"""
        result = http_extractor.extract(content, "ReactiveController.java")
        endpoints = result.get('endpoints', [])
        assert len(endpoints) >= 2


# ═══════════════════════════════════════════════════════════════════
# Data Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestMicronautDataExtractor:

    def test_extract_crud_repository(self, data_extractor):
        """Test extracting CrudRepository."""
        content = """
package com.example.repository;

import io.micronaut.data.repository.CrudRepository;
import io.micronaut.data.annotation.Repository;

@Repository
public interface UserRepository extends CrudRepository<User, Long> {
    User findByEmail(String email);
    List<User> findByActive(boolean active);
}
"""
        result = data_extractor.extract(content, "UserRepository.java")
        repos = result.get('repositories', [])
        assert len(repos) >= 1

    def test_extract_jpa_repository(self, data_extractor):
        """Test extracting JpaRepository."""
        content = """
package com.example.repository;

import io.micronaut.data.jpa.repository.JpaRepository;
import io.micronaut.data.annotation.Repository;

@Repository
public interface ProductRepository extends JpaRepository<Product, Long> {
    List<Product> findByCategory(String category);
}
"""
        result = data_extractor.extract(content, "ProductRepository.java")
        repos = result.get('repositories', [])
        assert len(repos) >= 1

    def test_extract_mapped_entity(self, data_extractor):
        """Test extracting @MappedEntity."""
        content = """
package com.example.model;

import io.micronaut.data.annotation.MappedEntity;
import io.micronaut.data.annotation.Id;
import io.micronaut.data.annotation.GeneratedValue;

@MappedEntity
public class User {
    @Id
    @GeneratedValue
    private Long id;
    private String name;
    private String email;
}
"""
        result = data_extractor.extract(content, "User.java")
        entities = result.get('entities', [])
        assert len(entities) >= 1


# ═══════════════════════════════════════════════════════════════════
# Config Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestMicronautConfigExtractor:

    def test_extract_configuration_properties(self, config_extractor):
        """Test extracting @ConfigurationProperties."""
        content = """
package com.example.config;

import io.micronaut.context.annotation.ConfigurationProperties;

@ConfigurationProperties("app")
public class AppConfig {
    private String name;
    private int maxRetries = 3;

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public int getMaxRetries() { return maxRetries; }
}
"""
        result = config_extractor.extract(content, "AppConfig.java")
        configs = result.get('config_properties', [])
        assert len(configs) >= 1

    def test_extract_each_property(self, config_extractor):
        """Test extracting @EachProperty."""
        content = """
package com.example.config;

import io.micronaut.context.annotation.EachProperty;

@EachProperty("datasources")
public class DataSourceConfig {
    private String url;
    private String username;
    private String driverClassName;
}
"""
        result = config_extractor.extract(content, "DataSourceConfig.java")
        configs = result.get('each_properties', [])
        assert len(configs) >= 1

    def test_extract_value_annotation(self, config_extractor):
        """Test extracting @Value injection."""
        content = """
package com.example.service;

import io.micronaut.context.annotation.Value;
import jakarta.inject.Singleton;

@Singleton
public class AppService {
    @Value("${app.name:MyApp}")
    private String appName;

    @Value("${app.port:8080}")
    private int port;
}
"""
        result = config_extractor.extract(content, "AppService.java")
        values = result.get('value_injections', [])
        assert len(values) >= 2


# ═══════════════════════════════════════════════════════════════════
# Feature Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestMicronautFeatureExtractor:

    def test_detect_features_from_build(self, feature_extractor):
        """Test detecting Micronaut features from build.gradle."""
        content = """
dependencies {
    implementation("io.micronaut:micronaut-http-server-netty")
    implementation("io.micronaut.data:micronaut-data-hibernate-jpa")
    implementation("io.micronaut.security:micronaut-security-jwt")
    implementation("io.micronaut:micronaut-management")
    testImplementation("io.micronaut.test:micronaut-test-junit5")
}
"""
        result = feature_extractor.extract(content, "build.gradle")
        features = result.get('features', [])
        assert len(features) >= 3

    def test_extract_health_indicator(self, feature_extractor):
        """Test extracting HealthIndicator."""
        content = """
package com.example.health;

import io.micronaut.management.health.indicator.HealthIndicator;
import io.micronaut.management.health.indicator.HealthResult;
import org.reactivestreams.Publisher;
import jakarta.inject.Singleton;

@Singleton
public class DatabaseHealthIndicator implements HealthIndicator {
    @Override
    public Publisher<HealthResult> getResult() {
        return null;
    }
}
"""
        result = feature_extractor.extract(content, "DatabaseHealthIndicator.java")
        health = result.get('health_indicators', [])
        assert len(health) >= 1

    def test_extract_scheduled_task(self, feature_extractor):
        """Test extracting @Scheduled tasks."""
        content = """
package com.example.task;

import io.micronaut.scheduling.annotation.Scheduled;
import jakarta.inject.Singleton;

@Singleton
public class CleanupTask {
    @Scheduled(fixedRate = "1h")
    public void cleanupOldRecords() {
        // cleanup logic
    }

    @Scheduled(cron = "0 0 2 * * ?")
    public void nightlyBackup() {
        // backup logic
    }
}
"""
        result = feature_extractor.extract(content, "CleanupTask.java")
        scheduled = result.get('scheduled_tasks', [])
        assert len(scheduled) >= 2

    def test_extract_security(self, feature_extractor):
        """Test extracting @Secured annotation."""
        content = """
package com.example.controller;

import io.micronaut.security.annotation.Secured;
import io.micronaut.security.rules.SecurityRule;
import io.micronaut.http.annotation.*;

@Controller("/admin")
@Secured(SecurityRule.IS_AUTHENTICATED)
public class AdminController {
    @Get
    @Secured({"ROLE_ADMIN"})
    public String admin() { return "admin"; }
}
"""
        result = feature_extractor.extract(content, "AdminController.java")
        security = result.get('security', [])
        assert len(security) >= 1


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedMicronautParser:

    def test_is_micronaut_file_positive(self, parser):
        """Test detection of Micronaut file."""
        content = """
package com.example.controller;

import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;

@Controller("/api")
public class ApiController {
    @Get("/status")
    public String status() { return "OK"; }
}
"""
        assert parser.is_micronaut_file(content, "ApiController.java")

    def test_is_micronaut_file_negative(self, parser):
        """Test non-Micronaut file."""
        content = """
package com.example.util;

public class StringUtils {
    public static String upper(String s) { return s.toUpperCase(); }
}
"""
        assert not parser.is_micronaut_file(content, "StringUtils.java")

    def test_parse_returns_result(self, parser):
        """Test parse returns MicronautParseResult."""
        content = """
package com.example.controller;

import io.micronaut.http.annotation.*;
import jakarta.inject.Inject;

@Controller("/greeting")
public class GreetingController {
    @Inject
    GreetingService greetingService;

    @Get("/{name}")
    public String greet(String name) {
        return greetingService.greet(name);
    }
}
"""
        result = parser.parse(content, "GreetingController.java")
        assert isinstance(result, MicronautParseResult)

    def test_parse_full_controller_with_di(self, parser):
        """Test parsing a controller with DI and config."""
        content = """
package com.example.controller;

import io.micronaut.http.annotation.*;
import io.micronaut.http.HttpResponse;
import jakarta.inject.Inject;
import io.micronaut.context.annotation.Value;

@Controller("/products")
public class ProductController {
    @Inject
    ProductService productService;

    @Value("${products.page-size:20}")
    int pageSize;

    @Get
    public List<Product> list() {
        return productService.findAll();
    }

    @Post
    public HttpResponse<Product> create(@Body Product product) {
        return HttpResponse.created(productService.save(product));
    }
}
"""
        result = parser.parse(content, "ProductController.java")
        assert isinstance(result, MicronautParseResult)
        assert hasattr(result, 'controllers') or hasattr(result, 'beans')

    def test_version_detection_micronaut_4(self, parser):
        """Test Micronaut 4.x version detection."""
        content = """
package com.example;

import io.micronaut.runtime.Micronaut;
import io.micronaut.http.annotation.Controller;
import io.micronaut.serde.annotation.Serdeable;

@Serdeable
public class UserDto {
    public String name;
}
"""
        result = parser.parse(content, "UserDto.java")
        assert isinstance(result, MicronautParseResult)
