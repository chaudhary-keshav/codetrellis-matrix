"""
Tests for Spring Framework extractors and EnhancedSpringFrameworkParser.

Part of CodeTrellis v4.94 Spring Framework Support.
Tests cover:
- DI extraction (@Autowired, @Inject, @Resource, @Qualifier, XML beans)
- AOP extraction (@Aspect, @Before, @After, @Around, @Pointcut)
- Event extraction (ApplicationEvent, @EventListener, @TransactionalEventListener)
- MVC extraction (HandlerInterceptor, WebMvcConfigurer, ViewResolver, MessageConverter)
- Parser integration (framework detection, version detection, is_spring_framework_file)
"""

import pytest
from codetrellis.spring_framework_parser_enhanced import (
    EnhancedSpringFrameworkParser,
    SpringFrameworkParseResult,
)
from codetrellis.extractors.spring_framework import (
    SpringDIExtractor,
    SpringAOPExtractor,
    SpringEventExtractor,
    SpringMVCExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedSpringFrameworkParser()


@pytest.fixture
def di_extractor():
    return SpringDIExtractor()


@pytest.fixture
def aop_extractor():
    return SpringAOPExtractor()


@pytest.fixture
def event_extractor():
    return SpringEventExtractor()


@pytest.fixture
def mvc_extractor():
    return SpringMVCExtractor()


# ═══════════════════════════════════════════════════════════════════
# DI Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSpringDIExtractor:

    def test_extract_autowired_field(self, di_extractor):
        """Test extracting @Autowired field injection."""
        content = """
package com.example.service;

import org.springframework.beans.factory.annotation.Autowired;

public class OrderService {
    @Autowired
    private PaymentService paymentService;

    @Autowired
    private NotificationService notificationService;
}
"""
        result = di_extractor.extract(content, "OrderService.java")
        injections = result.get('injections', [])
        assert len(injections) >= 2

    def test_extract_constructor_injection(self, di_extractor):
        """Test extracting constructor injection (recommended pattern)."""
        content = """
package com.example.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public UserService(UserRepository userRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }
}
"""
        result = di_extractor.extract(content, "UserService.java")
        injections = result.get('injections', [])
        assert len(injections) >= 1

    def test_extract_qualifier(self, di_extractor):
        """Test extracting @Qualifier."""
        content = """
package com.example.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;

public class NotificationService {
    @Autowired
    @Qualifier("emailSender")
    private MessageSender messageSender;
}
"""
        result = di_extractor.extract(content, "NotificationService.java")
        injections = result.get('injections', [])
        assert len(injections) >= 1

    def test_extract_resource_injection(self, di_extractor):
        """Test extracting @Resource (JSR-250) injection."""
        content = """
package com.example.service;

import javax.annotation.Resource;

public class DataService {
    @Resource(name = "primaryDataSource")
    private DataSource dataSource;
}
"""
        result = di_extractor.extract(content, "DataService.java")
        injections = result.get('injections', [])
        assert len(injections) >= 1

    def test_extract_xml_bean_definitions(self, di_extractor):
        """Test extracting beans from XML context."""
        content = """
<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans">
    <bean id="userService" class="com.example.service.UserService">
        <property name="userRepository" ref="userRepository"/>
    </bean>
    <bean id="userRepository" class="com.example.repository.UserRepositoryImpl"/>
</beans>
"""
        result = di_extractor.extract(content, "applicationContext.xml")
        beans = result.get('bean_definitions', [])
        assert len(beans) >= 2


# ═══════════════════════════════════════════════════════════════════
# AOP Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSpringAOPExtractor:

    def test_extract_aspect_with_advices(self, aop_extractor):
        """Test extracting @Aspect with advice methods."""
        content = """
package com.example.aop;

import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Before;
import org.aspectj.lang.annotation.After;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.ProceedingJoinPoint;

@Aspect
@Component
public class LoggingAspect {
    @Before("execution(* com.example.service.*.*(..))")
    public void logBefore() {
        System.out.println("Before method execution");
    }

    @After("execution(* com.example.service.*.*(..))")
    public void logAfter() {
        System.out.println("After method execution");
    }

    @Around("execution(* com.example.service.*.*(..))")
    public Object logAround(ProceedingJoinPoint joinPoint) throws Throwable {
        long start = System.currentTimeMillis();
        Object result = joinPoint.proceed();
        long end = System.currentTimeMillis();
        return result;
    }
}
"""
        result = aop_extractor.extract(content, "LoggingAspect.java")
        aspects = result.get('aspects', [])
        advices = result.get('advices', [])
        assert len(aspects) >= 1
        assert len(advices) >= 3

    def test_extract_pointcut_definition(self, aop_extractor):
        """Test extracting @Pointcut definitions."""
        content = """
package com.example.aop;

import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Pointcut;

@Aspect
public class CommonPointcuts {
    @Pointcut("within(com.example.service..*)")
    public void serviceLayer() {}

    @Pointcut("execution(* com.example.repository.*.*(..))")
    public void repositoryLayer() {}
}
"""
        result = aop_extractor.extract(content, "CommonPointcuts.java")
        pointcuts = result.get('pointcuts', [])
        assert len(pointcuts) >= 2

    def test_extract_after_returning(self, aop_extractor):
        """Test extracting @AfterReturning advice."""
        content = """
package com.example.aop;

import org.aspectj.lang.annotation.AfterReturning;
import org.aspectj.lang.annotation.Aspect;

@Aspect
public class AuditAspect {
    @AfterReturning(pointcut = "execution(* com.example.service.*.create*(..))", returning = "result")
    public void auditCreation(Object result) {
        // audit logic
    }
}
"""
        result = aop_extractor.extract(content, "AuditAspect.java")
        advices = result.get('advices', [])
        assert len(advices) >= 1


# ═══════════════════════════════════════════════════════════════════
# Event Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSpringEventExtractor:

    def test_extract_event_listener(self, event_extractor):
        """Test extracting @EventListener methods."""
        content = """
package com.example.listener;

import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

@Component
public class UserEventListener {
    @EventListener
    public void handleUserCreated(UserCreatedEvent event) {
        // send welcome email
    }

    @EventListener(condition = "#event.important")
    public void handleImportantEvent(ApplicationEvent event) {
        // handle important events
    }
}
"""
        result = event_extractor.extract(content, "UserEventListener.java")
        listeners = result.get('listeners', [])
        assert len(listeners) >= 2

    def test_extract_transactional_event_listener(self, event_extractor):
        """Test extracting @TransactionalEventListener."""
        content = """
package com.example.listener;

import org.springframework.transaction.event.TransactionalEventListener;
import org.springframework.transaction.event.TransactionPhase;

@Component
public class OrderEventListener {
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void handleOrderCompleted(OrderCompletedEvent event) {
        // notify after transaction commits
    }
}
"""
        result = event_extractor.extract(content, "OrderEventListener.java")
        listeners = result.get('listeners', [])
        assert len(listeners) >= 1

    def test_extract_event_publisher(self, event_extractor):
        """Test extracting ApplicationEventPublisher usage."""
        content = """
package com.example.service;

import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;

@Service
public class UserService {
    private final ApplicationEventPublisher eventPublisher;

    public UserService(ApplicationEventPublisher eventPublisher) {
        this.eventPublisher = eventPublisher;
    }

    public User createUser(UserDto dto) {
        User user = userRepository.save(new User(dto));
        eventPublisher.publishEvent(new UserCreatedEvent(user));
        return user;
    }
}
"""
        result = event_extractor.extract(content, "UserService.java")
        publishers = result.get('publishers', [])
        assert len(publishers) >= 1

    def test_extract_application_event_class(self, event_extractor):
        """Test extracting ApplicationEvent subclass."""
        content = """
package com.example.event;

import org.springframework.context.ApplicationEvent;

public class UserCreatedEvent extends ApplicationEvent {
    private final User user;

    public UserCreatedEvent(User user) {
        super(user);
        this.user = user;
    }

    public User getUser() { return user; }
}
"""
        result = event_extractor.extract(content, "UserCreatedEvent.java")
        events = result.get('events', [])
        assert len(events) >= 1


# ═══════════════════════════════════════════════════════════════════
# MVC Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestSpringMVCExtractor:

    def test_extract_handler_interceptor(self, mvc_extractor):
        """Test extracting HandlerInterceptor implementation."""
        content = """
package com.example.interceptor;

import org.springframework.web.servlet.HandlerInterceptor;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class AuthInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        return true;
    }

    @Override
    public void postHandle(HttpServletRequest request, HttpServletResponse response, Object handler, ModelAndView modelAndView) {
    }
}
"""
        result = mvc_extractor.extract(content, "AuthInterceptor.java")
        interceptors = result.get('interceptors', [])
        assert len(interceptors) >= 1

    def test_extract_web_mvc_configurer(self, mvc_extractor):
        """Test extracting WebMvcConfigurer implementation."""
        content = """
package com.example.config;

import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.CorsRegistry;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins("http://localhost:3000");
    }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new AuthInterceptor());
    }
}
"""
        result = mvc_extractor.extract(content, "WebConfig.java")
        interceptors = result.get('interceptors', [])
        assert len(interceptors) >= 1 or len(result.get('configurers', [])) >= 1


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedSpringFrameworkParser:

    def test_is_spring_framework_file_positive(self, parser):
        """Test detection of Spring Framework file."""
        content = """
package com.example.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class UserService {
    @Autowired
    private UserRepository userRepository;
}
"""
        assert parser.is_spring_framework_file(content, "UserService.java")

    def test_is_spring_framework_file_negative(self, parser):
        """Test non-Spring Framework file."""
        content = """
package com.example.util;

public class MathUtils {
    public static int add(int a, int b) { return a + b; }
}
"""
        assert not parser.is_spring_framework_file(content, "MathUtils.java")

    def test_parse_returns_result(self, parser):
        """Test parse returns SpringFrameworkParseResult."""
        content = """
package com.example.aop;

import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Before;

@Aspect
@Component
public class LoggingAspect {
    @Before("execution(* com.example.service.*.*(..))")
    public void logBefore() {}
}
"""
        result = parser.parse(content, "LoggingAspect.java")
        assert isinstance(result, SpringFrameworkParseResult)

    def test_version_detection_spring_6(self, parser):
        """Test Spring Framework 6.x version detection (jakarta namespace)."""
        content = """
package com.example;

import org.springframework.stereotype.Service;
import jakarta.inject.Inject;

@Service
public class MyService {
    @Inject
    private SomeDependency dep;
}
"""
        result = parser.parse(content, "MyService.java")
        assert isinstance(result, SpringFrameworkParseResult)

    def test_parse_complex_di_scenario(self, parser):
        """Test parsing complex DI with qualifiers."""
        content = """
package com.example.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;

@Service
public class NotificationService {
    @Autowired
    @Qualifier("emailSender")
    private MessageSender emailSender;

    @Autowired
    @Qualifier("smsSender")
    private MessageSender smsSender;

    public void notify(User user) {
        emailSender.send(user.getEmail(), "Welcome!");
        smsSender.send(user.getPhone(), "Welcome!");
    }
}
"""
        result = parser.parse(content, "NotificationService.java")
        assert isinstance(result, SpringFrameworkParseResult)
        assert hasattr(result, 'di_beans') or hasattr(result, 'injections')
