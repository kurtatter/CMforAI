"""
Graphical user interface for CMforAI using customtkinter.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import customtkinter as ctk
from pathlib import Path
import threading
from typing import Optional
from .analyzer import ProjectAnalyzer
from .generator import MarkdownGenerator, GenerationConfig
from .config import ConfigManager, AppConfig


class CMforAIGUI:
    """Main GUI application class."""
    
    def __init__(self):
        """Initialize the GUI application."""
        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("CMforAI - Context Manager for LLMs")
        self.root.geometry("1000x700")
        
        # Configuration
        self.config_manager = ConfigManager()
        self.app_config = self.config_manager.load()
        self.project_path: Optional[Path] = None
        self.project_info = None
        
        # Create UI
        self._create_widgets()
        
    def _create_widgets(self):
        """Create and layout all widgets."""
        # Main container
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top section - Project selection
        top_frame = ctk.CTkFrame(main_frame)
        top_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(top_frame, text="Project Path:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=5)
        
        self.path_entry = ctk.CTkEntry(top_frame, width=500)
        self.path_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        ctk.CTkButton(top_frame, text="Browse", command=self._browse_project, width=100).pack(side="left", padx=5)
        ctk.CTkButton(top_frame, text="Analyze", command=self._analyze_project, width=100).pack(side="left", padx=5)
        
        # Middle section - Configuration
        config_frame = ctk.CTkFrame(main_frame)
        config_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left side - Settings
        left_config = ctk.CTkFrame(config_frame)
        left_config.pack(side="left", fill="both", expand=True, padx=5)
        
        ctk.CTkLabel(left_config, text="Generation Settings", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=5)
        
        # Max tokens
        tokens_frame = ctk.CTkFrame(left_config)
        tokens_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(tokens_frame, text="Max Tokens:").pack(side="left", padx=5)
        self.max_tokens_var = ctk.StringVar(value="")
        ctk.CTkEntry(tokens_frame, textvariable=self.max_tokens_var, width=150).pack(side="left", padx=5)
        
        # Max files
        files_frame = ctk.CTkFrame(left_config)
        files_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(files_frame, text="Max Files:").pack(side="left", padx=5)
        self.max_files_var = ctk.StringVar(value="")
        ctk.CTkEntry(files_frame, textvariable=self.max_files_var, width=150).pack(side="left", padx=5)
        
        # Max file size
        size_frame = ctk.CTkFrame(left_config)
        size_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(size_frame, text="Max File Size (bytes):").pack(side="left", padx=5)
        self.max_file_size_var = ctk.StringVar(value="")
        ctk.CTkEntry(size_frame, textvariable=self.max_file_size_var, width=150).pack(side="left", padx=5)
        
        # Max lines per file
        lines_frame = ctk.CTkFrame(left_config)
        lines_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(lines_frame, text="Max Lines/File:").pack(side="left", padx=5)
        self.max_lines_var = ctk.StringVar(value="")
        ctk.CTkEntry(lines_frame, textvariable=self.max_lines_var, width=150).pack(side="left", padx=5)
        
        # Compress threshold
        compress_frame = ctk.CTkFrame(left_config)
        compress_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(compress_frame, text="Compress Threshold:").pack(side="left", padx=5)
        self.compress_threshold_var = ctk.StringVar(value="200")
        ctk.CTkEntry(compress_frame, textvariable=self.compress_threshold_var, width=150).pack(side="left", padx=5)
        
        # Checkboxes
        self.compress_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(left_config, text="Compress large files", variable=self.compress_var).pack(anchor="w", pady=2)
        
        self.comments_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(left_config, text="Include comments", variable=self.comments_var).pack(anchor="w", pady=2)
        
        self.structure_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(left_config, text="Include structure", variable=self.structure_var).pack(anchor="w", pady=2)
        
        self.dependencies_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(left_config, text="Include dependencies", variable=self.dependencies_var).pack(anchor="w", pady=2)
        
        self.metadata_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(left_config, text="Include metadata", variable=self.metadata_var).pack(anchor="w", pady=2)
        
        self.instructions_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(left_config, text="Include instructions", variable=self.instructions_var).pack(anchor="w", pady=2)
        
        # Right side - Project info
        right_config = ctk.CTkFrame(config_frame)
        right_config.pack(side="right", fill="both", expand=True, padx=5)
        
        ctk.CTkLabel(right_config, text="Project Information", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=5)
        
        self.info_text = ctk.CTkTextbox(right_config, height=200)
        self.info_text.pack(fill="both", expand=True, pady=5)
        
        # Bottom section - Actions and output
        bottom_frame = ctk.CTkFrame(main_frame)
        bottom_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Buttons
        button_frame = ctk.CTkFrame(bottom_frame)
        button_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(button_frame, text="Generate Context", command=self._generate_context, width=150).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Save to File", command=self._save_to_file, width=150).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Copy to Clipboard", command=self._copy_to_clipboard, width=150).pack(side="left", padx=5)
        
        # Output text area
        ctk.CTkLabel(bottom_frame, text="Generated Context (Markdown):", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=5)
        
        self.output_text = ctk.CTkTextbox(bottom_frame)
        self.output_text.pack(fill="both", expand=True, pady=5)
        
        # Status bar
        self.status_label = ctk.CTkLabel(main_frame, text="Ready", anchor="w")
        self.status_label.pack(fill="x", padx=10, pady=5)
        
        # Load default values
        self._load_config_to_ui()
    
    def _load_config_to_ui(self):
        """Load configuration values into UI."""
        config = self.app_config.generation_config
        
        if config.max_tokens:
            self.max_tokens_var.set(str(config.max_tokens))
        if config.max_files:
            self.max_files_var.set(str(config.max_files))
        if config.max_file_size:
            self.max_file_size_var.set(str(config.max_file_size))
        if config.max_lines_per_file:
            self.max_lines_var.set(str(config.max_lines_per_file))
        
        self.compress_threshold_var.set(str(config.compress_threshold_lines))
        self.compress_var.set(config.compress_large_files)
        self.comments_var.set(config.include_comments)
        self.structure_var.set(config.include_structure)
        self.dependencies_var.set(config.include_dependencies)
        self.metadata_var.set(config.include_metadata)
        self.instructions_var.set(config.add_instructions)
    
    def _browse_project(self):
        """Open file dialog to select project directory."""
        path = filedialog.askdirectory(title="Select Project Directory")
        if path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)
            self.project_path = Path(path)
    
    def _analyze_project(self):
        """Analyze the selected project."""
        path_str = self.path_entry.get().strip()
        if not path_str:
            messagebox.showerror("Error", "Please select a project directory")
            return
        
        project_path = Path(path_str)
        if not project_path.exists():
            messagebox.showerror("Error", f"Path does not exist: {project_path}")
            return
        
        if not project_path.is_dir():
            messagebox.showerror("Error", f"Path is not a directory: {project_path}")
            return
        
        self.project_path = project_path
        self.status_label.configure(text="Analyzing project...")
        
        # Run analysis in thread to avoid freezing UI
        def analyze_thread():
            try:
                analyzer = ProjectAnalyzer(
                    str(project_path),
                    ignore_patterns=self.app_config.custom_ignore_patterns or None,
                    custom_important_files=set(self.app_config.custom_important_files) if self.app_config.custom_important_files else None
                )
                self.project_info = analyzer.analyze()
                
                # Update UI in main thread
                self.root.after(0, self._update_project_info)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Analysis failed: {e}"))
                self.root.after(0, lambda: self.status_label.configure(text="Analysis failed"))
        
        threading.Thread(target=analyze_thread, daemon=True).start()
    
    def _update_project_info(self):
        """Update project information display."""
        if not self.project_info:
            return
        
        info_lines = [
            f"Project: {self.project_info.root.name}",
            f"Total Files: {len(self.project_info.files)}",
            f"Root: {self.project_info.root}",
        ]
        
        if self.project_info.python_version:
            info_lines.append(f"Python Version: {self.project_info.python_version}")
        
        if self.project_info.description:
            info_lines.append(f"Description: {self.project_info.description[:100]}...")
        
        if self.project_info.dependencies:
            info_lines.append(f"Dependencies: {len(self.project_info.dependencies)}")
        
        # Count by language
        lang_counts = {}
        for file_info in self.project_info.files:
            lang_counts[file_info.language] = lang_counts.get(file_info.language, 0) + 1
        
        info_lines.append("\nFiles by Language:")
        for lang, count in sorted(lang_counts.items(), key=lambda x: x[1], reverse=True):
            info_lines.append(f"  {lang}: {count}")
        
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", "\n".join(info_lines))
        self.status_label.configure(text=f"Analysis complete: {len(self.project_info.files)} files found")
    
    def _get_generation_config(self) -> GenerationConfig:
        """Get generation configuration from UI."""
        config = GenerationConfig()
        
        # Parse numeric values
        try:
            if self.max_tokens_var.get().strip():
                config.max_tokens = int(self.max_tokens_var.get())
        except ValueError:
            pass
        
        try:
            if self.max_files_var.get().strip():
                config.max_files = int(self.max_files_var.get())
        except ValueError:
            pass
        
        try:
            if self.max_file_size_var.get().strip():
                config.max_file_size = int(self.max_file_size_var.get())
        except ValueError:
            pass
        
        try:
            if self.max_lines_var.get().strip():
                config.max_lines_per_file = int(self.max_lines_var.get())
        except ValueError:
            pass
        
        try:
            config.compress_threshold_lines = int(self.compress_threshold_var.get())
        except ValueError:
            config.compress_threshold_lines = 200
        
        config.compress_large_files = self.compress_var.get()
        config.include_comments = self.comments_var.get()
        config.include_structure = self.structure_var.get()
        config.include_dependencies = self.dependencies_var.get()
        config.include_metadata = self.metadata_var.get()
        config.add_instructions = self.instructions_var.get()
        
        return config
    
    def _generate_context(self):
        """Generate markdown context."""
        if not self.project_info:
            messagebox.showwarning("Warning", "Please analyze a project first")
            return
        
        self.status_label.configure(text="Generating context...")
        
        def generate_thread():
            try:
                config = self._get_generation_config()
                generator = MarkdownGenerator(config)
                markdown = generator.generate(self.project_info)
                
                # Update UI in main thread
                self.root.after(0, lambda: self._display_context(markdown))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Generation failed: {e}"))
                self.root.after(0, lambda: self.status_label.configure(text="Generation failed"))
        
        threading.Thread(target=generate_thread, daemon=True).start()
    
    def _display_context(self, markdown: str):
        """Display generated context in output area."""
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", markdown)
        self.status_label.configure(text=f"Context generated ({len(markdown)} characters)")
    
    def _save_to_file(self):
        """Save generated context to file."""
        content = self.output_text.get("1.0", tk.END)
        if not content.strip():
            messagebox.showwarning("Warning", "No context generated. Please generate context first.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Context saved to:\n{file_path}")
                self.status_label.configure(text=f"Saved to: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")
    
    def _copy_to_clipboard(self):
        """Copy generated context to clipboard."""
        content = self.output_text.get("1.0", tk.END)
        if not content.strip():
            messagebox.showwarning("Warning", "No context generated. Please generate context first.")
            return
        
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        messagebox.showinfo("Success", "Context copied to clipboard!")
        self.status_label.configure(text="Context copied to clipboard")
    
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


def main():
    """Main GUI entry point."""
    app = CMforAIGUI()
    app.run()


if __name__ == '__main__':
    main()

