"""
Vue.js Directive Extractor for CodeTrellis

Extracts custom directive definitions from Vue.js source code:
- Custom directives (app.directive, local directive option)
- Directive hooks (created, beforeMount, mounted, beforeUpdate, updated,
                   beforeUnmount, unmounted - Vue 3.x)
- Vue 2.x directive hooks (bind, inserted, update, componentUpdated, unbind)
- Transition components and hooks
- v-model custom modifiers

Supports Vue 2.x through Vue 3.5+.

Part of CodeTrellis v4.34 - Vue.js Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class VueDirectiveInfo:
    """Information about a Vue custom directive."""
    name: str
    file: str = ""
    line_number: int = 0
    hooks: List[str] = field(default_factory=list)
    is_global: bool = False
    is_exported: bool = False
    has_argument: bool = False
    has_modifiers: bool = False


@dataclass
class VueTransitionInfo:
    """Information about a Vue transition usage."""
    name: str
    file: str = ""
    line_number: int = 0
    transition_type: str = ""  # transition, transition-group
    hooks: List[str] = field(default_factory=list)  # before-enter, enter, after-enter, etc.
    css_class: str = ""
    mode: str = ""  # out-in, in-out


class VueDirectiveExtractor:
    """
    Extracts Vue.js custom directive definitions from source code.

    Detects:
    - Global directives (app.directive('name', { ... }))
    - Local directives (directives: { focus: { ... } })
    - Directive function shorthand
    - Vue 3 directive hooks (created, beforeMount, mounted, etc.)
    - Vue 2 directive hooks (bind, inserted, update, etc.)
    - Transition components and their hooks
    """

    # Global directive registration: app.directive('name', ...)
    GLOBAL_DIRECTIVE_PATTERN = re.compile(
        r'(?:app|Vue)\s*\.\s*directive\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,',
        re.MULTILINE
    )

    # Local directives in Options API: directives: { name: { ... } }
    LOCAL_DIRECTIVES_PATTERN = re.compile(
        r'directives\s*:\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}',
        re.MULTILINE | re.DOTALL
    )

    # Exported directive: export const vFocus = { ... }
    EXPORTED_DIRECTIVE_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(v[A-Z]\w+)\s*=\s*\{',
        re.MULTILINE
    )

    # <script setup> local directive: const vFocus = { ... }
    SETUP_DIRECTIVE_PATTERN = re.compile(
        r'(?:const|let|var)\s+(v[A-Z]\w+)\s*=\s*(?:\{|function|\()',
        re.MULTILINE
    )

    # Vue 3 directive hooks
    VUE3_HOOKS = ['created', 'beforeMount', 'mounted', 'beforeUpdate',
                  'updated', 'beforeUnmount', 'unmounted', 'getSSRProps']

    # Vue 2 directive hooks
    VUE2_HOOKS = ['bind', 'inserted', 'update', 'componentUpdated', 'unbind']

    # Transition component
    TRANSITION_PATTERN = re.compile(
        r'<(?:Transition|transition|TransitionGroup|transition-group)\b([^>]*?)>',
        re.MULTILINE | re.DOTALL
    )

    # Transition hooks
    TRANSITION_HOOK_PATTERN = re.compile(
        r'@(before-enter|enter|after-enter|enter-cancelled|'
        r'before-leave|leave|after-leave|leave-cancelled|'
        r'before-appear|appear|after-appear|appear-cancelled)\s*=',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Vue directive definitions from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'directives', 'transitions'
        """
        result: Dict[str, Any] = {
            'directives': [],
            'transitions': [],
        }

        # Global directives
        for m in self.GLOBAL_DIRECTIVE_PATTERN.finditer(content):
            name = m.group(1)
            after = content[m.end():m.end() + 500]
            hooks = self._detect_hooks(after)
            result['directives'].append(VueDirectiveInfo(
                name=name,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                hooks=hooks,
                is_global=True,
            ))

        # Local directives
        local_match = self.LOCAL_DIRECTIVES_PATTERN.search(content)
        if local_match:
            body = local_match.group(1)
            directive_names = re.findall(r'(\w+)\s*:\s*\{', body)
            for name in directive_names:
                directive_body = body[body.index(name):]
                hooks = self._detect_hooks(directive_body)
                result['directives'].append(VueDirectiveInfo(
                    name=name,
                    file=file_path,
                    line_number=content[:local_match.start()].count('\n') + 1,
                    hooks=hooks,
                    is_global=False,
                ))

        # Exported directives (v-prefix convention: vFocus → focus)
        for m in self.EXPORTED_DIRECTIVE_PATTERN.finditer(content):
            v_name = m.group(1)
            # Convert vFocus to focus
            name = v_name[1].lower() + v_name[2:] if len(v_name) > 1 else v_name
            after = content[m.end():m.end() + 500]
            hooks = self._detect_hooks(after)
            existing_names = {d.name for d in result['directives']}
            if name not in existing_names:
                result['directives'].append(VueDirectiveInfo(
                    name=name,
                    file=file_path,
                    line_number=content[:m.start()].count('\n') + 1,
                    hooks=hooks,
                    is_exported='export' in content[max(0, m.start() - 10):m.start() + 10],
                ))

        # Transitions
        for m in self.TRANSITION_PATTERN.finditer(content):
            attrs = m.group(1) or ""
            tag_text = m.group(0)
            is_group = 'group' in tag_text.lower()

            name_match = re.search(r'name=[\'"]([^\'"]+)[\'"]', attrs)
            name = name_match.group(1) if name_match else ""

            mode_match = re.search(r'mode=[\'"]([^\'"]+)[\'"]', attrs)
            mode = mode_match.group(1) if mode_match else ""

            # Find hooks used
            after = content[m.end():m.end() + 1000]
            hooks = self.TRANSITION_HOOK_PATTERN.findall(after[:500])

            result['transitions'].append(VueTransitionInfo(
                name=name,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
                transition_type="transition-group" if is_group else "transition",
                hooks=hooks,
                mode=mode,
            ))

        return result

    def _detect_hooks(self, body: str) -> List[str]:
        """Detect directive hooks in body text."""
        hooks = []
        for hook in self.VUE3_HOOKS:
            if re.search(rf'\b{hook}\s*[:(]', body):
                hooks.append(hook)
        if not hooks:
            for hook in self.VUE2_HOOKS:
                if re.search(rf'\b{hook}\s*[:(]', body):
                    hooks.append(hook)
        return hooks
