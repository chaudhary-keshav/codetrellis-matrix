"""
Tests for EnhancedBashParser — full integration parser tests.

Part of CodeTrellis v4.18 Bash Language Support.
"""

import pytest
from codetrellis.bash_parser_enhanced import EnhancedBashParser, BashParseResult


@pytest.fixture
def parser():
    return EnhancedBashParser()


# ===== BASIC PARSING =====

class TestBasicParsing:
    """Tests for basic parsing functionality."""

    def test_empty_script(self, parser):
        result = parser.parse("", "empty.sh")
        assert isinstance(result, BashParseResult)
        assert result.file_path == "empty.sh"
        assert len(result.functions) == 0

    def test_comment_only_script(self, parser):
        code = '''#!/bin/bash
# This is just a comment
# Nothing else
'''
        result = parser.parse(code, "comments.sh")
        assert isinstance(result, BashParseResult)
        assert result.comment_lines >= 2

    def test_shebang_detection_bash(self, parser):
        code = '''#!/usr/bin/env bash
echo "hello"
'''
        result = parser.parse(code, "test.sh")
        assert result.shebang is not None
        assert result.shebang.shell_type == "bash"

    def test_shebang_detection_sh(self, parser):
        code = '''#!/bin/sh
echo "hello"
'''
        result = parser.parse(code, "test.sh")
        assert result.shebang is not None
        assert result.shebang.shell_type == "sh"

    def test_shebang_detection_zsh(self, parser):
        code = '''#!/usr/bin/env zsh
echo "hello"
'''
        result = parser.parse(code, "test.zsh")
        assert result.shebang is not None
        assert result.shebang.shell_type == "zsh"


# ===== FUNCTION INTEGRATION =====

class TestFunctionIntegration:
    """Tests for function extraction via parser."""

    def test_functions_extracted(self, parser):
        code = '''#!/bin/bash
setup() {
    echo "setting up"
}

teardown() {
    echo "tearing down"
}

main() {
    setup
    teardown
}
main "$@"
'''
        result = parser.parse(code, "script.sh")
        assert len(result.functions) >= 3
        names = [f.name for f in result.functions]
        assert "setup" in names
        assert "teardown" in names
        assert "main" in names


# ===== VARIABLE INTEGRATION =====

class TestVariableIntegration:
    """Tests for variable extraction via parser."""

    def test_variables_and_exports(self, parser):
        code = '''#!/bin/bash
export PATH="/usr/local/bin:$PATH"
readonly MAX_RETRIES=3
VERBOSE=false
declare -a SERVERS=("web1" "web2" "web3")
'''
        result = parser.parse(code, "config.sh")
        assert len(result.exports) >= 1
        assert len(result.variables) >= 1 or len(result.arrays) >= 1


# ===== COMMAND INTEGRATION =====

class TestCommandIntegration:
    """Tests for command-level extraction via parser."""

    def test_pipeline_detection(self, parser):
        code = '''#!/bin/bash
find . -name "*.log" | grep ERROR | wc -l
ps aux | grep nginx | grep -v grep
'''
        result = parser.parse(code, "pipes.sh")
        assert len(result.pipelines) >= 1

    def test_trap_detection(self, parser):
        code = '''#!/bin/bash
cleanup() { rm -f /tmp/lock; }
trap cleanup EXIT
trap 'echo "interrupted"' INT TERM
'''
        result = parser.parse(code, "traps.sh")
        assert len(result.traps) >= 1

    def test_heredoc_detection(self, parser):
        code = '''#!/bin/bash
cat <<EOF
Hello World
This is a heredoc
EOF

cat <<-INDENT
	Indented heredoc
INDENT
'''
        result = parser.parse(code, "heredocs.sh")
        assert len(result.heredocs) >= 1


# ===== API/SERVICE INTEGRATION =====

class TestAPIIntegration:
    """Tests for API and service extraction via parser."""

    def test_curl_detection(self, parser):
        code = '''#!/bin/bash
curl -X POST https://api.example.com/data \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"key": "value"}'

wget -q https://releases.example.com/latest.tar.gz
'''
        result = parser.parse(code, "api.sh")
        assert len(result.http_calls) >= 1

    def test_docker_detection(self, parser):
        code = '''#!/bin/bash
docker build -t myapp:latest .
docker run -d -p 8080:80 myapp:latest
docker-compose up -d
'''
        result = parser.parse(code, "deploy.sh")
        assert len(result.services) >= 1

    def test_kubernetes_detection(self, parser):
        code = '''#!/bin/bash
kubectl apply -f deployment.yaml
kubectl get pods -n production
kubectl rollout status deployment/myapp
'''
        result = parser.parse(code, "k8s.sh")
        assert len(result.services) >= 1


# ===== ALIAS & SOURCE INTEGRATION =====

class TestAliasSourceIntegration:
    """Tests for alias and source extraction via parser."""

    def test_alias_detection(self, parser):
        code = '''#!/bin/bash
alias ll='ls -la'
alias gs='git status'
alias dc='docker-compose'
'''
        result = parser.parse(code, "aliases.sh")
        assert len(result.aliases) >= 2

    def test_source_detection(self, parser):
        code = '''#!/bin/bash
source /etc/profile
. ~/.bashrc
if [[ -f ~/.local_config ]]; then
    source ~/.local_config
fi
'''
        result = parser.parse(code, "init.sh")
        assert len(result.sources) >= 2


