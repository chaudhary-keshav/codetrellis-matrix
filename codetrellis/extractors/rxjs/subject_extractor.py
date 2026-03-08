"""
RxJS Subject Extractor — Subject, BehaviorSubject, ReplaySubject, AsyncSubject.

Extracts:
- Subject creation and usage
- BehaviorSubject with initial values
- ReplaySubject with buffer size/time
- AsyncSubject usage
- Subject.next(), .error(), .complete() calls
- Subject as Observable (asObservable())
- WebSocketSubject
- Subject multicasting patterns

Supports RxJS v5, v6, v7.
v4.77: Full RxJS subject support.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class RxjsSubjectInfo:
    """A Subject instance."""
    name: str = ""
    file: str = ""
    line_number: int = 0
    subject_type: str = ""            # 'Subject', 'BehaviorSubject', 'ReplaySubject', 'AsyncSubject', 'WebSocketSubject'
    type_param: str = ""              # Generic type
    initial_value: str = ""           # For BehaviorSubject
    buffer_size: str = ""             # For ReplaySubject
    window_time: str = ""             # For ReplaySubject
    has_as_observable: bool = False
    next_count: int = 0
    has_error_call: bool = False
    has_complete_call: bool = False


@dataclass
class RxjsSubjectEmissionInfo:
    """A Subject emission (.next(), .error(), .complete())."""
    subject_name: str = ""
    file: str = ""
    line_number: int = 0
    emission_type: str = ""           # 'next', 'error', 'complete'


class RxjsSubjectExtractor:
    """
    Extracts RxJS Subject patterns from source code.
    """

    # Subject constructors
    SUBJECT_PATTERN = re.compile(
        r'(?:(?:const|let|var|private|protected|public|readonly)\s+)+(\w+)\s*(?::\s*(?:Subject|BehaviorSubject|ReplaySubject|AsyncSubject|WebSocketSubject)(?:<([^>]*)>)?)?\s*=\s*new\s+(Subject|BehaviorSubject|ReplaySubject|AsyncSubject|WebSocketSubject)\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # Simpler Subject patterns (without type annotations in declaration)
    SUBJECT_SIMPLE = re.compile(
        r'(?:(?:const|let|var)\s+)?(\w+)\s*=\s*new\s+(Subject|BehaviorSubject|ReplaySubject|AsyncSubject|WebSocketSubject)\s*(?:<([^>]*)>)?\s*\(([^)]*)\)',
        re.MULTILINE
    )

    # Class field Subject (TypeScript)
    CLASS_SUBJECT = re.compile(
        r'(?:private|protected|public|readonly)\s+(\w+)\s*(?::\s*(Subject|BehaviorSubject|ReplaySubject|AsyncSubject|WebSocketSubject)(?:<([^>]*)>)?)\s*(?:=\s*new\s+(?:Subject|BehaviorSubject|ReplaySubject|AsyncSubject|WebSocketSubject)\s*(?:<[^>]*>)?\s*\(([^)]*)\))?',
        re.MULTILINE
    )

    # .next() call
    NEXT_CALL = re.compile(
        r'(\w+)\.next\s*\(',
    )

    # .error() call
    ERROR_CALL = re.compile(
        r'(\w+)\.error\s*\(',
    )

    # .complete() call
    COMPLETE_CALL = re.compile(
        r'(\w+)\.complete\s*\(\s*\)',
    )

    # .asObservable()
    AS_OBSERVABLE = re.compile(
        r'(\w+)\.asObservable\s*\(',
    )

    def extract(self, content: str, file_path: str = "") -> dict:
        """Extract all RxJS subject constructs."""
        subjects = []
        emissions = []
        seen_subjects = {}

        # Collect emission data first
        next_counts = {}
        error_vars = set()
        complete_vars = set()
        as_observable_vars = set()

        for match in self.NEXT_CALL.finditer(content):
            var = match.group(1)
            next_counts[var] = next_counts.get(var, 0) + 1
            line_num = content[:match.start()].count('\n') + 1
            emissions.append(RxjsSubjectEmissionInfo(
                subject_name=var,
                file=file_path,
                line_number=line_num,
                emission_type='next',
            ))

        for match in self.ERROR_CALL.finditer(content):
            error_vars.add(match.group(1))
            line_num = content[:match.start()].count('\n') + 1
            emissions.append(RxjsSubjectEmissionInfo(
                subject_name=match.group(1),
                file=file_path,
                line_number=line_num,
                emission_type='error',
            ))

        for match in self.COMPLETE_CALL.finditer(content):
            complete_vars.add(match.group(1))
            line_num = content[:match.start()].count('\n') + 1
            emissions.append(RxjsSubjectEmissionInfo(
                subject_name=match.group(1),
                file=file_path,
                line_number=line_num,
                emission_type='complete',
            ))

        for match in self.AS_OBSERVABLE.finditer(content):
            as_observable_vars.add(match.group(1))

        # ── Subject constructors ────────────────────────────────
        for match in self.SUBJECT_SIMPLE.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            name = match.group(1)
            subject_type = match.group(2)
            type_param = match.group(3) or ''
            args = match.group(4).strip()

            initial_value = ''
            buffer_size = ''
            window_time = ''

            if subject_type == 'BehaviorSubject' and args:
                initial_value = args.split(',')[0].strip()
            elif subject_type == 'ReplaySubject' and args:
                parts = [p.strip() for p in args.split(',')]
                if parts:
                    buffer_size = parts[0]
                if len(parts) > 1:
                    window_time = parts[1]

            if name not in seen_subjects:
                seen_subjects[name] = True
                subjects.append(RxjsSubjectInfo(
                    name=name,
                    file=file_path,
                    line_number=line_num,
                    subject_type=subject_type,
                    type_param=type_param,
                    initial_value=initial_value,
                    buffer_size=buffer_size,
                    window_time=window_time,
                    has_as_observable=name in as_observable_vars,
                    next_count=next_counts.get(name, 0),
                    has_error_call=name in error_vars,
                    has_complete_call=name in complete_vars,
                ))

        # ── Class field subjects (TS) ───────────────────────────
        for match in self.CLASS_SUBJECT.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            name = match.group(1)
            subject_type = match.group(2)
            type_param = match.group(3) or ''
            args = (match.group(4) or '').strip()

            initial_value = ''
            buffer_size = ''

            if subject_type == 'BehaviorSubject' and args:
                initial_value = args.split(',')[0].strip()
            elif subject_type == 'ReplaySubject' and args:
                buffer_size = args.split(',')[0].strip()

            if name not in seen_subjects:
                seen_subjects[name] = True
                subjects.append(RxjsSubjectInfo(
                    name=name,
                    file=file_path,
                    line_number=line_num,
                    subject_type=subject_type,
                    type_param=type_param,
                    initial_value=initial_value,
                    buffer_size=buffer_size,
                    has_as_observable=name in as_observable_vars,
                    next_count=next_counts.get(name, 0),
                    has_error_call=name in error_vars,
                    has_complete_call=name in complete_vars,
                ))

        return {
            'subjects': subjects[:50],
            'emissions': emissions[:100],
        }
