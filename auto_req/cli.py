# # import argparse
# # import subprocess
# # import sys
# # from pathlib import Path
# # from auto_req.analyzer import CodeAnalyzer
# # from auto_req.installer import PackageInstaller


# # def main():
# #     parser = argparse.ArgumentParser(
# #         description="TraceReq: Auto-detect and install missing Python requirements by analyzing code."
# #     )
# #     parser.add_argument(
# #         "target",
# #         nargs="?",
# #         default=".",
# #         help="Target directory or Python file to analyze (default: current directory)",
# #     )
# #     args = parser.parse_args()

# #     target_path = Path(args.target).resolve()
# #     analyzer = CodeAnalyzer()

# #     if target_path.is_file():
# #         required_imports = analyzer.extract_imports_from_file(target_path)
# #     elif target_path.is_dir():
# #         required_imports = analyzer.scan_directory(target_path)
# #     else:
# #         print(f"Error: Target path '{target_path}' does not exist.")
# #         sys.exit(1)

# #     installer = PackageInstaller(
# #         project_root=target_path.parent if target_path.is_file() else target_path
# #     )
# #     missing = installer.resolve_missing(required_imports)

# #     if not missing:
# #         print("[TraceReq] All required dependencies are already installed.")
# #     else:
# #         success = installer.install_packages(missing)
# #         if not success:
# #             sys.exit(1)

# #     # Automatically execute the file if target is a single Python script
# #     if target_path.is_file():
# #         python_exec = installer.get_target_python()
# #         print(f"[TraceReq] Running {target_path.name} using {python_exec.name}...\n")

# #         # Step 1: Run execution and capture output to intercept runtime errors
# #         process = subprocess.run(
# #             [str(python_exec), str(target_path)],
# #             capture_output=True,
# #             text=True,
# #         )

# #         # Print standard output cleanly
# #         if process.stdout:
# #             print(process.stdout, end="")

# #         # Step 2: Intercept execution failures & trigger auto-remediation
# #         if process.returncode != 0:
# #             error_output = (process.stderr or "") + (process.stdout or "")
# #             if process.stderr:
# #                 print(process.stderr, file=sys.stderr, end="")

# #             # Attempt self-healing repair via post-execution error rules
# #             remediated = installer.attempt_error_remediation(error_output)

# #             if remediated:
# #                 print(f"[TraceReq] Retrying execution for {target_path.name}...\n")
# #                 retry_process = subprocess.run([str(python_exec), str(target_path)])
# #                 sys.exit(retry_process.returncode)
# #             else:
# #                 print(f"\n[TraceReq] Execution failed with exit code {process.returncode}")
# #                 sys.exit(process.returncode)


# # if __name__ == "__main__":
# #     main()

# import argparse
# import subprocess
# import sys
# from pathlib import Path

# from auto_req.analyzer import CodeAnalyzer
# from auto_req.installer import PackageInstaller


# def main():
#     parser = argparse.ArgumentParser(
#         description="TraceReq: discover runtime dependencies recursively and install missing packages."
#     )
#     parser.add_argument(
#         "target",
#         nargs="?",
#         default=".",
#         help="Python entry file or project directory (default: current directory)",
#     )
#     args = parser.parse_args()

#     target_path = Path(args.target).resolve()
#     if not target_path.exists():
#         print(f"Error: Target path '{target_path}' does not exist.")
#         sys.exit(1)

#     project_root = CodeAnalyzer.discover_project_root(target_path)
#     analyzer = CodeAnalyzer(project_root=project_root)

#     if target_path.is_file():
#         if target_path.suffix != ".py":
#             print(f"Error: '{target_path}' is not a Python file.")
#             sys.exit(1)
#         print(f"[TraceReq] Analyzing dependency graph from: {target_path.name}")
#         required_imports = analyzer.analyze_entrypoint(target_path)
#     else:
#         print(f"[TraceReq] Scanning project: {target_path}")
#         required_imports = analyzer.scan_directory(target_path)

