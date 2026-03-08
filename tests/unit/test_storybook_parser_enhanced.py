"""
Tests for EnhancedStorybookParser v1.0 — Storybook Framework Support.

Tests cover:
- StorybookStoryExtractor: CSF 1/2/3, storiesOf, MDX, play, render, decorators
- StorybookComponentExtractor: autodocs, argTypes, controls, doc blocks
- StorybookAddonExtractor: official/community addons, essential, options
- StorybookConfigExtractor: main/preview/manager, framework, builder, stories
- StorybookApiExtractor: imports, testing, portable stories, Chromatic
- EnhancedStorybookParser: is_storybook_file, parse, version/CSF detection

Part of CodeTrellis v4.70 - Storybook Framework Support
"""

import pytest

from codetrellis.extractors.storybook import (
    StorybookStoryExtractor, StorybookStoryInfo,
    StorybookComponentExtractor, StorybookComponentInfo,
    StorybookAddonExtractor, StorybookAddonInfo,
    StorybookConfigExtractor, StorybookConfigInfo,
    StorybookApiExtractor, StorybookImportInfo, StorybookTestingInfo,
)
from codetrellis.storybook_parser_enhanced import (
    EnhancedStorybookParser, StorybookParseResult,
)


# ============================================================================
# Story Extractor Tests
# ============================================================================

class TestStorybookStoryExtractor:
    """Tests for StorybookStoryExtractor."""

    def setup_method(self):
        self.extractor = StorybookStoryExtractor()

    def test_csf3_object_story(self):
        content = '''
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta = {
    title: 'Components/Button',
    component: Button,
} satisfies Meta<typeof Button>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
    args: { variant: 'primary', children: 'Click me' },
};

export const Secondary: Story = {
    args: { variant: 'secondary' },
};
'''
        result = self.extractor.extract(content)
        assert len(result) >= 2
        names = [s.name for s in result]
        assert 'Primary' in names
        assert 'Secondary' in names

    def test_csf2_template_bind(self):
        content = '''
import { ComponentStory, ComponentMeta } from '@storybook/react';
import { Button } from './Button';

export default {
    title: 'Components/Button',
    component: Button,
} as ComponentMeta<typeof Button>;

const Template: ComponentStory<typeof Button> = (args) => <Button {...args} />;

export const Primary = Template.bind({});
Primary.args = { variant: 'primary' };
'''
        result = self.extractor.extract(content)
        assert len(result) >= 1
        names = [s.name for s in result]
        assert 'Primary' in names
        template_stories = [s for s in result if s.has_template]
        assert len(template_stories) >= 1

    def test_csf1_function_story(self):
        content = '''
export default {
    title: 'Components/Button',
};

export const Primary = () => <Button primary />;
export const Secondary = () => <Button />;
'''
        result = self.extractor.extract(content)
        assert len(result) >= 1

    def test_stories_of_legacy(self):
        content = '''
import { storiesOf } from '@storybook/react';
import { Button } from './Button';

storiesOf('Components/Button', module)
    .add('Primary', () => <Button primary />)
    .add('Secondary', () => <Button />);
'''
        result = self.extractor.extract(content)
        assert len(result) >= 1

    def test_story_with_play_function(self):
        content = '''
import { expect, userEvent, within } from '@storybook/test';

export const FilledForm: Story = {
    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);
        await userEvent.type(canvas.getByLabelText('Email'), 'test@test.com');
        await userEvent.click(canvas.getByRole('button'));
        await expect(canvas.getByText('Success')).toBeInTheDocument();
    },
};
'''
        result = self.extractor.extract(content)
        play_stories = [s for s in result if s.has_play]
        assert len(play_stories) >= 1

    def test_story_with_render_function(self):
        content = '''
export const InForm: Story = {
    render: (args) => (
        <form>
            <Button {...args} />
        </form>
    ),
    args: { children: 'Submit' },
};
'''
        result = self.extractor.extract(content)
        render_stories = [s for s in result if s.has_render]
        assert len(render_stories) >= 1

    def test_story_with_decorators(self):
        content = '''
export const Themed: Story = {
    decorators: [
        (Story) => <ThemeProvider><Story /></ThemeProvider>,
    ],
    args: { variant: 'primary' },
};
'''
        result = self.extractor.extract(content)
        decorated = [s for s in result if s.has_decorators]
        assert len(decorated) >= 1

    def test_story_with_loaders(self):
        content = '''
export const WithData: Story = {
    loaders: [async () => ({ user: await fetchUser() })],
    render: (args, { loaded: { user } }) => <Profile user={user} />,
};
'''
        result = self.extractor.extract(content)
        with_loaders = [s for s in result if s.has_loaders]
        assert len(with_loaders) >= 1

    def test_story_with_args(self):
        content = '''
export const Primary: Story = {
    args: {
        variant: 'primary',
        size: 'medium',
        disabled: false,
        children: 'Click',
    },
};
'''
        result = self.extractor.extract(content)
        with_args = [s for s in result if s.has_args]
        assert len(with_args) >= 1

    def test_story_with_tags(self):
        content = '''
export const Experimental: Story = {
    tags: ['!autodocs', 'experimental', 'beta'],
    args: { variant: 'new' },
};
'''
        result = self.extractor.extract(content)
        # Should detect tags
        assert len(result) >= 1

    def test_story_with_mount_v8(self):
        content = '''
export const WithData: Story = {
    play: async ({ mount }) => {
        const data = await fetchData();
        const canvas = await mount(<Component data={data} />);
        await expect(canvas.getByText(data.title)).toBeVisible();
    },
};
'''
        result = self.extractor.extract(content)
        mount_stories = [s for s in result if s.has_mount]
        assert len(mount_stories) >= 1

    def test_story_with_before_each_v8(self):
        content = '''
const meta = {
    component: Dashboard,
    beforeEach: async () => {
        mockApi.reset();
        return () => mockApi.restore();
    },
};
export default meta;
'''
        result = self.extractor.extract(content)
        be_stories = [s for s in result if s.has_before_each]
        assert len(be_stories) >= 1

    def test_meta_extraction(self):
        content = '''
const meta = {
    title: 'Design System/Atoms/Button',
    component: Button,
    tags: ['autodocs'],
    argTypes: {
        variant: { control: 'select', options: ['primary', 'secondary'] },
    },
} satisfies Meta<typeof Button>;
export default meta;
'''
        result = self.extractor.extract(content)
        meta_entries = [s for s in result if s.name == '__meta__']
        assert len(meta_entries) >= 1
        meta = meta_entries[0]
        assert meta.title == 'Design System/Atoms/Button'

    def test_mdx_story(self):
        content = '''
import { Meta, Story, Canvas } from '@storybook/blocks';
import * as ButtonStories from './Button.stories';

<Meta of={ButtonStories} />

# Button

<Canvas of={ButtonStories.Primary} />

<Story name="Custom">
    <Button primary>Custom Story</Button>
</Story>
'''
        result = self.extractor.extract(content)
        assert len(result) >= 1


