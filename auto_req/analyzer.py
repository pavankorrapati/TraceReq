import ast
import sys
from pathlib import Path
from typing import Set


class CodeAnalyzer:
    """Analyzes Python code to extract top-level third-party imported modules."""

    def __init__(self):
        # Retrieve all standard library modules for the current Python runtime
        self.stdlib_modules: Set[str] = set(sys.stdlib_module_names)

    def extract_imports_from_file(self, file_path: Path) -> Set[str]:
        """Parses a single .py file and returns non-stdlib top-level import names."""
        if not file_path.is_file() or file_path.suffix != ".py":
            return set()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return set()

        modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Capture top-level package (e.g., 'os.path' -> 'os')
                    modules.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                # Ensure it's an absolute import (level == 0)
                if node.module and node.level == 0:
                    modules.add(node.module.split(".")[0])

        # Exclude standard library modules
        return modules - self.stdlib_modules

    def scan_directory(self, target_dir: Path) -> Set[str]:
        """Recursively scans a directory for Python files and aggregates imports."""
        all_imports = set()
        for py_file in target_dir.rglob("*.py"):
            # Ignore virtual environment directories
            if any(part.startswith((".", "venv", "env")) for part in py_file.parts):
                continue
            all_imports.update(self.extract_imports_from_file(py_file))
        return all_imports