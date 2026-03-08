"""
Qwik Store & Context Extractor for CodeTrellis

Extracts Qwik context and serialization patterns:
- createContextId() — context identifier creation
- useContextProvider() — providing context to descendants
- useContext() — consuming context
- noSerialize() — marking non-serializable values

Supports:
- Qwik v0.x (createContext, useContextProvider, useContext)
- Qwik v1.x (createContextId, same API)
- Qwik v2.x (@qwik.dev/core)

Part of CodeTrellis v4.63 - Qwik Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class QwikContextInfo:
    """Information about a Qwik context."""
    name: str
    file: str = ""
    line_number: int = 0
    type_annotation: str = ""  # TypeScript type for context value
    context_name: str = ""  # The string identifier
    is_exported: bool = False
    has_provider: bool = False  # useContextProvider found
    has_consumer: bool = False  # useContext found


@dataclass
class QwikNoSerializeInfo:
    """Information about noSerialize() usage."""
    file: str = ""
    line_number: int = 0
    target_variable: str = ""


class QwikStoreExtractor:
    """
    Extracts Qwik context and serialization patterns.

    Detects:
    - createContextId<T>('identifier') context creation
    - useContextProvider(CTX, value) context provision
    - useContext(CTX) context consumption
    - noSerialize(value) non-serializable marking
    """

    # createContextId<T>('name')
    CREATE_CONTEXT_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createContextId\s*(?:<([^>]*)>)?\s*\(\s*[\'"]([^\'"]*)[\'"]',
        re.MULTILINE
    )

    # Legacy: createContext<T>('name')
    CREATE_CONTEXT_LEGACY_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createContext\s*(?:<([^>]*)>)?\s*\(\s*[\'"]([^\'"]*)[\'"]',
        re.MULTILINE
    )

    # useContextProvider(CTX, value)
    USE_CONTEXT_PROVIDER_PATTERN = re.compile(
        r'useContextProvider\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # useContext(CTX)
    USE_CONTEXT_PATTERN = re.compile(
        r'useContext\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # noSerialize(value)
    NO_SERIALIZE_PATTERN = re.compile(
        r'noSerialize\s*\(',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Qwik context and serialization patterns."""
        contexts: List[QwikContextInfo] = []
        no_serializes: List[QwikNoSerializeInfo] = []

        # Collect provider and consumer context names
        provider_names = set()
        consumer_names = set()

        for m in self.USE_CONTEXT_PROVIDER_PATTERN.finditer(content):
            provider_names.add(m.group(1))

        for m in self.USE_CONTEXT_PATTERN.finditer(content):
            consumer_names.add(m.group(1))

        # ── createContextId ───────────────────────────────────────
        for m in self.CREATE_CONTEXT_PATTERN.finditer(content):
            name = m.group(1)
            type_ann = m.group(2) or ""
            ctx_name = m.group(3)
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 30):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix

            contexts.append(QwikContextInfo(
                name=name,
                file=file_path,
                line_number=line,
                type_annotation=type_ann,
                context_name=ctx_name,
                is_exported=is_exported,
                has_provider=name in provider_names,
                has_consumer=name in consumer_names,
            ))

        # ── createContext (legacy) ────────────────────────────────
        for m in self.CREATE_CONTEXT_LEGACY_PATTERN.finditer(content):
            name = m.group(1)
            # Skip if already captured
            if any(c.name == name for c in contexts):
                continue

            type_ann = m.group(2) or ""
            ctx_name = m.group(3)
            line = content[:m.start()].count('\n') + 1

            prefix = content[max(0, m.start() - 30):m.start() + len(m.group(0))]
            is_exported = 'export' in prefix

            contexts.append(QwikContextInfo(
                name=name,
                file=file_path,
                line_number=line,
                type_annotation=type_ann,
                context_name=ctx_name,
                is_exported=is_exported,
                has_provider=name in provider_names,
                has_consumer=name in consumer_names,
            ))

        # ── noSerialize ──────────────────────────────────────────
        for m in self.NO_SERIALIZE_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1

            # Try to find target variable
            target = ""
            prev_line = content[max(0, m.start() - 100):m.start()]
            assign_match = re.search(r'(\w+)\s*(?:\.value)?\s*=\s*$', prev_line)
            if assign_match:
                target = assign_match.group(1)

            no_serializes.append(QwikNoSerializeInfo(
                file=file_path,
                line_number=line,
                target_variable=target,
            ))

        return {
            "contexts": contexts,
            "no_serializes": no_serializes,
        }
