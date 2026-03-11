"""
Enhanced WordPress Framework Parser for CodeTrellis.

v5.3: Full WordPress Plugin/Theme development support.
Extracts hooks (actions/filters), custom post types, taxonomies,
shortcodes, REST API endpoints, Gutenberg blocks, widgets,
admin pages, settings, enqueued scripts/styles, cron events,
transients, meta boxes, custom tables, AJAX handlers.

Runs AFTER the base PHP parser when WordPress is detected.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


# ===== DATACLASSES =====

@dataclass
class WordPressHookInfo:
    """Information about a WordPress hook (action or filter)."""
    name: str
    kind: str = ""  # action, filter
    callback: str = ""
    priority: int = 10
    accepted_args: int = 1
    file: str = ""
    line_number: int = 0


@dataclass
class WordPressCustomPostTypeInfo:
    """Information about a custom post type."""
    name: str
    label: str = ""
    public: bool = True
    has_archive: bool = False
    supports: List[str] = field(default_factory=list)
    taxonomies: List[str] = field(default_factory=list)
    menu_icon: str = ""
    hierarchical: bool = False
    show_in_rest: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class WordPressTaxonomyInfo:
    """Information about a custom taxonomy."""
    name: str
    label: str = ""
    post_types: List[str] = field(default_factory=list)
    hierarchical: bool = False
    public: bool = True
    show_in_rest: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class WordPressShortcodeInfo:
    """Information about a shortcode."""
    tag: str
    callback: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class WordPressRESTRouteInfo:
    """Information about a REST API route."""
    namespace: str = ""
    route: str = ""
    method: str = ""
    callback: str = ""
    permission_callback: str = ""
    args: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class WordPressBlockInfo:
    """Information about a Gutenberg block."""
    name: str
    title: str = ""
    category: str = ""
    attributes: List[str] = field(default_factory=list)
    render_callback: str = ""
    editor_script: str = ""
    is_dynamic: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class WordPressWidgetInfo:
    """Information about a widget."""
    name: str
    class_name: str = ""
    description: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class WordPressAdminPageInfo:
    """Information about an admin menu page."""
    title: str
    slug: str = ""
    capability: str = ""
    callback: str = ""
    parent_slug: str = ""
    icon: str = ""
    position: int = 0
    file: str = ""
    line_number: int = 0


@dataclass
class WordPressEnqueueInfo:
    """Information about an enqueued script or style."""
    handle: str
    kind: str = ""  # script, style
    src: str = ""
    deps: List[str] = field(default_factory=list)
    version: str = ""
    in_footer: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class WordPressCronInfo:
    """Information about a cron event."""
    hook: str
    recurrence: str = ""  # hourly, daily, twicedaily
    callback: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class WordPressAjaxInfo:
    """Information about a WordPress AJAX handler."""
    action: str
    callback: str = ""
    is_nopriv: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class WordPressMetaBoxInfo:
    """Information about a meta box."""
    id: str
    title: str = ""
    callback: str = ""
    screen: str = ""
    context: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class WordPressSettingInfo:
    """Information about a WordPress setting."""
    option_name: str
    group: str = ""
    section: str = ""
    kind: str = ""  # option, setting_field, setting_section
    file: str = ""
    line_number: int = 0


@dataclass
class WordPressParseResult:
    """Complete parse result for a WordPress file."""
    file_path: str
    file_type: str = "php"

    # Hooks
    hooks: List[WordPressHookInfo] = field(default_factory=list)

    # Custom Post Types
    post_types: List[WordPressCustomPostTypeInfo] = field(default_factory=list)

    # Taxonomies
    taxonomies: List[WordPressTaxonomyInfo] = field(default_factory=list)

    # Shortcodes
    shortcodes: List[WordPressShortcodeInfo] = field(default_factory=list)

    # REST API
    rest_routes: List[WordPressRESTRouteInfo] = field(default_factory=list)

    # Gutenberg Blocks
    blocks: List[WordPressBlockInfo] = field(default_factory=list)

    # Widgets
    widgets: List[WordPressWidgetInfo] = field(default_factory=list)

    # Admin Pages
    admin_pages: List[WordPressAdminPageInfo] = field(default_factory=list)

    # Enqueued Assets
    enqueues: List[WordPressEnqueueInfo] = field(default_factory=list)

    # Cron Events
    cron_events: List[WordPressCronInfo] = field(default_factory=list)

    # AJAX Handlers
    ajax_handlers: List[WordPressAjaxInfo] = field(default_factory=list)

    # Meta Boxes
    meta_boxes: List[WordPressMetaBoxInfo] = field(default_factory=list)

    # Settings
    settings: List[WordPressSettingInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    wordpress_version: str = ""
    is_plugin: bool = False
    is_theme: bool = False
    is_mu_plugin: bool = False
    has_gutenberg: bool = False
    has_woocommerce: bool = False
    has_acf: bool = False
    has_elementor: bool = False


# ===== PARSER =====

class EnhancedWordPressParser:
    """
    Enhanced parser for WordPress Plugin/Theme development.
    Extracts hooks, post types, taxonomies, shortcodes, REST API,
    blocks, widgets, admin pages, enqueues, cron, AJAX, meta boxes, settings.
    """

    # Detection pattern
    WP_DETECT = re.compile(
        r"(?:wp_|WP_|add_action|add_filter|get_option|update_option|"
        r"wp_enqueue_script|wp_enqueue_style|register_post_type|"
        r"register_taxonomy|add_shortcode|register_rest_route|"
        r"register_block_type|add_menu_page|add_submenu_page|"
        r"wp_schedule_event|wp_ajax_|is_admin\(\)|"
        r"Plugin\s+Name:|Theme\s+Name:)",
        re.MULTILINE,
    )

    # Framework ecosystem patterns
    FRAMEWORK_PATTERNS = {
        'wordpress': re.compile(r'(?:wp_|WP_|add_action|add_filter)'),
        'woocommerce': re.compile(r'(?:WooCommerce|wc_|WC\(\)|woocommerce_)'),
        'acf': re.compile(r'(?:acf_|get_field|the_field|ACF)'),
        'elementor': re.compile(r'(?:Elementor\\|elementor)'),
        'wpml': re.compile(r'(?:ICL_LANGUAGE_CODE|wpml_)'),
        'yoast': re.compile(r'(?:Yoast\\|wpseo_)'),
        'buddypress': re.compile(r'(?:BuddyPress|buddypress|bp_)'),
        'bbpress': re.compile(r'(?:bbPress|bbpress|bbp_)'),
        'gravity_forms': re.compile(r'(?:GFFormsModel|gform_|GFAPI)'),
        'jetpack': re.compile(r'(?:Jetpack|jetpack_)'),
        'wp_cli': re.compile(r'(?:WP_CLI|WP_CLI::)'),
    }

    # Hook patterns
    ADD_ACTION = re.compile(
        r"add_action\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*"
        r"(?:\[([^\]]*)\]|['\"]([^'\"]+)['\"]|(\$\w+)|(\w+))"
        r"(?:\s*,\s*(\d+))?"
        r"(?:\s*,\s*(\d+))?",
        re.MULTILINE,
    )
    ADD_FILTER = re.compile(
        r"add_filter\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*"
        r"(?:\[([^\]]*)\]|['\"]([^'\"]+)['\"]|(\$\w+)|(\w+))"
        r"(?:\s*,\s*(\d+))?"
        r"(?:\s*,\s*(\d+))?",
        re.MULTILINE,
    )

    # Custom post type
    REGISTER_CPT = re.compile(
        r"register_post_type\s*\(\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )
    CPT_LABEL = re.compile(
        r"['\"]label['\"]\s*=>\s*['\"]([^'\"]+)['\"]",
    )
    CPT_SUPPORTS = re.compile(
        r"['\"]supports['\"]\s*=>\s*\[([^\]]*)\]",
    )
    CPT_SHOW_IN_REST = re.compile(
        r"['\"]show_in_rest['\"]\s*=>\s*(true|false)",
    )
    CPT_HAS_ARCHIVE = re.compile(
        r"['\"]has_archive['\"]\s*=>\s*(true|false)",
    )

    # Taxonomy
    REGISTER_TAXONOMY = re.compile(
        r"register_taxonomy\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*"
        r"(?:\[([^\]]*)\]|['\"]([^'\"]+)['\"])",
        re.MULTILINE,
    )

    # Shortcode
    ADD_SHORTCODE = re.compile(
        r"add_shortcode\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*"
        r"(?:\[([^\]]*)\]|['\"]([^'\"]+)['\"]|(\w+))",
        re.MULTILINE,
    )

    # REST API
    REGISTER_REST_ROUTE = re.compile(
        r"register_rest_route\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*"
        r"['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )
    REST_METHOD = re.compile(
        r"['\"]methods['\"]\s*=>\s*(?:WP_REST_Server::(\w+)|['\"](\w+)['\"])",
    )
    REST_CALLBACK = re.compile(
        r"['\"]callback['\"]\s*=>\s*(?:\[([^\]]*)\]|['\"]([^'\"]+)['\"]|(\w+))",
    )
    REST_PERMISSION = re.compile(
        r"['\"]permission_callback['\"]\s*=>\s*(?:\[([^\]]*)\]|['\"]([^'\"]+)['\"]|(\w+))",
    )

    # Gutenberg blocks
    REGISTER_BLOCK = re.compile(
        r"register_block_type\s*\(\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )
    REGISTER_BLOCK_PATTERN = re.compile(
        r"register_block_pattern\s*\(\s*['\"]([^'\"]+)['\"]",
    )

    # Widget
    WIDGET_CLASS = re.compile(
        r"class\s+(\w+)\s+extends\s+WP_Widget",
        re.MULTILINE,
    )

    # Admin pages
    ADD_MENU_PAGE = re.compile(
        r"add_menu_page\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*"
        r"['\"]([^'\"]+)['\"]\s*,\s*"
        r"['\"]([^'\"]+)['\"]\s*,\s*"
        r"['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )
    ADD_SUBMENU_PAGE = re.compile(
        r"add_submenu_page\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*"
        r"['\"]([^'\"]+)['\"]\s*,\s*"
        r"['\"]([^'\"]+)['\"]\s*,\s*"
        r"['\"]([^'\"]+)['\"]\s*,\s*"
        r"['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # Enqueue
    WP_ENQUEUE_SCRIPT = re.compile(
        r"wp_enqueue_script\s*\(\s*['\"]([^'\"]+)['\"]"
        r"(?:\s*,\s*['\"]([^'\"]*)['\"])?",
        re.MULTILINE,
    )
    WP_ENQUEUE_STYLE = re.compile(
        r"wp_enqueue_style\s*\(\s*['\"]([^'\"]+)['\"]"
        r"(?:\s*,\s*['\"]([^'\"]*)['\"])?",
        re.MULTILINE,
    )
    WP_REGISTER_SCRIPT = re.compile(
        r"wp_register_script\s*\(\s*['\"]([^'\"]+)['\"]",
    )
    WP_REGISTER_STYLE = re.compile(
        r"wp_register_style\s*\(\s*['\"]([^'\"]+)['\"]",
    )

    # Cron
    WP_SCHEDULE_EVENT = re.compile(
        r"wp_schedule_event\s*\(\s*[^,]+,\s*['\"](\w+)['\"]\s*,\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )
    WP_SCHEDULE_SINGLE = re.compile(
        r"wp_schedule_single_event\s*\(\s*[^,]+,\s*['\"]([^'\"]+)['\"]",
    )

    # AJAX
    AJAX_ACTION = re.compile(
        r"add_action\s*\(\s*['\"]wp_ajax_(nopriv_)?([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # Meta boxes
    ADD_META_BOX = re.compile(
        r"add_meta_box\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*"
        r"['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # Settings
    REGISTER_SETTING = re.compile(
        r"register_setting\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )
    ADD_SETTINGS_SECTION = re.compile(
        r"add_settings_section\s*\(\s*['\"]([^'\"]+)['\"]",
    )
    ADD_SETTINGS_FIELD = re.compile(
        r"add_settings_field\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]",
    )

    # Plugin/Theme header detection
    PLUGIN_HEADER = re.compile(r"Plugin\s+Name:\s*(.+)", re.MULTILINE)
    THEME_HEADER = re.compile(r"Theme\s+Name:\s*(.+)", re.MULTILINE)

    # Version detection
    VERSION_PATTERNS = [
        (r'register_block_type|wp_set_script_translations', '5.x+'),
        (r'register_rest_route|WP_REST_', '4.7+'),
        (r'WP_Customize_', '4.x+'),
    ]

    def parse(self, content: str, file_path: str = "") -> WordPressParseResult:
        """Parse PHP source code for WordPress-specific patterns."""
        result = WordPressParseResult(file_path=file_path)

        if not content.strip():
            return result

        # Check if this file uses WordPress
        if not self.WP_DETECT.search(content):
            return result

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect version
        result.wordpress_version = self._detect_version(content)

        # Plugin/Theme detection
        result.is_plugin = bool(self.PLUGIN_HEADER.search(content))
        result.is_theme = bool(self.THEME_HEADER.search(content))
        result.is_mu_plugin = '/mu-plugins/' in file_path

        # Ecosystem detection
        result.has_gutenberg = bool(re.search(r'register_block_type|wp\.blocks', content))
        result.has_woocommerce = bool(self.FRAMEWORK_PATTERNS['woocommerce'].search(content))
        result.has_acf = bool(self.FRAMEWORK_PATTERNS['acf'].search(content))
        result.has_elementor = bool(self.FRAMEWORK_PATTERNS['elementor'].search(content))

        # Extract all entities
        self._extract_hooks(content, file_path, result)
        self._extract_post_types(content, file_path, result)
        self._extract_taxonomies(content, file_path, result)
        self._extract_shortcodes(content, file_path, result)
        self._extract_rest_routes(content, file_path, result)
        self._extract_blocks(content, file_path, result)
        self._extract_widgets(content, file_path, result)
        self._extract_admin_pages(content, file_path, result)
        self._extract_enqueues(content, file_path, result)
        self._extract_cron_events(content, file_path, result)
        self._extract_ajax_handlers(content, file_path, result)
        self._extract_meta_boxes(content, file_path, result)
        self._extract_settings(content, file_path, result)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect WordPress ecosystem frameworks used."""
        detected = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                detected.append(name)
        return detected

    def _detect_version(self, content: str) -> str:
        """Detect minimum WordPress version from code features."""
        for pattern, version in self.VERSION_PATTERNS:
            if re.search(pattern, content):
                return version
        return ""

    def _get_line(self, content: str, pos: int) -> int:
        """Get 1-based line number for a position."""
        return content[:pos].count('\n') + 1

    def _extract_callback(self, group1, group2, group3, group4=None):
        """Extract callback name from match groups."""
        if group1:  # Array callback [$this, 'method'] or [ClassName::class, 'method']
            parts = [s.strip().strip("'\"$") for s in group1.split(',')]
            return '::'.join(parts) if len(parts) > 1 else parts[0]
        return group2 or group3 or group4 or ""

    def _extract_hooks(self, content: str, file_path: str, result: WordPressParseResult):
        """Extract WordPress action and filter hooks."""
        # Actions
        for m in self.ADD_ACTION.finditer(content):
            # Skip AJAX actions - handled separately
            if m.group(1).startswith('wp_ajax_'):
                continue
            hook_name = m.group(1)
            callback = self._extract_callback(m.group(2), m.group(3), m.group(5), m.group(4))
            priority = int(m.group(6)) if m.group(6) else 10
            accepted_args = int(m.group(7)) if m.group(7) else 1
            line = self._get_line(content, m.start())
            hook = WordPressHookInfo(
                name=hook_name,
                kind="action",
                callback=callback,
                priority=priority,
                accepted_args=accepted_args,
                file=file_path,
                line_number=line,
            )
            result.hooks.append(hook)

        # Filters
        for m in self.ADD_FILTER.finditer(content):
            hook_name = m.group(1)
            callback = self._extract_callback(m.group(2), m.group(3), m.group(5), m.group(4))
            priority = int(m.group(6)) if m.group(6) else 10
            accepted_args = int(m.group(7)) if m.group(7) else 1
            line = self._get_line(content, m.start())
            hook = WordPressHookInfo(
                name=hook_name,
                kind="filter",
                callback=callback,
                priority=priority,
                accepted_args=accepted_args,
                file=file_path,
                line_number=line,
            )
            result.hooks.append(hook)

    def _extract_post_types(self, content: str, file_path: str, result: WordPressParseResult):
        """Extract custom post type registrations."""
        for m in self.REGISTER_CPT.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())

            # Look for args in nearby context
            ctx = content[m.start():m.start() + 2000]

            label = ""
            label_m = self.CPT_LABEL.search(ctx)
            if label_m:
                label = label_m.group(1)

            supports = []
            sup_m = self.CPT_SUPPORTS.search(ctx)
            if sup_m:
                supports = [s.strip().strip("'\"") for s in sup_m.group(1).split(',') if s.strip().strip("'\"")]

            show_in_rest = False
            rest_m = self.CPT_SHOW_IN_REST.search(ctx)
            if rest_m:
                show_in_rest = rest_m.group(1) == 'true'

            has_archive = False
            archive_m = self.CPT_HAS_ARCHIVE.search(ctx)
            if archive_m:
                has_archive = archive_m.group(1) == 'true'

            cpt = WordPressCustomPostTypeInfo(
                name=name,
                label=label,
                supports=supports[:10],
                show_in_rest=show_in_rest,
                has_archive=has_archive,
                file=file_path,
                line_number=line,
            )
            result.post_types.append(cpt)

    def _extract_taxonomies(self, content: str, file_path: str, result: WordPressParseResult):
        """Extract custom taxonomy registrations."""
        for m in self.REGISTER_TAXONOMY.finditer(content):
            name = m.group(1)
            post_types_str = m.group(2) or m.group(3) or ""
            line = self._get_line(content, m.start())

            post_types = []
            if m.group(2):
                post_types = [s.strip().strip("'\"") for s in post_types_str.split(',') if s.strip().strip("'\"")]
            elif post_types_str:
                post_types = [post_types_str]

            ctx = content[m.start():m.start() + 1500]
            hierarchical = bool(re.search(r"['\"]hierarchical['\"]\s*=>\s*true", ctx))
            show_in_rest = bool(re.search(r"['\"]show_in_rest['\"]\s*=>\s*true", ctx))

            tax = WordPressTaxonomyInfo(
                name=name,
                post_types=post_types[:5],
                hierarchical=hierarchical,
                show_in_rest=show_in_rest,
                file=file_path,
                line_number=line,
            )
            result.taxonomies.append(tax)

    def _extract_shortcodes(self, content: str, file_path: str, result: WordPressParseResult):
        """Extract shortcode registrations."""
        for m in self.ADD_SHORTCODE.finditer(content):
            tag = m.group(1)
            callback = self._extract_callback(m.group(2), m.group(3), m.group(4))
            line = self._get_line(content, m.start())
            sc = WordPressShortcodeInfo(
                tag=tag,
                callback=callback,
                file=file_path,
                line_number=line,
            )
            result.shortcodes.append(sc)

    def _extract_rest_routes(self, content: str, file_path: str, result: WordPressParseResult):
        """Extract REST API route registrations."""
        for m in self.REGISTER_REST_ROUTE.finditer(content):
            namespace = m.group(1)
            route = m.group(2)
            line = self._get_line(content, m.start())

            ctx = content[m.start():m.start() + 1500]

            method = ""
            method_m = self.REST_METHOD.search(ctx)
            if method_m:
                method = (method_m.group(1) or method_m.group(2) or "").upper()
                if method == 'READABLE':
                    method = 'GET'
                elif method == 'CREATABLE':
                    method = 'POST'
                elif method == 'EDITABLE':
                    method = 'PUT'
                elif method == 'DELETABLE':
                    method = 'DELETE'

            callback = ""
            cb_m = self.REST_CALLBACK.search(ctx)
            if cb_m:
                callback = self._extract_callback(cb_m.group(1), cb_m.group(2), cb_m.group(3))

            permission = ""
            perm_m = self.REST_PERMISSION.search(ctx)
            if perm_m:
                permission = self._extract_callback(perm_m.group(1), perm_m.group(2), perm_m.group(3))

            rest = WordPressRESTRouteInfo(
                namespace=namespace,
                route=route,
                method=method or "GET",
                callback=callback,
                permission_callback=permission,
                file=file_path,
                line_number=line,
            )
            result.rest_routes.append(rest)

    def _extract_blocks(self, content: str, file_path: str, result: WordPressParseResult):
        """Extract Gutenberg block registrations."""
        for m in self.REGISTER_BLOCK.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())

            ctx = content[m.start():m.start() + 2000]
            render_cb = ""
            render_m = re.search(r"['\"]render_callback['\"]\s*=>\s*(?:\[([^\]]*)\]|['\"]([^'\"]+)['\"]|(\w+))", ctx)
            if render_m:
                render_cb = self._extract_callback(render_m.group(1), render_m.group(2), render_m.group(3))

            is_dynamic = bool(render_cb)

            block = WordPressBlockInfo(
                name=name,
                render_callback=render_cb,
                is_dynamic=is_dynamic,
                file=file_path,
                line_number=line,
            )
            result.blocks.append(block)

    def _extract_widgets(self, content: str, file_path: str, result: WordPressParseResult):
        """Extract widget class definitions."""
        for m in self.WIDGET_CLASS.finditer(content):
            name = m.group(1)
            line = self._get_line(content, m.start())
            widget = WordPressWidgetInfo(
                name=name,
                class_name=name,
                file=file_path,
                line_number=line,
            )
            result.widgets.append(widget)

    def _extract_admin_pages(self, content: str, file_path: str, result: WordPressParseResult):
        """Extract admin menu page registrations."""
        # Top-level pages
        for m in self.ADD_MENU_PAGE.finditer(content):
            page = WordPressAdminPageInfo(
                title=m.group(1),
                slug=m.group(4),
                capability=m.group(3),
                file=file_path,
                line_number=self._get_line(content, m.start()),
            )
            result.admin_pages.append(page)

        # Subpages
        for m in self.ADD_SUBMENU_PAGE.finditer(content):
            page = WordPressAdminPageInfo(
                title=m.group(2),
                slug=m.group(5),
                capability=m.group(4),
                parent_slug=m.group(1),
                file=file_path,
                line_number=self._get_line(content, m.start()),
            )
            result.admin_pages.append(page)

    def _extract_enqueues(self, content: str, file_path: str, result: WordPressParseResult):
        """Extract enqueued scripts and styles."""
        for m in self.WP_ENQUEUE_SCRIPT.finditer(content):
            handle = m.group(1)
            src = m.group(2) or ""
            line = self._get_line(content, m.start())
            enq = WordPressEnqueueInfo(
                handle=handle,
                kind="script",
                src=src,
                file=file_path,
                line_number=line,
            )
            result.enqueues.append(enq)

        for m in self.WP_ENQUEUE_STYLE.finditer(content):
            handle = m.group(1)
            src = m.group(2) or ""
            line = self._get_line(content, m.start())
            enq = WordPressEnqueueInfo(
                handle=handle,
                kind="style",
                src=src,
                file=file_path,
                line_number=line,
            )
            result.enqueues.append(enq)

    def _extract_cron_events(self, content: str, file_path: str, result: WordPressParseResult):
        """Extract WP-Cron event schedules."""
        for m in self.WP_SCHEDULE_EVENT.finditer(content):
            recurrence = m.group(1)
            hook = m.group(2)
            line = self._get_line(content, m.start())
            cron = WordPressCronInfo(
                hook=hook,
                recurrence=recurrence,
                file=file_path,
                line_number=line,
            )
            result.cron_events.append(cron)

        for m in self.WP_SCHEDULE_SINGLE.finditer(content):
            hook = m.group(1)
            line = self._get_line(content, m.start())
            cron = WordPressCronInfo(
                hook=hook,
                recurrence="once",
                file=file_path,
                line_number=line,
            )
            result.cron_events.append(cron)

    def _extract_ajax_handlers(self, content: str, file_path: str, result: WordPressParseResult):
        """Extract AJAX handler registrations."""
        for m in self.AJAX_ACTION.finditer(content):
            is_nopriv = bool(m.group(1))
            action = m.group(2)
            line = self._get_line(content, m.start())

            # Try to find the callback from the full add_action line
            full_line = content[m.start():m.start() + 300]
            callback = ""
            cb_m = re.search(r",\s*(?:\[([^\]]*)\]|['\"]([^'\"]+)['\"]|(\w+))", full_line)
            if cb_m:
                callback = self._extract_callback(cb_m.group(1), cb_m.group(2), cb_m.group(3))

            ajax = WordPressAjaxInfo(
                action=action,
                callback=callback,
                is_nopriv=is_nopriv,
                file=file_path,
                line_number=line,
            )
            result.ajax_handlers.append(ajax)

    def _extract_meta_boxes(self, content: str, file_path: str, result: WordPressParseResult):
        """Extract meta box registrations."""
        for m in self.ADD_META_BOX.finditer(content):
            box_id = m.group(1)
            title = m.group(2)
            line = self._get_line(content, m.start())
            mb = WordPressMetaBoxInfo(
                id=box_id,
                title=title,
                file=file_path,
                line_number=line,
            )
            result.meta_boxes.append(mb)

    def _extract_settings(self, content: str, file_path: str, result: WordPressParseResult):
        """Extract WordPress settings registrations."""
        for m in self.REGISTER_SETTING.finditer(content):
            group = m.group(1)
            option = m.group(2)
            line = self._get_line(content, m.start())
            setting = WordPressSettingInfo(
                option_name=option,
                group=group,
                kind="option",
                file=file_path,
                line_number=line,
            )
            result.settings.append(setting)

        for m in self.ADD_SETTINGS_FIELD.finditer(content):
            field_id = m.group(1)
            title = m.group(2)
            line = self._get_line(content, m.start())
            setting = WordPressSettingInfo(
                option_name=field_id,
                kind="setting_field",
                file=file_path,
                line_number=line,
            )
            result.settings.append(setting)
