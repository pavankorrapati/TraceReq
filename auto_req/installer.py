# import importlib.metadata
# import os
# import subprocess
# import sys
# from pathlib import Path
# from typing import List, Optional, Set
# from auto_req.mapper import PyPIMapper


# class PackageInstaller:
#     """Detects missing dependencies and installs them into a project's local virtual environment."""

#     COMMON_VENV_NAMES = [".venv", "venv", "env", ".env", "virtualenv"]

#     def __init__(self, project_root: Optional[Path] = None):
#         self.mapper = PyPIMapper()
#         self.stdlib_modules = set(sys.stdlib_module_names)
#         self.project_root = Path(project_root or Path.cwd()).resolve()
#         self.venv_path = self._detect_virtual_env()

#     def _detect_virtual_env(self) -> Optional[Path]:
#         """Dynamically locates any virtual environment directory inside or around the project root."""
#         # 1. Check if VIRTUAL_ENV variable is set in the environment
#         if "VIRTUAL_ENV" in os.environ:
#             active_env = Path(os.environ["VIRTUAL_ENV"])
#             if self._is_valid_venv(active_env):
#                 return active_env

#         # 2. Check if the currently running Python runtime itself is a venv
#         if sys.prefix != sys.base_prefix:
#             active_sys_venv = Path(sys.prefix)
#             if self._is_valid_venv(active_sys_venv):
#                 return active_sys_venv

#         # 3. Check common venv folder names inside project_root
#         for name in self.COMMON_VENV_NAMES:
#             candidate = self.project_root / name
#             if self._is_valid_venv(candidate):
#                 return candidate

#         # 4. Check parent directory if project_root is inside a nested package
#         for name in self.COMMON_VENV_NAMES:
#             candidate = self.project_root.parent / name
#             if self._is_valid_venv(candidate):
#                 return candidate

#         # 5. Fallback: Scan root directory for any subfolder containing a valid python executable
#         try:
#             for item in self.project_root.iterdir():
#                 if item.is_dir() and item.name not in self.COMMON_VENV_NAMES:
#                     if self._is_valid_venv(item):
#                         return item
#         except PermissionError:
#             pass

#         return None

#     def _is_valid_venv(self, path: Path) -> bool:
#         """Checks if a directory contains a valid virtual environment Python binary."""
#         if os.name == "nt":  # Windows
#             py_exec = path / "Scripts" / "python.exe"
#         else:  # macOS / Linux
#             py_exec = path / "bin" / "python"
#         return py_exec.exists()

#     def get_target_python(self) -> Path:
#         """Returns the Python binary path of the detected venv, or system Python fallback."""
#         if self.venv_path:
#             if os.name == "nt":
#                 py_exec = self.venv_path / "Scripts" / "python.exe"
#             else:
#                 py_exec = self.venv_path / "bin" / "python"

#             if py_exec.exists():
#                 return py_exec

#         return Path(sys.executable)

#     def get_installed_packages(self) -> Set[str]:
#         """Returns normalized names of installed packages in the target venv/environment."""
#         search_paths = []

#         if self.venv_path:
#             if os.name == "nt":
#                 venv_site = self.venv_path / "Lib" / "site-packages"
#             else:
#                 venv_site = (
#                     self.venv_path
#                     / "lib"
#                     / f"python{sys.version_info.major}.{sys.version_info.minor}"
#                     / "site-packages"
#                 )
#             if venv_site.exists():
#                 search_paths = [str(venv_site)]

#         installed = set()

#         # Query site-packages of the target venv directly if present
#         dists = (
#             importlib.metadata.distributions(path=search_paths)
#             if search_paths
#             else importlib.metadata.distributions()
#         )

#         for dist in dists:
#             name = dist.metadata.get("Name")
#             if name:
#                 installed.add(name.lower().replace("_", "-"))
#         return installed

#     def resolve_missing(self, required_imports: Set[str]) -> List[str]:
#         """Identifies imports that are not installed in the target environment."""
#         installed = self.get_installed_packages()
#         missing_pypi_packages = []

#         # Strip standard library imports first
#         third_party_imports = required_imports - self.stdlib_modules

#         for imp in third_party_imports:
#             pypi_name = self.mapper.map_import_to_pypi(imp)
#             normalized_pypi = pypi_name.lower().replace("_", "-")

#             if normalized_pypi not in installed:
#                 missing_pypi_packages.append(pypi_name)

#         return missing_pypi_packages

#     def install_packages(self, packages: List[str]) -> bool:
#         """Executes pip install targeting the detected virtual environment."""
#         if not packages:
#             return True

#         python_exec = self.get_target_python()