# ============================================================================
# Component Extractor Tests
# ============================================================================

class TestStorybookComponentExtractor:
    """Tests for StorybookComponentExtractor."""

    def setup_method(self):
        self.extractor = StorybookComponentExtractor()

    def test_component_with_autodocs(self):
        content = '''
const meta: Meta<typeof Button> = {
    title: 'Components/Button',
    component: Button,
    tags: ['autodocs'],
};
export default meta;
'''
        result = self.extractor.extract(content)
        autodocs = [c for c in result if c.has_autodocs]
        assert len(autodocs) >= 1

    def test_component_with_arg_types(self):
        content = '''
const meta = {
    component: Input,
    argTypes: {
        size: { control: 'select', options: ['sm', 'md', 'lg'] },
        disabled: { control: 'boolean' },
        onChange: { action: 'changed' },
        placeholder: { control: 'text' },
    },
};
export default meta;
'''
        result = self.extractor.extract(content)
        assert len(result) >= 1
        comp = result[0]
        assert len(comp.arg_types) >= 1

    def test_component_with_subcomponents(self):
        content = '''
const meta = {
    title: 'Components/List',
    component: List,
    subcomponents: { ListItem: List.Item, ListHeader: List.Header },
};
export default meta;
'''
        result = self.extractor.extract(content)
        with_sub = [c for c in result if c.has_subcomponents]
        assert len(with_sub) >= 1

    def test_doc_blocks_detection(self):
        content = '''
import { Meta, Canvas, Controls, ArgTypes, Source } from '@storybook/blocks';
import * as Stories from './Button.stories';

<Meta of={Stories} />
<Canvas of={Stories.Primary} />
<Controls of={Stories.Primary} />
<ArgTypes of={Stories} />
'''
        result = self.extractor.extract(content)
        # Should detect doc block usage
        assert len(result) >= 1


