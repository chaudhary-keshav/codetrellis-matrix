"""
CodeTrellis TODO/FIXME Extractor
=========================

Extracts TODO, FIXME, HACK, NOTE, and XXX comments from source files.

Features:
- TODO comments with optional author/date
- FIXME comments (potential bugs)
- HACK comments (technical debt)
- NOTE comments (important notes)
- XXX comments (needs attention)
- Priority markers (TODO(HIGH), TODO(P0))

Output format:
    [TODOS]
    file.ts
      TODO:line 42|implement caching
      FIXME:line 58|memory leak in subscription
      HACK:line 102|temporary workaround for API bug
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
from enum import Enum


class TodoType(Enum):
    """Type of todo comment"""
    TODO = "TODO"
    FIXME = "FIXME"
    HACK = "HACK"
    NOTE = "NOTE"
    XXX = "XXX"
    BUG = "BUG"
    OPTIMIZE = "OPTIMIZE"
    REVIEW = "REVIEW"


class Priority(Enum):
    """Priority level for todos"""
    P0 = "P0"  # Critical
    P1 = "P1"  # High
    P2 = "P2"  # Medium
    P3 = "P3"  # Low
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


@dataclass
class TodoComment:
    """Information about a single TODO/FIXME comment"""
    todo_type: TodoType
    line_number: int
    message: str
    author: Optional[str] = None
    priority: Priority = Priority.NONE
    date: Optional[str] = None
    related_code: Optional[str] = None  # Function/class context

    def to_codetrellis_format(self) -> str:
        """Convert to CodeTrellis format string"""
        result = f"{self.todo_type.value}:line {self.line_number}"

        if self.priority != Priority.NONE:
            result += f"|{self.priority.value}"

        if self.author:
            result += f"|@{self.author}"

        result += f"|{self.message}"

        return result


@dataclass
class TodoFileInfo:
    """All TODO comments for a single file"""
    file_path: str
    todos: List[TodoComment] = field(default_factory=list)

    def has_todos(self) -> bool:
        return len(self.todos) > 0

    def get_by_type(self, todo_type: TodoType) -> List[TodoComment]:
        """Get todos filtered by type"""
        return [t for t in self.todos if t.todo_type == todo_type]

    def get_high_priority(self) -> List[TodoComment]:
        """Get high priority todos (P0, P1, HIGH)"""
        high = {Priority.P0, Priority.P1, Priority.HIGH}
        return [t for t in self.todos if t.priority in high]

    def to_codetrellis_format(self) -> str:
        lines = [self.file_path]

        # Sort by line number
        sorted_todos = sorted(self.todos, key=lambda t: t.line_number)

        for todo in sorted_todos:
            lines.append(f"  {todo.to_codetrellis_format()}")

        return "\n".join(lines)


@dataclass
class TodoSummary:
    """Summary of all TODOs in a project"""
    total_count: int = 0
    by_type: dict = field(default_factory=dict)
    by_priority: dict = field(default_factory=dict)
    files_with_todos: int = 0

    def to_codetrellis_format(self) -> str:
        lines = [f"Total: {self.total_count} todos in {self.files_with_todos} files"]

        if self.by_type:
            type_str = ", ".join(f"{k}:{v}" for k, v in self.by_type.items())
            lines.append(f"By type: {type_str}")

        if self.by_priority:
            prio_str = ", ".join(f"{k}:{v}" for k, v in self.by_priority.items() if v > 0)
            if prio_str:
                lines.append(f"By priority: {prio_str}")

        return "\n".join(lines)


class TodoExtractor:
    """
    Extracts TODO/FIXME/HACK/NOTE comments from source files.

    Usage:
        extractor = TodoExtractor()
        file_info = extractor.extract(content, file_path)
        print(file_info.to_codetrellis_format())
    """

    # Main pattern for TODO-like comments
    # Matches: // TODO: message, /* TODO: message */, # TODO: message
    TODO_PATTERN = re.compile(
        r'(?://|/\*|#)\s*'  # Comment start
        r'(?P<type>TODO|FIXME|HACK|NOTE|XXX|BUG|OPTIMIZE|REVIEW)'  # Todo type
        r'(?:\s*\((?P<meta>[^)]+)\))?'  # Optional metadata (author, priority, date)
        r'\s*:?\s*'  # Optional colon
        r'(?P<message>[^\n\*/]+)',  # Message content
        re.IGNORECASE | re.MULTILINE
    )

    # Pattern for extracting author from metadata
    AUTHOR_PATTERN = re.compile(r'@?(?P<author>\w+)', re.IGNORECASE)

    # Pattern for extracting priority from metadata
    PRIORITY_PATTERN = re.compile(
        r'(?P<priority>P[0-3]|HIGH|MEDIUM|LOW)',
        re.IGNORECASE
    )

    # Pattern for extracting date from metadata
    DATE_PATTERN = re.compile(
        r'(?P<date>\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4})',
        re.IGNORECASE
    )

    # Pattern for finding function/class context
    CONTEXT_PATTERN = re.compile(
        r'(?:(?:export\s+)?(?:async\s+)?(?:function|class|const|let|var)\s+(\w+)|'
        r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*[\w<>\[\]|,\s]+)?\s*\{)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str) -> TodoFileInfo:
        """
        Extract all TODO-like comments from file content.

        Args:
            content: File content to parse
            file_path: Path to the file (for reporting)

        Returns:
            TodoFileInfo with all extracted TODOs
        """
        file_info = TodoFileInfo(file_path=file_path)

        # Split content into lines for line number tracking
        lines = content.split('\n')

        # Track function/class context
        context_map = self._build_context_map(content)

        for match in self.TODO_PATTERN.finditer(content):
            # Calculate line number
            line_number = content[:match.start()].count('\n') + 1

            # Extract todo type
            todo_type_str = match.group('type').upper()
            try:
                todo_type = TodoType[todo_type_str]
            except KeyError:
                todo_type = TodoType.TODO

            # Extract message
            message = match.group('message').strip()
            # Clean up message (remove trailing comment markers)
            message = re.sub(r'\s*\*/$', '', message)
            message = message.strip()

            # Extract metadata (author, priority, date)
            meta = match.group('meta') or ''
            author = self._extract_author(meta)
            priority = self._extract_priority(meta)
            date = self._extract_date(meta)

            # Find context (function/class name)
            context = self._find_context(line_number, context_map)

            todo = TodoComment(
                todo_type=todo_type,
                line_number=line_number,
                message=message,
                author=author,
                priority=priority,
                date=date,
                related_code=context
            )

            file_info.todos.append(todo)

        return file_info

    def _extract_author(self, meta: str) -> Optional[str]:
        """Extract author from metadata string"""
        match = self.AUTHOR_PATTERN.search(meta)
        if match:
            author = match.group('author')
            # Filter out priority-like strings
            if author.upper() not in ['P0', 'P1', 'P2', 'P3', 'HIGH', 'MEDIUM', 'LOW']:
                return author
        return None

    def _extract_priority(self, meta: str) -> Priority:
        """Extract priority from metadata string"""
        match = self.PRIORITY_PATTERN.search(meta)
        if match:
            prio_str = match.group('priority').upper()
            try:
                return Priority[prio_str]
            except KeyError:
                pass
        return Priority.NONE

    def _extract_date(self, meta: str) -> Optional[str]:
        """Extract date from metadata string"""
        match = self.DATE_PATTERN.search(meta)
        if match:
            return match.group('date')
        return None

    def _build_context_map(self, content: str) -> List[tuple]:
        """
        Build a map of line numbers to function/class context.
        Returns list of (start_line, end_line, context_name) tuples.

        Uses pre-computed line offset array for O(n) instead of O(n²)
        line counting.
        """
        context_map = []

        # Pre-compute a sorted list of newline positions for O(log n) line lookups
        newline_positions = []
        idx = -1
        while True:
            idx = content.find('\n', idx + 1)
            if idx == -1:
                break
            newline_positions.append(idx)

        def _offset_to_line(offset: int) -> int:
            """Convert byte offset to 1-based line number using binary search."""
            import bisect
            return bisect.bisect_right(newline_positions, offset - 1) + 1

        for match in self.CONTEXT_PATTERN.finditer(content):
            name = match.group(1) or match.group(2)
            if not name:
                continue

            start_line = _offset_to_line(match.start())

            # Find the end of this block (simplified: look for closing brace)
            block_start = match.end()
            depth = 1
            i = content.find('{', match.start())
            if i == -1:
                continue

            i += 1
            while i < len(content) and depth > 0:
                if content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                i += 1

            end_line = _offset_to_line(i)
            context_map.append((start_line, end_line, name))

        return context_map

    def _find_context(self, line_number: int, context_map: List[tuple]) -> Optional[str]:
        """Find the function/class context for a given line number"""
        for start, end, name in context_map:
            if start <= line_number <= end:
                return name
        return None


def extract_todos(file_path: Path) -> Optional[TodoFileInfo]:
    """
    Convenience function to extract TODOs from a file.

    Args:
        file_path: Path to the source file

    Returns:
        TodoFileInfo or None if no TODOs found
    """
    if not file_path.exists():
        return None

    content = file_path.read_text(encoding='utf-8')
    extractor = TodoExtractor()
    file_info = extractor.extract(content, str(file_path))

    if file_info.has_todos():
        return file_info
    return None


def extract_project_todos(
    project_path: Path,
    extensions: List[str] = None
) -> tuple[List[TodoFileInfo], TodoSummary]:
    """
    Extract TODOs from all source files in a project.

    Args:
        project_path: Root path of the project
        extensions: File extensions to scan (default: .ts, .js, .py, .tsx, .jsx)

    Returns:
        Tuple of (list of TodoFileInfo, TodoSummary)
    """
    if extensions is None:
        extensions = ['.ts', '.js', '.py', '.tsx', '.jsx', '.vue', '.svelte']

    results = []
    summary = TodoSummary()
    extractor = TodoExtractor()

    for ext in extensions:
        for source_file in project_path.rglob(f'*{ext}'):
            # Skip node_modules, dist, build directories
            if any(skip in str(source_file) for skip in ['node_modules', 'dist', 'build', '.git']):
                continue

            try:
                content = source_file.read_text(encoding='utf-8')
                file_info = extractor.extract(content, str(source_file))

                if file_info.has_todos():
                    results.append(file_info)
                    summary.files_with_todos += 1
                    summary.total_count += len(file_info.todos)

                    # Count by type
                    for todo in file_info.todos:
                        type_name = todo.todo_type.value
                        summary.by_type[type_name] = summary.by_type.get(type_name, 0) + 1

                        prio_name = todo.priority.value
                        summary.by_priority[prio_name] = summary.by_priority.get(prio_name, 0) + 1

            except Exception:
                # Skip files that can't be read
                continue

    return results, summary
