# import json
# import sys
# import urllib.error
# import urllib.request
# from importlib import metadata
# from pathlib import Path
# from typing import Dict, List, Optional, Set


# class PyPIMapper:
#     """
#     Reliable import-name -> PyPI distribution-name resolver.

#     Resolution order:

#     1. Explicit known mappings
#     2. Installed distribution metadata
#     3. Cache
#     4. PyPI candidate verification
#     5. Heuristic fallback

#     The mapper also avoids:
#     - Python standard-library modules
#     - Local project modules
#     - invalid PyPI mappings
#     """

#     KNOWN_MAPPINGS: Dict[str, str] = {
#         # Web / HTTP
#         "requests": "requests",
#         "httpx": "httpx",
#         "aiohttp": "aiohttp",

#         # Testing
#         "pytest": "pytest",
#         "pytest_cov": "pytest-cov",
#         "pytest_asyncio": "pytest-asyncio",
#         "pytest_mock": "pytest-mock",
#         "pytest_xdist": "pytest-xdist",
#         "pytest_html": "pytest-html",
#         "pytest_bdd": "pytest-bdd",
#         "allure": "allure-pytest",
#         "hypothesis": "hypothesis",

#         # HTML / XML
#         "bs4": "beautifulsoup4",
#         "lxml": "lxml",

#         # Images / computer vision
#         "PIL": "Pillow",
#         "pil": "Pillow",
#         "cv2": "opencv-python",
#         "imageio": "imageio",

#         # Data science
#         "numpy": "numpy",
#         "pandas": "pandas",
#         "scipy": "scipy",
#         "sklearn": "scikit-learn",
#         "matplotlib": "matplotlib",
#         "seaborn": "seaborn",

#         # YAML / configuration
#         "yaml": "PyYAML",
#         "dotenv": "python-dotenv",

#         # PDF / documents
#         "fitz": "PyMuPDF",
#         "docx": "python-docx",
#         "pptx": "python-pptx",
#         "openpyxl": "openpyxl",
#         "xlsxwriter": "XlsxWriter",

#         # Google
#         "google.protobuf": "protobuf",
#         "google.auth": "google-auth",
#         "google.cloud": "google-cloud",
#         "google.generativeai": "google-generativeai",
#         "google.genai": "google-genai",

#         # Database
#         "sqlalchemy": "SQLAlchemy",
#         "psycopg2": "psycopg2-binary",
#         "pymysql": "PyMySQL",
#         "redis": "redis",

#         # Security / crypto
#         "crypto": "pycryptodome",
#         "cryptography": "cryptography",
#         "jose": "python-jose",

#         # Serial / hardware
#         "serial": "pyserial",

#         # Selenium / browser automation
#         "selenium": "selenium",
#         "playwright": "playwright",

#         # CLI / utilities
#         "click": "click",
#         "rich": "rich",
#         "requests_html": "requests-html",
#     }

#     # Imports that must never be installed from PyPI.
#     # This list is supplemented automatically by Python's stdlib.
#     IGNORED_IMPORTS: Set[str] = {
#         "__future__",
#         "__main__",
#         "typing_extensions",
#     }

#     # Candidate prefixes/suffixes are intentionally conservative.
#     COMMON_PREFIXES = (
#         "python-",
#     )

#     COMMON_SUFFIXES = (
#         "-python",
#     )

#     def __init__(
#         self,
#         cache_file: Path = Path(".reqpilot_cache.json"),
#         project_root: Optional[Path] = None,
#     ):
#         self.project_root = (
#             project_root.resolve()
#             if project_root
#             else Path.cwd().resolve()
#         )

#         self.cache_file = (
#             cache_file
#             if cache_file.is_absolute()
#             else self.project_root / cache_file
#         )

#         self.cache: Dict[str, str] = self._load_cache()

#         self._stdlib_modules = self._get_stdlib_modules()
#         self._local_modules = self._get_local_modules()
#         self._installed_import_map = self._build_installed_import_map()

#     # ------------------------------------------------------------------
#     # Cache
#     # ------------------------------------------------------------------

#     def _load_cache(self) -> Dict[str, str]:
#         if not self.cache_file.exists():
#             return {}

