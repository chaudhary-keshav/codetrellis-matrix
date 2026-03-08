"""
Data Processing Extractors for Python.

This module provides extractors for data processing libraries:
- Pandas (DataFrames, I/O, Transformations)
- Data Pipelines (Airflow, Prefect, Dagster, Luigi)

Part of CodeTrellis v2.0 - Python Data Engineering Support
"""

from .pandas_extractor import PandasExtractor, extract_pandas
from .pipeline_extractor import DataPipelineExtractor, extract_data_pipeline

__all__ = [
    # Pandas
    'PandasExtractor',
    'extract_pandas',

    # Pipelines
    'DataPipelineExtractor',
    'extract_data_pipeline',
]
