# import json
# import urllib.request
# import urllib.error
# from pathlib import Path
# from typing import Dict


# class PyPIMapper:
#     """Maps import names to PyPI package names with static overrides and PyPI API fallback."""

#     # Well-known import-to-PyPI mismatches
#     KNOWN_MAPPINGS: Dict[str, str] = {
#         "bs4": "beautifulsoup4",
#         "PIL": "Pillow",
#         "cv2": "opencv-python",
#         "yaml": "PyYAML",
#         "sklearn": "scikit-learn",
#         "fitz": "PyMuPDF",
#         "docx": "python-docx",
#         "pptx": "python-pptx",
#         "google/protobuf": "protobuf",
#         "crypto": "pycryptodome",
#         "serial": "pyserial",
#         "jose": "python-jose",
#     }

#     def __init__(self, cache_file: Path = Path(".auto_req_cache.json")):
#         self.cache_file = cache_file
#         self.cache: Dict[str, str] = self._load_cache()

#     def _load_cache(self) -> Dict[str, str]:
#         if self.cache_file.exists():
#             try:
#                 with open(self.cache_file, "r", encoding="utf-8") as f:
#                     return json.load(f)
#             except Exception:
#                 return {}
#         return {}

#     def _save_cache(self):
#         try:
#             with open(self.cache_file, "w", encoding="utf-8") as f:
#                 json.dump(self.cache, f, indent=2)
#         except Exception:
#             pass

#     def map_import_to_pypi(self, import_name: str) -> str:
#         """Resolves an import name to a PyPI package name."""
#         # 1. Check known mappings override
#         if import_name in self.KNOWN_MAPPINGS:
#             return self.KNOWN_MAPPINGS[import_name]

#         # 2. Check local disk cache
#         if import_name in self.cache:
#             return self.cache[import_name]

#         # 3. Query PyPI JSON API to confirm package existence
#         pypi_name = import_name
#         url = f"https://pypi.org/pypi/{import_name}/json"
#         try:
#             req = urllib.request.Request(url, headers={"User-Agent": "auto-req"})
#             with urllib.request.urlopen(req, timeout=2):
#                 pypi_name = import_name
#         except urllib.error.HTTPError as e:
#             if e.code == 404:
#                 # Common fallback heuristic: underscore to dash
#                 pypi_name = import_name.replace("_", "-")

#         # Update cache
#         self.cache[import_name] = pypi_name
#         self._save_cache()
#         return pypi_name


import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Optional


class PyPIMapper:
    """Dynamically resolves import names to PyPI package names using heuristics,

    well-known mappings, and PyPI API checks.
    """

    # Primary overrides where import name and PyPI package name completely diverge
    KNOWN_MAPPINGS: Dict[str, str] = {
        "allure": "allure-pytest",
        "bs4": "beautifulsoup4",
        "PIL": "Pillow",
        "cv2": "opencv-python",
        "yaml": "PyYAML",
        "sklearn": "scikit-learn",
        "fitz": "PyMuPDF",
        "docx": "python-docx",
        "pptx": "python-pptx",
        "google/protobuf": "protobuf",
        "crypto": "pycryptodome",
        "serial": "pyserial",
        "jose": "python-jose",
    }

    def __init__(self, cache_file: Path = Path(".auto_req_cache.json")):
        self.cache_file = cache_file
        self.cache: Dict[str, str] = self._load_cache()

    def _load_cache(self) -> Dict[str, str]:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2)
        except Exception:
            pass

    def _verify_pypi_package(self, package_name: str) -> bool:
        """Queries PyPI JSON API to check if a package name exists."""
        url = f"https://pypi.org/pypi/{package_name}/json"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TraceReq"})
            with urllib.request.urlopen(req, timeout=3):
                return True
        except (urllib.error.HTTPError, urllib.error.URLError, Exception):
            return False

    def map_import_to_pypi(self, import_name: str) -> str:
        """Resolves an import name to a PyPI package name dynamically."""
        clean_import = import_name.lower().strip()

        # 1. Check known static overrides
        if clean_import in self.KNOWN_MAPPINGS:
            return self.KNOWN_MAPPINGS[clean_import]

        # 2. Check local disk cache
        if clean_import in self.cache:
            return self.cache[clean_import]

        # 3. Dynamic candidate resolution heuristics
        candidates = [
            clean_import,                           # Exact match (e.g., requests -> requests)
            clean_import.replace("_", "-"),         # Underscore to dash (e.g., pytest_cov -> pytest-cov)
            f"pytest-{clean_import}",               # Pytest plugin naming convention
            f"python-{clean_import.replace('_', '-')}",  # Common prefix (e.g., python-dotenv)
            f"{clean_import.replace('_', '-')}-python",  # Common suffix
        ]

        # 4. Probe candidates against PyPI API
        resolved_pypi_name = clean_import
        for candidate in candidates:
            if self._verify_pypi_package(candidate):
                resolved_pypi_name = candidate
                break

        # 5. Persist resolved candidate to cache
        self.cache[clean_import] = resolved_pypi_name
        self._save_cache()
        return resolved_pypi_name