#         try:
#             with self.cache_file.open("r", encoding="utf-8") as file:
#                 data = json.load(file)

#             if isinstance(data, dict):
#                 return data

#         except (OSError, json.JSONDecodeError):
#             pass

#         return {}

#     def _save_cache(self) -> None:
#         try:
#             self.cache_file.parent.mkdir(
#                 parents=True,
#                 exist_ok=True,
#             )

#             with self.cache_file.open("w", encoding="utf-8") as file:
#                 json.dump(
#                     self.cache,
#                     file,
#                     indent=2,
#                     sort_keys=True,
#                 )

#         except OSError:
#             # Cache failure must never break ReqPilot.
#             pass

#     # ------------------------------------------------------------------
#     # Standard library detection
#     # ------------------------------------------------------------------

#     def _get_stdlib_modules(self) -> Set[str]:
#         """
#         Get Python standard-library module names.

#         This prevents ReqPilot from trying to install things such as:

#             os
#             sys
#             json
#             pathlib
#             typing
#             subprocess
#             urllib
#             unittest
#         """

#         modules = set(sys.stdlib_module_names)

#         return {
#             module.lower()
#             for module in modules
#         }

#     # ------------------------------------------------------------------
#     # Local project detection
#     # ------------------------------------------------------------------

#     def _get_local_modules(self) -> Set[str]:
#         """
#         Detect Python modules/packages belonging to the current project.
#         """

#         modules: Set[str] = set()

#         try:
#             for path in self.project_root.iterdir():

#                 if path.is_file() and path.suffix == ".py":
#                     modules.add(path.stem.lower())

#                 elif path.is_dir():
#                     init_file = path / "__init__.py"

#                     if init_file.exists():
#                         modules.add(path.name.lower())

#         except OSError:
#             pass

#         return modules

#     # ------------------------------------------------------------------
#     # Installed distribution detection
#     # ------------------------------------------------------------------

#     def _build_installed_import_map(self) -> Dict[str, str]:
#         """
#         Build:

#             import_name -> installed distribution

#         using Python package metadata.

#         Example:

#             bs4 -> beautifulsoup4
#             PIL -> Pillow
#             cv2 -> opencv-python
#         """

#         result: Dict[str, str] = {}

#         try:
#             package_map = metadata.packages_distributions()

#             for import_name, distributions in package_map.items():

#                 if not distributions:
#                     continue

#                 # Usually the first distribution is sufficient.
#                 result[import_name.lower()] = distributions[0]

#         except Exception:
#             pass

#         return result

#     # ------------------------------------------------------------------
#     # Helpers
#     # ------------------------------------------------------------------

#     @staticmethod
#     def _normalize_import(import_name: str) -> str:
#         """
#         Normalize an import without destroying useful case information.
#         """

#         return (
#             import_name
#             .strip()
#             .replace("/", ".")
#         )

#     @staticmethod
#     def _root_import(import_name: str) -> str:
#         """
#         Extract root package.

#         Example:

#             selenium.webdriver
#                 -> selenium

#             google.genai
#                 -> google

#             mypackage.utils
#                 -> mypackage
#         """

#         return import_name.split(".", 1)[0]

#     # ------------------------------------------------------------------
#     # Ignore detection
#     # ------------------------------------------------------------------

#     def is_standard_library(self, import_name: str) -> bool:
#         normalized = self._normalize_import(import_name)
#         root = self._root_import(normalized)

#         return (
#             normalized.lower() in self._stdlib_modules
#             or root.lower() in self._stdlib_modules
#         )

#     def is_local_module(self, import_name: str) -> bool:
#         normalized = self._normalize_import(import_name)
#         root = self._root_import(normalized)

#         return (
#             normalized.lower() in self._local_modules
#             or root.lower() in self._local_modules
#         )

#     # ------------------------------------------------------------------
#     # PyPI verification
#     # ------------------------------------------------------------------

#     def _verify_pypi_package(self, package_name: str) -> bool:
#         """
#         Check whether a distribution exists on PyPI.
#         """

#         url = (
#             f"https://pypi.org/pypi/"
#             f"{package_name}/json"
#         )