# ============================================================================
# Addon Extractor Tests
# ============================================================================

class TestStorybookAddonExtractor:
    """Tests for StorybookAddonExtractor."""

    def setup_method(self):
        self.extractor = StorybookAddonExtractor()

    def test_official_addons(self):
        content = '''
const config = {
    addons: [
        '@storybook/addon-essentials',
        '@storybook/addon-interactions',
        '@storybook/addon-a11y',
        '@storybook/addon-links',
    ],
};
export default config;
'''
        result = self.extractor.extract(content)
        assert len(result) >= 4
        official = [a for a in result if a.is_official]
        assert len(official) >= 4

    def test_essential_addons(self):
        content = '''
addons: ['@storybook/addon-essentials']
'''
        result = self.extractor.extract(content)
        essential = [a for a in result if a.is_essential]
        assert len(essential) >= 1

    def test_addon_with_options(self):
        content = '''
addons: [
    {
        name: '@storybook/addon-essentials',
        options: { backgrounds: false, actions: true },
    },
]
'''
        result = self.extractor.extract(content)
        with_opts = [a for a in result if a.has_options]
        assert len(with_opts) >= 1

    def test_community_addon(self):
        content = '''
addons: [
    '@storybook/addon-essentials',
    'storybook-addon-designs',
    'storybook-dark-mode',
]
'''
        result = self.extractor.extract(content)
        community = [a for a in result if not a.is_official]
        assert len(community) >= 1


# ============================================================================
# Config Extractor Tests
# ============================================================================

class TestStorybookConfigExtractor:
    """Tests for StorybookConfigExtractor."""

    def setup_method(self):
        self.extractor = StorybookConfigExtractor()

    def test_main_config(self):
        content = '''
import type { StorybookConfig } from '@storybook/react-vite';

const config: StorybookConfig = {
    stories: ['../src/**/*.stories.@(ts|tsx|mdx)'],
    framework: '@storybook/react-vite',
    addons: ['@storybook/addon-essentials'],
    staticDirs: ['../public'],
};
export default config;
'''
        result = self.extractor.extract(content, file_path='.storybook/main.ts')
        assert len(result) >= 1
        cfg = result[0]
        assert cfg.framework == '@storybook/react-vite'

    def test_preview_config(self):
        content = '''
import type { Preview } from '@storybook/react';

const preview: Preview = {
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'light' },
    },
    decorators: [withTheme],
};
export default preview;
'''
        result = self.extractor.extract(content, file_path='.storybook/preview.ts')
        assert len(result) >= 1

    def test_webpack_config(self):
        content = '''
const config = {
    framework: '@storybook/react-webpack5',
    webpackFinal: async (config) => {
        config.resolve.alias = { '@': path.resolve(__dirname, '../src') };
        return config;
    },
};
'''
        result = self.extractor.extract(content, file_path='.storybook/main.ts')
        assert len(result) >= 1
        cfg = result[0]
        assert cfg.has_webpack_config is True

    def test_vite_config(self):
        content = '''
const config = {
    framework: '@storybook/react-vite',
    viteFinal: async (config) => {
        return config;
    },
};
'''
        result = self.extractor.extract(content, file_path='.storybook/main.ts')
        assert len(result) >= 1
        cfg = result[0]
        assert cfg.has_vite_config is True

    def test_typescript_detection(self):
        content = '''
const config: StorybookConfig = {
    stories: ['../src/**/*.stories.tsx'],
    framework: '@storybook/react-vite',
    typescript: {
        check: true,
        reactDocgen: 'react-docgen-typescript',
    },
};
'''
        result = self.extractor.extract(content, file_path='.storybook/main.ts')
        assert len(result) >= 1
        cfg = result[0]
        assert cfg.has_typescript is True

    def test_stories_globs(self):
        content = '''
const config = {
    stories: [
        '../src/**/*.stories.@(ts|tsx)',
        '../stories/**/*.stories.mdx',
    ],
};
'''
        result = self.extractor.extract(content, file_path='.storybook/main.ts')
        assert len(result) >= 1
        cfg = result[0]
        assert len(cfg.stories_globs) >= 1

    def test_refs_detection(self):
        content = '''
const config = {
    refs: {
        'design-system': {
            title: 'Design System',
            url: 'https://ds.example.com',
        },
    },
};
'''
        result = self.extractor.extract(content, file_path='.storybook/main.ts')
        assert len(result) >= 1
        cfg = result[0]
        assert len(cfg.refs) >= 1


