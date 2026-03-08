"""
PhpAttributeExtractor - Extracts PHP attributes, annotations, DI bindings, and composer info.

This extractor parses PHP source code and extracts:
- PHP 8.0+ attributes (#[Attribute])
- Doctrine/Symfony annotations (@annotation)
- Composer.json dependency parsing
- Service container bindings (Laravel, Symfony)
- Event listeners and subscribers
- Custom annotations/attributes
- PHP configuration patterns
- Middleware registration
- Service provider bindings
- Observer registration
- Scheduled tasks
- Artisan commands
- PHPUnit test attributes

Supports PHP 5.x through PHP 8.3+ features.

Part of CodeTrellis v4.24 - PHP Language Support
"""

import re
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class PhpPackageInfo:
    """Information about a PHP composer package."""
    name: str
    version: str = ""
    is_dev: bool = False
    description: Optional[str] = None


@dataclass
class PhpAnnotationInfo:
    """Information about a PHP annotation (@Annotation)."""
    name: str
    target: Optional[str] = None  # Class/method this annotates
    arguments: Dict[str, str] = field(default_factory=dict)
    file: str = ""
    line_number: int = 0


@dataclass
class PhpAttributeInfo:
    """Information about a PHP 8.0+ attribute (#[Attribute])."""
    name: str
    target: Optional[str] = None
    arguments: List[str] = field(default_factory=list)
    is_repeated: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class PhpDIBindingInfo:
    """Information about a PHP dependency injection binding."""
    abstract: str  # Interface or abstract class
    concrete: str  # Concrete implementation
    kind: str = "bind"  # bind, singleton, scoped, instance
    framework: str = "laravel"
    file: str = ""
    line_number: int = 0


@dataclass
class PhpEventListenerInfo:
    """Information about a PHP event listener."""
    event: str
    listener: str
    kind: str = "listener"  # listener, subscriber, observer
    file: str = ""
    line_number: int = 0


