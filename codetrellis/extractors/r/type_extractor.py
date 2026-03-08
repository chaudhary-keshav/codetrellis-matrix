"""
R Type Extractor for CodeTrellis

Extracts type definitions from R source code:
- R5 Reference Classes (setRefClass)
- R6 Classes (R6Class)
- S4 Classes (setClass, setGeneric, setMethod)
- S3 class constructors (structure(), class<-)
- R7/S7 Classes (new_class) — R 4.3+
- Proto objects (proto package)
- Environments as objects (new.env)
- Package/namespace definitions

Supports: R 2.x through R 4.4+
Part of CodeTrellis v4.26 - R Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RFieldInfo:
    """Information about an R class field/slot."""
    name: str
    type: str = ""
    default_value: Optional[str] = None
    is_active_binding: bool = False
    visibility: str = "public"  # public, private
    comment: Optional[str] = None


@dataclass
class RClassInfo:
    """Information about an R class."""
    name: str
    kind: str = "R6"  # R6, R5, S4, S3, S7, proto
    fields: List[RFieldInfo] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    public_methods: List[str] = field(default_factory=list)
    private_methods: List[str] = field(default_factory=list)
    active_bindings: List[str] = field(default_factory=list)
    parent_class: Optional[str] = None
    contains: List[str] = field(default_factory=list)  # S4 contains
    slots: List[RFieldInfo] = field(default_factory=list)  # S4 slots
    is_virtual: bool = False  # S4 virtual class
    is_sealed: bool = False  # S4 sealed class
    portable: bool = True  # R6 portable
    cloneable: bool = True  # R6 cloneable
    lock_objects: bool = True  # R6 lock_objects
    file: str = ""
    line_number: int = 0
    doc_comment: Optional[str] = None
    package: str = ""


@dataclass
class RGenericInfo:
    """Information about an S4/S7 generic function."""
    name: str
    kind: str = "S4"  # S4 or S7
    signature: List[str] = field(default_factory=list)
    package: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class RS4MethodInfo:
    """Information about an S4 method implementation."""
    generic_name: str
    signature: List[str] = field(default_factory=list)
    target_classes: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class REnvironmentInfo:
    """Information about an R environment used as a namespace/module."""
    name: str
    parent: str = ""
    bindings: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


class RTypeExtractor:
    """
    Extracts R type definitions from source code.

    Supported patterns:
    - R6Class("ClassName", ...)
    - setRefClass("ClassName", ...)
    - setClass("ClassName", ...)
    - setGeneric("name", ...)
    - setMethod("name", ...)
    - new_class("ClassName", ...) [S7/R7]
    - structure(list(), class = "ClassName") [S3]
    - new.env() environment as module
    """

    # R6 class pattern: ClassName <- R6Class("ClassName", ...)  or  R6::R6Class(...)
    R6_CLASS_PATTERN = re.compile(
        r'(\w+)\s*<-\s*(?:R6::)?R6Class\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    # R6 public/private field/method sections
    R6_PUBLIC_SECTION = re.compile(
        r'public\s*=\s*list\s*\((.*?)\)',
        re.DOTALL
    )

    R6_PRIVATE_SECTION = re.compile(
        r'private\s*=\s*list\s*\((.*?)\)',
        re.DOTALL
    )

    R6_ACTIVE_SECTION = re.compile(
        r'active\s*=\s*list\s*\((.*?)\)',
        re.DOTALL
    )

    R6_INHERIT = re.compile(
        r'inherit\s*=\s*(\w+)',
    )

    R6_PORTABLE = re.compile(
        r'portable\s*=\s*(TRUE|FALSE)',
    )

    R6_CLONEABLE = re.compile(
        r'cloneable\s*=\s*(TRUE|FALSE)',
    )

    R6_LOCK_OBJECTS = re.compile(
        r'lock_objects\s*=\s*(TRUE|FALSE)',
    )

    # S4 class patterns
    S4_SET_CLASS = re.compile(
        r'setClass\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    S4_SLOTS = re.compile(
        r'(?:slots|representation)\s*=\s*(?:list|c)\s*\((.*?)\)',
        re.DOTALL
    )

    S4_CONTAINS = re.compile(
        r'contains\s*=\s*(?:["\'](\w+)["\']|c\s*\((.*?)\))',
        re.DOTALL
    )

    S4_VALIDITY = re.compile(
        r'validity\s*=\s*function',
    )

    S4_SEALED = re.compile(
        r'sealed\s*=\s*TRUE',
    )

    # S4 generic and method
    S4_SET_GENERIC = re.compile(
        r'setGeneric\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    S4_SET_METHOD = re.compile(
        r'setMethod\s*\(\s*["\'](\w+)["\']\s*,\s*(?:signature\s*=\s*)?(?:["\'](\w+)["\']|c\s*\((.*?)\))',
        re.MULTILINE
    )

    # R5 Reference class pattern
    R5_SET_REF_CLASS = re.compile(
        r'(\w+)\s*<-\s*setRefClass\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    R5_FIELDS = re.compile(
        r'fields\s*=\s*list\s*\((.*?)\)',
        re.DOTALL
    )

    R5_METHODS = re.compile(
        r'methods\s*=\s*list\s*\((.*?)\)',
        re.DOTALL
    )

    # S3 class construction patterns
    S3_STRUCTURE = re.compile(
        r'structure\s*\(\s*(?:list\s*\(.*?\)|\.Data)\s*,\s*class\s*=\s*["\'](\w+)["\']',
        re.DOTALL
    )

    S3_CLASS_ASSIGN = re.compile(
        r'class\s*\(\s*(\w+)\s*\)\s*<-\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    S3_NEW_CONSTRUCTOR = re.compile(
        r'(?:new_)?(\w+)\s*<-\s*function\s*\(.*?\)\s*\{[^}]*?(?:structure\s*\(|class\s*\()',
        re.DOTALL
    )

    # S7/R7 new_class pattern (R 4.3+)
    S7_NEW_CLASS = re.compile(
        r'(\w+)\s*<-\s*(?:S7::)?new_class\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    S7_PROPERTIES = re.compile(
        r'properties\s*=\s*list\s*\((.*?)\)',
        re.DOTALL
    )

    S7_PARENT = re.compile(
        r'parent\s*=\s*(\w+)',
    )

    # S7 new_generic pattern (R 4.3+)
    S7_NEW_GENERIC = re.compile(
        r'(\w+)\s*<-\s*(?:S7::)?new_generic\s*\(\s*["\'](\w+)["\']\s*(?:,\s*["\'](\w+)["\'])?',
        re.MULTILINE
    )

    # Environment as module pattern
    ENV_PATTERN = re.compile(
        r'(\w+)\s*<-\s*(?:new\.env|rlang::new_environment|as\.environment)\s*\(',
        re.MULTILINE
    )

    # Package/namespace
    PACKAGE_PATTERN = re.compile(
        r'(?:package|packageName)\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    NAMESPACE_PATTERN = re.compile(
        r'(?:library|require)\s*\(\s*["\']?(\w+)["\']?\s*\)',
        re.MULTILINE
    )

    # Roxygen docstring
    ROXYGEN_PATTERN = re.compile(
        r"((?:#'\s+.*\n)+)",
        re.MULTILINE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract all R type definitions from source code."""
        result = {
            "classes": [],
            "generics": [],
            "s4_methods": [],
            "environments": [],
        }

        lines = content.split('\n')

        # Extract R6 classes
        result["classes"].extend(self._extract_r6_classes(content, file_path, lines))

        # Extract S4 classes
        result["classes"].extend(self._extract_s4_classes(content, file_path, lines))

        # Extract S4 generics and methods
        result["generics"].extend(self._extract_s4_generics(content, file_path, lines))
        result["s4_methods"].extend(self._extract_s4_methods(content, file_path, lines))

        # Extract R5 Reference classes
        result["classes"].extend(self._extract_r5_classes(content, file_path, lines))

        # Extract S3 class constructors
        result["classes"].extend(self._extract_s3_classes(content, file_path, lines))

        # Extract S7/R7 classes
        result["classes"].extend(self._extract_s7_classes(content, file_path, lines))

        # Extract S7 generics (new_generic)
        result["generics"].extend(self._extract_s7_generics(content, file_path, lines))

        # Extract environments as modules
        result["environments"].extend(self._extract_environments(content, file_path, lines))

        return result

    def _get_line_number(self, content: str, pos: int) -> int:
        """Get line number for a position in content."""
        return content[:pos].count('\n') + 1

    def _get_roxygen_comment(self, lines: List[str], line_num: int) -> Optional[str]:
        """Extract roxygen docstring above a line."""
        comments = []
        i = line_num - 2  # line_num is 1-based, list is 0-based
        while i >= 0 and lines[i].strip().startswith("#'"):
            comments.insert(0, lines[i].strip()[2:].strip())
            i -= 1
        return '\n'.join(comments) if comments else None

    def _extract_field_assignments(self, section_body: str) -> List[RFieldInfo]:
        """Extract fields from an R6/R5 section body."""
        fields = []
        # Pattern: name = value or name = function(...)
        field_pattern = re.compile(r'(\w+)\s*=\s*(?:function\s*\(|NULL|TRUE|FALSE|["\']|[\d.]+|list\(|c\(|NA)')
        for m in field_pattern.finditer(section_body):
            name = m.group(1)
            if name in ('initialize', 'finalize', 'clone', 'print', 'format'):
                continue  # These are methods, not fields
            is_func = 'function(' in section_body[m.start():m.start() + 100]
            if not is_func:
                fields.append(RFieldInfo(
                    name=name,
                    type="",
                    default_value=section_body[m.end():m.end() + 30].split(',')[0].split(')')[0].strip(),
                ))
        return fields

    def _extract_method_names(self, section_body: str) -> List[str]:
        """Extract method names from an R6/R5 section body."""
        methods = []
        method_pattern = re.compile(r'(\w+)\s*=\s*function\s*\(')
        for m in method_pattern.finditer(section_body):
            methods.append(m.group(1))
        return methods

    def _extract_r6_classes(self, content: str, file_path: str, lines: List[str]) -> List[RClassInfo]:
        """Extract R6 class definitions."""
        classes = []
        for m in self.R6_CLASS_PATTERN.finditer(content):
            var_name = m.group(1)
            class_name = m.group(2)
            line_num = self._get_line_number(content, m.start())

            cls = RClassInfo(
                name=class_name,
                kind="R6",
                file=file_path,
                line_number=line_num,
                doc_comment=self._get_roxygen_comment(lines, line_num),
            )

            # Find the full R6Class(...) block — scan forward for balanced parens
            block_start = m.start()
            block = self._extract_balanced_block(content, block_start, '(', ')')

            if block:
                # Inherit
                inherit_m = self.R6_INHERIT.search(block)
                if inherit_m:
                    cls.parent_class = inherit_m.group(1)

                # Portable
                portable_m = self.R6_PORTABLE.search(block)
                if portable_m:
                    cls.portable = portable_m.group(1) == 'TRUE'

                # Cloneable
                cloneable_m = self.R6_CLONEABLE.search(block)
                if cloneable_m:
                    cls.cloneable = cloneable_m.group(1) == 'TRUE'

                # Lock objects
                lock_m = self.R6_LOCK_OBJECTS.search(block)
                if lock_m:
                    cls.lock_objects = lock_m.group(1) == 'TRUE'

                # Public section
                public_m = re.search(r'public\s*=\s*list\s*\(', block)
                if public_m:
                    pub_block = self._extract_balanced_block(block, public_m.start() + len('public = '), '(', ')')
                    if pub_block:
                        cls.public_methods = self._extract_method_names(pub_block)
                        cls.fields.extend(self._extract_field_assignments(pub_block))
                        cls.methods.extend(cls.public_methods)

                # Private section
                private_m = re.search(r'private\s*=\s*list\s*\(', block)
                if private_m:
                    priv_block = self._extract_balanced_block(block, private_m.start() + len('private = '), '(', ')')
                    if priv_block:
                        cls.private_methods = self._extract_method_names(priv_block)
                        priv_fields = self._extract_field_assignments(priv_block)
                        for f in priv_fields:
                            f.visibility = "private"
                        cls.fields.extend(priv_fields)
                        cls.methods.extend(cls.private_methods)

                # Active bindings
                active_m = re.search(r'active\s*=\s*list\s*\(', block)
                if active_m:
                    act_block = self._extract_balanced_block(block, active_m.start() + len('active = '), '(', ')')
                    if act_block:
                        cls.active_bindings = self._extract_method_names(act_block)

            classes.append(cls)
        return classes

    def _extract_s4_classes(self, content: str, file_path: str, lines: List[str]) -> List[RClassInfo]:
        """Extract S4 class definitions."""
        classes = []
        for m in self.S4_SET_CLASS.finditer(content):
            class_name = m.group(1)
            line_num = self._get_line_number(content, m.start())

            cls = RClassInfo(
                name=class_name,
                kind="S4",
                file=file_path,
                line_number=line_num,
                doc_comment=self._get_roxygen_comment(lines, line_num),
            )

            # Extract full setClass block
            block = self._extract_balanced_block(content, m.start(), '(', ')')
            if block:
                # Slots
                slots_m = self.S4_SLOTS.search(block)
                if slots_m:
                    slots_body = slots_m.group(1)
                    slot_pairs = re.findall(r'(\w+)\s*=\s*["\'](\w+)["\']', slots_body)
                    for name, stype in slot_pairs:
                        cls.slots.append(RFieldInfo(name=name, type=stype))

                # Contains (inheritance)
                contains_m = self.S4_CONTAINS.search(block)
                if contains_m:
                    if contains_m.group(1):
                        cls.parent_class = contains_m.group(1)
                    elif contains_m.group(2):
                        parents = re.findall(r'["\'](\w+)["\']', contains_m.group(2))
                        if parents:
                            cls.parent_class = parents[0]
                            cls.contains = parents[1:]

                # Sealed
                if self.S4_SEALED.search(block):
                    cls.is_sealed = True

                # Validity check
                if self.S4_VALIDITY.search(block):
                    cls.methods.append("validity")

            classes.append(cls)
        return classes

    def _extract_s4_generics(self, content: str, file_path: str, lines: List[str]) -> List[RGenericInfo]:
        """Extract S4 generic function definitions."""
        generics = []
        for m in self.S4_SET_GENERIC.finditer(content):
            name = m.group(1)
            line_num = self._get_line_number(content, m.start())

            # Extract signature if present
            block = self._extract_balanced_block(content, m.start(), '(', ')')
            sig = []
            if block:
                sig_m = re.search(r'signature\s*=\s*(?:c\s*\()?\s*(.*?)(?:\)|$)', block)
                if sig_m:
                    sig = re.findall(r'["\'](\w+)["\']', sig_m.group(1))

            generics.append(RGenericInfo(
                name=name,
                signature=sig,
                file=file_path,
                line_number=line_num,
            ))
        return generics

    def _extract_s4_methods(self, content: str, file_path: str, lines: List[str]) -> List[RS4MethodInfo]:
        """Extract S4 method implementations."""
        methods = []
        for m in self.S4_SET_METHOD.finditer(content):
            name = m.group(1)
            line_num = self._get_line_number(content, m.start())

            target = []
            if m.group(2):
                target = [m.group(2)]
            elif m.group(3):
                target = re.findall(r'["\'](\w+)["\']', m.group(3))

            methods.append(RS4MethodInfo(
                generic_name=name,
                target_classes=target,
                file=file_path,
                line_number=line_num,
            ))
        return methods

    def _extract_r5_classes(self, content: str, file_path: str, lines: List[str]) -> List[RClassInfo]:
        """Extract R5 Reference class definitions."""
        classes = []
        for m in self.R5_SET_REF_CLASS.finditer(content):
            var_name = m.group(1)
            class_name = m.group(2)
            line_num = self._get_line_number(content, m.start())

            cls = RClassInfo(
                name=class_name,
                kind="R5",
                file=file_path,
                line_number=line_num,
                doc_comment=self._get_roxygen_comment(lines, line_num),
            )

            block = self._extract_balanced_block(content, m.start(), '(', ')')
            if block:
                # Fields
                fields_m = self.R5_FIELDS.search(block)
                if fields_m:
                    field_body = fields_m.group(1)
                    field_pairs = re.findall(r'(\w+)\s*=\s*["\'](\w+)["\']', field_body)
                    for name, ftype in field_pairs:
                        cls.fields.append(RFieldInfo(name=name, type=ftype))

                # Methods
                methods_m = self.R5_METHODS.search(block)
                if methods_m:
                    cls.methods = self._extract_method_names(methods_m.group(1))

                # Contains (inheritance)
                contains_m = re.search(r'contains\s*=\s*["\'](\w+)["\']', block)
                if contains_m:
                    cls.parent_class = contains_m.group(1)

            classes.append(cls)
        return classes

    def _extract_s3_classes(self, content: str, file_path: str, lines: List[str]) -> List[RClassInfo]:
        """Extract S3 class construction patterns."""
        classes = []
        seen = set()

        # structure(..., class = "ClassName")
        for m in self.S3_STRUCTURE.finditer(content):
            class_name = m.group(1)
            if class_name in seen:
                continue
            seen.add(class_name)
            line_num = self._get_line_number(content, m.start())
            classes.append(RClassInfo(
                name=class_name,
                kind="S3",
                file=file_path,
                line_number=line_num,
                doc_comment=self._get_roxygen_comment(lines, line_num),
            ))

        # class(x) <- "ClassName"
        for m in self.S3_CLASS_ASSIGN.finditer(content):
            class_name = m.group(2)
            if class_name in seen:
                continue
            seen.add(class_name)
            line_num = self._get_line_number(content, m.start())
            classes.append(RClassInfo(
                name=class_name,
                kind="S3",
                file=file_path,
                line_number=line_num,
                doc_comment=self._get_roxygen_comment(lines, line_num),
            ))

        return classes

    def _extract_s7_classes(self, content: str, file_path: str, lines: List[str]) -> List[RClassInfo]:
        """Extract S7/R7 new_class definitions (R 4.3+)."""
        classes = []
        for m in self.S7_NEW_CLASS.finditer(content):
            var_name = m.group(1)
            class_name = m.group(2)
            line_num = self._get_line_number(content, m.start())

            cls = RClassInfo(
                name=class_name,
                kind="S7",
                file=file_path,
                line_number=line_num,
                doc_comment=self._get_roxygen_comment(lines, line_num),
            )

            block = self._extract_balanced_block(content, m.start(), '(', ')')
            if block:
                # Properties
                props_m = self.S7_PROPERTIES.search(block)
                if props_m:
                    props_body = props_m.group(1)
                    prop_pairs = re.findall(r'(\w+)\s*=\s*(?:class_(\w+)|new_property\s*\(\s*class_(\w+))', props_body)
                    for ppair in prop_pairs:
                        name = ppair[0]
                        ptype = ppair[1] or ppair[2] or ""
                        cls.fields.append(RFieldInfo(name=name, type=ptype))

                # Parent
                parent_m = self.S7_PARENT.search(block)
                if parent_m:
                    cls.parent_class = parent_m.group(1)

            classes.append(cls)
        return classes

    def _extract_s7_generics(self, content: str, file_path: str, lines: List[str]) -> List[RGenericInfo]:
        """Extract S7/R7 new_generic definitions (R 4.3+)."""
        generics = []
        for m in self.S7_NEW_GENERIC.finditer(content):
            var_name = m.group(1)
            generic_name = m.group(2)
            dispatch_arg = m.group(3)  # may be None
            line_num = self._get_line_number(content, m.start())

            sig = [dispatch_arg] if dispatch_arg else []

            generics.append(RGenericInfo(
                name=generic_name,
                kind="S7",
                signature=sig,
                file=file_path,
                line_number=line_num,
            ))
        return generics

    def _extract_environments(self, content: str, file_path: str, lines: List[str]) -> List[REnvironmentInfo]:
        """Extract environments used as modules/namespaces."""
        envs = []
        for m in self.ENV_PATTERN.finditer(content):
            name = m.group(1)
            line_num = self._get_line_number(content, m.start())
            envs.append(REnvironmentInfo(
                name=name,
                file=file_path,
                line_number=line_num,
            ))
        return envs

    def _extract_balanced_block(self, content: str, start: int, open_char: str, close_char: str) -> Optional[str]:
        """Extract a balanced block of text (e.g., matching parentheses)."""
        # Find the first open_char from start
        idx = content.find(open_char, start)
        if idx == -1:
            return None

        depth = 0
        i = idx
        in_string = False
        string_char = None

        while i < len(content):
            c = content[i]

            # Handle string literals
            if c in ('"', "'") and not in_string:
                in_string = True
                string_char = c
            elif c == string_char and in_string:
                # Check for escaped quotes
                if i > 0 and content[i - 1] != '\\':
                    in_string = False
            elif not in_string:
                if c == '#':
                    # Skip to end of line (R comment)
                    newline = content.find('\n', i)
                    if newline == -1:
                        break
                    i = newline
                elif c == open_char:
                    depth += 1
                elif c == close_char:
                    depth -= 1
                    if depth == 0:
                        return content[idx:i + 1]
            i += 1

        return None
