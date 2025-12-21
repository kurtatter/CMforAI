import argparse
import sys
from pathlib import Path
from typing import List, Optional
from .analyzer import ProjectAnalyzer, FileInfo
from .generator import MarkdownGenerator, GenerationConfig
from .config import ConfigManager

def create_parser() -> argparse.ArgumentParser:
    """Создание парсера аргументов для анализа конкретных файлов"""
    parser = argparse.ArgumentParser(
        description='CMforAI File Analyzer - Анализ конкретных файлов с сохранением метаинформации проекта',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Примеры:
        cmforai-file-analyzer /path/to/project file1.py file2.py -o context.md
        cmforai-file-analyzer /path/to/project **/*.py --exclude tests/ -o context.md
        """
    )
    parser.add_argument(
        'project_path',
        type=str,
        help='Путь к корневой директории проекта'
    )
    parser.add_argument(
        'files',
        nargs='+',
        help='Список файлов для анализа (относительно корня проекта) или шаблоны'
    )
    parser.add_argument(
        '--exclude',
        nargs='*',
        default=[],
        help='Шаблоны файлов для исключения из анализа'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Путь к выходному файлу (по умолчанию: stdout)'
    )
    # Наследуем основные параметры генерации
    parser.add_argument(
        '--no-comments',
        action='store_true',
        help='Удалить комментарии из кода'
    )
    parser.add_argument(
        '--no-instructions',
        action='store_true',
        help='Не включать инструкции для LLM'
    )
    parser.add_argument(
        '--max-tokens',
        type=int,
        default=None,
        help='Максимальное количество токенов'
    )
    return parser

class FileAnalyzer:
    """Анализатор конкретных файлов с сохранением метаинформации проекта"""
    
    def __init__(self, project_path: str, config: Optional[GenerationConfig] = None):
        self.project_path = Path(project_path).resolve()
        self.config = config or GenerationConfig()
        self.analyzer = ProjectAnalyzer(str(self.project_path))
        self.project_info = self.analyzer.analyze()
    
    def analyze_specific_files(self, file_patterns: List[str], exclude_patterns: List[str] = None) -> str:
        """
        Анализирует только указанные файлы, сохраняя метаинформацию проекта
        """
        exclude_patterns = exclude_patterns or []
        
        # Собираем все пути файлов из метаданных проекта
        all_file_paths = {str(f.relative_path): f for f in self.project_info.files}
        
        # Фильтруем файлы по шаблонам
        selected_files = []
        for pattern in file_patterns:
            if '*' in pattern or '?' in pattern:
                # Обработка шаблонов (glob)
                for file_path in all_file_paths.keys():
                    if Path(file_path).match(pattern) and not any(Path(file_path).match(ex) for ex in exclude_patterns):
                        selected_files.append(all_file_paths[file_path])
            else:
                # Точный путь к файлу
                if pattern in all_file_paths and not any(Path(pattern).match(ex) for ex in exclude_patterns):
                    selected_files.append(all_file_paths[pattern])
        
        if not selected_files:
            raise ValueError("Не найдено файлов для анализа по указанным шаблонам")
        
        # Создаем новый ProjectInfo только с выбранными файлами
        from dataclasses import replace
        filtered_project_info = replace(
            self.project_info,
            files=selected_files,
            structure=self._filter_structure(selected_files)
        )
        
        # Генерируем markdown с метаинформацией
        generator = MarkdownGenerator(self.config)
        return generator.generate(filtered_project_info)
    
    def _filter_structure(self, selected_files: List[FileInfo]) -> dict:
        """Фильтрует структуру проекта, оставляя только директории с выбранными файлами"""
        filtered_structure = {}
        for file_info in selected_files:
            dir_path = str(Path(file_info.relative_path).parent)
            if dir_path == '.':
                dir_path = '/'
                
            if dir_path not in filtered_structure:
                filtered_structure[dir_path] = []
            
            filtered_structure[dir_path].append(file_info.relative_path)
        
        return filtered_structure

def main():
    """Основная точка входа"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Валидация пути проекта
    project_path = Path(args.project_path).resolve()
    if not project_path.exists():
        print(f"Ошибка: Путь проекта не существует: {project_path}", file=sys.stderr)
        sys.exit(1)
    
    # Загрузка конфигурации
    config_manager = ConfigManager()
    app_config = config_manager.load()
    
    # Настройка конфигурации генерации
    gen_config = app_config.generation_config
    if args.max_tokens is not None:
        gen_config.max_tokens = args.max_tokens
    if args.no_comments:
        gen_config.include_comments = False
    if args.no_instructions:
        gen_config.add_instructions = False
    
    try:
        # Анализ указанных файлов
        analyzer = FileAnalyzer(str(project_path), gen_config)
        markdown = analyzer.analyze_specific_files(args.files, args.exclude)
        
        # Вывод результата
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
            print(f"Контекст сохранен в: {output_path}", file=sys.stderr)
        else:
            print(markdown)
            
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
