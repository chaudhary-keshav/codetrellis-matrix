"""
tRPC Context Extractor - Extracts context creation, input/output schemas.

Supports:
- createContext / createTRPCContext functions
- Input schemas (zod, yup, superstruct, io-ts, typebox)
- Output schemas
- Context typing (Context, inferAsyncReturnType)
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TRPCContextInfo:
    """A tRPC context creation function."""
    name: str
    file: str = ""
    line_number: int = 0
    is_async: bool = False
    uses_session: bool = False
    uses_db: bool = False
    uses_req: bool = False
    uses_res: bool = False
    context_fields: List[str] = field(default_factory=list)


@dataclass
class TRPCInputInfo:
    """An input validation schema used in a tRPC procedure."""
    procedure_name: str
    schema_type: str = ""  # zod, yup, superstruct, io-ts, typebox, custom
    schema_text: str = ""
    file: str = ""
    line_number: int = 0
    has_required: bool = False


@dataclass
class TRPCOutputInfo:
    """An output validation schema used in a tRPC procedure."""
    procedure_name: str
    schema_type: str = ""
    schema_text: str = ""
    file: str = ""
    line_number: int = 0


class TRPCContextExtractor:
    """Extracts tRPC context and schema definitions."""

    # createContext / createTRPCContext
    CONTEXT_CREATE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var|async\s+function|function)\s+'
        r'(create\w*Context|createTRPCContext|createInnerTRPCContext)\s*'
        r'(?:=\s*(?:async\s+)?\(|\()',
        re.MULTILINE,
    )

    # Context type inference: type Context = inferAsyncReturnType<typeof createContext>
    CONTEXT_TYPE_PATTERN = re.compile(
        r'(?:type|interface)\s+(\w*Context\w*)\s*=\s*'
        r'(?:inferAsyncReturnType|Awaited)\s*<',
        re.MULTILINE,
    )

    # Zod schema patterns
    ZOD_PATTERN = re.compile(
        r'z\.\w+\s*\(',
    )

    # Yup schema
    YUP_PATTERN = re.compile(
        r'(?:yup|Yup)\.\w+\s*\(',
    )

    # TypeBox schema
    TYPEBOX_PATTERN = re.compile(
        r'Type\.\w+\s*\(',
    )

    # Superstruct
    SUPERSTRUCT_PATTERN = re.compile(
        r'(?:object|string|number|boolean|array|optional)\s*\(',
    )

    # Input schema usage: .input(z.object({...}))
    INPUT_USAGE_PATTERN = re.compile(
        r'(\w+)\s*:\s*\w+\s*\.input\s*\(\s*(.+?)\s*\)\s*\.',
        re.MULTILINE | re.DOTALL,
    )

    # Output schema usage: .output(z.object({...}))
    OUTPUT_USAGE_PATTERN = re.compile(
        r'(\w+)\s*:\s*\w+\s*\.output\s*\(\s*(.+?)\s*\)\s*\.',
        re.MULTILINE | re.DOTALL,
    )

    def _detect_schema_type(self, schema_text: str) -> str:
        """Detect which validation library is used."""
        if self.ZOD_PATTERN.search(schema_text):
            return 'zod'
        if self.YUP_PATTERN.search(schema_text):
            return 'yup'
        if self.TYPEBOX_PATTERN.search(schema_text):
            return 'typebox'
        if self.SUPERSTRUCT_PATTERN.search(schema_text):
            return 'superstruct'
        return 'custom'

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract tRPC context and schema definitions.

        Returns dict with keys: contexts, inputs, outputs
        """
        contexts = []
        inputs = []
        outputs = []

        # ── Context creation ────────────────────────────────────
        for match in self.CONTEXT_CREATE_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            is_async = 'async' in content[max(0, match.start() - 20):match.end()]

            # Scan body for common patterns
            body_start = match.end()
            body_preview = content[body_start:body_start + 1000]

            ctx_fields = []
            if 'session' in body_preview:
                ctx_fields.append('session')
            if 'db' in body_preview or 'prisma' in body_preview or 'drizzle' in body_preview:
                ctx_fields.append('db')
            if 'user' in body_preview:
                ctx_fields.append('user')
            if 'req' in body_preview:
                ctx_fields.append('req')
            if 'res' in body_preview:
                ctx_fields.append('res')

            contexts.append(TRPCContextInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                is_async=is_async,
                uses_session='session' in ctx_fields,
                uses_db='db' in ctx_fields,
                uses_req='req' in ctx_fields,
                uses_res='res' in ctx_fields,
                context_fields=ctx_fields,
            ))

        # ── Input schemas ───────────────────────────────────────
        # Simple approach: find .input() calls with schema
        input_pattern = re.compile(
            r'(\w+)\s*:\s*\w+(?:Procedure)?\s*\.input\s*\(',
            re.MULTILINE,
        )
        for match in input_pattern.finditer(content):
            proc_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Extract schema text (up to the closing .query/.mutation)
            schema_start = match.end()
            schema_text = content[schema_start:schema_start + 200]

            schema_type = self._detect_schema_type(schema_text)

            inputs.append(TRPCInputInfo(
                procedure_name=proc_name,
                schema_type=schema_type,
                schema_text=schema_text[:100].strip(),
                file=file_path,
                line_number=line_num,
                has_required='required' in schema_text.lower() or '.min(' in schema_text,
            ))

        # ── Output schemas ──────────────────────────────────────
        output_pattern = re.compile(
            r'(\w+)\s*:\s*\w+(?:Procedure)?\s*(?:\.input\s*\([^)]*\)\s*)?\.output\s*\(',
            re.MULTILINE,
        )
        for match in output_pattern.finditer(content):
            proc_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            schema_start = match.end()
            schema_text = content[schema_start:schema_start + 200]
            schema_type = self._detect_schema_type(schema_text)

            outputs.append(TRPCOutputInfo(
                procedure_name=proc_name,
                schema_type=schema_type,
                schema_text=schema_text[:100].strip(),
                file=file_path,
                line_number=line_num,
            ))

        return {
            'contexts': contexts,
            'inputs': inputs,
            'outputs': outputs,
        }
