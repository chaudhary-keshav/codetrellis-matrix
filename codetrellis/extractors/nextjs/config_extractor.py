"""
Next.js Config Extractor for CodeTrellis

Extracts configuration from Next.js projects:
- next.config.js/mjs/ts parsing
- Image optimization config (domains, formats, sizes)
- i18n configuration (locales, default locale, domains)
- Redirects and rewrites
- Headers configuration
- Webpack/Turbopack customization
- Environment variables (env, publicRuntimeConfig)
- basePath, assetPrefix
- Experimental features
- Instrumentation (instrumentation.ts)
- Module aliases (@/ paths)
- Output mode (standalone, export)

Supports:
- next.config.js (CommonJS)
- next.config.mjs (ESM)
- next.config.ts (TypeScript - Next.js 15+)

Part of CodeTrellis v4.33 - Next.js Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class NextConfigInfo:
    """Information about Next.js project configuration."""
    file: str = ""
    config_format: str = ""  # js, mjs, ts
    output_mode: str = ""  # standalone, export, default
    base_path: str = ""
    asset_prefix: str = ""
    trailing_slash: bool = False
    react_strict_mode: bool = False
    powered_by_header: bool = True
    compress: bool = True
    has_webpack_config: bool = False
    has_turbopack_config: bool = False
    env_vars: List[str] = field(default_factory=list)
    transpile_packages: List[str] = field(default_factory=list)
    modular_imports: List[str] = field(default_factory=list)
    page_extensions: List[str] = field(default_factory=list)
    rewrites_count: int = 0
    redirects_count: int = 0
    headers_count: int = 0


@dataclass
class NextImageConfigInfo:
    """Information about Next.js image optimization config."""
    file: str = ""
    line_number: int = 0
    domains: List[str] = field(default_factory=list)
    remote_patterns: List[str] = field(default_factory=list)
    formats: List[str] = field(default_factory=list)  # avif, webp
    device_sizes: List[int] = field(default_factory=list)
    image_sizes: List[int] = field(default_factory=list)
    loader: str = ""  # default, custom, cloudinary, etc.
    unoptimized: bool = False


@dataclass
class NextI18nConfigInfo:
    """Information about Next.js i18n configuration."""
    file: str = ""
    line_number: int = 0
    locales: List[str] = field(default_factory=list)
    default_locale: str = ""
    locale_detection: bool = True
    domains: List[Dict] = field(default_factory=list)


@dataclass
class NextExperimentalInfo:
    """Information about Next.js experimental features."""
    file: str = ""
    line_number: int = 0
    features: List[str] = field(default_factory=list)
    # Known experimental features
    ppr: bool = False  # Partial Prerendering
    server_actions: bool = False
    mdx_rs: bool = False  # Rust-based MDX compiler
    turbo: bool = False
    typed_routes: bool = False
    instrument: bool = False
    after: bool = False  # after() API


class NextConfigExtractor:
    """
    Extracts configuration from Next.js config files.

    Detects:
    - Core config options (output, basePath, reactStrictMode)
    - Image optimization settings
    - i18n configuration
    - Webpack/Turbopack customization
    - Environment variables
    - Experimental features
    - Redirects, rewrites, headers
    """

    # Output mode
    OUTPUT_PATTERN = re.compile(
        r"output\s*:\s*['\"](\w+)['\"]",
        re.MULTILINE
    )

    # basePath
    BASE_PATH = re.compile(
        r"basePath\s*:\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )

    # assetPrefix
    ASSET_PREFIX = re.compile(
        r"assetPrefix\s*:\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE
    )

    # reactStrictMode
    STRICT_MODE = re.compile(
        r"reactStrictMode\s*:\s*(true|false)",
        re.MULTILINE
    )

    # trailingSlash
    TRAILING_SLASH = re.compile(
        r"trailingSlash\s*:\s*(true|false)",
        re.MULTILINE
    )

    # poweredByHeader
    POWERED_BY = re.compile(
        r"poweredByHeader\s*:\s*(true|false)",
        re.MULTILINE
    )

    # webpack customization
    WEBPACK_CONFIG = re.compile(
        r"webpack\s*:\s*(?:\(\s*config|function\s*\(\s*config)",
        re.MULTILINE
    )

    # turbopack
    TURBOPACK_CONFIG = re.compile(
        r"turbo\s*:\s*\{|turbopack\s*:\s*\{|experimental\s*:.*turbo",
        re.MULTILINE
    )

    # env vars
    ENV_PATTERN = re.compile(
        r"env\s*:\s*\{([^}]+)\}",
        re.MULTILINE | re.DOTALL
    )

    # transpilePackages
    TRANSPILE_PACKAGES = re.compile(
        r"transpilePackages\s*:\s*\[([^\]]+)\]",
        re.MULTILINE
    )

    # Image config
    IMAGE_DOMAINS = re.compile(
        r"domains\s*:\s*\[([^\]]+)\]",
        re.MULTILINE
    )
    IMAGE_REMOTE_PATTERNS = re.compile(
        r"remotePatterns\s*:\s*\[",
        re.MULTILINE
    )
    IMAGE_FORMATS = re.compile(
        r"formats\s*:\s*\[([^\]]+)\]",
        re.MULTILINE
    )
    IMAGE_LOADER = re.compile(
        r"loader\s*:\s*['\"](\w+)['\"]",
        re.MULTILINE
    )
    IMAGE_UNOPTIMIZED = re.compile(
        r"unoptimized\s*:\s*true",
        re.MULTILINE
    )

    # i18n config
    I18N_LOCALES = re.compile(
        r"locales\s*:\s*\[([^\]]+)\]",
        re.MULTILINE
    )
    I18N_DEFAULT = re.compile(
        r"defaultLocale\s*:\s*['\"](\w+)['\"]",
        re.MULTILINE
    )

    # Experimental features
    EXPERIMENTAL_PATTERN = re.compile(
        r"experimental\s*:\s*\{",
        re.MULTILINE
    )
    EXPERIMENTAL_FEATURES = re.compile(
        r"(\w+)\s*:\s*true",
        re.MULTILINE
    )

    # Rewrites/Redirects/Headers functions
    REWRITES = re.compile(r"(?:async\s+)?rewrites\s*\(\s*\)|rewrites\s*:", re.MULTILINE)
    REDIRECTS = re.compile(r"(?:async\s+)?redirects\s*\(\s*\)|redirects\s*:", re.MULTILINE)
    HEADERS = re.compile(r"(?:async\s+)?headers\s*\(\s*\)|headers\s*:", re.MULTILINE)

    # pageExtensions
    PAGE_EXTENSIONS = re.compile(
        r"pageExtensions\s*:\s*\[([^\]]+)\]",
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract configuration from Next.js config file.

        Args:
            content: Source code content
            file_path: Path to config file

        Returns:
            Dict with 'config', 'image_config', 'i18n_config', 'experimental'
        """
        normalized = file_path.replace('\\', '/')
        basename = normalized.split('/')[-1] if normalized else ""

        config = NextConfigInfo(file=file_path)
        image_config = None
        i18n_config = None
        experimental = None

        # Determine format
        if basename.endswith('.mjs'):
            config.config_format = "mjs"
        elif basename.endswith('.ts'):
            config.config_format = "ts"
        else:
            config.config_format = "js"

        # Core config
        m = self.OUTPUT_PATTERN.search(content)
        if m:
            config.output_mode = m.group(1)

        m = self.BASE_PATH.search(content)
        if m:
            config.base_path = m.group(1)

        m = self.ASSET_PREFIX.search(content)
        if m:
            config.asset_prefix = m.group(1)

        m = self.STRICT_MODE.search(content)
        if m:
            config.react_strict_mode = m.group(1) == 'true'

        m = self.TRAILING_SLASH.search(content)
        if m:
            config.trailing_slash = m.group(1) == 'true'

        m = self.POWERED_BY.search(content)
        if m:
            config.powered_by_header = m.group(1) == 'true'

        config.has_webpack_config = bool(self.WEBPACK_CONFIG.search(content))
        config.has_turbopack_config = bool(self.TURBOPACK_CONFIG.search(content))

        # Env vars
        env_match = self.ENV_PATTERN.search(content)
        if env_match:
            env_keys = re.findall(r"(\w+)\s*:", env_match.group(1))
            config.env_vars = env_keys

        # Transpile packages
        tp_match = self.TRANSPILE_PACKAGES.search(content)
        if tp_match:
            pkgs = re.findall(r"['\"]([^'\"]+)['\"]", tp_match.group(1))
            config.transpile_packages = pkgs

        # Page extensions
        pe_match = self.PAGE_EXTENSIONS.search(content)
        if pe_match:
            exts = re.findall(r"['\"]([^'\"]+)['\"]", pe_match.group(1))
            config.page_extensions = exts

        # Rewrites/Redirects/Headers counts
        config.rewrites_count = len(self.REWRITES.findall(content))
        config.redirects_count = len(self.REDIRECTS.findall(content))
        config.headers_count = len(self.HEADERS.findall(content))

        # ── Image config ─────────────────────────────────────────
        if re.search(r'images\s*:\s*\{', content):
            domains = []
            dm = self.IMAGE_DOMAINS.search(content)
            if dm:
                domains = re.findall(r"['\"]([^'\"]+)['\"]", dm.group(1))

            formats = []
            fm = self.IMAGE_FORMATS.search(content)
            if fm:
                formats = re.findall(r"['\"]([^'\"]+)['\"]", fm.group(1))

            loader = ""
            lm = self.IMAGE_LOADER.search(content)
            if lm:
                loader = lm.group(1)

            image_config = NextImageConfigInfo(
                file=file_path,
                domains=domains,
                remote_patterns=["configured"] if self.IMAGE_REMOTE_PATTERNS.search(content) else [],
                formats=formats,
                loader=loader,
                unoptimized=bool(self.IMAGE_UNOPTIMIZED.search(content)),
            )

        # ── i18n config ──────────────────────────────────────────
        if re.search(r'i18n\s*:\s*\{', content):
            locales = []
            lm = self.I18N_LOCALES.search(content)
            if lm:
                locales = re.findall(r"['\"]([^'\"]+)['\"]", lm.group(1))

            default_locale = ""
            dl = self.I18N_DEFAULT.search(content)
            if dl:
                default_locale = dl.group(1)

            i18n_config = NextI18nConfigInfo(
                file=file_path,
                locales=locales,
                default_locale=default_locale,
            )

        # ── Experimental features ────────────────────────────────
        exp_match = self.EXPERIMENTAL_PATTERN.search(content)
        if exp_match:
            # Extract features between braces
            start = exp_match.end()
            depth = 1
            end = start
            for i in range(start, min(start + 2000, len(content))):
                if content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                    if depth == 0:
                        end = i
                        break

            exp_block = content[start:end]
            features = []
            for fm in self.EXPERIMENTAL_FEATURES.finditer(exp_block):
                features.append(fm.group(1))

            experimental = NextExperimentalInfo(
                file=file_path,
                features=features,
                ppr='ppr' in features,
                server_actions='serverActions' in features,
                mdx_rs='mdxRs' in features,
                turbo='turbo' in features or 'turbopack' in features,
                typed_routes='typedRoutes' in features,
                instrument='instrumentationHook' in features,
                after='after' in features,
            )

        return {
            "config": config,
            "image_config": image_config,
            "i18n_config": i18n_config,
            "experimental": experimental,
        }
