"""
Next.js Server Action Extractor for CodeTrellis

Extracts server action patterns from Next.js applications:
- 'use server' directive at file top (whole-file server actions)
- 'use server' inside async function bodies (inline server actions)
- Form actions (action={serverAction})
- useFormState / useFormStatus / useActionState usage
- revalidatePath / revalidateTag calls
- redirect() after mutation
- Server action in separate files (actions.ts)
- Mutation patterns (create, update, delete)

Supports:
- Next.js 13.4+ (Server Actions alpha)
- Next.js 14.x (Server Actions stable)
- Next.js 15.x (improved server action patterns, async request APIs)

Part of CodeTrellis v4.33 - Next.js Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class NextServerActionInfo:
    """Information about a Next.js server action."""
    name: str
    file: str = ""
    line_number: int = 0
    is_file_level: bool = False  # 'use server' at file top
    is_inline: bool = False  # 'use server' inside function
    is_exported: bool = False
    is_async: bool = True  # Server actions are always async
    params: List[str] = field(default_factory=list)
    has_revalidate_path: bool = False
    has_revalidate_tag: bool = False
    has_redirect: bool = False
    mutation_type: str = ""  # create, update, delete, read
    uses_form_data: bool = False  # FormData parameter
    uses_prev_state: bool = False  # prevState parameter (useFormState)
    orm_calls: List[str] = field(default_factory=list)  # prisma, drizzle, etc.
    error_handling: str = ""  # try-catch, throw, return error


@dataclass
class NextFormActionInfo:
    """Information about a form using a server action."""
    file: str = ""
    line_number: int = 0
    action_name: str = ""
    uses_form_state: bool = False  # useFormState
    uses_form_status: bool = False  # useFormStatus
    uses_action_state: bool = False  # useActionState (React 19)
    uses_optimistic: bool = False  # useOptimistic
    form_fields: List[str] = field(default_factory=list)


class NextServerActionExtractor:
    """
    Extracts server action patterns from Next.js source code.

    Detects:
    - File-level 'use server' directives
    - Inline 'use server' in async functions
    - Server action exports
    - Form action patterns
    - Revalidation calls
    - Mutation patterns
    """

    # File-level 'use server'
    FILE_USE_SERVER = re.compile(
        r'''^['"]use server['"]''',
        re.MULTILINE
    )

    # Inline 'use server'
    INLINE_USE_SERVER = re.compile(
        r"(?:async\s+function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*async)\s*"
        r"(?:\([^)]*\)\s*(?::\s*[^{]+)?\s*)?{\s*"
        r"['\"]use server['\"]",
        re.MULTILINE
    )

    # Exported async function (in 'use server' file)
    EXPORTED_ACTION = re.compile(
        r'^[ \t]*export\s+(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)',
        re.MULTILINE
    )

    # Exported arrow function (in 'use server' file)
    EXPORTED_ACTION_ARROW = re.compile(
        r'^[ \t]*export\s+(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(([^)]*)\)',
        re.MULTILINE
    )

    # revalidatePath
    REVALIDATE_PATH = re.compile(
        r"revalidatePath\s*\(",
        re.MULTILINE
    )

    # revalidateTag
    REVALIDATE_TAG = re.compile(
        r"revalidateTag\s*\(",
        re.MULTILINE
    )

    # redirect
    REDIRECT_CALL = re.compile(
        r"redirect\s*\(",
        re.MULTILINE
    )

    # FormData parameter
    FORM_DATA_PARAM = re.compile(
        r"formData\s*:\s*FormData|FormData|formData\s*\.\s*get",
        re.MULTILINE
    )

    # Mutation type inference
    CREATE_PATTERN = re.compile(
        r'\.create\(|INSERT\s+INTO|\.insert\(|\.add\(|new\s+\w+\(',
        re.MULTILINE | re.IGNORECASE
    )
    UPDATE_PATTERN = re.compile(
        r'\.update\(|UPDATE\s+|\.save\(|\.set\(|\.patch\(',
        re.MULTILINE | re.IGNORECASE
    )
    DELETE_PATTERN = re.compile(
        r'\.delete\(|DELETE\s+FROM|\.remove\(|\.destroy\(',
        re.MULTILINE | re.IGNORECASE
    )

    # ORM detection
    ORM_PATTERNS = {
        'prisma': re.compile(r'prisma\.\w+\.\w+', re.MULTILINE),
        'drizzle': re.compile(r'db\.\w+\(|drizzle\.\w+', re.MULTILINE),
        'typeorm': re.compile(r'getRepository|EntityManager|\.createQueryBuilder', re.MULTILINE),
        'mongoose': re.compile(r'Model\.\w+|\.findById|\.findOne', re.MULTILINE),
        'supabase': re.compile(r'supabase\.\w+\.\w+|\.from\([\'"]', re.MULTILINE),
    }

    # Error handling
    TRY_CATCH = re.compile(r'try\s*\{', re.MULTILINE)
    THROW_ERROR = re.compile(r'throw\s+new\s+\w*Error', re.MULTILINE)

    # Form hooks
    USE_FORM_STATE = re.compile(
        r'useFormState\s*\(|useFormState\b',
        re.MULTILINE
    )
    USE_FORM_STATUS = re.compile(
        r'useFormStatus\s*\(|useFormStatus\b',
        re.MULTILINE
    )
    USE_ACTION_STATE = re.compile(
        r'useActionState\s*\(|useActionState\b',
        re.MULTILINE
    )
    USE_OPTIMISTIC = re.compile(
        r'useOptimistic\s*\(|useOptimistic\b',
        re.MULTILINE
    )

    # Form action JSX
    FORM_ACTION = re.compile(
        r'<form[^>]*action\s*=\s*\{([^}]+)\}',
        re.MULTILINE | re.DOTALL
    )

    # prevState parameter
    PREV_STATE = re.compile(
        r'prevState|previousState|currentState|state\s*,\s*formData',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract server action patterns from Next.js source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'server_actions', 'form_actions'
        """
        server_actions = []
        form_actions = []

        is_file_level = bool(self.FILE_USE_SERVER.search(content))

        # ── File-level server actions ────────────────────────────
        if is_file_level:
            # All exported functions are server actions
            for m in self.EXPORTED_ACTION.finditer(content):
                name = m.group(1)
                params_str = m.group(2).strip()
                line = content[:m.start()].count('\n') + 1
                params = [p.strip().split(':')[0].strip() for p in params_str.split(',') if p.strip()] if params_str else []

                action = self._build_action_info(
                    name=name, file=file_path, line=line,
                    is_file_level=True, is_exported=True,
                    params=params, content=content,
                    start=m.start(), end=min(m.start() + 2000, len(content))
                )
                server_actions.append(action)

            for m in self.EXPORTED_ACTION_ARROW.finditer(content):
                name = m.group(1)
                params_str = m.group(2).strip()
                line = content[:m.start()].count('\n') + 1
                params = [p.strip().split(':')[0].strip() for p in params_str.split(',') if p.strip()] if params_str else []

                action = self._build_action_info(
                    name=name, file=file_path, line=line,
                    is_file_level=True, is_exported=True,
                    params=params, content=content,
                    start=m.start(), end=min(m.start() + 2000, len(content))
                )
                server_actions.append(action)

        # ── Inline server actions ────────────────────────────────
        for m in self.INLINE_USE_SERVER.finditer(content):
            name = m.group(1) or m.group(2) or "anonymous"
            line = content[:m.start()].count('\n') + 1

            action = NextServerActionInfo(
                name=name,
                file=file_path,
                line_number=line,
                is_inline=True,
                is_exported=False,
            )
            server_actions.append(action)

        # ── Form actions ─────────────────────────────────────────
        for m in self.FORM_ACTION.finditer(content):
            action_name = m.group(1).strip()
            line = content[:m.start()].count('\n') + 1

            form = NextFormActionInfo(
                file=file_path,
                line_number=line,
                action_name=action_name,
                uses_form_state=bool(self.USE_FORM_STATE.search(content)),
                uses_form_status=bool(self.USE_FORM_STATUS.search(content)),
                uses_action_state=bool(self.USE_ACTION_STATE.search(content)),
                uses_optimistic=bool(self.USE_OPTIMISTIC.search(content)),
            )
            form_actions.append(form)

        return {
            "server_actions": server_actions,
            "form_actions": form_actions,
        }

    def _build_action_info(self, name: str, file: str, line: int,
                            is_file_level: bool, is_exported: bool,
                            params: List[str], content: str,
                            start: int, end: int) -> NextServerActionInfo:
        """Build a NextServerActionInfo from extracted data."""
        body = content[start:end]

        # Detect mutation type
        mutation_type = ""
        if self.CREATE_PATTERN.search(body):
            mutation_type = "create"
        elif self.UPDATE_PATTERN.search(body):
            mutation_type = "update"
        elif self.DELETE_PATTERN.search(body):
            mutation_type = "delete"

        # Detect ORM calls
        orm_calls = []
        for orm_name, pattern in self.ORM_PATTERNS.items():
            if pattern.search(body):
                orm_calls.append(orm_name)

        # Error handling
        error_handling = ""
        if self.TRY_CATCH.search(body):
            error_handling = "try-catch"
        elif self.THROW_ERROR.search(body):
            error_handling = "throw"

        return NextServerActionInfo(
            name=name,
            file=file,
            line_number=line,
            is_file_level=is_file_level,
            is_exported=is_exported,
            params=params,
            has_revalidate_path=bool(self.REVALIDATE_PATH.search(body)),
            has_revalidate_tag=bool(self.REVALIDATE_TAG.search(body)),
            has_redirect=bool(self.REDIRECT_CALL.search(body)),
            mutation_type=mutation_type,
            uses_form_data=bool(self.FORM_DATA_PARAM.search(body)),
            uses_prev_state=bool(self.PREV_STATE.search(body)),
            orm_calls=orm_calls,
            error_handling=error_handling,
        )
