"""
Apache Camel Processor Extractor - Extracts processors and EIP patterns.

Extracts:
- Processor implementations
- Bean references and method calls
- EIP patterns (split, aggregate, filter, multicast, recipientList, etc.)
- Content-based router (choice/when/otherwise)
- Message transformation (transform, setBody, setHeader)
- Enrich patterns (enrich, pollEnrich)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class CamelProcessorInfo:
    """Information about a Camel processor."""
    class_name: str = ""
    processor_type: str = ""  # Processor, bean, method
    method_name: str = ""
    line_number: int = 0


@dataclass
class CamelEIPInfo:
    """Information about an EIP (Enterprise Integration Pattern) usage."""
    pattern_name: str = ""  # split, aggregate, filter, multicast, etc.
    expression_type: str = ""  # simple, xpath, jsonpath, method, header, body
    expression: str = ""
    strategy: str = ""  # for aggregation strategy
    parallel: bool = False
    streaming: bool = False
    line_number: int = 0


class CamelProcessorExtractor:
    """Extracts processor and EIP pattern information."""

    # Processor implementation
    PROCESSOR_PATTERN = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+implements\s+(?:[\w,\s]*\b)?Processor\b',
        re.DOTALL
    )

    # Bean reference
    BEAN_PATTERN = re.compile(
        r'\.bean\s*\(\s*(?:(\w+)\.class|["\'](\w+)["\'])'
        r'(?:\s*,\s*["\'](\w+)["\'])?\s*\)',
        re.MULTILINE
    )

    # Process (inline)
    PROCESS_PATTERN = re.compile(
        r'\.process\s*\(\s*(?:new\s+(\w+)|(\w+))\s*(?:\(\))?',
        re.MULTILINE
    )

    # EIP Patterns
    SPLIT_PATTERN = re.compile(
        r'\.split\s*\(\s*(?:body\(\)|header\(["\'](\w+)["\']\)|'
        r'simple\(["\']([^"\']+)["\']\)|'
        r'xpath\(["\']([^"\']+)["\']\)|'
        r'jsonpath\(["\']([^"\']+)["\']\)|'
        r'method\((\w+))',
        re.MULTILINE
    )

    AGGREGATE_PATTERN = re.compile(
        r'\.aggregate\s*\(\s*(?:header\(["\'](\w+)["\']\)|'
        r'simple\(["\']([^"\']+)["\']\)|'
        r'constant\(["\']([^"\']+)["\']\))',
        re.MULTILINE
    )

    AGGREGATION_STRATEGY_PATTERN = re.compile(
        r'\.aggregationStrategy\s*\(\s*(?:new\s+)?(\w+)',
        re.MULTILINE
    )

    FILTER_PATTERN = re.compile(
        r'\.filter\s*\(\s*(?:simple\(["\']([^"\']+)["\']\)|'
        r'header\(["\'](\w+)["\']\)|'
        r'body\(\)|'
        r'xpath\(["\']([^"\']+)["\']\)|'
        r'method\((\w+))',
        re.MULTILINE
    )

    CHOICE_PATTERN = re.compile(r'\.choice\s*\(', re.MULTILINE)
    WHEN_PATTERN = re.compile(
        r'\.when\s*\(\s*(?:simple\(["\']([^"\']+)["\']\)|'
        r'header\(["\'](\w+)["\']\)|'
        r'body\(\)|'
        r'xpath\(["\']([^"\']+)["\']\))',
        re.MULTILINE
    )
    OTHERWISE_PATTERN = re.compile(r'\.otherwise\s*\(', re.MULTILINE)

    MULTICAST_PATTERN = re.compile(r'\.multicast\s*\(', re.MULTILINE)
    RECIPIENT_LIST_PATTERN = re.compile(
        r'\.recipientList\s*\(\s*(?:header\(["\'](\w+)["\']\)|'
        r'simple\(["\']([^"\']+)["\']\))',
        re.MULTILINE
    )
    ROUTING_SLIP_PATTERN = re.compile(
        r'\.routingSlip\s*\(\s*(?:header\(["\'](\w+)["\']\))',
        re.MULTILINE
    )
    DYNAMIC_ROUTER_PATTERN = re.compile(
        r'\.dynamicRouter\s*\(\s*method\((\w+)',
        re.MULTILINE
    )

    # Message transformation
    TRANSFORM_PATTERN = re.compile(
        r'\.transform\s*\(\s*(?:simple\(["\']([^"\']+)["\']\)|body\(\))',
        re.MULTILINE
    )
    SET_BODY_PATTERN = re.compile(
        r'\.setBody\s*\(\s*(?:simple\(["\']([^"\']+)["\']\)|constant\(["\']([^"\']+)["\']\))',
        re.MULTILINE
    )
    SET_HEADER_PATTERN = re.compile(
        r'\.setHeader\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # Enrich
    ENRICH_PATTERN = re.compile(
        r'\.enrich\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )
    POLL_ENRICH_PATTERN = re.compile(
        r'\.pollEnrich\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )

    # Parallel/streaming flags
    PARALLEL_PROCESSING_PATTERN = re.compile(
        r'\.parallelProcessing\s*\(',
        re.MULTILINE
    )
    STREAMING_PATTERN = re.compile(
        r'\.streaming\s*\(',
        re.MULTILINE
    )

    # Idempotent consumer
    IDEMPOTENT_PATTERN = re.compile(
        r'\.idempotentConsumer\s*\(',
        re.MULTILINE
    )

    # Throttle
    THROTTLE_PATTERN = re.compile(
        r'\.throttle\s*\(\s*(\d+|simple\([^)]+\))',
        re.MULTILINE
    )

    # Delay
    DELAY_PATTERN = re.compile(
        r'\.delay\s*\(\s*(\d+)',
        re.MULTILINE
    )

    # Circuit breaker
    CIRCUIT_BREAKER_PATTERN = re.compile(
        r'\.circuitBreaker\s*\(',
        re.MULTILINE
    )

    # Saga
    SAGA_PATTERN = re.compile(
        r'\.saga\s*\(',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract processor and EIP information."""
        processors: List[CamelProcessorInfo] = []
        eip_patterns: List[CamelEIPInfo] = []

        if not content or not content.strip():
            return {'processors': processors, 'eip_patterns': eip_patterns}

        # Processor implementations
        for match in self.PROCESSOR_PATTERN.finditer(content):
            processors.append(CamelProcessorInfo(
                class_name=match.group(1),
                processor_type="Processor",
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Bean references
        for match in self.BEAN_PATTERN.finditer(content):
            processors.append(CamelProcessorInfo(
                class_name=match.group(1) or match.group(2) or "",
                processor_type="bean",
                method_name=match.group(3) or "",
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Process references
        for match in self.PROCESS_PATTERN.finditer(content):
            processors.append(CamelProcessorInfo(
                class_name=match.group(1) or match.group(2) or "",
                processor_type="process",
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # EIP patterns
        eip_detectors = [
            ('split', self.SPLIT_PATTERN),
            ('aggregate', self.AGGREGATE_PATTERN),
            ('filter', self.FILTER_PATTERN),
            ('choice', self.CHOICE_PATTERN),
            ('multicast', self.MULTICAST_PATTERN),
            ('recipientList', self.RECIPIENT_LIST_PATTERN),
            ('routingSlip', self.ROUTING_SLIP_PATTERN),
            ('dynamicRouter', self.DYNAMIC_ROUTER_PATTERN),
            ('enrich', self.ENRICH_PATTERN),
            ('pollEnrich', self.POLL_ENRICH_PATTERN),
            ('idempotentConsumer', self.IDEMPOTENT_PATTERN),
            ('throttle', self.THROTTLE_PATTERN),
            ('circuitBreaker', self.CIRCUIT_BREAKER_PATTERN),
            ('saga', self.SAGA_PATTERN),
        ]

        for pattern_name, pattern in eip_detectors:
            for match in pattern.finditer(content):
                eip = CamelEIPInfo(
                    pattern_name=pattern_name,
                    line_number=content[:match.start()].count('\n') + 1,
                )

                # Check for parallel/streaming in nearby context
                context = content[match.end():match.end() + 200]
                if self.PARALLEL_PROCESSING_PATTERN.search(context):
                    eip.parallel = True
                if self.STREAMING_PATTERN.search(context):
                    eip.streaming = True

                eip_patterns.append(eip)

        return {'processors': processors, 'eip_patterns': eip_patterns}
