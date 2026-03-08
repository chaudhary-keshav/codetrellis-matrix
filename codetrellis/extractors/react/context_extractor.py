"""
React Context Extractor for CodeTrellis

Extracts React Context patterns from JavaScript/TypeScript source code:
- React.createContext() definitions
- Context.Provider usage
- useContext() consumers
- Context composition patterns
- Context value type detection

Part of CodeTrellis v4.32 - React Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ReactContextInfo:
    """Information about a React Context definition."""
    name: str
    file: str = ""
    line_number: int = 0
    value_type: str = ""  # TypeScript type of the context value
    default_value: str = ""  # Default value passed to createContext
    has_provider: bool = False  # Whether a Provider component is defined nearby
    provider_name: str = ""  # Name of the provider component
    is_exported: bool = False
    consumers: List[str] = field(default_factory=list)  # Components that consume this context


@dataclass
class ReactContextConsumerInfo:
    """Information about a context consumer."""
    context_name: str
    consumer_component: str = ""
    file: str = ""
    line_number: int = 0
    usage_pattern: str = "useContext"  # useContext, Context.Consumer, static contextType


class ReactContextExtractor:
    """
    Extracts React Context patterns from JavaScript/TypeScript source code.

    Detects:
    - createContext() definitions with type detection
    - Provider wrapper components
    - useContext() usage
    - Legacy Context.Consumer and contextType patterns
    """

    # createContext pattern
    CREATE_CONTEXT_PATTERN = re.compile(
        r'(?:export\s+)?'
        r'(?:const|let|var)\s+(\w+)\s*'
        r'(?::\s*React\.Context\s*<\s*([^>]+?)\s*>)?\s*'
        r'=\s*(?:React\.)?createContext\s*'
        r'(?:<\s*([^>]+?)\s*>)?\s*\(\s*'
        r'([^)]*?)\s*\)',
        re.MULTILINE
    )

    # useContext usage
    USE_CONTEXT_PATTERN = re.compile(
        r'(?:const|let)\s+(\w+)\s*=\s*useContext\s*\(\s*(\w+)\s*\)',
        re.MULTILINE
    )

    # Context.Consumer (legacy)
    CONSUMER_PATTERN = re.compile(
        r'<(\w+)\.Consumer\s*>',
        re.MULTILINE
    )

    # static contextType (class components)
    CONTEXT_TYPE_PATTERN = re.compile(
        r'static\s+contextType\s*=\s*(\w+)',
        re.MULTILINE
    )

    # Provider component pattern
    PROVIDER_COMPONENT_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|function)\s+(\w+Provider)\s*'
        r'(?::\s*\w+)?\s*[=(]',
        re.MULTILINE
    )

    # Context.Provider usage
    CONTEXT_PROVIDER_USAGE = re.compile(
        r'<(\w+)\.Provider\s+value\s*=',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract React Context patterns from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'contexts', 'consumers'
        """
        contexts = []
        consumers = []

        # ── Context Definitions ───────────────────────────────────
        for m in self.CREATE_CONTEXT_PATTERN.finditer(content):
            name = m.group(1)
            type_annotation = m.group(2) or m.group(3) or ""
            default_value = m.group(4) or ""
            line = content[:m.start()].count('\n') + 1

            is_exported = 'export' in content[max(0, m.start() - 20):m.start()]

            # Check if a Provider component exists in the same file
            provider_name = ""
            has_provider = False
            provider_match = re.search(
                rf'(?:const|function)\s+(\w*{re.escape(name.replace("Context", ""))}Provider\w*)',
                content
            )
            if provider_match:
                provider_name = provider_match.group(1)
                has_provider = True

            # Also check for direct Provider usage
            if not has_provider:
                if re.search(rf'<{re.escape(name)}\.Provider', content):
                    has_provider = True

            ctx = ReactContextInfo(
                name=name,
                file=file_path,
                line_number=line,
                value_type=type_annotation.strip(),
                default_value=default_value.strip()[:100],
                has_provider=has_provider,
                provider_name=provider_name,
                is_exported=is_exported,
            )
            contexts.append(ctx)

        # ── useContext Consumers ──────────────────────────────────
        for m in self.USE_CONTEXT_PATTERN.finditer(content):
            variable = m.group(1)
            context_name = m.group(2)
            line = content[:m.start()].count('\n') + 1

            consumer = ReactContextConsumerInfo(
                context_name=context_name,
                consumer_component=variable,
                file=file_path,
                line_number=line,
                usage_pattern="useContext",
            )
            consumers.append(consumer)

        # ── Legacy Context.Consumer ───────────────────────────────
        for m in self.CONSUMER_PATTERN.finditer(content):
            context_name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            consumer = ReactContextConsumerInfo(
                context_name=context_name,
                file=file_path,
                line_number=line,
                usage_pattern="Consumer",
            )
            consumers.append(consumer)

        # ── static contextType ────────────────────────────────────
        for m in self.CONTEXT_TYPE_PATTERN.finditer(content):
            context_name = m.group(1)
            line = content[:m.start()].count('\n') + 1

            consumer = ReactContextConsumerInfo(
                context_name=context_name,
                file=file_path,
                line_number=line,
                usage_pattern="contextType",
            )
            consumers.append(consumer)

        return {
            'contexts': contexts,
            'consumers': consumers,
        }