#         try:
#             request = urllib.request.Request(
#                 url,
#                 headers={
#                     "User-Agent": "ReqPilot/0.1.0"
#                 },
#             )

#             with urllib.request.urlopen(
#                 request,
#                 timeout=3,
#             ):

#                 return True

#         except (
#             urllib.error.HTTPError,
#             urllib.error.URLError,
#             TimeoutError,
#             OSError,
#         ):
#             return False

#     # ------------------------------------------------------------------
#     # Candidate generation
#     # ------------------------------------------------------------------

#     def _generate_candidates(
#         self,
#         import_name: str,
#     ) -> List[str]:

#         normalized = self._normalize_import(import_name)

#         root = self._root_import(normalized)

#         candidates: List[str] = []

#         def add(candidate: str) -> None:
#             candidate = candidate.strip()

#             if not candidate:
#                 return

#             if candidate not in candidates:
#                 candidates.append(candidate)

#         # Exact import name
#         add(root)

#         # underscore -> hyphen
#         add(root.replace("_", "-"))

#         # dot -> hyphen
#         add(normalized.replace(".", "-"))

#         # underscore + dot -> hyphen
#         add(
#             normalized
#             .replace(".", "-")
#             .replace("_", "-")
#         )

#         # Conservative python- prefix
#         for candidate in list(candidates):
#             add(f"python-{candidate}")

#         # Conservative -python suffix
#         for candidate in list(candidates):
#             add(f"{candidate}-python")

#         return candidates

#     # ------------------------------------------------------------------
#     # Main resolver
#     # ------------------------------------------------------------------

#     def map_import_to_pypi(
#         self,
#         import_name: str,
#     ) -> Optional[str]:
#         """
#         Resolve an import name to a PyPI distribution.

#         Returns:
#             PyPI package name
#             None when the dependency should not be installed
#             or cannot be safely resolved.
#         """

#         if not import_name:
#             return None

#         normalized = self._normalize_import(import_name)

#         root = self._root_import(normalized)

#         normalized_lower = normalized.lower()
#         root_lower = root.lower()

#         # --------------------------------------------------------------
#         # 1. Ignore special imports
#         # --------------------------------------------------------------

#         if normalized_lower in self.IGNORED_IMPORTS:
#             return None

#         # --------------------------------------------------------------
#         # 2. Standard library
#         # --------------------------------------------------------------

#         if self.is_standard_library(normalized):
#             return None

#         # --------------------------------------------------------------
#         # 3. Local project module
#         # --------------------------------------------------------------

#         if self.is_local_module(normalized):
#             return None

#         # --------------------------------------------------------------
#         # 4. Explicit mapping
#         # --------------------------------------------------------------

#         # First preserve case-sensitive mappings such as PIL.
#         if normalized in self.KNOWN_MAPPINGS:
#             return self.KNOWN_MAPPINGS[normalized]

#         # Then case-insensitive mapping.
#         mapping_lookup = {
#             key.lower(): value
#             for key, value in self.KNOWN_MAPPINGS.items()
#         }

#         if normalized_lower in mapping_lookup:
#             return mapping_lookup[normalized_lower]

#         if root_lower in mapping_lookup:
#             return mapping_lookup[root_lower]

#         # --------------------------------------------------------------
#         # 5. Installed distribution metadata
#         # --------------------------------------------------------------

#         if normalized_lower in self._installed_import_map:
#             return self._installed_import_map[
#                 normalized_lower
#             ]

#         if root_lower in self._installed_import_map:
#             return self._installed_import_map[
#                 root_lower
#             ]

#         # --------------------------------------------------------------
#         # 6. Cache
#         # --------------------------------------------------------------

#         if normalized_lower in self.cache:

#             cached = self.cache[normalized_lower]

#             if cached:
#                 return cached

#         # --------------------------------------------------------------
#         # 7. PyPI candidates
#         # --------------------------------------------------------------

#         candidates = self._generate_candidates(
#             normalized
#         )

#         for candidate in candidates:

#             if self._verify_pypi_package(candidate):

#                 self.cache[normalized_lower] = candidate
#                 self._save_cache()

