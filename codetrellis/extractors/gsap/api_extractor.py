"""
GSAP API Extractor — Imports, integrations, TypeScript types, context, matchMedia.

Extracts:
- ESM imports (gsap, gsap/*, @gsap/*)
- CommonJS require (gsap, TweenMax)
- CDN script tags
- Dynamic imports
- Framework integrations (React, Vue, Angular, Svelte, Next.js, etc.)
- TypeScript type imports
- gsap.context() (v3.11+)
- gsap.matchMedia() (v3.11+)
- Version detection from import paths and API usage

v4.77: Full GSAP API support.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class GsapImportInfo:
    """A GSAP import statement."""
    source: str = ""                 # Package path (e.g., 'gsap', 'gsap/ScrollTrigger')
    file: str = ""
    line_number: int = 0
    named_imports: List[str] = field(default_factory=list)
    default_import: str = ""
    import_type: str = ""            # 'esm', 'cjs', 'cdn', 'dynamic'
    is_type_import: bool = False


@dataclass
class GsapIntegrationInfo:
    """A framework integration with GSAP."""
    name: str = ""                   # Framework name
    file: str = ""
    line_number: int = 0
    integration_type: str = ""       # 'react', 'vue', 'angular', 'svelte', 'next', 'nuxt', 'gatsby'
    details: str = ""


@dataclass
class GsapTypeInfo:
    """A GSAP TypeScript type reference."""
    type_name: str = ""
    file: str = ""
    line_number: int = 0
    source: str = ""


@dataclass
class GsapContextInfo:
    """A gsap.context() usage (v3.11+)."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    has_scope: bool = False
    has_cleanup: bool = False