# ===== FRAMEWORK DETECTION =====

class TestFrameworkDetection:
    """Tests for framework/tool detection."""

    def test_docker_framework(self, parser):
        code = '''#!/bin/bash
docker build -t myapp .
docker push myapp:latest
'''
        result = parser.parse(code, "ci.sh")
        assert "docker" in result.detected_frameworks

    def test_aws_framework(self, parser):
        code = '''#!/bin/bash
aws s3 cp data.tar.gz s3://my-bucket/
aws ec2 describe-instances
'''
        result = parser.parse(code, "aws.sh")
        assert any("aws" in fw for fw in result.detected_frameworks)

    def test_git_framework(self, parser):
        code = '''#!/bin/bash
git clone https://github.com/user/repo.git
git checkout -b feature/new
git push origin feature/new
'''
        result = parser.parse(code, "git.sh")
        assert "git" in result.detected_frameworks


# ===== STRICT MODE DETECTION =====

class TestStrictMode:
    """Tests for strict mode detection."""

    def test_strict_mode_detection(self, parser):
        code = '''#!/bin/bash
set -euo pipefail
echo "strict"
'''
        result = parser.parse(code, "strict.sh")
        assert result.has_strict_mode is True

    def test_no_strict_mode(self, parser):
        code = '''#!/bin/bash
echo "no strict mode"
'''
        result = parser.parse(code, "no_strict.sh")
        assert result.has_strict_mode is False


# ===== LINE COUNTING =====

class TestLineCounting:
    """Tests for line counting."""

    def test_total_lines(self, parser):
        code = '''#!/bin/bash
# Comment
echo "hello"

echo "world"
'''
        result = parser.parse(code, "lines.sh")
        assert result.total_lines >= 4
        assert result.comment_lines >= 1
        assert result.blank_lines >= 1


# ===== COMPLEX SCRIPT =====

class TestComplexScript:
    """Tests for complex real-world-like scripts."""

    def test_deployment_script(self, parser):
        code = '''#!/usr/bin/env bash
set -euo pipefail

readonly VERSION="1.0.0"
readonly APP_NAME="myapp"
readonly DEPLOY_DIR="/opt/deploy"

# Logging
log_info()  { echo "[INFO]  $(date +%T) $*" >&2; }
log_error() { echo "[ERROR] $(date +%T) $*" >&2; }

# Cleanup handler
cleanup() {
    local exit_code=$?
    rm -rf "${TMPDIR:-/tmp}/${APP_NAME}_deploy"
    exit "$exit_code"
}
trap cleanup EXIT

# Build the application
build() {
    log_info "Building ${APP_NAME} v${VERSION}"
    docker build -t "${APP_NAME}:${VERSION}" .
    docker push "${APP_NAME}:${VERSION}"
}

# Deploy to Kubernetes
deploy() {
    local environment="${1:?Environment required}"
    log_info "Deploying to ${environment}"
    kubectl apply -f "k8s/${environment}/"
    kubectl rollout status "deployment/${APP_NAME}" -n "${environment}"
}

# Health check
health_check() {
    local url="https://${APP_NAME}.example.com/health"
    local retries=10
    local -i i=0
    while (( i < retries )); do
        if curl -sf "$url" > /dev/null 2>&1; then
            log_info "Health check passed"
            return 0
        fi
        sleep 5
        (( i++ ))
    done
    log_error "Health check failed after ${retries} retries"
    return 1
}

main() {
    build
    deploy "${1:-staging}"
    health_check
}
main "$@"
'''
        result = parser.parse(code, "deploy.sh")

        # Should detect functions
        assert len(result.functions) >= 5
        func_names = [f.name for f in result.functions]
        assert "build" in func_names
        assert "deploy" in func_names
        assert "health_check" in func_names
        assert "main" in func_names
        assert "cleanup" in func_names

        # Should detect strict mode
        assert result.has_strict_mode is True

        # Should detect shebang
        assert result.shebang is not None
        assert result.shebang.shell_type == "bash"

        # Should detect exports/variables
        assert len(result.variables) >= 1 or len(result.exports) >= 1

        # Should detect traps
        assert len(result.traps) >= 1

        # Should detect frameworks
        assert "docker" in result.detected_frameworks
        assert "kubernetes" in result.detected_frameworks

        # Should detect HTTP calls
        assert len(result.http_calls) >= 1

        # Should detect services
        assert len(result.services) >= 1


# ===== STATIC HELPER =====

class TestStaticHelper:
    """Tests for static is_shell_script helper."""

    def test_is_shell_script_by_extension(self):
        assert EnhancedBashParser.is_shell_script("script.sh") is True
        assert EnhancedBashParser.is_shell_script("script.bash") is True
        assert EnhancedBashParser.is_shell_script("script.zsh") is True
        assert EnhancedBashParser.is_shell_script("script.py") is False
        assert EnhancedBashParser.is_shell_script("script.js") is False
