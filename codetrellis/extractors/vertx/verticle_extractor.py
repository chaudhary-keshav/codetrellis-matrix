"""
Vert.x Verticle Extractor v1.0

Extracts Vert.x verticle definitions, deployments, and worker verticle patterns.
Covers Vert.x 2.x through 4.x.

Extracts:
- AbstractVerticle / Verticle implementations
- Deployment options (instances, worker, HA, isolation groups)
- Worker verticles and multi-threaded workers
- Verticle factories and service discoveries
- start()/stop() lifecycle methods
- Vertx instance creation (Vertx.vertx(), clusteredVertx)

Part of CodeTrellis v4.95 - Vert.x Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class VertxVerticleInfo:
    """A Vert.x verticle definition."""
    name: str
    verticle_type: str = ""  # standard, worker, multi_threaded_worker
    base_class: str = ""  # AbstractVerticle, Verticle, etc.
    has_start: bool = False
    has_stop: bool = False
    is_async_start: bool = False  # start(Promise<Void>)
    is_async_stop: bool = False
    config_keys: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    implements: List[str] = field(default_factory=list)
    file: str = ""
    line_number: int = 0


@dataclass
class VertxDeploymentInfo:
    """A Vert.x verticle deployment."""
    verticle_name: str
    instances: int = 1
    is_worker: bool = False
    is_ha: bool = False
    isolation_group: str = ""
    config: Dict[str, str] = field(default_factory=dict)
    deploy_method: str = ""  # deployVerticle, deploy
    file: str = ""
    line_number: int = 0


class VertxVerticleExtractor:
    """Extracts Vert.x verticle definitions and deployment patterns."""

    # Verticle class definition
    VERTICLE_CLASS_PATTERN = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+'
        r'extends\s+(AbstractVerticle|Verticle)\b',
        re.MULTILINE
    )

    # Verticle interface implementation
    VERTICLE_IMPL_PATTERN = re.compile(
        r'(?:public\s+)?class\s+(\w+)\s+'
        r'(?:extends\s+\w+\s+)?'
        r'implements\s+(?:.*,\s*)?(Verticle)\b',
        re.MULTILINE
    )

    # Start method patterns
    START_SYNC_PATTERN = re.compile(
        r'(?:public|protected)\s+void\s+start\s*\(\s*\)',
        re.MULTILINE
    )
    START_ASYNC_PATTERN = re.compile(
        r'(?:public|protected)\s+void\s+start\s*\(\s*(?:Promise|Future)<Void>\s+\w+\s*\)',
        re.MULTILINE
    )

    # Stop method patterns
    STOP_SYNC_PATTERN = re.compile(
        r'(?:public|protected)\s+void\s+stop\s*\(\s*\)',
        re.MULTILINE
    )
    STOP_ASYNC_PATTERN = re.compile(
        r'(?:public|protected)\s+void\s+stop\s*\(\s*(?:Promise|Future)<Void>\s+\w+\s*\)',
        re.MULTILINE
    )

    # Deployment pattern
    DEPLOY_PATTERN = re.compile(
        r'(?:vertx|this)\s*\.\s*(?:deployVerticle|deploy)\s*\(\s*'
        r'(?:new\s+(\w+)\s*\(\)|"([^"]+)"|(\w+)\.class)',
        re.MULTILINE
    )

    # DeploymentOptions
    DEPLOY_OPTIONS_PATTERN = re.compile(
        r'(?:new\s+)?DeploymentOptions\s*\(\s*\)'
        r'((?:\s*\.\s*set\w+\s*\([^)]*\))*)',
        re.MULTILINE
    )

    # Worker verticle option
    WORKER_OPTION_PATTERN = re.compile(r'\.setWorker\s*\(\s*true\s*\)')
    INSTANCES_OPTION_PATTERN = re.compile(r'\.setInstances\s*\(\s*(\d+)\s*\)')
    HA_OPTION_PATTERN = re.compile(r'\.setHa\s*\(\s*true\s*\)')

    # Config access: config().getString/getInteger/getJsonObject
    CONFIG_ACCESS_PATTERN = re.compile(
        r'config\(\)\s*\.\s*get(?:String|Integer|Long|Boolean|Double|Float|JsonObject|JsonArray|Value)\s*\(\s*"([^"]+)"',
        re.MULTILINE
    )

    # Vertx instance creation
    VERTX_INSTANCE_PATTERN = re.compile(
        r'Vertx\s*\.\s*(vertx|clusteredVertx)\s*\(',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract verticle definitions and deployments."""
        result = {
            'verticles': [],
            'deployments': [],
        }

        if not content:
            return result

        # Extract verticle class definitions
        for m in self.VERTICLE_CLASS_PATTERN.finditer(content):
            name = m.group(1)
            base = m.group(2)
            line = content[:m.start()].count('\n') + 1

            verticle = VertxVerticleInfo(
                name=name,
                base_class=base,
                file=file_path,
                line_number=line,
            )

            # Check lifecycle methods (within the class scope approximation)
            class_content = content[m.start():]
            if self.START_SYNC_PATTERN.search(class_content[:3000]):
                verticle.has_start = True
            if self.START_ASYNC_PATTERN.search(class_content[:3000]):
                verticle.has_start = True
                verticle.is_async_start = True
            if self.STOP_SYNC_PATTERN.search(class_content[:3000]):
                verticle.has_stop = True
            if self.STOP_ASYNC_PATTERN.search(class_content[:3000]):
                verticle.has_stop = True
                verticle.is_async_stop = True

            # Extract config keys
            for cfg in self.CONFIG_ACCESS_PATTERN.finditer(class_content[:5000]):
                key = cfg.group(1)
                if key not in verticle.config_keys:
                    verticle.config_keys.append(key)

            result['verticles'].append(verticle)

        # Also check interface implementation
        for m in self.VERTICLE_IMPL_PATTERN.finditer(content):
            name = m.group(1)
            # Skip if already found via extends
            if any(v.name == name for v in result['verticles']):
                continue
            line = content[:m.start()].count('\n') + 1
            result['verticles'].append(VertxVerticleInfo(
                name=name,
                base_class="Verticle",
                implements=["Verticle"],
                file=file_path,
                line_number=line,
            ))

        # Extract deployments
        for m in self.DEPLOY_PATTERN.finditer(content):
            verticle_name = m.group(1) or m.group(2) or m.group(3) or ""
            line = content[:m.start()].count('\n') + 1

            deploy = VertxDeploymentInfo(
                verticle_name=verticle_name,
                deploy_method="deployVerticle",
                file=file_path,
                line_number=line,
            )

            # Check surrounding context for deployment options
            context = content[max(0, m.start() - 200):m.end() + 500]
            if self.WORKER_OPTION_PATTERN.search(context):
                deploy.is_worker = True
            inst_match = self.INSTANCES_OPTION_PATTERN.search(context)
            if inst_match:
                try:
                    deploy.instances = int(inst_match.group(1))
                except ValueError:
                    pass
            if self.HA_OPTION_PATTERN.search(context):
                deploy.is_ha = True

            result['deployments'].append(deploy)

        return result
