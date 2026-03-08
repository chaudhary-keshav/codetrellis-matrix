"""
Hibernate Session Extractor - Extracts SessionFactory/Session/EntityManager usage.

Extracts:
- SessionFactory configuration and creation
- Session operations (save, update, delete, merge, persist, get, load)
- EntityManager usage (JPA standard)
- Transaction management (@Transactional, manual begin/commit/rollback)
- Flush modes, connection handling
- Stateless sessions
- Multi-tenancy configuration
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class HibernateSessionFactoryInfo:
    """Information about SessionFactory / EntityManagerFactory configuration."""
    factory_type: str = ""  # SessionFactory, EntityManagerFactory
    config_method: str = ""  # xml, annotation, programmatic
    data_source: str = ""
    dialect: str = ""
    properties: Dict[str, str] = field(default_factory=dict)
    is_multi_tenant: bool = False
    tenant_strategy: str = ""  # DATABASE, SCHEMA, DISCRIMINATOR
    line_number: int = 0


@dataclass
class HibernateTransactionInfo:
    """Information about transaction management."""
    transaction_type: str = ""  # declarative, programmatic
    annotation: str = ""  # @Transactional
    propagation: str = ""  # REQUIRED, REQUIRES_NEW, etc.
    isolation: str = ""  # READ_COMMITTED, SERIALIZABLE, etc.
    read_only: bool = False
    timeout: int = -1
    rollback_for: List[str] = field(default_factory=list)
    method_name: str = ""
    line_number: int = 0


class HibernateSessionExtractor:
    """Extracts Hibernate session and transaction information."""

    # SessionFactory patterns
    SESSION_FACTORY_PATTERN = re.compile(
        r'(?:SessionFactory|EntityManagerFactory)\s+\w+\s*=\s*'
        r'(?:new\s+Configuration\(\)|'
        r'Persistence\.createEntityManagerFactory|'
        r'new\s+MetadataSources)',
        re.MULTILINE
    )

    LOCAL_SESSION_FACTORY_PATTERN = re.compile(
        r'@Bean\s*(?:\(.*?\))?\s*(?:public\s+)?'
        r'(?:LocalSessionFactoryBean|LocalContainerEntityManagerFactoryBean)\s+(\w+)',
        re.DOTALL
    )

    # Session operations
    SESSION_OPERATION_PATTERN = re.compile(
        r'(?:session|entityManager|em)\s*\.\s*'
        r'(save|persist|update|merge|delete|remove|get|load|find|'
        r'saveOrUpdate|refresh|evict|detach|lock|replicate)\s*\(',
        re.MULTILINE
    )

    # Flush mode
    FLUSH_MODE_PATTERN = re.compile(
        r'setFlushMode\s*\(\s*FlushMode(?:Type)?\.(\w+)\s*\)',
        re.MULTILINE
    )

    # Transaction patterns
    TRANSACTIONAL_PATTERN = re.compile(
        r'@Transactional\s*(?:\(\s*(.*?)\))?\s*'
        r'(?:public|protected|private)?\s*\w+(?:<[^>]+>)?\s+(\w+)\s*\(',
        re.DOTALL
    )

    PROGRAMMATIC_TX_PATTERN = re.compile(
        r'(?:session|entityManager|em)\s*\.\s*'
        r'(?:beginTransaction|getTransaction\(\)\.begin)\s*\(',
        re.MULTILINE
    )

    TX_COMMIT_PATTERN = re.compile(
        r'(?:transaction|tx)\s*\.\s*commit\s*\(',
        re.MULTILINE
    )

    TX_ROLLBACK_PATTERN = re.compile(
        r'(?:transaction|tx)\s*\.\s*rollback\s*\(',
        re.MULTILINE
    )

    # Stateless session
    STATELESS_SESSION_PATTERN = re.compile(
        r'openStatelessSession\s*\(',
        re.MULTILINE
    )

    # Multi-tenancy
    MULTI_TENANT_PATTERN = re.compile(
        r'MultiTenancyStrategy\.(\w+)|'
        r'@TenantId|'
        r'CurrentTenantIdentifierResolver|'
        r'MultiTenantConnectionProvider',
        re.MULTILINE
    )

    # Dialect
    DIALECT_PATTERN = re.compile(
        r'(?:hibernate\.dialect|setProperty\s*\(\s*["\']hibernate\.dialect["\'])\s*'
        r'[,=]\s*["\']?(?:org\.hibernate\.dialect\.)?(\w+Dialect)["\']?',
        re.MULTILINE
    )

    # Data source
    DATASOURCE_PATTERN = re.compile(
        r'(?:dataSource|DataSource|connection\.url)\s*[=,]\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract session and transaction information."""
        session_factories: List[HibernateSessionFactoryInfo] = []
        transactions: List[HibernateTransactionInfo] = []
        session_operations: List[str] = []
        has_stateless_session = False
        flush_modes: List[str] = []

        if not content or not content.strip():
            return {
                'session_factories': session_factories,
                'transactions': transactions,
                'session_operations': session_operations,
                'has_stateless_session': has_stateless_session,
                'flush_modes': flush_modes,
            }

        # Session factories
        for match in self.SESSION_FACTORY_PATTERN.finditer(content):
            factory = HibernateSessionFactoryInfo(
                factory_type="SessionFactory",
                config_method="programmatic",
                line_number=content[:match.start()].count('\n') + 1,
            )

            # Detect dialect
            dialect = self.DIALECT_PATTERN.search(content)
            if dialect:
                factory.dialect = dialect.group(1)

            # Detect data source
            ds = self.DATASOURCE_PATTERN.search(content)
            if ds:
                factory.data_source = ds.group(1)

            # Multi-tenancy
            mt = self.MULTI_TENANT_PATTERN.search(content)
            if mt:
                factory.is_multi_tenant = True
                if mt.group(1):
                    factory.tenant_strategy = mt.group(1)

            session_factories.append(factory)

        # Spring-managed session factories
        for match in self.LOCAL_SESSION_FACTORY_PATTERN.finditer(content):
            factory = HibernateSessionFactoryInfo(
                factory_type=match.group(1) or "localSessionFactory",
                config_method="spring",
                line_number=content[:match.start()].count('\n') + 1,
            )
            session_factories.append(factory)

        # Session operations
        for match in self.SESSION_OPERATION_PATTERN.finditer(content):
            session_operations.append(match.group(1))

        # Flush modes
        for match in self.FLUSH_MODE_PATTERN.finditer(content):
            flush_modes.append(match.group(1))

        # Stateless session
        has_stateless_session = bool(self.STATELESS_SESSION_PATTERN.search(content))

        # Declarative transactions
        for match in self.TRANSACTIONAL_PATTERN.finditer(content):
            tx = HibernateTransactionInfo(
                transaction_type="declarative",
                annotation="@Transactional",
                method_name=match.group(2) or "",
                line_number=content[:match.start()].count('\n') + 1,
            )

            attrs = match.group(1) or ""
            # Parse propagation
            prop = re.search(r'propagation\s*=\s*Propagation\.(\w+)', attrs)
            if prop:
                tx.propagation = prop.group(1)

            # Parse isolation
            iso = re.search(r'isolation\s*=\s*Isolation\.(\w+)', attrs)
            if iso:
                tx.isolation = iso.group(1)

            # Parse readOnly
            if 'readOnly' in attrs and 'true' in attrs:
                tx.read_only = True

            # Parse rollbackFor
            rbf = re.findall(r'(\w+Exception)\.class', attrs)
            tx.rollback_for = rbf

            transactions.append(tx)

        # Programmatic transactions
        for match in self.PROGRAMMATIC_TX_PATTERN.finditer(content):
            tx = HibernateTransactionInfo(
                transaction_type="programmatic",
                line_number=content[:match.start()].count('\n') + 1,
            )
            transactions.append(tx)

        return {
            'session_factories': session_factories,
            'transactions': transactions,
            'session_operations': session_operations,
            'has_stateless_session': has_stateless_session,
            'flush_modes': flush_modes,
        }