#     if required_imports:
#         print(f"[TraceReq] Third-party imports detected: {', '.join(sorted(required_imports))}")
#     else:
#         print("[TraceReq] No third-party imports detected.")

#     installer = PackageInstaller(project_root=project_root)
#     missing = installer.resolve_missing(required_imports)

#     if not missing:
#         print("[TraceReq] All required dependencies are already installed.")
#     elif not installer.install_packages(missing):
#         sys.exit(1)

#     if target_path.is_file():
#         python_exec = installer.get_target_python()
#         print(f"[TraceReq] Running {target_path.name} using {python_exec}...\n")

#         process = subprocess.run(
#             [str(python_exec), str(target_path)],
#             cwd=str(target_path.parent),
#             capture_output=True,
#             text=True,
#         )

#         if process.stdout:
#             print(process.stdout, end="")

#         if process.returncode != 0:
#             error_output = (process.stderr or "") + (process.stdout or "")
#             if process.stderr:
#                 print(process.stderr, file=sys.stderr, end="")

#             if installer.attempt_error_remediation(error_output):
#                 print(f"[TraceReq] Retrying execution for {target_path.name}...\n")
#                 retry = subprocess.run(
#                     [str(python_exec), str(target_path)],
#                     cwd=str(target_path.parent),
#                 )
#                 sys.exit(retry.returncode)

#             print(f"\n[TraceReq] Execution failed with exit code {process.returncode}")
#             sys.exit(process.returncode)


# if __name__ == "__main__":
#     main()

# import argparse
# import os
# import subprocess
# import sys
# from pathlib import Path

# from auto_req.analyzer import CodeAnalyzer
# from auto_req.installer import PackageInstaller


# def build_execution_command(
#     target_path: Path,
#     python_exec: Path,
#     project_root: Path,
# ) -> list[str]:
#     """
#     Build the correct command for executing the target.

#     Pytest test files are executed through:
#         python -m pytest ...

#     Normal Python files are executed directly:
#         python file.py
#     """

#     relative_target = target_path.relative_to(project_root)

#     # Detect pytest-style test files.
#     is_pytest_test = (
#         target_path.name.startswith("test_")
#         or target_path.name.endswith("_test.py")
#     )

#     if is_pytest_test:
#         return [
#             str(python_exec),
#             "-m",
#             "pytest",
#             str(relative_target),
#             "-v",
#             "-s",
#         ]

#     return [
#         str(python_exec),
#         str(relative_target),
#     ]


# def build_execution_environment(
#     project_root: Path,
# ) -> dict[str, str]:
#     """
#     Build the subprocess environment.

#     The project root is added to PYTHONPATH so local packages such as
#     'app' can be imported regardless of where the target file is located.
#     """

#     environment = os.environ.copy()

#     project_root_string = str(project_root)

#     existing_pythonpath = environment.get("PYTHONPATH")

#     if existing_pythonpath:
#         environment["PYTHONPATH"] = (
#             project_root_string
#             + os.pathsep
#             + existing_pythonpath
#         )
#     else:
#         environment["PYTHONPATH"] = project_root_string

#     return environment


# def run_target(
#     target_path: Path,
#     python_exec: Path,
#     project_root: Path,
# ):
#     """
#     Execute the requested target from the project root.
#     """

#     command = build_execution_command(
#         target_path=target_path,
#         python_exec=python_exec,
#         project_root=project_root,
#     )

#     environment = build_execution_environment(project_root)

#     print(
#         "[TraceReq] Execution command:\n"
#         f"  {' '.join(command)}"
#     )

#     print(
#         f"[TraceReq] Working directory:\n"
#         f"  {project_root}\n"
#     )

#     return subprocess.run(
#         command,
#         cwd=str(project_root),
#         env=environment,
#         capture_output=True,
#         text=True,
#     )


# def main():
#     parser = argparse.ArgumentParser(
#         description=(
#             "TraceReq: discover runtime dependencies recursively "
#             "and install missing packages."
#         )
#     )

#     parser.add_argument(
#         "target",
#         nargs="?",
#         default=".",
#         help=(
#             "Python entry file or project directory "
#             "(default: current directory)"
#         ),
#     )

