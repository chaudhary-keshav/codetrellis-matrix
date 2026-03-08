#!/usr/bin/env python3
"""
CodeTrellis Validation Findings Generator
====================================
Reads all validation-results/*.prompt files and generates a comprehensive
VALIDATION_FINDINGS.md with per-repo quality analysis and improvement items.

Usage:
    python3 generate_findings.py
    python3 generate_findings.py --results-dir ./validation-results
    python3 generate_findings.py --output VALIDATION_FINDINGS.md
"""

import csv
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime


# Known correct domains for repos
KNOWN_DOMAINS = {
    # Category 1: Full-Stack Applications
    "calcom/cal.com": "Scheduling/Calendar",
    "medusajs/medusa": "E-Commerce",
    "formbricks/formbricks": "Survey/Forms",
    "documenso/documenso": "Document Signing",
    "twentyhq/twenty": "CRM",
    "hoppscotch/hoppscotch": "API Development Tool",
    "immich-app/immich": "Photo Management",
    "maybe-finance/maybe": "Personal Finance",
    "appwrite/appwrite": "Backend-as-a-Service",
    "logto-io/logto": "Authentication/Identity",

    # Category 2: Microservices & Backend
    "nestjs/nest": "Backend Framework",
    "fastapi/fastapi": "Backend Framework",
    "pallets/flask": "Backend Framework",
    "tiangolo/full-stack-fastapi-template": "Full-Stack Template",
    "GoogleCloudPlatform/microservices-demo": "Microservices Demo",
    "dotnet/eShop": "E-Commerce Microservices",
    "gothinkster/realworld": "Full-Stack Spec/Demo",
    "amplication/amplication": "Code Generation Platform",
    "backstage/backstage": "Developer Portal",
    "supabase/supabase": "Backend-as-a-Service",

    # Category 3: AI/ML Projects
    "langchain-ai/langchain": "AI/LLM Framework",
    "openai/openai-cookbook": "AI Documentation/Tutorials",
    "run-llama/llama_index": "AI/RAG Framework",
    "huggingface/transformers": "ML Framework",
    "mlflow/mlflow": "ML Experiment Tracking",
    "bentoml/BentoML": "ML Model Serving",
    "ray-project/ray": "Distributed Computing",
    "qdrant/qdrant": "Vector Database",
    "chroma-core/chroma": "Vector Database",
    "open-webui/open-webui": "AI Chat Interface",

    # Category 4: DevTools & Infrastructure
    "grafana/grafana": "Observability Platform",
    "prometheus/prometheus": "Monitoring System",
    "traefik/traefik": "Reverse Proxy/Load Balancer",
    "hashicorp/terraform": "Infrastructure as Code",
    "docker/compose": "Container Orchestration",
    "pulumi/pulumi": "Infrastructure as Code",
    "n8n-io/n8n": "Workflow Automation",
    "nocodb/nocodb": "Database UI/Airtable Alternative",
    "strapi/strapi": "Headless CMS",
    "directus/directus": "Data Platform/Headless CMS",

    # Category 5: Frontend Frameworks
    "angular/angular": "Frontend Framework",
    "vercel/next.js": "React Meta-Framework",
    "vuejs/core": "Frontend Framework",
    "sveltejs/svelte": "Frontend Framework/Compiler",
    "shadcn-ui/ui": "UI Component Library",
    "ionic-team/ionic-framework": "Cross-Platform UI Framework",
    "ant-design/ant-design": "UI Component Library",
    "storybookjs/storybook": "UI Component Development",
    "excalidraw/excalidraw": "Drawing/Whiteboard Tool",
    "TanStack/query": "Data Fetching Library",

    # Category 6: Specialized & Edge Cases
    "prisma/prisma": "ORM / Database Toolkit",
    "trpc/trpc": "Type-Safe API Framework",
    "dagger/dagger": "CI/CD Engine",
    "minio/minio": "Object Storage",
    "pocketbase/pocketbase": "Backend-as-a-Service (Go)",
    "tailwindlabs/tailwindcss": "CSS Framework",
    "denoland/deno": "JavaScript Runtime",
    "gitbutler/gitbutler": "Git Client",
    "juspay/hyperswitch": "Payment Switch",
    "chartdb/chartdb": "Database Visualization",
}

