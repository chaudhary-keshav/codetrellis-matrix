"""
R Model Extractor for CodeTrellis

Extracts data model and database-related definitions from R source code:
- DBI database connections and queries
- dbplyr table references
- dplyr data transformations
- data.table operations
- tidyverse data pipelines
- Arrow/Parquet dataset definitions
- Spark DataFrames (sparklyr)
- MonetDBLite/DuckDB connections
- SQLite, PostgreSQL, MySQL connections via DBI
- Pool database connection pools

Supports: R 3.x through R 4.4+
Part of CodeTrellis v4.26 - R Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RDataModelInfo:
    """Information about an R data model/schema."""
    name: str
    kind: str = "data.frame"  # data.frame, tibble, data.table, arrow, spark
    columns: List[Dict[str, str]] = field(default_factory=list)  # name, type pairs
    source: str = ""  # CSV, database, API, etc.
    file: str = ""
    line_number: int = 0


@dataclass
class RDBConnectionInfo:
    """Information about a database connection in R."""
    name: str
    driver: str = ""  # RSQLite, RPostgres, RMySQL, etc.
    database: str = ""
    host: str = ""
    pool: bool = False  # Uses pool package
    file: str = ""
    line_number: int = 0


@dataclass
class RDBQueryInfo:
    """Information about a database query in R."""
    name: str
    query_type: str = "SELECT"  # SELECT, INSERT, UPDATE, DELETE
    table: str = ""
    connection_var: str = ""
    is_parameterized: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class RDataPipelineInfo:
    """Information about a data transformation pipeline."""
    name: str
    steps: List[str] = field(default_factory=list)
    input_source: str = ""
    output_target: str = ""
    framework: str = "dplyr"  # dplyr, data.table, base
    file: str = ""
    line_number: int = 0


class RModelExtractor:
    """
    Extracts R data model and database definitions.

    Detects:
    - DBI connections: dbConnect(RSQLite::SQLite(), ...)
    - Pool connections: dbPool(drv, ...)
    - SQL queries: dbGetQuery, dbSendQuery, dbExecute
    - dbplyr: tbl(con, "table"), tbl(con, in_schema(...))
    - dplyr verbs: select, filter, mutate, group_by, summarize, join
    - data.table: [, := , .SD, .N, .GRP, merge, fread]
    - Arrow: read_parquet, read_feather, open_dataset
    - sparklyr: spark_read_*, sdf_* functions
    - Data schema inference from read_csv/read_tsv column definitions
    """

    # DBI connection patterns
    DBI_CONNECT = re.compile(
        r'(\w+)\s*(?:<-|=)\s*(?:DBI::)?dbConnect\s*\(\s*(\w+(?:::\w+)?(?:\(\))?)',
        re.MULTILINE
    )

    # Pool connection patterns
    POOL_CONNECT = re.compile(
        r'(\w+)\s*(?:<-|=)\s*(?:pool::)?dbPool\s*\(\s*(\w+(?:::\w+)?(?:\(\))?)',
        re.MULTILINE
    )

    # Database queries
    DB_QUERY = re.compile(
        r'(?:DBI::)?(?:dbGetQuery|dbSendQuery|dbExecute|dbSendStatement)\s*\(\s*(\w+)\s*,\s*["\']([^"\']*)["\']',
        re.MULTILINE
    )

    # Parameterized queries
    DB_PARAM_QUERY = re.compile(
        r'(?:DBI::)?(?:dbGetQuery|dbSendQuery|dbExecute)\s*\(\s*(\w+)\s*,.*?(?:params|param)\s*=',
        re.MULTILINE | re.DOTALL
    )

    # dbplyr table reference
    DBPLYR_TBL = re.compile(
        r'(\w+)\s*(?:<-|=)\s*(?:dplyr::)?tbl\s*\(\s*(\w+)\s*,\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    # dbplyr in_schema
    DBPLYR_SCHEMA = re.compile(
        r'tbl\s*\(\s*\w+\s*,\s*(?:dbplyr::)?in_schema\s*\(\s*["\'](\w+)["\']\s*,\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    # CSV/TSV read with column types
    READR_READ = re.compile(
        r'(\w+)\s*(?:<-|=)\s*(?:readr::)?(?:read_csv|read_tsv|read_delim|read_csv2)\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # data.table fread
    DT_FREAD = re.compile(
        r'(\w+)\s*(?:<-|=)\s*(?:data\.table::)?fread\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # Arrow/Parquet
    ARROW_READ = re.compile(
        r'(\w+)\s*(?:<-|=)\s*(?:arrow::)?(?:read_parquet|read_feather|open_dataset|read_ipc_stream)\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # sparklyr
    SPARK_READ = re.compile(
        r'(\w+)\s*(?:<-|=)\s*(?:sparklyr::)?(?:spark_read_csv|spark_read_parquet|spark_read_json|spark_read_table|sdf_copy_to)\s*\(',
        re.MULTILINE
    )

    # Driver to database type mapping
    DRIVER_DB_MAP = {
        'RSQLite::SQLite': 'sqlite',
        'SQLite': 'sqlite',
        'RPostgres::Postgres': 'postgresql',
        'Postgres': 'postgresql',
        'RPostgreSQL::PostgreSQL': 'postgresql',
        'RMySQL::MySQL': 'mysql',
        'MySQL': 'mysql',
        'RMariaDB::MariaDB': 'mysql',
        'MariaDB': 'mysql',
        'odbc::odbc': 'odbc',
        'RODBC::RODBC': 'odbc',
        'bigrquery::bigquery': 'bigquery',
        'bigquery': 'bigquery',
        'duckdb::duckdb': 'duckdb',
        'duckdb': 'duckdb',
        'MonetDBLite::MonetDBLite': 'monetdb',
        'clickhouse::clickhouse': 'clickhouse',
    }

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract all R data model definitions from source code."""
        result = {
            "data_models": [],
            "db_connections": [],
            "db_queries": [],
            "data_pipelines": [],
        }

        # Database connections
        result["db_connections"].extend(self._extract_db_connections(content, file_path))

        # Database queries
        result["db_queries"].extend(self._extract_db_queries(content, file_path))

        # Data models (from file reads)
        result["data_models"].extend(self._extract_data_models(content, file_path))

        # Data pipelines (dplyr/data.table chains)
        result["data_pipelines"].extend(self._extract_data_pipelines(content, file_path))

        return result

    def _extract_db_connections(self, content: str, file_path: str) -> List[RDBConnectionInfo]:
        """Extract database connection definitions."""
        connections = []

        # DBI connections
        for m in self.DBI_CONNECT.finditer(content):
            var_name = m.group(1)
            driver = m.group(2).replace('()', '')
            line_num = content[:m.start()].count('\n') + 1

            db_type = self.DRIVER_DB_MAP.get(driver, driver)

            # Try to find database name
            block = content[m.start():m.start() + 500]
            db_m = re.search(r'(?:dbname|database)\s*=\s*["\']([^"\']+)["\']', block)
            host_m = re.search(r'(?:host)\s*=\s*["\']([^"\']+)["\']', block)

            connections.append(RDBConnectionInfo(
                name=var_name,
                driver=db_type,
                database=db_m.group(1) if db_m else "",
                host=host_m.group(1) if host_m else "",
                pool=False,
                file=file_path,
                line_number=line_num,
            ))

        # Pool connections
        for m in self.POOL_CONNECT.finditer(content):
            var_name = m.group(1)
            driver = m.group(2).replace('()', '')
            line_num = content[:m.start()].count('\n') + 1

            db_type = self.DRIVER_DB_MAP.get(driver, driver)

            connections.append(RDBConnectionInfo(
                name=var_name,
                driver=db_type,
                pool=True,
                file=file_path,
                line_number=line_num,
            ))

        return connections

    def _extract_db_queries(self, content: str, file_path: str) -> List[RDBQueryInfo]:
        """Extract database query patterns."""
        queries = []

        for m in self.DB_QUERY.finditer(content):
            conn_var = m.group(1)
            sql = m.group(2).strip()
            line_num = content[:m.start()].count('\n') + 1

            # Determine query type
            query_type = "SELECT"
            sql_upper = sql.upper().strip()
            if sql_upper.startswith("INSERT"):
                query_type = "INSERT"
            elif sql_upper.startswith("UPDATE"):
                query_type = "UPDATE"
            elif sql_upper.startswith("DELETE"):
                query_type = "DELETE"
            elif sql_upper.startswith("CREATE"):
                query_type = "CREATE"

            # Extract table name
            table = ""
            table_m = re.search(r'(?:FROM|INTO|UPDATE|TABLE)\s+["\']?(\w+)', sql, re.IGNORECASE)
            if table_m:
                table = table_m.group(1)

            # Check if parameterized
            is_param = '?' in sql or '$' in sql

            queries.append(RDBQueryInfo(
                name=f"{query_type}:{table}" if table else query_type,
                query_type=query_type,
                table=table,
                connection_var=conn_var,
                is_parameterized=is_param,
                file=file_path,
                line_number=line_num,
            ))

        return queries

    def _extract_data_models(self, content: str, file_path: str) -> List[RDataModelInfo]:
        """Extract data model definitions from file reads."""
        models = []

        # CSV/TSV reads
        for m in self.READR_READ.finditer(content):
            name = m.group(1)
            source = m.group(2)
            line_num = content[:m.start()].count('\n') + 1
            models.append(RDataModelInfo(
                name=name,
                kind="tibble",
                source=source,
                file=file_path,
                line_number=line_num,
            ))

        # data.table fread
        for m in self.DT_FREAD.finditer(content):
            name = m.group(1)
            source = m.group(2)
            line_num = content[:m.start()].count('\n') + 1
            models.append(RDataModelInfo(
                name=name,
                kind="data.table",
                source=source,
                file=file_path,
                line_number=line_num,
            ))

        # Arrow/Parquet
        for m in self.ARROW_READ.finditer(content):
            name = m.group(1)
            source = m.group(2)
            line_num = content[:m.start()].count('\n') + 1
            models.append(RDataModelInfo(
                name=name,
                kind="arrow",
                source=source,
                file=file_path,
                line_number=line_num,
            ))

        # dbplyr tables
        for m in self.DBPLYR_TBL.finditer(content):
            name = m.group(1)
            table = m.group(3)
            line_num = content[:m.start()].count('\n') + 1
            models.append(RDataModelInfo(
                name=name,
                kind="dbplyr",
                source=f"table:{table}",
                file=file_path,
                line_number=line_num,
            ))

        # sparklyr
        for m in self.SPARK_READ.finditer(content):
            name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1
            models.append(RDataModelInfo(
                name=name,
                kind="spark",
                file=file_path,
                line_number=line_num,
            ))

        return models

    def _extract_data_pipelines(self, content: str, file_path: str) -> List[RDataPipelineInfo]:
        """Extract data transformation pipelines."""
        pipelines = []

        # Look for multi-step pipe chains with dplyr verbs
        dplyr_verbs = {'select', 'filter', 'mutate', 'group_by', 'summarize', 'summarise',
                       'arrange', 'slice', 'rename', 'relocate', 'across', 'distinct',
                       'count', 'tally', 'left_join', 'right_join', 'inner_join',
                       'full_join', 'anti_join', 'semi_join', 'bind_rows', 'bind_cols',
                       'pivot_longer', 'pivot_wider', 'unnest', 'nest', 'separate',
                       'unite', 'fill', 'replace_na', 'complete', 'expand'}

        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            # Check for assignment followed by pipe chain
            assign_m = re.match(r'(\w+)\s*(?:<-|=)\s*(\w+)\s*(?:\|>|%>%)', line)
            if assign_m:
                name = assign_m.group(1)
                source = assign_m.group(2)
                steps = []

                # Collect all piped steps
                j = i
                while j < len(lines):
                    current = lines[j]
                    # Extract function calls
                    for verb_m in re.finditer(r'\b(\w+)\s*\(', current):
                        verb = verb_m.group(1)
                        if verb in dplyr_verbs:
                            steps.append(verb)
                    # Check if line continues (ends with pipe or has trailing pipe)
                    if j > i and '|>' not in current and '%>%' not in current:
                        break
                    j += 1

                if len(steps) >= 2:
                    pipelines.append(RDataPipelineInfo(
                        name=name,
                        steps=steps,
                        input_source=source,
                        framework="dplyr",
                        file=file_path,
                        line_number=i + 1,
                    ))

            i += 1

        return pipelines
