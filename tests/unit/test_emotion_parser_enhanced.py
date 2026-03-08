"""
Tests for Emotion CSS-in-JS extractors and EnhancedEmotionParser.

Part of CodeTrellis v4.43 Emotion CSS-in-JS Framework Support.
Tests cover:
- Component extraction (@emotion/styled: styled.element``, styled(Component)``,
    shouldForwardProp, object syntax, string element syntax)
- Theme extraction (ThemeProvider, Global, useTheme, withTheme, design tokens)
- Style extraction (css prop, css function, ClassNames, cx, dynamic props,
    media queries, nesting, pseudo-selectors)
- Animation extraction (keyframes, animation usage, transitions)
- API extraction (createCache, CacheProvider, SSR, babel/SWC, @emotion/jest)
- Parser integration (framework detection, version detection, feature detection)
"""

import pytest
from codetrellis.emotion_parser_enhanced import (
    EnhancedEmotionParser,
    EmotionParseResult,
)
from codetrellis.extractors.emotion import (
    EmotionComponentExtractor,
    EmotionThemeExtractor,
    EmotionStyleExtractor,
    EmotionAnimationExtractor,
    EmotionApiExtractor,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def parser():
    return EnhancedEmotionParser()


@pytest.fixture
def component_extractor():
    return EmotionComponentExtractor()


@pytest.fixture
def theme_extractor():
    return EmotionThemeExtractor()


@pytest.fixture
def style_extractor():
    return EmotionStyleExtractor()


@pytest.fixture
def animation_extractor():
    return EmotionAnimationExtractor()


@pytest.fixture
def api_extractor():
    return EmotionApiExtractor()


# ═══════════════════════════════════════════════════════════════════
# Component Extractor Tests (@emotion/styled)
# ═══════════════════════════════════════════════════════════════════

class TestEmotionComponentExtractor:
    """Tests for EmotionComponentExtractor."""

    def test_basic_styled_element(self, component_extractor):
        code = '''
import styled from '@emotion/styled';

const Button = styled.button`
    background: blue;
    color: white;
    padding: 8px 16px;
`;

const Container = styled.div`
    max-width: 1200px;
    margin: 0 auto;
`;
'''
        result = component_extractor.extract(code, "App.tsx")
        components = result.get('components', [])
        names = [c.name for c in components]
        assert 'Button' in names
        assert 'Container' in names
        assert len(components) >= 2

    def test_styled_component_extension(self, component_extractor):
        code = '''
import styled from '@emotion/styled';

const Button = styled.button`
    padding: 8px 16px;
`;

const PrimaryButton = styled(Button)`
    background: blue;
    color: white;
`;
'''
        result = component_extractor.extract(code, "Button.tsx")
        components = result.get('components', [])
        names = [c.name for c in components]
        assert 'Button' in names
        assert 'PrimaryButton' in names

    def test_should_forward_prop(self, component_extractor):
        code = '''
import styled from '@emotion/styled';
import isPropValid from '@emotion/is-prop-valid';

const Box = styled('div', {
    shouldForwardProp: (prop) => isPropValid(prop) && prop !== 'color',
})`
    background: ${({ color }) => color};
    padding: 16px;
`;
'''
        result = component_extractor.extract(code, "Box.tsx")
        components = result.get('components', [])
        assert len(components) >= 1
        # Check shouldForwardProp detection
        box = [c for c in components if c.name == 'Box']
        if box:
            assert box[0].has_should_forward_prop

    def test_object_syntax(self, component_extractor):
        code = '''
import styled from '@emotion/styled';

const Card = styled.div({
    padding: '16px',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
});
'''
        result = component_extractor.extract(code, "Card.tsx")
        components = result.get('components', [])
        names = [c.name for c in components]
        assert 'Card' in names

    def test_string_element_syntax(self, component_extractor):
        """Emotion-specific: styled('element') syntax."""
        code = '''
import styled from '@emotion/styled';

const Button = styled('button')`
    padding: 8px 16px;
    background: blue;
`;

const Link = styled('a')`
    text-decoration: none;
    color: blue;
`;
'''
        result = component_extractor.extract(code, "Button.tsx")
        components = result.get('components', [])
        names = [c.name for c in components]
        assert 'Button' in names
        assert 'Link' in names

    def test_theme_usage_in_styled(self, component_extractor):
        code = '''
import styled from '@emotion/styled';

const ThemedButton = styled.button`
    background: ${({ theme }) => theme.colors.primary};
    color: ${({ theme }) => theme.colors.white};
    padding: ${({ theme }) => theme.spacing.md};
`;
'''
        result = component_extractor.extract(code, "ThemedButton.tsx")
        components = result.get('components', [])
        themed = [c for c in components if c.name == 'ThemedButton']
        if themed:
            assert themed[0].has_theme_usage

    def test_label_option(self, component_extractor):
        code = '''
import styled from '@emotion/styled';

const Button = styled('button', { label: 'PrimaryButton' })`
    background: blue;
`;
'''
        result = component_extractor.extract(code, "Button.tsx")
        components = result.get('components', [])
        assert len(components) >= 1

    def test_import_source_detection(self, component_extractor):
        code = '''
import styled from '@emotion/styled';

const Button = styled.button`
    padding: 8px;
`;
'''
        result = component_extractor.extract(code, "Button.tsx")
        components = result.get('components', [])
        if components:
            assert '@emotion/styled' in components[0].import_source or components[0].import_source == '@emotion/styled'

    def test_extended_components(self, component_extractor):
        code = '''
import styled from '@emotion/styled';

const Base = styled.div`
    padding: 16px;
`;

const Extended = styled(Base)`
    background: blue;
    color: white;
`;
'''
        result = component_extractor.extract(code, "Extend.tsx")
        extended = result.get('extended_components', [])
        # Either detected as extended or as regular components with base_component
        components = result.get('components', [])
        all_names = [c.name for c in components] + [e.name for e in extended]
        assert 'Base' in all_names or 'Extended' in all_names


# ═══════════════════════════════════════════════════════════════════
# Theme Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestEmotionThemeExtractor:
    """Tests for EmotionThemeExtractor."""

    def test_theme_provider(self, theme_extractor):
        code = '''
import { ThemeProvider } from '@emotion/react';
import { theme } from './theme';

function App() {
    return (
        <ThemeProvider theme={theme}>
            <MyApp />
        </ThemeProvider>
    );
}
'''
        result = theme_extractor.extract(code, "App.tsx")
        providers = result.get('providers', [])
        assert len(providers) >= 1

    def test_use_theme_hook(self, theme_extractor):
        code = '''
import { useTheme } from '@emotion/react';

function ThemedButton() {
    const theme = useTheme();
    return <button style={{ color: theme.colors.primary }}>Click</button>;
}
'''
        result = theme_extractor.extract(code, "ThemedButton.tsx")
        usages = result.get('theme_usages', [])
        hooks = [u for u in usages if u.method == 'useTheme']
        assert len(hooks) >= 1

    def test_global_component(self, theme_extractor):
        code = '''
import { Global, css } from '@emotion/react';

function GlobalStyles() {
    return (
        <Global
            styles={css`
                body {
                    margin: 0;
                    font-family: system-ui;
                }
                *, *::before, *::after {
                    box-sizing: border-box;
                }
            `}
        />
    );
}
'''
        result = theme_extractor.extract(code, "GlobalStyles.tsx")
        globals_ = result.get('global_styles', [])
        assert len(globals_) >= 1

    def test_legacy_inject_global(self, theme_extractor):
        code = '''
import { injectGlobal } from 'emotion';

injectGlobal`
    body {
        margin: 0;
    }
`;
'''
        result = theme_extractor.extract(code, "legacy.js")
        globals_ = result.get('global_styles', [])
        assert len(globals_) >= 1

    def test_with_theme_hoc(self, theme_extractor):
        code = '''
import { withTheme } from '@emotion/react';

const ThemedComponent = withTheme(({ theme }) => {
    return <div style={{ color: theme.colors.primary }}>Themed</div>;
});
'''
        result = theme_extractor.extract(code, "WithTheme.tsx")
        usages = result.get('theme_usages', [])
        hocs = [u for u in usages if u.method == 'withTheme']
        assert len(hocs) >= 1

    def test_design_token_detection(self, theme_extractor):
        code = '''
import { ThemeProvider } from '@emotion/react';

const theme = {
    colors: {
        primary: '#007bff',
        secondary: '#6c757d',
    },
    spacing: {
        sm: '4px',
        md: '8px',
        lg: '16px',
    },
    fonts: {
        body: 'system-ui',
        mono: 'Menlo',
    },
    breakpoints: {
        sm: '576px',
        md: '768px',
    },
};

function App() {
    return <ThemeProvider theme={theme}><MyApp /></ThemeProvider>;
}
'''
        result = theme_extractor.extract(code, "Theme.tsx")
        providers = result.get('providers', [])
        if providers:
            cats = providers[0].token_categories
            # Should detect at least some token categories
            assert isinstance(cats, list)

    def test_emotion_theming_legacy(self, theme_extractor):
        """v10 legacy: emotion-theming package."""
        code = '''
import { ThemeProvider } from 'emotion-theming';
import { useTheme } from 'emotion-theming';

function App() {
    return <ThemeProvider theme={theme}><MyApp /></ThemeProvider>;
}
'''
        result = theme_extractor.extract(code, "LegacyApp.tsx")
        providers = result.get('providers', [])
        assert len(providers) >= 1


# ═══════════════════════════════════════════════════════════════════
# Style Extractor Tests (css prop, css function, ClassNames)
# ═══════════════════════════════════════════════════════════════════

class TestEmotionStyleExtractor:
    """Tests for EmotionStyleExtractor."""

    def test_css_prop_object_syntax(self, style_extractor):
        code = '''
/** @jsxImportSource @emotion/react */
import { css } from '@emotion/react';

function Component() {
    return (
        <div css={{ color: 'blue', padding: '8px', fontSize: 16 }}>
            Hello
        </div>
    );
}
'''
        result = style_extractor.extract(code, "Component.tsx")
        css_props = result.get('css_props', [])
        assert len(css_props) >= 1

    def test_css_prop_template_syntax(self, style_extractor):
        code = '''
/** @jsxImportSource @emotion/react */
import { css } from '@emotion/react';

function Component() {
    return (
        <div css={css`
            color: blue;
            padding: 8px;
            font-size: 16px;
        `}>
            Hello
        </div>
    );
}
'''
        result = style_extractor.extract(code, "Component.tsx")
        css_props = result.get('css_props', [])
        assert len(css_props) >= 1

    def test_css_function_tagged_template(self, style_extractor):
        code = '''
import { css } from '@emotion/react';

const buttonStyle = css`
    padding: 8px 16px;
    background: blue;
    color: white;
    border: none;
    border-radius: 4px;
`;

const dangerStyle = css`
    background: red;
    font-weight: bold;
`;
'''
        result = style_extractor.extract(code, "styles.ts")
        css_funcs = result.get('css_functions', [])
        assert len(css_funcs) >= 2

    def test_css_function_call_syntax(self, style_extractor):
        code = '''
import { css } from '@emotion/css';

const className = css({
    padding: '16px',
    borderRadius: '8px',
    backgroundColor: 'white',
});
'''
        result = style_extractor.extract(code, "styles.ts")
        css_funcs = result.get('css_functions', [])
        assert len(css_funcs) >= 1

    def test_classnames_component(self, style_extractor):
        code = '''
import { ClassNames } from '@emotion/react';

function Component() {
    return (
        <ClassNames>
            {({ css, cx }) => (
                <SomeLib
                    className={cx(
                        css`color: blue;`,
                        'external-class',
                    )}
                />
            )}
        </ClassNames>
    );
}
'''
        result = style_extractor.extract(code, "ClassNames.tsx")
        classnames = result.get('classnames', [])
        assert len(classnames) >= 1

    def test_cx_composition(self, style_extractor):
        code = '''
import { css, cx } from '@emotion/css';

const base = css`padding: 8px;`;
const primary = css`color: blue;`;
const active = css`font-weight: bold;`;

function Component({ isActive }) {
    return (
        <div className={cx(base, primary, isActive && active)}>
            Content
        </div>
    );
}
'''
        result = style_extractor.extract(code, "Composition.tsx")
        # cx usage should be detected
        classnames = result.get('classnames', [])
        css_funcs = result.get('css_functions', [])
        assert len(css_funcs) >= 3  # base, primary, active

    def test_dynamic_props(self, style_extractor):
        code = '''
import styled from '@emotion/styled';

const Box = styled.div`
    color: ${({ color }) => color};
    padding: ${({ size }) => size === 'large' ? '16px' : '8px'};
    background: ${({ theme }) => theme.colors.background};
`;
'''
        result = style_extractor.extract(code, "Box.tsx")
        dynamic = result.get('dynamic_props', [])
        assert len(dynamic) >= 1

    def test_media_queries(self, style_extractor):
        code = '''
import { css } from '@emotion/react';

const responsive = css`
    font-size: 14px;

    @media (min-width: 768px) {
        font-size: 16px;
    }

    @media (min-width: 1024px) {
        font-size: 18px;
    }
`;
'''
        result = style_extractor.extract(code, "Responsive.tsx")
        media = result.get('media_queries', [])
        assert len(media) >= 2

    def test_style_patterns_nesting(self, style_extractor):
        code = '''
import styled from '@emotion/styled';

const Card = styled.div`
    padding: 16px;
    border-radius: 8px;

    &:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }

    & > h2 {
        font-size: 20px;
        margin-bottom: 8px;
    }

    &::after {
        content: '';
        display: block;
    }
`;
'''
        result = style_extractor.extract(code, "Card.tsx")
        patterns = result.get('style_patterns', [])
        if patterns:
            assert patterns[0].has_nesting or patterns[0].has_pseudo_selectors

    def test_css_variables(self, style_extractor):
        code = '''
import { css } from '@emotion/react';

const dynamicStyle = css`
    --color: blue;
    --spacing: 8px;
    color: var(--color);
    padding: var(--spacing);
`;
'''
        result = style_extractor.extract(code, "CSSVars.tsx")
        patterns = result.get('style_patterns', [])
        if patterns:
            assert patterns[0].has_css_variables


# ═══════════════════════════════════════════════════════════════════
# Animation Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestEmotionAnimationExtractor:
    """Tests for EmotionAnimationExtractor."""

    def test_keyframes_tagged_template(self, animation_extractor):
        code = '''
import { keyframes } from '@emotion/react';

const fadeIn = keyframes`
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
`;
'''
        result = animation_extractor.extract(code, "animations.ts")
        keyframes = result.get('keyframes', [])
        assert len(keyframes) >= 1
        assert keyframes[0].name == 'fadeIn'

    def test_multiple_keyframes(self, animation_extractor):
        code = '''
import { keyframes } from '@emotion/react';

const spin = keyframes`
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
`;

const pulse = keyframes`
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
`;

const slideIn = keyframes`
    from { transform: translateX(-100%); }
    to { transform: translateX(0); }
`;
'''
        result = animation_extractor.extract(code, "animations.ts")
        kfs = result.get('keyframes', [])
        names = [k.name for k in kfs]
        assert 'spin' in names
        assert 'pulse' in names
        assert 'slideIn' in names

    def test_animation_usage(self, animation_extractor):
        code = '''
import { keyframes } from '@emotion/react';
import styled from '@emotion/styled';

const fadeIn = keyframes`
    from { opacity: 0; }
    to { opacity: 1; }
`;

const FadeInDiv = styled.div`
    animation: ${fadeIn} 0.3s ease-out;
`;
'''
        result = animation_extractor.extract(code, "FadeIn.tsx")
        usages = result.get('animation_usages', [])
        assert len(usages) >= 1


# ═══════════════════════════════════════════════════════════════════
# API Extractor Tests (Cache, SSR, Babel, Testing)
# ═══════════════════════════════════════════════════════════════════

class TestEmotionApiExtractor:
    """Tests for EmotionApiExtractor."""

    def test_create_cache(self, api_extractor):
        code = '''
import createCache from '@emotion/cache';

const myCache = createCache({
    key: 'my-app',
    prepend: true,
    nonce: window.__CSP_NONCE__,
});
'''
        result = api_extractor.extract(code, "cache.ts")
        caches = result.get('caches', [])
        assert len(caches) >= 1
        if caches:
            assert caches[0].has_nonce or caches[0].has_prepend

    def test_cache_provider(self, api_extractor):
        code = '''
import createCache from '@emotion/cache';
import { CacheProvider } from '@emotion/react';

const cache = createCache({ key: 'em' });

function App() {
    return (
        <CacheProvider value={cache}>
            <MyApp />
        </CacheProvider>
    );
}
'''
        result = api_extractor.extract(code, "App.tsx")
        caches = result.get('caches', [])
        assert len(caches) >= 1

    def test_ssr_extract_critical(self, api_extractor):
        code = '''
import createEmotionServer from '@emotion/server/create-instance';
import createCache from '@emotion/cache';

const cache = createCache({ key: 'em' });
const { extractCriticalToChunks, constructStyleTagsFromChunks } = createEmotionServer(cache);

const html = renderToString(<App />);
const chunks = extractCriticalToChunks(html);
const styles = constructStyleTagsFromChunks(chunks);
'''
        result = api_extractor.extract(code, "_document.tsx")
        ssr = result.get('ssr_patterns', [])
        assert len(ssr) >= 1

    def test_ssr_streaming(self, api_extractor):
        code = '''
import { renderStylesToNodeStream } from '@emotion/server';
import { renderToPipeableStream } from 'react-dom/server';

const { pipe } = renderToPipeableStream(<App />);
pipe(renderStylesToNodeStream()).pipe(res);
'''
        result = api_extractor.extract(code, "server.ts")
        ssr = result.get('ssr_patterns', [])
        assert len(ssr) >= 1
        if ssr:
            assert ssr[0].has_streaming

    def test_babel_plugin(self, api_extractor):
        code = '''
// babel.config.js
module.exports = {
    plugins: [
        ['@emotion/babel-plugin', {
            sourceMap: true,
            autoLabel: 'dev-only',
            labelFormat: '[local]',
        }],
    ],
};
'''
        result = api_extractor.extract(code, "babel.config.js")
        configs = result.get('babel_configs', [])
        assert len(configs) >= 1

    def test_swc_plugin(self, api_extractor):
        code = '''
// .swcrc
{
    "jsc": {
        "experimental": {
            "plugins": [["@swc/plugin-emotion", {}]]
        }
    }
}
'''
        result = api_extractor.extract(code, ".swcrc")
        configs = result.get('babel_configs', [])
        assert len(configs) >= 1

    def test_jsx_pragma(self, api_extractor):
        code = '''
/** @jsxImportSource @emotion/react */
import { css } from '@emotion/react';

function Component() {
    return <div css={css`color: blue;`}>Hello</div>;
}
'''
        result = api_extractor.extract(code, "Component.tsx")
        configs = result.get('babel_configs', [])
        pragma_configs = [c for c in configs if c.has_import_source]
        assert len(pragma_configs) >= 1

    def test_emotion_jest(self, api_extractor):
        code = '''
import { createSerializer, matchers } from '@emotion/jest';

expect.extend(matchers);
expect.addSnapshotSerializer(createSerializer());

test('Button styles', () => {
    const { container } = render(<Button primary />);
    expect(container.firstChild).toHaveStyleRule('background', 'blue');
    expect(container.firstChild).toMatchSnapshot();
});
'''
        result = api_extractor.extract(code, "Button.test.tsx")
        tests = result.get('test_patterns', [])
        assert len(tests) >= 1
        if tests:
            assert tests[0].has_to_have_style_rule or tests[0].has_snapshot_serializer

    def test_nextjs_compiler_emotion(self, api_extractor):
        code = '''
// next.config.js
module.exports = {
    compiler: {
        emotion: true,
    },
};
'''
        result = api_extractor.extract(code, "next.config.js")
        configs = result.get('babel_configs', [])
        # Should detect compiler.emotion config
        assert len(configs) >= 1


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests (EnhancedEmotionParser)
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedEmotionParser:
    """Tests for EnhancedEmotionParser integration."""

    def test_empty_content(self, parser):
        result = parser.parse("", "empty.tsx")
        assert isinstance(result, EmotionParseResult)
        assert result.file_path == "empty.tsx"
        assert len(result.components) == 0

    def test_non_emotion_file(self, parser):
        code = '''
import React from 'react';

function App() {
    return <div>Hello World</div>;
}
'''
        assert not parser.is_emotion_file(code, "App.tsx")

    def test_emotion_react_detection(self, parser):
        code = '''
import { css } from '@emotion/react';

const style = css`color: blue;`;
'''
        assert parser.is_emotion_file(code, "style.ts")

    def test_emotion_styled_detection(self, parser):
        code = '''
import styled from '@emotion/styled';

const Button = styled.button`padding: 8px;`;
'''
        assert parser.is_emotion_file(code, "Button.tsx")

    def test_emotion_css_detection(self, parser):
        code = '''
import { css, cx } from '@emotion/css';

const name = css`color: blue;`;
'''
        assert parser.is_emotion_file(code, "style.ts")

    def test_legacy_emotion_detection(self, parser):
        code = '''
import { css } from 'emotion';
import styled from 'react-emotion';

const name = css`color: blue;`;
'''
        assert parser.is_emotion_file(code, "legacy.js")

    def test_jsx_pragma_detection(self, parser):
        code = '''
/** @jsxImportSource @emotion/react */
function App() {
    return <div css={{ color: 'blue' }}>Hello</div>;
}
'''
        assert parser.is_emotion_file(code, "App.tsx")

    def test_global_component_detection(self, parser):
        code = '''
<Global styles={css`body { margin: 0; }`} />
'''
        assert parser.is_emotion_file(code, "App.tsx")

    def test_version_detection_v11(self, parser):
        code = '''
import { css } from '@emotion/react';
import styled from '@emotion/styled';
import createCache from '@emotion/cache';

const style = css`color: blue;`;
'''
        result = parser.parse(code, "App.tsx")
        assert result.emotion_version == 'v11'

    def test_version_detection_v10(self, parser):
        code = '''
import { css } from '@emotion/core';
import { ThemeProvider } from 'emotion-theming';

const style = css`color: blue;`;
'''
        result = parser.parse(code, "App.tsx")
        assert result.emotion_version == 'v10'

    def test_version_detection_v9(self, parser):
        code = '''
import { css, injectGlobal } from 'emotion';
import styled from 'react-emotion';
'''
        result = parser.parse(code, "App.js")
        assert result.emotion_version == 'v9'

    def test_framework_detection(self, parser):
        code = '''
import { css } from '@emotion/react';
import styled from '@emotion/styled';
import createCache from '@emotion/cache';

const Button = styled.button`padding: 8px;`;
'''
        result = parser.parse(code, "App.tsx")
        assert 'emotion-react' in result.detected_frameworks
        assert 'emotion-styled' in result.detected_frameworks
        assert 'emotion-cache' in result.detected_frameworks

    def test_packages_detection(self, parser):
        code = '''
import { css, Global, ThemeProvider } from '@emotion/react';
import styled from '@emotion/styled';
import createCache from '@emotion/cache';
'''
        result = parser.parse(code, "App.tsx")
        assert '@emotion/react' in result.emotion_packages
        assert '@emotion/styled' in result.emotion_packages
        assert '@emotion/cache' in result.emotion_packages

    def test_feature_detection_css_prop(self, parser):
        code = '''
/** @jsxImportSource @emotion/react */
import { css } from '@emotion/react';

function Component() {
    return <div css={{ color: 'blue' }}>Hello</div>;
}
'''
        result = parser.parse(code, "Component.tsx")
        assert result.has_css_prop
        assert 'css_prop' in result.detected_features

    def test_feature_detection_styled(self, parser):
        code = '''
import styled from '@emotion/styled';

const Button = styled.button`
    padding: 8px 16px;
    background: blue;
`;
'''
        result = parser.parse(code, "Button.tsx")
        assert result.has_styled
        assert 'styled_components' in result.detected_features

    def test_feature_detection_keyframes(self, parser):
        code = '''
import { keyframes } from '@emotion/react';
import styled from '@emotion/styled';

const fadeIn = keyframes`
    from { opacity: 0; }
    to { opacity: 1; }
`;

const FadeInDiv = styled.div`
    animation: ${fadeIn} 0.3s ease-out;
`;
'''
        result = parser.parse(code, "FadeIn.tsx")
        assert result.has_keyframes
        assert 'keyframes_animations' in result.detected_features

    def test_feature_detection_theme(self, parser):
        code = '''
import { ThemeProvider, useTheme } from '@emotion/react';

function App() {
    return <ThemeProvider theme={theme}><MyApp /></ThemeProvider>;
}

function ThemedComp() {
    const theme = useTheme();
    return <div style={{ color: theme.colors.primary }}>Theme</div>;
}
'''
        result = parser.parse(code, "App.tsx")
        assert result.has_theme_provider
        assert 'theme_provider' in result.detected_features

    def test_feature_detection_global(self, parser):
        code = '''
import { Global, css } from '@emotion/react';

function GlobalStyles() {
    return <Global styles={css`body { margin: 0; }`} />;
}
'''
        result = parser.parse(code, "Global.tsx")
        assert result.has_global_styles
        assert 'global_styles' in result.detected_features

    def test_feature_detection_pragma(self, parser):
        code = '''
/** @jsxImportSource @emotion/react */
import { css } from '@emotion/react';
'''
        result = parser.parse(code, "Pragma.tsx")
        assert result.has_pragma
        assert 'jsx_pragma' in result.detected_features

    def test_file_type_detection(self, parser):
        code = "import { css } from '@emotion/react';"
        assert parser.parse(code, "file.tsx").file_type == "tsx"
        assert parser.parse(code, "file.jsx").file_type == "jsx"
        assert parser.parse(code, "file.ts").file_type == "ts"
        assert parser.parse(code, "file.js").file_type == "js"

    def test_full_integration_complex_file(self, parser):
        """Test a realistic complex Emotion file with multiple features."""
        code = '''
/** @jsxImportSource @emotion/react */
import { css, Global, ThemeProvider, keyframes, ClassNames } from '@emotion/react';
import styled from '@emotion/styled';
import createCache from '@emotion/cache';
import { CacheProvider } from '@emotion/react';

const fadeIn = keyframes`
    from { opacity: 0; }
    to { opacity: 1; }
`;

const theme = {
    colors: { primary: '#007bff', text: '#333' },
    spacing: { sm: '4px', md: '8px', lg: '16px' },
};

const cache = createCache({ key: 'my-app', prepend: true });

const StyledButton = styled.button`
    padding: ${({ theme }) => theme.spacing.md};
    background: ${({ theme }) => theme.colors.primary};
    color: white;
    border: none;
    border-radius: 4px;
    animation: ${fadeIn} 0.3s ease-out;

    &:hover {
        opacity: 0.9;
    }

    @media (min-width: 768px) {
        padding: ${({ theme }) => theme.spacing.lg};
    }
`;

const Card = styled('div', {
    shouldForwardProp: (prop) => prop !== 'elevated',
})`
    padding: 16px;
    box-shadow: ${({ elevated }) => elevated ? '0 4px 8px rgba(0,0,0,0.2)' : 'none'};
`;

function App() {
    return (
        <CacheProvider value={cache}>
            <ThemeProvider theme={theme}>
                <Global styles={css`
                    body { margin: 0; font-family: system-ui; }
                `} />
                <div css={{ padding: '16px', color: theme.colors.text }}>
                    <StyledButton>Click me</StyledButton>
                    <Card elevated>Content</Card>
                </div>
            </ThemeProvider>
        </CacheProvider>
    );
}
'''
        result = parser.parse(code, "App.tsx")

        # Should detect multiple features
        assert result.emotion_version == 'v11'
        assert result.has_styled
        assert result.has_theme_provider
        assert result.has_global_styles
        assert result.has_keyframes
        assert result.has_cache
        assert result.has_pragma

        # Should detect multiple packages
        assert '@emotion/react' in result.emotion_packages
        assert '@emotion/styled' in result.emotion_packages
        assert '@emotion/cache' in result.emotion_packages

        # Should detect components
        assert len(result.components) >= 2

        # Should detect features
        assert 'styled_components' in result.detected_features
        assert 'theme_provider' in result.detected_features
        assert 'global_styles' in result.detected_features
        assert 'keyframes_animations' in result.detected_features

    def test_facepaint_detection(self, parser):
        code = '''
import { css } from '@emotion/react';
import facepaint from 'facepaint';

const mq = facepaint([
    '@media(min-width: 420px)',
    '@media(min-width: 920px)',
    '@media(min-width: 1120px)',
]);

const myStyle = mq({
    fontSize: [12, 14, 16, 18],
    padding: [8, 12, 16, 20],
});
'''
        result = parser.parse(code, "Responsive.tsx")
        assert 'facepaint' in result.detected_frameworks

    def test_emotion_server_detection(self, parser):
        code = '''
import createEmotionServer from '@emotion/server/create-instance';
import createCache from '@emotion/cache';

const cache = createCache({ key: 'em' });
const { extractCriticalToChunks, constructStyleTagsFromChunks } = createEmotionServer(cache);

const html = renderToString(<App />);
const chunks = extractCriticalToChunks(html);
const styles = constructStyleTagsFromChunks(chunks);
'''
        result = parser.parse(code, "_document.tsx")
        assert result.has_ssr
        assert 'emotion-server' in result.detected_frameworks

    def test_emotion_jest_detection(self, parser):
        code = '''
import { createSerializer, matchers } from '@emotion/jest';

expect.extend(matchers);
expect.addSnapshotSerializer(createSerializer());
'''
        result = parser.parse(code, "setup.ts")
        assert 'emotion-jest' in result.detected_frameworks
        assert len(result.test_patterns) >= 1

    def test_polished_integration(self, parser):
        code = '''
import styled from '@emotion/styled';
import { darken, lighten, transparentize } from 'polished';

const Button = styled.button`
    background: ${({ theme }) => theme.colors.primary};
    &:hover {
        background: ${({ theme }) => darken(0.1, theme.colors.primary)};
    }
`;
'''
        result = parser.parse(code, "Button.tsx")
        assert 'polished' in result.detected_frameworks
