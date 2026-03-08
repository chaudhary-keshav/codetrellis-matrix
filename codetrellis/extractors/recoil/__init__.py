"""
CodeTrellis Recoil Extractors Module v1.0

Provides comprehensive extractors for Recoil state management constructs:

Atom Extractor:
- RecoilAtomExtractor: atom(), atomFamily(), atom with default/dangerouslyAllowMutability,
                        primitive atoms, atom effects, TypeScript generics

Selector Extractor:
- RecoilSelectorExtractor: selector(), selectorFamily(), async selectors,
                            constSelector, errorSelector, noWait, waitForAll,
                            waitForAllSettled, waitForAny, waitForNone

Effect Extractor:
- RecoilEffectExtractor: Atom effects (onSet, setSelf, resetSelf, trigger,
                           storeID, parentStoreID_UNSTABLE), effect factories,
                           persistence effects (localStorage, sessionStorage, URL sync),
                           logging/validation/sync/broadcast effects

Hook Extractor:
- RecoilHookExtractor: useRecoilState, useRecoilValue, useSetRecoilState,
                        useResetRecoilState, useRecoilStateLoadable,
                        useRecoilValueLoadable, useRecoilCallback,
                        useRecoilTransaction_UNSTABLE, useRecoilBridgeAcrossReactRoots_UNSTABLE,
                        useRecoilRefresher_UNSTABLE, isRecoilValue

API Extractor:
- RecoilApiExtractor: Import patterns (recoil, recoil/native),
                       Snapshot API (snapshot_UNSTABLE, useRecoilSnapshot,
                       useGotoRecoilSnapshot, Snapshot, getLoadable/getPromise/
                       getInfo_UNSTABLE/getNodes_UNSTABLE/map/asyncMap/retain),
                       RecoilRoot/RecoilBridge, TypeScript types (RecoilState,
                       RecoilValueReadOnly, RecoilLoadable, AtomEffect,
                       SerializableParam, Loadable, DefaultValue, GetRecoilValue,
                       SetRecoilState, ResetRecoilState),
                       ecosystem detection (recoil, recoil-sync, recoil-relay,
                       recoil-nexus, recoil-persist, jotai/recoil adapter)

Part of CodeTrellis v4.50 - Recoil Framework Support
"""

from .atom_extractor import (
    RecoilAtomExtractor,
    RecoilAtomInfo,
    RecoilAtomFamilyInfo,
)
from .selector_extractor import (
    RecoilSelectorExtractor,
    RecoilSelectorInfo,
    RecoilSelectorFamilyInfo,
)
from .effect_extractor import (
    RecoilEffectExtractor,
    RecoilEffectInfo,
)
from .hook_extractor import (
    RecoilHookExtractor,
    RecoilHookUsageInfo,
    RecoilCallbackInfo,
)
from .api_extractor import (
    RecoilApiExtractor,
    RecoilImportInfo,
    RecoilSnapshotUsageInfo,
    RecoilTypeInfo,
)

__all__ = [
    # Atom
    "RecoilAtomExtractor",
    "RecoilAtomInfo",
    "RecoilAtomFamilyInfo",
    # Selector
    "RecoilSelectorExtractor",
    "RecoilSelectorInfo",
    "RecoilSelectorFamilyInfo",
    # Effect
    "RecoilEffectExtractor",
    "RecoilEffectInfo",
    # Hook
    "RecoilHookExtractor",
    "RecoilHookUsageInfo",
    "RecoilCallbackInfo",
    # API
    "RecoilApiExtractor",
    "RecoilImportInfo",
    "RecoilSnapshotUsageInfo",
    "RecoilTypeInfo",
]
