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

#     installer = PackageInstaller(project_root=target_path.parent if target_path.is_file() else target_path)
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
        
#         try:
#             subprocess.run([str(python_exec), str(target_path)], check=True)
#         except subprocess.CalledProcessError as e:
#             print(f"\n[TraceReq] Execution failed with exit code {e.returncode}")
#             sys.exit(e.returncode)


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
        description="TraceReq: Auto-detect and install missing Python requirements by analyzing code."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target directory or Python file to analyze (default: current directory)",
    )
    args = parser.parse_args()

    target_path = Path(args.target).resolve()
    analyzer = CodeAnalyzer()

    if target_path.is_file():
        required_imports = analyzer.extract_imports_from_file(target_path)
    elif target_path.is_dir():
        required_imports = analyzer.scan_directory(target_path)
    else:
        print(f"Error: Target path '{target_path}' does not exist.")
        sys.exit(1)

    installer = PackageInstaller(
        project_root=target_path.parent if target_path.is_file() else target_path
    )
    missing = installer.resolve_missing(required_imports)

    if not missing:
        print("[TraceReq] All required dependencies are already installed.")
    else:
        success = installer.install_packages(missing)
        if not success:
            sys.exit(1)

    # Automatically execute the file if target is a single Python script
    if target_path.is_file():
        python_exec = installer.get_target_python()
        print(f"[TraceReq] Running {target_path.name} using {python_exec.name}...\n")

        # Step 1: Run execution and capture output to intercept runtime errors
        process = subprocess.run(
            [str(python_exec), str(target_path)],
            capture_output=True,
            text=True,
        )

        # Print standard output cleanly
        if process.stdout:
            print(process.stdout, end="")

        # Step 2: Intercept execution failures & trigger auto-remediation
        if process.returncode != 0:
            error_output = (process.stderr or "") + (process.stdout or "")
            if process.stderr:
                print(process.stderr, file=sys.stderr, end="")

            # Attempt self-healing repair via post-execution error rules
            remediated = installer.attempt_error_remediation(error_output)

            if remediated:
                print(f"[TraceReq] Retrying execution for {target_path.name}...\n")
                retry_process = subprocess.run([str(python_exec), str(target_path)])
                sys.exit(retry_process.returncode)
            else:
                print(f"\n[TraceReq] Execution failed with exit code {process.returncode}")
                sys.exit(process.returncode)


if __name__ == "__main__":
    main()