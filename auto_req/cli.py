# import argparse
# import subprocess
# import sys
# from pathlib import Path
# from auto_req.analyzer import CodeAnalyzer
# from auto_req.installer import PackageInstaller


# def main():
#     parser = argparse.ArgumentParser(
#         description="TraceReq: Auto-detect and install missing Python requirements by analyzing code."
#     )
#     parser.add_argument(
#         "target",
#         nargs="?",
#         default=".",
#         help="Target directory or Python file to analyze (default: current directory)",
#     )
#     args = parser.parse_args()

#     target_path = Path(args.target).resolve()
#     analyzer = CodeAnalyzer()

#     if target_path.is_file():
#         required_imports = analyzer.extract_imports_from_file(target_path)
#     elif target_path.is_dir():
#         required_imports = analyzer.scan_directory(target_path)
#     else:
#         print(f"Error: Target path '{target_path}' does not exist.")
#         sys.exit(1)

#     installer = PackageInstaller(
#         project_root=target_path.parent if target_path.is_file() else target_path
#     )
#     missing = installer.resolve_missing(required_imports)

#     if not missing:
#         print("[TraceReq] All required dependencies are already installed.")
#     else:
#         success = installer.install_packages(missing)
#         if not success:
#             sys.exit(1)

#     # Automatically execute the file if target is a single Python script
#     if target_path.is_file():
#         python_exec = installer.get_target_python()
#         print(f"[TraceReq] Running {target_path.name} using {python_exec.name}...\n")

#         # Step 1: Run execution and capture output to intercept runtime errors
#         process = subprocess.run(
#             [str(python_exec), str(target_path)],
#             capture_output=True,
#             text=True,
#         )

#         # Print standard output cleanly
#         if process.stdout:
#             print(process.stdout, end="")

#         # Step 2: Intercept execution failures & trigger auto-remediation
#         if process.returncode != 0:
#             error_output = (process.stderr or "") + (process.stdout or "")
#             if process.stderr:
#                 print(process.stderr, file=sys.stderr, end="")

#             # Attempt self-healing repair via post-execution error rules
#             remediated = installer.attempt_error_remediation(error_output)

#             if remediated:
#                 print(f"[TraceReq] Retrying execution for {target_path.name}...\n")
#                 retry_process = subprocess.run([str(python_exec), str(target_path)])
#                 sys.exit(retry_process.returncode)
#             else:
#                 print(f"\n[TraceReq] Execution failed with exit code {process.returncode}")
#                 sys.exit(process.returncode)


# if __name__ == "__main__":
#     main()

import argparse
import subprocess
import sys
from pathlib import Path

from auto_req.analyzer import CodeAnalyzer
from auto_req.installer import PackageInstaller


def main():
    parser = argparse.ArgumentParser(
        description="TraceReq: discover runtime dependencies recursively and install missing packages."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Python entry file or project directory (default: current directory)",
    )
    args = parser.parse_args()

    target_path = Path(args.target).resolve()
    if not target_path.exists():
        print(f"Error: Target path '{target_path}' does not exist.")
        sys.exit(1)

    project_root = CodeAnalyzer.discover_project_root(target_path)
    analyzer = CodeAnalyzer(project_root=project_root)

    if target_path.is_file():
        if target_path.suffix != ".py":
            print(f"Error: '{target_path}' is not a Python file.")
            sys.exit(1)
        print(f"[TraceReq] Analyzing dependency graph from: {target_path.name}")
        required_imports = analyzer.analyze_entrypoint(target_path)
    else:
        print(f"[TraceReq] Scanning project: {target_path}")
        required_imports = analyzer.scan_directory(target_path)

    if required_imports:
        print(f"[TraceReq] Third-party imports detected: {', '.join(sorted(required_imports))}")
    else:
        print("[TraceReq] No third-party imports detected.")

    installer = PackageInstaller(project_root=project_root)
    missing = installer.resolve_missing(required_imports)

    if not missing:
        print("[TraceReq] All required dependencies are already installed.")
    elif not installer.install_packages(missing):
        sys.exit(1)

    if target_path.is_file():
        python_exec = installer.get_target_python()
        print(f"[TraceReq] Running {target_path.name} using {python_exec}...\n")

        process = subprocess.run(
            [str(python_exec), str(target_path)],
            cwd=str(target_path.parent),
            capture_output=True,
            text=True,
        )

        if process.stdout:
            print(process.stdout, end="")

        if process.returncode != 0:
            error_output = (process.stderr or "") + (process.stdout or "")
            if process.stderr:
                print(process.stderr, file=sys.stderr, end="")

            if installer.attempt_error_remediation(error_output):
                print(f"[TraceReq] Retrying execution for {target_path.name}...\n")
                retry = subprocess.run(
                    [str(python_exec), str(target_path)],
                    cwd=str(target_path.parent),
                )
                sys.exit(retry.returncode)

            print(f"\n[TraceReq] Execution failed with exit code {process.returncode}")
            sys.exit(process.returncode)


if __name__ == "__main__":
    main()