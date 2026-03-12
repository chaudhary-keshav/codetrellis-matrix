"""
Elixir Function Extractor for CodeTrellis

Extracts function-level constructs from Elixir source code:
- Public functions (def)
- Private functions (defp)
- Macros (defmacro, defmacrop)
- Guards (defguard, defguardp)
- Callbacks (@callback implementations)
- Function clauses / pattern matching heads
- Pipeline chains (|>)
- GenServer callbacks (handle_call, handle_cast, handle_info, init)

Supports Elixir 1.0 through 1.17+.

Part of CodeTrellis - Elixir Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ElixirFunctionInfo:
    """Information about an Elixir function definition."""
    name: str
    file: str = ""
    line_number: int = 0
    arity: int = 0
    is_public: bool = True
    is_async: bool = False  # Task.async / spawn patterns
    has_guard: bool = False
    guard_clause: str = ""
    params: List[str] = field(default_factory=list)
    return_type: str = ""  # From @spec if available
    doc: str = ""
    has_spec: bool = False
    clause_count: int = 1
    module: str = ""
    is_genserver_callback: bool = False
    callback_type: str = ""  # handle_call, handle_cast, handle_info, init, terminate


@dataclass
class ElixirMacroInfo:
    """Information about an Elixir macro."""
    name: str
    file: str = ""
    line_number: int = 0
    arity: int = 0
    is_public: bool = True
    doc: str = ""


@dataclass
class ElixirGuardInfo:
    """Information about an Elixir guard definition."""
    name: str
    file: str = ""
    line_number: int = 0
    is_public: bool = True
    expression: str = ""


@dataclass
class ElixirCallbackInfo:
    """Information about an Elixir callback implementation."""
    name: str
    file: str = ""
    line_number: int = 0
    behaviour: str = ""
    arity: int = 0


class ElixirFunctionExtractor:
    """Extracts function-level constructs from Elixir source code."""

    # Function patterns
    _DEF_RE = re.compile(
        r'^\s*(def|defp)\s+(\w+)\s*(?:\(([^)]*)\))?\s*(?:when\s+(.+?))?\s*(?:do\b|,)',
        re.MULTILINE
    )

    # Macro patterns
    _MACRO_RE = re.compile(
        r'^\s*(defmacro|defmacrop)\s+(\w+)\s*(?:\(([^)]*)\))?',
        re.MULTILINE
    )

    # Guard patterns
    _GUARD_RE = re.compile(
        r'^\s*(defguard|defguardp)\s+(\w+)\s*(?:\(([^)]*)\))?\s*when\s+(.+)',
        re.MULTILINE
    )

    # @doc pattern
    _DOC_RE = re.compile(
        r'@doc\s+"""(.*?)"""',
        re.DOTALL
    )

    _DOC_FALSE_RE = re.compile(r'@doc\s+false')

    # @spec pattern
    _SPEC_RE = re.compile(
        r'@spec\s+(\w+)\(([^)]*)\)\s*::\s*(.+)',
        re.MULTILINE
    )

    # GenServer callback names
    GENSERVER_CALLBACKS = {
        'init', 'handle_call', 'handle_cast', 'handle_info',
        'handle_continue', 'terminate', 'code_change', 'format_status',
    }

    # Module name pattern
    _MODULE_RE = re.compile(r'^\s*defmodule\s+([\w.]+)', re.MULTILINE)

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract all function-level constructs."""
        functions = self._extract_functions(content, file_path)
        macros = self._extract_macros(content, file_path)
        guards = self._extract_guards(content, file_path)
        callbacks = self._extract_callbacks(content, file_path)

        return {
            "functions": functions,
            "macros": macros,
            "guards": guards,
            "callbacks": callbacks,
        }

    def _extract_functions(self, content: str, file_path: str) -> List[ElixirFunctionInfo]:
        functions = []
        # Get module name
        mod_m = self._MODULE_RE.search(content)
        module = mod_m.group(1) if mod_m else ""

        # Collect specs
        specs = {}
        for m in self._SPEC_RE.finditer(content):
            specs[m.group(1)] = m.group(3).strip()

        # Track function clauses
        clause_counts: dict = {}

        for m in self._DEF_RE.finditer(content):
            visibility = m.group(1)
            name = m.group(2)
            params_str = m.group(3) or ""
            guard_clause = m.group(4) or ""
            line = content[:m.start()].count('\n') + 1

            params = [p.strip() for p in params_str.split(',') if p.strip()] if params_str else []
            arity = len(params)
            key = f"{name}/{arity}"

            # Track clause count
            clause_counts[key] = clause_counts.get(key, 0) + 1
            if clause_counts[key] > 1:
                # Update existing function's clause_count
                for f in functions:
                    if f.name == name and f.arity == arity:
                        f.clause_count = clause_counts[key]
                continue

            is_genserver = name in self.GENSERVER_CALLBACKS
            callback_type = name if is_genserver else ""

            # Check for @doc before this function
            doc = ""
            before = content[:m.start()]
            doc_m = re.search(r'@doc\s+"""(.*?)"""\s*$', before, re.DOTALL)
            if doc_m:
                doc = doc_m.group(1).strip()[:200]

            functions.append(ElixirFunctionInfo(
                name=name,
                file=file_path,
                line_number=line,
                arity=arity,
                is_public=(visibility == "def"),
                has_guard=bool(guard_clause),
                guard_clause=guard_clause[:100],
                params=[p[:50] for p in params[:10]],
                return_type=specs.get(name, ""),
                doc=doc,
                has_spec=name in specs,
                clause_count=1,
                module=module,
                is_genserver_callback=is_genserver,
                callback_type=callback_type,
            ))
        return functions

    def _extract_macros(self, content: str, file_path: str) -> List[ElixirMacroInfo]:
        macros = []
        for m in self._MACRO_RE.finditer(content):
            visibility = m.group(1)
            name = m.group(2)
            params_str = m.group(3) or ""
            line = content[:m.start()].count('\n') + 1
            params = [p.strip() for p in params_str.split(',') if p.strip()] if params_str else []

            macros.append(ElixirMacroInfo(
                name=name,
                file=file_path,
                line_number=line,
                arity=len(params),
                is_public=(visibility == "defmacro"),
            ))
        return macros

    def _extract_guards(self, content: str, file_path: str) -> List[ElixirGuardInfo]:
        guards = []
        for m in self._GUARD_RE.finditer(content):
            visibility = m.group(1)
            name = m.group(2)
            expression = m.group(4) or ""
            line = content[:m.start()].count('\n') + 1

            guards.append(ElixirGuardInfo(
                name=name,
                file=file_path,
                line_number=line,
                is_public=(visibility == "defguard"),
                expression=expression[:200],
            ))
        return guards

    def _extract_callbacks(self, content: str, file_path: str) -> List[ElixirCallbackInfo]:
        callbacks = []
        # Find @behaviour declarations
        behaviour_re = re.compile(r'@behaviour\s+([\w.]+)', re.MULTILINE)
        behaviours = [b.group(1) for b in behaviour_re.finditer(content)]

        # Find @impl true / @impl BehaviourName
        impl_re = re.compile(
            r'@impl\s+(?:true|([\w.]+))\s*\n\s*(?:def|defp)\s+(\w+)\s*(?:\(([^)]*)\))?',
            re.MULTILINE
        )

        for m in impl_re.finditer(content):
            behaviour = m.group(1) or (behaviours[0] if behaviours else "")
            name = m.group(2)
            params_str = m.group(3) or ""
            line = content[:m.start()].count('\n') + 1
            params = [p.strip() for p in params_str.split(',') if p.strip()] if params_str else []

            callbacks.append(ElixirCallbackInfo(
                name=name,
                file=file_path,
                line_number=line,
                behaviour=behaviour,
                arity=len(params),
            ))
        return callbacks