#                 return candidate

#         # --------------------------------------------------------------
#         # 8. Do NOT blindly return the import name
#         # --------------------------------------------------------------

#         return None

#     # ------------------------------------------------------------------
#     # Detailed resolution
#     # ------------------------------------------------------------------

#     def resolve(
#         self,
#         import_name: str,
#     ) -> Dict[str, Optional[str]]:

#         package = self.map_import_to_pypi(import_name)

#         if package is None:

#             reason = "unresolved"

#             if self.is_standard_library(import_name):
#                 reason = "standard_library"

#             elif self.is_local_module(import_name):
#                 reason = "local_module"

#             return {
#                 "import": import_name,
#                 "package": None,
#                 "status": reason,
#             }

#         return {
#             "import": import_name,
#             "package": package,
#             "status": "resolved",
#         }
import json
import sys
import urllib.error
import urllib.request
from importlib import metadata
from pathlib import Path
from typing import Dict, List, Optional, Set


class PyPIMapper:
    """
    Reliable import-name -> PyPI distribution-name resolver.

    Resolution order:

    1. Explicit known mappings
    2. Installed distribution metadata
    3. Cache
    4. PyPI candidate verification
    5. Heuristic fallback

    The mapper also avoids:
    - Python standard-library modules
    - Local project modules
    - invalid PyPI mappings
    """

    KNOWN_MAPPINGS: Dict[str, str] = {
        # Web / HTTP
        "requests": "requests",
        "httpx": "httpx",
        "aiohttp": "aiohttp",

        # Testing
        "pytest": "pytest",
        "pytest_cov": "pytest-cov",
        "pytest_asyncio": "pytest-asyncio",
        "pytest_mock": "pytest-mock",
        "pytest_xdist": "pytest-xdist",
        "pytest_html": "pytest-html",
        "pytest_bdd": "pytest-bdd",
        "allure": "allure-pytest",
        "hypothesis": "hypothesis",

        # HTML / XML
        "bs4": "beautifulsoup4",
        "lxml": "lxml",

        # Images / computer vision
        "PIL": "Pillow",
        "pil": "Pillow",
        "cv2": "opencv-python",
        "imageio": "imageio",

        # Data science
        "numpy": "numpy",
        "pandas": "pandas",
        "scipy": "scipy",
        "sklearn": "scikit-learn",
        "matplotlib": "matplotlib",
        "seaborn": "seaborn",

        # YAML / configuration
        "yaml": "PyYAML",
        "dotenv": "python-dotenv",

        # PDF / documents
        "fitz": "PyMuPDF",
        "docx": "python-docx",
        "pptx": "python-pptx",
        "openpyxl": "openpyxl",
        "xlsxwriter": "XlsxWriter",

        # Google
        "google.protobuf": "protobuf",
        "google.auth": "google-auth",
        "google.cloud": "google-cloud",
        "google.generativeai": "google-generativeai",
        "google.genai": "google-genai",

        # Database
        "sqlalchemy": "SQLAlchemy",
        "psycopg2": "psycopg2-binary",
        "pymysql": "PyMySQL",
        "redis": "redis",

        # Security / crypto
        "crypto": "pycryptodome",
        "cryptography": "cryptography",
        "jose": "python-jose",

        # Serial / hardware
        "serial": "pyserial",

        # Selenium / browser automation
        "selenium": "selenium",
        "playwright": "playwright",

        # CLI / utilities
        "click": "click",
        "rich": "rich",
        "requests_html": "requests-html",
    }

    # Imports that must never be installed from PyPI.
    # This list is supplemented automatically by Python's stdlib.
    IGNORED_IMPORTS: Set[str] = {
        "__future__",
        "__main__",
        "typing_extensions",
    }

    # Candidate prefixes/suffixes are intentionally conservative.
    COMMON_PREFIXES = (
        "python-",
    )

    COMMON_SUFFIXES = (
        "-python",
    )

    def __init__(
        self,
        cache_file: Path = Path(".reqpilot_cache.json"),
        project_root: Optional[Path] = None,
    ):
        self.project_root = (
            project_root.resolve()
            if project_root
            else Path.cwd().resolve()
        )

        self.cache_file = (
            cache_file
            if cache_file.is_absolute()
            else self.project_root / cache_file
        )

        self.cache: Dict[str, str] = self._load_cache()

        self._stdlib_modules = self._get_stdlib_modules()
        self._local_modules = self._get_local_modules()
        self._installed_import_map = self._build_installed_import_map()

    # ------------------------------------------------------------------
    # Cache
    # ------------------------------------------------------------------

    def _load_cache(self) -> Dict[str, str]:
        if not self.cache_file.exists():
            return {}

        try:
            with self.cache_file.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, dict):
                return data

        except (OSError, json.JSONDecodeError):
            pass

        return {}

    def _save_cache(self) -> None:
        try:
            self.cache_file.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with self.cache_file.open("w", encoding="utf-8") as file:
                json.dump(
                    self.cache,
                    file,
                    indent=2,
                    sort_keys=True,
                )

        except OSError:
            # Cache failure must never break ReqPilot.
            pass

    # ------------------------------------------------------------------
    # Standard library detection
    # ------------------------------------------------------------------

    def _get_stdlib_modules(self) -> Set[str]:
        """
        Get Python standard-library module names.

        This prevents ReqPilot from trying to install things such as:

            os
            sys
            json
            pathlib
            typing
            subprocess
            urllib
            unittest
        """

        modules = set(sys.stdlib_module_names)

        return {
            module.lower()
            for module in modules
        }

    # ------------------------------------------------------------------
    # Local project detection
    # ------------------------------------------------------------------

    def _get_local_modules(self) -> Set[str]:
        """
        Detect Python modules/packages belonging to the current project.
        """

        modules: Set[str] = set()

        try:
            for path in self.project_root.iterdir():

                if path.is_file() and path.suffix == ".py":
                    modules.add(path.stem.lower())

                elif path.is_dir():
                    init_file = path / "__init__.py"

                    if init_file.exists():
                        modules.add(path.name.lower())

        except OSError:
            pass

        return modules

    # ------------------------------------------------------------------
    # Installed distribution detection
    # ------------------------------------------------------------------

    def _build_installed_import_map(self) -> Dict[str, str]:
        """
        Build:

            import_name -> installed distribution

        using Python package metadata.

        Example:

            bs4 -> beautifulsoup4
            PIL -> Pillow
            cv2 -> opencv-python
        """

        result: Dict[str, str] = {}

        try:
            package_map = metadata.packages_distributions()

            for import_name, distributions in package_map.items():

                if not distributions:
                    continue

                # Usually the first distribution is sufficient.
                result[import_name.lower()] = distributions[0]

        except Exception:
            pass

        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_import(import_name: str) -> str:
        """
        Normalize an import without destroying useful case information.
        """

        return (
            import_name
            .strip()
            .replace("/", ".")
        )

    @staticmethod
    def _root_import(import_name: str) -> str:
        """
        Extract root package.

        Example:

            selenium.webdriver
                -> selenium

            google.genai
                -> google

            mypackage.utils
                -> mypackage
        """

        return import_name.split(".", 1)[0]

    # ------------------------------------------------------------------
    # Ignore detection
    # ------------------------------------------------------------------

    def is_standard_library(self, import_name: str) -> bool:
        normalized = self._normalize_import(import_name)
        root = self._root_import(normalized)

        return (
            normalized.lower() in self._stdlib_modules
            or root.lower() in self._stdlib_modules
        )

    def is_local_module(self, import_name: str) -> bool:
        normalized = self._normalize_import(import_name)
        root = self._root_import(normalized)

        return (
            normalized.lower() in self._local_modules
            or root.lower() in self._local_modules
        )

    # ------------------------------------------------------------------
    # PyPI verification
    # ------------------------------------------------------------------

    def _verify_pypi_package(self, package_name: str) -> bool:
        """
        Check whether a distribution exists on PyPI.
        """

        url = (
            f"https://pypi.org/pypi/"
            f"{package_name}/json"
        )

        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "ReqPilot/0.1.0"
                },
            )

            with urllib.request.urlopen(
                request,
                timeout=3,
            ):

                return True

        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            OSError,
        ):
            return False

    # ------------------------------------------------------------------
    # Candidate generation
    # ------------------------------------------------------------------

    def _generate_candidates(
        self,
        import_name: str,
    ) -> List[str]:

        normalized = self._normalize_import(import_name)

        root = self._root_import(normalized)

        candidates: List[str] = []

        def add(candidate: str) -> None:
            candidate = candidate.strip()

            if not candidate:
                return

            if candidate not in candidates:
                candidates.append(candidate)

        # Exact import name
        add(root)

        # underscore -> hyphen
        add(root.replace("_", "-"))

        # dot -> hyphen
        add(normalized.replace(".", "-"))

        # underscore + dot -> hyphen
        add(
            normalized
            .replace(".", "-")
            .replace("_", "-")
        )

        # Conservative python- prefix
        for candidate in list(candidates):
            add(f"python-{candidate}")

        # Conservative -python suffix
        for candidate in list(candidates):
            add(f"{candidate}-python")

        return candidates

    # ------------------------------------------------------------------
    # Main resolver
    # ------------------------------------------------------------------

    def map_import_to_pypi(
        self,
        import_name: str,
    ) -> Optional[str]:
        """
        Resolve an import name to a PyPI distribution.

        Returns:
            PyPI package name
            None when the dependency should not be installed
            or cannot be safely resolved.
        """

        if not import_name:
            return None

        normalized = self._normalize_import(import_name)

        root = self._root_import(normalized)

        normalized_lower = normalized.lower()
        root_lower = root.lower()

        # --------------------------------------------------------------
        # 1. Ignore special imports
        # --------------------------------------------------------------

        if normalized_lower in self.IGNORED_IMPORTS:
            return None

        # --------------------------------------------------------------
        # 2. Standard library
        # --------------------------------------------------------------

        if self.is_standard_library(normalized):
            return None

        # --------------------------------------------------------------
        # 3. Local project module
        # --------------------------------------------------------------

        if self.is_local_module(normalized):
            return None

        # --------------------------------------------------------------
        # 4. Explicit mapping
        # --------------------------------------------------------------

        # First preserve case-sensitive mappings such as PIL.
        if normalized in self.KNOWN_MAPPINGS:
            return self.KNOWN_MAPPINGS[normalized]

        # Then case-insensitive mapping.
        mapping_lookup = {
            key.lower(): value
            for key, value in self.KNOWN_MAPPINGS.items()
        }

        if normalized_lower in mapping_lookup:
            return mapping_lookup[normalized_lower]

        if root_lower in mapping_lookup:
            return mapping_lookup[root_lower]

        # --------------------------------------------------------------
        # 5. Installed distribution metadata
        # --------------------------------------------------------------

        if normalized_lower in self._installed_import_map:
            return self._installed_import_map[
                normalized_lower
            ]

        if root_lower in self._installed_import_map:
            return self._installed_import_map[
                root_lower
            ]

        # --------------------------------------------------------------
        # 6. Cache
        # --------------------------------------------------------------

        if normalized_lower in self.cache:

            cached = self.cache[normalized_lower]

            if cached:
                return cached

        # --------------------------------------------------------------
        # 7. PyPI candidates
        # --------------------------------------------------------------

        candidates = self._generate_candidates(
            normalized
        )

        for candidate in candidates:

            if self._verify_pypi_package(candidate):

                self.cache[normalized_lower] = candidate
                self._save_cache()

                return candidate

        # --------------------------------------------------------------
        # 8. Do NOT blindly return the import name
        # --------------------------------------------------------------

        return None

    # ------------------------------------------------------------------
    # Detailed resolution
    # ------------------------------------------------------------------

    def resolve(
        self,
        import_name: str,
    ) -> Dict[str, Optional[str]]:

        package = self.map_import_to_pypi(import_name)

        if package is None:

            reason = "unresolved"

            if self.is_standard_library(import_name):
                reason = "standard_library"

            elif self.is_local_module(import_name):
                reason = "local_module"

            return {
                "import": import_name,
                "package": None,
                "status": reason,
            }

        return {
            "import": import_name,
            "package": package,
            "status": "resolved",
        }