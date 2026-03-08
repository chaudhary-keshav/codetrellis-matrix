"""
NgRx Effect Extractor for CodeTrellis

Extracts NgRx effect patterns:
- createEffect() (class-based effects, NgRx v8+)
- Functional effects (NgRx v16+)
- Actions service and ofType operator
- RxJS operators (concatLatestFrom, switchMap, mergeMap, exhaustMap, concatMap)
- Non-dispatching effects (dispatch: false / {functional: true, dispatch: false})
- Effect lifecycle hooks (OnInitEffects, OnRunEffects, OnIdentifyEffects)
- ComponentStore effects (this.effect())
- Root effects registration (EffectsModule.forRoot, provideEffects)
- Error handling in effects (catchError, tap + EMPTY)

Supports:
- NgRx 4.x-7.x (legacy @Effect() decorator)
- NgRx 8.x-15.x (createEffect with class injection)
- NgRx 16.x-19.x (functional effects, inject-based)

Part of CodeTrellis v4.53 - NgRx Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class NgrxEffectInfo:
    """Information about an NgRx effect."""
    name: str
    file: str = ""
    line_number: int = 0
    action_types: List[str] = field(default_factory=list)  # ofType() args
    rxjs_operators: List[str] = field(default_factory=list)  # switchMap, mergeMap, etc.
    dispatches: bool = True  # False if dispatch: false
    is_functional: bool = False  # v16+ functional effect
    is_root_effect: bool = False
    has_error_handling: bool = False
    has_concatLatestFrom: bool = False
    lifecycle_hooks: List[str] = field(default_factory=list)
    effect_class: str = ""  # containing class name
    is_exported: bool = False


@dataclass
class NgrxComponentStoreEffectInfo:
    """Information about a ComponentStore effect."""
    name: str
    file: str = ""
    line_number: int = 0
    trigger_type: str = ""  # Observable, void, specific type
    rxjs_operators: List[str] = field(default_factory=list)
    has_error_handling: bool = False
    component_store_class: str = ""


class NgrxEffectExtractor:
    """
    Extracts NgRx effect patterns from source code.

    Detects:
    - createEffect() with actions$.pipe() pattern
    - Functional effects (v16+)
    - Legacy @Effect() decorator
    - ofType() action filtering
    - RxJS operator chains
    - Non-dispatching effects
    - Error handling patterns
    - Lifecycle hooks
    """

    # createEffect() pattern
    CREATE_EFFECT_PATTERN = re.compile(
        r'(?:readonly\s+)?(\w+)\$?\s*=\s*createEffect\s*\(',
        re.MULTILINE
    )

    # Legacy @Effect() decorator
    LEGACY_EFFECT_PATTERN = re.compile(
        r'@Effect\s*\(([^)]*)\)\s*\n\s*(?:readonly\s+)?(\w+)\$?\s*=',
        re.MULTILINE
    )

    # Functional effects (v16+)
    FUNCTIONAL_EFFECT_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*createEffect\s*\(\s*\(',
        re.MULTILINE
    )

    # ofType() for action filtering
    OF_TYPE_PATTERN = re.compile(
        r'ofType\s*\(\s*([\w\s,.\[\]]*?)\s*\)',
        re.MULTILINE
    )

    # RxJS operators used in effects
    RXJS_OPERATORS = [
        'switchMap', 'mergeMap', 'concatMap', 'exhaustMap',
        'map', 'tap', 'filter', 'catchError', 'withLatestFrom',
        'concatLatestFrom', 'debounceTime', 'throttleTime',
        'distinctUntilChanged', 'take', 'takeUntil', 'retry',
        'delay', 'share', 'shareReplay',
    ]

    RXJS_PATTERN = re.compile(
        r'\b(' + '|'.join(RXJS_OPERATORS) + r')\s*\(',
        re.MULTILINE
    )

    # dispatch: false
    NO_DISPATCH_PATTERN = re.compile(
        r'dispatch\s*:\s*false',
        re.MULTILINE
    )

    # Error handling in effects
    ERROR_HANDLING_PATTERN = re.compile(
        r'catchError|EMPTY|of\s*\(\s*\)|tap\s*\(\s*\{[^}]*error',
        re.MULTILINE
    )

    # concatLatestFrom
    CONCAT_LATEST_FROM_PATTERN = re.compile(
        r'concatLatestFrom\s*\(',
        re.MULTILINE
    )

    # Effect class declaration
    EFFECT_CLASS_PATTERN = re.compile(
        r'(?:export\s+)?class\s+(\w+(?:Effects?))\s+',
        re.MULTILINE
    )

    # Lifecycle hooks
    LIFECYCLE_PATTERN = re.compile(
        r'implements\s+[^{]*(OnInitEffects|OnRunEffects|OnIdentifyEffects)',
        re.MULTILINE
    )

    # ComponentStore effect
    CS_EFFECT_PATTERN = re.compile(
        r'(?:readonly\s+)?(\w+)\s*=\s*this\.effect\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # provideEffects / EffectsModule
    PROVIDE_EFFECTS_PATTERN = re.compile(
        r'(?:provideEffects|EffectsModule\s*\.\s*(?:forRoot|forFeature))\s*\(\s*\[?([^\])\n]*)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict:
        """Extract all NgRx effect information from source code."""
        result: Dict = {
            'effects': [],
            'component_store_effects': [],
            'registered_effects': [],
        }

        # Detect effect classes
        effect_classes = [m.group(1) for m in self.EFFECT_CLASS_PATTERN.finditer(content)]
        current_class = effect_classes[0] if effect_classes else ""

        # Lifecycle hooks
        lifecycle_hooks = [m.group(1) for m in self.LIFECYCLE_PATTERN.finditer(content)]

        # ── createEffect() ────────────────────────────────────
        for match in self.CREATE_EFFECT_PATTERN.finditer(content):
            name = match.group(1)
            line_number = content[:match.start()].count('\n') + 1

            # Get the effect body (up to 800 chars)
            block_start = match.start()
            block_end = min(block_start + 800, len(content))
            block = content[block_start:block_end]

            # Extract ofType actions
            action_types = []
            for ot_match in self.OF_TYPE_PATTERN.finditer(block):
                actions_text = ot_match.group(1)
                actions = [a.strip().rstrip(',') for a in actions_text.split(',') if a.strip()]
                action_types.extend(actions)

            # Extract RxJS operators
            rxjs_ops = list(set(m.group(1) for m in self.RXJS_PATTERN.finditer(block)))

            # Check dispatch: false
            dispatches = not bool(self.NO_DISPATCH_PATTERN.search(block))

            # Check error handling
            has_error_handling = bool(self.ERROR_HANDLING_PATTERN.search(block))

            # Check concatLatestFrom
            has_clf = bool(self.CONCAT_LATEST_FROM_PATTERN.search(block))

            # Check if functional (no `this.actions$`)
            is_functional = 'inject(' in block or ('Actions' in block and 'this.actions' not in block.lower())

            effect = NgrxEffectInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                action_types=action_types,
                rxjs_operators=rxjs_ops,
                dispatches=dispatches,
                is_functional=is_functional,
                has_error_handling=has_error_handling,
                has_concatLatestFrom=has_clf,
                lifecycle_hooks=lifecycle_hooks,
                effect_class=current_class,
                is_exported='export' in content[max(0, match.start() - 20):match.start()],
            )
            result['effects'].append(effect)

        # ── Legacy @Effect() ──────────────────────────────────
        for match in self.LEGACY_EFFECT_PATTERN.finditer(content):
            decorator_args = match.group(1)
            name = match.group(2)
            line_number = content[:match.start()].count('\n') + 1

            block_start = match.start()
            block_end = min(block_start + 800, len(content))
            block = content[block_start:block_end]

            action_types = []
            for ot_match in self.OF_TYPE_PATTERN.finditer(block):
                actions_text = ot_match.group(1)
                actions = [a.strip().rstrip(',') for a in actions_text.split(',') if a.strip()]
                action_types.extend(actions)

            rxjs_ops = list(set(m.group(1) for m in self.RXJS_PATTERN.finditer(block)))
            dispatches = 'dispatch: false' not in decorator_args

            effect = NgrxEffectInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                action_types=action_types,
                rxjs_operators=rxjs_ops,
                dispatches=dispatches,
                is_functional=False,
                has_error_handling=bool(self.ERROR_HANDLING_PATTERN.search(block)),
                effect_class=current_class,
            )
            result['effects'].append(effect)

        # ── ComponentStore effects ────────────────────────────
        for match in self.CS_EFFECT_PATTERN.finditer(content):
            name = match.group(1)
            trigger_type = match.group(2) or "void"
            line_number = content[:match.start()].count('\n') + 1

            block_start = match.start()
            block_end = min(block_start + 500, len(content))
            block = content[block_start:block_end]

            rxjs_ops = list(set(m.group(1) for m in self.RXJS_PATTERN.finditer(block)))

            cs_effect = NgrxComponentStoreEffectInfo(
                name=name,
                file=file_path,
                line_number=line_number,
                trigger_type=trigger_type,
                rxjs_operators=rxjs_ops,
                has_error_handling=bool(self.ERROR_HANDLING_PATTERN.search(block)),
            )
            result['component_store_effects'].append(cs_effect)

        # ── Registered effects ────────────────────────────────
        for match in self.PROVIDE_EFFECTS_PATTERN.finditer(content):
            effects_text = match.group(1)
            registered = [e.strip().rstrip(',') for e in effects_text.split(',') if e.strip() and e.strip() != ']']
            result['registered_effects'].extend(registered)

        return result