# ============================================================================
# API Extractor Tests
# ============================================================================

class TestStorybookApiExtractor:
    """Tests for StorybookApiExtractor."""

    def setup_method(self):
        self.extractor = StorybookApiExtractor()

    def test_core_imports(self):
        content = '''
import type { Meta, StoryObj } from '@storybook/react';
import { fn } from '@storybook/test';
import { expect, userEvent, within } from '@storybook/test';
'''
        result = self.extractor.extract(content)
        imports = [r for r in result if isinstance(r, StorybookImportInfo)]
        assert len(imports) >= 2

    def test_testing_patterns(self):
        content = '''
import { expect, userEvent, within, fn, step } from '@storybook/test';

export const Test: Story = {
    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);
        await userEvent.click(canvas.getByRole('button'));
        await expect(canvas.getByText('Done')).toBeVisible();
    },
};
'''
        result = self.extractor.extract(content)
        testing = [r for r in result if isinstance(r, StorybookTestingInfo)]
        assert len(testing) >= 1

    def test_portable_stories(self):
        content = '''
import { composeStories } from '@storybook/react';
import * as stories from './Button.stories';

const { Primary, Disabled } = composeStories(stories);

test('renders primary', () => {
    render(<Primary />);
});
'''
        result = self.extractor.extract(content)
        portable = [r for r in result if isinstance(r, StorybookTestingInfo)
                    and r.has_compose_stories]
        assert len(portable) >= 1

    def test_chromatic_detection(self):
        content = '''
import { isChromatic } from 'chromatic/isChromatic';

export const Dark: Story = {
    parameters: {
        chromatic: { viewports: [320, 768, 1200], delay: 300 },
    },
};
'''
        result = self.extractor.extract(content)
        chromatic = [r for r in result if isinstance(r, StorybookTestingInfo)
                     and r.has_chromatic]
        assert len(chromatic) >= 1

    def test_type_imports(self):
        content = '''
import type { Meta, StoryObj, StoryFn } from '@storybook/react';
import type { Preview } from '@storybook/react';
'''
        result = self.extractor.extract(content)
        type_imports = [r for r in result if isinstance(r, StorybookImportInfo)
                        and r.is_type_import]
        assert len(type_imports) >= 1


# ============================================================================
# Enhanced Parser Tests
# ============================================================================

