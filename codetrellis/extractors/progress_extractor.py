"""
CodeTrellis Progress Extractor
=======================

Extracts project progress indicators including:
- TODO/FIXME/HACK/NOTE comments
- Status markers (@status: complete/in-progress/pending)
- Empty/placeholder implementations
- Deprecated markers
- Implementation completeness metrics

This helps AI understand project progress and what needs work.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ProgressStatus(Enum):
    """Status of a code element"""
    COMPLETE = "complete"
    IN_PROGRESS = "in-progress"
    PENDING = "pending"
    DEPRECATED = "deprecated"
    BLOCKED = "blocked"


class MarkerType(Enum):
    """Type of progress marker"""
    TODO = "todo"
    FIXME = "fixme"
    HACK = "hack"
    NOTE = "note"
    STATUS = "status"
    DEPRECATED = "deprecated"
    PLACEHOLDER = "placeholder"
    BLOCKER = "blocker"


@dataclass
class ProgressMarker:
    """A single progress marker found in code"""
    marker_type: MarkerType
    message: str
    file_path: str
    line_number: int
    priority: str = "normal"  # low, normal, high, critical
    assignee: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.marker_type.value,
            "message": self.message,
            "file": self.file_path,
            "line": self.line_number,
            "priority": self.priority,
            "assignee": self.assignee,
            "tags": self.tags,
        }

    def to_codetrellis_format(self) -> str:
        """Convert to compact CodeTrellis format"""
        short_file = Path(self.file_path).name
        priority_marker = ""
        if self.priority == "high":
            priority_marker = "!"
        elif self.priority == "critical":
            priority_marker = "!!"

        # Truncate message to 50 chars
        msg = self.message[:50] + "..." if len(self.message) > 50 else self.message
        return f"{self.marker_type.value.upper()}{priority_marker}:{short_file}:{self.line_number}:{msg}"


@dataclass
class PlaceholderImplementation:
    """An empty or placeholder implementation"""
    name: str
    kind: str  # function, method, class
    file_path: str
    line_number: int
    reason: str = "not implemented"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "file": self.file_path,
            "line": self.line_number,
            "reason": self.reason,
        }

    def to_codetrellis_format(self) -> str:
        short_file = Path(self.file_path).name
        return f"{self.kind}:{self.name}@{short_file}:{self.line_number}"


@dataclass
class FileProgress:
    """Progress information for a single file"""
    file_path: str
    markers: List[ProgressMarker] = field(default_factory=list)
    placeholders: List[PlaceholderImplementation] = field(default_factory=list)
    status: ProgressStatus = ProgressStatus.COMPLETE
    completion_estimate: int = 100  # 0-100 percentage

    @property
    def todos(self) -> List[ProgressMarker]:
        return [m for m in self.markers if m.marker_type == MarkerType.TODO]

    @property
    def fixmes(self) -> List[ProgressMarker]:
        return [m for m in self.markers if m.marker_type == MarkerType.FIXME]

    @property
    def deprecated_count(self) -> int:
        return len([m for m in self.markers if m.marker_type == MarkerType.DEPRECATED])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file_path,
            "status": self.status.value,
            "completion": self.completion_estimate,
            "markers": [m.to_dict() for m in self.markers],
            "placeholders": [p.to_dict() for p in self.placeholders],
            "summary": {
                "todos": len(self.todos),
                "fixmes": len(self.fixmes),
                "deprecated": self.deprecated_count,
                "placeholders": len(self.placeholders),
            }
        }


@dataclass
class ProjectProgress:
    """Aggregated progress for entire project"""
    files: List[FileProgress] = field(default_factory=list)

    @property
    def total_todos(self) -> int:
        return sum(len(f.todos) for f in self.files)

    @property
    def total_fixmes(self) -> int:
        return sum(len(f.fixmes) for f in self.files)

    @property
    def total_deprecated(self) -> int:
        return sum(f.deprecated_count for f in self.files)

    @property
    def total_placeholders(self) -> int:
        return sum(len(f.placeholders) for f in self.files)

    @property
    def all_markers(self) -> List[ProgressMarker]:
        markers = []
        for f in self.files:
            markers.extend(f.markers)
        return markers

    @property
    def high_priority_items(self) -> List[ProgressMarker]:
        return [m for m in self.all_markers if m.priority in ("high", "critical")]

    @property
    def blockers(self) -> List[ProgressMarker]:
        return [m for m in self.all_markers if m.marker_type == MarkerType.BLOCKER]

    @property
    def completion_percentage(self) -> int:
        """Estimate overall project completion"""
        if not self.files:
            return 100

        # Weight by file count and marker density
        total_issues = self.total_todos + self.total_fixmes + self.total_placeholders

        # Rough heuristic: each issue reduces completion by ~2%
        # Max penalty is 50%
        penalty = min(total_issues * 2, 50)
        return max(100 - penalty, 50)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "completion": self.completion_percentage,
            "summary": {
                "todos": self.total_todos,
                "fixmes": self.total_fixmes,
                "deprecated": self.total_deprecated,
                "placeholders": self.total_placeholders,
                "blockers": len(self.blockers),
                "high_priority": len(self.high_priority_items),
            },
            "files": [f.to_dict() for f in self.files],
        }

    def to_codetrellis_format(self) -> str:
        """Convert to compact CodeTrellis format for prompt injection"""
        lines = []

        # Summary line
        lines.append(f"completion:{self.completion_percentage}%|"
                    f"todos:{self.total_todos}|fixmes:{self.total_fixmes}|"
                    f"deprecated:{self.total_deprecated}|placeholders:{self.total_placeholders}")

        # High priority items (limited to top 5)
        if self.high_priority_items:
            priority_items = self.high_priority_items[:5]
            items_str = ",".join(m.to_codetrellis_format() for m in priority_items)
            lines.append(f"priority:{items_str}")

        # Blockers (limited to top 3)
        if self.blockers:
            blocker_items = self.blockers[:3]
            items_str = ",".join(m.to_codetrellis_format() for m in blocker_items)
            lines.append(f"blockers:{items_str}")

        # Recent/notable TODOs (limited to top 5)
        recent_todos = [m for m in self.all_markers if m.marker_type == MarkerType.TODO][:5]
        if recent_todos:
            items_str = ",".join(m.to_codetrellis_format() for m in recent_todos)
            lines.append(f"todos:{items_str}")

        return "\n".join(lines)


class ProgressExtractor:
    """
    Extracts progress indicators from source code.

    Supports:
    - TypeScript/JavaScript
    - Python
    - Multiple comment styles (// /* */ # \"\"\" ''')
    """

    # Regex patterns for different marker types
    PATTERNS = {
        # TODO patterns: // TODO: message, // TODO(assignee): message, # TODO: message
        "todo": [
            r'(?://|#|/\*|\*)\s*TODO(?:\s*\(([^)]+)\))?:\s*(.+?)(?:\*/|\n|$)',
            r'(?://|#)\s*TODO(?:\s*\(([^)]+)\))?[:\s]+(.+?)$',
        ],
        # FIXME patterns
        "fixme": [
            r'(?://|#|/\*|\*)\s*FIXME(?:\s*\(([^)]+)\))?:\s*(.+?)(?:\*/|\n|$)',
            r'(?://|#)\s*FIXME(?:\s*\(([^)]+)\))?[:\s]+(.+?)$',
        ],
        # HACK patterns
        "hack": [
            r'(?://|#|/\*|\*)\s*HACK(?:\s*\(([^)]+)\))?:\s*(.+?)(?:\*/|\n|$)',
            r'(?://|#)\s*HACK(?:\s*\(([^)]+)\))?[:\s]+(.+?)$',
        ],
        # NOTE patterns
        "note": [
            r'(?://|#|/\*|\*)\s*NOTE(?:\s*\(([^)]+)\))?:\s*(.+?)(?:\*/|\n|$)',
        ],
        # @status: complete|in-progress|pending
        "status": [
            r'@status:\s*(complete|in-progress|pending|wip|done|blocked)',
        ],
        # @deprecated markers
        "deprecated": [
            r'@deprecated(?:\s+(.+?))?(?:\*/|\n|$)',
            r'(?://|#)\s*DEPRECATED:\s*(.+?)$',
        ],
        # BLOCKER patterns
        "blocker": [
            r'(?://|#|/\*|\*)\s*BLOCKER:\s*(.+?)(?:\*/|\n|$)',
            r'(?://|#)\s*BLOCKED(?:\s+BY)?:\s*(.+?)$',
        ],
    }

    # Patterns for placeholder/empty implementations
    PLACEHOLDER_PATTERNS = {
        "typescript": [
            # throw new Error('Not implemented')
            r'(?:async\s+)?(?:function|method)?\s*(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{\s*throw\s+(?:new\s+)?Error\s*\([\'"](?:Not implemented|TODO)[\'"]',
            # return null; or return undefined;
            r'(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{\s*(?://.*\n\s*)?return\s+(?:null|undefined)\s*;\s*\}',
            # Empty body with just a comment
            r'(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{\s*//\s*(?:TODO|FIXME|implement)',
        ],
        "python": [
            # raise NotImplementedError
            r'def\s+(\w+)\s*\([^)]*\)\s*(?:->.*)?:\s*(?:#.*\n\s*)?raise\s+NotImplementedError',
            # pass only
            r'def\s+(\w+)\s*\([^)]*\)\s*(?:->.*)?:\s*(?:#.*\n\s*)?pass\s*(?:\n|$)',
            # ... (ellipsis)
            r'def\s+(\w+)\s*\([^)]*\)\s*(?:->.*)?:\s*(?:#.*\n\s*)?\.\.\.\s*(?:\n|$)',
        ],
    }

    # Priority keywords
    PRIORITY_KEYWORDS = {
        "critical": ["CRITICAL", "URGENT", "ASAP", "!!!"],
        "high": ["HIGH", "IMPORTANT", "!!"],
        "low": ["LOW", "MINOR", "LATER", "SOMEDAY"],
    }

    def __init__(self):
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance"""
        for marker_type, patterns in self.PATTERNS.items():
            self._compiled_patterns[marker_type] = [
                re.compile(p, re.MULTILINE | re.IGNORECASE)
                for p in patterns
            ]

    @staticmethod
    def _is_inside_string_literal(line: str, match_text: str) -> bool:
        """Check if a matched marker is inside a string literal or regex definition.

        Phase E fix: Prevents self-contamination when CodeTrellis scans its own source.
        The PATTERNS dict contains raw regex strings with markers like 'BLOCKER:'
        that would otherwise match as real blockers during self-scan.

        Heuristics:
        1. Line contains r' or r\" before the match (raw string / regex definition)
        2. Line is a dict/list string entry (enclosed in quotes with comma)
        3. Match text contains regex metacharacters (escaped sequences)
        """
        stripped = line.strip()

        # Check for raw string patterns: r'...' or r"..."
        if "r'" in stripped or 'r"' in stripped:
            return True

        # Check for regular string assignments containing the marker
        # e.g., pattern = '...BLOCKER...'
        if stripped.startswith(('r"', "r'", '"', "'", 'f"', "f'")):
            return True

        # Check if the matched text contains regex metacharacters
        # Real comments don't have (?:  \s*  (.+?)  etc.
        regex_indicators = [r'\s*', r'(.+?)', r'(?:', r'\*)', r'\n|$', r'\\']
        if match_text and any(ind in match_text for ind in regex_indicators):
            return True

        return False

    def extract(self, content: str, file_path: str = "") -> FileProgress:
        """
        Extract all progress markers from file content.

        Args:
            content: Source code content
            file_path: Path to the file (for context)

        Returns:
            FileProgress with all extracted markers
        """
        markers: List[ProgressMarker] = []
        placeholders: List[PlaceholderImplementation] = []

        lines = content.split('\n')

        # Extract comment markers
        for marker_type, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(content):
                    line_num = content[:match.start()].count('\n') + 1

                    # Phase E fix: Skip matches that are inside string literals
                    # or regex pattern definitions. When CodeTrellis self-scans, the
                    # BLOCKER regex strings in this file's PATTERNS dict match
                    # themselves, leaking raw regex into ACTIONABLE_ITEMS.
                    matched_line = lines[line_num - 1] if line_num <= len(lines) else ""
                    if self._is_inside_string_literal(matched_line, match.group()):
                        continue

                    # Extract message and optional assignee
                    groups = match.groups()
                    if marker_type == "status":
                        message = groups[0] if groups else ""
                        assignee = None
                    elif len(groups) >= 2:
                        assignee = groups[0]
                        message = groups[1] if groups[1] else ""
                    else:
                        assignee = None
                        message = groups[0] if groups else ""

                    # Determine priority
                    priority = self._detect_priority(message or "")

                    # Extract tags (e.g., #tag or #tag-123 in message)
                    tags = re.findall(r'#([\w-]+)', message or "")

                    marker = ProgressMarker(
                        marker_type=MarkerType(marker_type),
                        message=message.strip() if message else "",
                        file_path=file_path,
                        line_number=line_num,
                        priority=priority,
                        assignee=assignee,
                        tags=tags,
                    )
                    markers.append(marker)

        # Extract placeholder implementations
        placeholders.extend(self._extract_placeholders(content, file_path))

        # Calculate file status and completion
        status = self._determine_status(markers)
        completion = self._estimate_completion(markers, placeholders)

        return FileProgress(
            file_path=file_path,
            markers=markers,
            placeholders=placeholders,
            status=status,
            completion_estimate=completion,
        )

    def _detect_priority(self, message: str) -> str:
        """Detect priority from message content.
        
        Priority keywords at the start of the message (e.g., 'HIGH: ...')
        take precedence over keywords appearing later in the message body.
        """
        upper_msg = message.upper().strip()

        # First pass: check if message STARTS with a priority keyword
        for priority, keywords in self.PRIORITY_KEYWORDS.items():
            for keyword in keywords:
                if upper_msg.startswith(keyword):
                    return priority

        # Second pass: check anywhere in message
        for priority, keywords in self.PRIORITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in upper_msg:
                    return priority

        return "normal"

    def _extract_placeholders(self, content: str, file_path: str) -> List[PlaceholderImplementation]:
        """Extract placeholder/stub implementations"""
        placeholders = []

        # Determine language from file extension
        ext = Path(file_path).suffix.lower() if file_path else ""

        if ext in ('.ts', '.js', '.tsx', '.jsx'):
            patterns = self.PLACEHOLDER_PATTERNS.get("typescript", [])
        elif ext == '.py':
            patterns = self.PLACEHOLDER_PATTERNS.get("python", [])
        else:
            patterns = []

        for pattern_str in patterns:
            pattern = re.compile(pattern_str, re.MULTILINE)
            for match in pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                name = match.group(1) if match.groups() else "unknown"

                placeholder = PlaceholderImplementation(
                    name=name,
                    kind="function",
                    file_path=file_path,
                    line_number=line_num,
                    reason="not implemented",
                )
                placeholders.append(placeholder)

        return placeholders

    def _determine_status(self, markers: List[ProgressMarker]) -> ProgressStatus:
        """Determine file status based on markers"""
        # Check for explicit status markers
        status_markers = [m for m in markers if m.marker_type == MarkerType.STATUS]
        if status_markers:
            status_text = status_markers[-1].message.lower()
            if status_text in ("complete", "done"):
                return ProgressStatus.COMPLETE
            elif status_text in ("in-progress", "wip"):
                return ProgressStatus.IN_PROGRESS
            elif status_text == "blocked":
                return ProgressStatus.BLOCKED
            elif status_text == "pending":
                return ProgressStatus.PENDING

        # Check for blockers
        if any(m.marker_type == MarkerType.BLOCKER for m in markers):
            return ProgressStatus.BLOCKED

        # Check for FIXMEs (indicates issues)
        fixmes = [m for m in markers if m.marker_type == MarkerType.FIXME]
        if len(fixmes) > 3:
            return ProgressStatus.IN_PROGRESS

        # Check for TODOs
        todos = [m for m in markers if m.marker_type == MarkerType.TODO]
        if len(todos) > 5:
            return ProgressStatus.IN_PROGRESS

        return ProgressStatus.COMPLETE

    def _estimate_completion(self, markers: List[ProgressMarker],
                            placeholders: List[PlaceholderImplementation]) -> int:
        """Estimate file completion percentage"""
        base = 100

        # Deduct for TODOs (2% each, max 30%)
        todos = len([m for m in markers if m.marker_type == MarkerType.TODO])
        base -= min(todos * 2, 30)

        # Deduct for FIXMEs (3% each, max 20%)
        fixmes = len([m for m in markers if m.marker_type == MarkerType.FIXME])
        base -= min(fixmes * 3, 20)

        # Deduct for placeholders (5% each, max 30%)
        base -= min(len(placeholders) * 5, 30)

        # Deduct for blockers (10% each)
        blockers = len([m for m in markers if m.marker_type == MarkerType.BLOCKER])
        base -= min(blockers * 10, 20)

        return max(base, 10)  # Minimum 10%

    def can_extract(self, file_path: str) -> bool:
        """Check if this extractor can handle the file"""
        ext = Path(file_path).suffix.lower()
        return ext in ('.ts', '.tsx', '.js', '.jsx', '.py', '.java', '.go', '.rs', '.cpp', '.c', '.h')

    def to_dict(self, progress: FileProgress) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return progress.to_dict()

    def to_codetrellis_format(self, progress: FileProgress) -> str:
        """Convert to CodeTrellis compact format"""
        lines = []
        short_file = Path(progress.file_path).name

        if progress.markers or progress.placeholders:
            lines.append(f"{short_file}|status:{progress.status.value}|"
                        f"completion:{progress.completion_estimate}%")

            # Add marker summary
            summary_parts = []
            if progress.todos:
                summary_parts.append(f"todos:{len(progress.todos)}")
            if progress.fixmes:
                summary_parts.append(f"fixmes:{len(progress.fixmes)}")
            if progress.placeholders:
                summary_parts.append(f"stubs:{len(progress.placeholders)}")

            if summary_parts:
                lines.append("  " + "|".join(summary_parts))

        return "\n".join(lines)
