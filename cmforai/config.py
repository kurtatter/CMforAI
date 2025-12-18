"""
Configuration management module.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from .generator import GenerationConfig


@dataclass
class AppConfig:
    """Application configuration."""
    generation_config: GenerationConfig
    custom_ignore_patterns: List[str]
    custom_important_files: List[str]
    
    @classmethod
    def default(cls) -> 'AppConfig':
        """Create default configuration."""
        return cls(
            generation_config=GenerationConfig(),
            custom_ignore_patterns=[],
            custom_important_files=[]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'generation_config': asdict(self.generation_config),
            'custom_ignore_patterns': self.custom_ignore_patterns,
            'custom_important_files': self.custom_important_files
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """Create from dictionary."""
        gen_config_data = data.get('generation_config', {})
        gen_config = GenerationConfig(**gen_config_data)
        return cls(
            generation_config=gen_config,
            custom_ignore_patterns=data.get('custom_ignore_patterns', []),
            custom_important_files=data.get('custom_important_files', [])
        )


class ConfigManager:
    """Manages configuration files."""
    
    CONFIG_FILENAME = '.cmforai.json'
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize config manager."""
        if config_dir is None:
            config_dir = Path.home() / '.config' / 'cmforai'
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.config_dir / self.CONFIG_FILENAME
    
    def load(self) -> AppConfig:
        """Load configuration from file."""
        if not self.config_path.exists():
            return AppConfig.default()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return AppConfig.from_dict(data)
        except Exception:
            return AppConfig.default()
    
    def save(self, config: AppConfig) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise ValueError(f"Failed to save config: {e}")
    
    def load_project_config(self, project_root: Path) -> Optional[AppConfig]:
        """Load project-specific configuration."""
        project_config_path = project_root / self.CONFIG_FILENAME
        if not project_config_path.exists():
            return None
        
        try:
            with open(project_config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return AppConfig.from_dict(data)
        except Exception:
            return None

