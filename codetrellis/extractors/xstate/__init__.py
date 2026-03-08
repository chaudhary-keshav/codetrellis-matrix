"""
CodeTrellis XState Extractors Module v1.0

Provides comprehensive extractors for XState state machine constructs:

Machine Extractor:
- XstateMachineExtractor: createMachine/Machine (v3-v4), setup().createMachine (v5),
                           machine IDs, initial states, context types, machine options,
                           predictableActionArguments (v4), machine version,
                           TypeScript generics and typegen

State Extractor:
- XstateStateExtractor: State nodes (atomic, compound, parallel, final, history),
                         transitions (event → target), entry/exit actions,
                         invoke (services/actors), after (delayed transitions),
                         always (eventless transitions), tags, meta, descriptions

Action Extractor:
- XstateActionExtractor: assign, send/sendTo, raise, log, stop, cancel,
                          pure, choose, forwardTo, escalate, respond,
                          custom actions, action creators, inline actions,
                          enqueueActions (v5), emit (v5)

Guard Extractor:
- XstateGuardExtractor: cond (v4) / guard (v5), inline guards,
                         named guards, guard objects, not/and/or combinators (v5),
                         stateIn guards, custom guard functions

API Extractor:
- XstateApiExtractor: xstate, @xstate/react (useMachine, useActor, useSelector,
                       useActorRef, useInterpret), @xstate/vue (useMachine),
                       @xstate/svelte (useMachine), @xstate/solid,
                       @xstate/inspect, @xstate/test, @xstate/graph,
                       @xstate/store, @statelyai/inspect,
                       createActor/interpret, TypeScript typegen,
                       spawn, fromPromise/fromObservable/fromCallback/fromTransition

Part of CodeTrellis v4.55 - XState Framework Support
"""

from .machine_extractor import (
    XstateMachineExtractor,
    XstateMachineInfo,
)
from .state_extractor import (
    XstateStateExtractor,
    XstateStateNodeInfo,
    XstateTransitionInfo,
    XstateInvokeInfo,
)
from .action_extractor import (
    XstateActionExtractor,
    XstateActionInfo,
)
from .guard_extractor import (
    XstateGuardExtractor,
    XstateGuardInfo,
)
from .api_extractor import (
    XstateApiExtractor,
    XstateImportInfo,
    XstateActorInfo,
    XstateTypegenInfo,
)

__all__ = [
    # Machine
    "XstateMachineExtractor",
    "XstateMachineInfo",
    # State
    "XstateStateExtractor",
    "XstateStateNodeInfo",
    "XstateTransitionInfo",
    "XstateInvokeInfo",
    # Action
    "XstateActionExtractor",
    "XstateActionInfo",
    # Guard
    "XstateGuardExtractor",
    "XstateGuardInfo",
    # API
    "XstateApiExtractor",
    "XstateImportInfo",
    "XstateActorInfo",
    "XstateTypegenInfo",
]