#     args = parser.parse_args()

#     target_path = Path(args.target).resolve()

#     if not target_path.exists():
#         print(
#             f"Error: Target path '{target_path}' does not exist."
#         )
#         sys.exit(1)

#     # ---------------------------------------------------------
#     # Discover project root
#     # ---------------------------------------------------------
#     project_root = CodeAnalyzer.discover_project_root(
#         target_path
#     )

#     print(
#         f"[TraceReq] Project root: {project_root}"
#     )

#     analyzer = CodeAnalyzer(
#         project_root=project_root
#     )

#     # ---------------------------------------------------------
#     # Analyze dependencies
#     # ---------------------------------------------------------
#     if target_path.is_file():

#         if target_path.suffix != ".py":
#             print(
#                 f"Error: '{target_path}' is not a Python file."
#             )
#             sys.exit(1)

#         print(
#             "[TraceReq] Analyzing dependency graph from: "
#             f"{target_path.name}"
#         )

#         required_imports = analyzer.analyze_entrypoint(
#             target_path
#         )

#     else:

#         print(
#             f"[TraceReq] Scanning project: {target_path}"
#         )

#         required_imports = analyzer.scan_directory(
#             target_path
#         )

#     # ---------------------------------------------------------
#     # Display detected dependencies
#     # ---------------------------------------------------------
#     if required_imports:
#         print(
#             "[TraceReq] Third-party imports detected: "
#             + ", ".join(sorted(required_imports))
#         )
#     else:
#         print(
#             "[TraceReq] No third-party imports detected."
#         )

#     # ---------------------------------------------------------
#     # Resolve/install dependencies
#     # ---------------------------------------------------------
#     installer = PackageInstaller(
#         project_root=project_root
#     )

#     missing = installer.resolve_missing(
#         required_imports
#     )

#     if not missing:

#         print(
#             "[TraceReq] All required dependencies "
#             "are already installed."
#         )

#     elif not installer.install_packages(missing):

#         sys.exit(1)

#     # ---------------------------------------------------------
#     # Execute a single Python file
#     # ---------------------------------------------------------
#     if target_path.is_file():

#         python_exec = installer.get_target_python()

#         is_pytest_test = (
#             target_path.name.startswith("test_")
#             or target_path.name.endswith("_test.py")
#         )

#         if is_pytest_test:
#             execution_type = "pytest test"
#         else:
#             execution_type = "Python script"

#         print(
#             f"[TraceReq] Running {execution_type} "
#             f"{target_path.name} using {python_exec}...\n"
#         )

#         process = run_target(
#             target_path=target_path,
#             python_exec=python_exec,
#             project_root=project_root,
#         )

#         # -----------------------------------------------------
#         # Print standard output
#         # -----------------------------------------------------
#         if process.stdout:
#             print(
#                 process.stdout,
#                 end="",
#             )

#         # -----------------------------------------------------
#         # Handle execution failure
#         # -----------------------------------------------------
#         if process.returncode != 0:

#             error_output = (
#                 (process.stderr or "")
#                 + (process.stdout or "")
#             )

#             if process.stderr:
#                 print(
#                     process.stderr,
#                     file=sys.stderr,
#                     end="",
#                 )

#             # -------------------------------------------------
#             # Attempt automatic remediation
#             # -------------------------------------------------
#             remediated = (
#                 installer.attempt_error_remediation(
#                     error_output
#                 )
#             )

#             if remediated:

#                 print(
#                     "[TraceReq] Retrying execution for "
#                     f"{target_path.name}...\n"
#                 )

#                 retry = run_target(
#                     target_path=target_path,
#                     python_exec=python_exec,
#                     project_root=project_root,
#                 )

#                 if retry.stdout:
#                     print(
#                         retry.stdout,
#                         end="",
#                     )

#                 if retry.stderr:
#                     print(
#                         retry.stderr,
#                         file=sys.stderr,
#                         end="",
#                     )

#                 sys.exit(
#                     retry.returncode
#                 )

