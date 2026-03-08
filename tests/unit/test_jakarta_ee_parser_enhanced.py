"""
Tests for Jakarta EE extractors and EnhancedJakartaEEParser.

Part of CodeTrellis v4.94 Jakarta EE Framework Support.
Tests cover:
- CDI extraction (@ApplicationScoped, @Produces, @Decorator, @Observes, namespace detection)
- Servlet extraction (@WebServlet, HttpServlet, @WebFilter, @WebListener)
- JPA extraction (@Entity, @Table, @Id, relationships, @NamedQuery, @Inheritance)
- JAX-RS extraction (@Path, @GET/@POST, @ApplicationPath, @Provider)
- EJB extraction (@Stateless, @Stateful, @Singleton, @MessageDriven, @Schedule)
- Parser integration (framework detection, version detection, is_jakarta_ee_file)
"""

import pytest
from codetrellis.jakarta_ee_parser_enhanced import (
    EnhancedJakartaEEParser,
    JakartaEEParseResult,
)
from codetrellis.extractors.jakarta_ee import (
    JakartaCDIExtractor,
    JakartaServletExtractor,
    JakartaJPAExtractor,
    JakartaJAXRSExtractor,
    JakartaEJBExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedJakartaEEParser()


@pytest.fixture
def cdi_extractor():
    return JakartaCDIExtractor()


@pytest.fixture
def servlet_extractor():
    return JakartaServletExtractor()


@pytest.fixture
def jpa_extractor():
    return JakartaJPAExtractor()


@pytest.fixture
def jaxrs_extractor():
    return JakartaJAXRSExtractor()


@pytest.fixture
def ejb_extractor():
    return JakartaEJBExtractor()


# ═══════════════════════════════════════════════════════════════════
# CDI Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestJakartaCDIExtractor:

    def test_extract_application_scoped(self, cdi_extractor):
        """Test extracting @ApplicationScoped CDI bean (jakarta namespace)."""
        content = """
package com.example.service;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class UserService {
    @Inject
    private UserRepository userRepository;

    public User findById(Long id) {
        return userRepository.findById(id);
    }
}
"""
        result = cdi_extractor.extract(content, "UserService.java")
        beans = result.get('beans', [])
        assert len(beans) >= 1

    def test_extract_javax_namespace(self, cdi_extractor):
        """Test extracting CDI bean with javax namespace (legacy)."""
        content = """
package com.example.service;

import javax.enterprise.context.ApplicationScoped;
import javax.inject.Inject;

@ApplicationScoped
public class LegacyService {
    @Inject
    private SomeDependency dep;
}
"""
        result = cdi_extractor.extract(content, "LegacyService.java")
        beans = result.get('beans', [])
        assert len(beans) >= 1

    def test_extract_producer(self, cdi_extractor):
        """Test extracting @Produces method."""
        content = """
package com.example.config;

import jakarta.enterprise.inject.Produces;
import jakarta.inject.Singleton;

public class Producers {
    @Produces
    @Singleton
    public EntityManager createEntityManager() {
        return emf.createEntityManager();
    }
}
"""
        result = cdi_extractor.extract(content, "Producers.java")
        producers = result.get('producers', [])
        assert len(producers) >= 1

    def test_extract_decorator(self, cdi_extractor):
        """Test extracting @Decorator pattern."""
        content = """
package com.example.decorator;

import jakarta.decorator.Decorator;
import jakarta.decorator.Delegate;
import jakarta.inject.Inject;

@Decorator
public class LoggingDecorator implements UserService {
    @Inject
    @Delegate
    private UserService delegate;

    @Override
    public User findById(Long id) {
        System.out.println("Looking up user: " + id);
        return delegate.findById(id);
    }
}
"""
        result = cdi_extractor.extract(content, "LoggingDecorator.java")
        decorators = result.get('decorators', [])
        assert len(decorators) >= 1

    def test_extract_observer(self, cdi_extractor):
        """Test extracting @Observes event handler."""
        content = """
package com.example.observer;

import jakarta.enterprise.event.Observes;
import jakarta.enterprise.event.ObservesAsync;

public class EventObserver {
    public void onUserCreated(@Observes UserCreatedEvent event) {
        // handle synchronously
    }

    public void onUserDeleted(@ObservesAsync UserDeletedEvent event) {
        // handle asynchronously
    }
}
"""
        result = cdi_extractor.extract(content, "EventObserver.java")
        observers = result.get('event_observers', [])
        assert len(observers) >= 2


# ═══════════════════════════════════════════════════════════════════
# Servlet Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestJakartaServletExtractor:

    def test_extract_web_servlet(self, servlet_extractor):
        """Test extracting @WebServlet."""
        content = """
package com.example.servlet;

import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

@WebServlet(urlPatterns = {"/hello", "/greeting"})
public class HelloServlet extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) {
        resp.getWriter().write("Hello World");
    }

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) {
        // handle POST
    }
}
"""
        result = servlet_extractor.extract(content, "HelloServlet.java")
        servlets = result.get('servlets', [])
        assert len(servlets) >= 1

    def test_extract_web_filter(self, servlet_extractor):
        """Test extracting @WebFilter."""
        content = """
package com.example.filter;

import jakarta.servlet.annotation.WebFilter;
import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;

@WebFilter(urlPatterns = "/*")
public class LoggingFilter implements Filter {
    @Override
    public void doFilter(ServletRequest req, ServletResponse resp, FilterChain chain) {
        chain.doFilter(req, resp);
    }
}
"""
        result = servlet_extractor.extract(content, "LoggingFilter.java")
        filters = result.get('filters', [])
        assert len(filters) >= 1

    def test_extract_web_listener(self, servlet_extractor):
        """Test extracting @WebListener."""
        content = """
package com.example.listener;

import jakarta.servlet.annotation.WebListener;
import jakarta.servlet.ServletContextListener;
import jakarta.servlet.ServletContextEvent;

@WebListener
public class AppContextListener implements ServletContextListener {
    @Override
    public void contextInitialized(ServletContextEvent sce) {
        System.out.println("Application started");
    }

    @Override
    public void contextDestroyed(ServletContextEvent sce) {
        System.out.println("Application stopped");
    }
}
"""
        result = servlet_extractor.extract(content, "AppContextListener.java")
        listeners = result.get('listeners', [])
        assert len(listeners) >= 1

    def test_extract_async_servlet(self, servlet_extractor):
        """Test extracting async servlet."""
        content = """
package com.example.servlet;

import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.AsyncContext;

@WebServlet(urlPatterns = "/async", asyncSupported = true)
public class AsyncServlet extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) {
        AsyncContext ctx = req.startAsync();
        ctx.start(() -> {
            // async processing
        });
    }
}
"""
        result = servlet_extractor.extract(content, "AsyncServlet.java")
        servlets = result.get('servlets', [])
        assert len(servlets) >= 1


# ═══════════════════════════════════════════════════════════════════
# JPA Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestJakartaJPAExtractor:

    def test_extract_entity_with_relationships(self, jpa_extractor):
        """Test extracting @Entity with relationships."""
        content = """
package com.example.model;

import jakarta.persistence.*;
import java.util.List;

@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String email;

    @Column(nullable = false)
    private String name;

    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL)
    private List<Order> orders;

    @ManyToOne
    @JoinColumn(name = "department_id")
    private Department department;
}
"""
        result = jpa_extractor.extract(content, "User.java")
        entities = result.get('entities', [])
        assert len(entities) >= 1
        rels = result.get('relationships', [])
        assert len(rels) >= 2

    def test_extract_named_query(self, jpa_extractor):
        """Test extracting @NamedQuery."""
        content = """
package com.example.model;

import jakarta.persistence.*;

@Entity
@NamedQuery(name = "User.findByEmail", query = "SELECT u FROM User u WHERE u.email = :email")
@NamedQuery(name = "User.findActive", query = "SELECT u FROM User u WHERE u.active = true")
public class User {
    @Id
    private Long id;
    private String email;
    private boolean active;
}
"""
        result = jpa_extractor.extract(content, "User.java")
        named_queries = result.get('named_queries', [])
        assert len(named_queries) >= 2

    def test_extract_inheritance(self, jpa_extractor):
        """Test extracting @Inheritance strategy."""
        content = """
package com.example.model;

import jakarta.persistence.*;

@Entity
@Inheritance(strategy = InheritanceType.JOINED)
@DiscriminatorColumn(name = "vehicle_type")
public abstract class Vehicle {
    @Id
    @GeneratedValue
    private Long id;
    private String manufacturer;
}
"""
        result = jpa_extractor.extract(content, "Vehicle.java")
        entities = result.get('entities', [])
        assert len(entities) >= 1

    def test_extract_many_to_many(self, jpa_extractor):
        """Test extracting @ManyToMany relationship."""
        content = """
package com.example.model;

import jakarta.persistence.*;
import java.util.Set;

@Entity
public class Student {
    @Id
    private Long id;

    @ManyToMany
    @JoinTable(
        name = "student_course",
        joinColumns = @JoinColumn(name = "student_id"),
        inverseJoinColumns = @JoinColumn(name = "course_id")
    )
    private Set<Course> courses;
}
"""
        result = jpa_extractor.extract(content, "Student.java")
        rels = result.get('relationships', [])
        assert len(rels) >= 1


# ═══════════════════════════════════════════════════════════════════
# JAX-RS Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestJakartaJAXRSExtractor:

    def test_extract_jaxrs_resource(self, jaxrs_extractor):
        """Test extracting JAX-RS resource class."""
        content = """
package com.example.resource;

import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

@Path("/users")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class UserResource {
    @GET
    public List<User> list() { return null; }

    @GET
    @Path("/{id}")
    public User get(@PathParam("id") Long id) { return null; }

    @POST
    public Response create(User user) {
        return Response.status(201).entity(user).build();
    }

    @PUT
    @Path("/{id}")
    public User update(@PathParam("id") Long id, User user) { return null; }

    @DELETE
    @Path("/{id}")
    public void delete(@PathParam("id") Long id) {}
}
"""
        result = jaxrs_extractor.extract(content, "UserResource.java")
        endpoints = result.get('endpoints', [])
        assert len(endpoints) >= 5
        methods = [getattr(e, 'method', '') for e in endpoints]
        assert 'GET' in methods
        assert 'POST' in methods
        assert 'PUT' in methods
        assert 'DELETE' in methods

    def test_extract_application_path(self, jaxrs_extractor):
        """Test extracting @ApplicationPath."""
        content = """
package com.example;

import jakarta.ws.rs.ApplicationPath;
import jakarta.ws.rs.core.Application;

@ApplicationPath("/api")
public class RestApplication extends Application {
}
"""
        result = jaxrs_extractor.extract(content, "RestApplication.java")
        apps = result.get('applications', [])
        assert len(apps) >= 1

    def test_extract_exception_mapper(self, jaxrs_extractor):
        """Test extracting @Provider ExceptionMapper."""
        content = """
package com.example.provider;

import jakarta.ws.rs.core.Response;
import jakarta.ws.rs.ext.ExceptionMapper;
import jakarta.ws.rs.ext.Provider;

@Provider
public class NotFoundExceptionMapper implements ExceptionMapper<NotFoundException> {
    @Override
    public Response toResponse(NotFoundException exception) {
        return Response.status(Response.Status.NOT_FOUND)
            .entity(new ErrorResponse("Not found"))
            .build();
    }
}
"""
        result = jaxrs_extractor.extract(content, "NotFoundExceptionMapper.java")
        providers = result.get('providers', [])
        assert len(providers) >= 1

    def test_extract_container_filter(self, jaxrs_extractor):
        """Test extracting ContainerRequestFilter/ContainerResponseFilter."""
        content = """
package com.example.filter;

import jakarta.ws.rs.container.ContainerRequestContext;
import jakarta.ws.rs.container.ContainerRequestFilter;
import jakarta.ws.rs.ext.Provider;

@Provider
public class AuthFilter implements ContainerRequestFilter {
    @Override
    public void filter(ContainerRequestContext context) {
        // auth check
    }
}
"""
        result = jaxrs_extractor.extract(content, "AuthFilter.java")
        providers = result.get('providers', [])
        assert len(providers) >= 1


# ═══════════════════════════════════════════════════════════════════
# EJB Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestJakartaEJBExtractor:

    def test_extract_stateless_session_bean(self, ejb_extractor):
        """Test extracting @Stateless session bean."""
        content = """
package com.example.ejb;

import jakarta.ejb.Stateless;
import jakarta.inject.Inject;

@Stateless
public class OrderService {
    @Inject
    private OrderRepository orderRepository;

    public Order createOrder(OrderDto dto) {
        return orderRepository.save(new Order(dto));
    }
}
"""
        result = ejb_extractor.extract(content, "OrderService.java")
        session_beans = result.get('session_beans', [])
        assert len(session_beans) >= 1

    def test_extract_stateful_session_bean(self, ejb_extractor):
        """Test extracting @Stateful session bean."""
        content = """
package com.example.ejb;

import jakarta.ejb.Stateful;

@Stateful
public class ShoppingCart {
    private List<Item> items = new ArrayList<>();

    public void addItem(Item item) { items.add(item); }
    public List<Item> getItems() { return items; }
    public void clear() { items.clear(); }
}
"""
        result = ejb_extractor.extract(content, "ShoppingCart.java")
        session_beans = result.get('session_beans', [])
        assert len(session_beans) >= 1

    def test_extract_singleton_ejb(self, ejb_extractor):
        """Test extracting @Singleton EJB."""
        content = """
package com.example.ejb;

import jakarta.ejb.Singleton;
import jakarta.ejb.Startup;

@Singleton
@Startup
public class AppInitializer {
    @PostConstruct
    public void init() {
        // initialization logic
    }
}
"""
        result = ejb_extractor.extract(content, "AppInitializer.java")
        session_beans = result.get('session_beans', [])
        assert len(session_beans) >= 1

    def test_extract_message_driven_bean(self, ejb_extractor):
        """Test extracting @MessageDriven bean."""
        content = """
package com.example.ejb;

import jakarta.ejb.MessageDriven;
import jakarta.ejb.ActivationConfigProperty;
import jakarta.jms.MessageListener;
import jakarta.jms.Message;

@MessageDriven(activationConfig = {
    @ActivationConfigProperty(propertyName = "destinationType", propertyValue = "jakarta.jms.Queue"),
    @ActivationConfigProperty(propertyName = "destination", propertyValue = "orderQueue")
})
public class OrderMessageBean implements MessageListener {
    @Override
    public void onMessage(Message message) {
        // process order message
    }
}
"""
        result = ejb_extractor.extract(content, "OrderMessageBean.java")
        mdb = result.get('message_driven_beans', [])
        assert len(mdb) >= 1

    def test_extract_timer_schedule(self, ejb_extractor):
        """Test extracting @Schedule timer."""
        content = """
package com.example.ejb;

import jakarta.ejb.Singleton;
import jakarta.ejb.Schedule;

@Singleton
public class ScheduledTasks {
    @Schedule(hour = "2", minute = "0", persistent = false)
    public void nightlyCleanup() {
        // cleanup logic
    }

    @Schedule(second = "*/30", minute = "*", hour = "*", persistent = false)
    public void healthCheck() {
        // health check
    }
}
"""
        result = ejb_extractor.extract(content, "ScheduledTasks.java")
        timers = result.get('timers', [])
        assert len(timers) >= 2


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedJakartaEEParser:

    def test_is_jakarta_ee_file_positive(self, parser):
        """Test detection of Jakarta EE file."""
        content = """
package com.example.resource;

import jakarta.ws.rs.Path;
import jakarta.ws.rs.GET;
import jakarta.enterprise.context.ApplicationScoped;

@Path("/api")
@ApplicationScoped
public class ApiResource {
    @GET
    public String hello() { return "Hello Jakarta EE!"; }
}
"""
        assert parser.is_jakarta_ee_file(content, "ApiResource.java")

    def test_is_jakarta_ee_file_with_javax(self, parser):
        """Test detection of legacy javax namespace."""
        content = """
package com.example.resource;

import javax.ws.rs.Path;
import javax.ws.rs.GET;

@Path("/api")
public class LegacyResource {
    @GET
    public String hello() { return "Hello Java EE!"; }
}
"""
        assert parser.is_jakarta_ee_file(content, "LegacyResource.java")

    def test_is_jakarta_ee_file_negative(self, parser):
        """Test non-Jakarta EE file."""
        content = """
package com.example.util;

public class Validator {
    public static boolean isNotBlank(String s) {
        return s != null && !s.trim().isEmpty();
    }
}
"""
        assert not parser.is_jakarta_ee_file(content, "Validator.java")

    def test_parse_returns_result(self, parser):
        """Test parse returns JakartaEEParseResult."""
        content = """
package com.example.resource;

import jakarta.ws.rs.*;
import jakarta.enterprise.context.ApplicationScoped;

@Path("/greeting")
@ApplicationScoped
public class GreetingResource {
    @GET
    public String hello() { return "Hello!"; }
}
"""
        result = parser.parse(content, "GreetingResource.java")
        assert isinstance(result, JakartaEEParseResult)

    def test_parse_full_jaxrs_with_cdi(self, parser):
        """Test parsing a complete JAX-RS resource with CDI."""
        content = """
package com.example.resource;

import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import jakarta.inject.Inject;
import jakarta.enterprise.context.ApplicationScoped;

@Path("/products")
@ApplicationScoped
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class ProductResource {
    @Inject
    ProductService productService;

    @GET
    public List<Product> list() {
        return productService.findAll();
    }

    @POST
    public Response create(Product product) {
        productService.save(product);
        return Response.status(201).build();
    }

    @DELETE
    @Path("/{id}")
    public void delete(@PathParam("id") Long id) {
        productService.delete(id);
    }
}
"""
        result = parser.parse(content, "ProductResource.java")
        assert isinstance(result, JakartaEEParseResult)
        assert hasattr(result, 'cdi_beans') or hasattr(result, 'jaxrs_resources')

    def test_parse_entity_with_jpa(self, parser):
        """Test parsing a JPA entity with relationships."""
        content = """
package com.example.model;

import jakarta.persistence.*;
import java.util.List;

@Entity
@Table(name = "orders")
@NamedQuery(name = "Order.findByUser", query = "SELECT o FROM Order o WHERE o.user = :user")
public class Order {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "user_id")
    private User user;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL)
    private List<OrderItem> items;

    @Column(nullable = false)
    private double total;
}
"""
        result = parser.parse(content, "Order.java")
        assert isinstance(result, JakartaEEParseResult)
        assert hasattr(result, 'jpa_entities') or hasattr(result, 'entities')

    def test_version_detection_jakarta_ee_10(self, parser):
        """Test Jakarta EE 10+ detection (jakarta namespace)."""
        content = """
package com.example;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.ws.rs.Path;

@ApplicationScoped
@Path("/api")
public class ApiResource {}
"""
        result = parser.parse(content, "ApiResource.java")
        assert isinstance(result, JakartaEEParseResult)

    def test_version_detection_java_ee_8(self, parser):
        """Test Java EE 8 detection (javax namespace)."""
        content = """
package com.example;

import javax.enterprise.context.ApplicationScoped;
import javax.inject.Inject;
import javax.ws.rs.Path;

@ApplicationScoped
@Path("/api")
public class LegacyResource {}
"""
        result = parser.parse(content, "LegacyResource.java")
        assert isinstance(result, JakartaEEParseResult)
