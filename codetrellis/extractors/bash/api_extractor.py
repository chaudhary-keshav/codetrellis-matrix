"""
Bash/Shell API Extractor for CodeTrellis

Extracts API-related patterns from Bash/Shell source files.

Supports:
- HTTP calls: curl, wget, httpie (http/https)
- Cron job definitions: crontab patterns
- Systemd service definitions
- Docker commands: docker run, docker-compose, docker build
- Kubernetes commands: kubectl, helm
- Cloud CLI: aws, gcloud, az
- Package manager commands: apt, yum, brew, pip, npm
- Database CLI: mysql, psql, redis-cli, mongo

Part of CodeTrellis v4.18 - Bash/Shell Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class BashHTTPCallInfo:
    """Information about an HTTP API call in a script."""
    tool: str = ""                 # curl, wget, httpie
    url: str = ""
    method: str = "GET"            # GET, POST, PUT, DELETE, PATCH
    line_number: int = 0
    has_auth: bool = False         # -H "Authorization:", --user
    has_data: bool = False         # -d, --data
    content_type: str = ""         # application/json, etc.
    headers: List[str] = field(default_factory=list)


@dataclass
class BashCronJobInfo:
    """Information about a cron job definition."""
    schedule: str = ""             # "0 * * * *"
    command: str = ""
    line_number: int = 0
    description: str = ""
    is_reboot: bool = False        # @reboot


@dataclass
class BashServiceInfo:
    """Information about a service management command."""
    service_type: str = ""         # docker, kubernetes, systemd, cloud
    command: str = ""              # run, build, deploy, apply
    target: str = ""               # image name, service name, etc.
    line_number: int = 0
    flags: List[str] = field(default_factory=list)


class BashAPIExtractor:
    """
    Extracts API and service management patterns from Bash/Shell scripts.
    """

    # Curl patterns
    CURL_PATTERN = re.compile(
        r'curl\s+(.*?)(?:\s*(?:[\n;|&]|$))',
        re.MULTILINE | re.DOTALL
    )

    # Wget patterns
    WGET_PATTERN = re.compile(
        r'wget\s+(.*?)(?:\s*(?:[\n;|&]|$))',
        re.MULTILINE
    )

    # httpie patterns
    HTTPIE_PATTERN = re.compile(
        r'\bhttp\s+(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)?\s*(https?://\S+)',
        re.MULTILINE
    )

    # Cron job: standard 5-field + @reboot
    CRON_PATTERN = re.compile(
        r'^((?:\d+|\*|\*/\d+)(?:\s+(?:\d+|\*|\*/\d+)){4})\s+(.+)$',
        re.MULTILINE
    )
    CRON_REBOOT = re.compile(
        r'^@reboot\s+(.+)$',
        re.MULTILINE
    )

    # Docker commands
    DOCKER_PATTERN = re.compile(
        r'\b(docker(?:-compose)?|podman)\s+(run|build|exec|push|pull|stop|start|restart|logs|compose\s+\w+)\s*(.*?)(?:\s*[;\n|&]|$)',
        re.MULTILINE
    )

    # Kubernetes commands
    K8S_PATTERN = re.compile(
        r'\b(kubectl|helm|k9s|minikube|kind)\s+(apply|create|delete|get|describe|rollout|deploy|install|upgrade|scale)\s*(.*?)(?:\s*[;\n|&]|$)',
        re.MULTILINE
    )

    # Cloud CLI commands
    CLOUD_PATTERN = re.compile(
        r'\b(aws|gcloud|az|terraform|pulumi|cdktf)\s+(\S+)\s*(.*?)(?:\s*[;\n|&]|$)',
        re.MULTILINE
    )

    # Systemd commands
    SYSTEMD_PATTERN = re.compile(
        r'\b(systemctl|service)\s+(start|stop|restart|enable|disable|status|reload)\s+(\S+)',
        re.MULTILINE
    )

    # Database CLI
    DB_CLI_PATTERN = re.compile(
        r'\b(mysql|psql|redis-cli|mongo|mongosh|sqlite3|sqlcmd)\s+(.*?)(?:\s*[;\n|&]|$)',
        re.MULTILINE
    )

    # Package managers
    PKG_PATTERN = re.compile(
        r'\b(apt-get|apt|yum|dnf|apk|brew|pip|pip3|npm|yarn|pnpm|cargo|go\s+install)\s+(install|add|remove|update|upgrade)\s+(.*?)(?:\s*[;\n|&]|$)',
        re.MULTILINE
    )

    # URL pattern for extracting URLs from curl/wget args
    URL_PATTERN = re.compile(r'(https?://[^\s\'"]+)')

    # HTTP method from curl
    CURL_METHOD = re.compile(r'-X\s*(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)')

    # Auth patterns in curl
    AUTH_PATTERN = re.compile(r'(-H\s*["\']Authorization:|--user\s|--basic|--digest|-u\s)')

    # Data patterns in curl
    DATA_PATTERN = re.compile(r'(-d\s|--data\s|--data-raw\s|--json\s)')

    # Content-Type header
    CONTENT_TYPE = re.compile(r'Content-Type:\s*(\S+)')

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract API and service patterns from Bash/Shell source.

        Args:
            content: Shell script content
            file_path: Path to source file

        Returns:
            Dict with 'http_calls', 'cron_jobs', 'services', 'db_commands', 'packages'
        """
        http_calls = []
        cron_jobs = []
        services = []
        db_commands = []
        packages = []

        # Extract curl calls
        for match in self.CURL_PATTERN.finditer(content):
            args = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Extract URL
            url_match = self.URL_PATTERN.search(args)
            url = url_match.group(1) if url_match else ""

            # Extract method
            method_match = self.CURL_METHOD.search(args)
            method = method_match.group(1) if method_match else "GET"
            if self.DATA_PATTERN.search(args) and not method_match:
                method = "POST"

            # Check auth
            has_auth = bool(self.AUTH_PATTERN.search(args))
            has_data = bool(self.DATA_PATTERN.search(args))

            # Content type
            ct_match = self.CONTENT_TYPE.search(args)
            content_type = ct_match.group(1) if ct_match else ""

            # Extract headers
            headers = re.findall(r'-H\s*["\']([^"\']+)["\']', args)

            http_calls.append(BashHTTPCallInfo(
                tool="curl",
                url=url,
                method=method,
                line_number=line_num,
                has_auth=has_auth,
                has_data=has_data,
                content_type=content_type,
                headers=headers[:5],
            ))

        # Extract wget calls
        for match in self.WGET_PATTERN.finditer(content):
            args = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            url_match = self.URL_PATTERN.search(args)
            if url_match:
                http_calls.append(BashHTTPCallInfo(
                    tool="wget",
                    url=url_match.group(1),
                    method="GET",
                    line_number=line_num,
                ))

        # Extract httpie calls
        for match in self.HTTPIE_PATTERN.finditer(content):
            method = match.group(1) or "GET"
            url = match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            http_calls.append(BashHTTPCallInfo(
                tool="httpie",
                url=url,
                method=method,
                line_number=line_num,
            ))

        # Extract cron jobs
        for match in self.CRON_PATTERN.finditer(content):
            schedule = match.group(1)
            command = match.group(2).strip()
            line_num = content[:match.start()].count('\n') + 1
            cron_jobs.append(BashCronJobInfo(
                schedule=schedule,
                command=command,
                line_number=line_num,
            ))

        for match in self.CRON_REBOOT.finditer(content):
            command = match.group(1).strip()
            line_num = content[:match.start()].count('\n') + 1
            cron_jobs.append(BashCronJobInfo(
                schedule="@reboot",
                command=command,
                line_number=line_num,
                is_reboot=True,
            ))

        # Extract Docker commands
        for match in self.DOCKER_PATTERN.finditer(content):
            tool = match.group(1)
            action = match.group(2)
            args = match.group(3).strip()
            line_num = content[:match.start()].count('\n') + 1

            target = ""
            flag_list = []
            for part in args.split():
                if part.startswith('-'):
                    flag_list.append(part)
                elif not target:
                    target = part

            services.append(BashServiceInfo(
                service_type="docker" if "docker" in tool else "podman",
                command=action,
                target=target,
                line_number=line_num,
                flags=flag_list[:5],
            ))

        # Extract Kubernetes commands
        for match in self.K8S_PATTERN.finditer(content):
            tool = match.group(1)
            action = match.group(2)
            args = match.group(3).strip()
            line_num = content[:match.start()].count('\n') + 1

            target = ""
            for part in args.split():
                if not part.startswith('-'):
                    target = part
                    break

            services.append(BashServiceInfo(
                service_type="kubernetes",
                command=f"{tool} {action}",
                target=target,
                line_number=line_num,
            ))

        # Extract cloud CLI
        for match in self.CLOUD_PATTERN.finditer(content):
            tool = match.group(1)
            subcommand = match.group(2)
            line_num = content[:match.start()].count('\n') + 1

            services.append(BashServiceInfo(
                service_type="cloud",
                command=f"{tool} {subcommand}",
                line_number=line_num,
            ))

        # Extract systemd
        for match in self.SYSTEMD_PATTERN.finditer(content):
            tool = match.group(1)
            action = match.group(2)
            target = match.group(3)
            line_num = content[:match.start()].count('\n') + 1

            services.append(BashServiceInfo(
                service_type="systemd",
                command=action,
                target=target,
                line_number=line_num,
            ))

        # Extract database CLI
        for match in self.DB_CLI_PATTERN.finditer(content):
            tool = match.group(1)
            args = match.group(2).strip()
            line_num = content[:match.start()].count('\n') + 1

            db_commands.append({
                'tool': tool,
                'args': args[:80],
                'line': line_num,
            })

        # Extract package manager commands
        for match in self.PKG_PATTERN.finditer(content):
            tool = match.group(1)
            action = match.group(2)
            pkgs = match.group(3).strip()
            line_num = content[:match.start()].count('\n') + 1

            packages.append({
                'manager': tool,
                'action': action,
                'packages': pkgs[:100],
                'line': line_num,
            })

        return {
            'http_calls': http_calls,
            'cron_jobs': cron_jobs,
            'services': services,
            'db_commands': db_commands,
            'packages': packages,
        }
