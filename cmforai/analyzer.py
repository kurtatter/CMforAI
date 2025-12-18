"""
Project analyzer module for extracting and analyzing project structure.
Supports multiple programming languages and project types.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class FileInfo:
    """Information about a file in the project."""
    path: Path
    relative_path: str
    size: int
    lines: int
    language: str
    is_important: bool = False
    priority: int = 0


@dataclass
class ProjectInfo:
    """Information about the analyzed project."""
    root: Path
    files: List[FileInfo]
    structure: Dict[str, List[str]]
    dependencies: List[str]
    project_type: str = 'unknown'
    python_version: Optional[str] = None
    description: Optional[str] = None


class ProjectAnalyzer:
    """Analyzes projects and extracts relevant information for various programming languages."""
    
    # Universal important files (common across all project types)
    UNIVERSAL_IMPORTANT_FILES = {
        'README.md', 'README.rst', 'README.txt', 'README',
        'LICENSE', 'LICENSE.txt', 'LICENSE.md',
        'CHANGELOG.md', 'CHANGELOG.txt', 'CHANGELOG',
        'CONTRIBUTING.md', 'CONTRIBUTING.txt',
        '.gitignore', '.gitattributes',
        'Dockerfile', 'docker-compose.yml', 'docker-compose.yaml',
        '.env.example', '.env.template',
        'Makefile', 'makefile',
    }
    
    # Language-specific important files
    LANGUAGE_IMPORTANT_FILES = {
        'python': {
            'main.py', 'app.py', 'run.py', 'manage.py', '__init__.py',
            'setup.py', 'setup.cfg', 'pyproject.toml', 'requirements.txt',
            'requirements-dev.txt', 'Pipfile', 'Pipfile.lock', 'poetry.lock',
            'config.py', 'settings.py', '.python-version', 'runtime.txt',
        },
        'javascript': {
            'package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
            'tsconfig.json', 'jsconfig.json', '.babelrc', '.babelrc.js',
            'webpack.config.js', 'vite.config.js', 'rollup.config.js',
            'index.js', 'index.ts', 'main.js', 'main.ts', 'app.js', 'app.ts',
            'server.js', 'server.ts',
        },
        'typescript': {
            'package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
            'tsconfig.json', 'tsconfig.base.json',
            'index.ts', 'main.ts', 'app.ts', 'server.ts',
        },
        'java': {
            'pom.xml', 'build.gradle', 'build.gradle.kts', 'settings.gradle',
            'gradle.properties', 'gradlew', 'gradlew.bat',
            'src/main/java', 'src/main/resources', 'src/test/java',
        },
        'go': {
            'go.mod', 'go.sum', 'main.go', 'Gopkg.toml', 'Gopkg.lock',
            'glide.yaml', 'glide.lock', 'vendor.json',
        },
        'rust': {
            'Cargo.toml', 'Cargo.lock', 'main.rs', 'lib.rs',
        },
        'c': {
            'CMakeLists.txt', 'Makefile', 'configure', 'configure.ac',
            'main.c', 'CMakeCache.txt',
        },
        'cpp': {
            'CMakeLists.txt', 'Makefile', 'configure', 'configure.ac',
            'main.cpp', 'CMakeCache.txt', '.clang-format',
        },
        'csharp': {
            '*.csproj', '*.sln', '*.csproj.user', 'Program.cs', 'Startup.cs',
            'appsettings.json', 'appsettings.Development.json',
        },
        'ruby': {
            'Gemfile', 'Gemfile.lock', 'Rakefile', 'config.ru',
            'application.rb', 'routes.rb',
        },
        'php': {
            'composer.json', 'composer.lock', 'index.php', 'config.php',
            'artisan', 'package.json',
        },
    }
    
    # Common ignore patterns
    DEFAULT_IGNORE_PATTERNS = [
        r'\.git/',
        r'__pycache__/',
        r'\.pyc$',
        r'\.pyo$',
        r'\.pyd$',
        r'\.egg-info/',
        r'\.eggs/',
        r'\.venv/',
        r'venv/',
        r'env/',
        r'ENV/',
        r'\.env$',
        r'node_modules/',
        r'\.pytest_cache/',
        r'\.mypy_cache/',
        r'\.ruff_cache/',
        r'\.coverage',
        r'\.tox/',
        r'dist/',
        r'build/',
        r'\.idea/',
        r'\.vscode/',
        r'\.DS_Store',
        r'\.swp$',
        r'\.swo$',
        r'~$',
    ]
    
    # Language detection patterns (extended for multiple languages)
    LANGUAGE_PATTERNS = {
        'python': [r'\.py$', r'\.pyw$', r'\.pyi$'],
        'javascript': [r'\.js$', r'\.jsx$', r'\.mjs$', r'\.cjs$'],
        'typescript': [r'\.ts$', r'\.tsx$'],
        'java': [r'\.java$'],
        'kotlin': [r'\.kt$', r'\.kts$'],
        'scala': [r'\.scala$', r'\.sc$'],
        'go': [r'\.go$'],
        'rust': [r'\.rs$'],
        'c': [r'\.c$', r'\.h$'],
        'cpp': [r'\.cpp$', r'\.cxx$', r'\.cc$', r'\.hpp$', r'\.hxx$', r'\.hh$'],
        'csharp': [r'\.cs$', r'\.csx$'],
        'ruby': [r'\.rb$', r'\.rake$', r'\.gemspec$'],
        'php': [r'\.php$', r'\.phtml$', r'\.php3$', r'\.php4$', r'\.php5$'],
        'swift': [r'\.swift$'],
        'objectivec': [r'\.m$', r'\.mm$', r'\.h$'],
        'dart': [r'\.dart$'],
        'lua': [r'\.lua$'],
        'perl': [r'\.pl$', r'\.pm$', r'\.t$'],
        'r': [r'\.r$', r'\.R$'],
        'matlab': [r'\.m$'],
        'sql': [r'\.sql$'],
        'html': [r'\.html$', r'\.htm$', r'\.xhtml$'],
        'css': [r'\.css$', r'\.scss$', r'\.sass$', r'\.less$'],
        'markdown': [r'\.md$', r'\.markdown$'],
        'yaml': [r'\.yaml$', r'\.yml$'],
        'json': [r'\.json$'],
        'toml': [r'\.toml$'],
        'xml': [r'\.xml$'],
        'txt': [r'\.txt$', r'\.rst$'],
        'shell': [r'\.sh$', r'\.bash$', r'\.zsh$', r'\.fish$'],
        'powershell': [r'\.ps1$', r'\.psm1$', r'\.psd1$'],
        'docker': [r'Dockerfile', r'\.dockerignore$'],
        'makefile': [r'Makefile', r'makefile', r'\.mk$'],
    }
    
    def __init__(self, root_path: str, ignore_patterns: Optional[List[str]] = None,
                 custom_important_files: Optional[Set[str]] = None):
        """
        Initialize the analyzer.
        
        Args:
            root_path: Root directory of the project
            ignore_patterns: Additional ignore patterns (regex)
            custom_important_files: Additional important file names
        """
        self.root = Path(root_path).resolve()
        if not self.root.exists():
            raise ValueError(f"Path does not exist: {root_path}")
        
        self.ignore_patterns = self.DEFAULT_IGNORE_PATTERNS.copy()
        if ignore_patterns:
            self.ignore_patterns.extend(ignore_patterns)
        
        # Detect project type and build important files list
        self.project_type = self._detect_project_type()
        self.important_files = self._build_important_files()
        if custom_important_files:
            self.important_files.update(custom_important_files)
    
    def _detect_project_type(self) -> str:
        """Detect the primary project type based on files in the root directory."""
        type_indicators = {
            'python': ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile', '.python-version'],
            'javascript': ['package.json', 'node_modules'],
            'typescript': ['tsconfig.json', 'package.json'],
            'java': ['pom.xml', 'build.gradle', '.gradle'],
            'go': ['go.mod', 'go.sum'],
            'rust': ['Cargo.toml', 'Cargo.lock'],
            'c': ['CMakeLists.txt', 'configure', 'Makefile'],
            'cpp': ['CMakeLists.txt', 'configure', 'Makefile'],
            'csharp': ['.sln', '.csproj'],
            'ruby': ['Gemfile', 'Rakefile'],
            'php': ['composer.json', 'artisan'],
        }
        
        scores = {}
        for project_type, indicators in type_indicators.items():
            score = 0
            for indicator in indicators:
                if (self.root / indicator).exists():
                    score += 1
                # Also check in subdirectories for some indicators
                if indicator in ['node_modules', '.gradle']:
                    for path in self.root.rglob(indicator):
                        if path.is_dir():
                            score += 1
                            break
            scores[project_type] = score
        
        # Return project type with highest score, or 'unknown' if no matches
        if scores:
            max_score = max(scores.values())
            if max_score > 0:
                return max(scores.items(), key=lambda x: x[1])[0]
        
        return 'unknown'
    
    def _build_important_files(self) -> Set[str]:
        """Build important files set based on project type."""
        important = self.UNIVERSAL_IMPORTANT_FILES.copy()
        
        # Add language-specific files
        if self.project_type in self.LANGUAGE_IMPORTANT_FILES:
            important.update(self.LANGUAGE_IMPORTANT_FILES[self.project_type])
        
        # Add files for related languages (e.g., JS/TS often together)
        if self.project_type == 'typescript':
            important.update(self.LANGUAGE_IMPORTANT_FILES.get('javascript', set()))
        elif self.project_type == 'javascript':
            # Check if TypeScript is also present
            if (self.root / 'tsconfig.json').exists():
                important.update(self.LANGUAGE_IMPORTANT_FILES.get('typescript', set()))
        
        return important
    
    def _should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored."""
        path_str = str(path)
        rel_path = str(path.relative_to(self.root))
        
        for pattern in self.ignore_patterns:
            if re.search(pattern, path_str) or re.search(pattern, rel_path):
                return True
        
        # Check .gitignore if exists
        gitignore_path = self.root / '.gitignore'
        if gitignore_path.exists():
            if self._matches_gitignore(path, gitignore_path):
                return True
        
        return False
    
    def _matches_gitignore(self, path: Path, gitignore_path: Path) -> bool:
        """Simple gitignore pattern matching."""
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                patterns = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            rel_path = str(path.relative_to(self.root))
            for pattern in patterns:
                # Simple pattern matching (not full gitignore spec)
                if '*' in pattern or '?' in pattern:
                    import fnmatch
                    if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(path.name, pattern):
                        return True
                elif pattern in rel_path or pattern == path.name:
                    return True
        except Exception:
            pass
        return False
    
    def _detect_language(self, path: Path) -> str:
        """Detect programming language from file extension."""
        for lang, patterns in self.LANGUAGE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, path.name, re.IGNORECASE):
                    return lang
        return 'unknown'
    
    def _get_file_info(self, path: Path) -> FileInfo:
        """Extract information about a file."""
        relative_path = str(path.relative_to(self.root))
        size = path.stat().st_size
        
        # Count lines
        lines = 0
        try:
            with open(path, 'rb') as f:
                lines = sum(1 for _ in f)
        except Exception:
            pass
        
        language = self._detect_language(path)
        is_important = path.name in self.important_files or any(
            important in relative_path for important in self.important_files
        )
        
        # Calculate priority (higher = more important)
        priority = 0
        if is_important:
            priority += 10
        
        # Boost priority for files matching project's primary language
        primary_languages = {
            'python': ['python'],
            'javascript': ['javascript', 'typescript'],
            'typescript': ['javascript', 'typescript'],
            'java': ['java', 'kotlin', 'scala'],
            'go': ['go'],
            'rust': ['rust'],
            'c': ['c', 'cpp'],
            'cpp': ['c', 'cpp'],
            'csharp': ['csharp'],
            'ruby': ['ruby'],
            'php': ['php'],
        }
        
        if self.project_type in primary_languages:
            if language in primary_languages[self.project_type]:
                priority += 5
        
        if 'test' in relative_path.lower():
            priority -= 2  # Tests are less important for context
        if 'example' in relative_path.lower() or 'demo' in relative_path.lower():
            priority -= 1
        
        return FileInfo(
            path=path,
            relative_path=relative_path,
            size=size,
            lines=lines,
            language=language,
            is_important=is_important,
            priority=priority
        )
    
    def analyze(self) -> ProjectInfo:
        """Analyze the project and return project information."""
        files: List[FileInfo] = []
        structure: Dict[str, List[str]] = defaultdict(list)
        
        # Walk through the project
        for root, dirs, filenames in os.walk(self.root):
            root_path = Path(root)
            
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not self._should_ignore(root_path / d)]
            
            for filename in filenames:
                file_path = root_path / filename
                if self._should_ignore(file_path):
                    continue
                
                file_info = self._get_file_info(file_path)
                files.append(file_info)
                
                # Build structure
                rel_dir = str(file_path.parent.relative_to(self.root))
                if rel_dir == '.':
                    rel_dir = '/'
                structure[rel_dir].append(file_info.relative_path)
        
        # Sort files by priority (descending)
        files.sort(key=lambda f: f.priority, reverse=True)
        
        # Extract dependencies
        dependencies = self._extract_dependencies()
        
        # Extract Python version
        python_version = self._extract_python_version()
        
        # Extract description from README
        description = self._extract_description()
        
        return ProjectInfo(
            root=self.root,
            files=files,
            structure=dict(structure),
            dependencies=dependencies,
            project_type=self.project_type,
            python_version=python_version,
            description=description
        )
    
    def _extract_dependencies(self) -> List[str]:
        """Extract dependencies from various package manager files."""
        dependencies = []
        
        # Python dependencies
        req_file = self.root / 'requirements.txt'
        if req_file.exists():
            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            dependencies.append(f"python: {line}")
            except Exception:
                pass
        
        # Python pyproject.toml
        pyproject_file = self.root / 'pyproject.toml'
        if pyproject_file.exists():
            try:
                import tomllib
                with open(pyproject_file, 'rb') as f:
                    data = tomllib.load(f)
                    if 'project' in data and 'dependencies' in data['project']:
                        for dep in data['project']['dependencies']:
                            dependencies.append(f"python: {dep}")
            except Exception:
                try:
                    import tomli
                    with open(pyproject_file, 'rb') as f:
                        data = tomli.load(f)
                        if 'project' in data and 'dependencies' in data['project']:
                            for dep in data['project']['dependencies']:
                                dependencies.append(f"python: {dep}")
                except Exception:
                    pass
        
        # Node.js/JavaScript dependencies
        package_json = self.root / 'package.json'
        if package_json.exists():
            try:
                import json
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    deps = data.get('dependencies', {})
                    dev_deps = data.get('devDependencies', {})
                    for name, version in deps.items():
                        dependencies.append(f"npm: {name}@{version}")
                    for name, version in dev_deps.items():
                        dependencies.append(f"npm (dev): {name}@{version}")
            except Exception:
                pass
        
        # Java Maven dependencies
        pom_xml = self.root / 'pom.xml'
        if pom_xml.exists():
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(pom_xml)
                root = tree.getroot()
                # Handle namespace
                ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
                deps = root.findall('.//maven:dependency', ns)
                for dep in deps[:50]:  # Limit to first 50
                    group_id = dep.find('maven:groupId', ns)
                    artifact_id = dep.find('maven:artifactId', ns)
                    version = dep.find('maven:version', ns)
                    if group_id is not None and artifact_id is not None:
                        dep_str = f"{group_id.text}:{artifact_id.text}"
                        if version is not None and version.text:
                            dep_str += f":{version.text}"
                        dependencies.append(f"maven: {dep_str}")
            except Exception:
                pass
        
        # Go dependencies
        go_mod = self.root / 'go.mod'
        if go_mod.exists():
            try:
                with open(go_mod, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('require ') and not line.startswith('require ('):
                            parts = line.split()
                            if len(parts) >= 2:
                                dependencies.append(f"go: {parts[1]}")
                        elif line and not line.startswith(('module ', 'go ', '//', 'require (')):
                            parts = line.split()
                            if len(parts) >= 1:
                                dependencies.append(f"go: {parts[0]}")
            except Exception:
                pass
        
        # Rust dependencies
        cargo_toml = self.root / 'Cargo.toml'
        if cargo_toml.exists():
            try:
                import tomllib
                with open(cargo_toml, 'rb') as f:
                    data = tomllib.load(f)
                    deps = data.get('dependencies', {})
                    for name, version in deps.items():
                        if isinstance(version, str):
                            dependencies.append(f"cargo: {name} = \"{version}\"")
                        elif isinstance(version, dict):
                            ver = version.get('version', '?')
                            dependencies.append(f"cargo: {name} = \"{ver}\"")
            except Exception:
                try:
                    import tomli
                    with open(cargo_toml, 'rb') as f:
                        data = tomli.load(f)
                        deps = data.get('dependencies', {})
                        for name, version in deps.items():
                            if isinstance(version, str):
                                dependencies.append(f"cargo: {name} = \"{version}\"")
                            elif isinstance(version, dict):
                                ver = version.get('version', '?')
                                dependencies.append(f"cargo: {name} = \"{ver}\"")
                except Exception:
                    pass
        
        # Ruby dependencies
        gemfile = self.root / 'Gemfile'
        if gemfile.exists():
            try:
                with open(gemfile, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('gem ') and not line.startswith('#'):
                            # Extract gem name
                            parts = line.split("'")
                            if len(parts) >= 2:
                                dependencies.append(f"ruby: {parts[1]}")
            except Exception:
                pass
        
        # PHP dependencies
        composer_json = self.root / 'composer.json'
        if composer_json.exists():
            try:
                import json
                with open(composer_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    deps = data.get('require', {})
                    for name, version in deps.items():
                        dependencies.append(f"composer: {name} ({version})")
            except Exception:
                pass
        
        return dependencies
    
    def _extract_python_version(self) -> Optional[str]:
        """Extract Python version from .python-version or runtime.txt."""
        # Only extract Python version if this is a Python project
        if self.project_type not in ['python', 'unknown']:
            return None
        
        # Check .python-version
        py_version_file = self.root / '.python-version'
        if py_version_file.exists():
            try:
                with open(py_version_file, 'r', encoding='utf-8') as f:
                    version = f.read().strip()
                    if version:
                        return version
            except Exception:
                pass
        
        # Check runtime.txt (for Heroku)
        runtime_file = self.root / 'runtime.txt'
        if runtime_file.exists():
            try:
                with open(runtime_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    match = re.search(r'python-(\d+\.\d+\.?\d*)', content)
                    if match:
                        return match.group(1)
            except Exception:
                pass
        
        # Check pyproject.toml
        pyproject_file = self.root / 'pyproject.toml'
        if pyproject_file.exists():
            try:
                import tomllib
                with open(pyproject_file, 'rb') as f:
                    data = tomllib.load(f)
                    if 'project' in data and 'requires-python' in data['project']:
                        return data['project']['requires-python']
            except Exception:
                try:
                    import tomli
                    with open(pyproject_file, 'rb') as f:
                        data = tomli.load(f)
                        if 'project' in data and 'requires-python' in data['project']:
                            return data['project']['requires-python']
                except Exception:
                    pass
        
        return None
    
    def _extract_description(self) -> Optional[str]:
        """Extract project description from README."""
        readme_files = ['README.md', 'README.rst', 'README.txt', 'README']
        for readme_name in readme_files:
            readme_path = self.root / readme_name
            if readme_path.exists():
                try:
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Extract first paragraph or first few lines
                        lines = content.split('\n')
                        description_lines = []
                        for line in lines[:10]:  # First 10 lines
                            line = line.strip()
                            if line and not line.startswith('#'):
                                description_lines.append(line)
                                if len(description_lines) >= 3:
                                    break
                        if description_lines:
                            return ' '.join(description_lines)
                except Exception:
                    pass
        return None

