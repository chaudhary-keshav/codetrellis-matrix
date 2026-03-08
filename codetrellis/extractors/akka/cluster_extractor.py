"""
Akka Cluster Extractor - Extracts Akka Cluster definitions.

Extracts:
- Cluster membership and roles
- Cluster Sharding (EntityTypeKey, ShardRegion)
- Cluster Singleton
- Distributed Pub/Sub (DistributedPubSub.mediator)
- Cluster-aware routers
- Split-brain resolver
- Distributed Data (CRDTs: GCounter, PNCounter, GSet, ORSet, LWWMap, etc.)
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class AkkaClusterShardingInfo:
    """Information about cluster sharding setup."""
    entity_type_key: str = ""
    entity_class: str = ""
    shard_region_name: str = ""
    number_of_shards: int = 0
    role: str = ""
    is_typed: bool = False
    line_number: int = 0


@dataclass
class AkkaClusterSingletonInfo:
    """Information about cluster singleton."""
    singleton_name: str = ""
    actor_class: str = ""
    role: str = ""
    is_typed: bool = False
    line_number: int = 0


@dataclass
class AkkaClusterPubSubInfo:
    """Information about distributed pub/sub."""
    topic: str = ""
    message_class: str = ""
    is_subscribe: bool = False
    is_publish: bool = False
    line_number: int = 0


class AkkaClusterExtractor:
    """Extracts Akka Cluster information."""

    # Cluster join/membership
    CLUSTER_JOIN_PATTERN = re.compile(
        r'Cluster\s*\(\s*(?:system|context\.system)\s*\)\s*\.\s*'
        r'(?:join|manager|subscriptions|selfMember|state)',
        re.MULTILINE
    )

    CLUSTER_ROLE_PATTERN = re.compile(
        r'\.withRole\s*\(\s*["\'](\w+)["\']\s*\)|'
        r'hasRole\s*\(\s*["\'](\w+)["\']\s*\)|'
        r'akka\.cluster\.roles\s*=\s*\[\s*["\'](\w+)',
        re.MULTILINE
    )

    # Cluster Sharding — typed
    SHARDING_TYPED_PATTERN = re.compile(
        r'ClusterSharding\s*\(\s*(?:system|context\.system)\s*\)\s*\.\s*init\s*\(',
        re.MULTILINE
    )

    ENTITY_TYPE_KEY_PATTERN = re.compile(
        r'EntityTypeKey\s*\[\s*(\w+)\s*\]\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    ENTITY_PATTERN = re.compile(
        r'Entity\s*\(\s*(\w+)\s*\)\s*\{',
        re.MULTILINE
    )

    # Cluster Sharding — classic
    SHARDING_CLASSIC_PATTERN = re.compile(
        r'ClusterSharding\s*\(\s*system\s*\)\s*\.\s*start\s*\(\s*'
        r'typeName\s*=\s*["\'](\w+)["\']\s*,',
        re.MULTILINE
    )

    SHARD_REGION_PATTERN = re.compile(
        r'ClusterSharding\s*\(\s*system\s*\)\s*\.\s*shardRegion\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    NUMBER_OF_SHARDS_PATTERN = re.compile(
        r'numberOfShards\s*=\s*(\d+)|'
        r'number-of-shards\s*=\s*(\d+)',
        re.MULTILINE
    )

    # Cluster Singleton — typed
    SINGLETON_TYPED_PATTERN = re.compile(
        r'ClusterSingleton\s*\(\s*(?:system|context\.system)\s*\)\s*\.\s*init\s*\(',
        re.MULTILINE
    )

    SINGLETON_OF_PATTERN = re.compile(
        r'SingletonActor\s*\.\s*of\s*\(\s*(\w+)\s*\.\s*create\s*\([^)]*\)\s*,\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    # Cluster Singleton — classic
    SINGLETON_CLASSIC_PATTERN = re.compile(
        r'ClusterSingletonManager\.\s*props\s*\(|'
        r'ClusterSingletonProxy\.\s*props\s*\(',
        re.MULTILINE
    )

    # Distributed Pub/Sub
    PUBSUB_MEDIATOR_PATTERN = re.compile(
        r'DistributedPubSub\s*\(\s*(?:system|context\.system)\s*\)\s*\.\s*mediator',
        re.MULTILINE
    )

    PUBSUB_SUBSCRIBE_PATTERN = re.compile(
        r'DistributedPubSubMediator\.\s*Subscribe\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    PUBSUB_PUBLISH_PATTERN = re.compile(
        r'DistributedPubSubMediator\.\s*Publish\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    # Typed Pub/Sub (Akka 2.6+)
    TYPED_PUBSUB_PATTERN = re.compile(
        r'PubSub\s*\.\s*(?:of|multiOf)\s*\[\s*(\w+)\s*\]\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    # Cluster routers
    CLUSTER_ROUTER_PATTERN = re.compile(
        r'(?:ClusterRouterGroup|ClusterRouterPool|'
        r'Routers\.group|Routers\.pool)\s*[(<]',
        re.MULTILINE
    )

    # Split brain resolver
    SBR_PATTERN = re.compile(
        r'split-brain-resolver|'
        r'akka\.cluster\.downing-provider-class|'
        r'SplitBrainResolverSettings|'
        r'keep-majority|keep-oldest|keep-referee|down-all|'
        r'static-quorum|lease-majority',
        re.MULTILINE
    )

    # Distributed Data (CRDTs)
    DDATA_REPLICATOR_PATTERN = re.compile(
        r'DistributedData\s*\(\s*(?:system|context\.system)\s*\)|'
        r'Replicator\.\s*(?:Get|Update|Subscribe|Changed|GetSuccess)',
        re.MULTILINE
    )

    CRDT_PATTERN = re.compile(
        r'\b(GCounter|PNCounter|GSet|ORSet|ORMap|LWWMap|'
        r'LWWRegister|Flag|PNCounterMap|ORMultiMap)\b',
        re.MULTILINE
    )

    CRDT_KEY_PATTERN = re.compile(
        r'(\w+Key)\s*\[\s*(\w+)\s*\]\s*\(\s*["\'](\w+)["\']',
        re.MULTILINE
    )

    # Receptionist (Akka Typed)
    RECEPTIONIST_PATTERN = re.compile(
        r'ServiceKey\s*\[\s*(\w+)\s*\]\s*\(\s*["\'](\w+)["\']\s*\)|'
        r'context\.system\.receptionist|'
        r'Receptionist\.\s*(?:Register|Find|Listing)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract Akka Cluster information."""
        sharding: List[AkkaClusterShardingInfo] = []
        singletons: List[AkkaClusterSingletonInfo] = []
        pubsub: List[AkkaClusterPubSubInfo] = []
        metadata: Dict[str, Any] = {
            'roles': [],
            'has_ddata': False,
            'crdts': [],
            'has_sbr': False,
            'has_cluster_routers': False,
            'has_receptionist': False,
        }

        if not content or not content.strip():
            return {'sharding': sharding, 'singletons': singletons,
                    'pubsub': pubsub, 'metadata': metadata}

        # Roles
        for match in self.CLUSTER_ROLE_PATTERN.finditer(content):
            role = match.group(1) or match.group(2) or match.group(3)
            if role and role not in metadata['roles']:
                metadata['roles'].append(role)

        # Typed Sharding
        for match in self.SHARDING_TYPED_PATTERN.finditer(content):
            info = AkkaClusterShardingInfo(
                is_typed=True,
                line_number=content[:match.start()].count('\n') + 1,
            )
            sharding.append(info)

        # EntityTypeKey
        for match in self.ENTITY_TYPE_KEY_PATTERN.finditer(content):
            info = AkkaClusterShardingInfo(
                entity_class=match.group(1),
                entity_type_key=match.group(2),
                is_typed=True,
                line_number=content[:match.start()].count('\n') + 1,
            )
            sharding.append(info)

        # Classic Sharding
        for match in self.SHARDING_CLASSIC_PATTERN.finditer(content):
            info = AkkaClusterShardingInfo(
                shard_region_name=match.group(1),
                is_typed=False,
                line_number=content[:match.start()].count('\n') + 1,
            )
            sharding.append(info)

        # Number of shards
        shard_match = self.NUMBER_OF_SHARDS_PATTERN.search(content)
        if shard_match and sharding:
            sharding[-1].number_of_shards = int(shard_match.group(1) or shard_match.group(2))

        # Typed Singleton
        for match in self.SINGLETON_TYPED_PATTERN.finditer(content):
            singletons.append(AkkaClusterSingletonInfo(
                is_typed=True,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        for match in self.SINGLETON_OF_PATTERN.finditer(content):
            singletons.append(AkkaClusterSingletonInfo(
                actor_class=match.group(1),
                singleton_name=match.group(2),
                is_typed=True,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Classic Singleton
        for match in self.SINGLETON_CLASSIC_PATTERN.finditer(content):
            singletons.append(AkkaClusterSingletonInfo(
                is_typed=False,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Distributed Pub/Sub
        for match in self.PUBSUB_SUBSCRIBE_PATTERN.finditer(content):
            pubsub.append(AkkaClusterPubSubInfo(
                topic=match.group(1),
                is_subscribe=True,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        for match in self.PUBSUB_PUBLISH_PATTERN.finditer(content):
            pubsub.append(AkkaClusterPubSubInfo(
                topic=match.group(1),
                is_publish=True,
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # Typed Pub/Sub
        for match in self.TYPED_PUBSUB_PATTERN.finditer(content):
            pubsub.append(AkkaClusterPubSubInfo(
                message_class=match.group(1),
                topic=match.group(2),
                line_number=content[:match.start()].count('\n') + 1,
            ))

        # DData
        if self.DDATA_REPLICATOR_PATTERN.search(content):
            metadata['has_ddata'] = True

        for match in self.CRDT_PATTERN.finditer(content):
            crdt = match.group(1)
            if crdt not in metadata['crdts']:
                metadata['crdts'].append(crdt)

        # SBR
        if self.SBR_PATTERN.search(content):
            metadata['has_sbr'] = True

        # Cluster routers
        if self.CLUSTER_ROUTER_PATTERN.search(content):
            metadata['has_cluster_routers'] = True

        # Receptionist
        if self.RECEPTIONIST_PATTERN.search(content):
            metadata['has_receptionist'] = True

        return {
            'sharding': sharding,
            'singletons': singletons,
            'pubsub': pubsub,
            'metadata': metadata,
        }
