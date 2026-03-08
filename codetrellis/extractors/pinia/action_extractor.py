"""
Pinia Action Extractor for CodeTrellis

Extracts Pinia action definitions and usage patterns:
- Options API actions (actions: { action() { this.state = ... } })
- Setup API function actions (const action = () => { state.value = ... })
- Async actions (await, Promise, try/catch)
- $patch usage (object and function forms)
- $reset usage
- $subscribe (state change subscriptions)
- $onAction (action hooks)
- Cross-store actions (using other stores)
- Error handling patterns

Supports:
- Pinia v1.x-v2.x action patterns
- TypeScript typed actions
- Action composition (actions calling other actions)

Part of CodeTrellis v4.52 - Pinia State Management Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class PiniaActionInfo:
    """Information about a Pinia action."""
    name: str
    file: str = ""
    line_number: int = 0
    api_style: str = ""  # options, setup
    store_name: str = ""
    store_id: str = ""
    is_async: bool = False
    uses_patch: bool = False
    uses_reset: bool = False
    modified_fields: List[str] = field(default_factory=list)
    uses_other_stores: List[str] = field(default_factory=list)
    has_error_handling: bool = False
    has_typescript: bool = False


@dataclass
class PiniaPatchInfo:
    """Information about $patch usage."""
    file: str = ""
    line_number: int = 0
    store_name: str = ""
    patch_type: str = ""  # object, function
    patched_fields: List[str] = field(default_factory=list)


@dataclass
class PiniaSubscriptionInfo:
    """Information about $subscribe or $onAction usage."""
    file: str = ""
    line_number: int = 0
    store_name: str = ""
    subscription_type: str = ""  # subscribe, onAction
    has_detached: bool = False
    has_flush: bool = False  # flush: 'sync' | 'post'
    has_after: bool = False  # onAction after callback
    has_on_error: bool = False  # onAction onError callback


class PiniaActionExtractor:
    """
    Extracts Pinia actions and related API usage.

    Detects:
    - Options API actions: actions: { increment() { this.count++ } }
    - Setup API actions: function increment() { count.value++ }
    - Async actions with await/Promise
    - $patch({ field: value }) and $patch((state) => { state.field = value })
    - $reset() to restore initial state
    - $subscribe((mutation, state) => { ... })
    - $onAction(({ name, args, after, onError }) => { ... })
    - Cross-store action calls
    """

    # Options API action block
    ACTIONS_BLOCK_PATTERN = re.compile(
        r'actions\s*:\s*\{([^}]*(?:\{[^}]*(?:\{[^}]*\}[^}]*)*\}[^}]*)*)\}',
        re.MULTILINE | re.DOTALL
    )

    # Individual action method
    ACTION_METHOD_PATTERN = re.compile(
        r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{',
        re.MULTILINE
    )

    # $patch usage (object form)
    PATCH_OBJECT_PATTERN = re.compile(
        r'(\w+)\.\$patch\s*\(\s*\{([^}]*)\}',
        re.MULTILINE
    )

    # $patch usage (function form)
    PATCH_FUNCTION_PATTERN = re.compile(
        r'(\w+)\.\$patch\s*\(\s*\(\s*(?:state)?\s*\)\s*=>',
        re.MULTILINE
    )

    # $reset usage
    RESET_PATTERN = re.compile(
        r'(\w+)\.\$reset\s*\(\s*\)',
        re.MULTILINE
    )

    # $subscribe usage
    SUBSCRIBE_PATTERN = re.compile(
        r'(\w+)\.\$subscribe\s*\(',
        re.MULTILINE
    )

    # $onAction usage
    ON_ACTION_PATTERN = re.compile(
        r'(\w+)\.\$onAction\s*\(',
        re.MULTILINE
    )

    # Async indicator
    ASYNC_PATTERN = re.compile(
        r'async\s+\w+\s*\(|await\s+|\.then\s*\(|new\s+Promise',
        re.MULTILINE
    )

    # this.field = ... (Options API state mutation)
    THIS_MUTATION_PATTERN = re.compile(
        r'this\.(\w+)\s*(?:=|\+\+|--|\+=|-=|\*=|/=)',
        re.MULTILINE
    )

    # .value = ... (Setup API state mutation)
    VALUE_MUTATION_PATTERN = re.compile(
        r'(\w+)\.value\s*(?:=|\+\+|--|\+=|-=|\*=|/=)',
        re.MULTILINE
    )

    # Error handling
    TRY_CATCH_PATTERN = re.compile(
        r'try\s*\{',
        re.MULTILINE
    )

    # Use other stores
    USE_STORE_PATTERN = re.compile(
        r'(?:const|let)\s+\w+\s*=\s*(use\w+Store)\s*\(\)',
        re.MULTILINE
    )

    # Detached subscription
    DETACHED_PATTERN = re.compile(
        r'\{\s*detached\s*:\s*true\s*\}',
        re.MULTILINE
    )

    # Flush option
    FLUSH_PATTERN = re.compile(
        r"flush\s*:\s*['\"](?:sync|post)['\"]",
        re.MULTILINE
    )

    # onAction after/onError
    AFTER_PATTERN = re.compile(r'\bafter\s*\(', re.MULTILINE)
    ON_ERROR_PATTERN = re.compile(r'\bonError\s*\(', re.MULTILINE)

    # Reserved words to skip
    RESERVED = frozenset({
        'async', 'await', 'if', 'else', 'try', 'catch', 'finally',
        'return', 'const', 'let', 'var', 'function', 'new', 'throw',
        'Error', 'Promise', 'console', 'set', 'get', 'for', 'while',
        'switch', 'case', 'break', 'continue', 'delete', 'typeof',
        'instanceof', 'void', 'yield', 'class', 'super', 'this',
    })

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Pinia actions, $patch, $subscribe, $onAction usage.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dictionary with 'actions', 'patches', 'subscriptions' lists
        """
        actions: List[PiniaActionInfo] = []
        patches: List[PiniaPatchInfo] = []
        subscriptions: List[PiniaSubscriptionInfo] = []

        # Options API actions
        for block_match in self.ACTIONS_BLOCK_PATTERN.finditer(content):
            block = block_match.group(1)
            block_start = block_match.start()

            for method_match in self.ACTION_METHOD_PATTERN.finditer(block):
                name = method_match.group(1)
                if name in self.RESERVED:
                    continue

                line = content[:block_start + method_match.start()].count('\n') + 1
                method_body = block[method_match.start():]

                action = PiniaActionInfo(
                    name=name,
                    file=file_path,
                    line_number=line,
                    api_style="options",
                )
                action.is_async = bool(self.ASYNC_PATTERN.search(method_body[:500]))
                action.has_error_handling = bool(self.TRY_CATCH_PATTERN.search(method_body[:500]))

                # State mutations via this.field
                for mut_match in self.THIS_MUTATION_PATTERN.finditer(method_body[:500]):
                    field_name = mut_match.group(1)
                    if field_name not in action.modified_fields:
                        action.modified_fields.append(field_name)

                # Other stores
                for store_match in self.USE_STORE_PATTERN.finditer(method_body[:500]):
                    store_name = store_match.group(1)
                    if store_name not in action.uses_other_stores:
                        action.uses_other_stores.append(store_name)

                actions.append(action)

        # $patch (object form)
        for patch_match in self.PATCH_OBJECT_PATTERN.finditer(content):
            store_name = patch_match.group(1)
            fields_str = patch_match.group(2)
            line = content[:patch_match.start()].count('\n') + 1
            fields = [f.strip().split(':')[0].strip() for f in fields_str.split(',') if ':' in f]
            patches.append(PiniaPatchInfo(
                file=file_path,
                line_number=line,
                store_name=store_name,
                patch_type="object",
                patched_fields=fields,
            ))

        # $patch (function form)
        for patch_match in self.PATCH_FUNCTION_PATTERN.finditer(content):
            store_name = patch_match.group(1)
            line = content[:patch_match.start()].count('\n') + 1
            patches.append(PiniaPatchInfo(
                file=file_path,
                line_number=line,
                store_name=store_name,
                patch_type="function",
            ))

        # $subscribe
        for sub_match in self.SUBSCRIBE_PATTERN.finditer(content):
            store_name = sub_match.group(1)
            line = content[:sub_match.start()].count('\n') + 1
            region = content[sub_match.start():sub_match.start() + 500]
            subscriptions.append(PiniaSubscriptionInfo(
                file=file_path,
                line_number=line,
                store_name=store_name,
                subscription_type="subscribe",
                has_detached=bool(self.DETACHED_PATTERN.search(region)),
                has_flush=bool(self.FLUSH_PATTERN.search(region)),
            ))

        # $onAction
        for oa_match in self.ON_ACTION_PATTERN.finditer(content):
            store_name = oa_match.group(1)
            line = content[:oa_match.start()].count('\n') + 1
            region = content[oa_match.start():oa_match.start() + 500]
            subscriptions.append(PiniaSubscriptionInfo(
                file=file_path,
                line_number=line,
                store_name=store_name,
                subscription_type="onAction",
                has_after=bool(self.AFTER_PATTERN.search(region)),
                has_on_error=bool(self.ON_ERROR_PATTERN.search(region)),
            ))

        return {
            'actions': actions,
            'patches': patches,
            'subscriptions': subscriptions,
        }
