"""
CodeTrellis Generic Language Extractor — Phase 7 of v5.0 Universal Scanner
============================================================================

Provides graceful degradation for languages without dedicated parsers.
When CodeTrellis encounters .java, .rs, .rb, .php, .c, .cpp, .cs, .swift,
.kt, etc., this extractor captures:

- Function/method signatures via regex
- Class/struct/interface definitions
- Import statements
- Constant/variable declarations
- Basic metrics (LOC, function count)

NOT a substitute for proper AST parsing, but ensures every file in the
project contributes to the context instead of being silently ignored.

Part of CodeTrellis v5.0 — Universal Scanner
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from codetrellis.file_classifier import GitignoreFilter


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class GenericFunction:
    """A function/method extracted from any language."""
    name: str
    signature: str           # Full signature line
    file_path: str = ""
    line_number: int = 0
    is_public: bool = True
    return_type: Optional[str] = None
    params: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "signature": self.signature[:200],
            "file_path": self.file_path,
            "line_number": self.line_number,
            "is_public": self.is_public,
            "return_type": self.return_type,
        }


@dataclass
class GenericType:
    """A class/struct/interface/enum extracted from any language."""
    name: str
    kind: str                # "class", "struct", "interface", "enum", "trait", "protocol"
    file_path: str = ""
    line_number: int = 0
    is_public: bool = True
    extends: Optional[str] = None
    implements: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "kind": self.kind,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "is_public": self.is_public,
        }
        if self.extends:
            result["extends"] = self.extends
        if self.implements:
            result["implements"] = self.implements
        return result


@dataclass
class GenericImport:
    """An import/include/use statement."""
    module: str
    file_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"module": self.module, "file_path": self.file_path}


@dataclass
class GenericFileResult:
    """Result for a single file."""
    file_path: str
    language: str
    loc: int = 0
    functions: List[GenericFunction] = field(default_factory=list)
    types: List[GenericType] = field(default_factory=list)
    imports: List[GenericImport] = field(default_factory=list)


@dataclass
class GenericLanguageResult:
    """Aggregate result for all generically-parsed files."""
    files: List[GenericFileResult] = field(default_factory=list)
    language_stats: Dict[str, int] = field(default_factory=dict)  # language → file count

    def to_dict(self) -> Dict[str, Any]:
        all_functions = []
        all_types = []
        for f in self.files:
            all_functions.extend(fn.to_dict() for fn in f.functions)
            all_types.extend(t.to_dict() for t in f.types)

        return {
            "language_stats": self.language_stats,
            "total_files": len(self.files),
            "total_functions": len(all_functions),
            "total_types": len(all_types),
            "functions": all_functions[:200],
            "types": all_types[:100],
        }

    def to_codetrellis_format(self) -> str:
        """Convert to compact CodeTrellis format."""
        lines = []
        lines.append(f"# Generic Languages ({len(self.files)} files)")

        # Stats
        for lang, count in sorted(self.language_stats.items(), key=lambda x: -x[1]):
            lines.append(f"  {lang}: {count} files")

        # Types grouped by language
        types_by_lang: Dict[str, List[GenericType]] = {}
        funcs_by_lang: Dict[str, List[GenericFunction]] = {}

        for f in self.files:
            for t in f.types:
                lang = f.language
                if lang not in types_by_lang:
                    types_by_lang[lang] = []
                types_by_lang[lang].append(t)
            for fn in f.functions:
                lang = f.language
                if lang not in funcs_by_lang:
                    funcs_by_lang[lang] = []
                funcs_by_lang[lang].append(fn)

        for lang, types in types_by_lang.items():
            lines.append(f"## {lang} Types ({len(types)})")
            for t in types[:30]:
                ext = f" extends {t.extends}" if t.extends else ""
                impl = f" implements {','.join(t.implements)}" if t.implements else ""
                pub = "" if t.is_public else " (private)"
                lines.append(f"  {t.kind} {t.name}{ext}{impl}{pub}")

        for lang, funcs in funcs_by_lang.items():
            public_funcs = [fn for fn in funcs if fn.is_public]
            if public_funcs:
                lines.append(f"## {lang} Functions ({len(public_funcs)} public)")
                for fn in public_funcs[:50]:
                    lines.append(f"  {fn.signature[:120]}")

        return '\n'.join(lines)


# =============================================================================
# Language Definitions
# =============================================================================

# Extension → language name
EXTENSION_LANGUAGE: Dict[str, str] = {
    # '.java' excluded — handled by dedicated Java parser (java_parser_enhanced.py)
    # '.kt'/'.kts' excluded — handled by dedicated Kotlin parser (kotlin_parser_enhanced.py)
    '.rs': 'Rust',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.c': 'C',
    '.h': 'C',
    '.cpp': 'C++',
    '.hpp': 'C++',
    '.cc': 'C++',
    '.cxx': 'C++',
    '.cs': 'C#',
    '.swift': 'Swift',
    '.scala': 'Scala',
    '.ex': 'Elixir',
    '.exs': 'Elixir',
    '.erl': 'Erlang',
    '.hrl': 'Erlang',
    '.lua': 'Lua',
    '.r': 'R',
    '.R': 'R',
    '.dart': 'Dart',
    '.zig': 'Zig',
    '.nim': 'Nim',
    '.v': 'V',
    '.pl': 'Perl',
    '.pm': 'Perl',
    '.m': 'Objective-C',
    '.mm': 'Objective-C++',
    '.groovy': 'Groovy',
    '.clj': 'Clojure',
    '.cljs': 'ClojureScript',
    '.fs': 'F#',
    '.fsx': 'F#',
    '.hs': 'Haskell',
    '.ml': 'OCaml',
    '.mli': 'OCaml',
}

# Languages already handled by dedicated parsers — skip these
HANDLED_LANGUAGES = {
    '.go', '.py', '.ts', '.tsx', '.js', '.jsx', '.mjs',
    '.proto',
    '.java', '.kt', '.kts',  # v4.12: Java + Kotlin
    '.cs',                    # v4.13: C#
    '.rs',                    # v4.14: Rust
    '.sql',                   # v4.15: SQL
}


# =============================================================================
# Per-Language Extraction Patterns
# =============================================================================

def _build_patterns() -> Dict[str, Dict[str, Any]]:
    """Build regex patterns per language family."""
    return {
        'c_family': {
            # C, C++, C#, Java, Kotlin, Dart, Swift, Rust
            'function': re.compile(
                r'^\s*'
                r'(?:(?:public|private|protected|static|async|override|virtual|abstract|inline|extern)\s+)*'
                r'(?:(?:fun|func|fn|def|void|int|bool|string|float|double|var|val|let)\s+)?'
                r'(\w+)\s*'
                r'\(([^)]*)\)'
                r'(?:\s*(?:->|:)\s*(\S+))?'
                r'\s*\{?',
                re.M
            ),
            'type': re.compile(
                r'^\s*'
                r'(?:(?:public|private|protected|internal|abstract|sealed|final|open|data)\s+)*'
                r'(class|struct|interface|enum|trait|protocol|object)\s+'
                r'(\w+)'
                r'(?:\s*(?:<[^>]*>))?'
                r'(?:\s*(?:extends|:)\s*(\w+))?'
                r'(?:\s*(?:implements|,)\s*([\w,\s]+))?',
                re.M
            ),
            'import': re.compile(
                r'^\s*(?:import|using|include|require)\s+(.+?)(?:\s*;|\s*$)',
                re.M
            ),
            'public_prefix': re.compile(r'^\s*(?:public|export)', re.I),
            'private_prefix': re.compile(r'^\s*(?:private|protected|internal)'),
        },
        'ruby': {
            'function': re.compile(
                r'^\s*def\s+(?:self\.)?(\w+[!?=]?)\s*(?:\(([^)]*)\))?',
                re.M
            ),
            'type': re.compile(
                r'^\s*(class|module)\s+(\w+(?:::\w+)*)'
                r'(?:\s*<\s*(\w+(?:::\w+)*))?',
                re.M
            ),
            'import': re.compile(
                r'^\s*(?:require|require_relative|include|extend)\s+["\']?(\S+)["\']?',
                re.M
            ),
            'public_prefix': re.compile(r''),  # Ruby: public by default
            'private_prefix': re.compile(r'^\s*private'),
        },
        'php': {
            'function': re.compile(
                r'^\s*(?:(?:public|private|protected|static)\s+)*'
                r'function\s+(\w+)\s*\(([^)]*)\)'
                r'(?:\s*:\s*(\S+))?',
                re.M
            ),
            'type': re.compile(
                r'^\s*(?:(?:abstract|final)\s+)?'
                r'(class|interface|trait|enum)\s+'
                r'(\w+)'
                r'(?:\s+extends\s+(\w+))?'
                r'(?:\s+implements\s+([\w,\s]+))?',
                re.M
            ),
            'import': re.compile(
                r'^\s*(?:use|require|include|require_once|include_once)\s+(.+?)(?:\s*;|\s*$)',
                re.M
            ),
            'public_prefix': re.compile(r'^\s*public'),
            'private_prefix': re.compile(r'^\s*(?:private|protected)'),
        },
        'elixir': {
            'function': re.compile(
                r'^\s*(?:def|defp)\s+(\w+[!?]?)\s*(?:\(([^)]*)\))?',
                re.M
            ),
            'type': re.compile(
                r'^\s*defmodule\s+(\w+(?:\.\w+)*)',
                re.M
            ),
            'import': re.compile(
                r'^\s*(?:import|alias|use|require)\s+(\S+)',
                re.M
            ),
            'public_prefix': re.compile(r'^\s*def\s'),
            'private_prefix': re.compile(r'^\s*defp\s'),
        },
        'rust': {
            'function': re.compile(
                r'^\s*(?:pub(?:\(crate\))?\s+)?'
                r'(?:async\s+)?'
                r'fn\s+(\w+)\s*'
                r'(?:<[^>]*>)?\s*'
                r'\(([^)]*)\)'
                r'(?:\s*->\s*(\S+))?',
                re.M
            ),
            'type': re.compile(
                r'^\s*(?:pub(?:\(crate\))?\s+)?'
                r'(struct|enum|trait|impl)\s+'
                r'(\w+)'
                r'(?:\s*<[^>]*>)?',
                re.M
            ),
            'import': re.compile(
                r'^\s*use\s+(.+?)(?:\s*;|\s*$)',
                re.M
            ),
            'public_prefix': re.compile(r'^\s*pub\b'),
            'private_prefix': re.compile(r'^(?!\s*pub)'),
        },
    }


LANG_PATTERN_MAP: Dict[str, str] = {
    'Java': 'c_family',
    'Kotlin': 'c_family',
    'C': 'c_family',
    'C++': 'c_family',
    'C#': 'c_family',
    'Swift': 'c_family',
    'Scala': 'c_family',
    'Dart': 'c_family',
    'Zig': 'c_family',
    'Groovy': 'c_family',
    'V': 'c_family',
    'Objective-C': 'c_family',
    'Objective-C++': 'c_family',
    'Ruby': 'ruby',
    'PHP': 'php',
    'Elixir': 'elixir',
    'Erlang': 'elixir',
    'Rust': 'rust',
    'Nim': 'c_family',
    'Haskell': 'c_family',
    'OCaml': 'c_family',
    'F#': 'c_family',
    'Clojure': 'c_family',
    'ClojureScript': 'c_family',
    'R': 'c_family',
    'Lua': 'c_family',
    'Perl': 'c_family',
}

# Build patterns once
PATTERNS = _build_patterns()


# =============================================================================
# Generic Language Extractor
# =============================================================================

class GenericLanguageExtractor:
    """
    Regex-based extractor for languages without dedicated AST parsers.

    Provides partial but useful extraction for any file type,
    ensuring no source file is silently ignored.
    """

    IGNORE_DIRS = {
        'node_modules', '.git', 'dist', 'build', '__pycache__',
        'vendor', '.next', 'coverage', 'venv', '.venv',
        'target', 'bin', 'obj',
    }

    # Skip well-known non-meaningful function names
    SKIP_FUNCTIONS = {
        'if', 'for', 'while', 'switch', 'case', 'return',
        'else', 'elif', 'do', 'try', 'catch', 'throw',
        'new', 'delete', 'sizeof', 'typeof', 'instanceof',
        'main',  # Usually already captured elsewhere
    }

    def can_extract(self, file_path: Path) -> bool:
        """Check if this file should be generically parsed."""
        ext = file_path.suffix.lower()
        return ext in EXTENSION_LANGUAGE and ext not in HANDLED_LANGUAGES

    def extract_file(self, file_path: Path) -> Optional[GenericFileResult]:
        """
        Extract functions, types, and imports from a single file.

        Args:
            file_path: Path to the source file

        Returns:
            GenericFileResult or None
        """
        ext = file_path.suffix.lower()
        language = EXTENSION_LANGUAGE.get(ext)
        if not language:
            return None

        try:
            content = file_path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            return None

        result = GenericFileResult(
            file_path=str(file_path),
            language=language,
            loc=len(content.splitlines()),
        )

        pattern_family = LANG_PATTERN_MAP.get(language, 'c_family')
        patterns = PATTERNS.get(pattern_family)
        if not patterns:
            return result

        self._extract_functions(content, patterns, file_path, result)
        self._extract_types(content, patterns, file_path, result)
        self._extract_imports(content, patterns, file_path, result)

        return result

    def extract_from_directory(self, root_dir: Path,
                               gitignore_filter: Optional[GitignoreFilter] = None,
                               ) -> Optional[GenericLanguageResult]:
        """
        Scan directory for files in unsupported languages and extract basics.

        Args:
            root_dir: Root directory
            gitignore_filter: Optional GitignoreFilter to respect .gitignore rules

        Returns:
            GenericLanguageResult or None
        """
        result = GenericLanguageResult()

        gi = gitignore_filter

        for root, dirs, files in _walk_compat(root_dir):
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS
                       and not (gi and not gi.is_empty and gi.should_ignore(
                           os.path.relpath(os.path.join(str(root), d), str(root_dir)),
                           is_dir=True))]

            for f in files:
                fp = root / f
                if not self.can_extract(fp):
                    continue

                file_result = self.extract_file(fp)
                if file_result:
                    result.files.append(file_result)
                    lang = file_result.language
                    result.language_stats[lang] = result.language_stats.get(lang, 0) + 1

        return result if result.files else None

    def _extract_functions(
        self, content: str, patterns: Dict, file_path: Path, result: GenericFileResult
    ) -> None:
        """Extract function signatures."""
        func_pattern = patterns.get('function')
        if not func_pattern:
            return

        public_re = patterns.get('public_prefix')
        private_re = patterns.get('private_prefix')

        for i, line in enumerate(content.splitlines(), 1):
            m = func_pattern.match(line)
            if not m:
                continue

            name = m.group(1)
            if name in self.SKIP_FUNCTIONS:
                continue

            is_public = True
            if private_re and private_re.match(line):
                is_public = False

            return_type = m.group(3) if m.lastindex and m.lastindex >= 3 else None

            result.functions.append(GenericFunction(
                name=name,
                signature=line.strip()[:200],
                file_path=str(file_path),
                line_number=i,
                is_public=is_public,
                return_type=return_type,
            ))

    def _extract_types(
        self, content: str, patterns: Dict, file_path: Path, result: GenericFileResult
    ) -> None:
        """Extract class/struct/interface definitions."""
        type_pattern = patterns.get('type')
        if not type_pattern:
            return

        for m in type_pattern.finditer(content):
            groups = m.groups()

            # Different patterns have different group layouts
            if len(groups) >= 2:
                kind = groups[0] if groups[0] in (
                    'class', 'struct', 'interface', 'enum', 'trait',
                    'protocol', 'module', 'object', 'impl',
                ) else 'class'
                name = groups[1] if len(groups) > 1 else groups[0]
            else:
                kind = 'class'
                name = groups[0]

            extends = groups[2] if len(groups) > 2 and groups[2] else None

            implements = []
            if len(groups) > 3 and groups[3]:
                implements = [i.strip() for i in groups[3].split(',') if i.strip()]

            # Check line for public/private
            line_start = content.rfind('\n', 0, m.start()) + 1
            line = content[line_start:m.end()]

            is_public = True
            private_re = patterns.get('private_prefix')
            if private_re and private_re.match(line):
                is_public = False

            line_number = content[:m.start()].count('\n') + 1

            result.types.append(GenericType(
                name=name,
                kind=kind,
                file_path=str(file_path),
                line_number=line_number,
                is_public=is_public,
                extends=extends,
                implements=implements,
            ))

    def _extract_imports(
        self, content: str, patterns: Dict, file_path: Path, result: GenericFileResult
    ) -> None:
        """Extract import statements."""
        import_pattern = patterns.get('import')
        if not import_pattern:
            return

        seen: Set[str] = set()
        for m in import_pattern.finditer(content):
            module = m.group(1).strip().strip('"').strip("'").strip(';')
            if module and module not in seen:
                seen.add(module)
                result.imports.append(GenericImport(
                    module=module,
                    file_path=str(file_path),
                ))


# =============================================================================
# Compatibility helper
# =============================================================================

def _walk_compat(root: Path):
    """os.walk wrapper that yields (Path, dirs, files)."""
    import os
    for dirpath, dirs, files in os.walk(root):
        yield Path(dirpath), dirs, files