#             print(
#                 "\n[TraceReq] Execution failed with "
#                 f"exit code {process.returncode}"
#             )

#             sys.exit(
#                 process.returncode
#             )


# if __name__ == "__main__":
#     main()


import argparse
import os
import subprocess
import sys
from pathlib import Path

from auto_req.analyzer import CodeAnalyzer
from auto_req.installer import PackageInstaller


# ============================================================
# Test discovery configuration
# ============================================================

TEST_FILE_PATTERNS = (
    "test_*.py",
    "*_test.py",
)

IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "env",
    ".env",
    "__pycache__",
    ".pytest_cache",
    "build",
    "dist",
}


# ============================================================
# Test detection
# ============================================================

def is_pytest_test_file(
    path: Path,
) -> bool:
    """
    Return True when the file follows a pytest test-file naming
    convention.

    Supported patterns:

        test_*.py
        *_test.py
    """

    if not path.is_file():
        return False

    if path.suffix.lower() != ".py":
        return False

    return (
        path.name.startswith("test_")
        or path.name.endswith("_test.py")
    )


# ============================================================
# Recursive test discovery
# ============================================================

def discover_test_files(
    target_path: Path,
) -> list[Path]:
    """
    Recursively discover pytest test files.

    If target_path is a file:
        return the file when it is a pytest test file.

    If target_path is a directory:
        recursively search for:

            test_*.py
            *_test.py

    Virtual environments, caches, build directories, and Git
    metadata are ignored.
    """

    # --------------------------------------------------------
    # Single file
    # --------------------------------------------------------

    if target_path.is_file():

        if is_pytest_test_file(target_path):
            return [target_path]

        return []

    # --------------------------------------------------------
    # Directory
    # --------------------------------------------------------

    test_files: list[Path] = []

    for path in target_path.rglob("*.py"):

        # Ignore generated/environment directories.
        if any(
            part in IGNORED_DIRECTORIES
            for part in path.parts
        ):
            continue

        if is_pytest_test_file(path):
            test_files.append(path)

    return sorted(test_files)


# ============================================================
# Build pytest command
# ============================================================

def build_pytest_command(
    test_files: list[Path],
    python_exec: Path,
    project_root: Path,
) -> list[str]:
    """
    Build one pytest command containing all discovered test files.
    """

    relative_tests = []

    for test_file in test_files:

        relative_test = test_file.relative_to(
            project_root
        )

        relative_tests.append(
            str(relative_test)
        )

    return [
        str(python_exec),
        "-m",
        "pytest",
        *relative_tests,
        "-v",
        "-s",
    ]


# ============================================================
# Build Python script command
# ============================================================

def build_python_command(
    target_path: Path,
    python_exec: Path,
    project_root: Path,
) -> list[str]:
    """
    Build the command for a normal Python script.
    """

    relative_target = target_path.relative_to(
        project_root
    )

    return [
        str(python_exec),
        str(relative_target),
    ]


# ============================================================
# Build subprocess environment
# ============================================================

def build_execution_environment(
    project_root: Path,
) -> dict[str, str]:
    """
    Build the subprocess environment.

    The project root is added to PYTHONPATH so local modules
    such as 'app' can be imported correctly.
    """

    environment = os.environ.copy()

    project_root_string = str(
        project_root
    )

    existing_pythonpath = environment.get(
        "PYTHONPATH"
    )

    if existing_pythonpath:

        environment["PYTHONPATH"] = (
            project_root_string
            + os.pathsep
            + existing_pythonpath
        )

    else:

        environment["PYTHONPATH"] = (
            project_root_string
        )

    return environment


# ============================================================
# Execute subprocess
# ============================================================

def execute_command(
    command: list[str],
    project_root: Path,
) -> subprocess.CompletedProcess:
    """
    Execute a command from the project root.
    """

    environment = build_execution_environment(
        project_root
    )

    print(
        "[TraceReq] Execution command:\n"
        f"  {' '.join(command)}"
    )

    print(
        "[TraceReq] Working directory:\n"
        f"  {project_root}\n"
    )

    return subprocess.run(
        command,
        cwd=str(project_root),
        env=environment,
        capture_output=True,
        text=True,
    )