REPO_CATEGORIES = {
    "calcom/cal.com": "Full-Stack Applications",
    "medusajs/medusa": "Full-Stack Applications",
    "formbricks/formbricks": "Full-Stack Applications",
    "documenso/documenso": "Full-Stack Applications",
    "twentyhq/twenty": "Full-Stack Applications",
    "hoppscotch/hoppscotch": "Full-Stack Applications",
    "immich-app/immich": "Full-Stack Applications",
    "maybe-finance/maybe": "Full-Stack Applications",
    "appwrite/appwrite": "Full-Stack Applications",
    "logto-io/logto": "Full-Stack Applications",
    "nestjs/nest": "Microservices & Backend",
    "fastapi/fastapi": "Microservices & Backend",
    "pallets/flask": "Microservices & Backend",
    "tiangolo/full-stack-fastapi-template": "Microservices & Backend",
    "GoogleCloudPlatform/microservices-demo": "Microservices & Backend",
    "dotnet/eShop": "Microservices & Backend",
    "gothinkster/realworld": "Microservices & Backend",
    "amplication/amplication": "Microservices & Backend",
    "backstage/backstage": "Microservices & Backend",
    "supabase/supabase": "Microservices & Backend",
    "langchain-ai/langchain": "AI/ML Projects",
    "openai/openai-cookbook": "AI/ML Projects",
    "run-llama/llama_index": "AI/ML Projects",
    "huggingface/transformers": "AI/ML Projects",
    "mlflow/mlflow": "AI/ML Projects",
    "bentoml/BentoML": "AI/ML Projects",
    "ray-project/ray": "AI/ML Projects",
    "qdrant/qdrant": "AI/ML Projects",
    "chroma-core/chroma": "AI/ML Projects",
    "open-webui/open-webui": "AI/ML Projects",
    "grafana/grafana": "DevTools & Infrastructure",
    "prometheus/prometheus": "DevTools & Infrastructure",
    "traefik/traefik": "DevTools & Infrastructure",
    "hashicorp/terraform": "DevTools & Infrastructure",
    "docker/compose": "DevTools & Infrastructure",
    "pulumi/pulumi": "DevTools & Infrastructure",
    "n8n-io/n8n": "DevTools & Infrastructure",
    "nocodb/nocodb": "DevTools & Infrastructure",
    "strapi/strapi": "DevTools & Infrastructure",
    "directus/directus": "DevTools & Infrastructure",
    "angular/angular": "Frontend Frameworks",
    "vercel/next.js": "Frontend Frameworks",
    "vuejs/core": "Frontend Frameworks",
    "sveltejs/svelte": "Frontend Frameworks",
    "shadcn-ui/ui": "Frontend Frameworks",
    "ionic-team/ionic-framework": "Frontend Frameworks",
    "ant-design/ant-design": "Frontend Frameworks",
    "storybookjs/storybook": "Frontend Frameworks",
    "excalidraw/excalidraw": "Frontend Frameworks",
    "TanStack/query": "Frontend Frameworks",
    "prisma/prisma": "Specialized & Edge Cases",
    "trpc/trpc": "Specialized & Edge Cases",
    "dagger/dagger": "Specialized & Edge Cases",
    "minio/minio": "Specialized & Edge Cases",
    "pocketbase/pocketbase": "Specialized & Edge Cases",
    "tailwindlabs/tailwindcss": "Specialized & Edge Cases",
    "denoland/deno": "Specialized & Edge Cases",
    "gitbutler/gitbutler": "Specialized & Edge Cases",
    "juspay/hyperswitch": "Specialized & Edge Cases",
    "chartdb/chartdb": "Specialized & Edge Cases",
}

# What sections CodeTrellis should ideally produce
EXPECTED_SECTIONS = [
    "AI_INSTRUCTION", "PROJECT", "ENUMS", "DTOS", "SCHEMAS",
    "INTERFACES", "TYPES", "CONTROLLERS", "INFRASTRUCTURE",
    "CONTEXT", "ERROR_HANDLING", "TODOS", "ACTIONABLE_ITEMS",
    "RUNBOOK", "IMPLEMENTATION_LOGIC", "PROGRESS", "OVERVIEW",
    "BEST_PRACTICES", "BUSINESS_DOMAIN", "DATA_FLOWS",
    "NESTJS_MODULES", "SERVICE_MAP", "GRPC", "PROJECT_STRUCTURE",
    "PROGRESS_DETAIL",
]

