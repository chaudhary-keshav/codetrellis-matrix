"""
Tests for Akka extractors and EnhancedAkkaParser.

Part of CodeTrellis v4.95 Akka Framework Support.
Tests cover:
- Actor extraction (Classic AbstractActor, Typed AbstractBehavior, supervision)
- Stream extraction (Source, Flow, Sink, Graph DSL, operators)
- HTTP extraction (routes, directives, marshalling, WebSocket)
- Cluster extraction (sharding, singleton, pub/sub, CRDTs)
- Persistence extraction (EventSourcedBehavior, DurableStateBehavior, projections)
- Parser integration (framework detection, version detection, is_akka_file)
"""

import pytest
from codetrellis.akka_parser_enhanced import EnhancedAkkaParser, AkkaParseResult
from codetrellis.extractors.akka import (
    AkkaActorExtractor,
    AkkaStreamExtractor,
    AkkaHttpExtractor,
    AkkaClusterExtractor,
    AkkaPersistenceExtractor,
)


@pytest.fixture
def parser():
    return EnhancedAkkaParser()


@pytest.fixture
def actor_extractor():
    return AkkaActorExtractor()


@pytest.fixture
def stream_extractor():
    return AkkaStreamExtractor()


@pytest.fixture
def http_extractor():
    return AkkaHttpExtractor()


@pytest.fixture
def cluster_extractor():
    return AkkaClusterExtractor()


@pytest.fixture
def persistence_extractor():
    return AkkaPersistenceExtractor()


# ═══════════════════════════════════════════════════════════════════
# Actor Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestAkkaActorExtractor:

    def test_extract_classic_actor(self, actor_extractor):
        content = """
import akka.actor.AbstractActor;

public class GreeterActor extends AbstractActor {
    @Override
    public Receive createReceive() {
        return receiveBuilder()
            .match(Greet.class, this::onGreet)
            .match(GetGreeting.class, this::onGetGreeting)
            .build();
    }
}
"""
        result = actor_extractor.extract(content)
        assert len(result['actors']) > 0
        assert result['actors'][0].actor_type == 'classic'

    def test_extract_typed_actor(self, actor_extractor):
        content = """
import akka.actor.typed.javadsl.AbstractBehavior;
import akka.actor.typed.Behavior;

public class Counter extends AbstractBehavior<Command> {
    @Override
    public Receive<Command> createReceive() {
        return newReceiveBuilder()
            .onMessage(Increment.class, this::onIncrement)
            .onMessage(GetCount.class, this::onGetCount)
            .build();
    }
}
"""
        result = actor_extractor.extract(content)
        assert len(result['actors']) > 0
        assert result['actors'][0].actor_type == 'typed'

    def test_extract_supervision(self, actor_extractor):
        content = """
private static SupervisorStrategy strategy =
    new OneForOneStrategy(10, Duration.create("1 minute",
        DeciderBuilder
            .match(ArithmeticException.class, e -> SupervisorStrategy.resume())
            .match(NullPointerException.class, e -> SupervisorStrategy.restart())
            .build()));
"""
        result = actor_extractor.extract(content)
        assert len(result['supervisions']) > 0

    def test_extract_messages(self, actor_extractor):
        content = """
public sealed interface Command {}
public record Start() implements Command {}
public record Stop(String reason) implements Command {}
public static final class Tick implements Command {
    public static final Tick INSTANCE = new Tick();
}
"""
        result = actor_extractor.extract(content)
        assert len(result['messages']) > 0

    def test_empty_content(self, actor_extractor):
        result = actor_extractor.extract("")
        assert result['actors'] == []
        assert result['messages'] == []


# ═══════════════════════════════════════════════════════════════════
# Stream Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestAkkaStreamExtractor:

    def test_extract_source(self, stream_extractor):
        content = """
Source<Integer, NotUsed> source = Source.from(Arrays.asList(1, 2, 3, 4, 5));
Source<String, NotUsed> tickSource = Source.tick(Duration.ofSeconds(1), Duration.ofSeconds(1), "tick");
"""
        result = stream_extractor.extract(content)
        assert len(result['stages']) > 0

    def test_extract_flow(self, stream_extractor):
        content = """
Flow<Integer, String, NotUsed> flow = Flow.of(Integer.class)
    .map(i -> i * 2)
    .filter(i -> i > 5)
    .mapAsync(4, i -> CompletableFuture.supplyAsync(() -> String.valueOf(i)));
"""
        result = stream_extractor.extract(content)
        assert 'map' in result['operators']
        assert 'filter' in result['operators']

    def test_extract_sink(self, stream_extractor):
        content = """
Sink<String, CompletionStage<Done>> sink = Sink.foreach(System.out::println);
Sink<Integer, CompletionStage<Integer>> foldSink = Sink.fold(0, Integer::sum);
"""
        result = stream_extractor.extract(content)
        assert len(result['stages']) > 0

    def test_extract_graph_dsl(self, stream_extractor):
        content = """
RunnableGraph<NotUsed> graph = RunnableGraph.fromGraph(
    GraphDSL.create(builder -> {
        UniformFanOutShape<Integer, Integer> bcast = builder.add(Broadcast.create(2));
        UniformFanInShape<Integer, Integer> merge = builder.add(Merge.create(2));
        builder.from(source).viaFanOut(bcast);
        builder.from(bcast).via(flow1).toFanIn(merge);
        builder.from(bcast).via(flow2).toFanIn(merge);
        builder.from(merge).to(sink);
        return ClosedShape.getInstance();
    })
);
"""
        result = stream_extractor.extract(content)
        assert len(result['graphs']) > 0

    def test_empty_content(self, stream_extractor):
        result = stream_extractor.extract("")
        assert result['stages'] == []
        assert result['operators'] == []


