"""
MLflowExtractor - Extracts MLflow experiment tracking and model registry components.

This extractor parses Python code using MLflow and extracts:
- Experiment configurations
- Run tracking (params, metrics, artifacts)
- Model logging and registry
- Model signatures and input examples
- Autolog configurations

Part of CodeTrellis v2.0 - Python MLOps Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class MLflowExperimentInfo:
    """Information about an MLflow experiment."""
    name: str
    experiment_id: Optional[str] = None
    tracking_uri: Optional[str] = None
    artifact_location: Optional[str] = None
    line_number: int = 0


@dataclass
class MLflowRunInfo:
    """Information about an MLflow run context."""
    run_name: Optional[str] = None
    experiment_name: Optional[str] = None
    nested: bool = False
    tags: Dict[str, str] = field(default_factory=dict)
    line_number: int = 0


@dataclass
class MLflowParamInfo:
    """Information about logged MLflow parameters."""
    params: List[str] = field(default_factory=list)
    param_dict: bool = False  # log_params with dict


@dataclass
class MLflowMetricInfo:
    """Information about logged MLflow metrics."""
    metrics: List[str] = field(default_factory=list)
    step_metrics: List[str] = field(default_factory=list)  # metrics with step


@dataclass
class MLflowModelInfo:
    """Information about logged MLflow models."""
    model_name: str
    flavor: str  # sklearn, pytorch, tensorflow, etc.
    registered_name: Optional[str] = None
    signature: bool = False
    input_example: bool = False
    line_number: int = 0


@dataclass
class MLflowAutologInfo:
    """Information about MLflow autolog configuration."""
    framework: str  # sklearn, pytorch, tensorflow, etc.
    log_models: bool = True
    log_input_examples: bool = False
    silent: bool = False


class MLflowExtractor:
    """
    Extracts MLflow-related components from Python source code.

    Handles:
    - Experiment setup and configuration
    - Run contexts and management
    - Parameter and metric logging
    - Model logging with various flavors
    - Model registry operations
    - Autolog configurations
    """

    # Tracking URI
    TRACKING_URI_PATTERN = re.compile(
        r'mlflow\.set_tracking_uri\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    # Experiment patterns
    SET_EXPERIMENT_PATTERN = re.compile(
        r'mlflow\.set_experiment\s*\(\s*(?:experiment_name\s*=\s*)?[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    CREATE_EXPERIMENT_PATTERN = re.compile(
        r'mlflow\.create_experiment\s*\(\s*(?:name\s*=\s*)?[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    # Run patterns
    START_RUN_PATTERN = re.compile(
        r'(?:with\s+)?mlflow\.start_run\s*\(',
        re.MULTILINE
    )

    RUN_NAME_PATTERN = re.compile(
        r'run_name\s*=\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    NESTED_RUN_PATTERN = re.compile(
        r'nested\s*=\s*True',
        re.MULTILINE
    )

    # Logging patterns
    LOG_PARAM_PATTERN = re.compile(
        r'mlflow\.log_param\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    LOG_PARAMS_PATTERN = re.compile(
        r'mlflow\.log_params\s*\(',
        re.MULTILINE
    )

    LOG_METRIC_PATTERN = re.compile(
        r'mlflow\.log_metric\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    LOG_METRICS_PATTERN = re.compile(
        r'mlflow\.log_metrics\s*\(',
        re.MULTILINE
    )

    LOG_ARTIFACT_PATTERN = re.compile(
        r'mlflow\.log_artifact\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    LOG_ARTIFACTS_PATTERN = re.compile(
        r'mlflow\.log_artifacts\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    # Model logging patterns
    LOG_MODEL_PATTERNS = {
        'sklearn': re.compile(r'mlflow\.sklearn\.log_model\s*\(', re.MULTILINE),
        'pytorch': re.compile(r'mlflow\.pytorch\.log_model\s*\(', re.MULTILINE),
        'tensorflow': re.compile(r'mlflow\.tensorflow\.log_model\s*\(', re.MULTILINE),
        'keras': re.compile(r'mlflow\.keras\.log_model\s*\(', re.MULTILINE),
        'xgboost': re.compile(r'mlflow\.xgboost\.log_model\s*\(', re.MULTILINE),
        'lightgbm': re.compile(r'mlflow\.lightgbm\.log_model\s*\(', re.MULTILINE),
        'transformers': re.compile(r'mlflow\.transformers\.log_model\s*\(', re.MULTILINE),
        'pyfunc': re.compile(r'mlflow\.pyfunc\.log_model\s*\(', re.MULTILINE),
    }

    REGISTERED_MODEL_PATTERN = re.compile(
        r'registered_model_name\s*=\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    SIGNATURE_PATTERN = re.compile(
        r'signature\s*=',
        re.MULTILINE
    )

    INPUT_EXAMPLE_PATTERN = re.compile(
        r'input_example\s*=',
        re.MULTILINE
    )

    # Autolog patterns
    AUTOLOG_PATTERN = re.compile(
        r'mlflow\.(\w+)\.autolog\s*\(',
        re.MULTILINE
    )

    GENERIC_AUTOLOG_PATTERN = re.compile(
        r'mlflow\.autolog\s*\(',
        re.MULTILINE
    )

    # Model registry patterns
    REGISTER_MODEL_PATTERN = re.compile(
        r'mlflow\.register_model\s*\([^)]*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    LOAD_MODEL_PATTERN = re.compile(
        r'mlflow\.(\w+)\.load_model\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    # Tags
    SET_TAG_PATTERN = re.compile(
        r'mlflow\.set_tag\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the MLflow extractor."""
        pass

    def extract(self, content: str) -> Dict[str, Any]:
        """
        Extract all MLflow components from Python content.

        Args:
            content: Python source code

        Returns:
            Dict with experiments, runs, params, metrics, models, autologs
        """
        experiments = self._extract_experiments(content)
        runs = self._extract_runs(content)
        params = self._extract_params(content)
        metrics = self._extract_metrics(content)
        models = self._extract_models(content)
        autologs = self._extract_autologs(content)
        artifacts = self._extract_artifacts(content)

        return {
            'experiments': experiments,
            'runs': runs,
            'params': params,
            'metrics': metrics,
            'models': models,
            'autologs': autologs,
            'artifacts': artifacts
        }

    def _extract_experiments(self, content: str) -> List[MLflowExperimentInfo]:
        """Extract MLflow experiment configurations."""
        experiments = []

        # Tracking URI
        tracking_uri = None
        uri_match = self.TRACKING_URI_PATTERN.search(content)
        if uri_match:
            tracking_uri = uri_match.group(1)

        # Set experiment
        for match in self.SET_EXPERIMENT_PATTERN.finditer(content):
            exp_name = match.group(1)
            experiments.append(MLflowExperimentInfo(
                name=exp_name,
                tracking_uri=tracking_uri,
                line_number=content[:match.start()].count('\n') + 1
            ))

        # Create experiment
        for match in self.CREATE_EXPERIMENT_PATTERN.finditer(content):
            exp_name = match.group(1)
            context = content[match.start():match.start()+300]

            artifact_loc = None
            loc_match = re.search(r'artifact_location\s*=\s*[\'"]([^"\']+)[\'"]', context)
            if loc_match:
                artifact_loc = loc_match.group(1)

            experiments.append(MLflowExperimentInfo(
                name=exp_name,
                tracking_uri=tracking_uri,
                artifact_location=artifact_loc,
                line_number=content[:match.start()].count('\n') + 1
            ))

        return experiments

    def _extract_runs(self, content: str) -> List[MLflowRunInfo]:
        """Extract MLflow run contexts."""
        runs = []

        for match in self.START_RUN_PATTERN.finditer(content):
            context = content[match.start():match.start()+200]

            run_name = None
            name_match = self.RUN_NAME_PATTERN.search(context)
            if name_match:
                run_name = name_match.group(1)

            nested = bool(self.NESTED_RUN_PATTERN.search(context))

            runs.append(MLflowRunInfo(
                run_name=run_name,
                nested=nested,
                line_number=content[:match.start()].count('\n') + 1
            ))

        return runs

    def _extract_params(self, content: str) -> MLflowParamInfo:
        """Extract logged parameters."""
        params = []
        param_dict = False

        for match in self.LOG_PARAM_PATTERN.finditer(content):
            params.append(match.group(1))

        if self.LOG_PARAMS_PATTERN.search(content):
            param_dict = True

        return MLflowParamInfo(
            params=params,
            param_dict=param_dict
        )

    def _extract_metrics(self, content: str) -> MLflowMetricInfo:
        """Extract logged metrics."""
        metrics = []
        step_metrics = []

        for match in self.LOG_METRIC_PATTERN.finditer(content):
            metric_name = match.group(1)
            context = content[match.start():match.start()+100]

            if 'step=' in context or 'step =' in context:
                step_metrics.append(metric_name)
            else:
                metrics.append(metric_name)

        return MLflowMetricInfo(
            metrics=metrics,
            step_metrics=step_metrics
        )

    def _extract_models(self, content: str) -> List[MLflowModelInfo]:
        """Extract logged and registered models."""
        models = []

        for flavor, pattern in self.LOG_MODEL_PATTERNS.items():
            for match in pattern.finditer(content):
                context = content[match.start():match.start()+300]

                # Check for registered model name
                registered_name = None
                reg_match = self.REGISTERED_MODEL_PATTERN.search(context)
                if reg_match:
                    registered_name = reg_match.group(1)

                # Check for signature
                has_signature = bool(self.SIGNATURE_PATTERN.search(context))

                # Check for input example
                has_input_example = bool(self.INPUT_EXAMPLE_PATTERN.search(context))

                models.append(MLflowModelInfo(
                    model_name=f"{flavor}_model",
                    flavor=flavor,
                    registered_name=registered_name,
                    signature=has_signature,
                    input_example=has_input_example,
                    line_number=content[:match.start()].count('\n') + 1
                ))

        return models

    def _extract_autologs(self, content: str) -> List[MLflowAutologInfo]:
        """Extract autolog configurations."""
        autologs = []

        # Framework-specific autologs
        for match in self.AUTOLOG_PATTERN.finditer(content):
            framework = match.group(1)
            context = content[match.start():match.start()+200]

            log_models = 'log_models=False' not in context
            log_input_examples = 'log_input_examples=True' in context
            silent = 'silent=True' in context

            autologs.append(MLflowAutologInfo(
                framework=framework,
                log_models=log_models,
                log_input_examples=log_input_examples,
                silent=silent
            ))

        # Generic autolog
        for match in self.GENERIC_AUTOLOG_PATTERN.finditer(content):
            autologs.append(MLflowAutologInfo(
                framework="all",
                log_models=True
            ))

        return autologs

    def _extract_artifacts(self, content: str) -> List[str]:
        """Extract logged artifacts."""
        artifacts = []

        for match in self.LOG_ARTIFACT_PATTERN.finditer(content):
            artifacts.append(match.group(1))

        for match in self.LOG_ARTIFACTS_PATTERN.finditer(content):
            artifacts.append(match.group(1) + "/")  # Directory

        return artifacts

    def to_codetrellis_format(self, result: Dict[str, Any]) -> str:
        """Convert extracted MLflow data to CodeTrellis format."""
        lines = []

        # Experiments
        experiments = result.get('experiments', [])
        if experiments:
            lines.append("[MLFLOW_EXPERIMENTS]")
            for exp in experiments:
                parts = [exp.name]
                if exp.tracking_uri:
                    parts.append(f"uri:{exp.tracking_uri}")
                lines.append("|".join(parts))
            lines.append("")

        # Runs
        runs = result.get('runs', [])
        if runs:
            lines.append("[MLFLOW_RUNS]")
            for run in runs:
                parts = [run.run_name or "unnamed"]
                if run.nested:
                    parts.append("nested")
                lines.append("|".join(parts))
            lines.append("")

        # Parameters
        params = result.get('params', MLflowParamInfo())
        if params.params or params.param_dict:
            lines.append("[MLFLOW_PARAMS]")
            if params.params:
                lines.append(f"logged:[{','.join(params.params[:10])}]")
            if params.param_dict:
                lines.append("batch_logging:true")
            lines.append("")

        # Metrics
        metrics = result.get('metrics', MLflowMetricInfo())
        if metrics.metrics or metrics.step_metrics:
            lines.append("[MLFLOW_METRICS]")
            if metrics.metrics:
                lines.append(f"scalar:[{','.join(metrics.metrics[:10])}]")
            if metrics.step_metrics:
                lines.append(f"stepped:[{','.join(metrics.step_metrics[:10])}]")
            lines.append("")

        # Models
        models = result.get('models', [])
        if models:
            lines.append("[MLFLOW_MODELS]")
            for model in models:
                parts = [model.flavor]
                if model.registered_name:
                    parts.append(f"registry:{model.registered_name}")
                if model.signature:
                    parts.append("signature")
                if model.input_example:
                    parts.append("input_example")
                lines.append("|".join(parts))
            lines.append("")

        # Autologs
        autologs = result.get('autologs', [])
        if autologs:
            lines.append("[MLFLOW_AUTOLOG]")
            for auto in autologs:
                parts = [auto.framework]
                if not auto.log_models:
                    parts.append("no_models")
                if auto.log_input_examples:
                    parts.append("input_examples")
                lines.append("|".join(parts))

        return "\n".join(lines)


# Convenience function
def extract_mlflow(content: str) -> Dict[str, Any]:
    """Extract MLflow components from Python content."""
    extractor = MLflowExtractor()
    return extractor.extract(content)
