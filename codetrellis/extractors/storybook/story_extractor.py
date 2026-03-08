"""
Storybook Story Extractor for CodeTrellis

Extracts Storybook story definitions from JavaScript/TypeScript/MDX source code:
- CSF 1.0: Named exports with component/title metadata
- CSF 2.0: Args/argTypes on story objects, Template.bind({})
- CSF 3.0: Object notation stories with render/play/args/argTypes
- storiesOf API (legacy Storybook 5.x)
- MDX stories: <Story>, <Canvas>, <Meta> components
- Play functions (interaction testing)
- Render functions
- Decorators and loaders (story-level and meta-level)
- Parameters (layout, backgrounds, viewport, etc.)
- Tags (autodocs, !dev, !test, etc.)

Supports:
- Storybook 5.x (storiesOf, knobs)
- Storybook 6.x (CSF 2.0, Template.bind, controls, actions)
- Storybook 7.x (CSF 3.0, play functions, interaction testing, autodocs)
- Storybook 8.x (CSF 3.0+, mount in play, beforeEach, portable stories)

Part of CodeTrellis v4.70 - Storybook Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StorybookStoryInfo:
    """Information about a Storybook story definition."""
    name: str  # Story export name (e.g., Primary, Default, WithArgs)
    file: str = ""
    line_number: int = 0
    title: str = ""  # Meta title (e.g., "Components/Button")
    component_name: str = ""  # Component being documented
    csf_version: str = ""  # csf1, csf2, csf3
    story_type: str = ""  # named_export, stories_of, mdx, template_bind
    has_args: bool = False
    has_arg_types: bool = False
    has_play: bool = False  # CSF 3.0 play function
    has_render: bool = False  # Custom render function
    has_decorators: bool = False
    has_loaders: bool = False  # v6.1+
    has_parameters: bool = False
    has_template: bool = False  # CSF 2.0 Template.bind({})
    has_before_each: bool = False  # v8.x
    has_mount: bool = False  # v8.x mount in play
    is_default_export: bool = False  # Meta/default export
    tags: List[str] = field(default_factory=list)  # v7+ tags
    args_keys: List[str] = field(default_factory=list)
    arg_type_keys: List[str] = field(default_factory=list)
    decorator_count: int = 0
    parameter_keys: List[str] = field(default_factory=list)


# ── CSF 3.0: Object notation stories ─────────────────────────────────
# export const Primary: Story = { args: {...}, render: ..., play: ... }
CSF3_STORY_PATTERN = re.compile(
    r'^export\s+const\s+(?P<name>\w+)'
    r'(?:\s*:\s*(?:Story|StoryObj|StoryFn|Meta)(?:<[^>]*>)?)?'
    r'\s*=\s*\{',
    re.MULTILINE
)

# ── CSF 2.0: Template.bind stories ─────────────────────────────────
# export const Primary = Template.bind({})
CSF2_TEMPLATE_BIND_PATTERN = re.compile(
    r'^export\s+const\s+(?P<name>\w+)\s*=\s*'
    r'(?P<template>\w+)\.bind\s*\(\s*\{',
    re.MULTILINE
)

# ── CSF 1.0/2.0: Simple named export stories ──────────────────────
# export const Primary = () => <Button />
# export const Primary = (args) => <Button {...args} />
CSF1_STORY_PATTERN = re.compile(
    r'^export\s+const\s+(?P<name>\w+)\s*=\s*'
    r'(?:\([^)]*\)\s*=>|\([^)]*\)\s*:\s*\w+\s*=>|function)',
    re.MULTILINE
)

# ── Default export (Meta) ──────────────────────────────────────────
# export default { title: 'Components/Button', component: Button, ... }
# const meta: Meta<typeof Button> = { ... }; export default meta;
# const meta = { ... } satisfies Meta<typeof Button>; export default meta;
DEFAULT_EXPORT_PATTERN = re.compile(
    r'export\s+default\s+(?:\{|(?P<meta_var>\w+)\s*;?)',
    re.MULTILINE
)

# Meta variable pattern: const meta = { ... } or const meta: Meta<...> = { ... }
META_VAR_PATTERN = re.compile(
    r'(?:const|let|var)\s+(?P<name>\w+)'
    r'(?:\s*:\s*Meta(?:<[^>]*>)?)?'
    r'\s*=\s*\{',
    re.MULTILINE
)

# ── storiesOf API (legacy) ─────────────────────────────────────────
# storiesOf('Components/Button', module).add('Primary', () => <Button />)
STORIES_OF_PATTERN = re.compile(
    r'storiesOf\s*\(\s*["\']([^"\']+)["\']\s*,\s*module\s*\)',
    re.MULTILINE
)

# .add('StoryName', ...)
STORIES_OF_ADD_PATTERN = re.compile(
    r'\.add\s*\(\s*["\']([^"\']+)["\']\s*,',
    re.MULTILINE
)

# ── MDX components ──────────────────────────────────────────────────
# <Meta title="Components/Button" component={Button} />
MDX_META_PATTERN = re.compile(
    r'<Meta\s+([^>]*)/?>',
    re.DOTALL
)

# <Story name="Primary">...</Story>  or  <Story of={Primary} />
MDX_STORY_PATTERN = re.compile(
    r'<Story\s+(?:name=["\']([^"\']+)["\']|of=\{(\w+)\})',
    re.MULTILINE
)

# <Canvas> block
MDX_CANVAS_PATTERN = re.compile(r'<Canvas', re.MULTILINE)

# ── Story-level properties ───────────────────────────────────────
ARGS_PATTERN = re.compile(r'\bargs\s*:\s*\{', re.MULTILINE)
ARG_TYPES_PATTERN = re.compile(r'\bargTypes\s*:\s*\{', re.MULTILINE)
PLAY_PATTERN = re.compile(r'\bplay\s*:\s*(?:async\s+)?\(?\{?\s*(?:canvasElement|mount|step)', re.MULTILINE)
RENDER_PATTERN = re.compile(r'\brender\s*:\s*(?:\([^)]*\)|function)', re.MULTILINE)
DECORATORS_PATTERN = re.compile(r'\bdecorators\s*:\s*\[', re.MULTILINE)
LOADERS_PATTERN = re.compile(r'\bloaders\s*:\s*\[', re.MULTILINE)
PARAMETERS_PATTERN = re.compile(r'\bparameters\s*:\s*\{', re.MULTILINE)
TAGS_PATTERN = re.compile(r'\btags\s*:\s*\[([^\]]*)\]', re.MULTILINE)
BEFORE_EACH_PATTERN = re.compile(r'\bbeforeEach\s*:\s*', re.MULTILINE)
MOUNT_PATTERN = re.compile(r'\bmount\s*\(', re.MULTILINE)

# ── Title / component from meta ───────────────────────────────────
TITLE_PATTERN = re.compile(r'\btitle\s*:\s*["\']([^"\']+)["\']', re.MULTILINE)
COMPONENT_PATTERN = re.compile(r'\bcomponent\s*:\s*(\w+)', re.MULTILINE)

# ── Template pattern ──────────────────────────────────────────────
TEMPLATE_PATTERN = re.compile(
    r'(?:const|let|var)\s+Template\s*(?::\s*\w+(?:<[^>]*>)?\s*)?=\s*',
    re.MULTILINE
)

# Args keys extraction
ARGS_KEYS_PATTERN = re.compile(
    r'args\s*:\s*\{([^}]*)\}',
    re.DOTALL
)

# ArgTypes keys extraction
ARG_TYPE_KEYS_PATTERN = re.compile(
    r'argTypes\s*:\s*\{([^}]*)\}',
    re.DOTALL
)

# Key extraction from object
OBJECT_KEY_PATTERN = re.compile(r'(\w+)\s*:', re.MULTILINE)

# Parameters keys extraction
PARAM_KEYS_PATTERN = re.compile(
    r'parameters\s*:\s*\{([^}]*)\}',
    re.DOTALL
)


class StorybookStoryExtractor:
    """
    Extracts Storybook story definitions from JS/TS/MDX source code.

    Detects:
    - CSF 3.0 object stories (v7+)
    - CSF 2.0 Template.bind stories (v6.x)
    - CSF 1.0 function export stories (v5.x)
    - storiesOf API (legacy v5.x)
    - MDX stories (<Meta>, <Story>, <Canvas>)
    - Play functions, render, decorators, loaders, parameters, tags
    """

    def extract(self, content: str, file_path: str = "") -> List[StorybookStoryInfo]:
        """Extract all story definitions from source code.

        Args:
            content: File content to parse.
            file_path: Path to the file (for metadata).

        Returns:
            List of StorybookStoryInfo objects.
        """
        results: List[StorybookStoryInfo] = []
        seen_names: set = set()

        # Extract meta-level info (title, component)
        meta_title = ""
        meta_component = ""
        title_match = TITLE_PATTERN.search(content)
        if title_match:
            meta_title = title_match.group(1)
        comp_match = COMPONENT_PATTERN.search(content)
        if comp_match:
            meta_component = comp_match.group(1)

        # Check for template
        has_template = bool(TEMPLATE_PATTERN.search(content))

        # ── CSF 3.0 stories ──────────────────────────────────
        for m in CSF3_STORY_PATTERN.finditer(content):
            name = m.group("name")
            if name in ("default", "meta", "__namedExportsOrder"):
                continue
            if name in seen_names:
                continue
            seen_names.add(name)

            # Get context around this story for property detection
            start = m.start()
            # Find the story object end (brace matching)
            story_body = self._extract_brace_body(content, start)

            info = StorybookStoryInfo(
                name=name,
                file=file_path,
                line_number=content[:start].count("\n") + 1,
                title=meta_title,
                component_name=meta_component,
                csf_version="csf3",
                story_type="named_export",
                has_args=bool(ARGS_PATTERN.search(story_body)),
                has_arg_types=bool(ARG_TYPES_PATTERN.search(story_body)),
                has_play=bool(PLAY_PATTERN.search(story_body)),
                has_render=bool(RENDER_PATTERN.search(story_body)),
                has_decorators=bool(DECORATORS_PATTERN.search(story_body)),
                has_loaders=bool(LOADERS_PATTERN.search(story_body)),
                has_parameters=bool(PARAMETERS_PATTERN.search(story_body)),
                has_template=False,
                has_before_each=bool(BEFORE_EACH_PATTERN.search(story_body)),
                has_mount=bool(MOUNT_PATTERN.search(story_body)),
            )

            # Extract tags
            tags_match = TAGS_PATTERN.search(story_body)
            if tags_match:
                info.tags = self._extract_string_list(tags_match.group(1))

            # Extract args keys
            info.args_keys = self._extract_object_keys(story_body, ARGS_KEYS_PATTERN)
            info.arg_type_keys = self._extract_object_keys(story_body, ARG_TYPE_KEYS_PATTERN)
            info.parameter_keys = self._extract_object_keys(story_body, PARAM_KEYS_PATTERN)

            if info.has_decorators:
                info.decorator_count = story_body.count("(") - story_body.count("=>")  # rough

            results.append(info)

        # ── CSF 2.0 Template.bind stories ─────────────────────
        for m in CSF2_TEMPLATE_BIND_PATTERN.finditer(content):
            name = m.group("name")
            if name in seen_names:
                continue
            seen_names.add(name)

            start = m.start()
            # Look for .args = { ... } and .argTypes = { ... } after bind
            post_content = content[start:start + 1000]

            info = StorybookStoryInfo(
                name=name,
                file=file_path,
                line_number=content[:start].count("\n") + 1,
                title=meta_title,
                component_name=meta_component,
                csf_version="csf2",
                story_type="template_bind",
                has_template=True,
            )

            # Check for StoryName.args = { ... }
            args_assign = re.search(
                rf'{re.escape(name)}\.args\s*=\s*\{{', post_content
            )
            if args_assign:
                info.has_args = True
                info.args_keys = self._extract_object_keys(
                    post_content[args_assign.start():], ARGS_KEYS_PATTERN
                )

            # Check for StoryName.argTypes = { ... }
            argtypes_assign = re.search(
                rf'{re.escape(name)}\.argTypes\s*=\s*\{{', post_content
            )
            if argtypes_assign:
                info.has_arg_types = True

            # Check for StoryName.decorators = [...]
            if re.search(rf'{re.escape(name)}\.decorators\s*=\s*\[', post_content):
                info.has_decorators = True

            # Check for StoryName.parameters = { ... }
            if re.search(rf'{re.escape(name)}\.parameters\s*=\s*\{{', post_content):
                info.has_parameters = True

            # Check for StoryName.play = ...
            if re.search(rf'{re.escape(name)}\.play\s*=\s*', post_content):
                info.has_play = True

            results.append(info)

        # ── CSF 1.0 function stories ──────────────────────────
        for m in CSF1_STORY_PATTERN.finditer(content):
            name = m.group("name")
            if name in ("default", "meta", "Template", "__namedExportsOrder"):
                continue
            if name in seen_names:
                continue
            seen_names.add(name)

            start = m.start()
            info = StorybookStoryInfo(
                name=name,
                file=file_path,
                line_number=content[:start].count("\n") + 1,
                title=meta_title,
                component_name=meta_component,
                csf_version="csf1",
                story_type="named_export",
            )
            results.append(info)

        # ── storiesOf API (legacy) ─────────────────────────────
        for m in STORIES_OF_PATTERN.finditer(content):
            stories_of_title = m.group(1)
            start_pos = m.end()
            # Find all .add() calls chained
            for add_m in STORIES_OF_ADD_PATTERN.finditer(content[start_pos:]):
                story_name = add_m.group(1)
                if story_name in seen_names:
                    continue
                seen_names.add(story_name)
                info = StorybookStoryInfo(
                    name=story_name,
                    file=file_path,
                    line_number=content[:start_pos + add_m.start()].count("\n") + 1,
                    title=stories_of_title,
                    csf_version="legacy",
                    story_type="stories_of",
                )
                results.append(info)

        # ── MDX stories ────────────────────────────────────────
        # Extract <Meta> for title/component
        mdx_meta_match = MDX_META_PATTERN.search(content)
        if mdx_meta_match:
            meta_attrs = mdx_meta_match.group(1)
            mdx_title_match = re.search(r'title=["\']([^"\']+)["\']', meta_attrs)
            if mdx_title_match:
                meta_title = mdx_title_match.group(1)
            mdx_comp_match = re.search(r'component=\{(\w+)\}', meta_attrs)
            if mdx_comp_match:
                meta_component = mdx_comp_match.group(1)

        # Extract <Story> blocks
        for m in MDX_STORY_PATTERN.finditer(content):
            story_name = m.group(1) or m.group(2) or "Unknown"
            if story_name in seen_names:
                continue
            seen_names.add(story_name)
            info = StorybookStoryInfo(
                name=story_name,
                file=file_path,
                line_number=content[:m.start()].count("\n") + 1,
                title=meta_title,
                component_name=meta_component,
                csf_version="mdx",
                story_type="mdx",
            )
            results.append(info)

        # ── Default export (Meta) ──────────────────────────────
        default_match = DEFAULT_EXPORT_PATTERN.search(content)
        if default_match and "default" not in seen_names:
            start = default_match.start()
            meta_body = ""

            # Check if this is `export default { ... }` (inline) or
            # `export default meta;` (variable reference)
            meta_var = default_match.group("meta_var")
            if meta_var:
                # Find the variable definition: const meta = { ... }
                var_pattern = re.compile(
                    rf'(?:const|let|var)\s+{re.escape(meta_var)}'
                    rf'(?:\s*:\s*\w+(?:<[^>]*>)?)?\s*=\s*\{{',
                    re.MULTILINE,
                )
                var_match = var_pattern.search(content)
                if var_match:
                    meta_body = self._extract_brace_body(content, var_match.start())
            elif "{" in content[start:start + 200]:
                meta_body = self._extract_brace_body(content, start)

            info = StorybookStoryInfo(
                name="__meta__",
                file=file_path,
                line_number=content[:start].count("\n") + 1,
                title=meta_title,
                component_name=meta_component,
                is_default_export=True,
                story_type="meta",
            )

            if meta_body:
                info.has_args = bool(ARGS_PATTERN.search(meta_body))
                info.has_arg_types = bool(ARG_TYPES_PATTERN.search(meta_body))
                info.has_decorators = bool(DECORATORS_PATTERN.search(meta_body))
                info.has_loaders = bool(LOADERS_PATTERN.search(meta_body))
                info.has_parameters = bool(PARAMETERS_PATTERN.search(meta_body))
                info.has_before_each = bool(BEFORE_EACH_PATTERN.search(meta_body))

                tags_match = TAGS_PATTERN.search(meta_body)
                if tags_match:
                    info.tags = self._extract_string_list(tags_match.group(1))

                info.parameter_keys = self._extract_object_keys(meta_body, PARAM_KEYS_PATTERN)

            results.append(info)

        return results

    def _extract_brace_body(self, content: str, start: int) -> str:
        """Extract content within braces starting from a position."""
        brace_start = content.find("{", start)
        if brace_start == -1:
            return ""
        depth = 0
        for i in range(brace_start, min(len(content), brace_start + 5000)):
            if content[i] == "{":
                depth += 1
            elif content[i] == "}":
                depth -= 1
                if depth == 0:
                    return content[brace_start:i + 1]
        return content[brace_start:brace_start + 2000]

    def _extract_string_list(self, text: str) -> List[str]:
        """Extract string values from a list literal."""
        return re.findall(r'["\']([^"\']+)["\']', text)

    def _extract_object_keys(self, text: str, pattern: re.Pattern) -> List[str]:
        """Extract top-level keys from an object literal found by pattern."""
        match = pattern.search(text)
        if not match:
            return []
        body = match.group(1)
        keys = OBJECT_KEY_PATTERN.findall(body)
        # Filter out common non-key words
        skip = {"return", "const", "let", "var", "if", "else", "true", "false", "null", "undefined"}
        return [k for k in keys if k not in skip][:20]