# ═══════════════════════════════════════════════════════════════════
# HTTP Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestAkkaHttpExtractor:

    def test_extract_routes(self, http_extractor):
        content = """
Route route = concat(
    path("hello", () ->
        get(() ->
            complete(StatusCodes.OK, "Hello World!")
        )
    ),
    path("users", () ->
        post(() ->
            entity(Jackson.unmarshaller(User.class), user ->
                complete(StatusCodes.CREATED, user)
            )
        )
    )
);
"""
        result = http_extractor.extract(content)
        assert len(result['routes']) > 0

    def test_extract_websocket(self, http_extractor):
        content = """
Route wsRoute = path("ws", () ->
    handleWebSocketMessages(
        Flow.fromSinkAndSource(Sink.ignore(), Source.single(TextMessage.create("Hello")))
    )
);
"""
        result = http_extractor.extract(content)
        assert result['metadata']['has_websocket'] is True

    def test_extract_security(self, http_extractor):
        content = """
Route secured = authenticateBasic("my-realm", myAuthenticator, user ->
    authorize(user::isAdmin, () ->
        complete("admin area")
    )
);
"""
        result = http_extractor.extract(content)
        assert len(result['metadata']['security_mechanisms']) > 0

    def test_extract_server_binding(self, http_extractor):
        content = """
Http.get(system).newServerAt("0.0.0.0", 8080).bind(route);
"""
        result = http_extractor.extract(content)
        assert len(result['metadata']['server_bindings']) > 0

    def test_empty_content(self, http_extractor):
        result = http_extractor.extract("")
        assert result['routes'] == []


# ═══════════════════════════════════════════════════════════════════
# Cluster Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestAkkaClusterExtractor:

    def test_extract_sharding(self, cluster_extractor):
        content = """
import akka.cluster.sharding.typed.javadsl.ClusterSharding;

EntityTypeKey<Command> typeKey = EntityTypeKey.create(Command.class, "Counter");
ClusterSharding(system).init(Entity.of(typeKey, ctx -> Counter.create(ctx.getEntityId())));
"""
        result = cluster_extractor.extract(content)
        assert len(result['sharding']) > 0

    def test_extract_singleton(self, cluster_extractor):
        content = """
ClusterSingleton(system).init(SingletonActor.of(Guardian.create(), "guardian"));
"""
        result = cluster_extractor.extract(content)
        assert len(result['singletons']) > 0

    def test_extract_pubsub(self, cluster_extractor):
        content = """
DistributedPubSub pubsub = DistributedPubSub.get(system);
ActorRef mediator = pubsub.mediator();
mediator.tell(new DistributedPubSubMediator.Subscribe("topic1", self()));
mediator.tell(new DistributedPubSubMediator.Publish("topic1", message));
"""
        result = cluster_extractor.extract(content)
        assert len(result['pubsub']) > 0

    def test_extract_ddata(self, cluster_extractor):
        content = """
DistributedData(system);
GCounter counter = GCounter.empty();
ORSet<String> orSet = ORSet.empty();
"""
        result = cluster_extractor.extract(content)
        assert result['metadata']['has_ddata'] is True
        assert len(result['metadata']['crdts']) > 0

    def test_empty_content(self, cluster_extractor):
        result = cluster_extractor.extract("")
        assert result['sharding'] == []


# ═══════════════════════════════════════════════════════════════════
# Persistence Extractor Tests
# ═══════════════════════════════════════════════════════════════════

