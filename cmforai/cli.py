"""
Command-line interface for CMforAI.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional
from .analyzer import ProjectAnalyzer
from .generator import MarkdownGenerator, GenerationConfig
from .config import ConfigManager, AppConfig


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description='Context Manager for LLMs - Extract and format project context',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  cmforai /path/to/project                    # Generate context for project
  cmforai /path/to/project -o output.md       # Save to file
  cmforai /path/to/project --max-tokens 50000 # Limit token count
  cmforai /path/to/project --max-files 100    # Limit number of files
        """
    )

    parser.add_argument(
        'project_path',
        type=str,
        help='Path to the project directory'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Output file path (default: print to stdout)'
    )

    # Generation options
    parser.add_argument(
        '--max-tokens',
        type=int,
        default=None,
        help='Maximum approximate token count (default: unlimited)'
    )

    parser.add_argument(
        '--max-files',
        type=int,
        default=None,
        help='Maximum number of files to include (default: unlimited)'
    )

    parser.add_argument(
        '--max-file-size',
        type=int,
        default=None,
        help='Maximum file size in bytes (default: unlimited)'
    )

    parser.add_argument(
        '--max-lines-per-file',
        type=int,
        default=None,
        help='Maximum lines per file (default: unlimited)'
    )

    parser.add_argument(
        '--compress-threshold',
        type=int,
        default=200,
        help='Compress files larger than this many lines (default: 200)'
    )

    parser.add_argument(
        '--no-compress',
        action='store_true',
        help='Disable compression of large files'
    )

    parser.add_argument(
        '--no-comments',
        action='store_true',
        help='Remove comments from code'
    )

    parser.add_argument(
        '--no-structure',
        action='store_true',
        help='Do not include project structure tree'
    )

    parser.add_argument(
        '--no-dependencies',
        action='store_true',
        help='Do not include dependencies section'
    )

    parser.add_argument(
        '--no-metadata',
        action='store_true',
        help='Do not include metadata section'
    )

    parser.add_argument(
        '--no-instructions',
        action='store_true',
        help='Do not include LLM instructions header'
    )

    # Ignore patterns
    parser.add_argument(
        '--ignore',
        type=str,
        action='append',
        default=[],
        help='Additional ignore patterns (regex, can be used multiple times)'
    )

    # Important files
    parser.add_argument(
        '--important',
        type=str,
        action='append',
        default=[],
        help='Additional important file names (can be used multiple times)'
    )

    # Config file
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to configuration file (default: use default config)'
    )

    parser.add_argument(
        '--files',
        nargs='+',
        default=None,
        help='Analyze only specified files (relative paths), but keep project metadata'
    )

    parser.add_argument(
        '--gitlogs', 
        type=int, 
        nargs='?', 
        const=5, 
        default=None,
        help='Include git commit history (optionally specify number of commits, default 5)'
    )

    return parser


def print_console_banner():
    print("\033[40m\033[97m")  # черный фон, белый текст
    print("00000000  3c 73 69 6d 70 6c 65 2e  68 61 72 64 57 6f 72 6b  |<simple.hardWork|")
    print("00000010  2e 68 61 72 64 43 6f 64  65 3e 20 20 4b 52 59 20  |.hardCode>  KRY |")
    print("00000020  43 4f 44 45 20 49 53 20  4c 41 57 00 00 00 00 00  |CODE IS LAW.....|")
    print("00000030  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  |................|")
    print(">> Checksum valid. Core philosophy verified.", "\033[0m")


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Validate project path
    project_path = Path(args.project_path).resolve()
    if not project_path.exists():
        print(f"Error: Project path does not exist: {project_path}", file=sys.stderr)
        sys.exit(1)

    if not project_path.is_dir():
        print(f"Error: Project path is not a directory: {project_path}", file=sys.stderr)
        sys.exit(1)

    # Load configuration
    config_manager = ConfigManager()
    app_config = config_manager.load()

    # Override with project-specific config if exists
    project_config = config_manager.load_project_config(project_path)
    if project_config:
        app_config = project_config

    # Override with command-line arguments
    gen_config = app_config.generation_config

    if args.max_tokens is not None:
        gen_config.max_tokens = args.max_tokens
    if args.max_files is not None:
        gen_config.max_files = args.max_files
    if args.max_file_size is not None:
        gen_config.max_file_size = args.max_file_size
    if args.max_lines_per_file is not None:
        gen_config.max_lines_per_file = args.max_lines_per_file
    if args.compress_threshold is not None:
        gen_config.compress_threshold_lines = args.compress_threshold
    if args.no_compress:
        gen_config.compress_large_files = False
    if args.no_comments:
        gen_config.include_comments = False
    if args.no_structure:
        gen_config.include_structure = False
    if args.no_dependencies:
        gen_config.include_dependencies = False
    if args.no_metadata:
        gen_config.include_metadata = False
    if args.no_instructions:
        gen_config.add_instructions = False
    if args.files:
        gen_config.files_to_analyze = args.files
    if args.gitlogs:
        gen_config.gitlogs = args.gitlogs

    # Merge ignore patterns and important files
    ignore_patterns = app_config.custom_ignore_patterns + args.ignore
    important_files = set(app_config.custom_important_files + args.important)

    try:
        # Analyze project
        print_console_banner()
        print(f"Analyzing project: {project_path}", file=sys.stderr)
        analyzer = ProjectAnalyzer(
            str(project_path),
            ignore_patterns=ignore_patterns if ignore_patterns else None,
            custom_important_files=important_files if important_files else None
        )
        project_info = analyzer.analyze()

        print(f"Found {len(project_info.files)} files", file=sys.stderr)

        # Generate markdown
        print("Generating markdown context...", file=sys.stderr)
        generator = MarkdownGenerator(gen_config)
        markdown = generator.generate(project_info)

        # Output
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
            print(f"Context saved to: {output_path}", file=sys.stderr)
        else:
            print(markdown)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
