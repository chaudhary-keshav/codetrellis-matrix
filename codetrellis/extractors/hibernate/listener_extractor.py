"""
Hibernate Listener Extractor - Extracts entity lifecycle callbacks and event listeners.

Extracts:
- JPA lifecycle callbacks (@PrePersist, @PostPersist, @PreUpdate, @PostUpdate, etc.)
- Entity listener classes (@EntityListeners)
- Hibernate event listeners (PreInsertEventListener, PostInsertEventListener, etc.)
- Hibernate Interceptor implementations
- Envers auditing listeners
- Spring-managed listeners
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class HibernateCallbackInfo:
    """Information about a JPA lifecycle callback."""
    callback_type: str = ""  # PrePersist, PostPersist, PreUpdate, PostUpdate, PreRemove, PostRemove, PostLoad
    method_name: str = ""
    entity_class: str = ""  # if in a listener class
    line_number: int = 0


@dataclass
class HibernateListenerInfo:
    """Information about a Hibernate event listener."""
    listener_type: str = ""  # PreInsertEventListener, PostInsertEventListener, etc.
    class_name: str = ""
    events_handled: List[str] = field(default_factory=list)
    is_spring_managed: bool = False
    line_number: int = 0


@dataclass
class HibernateInterceptorInfo:
    """Information about a Hibernate interceptor."""
    class_name: str = ""
    intercepted_methods: List[str] = field(default_factory=list)
    is_empty_interceptor: bool = False
    line_number: int = 0


class HibernateListenerExtractor:
    """Extracts Hibernate listener and lifecycle callback information."""

    # JPA lifecycle callbacks
    CALLBACK_PATTERN = re.compile(
        r'@(PrePersist|PostPersist|PreUpdate|PostUpdate|PreRemove|PostRemove|PostLoad)\s*'
        r'(?:public|protected|private)?\s*void\s+(\w+)\s*\(',
        re.MULTILINE
    )

    # Entity listeners
    ENTITY_LISTENERS_PATTERN = re.compile(
        r'@EntityListeners\s*\(\s*\{?\s*'
        r'([\w.,\s]+)'
        r'\s*\.class',
        re.DOTALL
    )

    # Single entity listener
    ENTITY_LISTENER_SINGLE_PATTERN = re.compile(
        r'@EntityListeners\s*\(\s*(\w+)\.class\s*\)',
        re.MULTILINE
    )

    # Hibernate event listener implementation
    EVENT_LISTENER_PATTERN = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+'
        r'(?:extends\s+\w+\s+)?'
        r'implements\s+(?:[\w,\s]*)'
        r'(PreInsertEventListener|PostInsertEventListener|'
        r'PreUpdateEventListener|PostUpdateEventListener|'
        r'PreDeleteEventListener|PostDeleteEventListener|'
        r'PreLoadEventListener|PostLoadEventListener|'
        r'FlushEventListener|AutoFlushEventListener|'
        r'SaveOrUpdateEventListener|MergeEventListener|'
        r'PersistEventListener|DeleteEventListener|'
        r'ReplicateEventListener|LockEventListener|'
        r'RefreshEventListener|EvictEventListener|'
        r'InitializeCollectionEventListener|'
        r'ResolveNaturalIdEventListener)',
        re.DOTALL
    )

    # Hibernate interceptor
    INTERCEPTOR_PATTERN = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+'
        r'(?:extends\s+(EmptyInterceptor|Interceptor)\s*)?'
        r'(?:implements\s+[\w,\s]*Interceptor)?',
        re.DOTALL
    )

    INTERCEPTOR_METHOD_PATTERN = re.compile(
        r'(?:@Override\s*)?(?:public\s+)?(?:boolean|String|Object|void|int\[\])\s+'
        r'(onSave|onFlushDirty|onDelete|onLoad|onPrepareStatement|'
        r'afterTransactionBegin|afterTransactionCompletion|'
        r'beforeTransactionCompletion|findDirty|instantiate|'
        r'getEntity|getEntityName|isTransient)\s*\(',
        re.MULTILINE
    )

    # Envers auditing
    ENVERS_PATTERN = re.compile(
        r'@Audited|@AuditOverride|@AuditJoinTable|'
        r'@NotAudited|@AuditTable|'
        r'AuditReader|AuditReaderFactory',
        re.MULTILINE
    )

    # Spring @Component or @Bean on listener
    SPRING_LISTENER_PATTERN = re.compile(
        r'(?:@Component|@Service|@Bean)\s*(?:\(.*?\))?\s*'
        r'(?:public\s+)?class\s+(\w+)\s+implements\s+.*EventListener',
        re.DOTALL
    )

    # @EventListener (Spring)
    SPRING_EVENT_LISTENER_PATTERN = re.compile(
        r'@(?:TransactionalEventListener|EventListener)\s*'
        r'(?:\(\s*(?:phase\s*=\s*TransactionPhase\.(\w+))?\s*\))?\s*'
        r'(?:public|protected|private)?\s*void\s+(\w+)\s*\(',
        re.DOTALL
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract listener and callback information."""
        callbacks: List[HibernateCallbackInfo] = []
        listeners: List[HibernateListenerInfo] = []
        interceptors: List[HibernateInterceptorInfo] = []
        entity_listener_classes: List[str] = []
        has_envers: bool = False

        if not content or not content.strip():
            return {
                'callbacks': callbacks,
                'listeners': listeners,
                'interceptors': interceptors,
                'entity_listener_classes': entity_listener_classes,
                'has_envers': has_envers,
            }

        # JPA lifecycle callbacks
        for match in self.CALLBACK_PATTERN.finditer(content):
            cb = HibernateCallbackInfo(
                callback_type=match.group(1),
                method_name=match.group(2),
                line_number=content[:match.start()].count('\n') + 1,
            )
            callbacks.append(cb)

        # Entity listener classes
        for match in self.ENTITY_LISTENER_SINGLE_PATTERN.finditer(content):
            entity_listener_classes.append(match.group(1))

        for match in self.ENTITY_LISTENERS_PATTERN.finditer(content):
            classes_str = match.group(1)
            classes = [c.strip() for c in classes_str.split(',') if c.strip()]
            entity_listener_classes.extend(classes)

        # Hibernate event listeners
        for match in self.EVENT_LISTENER_PATTERN.finditer(content):
            listener = HibernateListenerInfo(
                class_name=match.group(1),
                listener_type=match.group(2),
                line_number=content[:match.start()].count('\n') + 1,
            )
            listeners.append(listener)

        # Spring-managed listeners
        for match in self.SPRING_LISTENER_PATTERN.finditer(content):
            listener = HibernateListenerInfo(
                class_name=match.group(1),
                listener_type="spring_managed",
                is_spring_managed=True,
                line_number=content[:match.start()].count('\n') + 1,
            )
            listeners.append(listener)

        # Spring @EventListener / @TransactionalEventListener
        for match in self.SPRING_EVENT_LISTENER_PATTERN.finditer(content):
            cb = HibernateCallbackInfo(
                callback_type="TransactionalEventListener" if match.group(1) else "EventListener",
                method_name=match.group(2),
                line_number=content[:match.start()].count('\n') + 1,
            )
            callbacks.append(cb)

        # Interceptors - only if file contains Interceptor reference
        if 'Interceptor' in content and ('EmptyInterceptor' in content or 'implements' in content):
            for match in self.INTERCEPTOR_PATTERN.finditer(content):
                if match.group(2) or 'Interceptor' in (match.group(0) or ""):
                    interceptor = HibernateInterceptorInfo(
                        class_name=match.group(1),
                        is_empty_interceptor=match.group(2) == "EmptyInterceptor" if match.group(2) else False,
                        line_number=content[:match.start()].count('\n') + 1,
                    )

                    # Find intercepted methods
                    for m in self.INTERCEPTOR_METHOD_PATTERN.finditer(content):
                        interceptor.intercepted_methods.append(m.group(1))

                    if interceptor.intercepted_methods:
                        interceptors.append(interceptor)

        # Envers
        has_envers = bool(self.ENVERS_PATTERN.search(content))

        return {
            'callbacks': callbacks,
            'listeners': listeners,
            'interceptors': interceptors,
            'entity_listener_classes': entity_listener_classes,
            'has_envers': has_envers,
        }