class TestAkkaPersistenceExtractor:

    def test_extract_event_sourced(self, persistence_extractor):
        content = """
import akka.persistence.typed.javadsl.EventSourcedBehavior;

public class Account extends EventSourcedBehavior<Command, Event, State> {
    PersistenceId persistenceId = PersistenceId.of("Account", entityId);

    @Override
    public State emptyState() { return new State(); }

    @Override
    public CommandHandler<Command, Event, State> commandHandler() {
        return newCommandHandlerBuilder()
            .forAnyState()
            .onCommand(Deposit.class, this::onDeposit)
            .build();
    }

    @Override
    public EventHandler<State, Event> eventHandler() {
        return newEventHandlerBuilder()
            .forAnyState()
            .onEvent(Deposited.class, (state, evt) -> state.withBalance(state.balance + evt.amount))
            .build();
    }
}
"""
        result = persistence_extractor.extract(content)
        assert len(result['actors']) > 0
        assert result['actors'][0].is_typed is True

    def test_extract_classic_persistent_actor(self, persistence_extractor):
        content = """
import akka.persistence.AbstractPersistentActor;

public class MyPersistentActor extends AbstractPersistentActor {
    @Override
    public String persistenceId() { return "my-id"; }

    @Override
    public Receive createReceiveRecover() {
        return receiveBuilder().build();
    }

    @Override
    public Receive createReceive() {
        return receiveBuilder()
            .match(String.class, cmd -> persist(new MyEvent(cmd), evt -> {}))
            .build();
    }
}
"""
        result = persistence_extractor.extract(content)
        assert len(result['actors']) > 0
        assert result['actors'][0].is_typed is False

    def test_extract_snapshots(self, persistence_extractor):
        content = """
.withRetention(RetentionCriteria.snapshotEvery(100, 3))
"""
        result = persistence_extractor.extract(content)
        assert len(result['snapshots']) > 0

    def test_extract_projections(self, persistence_extractor):
        content = """
import akka.projection.r2dbc.javadsl.R2dbcProjection;

ProjectionId projId = ProjectionId.of("OrderProjection", "tag1");
R2dbcProjection.exactlyOnce(projId, sourceProvider, handler);
"""
        result = persistence_extractor.extract(content)
        assert len(result['projections']) > 0

    def test_empty_content(self, persistence_extractor):
        result = persistence_extractor.extract("")
        assert result['actors'] == []


# ═══════════════════════════════════════════════════════════════════
# Parser Integration Tests
# ═══════════════════════════════════════════════════════════════════

class TestEnhancedAkkaParser:

    def test_is_akka_file(self, parser):
        content = """
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.AbstractBehavior;
"""
        assert parser.is_akka_file(content) is True

    def test_is_pekko_file(self, parser):
        content = """
import org.apache.pekko.actor.typed.Behavior;
"""
        assert parser.is_akka_file(content) is True

    def test_is_not_akka_file(self, parser):
        content = """
import java.util.List;
public class Main {}
"""
        assert parser.is_akka_file(content) is False

    def test_detect_frameworks(self, parser):
        content = """
import akka.actor.typed.Behavior;
import akka.stream.javadsl.Source;
import akka.http.javadsl.server.Route;
import akka.cluster.sharding.typed.javadsl.ClusterSharding;
import akka.persistence.typed.javadsl.EventSourcedBehavior;
"""
        frameworks = parser._detect_frameworks(content)
        assert 'akka-actor-typed' in frameworks
        assert 'akka-stream' in frameworks
        assert 'akka-http' in frameworks
        assert 'akka-cluster-sharding' in frameworks
        assert 'akka-persistence-typed' in frameworks

    def test_detect_version_26(self, parser):
        content = """
"com.typesafe.akka" %% "akka-actor-typed" % "2.6.20"
"""
        version = parser._detect_version(content)
        assert '2.6' in version

    def test_detect_version_pekko(self, parser):
        content = """
import org.apache.pekko.actor.typed.Behavior;
"""
        version = parser._detect_version(content)
        assert 'Pekko' in version

    def test_parse_full(self, parser):
        content = """
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.AbstractBehavior;
import akka.actor.typed.javadsl.Behaviors;
import akka.stream.javadsl.Source;

public class Guardian extends AbstractBehavior<Command> {
    public sealed interface Command {}
    public record Start() implements Command {}

    public static Behavior<Command> create() {
        return Behaviors.setup(Guardian::new);
    }

    @Override
    public Receive<Command> createReceive() {
        return newReceiveBuilder()
            .onMessage(Start.class, this::onStart)
            .build();
    }

    private Behavior<Command> onStart(Start cmd) {
        Source.from(Arrays.asList(1, 2, 3))
            .map(i -> i * 2)
            .runWith(Sink.foreach(System.out::println), materializer);
        return this;
    }
}
"""
        result = parser.parse(content)
        assert isinstance(result, AkkaParseResult)
        assert len(result.actors) > 0
        assert len(result.frameworks) > 0

    def test_parse_empty(self, parser):
        result = parser.parse("")
        assert isinstance(result, AkkaParseResult)
        assert result.actors == []
        assert result.stream_stages == []
        assert result.http_routes == []

    def test_parse_returns_dataclass_items(self, parser):
        content = """
import akka.actor.typed.javadsl.AbstractBehavior;
public class MyActor extends AbstractBehavior<String> {}
"""
        result = parser.parse(content)
        for a in result.actors:
            assert 'class_name' in a
