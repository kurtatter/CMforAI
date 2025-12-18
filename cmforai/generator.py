"""
Markdown generator module for creating formatted context from project analysis.
"""

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
        
        # Metadata section
        if self.config.include_metadata:
            parts.append(self._generate_metadata(project_info))
        
        # Project structure
        if self.config.include_structure:
            parts.append(self._generate_structure(project_info))
        
        # Dependencies
        if self.config.include_dependencies and project_info.dependencies:
            parts.append(self._generate_dependencies(project_info))
        
        # File contents
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
        
        # File header
        importance_marker = " ⭐" if file_info.is_important else ""
        lines.append(f"#### File: `{file_info.relative_path}`{importance_marker}")
        lines.append(f"*Language: {file_info.language} | Lines: {file_info.lines} | Size: {file_info.size} bytes*")
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

