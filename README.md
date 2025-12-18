# CMforAI
Context Manager for LLMs

> **⚠️ ВНИМАНИЕ: ПРОЕКТ НАХОДИТСЯ НА НАЧАЛЬНОЙ СТАДИИ РАЗРАБОТКИ И МОЖЕТ БЫТЬ СЫРЫМ. ИСПОЛЬЗУЙТЕ НА СВОЙ РИСК. ⚠️**
> 
> **⚠️ WARNING: PROJECT IS IN EARLY DEVELOPMENT STAGE AND MAY BE ROUGH. USE AT YOUR OWN RISK. ⚠️**

A powerful tool to extract and format project context for LLM consumption. Designed to help you quickly share your codebase context with ChatGPT, Qwen, Claude, and other LLMs.

## Features

- 🔍 **Smart Project Analysis**: Automatically analyzes projects (Python, JavaScript/TypeScript, Java, Go, Rust, and more) and identifies important files
- 📝 **Markdown Output**: Generates well-formatted markdown context ready for LLM consumption
- 🎯 **Intelligent Filtering**: Excludes unnecessary files (`.git`, `__pycache__`, `venv`, etc.)
- 📊 **Large Project Support**: Handles very large projects with compression and token limits
- ⚙️ **Flexible Configuration**: Highly configurable with command-line options and config files
- 🖥️ **Dual Interface**: Both CLI and GUI interfaces available
- 🚀 **Fast & Efficient**: Optimized for large codebases

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/CMforAI.git
cd CMforAI

# Install the package
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt
```

## Usage

### Command Line Interface

Basic usage:
```bash
cmforai /path/to/your/project
```

Save to file:
```bash
cmforai /path/to/your/project -o output.md
```

With token limit:
```bash
cmforai /path/to/your/project --max-tokens 50000 -o context.md
```

Limit number of files:
```bash
cmforai /path/to/your/project --max-files 100 -o context.md
```

Custom ignore patterns:
```bash
cmforai /path/to/your/project --ignore ".*\.log$" --ignore "test_.*"
```

### Graphical User Interface

Launch the GUI:
```bash
cmforai-gui
```

Or:
```bash
python -m cmforai.gui
```

The GUI provides:
- Project browser and analyzer
- Interactive configuration
- Real-time preview
- Save to file or copy to clipboard

### Configuration Options

#### Command-Line Options

- `-o, --output`: Output file path (default: stdout)
- `--max-tokens`: Maximum approximate token count
- `--max-files`: Maximum number of files to include
- `--max-file-size`: Maximum file size in bytes
- `--max-lines-per-file`: Maximum lines per file
- `--compress-threshold`: Compress files larger than N lines (default: 200)
- `--no-compress`: Disable compression of large files
- `--no-comments`: Remove comments from code
- `--no-structure`: Do not include project structure tree
- `--no-dependencies`: Do not include dependencies section
- `--no-metadata`: Do not include metadata section
- `--no-instructions`: Do not include LLM instructions header
- `--ignore`: Additional ignore patterns (regex, can be used multiple times)
- `--important`: Additional important file names (can be used multiple times)

#### Configuration File

Create a `.cmforai.json` file in your project root or in `~/.config/cmforai/.cmforai.json`:

```json
{
  "generation_config": {
    "max_tokens": 50000,
    "max_files": 100,
    "max_file_size": 1000000,
    "max_lines_per_file": 1000,
    "compress_large_files": true,
    "compress_threshold_lines": 200,
    "include_comments": true,
    "include_structure": true,
    "include_dependencies": true,
    "include_metadata": true,
    "add_instructions": true
  },
  "custom_ignore_patterns": [
    ".*\\.log$",
    ".*\\.tmp$"
  ],
  "custom_important_files": [
    "custom_config.py",
    "important_file.txt"
  ]
}
```

## How It Works

1. **Analysis**: Scans the project directory, identifies files, and extracts metadata
2. **Filtering**: Applies ignore patterns and prioritizes important files
3. **Selection**: Selects files based on configuration (token limits, file limits, etc.)
4. **Compression**: Compresses large files by extracting structure and key components
5. **Generation**: Formats everything into a markdown document with:
   - Project metadata
   - Directory structure tree
   - Dependencies list
   - File contents with syntax highlighting

## Output Format

The generated markdown includes:

- **Header**: Instructions for the LLM
- **Metadata**: Project information (size, file count, Python version, etc.)
- **Structure**: Tree view of project directories
- **Dependencies**: List of project dependencies
- **File Contents**: All selected files with code blocks

## Examples

### Small Project
```bash
cmforai ./my-project -o context.md
```

### Large Project with Limits
```bash
cmforai ./large-project --max-tokens 100000 --max-files 200 -o context.md
```

### Focus on Important Files Only
```bash
cmforai ./project --max-files 50 --no-compress -o important.md
```

## Requirements

- Python 3.8+
- customtkinter >= 5.2.0
- pyyaml >= 6.0.1

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

kurtatter