#         if self.venv_path:
#             print(f"\n[TraceReq] Target Virtual Environment Found: {self.venv_path.name}")
#         else:
#             print("\n[TraceReq] No local venv found. Target: Global Environment")

#         print(f"[TraceReq] Target Python: {python_exec}")
#         print(f"[TraceReq] Installing dependencies: {', '.join(packages)}...")

#         cmd = [str(python_exec), "-m", "pip", "install", *packages]
#         result = subprocess.run(cmd)

#         if result.returncode == 0:
#             print("[TraceReq] Installation completed successfully!\n")
#             return True

#         print("[TraceReq] Error occurred during pip installation.\n")
#         return False

# import importlib.metadata
# import os
# import subprocess
# import sys
# from pathlib import Path
# from typing import List, Optional, Set
# from auto_req.mapper import PyPIMapper


# class PackageInstaller:
#     """Detects missing dependencies and installs them into a project's local virtual environment."""

#     COMMON_VENV_NAMES = [".venv", "venv", "env", ".env", "virtualenv"]

#     # Special packages that require additional setup commands after pip install
#     POST_INSTALL_HOOKS = {
#         "playwright": ["-m", "playwright", "install"]
#     }

#     def __init__(self, project_root: Optional[Path] = None):
#         self.mapper = PyPIMapper()
#         self.stdlib_modules = set(sys.stdlib_module_names)
#         self.project_root = Path(project_root or Path.cwd()).resolve()
#         self.venv_path = self._detect_virtual_env()

#     def _detect_virtual_env(self) -> Optional[Path]:
#         """Dynamically locates any virtual environment directory inside or around the project root."""
#         if "VIRTUAL_ENV" in os.environ:
#             active_env = Path(os.environ["VIRTUAL_ENV"])
#             if self._is_valid_venv(active_env):
#                 return active_env

#         if sys.prefix != sys.base_prefix:
#             active_sys_venv = Path(sys.prefix)
#             if self._is_valid_venv(active_sys_venv):
#                 return active_sys_venv

#         for name in self.COMMON_VENV_NAMES:
#             candidate = self.project_root / name
#             if self._is_valid_venv(candidate):
#                 return candidate

#         for name in self.COMMON_VENV_NAMES:
#             candidate = self.project_root.parent / name
#             if self._is_valid_venv(candidate):
#                 return candidate

#         try:
#             for item in self.project_root.iterdir():
#                 if item.is_dir() and item.name not in self.COMMON_VENV_NAMES:
#                     if self._is_valid_venv(item):
#                         return item
#         except PermissionError:
#             pass

#         return None

#     def _is_valid_venv(self, path: Path) -> bool:
#         """Checks if a directory contains a valid virtual environment Python binary."""
#         if os.name == "nt":
#             py_exec = path / "Scripts" / "python.exe"
#         else:
#             py_exec = path / "bin" / "python"
#         return py_exec.exists()

#     def get_target_python(self) -> Path:
#         """Returns the Python binary path of the detected venv, or system Python fallback."""
#         if self.venv_path:
#             if os.name == "nt":
#                 py_exec = self.venv_path / "Scripts" / "python.exe"
#             else:
#                 py_exec = self.venv_path / "bin" / "python"

#             if py_exec.exists():
#                 return py_exec

#         return Path(sys.executable)

#     def get_installed_packages(self) -> Set[str]:
#         """Returns normalized names of installed packages in the target venv/environment."""
#         search_paths = []

#         if self.venv_path:
#             if os.name == "nt":
#                 venv_site = self.venv_path / "Lib" / "site-packages"
#             else:
#                 venv_site = (
#                     self.venv_path
#                     / "lib"
#                     / f"python{sys.version_info.major}.{sys.version_info.minor}"
#                     / "site-packages"
#                 )
#             if venv_site.exists():
#                 search_paths = [str(venv_site)]

#         installed = set()
#         dists = (
#             importlib.metadata.distributions(path=search_paths)
#             if search_paths
#             else importlib.metadata.distributions()
#         )

#         for dist in dists:
#             name = dist.metadata.get("Name")
#             if name:
#                 installed.add(name.lower().replace("_", "-"))
#         return installed

#     def resolve_missing(self, required_imports: Set[str]) -> List[str]:
#         """Identifies imports that are not installed in the target environment."""
#         installed = self.get_installed_packages()
#         missing_pypi_packages = []

#         third_party_imports = required_imports - self.stdlib_modules

#         for imp in third_party_imports:
#             pypi_name = self.mapper.map_import_to_pypi(imp)
#             normalized_pypi = pypi_name.lower().replace("_", "-")

#             if normalized_pypi not in installed:
#                 missing_pypi_packages.append(pypi_name)

#         return missing_pypi_packages