# Known frameworks/ORMs CodeTrellis doesn't extract yet
MISSING_EXTRACTOR_PATTERNS = {
    "Prisma": (r"prisma|@prisma/client|schema\.prisma", "Prisma ORM models not extracted"),
    "tRPC": (r"trpc|@trpc/|createTRPCRouter|t\.procedure", "tRPC routers/procedures not extracted"),
    "Drizzle": (r"drizzle-orm|drizzle\(", "Drizzle ORM schemas not extracted"),
    "Sequelize": (r"sequelize|Model\.init\(", "Sequelize models not extracted"),
    "SQLAlchemy": (r"sqlalchemy|Base\.metadata|declarative_base", "SQLAlchemy models not extracted"),
    "Django ORM": (r"django\.db|models\.Model|from django", "Django models not extracted"),
    "GraphQL": (r"@Query|@Mutation|@Resolver|type Query|graphql", "GraphQL schema/resolvers not extracted"),
    "gRPC (Proto)": (r"\.proto|grpc|@GrpcMethod", "gRPC proto definitions partially extracted"),
    "Go": (r"package main|func main\(\)|go\.mod", "Go language not supported"),
    "Rust": (r"fn main\(\)|Cargo\.toml|use std::", "Rust language not supported"),
    "Java": (r"public class|@SpringBoot|pom\.xml", "Java language not supported"),
    "C#/.NET": (r"namespace |\.csproj|using System", "C#/.NET language not supported"),
    "Ruby": (r"Gemfile|class.*<.*ApplicationRecord|Rails\.application", "Ruby/Rails not supported"),
    "Svelte": (r"\.svelte|<script.*lang=\"ts\">", "Svelte components not extracted"),
    "Vue SFC": (r"\.vue|<template>|<script setup", "Vue SFC components not extracted"),
    "Expo/React Native": (r"expo|react-native|@react-navigation", "React Native components partially supported"),
}


@dataclass
class RepoFindings:
    """Quality findings for a single repository."""
    repo: str
    category: str
    correct_domain: str

    # Scan status
    scan_success: bool = False
    scan_timeout: bool = False
    clone_failed: bool = False
    exit_code: int = -1
    duration_s: int = 0
    output_lines: int = 0
    file_count: int = 0

    # Detection results
    detected_type: str = ""
    detected_stack: str = ""
    detected_domain: str = ""
    domain_correct: bool = False
    domain_vocabulary_wrong: bool = False

    # Section analysis
    sections_found: List[str] = field(default_factory=list)
    sections_missing: List[str] = field(default_factory=list)

    # Quality issues
    issues: List[str] = field(default_factory=list)  # human-readable issue descriptions
    improvements: List[str] = field(default_factory=list)  # suggested improvements
    missing_extractors: List[str] = field(default_factory=list)  # framework/language extractors needed

    # Quantitative
    schema_count: int = 0
    dto_count: int = 0
    controller_count: int = 0
    interface_count: int = 0
    type_count: int = 0
    enum_count: int = 0
    todo_count: int = 0
    runbook_commands: int = 0
    cicd_pipelines: int = 0
    env_vars: int = 0
    logic_snippets: int = 0
    bpl_practices: int = 0
    docker_count: int = 0

    # Scores
    has_traceback: bool = False
    has_contamination: bool = False


