"""
DataPipelineExtractor - Extracts data pipeline definitions and components.

This extractor parses Python code for data pipeline patterns:
- Airflow DAGs and tasks
- Prefect flows and tasks
- Luigi pipelines
- Dagster assets and jobs
- Generic ETL patterns

Part of CodeTrellis v2.0 - Python Data Engineering Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class AirflowDAGInfo:
    """Information about an Airflow DAG."""
    dag_id: str
    schedule: Optional[str] = None
    default_args: Dict[str, Any] = field(default_factory=dict)
    tasks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # task1 >> task2
    line_number: int = 0


@dataclass
class AirflowTaskInfo:
    """Information about an Airflow task."""
    task_id: str
    operator: str  # PythonOperator, BashOperator, etc.
    dag: Optional[str] = None
    python_callable: Optional[str] = None
    params: List[str] = field(default_factory=list)


@dataclass
class PrefectFlowInfo:
    """Information about a Prefect flow."""
    name: str
    function_name: str
    tasks: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class PrefectTaskInfo:
    """Information about a Prefect task."""
    name: str
    function_name: str
    retries: Optional[int] = None
    cache_key_fn: Optional[str] = None


@dataclass
class DagsterAssetInfo:
    """Information about a Dagster asset."""
    name: str
    function_name: str
    deps: List[str] = field(default_factory=list)
    group_name: Optional[str] = None
    io_manager: Optional[str] = None


@dataclass
class ETLStepInfo:
    """Generic ETL step information."""
    name: str
    step_type: str  # extract, transform, load
    source: Optional[str] = None
    destination: Optional[str] = None
    operations: List[str] = field(default_factory=list)


class DataPipelineExtractor:
    """
    Extracts data pipeline components from Python source code.

    Handles:
    - Apache Airflow DAGs and operators
    - Prefect flows and tasks
    - Dagster assets, ops, and jobs
    - Luigi tasks and dependencies
    - Generic ETL patterns
    """

    # Airflow patterns
    AIRFLOW_DAG_PATTERN = re.compile(
        r'(?:with\s+)?DAG\s*\(\s*(?:dag_id\s*=\s*)?[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    AIRFLOW_DAG_CONTEXT_PATTERN = re.compile(
        r'with\s+DAG\s*\([^)]+\)\s+as\s+(\w+)\s*:',
        re.MULTILINE
    )

    AIRFLOW_SCHEDULE_PATTERN = re.compile(
        r'schedule(?:_interval)?\s*=\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    AIRFLOW_OPERATOR_PATTERN = re.compile(
        r'(\w+)\s*=\s*(\w+Operator)\s*\(\s*task_id\s*=\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    AIRFLOW_PYTHON_OP_PATTERN = re.compile(
        r'(\w+)\s*=\s*PythonOperator\s*\([^)]*python_callable\s*=\s*(\w+)',
        re.MULTILINE
    )

    AIRFLOW_DEPENDENCY_PATTERN = re.compile(
        r'(\w+)\s*>>\s*(\w+)',
        re.MULTILINE
    )

    AIRFLOW_TASKFLOW_PATTERN = re.compile(
        r'@task(?:\([^)]*\))?\s*\n\s*def\s+(\w+)',
        re.MULTILINE
    )

    # Prefect patterns
    PREFECT_FLOW_PATTERN = re.compile(
        r'@flow(?:\([^)]*\))?\s*\n\s*def\s+(\w+)',
        re.MULTILINE
    )

    PREFECT_TASK_PATTERN = re.compile(
        r'@task(?:\([^)]*\))?\s*\n\s*def\s+(\w+)',
        re.MULTILINE
    )

    PREFECT_FLOW_NAME_PATTERN = re.compile(
        r'@flow\s*\(\s*name\s*=\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    PREFECT_RETRIES_PATTERN = re.compile(
        r'@task\s*\([^)]*retries\s*=\s*(\d+)',
        re.MULTILINE
    )

    # Dagster patterns
    DAGSTER_ASSET_PATTERN = re.compile(
        r'@asset(?:\([^)]*\))?\s*\n\s*def\s+(\w+)',
        re.MULTILINE
    )

    DAGSTER_OP_PATTERN = re.compile(
        r'@op(?:\([^)]*\))?\s*\n\s*def\s+(\w+)',
        re.MULTILINE
    )

    DAGSTER_JOB_PATTERN = re.compile(
        r'@job(?:\([^)]*\))?\s*\n\s*def\s+(\w+)',
        re.MULTILINE
    )

    DAGSTER_ASSET_DEPS_PATTERN = re.compile(
        r'@asset\s*\([^)]*deps\s*=\s*\[([^\]]+)\]',
        re.MULTILINE
    )

    # Luigi patterns
    LUIGI_TASK_PATTERN = re.compile(
        r'class\s+(\w+)\s*\(\s*luigi\.Task\s*\)',
        re.MULTILINE
    )

    LUIGI_REQUIRES_PATTERN = re.compile(
        r'def\s+requires\s*\([^)]*\)\s*:\s*\n\s*return\s+(\w+)',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the data pipeline extractor."""
        pass

    def extract(self, content: str) -> Dict[str, Any]:
        """
        Extract all data pipeline components from Python content.

        Args:
            content: Python source code

        Returns:
            Dict with airflow, prefect, dagster, luigi, etl_steps
        """
        airflow = self._extract_airflow(content)
        prefect = self._extract_prefect(content)
        dagster = self._extract_dagster(content)
        luigi = self._extract_luigi(content)
        etl_steps = self._extract_etl_patterns(content)

        return {
            'airflow': airflow,
            'prefect': prefect,
            'dagster': dagster,
            'luigi': luigi,
            'etl_steps': etl_steps
        }

    def _extract_airflow(self, content: str) -> Dict[str, Any]:
        """Extract Airflow DAG and task definitions."""
        dags = []
        tasks = []

        # DAGs
        for match in self.AIRFLOW_DAG_PATTERN.finditer(content):
            dag_id = match.group(1)
            context = content[match.start():match.start()+500]

            schedule = None
            sched_match = self.AIRFLOW_SCHEDULE_PATTERN.search(context)
            if sched_match:
                schedule = sched_match.group(1)

            dags.append(AirflowDAGInfo(
                dag_id=dag_id,
                schedule=schedule,
                line_number=content[:match.start()].count('\n') + 1
            ))

        # Regular operators
        for match in self.AIRFLOW_OPERATOR_PATTERN.finditer(content):
            var_name = match.group(1)
            operator = match.group(2)
            task_id = match.group(3)

            task = AirflowTaskInfo(
                task_id=task_id,
                operator=operator
            )

            # Get python_callable for PythonOperator
            if operator == 'PythonOperator':
                callable_match = re.search(
                    rf'{var_name}\s*=\s*PythonOperator\s*\([^)]*python_callable\s*=\s*(\w+)',
                    content
                )
                if callable_match:
                    task.python_callable = callable_match.group(1)

            tasks.append(task)

        # TaskFlow API tasks
        for match in self.AIRFLOW_TASKFLOW_PATTERN.finditer(content):
            func_name = match.group(1)
            tasks.append(AirflowTaskInfo(
                task_id=func_name,
                operator="@task",
                python_callable=func_name
            ))

        # Dependencies
        dependencies = []
        for match in self.AIRFLOW_DEPENDENCY_PATTERN.finditer(content):
            upstream = match.group(1)
            downstream = match.group(2)
            dependencies.append(f"{upstream}>>{downstream}")

        return {
            'dags': dags,
            'tasks': tasks,
            'dependencies': dependencies
        }

    def _extract_prefect(self, content: str) -> Dict[str, Any]:
        """Extract Prefect flow and task definitions."""
        flows = []
        tasks = []

        # Flows
        for match in self.PREFECT_FLOW_PATTERN.finditer(content):
            func_name = match.group(1)

            # Try to get flow name from decorator
            name = func_name
            name_match = self.PREFECT_FLOW_NAME_PATTERN.search(content[:match.start()+100])
            if name_match:
                name = name_match.group(1)

            flows.append(PrefectFlowInfo(
                name=name,
                function_name=func_name,
                line_number=content[:match.start()].count('\n') + 1
            ))

        # Tasks
        for match in self.PREFECT_TASK_PATTERN.finditer(content):
            func_name = match.group(1)

            # Check for retries
            retries = None
            context = content[max(0, match.start()-100):match.start()]
            retry_match = self.PREFECT_RETRIES_PATTERN.search(context)
            if retry_match:
                retries = int(retry_match.group(1))

            tasks.append(PrefectTaskInfo(
                name=func_name,
                function_name=func_name,
                retries=retries
            ))

        return {
            'flows': flows,
            'tasks': tasks
        }

    def _extract_dagster(self, content: str) -> Dict[str, Any]:
        """Extract Dagster asset and op definitions."""
        assets = []
        ops = []
        jobs = []

        # Assets
        for match in self.DAGSTER_ASSET_PATTERN.finditer(content):
            func_name = match.group(1)

            # Check for dependencies
            deps = []
            context = content[max(0, match.start()-200):match.start()+50]
            deps_match = self.DAGSTER_ASSET_DEPS_PATTERN.search(context)
            if deps_match:
                deps_str = deps_match.group(1)
                deps = [d.strip().strip('"\'') for d in deps_str.split(',')]

            assets.append(DagsterAssetInfo(
                name=func_name,
                function_name=func_name,
                deps=deps
            ))

        # Ops
        for match in self.DAGSTER_OP_PATTERN.finditer(content):
            func_name = match.group(1)
            ops.append({
                'name': func_name,
                'function_name': func_name
            })

        # Jobs
        for match in self.DAGSTER_JOB_PATTERN.finditer(content):
            func_name = match.group(1)
            jobs.append({
                'name': func_name,
                'function_name': func_name
            })

        return {
            'assets': assets,
            'ops': ops,
            'jobs': jobs
        }

    def _extract_luigi(self, content: str) -> Dict[str, Any]:
        """Extract Luigi task definitions."""
        tasks = []

        for match in self.LUIGI_TASK_PATTERN.finditer(content):
            task_name = match.group(1)
            class_body = self._extract_class_body(content, match.end())

            # Check for requires
            deps = []
            req_match = self.LUIGI_REQUIRES_PATTERN.search(class_body)
            if req_match:
                deps.append(req_match.group(1))

            tasks.append({
                'name': task_name,
                'dependencies': deps
            })

        return {'tasks': tasks}

    def _extract_etl_patterns(self, content: str) -> List[ETLStepInfo]:
        """Extract generic ETL patterns."""
        steps = []

        # Look for functions named extract_, transform_, load_
        etl_func_pattern = re.compile(
            r'def\s+(extract|transform|load)_(\w+)\s*\(',
            re.MULTILINE
        )

        for match in etl_func_pattern.finditer(content):
            step_type = match.group(1)
            name = match.group(2)

            steps.append(ETLStepInfo(
                name=f"{step_type}_{name}",
                step_type=step_type
            ))

        return steps

    def _extract_class_body(self, content: str, start: int) -> str:
        """Extract class body starting from position."""
        lines = content[start:].split('\n')
        body_lines = []
        indent = None

        for line in lines:
            if not line.strip():
                body_lines.append(line)
                continue

            current_spaces = len(line) - len(line.lstrip())

            if indent is None:
                if current_spaces > 0:
                    indent = current_spaces
                else:
                    break

            if line.strip() and current_spaces < indent:
                break

            body_lines.append(line)

        return '\n'.join(body_lines)

    def to_codetrellis_format(self, result: Dict[str, Any]) -> str:
        """Convert extracted pipeline data to CodeTrellis format."""
        lines = []

        # Airflow
        airflow = result.get('airflow', {})
        if airflow.get('dags') or airflow.get('tasks'):
            lines.append("[AIRFLOW_DAGS]")
            for dag in airflow.get('dags', []):
                parts = [dag.dag_id]
                if dag.schedule:
                    parts.append(f"schedule:{dag.schedule}")
                lines.append("|".join(parts))

            if airflow.get('tasks'):
                lines.append("")
                lines.append("[AIRFLOW_TASKS]")
                for task in airflow.get('tasks', []):
                    parts = [task.task_id, f"op:{task.operator}"]
                    if task.python_callable:
                        parts.append(f"callable:{task.python_callable}")
                    lines.append("|".join(parts))

            if airflow.get('dependencies'):
                lines.append("")
                lines.append("[AIRFLOW_DEPS]")
                for dep in airflow.get('dependencies', []):
                    lines.append(dep)
            lines.append("")

        # Prefect
        prefect = result.get('prefect', {})
        if prefect.get('flows') or prefect.get('tasks'):
            lines.append("[PREFECT_FLOWS]")
            for flow in prefect.get('flows', []):
                lines.append(f"{flow.name}|fn:{flow.function_name}")

            if prefect.get('tasks'):
                lines.append("")
                lines.append("[PREFECT_TASKS]")
                for task in prefect.get('tasks', []):
                    parts = [task.name]
                    if task.retries:
                        parts.append(f"retries:{task.retries}")
                    lines.append("|".join(parts))
            lines.append("")

        # Dagster
        dagster = result.get('dagster', {})
        if dagster.get('assets') or dagster.get('ops') or dagster.get('jobs'):
            if dagster.get('assets'):
                lines.append("[DAGSTER_ASSETS]")
                for asset in dagster.get('assets', []):
                    parts = [asset.name]
                    if asset.deps:
                        parts.append(f"deps:[{','.join(asset.deps)}]")
                    lines.append("|".join(parts))
                lines.append("")

            if dagster.get('jobs'):
                lines.append("[DAGSTER_JOBS]")
                for job in dagster.get('jobs', []):
                    lines.append(job['name'])
                lines.append("")

        # Luigi
        luigi = result.get('luigi', {})
        if luigi.get('tasks'):
            lines.append("[LUIGI_TASKS]")
            for task in luigi.get('tasks', []):
                parts = [task['name']]
                if task.get('dependencies'):
                    parts.append(f"requires:[{','.join(task['dependencies'])}]")
                lines.append("|".join(parts))
            lines.append("")

        # ETL steps
        etl_steps = result.get('etl_steps', [])
        if etl_steps:
            lines.append("[ETL_STEPS]")
            for step in etl_steps:
                lines.append(f"{step.name}|type:{step.step_type}")

        return "\n".join(lines)


# Convenience function
def extract_data_pipeline(content: str) -> Dict[str, Any]:
    """Extract data pipeline components from Python content."""
    extractor = DataPipelineExtractor()
    return extractor.extract(content)
