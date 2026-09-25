import ast
import os
import sys
from pathlib import Path
from typing import Iterable, Optional, Set, Tuple


class CodeAnalyzer:
    """Analyze Python imports, including dependencies hidden behind local modules."""

    PROJECT_MARKERS = (
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "pytest.ini",
        "tox.ini",
        ".git",
    )

    SKIP_DIR_NAMES = {
        ".git",
        ".hg",
        ".svn",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "build",
        "dist",
        "node_modules",
    }

    def __init__(self, project_root: Optional[Path] = None):
        self.stdlib_modules: Set[str] = set(sys.stdlib_module_names)
        self.project_root = Path(project_root).resolve() if project_root else None

    @classmethod
    def discover_project_root(cls, target: Path) -> Path:
        """Return the nearest ancestor that looks like the project root."""
        target = Path(target).resolve()
        start = target.parent if target.is_file() else target

        for candidate in (start, *start.parents):
            if any((candidate / marker).exists() for marker in cls.PROJECT_MARKERS):
                return candidate
        return start

    def _ensure_project_root(self, target: Path) -> Path:
        if self.project_root is None:
            self.project_root = self.discover_project_root(target)
        return self.project_root

    @staticmethod
    def _looks_like_venv(path: Path) -> bool:
        """Detect a virtual environment by structure, not by directory name."""
        if not path.is_dir():
            return False
        if (path / "pyvenv.cfg").is_file():
            return True
        return (
            (path / "Scripts" / "python.exe").is_file()
            or (path / "bin" / "python").is_file()
        ) and (
            (path / "Lib" / "site-packages").is_dir()
            or (path / "lib").is_dir()
        )

    def _source_roots(self, current_file: Optional[Path] = None) -> Tuple[Path, ...]:
        root = self.project_root or (current_file.parent if current_file else Path.cwd())
        roots = []
        for candidate in (
            current_file.parent if current_file else None,
            root,
            root / "src",
        ):
            if candidate and candidate.is_dir() and candidate not in roots:
                roots.append(candidate)
        return tuple(roots)

    @staticmethod
    def _module_candidates(base: Path, module_name: str) -> Iterable[Path]:
        if not module_name:
            return ()
        module_path = base.joinpath(*module_name.split("."))
        return (
            module_path.with_suffix(".py"),
            module_path / "__init__.py",
        )

    def _resolve_local_module(
        self,
        module_name: str,
        current_file: Path,
        level: int = 0,
    ) -> Optional[Path]:
        """Resolve an import to a local .py file/package if one exists."""
        candidates = []

        if level > 0:
            # from .x => current package; from ..x => parent package, etc.
            base = current_file.parent
            for _ in range(level - 1):
                base = base.parent
            candidates.extend(self._module_candidates(base, module_name))
        else:
            for root in self._source_roots(current_file):
                candidates.extend(self._module_candidates(root, module_name))

        for candidate in candidates:
            try:
                resolved = candidate.resolve()
            except OSError:
                continue
            if resolved.is_file() and self._is_inside_project(resolved):
                return resolved
        return None

    def _is_inside_project(self, path: Path) -> bool:
        root = self.project_root
        if root is None:
            return True
        try:
            path.resolve().relative_to(root.resolve())
            return True
        except ValueError:
            return False

    @staticmethod
    def _parse_tree(file_path: Path) -> Optional[ast.AST]:
        try:
            text = file_path.read_text(encoding="utf-8")
            return ast.parse(text, filename=str(file_path))
        except (OSError, SyntaxError, UnicodeDecodeError):
            return None

    def _analyze_file_imports(self, file_path: Path) -> Tuple[Set[str], Set[Path]]:
        """Return (external top-level imports, directly referenced local files)."""
        tree = self._parse_tree(file_path)
        if tree is None:
            return set(), set()

        external: Set[str] = set()
        local_files: Set[Path] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_name = alias.name.split(".", 1)[0]
                    if root_name in self.stdlib_modules:
                        continue
                    local = self._resolve_local_module(alias.name, file_path)
                    if local:
                        local_files.add(local)
                    else:
                        # Try the root package too, useful for package imports.
                        local_root = self._resolve_local_module(root_name, file_path)
                        if local_root:
                            local_files.add(local_root)
                        else:
                            external.add(root_name)

            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                root_name = module_name.split(".", 1)[0] if module_name else ""

                if node.level == 0 and root_name in self.stdlib_modules:
                    continue

                base_local = self._resolve_local_module(
                    module_name,
                    file_path,
                    level=node.level,
                ) if module_name else None

                found_local = False
                if base_local:
                    local_files.add(base_local)
                    found_local = True

                # `from package import submodule` can hide another local file.
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    child_name = f"{module_name}.{alias.name}" if module_name else alias.name
                    child_local = self._resolve_local_module(
                        child_name,
                        file_path,
                        level=node.level,
                    )
                    if child_local:
                        local_files.add(child_local)
                        found_local = True

                if not found_local and node.level == 0 and root_name:
                    external.add(root_name)

        return external, local_files

    def analyze_entrypoint(self, file_path: Path) -> Set[str]:
        """
        Recursively follow local imports starting at file_path and return only
        third-party imports required by the reachable dependency graph.
        """
        file_path = Path(file_path).resolve()
        self._ensure_project_root(file_path)

        required: Set[str] = set()
        visited: Set[Path] = set()
        pending = [file_path]

        while pending:
            current = pending.pop()
            if current in visited or not current.is_file():
                continue
            visited.add(current)

            external, local_files = self._analyze_file_imports(current)
            required.update(external)

            for local_file in local_files:
                if local_file not in visited:
                    pending.append(local_file)

        return required

    def extract_imports_from_file(self, file_path: Path) -> Set[str]:
        """
        Backward-compatible API. It now follows local dependencies recursively,
        which is the desired behavior for framework-based projects.
        """
        return self.analyze_entrypoint(file_path)

    def scan_directory(self, target_dir: Path) -> Set[str]:
        """Scan a project while pruning caches, build output, and any venv name."""
        target_dir = Path(target_dir).resolve()
        self._ensure_project_root(target_dir)
        all_imports: Set[str] = set()

        for current_root, dir_names, file_names in os.walk(target_dir):
            current_path = Path(current_root)

            kept_dirs = []
            for name in dir_names:
                directory = current_path / name
                if name in self.SKIP_DIR_NAMES:
                    continue
                if self._looks_like_venv(directory):
                    continue
                kept_dirs.append(name)
            dir_names[:] = kept_dirs

            for name in file_names:
                if not name.endswith(".py"):
                    continue
                all_imports.update(self.analyze_entrypoint(current_path / name))

        return all_imports