def parse_prompt_file(prompt_path: Path, log_path: Path, repo: str) -> RepoFindings:
    """Parse a .prompt file and extract quality findings."""
    category = REPO_CATEGORIES.get(repo, "Unknown")
    correct_domain = KNOWN_DOMAINS.get(repo, "Unknown")
    findings = RepoFindings(repo=repo, category=category, correct_domain=correct_domain)

    # Check if scan output exists
    if not prompt_path.exists() or prompt_path.stat().st_size == 0:
        findings.scan_success = False
        if log_path.exists():
            log_content = log_path.read_text()
            if "TIMEOUT" in log_content:
                findings.scan_timeout = True
                findings.issues.append("Scan timed out")
            elif "CLONE_FAILED" in log_content:
                findings.clone_failed = True
                findings.issues.append("Clone failed")
        return findings

    content = prompt_path.read_text()
    lines = content.split("\n")
    findings.output_lines = len(lines)

    # Check stderr log for tracebacks
    if log_path.exists():
        log_content = log_path.read_text()
        if "Traceback" in log_content:
            findings.has_traceback = True
            findings.issues.append("Python traceback in scan stderr")
        # Extract timing
        timing_match = re.search(r"TIMING: (\d+)s \(exit=(\d+)\)", log_content)
        if timing_match:
            findings.duration_s = int(timing_match.group(1))
            findings.exit_code = int(timing_match.group(2))

    # Determine scan success (exit_code 0 or not set means success if we have output)
    findings.scan_success = findings.output_lines > 10 and findings.exit_code <= 0

    # Extract scan metadata from CodeTrellis log lines at top
    for line in lines[:50]:
        if "Files scanned:" in line:
            m = re.search(r"Files scanned:\s+(\d+)", line)
            if m:
                findings.file_count = int(m.group(1))
        elif "Schemas:" in line:
            m = re.search(r"Schemas:\s+(\d+)", line)
            if m:
                findings.schema_count = int(m.group(1))
        elif "DTOs:" in line and "Controllers" not in line:
            m = re.search(r"DTOs:\s+(\d+)", line)
            if m:
                findings.dto_count = int(m.group(1))
        elif "Controllers:" in line:
            m = re.search(r"Controllers:\s+(\d+)", line)
            if m:
                findings.controller_count = int(m.group(1))
        elif "Interfaces:" in line:
            m = re.search(r"Interfaces:\s+(\d+)", line)
            if m:
                findings.interface_count = int(m.group(1))
        elif "Types:" in line and "AngularServices" not in line:
            m = re.search(r"Types:\s+(\d+)", line)
            if m:
                findings.type_count = int(m.group(1))
        elif "Enums:" in line:
            m = re.search(r"Enums:\s+(\d+)", line)
            if m:
                findings.enum_count = int(m.group(1))

    # Find sections in compressed output
    compressed_start = content.find("[AI_INSTRUCTION]")
    if compressed_start == -1:
        compressed_start = content.find("COMPRESSED MATRIX")
    if compressed_start == -1:
        compressed_start = 0

    compressed = content[compressed_start:]

    # Extract detected sections
    section_pattern = re.compile(r"^\[([A-Z_]+(?::[^\]]*)?)\]", re.MULTILINE)
    found_sections = set()
    for m in section_pattern.finditer(compressed):
        sec_name = m.group(1).split(":")[0]  # Strip :suffix
        found_sections.add(sec_name)

    findings.sections_found = sorted(found_sections)

    # Check for key sections we always expect
    always_expected = {"AI_INSTRUCTION", "PROJECT", "RUNBOOK", "IMPLEMENTATION_LOGIC",
                       "BEST_PRACTICES", "OVERVIEW", "TODOS", "ACTIONABLE_ITEMS",
                       "BUSINESS_DOMAIN", "CONTEXT", "ERROR_HANDLING", "PROJECT_STRUCTURE"}
    findings.sections_missing = sorted(always_expected - found_sections)

    if "RUNBOOK" not in found_sections:
        findings.issues.append("Missing [RUNBOOK] section — AI cannot know how to run project")

    if "IMPLEMENTATION_LOGIC" not in found_sections:
        findings.issues.append("Missing [IMPLEMENTATION_LOGIC] — no code flow analysis")

    if "BEST_PRACTICES" not in found_sections:
        findings.issues.append("Missing [BEST_PRACTICES] — no BPL practices selected")

    # Extract project detection
    project_match = re.search(r"\[PROJECT\]\nname=(.+)\ntype=(.+)\nstack=(.+)", compressed)
    if project_match:
        findings.detected_type = project_match.group(2).strip()
        findings.detected_stack = project_match.group(3).strip()

    # Extract domain
    domain_match = re.search(r"\[BUSINESS_DOMAIN\]\ndomain:(.+)", compressed)
    if domain_match:
        findings.detected_domain = domain_match.group(1).strip()
    else:
        findings.detected_domain = "Not detected"
        findings.issues.append("No business domain detected")

    # Check domain accuracy
    if findings.detected_domain and correct_domain != "Unknown":
        # Loose match — check if key words overlap
        detected_lower = findings.detected_domain.lower()
        correct_lower = correct_domain.lower()
        # Exact or close match
        if (correct_lower in detected_lower or detected_lower in correct_lower or
                any(w in detected_lower for w in correct_lower.split("/"))):
            findings.domain_correct = True
        else:
            findings.domain_correct = False
            findings.issues.append(
                f"Domain misdetection: detected '{findings.detected_domain}' "
                f"but should be '{correct_domain}'"
            )

    # Check vocabulary correctness
    vocab_match = re.search(r"vocabulary:(.+?)(?:\n\[|$)", compressed, re.DOTALL)
    if vocab_match and not findings.domain_correct:
        vocab_text = vocab_match.group(1)
        findings.domain_vocabulary_wrong = True
        findings.issues.append(f"Domain vocabulary is wrong for this project type")

    # Count RUNBOOK items
    runbook_section = re.search(r"\[RUNBOOK\](.*?)(?=\n\[|\Z)", compressed, re.DOTALL)
    if runbook_section:
        rb = runbook_section.group(1)
        findings.runbook_commands = len(re.findall(r"^[a-zA-Z_-]+=", rb, re.MULTILINE))
        findings.cicd_pipelines = len(re.findall(r"^ci:", rb, re.MULTILINE))
        findings.env_vars = len(re.findall(r"env:", rb, re.MULTILINE))

    # Count IMPLEMENTATION_LOGIC
    logic_match = re.search(r"LOGIC_STATS: (\d+) snippets", compressed)
    if logic_match:
        findings.logic_snippets = int(logic_match.group(1))

    # Count BPL practices
    bpl_match = re.search(r"Practices: (\d+) selected", compressed)
    if bpl_match:
        findings.bpl_practices = int(bpl_match.group(1))

    # Check contamination
    progress_match = re.search(r"completion:.*?todos:(\d+)", compressed)
    if progress_match:
        findings.todo_count = int(progress_match.group(1))
        if findings.todo_count > 500:
            findings.has_contamination = True
            # Only flag as issue for small repos
            if findings.file_count < 1000 and findings.todo_count > 500:
                findings.issues.append(f"Possible TODO contamination: {findings.todo_count} TODOs for {findings.file_count} files")

    # Check for missing extractors by scanning the actual source repo directory
    # Do NOT match on the .prompt output text (contains CodeTrellis template keywords)
    repo_name = repo.replace("/", "_")
    repo_dir = Path("/tmp/codetrellis-validation") / repo_name

    if repo_dir.exists():
        # Check for specific config files that indicate framework usage
        framework_indicators = {
            "Prisma": ["schema.prisma", "prisma/schema.prisma"],
            "tRPC": ["trpc"],  # Check via package.json
            "Drizzle": ["drizzle.config.ts", "drizzle.config.js"],
            "GraphQL": ["schema.graphql", ".graphql"],
            "Go": ["go.mod"],
            "Rust": ["Cargo.toml"],
            "Java": ["pom.xml", "build.gradle"],
            "C#/.NET": [".csproj"],
            "Ruby": ["Gemfile"],
            "Django ORM": ["manage.py", "django"],
            "SQLAlchemy": ["alembic.ini", "alembic"],
            "Svelte": ["svelte.config.js", "svelte.config.ts"],
            "Vue SFC": ["vue.config.js", "nuxt.config.ts"],
        }

        # Quick checks using find (only check top-level config files)
        for framework, indicators in framework_indicators.items():
            found = False
            for indicator in indicators:
                check_path = repo_dir / indicator
                if check_path.exists():
                    found = True
                    break
                # Also check one level deep
                for child in repo_dir.iterdir():
                    if child.is_dir() and (child / indicator).exists():
                        found = True
                        break
                if found:
                    break

            if found:
                # Check if CodeTrellis actually extracted from this framework
                extracted = False
                if framework == "Prisma" and findings.schema_count > 0:
                    extracted = True
                elif framework == "Go":
                    extracted = True  # Go is a different language, not an extractor gap
                elif framework == "Rust":
                    extracted = True  # Rust is a different language, not an extractor gap
                elif framework in ("Java", "C#/.NET", "Ruby"):
                    extracted = True  # Unsupported languages are expected

                if not extracted:
                    desc = MISSING_EXTRACTOR_PATTERNS.get(framework, (None, f"{framework} not extracted"))[1]
                    findings.missing_extractors.append(f"{framework}: {desc}")

    # Check for zero-extraction issues (only flag for TS/JS projects)
    total_entities = (findings.schema_count + findings.dto_count +
                      findings.controller_count + findings.interface_count +
                      findings.type_count + findings.enum_count)
    if total_entities == 0 and findings.scan_success and findings.file_count > 50:
        # Only flag as issue if this is a TS/JS project (has package.json)
        has_package_json = (repo_dir / "package.json").exists() if repo_dir.exists() else False
        if has_package_json:
            findings.issues.append(
                f"Zero entities extracted from {findings.file_count} files — "
                f"expected TS/JS entities from package.json project"
            )
        # Don't flag for Go/Rust/Python projects — they don't have TS entities

    # Check for enum duplication
    enum_lines = re.findall(r"^(.+)=.+$", compressed[compressed.find("[ENUMS]"):compressed.find("[ENUMS]")+500] if "[ENUMS]" in compressed else "", re.MULTILINE)
    if len(enum_lines) != len(set(enum_lines)):
        findings.issues.append("Enum duplication detected (same enum listed multiple times)")

    # Generate improvement suggestions
    if findings.missing_extractors:
        findings.improvements.append(
            f"Add extractors for: {', '.join(f.split(':')[0] for f in findings.missing_extractors)}"
        )
    if not findings.domain_correct and findings.detected_domain:
        findings.improvements.append(
            f"Add domain keywords for '{correct_domain}' to BusinessDomainExtractor"
        )
    if findings.schema_count == 0 and findings.file_count > 100:
        findings.improvements.append("Investigate why 0 schemas extracted — may need Prisma/Drizzle/Django model extractor")
    if findings.controller_count == 0 and findings.file_count > 100:
        findings.improvements.append("Investigate why 0 controllers — may need tRPC router or framework-specific extractor")

    return findings


