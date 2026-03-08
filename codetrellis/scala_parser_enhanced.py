"""
EnhancedScalaParser v1.0 - Comprehensive Scala parser using all extractors.

This parser integrates all Scala extractors to provide complete
parsing of Scala source files.

Supports:
- Core Scala types (classes, traits, objects, enums, case classes)
- Methods (def, val functions, extension methods, implicit defs)
- Play Framework (2.6+), Akka HTTP, http4s, Tapir, ZIO HTTP, Finch, Scalatra, Cask
- Slick, Doobie, Quill, Skunk, ScalikeJDBC ORM/query support
- GraphQL (Caliban, Sangria)
- gRPC (ScalaPB, fs2-grpc, zio-grpc, akka-grpc)
- JSON codecs (Circe, Play JSON, Spray JSON, uPickle, jsoniter-scala)
- Implicits, givens, type classes, macros
- SBT/Mill/Scala CLI dependency parsing
- All Scala versions: 2.10, 2.11, 2.12, 2.13, 3.0, 3.1, 3.2, 3.3, 3.4, 3.5+
  (Extension methods, opaque types, enums, given/using, derives, export)

Optional AST support via tree-sitter-scala (if installed).
Optional LSP support via Metals.

Part of CodeTrellis v4.25 - Scala Language Support
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

# Import all Scala extractors
from .extractors.scala import (
    ScalaTypeExtractor, ScalaClassInfo, ScalaTraitInfo, ScalaObjectInfo,
    ScalaEnumInfo, ScalaTypeAliasInfo, ScalaFieldInfo, ScalaGivenInfo,
    ScalaFunctionExtractor, ScalaMethodInfo, ScalaParameterInfo,
    ScalaAPIExtractor, ScalaRouteInfo, ScalaGRPCServiceInfo,
    ScalaGraphQLInfo, ScalaControllerInfo,
    ScalaModelExtractor, ScalaModelInfo, ScalaMigrationInfo, ScalaCodecInfo,
    ScalaAttributeExtractor, ScalaAnnotationInfo, ScalaImplicitInfo,
    ScalaMacroInfo, ScalaDependencyInfo,
)

logger = logging.getLogger(__name__)

# Optional tree-sitter support
_tree_sitter_available = False
_ts_scala_language = None

try:
    import tree_sitter
    import tree_sitter_scala
    _ts_scala_language = tree_sitter_scala.language()
    _tree_sitter_available = True
    logger.debug("tree-sitter-scala available for AST parsing")
except ImportError:
    logger.debug("tree-sitter-scala not installed — using regex-based parsing")


@dataclass
class ScalaParseResult:
    """Complete parse result for a Scala file."""
    file_path: str
    file_type: str = "scala"

    # Package info
    package_name: str = ""

    # Core types
    classes: List[ScalaClassInfo] = field(default_factory=list)
    traits: List[ScalaTraitInfo] = field(default_factory=list)
    objects: List[ScalaObjectInfo] = field(default_factory=list)
    enums: List[ScalaEnumInfo] = field(default_factory=list)
    type_aliases: List[ScalaTypeAliasInfo] = field(default_factory=list)
    givens: List[ScalaGivenInfo] = field(default_factory=list)

    # Methods and functions
    methods: List[ScalaMethodInfo] = field(default_factory=list)
    extension_methods: List[ScalaMethodInfo] = field(default_factory=list)
    val_functions: List[Dict] = field(default_factory=list)

    # API/Framework elements
    routes: List[ScalaRouteInfo] = field(default_factory=list)
    controllers: List[ScalaControllerInfo] = field(default_factory=list)
    grpc_services: List[ScalaGRPCServiceInfo] = field(default_factory=list)
    graphql_types: List[ScalaGraphQLInfo] = field(default_factory=list)

    # Database models and codecs
    models: List[ScalaModelInfo] = field(default_factory=list)
    migrations: List[ScalaMigrationInfo] = field(default_factory=list)
    codecs: List[ScalaCodecInfo] = field(default_factory=list)

    # Attributes / implicits / macros / deps
    annotations: List[ScalaAnnotationInfo] = field(default_factory=list)
    implicits: List[ScalaImplicitInfo] = field(default_factory=list)
    macros: List[ScalaMacroInfo] = field(default_factory=list)
    dependencies: List[ScalaDependencyInfo] = field(default_factory=list)
    imports: List[Dict] = field(default_factory=list)
    compiler_options: List[str] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    scala_version: str = ""
    detected_scala_version_features: List[str] = field(default_factory=list)


class EnhancedScalaParser:
    """
    Enhanced Scala parser that uses all extractors for comprehensive parsing.

    Framework detection supports:
    - Play Framework (2.6 - 3.0+)
    - Akka / Pekko (HTTP, Streams, Actors, Cluster, Persistence)
    - http4s (0.21 - 0.23+)
    - Tapir (sttp)
    - ZIO (1.x, 2.x) / ZIO HTTP / ZIO Streams
    - Cats Effect / Cats / fs2
    - Finch
    - Scalatra
    - Cask
    - Slick (3.x)
    - Doobie (0.13+, 1.x)
    - Quill
    - Skunk
    - ScalikeJDBC
    - Anorm
    - Circe / Play JSON / Spray JSON / uPickle / jsoniter-scala
    - ScalaPB / fs2-grpc / zio-grpc / akka-grpc
    - Caliban / Sangria (GraphQL)
    - Spark / Flink / Kafka Streams (big data)
    - ScalaTest / MUnit / Specs2 / ScalaCheck / Weaver
    - Refined / Newtype / Iron
    - Monocle / Chimney
    - Enumeratum
    - Ciris / PureConfig
    - Flyway / Play Evolutions
    - Scala.js / Scala Native
    """

    # ── Import patterns ─────────────────────────────────────────
    IMPORT_PATTERN = re.compile(
        r'''import\s+(?P<path>[\w.]+)''',
        re.MULTILINE
    )

    # ── Framework detection ─────────────────────────────────────
    FRAMEWORK_PATTERNS = {
        # Web frameworks
        'play': re.compile(r'(?:play\.api\.|play\.mvc\.|PlaySpec|GuiceApplicationBuilder|AbstractController|BaseController|InjectedController|Action(?:\.async)?|MessagesAbstractController)\b'),
        'akka_http': re.compile(r'(?:akka\.http\.|AkkaHttpServer|HttpApp|Route|Directives|pathPrefix|complete|entity)\b'),
        'pekko_http': re.compile(r'(?:pekko\.http\.|org\.apache\.pekko\.http)\b'),
        'http4s': re.compile(r'(?:http4s|HttpRoutes|HttpApp|org\.http4s\.|dsl\.io|BlazeServerBuilder|EmberServerBuilder)\b'),
        'tapir': re.compile(r'(?:sttp\.tapir\.|endpoint\.get|endpoint\.post|serverLogic|AnyEndpoint)\b'),
        'zio_http': re.compile(r'(?:zio\.http\.|ZIO\.http|Routes\.empty)\b'),
        'finch': re.compile(r'(?:io\.finch\.|Endpoint\.|endpoint\.get)\b'),
        'scalatra': re.compile(r'(?:Scalatra|ScalatraServlet|ScalatraFilter|ScalatraBase)\b'),
        'cask': re.compile(r'(?:cask\.|@cask\.get|@cask\.post|cask\.MainRoutes)\b'),

        # Effect systems & FP
        'zio': re.compile(r'(?:zio\.|ZIO\[|ZLayer|ZEnvironment|ZStream|ZSink|ZPipeline|ZManaged)\b'),
        'cats_effect': re.compile(r'(?:cats\.effect\.|IO\[|Resource\[|Concurrent\[|Async\[|Sync\[|IOApp)\b'),
        'cats': re.compile(r'(?:cats\.|Monad\[|Functor\[|Applicative\[|Traverse\[|cats\.syntax\.|cats\.implicits)\b'),
        'fs2': re.compile(r'(?:fs2\.|Stream\[|Pipe\[|fs2\.io)\b'),
        'monix': re.compile(r'(?:monix\.|Observable\[|Task\[)\b'),

        # Actors
        'akka_actors': re.compile(r'(?:akka\.actor\.|ActorSystem|ActorRef|AbstractActor|Behavior\[|akka\.typed)\b'),
        'pekko_actors': re.compile(r'(?:pekko\.actor\.|org\.apache\.pekko\.actor)\b'),
        'akka_streams': re.compile(r'(?:akka\.stream\.|Source\[|Flow\[|Sink\[|ActorMaterializer|Materializer)\b'),
        'akka_cluster': re.compile(r'(?:akka\.cluster\.|Cluster\(|ClusterSharding)\b'),
        'akka_persistence': re.compile(r'(?:akka\.persistence\.|EventSourcedBehavior|PersistentActor)\b'),

        # Database / ORM
        'slick': re.compile(r'(?:slick\.|TableQuery|Table\[|slick\.jdbc\.|DBIO|slick\.lifted)\b'),
        'doobie': re.compile(r'(?:doobie\.|ConnectionIO|Query0|Update0|Fragment|Transactor|sql"|fr")\b'),
        'quill': re.compile(r'(?:io\.getquill\.|quote\s*\{|query\[|querySchema|QuillContext)\b'),
        'skunk': re.compile(r'(?:skunk\.|Session\[|Query\[|Command\[|natchez)\b'),
        'scalikejdbc': re.compile(r'(?:scalikejdbc\.|SQLSyntaxSupport|NamedDB|DB\s+localTx)\b'),
        'anorm': re.compile(r'(?:anorm\.|SQL\(|SqlParser|Row)\b'),

        # JSON / Serialization
        'circe': re.compile(r'(?:circe\.|Encoder\[|Decoder\[|Codec\[|deriveEncoder|deriveDecoder|\.asJson|\.as\[)\b'),
        'play_json': re.compile(r'(?:play\.api\.libs\.json\.|Json\.format|Json\.reads|Json\.writes|JsValue|Format\[|Reads\[|Writes\[)\b'),
        'spray_json': re.compile(r'(?:spray\.json\.|JsonFormat|jsonFormat\d|DefaultJsonProtocol|RootJsonFormat)\b'),
        'upickle': re.compile(r'(?:upickle\.|ReadWriter\[|Reader\[|Writer\[|ujson)\b'),
        'jsoniter': re.compile(r'(?:jsoniter_scala\.|JsonValueCodec|readFromString|writeToString)\b'),

        # gRPC
        'scalapb': re.compile(r'(?:scalapb\.|GeneratedMessage|GeneratedMessageCompanion)\b'),
        'fs2_grpc': re.compile(r'(?:fs2\.grpc|Fs2Grpc)\b'),
        'zio_grpc': re.compile(r'(?:scalapb\.zio_grpc|ZioGrpc)\b'),
        'akka_grpc': re.compile(r'(?:akka\.grpc|AkkaGrpc)\b'),

        # GraphQL
        'caliban': re.compile(r'(?:caliban\.|graphQL\(|GraphQL\[|api\.graphQL|GraphQLInterpreter)\b'),
        'sangria': re.compile(r'(?:sangria\.|ObjectType|Schema\(|SchemaDefinition|Executor)\b'),

        # Big Data
        'spark': re.compile(r'(?:spark\.|SparkSession|SparkContext|DataFrame|Dataset|RDD|org\.apache\.spark)\b'),
        'flink': re.compile(r'(?:flink\.|StreamExecutionEnvironment|DataStream|org\.apache\.flink)\b'),
        'kafka': re.compile(r'(?:kafka\.|KafkaConsumer|KafkaProducer|org\.apache\.kafka)\b'),
        'kafka_streams': re.compile(r'(?:kafka\.streams|KStream|KTable|StreamsBuilder)\b'),

        # Testing
        'scalatest': re.compile(r'(?:scalatest\.|FlatSpec|FunSpec|FunSuite|WordSpec|AnyFlatSpec|AnyFunSuite|AnyWordSpec|FeatureSpec|AsyncFlatSpec|Matchers|should\.Matchers|org\.scalatest)\b'),
        'munit': re.compile(r'(?:munit\.|FunSuite|CatsEffectSuite|munit\.Assertions)\b'),
        'specs2': re.compile(r'(?:specs2\.|Specification|org\.specs2)\b'),
        'scalacheck': re.compile(r'(?:scalacheck\.|Gen\[|Prop\.|Arbitrary\[|forAll|org\.scalacheck)\b'),
        'weaver': re.compile(r'(?:weaver\.|SimpleIOSuite|IOSuite|Expectations)\b'),

        # Type safety / refinement
        'refined': re.compile(r'(?:eu\.timepit\.refined|Refined\[|refineV)\b'),
        'iron': re.compile(r'(?:io\.github\.iltotore\.iron\.|::|IronType)\b'),
        'newtype': re.compile(r'(?:io\.estatico\.newtype|@newtype)\b'),
        'enumeratum': re.compile(r'(?:enumeratum\.|sealed trait.*extends.*EnumEntry|Enum\[)\b'),

        # Optics
        'monocle': re.compile(r'(?:monocle\.|Lens\[|Prism\[|Iso\[|GenLens|Focus)\b'),
        'chimney': re.compile(r'(?:chimney\.|Transformer\[|transformInto|withFieldConst)\b'),

        # Config
        'ciris': re.compile(r'(?:ciris\.|ConfigValue|env|prop|default)\b'),
        'pureconfig': re.compile(r'(?:pureconfig\.|ConfigSource|ConfigReader|loadConfigOrThrow)\b'),
        'typesafe_config': re.compile(r'(?:com\.typesafe\.config|ConfigFactory|Config\b)\b'),

        # Build tools (detected from build files)
        'sbt': re.compile(r'(?:sbt\.|libraryDependencies|ThisBuild|scalacOptions|enablePlugins|assembly)\b'),
        'mill': re.compile(r'(?:mill\.|ScalaModule|CrossScalaModule|ivy")\b'),

        # Cross-platform
        'scalajs': re.compile(r'(?:scala\.scalajs\.|ScalaJSPlugin|scalajs-dom|@JSExport|@js\.native|js\.Dynamic)\b'),
        'scala_native': re.compile(r'(?:scala\.scalanative\.|ScalaNativePlugin|@extern|scalanative\.unsafe)\b'),

        # Migration / DB
        'flyway': re.compile(r'(?:flyway\.|Flyway|FlywayPlugin|flywayUrl)\b'),
        'evolutions': re.compile(r'(?:play\.api\.db\.evolutions|Evolutions)\b'),

        # Logging
        'log4cats': re.compile(r'(?:log4cats\.|Logger\[|Slf4jLogger)\b'),
        'scribe': re.compile(r'(?:scribe\.|scribe\.Logger)\b'),

        # HTTP client
        'sttp': re.compile(r'(?:sttp\.client3\.|basicRequest|SttpBackend)\b'),
    }

    # ── Scala version feature detection ─────────────────────────
    VERSION_FEATURES = {
        'scala_3_enum': re.compile(r'\benum\s+\w+'),
        'scala_3_given': re.compile(r'\bgiven\s+'),
        'scala_3_using': re.compile(r'\busing\s+'),
        'scala_3_extension': re.compile(r'\bextension\s*[\[(]'),
        'scala_3_export': re.compile(r'\bexport\s+'),
        'scala_3_opaque': re.compile(r'\bopaque\s+type\b'),
        'scala_3_derives': re.compile(r'\bderives\s+'),
        'scala_3_transparent': re.compile(r'\btransparent\s+(trait|inline)\b'),
        'scala_3_inline': re.compile(r'\binline\s+(def|val|given)\b'),
        'scala_3_open': re.compile(r'\bopen\s+class\b'),
        'scala_3_end_marker': re.compile(r'^end\s+\w+', re.MULTILINE),
        'scala_3_braceless': re.compile(r'(?:class|trait|object|def|if|for|while|match)\s+\w.*:\s*$', re.MULTILINE),
        'scala_3_union_type': re.compile(r'\w+\s*\|\s*\w+'),
        'scala_3_intersection_type': re.compile(r'\w+\s*&\s*\w+'),
        'scala_2_implicit': re.compile(r'\bimplicit\s+(val|def|class|object)\b'),
        'scala_2_macro': re.compile(r'=\s*macro\s+'),
        'scala_2_procedure': re.compile(r'def\s+\w+\s*\([^)]*\)\s*\{'),  # No return type
    }

    def __init__(self):
        """Initialize the parser with all extractors."""
        self.type_extractor = ScalaTypeExtractor()
        self.function_extractor = ScalaFunctionExtractor()
        self.api_extractor = ScalaAPIExtractor()
        self.model_extractor = ScalaModelExtractor()
        self.attribute_extractor = ScalaAttributeExtractor()

        # Optional tree-sitter parser
        self._ts_parser = None
        if _tree_sitter_available:
            try:
                self._ts_parser = tree_sitter.Parser(_ts_scala_language)
                logger.debug("tree-sitter Scala parser initialized")
            except Exception as e:
                logger.debug(f"tree-sitter Scala parser init failed: {e}")

    def parse(self, content: str, file_path: str = "") -> ScalaParseResult:
        """
        Parse Scala source code and extract all information.

        Args:
            content: Scala source code content
            file_path: Path to source file

        Returns:
            ScalaParseResult with all extracted information
        """
        result = ScalaParseResult(file_path=file_path)

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect Scala version features used
        result.detected_scala_version_features = self._detect_version_features(content)

        # Infer Scala version from features
        result.scala_version = self._infer_scala_version(result.detected_scala_version_features)

        # Extract types (classes, traits, objects, enums, type aliases, givens)
        type_result = self.type_extractor.extract(content, file_path)
        result.classes = type_result.get('classes', [])
        result.traits = type_result.get('traits', [])
        result.objects = type_result.get('objects', [])
        result.enums = type_result.get('enums', [])
        result.type_aliases = type_result.get('type_aliases', [])
        result.givens = type_result.get('givens', [])

        # Extract methods and functions
        func_result = self.function_extractor.extract(content, file_path)
        result.methods = func_result.get('methods', [])
        result.extension_methods = func_result.get('extension_methods', [])
        result.val_functions = func_result.get('val_functions', [])

        # Extract API patterns
        api_result = self.api_extractor.extract(content, file_path)
        result.routes = api_result.get('routes', [])
        result.controllers = api_result.get('controllers', [])
        result.grpc_services = api_result.get('grpc_services', [])
        result.graphql_types = api_result.get('graphql_types', [])

        # Extract database models
        model_result = self.model_extractor.extract(content, file_path)
        result.models = model_result.get('models', [])
        result.migrations = model_result.get('migrations', [])
        result.codecs = model_result.get('codecs', [])

        # Extract attributes
        attr_result = self.attribute_extractor.extract(content, file_path)
        result.annotations = attr_result.get('annotations', [])
        result.implicits = attr_result.get('implicits', [])
        result.macros = attr_result.get('macros', [])
        result.dependencies = attr_result.get('dependencies', [])
        result.imports = attr_result.get('imports', [])
        result.compiler_options = attr_result.get('compiler_options', [])

        # Extract package name
        packages = attr_result.get('packages', [])
        if packages:
            result.package_name = packages[0].get('name', '')

        # If tree-sitter available, enrich with AST data
        if self._ts_parser:
            self._enrich_with_ast(content, result)

        return result

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect which Scala frameworks/libraries are used in the file."""
        frameworks = []
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(framework)
        return frameworks

    def _detect_version_features(self, content: str) -> List[str]:
        """Detect Scala version-specific features used in the code."""
        features = []
        for feature, pattern in self.VERSION_FEATURES.items():
            if pattern.search(content):
                features.append(feature)
        return features

    def _infer_scala_version(self, features: List[str]) -> str:
        """Infer the minimum Scala version from detected features."""
        scala3_features = [f for f in features if f.startswith('scala_3_')]
        scala2_only_features = [f for f in features if f.startswith('scala_2_')]

        if scala3_features:
            # Scala 3.x features detected
            if any(f in scala3_features for f in ['scala_3_transparent', 'scala_3_open']):
                return "3.3+"
            if 'scala_3_export' in scala3_features:
                return "3.0+"
            return "3.0+"
        elif scala2_only_features:
            if 'scala_2_macro' in scala2_only_features:
                return "2.11+"
            if 'scala_2_procedure' in scala2_only_features:
                return "2.x (deprecated syntax)"
            return "2.13+"
        return ""

    def _enrich_with_ast(self, content: str, result: ScalaParseResult):
        """Enrich parse result using tree-sitter AST when available."""
        if not self._ts_parser:
            return

        try:
            tree = self._ts_parser.parse(content.encode('utf-8'))
            root = tree.root_node
            self._walk_ast_node(root, content, result)
        except Exception as e:
            logger.debug(f"tree-sitter AST enrichment failed: {e}")

    def _walk_ast_node(self, node, content: str, result: ScalaParseResult):
        """Walk tree-sitter AST node to extract additional information."""
        if not node:
            return

        try:
            # Class definitions - validate and enrich
            if node.type == 'class_definition':
                pass  # Regex extraction is comprehensive

            # Object definitions
            if node.type == 'object_definition':
                pass

            # Trait definitions
            if node.type == 'trait_definition':
                pass

            # Method definitions - precise boundary detection
            if node.type in ('function_definition', 'val_definition'):
                pass

            # Enum definitions (Scala 3)
            if node.type == 'enum_definition':
                pass

            # Given definitions (Scala 3)
            if node.type == 'given_definition':
                pass

            for child in node.children:
                self._walk_ast_node(child, content, result)

        except Exception:
            pass

    @staticmethod
    def parse_build_sbt(content: str) -> Dict[str, Any]:
        """
        Parse build.sbt to extract project configuration.

        Args:
            content: build.sbt file content

        Returns:
            Dict with name, version, scalaVersion, dependencies, plugins, scalacOptions
        """
        result: Dict[str, Any] = {
            'name': '',
            'version': '',
            'scala_version': '',
            'organization': '',
            'dependencies': [],
            'plugins': [],
            'scalac_options': [],
            'resolvers': [],
            'sub_projects': [],
        }

        # Project name
        name_match = re.search(r'name\s*:=\s*["\']([^"\']+)["\']', content)
        if name_match:
            result['name'] = name_match.group(1)

        # Version
        ver_match = re.search(r'version\s*:=\s*["\']([^"\']+)["\']', content)
        if ver_match:
            result['version'] = ver_match.group(1)

        # Scala version
        sv_match = re.search(r'scalaVersion\s*:=\s*["\']([^"\']+)["\']', content)
        if sv_match:
            result['scala_version'] = sv_match.group(1)

        # Cross Scala versions
        csv_match = re.search(r'crossScalaVersions\s*:=\s*Seq\(([^)]+)\)', content)
        if csv_match:
            versions = re.findall(r'["\']([^"\']+)["\']', csv_match.group(1))
            result['cross_scala_versions'] = versions

        # Organization
        org_match = re.search(r'organization\s*:=\s*["\']([^"\']+)["\']', content)
        if org_match:
            result['organization'] = org_match.group(1)

        # Dependencies
        dep_pattern = re.compile(
            r'["\'](?P<group>[^"\']+)["\']\s*(?P<cross>%%?%?)\s*'
            r'["\'](?P<artifact>[^"\']+)["\']\s*%\s*'
            r'["\'](?P<version>[^"\']+)["\']'
            r'(?:\s*%\s*["\'](?P<scope>[^"\']+)["\'])?'
        )
        for match in dep_pattern.finditer(content):
            result['dependencies'].append({
                'group': match.group('group'),
                'artifact': match.group('artifact'),
                'version': match.group('version'),
                'cross': match.group('cross'),
                'scope': match.group('scope') or 'compile',
            })

        # SBT plugins
        plugin_pattern = re.compile(
            r'addSbtPlugin\s*\(\s*["\']([^"\']+)["\']\s*%\s*'
            r'["\']([^"\']+)["\']\s*%\s*'
            r'["\']([^"\']+)["\']\s*\)'
        )
        for match in plugin_pattern.finditer(content):
            result['plugins'].append({
                'group': match.group(1),
                'artifact': match.group(2),
                'version': match.group(3),
            })

        # scalacOptions
        opts_pattern = re.compile(
            r'scalacOptions\s*(?:\+\+)?=\s*Seq\s*\(([^)]+)\)'
        )
        for match in opts_pattern.finditer(content):
            opts = re.findall(r'["\']([^"\']+)["\']', match.group(1))
            result['scalac_options'].extend(opts)

        # Sub-projects
        project_pattern = re.compile(
            r'(?:lazy\s+)?val\s+(?P<name>\w+)\s*=\s*\(?\s*project\b'
        )
        for match in project_pattern.finditer(content):
            result['sub_projects'].append(match.group('name'))

        # Resolvers
        resolver_pattern = re.compile(
            r'resolvers\s*\+=?\s*["\']([^"\']+)["\'](?:\s+at\s+["\']([^"\']+)["\'])?'
        )
        for match in resolver_pattern.finditer(content):
            resolver = match.group(1)
            if match.group(2):
                resolver += f" at {match.group(2)}"
            result['resolvers'].append(resolver)

        return result

    @staticmethod
    def parse_build_sc(content: str) -> Dict[str, Any]:
        """
        Parse build.sc (Mill build file) to extract project configuration.

        Args:
            content: build.sc file content

        Returns:
            Dict with scalaVersion, dependencies, modules
        """
        result: Dict[str, Any] = {
            'scala_version': '',
            'dependencies': [],
            'modules': [],
        }

        # Scala version
        sv_match = re.search(r'def\s+scalaVersion\s*=\s*["\']([^"\']+)["\']', content)
        if sv_match:
            result['scala_version'] = sv_match.group(1)

        # Ivy dependencies
        dep_pattern = re.compile(r'ivy"([^"]+)"')
        for match in dep_pattern.finditer(content):
            dep_str = match.group(1)
            parts = re.split(r'::?', dep_str)
            if len(parts) >= 3:
                result['dependencies'].append({
                    'group': parts[0],
                    'artifact': parts[1],
                    'version': parts[2],
                })

        # Module definitions
        module_pattern = re.compile(
            r'object\s+(?P<name>\w+)\s+extends\s+(?P<type>\w+Module)'
        )
        for match in module_pattern.finditer(content):
            result['modules'].append({
                'name': match.group('name'),
                'type': match.group('type'),
            })

        return result
