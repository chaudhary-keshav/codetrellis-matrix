"""
PostCSS Extractors for CodeTrellis

This package provides 5 dedicated extractors for comprehensive PostCSS analysis:

1. **PostCSSPluginExtractor** — Plugin declarations, require/import patterns, config entries
2. **PostCSSConfigExtractor** — postcss.config.{js,cjs,mjs,ts}, .postcssrc.{json,yaml,js}, package.json
3. **PostCSSTransformExtractor** — CSS transforms via plugins (@custom-media, @custom-selector, @nest, nesting, etc.)
4. **PostCSSSyntaxExtractor** — Custom syntax detection (postcss-scss, postcss-less, postcss-html, SugarSS, postcss-jsx)
5. **PostCSSApiExtractor** — PostCSS JavaScript API usage (postcss(), plugin(), process(), decl(), rule(), walk*)

Supports PostCSS versions:
- PostCSS 1.x-4.x (early versions, basic plugin API)
- PostCSS 5.x (plugin API change, Result/Warning/Root/Rule/Declaration/AtRule/Comment nodes)
- PostCSS 6.x (LazyResult, syntax option, custom parsers, stringifiers)
- PostCSS 7.x (stable API, large plugin ecosystem, node processing API)
- PostCSS 8.x (ESM support, new plugin API with Once/Root/Declaration/Rule/AtRule listeners,
               dependency-free, nanoid, PostCSS Modules, PostCSS Preset Env 7+,
               improved source maps, async plugins, document nodes, Container API)
- PostCSS 8.5+ (latest - performance improvements, enhanced plugin API)

Part of CodeTrellis v4.46 — PostCSS Language Support
"""

from .plugin_extractor import (
    PostCSSPluginExtractor,
    PostCSSPluginInfo,
)
from .config_extractor import (
    PostCSSConfigExtractor,
    PostCSSConfigInfo,
    PostCSSConfigPluginEntry,
)
from .transform_extractor import (
    PostCSSTransformExtractor,
    PostCSSTransformInfo,
)
from .syntax_extractor import (
    PostCSSSyntaxExtractor,
    PostCSSSyntaxInfo,
)
from .api_extractor import (
    PostCSSApiExtractor,
    PostCSSApiUsage,
)

__all__ = [
    # Plugin extractor
    'PostCSSPluginExtractor', 'PostCSSPluginInfo',
    # Config extractor
    'PostCSSConfigExtractor', 'PostCSSConfigInfo', 'PostCSSConfigPluginEntry',
    # Transform extractor
    'PostCSSTransformExtractor', 'PostCSSTransformInfo',
    # Syntax extractor
    'PostCSSSyntaxExtractor', 'PostCSSSyntaxInfo',
    # API extractor
    'PostCSSApiExtractor', 'PostCSSApiUsage',
]
