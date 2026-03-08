"""
CodeTrellis Storybook Extractors Module v1.0

Provides comprehensive extractors for the Storybook framework:

Story Extractor:
- StorybookStoryExtractor: Story definitions in CSF (v1/v2/v3), MDX,
                            storiesOf API, play functions, render functions,
                            argTypes, args, decorators, loaders

Component Extractor:
- StorybookComponentExtractor: Component documentation, autodocs,
                                 component/subcomponents metadata,
                                 controls, doc blocks, source code

Addon Extractor:
- StorybookAddonExtractor: Addon registrations, addon configs,
                             addon panels, decorators, parameters,
                             tool registration, arg types enhancers

Config Extractor:
- StorybookConfigExtractor: .storybook/main.{js,ts}, preview.{js,ts},
                              manager.{js,ts}, framework configs,
                              builders (webpack/vite), stories glob,
                              staticDirs, addons, features, env vars

API Extractor:
- StorybookApiExtractor: Import patterns (@storybook/*), API usage
                          (useArgs, useChannel, useGlobals, useParameter,
                          useStorybookState), testing utilities
                          (@storybook/test, composeStories, composeStory),
                          interaction testing, visual testing

Supports:
- Storybook 5.x (storiesOf API, knobs addon)
- Storybook 6.x (CSF 2.0, args/argTypes, controls, actions, MDX 1)
- Storybook 7.x (CSF 3.0, play functions, MDX 2, framework packages,
                  vite builder, autodocs, interaction testing)
- Storybook 8.x (CSF 3.0+, MDX 3, portable stories, mount, beforeEach,
                  vitest integration, visual testing, tags, project annotations)

Frameworks: React, Vue, Angular, Svelte, Web Components, HTML,
            Preact, Ember, Next.js, SvelteKit, Nuxt, Remix

Part of CodeTrellis v4.70 - Storybook Framework Support
"""

from .story_extractor import (
    StorybookStoryExtractor,
    StorybookStoryInfo,
)

from .component_extractor import (
    StorybookComponentExtractor,
    StorybookComponentInfo,
)

from .addon_extractor import (
    StorybookAddonExtractor,
    StorybookAddonInfo,
)

from .config_extractor import (
    StorybookConfigExtractor,
    StorybookConfigInfo,
)

from .api_extractor import (
    StorybookApiExtractor,
    StorybookImportInfo,
    StorybookTestingInfo,
)

__all__ = [
    # Story
    "StorybookStoryExtractor",
    "StorybookStoryInfo",
    # Component
    "StorybookComponentExtractor",
    "StorybookComponentInfo",
    # Addon
    "StorybookAddonExtractor",
    "StorybookAddonInfo",
    # Config
    "StorybookConfigExtractor",
    "StorybookConfigInfo",
    # API
    "StorybookApiExtractor",
    "StorybookImportInfo",
    "StorybookTestingInfo",
]
