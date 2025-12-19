"""
Markdown generator module for creating formatted context from project analysis.
"""

import re
from typing import List, Optional, Dict
from pathlib import Path
from dataclasses import dataclass
from .analyzer import ProjectInfo, FileInfo


@dataclass
class GenerationConfig:
    """Configuration for markdown generation."""
    max_tokens: Optional[int] = None  # Approximate token limit
    max_files: Optional[int] = None  # Maximum number of files to include
    max_file_size: Optional[int] = None  # Max file size in bytes
    max_lines_per_file: Optional[int] = None  # Max lines per file
    include_structure: bool = True
    include_dependencies: bool = True
    include_metadata: bool = True
    compress_large_files: bool = True
    compress_threshold_lines: int = 200  # Compress files larger than this
    include_comments: bool = True
    add_instructions: bool = True
    file_separator: str = "\n\n---\n\n"


class MarkdownGenerator:
    """Generates markdown formatted context from project information."""
    
    # Approximate tokens per character (rough estimate)
    TOKENS_PER_CHAR = 0.25
    
    def __init__(self, config: Optional[GenerationConfig] = None):
        """Initialize the generator with configuration."""
        self.config = config or GenerationConfig()
    
    def generate(self, project_info: ProjectInfo) -> str:
        """Generate markdown context from project information."""
        parts = []
        
        # Header with instructions
        if self.config.add_instructions:
            parts.append(self._generate_header(project_info))
        
        # Architecture overview (new - Level 1)
        parts.append(self._generate_architecture_overview(project_info))
        
        # Project roadmap (new - key components map)
        parts.append(self._generate_project_roadmap(project_info))
        
        # Metadata section
        if self.config.include_metadata:
            parts.append(self._generate_metadata(project_info))
        
        # Dependencies
        if self.config.include_dependencies and project_info.dependencies:
            parts.append(self._generate_dependencies(project_info))
        
        # Project structure
        if self.config.include_structure:
            parts.append(self._generate_structure(project_info))
        
        # Thematic grouping of components (new - Level 2)
        parts.append(self._generate_thematic_components(project_info))
        
        # File contents (Level 3 - detailed)
        files_content = self._generate_files_content(project_info)
        parts.append(files_content)
        
        return "\n\n".join(parts)
    
    def _generate_header(self, project_info: ProjectInfo) -> str:
        """Generate header with instructions for LLM."""
        return f"""# Project Context: {project_info.root.name}

This document contains the complete context of the Python project located at `{project_info.root}`.

**Instructions for LLM:**
- This is a complete codebase context for analysis, modification, or understanding
- Files are organized by their directory structure
- Important files are marked and prioritized
- Use this context to understand the project architecture, dependencies, and implementation details
- When referencing files, use the relative paths provided

---
"""
    
    def _generate_metadata(self, project_info: ProjectInfo) -> str:
        """Generate metadata section."""
        metadata = ["## Project Metadata\n"]
        
        metadata.append(f"- **Project Root:** `{project_info.root}`")
        metadata.append(f"- **Total Files:** {len(project_info.files)}")
        
        if project_info.python_version:
            metadata.append(f"- **Python Version:** {project_info.python_version}")
        
        if project_info.description:
            metadata.append(f"- **Description:** {project_info.description}")
        
        # Calculate total size
        total_size = sum(f.size for f in project_info.files)
        size_mb = total_size / (1024 * 1024)
        metadata.append(f"- **Total Size:** {size_mb:.2f} MB")
        
        # Count by language
        lang_counts = {}
        for file_info in project_info.files:
            lang_counts[file_info.language] = lang_counts.get(file_info.language, 0) + 1
        
        if lang_counts:
            metadata.append("\n**Files by Language:**")
            for lang, count in sorted(lang_counts.items(), key=lambda x: x[1], reverse=True):
                metadata.append(f"  - {lang}: {count} files")
        
        return "\n".join(metadata)
    
    def _generate_structure(self, project_info: ProjectInfo) -> str:
        """Generate project structure tree."""
        lines = ["## Project Structure\n"]
        lines.append("```")
        lines.append(self._build_tree(project_info.structure, project_info.root.name))
        lines.append("```")
        return "\n".join(lines)
    
    def _build_tree(self, structure: Dict[str, List[str]], root_name: str) -> str:
        """Build a tree representation of the project structure."""
        lines = [root_name + "/"]
        
        # Organize structure by directory depth
        dirs_by_depth = {}
        for directory in structure.keys():
            if directory == '/':
                depth = 0
            else:
                depth = len(Path(directory).parts)
            if depth not in dirs_by_depth:
                dirs_by_depth[depth] = []
            dirs_by_depth[depth].append(directory)
        
        # Sort directories at each depth
        for depth in sorted(dirs_by_depth.keys()):
            dirs_by_depth[depth].sort()
        
        # Build tree recursively
        def add_directory(dir_path: str, prefix: str, is_last: bool):
            """Add directory and its contents to tree."""
            if dir_path == '/':
                dir_name = root_name
                files = structure.get('/', [])
            else:
                dir_name = Path(dir_path).name
                files = [f for f in structure.get(dir_path, []) 
                        if str(Path(f).parent) == dir_path or (dir_path == '/' and str(Path(f).parent) == '.')]
            
            # Add directory line (skip root)
            if dir_path != '/':
                lines.append(prefix + ("└── " if is_last else "├── ") + dir_name + "/")
                new_prefix = prefix + ("    " if is_last else "│   ")
            else:
                new_prefix = ""
            
            # Add files in this directory
            sorted_files = sorted(set(files))
            for j, file_path in enumerate(sorted_files):
                file_is_last = j == len(sorted_files) - 1
                file_name = Path(file_path).name
                file_prefix = new_prefix + ("└── " if file_is_last else "├── ")
                lines.append(file_prefix + file_name)
            
            # Add subdirectories
            if dir_path == '/':
                subdirs = [d for d in structure.keys() if d != '/' and len(Path(d).parts) == 1]
            else:
                subdirs = [d for d in structure.keys() 
                          if d != '/' and str(Path(d).parent) == dir_path]
            
            subdirs.sort()
            for k, subdir in enumerate(subdirs):
                subdir_is_last = k == len(subdirs) - 1
                add_directory(subdir, new_prefix, subdir_is_last)
        
        # Start with root
        add_directory('/', '', True)
        
        return "\n".join(lines)
    
    def _generate_dependencies(self, project_info: ProjectInfo) -> str:
        """Generate dependencies section."""
        lines = ["## Dependencies\n"]
        lines.append("```")
        for dep in project_info.dependencies:
            lines.append(dep)
        lines.append("```")
        return "\n".join(lines)
    
    def _generate_architecture_overview(self, project_info: ProjectInfo) -> str:
        """Generate architecture overview (Level 1 - high level)."""
        lines = ["## 🌐 Architecture Overview\n"]
        
        # Detect project type from structure and files
        project_type = self._detect_project_type(project_info)
        lines.append(f"- **Project Type:** {project_type}")
        
        # Key technologies from dependencies
        key_tech = self._extract_key_technologies(project_info.dependencies)
        if key_tech:
            lines.append(f"- **Key Technologies:** {', '.join(key_tech)}")
        
        # Main entry point
        entry_point = self._find_entry_point(project_info)
        if entry_point:
            lines.append(f"- **Entry Point:** `{entry_point.relative_path}`")
        
        # Brief description
        if project_info.description:
            lines.append(f"\n**Description:** {project_info.description}")
        else:
            lines.append(f"\n**Description:** Python project with {len(project_info.files)} files")
        
        # Architecture pattern detection
        arch_pattern = self._detect_architecture_pattern(project_info)
        if arch_pattern:
            lines.append(f"- **Architecture Pattern:** {arch_pattern}")
        
        return "\n".join(lines)
    
    def _generate_project_roadmap(self, project_info: ProjectInfo) -> str:
        """Generate project roadmap with key components."""
        lines = ["## 🗺️ Project Roadmap\n"]
        
        # Entry point
        entry_point = self._find_entry_point(project_info)
        if entry_point:
            lines.append(f"- **🚪 Entry Point:** `{entry_point.relative_path}`")
        
        # Core business logic files (high priority, large files)
        core_files = [f for f in project_info.files 
                     if f.is_important and f.language == 'python' 
                     and f.priority >= 10 and f.lines > 50]
        core_files.sort(key=lambda x: (x.priority, x.lines), reverse=True)
        
        if core_files:
            lines.append("\n- **💼 Core Business Logic:**")
            for f in core_files[:5]:  # Top 5
                importance = self._get_importance_stars(f)
                lines.append(f"  - {importance} `{f.relative_path}` ({f.lines} lines)")
        
        # Critical dependencies
        critical_deps = self._identify_critical_dependencies(project_info.dependencies)
        if critical_deps:
            lines.append("\n- **🔗 Critical Dependencies:**")
            for dep in critical_deps:
                lines.append(f"  - {dep}")
        
        # Most complex component
        complex_file = max(project_info.files, key=lambda f: f.lines) if project_info.files else None
        if complex_file and complex_file.lines > 200:
            lines.append(f"\n- **⚙️ Most Complex Component:** `{complex_file.relative_path}` ({complex_file.lines} lines)")
        
        return "\n".join(lines)
    
    def _generate_thematic_components(self, project_info: ProjectInfo) -> str:
        """Generate thematic grouping of components (Level 2)."""
        lines = ["## 🧩 Key Components by Functionality\n"]
        
        # Group files by functionality/themes
        themes = self._group_by_themes(project_info.files)
        
        theme_icons = {
            'authentication': '🔐',
            'api': '🌐',
            'database': '💾',
            'websocket': '🔌',
            'chat': '💬',
            'config': '⚙️',
            'utils': '🛠️',
            'tests': '🧪',
            'main': '🚀',
        }
        
        for theme, files in themes.items():
            if not files:
                continue
            
            icon = theme_icons.get(theme, '📁')
            lines.append(f"\n### {icon} {theme.capitalize()}")
            
            # Sort by importance
            files.sort(key=lambda f: (f.priority, f.lines), reverse=True)
            
            for file_info in files[:10]:  # Top 10 per theme
                importance = self._get_importance_stars(file_info)
                lines.append(f"- {importance} **`{file_info.relative_path}`**")
                lines.append(f"  - *{file_info.lines} lines | {file_info.language}*")
                
                # Add context if important
                if file_info.is_important and file_info.lines > 100:
                    context = self._get_file_context(file_info)
                    if context:
                        lines.append(f"  - *Purpose: {context}*")
        
        return "\n".join(lines)
    
    def _get_importance_stars(self, file_info: FileInfo) -> str:
        """Get importance stars representation."""
        if file_info.priority >= 15:
            return "⭐⭐⭐"
        elif file_info.priority >= 10:
            return "⭐⭐"
        elif file_info.is_important:
            return "⭐"
        else:
            return "⬜"
    
    def _detect_project_type(self, project_info: ProjectInfo) -> str:
        """Detect project type from structure."""
        file_names = [f.path.name.lower() for f in project_info.files]
        
        if any('fastapi' in str(f.path) or 'main.py' in str(f.path) for f in project_info.files):
            if any('websocket' in str(f.path).lower() for f in project_info.files):
                return "FastAPI WebSocket Application"
            return "FastAPI Application"
        elif any('django' in str(f.path).lower() for f in project_info.files):
            return "Django Application"
        elif any('flask' in str(f.path).lower() for f in project_info.files):
            return "Flask Application"
        elif 'manage.py' in file_names:
            return "Django Project"
        elif any('test' in str(f.path).lower() for f in project_info.files):
            return "Python Project with Tests"
        else:
            return "Python Application"
    
    def _extract_key_technologies(self, dependencies: List[str]) -> List[str]:
        """Extract key technologies from dependencies."""
        key_tech = []
        tech_keywords = {
            'fastapi': 'FastAPI',
            'django': 'Django',
            'flask': 'Flask',
            'sqlalchemy': 'SQLAlchemy',
            'redis': 'Redis',
            'postgresql': 'PostgreSQL',
            'mongodb': 'MongoDB',
            'celery': 'Celery',
            'websocket': 'WebSocket',
            'pydantic': 'Pydantic',
        }
        
        deps_str = ' '.join(dependencies).lower()
        for keyword, tech_name in tech_keywords.items():
            if keyword in deps_str:
                key_tech.append(tech_name)
        
        return key_tech[:5]  # Top 5
    
    def _find_entry_point(self, project_info: ProjectInfo) -> Optional[FileInfo]:
        """Find main entry point of the project."""
        entry_points = ['main.py', 'app.py', 'run.py', '__main__.py']
        
        for file_info in project_info.files:
            if file_info.path.name in entry_points:
                return file_info
        
        # Look for files with 'if __name__ == "__main__"'
        for file_info in sorted(project_info.files, key=lambda f: f.priority, reverse=True):
            if file_info.language == 'python' and file_info.lines > 10:
                try:
                    with open(file_info.path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if '__name__' in content and '__main__' in content:
                            return file_info
                except Exception:
                    pass
        
        return None
    
    def _detect_architecture_pattern(self, project_info: ProjectInfo) -> Optional[str]:
        """Detect architecture pattern."""
        dirs = [str(Path(f.relative_path).parent) for f in project_info.files]
        dirs_str = ' '.join(dirs).lower()
        
        if 'mvc' in dirs_str or ('model' in dirs_str and 'view' in dirs_str):
            return "MVC"
        elif 'service' in dirs_str or 'services' in dirs_str:
            return "Service Layer"
        elif 'repository' in dirs_str:
            return "Repository Pattern"
        elif 'handler' in dirs_str or 'handlers' in dirs_str:
            return "Handler Pattern"
        
        return None
    
    def _identify_critical_dependencies(self, dependencies: List[str]) -> List[str]:
        """Identify critical dependencies."""
        critical = []
        critical_keywords = ['redis', 'postgresql', 'mysql', 'mongodb', 'sqlite', 
                           'celery', 'websocket', 'fastapi', 'django', 'flask']
        
        for dep in dependencies:
            dep_lower = dep.lower()
            for keyword in critical_keywords:
                if keyword in dep_lower:
                    critical.append(dep)
                    break
        
        return critical[:5]  # Top 5
    
    def _group_by_themes(self, files: List[FileInfo]) -> Dict[str, List[FileInfo]]:
        """Group files by thematic categories."""
        themes: Dict[str, List[FileInfo]] = {
            'authentication': [],
            'api': [],
            'database': [],
            'websocket': [],
            'chat': [],
            'config': [],
            'utils': [],
            'tests': [],
            'main': [],
            'other': [],
        }
        
        for file_info in files:
            path_lower = file_info.relative_path.lower()
            name_lower = file_info.path.name.lower()
            
            if 'auth' in path_lower or 'login' in path_lower or 'jwt' in path_lower:
                themes['authentication'].append(file_info)
            elif 'api' in path_lower or 'router' in path_lower or 'route' in path_lower:
                themes['api'].append(file_info)
            elif 'db' in path_lower or 'database' in path_lower or 'model' in path_lower or 'schema' in path_lower:
                themes['database'].append(file_info)
            elif 'websocket' in path_lower or 'ws' in path_lower:
                themes['websocket'].append(file_info)
            elif 'chat' in path_lower or 'message' in path_lower:
                themes['chat'].append(file_info)
            elif 'config' in name_lower or 'setting' in name_lower:
                themes['config'].append(file_info)
            elif 'util' in path_lower or 'helper' in path_lower or 'common' in path_lower:
                themes['utils'].append(file_info)
            elif 'test' in path_lower:
                themes['tests'].append(file_info)
            elif name_lower in ['main.py', 'app.py', 'run.py']:
                themes['main'].append(file_info)
            else:
                themes['other'].append(file_info)
        
        # Remove empty themes
        return {k: v for k, v in themes.items() if v}
    
    def _get_file_context(self, file_info: FileInfo) -> str:
        """Get context/purpose of a file by analyzing its content."""
        try:
            with open(file_info.path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1000)  # Read first 1000 chars
            
            # Look for docstrings or comments
            if '"""' in content or "'''" in content:
                # Try to extract docstring
                docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
                if docstring_match:
                    doc = docstring_match.group(1).strip()
                    if len(doc) < 200:
                        return doc.split('\n')[0]
            
            # Look for class/function names
            if 'class ' in content:
                class_match = re.search(r'class\s+(\w+)', content)
                if class_match:
                    return f"Class: {class_match.group(1)}"
            
            if 'def ' in content:
                func_match = re.search(r'def\s+(\w+)', content)
                if func_match:
                    return f"Function: {func_match.group(1)}"
        except Exception:
            pass
        
        return ""
    
    def _generate_files_content(self, project_info: ProjectInfo) -> str:
        """Generate file contents section."""
        lines = ["## File Contents\n"]
        
        # Filter and sort files
        files_to_include = self._select_files(project_info.files)
        
        current_dir = None
        for file_info in files_to_include:
            file_dir = str(Path(file_info.relative_path).parent)
            if file_dir == '.':
                file_dir = '/'
            
            # Add directory header if changed
            if file_dir != current_dir:
                if current_dir is not None:
                    lines.append("")  # Empty line between directories
                lines.append(f"### Directory: `{file_dir}`\n")
                current_dir = file_dir
            
            # Add file content
            file_content = self._generate_file_content(file_info)
            lines.append(file_content)
            lines.append(self.config.file_separator)
        
        return "\n".join(lines)
    
    def _select_files(self, files: List[FileInfo]) -> List[FileInfo]:
        """Select which files to include based on configuration."""
        selected = []
        total_tokens = 0
        
        # Separate important and regular files
        important_files = [f for f in files if f.is_important]
        regular_files = [f for f in files if not f.is_important]
        
        # First, add important files (up to limit)
        for file_info in important_files:
            # Skip if max files reached
            if self.config.max_files and len(selected) >= self.config.max_files:
                break
            
            # Skip if file too large (unless we can compress)
            if self.config.max_file_size and file_info.size > self.config.max_file_size:
                if not self.config.compress_large_files:
                    continue
            
            # Estimate tokens for this file
            file_tokens = self._estimate_file_tokens(file_info)
            
            # Check token limit
            if self.config.max_tokens:
                if total_tokens + file_tokens > self.config.max_tokens:
                    # If important and compress enabled, include anyway (will be compressed)
                    if self.config.compress_large_files:
                        selected.append(file_info)
                        total_tokens += file_tokens // 3  # Compressed files use ~1/3 tokens
                    continue
                else:
                    total_tokens += file_tokens
            else:
                total_tokens += file_tokens
            
            selected.append(file_info)
        
        # Then add regular files if we have space
        for file_info in regular_files:
            # Skip if max files reached
            if self.config.max_files and len(selected) >= self.config.max_files:
                break
            
            # Skip if file too large
            if self.config.max_file_size and file_info.size > self.config.max_file_size:
                continue
            
            # Estimate tokens for this file
            file_tokens = self._estimate_file_tokens(file_info)
            
            # Check token limit
            if self.config.max_tokens:
                if total_tokens + file_tokens > self.config.max_tokens:
                    break
            
            selected.append(file_info)
            total_tokens += file_tokens
        
        return selected
    
    def _estimate_file_tokens(self, file_info: FileInfo) -> int:
        """Estimate token count for a file."""
        # Rough estimate: size in bytes * tokens_per_char
        return int(file_info.size * self.TOKENS_PER_CHAR)
    
    def _generate_file_content(self, file_info: FileInfo) -> str:
        """Generate markdown representation of a file."""
        lines = []
        
        # File header with improved importance system
        importance_stars = self._get_importance_stars(file_info)
        lines.append(f"#### {importance_stars} File: `{file_info.relative_path}`")
        lines.append(f"*Language: {file_info.language} | Lines: {file_info.lines} | Size: {file_info.size} bytes*")
        
        # Add context for important files
        if file_info.is_important and file_info.lines > 50:
            context = self._get_file_context(file_info)
            if context:
                lines.append(f"*Purpose: {context}*")
        
        lines.append("")
        
        # Read and process file content
        try:
            with open(file_info.path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Always include full file content - no compression or truncation
            # Remove comments if requested
            if not self.config.include_comments and file_info.language == 'python':
                content = self._remove_python_comments(content)
            
            # Add code block
            lang_tag = file_info.language if file_info.language != 'unknown' else ''
            lines.append(f"```{lang_tag}")
            lines.append(content)
            lines.append("```")
            
        except Exception as e:
            lines.append(f"*Error reading file: {str(e)}*")
        
        return "\n".join(lines)
    
    def _compress_file_content(self, content: str, file_info: FileInfo) -> str:
        """Compress large file content by showing structure and key parts."""
        if file_info.language != 'python':
            # For non-Python files, just truncate
            lines = content.split('\n')
            if len(lines) > 100:
                return '\n'.join(lines[:50]) + f"\n\n... (truncated, showing first 50 of {len(lines)} lines) ...\n\n" + '\n'.join(lines[-50:])
            return content
        
        # For Python files, extract structure
        lines = content.split('\n')
        compressed = []
        compressed.append("# File structure and key components:\n")
        
        # Extract imports
        imports = [line for line in lines if line.strip().startswith(('import ', 'from '))]
        if imports:
            compressed.append("## Imports:")
            compressed.extend(imports[:20])  # Limit imports
            if len(imports) > 20:
                compressed.append(f"# ... and {len(imports) - 20} more imports")
            compressed.append("")
        
        # Extract class and function definitions
        definitions = []
        indent_level = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Detect class/function definitions
            if stripped.startswith(('class ', 'def ', 'async def ')):
                # Calculate indent
                indent = len(line) - len(line.lstrip())
                if indent <= indent_level + 4:  # New top-level or slightly nested
                    definitions.append((i, line, indent))
                    indent_level = indent
        
        if definitions:
            compressed.append("## Key Definitions:")
            for idx, (line_num, def_line, indent) in enumerate(definitions[:30]):  # Limit definitions
                compressed.append(def_line)
                # Include a few lines after definition (docstring, etc.)
                for j in range(line_num + 1, min(line_num + 5, len(lines))):
                    if lines[j].strip():
                        compressed.append(lines[j])
                        if not lines[j].strip().startswith(('"""', "'''", '#')):
                            break
                compressed.append("")
            
            if len(definitions) > 30:
                compressed.append(f"# ... and {len(definitions) - 30} more definitions")
        
        compressed.append("\n# Full file content (truncated for large files):")
        compressed.append("# Showing first and last portions...")
        compressed.append("")
        compressed.append("".join(lines[:50]))
        compressed.append("\n... (middle section omitted) ...\n")
        compressed.append("".join(lines[-50:]))
        
        return '\n'.join(compressed)
    
    def _remove_python_comments(self, content: str) -> str:
        """Remove Python comments from code."""
        lines = content.split('\n')
        cleaned = []
        in_multiline = False
        multiline_char = None
        
        for line in lines:
            # Handle multiline strings/comments
            if '"""' in line or "'''" in line:
                # Simple toggle (not perfect but works for most cases)
                if not in_multiline:
                    multiline_char = '"""' if '"""' in line else "'''"
                    in_multiline = True
                elif multiline_char in line:
                    in_multiline = False
                    multiline_char = None
                cleaned.append(line)
                continue
            
            if in_multiline:
                cleaned.append(line)
                continue
            
            # Remove inline comments
            if '#' in line:
                # Check if # is in a string
                in_string = False
                quote_char = None
                for i, char in enumerate(line):
                    if char in ('"', "'") and (i == 0 or line[i-1] != '\\'):
                        if not in_string:
                            in_string = True
                            quote_char = char
                        elif char == quote_char:
                            in_string = False
                            quote_char = None
                    elif char == '#' and not in_string:
                        line = line[:i]
                        break
                cleaned.append(line)
            else:
                cleaned.append(line)
        
        return '\n'.join(cleaned)

