"""
Emotion API Extractor for CodeTrellis

Extracts Emotion framework API patterns from JS/TS source code.
Covers:
- @emotion/cache: createCache, CacheProvider, custom nonce/prepend/container
- @emotion/server: extractCritical, extractCriticalToChunks,
                    renderStylesToString, renderStylesToNodeStream,
                    constructStyleTagsFromChunks (Next.js / Express SSR)
- @emotion/babel-plugin / babel-plugin-emotion: configuration and usage
- @swc/plugin-emotion (SWC compiler integration)
- @emotion/jest: snapshot serializer, toHaveStyleRule matcher
- Pragma: /** @jsxImportSource @emotion/react */ or /** @jsx jsx */
- Next.js compiler.emotion integration
- Gatsby gatsby-plugin-emotion
- Remix integration

Part of CodeTrellis v4.43 - Emotion CSS-in-JS Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class EmotionCacheInfo:
    """Information about @emotion/cache usage."""
    file: str = ""
    line_number: int = 0
    cache_key: str = ""         # The key passed to createCache
    has_nonce: bool = False
    has_prepend: bool = False
    has_container: bool = False
    has_stylis_plugins: bool = False
    is_provider: bool = False   # Used with CacheProvider


@dataclass
class EmotionSSRPatternInfo:
    """Information about Emotion SSR patterns."""
    file: str = ""
    line_number: int = 0
    method: str = ""            # extractCritical, extractCriticalToChunks,
                                # renderStylesToString, renderStylesToNodeStream,
                                # constructStyleTagsFromChunks
    framework: str = ""         # next, gatsby, remix, express
    has_streaming: bool = False
    has_critical_extraction: bool = False
    has_rehydration: bool = False


@dataclass
class EmotionBabelConfigInfo:
    """Information about Emotion babel/SWC plugin configuration."""
    file: str = ""
    line_number: int = 0
    plugin_type: str = ""       # babel-plugin-emotion, @emotion/babel-plugin, @swc/plugin-emotion
    has_source_map: bool = False
    has_auto_label: bool = False
    has_css_prop_optimization: bool = False
    has_import_source: bool = False  # jsxImportSource pragma


@dataclass
class EmotionTestPatternInfo:
    """Information about Emotion testing patterns."""
    file: str = ""
    line_number: int = 0
    test_library: str = ""      # @emotion/jest, jest
    has_to_have_style_rule: bool = False
    has_snapshot_serializer: bool = False
    has_theme_render: bool = False


class EmotionApiExtractor:
    """
    Extracts Emotion framework API patterns from JS/TS/JSX/TSX source code.

    Detects:
    - createCache / CacheProvider from @emotion/cache
    - SSR utilities from @emotion/server
    - Babel plugin configuration
    - SWC plugin configuration
    - Jest testing utilities
    - JSX pragma configuration
    - Framework-specific integrations (Next.js, Gatsby, Remix)
    """

    # ── Cache patterns ───────────────────────────────────────────
    RE_CREATE_CACHE = re.compile(
        r"createCache\s*\(\s*\{",
        re.MULTILINE
    )

    RE_CACHE_PROVIDER = re.compile(
        r"<CacheProvider\s+value\s*=\s*\{",
        re.MULTILINE
    )

    RE_CACHE_KEY = re.compile(
        r"key\s*:\s*['\"](\w+)['\"]",
        re.MULTILINE
    )

    # ── SSR patterns ─────────────────────────────────────────────
    RE_EXTRACT_CRITICAL = re.compile(
        r"extractCritical\s*\(",
        re.MULTILINE
    )

    RE_EXTRACT_CRITICAL_CHUNKS = re.compile(
        r"extractCriticalToChunks\s*\(",
        re.MULTILINE
    )

    RE_RENDER_STYLES_STRING = re.compile(
        r"renderStylesToString\s*\(",
        re.MULTILINE
    )

    RE_RENDER_STYLES_STREAM = re.compile(
        r"renderStylesToNodeStream\s*\(",
        re.MULTILINE
    )

    RE_CONSTRUCT_TAGS = re.compile(
        r"constructStyleTagsFromChunks\s*\(",
        re.MULTILINE
    )

    # ── Babel/SWC plugin patterns ────────────────────────────────
    RE_BABEL_PLUGIN = re.compile(
        r"(?:babel-plugin-emotion|@emotion/babel-plugin)",
        re.MULTILINE
    )

    RE_SWC_PLUGIN = re.compile(
        r"@swc/plugin-emotion",
        re.MULTILINE
    )

    RE_NEXTJS_COMPILER_EMOTION = re.compile(
        r"compiler\s*:\s*\{[^}]*emotion\s*:",
        re.DOTALL
    )

    RE_PRAGMA = re.compile(
        r"/\*\*?\s*@(?:jsxImportSource\s+@emotion/react|jsx\s+jsx)\s*\*/",
        re.MULTILINE
    )

    # ── Jest patterns ────────────────────────────────────────────
    RE_EMOTION_JEST = re.compile(
        r"@emotion/jest|createSerializer|toHaveStyleRule",
        re.MULTILINE
    )

    RE_SNAPSHOT_SERIALIZER = re.compile(
        r"createSerializer|addSnapshotSerializer|snapshotSerializers",
        re.MULTILINE
    )

    # ── Framework detection ──────────────────────────────────────
    RE_NEXT_EMOTION = re.compile(
        r"compiler\s*:\s*\{[^}]*emotion|emotionConfig",
        re.DOTALL
    )

    RE_GATSBY_EMOTION = re.compile(
        r"gatsby-plugin-emotion",
        re.MULTILINE
    )

    RE_NEXT_DOCUMENT = re.compile(
        r"_document|getInitialProps|renderPage",
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Emotion API patterns.

        Returns:
            Dict with 'caches', 'ssr_patterns', 'babel_configs', 'test_patterns' lists.
        """
        caches: List[EmotionCacheInfo] = []
        ssr_patterns: List[EmotionSSRPatternInfo] = []
        babel_configs: List[EmotionBabelConfigInfo] = []
        test_patterns: List[EmotionTestPatternInfo] = []

        if not content or not content.strip():
            return {
                'caches': caches,
                'ssr_patterns': ssr_patterns,
                'babel_configs': babel_configs,
                'test_patterns': test_patterns,
            }

        # ── createCache ─────────────────────────────────────────
        for match in self.RE_CREATE_CACHE.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            context = content[match.start():match.start() + 500]

            key_match = self.RE_CACHE_KEY.search(context)
            cache_key = key_match.group(1) if key_match else ""

            caches.append(EmotionCacheInfo(
                file=file_path,
                line_number=line_num,
                cache_key=cache_key,
                has_nonce=bool(re.search(r'nonce\s*:', context)),
                has_prepend=bool(re.search(r'prepend\s*:', context)),
                has_container=bool(re.search(r'container\s*:', context)),
                has_stylis_plugins=bool(re.search(r'stylisPlugins?\s*:', context)),
                is_provider=bool(self.RE_CACHE_PROVIDER.search(content)),
            ))

        # ── CacheProvider (without explicit createCache) ─────────
        if not caches:
            for match in self.RE_CACHE_PROVIDER.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                caches.append(EmotionCacheInfo(
                    file=file_path,
                    line_number=line_num,
                    is_provider=True,
                ))

        # ── SSR: extractCritical ─────────────────────────────────
        for match in self.RE_EXTRACT_CRITICAL.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            framework = self._detect_ssr_framework(content, file_path)

            ssr_patterns.append(EmotionSSRPatternInfo(
                file=file_path,
                line_number=line_num,
                method="extractCritical",
                framework=framework,
                has_critical_extraction=True,
                has_rehydration=bool(re.search(r'hydrate|__NEXT_DATA__|_document', content)),
            ))

        # ── SSR: extractCriticalToChunks ─────────────────────────
        for match in self.RE_EXTRACT_CRITICAL_CHUNKS.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            framework = self._detect_ssr_framework(content, file_path)

            ssr_patterns.append(EmotionSSRPatternInfo(
                file=file_path,
                line_number=line_num,
                method="extractCriticalToChunks",
                framework=framework,
                has_critical_extraction=True,
                has_rehydration=True,
            ))

        # ── SSR: renderStylesToString ────────────────────────────
        for match in self.RE_RENDER_STYLES_STRING.finditer(content):
            line_num = content[:match.start()].count('\n') + 1

            ssr_patterns.append(EmotionSSRPatternInfo(
                file=file_path,
                line_number=line_num,
                method="renderStylesToString",
                framework=self._detect_ssr_framework(content, file_path),
            ))

        # ── SSR: renderStylesToNodeStream ────────────────────────
        for match in self.RE_RENDER_STYLES_STREAM.finditer(content):
            line_num = content[:match.start()].count('\n') + 1

            ssr_patterns.append(EmotionSSRPatternInfo(
                file=file_path,
                line_number=line_num,
                method="renderStylesToNodeStream",
                framework=self._detect_ssr_framework(content, file_path),
                has_streaming=True,
            ))

        # ── SSR: constructStyleTagsFromChunks ────────────────────
        for match in self.RE_CONSTRUCT_TAGS.finditer(content):
            line_num = content[:match.start()].count('\n') + 1

            ssr_patterns.append(EmotionSSRPatternInfo(
                file=file_path,
                line_number=line_num,
                method="constructStyleTagsFromChunks",
                framework=self._detect_ssr_framework(content, file_path),
                has_critical_extraction=True,
            ))

        # ── Babel plugin ─────────────────────────────────────────
        if self.RE_BABEL_PLUGIN.search(content):
            line_num = content[:self.RE_BABEL_PLUGIN.search(content).start()].count('\n') + 1
            context = content

            babel_configs.append(EmotionBabelConfigInfo(
                file=file_path,
                line_number=line_num,
                plugin_type="@emotion/babel-plugin" if "@emotion/babel-plugin" in content else "babel-plugin-emotion",
                has_source_map=bool(re.search(r'sourceMap\s*:', context)),
                has_auto_label=bool(re.search(r'autoLabel\s*:', context)),
                has_css_prop_optimization=bool(re.search(r'cssPropOptimization\s*:', context)),
            ))

        # ── SWC plugin ──────────────────────────────────────────
        if self.RE_SWC_PLUGIN.search(content):
            line_num = content[:self.RE_SWC_PLUGIN.search(content).start()].count('\n') + 1

            babel_configs.append(EmotionBabelConfigInfo(
                file=file_path,
                line_number=line_num,
                plugin_type="@swc/plugin-emotion",
            ))

        # ── Next.js compiler.emotion config ─────────────────────
        if self.RE_NEXTJS_COMPILER_EMOTION.search(content):
            m = self.RE_NEXTJS_COMPILER_EMOTION.search(content)
            line_num = content[:m.start()].count('\n') + 1

            babel_configs.append(EmotionBabelConfigInfo(
                file=file_path,
                line_number=line_num,
                plugin_type="nextjs-compiler-emotion",
                has_source_map=bool(re.search(r'sourceMap\s*:', content)),
                has_auto_label=bool(re.search(r'autoLabel\s*:', content)),
                has_css_prop_optimization=bool(re.search(r'cssPropOptimization\s*:', content)),
            ))

        # ── Pragma ──────────────────────────────────────────────
        if self.RE_PRAGMA.search(content):
            line_num = content[:self.RE_PRAGMA.search(content).start()].count('\n') + 1

            babel_configs.append(EmotionBabelConfigInfo(
                file=file_path,
                line_number=line_num,
                plugin_type="jsxImportSource-pragma",
                has_import_source=True,
            ))

        # ── Jest testing ─────────────────────────────────────────
        if self.RE_EMOTION_JEST.search(content):
            line_num = content[:self.RE_EMOTION_JEST.search(content).start()].count('\n') + 1

            test_patterns.append(EmotionTestPatternInfo(
                file=file_path,
                line_number=line_num,
                test_library="@emotion/jest",
                has_to_have_style_rule=bool(re.search(r'toHaveStyleRule', content)),
                has_snapshot_serializer=bool(self.RE_SNAPSHOT_SERIALIZER.search(content)),
                has_theme_render=bool(re.search(r'ThemeProvider|renderWithTheme', content)),
            ))

        return {
            'caches': caches,
            'ssr_patterns': ssr_patterns,
            'babel_configs': babel_configs,
            'test_patterns': test_patterns,
        }

    def _detect_ssr_framework(self, content: str, file_path: str) -> str:
        """Detect which SSR framework is being used."""
        if self.RE_GATSBY_EMOTION.search(content) or 'gatsby' in file_path.lower():
            return "gatsby"
        if self.RE_NEXT_DOCUMENT.search(content) or 'next' in file_path.lower():
            return "next"
        if re.search(r'@remix-run', content):
            return "remix"
        if re.search(r'express|app\.get|app\.use', content):
            return "express"
        return ""
