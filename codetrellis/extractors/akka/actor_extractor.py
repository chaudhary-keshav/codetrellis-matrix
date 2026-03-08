"""
Akka Actor Extractor - Extracts actor definitions, messages, and supervision.

Extracts:
- Classic actors (extends AbstractActor, UntypedAbstractActor)
- Typed actors (extends AbstractBehavior, Behavior<T>)
- Message protocol definitions (sealed interfaces/classes)
- Supervision strategies (OneForOneStrategy, AllForOneStrategy, BackoffSupervisor)
- Actor lifecycle (preStart, postStop, preRestart, postRestart)
- Props and Behavior factories
- Stash, timers, and ask patterns
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class AkkaMessageInfo:
    """Information about an actor message type."""
    class_name: str = ""
    message_type: str = ""  # command, event, response, internal
    parent_protocol: str = ""  # The sealed trait/interface it belongs to
    fields: List[str] = field(default_factory=list)
    is_serializable: bool = False
    line_number: int = 0


@dataclass
class AkkaSupervisionInfo:
    """Information about a supervision strategy."""
    strategy_type: str = ""  # OneForOneStrategy, AllForOneStrategy, BackoffSupervisor
    max_retries: int = 0
    within_time: str = ""
    directives: List[str] = field(default_factory=list)  # Resume, Restart, Stop, Escalate
    line_number: int = 0


@dataclass
class AkkaActorInfo:
    """Information about an Akka actor."""
    class_name: str = ""
    actor_type: str = ""  # classic, typed, abstract_behavior
    message_type: str = ""  # The type parameter for typed actors
    behaviors: List[str] = field(default_factory=list)  # behavior factory method names
    message_handlers: List[str] = field(default_factory=list)
    supervision: Optional[AkkaSupervisionInfo] = None
    has_stash: bool = False
    has_timers: bool = False
    lifecycle_hooks: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)  # spawned child actors
    line_number: int = 0


class AkkaActorExtractor:
    """Extracts Akka actor information from Java/Scala source code."""

    # Classic actor
    CLASSIC_ACTOR_PATTERN = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+extends\s+'
        r'(?:AbstractActor|UntypedAbstractActor|AbstractActorWithStash|'
        r'AbstractActorWithTimers|AbstractLoggingActor)',
        re.MULTILINE
    )

    # Typed actor (Java)
    TYPED_ACTOR_PATTERN = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+extends\s+'
        r'AbstractBehavior\s*<\s*(\w+)\s*>',
        re.MULTILINE
    )

    # Typed actor (Scala style in Java)
    BEHAVIOR_FACTORY_PATTERN = re.compile(
        r'(?:public\s+)?static\s+Behavior\s*<\s*(\w+)\s*>\s+(\w+)\s*\(',
        re.MULTILINE
    )

    # Behavior.receive / Behaviors.receive
    BEHAVIOR_RECEIVE_PATTERN = re.compile(
        r'(?:Behaviors?\.)(?:receive|receiveMessage|setup|supervise|'
        r'withTimers|withStash|same|stopped|empty|ignore|unhandled)',
        re.MULTILINE
    )

    # Message handling (classic)
    RECEIVE_BUILDER_PATTERN = re.compile(
        r'receiveBuilder\s*\(\s*\)\s*'
        r'(?:\.match\s*\(\s*(\w+)\.class)?',
        re.DOTALL
    )

    MATCH_PATTERN = re.compile(
        r'\.match\s*\(\s*(\w+)\.class',
        re.MULTILINE
    )

    # Message handling (typed)
    ON_MESSAGE_PATTERN = re.compile(
        r'\.onMessage\s*\(\s*(\w+)\.class\s*,\s*(?:this::)?(\w+)',
        re.MULTILINE
    )

    ON_SIGNAL_PATTERN = re.compile(
        r'\.onSignal\s*\(\s*(\w+)\.class',
        re.MULTILINE
    )

    # Supervision strategies
    ONE_FOR_ONE_PATTERN = re.compile(
        r'new\s+OneForOneStrategy\s*\(\s*(\d+)\s*,\s*'
        r'Duration\.create\s*\(\s*["\']?([^"\')\s]+)',
        re.DOTALL
    )

    ALL_FOR_ONE_PATTERN = re.compile(
        r'new\s+AllForOneStrategy\s*\(\s*(\d+)',
        re.MULTILINE
    )

    BACKOFF_SUPERVISOR_PATTERN = re.compile(
        r'BackoffSupervisor\.\w+\s*\(|BackoffOpts\.\w+',
        re.MULTILINE
    )

    SUPERVISION_DIRECTIVE_PATTERN = re.compile(
        r'SupervisorStrategy\.\s*(resume|restart|stop|escalate)',
        re.MULTILINE
    )

    # Typed supervision
    TYPED_SUPERVISION_PATTERN = re.compile(
        r'Behaviors\.supervise\s*\(|'
        r'\.onFailure\s*\(\s*(?:(\w+)\.class\s*,\s*)?'
        r'SupervisorStrategy\.\s*(\w+)',
        re.MULTILINE
    )

    # Actor spawning
    SPAWN_PATTERN = re.compile(
        r'(?:getContext\(\)|context)\s*\.\s*(?:spawn|actorOf)\s*\(\s*'
        r'(?:(\w+)\.(?:create|props|apply)\s*\(|Props\.create\s*\(\s*(\w+))',
        re.MULTILINE
    )

    # Lifecycle hooks
    LIFECYCLE_PATTERN = re.compile(
        r'(?:@Override\s*)?(?:public\s+)?void\s+'
        r'(preStart|postStop|preRestart|postRestart)\s*\(',
        re.MULTILINE
    )

    # Stash
    STASH_PATTERN = re.compile(
        r'stash\s*\(\s*\)|unstashAll\s*\(\s*\)|Stash\b|WithStash',
        re.MULTILINE
    )

    # Timers
    TIMERS_PATTERN = re.compile(
        r'getTimers\s*\(\s*\)|timers\.startSingleTimer|timers\.startTimerWithFixedDelay|'
        r'Behaviors\.withTimers|TimerScheduler',
        re.MULTILINE
    )

    # Ask pattern
    ASK_PATTERN = re.compile(
        r'Patterns\.ask\s*\(|AskPattern\.ask\s*\(|\.ask\s*\(',
        re.MULTILINE
    )

    # Message protocol (sealed interface/class)
    SEALED_PROTOCOL_PATTERN = re.compile(
        r'(?:public\s+)?(?:sealed\s+)?interface\s+(\w+)\s+'
        r'(?:extends\s+\w+\s+)?'
        r'(?:permits\s+[\w,\s]+)?',
        re.DOTALL
    )

    # Message records/classes implementing protocol
    MESSAGE_RECORD_PATTERN = re.compile(
        r'(?:public\s+)?(?:record|final\s+class|static\s+final\s+class)\s+(\w+)\s*'
        r'(?:\([^)]*\))?\s*implements\s+(\w+)',
        re.DOTALL
    )

    # Akka Serializable
    SERIALIZABLE_PATTERN = re.compile(
        r'implements\s+(?:[\w,\s]*\b)(?:CborSerializable|JsonSerializable|'
        r'Serializable|JacksonSerializable)',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract actor information."""
        actors: List[AkkaActorInfo] = []
        messages: List[AkkaMessageInfo] = []
        supervisions: List[AkkaSupervisionInfo] = []

        if not content or not content.strip():
            return {
                'actors': actors,
                'messages': messages,
                'supervisions': supervisions,
            }

        # Classic actors
        for match in self.CLASSIC_ACTOR_PATTERN.finditer(content):
            actor = AkkaActorInfo(
                class_name=match.group(1),
                actor_type="classic",
                line_number=content[:match.start()].count('\n') + 1,
            )

            # Check for stash
            actor.has_stash = bool(self.STASH_PATTERN.search(content))
            actor.has_timers = bool(self.TIMERS_PATTERN.search(content))

            # Lifecycle hooks
            for lc in self.LIFECYCLE_PATTERN.finditer(content):
                actor.lifecycle_hooks.append(lc.group(1))

            # Message handlers
            for m in self.MATCH_PATTERN.finditer(content):
                actor.message_handlers.append(m.group(1))

            # Children
            for sp in self.SPAWN_PATTERN.finditer(content):
                child = sp.group(1) or sp.group(2) or ""
                if child:
                    actor.children.append(child)

            actors.append(actor)

        # Typed actors
        for match in self.TYPED_ACTOR_PATTERN.finditer(content):
            actor = AkkaActorInfo(
                class_name=match.group(1),
                actor_type="typed",
                message_type=match.group(2),
                line_number=content[:match.start()].count('\n') + 1,
            )

            actor.has_stash = bool(self.STASH_PATTERN.search(content))
            actor.has_timers = bool(self.TIMERS_PATTERN.search(content))

            # Message handlers (typed)
            for om in self.ON_MESSAGE_PATTERN.finditer(content):
                actor.message_handlers.append(om.group(1))

            # Signals
            for os in self.ON_SIGNAL_PATTERN.finditer(content):
                actor.message_handlers.append(f"Signal:{os.group(1)}")

            # Behavior factories
            for bf in self.BEHAVIOR_FACTORY_PATTERN.finditer(content):
                actor.behaviors.append(bf.group(2))

            # Children
            for sp in self.SPAWN_PATTERN.finditer(content):
                child = sp.group(1) or sp.group(2) or ""
                if child:
                    actor.children.append(child)

            actors.append(actor)

        # Supervision strategies
        for match in self.ONE_FOR_ONE_PATTERN.finditer(content):
            sup = AkkaSupervisionInfo(
                strategy_type="OneForOneStrategy",
                max_retries=int(match.group(1)) if match.group(1) else 0,
                within_time=match.group(2) or "",
                line_number=content[:match.start()].count('\n') + 1,
            )
            for d in self.SUPERVISION_DIRECTIVE_PATTERN.finditer(content):
                sup.directives.append(d.group(1))
            supervisions.append(sup)

        for match in self.ALL_FOR_ONE_PATTERN.finditer(content):
            sup = AkkaSupervisionInfo(
                strategy_type="AllForOneStrategy",
                max_retries=int(match.group(1)) if match.group(1) else 0,
                line_number=content[:match.start()].count('\n') + 1,
            )
            supervisions.append(sup)

        if self.BACKOFF_SUPERVISOR_PATTERN.search(content):
            supervisions.append(AkkaSupervisionInfo(strategy_type="BackoffSupervisor"))

        # Messages
        for match in self.MESSAGE_RECORD_PATTERN.finditer(content):
            msg = AkkaMessageInfo(
                class_name=match.group(1),
                parent_protocol=match.group(2),
                is_serializable=bool(self.SERIALIZABLE_PATTERN.search(content)),
                line_number=content[:match.start()].count('\n') + 1,
            )
            messages.append(msg)

        return {
            'actors': actors,
            'messages': messages,
            'supervisions': supervisions,
        }
