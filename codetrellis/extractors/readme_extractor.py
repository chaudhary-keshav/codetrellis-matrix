"""
README Extractor for Projects and Components

Extracts documentation from README files at various levels:
- Project-level README.md
- Module/feature README files
- Component-level documentation
- Inline .md documentation files

Extracts:
- Title and description
- Features/capabilities list
- Usage examples
- API documentation sections
- Installation/setup instructions

Part of CodeTrellis v2.0 - Phase 2 Context Enrichment
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class ReadmeSection:
    """Represents a section in a README file"""
    title: str
    level: int  # Heading level (1-6)
    content: str
    subsections: List['ReadmeSection'] = field(default_factory=list)


@dataclass
class ReadmeInfo:
    """Information extracted from a README file"""
    file_path: str
    title: Optional[str] = None
    description: Optional[str] = None
    features: List[str] = field(default_factory=list)
    installation: Optional[str] = None
    usage: Optional[str] = None
    api_docs: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    sections: List[ReadmeSection] = field(default_factory=list)
    raw_content: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'filePath': self.file_path,
            'title': self.title,
            'description': self.description,
            'features': self.features,
            'installation': self.installation,
            'usage': self.usage,
            'apiDocs': self.api_docs,
            'examples': self.examples,
            'sections': [
                {'title': s.title, 'level': s.level}
                for s in self.sections
            ],
        }

    def get_summary(self, max_length: int = 500) -> str:
        """Get a compressed summary suitable for prompt injection"""
        parts = []

        if self.title:
            parts.append(f"# {self.title}")

        if self.description:
            desc = self.description[:200] + "..." if len(self.description) > 200 else self.description
            parts.append(desc)

        if self.features:
            features_str = ", ".join(self.features[:5])
            if len(self.features) > 5:
                features_str += f" (+{len(self.features)-5} more)"
            parts.append(f"Features: {features_str}")

        summary = " | ".join(parts)
        return summary[:max_length] if len(summary) > max_length else summary


@dataclass
class ProjectReadmeInfo:
    """README information for an entire project"""
    project_path: str
    main_readme: Optional[ReadmeInfo] = None
    module_readmes: List[ReadmeInfo] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'projectPath': self.project_path,
            'mainReadme': self.main_readme.to_dict() if self.main_readme else None,
            'moduleReadmes': [r.to_dict() for r in self.module_readmes],
            'stats': {
                'totalReadmes': 1 + len(self.module_readmes) if self.main_readme else len(self.module_readmes),
            }
        }


class ReadmeExtractor:
    """
    Extracts documentation from README files.

    Example:
        extractor = ReadmeExtractor()
        result = extractor.extract_project("/path/to/project")
        print(result.main_readme.description)
    """

    # Pattern to match markdown headings
    HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

    # Pattern to match list items
    LIST_PATTERN = re.compile(r'^[\s]*[-*+]\s+(.+)$', re.MULTILINE)

    # Pattern to match code blocks
    CODE_BLOCK_PATTERN = re.compile(r'```[\w]*\n([\s\S]*?)```', re.MULTILINE)

    # Common section names to look for
    SECTION_KEYWORDS = {
        'features': ['features', 'capabilities', 'what it does', 'highlights'],
        'installation': ['installation', 'install', 'setup', 'getting started', 'quick start'],
        'usage': ['usage', 'how to use', 'basic usage', 'example'],
        'api': ['api', 'api reference', 'api documentation', 'methods', 'functions'],
        'examples': ['examples', 'code examples', 'sample', 'demo'],
    }

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> ReadmeInfo:
        """
        Extract information from README content.

        Args:
            content: README file content
            file_path: Path to the README file

        Returns:
            ReadmeInfo with extracted documentation
        """
        result = ReadmeInfo(file_path=file_path, raw_content=content)

        # Extract title (first H1)
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            result.title = title_match.group(1).strip()

        # Extract description (text after title, before first section)
        if title_match:
            after_title = content[title_match.end():].strip()
            # Find next heading
            next_heading = re.search(r'^#{1,6}\s+', after_title, re.MULTILINE)
            if next_heading:
                result.description = after_title[:next_heading.start()].strip()
            else:
                # Take first paragraph
                first_para = re.match(r'^([^\n]+(?:\n[^\n#]+)*)', after_title)
                if first_para:
                    result.description = first_para.group(1).strip()

        # Extract sections
        result.sections = self._extract_sections(content)

        # Extract features
        result.features = self._extract_section_content(content, 'features')

        # Gap #6 Fix: Extract architecture section
        architecture_content = self._find_section(content, 'architecture')
        if architecture_content:
            result.sections.append(ReadmeSection(
                title="Architecture",
                level=2,
                content=architecture_content[:1000]  # Increased from 500 to 1000
            ))

        # Extract installation
        installation_content = self._find_section(content, 'installation')
        if installation_content:
            result.installation = installation_content[:1000]  # Increased from 500 to 1000

        # Extract usage
        usage_content = self._find_section(content, 'usage')
        if usage_content:
            result.usage = usage_content[:1000]  # Increased from 500 to 1000

        # Extract API docs
        api_content = self._find_section(content, 'api')
        if api_content:
            result.api_docs = api_content[:2000]  # Increased from 1000 to 2000

        # Extract code examples
        result.examples = self._extract_code_examples(content)

        # Gap #6 Fix: Extract additional important sections
        for section_type in ['getting started', 'quickstart', 'configuration', 'deployment', 'contributing']:
            section_content = self._find_section(content, section_type)
            if section_content and not any(s.title.lower() == section_type for s in result.sections):
                result.sections.append(ReadmeSection(
                    title=section_type.title(),
                    level=2,
                    content=section_content[:800]
                ))

        return result

    def _extract_sections(self, content: str) -> List[ReadmeSection]:
        """Extract all sections from content"""
        sections = []

        for match in self.HEADING_PATTERN.finditer(content):
            level = len(match.group(1))
            title = match.group(2).strip()

            # Find content until next heading of same or higher level
            start = match.end()
            next_match = None
            for m in self.HEADING_PATTERN.finditer(content[start:]):
                if len(m.group(1)) <= level:
                    next_match = m
                    break

            if next_match:
                section_content = content[start:start + next_match.start()].strip()
            else:
                section_content = content[start:].strip()

            sections.append(ReadmeSection(
                title=title,
                level=level,
                content=section_content[:500]  # Limit content length
            ))

        return sections

    def _find_section(self, content: str, section_type: str) -> Optional[str]:
        """Find and extract content from a specific section type"""
        keywords = self.SECTION_KEYWORDS.get(section_type, [section_type])

        for keyword in keywords:
            # Look for heading with this keyword
            pattern = re.compile(
                rf'^(#{1,6})\s+[^#\n]*{re.escape(keyword)}[^#\n]*$',
                re.MULTILINE | re.IGNORECASE
            )
            match = pattern.search(content)

            if match:
                level = len(match.group(1))
                start = match.end()

                # Find next heading of same or higher level
                next_pattern = re.compile(rf'^#{{{1},{level}}}\s+', re.MULTILINE)
                next_match = next_pattern.search(content[start:])

                if next_match:
                    return content[start:start + next_match.start()].strip()
                else:
                    return content[start:].strip()

        return None

    def _extract_section_content(self, content: str, section_type: str) -> List[str]:
        """Extract list items from a section"""
        section_content = self._find_section(content, section_type)

        if not section_content:
            return []

        items = []
        for match in self.LIST_PATTERN.finditer(section_content):
            item = match.group(1).strip()
            # Clean up markdown formatting
            item = re.sub(r'\*\*([^*]+)\*\*', r'\1', item)  # Bold
            item = re.sub(r'\*([^*]+)\*', r'\1', item)  # Italic
            item = re.sub(r'`([^`]+)`', r'\1', item)  # Code
            items.append(item)

        return items

    def _extract_code_examples(self, content: str) -> List[str]:
        """Extract code examples from content"""
        examples = []

        for match in self.CODE_BLOCK_PATTERN.finditer(content):
            code = match.group(1).strip()
            if code and len(code) < 500:  # Only include reasonable-sized examples
                examples.append(code)

        return examples[:5]  # Limit number of examples

    def extract_file(self, file_path: str) -> ReadmeInfo:
        """
        Extract from a README file path.

        Args:
            file_path: Path to the README file

        Returns:
            ReadmeInfo with extracted documentation
        """
        path = Path(file_path)
        if not path.exists():
            return ReadmeInfo(file_path=file_path)

        content = path.read_text(encoding='utf-8', errors='ignore')
        return self.extract(content, file_path)

    def extract_project(self, project_path: str) -> ProjectReadmeInfo:
        """
        Extract all README files from a project.

        Args:
            project_path: Root path of the project

        Returns:
            ProjectReadmeInfo with all README information
        """
        project = Path(project_path)
        result = ProjectReadmeInfo(project_path=project_path)

        # Find main README
        for readme_name in ['README.md', 'readme.md', 'README', 'Readme.md']:
            readme_path = project / readme_name
            if readme_path.exists():
                result.main_readme = self.extract_file(str(readme_path))
                break

        # Find module/component READMEs (in src folder)
        src_path = project / 'src'
        if src_path.exists():
            for readme_file in src_path.rglob('README.md'):
                # Skip node_modules and other common directories
                if any(skip in str(readme_file) for skip in ['node_modules', '.git', 'dist', 'build']):
                    continue

                readme_info = self.extract_file(str(readme_file))
                result.module_readmes.append(readme_info)

        return result


# Convenience function
def extract_readme(content: str, file_path: str = "") -> ReadmeInfo:
    """
    Extract documentation from README content.

    Args:
        content: README file content
        file_path: Optional file path

    Returns:
        ReadmeInfo with extracted documentation
    """
    extractor = ReadmeExtractor()
    return extractor.extract(content, file_path)


def extract_project_readmes(project_path: str) -> ProjectReadmeInfo:
    """
    Extract all README files from a project.

    Args:
        project_path: Root path of the project

    Returns:
        ProjectReadmeInfo with all README information
    """
    extractor = ReadmeExtractor()
    return extractor.extract_project(project_path)