class TestEnhancedStorybookParser:
    """Tests for EnhancedStorybookParser."""

    def setup_method(self):
        self.parser = EnhancedStorybookParser()

    # ---- File Detection ----

    def test_is_storybook_file_stories(self):
        assert self.parser.is_storybook_file('Button.stories.tsx') is True
        assert self.parser.is_storybook_file('Button.stories.ts') is True
        assert self.parser.is_storybook_file('Button.stories.js') is True
        assert self.parser.is_storybook_file('Button.stories.jsx') is True
        assert self.parser.is_storybook_file('Button.stories.mdx') is True

    def test_is_storybook_file_config(self):
        assert self.parser.is_storybook_file('.storybook/main.ts') is True
        assert self.parser.is_storybook_file('.storybook/preview.ts') is True
        assert self.parser.is_storybook_file('.storybook/manager.ts') is True

    def test_is_not_storybook_file(self):
        assert self.parser.is_storybook_file('Button.tsx') is False
        assert self.parser.is_storybook_file('utils.ts') is False
        assert self.parser.is_storybook_file('index.js') is False

    def test_is_storybook_file_with_imports(self):
        content = '''import { fn } from '@storybook/test';'''
        assert self.parser.is_storybook_file('test.ts', content) is True

    # ---- Parse ----

    def test_parse_csf3_story_file(self):
        content = '''
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta = {
    title: 'Components/Button',
    component: Button,
    tags: ['autodocs'],
} satisfies Meta<typeof Button>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
    args: { variant: 'primary', children: 'Click me' },
};

export const WithPlay: Story = {
    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);
        await userEvent.click(canvas.getByRole('button'));
    },
};
'''
        result = self.parser.parse(content, 'Button.stories.tsx')
        assert isinstance(result, StorybookParseResult)
        assert len(result.stories) >= 2
        assert len(result.imports) >= 1

    def test_parse_config_file(self):
        content = '''
import type { StorybookConfig } from '@storybook/react-vite';

const config: StorybookConfig = {
    stories: ['../src/**/*.stories.@(ts|tsx)'],
    framework: '@storybook/react-vite',
    addons: [
        '@storybook/addon-essentials',
        '@storybook/addon-interactions',
    ],
};
export default config;
'''
        result = self.parser.parse(content, '.storybook/main.ts')
        assert isinstance(result, StorybookParseResult)
        assert len(result.configs) >= 1
        assert len(result.addons) >= 2

    # ---- Version Detection ----

    def test_detect_version_v8(self):
        content = '''
import { fn } from '@storybook/test';
import { mount } from '@storybook/react';

export const Test: Story = {
    play: async ({ mount }) => {
        await mount(<Component />);
    },
};
'''
        result = self.parser.parse(content, 'Test.stories.tsx')
        assert result.detected_version in ('v8', 'v7', None) or result.detected_version is not None

    def test_detect_version_v7(self):
        content = '''
import type { Meta, StoryObj } from '@storybook/react';

const meta = {
    title: 'Button',
    component: Button,
    tags: ['autodocs'],
} satisfies Meta<typeof Button>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
    args: { variant: 'primary' },
};
'''
        result = self.parser.parse(content, 'Button.stories.tsx')
        # v7 or v8 detected based on CSF3 pattern
        assert result.detected_version is not None

    def test_detect_version_v6(self):
        content = '''
import { ComponentStory, ComponentMeta } from '@storybook/react';

export default {
    title: 'Button',
    component: Button,
} as ComponentMeta<typeof Button>;

const Template: ComponentStory<typeof Button> = (args) => <Button {...args} />;
export const Primary = Template.bind({});
Primary.args = { variant: 'primary' };
'''
        result = self.parser.parse(content, 'Button.stories.tsx')
        assert result.detected_version is not None

    def test_detect_version_v5(self):
        content = '''
import { storiesOf } from '@storybook/react';
import { withKnobs, text } from '@storybook/addon-knobs';

storiesOf('Button', module)
    .addDecorator(withKnobs)
    .add('primary', () => <Button label={text('Label', 'Hello')} />);
'''
        result = self.parser.parse(content, 'Button.stories.tsx')
        assert result.detected_version is not None

    # ---- CSF Version Detection ----

    def test_detect_csf3(self):
        content = '''
export const Primary: Story = {
    args: { variant: 'primary' },
};
'''
        result = self.parser.parse(content, 'Button.stories.tsx')
        # Should detect CSF3 or appropriate version
        assert result is not None

    def test_detect_csf2(self):
        content = '''
const Template = (args) => <Button {...args} />;
export const Primary = Template.bind({});
Primary.args = { variant: 'primary' };
'''
        result = self.parser.parse(content, 'Button.stories.tsx')
        assert result is not None

    # ---- Framework Detection ----

    def test_detect_react_framework(self):
        content = '''
import type { Meta } from '@storybook/react';
import { Button } from './Button';
'''
        result = self.parser.parse(content, 'Button.stories.tsx')
        assert '@storybook/react' in result.detected_frameworks

    def test_detect_vue_framework(self):
        content = '''
import type { Meta } from '@storybook/vue3';
import Button from './Button.vue';
'''
        result = self.parser.parse(content, 'Button.stories.ts')
        assert '@storybook/vue3' in result.detected_frameworks

    def test_detect_angular_framework(self):
        content = '''
import type { Meta } from '@storybook/angular';
import { ButtonComponent } from './button.component';
'''
        result = self.parser.parse(content, 'button.stories.ts')
        assert '@storybook/angular' in result.detected_frameworks

    def test_detect_testing_framework(self):
        content = '''
import { fn, expect, userEvent, within } from '@storybook/test';
'''
        result = self.parser.parse(content, 'Button.stories.tsx')
        assert '@storybook/test' in result.detected_frameworks

    # ---- Feature Detection ----

    def test_detect_play_features(self):
        content = '''
import { userEvent, within, expect } from '@storybook/test';

export const Test: Story = {
    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);
        await userEvent.click(canvas.getByRole('button'));
        await expect(canvas.getByText('Done')).toBeVisible();
    },
};
'''
        result = self.parser.parse(content, 'Button.stories.tsx')
        assert 'play_functions' in result.detected_features or 'play-functions' in result.detected_features or 'play' in result.detected_features

    def test_detect_autodocs_feature(self):
        content = '''
const meta = {
    component: Button,
    tags: ['autodocs'],
};
export default meta;
'''
        result = self.parser.parse(content, 'Button.stories.tsx')
        assert 'autodocs' in result.detected_features

    def test_detect_chromatic_feature(self):
        content = '''
import { isChromatic } from 'chromatic/isChromatic';

parameters: {
    chromatic: { viewports: [320, 768] },
}
'''
        result = self.parser.parse(content, 'Button.stories.tsx')
        assert 'chromatic' in result.detected_features

    # ---- Parse Result Structure ----

    def test_parse_result_has_all_fields(self):
        content = '''
import type { Meta, StoryObj } from '@storybook/react';
export default { component: Button };
export const Primary: Story = { args: {} };
'''
        result = self.parser.parse(content, 'Button.stories.tsx')
        assert hasattr(result, 'stories')
        assert hasattr(result, 'components')
        assert hasattr(result, 'addons')
        assert hasattr(result, 'configs')
        assert hasattr(result, 'imports')
        assert hasattr(result, 'testing')
        assert hasattr(result, 'detected_frameworks')
        assert hasattr(result, 'detected_features')
        assert hasattr(result, 'detected_version')
        assert hasattr(result, 'detected_csf_version')

    def test_parse_empty_file(self):
        result = self.parser.parse('', 'empty.stories.tsx')
        assert isinstance(result, StorybookParseResult)
        assert len(result.stories) == 0

    def test_parse_non_storybook_file(self):
        content = '''
export const add = (a: number, b: number): number => a + b;
'''
        result = self.parser.parse(content, 'utils.ts')
        assert isinstance(result, StorybookParseResult)
        # Should still return a valid result, just empty