class PhpAttributeExtractor:
    """
    Extracts PHP attributes, annotations, DI bindings, and composer dependencies.

    Handles:
    - PHP 8.0+ attributes (#[Route], #[Inject], #[Test], etc.)
    - Doctrine annotations (@ORM\\Column, @Assert\\NotBlank, etc.)
    - Symfony annotations (@Route, @Security, etc.)
    - PHPUnit attributes (#[Test], #[DataProvider], etc.)
    - Laravel service container bindings ($this->app->bind, singleton, etc.)
    - Symfony DI configuration
    - Event listeners and subscribers
    - Model observers
    - Scheduled tasks (Laravel Console Kernel)
    - Artisan commands
    - Composer.json parsing (dependencies, autoloading, scripts)

    v4.24: Comprehensive PHP attribute extraction.
    """

    # PHP 8.0+ attribute
    ATTRIBUTE_PATTERN = re.compile(
        r'#\[(?P<name>[A-Za-z_\\][A-Za-z0-9_\\]*)(?:\s*\((?P<args>[^)]*)\))?\]',
        re.MULTILINE
    )

    # Doctrine/Symfony annotation
    ANNOTATION_PATTERN = re.compile(
        r'@(?P<name>[A-Z][A-Za-z_\\]+)(?:\s*\((?P<args>[^)]*)\))?',
        re.MULTILINE
    )

    # Laravel DI binding: $this->app->bind(...), $this->app->singleton(...)
    LARAVEL_BIND_PATTERN = re.compile(
        r'''\$this\s*->\s*app\s*->\s*(?P<kind>bind|singleton|scoped|instance)\s*\(\s*'''
        r'''(?P<abstract>[A-Za-z_\\]+(?:::class)?|['"][^'"]+['"]),\s*'''
        r'''(?P<concrete>[A-Za-z_\\]+(?:::class)?|['"][^'"]+['"]|function)''',
        re.MULTILINE
    )

    # Symfony service definition
    SYMFONY_SERVICE_PATTERN = re.compile(
        r'''#\[(?:Autowire|AsDecorator|AsAlias|AsEventListener|AsController|'''
        r'''AsMessageHandler|AsCommand|AsCronTask)\s*(?:\((?P<args>[^)]*)\))?\]''',
        re.MULTILINE
    )

    # Event listener: Event::listen or $events->listen
    EVENT_LISTEN_PATTERN = re.compile(
        r'''(?:Event::listen|events?\s*->\s*listen)\s*\(\s*'''
        r'''(?P<event>[A-Za-z_\\]+(?:::class)?|['"][^'"]+['"]),\s*'''
        r'''(?P<listener>[A-Za-z_\\]+(?:::class)?|['"][^'"]+['"])''',
        re.MULTILINE
    )

    # Event subscriber class
    EVENT_SUBSCRIBER_PATTERN = re.compile(
        r'class\s+(?P<name>\w+)\s+implements\s+.*?(?:EventSubscriberInterface|ShouldQueue)',
        re.MULTILINE
    )

    # Observer registration
    OBSERVER_PATTERN = re.compile(
        r'''(?P<model>\w+)::observe\s*\(\s*(?P<observer>[A-Za-z_\\]+)(?:::class)?\s*\)''',
        re.MULTILINE
    )

    # Artisan command
    ARTISAN_COMMAND_PATTERN = re.compile(
        r'''protected\s+\$(?:signature|name)\s*=\s*['"](?P<name>[^'"]+)['"]''',
    )

    # Schedule definition
    SCHEDULE_PATTERN = re.compile(
        r'''\$schedule\s*->\s*(?:command|call|job|exec)\s*\(\s*['"]?(?P<command>[^'")\s]+)['"]?''',
        re.MULTILINE
    )

    # Service provider class
    SERVICE_PROVIDER_PATTERN = re.compile(
        r'class\s+(?P<name>\w+ServiceProvider)\s+extends\s+ServiceProvider',
        re.MULTILINE
    )

    # Facade accessor
    FACADE_PATTERN = re.compile(
        r'''class\s+(?P<name>\w+)\s+extends\s+Facade.*?'''
        r'''getFacadeAccessor.*?return\s+['"](?P<accessor>[^'"]+)['"]''',
        re.DOTALL
    )

    def __init__(self):
        """Initialize the attribute extractor."""
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all PHP attributes, annotations, and bindings from source code.

        Args:
            content: PHP source code content
            file_path: Path to source file

        Returns:
            Dict with extracted information
        """
        attributes = self._extract_attributes(content, file_path)
        annotations = self._extract_annotations(content, file_path)
        di_bindings = self._extract_di_bindings(content, file_path)
        event_listeners = self._extract_event_listeners(content, file_path)
        commands = self._extract_commands(content, file_path)
        schedules = self._extract_schedules(content, file_path)
        service_providers = self._extract_service_providers(content, file_path)
        facades = self._extract_facades(content, file_path)

        return {
            'attributes': attributes,
            'annotations': annotations,
            'di_bindings': di_bindings,
            'event_listeners': event_listeners,
            'commands': commands,
            'schedules': schedules,
            'service_providers': service_providers,
            'facades': facades,
        }

    def _extract_attributes(self, content: str, file_path: str) -> List[PhpAttributeInfo]:
        """Extract PHP 8.0+ attributes."""
        attributes = []
        for match in self.ATTRIBUTE_PATTERN.finditer(content):
            name = match.group('name')
            args = match.group('args')
            line_number = content[:match.start()].count('\n') + 1

            # Find the target (next class/method/property declaration)
            after = content[match.end():match.end() + 300]
            target_match = re.search(
                r'(?:class|function|(?:public|protected|private)\s+(?:static\s+)?(?:\??\w+\s+)?\$)\s*(\w+)',
                after
            )
            target = target_match.group(1) if target_match else None

            arguments = []
            if args:
                arguments = [a.strip() for a in args.split(',') if a.strip()]

            attributes.append(PhpAttributeInfo(
                name=name.rsplit('\\', 1)[-1],  # Short name
                target=target,
                arguments=arguments[:5],
                file=file_path,
                line_number=line_number,
            ))

        return attributes

    def _extract_annotations(self, content: str, file_path: str) -> List[PhpAnnotationInfo]:
        """Extract Doctrine/Symfony annotations from doc blocks."""
        annotations = []

        # Only extract annotations inside doc blocks
        for doc_match in re.finditer(r'/\*\*([\s\S]*?)\*/', content):
            doc_content = doc_match.group(1)
            doc_start = doc_match.start()

            for match in self.ANNOTATION_PATTERN.finditer(doc_content):
                name = match.group('name')
                # Skip common PHPDoc tags
                if name.lower() in ('param', 'return', 'var', 'throws', 'see', 'todo',
                                     'deprecated', 'author', 'since', 'version',
                                     'inheritdoc', 'internal', 'link', 'method',
                                     'property', 'mixin', 'template', 'extends', 'implements'):
                    continue

                line_number = content[:doc_start].count('\n') + 1
                args = match.group('args') or ''
                arg_dict = {}
                for arg_match in re.finditer(r'(\w+)\s*=\s*(?:"([^"]*)"|(\w+))', args):
                    arg_dict[arg_match.group(1)] = arg_match.group(2) or arg_match.group(3)

                annotations.append(PhpAnnotationInfo(
                    name=name.rsplit('\\', 1)[-1],
                    arguments=arg_dict,
                    file=file_path,
                    line_number=line_number,
                ))

        return annotations

    def _extract_di_bindings(self, content: str, file_path: str) -> List[PhpDIBindingInfo]:
        """Extract dependency injection bindings."""
        bindings = []

        for match in self.LARAVEL_BIND_PATTERN.finditer(content):
            abstract = match.group('abstract').strip("'\"").replace('::class', '')
            concrete = match.group('concrete').strip("'\"").replace('::class', '')
            line_number = content[:match.start()].count('\n') + 1

            bindings.append(PhpDIBindingInfo(
                abstract=abstract.rsplit('\\', 1)[-1],
                concrete=concrete.rsplit('\\', 1)[-1],
                kind=match.group('kind'),
                framework="laravel",
                file=file_path,
                line_number=line_number,
            ))

        return bindings

    def _extract_event_listeners(self, content: str, file_path: str) -> List[PhpEventListenerInfo]:
        """Extract event listeners."""
        listeners = []

        for match in self.EVENT_LISTEN_PATTERN.finditer(content):
            event = match.group('event').strip("'\"").replace('::class', '')
            listener = match.group('listener').strip("'\"").replace('::class', '')
            line_number = content[:match.start()].count('\n') + 1

            listeners.append(PhpEventListenerInfo(
                event=event.rsplit('\\', 1)[-1],
                listener=listener.rsplit('\\', 1)[-1],
                kind="listener",
                file=file_path,
                line_number=line_number,
            ))

        for match in self.OBSERVER_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            listeners.append(PhpEventListenerInfo(
                event=match.group('model'),
                listener=match.group('observer').rsplit('\\', 1)[-1],
                kind="observer",
                file=file_path,
                line_number=line_number,
            ))

        return listeners

    def _extract_commands(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract Artisan command definitions."""
        commands = []

        for match in self.ARTISAN_COMMAND_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            commands.append({
                'name': match.group('name'),
                'file': file_path,
                'line': line_number,
            })

        return commands

    def _extract_schedules(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract scheduled task definitions."""
        schedules = []

        for match in self.SCHEDULE_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            schedules.append({
                'command': match.group('command'),
                'file': file_path,
                'line': line_number,
            })

        return schedules

    def _extract_service_providers(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract service provider classes."""
        providers = []

        for match in self.SERVICE_PROVIDER_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            providers.append({
                'name': match.group('name'),
                'file': file_path,
                'line': line_number,
            })

        return providers

    def _extract_facades(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract Facade classes."""
        facades = []

        for match in self.FACADE_PATTERN.finditer(content):
            facades.append({
                'name': match.group('name'),
                'accessor': match.group('accessor'),
                'file': file_path,
            })

        return facades

    @staticmethod
    def parse_composer_json(content: str) -> Dict[str, Any]:
        """
        Parse composer.json to extract dependency information.

        Args:
            content: composer.json file content

        Returns:
            Dict with 'php_version', 'packages', 'dev_packages',
            'autoload', 'scripts', 'name', 'description'
        """
        result: Dict[str, Any] = {
            'name': '',
            'description': '',
            'php_version': '',
            'packages': [],
            'dev_packages': [],
            'autoload': {},
            'scripts': {},
            'type': '',
        }

        try:
            data = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return result

        result['name'] = data.get('name', '')
        result['description'] = data.get('description', '')
        result['type'] = data.get('type', '')

        # PHP version requirement
        require = data.get('require', {})
        if 'php' in require:
            result['php_version'] = require['php']

        # Dependencies
        for pkg_name, version in require.items():
            if pkg_name == 'php':
                continue
            result['packages'].append(PhpPackageInfo(
                name=pkg_name,
                version=version,
                is_dev=False,
            ))

        # Dev dependencies
        require_dev = data.get('require-dev', {})
        for pkg_name, version in require_dev.items():
            result['dev_packages'].append(PhpPackageInfo(
                name=pkg_name,
                version=version,
                is_dev=True,
            ))

        # Autoload
        autoload = data.get('autoload', {})
        if 'psr-4' in autoload:
            result['autoload']['psr-4'] = autoload['psr-4']
        if 'psr-0' in autoload:
            result['autoload']['psr-0'] = autoload['psr-0']
        if 'classmap' in autoload:
            result['autoload']['classmap'] = autoload['classmap']

        # Scripts
        scripts = data.get('scripts', {})
        result['scripts'] = dict(list(scripts.items())[:10])

        return result
