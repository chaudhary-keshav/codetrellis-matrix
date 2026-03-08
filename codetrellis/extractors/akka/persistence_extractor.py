"""
Akka Persistence Extractor - Extracts Akka Persistence definitions.

Extracts:
- EventSourcedBehavior (typed) / PersistentActor (classic)
- DurableStateBehavior
- Commands, Events, State types
- Effect.persist / Effect.none / Effect.stash / Effect.unhandled
- Snapshots (snapshotWhen, retentionCriteria)
- Event adapters (tagging, journal)
- Projections (R2DBC, JDBC, Cassandra, Slick)
- Serialization (Jackson, Protobuf)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class AkkaPersistenceActorInfo:
    """Information about an Akka Persistence actor."""
    actor_name: str = ""
    persistence_id: str = ""
    command_type: str = ""
    event_type: str = ""
    state_type: str = ""
    is_typed: bool = False
    is_durable_state: bool = False
    line_number: int = 0


@dataclass
class AkkaSnapshotInfo:
    """Information about snapshot configuration."""
    every_n_events: int = 0
    keep_n_snapshots: int = 0
    delete_events_on_snapshot: bool = False
    line_number: int = 0


@dataclass
class AkkaProjectionInfo:
    """Information about Akka Projection."""
    projection_name: str = ""
    source_provider: str = ""  # eventsByTag, eventsBySlices, etc.
    offset_store: str = ""  # R2DBC, JDBC, Cassandra, etc.
    handler_type: str = ""
    line_number: int = 0


class AkkaPersistenceExtractor:
    """Extracts Akka Persistence information."""

    # EventSourcedBehavior (Typed)
    EVENT_SOURCED_PATTERN = re.compile(
        r'EventSourcedBehavior\s*(?:\.\s*(?:apply|withEnforcedReplies))?\s*[<\[]'
        r'\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*[>\]]',
        re.MULTILINE
    )

    EVENT_SOURCED_SIMPLE_PATTERN = re.compile(
        r'EventSourcedBehavior\s*(?:\.\s*(?:apply|withEnforcedReplies))?\s*\(',
        re.MULTILINE
    )

    # DurableStateBehavior (Typed)
    DURABLE_STATE_PATTERN = re.compile(
        r'DurableStateBehavior\s*(?:\.\s*(?:apply|withEnforcedReplies))?\s*[<\[]'
        r'\s*(\w+)\s*,\s*(\w+)\s*[>\]]',
        re.MULTILINE
    )

    DURABLE_STATE_SIMPLE_PATTERN = re.compile(
        r'DurableStateBehavior\s*(?:\.\s*(?:apply|withEnforcedReplies))?\s*\(',
        re.MULTILINE
    )

    # PersistentActor (Classic)
    PERSISTENT_ACTOR_PATTERN = re.compile(
        r'(?:extends|with)\s+(?:AbstractPersistentActor|PersistentActor|'
        r'AbstractPersistentActorWithAtLeastOnceDelivery|'
        r'PersistentActorWithAtLeastOnceDelivery)',
        re.MULTILINE
    )

    # PersistenceId
    PERSISTENCE_ID_PATTERN = re.compile(
        r'PersistenceId\s*\.\s*(?:of|ofUniqueId|apply)\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    PERSISTENCE_ID_CLASSIC_PATTERN = re.compile(
        r'(?:override\s+)?(?:def|val)\s+persistenceId\s*(?::\s*String)?\s*=\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    # Effects
    EFFECT_PERSIST_PATTERN = re.compile(
        r'Effect\s*\(\s*\)\s*\.\s*(?:persist|thenRun|thenReply|thenStop|'
        r'thenNoReply|thenUnstashAll|none|unhandled|stash|reply)',
        re.MULTILINE
    )

    CLASSIC_PERSIST_PATTERN = re.compile(
        r'(?:persist|persistAll|persistAsync|persistAllAsync|'
        r'defer|deferAsync)\s*\(',
        re.MULTILINE
    )

    # Snapshots
    SNAPSHOT_EVERY_PATTERN = re.compile(
        r'\.snapshotWhen\s*\(|\.withRetention\s*\(|'
        r'RetentionCriteria\.\s*(?:snapshotEvery|disabled)\s*\(\s*(\d+)\s*,\s*(\d+)',
        re.MULTILINE
    )

    SNAPSHOT_CLASSIC_PATTERN = re.compile(
        r'saveSnapshot\s*\(|'
        r'SnapshotOffer\s*\(|'
        r'deleteSnapshots?\s*\(',
        re.MULTILINE
    )

    # Event adapters / tagging
    EVENT_ADAPTER_PATTERN = re.compile(
        r'EventAdapter|WriteEventAdapter|ReadEventAdapter|'
        r'\.withTagger\s*\(|\.withTaggerForState\s*\(',
        re.MULTILINE
    )

    TAG_PATTERN = re.compile(
        r'["\'](\w+)["\'].*?tag',
        re.MULTILINE | re.IGNORECASE
    )

    # Projections
    PROJECTION_PATTERN = re.compile(
        r'(?:SlickProjection|JdbcProjection|R2dbcProjection|'
        r'CassandraProjection|KafkaProjection)\s*\.\s*'
        r'(?:exactlyOnce|atLeastOnce|atMostOnce|groupedWithin)\s*\(',
        re.MULTILINE
    )

    PROJECTION_SOURCE_PATTERN = re.compile(
        r'(?:EventSourcedProvider|DurableStateStoreProvider)\s*\.\s*'
        r'(?:eventsByTag|eventsBySlices|changesByTag|changesBySlices)\s*\(',
        re.MULTILINE
    )

    PROJECTION_NAME_PATTERN = re.compile(
        r'ProjectionId\s*\.\s*of\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    # Serialization
    SERIALIZATION_PATTERN = re.compile(
        r'(?:akka-serialization-jackson|'
        r'JacksonJsonSerializer|JacksonCborSerializer|'
        r'SerializerWithStringManifest|'
        r'akka\.serialization\.Serializer|'
        r'scalapb\.GeneratedMessage|'
        r'com\.google\.protobuf\.GeneratedMessageV3)',
        re.MULTILINE
    )

    # Recovery
    RECOVERY_PATTERN = re.compile(
        r'Recovery\s*\.\s*(?:default|disabled|create)|'
        r'\.onRecoveryCompleted|'
        r'RecoveryCompleted|'
        r'onRecoveryFailure|'
        r'SnapshotSelectionCriteria',
        re.MULTILINE
    )

    # Multi-DC / Replicated Event Sourcing
    REPLICATED_PATTERN = re.compile(
        r'ReplicatedEventSourcing|ReplicationId|Replica\.\s*apply|'
        r'akka\.persistence\.typed\.ReplicaId',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Akka Persistence information."""
        actors: List[AkkaPersistenceActorInfo] = []
        snapshots: List[AkkaSnapshotInfo] = []
        projections: List[AkkaProjectionInfo] = []
        metadata: Dict[str, Any] = {
            'has_event_adapters': False,
            'has_serialization': False,
            'has_recovery_config': False,
            'has_replicated_es': False,
            'effects_used': [],
            'serializers': [],
        }

        if not content or not content.strip():
            return {'actors': actors, 'snapshots': snapshots,
                    'projections': projections, 'metadata': metadata}

        # Typed EventSourcedBehavior
        for match in self.EVENT_SOURCED_PATTERN.finditer(content):
            actor = AkkaPersistenceActorInfo(
                command_type=match.group(1),
                event_type=match.group(2),
                state_type=match.group(3),
                is_typed=True,
                line_number=content[:match.start()].count('\n') + 1,
            )
            # Look for PersistenceId
            pid_match = self.PERSISTENCE_ID_PATTERN.search(content)
            if pid_match:
                actor.persistence_id = pid_match.group(1)
            actors.append(actor)

        # Simple EventSourcedBehavior (no generics extracted)
        if not actors:
            for match in self.EVENT_SOURCED_SIMPLE_PATTERN.finditer(content):
                actor = AkkaPersistenceActorInfo(
                    is_typed=True,
                    line_number=content[:match.start()].count('\n') + 1,
                )
                pid_match = self.PERSISTENCE_ID_PATTERN.search(content)
                if pid_match:
                    actor.persistence_id = pid_match.group(1)
                actors.append(actor)

        # DurableStateBehavior
        for match in self.DURABLE_STATE_PATTERN.finditer(content):
            actor = AkkaPersistenceActorInfo(
                command_type=match.group(1),
                state_type=match.group(2),
                is_typed=True,
                is_durable_state=True,
                line_number=content[:match.start()].count('\n') + 1,
            )
            pid_match = self.PERSISTENCE_ID_PATTERN.search(content)
            if pid_match:
                actor.persistence_id = pid_match.group(1)
            actors.append(actor)

        # Classic PersistentActor
        for match in self.PERSISTENT_ACTOR_PATTERN.finditer(content):
            actor = AkkaPersistenceActorInfo(
                is_typed=False,
                line_number=content[:match.start()].count('\n') + 1,
            )
            pid_match = self.PERSISTENCE_ID_CLASSIC_PATTERN.search(content)
            if pid_match:
                actor.persistence_id = pid_match.group(1)
            actors.append(actor)

        # Snapshots
        for match in self.SNAPSHOT_EVERY_PATTERN.finditer(content):
            snap = AkkaSnapshotInfo(
                line_number=content[:match.start()].count('\n') + 1,
            )
            if match.group(1):
                snap.every_n_events = int(match.group(1))
            if match.group(2):
                snap.keep_n_snapshots = int(match.group(2))
            snapshots.append(snap)

        if self.SNAPSHOT_CLASSIC_PATTERN.search(content):
            if not snapshots:
                snapshots.append(AkkaSnapshotInfo())

        # Effects
        for match in self.EFFECT_PERSIST_PATTERN.finditer(content):
            effect = match.group(0).rsplit('.', 1)[-1] if '.' in match.group(0) else ""
            if effect and effect not in metadata['effects_used']:
                metadata['effects_used'].append(effect)

        # Projections
        for match in self.PROJECTION_PATTERN.finditer(content):
            proj = AkkaProjectionInfo(
                offset_store=match.group(0).split('Projection')[0],
                line_number=content[:match.start()].count('\n') + 1,
            )
            # Source provider
            src_match = self.PROJECTION_SOURCE_PATTERN.search(content)
            if src_match:
                method = src_match.group(0).rsplit('.', 1)[-1].split('(')[0]
                proj.source_provider = method

            name_match = self.PROJECTION_NAME_PATTERN.search(content)
            if name_match:
                proj.projection_name = name_match.group(1)

            projections.append(proj)

        # Event adapters
        if self.EVENT_ADAPTER_PATTERN.search(content):
            metadata['has_event_adapters'] = True

        # Serialization
        for match in self.SERIALIZATION_PATTERN.finditer(content):
            metadata['has_serialization'] = True
            ser = match.group(0).strip()
            if ser not in metadata['serializers']:
                metadata['serializers'].append(ser)

        # Recovery
        if self.RECOVERY_PATTERN.search(content):
            metadata['has_recovery_config'] = True

        # Replicated Event Sourcing
        if self.REPLICATED_PATTERN.search(content):
            metadata['has_replicated_es'] = True

        return {
            'actors': actors,
            'snapshots': snapshots,
            'projections': projections,
            'metadata': metadata,
        }