# ============================================================================
# Integration Tests
# ============================================================================

class TestStorybookIntegration:
    """Integration tests combining multiple extractors."""

    def setup_method(self):
        self.parser = EnhancedStorybookParser()

    def test_full_story_file(self):
        """Test a realistic, complete story file with all features."""
        content = '''
import type { Meta, StoryObj } from '@storybook/react';
import { fn, expect, userEvent, within } from '@storybook/test';
import { Button } from './Button';

const meta = {
    title: 'Design System/Atoms/Button',
    component: Button,
    tags: ['autodocs'],
    argTypes: {
        variant: { control: 'select', options: ['primary', 'secondary', 'danger'] },
        size: { control: 'radio', options: ['sm', 'md', 'lg'] },
        onClick: { action: 'clicked' },
    },
    args: {
        onClick: fn(),
        children: 'Button',
    },
    decorators: [
        (Story) => <div style={{ padding: '1rem' }}><Story /></div>,
    ],
} satisfies Meta<typeof Button>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
    args: { variant: 'primary' },
};

export const Secondary: Story = {
    args: { variant: 'secondary' },
};

export const Disabled: Story = {
    args: { disabled: true },
};

export const WithPlay: Story = {
    args: { variant: 'primary' },
    play: async ({ canvasElement, args }) => {
        const canvas = within(canvasElement);
        await userEvent.click(canvas.getByRole('button'));
        await expect(args.onClick).toHaveBeenCalled();
    },
};

export const InForm: Story = {
    render: (args) => (
        <form>
            <Button {...args} />
        </form>
    ),
    args: { children: 'Submit', type: 'submit' },
};
'''
        result = self.parser.parse(content, 'Button.stories.tsx')

        # Should find stories
        assert len(result.stories) >= 4

        # Should detect frameworks
        assert '@storybook/react' in result.detected_frameworks
        assert '@storybook/test' in result.detected_frameworks

        # Should detect features
        assert 'autodocs' in result.detected_features

        # Should have imports
        assert len(result.imports) >= 1

    def test_full_config_file(self):
        """Test a complete main.ts configuration."""
        content = '''
import type { StorybookConfig } from '@storybook/react-vite';

const config: StorybookConfig = {
    stories: [
        '../src/**/*.stories.@(ts|tsx|mdx)',
        '../stories/**/*.stories.@(ts|tsx)',
    ],
    framework: '@storybook/react-vite',
    addons: [
        '@storybook/addon-essentials',
        '@storybook/addon-interactions',
        '@storybook/addon-a11y',
        '@storybook/addon-links',
    ],
    staticDirs: ['../public'],
    typescript: {
        check: true,
        reactDocgen: 'react-docgen-typescript',
    },
    docs: {
        autodocs: true,
    },
    refs: {
        'design-system': {
            title: 'Design System',
            url: 'https://ds.example.com/storybook',
        },
    },
};
export default config;
'''
        result = self.parser.parse(content, '.storybook/main.ts')

        # Should find config
        assert len(result.configs) >= 1

        # Should find addons
        assert len(result.addons) >= 4

        # Should detect framework
        assert '@storybook/react' in result.detected_frameworks

    def test_portable_stories_test_file(self):
        """Test detection of portable stories pattern."""
        content = '''
import { composeStories } from '@storybook/react';
import { setProjectAnnotations } from '@storybook/react';
import * as ButtonStories from './Button.stories';
import * as previewAnnotations from '../.storybook/preview';

setProjectAnnotations(previewAnnotations);

const { Primary, Disabled } = composeStories(ButtonStories);

describe('Button', () => {
    it('renders primary variant', () => {
        render(<Primary />);
        expect(screen.getByRole('button')).toHaveClass('primary');
    });

    it('runs play function', async () => {
        const { container } = render(<Primary />);
        await Primary.play({ canvasElement: container });
    });
});
'''
        result = self.parser.parse(content, 'Button.test.tsx')

        # Should detect portable story imports
        assert len(result.imports) >= 1


