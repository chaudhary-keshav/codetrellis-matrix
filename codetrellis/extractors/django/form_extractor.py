"""
Django Form Extractor for CodeTrellis.

Extracts Django Form and ModelForm definitions including fields,
widgets, validators, and clean methods.
Supports Django 1.x - 5.x form patterns.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class DjangoFormFieldInfo:
    """Information about a Django form field."""
    name: str
    field_type: str  # CharField, IntegerField, etc.
    required: bool = True
    widget: Optional[str] = None
    validators: List[str] = field(default_factory=list)
    kwargs: Dict[str, str] = field(default_factory=dict)


@dataclass
class DjangoFormInfo:
    """Information about a Django form."""
    name: str
    form_type: str  # form, model_form, inline_formset, formset
    file: str = ""
    base_classes: List[str] = field(default_factory=list)
    fields: List[DjangoFormFieldInfo] = field(default_factory=list)
    model: Optional[str] = None
    meta_fields: Optional[List[str]] = None  # From Meta.fields
    meta_exclude: Optional[List[str]] = None  # From Meta.exclude
    meta_widgets: Dict[str, str] = field(default_factory=dict)
    clean_methods: List[str] = field(default_factory=list)
    line_number: int = 0


# Django form field types
DJANGO_FORM_FIELD_TYPES = {
    'CharField', 'IntegerField', 'FloatField', 'DecimalField',
    'BooleanField', 'NullBooleanField', 'DateField', 'TimeField',
    'DateTimeField', 'DurationField', 'EmailField', 'URLField',
    'UUIDField', 'SlugField', 'IPAddressField', 'GenericIPAddressField',
    'FileField', 'ImageField', 'FilePathField',
    'ChoiceField', 'TypedChoiceField', 'MultipleChoiceField',
    'TypedMultipleChoiceField', 'ModelChoiceField', 'ModelMultipleChoiceField',
    'RegexField', 'JSONField', 'ComboField', 'MultiValueField',
    'SplitDateTimeField',
}

DJANGO_FORM_BASES = {
    'Form', 'ModelForm', 'BaseForm', 'BaseModelForm',
    'BaseFormSet', 'BaseModelFormSet', 'BaseInlineFormSet',
}


class DjangoFormExtractor:
    """
    Extracts Django form definitions.

    Handles:
    - Form and ModelForm classes
    - Form field declarations
    - Meta class (model, fields, exclude, widgets, labels)
    - clean_* validation methods
    - FormSets and InlineFormSets
    - Custom widgets
    """

    FORM_CLASS_PATTERN = re.compile(
        r'^class\s+(\w+)\s*\(\s*([^)]+)\s*\)\s*:',
        re.MULTILINE
    )

    FORM_FIELD_PATTERN = re.compile(
        r'^\s{4}(\w+)\s*=\s*(?:forms\.)?(\w+Field)\s*\(([^)]*)\)',
        re.MULTILINE
    )

    CLEAN_METHOD_PATTERN = re.compile(
        r'^\s{4}def\s+(clean(?:_\w+)?)\s*\(',
        re.MULTILINE
    )

    META_CLASS_PATTERN = re.compile(
        r'^\s{4}class\s+Meta\s*.*?:\s*\n((?:\s{8}.*\n)*)',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the Django form extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Django form definitions.

        Returns:
            Dict with 'forms'
        """
        forms = []

        for match in self.FORM_CLASS_PATTERN.finditer(content):
            class_name = match.group(1)
            bases_str = match.group(2)
            bases = [b.strip().split('.')[-1] for b in bases_str.split(',')]

            # Check if this is a form class
            form_type = self._classify_form(bases)
            if not form_type:
                continue

            class_body = self._extract_class_body(content, match.end())

            # Extract fields
            fields = self._extract_fields(class_body)

            # Extract clean methods
            clean_methods = self.CLEAN_METHOD_PATTERN.findall(class_body)

            # Extract Meta class
            model = None
            meta_fields = None
            meta_exclude = None
            meta_widgets = {}

            meta_match = self.META_CLASS_PATTERN.search(class_body)
            if meta_match:
                meta_body = meta_match.group(1)
                model = self._extract_meta_attr(meta_body, 'model')
                meta_fields = self._extract_meta_list(meta_body, 'fields')
                meta_exclude = self._extract_meta_list(meta_body, 'exclude')
                meta_widgets = self._extract_meta_dict(meta_body, 'widgets')

            form = DjangoFormInfo(
                name=class_name,
                form_type=form_type,
                file=file_path,
                base_classes=bases,
                fields=fields,
                model=model,
                meta_fields=meta_fields,
                meta_exclude=meta_exclude,
                meta_widgets=meta_widgets,
                clean_methods=clean_methods,
                line_number=content[:match.start()].count('\n') + 1,
            )
            forms.append(form)

        return {'forms': forms}

    def _classify_form(self, bases: List[str]) -> Optional[str]:
        """Classify the form type."""
        for base in bases:
            clean = base.strip()
            if 'ModelForm' in clean:
                return 'model_form'
            if 'InlineFormSet' in clean:
                return 'inline_formset'
            if 'FormSet' in clean:
                return 'formset'
            if 'Form' in clean and clean in DJANGO_FORM_BASES or clean.endswith('Form'):
                return 'form'
        return None

    def _extract_fields(self, class_body: str) -> List[DjangoFormFieldInfo]:
        """Extract form field declarations."""
        fields = []
        for match in self.FORM_FIELD_PATTERN.finditer(class_body):
            name = match.group(1)
            field_type = match.group(2)
            kwargs_str = match.group(3)

            required = True
            if 'required=False' in kwargs_str or 'required = False' in kwargs_str:
                required = False

            widget = None
            widget_match = re.search(r'widget\s*=\s*(?:forms\.)?(\w+)', kwargs_str)
            if widget_match:
                widget = widget_match.group(1)

            validators = re.findall(r'validators\s*=\s*\[([^\]]+)\]', kwargs_str)
            validator_list = []
            if validators:
                validator_list = [v.strip() for v in validators[0].split(',') if v.strip()]

            fields.append(DjangoFormFieldInfo(
                name=name,
                field_type=field_type,
                required=required,
                widget=widget,
                validators=validator_list,
            ))

        return fields

    def _extract_meta_attr(self, meta_body: str, attr: str) -> Optional[str]:
        """Extract a simple attribute from Meta class."""
        match = re.search(rf'{attr}\s*=\s*(\w+)', meta_body)
        return match.group(1) if match else None

    def _extract_meta_list(self, meta_body: str, attr: str) -> Optional[List[str]]:
        """Extract a list attribute from Meta class."""
        # Check for '__all__'
        if re.search(rf"{attr}\s*=\s*['\"]__all__['\"]", meta_body):
            return ['__all__']

        match = re.search(rf'{attr}\s*=\s*\[([^\]]+)\]', meta_body)
        if not match:
            match = re.search(rf'{attr}\s*=\s*\(([^)]+)\)', meta_body)
        if not match:
            return None

        items = re.findall(r"['\"](\w+)['\"]", match.group(1))
        return items if items else None

    def _extract_meta_dict(self, meta_body: str, attr: str) -> Dict[str, str]:
        """Extract a dict attribute from Meta class."""
        match = re.search(rf'{attr}\s*=\s*\{{([^}}]+)\}}', meta_body)
        if not match:
            return {}

        result = {}
        for pair in re.finditer(r"['\"](\w+)['\"]\s*:\s*(?:forms\.)?(\w+)", match.group(1)):
            result[pair.group(1)] = pair.group(2)
        return result

    def _extract_class_body(self, content: str, class_end: int) -> str:
        """Extract class body using indentation."""
        lines = content.split('\n')
        start_line = content[:class_end].count('\n')
        body_lines = []

        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            if not line.strip():
                body_lines.append(line)
                continue
            indent = len(line) - len(line.lstrip())
            if indent < 4 and line.strip():
                break
            body_lines.append(line)

        return '\n'.join(body_lines)
