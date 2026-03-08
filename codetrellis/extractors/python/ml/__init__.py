"""
ML/AI Extractors for Python.

This module provides extractors for machine learning and AI frameworks:
- PyTorch (nn.Module, Training Loops, Layers, Optimizers)
- HuggingFace Transformers (Models, Tokenizers, Trainers, Datasets)
- LangChain (Chains, Agents, Tools, Prompts, Memory)

Part of CodeTrellis v2.0 - Python AI/ML Lifecycle Support
"""

from .pytorch_extractor import PyTorchExtractor, extract_pytorch
from .huggingface_extractor import HuggingFaceExtractor, extract_huggingface
from .langchain_extractor import LangChainExtractor, extract_langchain

__all__ = [
    # PyTorch
    'PyTorchExtractor',
    'extract_pytorch',

    # HuggingFace
    'HuggingFaceExtractor',
    'extract_huggingface',

    # LangChain
    'LangChainExtractor',
    'extract_langchain',
]
