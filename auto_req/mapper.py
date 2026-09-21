import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict


class PyPIMapper:
    """Maps import names to PyPI package names with static overrides and PyPI API fallback."""

    # Well-known import-to-PyPI mismatches
    KNOWN_MAPPINGS: Dict[str, str] = {
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

    def map_import_to_pypi(self, import_name: str) -> str:
        """Resolves an import name to a PyPI package name."""
        # 1. Check known mappings override
        if import_name in self.KNOWN_MAPPINGS:
            return self.KNOWN_MAPPINGS[import_name]

        # 2. Check local disk cache
        if import_name in self.cache:
            return self.cache[import_name]

        # 3. Query PyPI JSON API to confirm package existence
        pypi_name = import_name
        url = f"https://pypi.org/pypi/{import_name}/json"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "auto-req"})
            with urllib.request.urlopen(req, timeout=2):
                pypi_name = import_name
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Common fallback heuristic: underscore to dash
                pypi_name = import_name.replace("_", "-")

        # Update cache
        self.cache[import_name] = pypi_name
        self._save_cache()
        return pypi_name