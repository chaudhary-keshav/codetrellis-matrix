"""
AdonisJS controller extractor - Extract controller classes, actions, and DI.

Extracts:
- Controller class declarations (export default class UsersController)
- Controller actions (index, show, create, store, edit, update, destroy, handle)
- Dependency injection via constructor (@inject decorator, IoC bindings)
- Request/Response type annotations (HttpContext, { request, response, auth })
- Validator usage (await request.validate(CreateUserValidator))
- Resource controller pattern (resourceful CRUD actions)
- Custom decorators

Supports AdonisJS v4 (class-based), v5 (TypeScript + IoC), v6 (ESM + inject).
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set


@dataclass
class AdonisActionInfo:
    """Information about a controller action/method."""
    name: str = ""              # index, show, store, update, destroy, handle
    is_async: bool = False
    is_resourceful: bool = False  # standard CRUD action
    params: List[str] = field(default_factory=list)     # destructured HttpContext params
    validator: str = ""         # validator class used
    return_type: str = ""       # TypeScript return type
    decorators: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class AdonisControllerInfo:
    """Information about an AdonisJS controller."""
    name: str = ""              # UsersController
    file: str = ""
    actions: List[AdonisActionInfo] = field(default_factory=list)
    is_resourceful: bool = False  # has standard CRUD actions
    has_injection: bool = False   # uses @inject
    injected_deps: List[str] = field(default_factory=list)  # injected service names
    extends: str = ""            # parent class
    decorators: List[str] = field(default_factory=list)
    line_number: int = 0


class AdonisControllerExtractor:
    """Extract AdonisJS controller definitions and actions."""

    # Resourceful action names
    RESOURCEFUL_ACTIONS: Set[str] = {
        'index', 'show', 'create', 'store', 'edit', 'update', 'destroy',
    }

    # Controller class: export default class UsersController { or export default class UsersController extends BaseController {
    CONTROLLER_CLASS_PATTERN = re.compile(
        r'(?:export\s+default\s+)?class\s+(\w+Controller)\s*(?:extends\s+(\w+))?\s*\{',
        re.MULTILINE,
    )

    # v4 style: module.exports = class UsersController {
    V4_CONTROLLER_PATTERN = re.compile(
        r'module\.exports\s*=\s*class\s+(\w+Controller)\s*(?:extends\s+(\w+))?\s*\{',
        re.MULTILINE,
    )

    # Action method: async index({ request, response, auth }: HttpContext) or async index(ctx: HttpContext)
    ACTION_PATTERN = re.compile(
        r'(?:(?:public|protected|private)\s+)?'
        r'(async\s+)?'
        r'(\w+)\s*\(\s*'
        r'(?:\{([^}]*)\}\s*:\s*HttpContext|(\w+)\s*:\s*HttpContext|'
        r'\{([^}]*)\})',
        re.MULTILINE,
    )

    # Simple method pattern (fallback)
    SIMPLE_METHOD_PATTERN = re.compile(
        r'(?:(?:public|protected|private)\s+)?'
        r'(async\s+)?'
        r'(\w+)\s*\(\s*[^)]*\)\s*(?::\s*[^{]+)?\s*\{',
        re.MULTILINE,
    )

    # @inject() decorator
    INJECT_PATTERN = re.compile(
        r'@inject\s*\(\s*\)',
        re.MULTILINE,
    )

    # Constructor with DI: constructor(private userService: UserService)
    CONSTRUCTOR_DI_PATTERN = re.compile(
        r'constructor\s*\(\s*([^)]+)\)',
        re.MULTILINE,
    )

    # Private/protected param in constructor
    DI_PARAM_PATTERN = re.compile(
        r'(?:private|protected|public)\s+(\w+)\s*:\s*(\w+)',
        re.MULTILINE,
    )

    # Validator usage: await request.validate(CreateUserValidator)
    VALIDATOR_PATTERN = re.compile(
        r'request\.validate\s*\(\s*(\w+)',
        re.MULTILINE,
    )

    # v6 vine validator: const payload = await request.validateUsing(createUserValidator)
    VINE_VALIDATOR_PATTERN = re.compile(
        r'request\.validateUsing\s*\(\s*(\w+)',
        re.MULTILINE,
    )

    # Decorator pattern: @decorator or @decorator()
    DECORATOR_PATTERN = re.compile(
        r'@(\w+)(?:\s*\([^)]*\))?',
        re.MULTILINE,
    )

    # Return type annotation
    RETURN_TYPE_PATTERN = re.compile(
        r'\)\s*:\s*(Promise<[^{]+>|[^{]+)\s*\{',
        re.MULTILINE,
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all AdonisJS controller information from source code.

        Returns:
            Dict with 'controllers' (List[AdonisControllerInfo])
        """
        controllers: List[AdonisControllerInfo] = []

        # Find controller classes
        for match in list(self.CONTROLLER_CLASS_PATTERN.finditer(content)) + \
                      list(self.V4_CONTROLLER_PATTERN.finditer(content)):
            name = match.group(1)
            extends = match.group(2) or ''
            line_number = content[:match.start()].count('\n') + 1

            controller = AdonisControllerInfo(
                name=name,
                extends=extends,
                file=file_path,
                line_number=line_number,
            )

            # Get the class body (rough extraction)
            class_start = match.end()
            class_end = self._find_class_end(content, class_start)
            class_body = content[class_start:class_end]

            # @inject decorator
            if self.INJECT_PATTERN.search(content[:match.start() + 200]):
                controller.has_injection = True

            # Class-level decorators
            prefix = content[max(0, match.start() - 200):match.start()]
            for dec_match in self.DECORATOR_PATTERN.finditer(prefix):
                controller.decorators.append(dec_match.group(1))

            # Constructor DI
            ctor_match = self.CONSTRUCTOR_DI_PATTERN.search(class_body)
            if ctor_match:
                ctor_params = ctor_match.group(1)
                for di_match in self.DI_PARAM_PATTERN.finditer(ctor_params):
                    controller.injected_deps.append(di_match.group(2))
                    controller.has_injection = True

            # Extract actions
            controller.actions = self._extract_actions(class_body, line_number)

            # Check if resourceful
            action_names = {a.name for a in controller.actions}
            resourceful_count = len(action_names & self.RESOURCEFUL_ACTIONS)
            controller.is_resourceful = resourceful_count >= 3

            controllers.append(controller)

        return {'controllers': controllers}

    def _extract_actions(self, class_body: str, base_line: int) -> List[AdonisActionInfo]:
        """Extract actions from a controller class body."""
        actions: List[AdonisActionInfo] = []
        seen_names: Set[str] = set()

        # Try the HttpContext-aware pattern first
        for match in self.ACTION_PATTERN.finditer(class_body):
            is_async = bool(match.group(1))
            name = match.group(2)
            params_str = match.group(3) or match.group(5) or ''
            ctx_var = match.group(4) or ''

            if name in seen_names or name in ('constructor', '__init__'):
                continue
            seen_names.add(name)

            line_number = base_line + class_body[:match.start()].count('\n')

            action = AdonisActionInfo(
                name=name,
                is_async=is_async,
                is_resourceful=name in self.RESOURCEFUL_ACTIONS,
                line_number=line_number,
            )

            # Destructured params
            if params_str:
                action.params = [p.strip() for p in params_str.split(',') if p.strip()]
            elif ctx_var:
                action.params = [ctx_var]

            # Find validator usage in action body
            action_start = match.end()
            action_end = min(action_start + 2000, len(class_body))
            action_body = class_body[action_start:action_end]

            val_match = self.VALIDATOR_PATTERN.search(action_body)
            if val_match:
                action.validator = val_match.group(1)
            else:
                vine_match = self.VINE_VALIDATOR_PATTERN.search(action_body)
                if vine_match:
                    action.validator = vine_match.group(1)

            # Decorators before the method
            prefix = class_body[max(0, match.start() - 200):match.start()]
            for dec_match in self.DECORATOR_PATTERN.finditer(prefix):
                action.decorators.append(dec_match.group(1))

            actions.append(action)

        # Fallback: simple method pattern for methods not matched above
        for match in self.SIMPLE_METHOD_PATTERN.finditer(class_body):
            is_async = bool(match.group(1))
            name = match.group(2)

            if name in seen_names or name in ('constructor', '__init__'):
                continue
            # Only include known controller-like method names
            if name not in self.RESOURCEFUL_ACTIONS and name != 'handle':
                continue
            seen_names.add(name)

            line_number = base_line + class_body[:match.start()].count('\n')

            action = AdonisActionInfo(
                name=name,
                is_async=is_async,
                is_resourceful=name in self.RESOURCEFUL_ACTIONS,
                line_number=line_number,
            )
            actions.append(action)

        return actions

    @staticmethod
    def _find_class_end(content: str, start: int) -> int:
        """Find the end of a class body by counting braces."""
        depth = 1
        i = start
        while i < len(content) and depth > 0:
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
            i += 1
        return i
