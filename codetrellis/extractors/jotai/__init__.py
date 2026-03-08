"""
CodeTrellis Jotai Extractors Module v1.0

Provides comprehensive extractors for Jotai atomic state management constructs:

Atom Extractor:
- JotaiAtomExtractor: atom(), atomWithDefault(), atomFamily(),
                       atomWithStorage(), atomWithHash(), atomWithLocation(),
                       primitive atoms, writable atoms, read-only atoms,
                       async atoms, resettable atoms (atomWithReset, RESET),
                       atom creators, TypeScript generics

Selector Extractor:
- JotaiSelectorExtractor: Derived atoms (read-only computed), selectAtom,
                           focusAtom (jotai-optics), splitAtom (jotai-utils),
                           loadable (jotai-utils), unwrap (jotai-utils),
                           atomWithReducer, atomWithObservable

Middleware Extractor:
- JotaiMiddlewareExtractor: atomWithStorage (jotai-utils), atomWithObservable,
                             atomWithMachine (jotai-xstate), atomEffect,
                             onMount (atom.onMount), atomWithProxy (jotai-valtio),
                             atomWithImmer (jotai-immer), atomWithLocation

Action Extractor:
- JotaiActionExtractor: useAtom, useAtomValue, useSetAtom, useStore,
                         atom write functions (set, get, reset),
                         Provider-scoped atoms, store.get/store.set/store.sub,
                         atomWithReducer dispatch patterns

API Extractor:
- JotaiApiExtractor: Import patterns (jotai, jotai/utils, jotai/react,
                      jotai-utils, jotai-devtools, jotai-immer, jotai-optics,
                      jotai-xstate, jotai-tanstack-query, jotai-trpc,
                      jotai-molecules, jotai-scope, jotai-effect),
                      TypeScript types (Atom, WritableAtom, PrimitiveAtom,
                      SetStateAction, Getter, Setter, ExtractAtomValue),
                      React integration (Provider, useHydrateAtoms, useStore),
                      DevTools integration (DevTools component, useAtomsDebugValue),
                      deprecated API detection, migration patterns

Part of CodeTrellis v4.49 - Jotai Framework Support
"""

from .atom_extractor import (
    JotaiAtomExtractor,
    JotaiAtomInfo,
    JotaiAtomFamilyInfo,
    JotaiResettableAtomInfo,
)
from .selector_extractor import (
    JotaiSelectorExtractor,
    JotaiDerivedAtomInfo,
    JotaiSelectAtomInfo,
    JotaiFocusAtomInfo,
)
from .middleware_extractor import (
    JotaiMiddlewareExtractor,
    JotaiStorageAtomInfo,
    JotaiEffectInfo,
    JotaiMachineAtomInfo,
)
from .action_extractor import (
    JotaiActionExtractor,
    JotaiHookUsageInfo,
    JotaiWriteFnInfo,
    JotaiStoreUsageInfo,
)
from .api_extractor import (
    JotaiApiExtractor,
    JotaiImportInfo,
    JotaiIntegrationInfo,
    JotaiTypeInfo,
)

__all__ = [
    # Atom
    "JotaiAtomExtractor",
    "JotaiAtomInfo",
    "JotaiAtomFamilyInfo",
    "JotaiResettableAtomInfo",
    # Selector
    "JotaiSelectorExtractor",
    "JotaiDerivedAtomInfo",
    "JotaiSelectAtomInfo",
    "JotaiFocusAtomInfo",
    # Middleware
    "JotaiMiddlewareExtractor",
    "JotaiStorageAtomInfo",
    "JotaiEffectInfo",
    "JotaiMachineAtomInfo",
    # Action
    "JotaiActionExtractor",
    "JotaiHookUsageInfo",
    "JotaiWriteFnInfo",
    "JotaiStoreUsageInfo",
    # API
    "JotaiApiExtractor",
    "JotaiImportInfo",
    "JotaiIntegrationInfo",
    "JotaiTypeInfo",
]
