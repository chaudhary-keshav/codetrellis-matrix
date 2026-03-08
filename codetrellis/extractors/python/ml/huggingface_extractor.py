"""
HuggingFaceExtractor - Extracts Hugging Face Transformers components.

This extractor parses Hugging Face code and extracts:
- Model configurations and architectures
- Tokenizer definitions
- Training arguments
- Trainer configurations
- Pipeline definitions
- Dataset loading
- Custom model classes

Part of CodeTrellis v2.0 - Python AI/ML Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class HFModelInfo:
    """Information about a Hugging Face model."""
    name: str
    model_class: str  # AutoModel, BertModel, GPT2LMHeadModel, etc.
    pretrained_name: Optional[str] = None  # "bert-base-uncased"
    task: Optional[str] = None  # classification, generation, etc.
    config_overrides: Dict[str, Any] = field(default_factory=dict)
    is_custom: bool = False
    base_model: Optional[str] = None
    line_number: int = 0


@dataclass
class HFTokenizerInfo:
    """Information about a Hugging Face tokenizer."""
    name: str
    tokenizer_class: str
    pretrained_name: Optional[str] = None
    max_length: Optional[int] = None
    padding: Optional[str] = None
    truncation: bool = False


@dataclass
class HFTrainingArgsInfo:
    """Information about training arguments."""
    output_dir: Optional[str] = None
    num_train_epochs: Optional[int] = None
    per_device_train_batch_size: Optional[int] = None
    per_device_eval_batch_size: Optional[int] = None
    learning_rate: Optional[float] = None
    weight_decay: Optional[float] = None
    warmup_steps: Optional[int] = None
    logging_steps: Optional[int] = None
    eval_strategy: Optional[str] = None
    save_strategy: Optional[str] = None
    fp16: bool = False
    bf16: bool = False
    gradient_accumulation_steps: Optional[int] = None
    deepspeed: Optional[str] = None


@dataclass
class HFTrainerInfo:
    """Information about a Trainer configuration."""
    name: str
    model: Optional[str] = None
    args: Optional[str] = None
    train_dataset: Optional[str] = None
    eval_dataset: Optional[str] = None
    tokenizer: Optional[str] = None
    data_collator: Optional[str] = None
    compute_metrics: Optional[str] = None
    callbacks: List[str] = field(default_factory=list)


@dataclass
class HFPipelineInfo:
    """Information about a Hugging Face pipeline."""
    name: str
    task: str
    model: Optional[str] = None
    tokenizer: Optional[str] = None
    device: Optional[str] = None
    framework: str = "pt"  # pt or tf


@dataclass
class HFDatasetInfo:
    """Information about dataset loading."""
    name: str
    dataset_name: Optional[str] = None  # e.g., "squad", "imdb"
    config_name: Optional[str] = None
    split: Optional[str] = None
    streaming: bool = False
    features: List[str] = field(default_factory=list)


class HuggingFaceExtractor:
    """
    Extracts Hugging Face Transformers components from source code.

    Handles:
    - AutoModel.from_pretrained() and variants
    - AutoTokenizer.from_pretrained()
    - Custom model classes extending PreTrainedModel
    - TrainingArguments configurations
    - Trainer setup
    - Pipeline definitions
    - Dataset loading with datasets library
    - PEFT/LoRA configurations
    """

    # Model loading patterns
    MODEL_FROM_PRETRAINED = re.compile(
        r'(\w+)\s*=\s*(Auto\w*|Bert\w*|GPT\w*|T5\w*|Llama\w*|Mistral\w*|Falcon\w*|\w*ForSequence\w*|\w*ForToken\w*|\w*ForCausal\w*|\w*ForMasked\w*|\w*Model\w*)\.from_pretrained\s*\(\s*[\'"]([^"\']+)[\'"](?:\s*,\s*([^)]*))?\s*\)',
        re.MULTILINE
    )

    # Custom model class
    CUSTOM_MODEL_PATTERN = re.compile(
        r'class\s+(\w+)\s*\(\s*(PreTrainedModel|\w*Model)\s*\)',
        re.MULTILINE
    )

    # Tokenizer pattern
    TOKENIZER_PATTERN = re.compile(
        r'(\w+)\s*=\s*(Auto\w*Tokenizer|\w*Tokenizer|AutoProcessor)\.from_pretrained\s*\(\s*[\'"]([^"\']+)[\'"](?:\s*,\s*([^)]*))?\s*\)',
        re.MULTILINE
    )

    # Training arguments pattern
    TRAINING_ARGS_PATTERN = re.compile(
        r'(\w+)\s*=\s*TrainingArguments\s*\(\s*([^)]*(?:\([^)]*\)[^)]*)*)\s*\)',
        re.MULTILINE | re.DOTALL
    )

    # Trainer pattern
    TRAINER_PATTERN = re.compile(
        r'(\w+)\s*=\s*Trainer\s*\(\s*([^)]*(?:\([^)]*\)[^)]*)*)\s*\)',
        re.MULTILINE | re.DOTALL
    )

    # Pipeline pattern
    PIPELINE_PATTERN = re.compile(
        r'(\w+)\s*=\s*pipeline\s*\(\s*[\'"]([^"\']+)[\'"](?:\s*,\s*([^)]*))?\s*\)',
        re.MULTILINE
    )

    # Dataset loading pattern
    DATASET_PATTERN = re.compile(
        r'(\w+)\s*=\s*load_dataset\s*\(\s*[\'"]([^"\']+)[\'"](?:\s*,\s*([^)]*))?\s*\)',
        re.MULTILINE
    )

    # PEFT/LoRA patterns
    LORA_CONFIG_PATTERN = re.compile(
        r'(\w+)\s*=\s*LoraConfig\s*\(\s*([^)]*)\s*\)',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the Hugging Face extractor."""
        pass

    def extract(self, content: str) -> Dict[str, Any]:
        """
        Extract all Hugging Face components from Python content.

        Args:
            content: Python source code

        Returns:
            Dict with models, tokenizers, training configs, etc.
        """
        models = self._extract_models(content)
        tokenizers = self._extract_tokenizers(content)
        training_args = self._extract_training_args(content)
        trainers = self._extract_trainers(content)
        pipelines = self._extract_pipelines(content)
        datasets = self._extract_datasets(content)
        lora_configs = self._extract_lora_configs(content)

        return {
            'models': models,
            'tokenizers': tokenizers,
            'training_args': training_args,
            'trainers': trainers,
            'pipelines': pipelines,
            'datasets': datasets,
            'lora_configs': lora_configs
        }

    def _extract_models(self, content: str) -> List[HFModelInfo]:
        """Extract model definitions."""
        models = []

        # From pretrained
        for match in self.MODEL_FROM_PRETRAINED.finditer(content):
            var_name = match.group(1)
            model_class = match.group(2)
            pretrained_name = match.group(3)
            extra_args = match.group(4) or ""

            # Infer task from class name
            task = self._infer_task(model_class)

            # Parse config overrides
            config_overrides = self._parse_config_overrides(extra_args)

            models.append(HFModelInfo(
                name=var_name,
                model_class=model_class,
                pretrained_name=pretrained_name,
                task=task,
                config_overrides=config_overrides,
                line_number=content[:match.start()].count('\n') + 1
            ))

        # Custom model classes
        for match in self.CUSTOM_MODEL_PATTERN.finditer(content):
            class_name = match.group(1)
            base_class = match.group(2)

            models.append(HFModelInfo(
                name=class_name,
                model_class=class_name,
                base_model=base_class,
                is_custom=True,
                line_number=content[:match.start()].count('\n') + 1
            ))

        return models

    def _extract_tokenizers(self, content: str) -> List[HFTokenizerInfo]:
        """Extract tokenizer definitions."""
        tokenizers = []

        for match in self.TOKENIZER_PATTERN.finditer(content):
            var_name = match.group(1)
            tokenizer_class = match.group(2)
            pretrained_name = match.group(3)
            extra_args = match.group(4) or ""

            # Parse tokenizer options
            max_length = self._extract_int_arg(extra_args, 'max_length')
            truncation = 'truncation=True' in extra_args
            padding = self._extract_string_arg(extra_args, 'padding')

            tokenizers.append(HFTokenizerInfo(
                name=var_name,
                tokenizer_class=tokenizer_class,
                pretrained_name=pretrained_name,
                max_length=max_length,
                truncation=truncation,
                padding=padding
            ))

        return tokenizers

    def _extract_training_args(self, content: str) -> List[HFTrainingArgsInfo]:
        """Extract TrainingArguments configurations."""
        training_args = []

        for match in self.TRAINING_ARGS_PATTERN.finditer(content):
            args_str = match.group(2)

            args = HFTrainingArgsInfo(
                output_dir=self._extract_string_arg(args_str, 'output_dir'),
                num_train_epochs=self._extract_int_arg(args_str, 'num_train_epochs'),
                per_device_train_batch_size=self._extract_int_arg(args_str, 'per_device_train_batch_size'),
                per_device_eval_batch_size=self._extract_int_arg(args_str, 'per_device_eval_batch_size'),
                learning_rate=self._extract_float_arg(args_str, 'learning_rate'),
                weight_decay=self._extract_float_arg(args_str, 'weight_decay'),
                warmup_steps=self._extract_int_arg(args_str, 'warmup_steps'),
                logging_steps=self._extract_int_arg(args_str, 'logging_steps'),
                eval_strategy=self._extract_string_arg(args_str, 'eval_strategy') or self._extract_string_arg(args_str, 'evaluation_strategy'),
                save_strategy=self._extract_string_arg(args_str, 'save_strategy'),
                fp16='fp16=True' in args_str,
                bf16='bf16=True' in args_str,
                gradient_accumulation_steps=self._extract_int_arg(args_str, 'gradient_accumulation_steps'),
                deepspeed=self._extract_string_arg(args_str, 'deepspeed')
            )

            training_args.append(args)

        return training_args

    def _extract_trainers(self, content: str) -> List[HFTrainerInfo]:
        """Extract Trainer configurations."""
        trainers = []

        for match in self.TRAINER_PATTERN.finditer(content):
            trainer_name = match.group(1)
            trainer_args = match.group(2)

            # Parse trainer arguments
            model = self._extract_var_arg(trainer_args, 'model')
            args = self._extract_var_arg(trainer_args, 'args')
            train_dataset = self._extract_var_arg(trainer_args, 'train_dataset')
            eval_dataset = self._extract_var_arg(trainer_args, 'eval_dataset')
            tokenizer = self._extract_var_arg(trainer_args, 'tokenizer')
            data_collator = self._extract_var_arg(trainer_args, 'data_collator')
            compute_metrics = self._extract_var_arg(trainer_args, 'compute_metrics')

            # Extract callbacks
            callbacks = re.findall(r'(\w+Callback)', trainer_args)

            trainers.append(HFTrainerInfo(
                name=trainer_name,
                model=model,
                args=args,
                train_dataset=train_dataset,
                eval_dataset=eval_dataset,
                tokenizer=tokenizer,
                data_collator=data_collator,
                compute_metrics=compute_metrics,
                callbacks=callbacks
            ))

        return trainers

    def _extract_pipelines(self, content: str) -> List[HFPipelineInfo]:
        """Extract pipeline definitions."""
        pipelines = []

        for match in self.PIPELINE_PATTERN.finditer(content):
            pipe_name = match.group(1)
            task = match.group(2)
            extra_args = match.group(3) or ""

            model = self._extract_string_arg(extra_args, 'model') or self._extract_var_arg(extra_args, 'model')
            tokenizer = self._extract_var_arg(extra_args, 'tokenizer')
            device = self._extract_var_arg(extra_args, 'device')

            pipelines.append(HFPipelineInfo(
                name=pipe_name,
                task=task,
                model=model,
                tokenizer=tokenizer,
                device=device
            ))

        return pipelines

    def _extract_datasets(self, content: str) -> List[HFDatasetInfo]:
        """Extract dataset loading."""
        datasets = []

        for match in self.DATASET_PATTERN.finditer(content):
            ds_name = match.group(1)
            dataset_id = match.group(2)
            extra_args = match.group(3) or ""

            config_name = self._extract_string_arg(extra_args, 'name')
            split = self._extract_string_arg(extra_args, 'split')
            streaming = 'streaming=True' in extra_args

            datasets.append(HFDatasetInfo(
                name=ds_name,
                dataset_name=dataset_id,
                config_name=config_name,
                split=split,
                streaming=streaming
            ))

        return datasets

    def _extract_lora_configs(self, content: str) -> List[Dict[str, Any]]:
        """Extract LoRA configurations."""
        configs = []

        for match in self.LORA_CONFIG_PATTERN.finditer(content):
            config_name = match.group(1)
            args_str = match.group(2)

            config = {
                'name': config_name,
                'r': self._extract_int_arg(args_str, 'r'),
                'lora_alpha': self._extract_int_arg(args_str, 'lora_alpha'),
                'target_modules': self._extract_list_arg(args_str, 'target_modules'),
                'lora_dropout': self._extract_float_arg(args_str, 'lora_dropout'),
                'bias': self._extract_string_arg(args_str, 'bias'),
                'task_type': self._extract_string_arg(args_str, 'task_type'),
            }

            configs.append(config)

        return configs

    def _infer_task(self, model_class: str) -> Optional[str]:
        """Infer task from model class name."""
        if 'ForSequenceClassification' in model_class:
            return 'sequence-classification'
        elif 'ForTokenClassification' in model_class:
            return 'token-classification'
        elif 'ForCausalLM' in model_class:
            return 'text-generation'
        elif 'ForMaskedLM' in model_class:
            return 'fill-mask'
        elif 'ForQuestionAnswering' in model_class:
            return 'question-answering'
        elif 'ForConditionalGeneration' in model_class:
            return 'text2text-generation'
        elif 'Encoder' in model_class:
            return 'feature-extraction'
        return None

    def _parse_config_overrides(self, args_str: str) -> Dict[str, Any]:
        """Parse model config overrides."""
        overrides = {}

        # Common config overrides
        if 'num_labels' in args_str:
            overrides['num_labels'] = self._extract_int_arg(args_str, 'num_labels')
        if 'torch_dtype' in args_str:
            overrides['torch_dtype'] = self._extract_var_arg(args_str, 'torch_dtype')
        if 'device_map' in args_str:
            overrides['device_map'] = self._extract_string_arg(args_str, 'device_map')
        if 'load_in_8bit' in args_str:
            overrides['load_in_8bit'] = 'load_in_8bit=True' in args_str
        if 'load_in_4bit' in args_str:
            overrides['load_in_4bit'] = 'load_in_4bit=True' in args_str

        return overrides

    def _extract_string_arg(self, args_str: str, key: str) -> Optional[str]:
        """Extract string argument."""
        match = re.search(rf'{key}\s*=\s*[\'"]([^"\']+)[\'"]', args_str)
        return match.group(1) if match else None

    def _extract_int_arg(self, args_str: str, key: str) -> Optional[int]:
        """Extract integer argument."""
        match = re.search(rf'{key}\s*=\s*(\d+)', args_str)
        return int(match.group(1)) if match else None

    def _extract_float_arg(self, args_str: str, key: str) -> Optional[float]:
        """Extract float argument."""
        match = re.search(rf'{key}\s*=\s*([\d.e-]+)', args_str)
        return float(match.group(1)) if match else None

    def _extract_var_arg(self, args_str: str, key: str) -> Optional[str]:
        """Extract variable reference argument."""
        match = re.search(rf'{key}\s*=\s*(\w+)', args_str)
        return match.group(1) if match else None

    def _extract_list_arg(self, args_str: str, key: str) -> List[str]:
        """Extract list argument."""
        match = re.search(rf'{key}\s*=\s*\[([^\]]+)\]', args_str)
        if match:
            items = re.findall(r'[\'"]([^"\']+)[\'"]', match.group(1))
            return items
        return []

    def to_codetrellis_format(self, result: Dict[str, Any]) -> str:
        """Convert extracted Hugging Face data to CodeTrellis format."""
        lines = []

        # Models
        models = result.get('models', [])
        if models:
            lines.append("[HF_MODELS]")
            for model in models:
                parts = [model.name]
                if model.is_custom:
                    parts.append(f"custom|extends:{model.base_model}")
                else:
                    parts.append(f"class:{model.model_class}")
                    if model.pretrained_name:
                        parts.append(f"pretrained:{model.pretrained_name}")
                if model.task:
                    parts.append(f"task:{model.task}")
                if model.config_overrides:
                    overrides = ','.join(f"{k}={v}" for k, v in model.config_overrides.items())
                    parts.append(f"config:[{overrides}]")
                lines.append("|".join(parts))
            lines.append("")

        # Tokenizers
        tokenizers = result.get('tokenizers', [])
        if tokenizers:
            lines.append("[HF_TOKENIZERS]")
            for tok in tokenizers:
                parts = [tok.name, f"class:{tok.tokenizer_class}"]
                if tok.pretrained_name:
                    parts.append(f"pretrained:{tok.pretrained_name}")
                if tok.max_length:
                    parts.append(f"max_len:{tok.max_length}")
                lines.append("|".join(parts))
            lines.append("")

        # Training args
        training_args = result.get('training_args', [])
        if training_args:
            lines.append("[HF_TRAINING_ARGS]")
            for args in training_args:
                parts = []
                if args.num_train_epochs:
                    parts.append(f"epochs:{args.num_train_epochs}")
                if args.learning_rate:
                    parts.append(f"lr:{args.learning_rate}")
                if args.per_device_train_batch_size:
                    parts.append(f"batch:{args.per_device_train_batch_size}")
                if args.fp16:
                    parts.append("fp16")
                if args.bf16:
                    parts.append("bf16")
                if args.deepspeed:
                    parts.append(f"deepspeed:{args.deepspeed}")
                if parts:
                    lines.append("|".join(parts))
            lines.append("")

        # Trainers
        trainers = result.get('trainers', [])
        if trainers:
            lines.append("[HF_TRAINERS]")
            for trainer in trainers:
                parts = [trainer.name]
                if trainer.model:
                    parts.append(f"model:{trainer.model}")
                if trainer.train_dataset:
                    parts.append(f"train:{trainer.train_dataset}")
                if trainer.eval_dataset:
                    parts.append(f"eval:{trainer.eval_dataset}")
                if trainer.callbacks:
                    parts.append(f"callbacks:[{','.join(trainer.callbacks)}]")
                lines.append("|".join(parts))
            lines.append("")

        # Pipelines
        pipelines = result.get('pipelines', [])
        if pipelines:
            lines.append("[HF_PIPELINES]")
            for pipe in pipelines:
                parts = [pipe.name, f"task:{pipe.task}"]
                if pipe.model:
                    parts.append(f"model:{pipe.model}")
                lines.append("|".join(parts))
            lines.append("")

        # Datasets
        datasets = result.get('datasets', [])
        if datasets:
            lines.append("[HF_DATASETS]")
            for ds in datasets:
                parts = [ds.name, f"dataset:{ds.dataset_name}"]
                if ds.split:
                    parts.append(f"split:{ds.split}")
                if ds.streaming:
                    parts.append("streaming")
                lines.append("|".join(parts))
            lines.append("")

        # LoRA configs
        lora_configs = result.get('lora_configs', [])
        if lora_configs:
            lines.append("[LORA_CONFIGS]")
            for config in lora_configs:
                parts = [config['name']]
                if config.get('r'):
                    parts.append(f"r:{config['r']}")
                if config.get('lora_alpha'):
                    parts.append(f"alpha:{config['lora_alpha']}")
                if config.get('target_modules'):
                    parts.append(f"targets:[{','.join(config['target_modules'])}]")
                lines.append("|".join(parts))

        return "\n".join(lines)


# Convenience function
def extract_huggingface(content: str) -> Dict[str, Any]:
    """Extract Hugging Face components from Python content."""
    extractor = HuggingFaceExtractor()
    return extractor.extract(content)
