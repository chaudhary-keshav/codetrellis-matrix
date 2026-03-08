"""
Jakarta EE EJB Extractor v1.0 - Session beans, message-driven beans, timers.
Part of CodeTrellis v4.94 - Jakarta EE Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any
from codetrellis.extractors.java_utils import normalize_java_content


@dataclass
class JakartaSessionBeanInfo:
    """An EJB session bean."""
    name: str
    bean_type: str = ""  # stateless, stateful, singleton
    local_interfaces: List[str] = field(default_factory=list)
    remote_interfaces: List[str] = field(default_factory=list)
    transaction_type: str = ""  # container, bean
    is_startup: bool = False
    annotations: List[str] = field(default_factory=list)
    namespace: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class JakartaMessageDrivenBeanInfo:
    """A message-driven bean."""
    name: str
    destination: str = ""
    destination_type: str = ""  # queue, topic
    message_listener_interface: str = ""
    activation_config: Dict[str, str] = field(default_factory=dict)
    file: str = ""
    line_number: int = 0


@dataclass
class JakartaTimerInfo:
    """An EJB timer."""
    name: str
    schedule: str = ""
    timer_type: str = ""  # schedule, timeout, programmatic
    persistent: bool = True
    file: str = ""
    line_number: int = 0


class JakartaEJBExtractor:
    """Extracts Jakarta EJB patterns."""

    STATELESS_PATTERN = re.compile(
        r'@Stateless\s*(?:\([^)]*\))?\s*\n'
        r'((?:@\w+(?:\([^)]*\))?\s*\n)*)'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    STATEFUL_PATTERN = re.compile(
        r'@Stateful\s*(?:\([^)]*\))?\s*\n'
        r'((?:@\w+(?:\([^)]*\))?\s*\n)*)'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    SINGLETON_PATTERN = re.compile(
        r'@Singleton\s*\n'
        r'((?:@\w+(?:\([^)]*\))?\s*\n)*)'
        r'(?:public\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    STARTUP_PATTERN = re.compile(r'@Startup\b')

    LOCAL_PATTERN = re.compile(
        r'@Local\(\s*\{?([^})]+)\}?\s*\)',
        re.MULTILINE
    )

    REMOTE_PATTERN = re.compile(
        r'@Remote\(\s*\{?([^})]+)\}?\s*\)',
        re.MULTILINE
    )

    TRANSACTION_ATTR_PATTERN = re.compile(
        r'@TransactionManagement\(\s*TransactionManagementType\.(\w+)\s*\)',
        re.MULTILINE
    )

    MDB_PATTERN = re.compile(
        r'@MessageDriven\(\s*(?:name\s*=\s*"[^"]*"\s*,\s*)?'
        r'(?:activationConfig\s*=\s*\{([^}]+)\})?\s*\)\s*\n'
        r'(?:public\s+)?class\s+(\w+)\s+implements\s+(\w+)',
        re.MULTILINE
    )

    ACTIVATION_CONFIG_PATTERN = re.compile(
        r'@ActivationConfigProperty\(\s*'
        r'propertyName\s*=\s*"([^"]+)"\s*,\s*'
        r'propertyValue\s*=\s*"([^"]+)"',
        re.MULTILINE
    )

    SCHEDULE_PATTERN = re.compile(
        r'@Schedule\(\s*([^)]+)\)\s*\n'
        r'(?:public\s+)?void\s+(\w+)',
        re.MULTILINE
    )

    TIMEOUT_PATTERN = re.compile(
        r'@Timeout\s*\n(?:public\s+)?void\s+(\w+)',
        re.MULTILINE
    )

    NAMESPACE_PATTERN = re.compile(r'import\s+(jakarta|javax)\.ejb\.')

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        result: Dict[str, Any] = {'session_beans': [], 'message_driven_beans': [], 'timers': []}
        if not content or not content.strip():
            return result

        content = normalize_java_content(content)

        ns_match = self.NAMESPACE_PATTERN.search(content)
        namespace = ns_match.group(1) if ns_match else ""

        # Extract session beans
        for bean_type, pattern in [('stateless', self.STATELESS_PATTERN),
                                    ('stateful', self.STATEFUL_PATTERN),
                                    ('singleton', self.SINGLETON_PATTERN)]:
            for match in pattern.finditer(content):
                between = match.group(1) or ""
                class_name = match.group(2)

                is_startup = bool(self.STARTUP_PATTERN.search(between))

                # Local interfaces
                local_match = self.LOCAL_PATTERN.search(content)
                local_interfaces = []
                if local_match:
                    local_interfaces = [i.strip().rstrip('.class') for i in local_match.group(1).split(',')]

                # Remote interfaces
                remote_match = self.REMOTE_PATTERN.search(content)
                remote_interfaces = []
                if remote_match:
                    remote_interfaces = [i.strip().rstrip('.class') for i in remote_match.group(1).split(',')]

                # Transaction type
                tx_match = self.TRANSACTION_ATTR_PATTERN.search(content)
                tx_type = tx_match.group(1).lower() if tx_match else "container"

                annotations = re.findall(r'@(\w+)', between)
                annotations.insert(0, bean_type.capitalize())

                result['session_beans'].append(JakartaSessionBeanInfo(
                    name=class_name, bean_type=bean_type,
                    local_interfaces=local_interfaces,
                    remote_interfaces=remote_interfaces,
                    transaction_type=tx_type,
                    is_startup=is_startup,
                    annotations=annotations,
                    namespace=namespace,
                    file=file_path, line_number=content[:match.start()].count('\n') + 1,
                ))

        # Extract message-driven beans
        for match in self.MDB_PATTERN.finditer(content):
            activation_raw = match.group(1) or ""
            class_name = match.group(2)
            listener_interface = match.group(3)

            activation_config = {}
            for am in self.ACTIVATION_CONFIG_PATTERN.finditer(activation_raw):
                activation_config[am.group(1)] = am.group(2)

            destination = activation_config.get('destination', '')
            dest_type = activation_config.get('destinationType', '')
            if 'Queue' in dest_type:
                dest_type = 'queue'
            elif 'Topic' in dest_type:
                dest_type = 'topic'

            result['message_driven_beans'].append(JakartaMessageDrivenBeanInfo(
                name=class_name, destination=destination,
                destination_type=dest_type,
                message_listener_interface=listener_interface,
                activation_config=activation_config,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        # Extract timers
        for match in self.SCHEDULE_PATTERN.finditer(content):
            schedule_attrs = match.group(1)
            method_name = match.group(2)
            persistent = 'persistent = false' not in schedule_attrs.lower()

            result['timers'].append(JakartaTimerInfo(
                name=method_name, schedule=schedule_attrs.strip(),
                timer_type='schedule', persistent=persistent,
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        for match in self.TIMEOUT_PATTERN.finditer(content):
            result['timers'].append(JakartaTimerInfo(
                name=match.group(1), timer_type='timeout',
                file=file_path, line_number=content[:match.start()].count('\n') + 1,
            ))

        return result
