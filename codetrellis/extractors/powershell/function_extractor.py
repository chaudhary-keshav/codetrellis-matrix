"""
PowerShell Function Extractor for CodeTrellis

Extracts function and script definitions from PowerShell source code:
- Functions (function keyword)
- Advanced functions (CmdletBinding)
- Filters
- Workflows (PS 3.0-5.1, removed in PS 7+)
- Script blocks
- Pipeline definitions
- Parameter sets
- Dynamic parameters

Supports PowerShell 1.0 through 7.4+ (PowerShell Core / pwsh).
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PSParameterInfo:
    """Information about a PowerShell function parameter."""
    name: str
    type: str = ""
    default_value: Optional[str] = None
    is_mandatory: bool = False
    position: Optional[int] = None
    pipeline_input: bool = False
    validate_set: List[str] = field(default_factory=list)
    validate_range: Optional[str] = None
    validate_pattern: Optional[str] = None
    validate_script: Optional[str] = None
    aliases: List[str] = field(default_factory=list)
    help_message: Optional[str] = None
    parameter_set: Optional[str] = None
    is_switch: bool = False
    attributes: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class PSFunctionInfo:
    """Information about a PowerShell function definition."""
    name: str
    file: str = ""
    line_number: int = 0
    function_type: str = "function"  # function, filter, workflow, cmdlet
    parameters: List[PSParameterInfo] = field(default_factory=list)
    output_type: Optional[str] = None
    is_advanced: bool = False
    is_exported: bool = False
    cmdlet_binding: bool = False
    supports_should_process: bool = False
    default_parameter_set: Optional[str] = None
    parameter_sets: List[str] = field(default_factory=list)
    begin_block: bool = False
    process_block: bool = False
    end_block: bool = False
    has_begin_process_end: bool = False
    verb: Optional[str] = None
    noun: Optional[str] = None
    aliases: List[str] = field(default_factory=list)
    help_synopsis: Optional[str] = None


@dataclass
class PSScriptBlockInfo:
    """Information about a PowerShell script block."""
    name: str
    file: str = ""
    line_number: int = 0
    block_type: str = ""  # begin, process, end, clean, scriptblock
    variables_used: List[str] = field(default_factory=list)


@dataclass
class PSPipelineInfo:
    """Information about a pipeline definition or pattern."""
    name: str
    file: str = ""
    line_number: int = 0
    commands: List[str] = field(default_factory=list)
    pipeline_type: str = ""  # sequential, parallel, foreach-object


class PowerShellFunctionExtractor:
    """
    Extracts function definitions from PowerShell source code.

    Detects:
    - Standard functions (function Verb-Noun {})
    - Advanced functions ([CmdletBinding()])
    - Filters (filter Name {})
    - Workflows (workflow Name {}) - PS 3.0-5.1
    - Script blocks ($sb = { ... })
    - Pipeline patterns (... | ForEach-Object { ... })
    """

    # Function/Filter/Workflow definition
    FUNCTION_PATTERN = re.compile(
        r'^\s*(function|filter|workflow)\s+'
        r'([\w-]+)'
        r'\s*(?:\(([^)]*)\))?\s*\{',
        re.MULTILINE | re.IGNORECASE
    )

    # CmdletBinding attribute
    CMDLET_BINDING_PATTERN = re.compile(
        r'\[CmdletBinding\(([^)]*)\)\]',
        re.IGNORECASE
    )

    # OutputType attribute
    OUTPUT_TYPE_PATTERN = re.compile(
        r'\[OutputType\(\[?(\w+(?:\[\])?)\]?\)\]',
        re.IGNORECASE
    )

    # Alias attribute
    ALIAS_PATTERN = re.compile(
        r"\[Alias\(([^)]+)\)\]",
        re.IGNORECASE
    )

    # Parameter block
    PARAM_BLOCK_PATTERN = re.compile(
        r'param\s*\((.+?)\)',
        re.DOTALL | re.IGNORECASE
    )

    # Individual parameter
    PARAM_PATTERN = re.compile(
        r'(?:(\[[\w\(\),\s="\'\.]+?\])\s*)*'
        r'\[(\w+(?:\[\])?)\]\s*'
        r'\$(\w+)'
        r'(?:\s*=\s*(.+?))?'
        r'\s*(?:,|$)',
        re.MULTILINE | re.DOTALL
    )

    # Simple parameter (no type annotation)
    SIMPLE_PARAM_PATTERN = re.compile(
        r'\$(\w+)\s*(?:=\s*(.+?))?\s*(?:,|$)',
        re.MULTILINE
    )

    # Script block assignment
    SCRIPT_BLOCK_PATTERN = re.compile(
        r'\$(\w+)\s*=\s*\{',
        re.MULTILINE
    )

    # Begin/Process/End blocks
    BLOCK_PATTERN = re.compile(
        r'^\s*(begin|process|end|clean)\s*\{',
        re.MULTILINE | re.IGNORECASE
    )

    # Verb-Noun pattern
    VERB_NOUN_PATTERN = re.compile(r'^(Get|Set|New|Remove|Add|Clear|Enable|Disable|Start|Stop|Restart|'
                                     r'Test|Update|Find|Search|Import|Export|Invoke|Enter|Exit|'
                                     r'Connect|Disconnect|Read|Write|Send|Receive|Move|Copy|'
                                     r'Register|Unregister|Install|Uninstall|Save|Restore|'
                                     r'Open|Close|Show|Hide|Wait|Resume|Suspend|'
                                     r'Publish|Unpublish|Measure|Compare|Convert|'
                                     r'Format|Select|Sort|Group|Join|Split|Merge|'
                                     r'Assert|Confirm|Deny|Grant|Revoke|'
                                     r'Protect|Unprotect|Lock|Unlock|'
                                     r'Mount|Dismount|Push|Pop|Use|'
                                     r'Initialize|Complete|Undo|Redo|Reset|Resize|'
                                     r'Optimize|Debug|Trace|Watch|Repair|Resolve)-([\w]+)$')

    # Pipeline pattern
    PIPELINE_PATTERN = re.compile(
        r'(\$[\w.]+|[\w-]+)\s*\|\s*([\w-]+(?:\s*\|[\s\w-]+)*)',
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> dict:
        """
        Extract all function definitions from PowerShell source code.

        Returns dict with keys: functions, script_blocks, pipelines
        """
        functions = self._extract_functions(content, file_path)
        script_blocks = self._extract_script_blocks(content, file_path)
        pipelines = self._extract_pipelines(content, file_path)

        return {
            'functions': functions,
            'script_blocks': script_blocks,
            'pipelines': pipelines,
        }

    def _extract_functions(self, content: str, file_path: str) -> List[PSFunctionInfo]:
        """Extract PowerShell function definitions."""
        functions = []
        seen_names = set()

        for match in self.FUNCTION_PATTERN.finditer(content):
            func_type = match.group(1).lower()
            name = match.group(2)
            inline_params = match.group(3) or ""
            line_num = content[:match.start()].count('\n') + 1

            if name in seen_names:
                continue
            seen_names.add(name)

            # Look for attributes above the function
            pre_text = content[:match.start()]
            pre_lines = pre_text.split('\n')
            attr_window = '\n'.join(pre_lines[-10:]) if len(pre_lines) >= 10 else '\n'.join(pre_lines)

            # Check CmdletBinding
            is_advanced = False
            cmdlet_binding = False
            supports_should_process = False
            default_param_set = None

            # Extract function body for further analysis
            body_start = match.end() - 1
            func_body = self._extract_brace_block(content, body_start)

            # Check for CmdletBinding in body or attributes
            search_text = (attr_window + '\n' + (func_body or ''))
            cb_match = self.CMDLET_BINDING_PATTERN.search(search_text)
            if cb_match:
                is_advanced = True
                cmdlet_binding = True
                cb_args = cb_match.group(1)
                if 'SupportsShouldProcess' in cb_args:
                    supports_should_process = True
                dps_match = re.search(r'DefaultParameterSetName\s*=\s*["\'](\w+)["\']', cb_args)
                if dps_match:
                    default_param_set = dps_match.group(1)

            # Check OutputType
            output_type = None
            ot_match = self.OUTPUT_TYPE_PATTERN.search(search_text)
            if ot_match:
                output_type = ot_match.group(1)

            # Check aliases
            aliases = []
            alias_match = self.ALIAS_PATTERN.search(search_text)
            if alias_match:
                aliases = [a.strip().strip("'\"") for a in alias_match.group(1).split(',')]

            # Extract parameters
            parameters = []
            param_sets = set()

            if func_body:
                param_text = self._extract_param_block(func_body)
                if param_text:
                    parameters = self._parse_parameters(param_text)
                    for p in parameters:
                        if p.parameter_set:
                            param_sets.add(p.parameter_set)

            # Parse inline parameters if no param block
            if not parameters and inline_params:
                parameters = self._parse_inline_params(inline_params)

            # Check for begin/process/end blocks
            has_begin = False
            has_process = False
            has_end = False
            if func_body:
                for block_match in self.BLOCK_PATTERN.finditer(func_body):
                    block_name = block_match.group(1).lower()
                    if block_name == 'begin':
                        has_begin = True
                    elif block_name == 'process':
                        has_process = True
                    elif block_name == 'end':
                        has_end = True

            # Parse Verb-Noun
            verb = None
            noun = None
            vn_match = self.VERB_NOUN_PATTERN.match(name)
            if vn_match:
                verb = vn_match.group(1)
                noun = vn_match.group(2)

            # Check for Export-ModuleMember
            is_exported = bool(re.search(
                rf'Export-ModuleMember\s.*?-Function\s.*?{re.escape(name)}',
                content, re.IGNORECASE | re.DOTALL
            ))

            # Extract help synopsis
            help_synopsis = None
            help_match = re.search(
                r'\.SYNOPSIS\s*\n\s*(.+?)(?:\n\s*\.|\n\s*#>)',
                attr_window, re.DOTALL | re.IGNORECASE
            )
            if help_match:
                help_synopsis = help_match.group(1).strip()

            functions.append(PSFunctionInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                function_type=func_type,
                parameters=parameters,
                output_type=output_type,
                is_advanced=is_advanced,
                is_exported=is_exported,
                cmdlet_binding=cmdlet_binding,
                supports_should_process=supports_should_process,
                default_parameter_set=default_param_set,
                parameter_sets=list(param_sets),
                begin_block=has_begin,
                process_block=has_process,
                end_block=has_end,
                has_begin_process_end=(has_begin or has_process or has_end),
                verb=verb,
                noun=noun,
                aliases=aliases,
                help_synopsis=help_synopsis,
            ))

        return functions

    def _extract_param_block(self, func_body: str) -> Optional[str]:
        """Extract param block content using balanced parenthesis matching."""
        match = re.search(r'param\s*\(', func_body, re.IGNORECASE)
        if not match:
            return None
        start = match.end()  # position after the opening '('
        depth = 1
        i = start
        while i < len(func_body) and depth > 0:
            if func_body[i] == '(':
                depth += 1
            elif func_body[i] == ')':
                depth -= 1
            i += 1
        if depth == 0:
            return func_body[start:i - 1]
        return func_body[start:]

    def _parse_parameters(self, param_text: str) -> List[PSParameterInfo]:
        """Parse parameter block text into PSParameterInfo list."""
        parameters = []
        # Split on commas that are outside brackets
        parts = self._split_params(param_text)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Extract attributes
            attrs = re.findall(r'\[([\w\(\),\s="\'\.]+?)\]', part)
            is_mandatory = any('Mandatory' in a for a in attrs)
            is_switch = False

            # Extract position
            position = None
            for a in attrs:
                pos_match = re.search(r'Position\s*=\s*(\d+)', a)
                if pos_match:
                    position = int(pos_match.group(1))

            # Extract pipeline input
            pipeline_input = any('ValueFromPipeline' in a for a in attrs)

            # Extract parameter set
            param_set = None
            for a in attrs:
                ps_match = re.search(r'ParameterSetName\s*=\s*["\'](\w+)["\']', a)
                if ps_match:
                    param_set = ps_match.group(1)

            # Extract ValidateSet
            validate_set = []
            for a in attrs:
                vs_match = re.search(r'ValidateSet\((.+)\)', a)
                if vs_match:
                    validate_set = [v.strip().strip("'\"") for v in vs_match.group(1).split(',')]

            # Extract type and name
            type_match = re.search(r'\[(\w+(?:\[\])?)\]\s*\$(\w+)', part)
            if type_match:
                param_type = type_match.group(1)
                param_name = type_match.group(2)
                is_switch = param_type.lower() == 'switch'
            else:
                # No type annotation
                name_match = re.search(r'\$(\w+)', part)
                if name_match:
                    param_name = name_match.group(1)
                    param_type = ""
                else:
                    continue

            # Extract default value
            default = None
            default_match = re.search(r'\$\w+\s*=\s*(.+?)(?:,|$)', part, re.DOTALL)
            if default_match:
                default = default_match.group(1).strip()

            parameters.append(PSParameterInfo(
                name=param_name,
                type=param_type,
                default_value=default,
                is_mandatory=is_mandatory,
                position=position,
                pipeline_input=pipeline_input,
                validate_set=validate_set,
                parameter_set=param_set,
                is_switch=is_switch,
                attributes=[a for a in attrs if a],
            ))

        return parameters

    def _parse_inline_params(self, params_str: str) -> List[PSParameterInfo]:
        """Parse inline function parameters (function Name($a, $b))."""
        parameters = []
        parts = [p.strip() for p in params_str.split(',')]
        for part in parts:
            if not part:
                continue
            type_match = re.match(r'\[(\w+(?:\[\])?)\]\s*\$(\w+)', part)
            if type_match:
                parameters.append(PSParameterInfo(
                    name=type_match.group(2),
                    type=type_match.group(1),
                ))
            else:
                name_match = re.match(r'\$(\w+)', part)
                if name_match:
                    parameters.append(PSParameterInfo(
                        name=name_match.group(1),
                    ))
        return parameters

    def _extract_script_blocks(self, content: str, file_path: str) -> List[PSScriptBlockInfo]:
        """Extract named script blocks."""
        blocks = []
        for match in self.SCRIPT_BLOCK_PATTERN.finditer(content):
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            blocks.append(PSScriptBlockInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                block_type='scriptblock',
            ))
        return blocks

    def _extract_pipelines(self, content: str, file_path: str) -> List[PSPipelineInfo]:
        """Extract significant pipeline patterns."""
        pipelines = []
        seen = set()

        # Process line by line, detecting lines with 2+ pipe operators
        for line_num, line in enumerate(content.split('\n'), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            # Remove string literals and scriptblock contents for pipe counting
            cleaned = re.sub(r"'[^']*'", '""', stripped)
            cleaned = re.sub(r'"[^"]*"', '""', cleaned)
            # Remove scriptblock contents but keep the pipe chars outside
            cleaned_for_count = re.sub(r'\{[^}]*\}', '{}', cleaned)

            # Count pipes outside of strings/scriptblocks
            pipe_count = cleaned_for_count.count(' | ') + cleaned_for_count.count('\t| ')
            if pipe_count < 2:
                continue

            # Extract command names from the pipeline
            # Split on | that isn't inside {} 
            parts = []
            depth = 0
            current = []
            for ch in stripped:
                if ch == '{':
                    depth += 1
                    current.append(ch)
                elif ch == '}':
                    depth -= 1
                    current.append(ch)
                elif ch == '|' and depth == 0:
                    parts.append(''.join(current).strip())
                    current = []
                else:
                    current.append(ch)
            if current:
                parts.append(''.join(current).strip())

            if len(parts) >= 3:
                # Extract just command names from each part
                commands = []
                for part in parts:
                    cmd_match = re.match(r'([\w][\w-]*)', part.strip())
                    if cmd_match:
                        commands.append(cmd_match.group(1))
                    else:
                        commands.append(part.strip()[:30])

                key = '|'.join(commands)
                if key in seen:
                    continue
                seen.add(key)

                pipe_type = 'parallel' if 'ForEach-Object' in stripped and '-Parallel' in stripped else 'sequential'
                pipelines.append(PSPipelineInfo(
                    name=f"pipeline_L{line_num}",
                    file=file_path,
                    line_number=line_num,
                    commands=commands[:10],
                    pipeline_type=pipe_type,
                ))

        return pipelines[:20]  # Limit to 20 most significant

    def _split_params(self, text: str) -> List[str]:
        """Split parameter text on commas, respecting brackets."""
        parts = []
        depth = 0
        current = []
        for ch in text:
            if ch in '([{':
                depth += 1
                current.append(ch)
            elif ch in ')]}':
                depth -= 1
                current.append(ch)
            elif ch == ',' and depth == 0:
                parts.append(''.join(current))
                current = []
            else:
                current.append(ch)
        if current:
            parts.append(''.join(current))
        return parts

    def _extract_brace_block(self, content: str, start_pos: int) -> Optional[str]:
        """Extract content within balanced braces starting at start_pos."""
        if start_pos >= len(content) or content[start_pos] != '{':
            return None

        depth = 0
        i = start_pos
        while i < len(content):
            if content[i] == '{':
                depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    return content[start_pos + 1:i]
            i += 1

        return content[start_pos + 1:]
