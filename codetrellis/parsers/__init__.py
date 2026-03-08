"""
CodeTrellis Parsers - File type specific parsers
==========================================

Each parser knows how to extract structured information
from a specific file type.
"""

from .typescript import TypeScriptParser
from .python_parser import PythonParser
from .proto import ProtoParser
from .angular import AngularParser

__all__ = [
    "TypeScriptParser",
    "PythonParser",
    "ProtoParser",
    "AngularParser",
]
