"""
Remix Action Extractor v1.0

Extracts mutation/action patterns from Remix / React Router v7 files:
- action function (server-side mutations)
- clientAction function (client-side mutations)
- Form component usage (<Form>, fetcher.Form)
- useActionData hook
- useSubmit hook
- useNavigation (pending/submitting state)
- request.formData() patterns
- Optimistic UI patterns
- Revalidation patterns

Supports:
- Remix v1.x (action, useActionData, ActionFunction, Form)
- Remix v2.x (typed action data, useNavigation)
- React Router v7 (Route.ActionArgs, actionData prop, middleware)

Part of CodeTrellis v4.61 - Remix Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class RemixActionInfo:
    """Information about an action function."""
    file_path: str = ""
    line_number: int = 0
    is_async: bool = False

    # Parameters
    has_request: bool = False
    has_params: bool = False
    has_context: bool = False

    # Request handling
    uses_form_data: bool = False
    uses_json_body: bool = False
    uses_url_search_params: bool = False

    # Return patterns
    returns_json: bool = False
    returns_redirect: bool = False
    returns_response: bool = False
    returns_throw: bool = False
    returns_plain: bool = False

    # Validation
    has_validation: bool = False
    validation_library: str = ""  # zod, yup, valibot, etc.

    # Type safety
    has_typed_args: bool = False
    args_type: str = ""  # ActionFunctionArgs, Route.ActionArgs

    # Intent pattern
    has_intent_pattern: bool = False
    intents: List[str] = field(default_factory=list)


@dataclass
class RemixClientActionInfo:
    """Information about a clientAction function."""
    file_path: str = ""
    line_number: int = 0
    is_async: bool = False
    calls_server_action: bool = False
    has_typed_args: bool = False
    args_type: str = ""


@dataclass
class RemixFormInfo:
    """Information about Form component usage."""
    file_path: str = ""
    line_number: int = 0
    method: str = ""  # post, get, put, patch, delete
    action_url: str = ""
    has_navigate: bool = False
    has_replace: bool = False
    has_fetcher_form: bool = False
    has_enctype: bool = False
    enctype: str = ""


class RemixActionExtractor:
    """Extracts action/mutation patterns from Remix/RR7 files."""

    # Action function patterns
    ACTION_PATTERN = re.compile(
        r'export\s+(async\s+)?function\s+action\s*\(\s*'
        r'(?:\{\s*([^}]*)\}\s*(?::\s*(\w[\w.]*))?)?\s*\)',
        re.MULTILINE
    )

    ACTION_ARROW_PATTERN = re.compile(
        r'export\s+(?:const|let)\s+action\s*(?::\s*(\w[\w.]*))?\s*=\s*(async\s+)?',
        re.MULTILINE
    )

    # Client action
    CLIENT_ACTION_PATTERN = re.compile(
        r'export\s+(async\s+)?function\s+clientAction\s*\(\s*'
        r'(?:\{\s*([^}]*)\}\s*(?::\s*(\w[\w.]*))?)?\s*\)',
        re.MULTILINE
    )

    SERVER_ACTION_CALL = re.compile(
        r'(?:await\s+)?serverAction\s*\(\s*\)',
        re.MULTILINE
    )

    # Form patterns
    FORM_PATTERN = re.compile(
        r'<Form\b([^>]*)>',
        re.MULTILINE | re.DOTALL
    )

    FETCHER_FORM_PATTERN = re.compile(
        r'<fetcher\.Form\b([^>]*)>',
        re.MULTILINE | re.DOTALL
    )

    FORM_METHOD = re.compile(
        r'method\s*=\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    FORM_ACTION = re.compile(
        r'action\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    FORM_NAVIGATE = re.compile(
        r'navigate\s*=\s*\{?\s*false\s*\}?',
        re.MULTILINE
    )

    FORM_REPLACE = re.compile(
        r'replace\b',
        re.MULTILINE
    )

    FORM_ENCTYPE = re.compile(
        r'encType\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # Hook patterns
    USE_ACTION_DATA = re.compile(
        r'useActionData\s*(?:<\s*typeof\s+action\s*>)?\s*\(\s*\)',
        re.MULTILINE
    )

    USE_SUBMIT = re.compile(
        r'useSubmit\s*\(\s*\)',
        re.MULTILINE
    )

    USE_NAVIGATION = re.compile(
        r'useNavigation\s*\(\s*\)',
        re.MULTILINE
    )

    NAVIGATION_STATE = re.compile(
        r'navigation\.state\s*===?\s*["\'](\w+)["\']|'
        r'state\s*===?\s*["\']submitting["\']|'
        r'isSubmitting\b',
        re.MULTILINE
    )

    # Request handling
    FORM_DATA_USAGE = re.compile(
        r'request\.formData\s*\(\s*\)|'
        r'await\s+request\.formData\s*\(\s*\)',
        re.MULTILINE
    )

    JSON_BODY_USAGE = re.compile(
        r'request\.json\s*\(\s*\)|'
        r'await\s+request\.json\s*\(\s*\)',
        re.MULTILINE
    )

    URL_SEARCH_PARAMS = re.compile(
        r'new\s+URL\s*\(\s*request\.url\s*\)\.searchParams|'
        r'request\.url.*searchParams',
        re.MULTILINE
    )

    # Validation patterns
    ZOD_VALIDATION = re.compile(r'\.parse\s*\(|\.safeParse\s*\(|z\.\w+', re.MULTILINE)
    YUP_VALIDATION = re.compile(r'\.validate\s*\(|yup\.\w+', re.MULTILINE)
    VALIBOT_VALIDATION = re.compile(r'v\.parse\s*\(|valibot\.\w+', re.MULTILINE)

    # Intent pattern (discriminated actions)
    INTENT_PATTERN = re.compile(
        r'\w+\.get\s*\(\s*["\'](?:intent|_action|action)["\']|'
        r'intent\s*===?\s*["\'](\w+)["\']|'
        r'name\s*=\s*["\']intent["\']\s+value\s*=\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    # Typed action args
    TYPED_ACTION_ARGS = re.compile(
        r'(?:ActionFunctionArgs|ActionArgs|Route\.ActionArgs)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract action/mutation information from source.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with actions, client_actions, forms
        """
        actions: List[RemixActionInfo] = []
        client_actions: List[RemixClientActionInfo] = []
        forms: List[RemixFormInfo] = []

        # Extract action function
        action = self._extract_action(content, file_path)
        if action:
            actions.append(action)

        # Extract clientAction
        client_action = self._extract_client_action(content, file_path)
        if client_action:
            client_actions.append(client_action)

        # Extract Form usage
        forms.extend(self._extract_forms(content, file_path))

        return {
            'actions': actions,
            'client_actions': client_actions,
            'forms': forms,
            'has_use_action_data': bool(self.USE_ACTION_DATA.search(content)),
            'has_use_submit': bool(self.USE_SUBMIT.search(content)),
            'has_use_navigation': bool(self.USE_NAVIGATION.search(content)),
            'has_optimistic_ui': bool(self.NAVIGATION_STATE.search(content)),
        }

    def _extract_action(self, content: str, file_path: str) -> Optional[RemixActionInfo]:
        """Extract action function information."""
        match = self.ACTION_PATTERN.search(content)
        arrow_match = self.ACTION_ARROW_PATTERN.search(content)

        if not match and not arrow_match:
            return None

        action = RemixActionInfo(file_path=file_path)

        if match:
            action.line_number = content[:match.start()].count('\n') + 1
            action.is_async = bool(match.group(1))
            params = match.group(2) or ""
            type_name = match.group(3) or ""

            action.has_request = 'request' in params
            action.has_params = 'params' in params
            action.has_context = 'context' in params

            if type_name:
                action.has_typed_args = True
                action.args_type = type_name
        elif arrow_match:
            action.line_number = content[:arrow_match.start()].count('\n') + 1
            action.is_async = bool(arrow_match.group(2))
            if arrow_match.group(1):
                action.has_typed_args = True
                action.args_type = arrow_match.group(1)

        # Request handling
        action.uses_form_data = bool(self.FORM_DATA_USAGE.search(content))
        action.uses_json_body = bool(self.JSON_BODY_USAGE.search(content))
        action.uses_url_search_params = bool(self.URL_SEARCH_PARAMS.search(content))

        # Return patterns
        action.returns_json = bool(re.search(r'\bjson\s*\(', content))
        action.returns_redirect = bool(re.search(r'\bredirect\s*\(', content))
        action.returns_response = bool(re.search(r'new\s+Response\s*\(', content))
        action.returns_throw = bool(re.search(r'throw\s+(?:new\s+Response|json|redirect)\s*\(', content))
        action.returns_plain = not any([
            action.returns_json, action.returns_redirect, action.returns_response,
        ])

        # Typed args
        if self.TYPED_ACTION_ARGS.search(content):
            action.has_typed_args = True

        # Validation
        if self.ZOD_VALIDATION.search(content):
            action.has_validation = True
            action.validation_library = "zod"
        elif self.YUP_VALIDATION.search(content):
            action.has_validation = True
            action.validation_library = "yup"
        elif self.VALIBOT_VALIDATION.search(content):
            action.has_validation = True
            action.validation_library = "valibot"

        # Intent pattern
        intent_matches = self.INTENT_PATTERN.findall(content)
        if intent_matches:
            action.has_intent_pattern = True
            for groups in intent_matches:
                for g in groups:
                    if g:
                        action.intents.append(g)

        return action

    def _extract_client_action(self, content: str, file_path: str) -> Optional[RemixClientActionInfo]:
        """Extract clientAction function."""
        match = self.CLIENT_ACTION_PATTERN.search(content)
        if not match:
            return None

        ca = RemixClientActionInfo(file_path=file_path)
        ca.line_number = content[:match.start()].count('\n') + 1
        ca.is_async = bool(match.group(1))
        params = match.group(2) or ""
        type_name = match.group(3) or ""

        ca.calls_server_action = bool(self.SERVER_ACTION_CALL.search(content))

        if type_name:
            ca.has_typed_args = True
            ca.args_type = type_name

        return ca

    def _extract_forms(self, content: str, file_path: str) -> List[RemixFormInfo]:
        """Extract Form component usage."""
        forms: List[RemixFormInfo] = []

        for match in self.FORM_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            attrs = match.group(1) or ""

            form = RemixFormInfo(
                file_path=file_path,
                line_number=line_num,
                has_fetcher_form=False,
            )

            method_match = self.FORM_METHOD.search(attrs)
            if method_match:
                form.method = method_match.group(1).lower()

            action_match = self.FORM_ACTION.search(attrs)
            if action_match:
                form.action_url = action_match.group(1)

            form.has_navigate = bool(self.FORM_NAVIGATE.search(attrs))
            form.has_replace = bool(self.FORM_REPLACE.search(attrs))

            enc_match = self.FORM_ENCTYPE.search(attrs)
            if enc_match:
                form.has_enctype = True
                form.enctype = enc_match.group(1)

            forms.append(form)

        # fetcher.Form
        for match in self.FETCHER_FORM_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            attrs = match.group(1) or ""

            form = RemixFormInfo(
                file_path=file_path,
                line_number=line_num,
                has_fetcher_form=True,
            )

            method_match = self.FORM_METHOD.search(attrs)
            if method_match:
                form.method = method_match.group(1).lower()

            forms.append(form)

        return forms
