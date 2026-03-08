"""
tRPC Router/Procedure Extractor - Extracts router definitions, procedures, and merged routers.

Supports tRPC 9.x through 11.x:
- v9: createRouter(), .query(), .mutation(), .subscription() on router
- v10: router({ ... }), publicProcedure.query(), .mutation(), .subscription()
       t.procedure / t.router / t.middleware pattern (init from initTRPC)
- v11: same as v10 with enhanced streaming, server functions, new adapters
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TRPCProcedureInfo:
    """A single tRPC procedure (query, mutation, or subscription)."""
    name: str
    procedure_type: str  # query, mutation, subscription
    file: str = ""
    line_number: int = 0
    input_type: str = ""
    output_type: str = ""
    has_input: bool = False
    has_output: bool = False
    has_middleware: bool = False
    middleware_names: List[str] = field(default_factory=list)
    is_protected: bool = False
    router_name: str = ""
    is_async: bool = False


@dataclass
class TRPCRouterInfo:
    """A tRPC router definition."""
    name: str
    file: str = ""
    line_number: int = 0
    procedure_count: int = 0
    procedure_names: List[str] = field(default_factory=list)
    is_exported: bool = False
    is_merged: bool = False
    sub_routers: List[str] = field(default_factory=list)


@dataclass
class TRPCMergedRouterInfo:
    """A merged tRPC router (mergeRouters or router composition)."""
    name: str
    file: str = ""
    line_number: int = 0
    merged_routers: List[str] = field(default_factory=list)
    is_app_router: bool = False


class TRPCRouterExtractor:
    """Extracts tRPC router and procedure definitions from source code."""

    # v10/v11: router({ key: procedure.query() }) pattern
    ROUTER_DEF_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'(?:(?:\w+\.)?router|createTRPCRouter|t\.router)\s*\(',
        re.MULTILINE,
    )

    # v9: createRouter() pattern
    V9_ROUTER_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'createRouter\s*\(',
        re.MULTILINE,
    )

    # v10/v11: procedure definitions within router
    # Matches: procedureName: publicProcedure[.input(...).output(...).use(...)].query(...)
    # Handles multi-line chains. Uses a two-pass approach: first find procedure
    # type calls (.query/.mutation/.subscription), then scan backward for the name.
    PROCEDURE_TYPE_PATTERN = re.compile(
        r'\.(query|mutation|subscription)\s*\(',
        re.MULTILINE,
    )

    # Pattern to find procedure name by scanning backward from procedure type
    PROCEDURE_NAME_PATTERN = re.compile(
        r'(\w+)\s*:\s*(\w+)',
    )

    # v9 procedure patterns: router.query('name', { ... })
    V9_PROCEDURE_PATTERN = re.compile(
        r'\.(?:query|mutation|subscription)\s*\(\s*[\'"](\w+)[\'"]',
        re.MULTILINE,
    )

    # Procedure with .input() — capture the input validation
    INPUT_PATTERN = re.compile(
        r'\.input\s*\(\s*([^)]+?)\s*\)',
        re.MULTILINE,
    )

    # Procedure with .output()
    OUTPUT_PATTERN = re.compile(
        r'\.output\s*\(\s*([^)]+?)\s*\)',
        re.MULTILINE,
    )

    # Protected procedure (uses middleware like protectedProcedure, authedProcedure)
    PROTECTED_PATTERN = re.compile(
        r'(protected|authed|admin|auth|logged\w*)\s*Procedure',
        re.IGNORECASE,
    )

    # mergeRouters() pattern
    MERGE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*'
        r'(?:mergeRouters|t\.mergeRouters)\s*\(\s*([^)]+)',
        re.MULTILINE,
    )

    # createCallerFactory / createCaller
    CALLER_PATTERN = re.compile(
        r'(?:createCallerFactory|createCaller)\s*\(\s*(\w+)',
        re.MULTILINE,
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all tRPC router and procedure definitions.

        Returns dict with keys: routers, procedures, merged_routers
        """
        routers = []
        procedures = []
        merged_routers = []

        lines = content.split('\n')

        # ── v10/v11 Router definitions ──────────────────────────
        for match in self.ROUTER_DEF_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 20):match.start() + 10]

            # Try to extract procedures defined inside this router
            router_start = match.end()
            # Find matching closing paren by counting braces
            brace_depth = 0
            paren_depth = 1  # we start after the opening (
            router_body = ""
            for i, ch in enumerate(content[router_start:], start=router_start):
                if ch == '(':
                    paren_depth += 1
                elif ch == ')':
                    paren_depth -= 1
                    if paren_depth == 0:
                        router_body = content[router_start:i]
                        break
                elif ch == '{':
                    brace_depth += 1
                elif ch == '}':
                    brace_depth -= 1

            proc_names = []
            for proc_match in self.PROCEDURE_TYPE_PATTERN.finditer(router_body):
                proc_type = proc_match.group(1)

                # Scan backward from the .query/.mutation/.subscription to find "name: base"
                lookback = router_body[max(0, proc_match.start() - 600):proc_match.start()]
                # Find the last "word: word" pattern (the procedure name and base)
                name_matches = list(self.PROCEDURE_NAME_PATTERN.finditer(lookback))
                if not name_matches:
                    continue
                last_name_match = name_matches[-1]
                proc_name = last_name_match.group(1)
                procedure_base = last_name_match.group(2)

                # Skip structural keywords
                if proc_name in ('export', 'const', 'let', 'var', 'async', 'return', 'import', 'from', 'type'):
                    continue

                proc_line = content[:match.start()].count('\n') + router_body[:proc_match.start()].count('\n') + 1

                # Check for input/output in the chain
                chain_start = max(0, proc_match.start() - 500)
                chain_text = router_body[chain_start:proc_match.end()]
                input_m = self.INPUT_PATTERN.search(chain_text)
                output_m = self.OUTPUT_PATTERN.search(chain_text)

                is_protected = bool(self.PROTECTED_PATTERN.search(procedure_base))

                proc_info = TRPCProcedureInfo(
                    name=proc_name,
                    procedure_type=proc_type,
                    file=file_path,
                    line_number=proc_line,
                    input_type=input_m.group(1).strip()[:100] if input_m else "",
                    output_type=output_m.group(1).strip()[:100] if output_m else "",
                    has_input=input_m is not None,
                    has_output=output_m is not None,
                    has_middleware=is_protected,
                    is_protected=is_protected,
                    router_name=name,
                )
                procedures.append(proc_info)
                proc_names.append(proc_name)

            # Detect sub-routers (nested router keys)
            sub_router_pattern = re.compile(r'(\w+)\s*:\s*(\w+Router\b)', re.MULTILINE)
            sub_routers = [m.group(2) for m in sub_router_pattern.finditer(router_body)]

            router_info = TRPCRouterInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                procedure_count=len(proc_names),
                procedure_names=proc_names[:20],
                is_exported=is_exported,
                is_merged=False,
                sub_routers=sub_routers[:10],
            )
            routers.append(router_info)

        # ── v9 Router definitions ───────────────────────────────
        for match in self.V9_ROUTER_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 20):match.start() + 10]

            # Find v9-style procedures
            v9_procs = []
            for pm in self.V9_PROCEDURE_PATTERN.finditer(content):
                v9_procs.append(pm.group(1))
                procedures.append(TRPCProcedureInfo(
                    name=pm.group(1),
                    procedure_type="query",  # v9 default
                    file=file_path,
                    line_number=content[:pm.start()].count('\n') + 1,
                    router_name=name,
                ))

            # Avoid duplicate router entries
            if not any(r.name == name for r in routers):
                routers.append(TRPCRouterInfo(
                    name=name,
                    file=file_path,
                    line_number=line_num,
                    procedure_count=len(v9_procs),
                    procedure_names=v9_procs[:20],
                    is_exported=is_exported,
                ))

        # ── Merged routers ──────────────────────────────────────
        for match in self.MERGE_PATTERN.finditer(content):
            name = match.group(1)
            merged_names_raw = match.group(2)
            merged_names = [n.strip() for n in merged_names_raw.split(',') if n.strip()]
            line_num = content[:match.start()].count('\n') + 1
            is_app = name.lower() in ('approuter', 'app_router', 'rootrouter', 'root_router')

            merged_routers.append(TRPCMergedRouterInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                merged_routers=merged_names[:20],
                is_app_router=is_app,
            ))

        return {
            'routers': routers,
            'procedures': procedures,
            'merged_routers': merged_routers,
        }
