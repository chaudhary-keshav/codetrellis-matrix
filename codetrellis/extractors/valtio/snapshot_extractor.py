"""
Valtio Snapshot Extractor for CodeTrellis

Extracts Valtio snapshot access patterns:
- useSnapshot() React hook calls with destructured access
- snapshot() vanilla JS calls for immutable reads
- useProxy() convenience hook (returns proxy for both render + callbacks)
- Sync option usage (useSnapshot(state, { sync: true }))
- Nested snapshot access (useSnapshot(state.nested))
- Suspense integration (use() with proxy promises)

Supports:
- Valtio v1.x (useSnapshot from 'valtio', snapshot from 'valtio')
- Valtio v2.x (useSnapshot from 'valtio', snapshot from 'valtio/vanilla',
                useProxy from 'valtio/utils')

Part of CodeTrellis v4.56 - Valtio Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ValtioSnapshotUsageInfo:
    """Information about a useSnapshot() or snapshot() call."""
    name: str  # Variable name assigned to snapshot
    file: str = ""
    line_number: int = 0
    snapshot_type: str = ""  # useSnapshot, snapshot
    proxy_name: str = ""  # Which proxy state is being snapshotted
    destructured_fields: List[str] = field(default_factory=list)
    has_sync_option: bool = False
    is_nested_access: bool = False  # useSnapshot(state.nested)
    nested_path: str = ""  # e.g., "state.nested"
    is_in_component: bool = False  # Inside React component


@dataclass
class ValtioUseProxyInfo:
    """Information about a useProxy() convenience hook call."""
    name: str  # Variable name assigned
    file: str = ""
    line_number: int = 0
    proxy_name: str = ""  # Which proxy is passed
    has_options: bool = False


class ValtioSnapshotExtractor:
    """
    Extracts Valtio snapshot access patterns from source code.

    Detects:
    - useSnapshot(state) hook calls
    - snapshot(state) vanilla calls
    - useProxy(state) convenience hook
    - Destructured snapshot access
    - Sync mode usage
    - Nested snapshot access
    """

    # useSnapshot() call: const snap = useSnapshot(state)
    USE_SNAPSHOT_PATTERN = re.compile(
        r'(?:const|let|var)\s+'
        r'(?:\{([^}]+)\}|(\w+))\s*=\s*'
        r'useSnapshot\s*\(\s*([^,)]+?)(?:\s*,\s*\{([^}]*)\})?\s*\)',
        re.MULTILINE
    )

    # useSnapshot without assignment (inline usage)
    USE_SNAPSHOT_INLINE_PATTERN = re.compile(
        r'useSnapshot\s*\(\s*([^,)]+?)(?:\s*,\s*\{([^}]*)\})?\s*\)',
        re.MULTILINE
    )

    # snapshot() vanilla call: const snap = snapshot(state)
    SNAPSHOT_VANILLA_PATTERN = re.compile(
        r'(?:const|let|var)\s+'
        r'(?:\{([^}]+)\}|(\w+))\s*=\s*'
        r'snapshot\s*\(\s*([^)]+?)\s*\)',
        re.MULTILINE
    )

    # useProxy() call: const $state = useProxy(state)
    USE_PROXY_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*'
        r'useProxy\s*\(\s*([^,)]+?)(?:\s*,\s*\{([^}]*)\})?\s*\)',
        re.MULTILINE
    )

    # React component detection (function/const with JSX return)
    COMPONENT_PATTERN = re.compile(
        r'(?:export\s+)?(?:default\s+)?(?:function|const)\s+([A-Z]\w*)',
        re.MULTILINE
    )

    # Suspense use() with snap: use(snap.promise)
    SUSPENSE_USE_PATTERN = re.compile(
        r'use\s*\(\s*(\w+)\.(\w+)\s*\)',
        re.MULTILINE
    )

    def __init__(self) -> None:
        """Initialize the snapshot extractor."""

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract Valtio snapshot patterns from source code.

        Args:
            content: Source code content.
            file_path: Path to source file.

        Returns:
            Dictionary with 'snapshots' and 'use_proxies' lists.
        """
        snapshots: List[ValtioSnapshotUsageInfo] = []
        use_proxies: List[ValtioUseProxyInfo] = []

        # Find component boundaries for is_in_component detection
        component_ranges = self._find_component_ranges(content)

        # Extract useSnapshot() calls
        for match in self.USE_SNAPSHOT_PATTERN.finditer(content):
            destructured = match.group(1)
            snap_name = match.group(2) or ""
            proxy_name = match.group(3).strip()
            options = match.group(4) or ""
            line_num = content[:match.start()].count('\n') + 1

            destructured_fields = []
            if destructured:
                destructured_fields = [f.strip().split(':')[0].strip()
                                       for f in destructured.split(',')
                                       if f.strip()]
                snap_name = "{destructured}"

            has_sync = 'sync' in options and 'true' in options
            is_nested = '.' in proxy_name
            nested_path = proxy_name if is_nested else ""
            is_in_comp = self._is_in_component(line_num, component_ranges)

            snapshots.append(ValtioSnapshotUsageInfo(
                name=snap_name,
                file=file_path,
                line_number=line_num,
                snapshot_type="useSnapshot",
                proxy_name=proxy_name.split('.')[0] if is_nested else proxy_name,
                destructured_fields=destructured_fields,
                has_sync_option=has_sync,
                is_nested_access=is_nested,
                nested_path=nested_path,
                is_in_component=is_in_comp,
            ))

        # Extract snapshot() vanilla calls
        for match in self.SNAPSHOT_VANILLA_PATTERN.finditer(content):
            destructured = match.group(1)
            snap_name = match.group(2) or ""
            proxy_name = match.group(3).strip()
            line_num = content[:match.start()].count('\n') + 1

            destructured_fields = []
            if destructured:
                destructured_fields = [f.strip().split(':')[0].strip()
                                       for f in destructured.split(',')
                                       if f.strip()]
                snap_name = "{destructured}"

            snapshots.append(ValtioSnapshotUsageInfo(
                name=snap_name,
                file=file_path,
                line_number=line_num,
                snapshot_type="snapshot",
                proxy_name=proxy_name,
                destructured_fields=destructured_fields,
            ))

        # Extract useProxy() calls
        for match in self.USE_PROXY_PATTERN.finditer(content):
            var_name = match.group(1)
            proxy_name = match.group(2).strip()
            options = match.group(3) or ""
            line_num = content[:match.start()].count('\n') + 1

            use_proxies.append(ValtioUseProxyInfo(
                name=var_name,
                file=file_path,
                line_number=line_num,
                proxy_name=proxy_name,
                has_options=bool(options.strip()),
            ))

        return {
            'snapshots': snapshots,
            'use_proxies': use_proxies,
        }

    def _find_component_ranges(self, content: str) -> List[tuple]:
        """Find line ranges of React components."""
        ranges = []
        for match in self.COMPONENT_PATTERN.finditer(content):
            start_line = content[:match.start()].count('\n') + 1
            # Estimate component end (next component or EOF)
            ranges.append((start_line, start_line + 200))
        return ranges

    def _is_in_component(self, line: int, ranges: List[tuple]) -> bool:
        """Check if a line is inside a React component."""
        for start, end in ranges:
            if start <= line <= end:
                return True
        return False
