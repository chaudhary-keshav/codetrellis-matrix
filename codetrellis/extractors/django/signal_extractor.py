"""
Django Signal Extractor for CodeTrellis.

Extracts Django signal definitions, connections, and receivers.
Supports Django 1.x - 5.x signal patterns.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class DjangoSignalInfo:
    """Information about a Django signal connection."""
    name: str
    signal_type: str  # pre_save, post_save, custom, etc.
    receiver_name: str = ""
    sender: Optional[str] = None
    dispatch_uid: Optional[str] = None
    connection_type: str = "decorator"  # decorator, connect_call
    is_async: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class DjangoCustomSignalInfo:
    """Information about a custom Django signal."""
    name: str
    providing_args: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


# Built-in Django signals
BUILTIN_SIGNALS = {
    # Model signals
    'pre_save', 'post_save', 'pre_delete', 'post_delete',
    'm2m_changed', 'pre_init', 'post_init',
    # Request signals
    'request_started', 'request_finished', 'got_request_exception',
    # Management signals
    'pre_migrate', 'post_migrate',
    # Database signals
    'connection_created',
    # Auth signals
    'user_logged_in', 'user_logged_out', 'user_login_failed',
    # Test signals
    'setting_changed', 'template_rendered',
}


class DjangoSignalExtractor:
    """
    Extracts Django signal connections and custom signals.

    Handles:
    - @receiver decorator pattern
    - signal.connect() pattern
    - Custom signal definitions (Signal())
    - Async receivers (Django 4.1+)
    - Multiple signals per receiver
    - sender specification
    """

    # @receiver(signal, sender=Model)
    RECEIVER_DECORATOR_PATTERN = re.compile(
        r'@receiver\s*\(\s*([^,\)]+)'
        r'(?:\s*,\s*sender\s*=\s*(\w+))?'
        r'(?:\s*,\s*dispatch_uid\s*=\s*["\']([^"\']+)["\'])?'
        r'[^)]*\)\s*\n'
        r'(?:@\w+[^\n]*\n)*'
        r'\s*(async\s+)?def\s+(\w+)',
        re.MULTILINE
    )

    # signal.connect(receiver, sender=Model)
    SIGNAL_CONNECT_PATTERN = re.compile(
        r'(\w+(?:\.\w+)*)\.connect\s*\(\s*(\w+)'
        r'(?:\s*,\s*sender\s*=\s*(\w+))?'
        r'(?:\s*,\s*dispatch_uid\s*=\s*["\']([^"\']+)["\'])?',
        re.MULTILINE
    )

    # Custom signal definition
    CUSTOM_SIGNAL_PATTERN = re.compile(
        r'^(\w+)\s*=\s*(?:django\.dispatch\.)?Signal\s*\('
        r'(?:\s*providing_args\s*=\s*\[([^\]]*)\])?',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the Django signal extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Django signal connections and definitions.

        Returns:
            Dict with 'signal_connections' and 'custom_signals'
        """
        connections = []
        custom_signals = []

        # Extract @receiver decorators
        for match in self.RECEIVER_DECORATOR_PATTERN.finditer(content):
            signal_ref = match.group(1).strip()
            sender = match.group(2)
            dispatch_uid = match.group(3)
            is_async = match.group(4) is not None
            receiver_name = match.group(5)

            # Handle multiple signals: @receiver([pre_save, post_save])
            signals = self._parse_signal_refs(signal_ref)

            for signal_name in signals:
                connections.append(DjangoSignalInfo(
                    name=signal_name,
                    signal_type=self._classify_signal(signal_name),
                    receiver_name=receiver_name,
                    sender=sender,
                    dispatch_uid=dispatch_uid,
                    connection_type='decorator',
                    is_async=is_async,
                    file=file_path,
                    line_number=content[:match.start()].count('\n') + 1,
                ))

        # Extract signal.connect() calls
        for match in self.SIGNAL_CONNECT_PATTERN.finditer(content):
            signal_ref = match.group(1)
            receiver_name = match.group(2)
            sender = match.group(3)
            dispatch_uid = match.group(4)

            signal_name = signal_ref.split('.')[-1]

            connections.append(DjangoSignalInfo(
                name=signal_name,
                signal_type=self._classify_signal(signal_name),
                receiver_name=receiver_name,
                sender=sender,
                dispatch_uid=dispatch_uid,
                connection_type='connect_call',
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Extract custom signal definitions
        for match in self.CUSTOM_SIGNAL_PATTERN.finditer(content):
            name = match.group(1)
            providing_args_str = match.group(2) or ""
            providing_args = re.findall(r"['\"](\w+)['\"]", providing_args_str)

            custom_signals.append(DjangoCustomSignalInfo(
                name=name,
                providing_args=providing_args,
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return {
            'signal_connections': connections,
            'custom_signals': custom_signals,
        }

    def _parse_signal_refs(self, signal_ref: str) -> List[str]:
        """Parse signal reference(s) — handles single or list."""
        # Remove list brackets
        signal_ref = signal_ref.strip('[] ')
        parts = [s.strip() for s in signal_ref.split(',') if s.strip()]

        result = []
        for part in parts:
            # Extract the actual signal name from qualified refs
            name = part.split('.')[-1].strip()
            result.append(name)
        return result if result else [signal_ref.split('.')[-1].strip()]

    def _classify_signal(self, signal_name: str) -> str:
        """Classify signal type."""
        if signal_name in BUILTIN_SIGNALS:
            return signal_name
        return 'custom'
