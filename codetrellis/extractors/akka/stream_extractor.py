"""
Akka Stream Extractor - Extracts Akka Streams definitions.

Extracts:
- Source definitions and types
- Flow stages and transformations
- Sink definitions
- Graph DSL usage (RunnableGraph, GraphDSL.create)
- Fan-in/Fan-out stages (Broadcast, Merge, Balance, Zip)
- Materialized values
- Stream attributes (buffer, dispatcher, supervision)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class AkkaStreamStageInfo:
    """Information about a stream stage."""
    stage_type: str = ""  # source, flow, sink
    stage_name: str = ""
    operator: str = ""  # map, filter, mapAsync, groupBy, etc.
    element_type: str = ""
    materialized_type: str = ""
    is_async: bool = False
    parallelism: int = 0
    line_number: int = 0


@dataclass
class AkkaStreamGraphInfo:
    """Information about a stream graph."""
    graph_type: str = ""  # RunnableGraph, ClosedShape, FlowShape, etc.
    fan_in_out: List[str] = field(default_factory=list)  # Broadcast, Merge, Balance, Zip
    stages: List[str] = field(default_factory=list)
    is_closed: bool = False
    line_number: int = 0


class AkkaStreamExtractor:
    """Extracts Akka Streams information."""

    # Source creation
    SOURCE_PATTERN = re.compile(
        r'Source\s*\.\s*(?:from|single|empty|failed|tick|queue|'
        r'actorRef|unfold|unfoldAsync|repeat|cycle|'
        r'fromIterator|fromPublisher|fromCompletionStage|'
        r'maybe|lazySingle|lazyFuture|combine)\s*[(<]',
        re.MULTILINE
    )

    SOURCE_TYPE_PATTERN = re.compile(
        r'Source\s*<\s*(\w+)\s*,\s*(\w+)\s*>',
        re.MULTILINE
    )

    # Flow creation
    FLOW_PATTERN = re.compile(
        r'Flow\s*\.\s*(?:of|create|fromFunction|fromSinkAndSource|'
        r'fromGraph|lazyFlow|lazyInit)\s*[(<]',
        re.MULTILINE
    )

    FLOW_TYPE_PATTERN = re.compile(
        r'Flow\s*<\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*>',
        re.MULTILINE
    )

    # Sink creation
    SINK_PATTERN = re.compile(
        r'Sink\s*\.\s*(?:foreach|fold|reduce|head|last|ignore|'
        r'cancelled|seq|actorRef|queue|fromSubscriber|'
        r'combine|lazySink)\s*[(<]',
        re.MULTILINE
    )

    SINK_TYPE_PATTERN = re.compile(
        r'Sink\s*<\s*(\w+)\s*,\s*(\w+)\s*>',
        re.MULTILINE
    )

    # Stream operators
    OPERATOR_PATTERN = re.compile(
        r'\.\s*(map|flatMapConcat|flatMapMerge|mapAsync|mapAsyncUnordered|'
        r'filter|filterNot|collect|grouped|sliding|take|drop|'
        r'takeWhile|dropWhile|scan|fold|reduce|buffer|'
        r'throttle|delay|batch|expand|conflate|'
        r'groupBy|splitWhen|splitAfter|merge|zip|'
        r'concat|interleave|alsoTo|wireTap|'
        r'via|viaMat|to|toMat|runWith|run|'
        r'mapMaterializedValue|watchTermination|'
        r'recover|recoverWith|recoverWithRetries|'
        r'log|named|addAttributes|async|'
        r'divertTo|statefulMapConcat)\s*[(<]',
        re.MULTILINE
    )

    # Graph DSL
    GRAPH_DSL_PATTERN = re.compile(
        r'GraphDSL\s*\.\s*create\s*\(|'
        r'RunnableGraph\s*\.\s*fromGraph\s*\(',
        re.MULTILINE
    )

    GRAPH_SHAPE_PATTERN = re.compile(
        r'(?:ClosedShape|FlowShape|SinkShape|SourceShape|'
        r'BidiShape|FanInShape|FanOutShape)\b',
        re.MULTILINE
    )

    # Fan-in / Fan-out
    FAN_PATTERN = re.compile(
        r'(?:builder\.add\s*\(\s*)?'
        r'(Broadcast|Merge|Balance|Zip|ZipWith|Unzip|'
        r'MergePreferred|MergePrioritized|Partition|'
        r'Concat|Interleave|OrElse)\s*[.<]',
        re.MULTILINE
    )

    # Materialized value
    MAT_VALUE_PATTERN = re.compile(
        r'Keep\.\s*(left|right|both|none)\s*\(\s*\)|'
        r'\.mapMaterializedValue\s*\(',
        re.MULTILINE
    )

    # Stream attributes
    BUFFER_ATTR_PATTERN = re.compile(
        r'\.buffer\s*\(\s*(\d+)\s*,\s*OverflowStrategy\.(\w+)',
        re.MULTILINE
    )

    ASYNC_PATTERN = re.compile(
        r'\.async\s*\(|\.addAttributes\s*\(.*?async',
        re.MULTILINE
    )

    DISPATCHER_PATTERN = re.compile(
        r'\.withAttributes\s*\(\s*ActorAttributes\.dispatcher\s*\(\s*["\']([^"\']+)',
        re.MULTILINE
    )

    # mapAsync parallelism
    MAP_ASYNC_PATTERN = re.compile(
        r'\.mapAsync(?:Unordered)?\s*\(\s*(\d+)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Akka Streams information."""
        stages: List[AkkaStreamStageInfo] = []
        graphs: List[AkkaStreamGraphInfo] = []
        operators: List[str] = []

        if not content or not content.strip():
            return {'stages': stages, 'graphs': graphs, 'operators': operators}

        # Sources
        for match in self.SOURCE_PATTERN.finditer(content):
            stage = AkkaStreamStageInfo(
                stage_type="source",
                operator=match.group(0).split('.')[1].split('(')[0].strip() if '.' in match.group(0) else "",
                line_number=content[:match.start()].count('\n') + 1,
            )
            stages.append(stage)

        # Flows
        for match in self.FLOW_PATTERN.finditer(content):
            stage = AkkaStreamStageInfo(
                stage_type="flow",
                operator=match.group(0).split('.')[1].split('(')[0].strip() if '.' in match.group(0) else "",
                line_number=content[:match.start()].count('\n') + 1,
            )
            stages.append(stage)

        # Sinks
        for match in self.SINK_PATTERN.finditer(content):
            stage = AkkaStreamStageInfo(
                stage_type="sink",
                operator=match.group(0).split('.')[1].split('(')[0].strip() if '.' in match.group(0) else "",
                line_number=content[:match.start()].count('\n') + 1,
            )
            stages.append(stage)

        # Operators
        for match in self.OPERATOR_PATTERN.finditer(content):
            op = match.group(1)
            operators.append(op)

            # Check for async operators
            if 'Async' in op:
                parallelism = 0
                p_match = self.MAP_ASYNC_PATTERN.search(content[match.start():match.start() + 100])
                if p_match:
                    parallelism = int(p_match.group(1))
                stages.append(AkkaStreamStageInfo(
                    stage_type="operator",
                    operator=op,
                    is_async=True,
                    parallelism=parallelism,
                    line_number=content[:match.start()].count('\n') + 1,
                ))

        # Graph DSL
        for match in self.GRAPH_DSL_PATTERN.finditer(content):
            graph = AkkaStreamGraphInfo(
                graph_type="RunnableGraph" if "RunnableGraph" in match.group(0) else "GraphDSL",
                line_number=content[:match.start()].count('\n') + 1,
            )

            # Find fan-in/fan-out
            for fan in self.FAN_PATTERN.finditer(content):
                graph.fan_in_out.append(fan.group(1))

            # Shapes
            for shape in self.GRAPH_SHAPE_PATTERN.finditer(content):
                if 'ClosedShape' in shape.group(0):
                    graph.is_closed = True

            graphs.append(graph)

        return {'stages': stages, 'graphs': graphs, 'operators': operators}
