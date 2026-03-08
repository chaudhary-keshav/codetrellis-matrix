"""
PandasExtractor - Extracts Pandas DataFrame operations and transformations.

This extractor parses Python code using Pandas and extracts:
- DataFrame creation and I/O operations
- Column transformations
- Aggregations and groupby operations
- Merge/join operations
- Data cleaning operations
- Type conversions

Part of CodeTrellis v2.0 - Python Data Engineering Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class DataFrameInfo:
    """Information about a DataFrame variable."""
    name: str
    source: Optional[str] = None  # csv, parquet, sql, dict, etc.
    source_path: Optional[str] = None
    columns: List[str] = field(default_factory=list)
    dtypes: Dict[str, str] = field(default_factory=dict)
    line_number: int = 0


@dataclass
class DataFrameOperationInfo:
    """Information about a DataFrame operation."""
    dataframe: str
    operation: str  # filter, transform, aggregate, merge, etc.
    columns: List[str] = field(default_factory=list)
    details: Optional[str] = None


@dataclass
class GroupByInfo:
    """Information about a groupby operation."""
    dataframe: str
    group_columns: List[str] = field(default_factory=list)
    aggregations: Dict[str, List[str]] = field(default_factory=dict)  # col: [agg_funcs]


@dataclass
class MergeJoinInfo:
    """Information about a merge/join operation."""
    left_df: str
    right_df: str
    how: str = "inner"  # inner, left, right, outer
    on: List[str] = field(default_factory=list)
    left_on: Optional[str] = None
    right_on: Optional[str] = None


@dataclass
class DataIOInfo:
    """Information about data I/O operations."""
    operation: str  # read, write
    format: str  # csv, parquet, json, excel, sql, etc.
    path_or_table: Optional[str] = None
    dataframe: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)


class PandasExtractor:
    """
    Extracts Pandas-related components from Python source code.

    Handles:
    - DataFrame creation from various sources
    - Read/write operations
    - Column selections and transformations
    - Groupby and aggregations
    - Merge and join operations
    - Data cleaning and type conversions
    """

    # DataFrame read patterns
    READ_CSV_PATTERN = re.compile(
        r'(\w+)\s*=\s*pd\.read_csv\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    READ_PARQUET_PATTERN = re.compile(
        r'(\w+)\s*=\s*pd\.read_parquet\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    READ_JSON_PATTERN = re.compile(
        r'(\w+)\s*=\s*pd\.read_json\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    READ_EXCEL_PATTERN = re.compile(
        r'(\w+)\s*=\s*pd\.read_excel\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    READ_SQL_PATTERN = re.compile(
        r'(\w+)\s*=\s*pd\.read_sql(?:_query|_table)?\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    # DataFrame from dict/list
    DATAFRAME_DICT_PATTERN = re.compile(
        r'(\w+)\s*=\s*pd\.DataFrame\s*\(\s*\{',
        re.MULTILINE
    )

    # Write patterns
    TO_CSV_PATTERN = re.compile(
        r'(\w+)\.to_csv\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    TO_PARQUET_PATTERN = re.compile(
        r'(\w+)\.to_parquet\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    TO_SQL_PATTERN = re.compile(
        r'(\w+)\.to_sql\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    # Column operations
    COLUMN_SELECT_PATTERN = re.compile(
        r'(\w+)\s*\[\s*\[\s*[\'"]([^"\']+)[\'"](?:,\s*[\'"]([^"\']+)[\'"])*\s*\]\s*\]',
        re.MULTILINE
    )

    COLUMN_RENAME_PATTERN = re.compile(
        r'(\w+)\.rename\s*\(\s*columns\s*=\s*\{([^}]+)\}',
        re.MULTILINE
    )

    # GroupBy patterns
    GROUPBY_PATTERN = re.compile(
        r'(\w+)\.groupby\s*\(\s*(?:\[)?[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    GROUPBY_AGG_PATTERN = re.compile(
        r'\.agg\s*\(\s*\{([^}]+)\}',
        re.MULTILINE
    )

    # Merge patterns
    MERGE_PATTERN = re.compile(
        r'(?:pd\.)?merge\s*\(\s*(\w+)\s*,\s*(\w+)',
        re.MULTILINE
    )

    DF_MERGE_PATTERN = re.compile(
        r'(\w+)\.merge\s*\(\s*(\w+)',
        re.MULTILINE
    )

    # Filter patterns
    FILTER_PATTERN = re.compile(
        r'(\w+)\s*\[\s*(\w+)\s*\[\s*[\'"]([^"\']+)[\'"]\s*\]',
        re.MULTILINE
    )

    QUERY_PATTERN = re.compile(
        r'(\w+)\.query\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    # Transform patterns
    APPLY_PATTERN = re.compile(
        r'(\w+)(?:\[[\'"][^\'"]+[\'"]\])?\.apply\s*\(',
        re.MULTILINE
    )

    TRANSFORM_PATTERN = re.compile(
        r'(\w+)\.transform\s*\(',
        re.MULTILINE
    )

    # Type conversion
    ASTYPE_PATTERN = re.compile(
        r'(\w+)\[[\'"]([^"\']+)[\'"]\]\s*=\s*\w+\[[\'"][^\'"]+[\'"]\]\.astype\s*\(\s*[\'"]?(\w+)[\'"]?',
        re.MULTILINE
    )

    # Fillna/dropna
    FILLNA_PATTERN = re.compile(
        r'(\w+)\.fillna\s*\(',
        re.MULTILINE
    )

    DROPNA_PATTERN = re.compile(
        r'(\w+)\.dropna\s*\(',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the Pandas extractor."""
        pass

    def extract(self, content: str) -> Dict[str, Any]:
        """
        Extract all Pandas components from Python content.

        Args:
            content: Python source code

        Returns:
            Dict with dataframes, io_operations, groupbys, merges, transformations
        """
        dataframes = self._extract_dataframes(content)
        io_operations = self._extract_io_operations(content)
        groupbys = self._extract_groupbys(content)
        merges = self._extract_merges(content)
        transformations = self._extract_transformations(content)

        return {
            'dataframes': dataframes,
            'io_operations': io_operations,
            'groupbys': groupbys,
            'merges': merges,
            'transformations': transformations
        }

    def _extract_dataframes(self, content: str) -> List[DataFrameInfo]:
        """Extract DataFrame variable definitions."""
        dataframes = []
        seen = set()

        # CSV reads
        for match in self.READ_CSV_PATTERN.finditer(content):
            var_name = match.group(1)
            source_path = match.group(2)
            if var_name not in seen:
                seen.add(var_name)
                dataframes.append(DataFrameInfo(
                    name=var_name,
                    source="csv",
                    source_path=source_path,
                    line_number=content[:match.start()].count('\n') + 1
                ))

        # Parquet reads
        for match in self.READ_PARQUET_PATTERN.finditer(content):
            var_name = match.group(1)
            source_path = match.group(2)
            if var_name not in seen:
                seen.add(var_name)
                dataframes.append(DataFrameInfo(
                    name=var_name,
                    source="parquet",
                    source_path=source_path,
                    line_number=content[:match.start()].count('\n') + 1
                ))

        # JSON reads
        for match in self.READ_JSON_PATTERN.finditer(content):
            var_name = match.group(1)
            source_path = match.group(2)
            if var_name not in seen:
                seen.add(var_name)
                dataframes.append(DataFrameInfo(
                    name=var_name,
                    source="json",
                    source_path=source_path,
                    line_number=content[:match.start()].count('\n') + 1
                ))

        # SQL reads
        for match in self.READ_SQL_PATTERN.finditer(content):
            var_name = match.group(1)
            query = match.group(2)
            if var_name not in seen:
                seen.add(var_name)
                dataframes.append(DataFrameInfo(
                    name=var_name,
                    source="sql",
                    source_path=query[:50] + "..." if len(query) > 50 else query,
                    line_number=content[:match.start()].count('\n') + 1
                ))

        # Dict/list DataFrames
        for match in self.DATAFRAME_DICT_PATTERN.finditer(content):
            var_name = match.group(1)
            if var_name not in seen:
                seen.add(var_name)
                dataframes.append(DataFrameInfo(
                    name=var_name,
                    source="dict",
                    line_number=content[:match.start()].count('\n') + 1
                ))

        return dataframes

    def _extract_io_operations(self, content: str) -> List[DataIOInfo]:
        """Extract data I/O operations."""
        io_ops = []

        # Read operations (summarized from dataframes)
        for pattern, fmt in [
            (self.READ_CSV_PATTERN, "csv"),
            (self.READ_PARQUET_PATTERN, "parquet"),
            (self.READ_JSON_PATTERN, "json"),
            (self.READ_SQL_PATTERN, "sql"),
        ]:
            for match in pattern.finditer(content):
                io_ops.append(DataIOInfo(
                    operation="read",
                    format=fmt,
                    path_or_table=match.group(2),
                    dataframe=match.group(1)
                ))

        # Write operations
        for match in self.TO_CSV_PATTERN.finditer(content):
            io_ops.append(DataIOInfo(
                operation="write",
                format="csv",
                path_or_table=match.group(2),
                dataframe=match.group(1)
            ))

        for match in self.TO_PARQUET_PATTERN.finditer(content):
            io_ops.append(DataIOInfo(
                operation="write",
                format="parquet",
                path_or_table=match.group(2),
                dataframe=match.group(1)
            ))

        for match in self.TO_SQL_PATTERN.finditer(content):
            io_ops.append(DataIOInfo(
                operation="write",
                format="sql",
                path_or_table=match.group(2),
                dataframe=match.group(1)
            ))

        return io_ops

    def _extract_groupbys(self, content: str) -> List[GroupByInfo]:
        """Extract groupby operations."""
        groupbys = []

        for match in self.GROUPBY_PATTERN.finditer(content):
            df_name = match.group(1)
            group_col = match.group(2)

            # Look for additional group columns and aggregations
            context = content[match.start():match.start()+300]

            # Check for .agg()
            agg_match = self.GROUPBY_AGG_PATTERN.search(context)
            aggregations = {}
            if agg_match:
                agg_str = agg_match.group(1)
                # Simple parsing of aggregations
                for agg_item in re.finditer(r'[\'"](\w+)[\'"]\s*:\s*\[?([^\],}]+)', agg_str):
                    col = agg_item.group(1)
                    funcs = re.findall(r'[\'"](\w+)[\'"]', agg_item.group(2))
                    if funcs:
                        aggregations[col] = funcs

            groupbys.append(GroupByInfo(
                dataframe=df_name,
                group_columns=[group_col],
                aggregations=aggregations
            ))

        return groupbys

    def _extract_merges(self, content: str) -> List[MergeJoinInfo]:
        """Extract merge/join operations."""
        merges = []

        # pd.merge()
        for match in self.MERGE_PATTERN.finditer(content):
            left_df = match.group(1)
            right_df = match.group(2)
            context = content[match.start():match.start()+200]

            how = "inner"
            how_match = re.search(r'how\s*=\s*[\'"](\w+)[\'"]', context)
            if how_match:
                how = how_match.group(1)

            on_cols = []
            on_match = re.search(r'on\s*=\s*[\'"](\w+)[\'"]', context)
            if on_match:
                on_cols = [on_match.group(1)]

            merges.append(MergeJoinInfo(
                left_df=left_df,
                right_df=right_df,
                how=how,
                on=on_cols
            ))

        # df.merge()
        for match in self.DF_MERGE_PATTERN.finditer(content):
            left_df = match.group(1)
            right_df = match.group(2)
            context = content[match.start():match.start()+200]

            how = "inner"
            how_match = re.search(r'how\s*=\s*[\'"](\w+)[\'"]', context)
            if how_match:
                how = how_match.group(1)

            merges.append(MergeJoinInfo(
                left_df=left_df,
                right_df=right_df,
                how=how
            ))

        return merges

    def _extract_transformations(self, content: str) -> List[DataFrameOperationInfo]:
        """Extract DataFrame transformation operations."""
        operations = []

        # Apply operations
        for match in self.APPLY_PATTERN.finditer(content):
            operations.append(DataFrameOperationInfo(
                dataframe=match.group(1),
                operation="apply"
            ))

        # Transform operations
        for match in self.TRANSFORM_PATTERN.finditer(content):
            operations.append(DataFrameOperationInfo(
                dataframe=match.group(1),
                operation="transform"
            ))

        # Query/filter operations
        for match in self.QUERY_PATTERN.finditer(content):
            operations.append(DataFrameOperationInfo(
                dataframe=match.group(1),
                operation="query",
                details=match.group(2)[:30] if len(match.group(2)) > 30 else match.group(2)
            ))

        # Fillna
        for match in self.FILLNA_PATTERN.finditer(content):
            operations.append(DataFrameOperationInfo(
                dataframe=match.group(1),
                operation="fillna"
            ))

        # Dropna
        for match in self.DROPNA_PATTERN.finditer(content):
            operations.append(DataFrameOperationInfo(
                dataframe=match.group(1),
                operation="dropna"
            ))

        return operations

    def to_codetrellis_format(self, result: Dict[str, Any]) -> str:
        """Convert extracted Pandas data to CodeTrellis format."""
        lines = []

        # DataFrames
        dataframes = result.get('dataframes', [])
        if dataframes:
            lines.append("[PANDAS_DATAFRAMES]")
            for df in dataframes:
                parts = [df.name, f"source:{df.source}"]
                if df.source_path:
                    path_short = df.source_path if len(df.source_path) < 40 else "..." + df.source_path[-37:]
                    parts.append(f"path:{path_short}")
                lines.append("|".join(parts))
            lines.append("")

        # I/O Operations summary
        io_ops = result.get('io_operations', [])
        if io_ops:
            reads = [op for op in io_ops if op.operation == "read"]
            writes = [op for op in io_ops if op.operation == "write"]

            if reads:
                lines.append("[PANDAS_READ_OPS]")
                for op in reads:
                    lines.append(f"{op.dataframe}|format:{op.format}")
                lines.append("")

            if writes:
                lines.append("[PANDAS_WRITE_OPS]")
                for op in writes:
                    lines.append(f"{op.dataframe}→{op.format}|path:{op.path_or_table}")
                lines.append("")

        # GroupBys
        groupbys = result.get('groupbys', [])
        if groupbys:
            lines.append("[PANDAS_GROUPBYS]")
            for gb in groupbys:
                parts = [gb.dataframe, f"by:[{','.join(gb.group_columns)}]"]
                if gb.aggregations:
                    aggs = []
                    for col, funcs in list(gb.aggregations.items())[:3]:
                        aggs.append(f"{col}:{','.join(funcs)}")
                    parts.append(f"agg:[{';'.join(aggs)}]")
                lines.append("|".join(parts))
            lines.append("")

        # Merges
        merges = result.get('merges', [])
        if merges:
            lines.append("[PANDAS_MERGES]")
            for m in merges:
                parts = [f"{m.left_df}⨝{m.right_df}", f"how:{m.how}"]
                if m.on:
                    parts.append(f"on:[{','.join(m.on)}]")
                lines.append("|".join(parts))
            lines.append("")

        # Transformations summary
        transformations = result.get('transformations', [])
        if transformations:
            lines.append("[PANDAS_TRANSFORMS]")
            # Group by operation type
            by_op = {}
            for t in transformations:
                if t.operation not in by_op:
                    by_op[t.operation] = []
                by_op[t.operation].append(t.dataframe)

            for op, dfs in by_op.items():
                unique_dfs = list(set(dfs))[:5]
                lines.append(f"{op}|dfs:[{','.join(unique_dfs)}]")

        return "\n".join(lines)


# Convenience function
def extract_pandas(content: str) -> Dict[str, Any]:
    """Extract Pandas components from Python content."""
    extractor = PandasExtractor()
    return extractor.extract(content)
