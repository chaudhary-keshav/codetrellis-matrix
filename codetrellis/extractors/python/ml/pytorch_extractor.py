"""
PyTorchExtractor - Extracts PyTorch model definitions and training components.

This extractor parses PyTorch code and extracts:
- nn.Module definitions with layers
- Forward pass signatures
- Loss functions
- Optimizers
- DataLoader configurations
- Training loops (Lightning modules)
- Model checkpoints

Part of CodeTrellis v2.0 - Python AI/ML Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class LayerType(Enum):
    """Types of neural network layers."""
    LINEAR = "Linear"
    CONV1D = "Conv1d"
    CONV2D = "Conv2d"
    CONV3D = "Conv3d"
    LSTM = "LSTM"
    GRU = "GRU"
    TRANSFORMER = "Transformer"
    ATTENTION = "Attention"
    BATCHNORM = "BatchNorm"
    LAYERNORM = "LayerNorm"
    DROPOUT = "Dropout"
    EMBEDDING = "Embedding"
    POOLING = "Pool"
    ACTIVATION = "Activation"
    CUSTOM = "Custom"


@dataclass
class LayerInfo:
    """Information about a neural network layer."""
    name: str
    layer_type: str
    params: Dict[str, Any] = field(default_factory=dict)
    input_shape: Optional[str] = None
    output_shape: Optional[str] = None


@dataclass
class ForwardSignature:
    """Information about the forward method signature."""
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    return_type: Optional[str] = None


@dataclass
class PyTorchModelInfo:
    """Complete information about a PyTorch model."""
    name: str
    base_class: str = "nn.Module"
    layers: List[LayerInfo] = field(default_factory=list)
    forward_signature: Optional[ForwardSignature] = None
    is_sequential: bool = False
    is_lightning: bool = False
    parameters_count: Optional[str] = None
    docstring: Optional[str] = None
    line_number: int = 0


@dataclass
class DataLoaderInfo:
    """Information about a DataLoader configuration."""
    name: str
    dataset: str
    batch_size: Optional[int] = None
    shuffle: bool = False
    num_workers: int = 0
    pin_memory: bool = False
    collate_fn: Optional[str] = None


@dataclass
class TrainingConfig:
    """Information about training configuration."""
    optimizer: Optional[str] = None
    optimizer_params: Dict[str, Any] = field(default_factory=dict)
    loss_function: Optional[str] = None
    learning_rate: Optional[float] = None
    scheduler: Optional[str] = None
    epochs: Optional[int] = None
    device: str = "cpu"


@dataclass
class LightningModuleInfo:
    """Information about a PyTorch Lightning module."""
    name: str
    model: Optional[str] = None
    training_step: bool = False
    validation_step: bool = False
    test_step: bool = False
    configure_optimizers: bool = False
    callbacks: List[str] = field(default_factory=list)


class PyTorchExtractor:
    """
    Extracts PyTorch model definitions and training components.

    Handles:
    - nn.Module subclasses
    - nn.Sequential models
    - Layer definitions (Linear, Conv, LSTM, etc.)
    - Forward pass analysis
    - PyTorch Lightning modules
    - DataLoader configurations
    - Training loop patterns
    """

    # Pattern for nn.Module class
    MODULE_PATTERN = re.compile(
        r'class\s+(\w+)\s*\(\s*(nn\.Module|LightningModule|pl\.LightningModule|L\.LightningModule)\s*\)\s*:',
        re.MULTILINE
    )

    # Pattern for layer definitions
    LAYER_PATTERN = re.compile(
        r'self\.(\w+)\s*=\s*nn\.(\w+)\s*\(\s*([^)]*)\s*\)',
        re.MULTILINE
    )

    # Pattern for Sequential model
    SEQUENTIAL_PATTERN = re.compile(
        r'(\w+)\s*=\s*nn\.Sequential\s*\(\s*([^)]*(?:\([^)]*\)[^)]*)*)\s*\)',
        re.MULTILINE | re.DOTALL
    )

    # Pattern for forward method
    FORWARD_PATTERN = re.compile(
        r'def\s+forward\s*\(\s*self\s*,?\s*([^)]*)\s*\)(?:\s*->\s*([^:]+))?\s*:',
        re.MULTILINE
    )

    # Pattern for DataLoader
    DATALOADER_PATTERN = re.compile(
        r'(\w+)\s*=\s*(?:torch\.utils\.data\.)?DataLoader\s*\(\s*([^)]*(?:\([^)]*\)[^)]*)*)\s*\)',
        re.MULTILINE | re.DOTALL
    )

    # Pattern for optimizer
    OPTIMIZER_PATTERN = re.compile(
        r'(\w+)\s*=\s*(?:torch\.optim\.|optim\.)(\w+)\s*\(\s*([^)]*)\s*\)',
        re.MULTILINE
    )

    # Pattern for loss function
    LOSS_PATTERN = re.compile(
        r'(\w+)\s*=\s*nn\.(\w*Loss\w*)\s*\(\s*([^)]*)\s*\)',
        re.MULTILINE
    )

    # Lightning-specific patterns
    TRAINING_STEP_PATTERN = re.compile(r'def\s+training_step\s*\(')
    VALIDATION_STEP_PATTERN = re.compile(r'def\s+validation_step\s*\(')
    TEST_STEP_PATTERN = re.compile(r'def\s+test_step\s*\(')
    CONFIGURE_OPTIMIZERS_PATTERN = re.compile(r'def\s+configure_optimizers\s*\(')

    def __init__(self):
        """Initialize the PyTorch extractor."""
        pass

    def extract(self, content: str) -> Dict[str, Any]:
        """
        Extract all PyTorch components from Python content.

        Args:
            content: Python source code

        Returns:
            Dict with models, dataloaders, training configs
        """
        models = self._extract_models(content)
        dataloaders = self._extract_dataloaders(content)
        training = self._extract_training_config(content)
        lightning = self._extract_lightning_modules(content)

        return {
            'models': models,
            'dataloaders': dataloaders,
            'training': training,
            'lightning_modules': lightning
        }

    def _extract_models(self, content: str) -> List[PyTorchModelInfo]:
        """Extract nn.Module definitions."""
        models = []

        for match in self.MODULE_PATTERN.finditer(content):
            model_name = match.group(1)
            base_class = match.group(2)

            # Extract class body
            class_start = match.end()
            class_body = self._extract_class_body(content, class_start)

            # Extract layers
            layers = self._extract_layers(class_body)

            # Extract forward signature
            forward_sig = self._extract_forward_signature(class_body)

            # Check if Lightning
            is_lightning = 'Lightning' in base_class

            line_number = content[:match.start()].count('\n') + 1

            model = PyTorchModelInfo(
                name=model_name,
                base_class=base_class,
                layers=layers,
                forward_signature=forward_sig,
                is_lightning=is_lightning,
                line_number=line_number
            )

            models.append(model)

        # Also extract Sequential models
        for match in self.SEQUENTIAL_PATTERN.finditer(content):
            model_name = match.group(1)
            seq_content = match.group(2)

            layers = self._extract_sequential_layers(seq_content)

            models.append(PyTorchModelInfo(
                name=model_name,
                base_class="nn.Sequential",
                layers=layers,
                is_sequential=True,
                line_number=content[:match.start()].count('\n') + 1
            ))

        return models

    def _extract_layers(self, class_body: str) -> List[LayerInfo]:
        """Extract layer definitions from __init__."""
        layers = []

        for match in self.LAYER_PATTERN.finditer(class_body):
            layer_name = match.group(1)
            layer_type = match.group(2)
            layer_params = match.group(3)

            params = self._parse_layer_params(layer_type, layer_params)

            layers.append(LayerInfo(
                name=layer_name,
                layer_type=layer_type,
                params=params
            ))

        return layers

    def _extract_sequential_layers(self, seq_content: str) -> List[LayerInfo]:
        """Extract layers from nn.Sequential definition."""
        layers = []

        # Find all nn.Layer() calls
        layer_calls = re.findall(r'nn\.(\w+)\s*\(\s*([^)]*)\s*\)', seq_content)

        for i, (layer_type, params_str) in enumerate(layer_calls):
            params = self._parse_layer_params(layer_type, params_str)
            layers.append(LayerInfo(
                name=f"layer_{i}",
                layer_type=layer_type,
                params=params
            ))

        return layers

    def _parse_layer_params(self, layer_type: str, params_str: str) -> Dict[str, Any]:
        """Parse layer parameters."""
        params = {}

        # Common patterns based on layer type
        if layer_type == 'Linear':
            match = re.match(r'(\d+)\s*,\s*(\d+)', params_str)
            if match:
                params['in_features'] = int(match.group(1))
                params['out_features'] = int(match.group(2))

        elif layer_type in ('Conv1d', 'Conv2d', 'Conv3d'):
            match = re.match(r'(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', params_str)
            if match:
                params['in_channels'] = int(match.group(1))
                params['out_channels'] = int(match.group(2))
                params['kernel_size'] = int(match.group(3))

        elif layer_type in ('LSTM', 'GRU'):
            match = re.match(r'(\d+)\s*,\s*(\d+)', params_str)
            if match:
                params['input_size'] = int(match.group(1))
                params['hidden_size'] = int(match.group(2))
            if 'num_layers' in params_str:
                layers_match = re.search(r'num_layers\s*=\s*(\d+)', params_str)
                if layers_match:
                    params['num_layers'] = int(layers_match.group(1))

        elif layer_type == 'Embedding':
            match = re.match(r'(\d+)\s*,\s*(\d+)', params_str)
            if match:
                params['num_embeddings'] = int(match.group(1))
                params['embedding_dim'] = int(match.group(2))

        elif layer_type == 'Dropout':
            match = re.match(r'([\d.]+)', params_str)
            if match:
                params['p'] = float(match.group(1))

        return params

    def _extract_forward_signature(self, class_body: str) -> Optional[ForwardSignature]:
        """Extract forward method signature."""
        match = self.FORWARD_PATTERN.search(class_body)
        if not match:
            return None

        params_str = match.group(1)
        return_type = match.group(2)

        # Parse input parameters
        inputs = []
        for param in params_str.split(','):
            param = param.strip()
            if param and param != 'self':
                if ':' in param:
                    name = param.split(':')[0].strip()
                else:
                    name = param.split('=')[0].strip()
                inputs.append(name)

        return ForwardSignature(
            inputs=inputs,
            return_type=return_type.strip() if return_type else None
        )

    def _extract_dataloaders(self, content: str) -> List[DataLoaderInfo]:
        """Extract DataLoader configurations."""
        dataloaders = []

        for match in self.DATALOADER_PATTERN.finditer(content):
            loader_name = match.group(1)
            loader_args = match.group(2)

            # Parse arguments
            dataset = self._extract_first_arg(loader_args)
            batch_size = self._extract_kwarg_int(loader_args, 'batch_size')
            shuffle = 'shuffle=True' in loader_args or 'shuffle = True' in loader_args
            num_workers = self._extract_kwarg_int(loader_args, 'num_workers') or 0
            pin_memory = 'pin_memory=True' in loader_args

            dataloaders.append(DataLoaderInfo(
                name=loader_name,
                dataset=dataset,
                batch_size=batch_size,
                shuffle=shuffle,
                num_workers=num_workers,
                pin_memory=pin_memory
            ))

        return dataloaders

    def _extract_training_config(self, content: str) -> TrainingConfig:
        """Extract training configuration."""
        config = TrainingConfig()

        # Extract optimizer
        for match in self.OPTIMIZER_PATTERN.finditer(content):
            config.optimizer = match.group(2)
            opt_args = match.group(3)

            # Extract learning rate
            lr_match = re.search(r'lr\s*=\s*([\d.e-]+)', opt_args)
            if lr_match:
                config.learning_rate = float(lr_match.group(1))

        # Extract loss function
        for match in self.LOSS_PATTERN.finditer(content):
            config.loss_function = match.group(2)

        # Extract device
        if 'cuda' in content.lower():
            config.device = 'cuda'
        elif 'mps' in content.lower():
            config.device = 'mps'

        return config

    def _extract_lightning_modules(self, content: str) -> List[LightningModuleInfo]:
        """Extract PyTorch Lightning specific information."""
        modules = []

        for match in self.MODULE_PATTERN.finditer(content):
            if 'Lightning' in match.group(2):
                module_name = match.group(1)
                class_body = self._extract_class_body(content, match.end())

                module = LightningModuleInfo(
                    name=module_name,
                    training_step=bool(self.TRAINING_STEP_PATTERN.search(class_body)),
                    validation_step=bool(self.VALIDATION_STEP_PATTERN.search(class_body)),
                    test_step=bool(self.TEST_STEP_PATTERN.search(class_body)),
                    configure_optimizers=bool(self.CONFIGURE_OPTIMIZERS_PATTERN.search(class_body))
                )

                # Extract callbacks from Trainer
                callbacks = re.findall(r'(\w+Callback)', content)
                module.callbacks = list(set(callbacks))

                modules.append(module)

        return modules

    def _extract_class_body(self, content: str, start: int) -> str:
        """Extract class body from content."""
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

    def _extract_first_arg(self, args_str: str) -> str:
        """Extract first positional argument."""
        # Split by comma, handling nested parentheses
        depth = 0
        current = ""
        for char in args_str:
            if char in '([{':
                depth += 1
            elif char in ')]}':
                depth -= 1
            elif char == ',' and depth == 0:
                break
            current += char
        return current.strip()

    def _extract_kwarg_int(self, args_str: str, key: str) -> Optional[int]:
        """Extract integer keyword argument."""
        match = re.search(rf'{key}\s*=\s*(\d+)', args_str)
        if match:
            return int(match.group(1))
        return None

    def to_codetrellis_format(self, result: Dict[str, Any]) -> str:
        """Convert extracted PyTorch data to CodeTrellis format."""
        lines = []

        # Models
        models = result.get('models', [])
        if models:
            lines.append("[PYTORCH_MODELS]")
            for model in models:
                parts = [f"{model.name}|base:{model.base_class}"]

                if model.is_sequential:
                    parts.append("type:Sequential")
                if model.is_lightning:
                    parts.append("type:Lightning")

                # Layers summary
                if model.layers:
                    layer_summary = []
                    for layer in model.layers:
                        if layer.params:
                            param_str = ','.join(f"{k}={v}" for k, v in list(layer.params.items())[:2])
                            layer_summary.append(f"{layer.name}:{layer.layer_type}({param_str})")
                        else:
                            layer_summary.append(f"{layer.name}:{layer.layer_type}")
                    parts.append(f"layers:[{';'.join(layer_summary[:5])}{'...' if len(layer_summary) > 5 else ''}]")

                # Forward signature
                if model.forward_signature:
                    inputs = ','.join(model.forward_signature.inputs)
                    ret = f"→{model.forward_signature.return_type}" if model.forward_signature.return_type else ""
                    parts.append(f"forward({inputs}){ret}")

                lines.append("|".join(parts))
            lines.append("")

        # Lightning modules
        lightning = result.get('lightning_modules', [])
        if lightning:
            lines.append("[LIGHTNING_MODULES]")
            for module in lightning:
                steps = []
                if module.training_step:
                    steps.append("train")
                if module.validation_step:
                    steps.append("val")
                if module.test_step:
                    steps.append("test")

                parts = [module.name, f"steps:[{','.join(steps)}]"]
                if module.callbacks:
                    parts.append(f"callbacks:[{','.join(module.callbacks)}]")

                lines.append("|".join(parts))
            lines.append("")

        # DataLoaders
        dataloaders = result.get('dataloaders', [])
        if dataloaders:
            lines.append("[DATALOADERS]")
            for dl in dataloaders:
                parts = [f"{dl.name}|dataset:{dl.dataset}"]
                if dl.batch_size:
                    parts.append(f"batch:{dl.batch_size}")
                if dl.shuffle:
                    parts.append("shuffle")
                if dl.num_workers:
                    parts.append(f"workers:{dl.num_workers}")
                lines.append("|".join(parts))
            lines.append("")

        # Training config
        training = result.get('training')
        if training and (training.optimizer or training.loss_function):
            lines.append("[TRAINING_CONFIG]")
            if training.optimizer:
                opt_str = f"optimizer:{training.optimizer}"
                if training.learning_rate:
                    opt_str += f"(lr={training.learning_rate})"
                lines.append(opt_str)
            if training.loss_function:
                lines.append(f"loss:{training.loss_function}")
            if training.device != 'cpu':
                lines.append(f"device:{training.device}")

        return "\n".join(lines)


# Convenience function
def extract_pytorch(content: str) -> Dict[str, Any]:
    """Extract PyTorch components from Python content."""
    extractor = PyTorchExtractor()
    return extractor.extract(content)