# ============================================================
# Execute single target
# ============================================================

def run_single_target(
    target_path: Path,
    python_exec: Path,
    project_root: Path,
) -> subprocess.CompletedProcess:
    """
    Execute a single Python file.

    Test files are executed using pytest.

    Normal Python files are executed directly.
    """

    # --------------------------------------------------------
    # Pytest test
    # --------------------------------------------------------

    if is_pytest_test_file(target_path):

        command = build_pytest_command(
            test_files=[target_path],
            python_exec=python_exec,
            project_root=project_root,
        )

        return execute_command(
            command=command,
            project_root=project_root,
        )

    # --------------------------------------------------------
    # Normal Python script
    # --------------------------------------------------------

    command = build_python_command(
        target_path=target_path,
        python_exec=python_exec,
        project_root=project_root,
    )

    return execute_command(
        command=command,
        project_root=project_root,
    )


# ============================================================
# Execute discovered tests
# ============================================================

def run_test_files(
    test_files: list[Path],
    python_exec: Path,
    project_root: Path,
) -> subprocess.CompletedProcess:
    """
    Execute all discovered pytest test files in one pytest
    session.
    """

    command = build_pytest_command(
        test_files=test_files,
        python_exec=python_exec,
        project_root=project_root,
    )

    return execute_command(
        command=command,
        project_root=project_root,
    )


# ============================================================
# Print process output
# ============================================================

def print_process_output(
    process: subprocess.CompletedProcess,
) -> None:
    """
    Print stdout and stderr from a subprocess.
    """

    if process.stdout:
        print(
            process.stdout,
            end="",
        )

    if process.stderr:
        print(
            process.stderr,
            file=sys.stderr,
            end="",
        )


# ============================================================
# Handle failed execution
# ============================================================

def handle_execution_failure(
    process: subprocess.CompletedProcess,
    target_name: str,
    installer: PackageInstaller,
    retry_function,
) -> None:
    """
    Attempt automatic error remediation and retry the failed
    execution when possible.
    """

    error_output = (
        (process.stderr or "")
        + "\n"
        + (process.stdout or "")
    )

    remediated = (
        installer.attempt_error_remediation(
            error_output
        )
    )

    if remediated:

        print(
            "[TraceReq] Retrying execution for "
            f"{target_name}...\n"
        )

        retry = retry_function()

        print_process_output(
            retry
        )

        sys.exit(
            retry.returncode
        )

    print(
        "\n[TraceReq] Execution failed with "
        f"exit code {process.returncode}"
    )

    sys.exit(
        process.returncode
    )


