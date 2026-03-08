"""
Bootstrap Component Extractor for CodeTrellis

Extracts Bootstrap component usage from HTML, JSX/TSX, and JavaScript/TypeScript
source code. Covers Bootstrap v3.x through v5.x, including:

Layout:
- Container, Row, Col (grid system)
- Breakpoint-responsive variants (col-sm-*, col-md-*, col-lg-*, col-xl-*, col-xxl-*)

Content:
- Typography (h1-h6, .lead, .display-*, .text-*)
- Images (.img-fluid, .img-thumbnail, .figure)
- Tables (.table, .table-striped, .table-bordered, .table-hover, .table-responsive)

Components (50+):
- Accordion, Alert, Badge, Breadcrumb, Button, ButtonGroup
- Card, Carousel, Collapse, Dropdown, ListGroup
- Modal, Navbar, Nav, Offcanvas, Pagination
- Placeholder, Popover, Progress, ScrollSpy, Spinner
- Toast, Tooltip, Close button

Forms:
- FormControl, FormSelect, FormCheck, FormRange, FormFloating
- InputGroup, FormText, Validation (.is-valid, .is-invalid, .valid-feedback)

Utilities:
- Spacing (m-*, p-*), Sizing (w-*, h-*), Display (d-*)
- Flex (d-flex, flex-*, align-items-*, justify-content-*)
- Colors (text-*, bg-*, border-*)
- Position, Shadows, Borders, Rounded, Opacity, Overflow

Part of CodeTrellis v4.40 - Bootstrap Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class BootstrapComponentInfo:
    """Information about a Bootstrap component usage."""
    name: str
    file: str = ""
    line_number: int = 0
    import_source: str = ""
    category: str = ""
    variant: str = ""
    props_used: List[str] = field(default_factory=list)
    classes_used: List[str] = field(default_factory=list)
    has_responsive: bool = False
    has_js_init: bool = False
    sub_components: List[str] = field(default_factory=list)


@dataclass
class BootstrapCustomComponentInfo:
    """Information about a custom component wrapping Bootstrap."""
    name: str
    file: str = ""
    line_number: int = 0
    base_component: str = ""
    method: str = ""
    has_theme_usage: bool = False
    additional_props: List[str] = field(default_factory=list)


class BootstrapComponentExtractor:
    """
    Extracts Bootstrap component usage from HTML/JSX/TSX source code.

    Detects:
    - Bootstrap CSS class-based components (50+ components)
    - React-Bootstrap / reactstrap JSX components
    - Bootstrap JS-initialized components (data-bs-toggle, jQuery)
    - Custom components wrapping Bootstrap
    - Sub-component composition (Card.Body, Modal.Header, etc.)
    """

    # Bootstrap component categories by CSS class prefix
    COMPONENT_CATEGORIES = {
        # Layout
        'container': 'layout', 'container-fluid': 'layout',
        'container-sm': 'layout', 'container-md': 'layout',
        'container-lg': 'layout', 'container-xl': 'layout',
        'container-xxl': 'layout',
        'row': 'layout', 'col': 'layout',
        'grid': 'layout',

        # Content
        'table': 'content', 'figure': 'content',
        'img-fluid': 'content', 'img-thumbnail': 'content',

        # Components
        'accordion': 'disclosure', 'alert': 'feedback',
        'badge': 'data-display', 'breadcrumb': 'navigation',
        'btn': 'forms', 'btn-group': 'forms', 'btn-toolbar': 'forms',
        'card': 'data-display', 'carousel': 'data-display',
        'collapse': 'disclosure', 'dropdown': 'overlay',
        'list-group': 'data-display', 'modal': 'overlay',
        'navbar': 'navigation', 'nav': 'navigation',
        'offcanvas': 'overlay', 'pagination': 'navigation',
        'placeholder': 'feedback', 'popover': 'overlay',
        'progress': 'feedback', 'scrollspy': 'navigation',
        'spinner': 'feedback', 'toast': 'feedback',
        'tooltip': 'overlay', 'close': 'utility',
        'tab': 'navigation',

        # Forms
        'form-control': 'forms', 'form-select': 'forms',
        'form-check': 'forms', 'form-range': 'forms',
        'form-floating': 'forms', 'form-label': 'forms',
        'form-text': 'forms', 'input-group': 'forms',
        'form-switch': 'forms',

        # Utility
        'clearfix': 'utility', 'ratio': 'utility',
        'visually-hidden': 'utility', 'stretched-link': 'utility',
        'text-truncate': 'utility', 'vstack': 'layout',
        'hstack': 'layout', 'vr': 'utility',
    }

    # React-Bootstrap / reactstrap component mappings
    REACT_COMPONENT_CATEGORIES = {
        # React-Bootstrap components
        'Accordion': 'disclosure', 'Alert': 'feedback',
        'Badge': 'data-display', 'Breadcrumb': 'navigation',
        'Button': 'forms', 'ButtonGroup': 'forms', 'ButtonToolbar': 'forms',
        'Card': 'data-display', 'Carousel': 'data-display',
        'CloseButton': 'utility',
        'Col': 'layout', 'Container': 'layout', 'Row': 'layout',
        'Collapse': 'disclosure', 'Dropdown': 'overlay',
        'Figure': 'content', 'FloatingLabel': 'forms',
        'Form': 'forms', 'FormControl': 'forms', 'FormGroup': 'forms',
        'FormLabel': 'forms', 'FormText': 'forms', 'FormCheck': 'forms',
        'FormSelect': 'forms', 'FormFloating': 'forms',
        'Image': 'content', 'InputGroup': 'forms',
        'ListGroup': 'data-display', 'ListGroupItem': 'data-display',
        'Modal': 'overlay', 'ModalHeader': 'overlay',
        'ModalBody': 'overlay', 'ModalFooter': 'overlay',
        'ModalTitle': 'overlay', 'ModalDialog': 'overlay',
        'Nav': 'navigation', 'NavItem': 'navigation',
        'NavLink': 'navigation', 'NavDropdown': 'navigation',
        'Navbar': 'navigation', 'NavbarBrand': 'navigation',
        'NavbarToggle': 'navigation', 'NavbarCollapse': 'navigation',
        'NavbarText': 'navigation', 'NavbarOffcanvas': 'navigation',
        'Offcanvas': 'overlay', 'OffcanvasHeader': 'overlay',
        'OffcanvasBody': 'overlay', 'OffcanvasTitle': 'overlay',
        'Overlay': 'overlay', 'OverlayTrigger': 'overlay',
        'PageItem': 'navigation', 'Pagination': 'navigation',
        'Placeholder': 'feedback', 'PlaceholderButton': 'feedback',
        'Popover': 'overlay', 'PopoverHeader': 'overlay',
        'PopoverBody': 'overlay',
        'ProgressBar': 'feedback', 'Ratio': 'utility',
        'Spinner': 'feedback', 'SplitButton': 'overlay',
        'Stack': 'layout', 'Tab': 'navigation', 'Tabs': 'navigation',
        'Table': 'content',
        'Toast': 'feedback', 'ToastHeader': 'feedback',
        'ToastBody': 'feedback', 'ToastContainer': 'feedback',
        'ToggleButton': 'forms', 'ToggleButtonGroup': 'forms',
        'Tooltip': 'overlay',
    }

    # Sub-component patterns
    SUB_COMPONENT_PATTERNS = {
        'Accordion': ['Item', 'Header', 'Body', 'Button', 'Collapse'],
        'Card': ['Body', 'Header', 'Footer', 'Title', 'Subtitle',
                 'Text', 'Img', 'ImgOverlay', 'Link', 'Group'],
        'Carousel': ['Item', 'Caption', 'Control'],
        'Dropdown': ['Toggle', 'Menu', 'Item', 'ItemText', 'Divider',
                     'Header'],
        'ListGroup': ['Item'],
        'Modal': ['Header', 'Body', 'Footer', 'Title', 'Dialog'],
        'Nav': ['Item', 'Link'],
        'Navbar': ['Brand', 'Toggle', 'Collapse', 'Text', 'Offcanvas'],
        'Offcanvas': ['Header', 'Body', 'Title'],
        'Pagination': ['Item', 'First', 'Prev', 'Next', 'Last', 'Ellipsis'],
        'Popover': ['Header', 'Body'],
        'Toast': ['Header', 'Body', 'Container'],
        'Form': ['Control', 'Group', 'Label', 'Text', 'Check',
                 'Select', 'Range', 'Floating'],
        'InputGroup': ['Text', 'Checkbox', 'Radio'],
        'Figure': ['Image', 'Caption'],
        'Tab': ['Container', 'Content', 'Pane'],
    }

    # Bootstrap JS data attributes
    DATA_BS_PATTERNS = [
        'data-bs-toggle', 'data-bs-target', 'data-bs-dismiss',
        'data-bs-backdrop', 'data-bs-keyboard', 'data-bs-scroll',
        'data-bs-placement', 'data-bs-trigger', 'data-bs-content',
        'data-bs-title', 'data-bs-ride', 'data-bs-slide',
        'data-bs-slide-to', 'data-bs-interval', 'data-bs-parent',
        'data-bs-config', 'data-bs-spy', 'data-bs-offset',
        'data-bs-delay', 'data-bs-animation', 'data-bs-html',
        'data-bs-theme',
    ]

    # Legacy v3/v4 data attributes
    DATA_LEGACY_PATTERNS = [
        'data-toggle', 'data-target', 'data-dismiss',
        'data-backdrop', 'data-keyboard', 'data-placement',
        'data-trigger', 'data-content', 'data-ride',
        'data-slide', 'data-slide-to', 'data-interval',
        'data-parent', 'data-spy', 'data-offset',
    ]

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Bootstrap component usage from source code.

        Args:
            content: Source code content (HTML, JSX, TSX, JS, TS)
            file_path: Path to source file

        Returns:
            Dict with 'components' and 'custom_components' keys
        """
        components: List[BootstrapComponentInfo] = []
        custom_components: List[BootstrapCustomComponentInfo] = []

        if not content or not content.strip():
            return {
                'components': components,
                'custom_components': custom_components,
            }

        is_react = file_path.endswith(('.jsx', '.tsx')) or bool(
            re.search(r"from\s+['\"]react-bootstrap['/\"]|from\s+['\"]reactstrap['/\"]", content)
        )

        if is_react:
            self._extract_react_components(content, file_path, components)
            self._extract_custom_react_components(
                content, file_path, custom_components
            )
        else:
            self._extract_html_components(content, file_path, components)

        # Also check for JS-initialized components
        self._extract_js_init_components(content, file_path, components)

        return {
            'components': components,
            'custom_components': custom_components,
        }

    def _extract_react_components(
        self, content: str, file_path: str,
        components: List[BootstrapComponentInfo]
    ):
        """Extract React-Bootstrap / reactstrap component usage."""
        # Detect imports
        import_pattern = re.compile(
            r"import\s*\{([^}]+)\}\s*from\s*['\"]"
            r"(react-bootstrap(?:/\w+)?|reactstrap)['\"]",
            re.MULTILINE
        )
        imported_components = set()
        import_source = ""
        for m in import_pattern.finditer(content):
            names = [n.strip().split(' as ')[0].strip() for n in m.group(1).split(',')]
            import_source = m.group(2)
            imported_components.update(names)

        # Extract JSX usage for known components
        for comp_name in imported_components:
            if comp_name not in self.REACT_COMPONENT_CATEGORIES:
                continue

            # Find JSX usage: <ComponentName ...>
            usage_pattern = re.compile(
                rf'<{re.escape(comp_name)}\b([^>]*?)(?:/>|>)',
                re.DOTALL
            )
            for um in usage_pattern.finditer(content):
                props_str = um.group(1)
                props = re.findall(r'(\w+)(?:=)', props_str)

                # Detect sub-components
                sub_comps = []
                for parent, subs in self.SUB_COMPONENT_PATTERNS.items():
                    if comp_name == parent:
                        for sub in subs:
                            full_name = f"{parent}.{sub}"
                            if full_name in content or f"{parent}{sub}" in content:
                                sub_comps.append(sub)

                # Check for responsive props
                has_responsive = bool(re.search(
                    r'\b(xs|sm|md|lg|xl|xxl)\s*=', props_str
                ))

                # Extract className for Bootstrap classes
                classes = []
                cls_m = re.search(r'className\s*=\s*["\'{]([^"\'}\)]+)', props_str)
                if cls_m:
                    classes = cls_m.group(1).split()

                line_num = content[:um.start()].count('\n') + 1

                components.append(BootstrapComponentInfo(
                    name=comp_name,
                    file=file_path,
                    line_number=line_num,
                    import_source=import_source,
                    category=self.REACT_COMPONENT_CATEGORIES.get(
                        comp_name, ""
                    ),
                    props_used=props[:15],
                    classes_used=classes[:10],
                    has_responsive=has_responsive,
                    has_js_init=False,
                    sub_components=sub_comps[:10],
                ))

    def _extract_html_components(
        self, content: str, file_path: str,
        components: List[BootstrapComponentInfo]
    ):
        """Extract Bootstrap components from HTML class usage."""
        seen = set()

        # Find elements with Bootstrap classes
        tag_pattern = re.compile(
            r'<(\w+)\b([^>]*class\s*=\s*["\'][^"\']*["\'][^>]*)>',
            re.DOTALL | re.IGNORECASE
        )

        for m in tag_pattern.finditer(content):
            tag = m.group(1)
            attrs = m.group(2)

            # Extract class names
            cls_match = re.search(r'class\s*=\s*["\']([^"\']+)["\']', attrs)
            if not cls_match:
                continue

            classes = cls_match.group(1).split()
            line_num = content[:m.start()].count('\n') + 1

            for cls in classes:
                base_cls = cls.split('-')[0] if '-' in cls else cls
                # Check col-* pattern
                if re.match(r'col(-\w+)?$', cls):
                    base_cls = 'col'

                if base_cls in self.COMPONENT_CATEGORIES:
                    key = (base_cls, line_num)
                    if key in seen:
                        continue
                    seen.add(key)

                    has_responsive = bool(re.match(
                        r'(col|d|m|p|text|float|order|offset|g)-'
                        r'(sm|md|lg|xl|xxl)',
                        cls
                    ))

                    # Check for data-bs-* attributes
                    has_js = bool(re.search(
                        r'data-bs-\w+', attrs
                    ))

                    components.append(BootstrapComponentInfo(
                        name=base_cls,
                        file=file_path,
                        line_number=line_num,
                        category=self.COMPONENT_CATEGORIES.get(
                            base_cls, ""
                        ),
                        classes_used=[c for c in classes
                                      if c.startswith(base_cls)][:10],
                        has_responsive=has_responsive,
                        has_js_init=has_js,
                    ))

    def _extract_js_init_components(
        self, content: str, file_path: str,
        components: List[BootstrapComponentInfo]
    ):
        """Extract Bootstrap components initialized via JavaScript."""
        # v5: new bootstrap.Modal(element), bootstrap.Toast.getInstance()
        js_init_pattern = re.compile(
            r'new\s+bootstrap\.(Modal|Tooltip|Popover|Toast|Carousel|'
            r'Collapse|Dropdown|Offcanvas|Tab|ScrollSpy|Alert|Button)\b',
            re.MULTILINE
        )
        for m in js_init_pattern.finditer(content):
            comp_name = m.group(1).lower()
            line_num = content[:m.start()].count('\n') + 1
            components.append(BootstrapComponentInfo(
                name=comp_name,
                file=file_path,
                line_number=line_num,
                category=self.COMPONENT_CATEGORIES.get(comp_name, ""),
                has_js_init=True,
            ))

        # jQuery-style: $(selector).modal('show'), .tooltip(), etc.
        jquery_pattern = re.compile(
            r'\$\([^)]+\)\.(modal|tooltip|popover|toast|carousel|'
            r'collapse|dropdown|offcanvas|tab|scrollspy|alert|button)'
            r'\s*\(',
            re.MULTILINE
        )
        for m in jquery_pattern.finditer(content):
            comp_name = m.group(1)
            line_num = content[:m.start()].count('\n') + 1
            components.append(BootstrapComponentInfo(
                name=comp_name,
                file=file_path,
                line_number=line_num,
                category=self.COMPONENT_CATEGORIES.get(comp_name, ""),
                has_js_init=True,
            ))

    def _extract_custom_react_components(
        self, content: str, file_path: str,
        custom_components: List[BootstrapCustomComponentInfo]
    ):
        """Extract custom React components wrapping Bootstrap."""
        # Pattern: function/const ComponentName = ... wrapping Bootstrap components
        wrapper_pattern = re.compile(
            r'(?:export\s+)?(?:function|const)\s+(\w+)\s*'
            r'(?:=\s*(?:React\.)?(?:forwardRef\s*\()?|(?:\([^)]*\)\s*(?::\s*\w+)?\s*(?:=>|{)))',
            re.MULTILINE
        )
        for m in wrapper_pattern.finditer(content):
            comp_name = m.group(1)
            # Must start with uppercase (React component)
            if not comp_name[0].isupper():
                continue

            # Check if it uses Bootstrap components in its body
            # Look ahead for react-bootstrap imports in the component
            body_start = m.end()
            body_end = min(body_start + 2000, len(content))
            body = content[body_start:body_end]

            bootstrap_used = False
            base_comp = ""
            for bc in self.REACT_COMPONENT_CATEGORIES:
                if f'<{bc}' in body or f'{bc}.' in body:
                    bootstrap_used = True
                    base_comp = bc
                    break

            if bootstrap_used:
                line_num = content[:m.start()].count('\n') + 1
                method = "forwardRef" if "forwardRef" in m.group(0) else "wrapper"
                custom_components.append(BootstrapCustomComponentInfo(
                    name=comp_name,
                    file=file_path,
                    line_number=line_num,
                    base_component=base_comp,
                    method=method,
                ))
