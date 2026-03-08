"""
Stimulus Target Extractor for CodeTrellis

Extracts Stimulus target definitions and usage from HTML and JavaScript/TypeScript:
- static targets = [...] declarations in controllers
- data-*-target HTML attributes
- Target getter usage: this.nameTarget, this.nameTargets, this.hasNameTarget
- Target callbacks: nameTargetConnected(), nameTargetDisconnected()

Supports:
- Stimulus v1.x (data-target="controller.name" format)
- Stimulus v2.x-v3.x (data-controller-target="name" format)

Part of CodeTrellis v4.68 - Stimulus / Hotwire Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StimulusTargetInfo:
    """Information about a Stimulus target usage."""
    name: str  # Target name (e.g., "output", "input")
    file: str = ""
    line_number: int = 0
    target_type: str = ""  # declaration, html_attribute, getter, callback
    controller_name: str = ""  # Associated controller identifier
    is_plural: bool = False  # this.nameTargets (plural getter)
    has_existence_check: bool = False  # this.hasNameTarget
    is_connected_callback: bool = False  # nameTargetConnected()
    is_disconnected_callback: bool = False  # nameTargetDisconnected()
    is_v1_format: bool = False  # data-target="controller.name" (v1 format)
    version_hint: str = ""  # v1, v2, v3


# HTML: data-controller-target="name" (v2+ format)
HTML_TARGET_V2_PATTERN = re.compile(
    r'data-(?P<controller>[\w-]+)-target\s*=\s*["\'](?P<name>\w+)["\']',
    re.IGNORECASE
)

# HTML: data-target="controller.name" (v1 format)
HTML_TARGET_V1_PATTERN = re.compile(
    r'data-target\s*=\s*["\'](?P<controller>[\w-]+)\.(?P<name>\w+)["\']',
    re.IGNORECASE
)

# JS: this.nameTarget, this.nameTargets, this.hasNameTarget
JS_TARGET_GETTER_PATTERN = re.compile(
    r'this\.\s*(?:has)?(?P<name>\w+?)(?P<suffix>Targets?)\b'
)

# JS: nameTargetConnected(target), nameTargetDisconnected(target)
JS_TARGET_CALLBACK_PATTERN = re.compile(
    r'(?P<name>\w+)Target(?P<type>Connected|Disconnected)\s*\(',
    re.MULTILINE
)


class StimulusTargetExtractor:
    """Extracts Stimulus target definitions and usages."""

    def extract(self, content: str, file_path: str = "") -> List[StimulusTargetInfo]:
        """Extract Stimulus target usage from source code or HTML.

        Args:
            content: File content to parse.
            file_path: Path to the file (for metadata).

        Returns:
            List of StimulusTargetInfo objects.
        """
        if not content or not content.strip():
            return []

        targets: List[StimulusTargetInfo] = []

        # HTML targets (v2+ format): data-controller-target="name"
        for match in HTML_TARGET_V2_PATTERN.finditer(content):
            controller = match.group('controller')
            name = match.group('name')
            line = content[:match.start()].count('\n') + 1
            targets.append(StimulusTargetInfo(
                name=name,
                file=file_path,
                line_number=line,
                target_type="html_attribute",
                controller_name=controller,
                version_hint="v2",
            ))

        # HTML targets (v1 format): data-target="controller.name"
        for match in HTML_TARGET_V1_PATTERN.finditer(content):
            controller = match.group('controller')
            name = match.group('name')
            line = content[:match.start()].count('\n') + 1
            targets.append(StimulusTargetInfo(
                name=name,
                file=file_path,
                line_number=line,
                target_type="html_attribute",
                controller_name=controller,
                is_v1_format=True,
                version_hint="v1",
            ))

        # JS target getters: this.nameTarget, this.nameTargets, this.hasNameTarget
        for match in JS_TARGET_GETTER_PATTERN.finditer(content):
            raw_name = match.group('name')
            suffix = match.group('suffix')
            line = content[:match.start()].count('\n') + 1

            # Determine if it's a has* check
            full_match = match.group(0)
            has_check = full_match.startswith('this.has')

            # Clean the name (remove 'has' prefix if present)
            name = raw_name
            if has_check and name.startswith('has'):
                name = name[3:]
            # Lowercase first letter
            if name:
                name = name[0].lower() + name[1:]

            targets.append(StimulusTargetInfo(
                name=name,
                file=file_path,
                line_number=line,
                target_type="getter",
                is_plural=suffix == 'Targets',
                has_existence_check=has_check,
            ))

        # JS target callbacks: nameTargetConnected(), nameTargetDisconnected()
        for match in JS_TARGET_CALLBACK_PATTERN.finditer(content):
            name = match.group('name')
            callback_type = match.group('type')
            line = content[:match.start()].count('\n') + 1

            # Lowercase first letter
            if name:
                name = name[0].lower() + name[1:]

            targets.append(StimulusTargetInfo(
                name=name,
                file=file_path,
                line_number=line,
                target_type="callback",
                is_connected_callback=callback_type == 'Connected',
                is_disconnected_callback=callback_type == 'Disconnected',
            ))

        return targets
