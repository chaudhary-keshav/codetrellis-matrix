"""
Vert.x API Extractor v1.0

Extracts Vert.x WebSocket, auth, cluster, and service proxy patterns.
Covers Vert.x 2.x through 4.x.

Part of CodeTrellis v4.95 - Vert.x Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class VertxWebSocketInfo:
    """A Vert.x WebSocket handler."""
    path: str = ""
    handler_type: str = ""  # server, client, sockjs
    file: str = ""
    line_number: int = 0


@dataclass
class VertxAuthProviderInfo:
    """A Vert.x auth provider."""
    auth_type: str = ""  # jwt, oauth2, basic, shiro, htdigest, ldap, mongo, sql
    provider_class: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class VertxClusterInfo:
    """A Vert.x cluster configuration."""
    cluster_manager: str = ""  # hazelcast, infinispan, ignite, zookeeper
    file: str = ""
    line_number: int = 0


@dataclass
class VertxServiceProxyInfo:
    """A Vert.x service proxy."""
    service_interface: str = ""
    address: str = ""
    is_proxy: bool = False  # vs implementation
    file: str = ""
    line_number: int = 0


class VertxApiExtractor:
    """Extracts Vert.x WebSocket, auth, cluster, and service proxy patterns."""

    # WebSocket server: httpServer.webSocketHandler(...) or router.route("/ws").handler(SockJSHandler...)
    WS_SERVER_PATTERN = re.compile(
        r'\.webSocketHandler\s*\(|\.webSocket\s*\(\s*"([^"]*)"',
        re.MULTILINE
    )

    # SockJS handler
    SOCKJS_PATTERN = re.compile(
        r'SockJSHandler\s*\.\s*create\s*\(',
        re.MULTILINE
    )

    # Auth providers
    JWT_AUTH_PATTERN = re.compile(r'JWTAuth\s*\.\s*create\s*\(', re.MULTILINE)
    OAUTH2_AUTH_PATTERN = re.compile(r'OAuth2Auth\s*\.\s*create\s*\(', re.MULTILINE)
    BASIC_AUTH_PATTERN = re.compile(r'BasicAuthHandler\s*\.\s*create\s*\(', re.MULTILINE)
    HTDIGEST_AUTH_PATTERN = re.compile(r'HtdigestAuth\s*\.\s*create\s*\(', re.MULTILINE)
    SHIRO_AUTH_PATTERN = re.compile(r'ShiroAuth\s*\.\s*create\s*\(', re.MULTILINE)
    LDAP_AUTH_PATTERN = re.compile(r'LdapAuthentication\s*\.\s*create\s*\(', re.MULTILINE)
    MONGO_AUTH_PATTERN = re.compile(r'MongoAuthentication\s*\.\s*create\s*\(', re.MULTILINE)
    SQL_AUTH_PATTERN = re.compile(r'SqlAuthentication\s*\.\s*create\s*\(', re.MULTILINE)

    # Cluster managers
    HAZELCAST_PATTERN = re.compile(r'HazelcastClusterManager', re.MULTILINE)
    INFINISPAN_PATTERN = re.compile(r'InfinispanClusterManager', re.MULTILINE)
    IGNITE_PATTERN = re.compile(r'IgniteClusterManager', re.MULTILINE)
    ZOOKEEPER_PATTERN = re.compile(r'ZookeeperClusterManager', re.MULTILINE)

    # Service proxy: @ProxyGen annotation or ServiceBinder
    PROXY_GEN_PATTERN = re.compile(r'@ProxyGen', re.MULTILINE)
    SERVICE_BINDER_PATTERN = re.compile(
        r'new\s+ServiceBinder\s*\(\s*\w+\s*\)\s*\.\s*setAddress\s*\(\s*"([^"]+)"',
        re.MULTILINE
    )
    SERVICE_PROXY_PATTERN = re.compile(
        r'(\w+)\s*\.\s*createProxy\s*\(\s*(\w+)\.class\s*,\s*"([^"]+)"',
        re.MULTILINE
    )

    # HTTP server creation
    HTTP_SERVER_PATTERN = re.compile(
        r'vertx\s*\.\s*createHttpServer\s*\(',
        re.MULTILINE
    )

    # gRPC server
    GRPC_SERVER_PATTERN = re.compile(
        r'GrpcServer\s*\.\s*server\s*\(|VertxServer\s*\.\s*create\s*\(',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """Extract WebSocket, auth, cluster, and service proxy patterns."""
        result = {
            'websockets': [],
            'auth_providers': [],
            'clusters': [],
            'service_proxies': [],
        }

        if not content:
            return result

        # WebSocket handlers
        for m in self.WS_SERVER_PATTERN.finditer(content):
            path = m.group(1) if m.group(1) else ""
            line = content[:m.start()].count('\n') + 1
            result['websockets'].append(VertxWebSocketInfo(
                path=path, handler_type='server',
                file=file_path, line_number=line,
            ))

        for m in self.SOCKJS_PATTERN.finditer(content):
            line = content[:m.start()].count('\n') + 1
            result['websockets'].append(VertxWebSocketInfo(
                handler_type='sockjs', file=file_path, line_number=line,
            ))

        # Auth providers
        auth_patterns = [
            (self.JWT_AUTH_PATTERN, 'jwt', 'JWTAuth'),
            (self.OAUTH2_AUTH_PATTERN, 'oauth2', 'OAuth2Auth'),
            (self.BASIC_AUTH_PATTERN, 'basic', 'BasicAuthHandler'),
            (self.HTDIGEST_AUTH_PATTERN, 'htdigest', 'HtdigestAuth'),
            (self.SHIRO_AUTH_PATTERN, 'shiro', 'ShiroAuth'),
            (self.LDAP_AUTH_PATTERN, 'ldap', 'LdapAuthentication'),
            (self.MONGO_AUTH_PATTERN, 'mongo', 'MongoAuthentication'),
            (self.SQL_AUTH_PATTERN, 'sql', 'SqlAuthentication'),
        ]
        for pattern, auth_type, provider_class in auth_patterns:
            for m in pattern.finditer(content):
                line = content[:m.start()].count('\n') + 1
                result['auth_providers'].append(VertxAuthProviderInfo(
                    auth_type=auth_type, provider_class=provider_class,
                    file=file_path, line_number=line,
                ))

        # Cluster managers
        cluster_patterns = [
            (self.HAZELCAST_PATTERN, 'hazelcast'),
            (self.INFINISPAN_PATTERN, 'infinispan'),
            (self.IGNITE_PATTERN, 'ignite'),
            (self.ZOOKEEPER_PATTERN, 'zookeeper'),
        ]
        for pattern, manager in cluster_patterns:
            for m in pattern.finditer(content):
                line = content[:m.start()].count('\n') + 1
                result['clusters'].append(VertxClusterInfo(
                    cluster_manager=manager, file=file_path, line_number=line,
                ))

        # Service proxies
        for m in self.SERVICE_BINDER_PATTERN.finditer(content):
            address = m.group(1)
            line = content[:m.start()].count('\n') + 1
            result['service_proxies'].append(VertxServiceProxyInfo(
                address=address, is_proxy=False,
                file=file_path, line_number=line,
            ))

        for m in self.SERVICE_PROXY_PATTERN.finditer(content):
            service_interface = m.group(2)
            address = m.group(3)
            line = content[:m.start()].count('\n') + 1
            result['service_proxies'].append(VertxServiceProxyInfo(
                service_interface=service_interface, address=address, is_proxy=True,
                file=file_path, line_number=line,
            ))

        return result
