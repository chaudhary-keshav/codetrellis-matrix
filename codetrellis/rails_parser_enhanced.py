"""
EnhancedRailsParser v1.0 - Comprehensive Ruby on Rails framework parser.

Runs as a supplementary layer on top of the Ruby parser, extracting
Rails-specific semantics.

Supports:
- Rails 3.x (basic MVC, asset pipeline, ActiveRecord)
- Rails 4.x (strong parameters, concerns, turbolinks)
- Rails 5.x (ActionCable, API mode, ApplicationRecord)
- Rails 6.x (Webpacker, Action Mailbox, Action Text, multi-db)
- Rails 7.x (Hotwire/Turbo/Stimulus, import maps, encrypted credentials, Propshaft)
- Rails 7.1+ (Dockerfile generation, async queries, composite primary keys)
- Rails 8.x (Kamal, Solid Queue, Solid Cache, Solid Cable, Thruster)

Rails-specific extraction:
- Routes: resources, namespace, scope, member/collection, constraints
- Controllers: actions, before_action/after_action, strong params, concerns
- Models: associations (belongs_to, has_many, has_one, HABTM), validations,
  scopes, callbacks, enums, delegations, ActiveRecord queries
- Views: layouts, partials, helpers, Turbo frames/streams
- Jobs: ActiveJob, perform_later/now, queue management
- Mailers: ActionMailer, deliver_later/now
- Channels: ActionCable channels, subscriptions, broadcasts
- Configuration: initializers, environments, credentials
- Migrations: create_table, add_column, add_index, references

Framework detection (40+ Rails ecosystem patterns):
- Core: rails, railties, action_pack, active_record, active_model
- Frontend: turbo-rails, stimulus-rails, importmap-rails, propshaft, sprockets
- Auth: devise, omniauth, doorkeeper, jwt, pundit, cancancan
- API: jbuilder, active_model_serializers, jsonapi-serializer, fast_jsonapi
- Background: sidekiq, resque, delayed_job, good_job, solid_queue
- Testing: rspec-rails, factory_bot_rails, shoulda, capybara, vcr
- Admin: activeadmin, rails_admin, administrate
- Storage: active_storage, shrine, carrierwave, paperclip
- Search: ransack, elasticsearch, searchkick, meilisearch
- Deployment: kamal, capistrano, puma, unicorn

Part of CodeTrellis v5.2.0 - Ruby Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class RailsRouteInfo:
    """Information about a Rails route."""
    method: str  # GET, POST, PUT, PATCH, DELETE, resources, resource, root
    path: str
    controller: str = ""
    action: str = ""
    route_name: str = ""
    namespace: str = ""
    constraints: List[str] = field(default_factory=list)
    is_api: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class RailsControllerInfo:
    """Information about a Rails controller."""
    name: str
    parent_class: str = ""
    actions: List[str] = field(default_factory=list)
    before_actions: List[str] = field(default_factory=list)
    after_actions: List[str] = field(default_factory=list)
    around_actions: List[str] = field(default_factory=list)
    skip_before_actions: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    rescue_handlers: List[str] = field(default_factory=list)
    strong_params_method: str = ""
    is_api_controller: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class RailsModelInfo:
    """Information about a Rails model."""
    name: str
    table_name: str = ""
    parent_class: str = ""
    associations: List[Dict[str, str]] = field(default_factory=list)
    validations: List[Dict[str, str]] = field(default_factory=list)
    scopes: List[Dict[str, str]] = field(default_factory=list)
    callbacks: List[str] = field(default_factory=list)
    enums: List[Dict[str, str]] = field(default_factory=list)
    delegations: List[str] = field(default_factory=list)
    has_sti: bool = False
    file: str = ""
    line_number: int = 0


@dataclass
class RailsMigrationInfo:
    """Information about a Rails migration."""
    name: str
    version: str = ""
    operations: List[str] = field(default_factory=list)
    tables_created: List[str] = field(default_factory=list)
    columns_added: List[str] = field(default_factory=list)
    indexes_added: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class RailsJobInfo:
    """Information about a Rails job."""
    name: str
    queue: str = ""
    retry_count: int = 0
    is_active_job: bool = True
    perform_method: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class RailsMailerInfo:
    """Information about a Rails mailer."""
    name: str
    methods: List[str] = field(default_factory=list)
    layout: str = ""
    default_from: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class RailsChannelInfo:
    """Information about an ActionCable channel."""
    name: str
    stream_for: str = ""
    subscribed_method: bool = False
    broadcast_to: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class RailsConfigInfo:
    """Information about Rails configuration."""
    setting: str
    value: str = ""
    environment: str = ""  # development, production, test, or general
    file: str = ""
    line_number: int = 0


@dataclass
class RailsParseResult:
    """Complete parse result for a Rails file."""
    file_path: str
    file_type: str = "ruby"

    # Routes
    routes: List[RailsRouteInfo] = field(default_factory=list)

    # Controllers
    controllers: List[RailsControllerInfo] = field(default_factory=list)

    # Models
    models: List[RailsModelInfo] = field(default_factory=list)
    migrations: List[RailsMigrationInfo] = field(default_factory=list)

    # Jobs
    jobs: List[RailsJobInfo] = field(default_factory=list)

    # Mailers
    mailers: List[RailsMailerInfo] = field(default_factory=list)

    # Channels
    channels: List[RailsChannelInfo] = field(default_factory=list)

    # Configuration
    configs: List[RailsConfigInfo] = field(default_factory=list)

    # Metadata
    detected_frameworks: List[str] = field(default_factory=list)
    rails_version: str = ""
    is_api_only: bool = False
    has_turbo: bool = False
    has_stimulus: bool = False
    has_hotwire: bool = False
    total_routes: int = 0
    total_models: int = 0
    total_controllers: int = 0


class EnhancedRailsParser:
    """
    Enhanced Rails parser for comprehensive Ruby on Rails extraction.

    Runs AFTER the Ruby parser when Rails framework is detected.
    Extracts Rails-specific patterns that the base Ruby parser
    cannot capture in full detail.
    """

    # Rails detection patterns
    RAILS_REQUIRE = re.compile(
        r"require\s+['\"]rails['\"]|"
        r"require\s+['\"]rails/all['\"]|"
        r"Rails\.application\b|"
        r"class\s+\w+\s*<\s*(?:Application)?Record\b|"
        r"class\s+\w+\s*<\s*(?:Action|Active|Application)"
    )

    # Route patterns
    ROUTE_RESOURCE = re.compile(
        r"^\s*resources?\s+:(\w+)(?:\s*,\s*(.+))?",
        re.MULTILINE,
    )
    ROUTE_HTTP = re.compile(
        r"^\s*(get|post|put|patch|delete|match)\s+['\"]([^'\"]+)['\"]"
        r"(?:\s*(?:=>|,)\s*['\"]?(\w+)#(\w+)['\"]?)?",
        re.MULTILINE,
    )
    ROUTE_ROOT = re.compile(
        r"^\s*root\s+(?:to:\s*)?['\"](\w+)#(\w+)['\"]",
        re.MULTILINE,
    )
    ROUTE_NAMESPACE = re.compile(
        r"^\s*namespace\s+:(\w+)",
        re.MULTILINE,
    )
    ROUTE_SCOPE = re.compile(
        r"^\s*scope\s+['\"]?:?(\w+)['\"]?",
        re.MULTILINE,
    )
    ROUTE_MEMBER_COLLECTION = re.compile(
        r"^\s*(member|collection)\s+do",
        re.MULTILINE,
    )
    ROUTE_MOUNT = re.compile(
        r"^\s*mount\s+(\w[\w:]*)\s*(?:=>|,\s*at:)\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )

    # Controller patterns
    CONTROLLER_CLASS = re.compile(
        r"class\s+(\w+Controller)\s*<\s*(\w[\w:]*Controller)",
    )
    BEFORE_ACTION = re.compile(
        r"^\s*(before_action|before_filter)\s+:(\w+)(?:\s*,\s*(.+))?",
        re.MULTILINE,
    )
    AFTER_ACTION = re.compile(
        r"^\s*(after_action|after_filter)\s+:(\w+)",
        re.MULTILINE,
    )
    AROUND_ACTION = re.compile(
        r"^\s*around_action\s+:(\w+)",
        re.MULTILINE,
    )
    SKIP_BEFORE_ACTION = re.compile(
        r"^\s*skip_before_action\s+:(\w+)",
        re.MULTILINE,
    )
    RESCUE_FROM = re.compile(
        r"^\s*rescue_from\s+(\w[\w:]*)",
        re.MULTILINE,
    )
    STRONG_PARAMS = re.compile(
        r"def\s+(\w+_params)\b",
    )
    CONTROLLER_ACTION = re.compile(
        r"^\s*def\s+(index|show|new|create|edit|update|destroy|"
        r"search|export|import|download|upload)\b",
        re.MULTILINE,
    )
    INCLUDE_CONCERN = re.compile(
        r"^\s*include\s+(\w+)",
        re.MULTILINE,
    )

    # Model patterns
    MODEL_CLASS = re.compile(
        r"class\s+(\w+)\s*<\s*(ApplicationRecord|ActiveRecord::Base)",
    )
    ASSOCIATION = re.compile(
        r"^\s*(belongs_to|has_many|has_one|has_and_belongs_to_many)\s+:(\w+)"
        r"(?:\s*,\s*(.+))?",
        re.MULTILINE,
    )
    VALIDATION = re.compile(
        r"^\s*validates?\s+:?(\w+)(?:\s*,\s*(.+))?",
        re.MULTILINE,
    )
    SCOPE = re.compile(
        r"^\s*scope\s+:(\w+)\s*,\s*(.+)",
        re.MULTILINE,
    )
    CALLBACK = re.compile(
        r"^\s*(before_validation|after_validation|before_save|after_save|"
        r"before_create|after_create|before_update|after_update|"
        r"before_destroy|after_destroy|after_commit|after_rollback|"
        r"after_initialize|after_find)\s+:(\w+)",
        re.MULTILINE,
    )
    ENUM_DEF = re.compile(
        r"^\s*enum\s+(?::)?(\w+)(?:\s*,\s*|\s*:\s*)(.+)",
        re.MULTILINE,
    )
    DELEGATION = re.compile(
        r"^\s*delegate\s+(.+?)(?:\s*,\s*to:\s*:(\w+))?$",
        re.MULTILINE,
    )

    # Migration patterns
    MIGRATION_CLASS = re.compile(
        r"class\s+(\w+)\s*<\s*ActiveRecord::Migration(?:\[(\d+\.\d+)\])?",
    )
    CREATE_TABLE = re.compile(
        r"^\s*create_table\s+[:\"](\w+)",
        re.MULTILINE,
    )
    ADD_COLUMN = re.compile(
        r"^\s*add_column\s+[:\"](\w+)['\"]?\s*,\s*[:\"](\w+)",
        re.MULTILINE,
    )
    ADD_INDEX = re.compile(
        r"^\s*add_index\s+[:\"](\w+)",
        re.MULTILINE,
    )

    # Job patterns
    JOB_CLASS = re.compile(
        r"class\s+(\w+Job)\s*<\s*(ApplicationJob|ActiveJob::Base)",
    )
    QUEUE_AS = re.compile(
        r"^\s*queue_as\s+[:\"]?(\w+)",
        re.MULTILINE,
    )
    RETRY_ON = re.compile(
        r"^\s*retry_on\s+(\w[\w:]*)",
        re.MULTILINE,
    )

    # Mailer patterns
    MAILER_CLASS = re.compile(
        r"class\s+(\w+Mailer)\s*<\s*(ApplicationMailer|ActionMailer::Base)",
    )
    MAILER_DEFAULT = re.compile(
        r"^\s*default\s+from:\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )
    MAILER_METHOD = re.compile(
        r"^\s*def\s+(\w+)\b",
        re.MULTILINE,
    )

    # Channel patterns
    CHANNEL_CLASS = re.compile(
        r"class\s+(\w+Channel)\s*<\s*(ApplicationCable::Channel|ActionCable::Channel::Base)",
    )
    STREAM_FOR = re.compile(
        r"^\s*stream_for\s+(.+)",
        re.MULTILINE,
    )
    STREAM_FROM = re.compile(
        r"^\s*stream_from\s+['\"]?(.+?)['\"]?\s*$",
        re.MULTILINE,
    )
    BROADCAST_TO = re.compile(
        r"(\w+Channel)\.broadcast_to\b|"
        r"ActionCable\.server\.broadcast\s*\(\s*['\"](\w+)['\"]",
    )

    # Config patterns
    RAILS_CONFIG = re.compile(
        r"(?:config|Rails\.application\.config)\.(\w[\w.]+)\s*=\s*(.+)",
    )

    # Framework ecosystem detection
    FRAMEWORK_PATTERNS = {
        'rails': re.compile(r"require\s+['\"]rails|Rails\.application|class\s+\w+\s*<\s*Application|ActiveRecord::Base|ActiveRecord::Migration|ActionController::|ActionMailer::|ActionCable::"),
        'turbo-rails': re.compile(r"gem\s+['\"]turbo-rails|turbo_frame_tag|turbo_stream\b"),
        'stimulus-rails': re.compile(r"gem\s+['\"]stimulus-rails|data-controller\s*="),
        'importmap-rails': re.compile(r"gem\s+['\"]importmap-rails|pin\s+['\"]"),
        'propshaft': re.compile(r"gem\s+['\"]propshaft"),
        'sprockets': re.compile(r"gem\s+['\"]sprockets|//=\s*require\b"),
        'webpacker': re.compile(r"gem\s+['\"]webpacker"),
        'devise': re.compile(r"gem\s+['\"]devise|devise_for\b|Devise\.\w+"),
        'omniauth': re.compile(r"gem\s+['\"]omniauth"),
        'doorkeeper': re.compile(r"gem\s+['\"]doorkeeper|use_doorkeeper"),
        'pundit': re.compile(r"gem\s+['\"]pundit|include\s+Pundit|authorize\s+"),
        'cancancan': re.compile(r"gem\s+['\"]cancancan|load_and_authorize_resource"),
        'jbuilder': re.compile(r"gem\s+['\"]jbuilder|json\.\w+"),
        'active_model_serializers': re.compile(r"gem\s+['\"]active_model_serializers|ActiveModelSerializers"),
        'jsonapi-serializer': re.compile(r"gem\s+['\"]jsonapi-serializer|include\s+JSONAPI"),
        'sidekiq': re.compile(r"gem\s+['\"]sidekiq|Sidekiq\.\w+"),
        'resque': re.compile(r"gem\s+['\"]resque|Resque\.\w+"),
        'delayed_job': re.compile(r"gem\s+['\"]delayed_job|\.delay\b|handle_asynchronously"),
        'good_job': re.compile(r"gem\s+['\"]good_job"),
        'solid_queue': re.compile(r"gem\s+['\"]solid_queue"),
        'rspec-rails': re.compile(r"gem\s+['\"]rspec-rails"),
        'factory_bot': re.compile(r"gem\s+['\"]factory_bot|FactoryBot\.\w+"),
        'capybara': re.compile(r"gem\s+['\"]capybara"),
        'activeadmin': re.compile(r"gem\s+['\"]activeadmin|ActiveAdmin\.\w+"),
        'rails_admin': re.compile(r"gem\s+['\"]rails_admin"),
        'administrate': re.compile(r"gem\s+['\"]administrate"),
        'active_storage': re.compile(r"has_one_attached|has_many_attached|ActiveStorage"),
        'shrine': re.compile(r"gem\s+['\"]shrine|include\s+\w*Shrine\w*Uploader"),
        'carrierwave': re.compile(r"gem\s+['\"]carrierwave|mount_uploader"),
        'ransack': re.compile(r"gem\s+['\"]ransack|\.ransack\b"),
        'searchkick': re.compile(r"gem\s+['\"]searchkick|searchkick\b"),
        'kamal': re.compile(r"gem\s+['\"]kamal"),
        'capistrano': re.compile(r"gem\s+['\"]capistrano"),
        'puma': re.compile(r"gem\s+['\"]puma"),
        'solid_cache': re.compile(r"gem\s+['\"]solid_cache"),
        'solid_cable': re.compile(r"gem\s+['\"]solid_cable"),
        'view_component': re.compile(r"gem\s+['\"]view_component|ViewComponent::Base"),
        'hotwire': re.compile(r"gem\s+['\"]hotwire-rails|turbo_stream_from"),
        'action_text': re.compile(r"has_rich_text|ActionText"),
        'action_mailbox': re.compile(r"ActionMailbox|ApplicationMailbox"),
        'kredis': re.compile(r"gem\s+['\"]kredis"),
    }

    def __init__(self):
        """Initialize the Rails parser."""
        pass

    def parse(self, content: str, file_path: str = "") -> RailsParseResult:
        """Parse Ruby source code for Rails-specific patterns."""
        result = RailsParseResult(file_path=file_path)

        # Check if this file uses Rails
        if not self.RAILS_REQUIRE.search(content):
            return result

        # Detect frameworks
        result.detected_frameworks = self._detect_frameworks(content)

        # Detect version
        result.rails_version = self._detect_version(content)

        # API mode detection
        result.is_api_only = bool(re.search(
            r"config\.api_only\s*=\s*true|class\s+\w+\s*<\s*ActionController::API",
            content,
        ))

        # Turbo/Stimulus/Hotwire detection
        result.has_turbo = bool(re.search(r"turbo_frame_tag|turbo_stream\b|Turbo::", content))
        result.has_stimulus = bool(re.search(r"data-controller|stimulus", content))
        result.has_hotwire = result.has_turbo or result.has_stimulus

        # Extract routes
        self._extract_routes(content, file_path, result)

        # Extract controllers
        self._extract_controllers(content, file_path, result)

        # Extract models
        self._extract_models(content, file_path, result)

        # Extract migrations
        self._extract_migrations(content, file_path, result)

        # Extract jobs
        self._extract_jobs(content, file_path, result)

        # Extract mailers
        self._extract_mailers(content, file_path, result)

        # Extract channels
        self._extract_channels(content, file_path, result)

        # Extract configs
        self._extract_configs(content, file_path, result)

        # Update totals
        result.total_routes = len(result.routes)
        result.total_models = len(result.models)
        result.total_controllers = len(result.controllers)

        return result

    def _extract_routes(self, content: str, file_path: str, result: RailsParseResult):
        """Extract Rails route definitions."""
        # Root route
        for m in self.ROUTE_ROOT.finditer(content):
            result.routes.append(RailsRouteInfo(
                method="root",
                path="/",
                controller=m.group(1),
                action=m.group(2),
                route_name="root",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Resource routes
        for m in self.ROUTE_RESOURCE.finditer(content):
            resource_name = m.group(1)
            opts = m.group(2) or ""
            is_singular = content[m.start():m.start() + 20].strip().startswith("resource ")
            result.routes.append(RailsRouteInfo(
                method="resources" if not is_singular else "resource",
                path=f"/{resource_name}",
                controller=resource_name,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # HTTP method routes
        for m in self.ROUTE_HTTP.finditer(content):
            result.routes.append(RailsRouteInfo(
                method=m.group(1).upper(),
                path=m.group(2),
                controller=m.group(3) or "",
                action=m.group(4) or "",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Namespace/scope
        for m in self.ROUTE_NAMESPACE.finditer(content):
            result.routes.append(RailsRouteInfo(
                method="namespace",
                path=f"/{m.group(1)}",
                namespace=m.group(1),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

        # Mount (engines/Sidekiq web, etc.)
        for m in self.ROUTE_MOUNT.finditer(content):
            result.routes.append(RailsRouteInfo(
                method="mount",
                path=m.group(2),
                controller=m.group(1),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _extract_controllers(self, content: str, file_path: str, result: RailsParseResult):
        """Extract Rails controller definitions."""
        for m in self.CONTROLLER_CLASS.finditer(content):
            ctrl = RailsControllerInfo(
                name=m.group(1),
                parent_class=m.group(2),
                is_api_controller="API" in m.group(2),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )

            # Extract actions
            for am in self.CONTROLLER_ACTION.finditer(content):
                ctrl.actions.append(am.group(1))

            # Extract before_actions
            for bm in self.BEFORE_ACTION.finditer(content):
                ctrl.before_actions.append(bm.group(2))

            # Extract after_actions
            for am_iter in self.AFTER_ACTION.finditer(content):
                ctrl.after_actions.append(am_iter.group(2))

            # Extract around_actions
            for am_iter in self.AROUND_ACTION.finditer(content):
                ctrl.around_actions.append(am_iter.group(1))

            # Extract skip_before_actions
            for sm in self.SKIP_BEFORE_ACTION.finditer(content):
                ctrl.skip_before_actions.append(sm.group(1))

            # Extract rescue_from handlers
            for rm in self.RESCUE_FROM.finditer(content):
                ctrl.rescue_handlers.append(rm.group(1))

            # Extract strong params method
            sp = self.STRONG_PARAMS.search(content)
            if sp:
                ctrl.strong_params_method = sp.group(1)

            # Extract concerns
            for cm in self.INCLUDE_CONCERN.finditer(content):
                ctrl.concerns.append(cm.group(1))

            result.controllers.append(ctrl)

    def _extract_models(self, content: str, file_path: str, result: RailsParseResult):
        """Extract Rails model definitions."""
        for m in self.MODEL_CLASS.finditer(content):
            model = RailsModelInfo(
                name=m.group(1),
                parent_class=m.group(2),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )

            # Associations
            for am in self.ASSOCIATION.finditer(content):
                assoc = {"type": am.group(1), "name": am.group(2)}
                opts = am.group(3)
                if opts:
                    assoc["options"] = opts.strip()[:100]
                model.associations.append(assoc)

            # Validations
            for vm in self.VALIDATION.finditer(content):
                val = {"field": vm.group(1)}
                opts = vm.group(2)
                if opts:
                    val["rules"] = opts.strip()[:100]
                model.validations.append(val)

            # Scopes
            for sm in self.SCOPE.finditer(content):
                model.scopes.append({
                    "name": sm.group(1),
                    "body": sm.group(2).strip()[:100],
                })

            # Callbacks
            for cm in self.CALLBACK.finditer(content):
                model.callbacks.append(f"{cm.group(1)}:{cm.group(2)}")

            # Enums
            for em in self.ENUM_DEF.finditer(content):
                model.enums.append({
                    "name": em.group(1),
                    "values": em.group(2).strip()[:100],
                })

            # Delegations
            for dm in self.DELEGATION.finditer(content):
                target = dm.group(2) or ""
                model.delegations.append(f"{dm.group(1).strip()} -> {target}")

            # STI detection
            model.has_sti = bool(re.search(
                r"self\.inheritance_column|self\.sti_name|type.*string",
                content,
            ))

            result.models.append(model)

    def _extract_migrations(self, content: str, file_path: str, result: RailsParseResult):
        """Extract Rails migration definitions."""
        for m in self.MIGRATION_CLASS.finditer(content):
            migration = RailsMigrationInfo(
                name=m.group(1),
                version=m.group(2) or "",
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )

            # Tables created
            for tm in self.CREATE_TABLE.finditer(content):
                migration.tables_created.append(tm.group(1))
                migration.operations.append(f"create_table:{tm.group(1)}")

            # Columns added
            for cm in self.ADD_COLUMN.finditer(content):
                migration.columns_added.append(f"{cm.group(1)}.{cm.group(2)}")
                migration.operations.append(f"add_column:{cm.group(1)}.{cm.group(2)}")

            # Indexes added
            for im in self.ADD_INDEX.finditer(content):
                migration.indexes_added.append(im.group(1))
                migration.operations.append(f"add_index:{im.group(1)}")

            result.migrations.append(migration)

    def _extract_jobs(self, content: str, file_path: str, result: RailsParseResult):
        """Extract Rails job definitions."""
        for m in self.JOB_CLASS.finditer(content):
            job = RailsJobInfo(
                name=m.group(1),
                is_active_job=True,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )

            # Queue
            qm = self.QUEUE_AS.search(content)
            if qm:
                job.queue = qm.group(1)

            # Retry
            rm = self.RETRY_ON.search(content)
            if rm:
                job.retry_count = 1

            result.jobs.append(job)

    def _extract_mailers(self, content: str, file_path: str, result: RailsParseResult):
        """Extract Rails mailer definitions."""
        for m in self.MAILER_CLASS.finditer(content):
            mailer = RailsMailerInfo(
                name=m.group(1),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )

            # Default from
            dm = self.MAILER_DEFAULT.search(content)
            if dm:
                mailer.default_from = dm.group(1)

            # Methods
            for mm in self.MAILER_METHOD.finditer(content):
                method_name = mm.group(1)
                if method_name not in ('initialize', 'self'):
                    mailer.methods.append(method_name)

            result.mailers.append(mailer)

    def _extract_channels(self, content: str, file_path: str, result: RailsParseResult):
        """Extract ActionCable channel definitions."""
        for m in self.CHANNEL_CLASS.finditer(content):
            channel = RailsChannelInfo(
                name=m.group(1),
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )

            channel.subscribed_method = bool(re.search(r"def\s+subscribed\b", content))

            # Stream for/from
            sf = self.STREAM_FOR.search(content)
            if sf:
                channel.stream_for = sf.group(1).strip()
            sf2 = self.STREAM_FROM.search(content)
            if sf2:
                channel.stream_for = sf2.group(1).strip()

            result.channels.append(channel)

    def _extract_configs(self, content: str, file_path: str, result: RailsParseResult):
        """Extract Rails configuration settings."""
        for m in self.RAILS_CONFIG.finditer(content):
            env = ""
            if "development" in file_path:
                env = "development"
            elif "production" in file_path:
                env = "production"
            elif "test" in file_path:
                env = "test"

            result.configs.append(RailsConfigInfo(
                setting=m.group(1),
                value=m.group(2).strip()[:100],
                environment=env,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            ))

    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect Rails ecosystem frameworks."""
        frameworks = []
        for name, pattern in self.FRAMEWORK_PATTERNS.items():
            if pattern.search(content):
                frameworks.append(name)
        return frameworks

    def _detect_version(self, content: str) -> str:
        """Detect Rails version from usage patterns."""
        # Rails 8 indicators
        if re.search(r"solid_queue|solid_cache|solid_cable|Kamal|Thruster", content):
            return "8.x"
        # Rails 7.1+ indicators
        if re.search(r"normalizes\b|generates_token_for\b|authenticate_by\b", content):
            return "7.1+"
        # Rails 7 indicators
        if re.search(r"import_map|turbo_stream_from|encrypt\b|Propshaft", content):
            return "7.x"
        # Rails 6 indicators
        if re.search(r"Webpacker|ApplicationRecord|multi_db|has_many_attached", content):
            return "6.x"
        # Rails 5 indicators
        if re.search(r"ApplicationRecord|ActionCable|api_only", content):
            return "5.x"
        # Rails 4 indicators
        if re.search(r"strong_parameters|concerns\b|turbolinks", content):
            return "4.x"
        # Generic
        if re.search(r"Rails\.application|ActiveRecord::Base", content):
            return "3.x+"
        return ""