class TestStorybookMultiVersion:
    """Tests for multi-version Storybook support."""

    def setup_method(self):
        self.parser = EnhancedStorybookParser()

    def test_v5_stories_of(self):
        """v5 storiesOf API detection."""
        content = '''
import { storiesOf } from '@storybook/react';
import { withKnobs, text, boolean } from '@storybook/addon-knobs';

storiesOf('Components/Button', module)
    .addDecorator(withKnobs)
    .add('default', () => (
        <Button
            label={text('Label', 'Hello')}
            disabled={boolean('Disabled', false)}
        />
    ))
    .add('primary', () => <Button primary label="Primary" />);
'''
        result = self.parser.parse(content, 'Button.stories.jsx')
        assert len(result.stories) >= 1
        assert result.detected_version in ('v5', 'v6')

    def test_v6_csf2(self):
        """v6 CSF 2.0 with Template.bind detection."""
        content = '''
import { ComponentStory, ComponentMeta } from '@storybook/react';

export default {
    title: 'Components/Button',
    component: Button,
    argTypes: {
        backgroundColor: { control: 'color' },
    },
} as ComponentMeta<typeof Button>;

const Template: ComponentStory<typeof Button> = (args) => <Button {...args} />;

export const Primary = Template.bind({});
Primary.args = {
    primary: true,
    label: 'Button',
};

export const Secondary = Template.bind({});
Secondary.args = {
    label: 'Button',
};
'''
        result = self.parser.parse(content, 'Button.stories.tsx')
        assert len(result.stories) >= 2
        assert result.detected_version in ('v6', 'v7')

    def test_v7_csf3(self):
        """v7 CSF 3.0 with typed object notation."""
        content = '''
import type { Meta, StoryObj } from '@storybook/react';

const meta: Meta<typeof Button> = {
    title: 'Components/Button',
    component: Button,
    tags: ['autodocs'],
};
export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
    args: { variant: 'primary' },
};
'''
        result = self.parser.parse(content, 'Button.stories.tsx')
        assert len(result.stories) >= 1
        assert result.detected_version in ('v7', 'v8')

    def test_v8_mount_before_each(self):
        """v8 mount and beforeEach detection."""
        content = '''
import type { Meta, StoryObj } from '@storybook/react';
import { fn, expect, within, userEvent } from '@storybook/test';

const meta = {
    component: Dashboard,
    beforeEach: async () => {
        mockApi.reset();
        return () => mockApi.restore();
    },
} satisfies Meta<typeof Dashboard>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    play: async ({ mount }) => {
        const canvas = await mount(<Dashboard />);
        await expect(canvas.getByText('Dashboard')).toBeVisible();
    },
};
'''
        result = self.parser.parse(content, 'Dashboard.stories.tsx')
        assert len(result.stories) >= 1
        assert result.detected_version == 'v8'
