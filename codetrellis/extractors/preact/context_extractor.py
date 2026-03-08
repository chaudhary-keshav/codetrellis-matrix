"""
Preact Context Extractor for CodeTrellis

Extracts Preact context usage patterns from JavaScript/TypeScript source code:
- createContext() definitions
- Provider component usage
- Consumer component usage (legacy)
- useContext() hook usage
- contextType class property (legacy)
- Context composition / nesting patterns

Supports:
- Preact X (10.x): createContext, Provider, useContext
- Preact 8.x: Legacy context API (contextType)

Part of CodeTrellis v4.64 - Preact Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PreactContextInfo:
    """Information about a Preact context definition."""
    name: str
    file: str = ""
    line_number: int = 0
    type_annotation: str = ""
    default_value: str = ""
    is_exported: bool = False
    has_provider: bool = False
    has_consumer: bool = False
    provider_count: int = 0


@dataclass
class PreactContextConsumerInfo:
    """Information about a useContext consumer."""
    context_name: str
    file: str = ""
    line_number: int = 0
    component: str = ""
    variable_name: str = ""


class PreactContextExtractor:
    """
    Extracts Preact context patterns from source code.

    Detects:
    - createContext() / createContext<T>() definitions
    - Provider usage (<Context.Provider>, <CtxProvider>)
    - Consumer usage (<Context.Consumer>) — legacy
    - useContext() hook calls
    - contextType class static property
    """

    # createContext() pattern
    CREATE_CONTEXT_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'(?:Preact\.)?createContext\s*'
        r'(?:<\s*([^>]*)\s*>)?\s*\(\s*([^)]*)\s*\)',
        re.MULTILINE
    )

    # Provider pattern: <SomeContext.Provider value={...}>
    PROVIDER_PATTERN = re.compile(
        r'<(\w+)\.Provider\b',
        re.MULTILINE
    )

    # Consumer pattern: <SomeContext.Consumer>
    CONSUMER_PATTERN = re.compile(
        r'<(\w+)\.Consumer\b',
        re.MULTILINE
    )

    # useContext() hook pattern
    USE_CONTEXT_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*'
        r'useContext\s*(?:<[^>]*>)?\s*\(\s*(\w+)\s*\)',
        re.MULTILINE
    )

    # Bare useContext (without variable assignment)
    BARE_USE_CONTEXT_PATTERN = re.compile(
        r'useContext\s*(?:<[^>]*>)?\s*\(\s*(\w+)\s*\)',
        re.MULTILINE
    )

    # contextType static property (class components)
    CONTEXT_TYPE_PATTERN = re.compile(
        r'static\s+contextType\s*=\s*(\w+)',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Preact context patterns from source code."""
        contexts: List[PreactContextInfo] = []
        consumers: List[PreactContextConsumerInfo] = []

        # Collect Provider/Consumer usages
        provider_names = set(m.group(1) for m in self.PROVIDER_PATTERN.finditer(content))
        consumer_names = set(m.group(1) for m in self.CONSUMER_PATTERN.finditer(content))

        # ── createContext() definitions ───────────────────────────
        for m in self.CREATE_CONTEXT_PATTERN.finditer(content):
            name = m.group(1)
            type_ann = m.group(2) or ""
            default_val = m.group(3) or ""
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 50):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix

            contexts.append(PreactContextInfo(
                name=name,
                file=file_path,
                line_number=line,
                type_annotation=type_ann,
                default_value=default_val.strip()[:50],
                is_exported=is_exported,
                has_provider=name in provider_names,
                has_consumer=name in consumer_names,
                provider_count=sum(1 for pm in self.PROVIDER_PATTERN.finditer(content) if pm.group(1) == name),
            ))

        # ── useContext() consumers ────────────────────────────────
        for m in self.USE_CONTEXT_PATTERN.finditer(content):
            var_name = m.group(1)
            ctx_name = m.group(2)
            line = content[:m.start()].count('\n') + 1

            # Find enclosing component
            before = content[max(0, m.start() - 2000):m.start()]
            func_match = re.findall(r'function\s+([A-Z]\w*|use[A-Z]\w*)\s*\(', before)
            arrow_match = re.findall(r'(?:const|let|var)\s+([A-Z]\w*|use[A-Z]\w*)\s*=', before)
            component = ""
            if func_match:
                component = func_match[-1]
            elif arrow_match:
                component = arrow_match[-1]

            consumers.append(PreactContextConsumerInfo(
                context_name=ctx_name,
                file=file_path,
                line_number=line,
                component=component,
                variable_name=var_name,
            ))

        # ── Bare useContext() (no variable) ───────────────────────
        assigned_lines = set()
        for m in self.USE_CONTEXT_PATTERN.finditer(content):
            assigned_lines.add(content[:m.start()].count('\n') + 1)

        for m in self.BARE_USE_CONTEXT_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            if line in assigned_lines:
                continue

            ctx_name = m.group(1)
            before = content[max(0, m.start() - 2000):m.start()]
            func_match = re.findall(r'function\s+([A-Z]\w*|use[A-Z]\w*)\s*\(', before)
            arrow_match = re.findall(r'(?:const|let|var)\s+([A-Z]\w*|use[A-Z]\w*)\s*=', before)
            component = ""
            if func_match:
                component = func_match[-1]
            elif arrow_match:
                component = arrow_match[-1]

            consumers.append(PreactContextConsumerInfo(
                context_name=ctx_name,
                file=file_path,
                line_number=line,
                component=component,
                variable_name="",
            ))

        return {
            'contexts': contexts,
            'consumers': consumers,
        }
