# from pathlib import Path
# from auto_req.analyzer import CodeAnalyzer
# from auto_req.installer import PackageInstaller


# def pytest_addoption(parser):
#     """Add CLI flags to PyTest."""
#     group = parser.getgroup("auto-req")
#     group.addoption(
#         "--no-auto-req",
#         action="store_true",
#         default=False,
#         help="Disable automatic requirement analysis and installation.",
#     )


# def pytest_configure(config):
#     """PyTest hook that runs early during test session setup."""
#     if config.getoption("--no-auto-req", default=False):
#         return

#     root_dir = Path(config.rootdir)
    
#     # 1. Scan codebase and test files
#     analyzer = CodeAnalyzer()
#     required_imports = analyzer.scan_directory(root_dir)

#     # 2. Resolve missing and auto-install
#     installer = PackageInstaller()
#     missing = installer.resolve_missing(required_imports)

#     if missing:
#         installer.install_packages(missing)
from pathlib import Path

from auto_req.analyzer import CodeAnalyzer
from auto_req.installer import PackageInstaller


def pytest_addoption(parser):
    group = parser.getgroup("auto-req")
    group.addoption(
        "--no-auto-req",
        action="store_true",
        default=False,
        help="Disable automatic dependency analysis and installation.",
    )


def pytest_configure(config):
    if config.getoption("--no-auto-req", default=False):
        return

    root_dir = Path(str(config.rootpath)).resolve()
    analyzer = CodeAnalyzer(project_root=root_dir)
    required_imports = analyzer.scan_directory(root_dir)

    installer = PackageInstaller(project_root=root_dir)
    missing = installer.resolve_missing(required_imports)
    if missing:
        installer.install_packages(missing)