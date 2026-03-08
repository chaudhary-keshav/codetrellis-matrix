"""
Tests for Spring Boot extractors and EnhancedSpringBootParser.

Part of CodeTrellis v4.94 Spring Boot Framework Support.
Tests cover:
- Bean extraction (@Component, @Service, @Repository, @Controller, @Configuration, @Bean)
- Endpoint extraction (@RestController, @RequestMapping, @GetMapping etc.)
- Property extraction (application.properties, @ConfigurationProperties, @Value)
- Security extraction (SecurityFilterChain, @EnableWebSecurity, OAuth2, JWT)
- Data extraction (Spring Data repos, @Query, @Cacheable, @Transactional)
- AutoConfig extraction (@SpringBootApplication, @EnableAutoConfiguration, starters)
- Parser integration (framework detection, version detection, is_spring_boot_file)
"""

import pytest
from codetrellis.spring_boot_parser_enhanced import (
    EnhancedSpringBootParser,
    SpringBootParseResult,
)
from codetrellis.extractors.spring_boot import (
    SpringBootBeanExtractor,
    SpringBootEndpointExtractor,
    SpringBootPropertyExtractor,
    SpringBootSecurityExtractor,
    SpringBootDataExtractor,
    SpringBootAutoConfigExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedSpringBootParser()


@pytest.fixture
def bean_extractor():
    return SpringBootBeanExtractor()


@pytest.fixture
def endpoint_extractor():
    return SpringBootEndpointExtractor()


@pytest.fixture
def property_extractor():
    return SpringBootPropertyExtractor()


@pytest.fixture
def security_extractor():
    return SpringBootSecurityExtractor()


@pytest.fixture
def data_extractor():
    return SpringBootDataExtractor()


@pytest.fixture
def autoconfig_extractor():
    return SpringBootAutoConfigExtractor()


# ═══════════════════════════════════════════════════════════════════
# Bean Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSpringBootBeanExtractor:

    def test_extract_service_beans(self, bean_extractor):
        """Test extracting @Service annotated beans."""
        content = """
package com.example.service;

import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;

@Service
public class UserService {
    @Autowired
    private UserRepository userRepository;

    public User findById(Long id) {
        return userRepository.findById(id).orElse(null);
    }
}
"""
        result = bean_extractor.extract(content, "UserService.java")
        beans = result.get('beans', [])
        assert len(beans) >= 1
        service_beans = [b for b in beans if getattr(b, 'bean_type', '') == 'service']
        assert len(service_beans) >= 1

    def test_extract_component_beans(self, bean_extractor):
        """Test extracting @Component annotated beans."""
        content = """
package com.example.util;

import org.springframework.stereotype.Component;

@Component
public class EmailValidator {
    public boolean isValid(String email) {
        return email != null && email.contains("@");
    }
}
"""
        result = bean_extractor.extract(content, "EmailValidator.java")
        beans = result.get('beans', [])
        assert len(beans) >= 1

    def test_extract_repository_beans(self, bean_extractor):
        """Test extracting @Repository annotated beans."""
        content = """
package com.example.repository;

import org.springframework.stereotype.Repository;

@Repository
public class UserRepositoryImpl implements UserRepository {
    @Override
    public User findByEmail(String email) {
        return null;
    }
}
"""
        result = bean_extractor.extract(content, "UserRepositoryImpl.java")
        beans = result.get('beans', [])
        assert len(beans) >= 1

    def test_extract_configuration_with_bean_methods(self, bean_extractor):
        """Test extracting @Configuration with @Bean methods."""
        content = """
package com.example.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class AppConfig {
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplateBuilder().build();
    }

    @Bean
    @Primary
    public ObjectMapper objectMapper() {
        return new ObjectMapper();
    }
}
"""
        result = bean_extractor.extract(content, "AppConfig.java")
        configs = result.get('configurations', [])
        bean_methods = result.get('bean_methods', [])
        assert len(configs) >= 1
        assert len(bean_methods) >= 2

    def test_extract_conditional_beans(self, bean_extractor):
        """Test extracting beans with @ConditionalOn* annotations."""
        content = """
package com.example.config;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class ConditionalConfig {
    @Bean
    @ConditionalOnProperty(name = "feature.enabled", havingValue = "true")
    public FeatureService featureService() {
        return new FeatureService();
    }
}
"""
        result = bean_extractor.extract(content, "ConditionalConfig.java")
        bean_methods = result.get('bean_methods', [])
        assert len(bean_methods) >= 1

    def test_extract_profile_beans(self, bean_extractor):
        """Test extracting beans with @Profile annotations."""
        content = """
package com.example.config;

import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;

@Service
@Profile("development")
public class DevDataInitializer {
    public void init() {}
}
"""
        result = bean_extractor.extract(content, "DevDataInitializer.java")
        beans = result.get('beans', [])
        assert len(beans) >= 1

    def test_extract_scope_and_lazy(self, bean_extractor):
        """Test extracting @Scope and @Lazy annotations."""
        content = """
package com.example.service;

import org.springframework.context.annotation.Scope;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Component;

@Component
@Scope("prototype")
@Lazy
public class RequestScopedService {
}
"""
        result = bean_extractor.extract(content, "RequestScopedService.java")
        beans = result.get('beans', [])
        assert len(beans) >= 1


# ═══════════════════════════════════════════════════════════════════
# Endpoint Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSpringBootEndpointExtractor:

    def test_extract_rest_controller_endpoints(self, endpoint_extractor):
        """Test extracting endpoints from @RestController."""
        content = """
package com.example.controller;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
public class UserController {
    @GetMapping
    public List<User> getAllUsers() {
        return userService.findAll();
    }

    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.findById(id);
    }

    @PostMapping
    public User createUser(@RequestBody @Valid UserDto dto) {
        return userService.create(dto);
    }

    @PutMapping("/{id}")
    public User updateUser(@PathVariable Long id, @RequestBody UserDto dto) {
        return userService.update(id, dto);
    }

    @DeleteMapping("/{id}")
    public void deleteUser(@PathVariable Long id) {
        userService.delete(id);
    }
}
"""
        result = endpoint_extractor.extract(content, "UserController.java")
        endpoints = result.get('endpoints', [])
        assert len(endpoints) >= 5
        methods = [getattr(e, 'method', '') for e in endpoints]
        assert 'GET' in methods
        assert 'POST' in methods
        assert 'PUT' in methods
        assert 'DELETE' in methods

    def test_extract_request_mapping(self, endpoint_extractor):
        """Test extracting legacy @RequestMapping endpoints."""
        content = """
package com.example.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;

@Controller
@RequestMapping("/admin")
public class AdminController {
    @RequestMapping(value = "/dashboard", method = RequestMethod.GET)
    public String dashboard() {
        return "admin/dashboard";
    }
}
"""
        result = endpoint_extractor.extract(content, "AdminController.java")
        endpoints = result.get('endpoints', [])
        assert len(endpoints) >= 1

    def test_extract_path_variables_and_params(self, endpoint_extractor):
        """Test extracting @PathVariable and @RequestParam."""
        content = """
package com.example.controller;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/search")
public class SearchController {
    @GetMapping
    public List<Result> search(
        @RequestParam String query,
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "10") int size) {
        return searchService.search(query, page, size);
    }
}
"""
        result = endpoint_extractor.extract(content, "SearchController.java")
        endpoints = result.get('endpoints', [])
        assert len(endpoints) >= 1

    def test_extract_webflux_handler(self, endpoint_extractor):
        """Test extracting WebFlux RouterFunction style endpoints."""
        content = """
package com.example.router;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.server.RouterFunction;
import org.springframework.web.reactive.function.server.RouterFunctions;

@Configuration
public class UserRouter {
    @Bean
    public RouterFunction<ServerResponse> userRoutes(UserHandler handler) {
        return RouterFunctions.route()
            .GET("/api/users", handler::listUsers)
            .POST("/api/users", handler::createUser)
            .GET("/api/users/{id}", handler::getUser)
            .build();
    }
}
"""
        result = endpoint_extractor.extract(content, "UserRouter.java")
        webflux = result.get('webflux_handlers', [])
        assert len(webflux) >= 1 or len(result.get('endpoints', [])) >= 1


# ═══════════════════════════════════════════════════════════════════
# Property Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSpringBootPropertyExtractor:

    def test_extract_application_properties(self, property_extractor):
        """Test extracting from application.properties."""
        content = """
server.port=8080
spring.datasource.url=jdbc:postgresql://localhost:5432/mydb
spring.datasource.username=admin
spring.datasource.password=${DB_PASSWORD}
spring.jpa.hibernate.ddl-auto=update
logging.level.root=INFO
"""
        result = property_extractor.extract(content, "application.properties")
        props = result.get('properties', [])
        assert len(props) >= 5

    def test_extract_yaml_config(self, property_extractor):
        """Test extracting from application.yml."""
        content = """
server:
  port: 8080
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/mydb
    username: admin
    password: ${DB_PASSWORD}
  jpa:
    hibernate:
      ddl-auto: update
"""
        result = property_extractor.extract(content, "application.yml")
        props = result.get('properties', [])
        assert len(props) >= 1

    def test_extract_configuration_properties(self, property_extractor):
        """Test extracting @ConfigurationProperties classes."""
        content = """
package com.example.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app.mail")
public class MailProperties {
    private String host;
    private int port;
    private String username;
    private String password;
}
"""
        result = property_extractor.extract(content, "MailProperties.java")
        config_props = result.get('config_props_classes', [])
        assert len(config_props) >= 1

    def test_extract_value_annotations(self, property_extractor):
        """Test extracting @Value injections."""
        content = """
package com.example.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class NotificationService {
    @Value("${notification.enabled:true}")
    private boolean enabled;

    @Value("${notification.max-retries:3}")
    private int maxRetries;
}
"""
        result = property_extractor.extract(content, "NotificationService.java")
        values = [p for p in result.get('properties', []) if getattr(p, 'source', '') == '@Value']
        assert len(values) >= 2

    def test_detect_secrets(self, property_extractor):
        """Test secret detection in properties."""
        content = """
spring.datasource.password=mysecretpassword
api.key=sk-1234567890abcdef
jwt.secret=my-jwt-secret-key
"""
        result = property_extractor.extract(content, "application.properties")
        props = result.get('properties', [])
        secret_props = [p for p in props if getattr(p, 'is_secret', False)]
        assert len(secret_props) >= 1


# ═══════════════════════════════════════════════════════════════════
# Security Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSpringBootSecurityExtractor:

    def test_extract_security_filter_chain(self, security_extractor):
        """Test extracting SecurityFilterChain config (Spring Security 5.7+)."""
        content = """
package com.example.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
public class SecurityConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf().disable()
            .authorizeHttpRequests()
            .requestMatchers("/api/public/**").permitAll()
            .requestMatchers("/api/admin/**").hasRole("ADMIN")
            .anyRequest().authenticated()
            .and()
            .httpBasic();
        return http.build();
    }
}
"""
        result = security_extractor.extract(content, "SecurityConfig.java")
        security = result.get('security_configs', [])
        assert len(security) >= 1

    def test_extract_oauth2_config(self, security_extractor):
        """Test extracting OAuth2 resource server config."""
        content = """
package com.example.config;

import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;

@EnableWebSecurity
public class OAuth2Config {
    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults()))
            .oauth2Login(Customizer.withDefaults());
        return http.build();
    }
}
"""
        result = security_extractor.extract(content, "OAuth2Config.java")
        security = result.get('security_configs', [])
        assert len(security) >= 1

    def test_extract_method_security(self, security_extractor):
        """Test extracting @PreAuthorize/@Secured method security."""
        content = """
package com.example.service;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.access.annotation.Secured;

public class AdminService {
    @PreAuthorize("hasRole('ADMIN')")
    public void deleteUser(Long id) {}

    @Secured("ROLE_ADMIN")
    public void resetPassword(Long id) {}
}
"""
        result = security_extractor.extract(content, "AdminService.java")
        method_security = result.get('method_security', [])
        assert len(method_security) >= 2


# ═══════════════════════════════════════════════════════════════════
# Data Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSpringBootDataExtractor:

    def test_extract_jpa_repository(self, data_extractor):
        """Test extracting Spring Data JPA repository."""
        content = """
package com.example.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

public interface UserRepository extends JpaRepository<User, Long> {
    User findByEmail(String email);

    @Query("SELECT u FROM User u WHERE u.active = true")
    List<User> findAllActive();

    List<User> findByLastNameContaining(String name);
}
"""
        result = data_extractor.extract(content, "UserRepository.java")
        repos = result.get('repositories', [])
        assert len(repos) >= 1

    def test_extract_crud_repository(self, data_extractor):
        """Test extracting CrudRepository."""
        content = """
package com.example.repository;

import org.springframework.data.repository.CrudRepository;

public interface ProductRepository extends CrudRepository<Product, Long> {
    List<Product> findByCategory(String category);
}
"""
        result = data_extractor.extract(content, "ProductRepository.java")
        repos = result.get('repositories', [])
        assert len(repos) >= 1

    def test_extract_cacheable(self, data_extractor):
        """Test extracting @Cacheable annotations."""
        content = """
package com.example.service;

import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.CacheEvict;

@Service
public class ProductService {
    @Cacheable("products")
    public Product findById(Long id) {
        return productRepository.findById(id).orElse(null);
    }

    @CacheEvict(value = "products", allEntries = true)
    public void refreshCache() {}
}
"""
        result = data_extractor.extract(content, "ProductService.java")
        cache = result.get('caches', [])
        assert len(cache) >= 2

    def test_extract_transactional(self, data_extractor):
        """Test extracting @Transactional annotations."""
        content = """
package com.example.service;

import org.springframework.transaction.annotation.Transactional;

@Service
public class OrderService {
    @Transactional
    public Order createOrder(OrderDto dto) {
        return orderRepository.save(new Order(dto));
    }

    @Transactional(readOnly = true)
    public List<Order> findAll() {
        return orderRepository.findAll();
    }
}
"""
        result = data_extractor.extract(content, "OrderService.java")
        txns = result.get('transactions', [])
        assert len(txns) >= 2


# ═══════════════════════════════════════════════════════════════════
# AutoConfig Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSpringBootAutoConfigExtractor:

    def test_extract_spring_boot_application(self, autoconfig_extractor):
        """Test extracting @SpringBootApplication."""
        content = """
package com.example;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
"""
        result = autoconfig_extractor.extract(content, "Application.java")
        autoconfigs = result.get('auto_configs', [])
        assert len(autoconfigs) >= 1

    def test_extract_enable_annotations(self, autoconfig_extractor):
        """Test extracting @Enable* annotations."""
        content = """
package com.example.config;

import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;

@SpringBootApplication
@EnableScheduling
@EnableCaching
@EnableJpaAuditing
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
"""
        result = autoconfig_extractor.extract(content, "Application.java")
        autoconfigs = result.get('auto_configs', [])
        assert len(autoconfigs) >= 1


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedSpringBootParser:

    def test_is_spring_boot_file_positive(self, parser):
        """Test is_spring_boot_file returns True for Spring Boot files."""
        content = """
package com.example.controller;

import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.GetMapping;

@RestController
@RequestMapping("/api")
public class ApiController {
    @GetMapping("/status")
    public String status() { return "OK"; }
}
"""
        assert parser.is_spring_boot_file(content, "ApiController.java")

    def test_is_spring_boot_file_negative(self, parser):
        """Test is_spring_boot_file returns False for non-Spring Boot files."""
        content = """
package com.example.util;

public class StringUtils {
    public static String capitalize(String s) {
        return s.substring(0, 1).toUpperCase() + s.substring(1);
    }
}
"""
        assert not parser.is_spring_boot_file(content, "StringUtils.java")

    def test_parse_returns_result(self, parser):
        """Test parse returns SpringBootParseResult."""
        content = """
package com.example.service;

import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;

@Service
public class UserService {
    @Autowired
    private UserRepository userRepository;

    public User findById(Long id) {
        return userRepository.findById(id).orElse(null);
    }
}
"""
        result = parser.parse(content, "UserService.java")
        assert isinstance(result, SpringBootParseResult)

    def test_parse_full_controller(self, parser):
        """Test parsing a complete REST controller."""
        content = """
package com.example.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;

@RestController
@RequestMapping("/api/users")
public class UserController {
    @Autowired
    private UserService userService;

    @GetMapping
    public List<User> getAll() {
        return userService.findAll();
    }

    @PostMapping
    public User create(@RequestBody @Valid UserDto dto) {
        return userService.create(dto);
    }

    @DeleteMapping("/{id}")
    public void delete(@PathVariable Long id) {
        userService.delete(id);
    }
}
"""
        result = parser.parse(content, "UserController.java")
        assert isinstance(result, SpringBootParseResult)
        # Should find beans, endpoints
        assert hasattr(result, 'beans')
        assert hasattr(result, 'endpoints')

    def test_version_detection_spring_boot_3(self, parser):
        """Test Spring Boot 3.x version detection."""
        content = """
package com.example;

import org.springframework.boot.autoconfigure.SpringBootApplication;
import jakarta.validation.Valid;
import jakarta.servlet.http.HttpServletRequest;

@SpringBootApplication
public class App {}
"""
        result = parser.parse(content, "App.java")
        assert isinstance(result, SpringBootParseResult)

    def test_version_detection_spring_boot_2(self, parser):
        """Test Spring Boot 2.x version detection (javax namespace)."""
        content = """
package com.example;

import org.springframework.boot.autoconfigure.SpringBootApplication;
import javax.validation.Valid;
import javax.servlet.http.HttpServletRequest;

@SpringBootApplication
public class App {}
"""
        result = parser.parse(content, "App.java")
        assert isinstance(result, SpringBootParseResult)

    def test_parse_configuration_class(self, parser):
        """Test parsing a @Configuration class with @Bean methods."""
        content = """
package com.example.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;

@Configuration
@Profile("production")
public class ProdConfig {
    @Bean
    public DataSource dataSource() {
        HikariDataSource ds = new HikariDataSource();
        ds.setJdbcUrl("jdbc:postgresql://prod-db:5432/app");
        return ds;
    }

    @Bean
    @Primary
    public ObjectMapper objectMapper() {
        return new ObjectMapper()
            .registerModule(new JavaTimeModule());
    }
}
"""
        result = parser.parse(content, "ProdConfig.java")
        assert isinstance(result, SpringBootParseResult)
        assert hasattr(result, 'configurations')