def generate_findings_document(findings_list: List[RepoFindings], output_path: Path):
    """Generate the VALIDATION_FINDINGS.md document."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Compute aggregates
    total = len(findings_list)
    passed = sum(1 for f in findings_list if f.scan_success)
    failed = sum(1 for f in findings_list if not f.scan_success)
    timeouts = sum(1 for f in findings_list if f.scan_timeout)
    clone_fails = sum(1 for f in findings_list if f.clone_failed)
    domain_correct = sum(1 for f in findings_list if f.domain_correct)
    domain_total = sum(1 for f in findings_list if f.scan_success)
    tracebacks = sum(1 for f in findings_list if f.has_traceback)

    # Collect all unique issues
    all_issues: Dict[str, int] = {}
    all_missing_extractors: Dict[str, int] = {}
    for f in findings_list:
        for issue in f.issues:
            # Generalize the issue
            gen = re.sub(r"'\w[^']*'", "'...'", issue)
            gen = re.sub(r"\d+", "N", gen)
            all_issues[gen] = all_issues.get(gen, 0) + 1
        for me in f.missing_extractors:
            key = me.split(":")[0].strip()
            all_missing_extractors[key] = all_missing_extractors.get(key, 0) + 1

    lines = []
    lines.append("# CodeTrellis Validation Findings — 60-Repository Quality Audit")
    lines.append("")
    lines.append(f"> **Generated:** {now}")
    lines.append(f"> **CodeTrellis Version:** 4.1.2 (Phase D — WS-8)")
    lines.append(f"> **Repos Scanned:** {total}")
    lines.append(f"> **Purpose:** Comprehensive quality analysis of CodeTrellis scan output across diverse public repositories")
    lines.append(f"> **Action:** Use this document to prioritize extractor development and quality fixes for future phases")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Executive Summary
    lines.append("## 1. Executive Summary")
    lines.append("")
    pass_rate = (passed / total * 100) if total else 0
    domain_rate = (domain_correct / domain_total * 100) if domain_total else 0
    lines.append(f"| Metric | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| Total repos scanned | {total} |")
    lines.append(f"| Scan success | {passed}/{total} ({pass_rate:.1f}%) |")
    lines.append(f"| Scan failures | {failed} (timeouts: {timeouts}, clone failures: {clone_fails}) |")
    lines.append(f"| Domain accuracy | {domain_correct}/{domain_total} ({domain_rate:.1f}%) |")
    lines.append(f"| Tracebacks | {tracebacks} |")
    lines.append(f"| Target pass rate | >70% |")
    lines.append(f"| Target met | {'🎉 YES' if pass_rate >= 70 else '⚠️  NO'} |")
    lines.append("")

    # Top Issues
    lines.append("## 2. Top Issues (By Frequency)")
    lines.append("")
    lines.append("| # | Issue | Repos Affected |")
    lines.append("|---|---|---|")
    for i, (issue, count) in enumerate(sorted(all_issues.items(), key=lambda x: -x[1]), 1):
        lines.append(f"| {i} | {issue} | {count} |")
    lines.append("")

    # Missing Extractors
    lines.append("## 3. Missing Extractors & Unsupported Frameworks")
    lines.append("")
    lines.append("| Framework/Language | Repos Needing It | Priority |")
    lines.append("|---|---|---|")
    for ext, count in sorted(all_missing_extractors.items(), key=lambda x: -x[1]):
        priority = "🔴 Critical" if count >= 10 else "🟡 High" if count >= 5 else "🟢 Medium"
        lines.append(f"| {ext} | {count} | {priority} |")
    lines.append("")

    # Per-Category Analysis
    lines.append("## 4. Per-Category Analysis")
    lines.append("")

    categories = {}
    for f in findings_list:
        cat = f.category
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(f)

    for cat_name, repos in sorted(categories.items()):
        cat_passed = sum(1 for r in repos if r.scan_success)
        cat_domain_correct = sum(1 for r in repos if r.domain_correct)
        lines.append(f"### 4.{list(sorted(categories.keys())).index(cat_name)+1} {cat_name}")
        lines.append("")
        lines.append(f"**Pass rate:** {cat_passed}/{len(repos)} | "
                     f"**Domain accuracy:** {cat_domain_correct}/{cat_passed if cat_passed else 1}")
        lines.append("")
        lines.append(f"| Repo | Status | Lines | Time | Type | Domain (Detected→Correct) | Issues |")
        lines.append(f"|---|---|---|---|---|---|---|")
        for r in repos:
            status = "✅" if r.scan_success else ("⏰" if r.scan_timeout else ("❌ Clone" if r.clone_failed else "❌"))
            domain_str = f"{r.detected_domain}→{r.correct_domain}" if r.detected_domain else f"None→{r.correct_domain}"
            domain_icon = "✅" if r.domain_correct else "❌"
            issues_short = "; ".join(r.issues[:2]) if r.issues else "—"
            if len(issues_short) > 80:
                issues_short = issues_short[:77] + "..."
            lines.append(
                f"| `{r.repo}` | {status} | {r.output_lines} | {r.duration_s}s | "
                f"{r.detected_type or '—'} | {domain_icon} {domain_str} | {issues_short} |"
            )
        lines.append("")

    # Detailed Per-Repo Findings
    lines.append("## 5. Detailed Per-Repo Findings")
    lines.append("")

    for f in findings_list:
        lines.append(f"### 5.{findings_list.index(f)+1} `{f.repo}` ({f.category})")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|---|---|")
        lines.append(f"| **Scan Status** | {'✅ Success' if f.scan_success else '❌ Failed'} (exit={f.exit_code}, {f.duration_s}s) |")
        lines.append(f"| **Files** | {f.file_count} |")
        lines.append(f"| **Output** | {f.output_lines} lines |")
        lines.append(f"| **Type** | {f.detected_type or 'Not detected'} |")
        lines.append(f"| **Stack** | {f.detected_stack or 'Not detected'} |")
        lines.append(f"| **Domain** | {f.detected_domain or 'Not detected'} (correct: {f.correct_domain}) {'✅' if f.domain_correct else '❌'} |")
        lines.append(f"| **Sections** | {len(f.sections_found)} found: {', '.join(f.sections_found) if f.sections_found else '—'} |")
        if f.sections_missing:
            lines.append(f"| **Missing Sections** | {', '.join(f.sections_missing)} |")
        lines.append(f"| **Entities** | Schemas:{f.schema_count} DTOs:{f.dto_count} Controllers:{f.controller_count} Interfaces:{f.interface_count} Types:{f.type_count} Enums:{f.enum_count} |")
        lines.append(f"| **Runbook** | {f.runbook_commands} commands, {f.cicd_pipelines} CI/CD, {f.env_vars} env var sections |")
        lines.append(f"| **Logic** | {f.logic_snippets} snippets |")
        lines.append(f"| **BPL** | {f.bpl_practices} practices |")
        lines.append(f"| **Traceback** | {'⚠️ YES' if f.has_traceback else '✅ No'} |")
        lines.append("")

        if f.issues:
            lines.append("**Issues:**")
            for issue in f.issues:
                lines.append(f"- ❌ {issue}")
            lines.append("")

        if f.missing_extractors:
            lines.append("**Missing Extractors:**")
            for me in f.missing_extractors:
                lines.append(f"- 🔧 {me}")
            lines.append("")

        if f.improvements:
            lines.append("**Suggested Improvements:**")
            for imp in f.improvements:
                lines.append(f"- 💡 {imp}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Improvement Roadmap
    lines.append("## 6. Improvement Roadmap")
    lines.append("")
    lines.append("Based on the findings above, here is the prioritized improvement roadmap:")
    lines.append("")

    # Sort missing extractors by frequency
    lines.append("### 6.1 New Extractors Needed")
    lines.append("")
    lines.append("| Priority | Extractor | Repos Affected | Effort Estimate |")
    lines.append("|---|---|---|---|")
    for ext, count in sorted(all_missing_extractors.items(), key=lambda x: -x[1]):
        if count >= 5:
            effort = "Medium (8-16h)" if ext in ("Prisma", "tRPC", "GraphQL", "Drizzle") else "High (16-40h)"
            lines.append(f"| 🔴 P1 | {ext} extractor | {count} repos | {effort} |")
        elif count >= 2:
            effort = "Medium (8-16h)"
            lines.append(f"| 🟡 P2 | {ext} extractor | {count} repos | {effort} |")
        else:
            lines.append(f"| 🟢 P3 | {ext} extractor | {count} repos | TBD |")
    lines.append("")

    # Domain improvements
    lines.append("### 6.2 Domain Detection Improvements")
    lines.append("")
    lines.append("| Domain | Currently Detected As | Repos | Fix |")
    lines.append("|---|---|---|---|")
    domain_fixes = {}
    for f in findings_list:
        if not f.domain_correct and f.scan_success:
            key = (f.correct_domain, f.detected_domain)
            if key not in domain_fixes:
                domain_fixes[key] = []
            domain_fixes[key].append(f.repo)
    for (correct, detected), repos in sorted(domain_fixes.items(), key=lambda x: -len(x[1])):
        repos_str = ", ".join(f"`{r}`" for r in repos[:3])
        if len(repos) > 3:
            repos_str += f" +{len(repos)-3} more"
        lines.append(f"| {correct} | {detected} | {repos_str} | Add domain keywords |")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append(f"_Generated by CodeTrellis Phase D Validation Framework on {now}_")
    lines.append(f"_Total repos: {total} | Passed: {passed} | Failed: {failed} | Domain accuracy: {domain_rate:.1f}%_")
    lines.append(f"_Use `codetrellis validate-repos --score-only` for automated scoring_")
    lines.append(f"_Use `codetrellis validate-repos --analyze-only` for Gap Analysis Round 2_")

    output_path.write_text("\n".join(lines))
    print(f"[CodeTrellis] Findings written to: {output_path}")
    print(f"[CodeTrellis] Total repos: {total} | Passed: {passed} | Failed: {failed}")
    print(f"[CodeTrellis] Domain accuracy: {domain_correct}/{domain_total} ({domain_rate:.1f}%)")
    print(f"[CodeTrellis] Unique issues: {len(all_issues)}")
    print(f"[CodeTrellis] Missing extractors: {len(all_missing_extractors)}")


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Generate CodeTrellis validation findings document"
    )
    parser.add_argument("--results-dir", default=None,
                        help="Directory with validation results")
    parser.add_argument("--output", default=None,
                        help="Output path for findings markdown")
    parser.add_argument("--repos-file", default=None,
                        help="Path to repos.txt file")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    results_dir = Path(args.results_dir) if args.results_dir else script_dir / "validation-results"
    output_path = Path(args.output) if args.output else script_dir / "VALIDATION_FINDINGS.md"
    repos_file = Path(args.repos_file) if args.repos_file else script_dir / "repos.txt"

    if not results_dir.exists():
        print(f"[CodeTrellis] ❌ Results directory not found: {results_dir}")
        sys.exit(1)

    # Read repos list
    repos = []
    with open(repos_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            repos.append(line)

    print(f"[CodeTrellis] Analyzing {len(repos)} repos from {repos_file}")
    print(f"[CodeTrellis] Results dir: {results_dir}")

    # Parse each repo's prompt file
    findings_list = []
    for repo in repos:
        repo_name = repo.replace("/", "_")
        prompt_path = results_dir / f"{repo_name}.prompt"
        log_path = results_dir / f"{repo_name}.log"

        if prompt_path.exists() or log_path.exists():
            findings = parse_prompt_file(prompt_path, log_path, repo)
            findings_list.append(findings)
            status = "✅" if findings.scan_success else ("⏰ TIMEOUT" if findings.scan_timeout else "❌")
            print(f"  {status} {repo}: {findings.output_lines} lines, {len(findings.issues)} issues")
        else:
            # No result file — scan didn't run for this repo
            findings = RepoFindings(
                repo=repo,
                category=REPO_CATEGORIES.get(repo, "Unknown"),
                correct_domain=KNOWN_DOMAINS.get(repo, "Unknown"),
            )
            findings.issues.append("No scan result — repo was not scanned")
            findings_list.append(findings)
            print(f"  ⬜ {repo}: not scanned")

    # Generate the findings document
    generate_findings_document(findings_list, output_path)


if __name__ == "__main__":
    main()