#     def run_post_install_hooks(self, installed_packages: List[str], python_exec: Path):
#         """Runs additional commands required by specific packages after pip install."""
#         for pkg in installed_packages:
#             normalized_pkg = pkg.lower().replace("_", "-")
#             if normalized_pkg in self.POST_INSTALL_HOOKS:
#                 hook_args = self.POST_INSTALL_HOOKS[normalized_pkg]
#                 cmd = [str(python_exec), *hook_args]
#                 print(f"[TraceReq] Running post-installation setup for '{pkg}': {' '.join(cmd)}")
#                 subprocess.run(cmd, check=False)

#     def install_packages(self, packages: List[str]) -> bool:
#         """Executes pip install targeting the detected virtual environment and triggers post-install hooks."""
#         if not packages:
#             return True

#         python_exec = self.get_target_python()

#         if self.venv_path:
#             print(f"\n[TraceReq] Target Virtual Environment Found: {self.venv_path.name}")
#         else:
#             print("\n[TraceReq] No local venv found. Target: Global Environment")

#         print(f"[TraceReq] Target Python: {python_exec}")
#         print(f"[TraceReq] Installing dependencies: {', '.join(packages)}...")

#         cmd = [str(python_exec), "-m", "pip", "install", *packages]
#         result = subprocess.run(cmd)

#         if result.returncode == 0:
#             print("[TraceReq] Installation completed successfully!")
#             # Run post-install hooks (e.g., downloading Playwright browser binaries)
#             self.run_post_install_hooks(packages, python_exec)
#             print()
#             return True

#         print("[TraceReq] Error occurred during pip installation.\n")
#         return False

import importlib.metadata
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Set
from auto_req.mapper import PyPIMapper