# ============================================================
# Main CLI
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Reqora: discover runtime dependencies, "
            "install missing packages, and execute "
            "Python projects and pytest tests."
        )
    )

    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help=(
            "Python file, pytest test file, folder, "
            "or project directory "
            "(default: current directory)"
        ),
    )

    args = parser.parse_args()

    target_path = Path(
        args.target
    ).resolve()

    # ========================================================
    # Validate target
    # ========================================================

    if not target_path.exists():

        print(
            f"Error: Target path '{target_path}' "
            "does not exist."
        )

        sys.exit(1)

    # ========================================================
    # Discover project root
    # ========================================================

    project_root = (
        CodeAnalyzer.discover_project_root(
            target_path
        )
    )

    print(
        f"[TraceReq] Project root: "
        f"{project_root}"
    )

    analyzer = CodeAnalyzer(
        project_root=project_root
    )

    # ========================================================
    # Analyze dependencies
    # ========================================================

    if target_path.is_file():

        # ----------------------------------------------------
        # Validate Python file
        # ----------------------------------------------------

        if target_path.suffix.lower() != ".py":

            print(
                f"Error: '{target_path}' "
                "is not a Python file."
            )

            sys.exit(1)

        print(
            "[TraceReq] Analyzing dependency graph from: "
            f"{target_path.name}"
        )

        required_imports = (
            analyzer.analyze_entrypoint(
                target_path
            )
        )

    else:

        print(
            "[TraceReq] Scanning project: "
            f"{target_path}"
        )

        required_imports = (
            analyzer.scan_directory(
                target_path
            )
        )

    # ========================================================
    # Display detected dependencies
    # ========================================================

    if required_imports:

        print(
            "[TraceReq] Third-party imports detected: "
            + ", ".join(
                sorted(required_imports)
            )
        )

    else:

        print(
            "[TraceReq] No third-party imports detected."
        )

    # ========================================================
    # Resolve/install dependencies
    # ========================================================

    installer = PackageInstaller(
        project_root=project_root
    )

    missing = installer.resolve_missing(
        required_imports
    )

    if not missing:

        print(
            "[TraceReq] All required dependencies "
            "are already installed."
        )

    elif not installer.install_packages(
        missing
    ):

        print(
            "[TraceReq] Failed to install "
            "required dependencies."
        )

        sys.exit(1)

    # ========================================================
    # Determine Python interpreter
    # ========================================================

    python_exec = (
        installer.get_target_python()
    )

    # ========================================================
    # CASE 1:
    # Individual Python file
    # ========================================================

    if target_path.is_file():

        is_test = (
            is_pytest_test_file(
                target_path
            )
        )

        if is_test:

            execution_type = (
                "pytest test"
            )

        else:

            execution_type = (
                "Python script"
            )

        print(
            f"[TraceReq] Running "
            f"{execution_type} "
            f"{target_path.name} "
            f"using {python_exec}...\n"
        )

        process = run_single_target(
            target_path=target_path,
            python_exec=python_exec,
            project_root=project_root,
        )

        print_process_output(
            process
        )

        # ----------------------------------------------------
        # Successful execution
        # ----------------------------------------------------

        if process.returncode == 0:

            sys.exit(0)

        # ----------------------------------------------------
        # Failed execution
        # ----------------------------------------------------

        handle_execution_failure(
            process=process,
            target_name=target_path.name,
            installer=installer,
            retry_function=lambda: (
                run_single_target(
                    target_path=target_path,
                    python_exec=python_exec,
                    project_root=project_root,
                )
            ),
        )

    # ========================================================
    # CASE 2:
    # Directory / folder
    # ========================================================

    print(
        "\n[TraceReq] Searching for pytest "
        "test files..."
    )

    test_files = discover_test_files(
        target_path
    )

    # --------------------------------------------------------
    # No tests found
    # --------------------------------------------------------

    if not test_files:

        print(
            "[TraceReq] No pytest test files found "
            "in the requested folder."
        )

        print(
            "[TraceReq] Dependency analysis completed. "
            "Nothing to execute."
        )

        sys.exit(0)

    # --------------------------------------------------------
    # Tests found
    # --------------------------------------------------------

    print(
        f"[TraceReq] Test files discovered: "
        f"{len(test_files)}"
    )

    for test_file in test_files:

        try:

            relative_test = (
                test_file.relative_to(
                    project_root
                )
            )

        except ValueError:

            relative_test = test_file

        print(
            f"  - {relative_test}"
        )

    print()

    print(
        "[TraceReq] Running all discovered "
        "tests with pytest..."
    )

    print(
        f"[TraceReq] Using Python: "
        f"{python_exec}"
    )

    process = run_test_files(
        test_files=test_files,
        python_exec=python_exec,
        project_root=project_root,
    )

    print_process_output(
        process
    )

    # --------------------------------------------------------
    # Successful test execution
    # --------------------------------------------------------

    if process.returncode == 0:

        print(
            "\n[TraceReq] All discovered tests "
            "completed successfully."
        )

        sys.exit(0)

    # --------------------------------------------------------
    # Failed test execution
    # --------------------------------------------------------

    handle_execution_failure(
        process=process,
        target_name=str(target_path),
        installer=installer,
        retry_function=lambda: (
            run_test_files(
                test_files=test_files,
                python_exec=python_exec,
                project_root=project_root,
            )
        ),
    )


# ============================================================
# CLI entry point
# ============================================================

if __name__ == "__main__":
    main()