"""
JavaAnnotationExtractor - Extracts annotation usage patterns from Java code.

Extracts:
- Spring annotations (@Service, @Component, @Repository, @Configuration, etc.)
- JPA annotations (@Entity, @Table, @Column, etc.)
- Validation annotations (@NotNull, @Size, @Valid, etc.)
- Security annotations (@PreAuthorize, @Secured, etc.)
- Test annotations (@Test, @SpringBootTest, @MockBean, etc.)
- Custom annotation usage

Part of CodeTrellis v4.12 - Java Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set


@dataclass
class JavaAnnotationUsage:
    """Information about an annotation usage in Java code."""
    name: str
    target: str  # class, method, field, parameter the annotation is applied to
    target_type: str  # class, method, field, parameter
    attributes: Dict[str, str] = field(default_factory=dict)
    category: str = "other"  # spring_di, jpa, validation, security, test, config, etc.
    file: str = ""
    line_number: int = 0


class JavaAnnotationExtractor:
    """
    Extracts annotation usage from Java source code.

    Categories annotations into:
    - Spring DI: @Service, @Component, @Repository, @Autowired, @Inject, @Bean
    - Spring Web: @RestController, @Controller, @RequestMapping
    - Spring Config: @Configuration, @Value, @ConfigurationProperties, @Profile
    - Spring Boot: @SpringBootApplication, @EnableAutoConfiguration
    - Spring Cloud: @FeignClient, @LoadBalanced, @EnableDiscoveryClient
    - JPA/Hibernate: @Entity, @Table, @Column, @ManyToOne, @OneToMany
    - Validation: @NotNull, @Size, @Min, @Max, @Pattern, @Valid
    - Security: @PreAuthorize, @Secured, @RolesAllowed
    - Test: @Test, @SpringBootTest, @MockBean, @DataJpaTest
    - Lombok: @Data, @Builder, @Getter, @Setter, @NoArgsConstructor
    - Jakarta: @Inject, @Named, @Singleton, @ApplicationScoped
    - Scheduling: @Scheduled, @Async, @EnableScheduling
    - Caching: @Cacheable, @CacheEvict, @EnableCaching
    """

    # Category mappings
    ANNOTATION_CATEGORIES: Dict[str, str] = {
        # Spring DI
        'Service': 'spring_di', 'Component': 'spring_di', 'Repository': 'spring_di',
        'Autowired': 'spring_di', 'Inject': 'spring_di', 'Bean': 'spring_di',
        'Qualifier': 'spring_di', 'Primary': 'spring_di', 'Lazy': 'spring_di',
        'Scope': 'spring_di', 'Conditional': 'spring_di',

        # Spring Web
        'RestController': 'spring_web', 'Controller': 'spring_web',
        'RequestMapping': 'spring_web', 'GetMapping': 'spring_web',
        'PostMapping': 'spring_web', 'PutMapping': 'spring_web',
        'DeleteMapping': 'spring_web', 'PatchMapping': 'spring_web',
        'ResponseBody': 'spring_web', 'RequestBody': 'spring_web',
        'PathVariable': 'spring_web', 'RequestParam': 'spring_web',
        'RequestHeader': 'spring_web', 'CrossOrigin': 'spring_web',

        # Spring Config
        'Configuration': 'spring_config', 'Value': 'spring_config',
        'ConfigurationProperties': 'spring_config', 'Profile': 'spring_config',
        'PropertySource': 'spring_config', 'EnableAutoConfiguration': 'spring_config',
        'SpringBootApplication': 'spring_config', 'ConditionalOnProperty': 'spring_config',

        # Spring Cloud
        'FeignClient': 'spring_cloud', 'LoadBalanced': 'spring_cloud',
        'EnableDiscoveryClient': 'spring_cloud', 'EnableEurekaClient': 'spring_cloud',
        'CircuitBreaker': 'spring_cloud', 'RefreshScope': 'spring_cloud',

        # JPA / Hibernate
        'Entity': 'jpa', 'Table': 'jpa', 'Column': 'jpa', 'Id': 'jpa',
        'GeneratedValue': 'jpa', 'ManyToOne': 'jpa', 'OneToMany': 'jpa',
        'ManyToMany': 'jpa', 'OneToOne': 'jpa', 'JoinColumn': 'jpa',
        'Embeddable': 'jpa', 'Embedded': 'jpa', 'MappedSuperclass': 'jpa',
        'Inheritance': 'jpa', 'NamedQuery': 'jpa', 'Transient': 'jpa',
        'Version': 'jpa', 'Lob': 'jpa', 'Enumerated': 'jpa',

        # Validation
        'NotNull': 'validation', 'NotBlank': 'validation', 'NotEmpty': 'validation',
        'Size': 'validation', 'Min': 'validation', 'Max': 'validation',
        'Pattern': 'validation', 'Email': 'validation', 'Valid': 'validation',
        'Positive': 'validation', 'Negative': 'validation', 'Past': 'validation',
        'Future': 'validation', 'DecimalMin': 'validation', 'DecimalMax': 'validation',

        # Security
        'PreAuthorize': 'security', 'PostAuthorize': 'security',
        'Secured': 'security', 'RolesAllowed': 'security',
        'EnableWebSecurity': 'security', 'EnableMethodSecurity': 'security',

        # Test
        'Test': 'test', 'SpringBootTest': 'test', 'MockBean': 'test',
        'DataJpaTest': 'test', 'WebMvcTest': 'test', 'BeforeEach': 'test',
        'AfterEach': 'test', 'ParameterizedTest': 'test', 'DisplayName': 'test',
        'ExtendWith': 'test', 'Mock': 'test', 'InjectMocks': 'test',

        # Lombok
        'Data': 'lombok', 'Builder': 'lombok', 'Getter': 'lombok',
        'Setter': 'lombok', 'NoArgsConstructor': 'lombok',
        'AllArgsConstructor': 'lombok', 'RequiredArgsConstructor': 'lombok',
        'ToString': 'lombok', 'EqualsAndHashCode': 'lombok', 'Slf4j': 'lombok',
        'Log': 'lombok', 'SuperBuilder': 'lombok',

        # Scheduling & Async
        'Scheduled': 'scheduling', 'Async': 'scheduling',
        'EnableScheduling': 'scheduling', 'EnableAsync': 'scheduling',

        # Caching
        'Cacheable': 'caching', 'CacheEvict': 'caching',
        'CachePut': 'caching', 'EnableCaching': 'caching',

        # Transactional
        'Transactional': 'transaction',

        # Jakarta/CDI
        'ApplicationScoped': 'jakarta', 'RequestScoped': 'jakarta',
        'SessionScoped': 'jakarta', 'Singleton': 'jakarta',
        'Named': 'jakarta', 'Produces': 'jakarta',
    }

    # Pattern to find annotations on classes/methods/fields
    ANNOTATION_ON_TARGET = re.compile(
        r'((?:@\w+(?:\([^)]*\))?[\s\n]*)+)'   # annotation block
        r'(?:(?:public|protected|private|static|final|abstract|synchronized|default|volatile|transient)\s+)*'
        r'(?:(?:class|interface|enum|record|@interface)\s+(\w+)|'     # class/interface/enum name
        r'(?:[\w<>\[\].,?\s]+?)\s+(\w+)\s*(?:\(|;|=))',              # method/field name
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> List[JavaAnnotationUsage]:
        """Extract all annotation usages from Java source code."""
        usages = []
        seen: Set[str] = set()

        for match in self.ANNOTATION_ON_TARGET.finditer(content):
            annotations_block = match.group(1)
            class_name = match.group(2)
            member_name = match.group(3)

            target = class_name or member_name or ""
            target_type = "class" if class_name else "method_or_field"

            # Parse individual annotations from the block
            for ann_match in re.finditer(r'@(\w+)(?:\(([^)]*)\))?', annotations_block):
                ann_name = ann_match.group(1)
                ann_attrs_str = ann_match.group(2) or ""

                # Deduplicate
                key = f"{ann_name}:{target}:{file_path}"
                if key in seen:
                    continue
                seen.add(key)

                category = self.ANNOTATION_CATEGORIES.get(ann_name, 'other')

                # Parse attributes
                attributes = {}
                if ann_attrs_str:
                    for attr in re.finditer(r'(\w+)\s*=\s*([^,]+)', ann_attrs_str):
                        attributes[attr.group(1)] = attr.group(2).strip().strip('"\'')

                line_number = content[:match.start()].count('\n') + 1

                usages.append(JavaAnnotationUsage(
                    name=ann_name,
                    target=target,
                    target_type=target_type,
                    attributes=attributes,
                    category=category,
                    file=file_path,
                    line_number=line_number,
                ))

        return usages

    def summarize(self, usages: List[JavaAnnotationUsage]) -> Dict[str, Any]:
        """Summarize annotation usage by category."""
        summary: Dict[str, Dict[str, int]] = {}
        for usage in usages:
            if usage.category not in summary:
                summary[usage.category] = {}
            if usage.name not in summary[usage.category]:
                summary[usage.category][usage.name] = 0
            summary[usage.category][usage.name] += 1
        return summary
