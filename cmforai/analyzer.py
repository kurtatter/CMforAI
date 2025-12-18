"""
Project analyzer module for extracting and analyzing Python project structure.
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
    python_version: Optional[str] = None
    description: Optional[str] = None


class ProjectAnalyzer:
    """Analyzes Python projects and extracts relevant information."""
    
    # Common important files for Python projects
    IMPORTANT_FILES = {
        'main.py', 'app.py', 'run.py', 'manage.py', '__init__.py',
        'setup.py', 'setup.cfg', 'pyproject.toml', 'requirements.txt',
        'requirements-dev.txt', 'Pipfile', 'Pipfile.lock', 'poetry.lock',
        'README.md', 'README.rst', 'README.txt', 'LICENSE', 'CHANGELOG.md',
        'config.py', 'settings.py', 'config.yaml', 'config.yml', '.env.example'
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
    
    # Language detection patterns
    LANGUAGE_PATTERNS = {
        'python': [r'\.py$', r'\.pyw$', r'\.pyi$'],
        'markdown': [r'\.md$', r'\.markdown$'],
        'yaml': [r'\.yaml$', r'\.yml$'],
        'json': [r'\.json$'],
        'toml': [r'\.toml$'],
        'txt': [r'\.txt$', r'\.rst$'],
        'shell': [r'\.sh$', r'\.bash$'],
        'docker': [r'Dockerfile', r'\.dockerignore$'],
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
        
        self.important_files = self.IMPORTANT_FILES.copy()
        if custom_important_files:
            self.important_files.update(custom_important_files)
    
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
        if language == 'python':
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
            python_version=python_version,
            description=description
        )
    
    def _extract_dependencies(self) -> List[str]:
        """Extract dependencies from requirements.txt or pyproject.toml."""
        dependencies = []
        
        # Check requirements.txt
        req_file = self.root / 'requirements.txt'
        if req_file.exists():
            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            dependencies.append(line)
            except Exception:
                pass
        
        # Check pyproject.toml
        pyproject_file = self.root / 'pyproject.toml'
        if pyproject_file.exists():
            try:
                import tomllib
                with open(pyproject_file, 'rb') as f:
                    data = tomllib.load(f)
                    if 'project' in data and 'dependencies' in data['project']:
                        dependencies.extend(data['project']['dependencies'])
            except Exception:
                try:
                    import tomli
                    with open(pyproject_file, 'rb') as f:
                        data = tomli.load(f)
                        if 'project' in data and 'dependencies' in data['project']:
                            dependencies.extend(data['project']['dependencies'])
                except Exception:
                    pass
        
        return dependencies
    
    def _extract_python_version(self) -> Optional[str]:
        """Extract Python version from .python-version or runtime.txt."""
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