class PackageInstaller:
    """Detects missing dependencies and installs them into a project's local virtual environment."""

    COMMON_VENV_NAMES = [".venv", "venv", "env", ".env", "virtualenv"]

    # Special packages requiring additional commands after initial pip install
    POST_INSTALL_HOOKS = {
        "playwright": ["-m", "playwright", "install","chromium"]
    }

    # Regex patterns mapped to repair actions when execution fails
    ERROR_REMEDIATION_RULES = [
        {
            "pattern": r"Executable doesn't exist at .*ms-playwright",
            "description": "Missing Playwright browser binaries",
            "args": ["-m", "playwright", "install"],
        },
        {
            "pattern": r"playwright install",
            "description": "Playwright post-install requirement detected",
            "args": ["-m", "playwright", "install"],
        },
        {
            "pattern": r"spacy\.util\.load_model.*Can't find model",
            "description": "Missing spaCy language model",
            "args": ["-m", "spacy", "download", "en_core_web_sm"],
        },
        {
            "pattern": r"Resource .* not found\. Please use the NLTK Downloader",
            "description": "Missing NLTK data package",
            "args": ["-c", "import nltk; nltk.download('all')"],
        },
    ]

    def __init__(self, project_root: Optional[Path] = None):
        self.mapper = PyPIMapper()
        self.stdlib_modules = set(sys.stdlib_module_names)
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.venv_path = self._detect_virtual_env()

    def _detect_virtual_env(self) -> Optional[Path]:
        """Dynamically locates any virtual environment directory inside or around the project root."""
        if "VIRTUAL_ENV" in os.environ:
            active_env = Path(os.environ["VIRTUAL_ENV"])
            if self._is_valid_venv(active_env):
                return active_env

        if sys.prefix != sys.base_prefix:
            active_sys_venv = Path(sys.prefix)
            if self._is_valid_venv(active_sys_venv):
                return active_sys_venv

        for name in self.COMMON_VENV_NAMES:
            candidate = self.project_root / name
            if self._is_valid_venv(candidate):
                return candidate

        for name in self.COMMON_VENV_NAMES:
            candidate = self.project_root.parent / name
            if self._is_valid_venv(candidate):
                return candidate

        try:
            for item in self.project_root.iterdir():
                if item.is_dir() and item.name not in self.COMMON_VENV_NAMES:
                    if self._is_valid_venv(item):
                        return item
        except PermissionError:
            pass

        return None

    def _is_valid_venv(self, path: Path) -> bool:
        """Checks if a directory contains a valid virtual environment Python binary."""
        if os.name == "nt":  # Windows
            py_exec = path / "Scripts" / "python.exe"
        else:  # macOS / Linux
            py_exec = path / "bin" / "python"
        return py_exec.exists()

    def get_target_python(self) -> Path:
        """Returns the Python binary path of the detected venv, or system Python fallback."""
        if self.venv_path:
            if os.name == "nt":
                py_exec = self.venv_path / "Scripts" / "python.exe"
            else:
                py_exec = self.venv_path / "bin" / "python"

            if py_exec.exists():
                return py_exec

        return Path(sys.executable)

    def get_installed_packages(self) -> Set[str]:
        """Returns normalized names of installed packages in the target venv/environment."""
        search_paths = []

        if self.venv_path:
            if os.name == "nt":
                venv_site = self.venv_path / "Lib" / "site-packages"
            else:
                venv_site = (
                    self.venv_path
                    / "lib"
                    / f"python{sys.version_info.major}.{sys.version_info.minor}"
                    / "site-packages"
                )
            if venv_site.exists():
                search_paths = [str(venv_site)]

        installed = set()
        dists = (
            importlib.metadata.distributions(path=search_paths)
            if search_paths
            else importlib.metadata.distributions()
        )

        for dist in dists:
            name = dist.metadata.get("Name")
            if name:
                installed.add(name.lower().replace("_", "-"))
        return installed

    # def resolve_missing(self, required_imports: Set[str]) -> List[str]:
    #     """Identifies imports that are not installed in the target environment."""
    #     installed = self.get_installed_packages()
    #     missing_pypi_packages = []

    #     third_party_imports = required_imports - self.stdlib_modules

    #     for imp in third_party_imports:
    #         pypi_name = self.mapper.map_import_to_pypi(imp)
    #         normalized_pypi = pypi_name.lower().replace("_", "-")

    #         if normalized_pypi not in installed:
    #             missing_pypi_packages.append(pypi_name)

    #     return missing_pypi_packages
    def resolve_missing(self, required_imports: Set[str]) -> List[str]:
        """Identifies imports that are not installed in the target environment."""
        installed = self.get_installed_packages()
        missing_pypi_packages = []

        # 1. Ignore Python built-in standard library modules (os, sys, math, etc.)
        third_party_imports = required_imports - self.stdlib_modules

        # 2. Ignore Local Project Modules/Folders (e.g., auto_req, utils, tests)
        external_imports = set()
        for imp in third_party_imports:
            local_folder = self.project_root / imp
            local_file = self.project_root / f"{imp}.py"
            
            # If the folder or file exists locally in your project, skip it!
            if local_folder.exists() or local_file.exists():
                continue
                
            external_imports.add(imp)

        # 3. Only attempt to download actual third-party packages from PyPI
        for imp in external_imports:
            pypi_name = self.mapper.map_import_to_pypi(imp)
            normalized_pypi = pypi_name.lower().replace("_", "-")

            if normalized_pypi not in installed:
                missing_pypi_packages.append(pypi_name)

        return missing_pypi_packages

    def run_post_install_hooks(self, installed_packages: List[str], python_exec: Path):
        """Runs additional setup commands required by specific packages after pip install."""
        for pkg in installed_packages:
            normalized_pkg = pkg.lower().replace("_", "-")
            if normalized_pkg in self.POST_INSTALL_HOOKS:
                hook_args = self.POST_INSTALL_HOOKS[normalized_pkg]
                cmd = [str(python_exec), *hook_args]
                print(f"[TraceReq] Running post-installation setup for '{pkg}': {' '.join(cmd)}")
                subprocess.run(cmd, check=False)

    def install_packages(self, packages: List[str]) -> bool:
        """Executes pip install targeting the detected virtual environment and triggers post-install hooks."""
        if not packages:
            return True

        python_exec = self.get_target_python()

        if self.venv_path:
            print(f"\n[TraceReq] Target Virtual Environment Found: {self.venv_path.name}")
        else:
            print("\n[TraceReq] No local venv found. Target: Global Environment")

        print(f"[TraceReq] Target Python: {python_exec}")
        print(f"[TraceReq] Installing dependencies: {', '.join(packages)}...")

        cmd = [str(python_exec), "-m", "pip", "install", *packages]
        result = subprocess.run(cmd)

        if result.returncode == 0:
            print("[TraceReq] Installation completed successfully!")
            self.run_post_install_hooks(packages, python_exec)
            print()
            return True

        print("[TraceReq] Error occurred during pip installation.\n")
        return False

    def attempt_error_remediation(self, error_output: str) -> bool:
        """Parses stdout/stderr tracebacks for known dependency errors and attempts repair."""
        python_exec = self.get_target_python()

        for rule in self.ERROR_REMEDIATION_RULES:
            if re.search(rule["pattern"], error_output, re.IGNORECASE):
                print(f"\n[TraceReq] Detected execution error: {rule['description']}")
                cmd = [str(python_exec), *rule["args"]]
                print(f"[TraceReq] Auto-remediating: {' '.join(cmd)}")

                result = subprocess.run(cmd)
                if result.returncode == 0:
                    print("[TraceReq] Auto-remediation succeeded!\n")
                    return True

                print("[TraceReq] Auto-remediation failed.\n")
                return False

        return False