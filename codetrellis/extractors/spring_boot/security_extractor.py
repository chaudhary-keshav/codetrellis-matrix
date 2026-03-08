"""
Spring Boot Security Extractor v1.0

Extracts Spring Security configuration patterns for Spring Boot applications.

Extracts:
- SecurityFilterChain beans (Spring Security 5.7+)
- WebSecurityConfigurerAdapter (legacy, Spring Security <5.7)
- @EnableWebSecurity, @EnableMethodSecurity
- OAuth2 login/resource server configurations
- JWT token configurations
- Method-level security (@PreAuthorize, @PostAuthorize, @Secured, @RolesAllowed)
- CORS and CSRF configuration
- Authentication providers

Part of CodeTrellis v4.94 - Spring Boot Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class SpringBootSecurityConfigInfo:
    """Security configuration class or SecurityFilterChain bean."""
    name: str
    config_type: str = ""  # filter_chain, web_security_adapter (legacy), global_method
    has_cors: bool = False
    has_csrf_disabled: bool = False
    has_session_management: bool = False
    session_policy: str = ""  # STATELESS, IF_REQUIRED, ALWAYS, NEVER
    auth_type: str = ""  # form_login, http_basic, oauth2, jwt, custom
    authorized_urls: List[str] = field(default_factory=list)
    permitted_urls: List[str] = field(default_factory=list)
    role_restrictions: List[Dict[str, str]] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class SpringBootAuthInfo:
    """Authentication provider or mechanism info."""
    auth_type: str = ""  # oauth2_login, oauth2_resource_server, jwt, ldap, jdbc, in_memory
    provider_class: str = ""
    user_details_service: str = ""
    jwt_decoder: str = ""
    has_custom_user_details: bool = False
    annotations: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class SpringBootMethodSecurityInfo:
    """Method-level security annotation."""
    annotation: str = ""  # PreAuthorize, PostAuthorize, Secured, RolesAllowed
    expression: str = ""  # SpEL expression or role name
    target_method: str = ""
    target_class: str = ""
    file: str = ""
    line_number: int = 0


class SpringBootSecurityExtractor:
    """Extracts Spring Security configuration patterns."""

    # SecurityFilterChain bean
    FILTER_CHAIN_PATTERN = re.compile(
        r'@Bean\s+'
        r'(?:@\w+(?:\([^)]*\))?\s+)*'
        r'(?:public\s+)?SecurityFilterChain\s+(\w+)\s*\(\s*HttpSecurity\s+(\w+)',
        re.MULTILINE
    )

    # WebSecurityConfigurerAdapter (legacy)
    LEGACY_SECURITY_PATTERN = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+extends\s+WebSecurityConfigurerAdapter',
        re.MULTILINE
    )

    # @EnableWebSecurity, @EnableMethodSecurity
    ENABLE_SECURITY_PATTERN = re.compile(
        r'@Enable(WebSecurity|MethodSecurity|GlobalMethodSecurity)',
        re.MULTILINE
    )

    # CORS configuration
    CORS_PATTERN = re.compile(r'\.cors\(', re.MULTILINE)

    # CSRF disabled
    CSRF_DISABLE_PATTERN = re.compile(
        r'\.csrf\(\s*(?:csrf\s*->\s*csrf\.disable\(\)|AbstractHttpConfigurer::disable)',
        re.MULTILINE
    )

    # Session management
    SESSION_PATTERN = re.compile(
        r'\.sessionManagement\(.*?SessionCreationPolicy\.(\w+)',
        re.DOTALL
    )

    # authorizeHttpRequests / authorizeRequests
    AUTH_REQUESTS_PATTERN = re.compile(
        r'\.(?:authorizeHttpRequests|authorizeRequests)\(',
    )

    # permitAll patterns
    PERMIT_ALL_PATTERN = re.compile(
        r'\.requestMatchers?\(\s*"([^"]*)"[^)]*\)\s*\.permitAll\(\)',
    )

    # hasRole / hasAuthority patterns
    ROLE_PATTERN = re.compile(
        r'\.requestMatchers?\(\s*"([^"]*)"[^)]*\)\s*\.has(?:Role|Authority)\(\s*"([^"]*)"\s*\)',
    )

    # OAuth2 login
    OAUTH2_LOGIN_PATTERN = re.compile(r'\.oauth2Login\(', re.MULTILINE)
    OAUTH2_RS_PATTERN = re.compile(r'\.oauth2ResourceServer\(', re.MULTILINE)

    # JWT
    JWT_PATTERN = re.compile(r'\.jwt\(|JwtDecoder|JwtAuthenticationConverter', re.MULTILINE)

    # Form login
    FORM_LOGIN_PATTERN = re.compile(r'\.formLogin\(', re.MULTILINE)

    # HTTP Basic
    HTTP_BASIC_PATTERN = re.compile(r'\.httpBasic\(', re.MULTILINE)

    # UserDetailsService
    USER_DETAILS_PATTERN = re.compile(
        r'(?:implements\s+UserDetailsService|UserDetailsService\s+\w+)',
        re.MULTILINE
    )

    # Method security annotations
    METHOD_SECURITY_PATTERN = re.compile(
        r'@(PreAuthorize|PostAuthorize|Secured|RolesAllowed)'
        r'\(\s*"([^"]*)"?\s*\)\s*\n'
        r'(?:@\w+(?:\([^)]*\))?\s*\n)*'
        r'(?:(?:public|protected|private)\s+)?'
        r'(?:static\s+)?(?:final\s+)?'
        r'(\w[\w<>,\s]*?)\s+(\w+)\s*\(',
        re.MULTILINE
    )

    # PasswordEncoder
    PASSWORD_ENCODER_PATTERN = re.compile(
        r'(BCryptPasswordEncoder|Pbkdf2PasswordEncoder|SCryptPasswordEncoder|'
        r'Argon2PasswordEncoder|DelegatingPasswordEncoder|NoOpPasswordEncoder)',
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Spring Security configuration from Java source code."""
        result: Dict[str, Any] = {
            'security_configs': [],
            'auth_infos': [],
            'method_security': [],
        }

        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        # SecurityFilterChain beans
        for match in self.FILTER_CHAIN_PATTERN.finditer(content):
            method_name = match.group(1)
            http_var = match.group(2)

            # Find the method body
            method_start = match.end()
            brace_count = 0
            method_end = method_start
            for i, ch in enumerate(content[method_start:], method_start):
                if ch == '{':
                    brace_count += 1
                elif ch == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        method_end = i
                        break

            body = content[match.start():method_end]

            has_cors = bool(self.CORS_PATTERN.search(body))
            has_csrf_disabled = bool(self.CSRF_DISABLE_PATTERN.search(body))

            session_match = self.SESSION_PATTERN.search(body)
            session_policy = session_match.group(1) if session_match else ""

            permitted_urls = [m.group(1) for m in self.PERMIT_ALL_PATTERN.finditer(body)]
            role_restrictions = [
                {'url': m.group(1), 'role': m.group(2)}
                for m in self.ROLE_PATTERN.finditer(body)
            ]

            # Determine auth type
            auth_type = ""
            if self.OAUTH2_RS_PATTERN.search(body):
                auth_type = "oauth2_resource_server"
            elif self.OAUTH2_LOGIN_PATTERN.search(body):
                auth_type = "oauth2"
            elif self.JWT_PATTERN.search(body):
                auth_type = "jwt"
            elif self.FORM_LOGIN_PATTERN.search(body):
                auth_type = "form_login"
            elif self.HTTP_BASIC_PATTERN.search(body):
                auth_type = "http_basic"

            result['security_configs'].append(SpringBootSecurityConfigInfo(
                name=method_name,
                config_type='filter_chain',
                has_cors=has_cors,
                has_csrf_disabled=has_csrf_disabled,
                has_session_management=bool(session_policy),
                session_policy=session_policy,
                auth_type=auth_type,
                permitted_urls=permitted_urls,
                role_restrictions=role_restrictions,
                annotations=['Bean'],
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Legacy WebSecurityConfigurerAdapter
        for match in self.LEGACY_SECURITY_PATTERN.finditer(content):
            class_name = match.group(1)
            result['security_configs'].append(SpringBootSecurityConfigInfo(
                name=class_name,
                config_type='web_security_adapter',
                annotations=['WebSecurityConfigurerAdapter'],
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Auth info
        if self.USER_DETAILS_PATTERN.search(content):
            result['auth_infos'].append(SpringBootAuthInfo(
                auth_type='custom',
                has_custom_user_details=True,
                file=file_path,
            ))

        if self.OAUTH2_LOGIN_PATTERN.search(content):
            result['auth_infos'].append(SpringBootAuthInfo(
                auth_type='oauth2_login',
                file=file_path,
            ))

        if self.OAUTH2_RS_PATTERN.search(content):
            result['auth_infos'].append(SpringBootAuthInfo(
                auth_type='oauth2_resource_server',
                file=file_path,
            ))

        # Method security
        for match in self.METHOD_SECURITY_PATTERN.finditer(content):
            annotation = match.group(1)
            expression = match.group(2)
            return_type = match.group(3)
            method_name = match.group(4)

            result['method_security'].append(SpringBootMethodSecurityInfo(
                annotation=annotation,
                expression=expression,
                target_method=method_name,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return result
