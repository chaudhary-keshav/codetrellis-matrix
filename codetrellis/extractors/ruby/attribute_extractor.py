"""
RubyAttributeExtractor - Extracts Ruby gems, DSL macros, metaprogramming, and callbacks.

This extractor parses Ruby source code and extracts:
- Gemfile dependencies (gem declarations, groups, platforms)
- DSL macros (class_attribute, mattr_accessor, cattr_accessor)
- ActiveSupport::Concern patterns (included, class_methods blocks)
- Callbacks (before_*, after_*, around_*)
- Metaprogramming patterns (method_missing, respond_to_missing?, class_eval, define_method)
- Mixins and module inclusions
- Configuration DSL (config/settings patterns)
- Rake tasks
- Sidekiq/Delayed::Job workers
- RSpec/Minitest test patterns

Supports Ruby 1.8 through Ruby 3.3+ and common gems ecosystem.

Part of CodeTrellis v4.23 - Ruby Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RubyGemInfo:
    """Information about a Ruby gem dependency."""
    name: str
    version: Optional[str] = None
    group: Optional[str] = None  # development, test, production
    require: Optional[str] = None
    platforms: List[str] = field(default_factory=list)
    git: Optional[str] = None
    path: Optional[str] = None
    line_number: int = 0


@dataclass
class RubyCallbackInfo:
    """Information about a Ruby callback/hook."""
    kind: str  # before_save, after_create, etc.
    name: str  # method name or inline block
    conditions: Dict[str, Any] = field(default_factory=dict)  # if:, unless:, on:
    file: str = ""
    line_number: int = 0


@dataclass
class RubyConcernInfo:
    """Information about an ActiveSupport::Concern."""
    name: str
    included_methods: List[str] = field(default_factory=list)
    class_methods: List[str] = field(default_factory=list)
    callbacks: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class RubyDSLMacroInfo:
    """Information about a Ruby DSL macro usage."""
    kind: str  # class_attribute, mattr_accessor, delegate, etc.
    names: List[str] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)
    file: str = ""
    line_number: int = 0


@dataclass
class RubyMetaprogrammingInfo:
    """Information about Ruby metaprogramming usage."""
    kind: str  # method_missing, class_eval, define_method, etc.
    target: Optional[str] = None
    file: str = ""
    line_number: int = 0
    description: Optional[str] = None


class RubyAttributeExtractor:
    """
    Extracts Ruby attribute-like constructs from source code.

    Handles:
    - Gemfile parsing (gem, group, source, ruby version)
    - DSL macros (class_attribute, delegate, mattr_accessor)
    - ActiveSupport::Concern (included, class_methods)
    - Callbacks (before_*, after_*, around_*)
    - Metaprogramming (method_missing, class_eval, instance_eval, define_method)
    - Rake task definitions
    - Sidekiq/ActiveJob workers
    - Initializer configuration blocks
    - Autoload declarations
    """

    # Gem declaration in Gemfile
    GEM_PATTERN = re.compile(
        r'''^\s*gem\s+['\"](?P<name>[^'"]+)['\"](?:\s*,\s*['\"](?P<version>[^'"]+)['\"])?(?P<options>[^\n]*)''',
        re.MULTILINE
    )

    # Gemfile group
    GEM_GROUP_PATTERN = re.compile(
        r'^\s*group\s+(?P<groups>[^\s]+(?:\s*,\s*[^\s]+)*)\s+do',
        re.MULTILINE
    )

    # Gemfile ruby version
    RUBY_VERSION_PATTERN = re.compile(
        r'''^\s*ruby\s+['\"](?P<version>[^'"]+)['\"]''',
        re.MULTILINE
    )

    # Gemfile source
    GEM_SOURCE_PATTERN = re.compile(
        r'''^\s*source\s+['\"](?P<url>[^'"]+)['\"]''',
        re.MULTILINE
    )

    # DSL macros
    DSL_MACRO_PATTERN = re.compile(
        r'^\s*(?P<macro>class_attribute|mattr_accessor|mattr_reader|mattr_writer|cattr_accessor|cattr_reader|cattr_writer|delegate|delegate_missing_to|store|store_accessor|serialize|attribute)\s+(?P<args>[^\n]+)',
        re.MULTILINE
    )

    # ActiveSupport::Concern included block
    CONCERN_INCLUDED_PATTERN = re.compile(
        r'^\s*included\s+do',
        re.MULTILINE
    )

    # ActiveSupport::Concern class_methods block
    CONCERN_CLASS_METHODS_PATTERN = re.compile(
        r'^\s*class_methods\s+do',
        re.MULTILINE
    )

    # Metaprogramming patterns
    META_METHOD_MISSING = re.compile(
        r'^\s*def\s+method_missing\b',
        re.MULTILINE
    )

    META_RESPOND_TO = re.compile(
        r'^\s*def\s+respond_to_missing\?\b',
        re.MULTILINE
    )

    META_CLASS_EVAL = re.compile(
        r'(?P<target>\w+(?:::\w+)*)\.(?P<method>class_eval|instance_eval|module_eval|class_exec|instance_exec)',
        re.MULTILINE
    )

    META_DEFINE_METHOD = re.compile(
        r'^\s*define_method\s+[:\'"]\s*(?P<name>\w+)',
        re.MULTILINE
    )

    META_METHOD_DEFINED = re.compile(
        r'(?:define_method|module_function|extend|include)\s',
        re.MULTILINE
    )

    # Rake task
    RAKE_TASK_PATTERN = re.compile(
        r'^\s*(?:task|desc)\s+(?:[:\'"]\s*(?P<name>[^\'"]+))?',
        re.MULTILINE
    )

    # Sidekiq worker
    SIDEKIQ_PATTERN = re.compile(
        r'^\s*include\s+Sidekiq::(?:Worker|Job)',
        re.MULTILINE
    )

    # ActiveJob
    ACTIVEJOB_PATTERN = re.compile(
        r'^\s*class\s+(?P<name>\w+)\s*<\s*(?:ApplicationJob|ActiveJob::Base)',
        re.MULTILINE
    )

    # Configuration block: Rails.application.configure / config.x.setting
    CONFIG_BLOCK_PATTERN = re.compile(
        r'(?:Rails\.application\.configure|config\.(?P<setting>\w+(?:\.\w+)*))\s*(?:do|\{|=)',
        re.MULTILINE
    )

    # Autoload declaration
    AUTOLOAD_PATTERN = re.compile(
        r'^\s*autoload\s+:(?P<name>\w+)',
        re.MULTILINE
    )

    # Callback pattern (comprehensive)
    CALLBACK_PATTERN = re.compile(
        r'^\s*(?P<kind>before_action|after_action|around_action|before_save|after_save|before_create|after_create|before_update|after_update|before_destroy|after_destroy|before_validation|after_validation|after_commit|after_rollback|after_initialize|after_find|around_save|around_create|around_update|around_destroy|before_filter|after_filter|around_filter|before_perform|after_perform|around_perform|on_load)\s+(?::(?P<name>\w+)|(?P<block>do|\{))',
        re.MULTILINE
    )

    # Frozen string literal
    FROZEN_STRING_PATTERN = re.compile(
        r'^#\s*frozen_string_literal:\s*(?P<value>true|false)',
        re.MULTILINE
    )

    # Typed: strict/true/false (Sorbet)
    SORBET_TYPED_PATTERN = re.compile(
        r'^#\s*typed:\s*(?P<level>strict|true|false|ignore)',
        re.MULTILINE
    )

    def __init__(self):
        """Initialize the attribute extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all attribute-like constructs from Ruby source code.

        Args:
            content: Ruby source code content
            file_path: Path to source file

        Returns:
            Dict with 'gems', 'callbacks', 'concerns', 'dsl_macros',
            'metaprogramming', 'workers', 'rake_tasks', 'config'
        """
        gems = self._extract_gems(content, file_path)
        callbacks = self._extract_callbacks(content, file_path)
        concerns = self._extract_concerns(content, file_path)
        dsl_macros = self._extract_dsl_macros(content, file_path)
        metaprogramming = self._extract_metaprogramming(content, file_path)
        workers = self._extract_workers(content, file_path)
        rake_tasks = self._extract_rake_tasks(content, file_path)
        config = self._extract_config(content, file_path)

        return {
            'gems': gems,
            'callbacks': callbacks,
            'concerns': concerns,
            'dsl_macros': dsl_macros,
            'metaprogramming': metaprogramming,
            'workers': workers,
            'rake_tasks': rake_tasks,
            'config': config,
        }

    def _extract_gems(self, content: str, file_path: str) -> List[RubyGemInfo]:
        """Extract gem declarations from Gemfile."""
        gems = []

        # Track current group
        current_group = None
        group_stack = []

        lines = content.split('\n')
        for i, line in enumerate(lines):
            # Check for group block
            group_match = self.GEM_GROUP_PATTERN.match(line)
            if group_match:
                groups = group_match.group('groups')
                group_names = re.findall(r':(\w+)', groups)
                current_group = ', '.join(group_names) if group_names else groups.strip()
                group_stack.append(current_group)
                continue

            if line.strip() == 'end' and group_stack:
                group_stack.pop()
                current_group = group_stack[-1] if group_stack else None
                continue

            # Check for gem declaration
            gem_match = self.GEM_PATTERN.match(line)
            if gem_match:
                name = gem_match.group('name')
                version = gem_match.group('version')
                options_str = gem_match.group('options') or ""

                # Parse options
                require_val = None
                req_match = re.search(r'require:\s*(?:false|[\'"]([^\'"]*)[\'"])', options_str)
                if req_match:
                    require_val = req_match.group(1) or 'false'

                git = None
                git_match = re.search(r'git:\s*[\'"]([^\'"]+)[\'"]', options_str)
                if git_match:
                    git = git_match.group(1)

                path = None
                path_match = re.search(r'path:\s*[\'"]([^\'"]+)[\'"]', options_str)
                if path_match:
                    path = path_match.group(1)

                gems.append(RubyGemInfo(
                    name=name,
                    version=version,
                    group=current_group,
                    require=require_val,
                    git=git,
                    path=path,
                    line_number=i + 1,
                ))

        return gems

    def _extract_callbacks(self, content: str, file_path: str) -> List[RubyCallbackInfo]:
        """Extract callback/hook declarations."""
        callbacks = []

        for match in self.CALLBACK_PATTERN.finditer(content):
            kind = match.group('kind')
            name = match.group('name') or 'block'
            line = content[:match.start()].count('\n') + 1

            callbacks.append(RubyCallbackInfo(
                kind=kind,
                name=name,
                file=file_path,
                line_number=line,
            ))

        return callbacks

    def _extract_concerns(self, content: str, file_path: str) -> List[RubyConcernInfo]:
        """Extract ActiveSupport::Concern patterns."""
        concerns = []

        if 'ActiveSupport::Concern' not in content:
            return concerns

        # Find the module name
        mod_match = re.search(r'^\s*module\s+(\w+(?:::\w+)*)', content, re.MULTILINE)
        if not mod_match:
            return concerns

        name = mod_match.group(1)
        line = content[:mod_match.start()].count('\n') + 1

        # Extract methods in included block
        included_methods = []
        class_methods = []

        # Simple heuristic: methods defined at module level
        for m_match in re.finditer(r'^\s*def\s+(?:self\.)?(\w+[?!=]?)', content, re.MULTILINE):
            method_name = m_match.group(1)
            included_methods.append(method_name)

        concerns.append(RubyConcernInfo(
            name=name,
            included_methods=included_methods,
            class_methods=class_methods,
            file=file_path,
            line_number=line,
        ))

        return concerns

    def _extract_dsl_macros(self, content: str, file_path: str) -> List[RubyDSLMacroInfo]:
        """Extract DSL macro declarations."""
        macros = []

        for match in self.DSL_MACRO_PATTERN.finditer(content):
            macro = match.group('macro')
            args_str = match.group('args')
            names = re.findall(r':(\w+)', args_str)
            line = content[:match.start()].count('\n') + 1

            macros.append(RubyDSLMacroInfo(
                kind=macro,
                names=names,
                file=file_path,
                line_number=line,
            ))

        return macros

    def _extract_metaprogramming(self, content: str, file_path: str) -> List[RubyMetaprogrammingInfo]:
        """Extract metaprogramming patterns."""
        patterns = []

        if self.META_METHOD_MISSING.search(content):
            patterns.append(RubyMetaprogrammingInfo(
                kind='method_missing',
                file=file_path,
                description='Dynamic method dispatch via method_missing',
            ))

        if self.META_RESPOND_TO.search(content):
            patterns.append(RubyMetaprogrammingInfo(
                kind='respond_to_missing?',
                file=file_path,
                description='Dynamic method introspection',
            ))

        for match in self.META_CLASS_EVAL.finditer(content):
            patterns.append(RubyMetaprogrammingInfo(
                kind=match.group('method'),
                target=match.group('target'),
                file=file_path,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        return patterns

    def _extract_workers(self, content: str, file_path: str) -> List[Dict]:
        """Extract background job worker definitions."""
        workers = []

        # Sidekiq workers
        if self.SIDEKIQ_PATTERN.search(content):
            class_match = re.search(r'class\s+(\w+)', content)
            if class_match:
                workers.append({
                    'name': class_match.group(1),
                    'kind': 'sidekiq',
                    'file': file_path,
                })

        # ActiveJob
        for match in self.ACTIVEJOB_PATTERN.finditer(content):
            workers.append({
                'name': match.group('name'),
                'kind': 'activejob',
                'file': file_path,
            })

        return workers

    def _extract_rake_tasks(self, content: str, file_path: str) -> List[Dict]:
        """Extract Rake task definitions."""
        tasks = []
        current_desc = None

        for line in content.split('\n'):
            desc_match = re.match(r'^\s*desc\s+[\'"]([^\'"]+)[\'"]', line)
            if desc_match:
                current_desc = desc_match.group(1)
                continue

            task_match = re.match(r'^\s*task\s+[:\'"]\s*(?P<name>[^\'":\s]+)', line)
            if task_match:
                tasks.append({
                    'name': task_match.group('name'),
                    'description': current_desc,
                    'file': file_path,
                })
                current_desc = None

        return tasks

    def _extract_config(self, content: str, file_path: str) -> List[Dict]:
        """Extract configuration patterns."""
        configs = []

        for match in self.CONFIG_BLOCK_PATTERN.finditer(content):
            setting = match.group('setting') or 'application'
            configs.append({
                'setting': setting,
                'file': file_path,
                'line': content[:match.start()].count('\n') + 1,
            })

        return configs

    @staticmethod
    def parse_gemfile(content: str) -> Dict[str, Any]:
        """
        Parse Gemfile to extract dependency information.

        Args:
            content: Gemfile content

        Returns:
            Dict with 'ruby_version', 'source', 'gems', 'groups'
        """
        result: Dict[str, Any] = {
            'ruby_version': '',
            'source': '',
            'gems': [],
            'groups': {},
        }

        # Ruby version
        rv_match = re.search(r'''ruby\s+['\"]([^'"]+)['\"]''', content)
        if rv_match:
            result['ruby_version'] = rv_match.group(1)

        # Source
        src_match = re.search(r'''source\s+['\"]([^\'"]+)['\"]''', content)
        if src_match:
            result['source'] = src_match.group(1)

        # All gems
        current_group = None
        for line in content.split('\n'):
            group_match = re.match(r'^\s*group\s+(.+?)\s+do', line)
            if group_match:
                groups = re.findall(r':(\w+)', group_match.group(1))
                current_group = ','.join(groups)
                continue

            if line.strip() == 'end' and current_group:
                current_group = None
                continue

            gem_match = re.match(r'''^\s*gem\s+['\"]([^\'"]+)['\"](?:\s*,\s*['\"]([^\'"]+)['\"])?''', line)
            if gem_match:
                gem_info = {
                    'name': gem_match.group(1),
                    'version': gem_match.group(2) or '',
                }
                if current_group:
                    gem_info['group'] = current_group
                    if current_group not in result['groups']:
                        result['groups'][current_group] = []
                    result['groups'][current_group].append(gem_info)
                result['gems'].append(gem_info)

        return result
