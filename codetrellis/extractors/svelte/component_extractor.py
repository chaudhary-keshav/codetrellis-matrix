"""
Svelte Component Extractor for CodeTrellis

Extracts component definitions from Svelte source code:
- .svelte component files with <script>, <style>, and template
- Props via export let (Svelte 3/4) and $props rune (Svelte 5)
- Events via createEventDispatcher (Svelte 3/4) and callback props (Svelte 5)
- Slots (default and named, with slot props / snippet blocks in Svelte 5)
- Bindings (bind:value, bind:this, bind:group, etc.)
- Transitions (transition:, in:, out:, animate:)
- Actions (use: directive)
- Component composition ({@render}, <svelte:component>, <svelte:self>)
- Context API (setContext, getContext)
- Svelte 5 runes ($state, $derived, $effect, $props, $bindable, $inspect)
- TypeScript support (<script lang="ts">)
- Module context (<script context="module"> / <script module>)

Supports Svelte 3.x through 5.x:
- Svelte 3.x: export let props, createEventDispatcher, $$props, $$restProps
- Svelte 4.x: improved TypeScript, satisfies, const generics
- Svelte 5.x: Runes ($state, $derived, $effect, $props, $bindable, $inspect),
              Snippets ({#snippet}, {@render}), event handlers as props,
              fine-grained reactivity, $effect.pre, $effect.root, $state.raw

Part of CodeTrellis v4.35 - Svelte/SvelteKit Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SveltePropInfo:
    """Information about a Svelte component prop."""
    name: str
    type: str = ""  # TypeScript type
    default_value: Optional[str] = None
    required: bool = False
    is_bindable: bool = False  # Svelte 5 $bindable()
    is_rune: bool = False  # declared via $props()
    line_number: int = 0


@dataclass
class SvelteEventInfo:
    """Information about a Svelte component event."""
    name: str
    detail_type: str = ""  # TypeScript type for event detail
    is_dispatcher: bool = False  # via createEventDispatcher
    is_callback_prop: bool = False  # Svelte 5 callback-based events
    line_number: int = 0


@dataclass
class SvelteSlotInfo:
    """Information about a Svelte component slot."""
    name: str
    is_default: bool = False
    props: List[str] = field(default_factory=list)  # slot props / let: bindings
    is_snippet: bool = False  # Svelte 5 {#snippet}
    line_number: int = 0


@dataclass
class SvelteBindingInfo:
    """Information about a Svelte binding."""
    name: str  # e.g. 'value', 'this', 'group', 'checked'
    target: str = ""  # component or element name
    is_two_way: bool = True
    line_number: int = 0


@dataclass
class SvelteComponentInfo:
    """Information about a Svelte component definition."""
    name: str
    file: str = ""
    line_number: int = 0
    is_page: bool = False  # +page.svelte
    is_layout: bool = False  # +layout.svelte
    is_error: bool = False  # +error.svelte

    # Script info
    has_script: bool = False
    has_module_script: bool = False  # <script context="module"> / <script module>
    script_lang: str = ""  # ts, js, or empty
    has_style: bool = False
    style_lang: str = ""  # css, scss, less, postcss
    style_global: bool = False  # :global()

    # Svelte version features
    svelte_version: str = ""  # inferred minimum version
    uses_runes: bool = False  # Svelte 5 runes detected
    uses_snippets: bool = False  # Svelte 5 snippets

    # Props & Events
    props: List[SveltePropInfo] = field(default_factory=list)
    events: List[SvelteEventInfo] = field(default_factory=list)
    slots: List[SvelteSlotInfo] = field(default_factory=list)
    bindings: List[SvelteBindingInfo] = field(default_factory=list)

    # Template features
    has_each_block: bool = False
    has_if_block: bool = False
    has_await_block: bool = False
    has_key_block: bool = False
    transitions: List[str] = field(default_factory=list)  # transition names
    animations: List[str] = field(default_factory=list)  # animate: names
    actions_used: List[str] = field(default_factory=list)  # use: names
    components_used: List[str] = field(default_factory=list)  # child components
    special_elements: List[str] = field(default_factory=list)  # svelte:window, etc.

    # Svelte 5 Runes
    state_runes: List[str] = field(default_factory=list)  # $state variable names
    derived_runes: List[str] = field(default_factory=list)  # $derived variable names
    effect_count: int = 0  # number of $effect() calls
    snippets: List[str] = field(default_factory=list)  # {#snippet} names

    # Context
    contexts_set: List[str] = field(default_factory=list)  # setContext keys
    contexts_get: List[str] = field(default_factory=list)  # getContext keys

    # Imports
    imports: List[str] = field(default_factory=list)  # imported modules


class SvelteComponentExtractor:
    """
    Extracts Svelte component information from .svelte files.

    Handles:
    - <script> and <script context="module"> / <script module> blocks
    - Props (export let, $props rune)
    - Events (createEventDispatcher, callback props)
    - Slots (default, named, snippets)
    - Bindings (bind:)
    - Transitions, animations, actions
    - Svelte 5 runes
    - TypeScript support
    """

    # Patterns for SFC block extraction
    SCRIPT_PATTERN = re.compile(
        r'<script(?P<attrs>[^>]*)>(?P<content>.*?)</script>',
        re.DOTALL
    )
    STYLE_PATTERN = re.compile(
        r'<style(?P<attrs>[^>]*)>(?P<content>.*?)</style>',
        re.DOTALL
    )

    # Svelte 3/4 prop patterns
    EXPORT_LET_PATTERN = re.compile(
        r'export\s+let\s+(\w+)\s*(?::\s*([^=;\n]+?))?\s*(?:=\s*([^;\n]+))?\s*[;\n]',
        re.MULTILINE
    )
    EXPORT_CONST_PATTERN = re.compile(
        r'export\s+const\s+(\w+)\s*(?::\s*([^=;]+?))?\s*=\s*([^;]+);',
        re.MULTILINE
    )

    # Svelte 5 rune patterns
    PROPS_RUNE_PATTERN = re.compile(
        r'let\s*\{([^}]+)\}\s*(?::\s*[^=]+?)?\s*=\s*\$props\s*\(\s*\)',
        re.MULTILINE
    )
    STATE_RUNE_PATTERN = re.compile(
        r'let\s+(\w+)\s*=\s*\$state\s*[<(]',
        re.MULTILINE
    )
    STATE_RUNE_SIMPLE_PATTERN = re.compile(
        r'let\s+(\w+)\s*=\s*\$state\s*\(',
        re.MULTILINE
    )
    DERIVED_RUNE_PATTERN = re.compile(
        r'let\s+(\w+)\s*=\s*\$derived\s*[.(]',
        re.MULTILINE
    )
    EFFECT_RUNE_PATTERN = re.compile(
        r'\$effect(?:\.pre|\.root)?\s*\(',
        re.MULTILINE
    )
    BINDABLE_RUNE_PATTERN = re.compile(
        r'\$bindable\s*\(',
        re.MULTILINE
    )
    INSPECT_RUNE_PATTERN = re.compile(
        r'\$inspect\s*\(',
        re.MULTILINE
    )

    # Event dispatcher pattern
    EVENT_DISPATCHER_PATTERN = re.compile(
        r'(?:const|let)\s+(\w+)\s*=\s*createEventDispatcher\s*(?:<([^>]+)>)?\s*\(\s*\)',
        re.MULTILINE
    )
    DISPATCH_CALL_PATTERN = re.compile(
        r'(\w+)\s*\(\s*[\'"](\w+)[\'"]',
        re.MULTILINE
    )

    # Slot patterns
    SLOT_PATTERN = re.compile(
        r'<slot(?:\s+name=["\'](\w+)["\'])?\s*(?:(?:let:(\w+)=[^>]*|[^>])*)/?\s*>',
        re.DOTALL
    )
    SNIPPET_PATTERN = re.compile(
        r'\{#snippet\s+(\w+)\s*\(([^)]*)\)\}',
        re.MULTILINE
    )
    RENDER_PATTERN = re.compile(
        r'\{@render\s+(\w+)\s*\(',
        re.MULTILINE
    )

    # Binding patterns
    BINDING_PATTERN = re.compile(
        r'bind:(\w+)',
        re.MULTILINE
    )

    # Transition/animation/action patterns
    TRANSITION_PATTERN = re.compile(
        r'(?:transition|in|out):(\w+)',
        re.MULTILINE
    )
    ANIMATE_PATTERN = re.compile(
        r'animate:(\w+)',
        re.MULTILINE
    )
    ACTION_PATTERN = re.compile(
        r'use:(\w+)',
        re.MULTILINE
    )

    # Special elements
    SPECIAL_ELEMENT_PATTERN = re.compile(
        r'<(svelte:(?:window|document|body|head|element|component|self|fragment|options))',
        re.MULTILINE
    )

    # Component usage
    COMPONENT_USAGE_PATTERN = re.compile(
        r'<([A-Z]\w+)',
        re.MULTILINE
    )

    # Import patterns
    IMPORT_PATTERN = re.compile(
        r'import\s+(?:(?:\{[^}]+\}|\w+)\s+from\s+)?[\'"]([^\'"]+)[\'"]',
        re.MULTILINE
    )

    # Template block patterns
    EACH_BLOCK_PATTERN = re.compile(r'\{#each\b', re.MULTILINE)
    IF_BLOCK_PATTERN = re.compile(r'\{#if\b', re.MULTILINE)
    AWAIT_BLOCK_PATTERN = re.compile(r'\{#await\b', re.MULTILINE)
    KEY_BLOCK_PATTERN = re.compile(r'\{#key\b', re.MULTILINE)

    # Context patterns
    SET_CONTEXT_PATTERN = re.compile(
        r'setContext\s*\(\s*[\'"]([^\'"]+)[\'"]',
        re.MULTILINE
    )
    GET_CONTEXT_PATTERN = re.compile(
        r'getContext\s*\(\s*[\'"]([^\'"]+)[\'"]',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Svelte component information from source content.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'components' list
        """
        components = []

        # Determine component name from file path
        name = "Component"
        if file_path:
            import os
            base = os.path.basename(file_path)
            if base.endswith('.svelte'):
                name = base[:-7]  # Remove .svelte extension

        comp = SvelteComponentInfo(name=name, file=file_path)

        # Detect page/layout/error from filename
        if '+page' in name or name == '+page':
            comp.is_page = True
        if '+layout' in name or name == '+layout':
            comp.is_layout = True
        if '+error' in name or name == '+error':
            comp.is_error = True

        # Extract script blocks
        scripts = self._extract_scripts(content)
        main_script = scripts.get('main', '')
        module_script = scripts.get('module', '')
        script_attrs = scripts.get('main_attrs', '')
        module_attrs = scripts.get('module_attrs', '')

        comp.has_script = bool(main_script.strip())
        comp.has_module_script = bool(module_script.strip())

        # Detect script language
        if 'lang="ts"' in script_attrs or "lang='ts'" in script_attrs:
            comp.script_lang = "ts"
        elif 'lang="typescript"' in script_attrs or "lang='typescript'" in script_attrs:
            comp.script_lang = "ts"

        # Check module script lang too
        if not comp.script_lang and (
            'lang="ts"' in module_attrs or "lang='ts'" in module_attrs
        ):
            comp.script_lang = "ts"

        # Style detection
        style_match = self.STYLE_PATTERN.search(content)
        if style_match:
            comp.has_style = True
            style_attrs = style_match.group('attrs')
            if 'lang="scss"' in style_attrs:
                comp.style_lang = "scss"
            elif 'lang="less"' in style_attrs:
                comp.style_lang = "less"
            elif 'lang="postcss"' in style_attrs:
                comp.style_lang = "postcss"
            elif 'lang="sass"' in style_attrs:
                comp.style_lang = "sass"
            else:
                comp.style_lang = "css"
            if ':global' in style_attrs or ':global' in (style_match.group('content') or ''):
                comp.style_global = True

        all_script = main_script + "\n" + module_script

        # Extract props
        self._extract_props(all_script, comp)

        # Extract events
        self._extract_events(all_script, comp)

        # Extract slots and snippets
        self._extract_slots(content, comp)

        # Extract bindings
        self._extract_bindings(content, comp)

        # Extract transitions, animations, actions
        self._extract_template_features(content, comp)

        # Extract component usage
        self._extract_component_usage(content, comp)

        # Extract special elements
        self._extract_special_elements(content, comp)

        # Extract imports
        self._extract_imports(all_script, comp)

        # Extract context usage
        self._extract_context(all_script, comp)

        # Extract Svelte 5 runes
        self._extract_runes(all_script, comp)

        # Detect template blocks
        comp.has_each_block = bool(self.EACH_BLOCK_PATTERN.search(content))
        comp.has_if_block = bool(self.IF_BLOCK_PATTERN.search(content))
        comp.has_await_block = bool(self.AWAIT_BLOCK_PATTERN.search(content))
        comp.has_key_block = bool(self.KEY_BLOCK_PATTERN.search(content))

        # Detect Svelte version
        comp.svelte_version = self._detect_svelte_version(all_script, content)

        comp.line_number = 1
        components.append(comp)

        return {'components': components}

    def _extract_scripts(self, content: str) -> Dict[str, str]:
        """Extract main and module script blocks."""
        result = {'main': '', 'module': '', 'main_attrs': '', 'module_attrs': ''}

        for match in self.SCRIPT_PATTERN.finditer(content):
            attrs = match.group('attrs')
            script_content = match.group('content')

            if 'context="module"' in attrs or 'module' in attrs.split():
                result['module'] = script_content
                result['module_attrs'] = attrs
            else:
                result['main'] = script_content
                result['main_attrs'] = attrs

        return result

    def _extract_props(self, script: str, comp: SvelteComponentInfo):
        """Extract props from script content."""
        # Svelte 3/4: export let
        for match in self.EXPORT_LET_PATTERN.finditer(script):
            name = match.group(1)
            type_str = (match.group(2) or '').strip()
            default = match.group(3)

            prop = SveltePropInfo(
                name=name,
                type=type_str,
                default_value=default.strip() if default else None,
                required=default is None,
                is_rune=False,
                line_number=script[:match.start()].count('\n') + 1,
            )
            comp.props.append(prop)

        # Svelte 5: $props() destructuring
        for match in self.PROPS_RUNE_PATTERN.finditer(script):
            destructured = match.group(1)
            for prop_str in destructured.split(','):
                prop_str = prop_str.strip()
                if not prop_str:
                    continue

                # Handle default values: name = default
                is_bindable = '$bindable()' in prop_str
                prop_str = prop_str.replace('$bindable()', '').strip()

                parts = prop_str.split('=', 1)
                prop_name = parts[0].strip().rstrip(':').strip()

                # Handle TypeScript type annotations
                type_str = ''
                if ':' in parts[0]:
                    name_type = parts[0].split(':', 1)
                    prop_name = name_type[0].strip()
                    type_str = name_type[1].strip()

                default_val = parts[1].strip() if len(parts) > 1 else None

                # Skip rest props
                if prop_name.startswith('...'):
                    continue

                prop = SveltePropInfo(
                    name=prop_name,
                    type=type_str,
                    default_value=default_val,
                    required=default_val is None and not is_bindable,
                    is_bindable=is_bindable,
                    is_rune=True,
                    line_number=script[:match.start()].count('\n') + 1,
                )
                comp.props.append(prop)
            comp.uses_runes = True

    def _extract_events(self, script: str, comp: SvelteComponentInfo):
        """Extract event definitions."""
        # Svelte 3/4: createEventDispatcher
        dispatchers = {}
        for match in self.EVENT_DISPATCHER_PATTERN.finditer(script):
            var_name = match.group(1)
            type_param = match.group(2) or ''
            dispatchers[var_name] = type_param

        # Find dispatch calls
        for var_name in dispatchers:
            pattern = re.compile(rf'{re.escape(var_name)}\s*\(\s*[\'"](\w+)[\'"]', re.MULTILINE)
            for call_match in pattern.finditer(script):
                event_name = call_match.group(1)
                event = SvelteEventInfo(
                    name=event_name,
                    is_dispatcher=True,
                    line_number=script[:call_match.start()].count('\n') + 1,
                )
                comp.events.append(event)

        # Svelte 5: callback props as events (detected from $props with on* naming)
        for prop in comp.props:
            if prop.name.startswith('on') and len(prop.name) > 2 and prop.name[2].isupper():
                event = SvelteEventInfo(
                    name=prop.name[2:].lower(),
                    is_callback_prop=True,
                    line_number=prop.line_number,
                )
                comp.events.append(event)

    def _extract_slots(self, content: str, comp: SvelteComponentInfo):
        """Extract slot definitions from template."""
        # Traditional slots
        for match in self.SLOT_PATTERN.finditer(content):
            slot_name = match.group(1) or 'default'
            slot = SvelteSlotInfo(
                name=slot_name,
                is_default=slot_name == 'default',
                is_snippet=False,
                line_number=content[:match.start()].count('\n') + 1,
            )
            comp.slots.append(slot)

        # Svelte 5: snippet blocks
        for match in self.SNIPPET_PATTERN.finditer(content):
            snippet_name = match.group(1)
            params = match.group(2).strip()
            snippet = SvelteSlotInfo(
                name=snippet_name,
                is_default=False,
                is_snippet=True,
                props=([p.strip() for p in params.split(',') if p.strip()] if params else []),
                line_number=content[:match.start()].count('\n') + 1,
            )
            comp.slots.append(snippet)
            comp.uses_snippets = True
            comp.snippets.append(snippet_name)

    def _extract_bindings(self, content: str, comp: SvelteComponentInfo):
        """Extract bind: directives from template."""
        seen = set()
        for match in self.BINDING_PATTERN.finditer(content):
            binding_name = match.group(1)
            if binding_name not in seen:
                seen.add(binding_name)
                binding = SvelteBindingInfo(
                    name=binding_name,
                    line_number=content[:match.start()].count('\n') + 1,
                )
                comp.bindings.append(binding)

    def _extract_template_features(self, content: str, comp: SvelteComponentInfo):
        """Extract transitions, animations, and actions from template."""
        # Transitions
        seen_transitions = set()
        for match in self.TRANSITION_PATTERN.finditer(content):
            name = match.group(1)
            if name not in seen_transitions:
                seen_transitions.add(name)
                comp.transitions.append(name)

        # Animations
        seen_anims = set()
        for match in self.ANIMATE_PATTERN.finditer(content):
            name = match.group(1)
            if name not in seen_anims:
                seen_anims.add(name)
                comp.animations.append(name)

        # Actions
        seen_actions = set()
        for match in self.ACTION_PATTERN.finditer(content):
            name = match.group(1)
            if name not in seen_actions:
                seen_actions.add(name)
                comp.actions_used.append(name)

    def _extract_component_usage(self, content: str, comp: SvelteComponentInfo):
        """Extract child component usage from template."""
        seen = set()
        for match in self.COMPONENT_USAGE_PATTERN.finditer(content):
            name = match.group(1)
            if name not in seen and not name.startswith('Svelte'):
                seen.add(name)
                comp.components_used.append(name)

    def _extract_special_elements(self, content: str, comp: SvelteComponentInfo):
        """Extract svelte: special elements."""
        seen = set()
        for match in self.SPECIAL_ELEMENT_PATTERN.finditer(content):
            elem = match.group(1)
            if elem not in seen:
                seen.add(elem)
                comp.special_elements.append(elem)

    def _extract_imports(self, script: str, comp: SvelteComponentInfo):
        """Extract import statements."""
        for match in self.IMPORT_PATTERN.finditer(script):
            module = match.group(1)
            comp.imports.append(module)

    def _extract_context(self, script: str, comp: SvelteComponentInfo):
        """Extract context API usage."""
        for match in self.SET_CONTEXT_PATTERN.finditer(script):
            comp.contexts_set.append(match.group(1))
        for match in self.GET_CONTEXT_PATTERN.finditer(script):
            comp.contexts_get.append(match.group(1))

    def _extract_runes(self, script: str, comp: SvelteComponentInfo):
        """Extract Svelte 5 rune usage."""
        # $state
        for match in self.STATE_RUNE_SIMPLE_PATTERN.finditer(script):
            comp.state_runes.append(match.group(1))
            comp.uses_runes = True

        # $derived
        for match in self.DERIVED_RUNE_PATTERN.finditer(script):
            comp.derived_runes.append(match.group(1))
            comp.uses_runes = True

        # $effect
        comp.effect_count = len(self.EFFECT_RUNE_PATTERN.findall(script))
        if comp.effect_count > 0:
            comp.uses_runes = True

        # $inspect
        if self.INSPECT_RUNE_PATTERN.search(script):
            comp.uses_runes = True

    def _detect_svelte_version(self, script: str, content: str) -> str:
        """Detect minimum Svelte version from features used."""
        # Svelte 5 features
        if any([
            self.STATE_RUNE_SIMPLE_PATTERN.search(script),
            self.DERIVED_RUNE_PATTERN.search(script),
            self.EFFECT_RUNE_PATTERN.search(script),
            self.PROPS_RUNE_PATTERN.search(script),
            self.BINDABLE_RUNE_PATTERN.search(script),
            self.INSPECT_RUNE_PATTERN.search(script),
            self.SNIPPET_PATTERN.search(content),
            self.RENDER_PATTERN.search(content),
        ]):
            return '5.0'

        # Svelte 4 features (const generics, enhanced TypeScript)
        if re.search(r'satisfies\s+\w+', script):
            return '4.0'

        # Svelte 3 (default)
        if script.strip():
            return '3.0'

        return ''
