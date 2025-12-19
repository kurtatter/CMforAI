# CMforAI
Context Manager for LLMs

> **⚠️ WARNING: PROJECT IS IN EARLY DEVELOPMENT STAGE AND MAY BE ROUGH. USE AT YOUR OWN RISK. ⚠️**
> 
> **⚠️ ВНИМАНИЕ: ПРОЕКТ НАХОДИТСЯ НА НАЧАЛЬНОЙ СТАДИИ РАЗРАБОТКИ И МОЖЕТ БЫТЬ СЫРЫМ. ИСПОЛЬЗУЙТЕ НА СВОЙ РИСК. ⚠️**

![CMforAI](cmforai.png)

A powerful tool to extract and format project context for LLM consumption. Designed to help you quickly share your codebase context with ChatGPT, Qwen, Claude, and other LLMs.

## Features

- 🔍 **Smart Project Analysis**: Automatically analyzes projects (Python, JavaScript/TypeScript, Java, Go, Rust, and more) and identifies important files
- 📝 **Markdown Output**: Generates well-formatted markdown context ready for LLM consumption
- 🎯 **Intelligent Filtering**: Excludes unnecessary files (`.git`, `__pycache__`, `venv`, etc.)
- 📊 **Large Project Support**: Handles very large projects with compression and token limits
- ⚙️ **Flexible Configuration**: Highly configurable with command-line options and config files
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
- pyyaml >= 6.0.1

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

kurtatter

---

# CMforAI
Менеджер контекста для LLM

Мощный инструмент для извлечения и форматирования контекста проекта для использования с большими языковыми моделями. Разработан для быстрого обмена контекстом вашей кодовой базы с ChatGPT, Qwen, Claude и другими LLM.

## Возможности

- 🔍 **Умный анализ проектов**: Автоматически анализирует проекты (Python, JavaScript/TypeScript, Java, Go, Rust и другие) и определяет важные файлы
- 📝 **Вывод в Markdown**: Генерирует хорошо отформатированный markdown-контекст, готовый для использования с LLM
- 🎯 **Интеллектуальная фильтрация**: Исключает ненужные файлы (`.git`, `__pycache__`, `venv` и т.д.)
- 📊 **Поддержка больших проектов**: Работает с очень большими проектами благодаря сжатию и ограничению токенов
- ⚙️ **Гибкая настройка**: Настраивается через параметры командной строки и конфигурационные файлы
- 🚀 **Быстро и эффективно**: Оптимизирован для больших кодовых баз

## Установка

```bash
# Клонируйте репозиторий
git clone https://github.com/yourusername/CMforAI.git
cd CMforAI

# Установите пакет
pip install -e .

# Или установите зависимости напрямую
pip install -r requirements.txt
```

## Использование

### Интерфейс командной строки

Базовое использование:
```bash
cmforai /путь/к/вашему/проекту
```

Сохранение в файл:
```bash
cmforai /путь/к/вашему/проекту -o output.md
```

С ограничением токенов:
```bash
cmforai /путь/к/вашему/проекту --max-tokens 50000 -o context.md
```

Ограничение количества файлов:
```bash
cmforai /путь/к/вашему/проекту --max-files 100 -o context.md
```

Пользовательские шаблоны игнорирования:
```bash
cmforai /путь/к/вашему/проекту --ignore ".*\.log$" --ignore "test_.*"
```

### Параметры конфигурации

#### Параметры командной строки

- `-o, --output`: Путь к выходному файлу (по умолчанию: stdout)
- `--max-tokens`: Максимальное приблизительное количество токенов
- `--max-files`: Максимальное количество файлов для включения
- `--max-file-size`: Максимальный размер файла в байтах
- `--max-lines-per-file`: Максимальное количество строк на файл
- `--compress-threshold`: Сжимать файлы размером больше N строк (по умолчанию: 200)
- `--no-compress`: Отключить сжатие больших файлов
- `--no-comments`: Удалить комментарии из кода
- `--no-structure`: Не включать дерево структуры проекта
- `--no-dependencies`: Не включать секцию зависимостей
- `--no-metadata`: Не включать секцию метаданных
- `--no-instructions`: Не включать заголовок с инструкциями для LLM
- `--ignore`: Дополнительные шаблоны игнорирования (regex, можно использовать несколько раз)
- `--important`: Дополнительные имена важных файлов (можно использовать несколько раз)

#### Конфигурационный файл

Создайте файл `.cmforai.json` в корне вашего проекта или в `~/.config/cmforai/.cmforai.json`:

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

## Как это работает

1. **Анализ**: Сканирует директорию проекта, идентифицирует файлы и извлекает метаданные
2. **Фильтрация**: Применяет шаблоны игнорирования и расставляет приоритеты важных файлов
3. **Отбор**: Выбирает файлы на основе конфигурации (лимиты токенов, лимиты файлов и т.д.)
4. **Сжатие**: Сжимает большие файлы путем извлечения структуры и ключевых компонентов
5. **Генерация**: Форматирует все в markdown-документ с:
   - Метаданными проекта
   - Деревом структуры директорий
   - Списком зависимостей
   - Содержимым файлов с подсветкой синтаксиса

## Формат вывода

Сгенерированный markdown включает:

- **Заголовок**: Инструкции для LLM
- **Метаданные**: Информация о проекте (размер, количество файлов, версия Python и т.д.)
- **Структура**: Древовидное представление директорий проекта
- **Зависимости**: Список зависимостей проекта
- **Содержимое файлов**: Все выбранные файлы с блоками кода

## Примеры

### Небольшой проект
```bash
cmforai ./my-project -o context.md
```

### Большой проект с ограничениями
```bash
cmforai ./large-project --max-tokens 100000 --max-files 200 -o context.md
```

### Фокус только на важных файлах
```bash
cmforai ./project --max-files 50 --no-compress -o important.md
```

## Требования

- Python 3.8+
- pyyaml >= 6.0.1

## Лицензия

MIT License - см. файл LICENSE для подробностей

## Вклад в проект

Мы приветствуем вклад в проект! Не стесняйтесь отправлять Pull Request.

## Автор

kurtatter
