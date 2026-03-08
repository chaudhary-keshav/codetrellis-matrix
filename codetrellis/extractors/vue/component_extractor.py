"""
Vue.js Component Extractor for CodeTrellis

Extracts component definitions from Vue.js source code:
- Single File Components (SFC) with <script setup>, <script>, <template>, <style>
- Options API components (data, computed, methods, watch, lifecycle hooks)
- Composition API components (setup(), defineComponent)
- <script setup> components (defineProps, defineEmits, defineExpose, defineSlots)
- defineAsyncComponent for lazy loading
- defineCustomElement for Web Components
- Props (type, default, required, validator)
- Emits (event definitions, typed emits)
- Slots (named slots, scoped slots)
- Provide/Inject patterns

Supports Vue 2.x (Options API) through Vue 3.5+ (Composition API, <script setup>,
defineModel, defineOptions, Vapor mode):
- Vue 2.x: Options API, mixins, filters, functional components
- Vue 3.0: Composition API, Teleport, Suspense, Fragments
- Vue 3.1: defineAsyncComponent improvements
- Vue 3.2: <script setup>, defineProps, defineEmits, defineExpose
- Vue 3.3: defineSlots, defineOptions, generic components, typed slots
- Vue 3.4: defineModel, v-bind shorthand, improved hydration
- Vue 3.5: Reactive Props Destructure, useTemplateRef, Deferred Teleport

Part of CodeTrellis v4.34 - Vue.js Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class VuePropInfo:
    """Information about a Vue component prop."""
    name: str
    type: str = ""  # String, Number, Boolean, Array, Object, Function, Symbol, custom
    default_value: Optional[str] = None
    required: bool = False
    has_validator: bool = False
    line_number: int = 0


@dataclass
class VueEmitInfo:
    """Information about a Vue component emit."""
    name: str
    payload_type: str = ""  # TypeScript type or inferred
    line_number: int = 0


@dataclass
class VueSlotInfo:
    """Information about a Vue component slot."""
    name: str
    scope_type: str = ""  # scoped slot props type
    is_default: bool = False
    line_number: int = 0


@dataclass
class VueProvideInjectInfo:
    """Information about provide/inject pattern."""
    key: str
    kind: str = "provide"  # provide or inject
    type: str = ""
    default_value: Optional[str] = None
    line_number: int = 0


@dataclass
class VueComponentInfo:
    """Information about a Vue component definition."""
    name: str
    file: str = ""
    line_number: int = 0
    api_style: str = ""  # options, composition, script-setup
    is_exported: bool = False
    is_default_export: bool = False
    is_async: bool = False
    is_functional: bool = False  # Vue 2 functional components
    is_custom_element: bool = False

    # Template info
    has_template: bool = False
    template_lang: str = ""  # html, pug, jade
    has_style: bool = False
    style_lang: str = ""  # css, scss, less, stylus
    style_scoped: bool = False
    style_module: bool = False

    # Props & Emits
    props: List[VuePropInfo] = field(default_factory=list)
    emits: List[VueEmitInfo] = field(default_factory=list)
    slots: List[VueSlotInfo] = field(default_factory=list)

    # Options API
    data_keys: List[str] = field(default_factory=list)
    computed_keys: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    watch_keys: List[str] = field(default_factory=list)
    mixins: List[str] = field(default_factory=list)
    components_used: List[str] = field(default_factory=list)
    directives_used: List[str] = field(default_factory=list)

    # Composition API / <script setup>
    composables_used: List[str] = field(default_factory=list)
    refs: List[str] = field(default_factory=list)
    reactives: List[str] = field(default_factory=list)

    # Provide/Inject
    provides: List[VueProvideInjectInfo] = field(default_factory=list)
    injects: List[VueProvideInjectInfo] = field(default_factory=list)

    # Model
    has_model: bool = False  # defineModel (Vue 3.4+)
    model_name: str = ""


class VueComponentExtractor:
    """
    Extracts Vue.js component definitions from source code.

    Detects:
    - SFC <script setup> components (Vue 3.2+)
    - defineComponent() calls (Vue 3 Composition API)
    - Options API objects (Vue 2.x compatible)
    - defineAsyncComponent() for lazy loading
    - defineCustomElement() for Web Components
    - Props (defineProps / props option)
    - Emits (defineEmits / emits option)
    - Slots (defineSlots / template slots)
    - Provide/Inject patterns
    """

    # SFC block patterns
    SCRIPT_SETUP_PATTERN = re.compile(
        r'<script\s+(?:[^>]*\s)?setup(?:\s[^>]*)?>',
        re.IGNORECASE
    )

    SCRIPT_PATTERN = re.compile(
        r'<script(?:\s+[^>]*)?>',
        re.IGNORECASE
    )

    TEMPLATE_PATTERN = re.compile(
        r'<template(?:\s+lang=["\'](\w+)["\'])?\s*>',
        re.IGNORECASE
    )

    STYLE_PATTERN = re.compile(
        r'<style(?:\s+(?:scoped|module|lang=["\'](\w+)["\']))?\s*'
        r'(?:(?:scoped|module|lang=["\'](\w+)["\'])\s*)*>',
        re.IGNORECASE | re.DOTALL
    )

    # defineComponent
    DEFINE_COMPONENT_PATTERN = re.compile(
        r'(?:export\s+default\s+)?defineComponent\s*\(\s*\{',
        re.MULTILINE
    )

    # <script setup> macros
    DEFINE_PROPS_PATTERN = re.compile(
        r'(?:const\s+\w+\s*=\s*)?defineProps\s*(?:<([^>]+)>)?\s*\(([^)]*)\)',
        re.MULTILINE | re.DOTALL
    )

    DEFINE_PROPS_GENERIC_PATTERN = re.compile(
        r'defineProps\s*<\s*\{([^}]+)\}\s*>\s*\(\s*\)',
        re.MULTILINE | re.DOTALL
    )

    DEFINE_EMITS_PATTERN = re.compile(
        r'(?:const\s+\w+\s*=\s*)?defineEmits\s*(?:<([^>]+)>)?\s*\(([^)]*)\)',
        re.MULTILINE | re.DOTALL
    )

    DEFINE_EXPOSE_PATTERN = re.compile(
        r'defineExpose\s*\(\s*\{([^}]*)\}\s*\)',
        re.MULTILINE | re.DOTALL
    )

    DEFINE_SLOTS_PATTERN = re.compile(
        r'defineSlots\s*<([^>]+)>\s*\(\s*\)',
        re.MULTILINE | re.DOTALL
    )

    DEFINE_OPTIONS_PATTERN = re.compile(
        r'defineOptions\s*\(\s*\{([^}]*)\}\s*\)',
        re.MULTILINE | re.DOTALL
    )

    DEFINE_MODEL_PATTERN = re.compile(
        r'(?:const\s+(\w+)\s*=\s*)?defineModel\s*(?:<([^>]+)>)?\s*\(([^)]*)\)',
        re.MULTILINE | re.DOTALL
    )

    # Options API patterns
    PROPS_OPTION_PATTERN = re.compile(
        r'props\s*:\s*(?:\[([^\]]+)\]|\{((?:[^{}]|\{[^{}]*\})*)\})',
        re.MULTILINE | re.DOTALL
    )

    DATA_OPTION_PATTERN = re.compile(
        r'data\s*\(\s*\)\s*\{?\s*(?:return\s*)?\{([^}]+(?:\{[^}]*\}[^}]*)*)\}',
        re.MULTILINE | re.DOTALL
    )

    COMPUTED_OPTION_PATTERN = re.compile(
        r'computed\s*:\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}',
        re.MULTILINE | re.DOTALL
    )

    METHODS_OPTION_PATTERN = re.compile(
        r'methods\s*:\s*\{',
        re.MULTILINE
    )

    WATCH_OPTION_PATTERN = re.compile(
        r'watch\s*:\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}',
        re.MULTILINE | re.DOTALL
    )

    MIXINS_OPTION_PATTERN = re.compile(
        r'mixins\s*:\s*\[([^\]]+)\]',
        re.MULTILINE
    )

    COMPONENTS_OPTION_PATTERN = re.compile(
        r'components\s*:\s*\{([^}]*)\}',
        re.MULTILINE | re.DOTALL
    )

    # Export patterns
    EXPORT_DEFAULT_PATTERN = re.compile(
        r'export\s+default\s+(?:defineComponent\s*\(|defineAsyncComponent\s*\(|\{)',
        re.MULTILINE
    )

    # defineAsyncComponent
    DEFINE_ASYNC_COMPONENT_PATTERN = re.compile(
        r'(?:const\s+(\w+)\s*=\s*)?defineAsyncComponent\s*\(',
        re.MULTILINE
    )

    # defineCustomElement
    DEFINE_CUSTOM_ELEMENT_PATTERN = re.compile(
        r'(?:const\s+(\w+)\s*=\s*)?defineCustomElement\s*\(',
        re.MULTILINE
    )

    # Provide/Inject
    PROVIDE_PATTERN = re.compile(
        r'provide\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,',
        re.MULTILINE
    )

    INJECT_PATTERN = re.compile(
        r'inject\s*\(\s*[\'"]([^\'"]+)[\'"]\s*(?:,\s*([^)]+))?\)',
        re.MULTILINE
    )

    PROVIDE_OPTION_PATTERN = re.compile(
        r'provide\s*(?:\(\s*\)\s*\{?\s*(?:return\s*)?\{([^}]+)\}|\s*:\s*\{([^}]+)\})',
        re.MULTILINE | re.DOTALL
    )

    INJECT_OPTION_PATTERN = re.compile(
        r'inject\s*:\s*(?:\[([^\]]+)\]|\{([^}]+)\})',
        re.MULTILINE | re.DOTALL
    )

    # Component name pattern (from Options API name property or filename)
    NAME_OPTION_PATTERN = re.compile(
        r"name\s*:\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Vue component definitions from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'components', 'async_components', 'custom_elements'
        """
        result: Dict[str, Any] = {
            'components': [],
            'async_components': [],
            'custom_elements': [],
        }

        is_sfc = file_path.endswith('.vue')

        if is_sfc:
            self._extract_sfc_component(content, file_path, result)
        else:
            self._extract_js_components(content, file_path, result)

        return result

    def _extract_sfc_component(self, content: str, file_path: str,
                                result: Dict[str, Any]) -> None:
        """Extract component from a .vue Single File Component."""
        import os
        # Determine component name from file
        basename = os.path.splitext(os.path.basename(file_path))[0]
        comp = VueComponentInfo(
            name=basename,
            file=file_path,
            line_number=1,
            is_exported=True,
            is_default_export=True,
        )

        # Detect <template>
        tmpl_match = self.TEMPLATE_PATTERN.search(content)
        if tmpl_match:
            comp.has_template = True
            comp.template_lang = tmpl_match.group(1) or "html"

        # Detect <style>
        style_match = self.STYLE_PATTERN.search(content)
        if style_match:
            comp.has_style = True
            comp.style_scoped = bool(re.search(r'<style[^>]*\bscoped\b', content, re.IGNORECASE))
            comp.style_module = bool(re.search(r'<style[^>]*\bmodule\b', content, re.IGNORECASE))
            lang = style_match.group(1) or style_match.group(2)
            comp.style_lang = lang or "css"

        # Detect <script setup>
        has_script_setup = bool(self.SCRIPT_SETUP_PATTERN.search(content))

        if has_script_setup:
            comp.api_style = "script-setup"
            self._extract_script_setup(content, comp)
        elif self.DEFINE_COMPONENT_PATTERN.search(content):
            comp.api_style = "composition"
            self._extract_composition_api(content, comp)
        else:
            comp.api_style = "options"
            self._extract_options_api(content, comp)

        # Name from options
        name_match = self.NAME_OPTION_PATTERN.search(content)
        if name_match:
            comp.name = name_match.group(1)

        # Extract used components from template
        self._extract_template_components(content, comp)

        # Extract directives used
        self._extract_template_directives(content, comp)

        # Extract composables used
        self._extract_composables(content, comp)

        result['components'].append(comp)

        # Also check for defineAsyncComponent
        for m in self.DEFINE_ASYNC_COMPONENT_PATTERN.finditer(content):
            name = m.group(1) or "AsyncComponent"
            async_comp = VueComponentInfo(
                name=name,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                is_async=True,
                is_exported=True,
            )
            result['async_components'].append(async_comp)

        # Check for defineCustomElement
        for m in self.DEFINE_CUSTOM_ELEMENT_PATTERN.finditer(content):
            name = m.group(1) or "CustomElement"
            ce = VueComponentInfo(
                name=name,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                is_custom_element=True,
                is_exported=True,
            )
            result['custom_elements'].append(ce)

    def _extract_js_components(self, content: str, file_path: str,
                                result: Dict[str, Any]) -> None:
        """Extract components from .js/.ts files (not SFC)."""
        import os

        # defineComponent
        for m in self.DEFINE_COMPONENT_PATTERN.finditer(content):
            name_match = self.NAME_OPTION_PATTERN.search(content[m.start():])
            basename = os.path.splitext(os.path.basename(file_path))[0]
            name = name_match.group(1) if name_match else basename

            comp = VueComponentInfo(
                name=name,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                api_style="composition",
                is_exported=bool(re.search(r'export\s+default', content[:m.start() + 30])),
                is_default_export=bool(re.search(r'export\s+default', content[:m.start() + 30])),
            )

            self._extract_options_api(content[m.start():], comp)
            self._extract_composables(content, comp)
            result['components'].append(comp)

        # defineAsyncComponent
        for m in self.DEFINE_ASYNC_COMPONENT_PATTERN.finditer(content):
            name = m.group(1) or "AsyncComponent"
            async_comp = VueComponentInfo(
                name=name,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                is_async=True,
                is_exported='export' in content[max(0, m.start() - 30):m.start()],
            )
            result['async_components'].append(async_comp)

        # defineCustomElement
        for m in self.DEFINE_CUSTOM_ELEMENT_PATTERN.finditer(content):
            name = m.group(1) or "CustomElement"
            ce = VueComponentInfo(
                name=name,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                is_custom_element=True,
                is_exported='export' in content[max(0, m.start() - 30):m.start()],
            )
            result['custom_elements'].append(ce)

    def _extract_script_setup(self, content: str, comp: VueComponentInfo) -> None:
        """Extract <script setup> macros."""
        # defineProps
        for m in self.DEFINE_PROPS_PATTERN.finditer(content):
            type_param = m.group(1)
            args = m.group(2)
            self._parse_props(type_param, args, comp)

        # defineProps with generic type only
        for m in self.DEFINE_PROPS_GENERIC_PATTERN.finditer(content):
            type_body = m.group(1)
            self._parse_typed_props(type_body, comp)

        # defineEmits
        for m in self.DEFINE_EMITS_PATTERN.finditer(content):
            type_param = m.group(1)
            args = m.group(2)
            self._parse_emits(type_param, args, comp)

        # defineExpose
        for m in self.DEFINE_EXPOSE_PATTERN.finditer(content):
            body = m.group(1)
            keys = re.findall(r'(\w+)', body)
            comp.methods.extend(keys)

        # defineSlots
        for m in self.DEFINE_SLOTS_PATTERN.finditer(content):
            type_body = m.group(1)
            self._parse_slots(type_body, comp)

        # defineModel (Vue 3.4+)
        for m in self.DEFINE_MODEL_PATTERN.finditer(content):
            model_name = m.group(1) or "modelValue"
            comp.has_model = True
            comp.model_name = model_name

        # defineOptions
        for m in self.DEFINE_OPTIONS_PATTERN.finditer(content):
            body = m.group(1)
            name_match = re.search(r"name\s*:\s*['\"]([^'\"]+)['\"]", body)
            if name_match:
                comp.name = name_match.group(1)

        # Provide/Inject in setup
        for m in self.PROVIDE_PATTERN.finditer(content):
            comp.provides.append(VueProvideInjectInfo(
                key=m.group(1),
                kind="provide",
                line_number=content[:m.start()].count('\n') + 1,
            ))

        for m in self.INJECT_PATTERN.finditer(content):
            comp.injects.append(VueProvideInjectInfo(
                key=m.group(1),
                kind="inject",
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _extract_composition_api(self, content: str, comp: VueComponentInfo) -> None:
        """Extract composition API patterns from defineComponent()."""
        # Props from defineComponent options
        self._extract_options_props(content, comp)

        # Emits from defineComponent options
        self._extract_options_emits(content, comp)

        # setup function body composables
        self._extract_composables(content, comp)

    def _extract_options_api(self, content: str, comp: VueComponentInfo) -> None:
        """Extract Options API patterns."""
        # Props
        self._extract_options_props(content, comp)

        # Data
        data_match = self.DATA_OPTION_PATTERN.search(content)
        if data_match:
            body = data_match.group(1)
            keys = re.findall(r'(\w+)\s*:', body)
            comp.data_keys = keys

        # Computed
        computed_match = self.COMPUTED_OPTION_PATTERN.search(content)
        if computed_match:
            body = computed_match.group(1)
            keys = re.findall(r'(\w+)\s*(?:\(|:)', body)
            comp.computed_keys = keys

        # Methods
        methods_match = self.METHODS_OPTION_PATTERN.search(content)
        if methods_match:
            # Extract method names by finding word followed by ( or :
            start = methods_match.end()
            depth = 1
            i = start
            while i < len(content) and depth > 0:
                if content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                i += 1
            methods_body = content[start:i - 1]
            method_names = re.findall(r'(?:async\s+)?(\w+)\s*\(', methods_body)
            comp.methods = method_names

        # Watch
        watch_match = self.WATCH_OPTION_PATTERN.search(content)
        if watch_match:
            body = watch_match.group(1)
            keys = re.findall(r"['\"]?(\w+)['\"]?\s*(?:\(|:|\{)", body)
            comp.watch_keys = keys

        # Mixins
        mixins_match = self.MIXINS_OPTION_PATTERN.search(content)
        if mixins_match:
            body = mixins_match.group(1)
            comp.mixins = [m.strip() for m in body.split(',') if m.strip()]

        # Components
        comps_match = self.COMPONENTS_OPTION_PATTERN.search(content)
        if comps_match:
            body = comps_match.group(1)
            comp.components_used = re.findall(r'(\w+)', body)

        # Emits
        self._extract_options_emits(content, comp)

        # Provide / Inject
        prov_match = self.PROVIDE_OPTION_PATTERN.search(content)
        if prov_match:
            body = prov_match.group(1) or prov_match.group(2) or ""
            keys = re.findall(r'(\w+)\s*:', body)
            for key in keys:
                comp.provides.append(VueProvideInjectInfo(key=key, kind="provide"))

        inj_match = self.INJECT_OPTION_PATTERN.search(content)
        if inj_match:
            array_body = inj_match.group(1)
            obj_body = inj_match.group(2)
            if array_body:
                keys = re.findall(r"['\"](\w+)['\"]", array_body)
            elif obj_body:
                keys = re.findall(r'(\w+)\s*:', obj_body)
            else:
                keys = []
            for key in keys:
                comp.injects.append(VueProvideInjectInfo(key=key, kind="inject"))

    def _extract_options_props(self, content: str, comp: VueComponentInfo) -> None:
        """Extract props from Options API props option."""
        props_match = self.PROPS_OPTION_PATTERN.search(content)
        if props_match:
            array_body = props_match.group(1)
            obj_body = props_match.group(2)
            if array_body:
                # Array syntax: props: ['title', 'likes']
                names = re.findall(r"['\"](\w+)['\"]", array_body)
                for name in names:
                    comp.props.append(VuePropInfo(name=name))
            elif obj_body:
                # Object syntax: props: { title: String, likes: { type: Number, default: 0 } }
                # Simple type: name: Type
                simple = re.findall(r'(\w+)\s*:\s*(String|Number|Boolean|Array|Object|Function|Symbol)\b', obj_body)
                for name, ptype in simple:
                    comp.props.append(VuePropInfo(name=name, type=ptype))

                # Complex: name: { type: ..., default: ..., required: ... }
                complex_pattern = re.finditer(
                    r'(\w+)\s*:\s*\{([^}]+)\}', obj_body
                )
                existing_names = {p.name for p in comp.props}
                for m in complex_pattern:
                    name = m.group(1)
                    if name in existing_names:
                        continue
                    body = m.group(2)
                    ptype = ""
                    type_match = re.search(r'type\s*:\s*(\w+)', body)
                    if type_match:
                        ptype = type_match.group(1)
                    required = bool(re.search(r'required\s*:\s*true', body))
                    has_validator = bool(re.search(r'validator\s*:', body))
                    default_match = re.search(r"default\s*:\s*(?:(?:\(\)\s*=>|function\s*\(\)\s*\{?\s*return)\s*)?([^\n,}]+)", body)
                    default_val = default_match.group(1).strip() if default_match else None
                    comp.props.append(VuePropInfo(
                        name=name, type=ptype, default_value=default_val,
                        required=required, has_validator=has_validator,
                    ))

    def _extract_options_emits(self, content: str, comp: VueComponentInfo) -> None:
        """Extract emits from Options API emits option or $emit calls."""
        # emits option: emits: ['update', 'change'] or emits: { ... }
        emits_match = re.search(r'emits\s*:\s*\[([^\]]+)\]', content)
        if emits_match:
            names = re.findall(r"['\"]([^'\"]+)['\"]", emits_match.group(1))
            for name in names:
                comp.emits.append(VueEmitInfo(name=name))
        else:
            emits_obj = re.search(r'emits\s*:\s*\{([^}]+)\}', content)
            if emits_obj:
                names = re.findall(r"['\"]?(\w+)['\"]?\s*:", emits_obj.group(1))
                for name in names:
                    comp.emits.append(VueEmitInfo(name=name))

        # Also find $emit calls
        emit_calls = re.findall(r"\$emit\s*\(\s*['\"]([^'\"]+)['\"]", content)
        existing = {e.name for e in comp.emits}
        for name in emit_calls:
            if name not in existing:
                comp.emits.append(VueEmitInfo(name=name))
                existing.add(name)

        # Also find emit() calls in <script setup>
        emit_setup = re.findall(r"emit\s*\(\s*['\"]([^'\"]+)['\"]", content)
        for name in emit_setup:
            if name not in existing:
                comp.emits.append(VueEmitInfo(name=name))
                existing.add(name)

    def _extract_template_components(self, content: str, comp: VueComponentInfo) -> None:
        """Extract child components used in template."""
        # PascalCase component tags: <MyComponent />
        pascal_comps = re.findall(r'<([A-Z][a-zA-Z0-9]+)[\s/>]', content)
        # kebab-case component tags: <my-component />
        kebab_comps = re.findall(r'<([a-z][a-z0-9]*(?:-[a-z0-9]+)+)[\s/>]', content)

        all_comps = set(pascal_comps + kebab_comps)
        # Exclude HTML5 elements
        html_tags = {'Transition', 'TransitionGroup', 'KeepAlive', 'Teleport', 'Suspense'}
        comp.components_used = list(all_comps - html_tags)

    def _extract_template_directives(self, content: str, comp: VueComponentInfo) -> None:
        """Extract custom directives used in template."""
        directive_pattern = re.findall(r'v-([a-z][a-z0-9-]+)', content)
        # Filter out built-in directives
        builtin = {'if', 'else', 'else-if', 'for', 'show', 'bind', 'on', 'model',
                    'slot', 'pre', 'once', 'text', 'html', 'cloak', 'memo'}
        custom = [d for d in directive_pattern if d not in builtin]
        comp.directives_used = list(set(custom))

    def _extract_composables(self, content: str, comp: VueComponentInfo) -> None:
        """Extract composable function calls (use* pattern)."""
        # use* function calls
        composable_calls = re.findall(r'\b(use[A-Z]\w+)\s*\(', content)
        # Exclude Vue built-in hooks that start with use
        vue_builtins = {'useSlots', 'useAttrs', 'useCssModule', 'useCssVars',
                        'useTemplateRef', 'useId'}
        comp.composables_used = list(set(composable_calls) - vue_builtins)

        # ref() / reactive() calls
        refs = re.findall(r'(?:const|let)\s+(\w+)\s*=\s*ref\s*(?:<[^>]*>)?\s*\(', content)
        comp.refs = refs

        reactives = re.findall(r'(?:const|let)\s+(\w+)\s*=\s*reactive\s*(?:<[^>]*>)?\s*\(', content)
        comp.reactives = reactives

    def _parse_props(self, type_param: Optional[str], args: str,
                     comp: VueComponentInfo) -> None:
        """Parse defineProps arguments."""
        if type_param:
            self._parse_typed_props(type_param, comp)
        elif args.strip():
            if args.strip().startswith('{'):
                # Object syntax defineProps({...})
                self._extract_options_props(f"props: {args}", comp)
            elif args.strip().startswith('['):
                names = re.findall(r"['\"](\w+)['\"]", args)
                for name in names:
                    comp.props.append(VuePropInfo(name=name))

    def _parse_typed_props(self, type_body: str, comp: VueComponentInfo) -> None:
        """Parse TypeScript typed props from defineProps<{ ... }>()."""
        # Extract prop: type pairs
        props = re.findall(r'(\w+)\s*(?:\?)?:\s*([^;\n]+)', type_body)
        for name, ptype in props:
            comp.props.append(VuePropInfo(
                name=name,
                type=ptype.strip().rstrip(','),
                required='?' not in type_body[type_body.index(name):type_body.index(name) + len(name) + 2],
            ))

    def _parse_emits(self, type_param: Optional[str], args: str,
                     comp: VueComponentInfo) -> None:
        """Parse defineEmits arguments."""
        if type_param:
            # Typed emits: defineEmits<{ (e: 'update', val: string): void }>()
            events = re.findall(r"['\"](\w+)['\"]", type_param)
            for name in events:
                comp.emits.append(VueEmitInfo(name=name))
        elif args.strip():
            if args.strip().startswith('['):
                names = re.findall(r"['\"](\w+)['\"]", args)
                for name in names:
                    comp.emits.append(VueEmitInfo(name=name))

    def _parse_slots(self, type_body: str, comp: VueComponentInfo) -> None:
        """Parse defineSlots<...>() type."""
        # Extract slot names from type
        slot_names = re.findall(r'(\w+)\s*(?:\?)?:', type_body)
        for name in slot_names:
            comp.slots.append(VueSlotInfo(
                name=name,
                is_default=(name == 'default'),
            ))
