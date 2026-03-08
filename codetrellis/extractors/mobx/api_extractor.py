"""
MobX API Extractor v1.0

Extracts MobX API patterns including:
- Import patterns (mobx, mobx-react, mobx-react-lite, mobx-utils)
- configure() settings (enforceActions, computedRequiresReaction, etc.)
- TypeScript types (IObservableValue, IComputedValue, IReactionDisposer, etc.)
- Ecosystem detection (mobx-state-tree, mobx-keystone, mobx-utils, etc.)
- Provider/inject patterns (legacy MobX React)
- observer() HOC (mobx-react / mobx-react-lite)
- useLocalObservable() hook
- useObserver() hook (deprecated)
- <Observer /> component
- toJS(), isObservable(), isObservableProp(), etc. utility functions

Part of CodeTrellis v4.51 - MobX Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MobXImportInfo:
    """Information about a MobX import statement."""
    name: str = ""
    file: str = ""
    line: int = 0
    source: str = ""  # 'mobx', 'mobx-react', 'mobx-react-lite', etc.
    imported_names: List[str] = field(default_factory=list)
    is_default: bool = False
    subpath: str = ""


@dataclass
class MobXConfigureInfo:
    """Information about a MobX configure() call."""
    name: str = ""
    file: str = ""
    line: int = 0
    enforce_actions: str = ""  # 'never', 'always', 'observed'
    computed_requires_reaction: bool = False
    reaction_requires_observable: bool = False
    observable_requires_reaction: bool = False
    disable_error_boundaries: bool = False
    safe_descriptors: bool = False
    use_proxies: str = ""  # 'always', 'never', 'ifavailable'


@dataclass
class MobXTypeInfo:
    """Information about a MobX TypeScript type usage."""
    name: str = ""
    file: str = ""
    line: int = 0
    type_category: str = ""  # 'observable', 'computed', 'action', 'reaction', 'utility'
    type_expression: str = ""


@dataclass
class MobXIntegrationInfo:
    """Information about MobX ecosystem integration."""
    name: str = ""
    file: str = ""
    line: int = 0
    integration_type: str = ""  # 'observer', 'Provider', 'inject', 'useLocalObservable', 'Observer', 'toJS', etc.
    library: str = ""  # 'mobx-react', 'mobx-react-lite', 'mobx-state-tree', etc.
    pattern: str = ""  # 'hoc', 'hook', 'component', 'utility'


class MobXApiExtractor:
    """Extracts MobX API patterns from source code."""

    # MobX import patterns
    IMPORT_PATTERN = re.compile(
        r'import\s+(?:'
        r'(?:\{([^}]+)\})'               # named imports
        r'|(\w+)'                         # default import
        r'|(?:(\w+)\s*,\s*\{([^}]+)\})'  # default + named
        r')\s+from\s+[\'"]'
        r'(mobx(?:-react(?:-lite)?|-state-tree|-keystone|-utils|-persist|'
        r'-react-form|[/\w-]*)?)'         # mobx-* packages
        r'[\'"]',
        re.MULTILINE,
    )

    # require() patterns for MobX
    REQUIRE_PATTERN = re.compile(
        r'(?:const|let|var)\s+(?:'
        r'\{([^}]+)\}'           # destructured
        r'|(\w+)'               # single var
        r')\s*=\s*require\s*\(\s*[\'"]'
        r'(mobx(?:-react(?:-lite)?|-state-tree|-keystone|-utils|-persist|'
        r'-react-form|[/\w-]*)?)'
        r'[\'"]\s*\)',
        re.MULTILINE,
    )

    # configure() call
    CONFIGURE = re.compile(
        r'configure\s*\(\s*\{([^}]*)\}',
        re.DOTALL,
    )

    # observer() HOC: observer(Component) or observer(function Component)
    OBSERVER_HOC = re.compile(
        r'(?:export\s+(?:default\s+)?)?(?:const|let|var)?\s*(\w+)\s*=\s*observer\s*\(',
    )

    # observer as decorator: @observer
    OBSERVER_DECORATOR = re.compile(
        r'@observer\s*\n?\s*(?:export\s+)?class\s+(\w+)',
    )

    # useLocalObservable(() => ({ ... }))
    USE_LOCAL_OBSERVABLE = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*useLocalObservable\s*\(',
    )

    # useObserver(() => jsx) — deprecated
    USE_OBSERVER = re.compile(
        r'useObserver\s*\(',
    )

    # <Observer>{() => ...}</Observer>
    OBSERVER_COMPONENT = re.compile(
        r'<Observer\s*>',
    )

    # Provider component (legacy mobx-react)
    PROVIDER = re.compile(
        r'<Provider\s+',
    )

    # inject() / @inject
    INJECT = re.compile(
        r'(?:@inject|inject)\s*\(\s*[\'"]?(\w+)',
    )

    # toJS(), isObservable(), isObservableProp(), isObservableMap(), etc.
    UTILITY_FUNCTIONS = re.compile(
        r'\b(toJS|isObservable|isObservableProp|isObservableMap|isObservableSet|'
        r'isObservableArray|isObservableObject|isAction|isComputed|isComputedProp|'
        r'isFlow|isFlowCancellationError|isBoxedObservable|'
        r'trace|spy|getDependencyTree|getObserverTree|getAtom|'
        r'untracked|transaction|comparer|createAtom)\s*\(',
    )

    # MobX TypeScript types
    MOBX_TYPES = re.compile(
        r':\s*(IObservableValue|IObservableArray|IObservableMap|IObservableSet|'
        r'IComputedValue|IReactionDisposer|IReactionPublic|IAutorunOptions|'
        r'IReactionOptions|IWhenOptions|Lambda|IAtom|IDepTreeNode|'
        r'ObservableMap|ObservableSet|IInterceptable|IListenable|'
        r'IValueWillChange|IValueDidChange|IArrayWillChange|IArrayDidChange|'
        r'IMapWillChange|IMapDidChange|ISetWillChange|ISetDidChange|'
        r'IObjectWillChange|IObjectDidChange|FlowReturn|CancellablePromise|'
        r'AnnotationsMap|Override|CreateObservableOptions)\b',
    )

    # Ecosystem packages
    ECOSYSTEM_PACKAGES = {
        'mobx': 'mobx',
        'mobx-react': 'mobx-react',
        'mobx-react-lite': 'mobx-react-lite',
        'mobx-state-tree': 'mobx-state-tree',
        'mobx-keystone': 'mobx-keystone',
        'mobx-utils': 'mobx-utils',
        'mobx-persist': 'mobx-persist',
        'mobx-persist-store': 'mobx-persist-store',
        'mobx-react-form': 'mobx-react-form',
        'mobx-react-router': 'mobx-react-router',
        'mobx-devtools': 'mobx-devtools',
        'mobx-logger': 'mobx-logger',
        'mst-middlewares': 'mst-middlewares',
        'mobx-angular': 'mobx-angular',
        'mobx-vue': 'mobx-vue',
        'mobx-vue-lite': 'mobx-vue-lite',
    }

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract all MobX API patterns from source content.

        Returns:
            Dict with keys:
            - imports: List[MobXImportInfo]
            - configures: List[MobXConfigureInfo]
            - types: List[MobXTypeInfo]
            - integrations: List[MobXIntegrationInfo]
            - detected_ecosystems: List[str]
        """
        imports: List[MobXImportInfo] = []
        configures: List[MobXConfigureInfo] = []
        types: List[MobXTypeInfo] = []
        integrations: List[MobXIntegrationInfo] = []
        detected_ecosystems: List[str] = []

        # Extract imports
        for match in self.IMPORT_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            named = match.group(1) or match.group(4) or ''
            default_name = match.group(2) or match.group(3) or ''
            source = match.group(5)

            imported_names = []
            if named:
                imported_names = [n.strip().split(' as ')[0].strip()
                                  for n in named.split(',') if n.strip()]
            if default_name:
                imported_names.insert(0, default_name)

            # Track ecosystem
            if source in self.ECOSYSTEM_PACKAGES:
                eco = self.ECOSYSTEM_PACKAGES[source]
                if eco not in detected_ecosystems:
                    detected_ecosystems.append(eco)

            info = MobXImportInfo(
                name=source,
                file=file_path,
                line=line_num,
                source=source,
                imported_names=imported_names,
                is_default=bool(default_name),
            )
            imports.append(info)

        # Extract require() patterns
        for match in self.REQUIRE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            named = match.group(1) or ''
            default_name = match.group(2) or ''
            source = match.group(3)

            imported_names = []
            if named:
                imported_names = [n.strip().split(':')[0].strip()
                                  for n in named.split(',') if n.strip()]
            if default_name:
                imported_names.insert(0, default_name)

            if source in self.ECOSYSTEM_PACKAGES:
                eco = self.ECOSYSTEM_PACKAGES[source]
                if eco not in detected_ecosystems:
                    detected_ecosystems.append(eco)

            info = MobXImportInfo(
                name=source,
                file=file_path,
                line=line_num,
                source=source,
                imported_names=imported_names,
                is_default=bool(default_name),
            )
            imports.append(info)

        # Extract configure() calls
        for match in self.CONFIGURE.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            config_body = match.group(1)

            enforce = ''
            if 'enforceActions' in config_body:
                ea_match = re.search(r'enforceActions\s*:\s*[\'"](\w+)[\'"]', config_body)
                if ea_match:
                    enforce = ea_match.group(1)

            info = MobXConfigureInfo(
                name='configure',
                file=file_path,
                line=line_num,
                enforce_actions=enforce,
                computed_requires_reaction='computedRequiresReaction' in config_body and 'true' in config_body,
                reaction_requires_observable='reactionRequiresObservable' in config_body and 'true' in config_body,
                observable_requires_reaction='observableRequiresReaction' in config_body and 'true' in config_body,
                disable_error_boundaries='disableErrorBoundaries' in config_body and 'true' in config_body,
                safe_descriptors='safeDescriptors' in config_body,
                use_proxies=re.search(r'useProxies\s*:\s*[\'"](\w+)[\'"]', config_body).group(1) if re.search(r'useProxies\s*:\s*[\'"](\w+)[\'"]', config_body) else '',
            )
            configures.append(info)

        # Extract observer() HOC
        for match in self.OBSERVER_HOC.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            comp_name = match.group(1)

            # Determine if from mobx-react or mobx-react-lite
            lib = 'mobx-react-lite' if 'mobx-react-lite' in content else 'mobx-react'

            info = MobXIntegrationInfo(
                name=comp_name,
                file=file_path,
                line=line_num,
                integration_type='observer',
                library=lib,
                pattern='hoc',
            )
            integrations.append(info)

        # Extract @observer decorator
        for match in self.OBSERVER_DECORATOR.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            class_name = match.group(1)

            info = MobXIntegrationInfo(
                name=class_name,
                file=file_path,
                line=line_num,
                integration_type='@observer',
                library='mobx-react',
                pattern='decorator',
            )
            integrations.append(info)

        # Extract useLocalObservable
        for match in self.USE_LOCAL_OBSERVABLE.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            var_name = match.group(1)

            lib = 'mobx-react-lite' if 'mobx-react-lite' in content else 'mobx-react'

            info = MobXIntegrationInfo(
                name=var_name,
                file=file_path,
                line=line_num,
                integration_type='useLocalObservable',
                library=lib,
                pattern='hook',
            )
            integrations.append(info)

        # Extract <Observer> component
        for match in self.OBSERVER_COMPONENT.finditer(content):
            line_num = content[:match.start()].count('\n') + 1

            info = MobXIntegrationInfo(
                name='Observer',
                file=file_path,
                line=line_num,
                integration_type='Observer',
                library='mobx-react' if 'mobx-react' in content else 'mobx-react-lite',
                pattern='component',
            )
            integrations.append(info)

        # Extract Provider (legacy)
        for match in self.PROVIDER.finditer(content):
            line_num = content[:match.start()].count('\n') + 1

            info = MobXIntegrationInfo(
                name='Provider',
                file=file_path,
                line=line_num,
                integration_type='Provider',
                library='mobx-react',
                pattern='component',
            )
            integrations.append(info)

        # Extract inject()
        for match in self.INJECT.finditer(content):
            line_num = content[:match.start()].count('\n') + 1

            info = MobXIntegrationInfo(
                name=match.group(1),
                file=file_path,
                line=line_num,
                integration_type='inject',
                library='mobx-react',
                pattern='hoc',
            )
            integrations.append(info)

        # Extract utility function usages
        for match in self.UTILITY_FUNCTIONS.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            func_name = match.group(1)

            info = MobXIntegrationInfo(
                name=func_name,
                file=file_path,
                line=line_num,
                integration_type=func_name,
                library='mobx',
                pattern='utility',
            )
            integrations.append(info)

        # Extract TypeScript type usages
        for match in self.MOBX_TYPES.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            type_name = match.group(1)

            # Categorize the type
            category = 'utility'
            if 'Observable' in type_name:
                category = 'observable'
            elif 'Computed' in type_name:
                category = 'computed'
            elif 'Reaction' in type_name or 'Autorun' in type_name or 'When' in type_name:
                category = 'reaction'
            elif 'Action' in type_name or 'Flow' in type_name:
                category = 'action'

            info = MobXTypeInfo(
                name=type_name,
                file=file_path,
                line=line_num,
                type_category=category,
                type_expression=type_name,
            )
            types.append(info)

        return {
            'imports': imports,
            'configures': configures,
            'types': types,
            'integrations': integrations,
            'detected_ecosystems': detected_ecosystems,
        }
