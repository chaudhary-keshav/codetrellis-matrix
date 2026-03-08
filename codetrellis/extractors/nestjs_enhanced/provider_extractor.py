"""
NestJS Provider Extractor - Per-file extraction of @Injectable() providers and DI.

Supports:
- @Injectable() decorator detection
- Constructor injection (constructor(private readonly service: ServiceType))
- @Inject() token injection
- @Optional() optional dependencies
- Custom provider patterns: useClass, useValue, useFactory, useExisting
- Scope (DEFAULT, REQUEST, TRANSIENT)
- NestJS 7.x through 10.x patterns
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class NestInjectableInfo:
    """An @Injectable() class (service, guard, interceptor, pipe, etc.)."""
    class_name: str
    file: str = ""
    line_number: int = 0
    scope: str = "DEFAULT"  # DEFAULT, REQUEST, TRANSIENT
    injectable_type: str = ""  # service, guard, interceptor, pipe, middleware, filter, gateway
    implements: List[str] = field(default_factory=list)
    injections: List[str] = field(default_factory=list)  # Constructor injected dependencies


@dataclass
class NestInjectionInfo:
    """A constructor dependency injection."""
    class_name: str  # The class containing the injection
    param_name: str = ""
    param_type: str = ""
    inject_token: str = ""  # @Inject(TOKEN) token name
    is_optional: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class NestCustomProviderInfo:
    """A custom provider definition."""
    provide_token: str
    file: str = ""
    line_number: int = 0
    strategy: str = ""  # useClass, useValue, useFactory, useExisting
    strategy_target: str = ""
    inject_deps: List[str] = field(default_factory=list)


class NestProviderExtractor:
    """Extracts NestJS provider and DI information from a single file."""

    # @Injectable() decorator
    INJECTABLE_PATTERN = re.compile(
        r'@Injectable\s*\(\s*(?:\{\s*scope\s*:\s*Scope\.(\w+)\s*\})?\s*\)'
    )

    # Class with implements
    CLASS_PATTERN = re.compile(
        r'(?:export\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?'
        r'(?:\s+implements\s+([\w,\s<>]+))?\s*\{'
    )

    # Constructor pattern
    CONSTRUCTOR_PATTERN = re.compile(
        r'constructor\s*\(([^)]*)\)',
        re.DOTALL
    )

    # @Inject() decorator in constructor params
    INJECT_PATTERN = re.compile(
        r"@Inject\s*\(\s*(['\"`]?[\w.]+['\"`]?)\s*\)"
    )

    # @Optional() decorator
    OPTIONAL_PATTERN = re.compile(r'@Optional\s*\(\s*\)')

    # Constructor param: private readonly name: Type
    PARAM_PATTERN = re.compile(
        r'(?:private|protected|public)?\s*(?:readonly\s+)?(\w+)\s*:\s*([\w<>,\s|]+)'
    )

    # Custom provider patterns
    CUSTOM_PROVIDER_PATTERN = re.compile(
        r'\{\s*provide\s*:\s*(\w+(?:\.\w+)?|[\'"`][^\'"`]+[\'"`])',
        re.DOTALL
    )

    # NestJS interface implementations → type classification
    TYPE_MAP = {
        'CanActivate': 'guard',
        'NestInterceptor': 'interceptor',
        'PipeTransform': 'pipe',
        'NestMiddleware': 'middleware',
        'ExceptionFilter': 'filter',
        'OnModuleInit': 'service',
        'OnModuleDestroy': 'service',
        'OnApplicationBootstrap': 'service',
        'OnApplicationShutdown': 'service',
    }

    def extract(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract provider and DI information from a NestJS source file."""
        injectables: List[NestInjectableInfo] = []
        injections: List[NestInjectionInfo] = []
        custom_providers: List[NestCustomProviderInfo] = []
        lines = content.split('\n')

        # Find @Injectable() classes
        for inj_match in self.INJECTABLE_PATTERN.finditer(content):
            scope = inj_match.group(1) or 'DEFAULT'
            line_num = content[:inj_match.start()].count('\n') + 1

            # Find class definition after decorator
            rest = content[inj_match.end():]
            class_match = self.CLASS_PATTERN.search(rest[:500])
            if not class_match:
                continue

            class_name = class_match.group(1)
            implements_str = class_match.group(2) or ''
            implements = [i.strip() for i in implements_str.split(',') if i.strip()]

            # Determine injectable type
            injectable_type = 'service'
            for iface, itype in self.TYPE_MAP.items():
                if iface in implements_str:
                    injectable_type = itype
                    break

            # Also check filename for type hints
            lower_path = file_path.lower()
            if '.guard.' in lower_path:
                injectable_type = 'guard'
            elif '.interceptor.' in lower_path:
                injectable_type = 'interceptor'
            elif '.pipe.' in lower_path:
                injectable_type = 'pipe'
            elif '.middleware.' in lower_path:
                injectable_type = 'middleware'
            elif '.filter.' in lower_path:
                injectable_type = 'filter'
            elif '.gateway.' in lower_path:
                injectable_type = 'gateway'

            # Extract constructor injections
            class_body = rest[class_match.end():]
            ctor_match = self.CONSTRUCTOR_PATTERN.search(class_body[:2000])
            injection_names = []
            if ctor_match:
                ctor_params = ctor_match.group(1)
                injection_names = self._extract_injections(
                    ctor_params, class_name, file_path, line_num, injections
                )

            injectables.append(NestInjectableInfo(
                class_name=class_name,
                file=file_path,
                line_number=line_num,
                scope=scope,
                injectable_type=injectable_type,
                implements=implements,
                injections=injection_names,
            ))

        # Find custom providers
        for cp_match in self.CUSTOM_PROVIDER_PATTERN.finditer(content):
            token = cp_match.group(1).strip("'\"` ")
            line_num = content[:cp_match.start()].count('\n') + 1
            block = content[cp_match.start():cp_match.start() + 500]

            strategy = ''
            target = ''
            inject_deps: List[str] = []

            if 'useClass' in block:
                strategy = 'useClass'
                m = re.search(r'useClass\s*:\s*(\w+)', block)
                target = m.group(1) if m else ''
            elif 'useFactory' in block:
                strategy = 'useFactory'
                m = re.search(r'useFactory\s*:\s*(\w+|(?:async\s+)?\([^)]*\)\s*=>)', block)
                target = m.group(1).strip() if m else 'factory'
                inj_m = re.search(r'inject\s*:\s*\[([^\]]*)\]', block)
                if inj_m:
                    inject_deps = [d.strip() for d in inj_m.group(1).split(',') if d.strip()]
            elif 'useValue' in block:
                strategy = 'useValue'
                m = re.search(r'useValue\s*:\s*([^,}\n]+)', block)
                target = m.group(1).strip() if m else ''
            elif 'useExisting' in block:
                strategy = 'useExisting'
                m = re.search(r'useExisting\s*:\s*(\w+)', block)
                target = m.group(1) if m else ''

            if strategy:
                custom_providers.append(NestCustomProviderInfo(
                    provide_token=token,
                    file=file_path,
                    line_number=line_num,
                    strategy=strategy,
                    strategy_target=target,
                    inject_deps=inject_deps,
                ))

        return {
            "injectables": injectables,
            "injections": injections,
            "custom_providers": custom_providers,
        }

    def _extract_injections(
        self,
        ctor_params: str,
        class_name: str,
        file_path: str,
        base_line: int,
        injections: List[NestInjectionInfo],
    ) -> List[str]:
        """Extract constructor injection parameters."""
        names = []
        # Split by comma at depth 0
        params = self._split_params(ctor_params)

        for param in params:
            param = param.strip()
            if not param:
                continue

            inject_token = ''
            is_optional = bool(self.OPTIONAL_PATTERN.search(param))
            inj_match = self.INJECT_PATTERN.search(param)
            if inj_match:
                inject_token = inj_match.group(1).strip("'\"` ")

            p_match = self.PARAM_PATTERN.search(param)
            if p_match:
                param_name = p_match.group(1)
                param_type = p_match.group(2).strip()
                names.append(param_type)

                injections.append(NestInjectionInfo(
                    class_name=class_name,
                    param_name=param_name,
                    param_type=param_type,
                    inject_token=inject_token,
                    is_optional=is_optional,
                    file=file_path,
                    line_number=base_line,
                ))

        return names

    def _split_params(self, params_str: str) -> List[str]:
        """Split constructor parameters at top-level commas."""
        parts = []
        depth = 0
        current = ''
        for ch in params_str:
            if ch in ('(', '<', '[', '{'):
                depth += 1
                current += ch
            elif ch in (')', '>', ']', '}'):
                depth -= 1
                current += ch
            elif ch == ',' and depth == 0:
                parts.append(current)
                current = ''
            else:
                current += ch
        if current.strip():
            parts.append(current)
        return parts