@dataclass
class GsapMatchMediaInfo:
    """A gsap.matchMedia() usage (v3.11+)."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    breakpoints: List[str] = field(default_factory=list)
    has_cleanup: bool = False


# Framework integration patterns
FRAMEWORK_INTEGRATIONS = {
    'react': re.compile(
        r"(?:from\s+['\"]react['\"]|useRef|useEffect|useLayoutEffect|useGSAP)"
    ),
    'vue': re.compile(
        r"(?:from\s+['\"]vue['\"]|onMounted|ref\s*\(|@gsap/vue)"
    ),
    'angular': re.compile(
        r"(?:from\s+['\"]@angular|ngOnInit|ngAfterViewInit|@gsap/angular)"
    ),
    'svelte': re.compile(
        r"(?:from\s+['\"]svelte['\"]|onMount|<script|@gsap/svelte)"
    ),
    'next': re.compile(
        r"(?:from\s+['\"]next|getServerSideProps|getStaticProps|use\s+client)"
    ),
    'nuxt': re.compile(
        r"(?:from\s+['\"]nuxt|defineNuxtPlugin|nuxt-gsap-module)"
    ),
    'gatsby': re.compile(
        r"(?:from\s+['\"]gatsby|gatsby-plugin)"
    ),
    '@gsap/react': re.compile(
        r"(?:from\s+['\"]@gsap/react['\"]|useGSAP)"
    ),
}

# Known GSAP TypeScript types
GSAP_TYPES = [
    'gsap', 'GSAPTween', 'GSAPTimeline', 'GSAPCallback',
    'ScrollTrigger', 'ScrollTriggerInstance', 'ScrollTriggerConfig',
    'Draggable', 'Observer', 'Flip', 'SplitText',
    'TweenVars', 'GSAPConfig', 'EaseFunction',
    'MotionPathPlugin', 'DrawSVGPlugin', 'MorphSVGPlugin',
    'TweenTarget', 'GSAPPluginScope',
]


class GsapAPIExtractor:
    """
    Extracts GSAP API patterns: imports, integrations, types, context.
    """

    # ESM import
    ESM_IMPORT = re.compile(
        r"import\s+(?:(?:type\s+)?\{([^}]*)\}|(\w+))\s+from\s+['\"]([^'\"]*gsap[^'\"]*)['\"]",
        re.MULTILINE
    )

    # Additional ESM: import gsap from 'gsap'
    ESM_DEFAULT = re.compile(
        r"import\s+(\w+)\s+from\s+['\"]gsap['\"]",
        re.MULTILINE
    )

    # CommonJS require
    CJS_REQUIRE = re.compile(
        r"(?:const|let|var)\s+(?:\{([^}]*)\}|(\w+))\s*=\s*require\s*\(\s*['\"]([^'\"]*gsap[^'\"]*|TweenMax|TweenLite|TimelineMax|TimelineLite)['\"]",
        re.MULTILINE
    )

    # Legacy global script includes
    CDN_SCRIPT = re.compile(
        r'<script[^>]*src\s*=\s*["\']([^"\']*(?:gsap|greensock|TweenMax|TimelineMax)[^"\']*)["\']',
        re.IGNORECASE
    )

    # Dynamic import
    DYNAMIC_IMPORT = re.compile(
        r"import\s*\(\s*['\"]([^'\"]*gsap[^'\"]*)['\"]",
    )

    # gsap.context()
    CONTEXT_PATTERN = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?gsap\.context\s*\(',
        re.MULTILINE
    )

    # gsap.matchMedia()
    MATCH_MEDIA = re.compile(
        r'(?:(?:const|let|var)\s+(\w+)\s*=\s*)?gsap\.matchMedia\s*\(',
        re.MULTILINE
    )

    # matchMedia breakpoint pattern
    BREAKPOINT_PATTERN = re.compile(
        r'["\'](\([^"\']+\))["\']'
    )

    # TypeScript type import
    TYPE_IMPORT = re.compile(
        r'import\s+type\s+\{([^}]*)\}\s+from\s+["\']([^"\']*gsap[^"\']*)["\']',
        re.MULTILINE
    )

    # v1/v2 legacy imports
    LEGACY_IMPORT = re.compile(
        r"(?:import|require)\s*[\({]?\s*['\"]?(TweenMax|TweenLite|TimelineMax|TimelineLite|TweenNano)['\"]?",
        re.MULTILINE
    )

    # useGSAP hook (@gsap/react)
    USE_GSAP = re.compile(
        r'useGSAP\s*\('
    )

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract all GSAP API constructs."""
        imports = []
        integrations = []
        types = []
        contexts = []
        match_medias = []
        version_info = {}

        # ── ESM imports ─────────────────────────────────────────
        for match in self.ESM_IMPORT.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            named = match.group(1)
            default = match.group(2)
            source = match.group(3)

            named_list = [n.strip().split(' as ')[0].strip()
                          for n in (named or '').split(',') if n.strip()]

            is_type = 'import type' in content[max(0, match.start()-20):match.start()+20]

            imports.append(GsapImportInfo(
                source=source,
                file=file_path,
                line_number=line_num,
                named_imports=named_list,
                default_import=default or '',
                import_type='esm',
                is_type_import=is_type,
            ))

            # Version hint from source path
            if '/dist/' in source or 'gsap-trial' in source:
                version_info['package'] = 'gsap-v3'
            elif source == 'gsap':
                version_info['package'] = 'gsap-v3'

        # ── Default import ──────────────────────────────────────
        for match in self.ESM_DEFAULT.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            # Avoid duplicates from ESM_IMPORT
            already = any(i.default_import == match.group(1) and i.source == 'gsap' for i in imports)
            if not already:
                imports.append(GsapImportInfo(
                    source='gsap',
                    file=file_path,
                    line_number=line_num,
                    default_import=match.group(1),
                    import_type='esm',
                ))
                version_info['package'] = 'gsap-v3'

        # ── CJS require ─────────────────────────────────────────
        for match in self.CJS_REQUIRE.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            named = match.group(1)
            default = match.group(2)
            source = match.group(3)

            named_list = [n.strip() for n in (named or '').split(',') if n.strip()]

            imports.append(GsapImportInfo(
                source=source,
                file=file_path,
                line_number=line_num,
                named_imports=named_list,
                default_import=default or '',
                import_type='cjs',
            ))

        # ── CDN scripts ─────────────────────────────────────────
        for match in self.CDN_SCRIPT.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            url = match.group(1)
            imports.append(GsapImportInfo(
                source=url,
                file=file_path,
                line_number=line_num,
                import_type='cdn',
            ))

        # ── Dynamic imports ─────────────────────────────────────
        for match in self.DYNAMIC_IMPORT.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            imports.append(GsapImportInfo(
                source=match.group(1),
                file=file_path,
                line_number=line_num,
                import_type='dynamic',
            ))

        # ── Legacy imports ──────────────────────────────────────
        for match in self.LEGACY_IMPORT.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            class_name = match.group(1)
            already = any(class_name in i.named_imports or class_name == i.default_import for i in imports)
            if not already:
                imports.append(GsapImportInfo(
                    source=class_name,
                    file=file_path,
                    line_number=line_num,
                    default_import=class_name,
                    import_type='legacy',
                ))
                version_info['package'] = 'gsap-v1'

        # ── Type imports ────────────────────────────────────────
        for match in self.TYPE_IMPORT.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            names = [n.strip() for n in match.group(1).split(',') if n.strip()]
            source = match.group(2)
            for name in names:
                types.append(GsapTypeInfo(
                    type_name=name,
                    file=file_path,
                    line_number=line_num,
                    source=source,
                ))

        # ── Framework integrations ──────────────────────────────
        for fw_name, pattern in FRAMEWORK_INTEGRATIONS.items():
            if pattern.search(content):
                line_num = 0
                m = pattern.search(content)
                if m:
                    line_num = content[:m.start()].count('\n') + 1
                integrations.append(GsapIntegrationInfo(
                    name=fw_name,
                    file=file_path,
                    line_number=line_num,
                    integration_type=fw_name.replace('@gsap/', ''),
                    details='',
                ))

        # ── gsap.context() ──────────────────────────────────────
        for match in self.CONTEXT_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            ctx = content[match.start():match.start() + 500]
            contexts.append(GsapContextInfo(
                name=match.group(1) or 'anonymous',
                file=file_path,
                line_number=line_num,
                has_scope='scope' in ctx[:200] or '.current' in ctx[:200],
                has_cleanup='.revert()' in ctx or 'return ()' in ctx,
            ))
            version_info.setdefault('min_version', 'v3.11')

        # ── gsap.matchMedia() ───────────────────────────────────
        for match in self.MATCH_MEDIA.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            ctx = content[match.start():match.start() + 1000]
            breakpoints = [bp.group(1) for bp in self.BREAKPOINT_PATTERN.finditer(ctx)]
            match_medias.append(GsapMatchMediaInfo(
                name=match.group(1) or 'anonymous',
                file=file_path,
                line_number=line_num,
                breakpoints=breakpoints[:10],
                has_cleanup='.revert()' in ctx,
            ))
            version_info.setdefault('min_version', 'v3.11')

        # ── useGSAP hook ───────────────────────────────────────
        if self.USE_GSAP.search(content):
            integrations.append(GsapIntegrationInfo(
                name='@gsap/react',
                file=file_path,
                line_number=0,
                integration_type='react',
                details='useGSAP hook',
            ))

        # ── Version detection ───────────────────────────────────
        if not version_info.get('package'):
            if re.search(r'gsap\.(to|from|fromTo|set|timeline|registerPlugin|context|matchMedia)\s*\(', content):
                version_info['package'] = 'gsap-v3'
            elif re.search(r'(TweenMax|TweenLite|TimelineMax|TimelineLite)\b', content):
                version_info['package'] = 'gsap-v1'

        return {
            'imports': imports[:50],
            'integrations': integrations[:20],
            'types': types[:30],
            'contexts': contexts[:20],
            'match_medias': match_medias[:10],
            'version_info': version_info,
        }
