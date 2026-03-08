"""
Storybook Component Extractor for CodeTrellis

Extracts Storybook component documentation metadata:
- Component declarations (component: Button)
- Subcomponents (subcomponents: { IconButton, ... })
- Autodocs tag (tags: ['autodocs'])
- ArgTypes with control types
- Doc blocks (Description, Primary, Controls, Stories)
- Source code annotations
- Component decorators

Supports:
- Storybook 6.x (component, subcomponents, argTypes with controls)
- Storybook 7.x (autodocs, Doc Blocks, CSF 3 component)
- Storybook 8.x (tags, portable stories, project annotations)

Part of CodeTrellis v4.70 - Storybook Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StorybookComponentInfo:
    """Information about a component documented in Storybook."""
    name: str  # Component name (from `component:`)
    file: str = ""
    line_number: int = 0
    title: str = ""  # Story title path (e.g., "Components/Button")
    has_autodocs: bool = False  # tags: ['autodocs']
    has_subcomponents: bool = False
    subcomponents: List[str] = field(default_factory=list)
    arg_types: List[str] = field(default_factory=list)  # ArgType names
    control_types: List[str] = field(default_factory=list)  # Control type names
    doc_blocks: List[str] = field(default_factory=list)  # Doc block components used
    decorators: List[str] = field(default_factory=list)  # Decorator descriptions
    story_count: int = 0  # Number of stories in this file
    has_source: bool = False  # Has source code annotation
    has_docs_page: bool = False  # Custom docs page
    category: str = ""  # Extracted from title path


# ── Component declaration ─────────────────────────────────────────
COMPONENT_DECL_PATTERN = re.compile(
    r'\bcomponent\s*:\s*(\w+)',
    re.MULTILINE
)

# ── Subcomponents ──────────────────────────────────────────────────
SUBCOMPONENTS_PATTERN = re.compile(
    r'\bsubcomponents\s*:\s*\{([^}]*)\}',
    re.DOTALL
)

# ── Autodocs tag ───────────────────────────────────────────────────
AUTODOCS_PATTERN = re.compile(
    r"""tags\s*:\s*\[.*?['"]autodocs['"].*?\]""",
    re.DOTALL
)

# ── ArgTypes ────────────────────────────────────────────────────────
ARGTYPES_PATTERN = re.compile(
    r'\bargTypes\s*:\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
    re.DOTALL
)

# Control type in argType
CONTROL_TYPE_PATTERN = re.compile(
    r'control\s*:\s*(?:["\'](\w+)["\']|\{\s*type\s*:\s*["\'](\w+)["\'])',
    re.MULTILINE
)

# ── Doc Blocks (MDX) ──────────────────────────────────────────────
DOC_BLOCK_PATTERN = re.compile(
    r'<(Description|Primary|Controls|Stories|Source|Canvas|'
    r'ArgTypes|ArgsTable|Subtitle|Title|Heading|Markdown|Unstyled|'
    r'ColorPalette|ColorItem|IconGallery|IconItem|Typeset)',
    re.MULTILINE
)

# ── Source annotation ──────────────────────────────────────────────
SOURCE_PATTERN = re.compile(
    r'parameters\s*:\s*\{[^}]*docs\s*:\s*\{[^}]*source',
    re.DOTALL
)

# ── Custom docs page ──────────────────────────────────────────────
DOCS_PAGE_PATTERN = re.compile(
    r'docs\s*:\s*\{[^}]*page\s*:',
    re.DOTALL
)

# ── Title extraction ──────────────────────────────────────────────
TITLE_PATTERN = re.compile(r'\btitle\s*:\s*["\']([^"\']+)["\']', re.MULTILINE)

# ── Named export count (story count) ──────────────────────────────
NAMED_EXPORT_PATTERN = re.compile(
    r'^export\s+const\s+(?!default\s)(\w+)',
    re.MULTILINE
)


class StorybookComponentExtractor:
    """
    Extracts component documentation metadata from Storybook files.

    Detects:
    - Component declarations and subcomponents
    - Autodocs configuration
    - ArgTypes with control types
    - Doc blocks usage (MDX)
    - Source code annotations
    """

    def extract(self, content: str, file_path: str = "") -> List[StorybookComponentInfo]:
        """Extract component documentation metadata.

        Args:
            content: File content to parse.
            file_path: Path to the file.

        Returns:
            List of StorybookComponentInfo objects.
        """
        results: List[StorybookComponentInfo] = []

        # Find all component declarations in this file
        comp_matches = list(COMPONENT_DECL_PATTERN.finditer(content))

        # For MDX files with doc blocks but no `component:`, still extract
        doc_block_matches = list(DOC_BLOCK_PATTERN.finditer(content))
        mdx_meta_match = re.search(r'<Meta\s+', content)

        if not comp_matches and not doc_block_matches:
            return results

        # Determine component name
        if comp_matches:
            primary_comp = comp_matches[0]
            comp_name = primary_comp.group(1)
            comp_line = content[:primary_comp.start()].count("\n") + 1
        elif mdx_meta_match:
            # MDX file with <Meta of={Stories}> — infer name from of= or title
            of_match = re.search(r'<Meta\s+of=\{(\w+)\}', content)
            comp_name = of_match.group(1) if of_match else "Unknown"
            comp_line = content[:mdx_meta_match.start()].count("\n") + 1
        else:
            comp_name = "Unknown"
            comp_line = 1

        # Extract title
        title = ""
        title_match = TITLE_PATTERN.search(content)
        if title_match:
            title = title_match.group(1)

        # Extract category from title path
        category = ""
        if title and "/" in title:
            category = title.rsplit("/", 1)[0]

        info = StorybookComponentInfo(
            name=comp_name,
            file=file_path,
            line_number=comp_line,
            title=title,
            category=category,
        )

        # Autodocs
        info.has_autodocs = bool(AUTODOCS_PATTERN.search(content))

        # Subcomponents
        sub_match = SUBCOMPONENTS_PATTERN.search(content)
        if sub_match:
            info.has_subcomponents = True
            info.subcomponents = re.findall(r'(\w+)', sub_match.group(1))[:10]

        # ArgTypes
        argtypes_match = ARGTYPES_PATTERN.search(content)
        if argtypes_match:
            body = argtypes_match.group(1)
            # Extract top-level keys
            info.arg_types = re.findall(r'(\w+)\s*:', body)[:20]
            # Extract control types
            for cm in CONTROL_TYPE_PATTERN.finditer(body):
                ctrl_type = cm.group(1) or cm.group(2)
                if ctrl_type and ctrl_type not in info.control_types:
                    info.control_types.append(ctrl_type)

        # Doc blocks (MDX)
        for db_match in DOC_BLOCK_PATTERN.finditer(content):
            block_name = db_match.group(1)
            if block_name not in info.doc_blocks:
                info.doc_blocks.append(block_name)

        # Source annotation
        info.has_source = bool(SOURCE_PATTERN.search(content))

        # Custom docs page
        info.has_docs_page = bool(DOCS_PAGE_PATTERN.search(content))

        # Story count (named exports minus meta)
        exports = NAMED_EXPORT_PATTERN.findall(content)
        info.story_count = len([e for e in exports if e not in ("meta", "default", "__namedExportsOrder")])

        # Decorators in meta
        decorators_match = re.search(r'decorators\s*:\s*\[([^\]]*)\]', content, re.DOTALL)
        if decorators_match:
            dec_body = decorators_match.group(1)
            # Extract function names or descriptions
            for dm in re.finditer(r'(\w+)\s*(?:\(|,|\])', dec_body):
                dec_name = dm.group(1)
                if dec_name not in ("Story", "fn", "args", "const", "return"):
                    info.decorators.append(dec_name)

        results.append(info)
        return results
