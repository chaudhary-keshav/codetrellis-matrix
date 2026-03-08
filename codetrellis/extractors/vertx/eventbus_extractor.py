"""
Vert.x Event Bus Extractor v1.0

Extracts Vert.x event bus patterns including consumers, publishers, request-reply, codecs.
Covers Vert.x 2.x through 4.x.

Part of CodeTrellis v4.95 - Vert.x Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class VertxEventBusConsumerInfo:
    """An event bus consumer registration."""
    address: str = ""
    handler_name: str = ""
    is_local: bool = False  # localConsumer vs consumer
    file: str = ""
    line_number: int = 0


@dataclass
class VertxEventBusPublisherInfo:
    """An event bus publish/send call."""
    address: str = ""
    publish_type: str = ""  # publish, send, request
    file: str = ""
    line_number: int = 0


@dataclass
class VertxCodecInfo:
    """A custom message codec registration."""
    codec_name: str = ""
    codec_class: str = ""
    file: str = ""
    line_number: int = 0


class VertxEventBusExtractor:
    """Extracts Vert.x event bus consumers, publishers, and codecs."""

    # Event bus consumer: vertx.eventBus().consumer("address", handler) / localConsumer
    CONSUMER_PATTERN = re.compile(
        r'(?:eventBus|eb)\s*(?:\(\))?\s*\.\s*(consumer|localConsumer)\s*\(\s*"([^"]+)"',
        re.MULTILINE
    )

    # Event bus publish: vertx.eventBus().publish("address", message)
    PUBLISH_PATTERN = re.compile(
        r'(?:eventBus|eb)\s*(?:\(\))?\s*\.\s*(publish|send|request)\s*\(\s*"([^"]+)"',
        re.MULTILINE
    )

    # Message codec: eventBus.registerCodec(new MyCodec())
    CODEC_PATTERN = re.compile(
        r'(?:eventBus|eb)\s*(?:\(\))?\s*\.\s*registerCodec\s*\(\s*new\s+(\w+)',
        re.MULTILINE
    )

    # Default codec: eventBus.registerDefaultCodec(MyClass.class, new MyCodec())
    DEFAULT_CODEC_PATTERN = re.compile(
        r'(?:eventBus|eb)\s*(?:\(\))?\s*\.\s*registerDefaultCodec\s*\(\s*(\w+)\.class\s*,\s*new\s+(\w+)',
        re.MULTILINE
    )

    # Address constant definitions: public static final String ADDRESS = "..."
    ADDRESS_CONST_PATTERN = re.compile(
        r'(?:public\s+)?(?:static\s+)?(?:final\s+)?String\s+(\w+(?:ADDRESS|ADDR|TOPIC|CHANNEL)\w*)\s*=\s*"([^"]+)"',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract event bus consumers, publishers, and codecs."""
        result = {
            'consumers': [],
            'publishers': [],
            'codecs': [],
        }

        if not content:
            return result

        # Extract consumers
        for m in self.CONSUMER_PATTERN.finditer(content):
            consumer_type = m.group(1)
            address = m.group(2)
            line = content[:m.start()].count('\n') + 1
            result['consumers'].append(VertxEventBusConsumerInfo(
                address=address,
                is_local=(consumer_type == 'localConsumer'),
                file=file_path,
                line_number=line,
            ))

        # Extract publishers/senders
        for m in self.PUBLISH_PATTERN.finditer(content):
            pub_type = m.group(1)
            address = m.group(2)
            line = content[:m.start()].count('\n') + 1
            result['publishers'].append(VertxEventBusPublisherInfo(
                address=address,
                publish_type=pub_type,
                file=file_path,
                line_number=line,
            ))

        # Extract codecs
        for m in self.CODEC_PATTERN.finditer(content):
            codec_class = m.group(1)
            line = content[:m.start()].count('\n') + 1
            result['codecs'].append(VertxCodecInfo(
                codec_class=codec_class,
                file=file_path,
                line_number=line,
            ))

        for m in self.DEFAULT_CODEC_PATTERN.finditer(content):
            codec_class = m.group(2)
            line = content[:m.start()].count('\n') + 1
            result['codecs'].append(VertxCodecInfo(
                codec_name=f"default:{m.group(1)}",
                codec_class=codec_class,
                file=file_path,
                line_number=line,
            ))

        return result
