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


# import argparse
# import os
# import subprocess
# import sys
# from pathlib import Path

# from auto_req.analyzer import CodeAnalyzer
# from auto_req.installer import PackageInstaller


# # ============================================================
# # Test discovery configuration
# # ============================================================

# TEST_FILE_PATTERNS = (
#     "test_*.py",
#     "*_test.py",
# )

# IGNORED_DIRECTORIES = {
#     ".git",
#     ".venv",
#     "venv",
#     "env",
#     ".env",
#     "__pycache__",
#     ".pytest_cache",
#     "build",
#     "dist",
# }


# # ============================================================
# # Test detection
# # ============================================================

# def is_pytest_test_file(
#     path: Path,
# ) -> bool:
#     """
#     Return True when the file follows a pytest test-file naming
#     convention.

#     Supported patterns:

#         test_*.py
#         *_test.py
#     """

#     if not path.is_file():
#         return False

#     if path.suffix.lower() != ".py":
#         return False

#     return (
#         path.name.startswith("test_")
#         or path.name.endswith("_test.py")
#     )


# # ============================================================
# # Recursive test discovery
# # ============================================================

# def discover_test_files(
#     target_path: Path,
# ) -> list[Path]:
#     """
#     Recursively discover pytest test files.

#     If target_path is a file:
#         return the file when it is a pytest test file.

#     If target_path is a directory:
#         recursively search for:

#             test_*.py
#             *_test.py

#     Virtual environments, caches, build directories, and Git
#     metadata are ignored.
#     """

#     # --------------------------------------------------------
#     # Single file
#     # --------------------------------------------------------

#     if target_path.is_file():

#         if is_pytest_test_file(target_path):
#             return [target_path]

#         return []

#     # --------------------------------------------------------
#     # Directory
#     # --------------------------------------------------------

#     test_files: list[Path] = []

#     for path in target_path.rglob("*.py"):

#         # Ignore generated/environment directories.
#         if any(
#             part in IGNORED_DIRECTORIES
#             for part in path.parts
#         ):
#             continue

#         if is_pytest_test_file(path):
#             test_files.append(path)

#     return sorted(test_files)


# # ============================================================
# # Build pytest command
# # ============================================================

# def build_pytest_command(
#     test_files: list[Path],
#     python_exec: Path,
#     project_root: Path,
# ) -> list[str]:
#     """
#     Build one pytest command containing all discovered test files.
#     """

#     relative_tests = []

#     for test_file in test_files:

#         relative_test = test_file.relative_to(
#             project_root
#         )

#         relative_tests.append(
#             str(relative_test)
#         )

#     return [
#         str(python_exec),
#         "-m",
#         "pytest",
#         *relative_tests,
#         "-v",
#         "-s",
#     ]


# # ============================================================
# # Build Python script command
# # ============================================================

# def build_python_command(
#     target_path: Path,
#     python_exec: Path,
#     project_root: Path,
# ) -> list[str]:
#     """
#     Build the command for a normal Python script.
#     """

#     relative_target = target_path.relative_to(
#         project_root
#     )

#     return [
#         str(python_exec),
#         str(relative_target),
#     ]


# # ============================================================
# # Build subprocess environment
# # ============================================================

# def build_execution_environment(
#     project_root: Path,
# ) -> dict[str, str]:
#     """
#     Build the subprocess environment.

#     The project root is added to PYTHONPATH so local modules
#     such as 'app' can be imported correctly.
#     """

#     environment = os.environ.copy()

#     project_root_string = str(
#         project_root
#     )

#     existing_pythonpath = environment.get(
#         "PYTHONPATH"
#     )

#     if existing_pythonpath:

#         environment["PYTHONPATH"] = (
#             project_root_string
#             + os.pathsep
#             + existing_pythonpath
#         )

#     else:

#         environment["PYTHONPATH"] = (
#             project_root_string
#         )

#     return environment


# # ============================================================
# # Execute subprocess
# # ============================================================

# def execute_command(
#     command: list[str],
#     project_root: Path,
# ) -> subprocess.CompletedProcess:
#     """
#     Execute a command from the project root.
#     """

#     environment = build_execution_environment(
#         project_root
#     )

#     print(
#         "[TraceReq] Execution command:\n"
#         f"  {' '.join(command)}"
#     )

#     print(
#         "[TraceReq] Working directory:\n"
#         f"  {project_root}\n"
#     )

#     return subprocess.run(
#         command,
#         cwd=str(project_root),
#         env=environment,
#         capture_output=True,
#         text=True,
#     )


# # ============================================================
# # Execute single target
# # ============================================================

# def run_single_target(
#     target_path: Path,
#     python_exec: Path,
#     project_root: Path,
# ) -> subprocess.CompletedProcess:
#     """
#     Execute a single Python file.

#     Test files are executed using pytest.

#     Normal Python files are executed directly.
#     """

#     # --------------------------------------------------------
#     # Pytest test
#     # --------------------------------------------------------

#     if is_pytest_test_file(target_path):

#         command = build_pytest_command(
#             test_files=[target_path],
#             python_exec=python_exec,
#             project_root=project_root,
#         )

#         return execute_command(
#             command=command,
#             project_root=project_root,
#         )

#     # --------------------------------------------------------
#     # Normal Python script
#     # --------------------------------------------------------

#     command = build_python_command(
#         target_path=target_path,
#         python_exec=python_exec,
#         project_root=project_root,
#     )

#     return execute_command(
#         command=command,
#         project_root=project_root,
#     )


# # ============================================================
# # Execute discovered tests
# # ============================================================

# def run_test_files(
#     test_files: list[Path],
#     python_exec: Path,
#     project_root: Path,
# ) -> subprocess.CompletedProcess:
#     """
#     Execute all discovered pytest test files in one pytest
#     session.
#     """

#     command = build_pytest_command(
#         test_files=test_files,
#         python_exec=python_exec,
#         project_root=project_root,
#     )

#     return execute_command(
#         command=command,
#         project_root=project_root,
#     )


# # ============================================================
# # Print process output
# # ============================================================

# def print_process_output(
#     process: subprocess.CompletedProcess,
# ) -> None:
#     """
#     Print stdout and stderr from a subprocess.
#     """

#     if process.stdout:
#         print(
#             process.stdout,
#             end="",
#         )

#     if process.stderr:
#         print(
#             process.stderr,
#             file=sys.stderr,
#             end="",
#         )


# # ============================================================
# # Handle failed execution
# # ============================================================

# def handle_execution_failure(
#     process: subprocess.CompletedProcess,
#     target_name: str,
#     installer: PackageInstaller,
#     retry_function,
# ) -> None:
#     """
#     Attempt automatic error remediation and retry the failed
#     execution when possible.
#     """

#     error_output = (
#         (process.stderr or "")
#         + "\n"
#         + (process.stdout or "")
#     )

#     remediated = (
#         installer.attempt_error_remediation(
#             error_output
#         )
#     )

#     if remediated:

#         print(
#             "[TraceReq] Retrying execution for "
#             f"{target_name}...\n"
#         )

#         retry = retry_function()

#         print_process_output(
#             retry
#         )

#         sys.exit(
#             retry.returncode
#         )

#     print(
#         "\n[TraceReq] Execution failed with "
#         f"exit code {process.returncode}"
#     )

#     sys.exit(
#         process.returncode
#     )


# # ============================================================
# # Main CLI
# # ============================================================

# def main():

#     parser = argparse.ArgumentParser(
#         description=(
#             "Reqora: discover runtime dependencies, "
#             "install missing packages, and execute "
#             "Python projects and pytest tests."
#         )
#     )

#     parser.add_argument(
#         "target",
#         nargs="?",
#         default=".",
#         help=(
#             "Python file, pytest test file, folder, "
#             "or project directory "
#             "(default: current directory)"
#         ),
#     )

#     args = parser.parse_args()

#     target_path = Path(
#         args.target
#     ).resolve()

#     # ========================================================
#     # Validate target
#     # ========================================================

#     if not target_path.exists():

#         print(
#             f"Error: Target path '{target_path}' "
#             "does not exist."
#         )

#         sys.exit(1)

#     # ========================================================
#     # Discover project root
#     # ========================================================

#     project_root = (
#         CodeAnalyzer.discover_project_root(
#             target_path
#         )
#     )

#     print(
#         f"[TraceReq] Project root: "
#         f"{project_root}"
#     )

#     analyzer = CodeAnalyzer(
#         project_root=project_root
#     )

#     # ========================================================
#     # Analyze dependencies
#     # ========================================================

#     if target_path.is_file():

#         # ----------------------------------------------------
#         # Validate Python file
#         # ----------------------------------------------------

#         if target_path.suffix.lower() != ".py":

#             print(
#                 f"Error: '{target_path}' "
#                 "is not a Python file."
#             )

#             sys.exit(1)

#         print(
#             "[TraceReq] Analyzing dependency graph from: "
#             f"{target_path.name}"
#         )

#         required_imports = (
#             analyzer.analyze_entrypoint(
#                 target_path
#             )
#         )

#     else:

#         print(
#             "[TraceReq] Scanning project: "
#             f"{target_path}"
#         )

#         required_imports = (
#             analyzer.scan_directory(
#                 target_path
#             )
#         )

#     # ========================================================
#     # Display detected dependencies
#     # ========================================================

#     if required_imports:

#         print(
#             "[TraceReq] Third-party imports detected: "
#             + ", ".join(
#                 sorted(required_imports)
#             )
#         )

#     else:

#         print(
#             "[TraceReq] No third-party imports detected."
#         )

#     # ========================================================
#     # Resolve/install dependencies
#     # ========================================================

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

#     elif not installer.install_packages(
#         missing
#     ):

#         print(
#             "[TraceReq] Failed to install "
#             "required dependencies."
#         )

#         sys.exit(1)

#     # ========================================================
#     # Determine Python interpreter
#     # ========================================================

#     python_exec = (
#         installer.get_target_python()
#     )

#     # ========================================================
#     # CASE 1:
#     # Individual Python file
#     # ========================================================

#     if target_path.is_file():

#         is_test = (
#             is_pytest_test_file(
#                 target_path
#             )
#         )

#         if is_test:

#             execution_type = (
#                 "pytest test"
#             )

#         else:

#             execution_type = (
#                 "Python script"
#             )

#         print(
#             f"[TraceReq] Running "
#             f"{execution_type} "
#             f"{target_path.name} "
#             f"using {python_exec}...\n"
#         )

#         process = run_single_target(
#             target_path=target_path,
#             python_exec=python_exec,
#             project_root=project_root,
#         )

#         print_process_output(
#             process
#         )

#         # ----------------------------------------------------
#         # Successful execution
#         # ----------------------------------------------------

#         if process.returncode == 0:

#             sys.exit(0)

#         # ----------------------------------------------------
#         # Failed execution
#         # ----------------------------------------------------

#         handle_execution_failure(
#             process=process,
#             target_name=target_path.name,
#             installer=installer,
#             retry_function=lambda: (
#                 run_single_target(
#                     target_path=target_path,
#                     python_exec=python_exec,
#                     project_root=project_root,
#                 )
#             ),
#         )

#     # ========================================================
#     # CASE 2:
#     # Directory / folder
#     # ========================================================

#     print(
#         "\n[TraceReq] Searching for pytest "
#         "test files..."
#     )

#     test_files = discover_test_files(
#         target_path
#     )

#     # --------------------------------------------------------
#     # No tests found
#     # --------------------------------------------------------

#     if not test_files:

#         print(
#             "[TraceReq] No pytest test files found "
#             "in the requested folder."
#         )

#         print(
#             "[TraceReq] Dependency analysis completed. "
#             "Nothing to execute."
#         )

#         sys.exit(0)

#     # --------------------------------------------------------
#     # Tests found
#     # --------------------------------------------------------

#     print(
#         f"[TraceReq] Test files discovered: "
#         f"{len(test_files)}"
#     )

#     for test_file in test_files:

#         try:

#             relative_test = (
#                 test_file.relative_to(
#                     project_root
#                 )
#             )

#         except ValueError:

#             relative_test = test_file

#         print(
#             f"  - {relative_test}"
#         )

#     print()

#     print(
#         "[TraceReq] Running all discovered "
#         "tests with pytest..."
#     )

#     print(
#         f"[TraceReq] Using Python: "
#         f"{python_exec}"
#     )

#     process = run_test_files(
#         test_files=test_files,
#         python_exec=python_exec,
#         project_root=project_root,
#     )

#     print_process_output(
#         process
#     )

#     # --------------------------------------------------------
#     # Successful test execution
#     # --------------------------------------------------------

#     if process.returncode == 0:

#         print(
#             "\n[TraceReq] All discovered tests "
#             "completed successfully."
#         )

#         sys.exit(0)

#     # --------------------------------------------------------
#     # Failed test execution
#     # --------------------------------------------------------

#     handle_execution_failure(
#         process=process,
#         target_name=str(target_path),
#         installer=installer,
#         retry_function=lambda: (
#             run_test_files(
#                 test_files=test_files,
#                 python_exec=python_exec,
#                 project_root=project_root,
#             )
#         ),
#     )


# # ============================================================
# # CLI entry point
# # ============================================================

# if __name__ == "__main__":
#     main()


import argparse
import os
import re
import shutil
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
# CLI dependency configuration
# ============================================================

# Executable names that do not have the same PyPI package name.
#
# This is intentionally kept small and only contains known
# import/executable -> PyPI package differences.
#
# If an executable has the same name as its PyPI package,
# Reqora automatically uses the executable name as the
# PyPI package name.
CLI_TO_PYPI = {
    "uvicorn": "uvicorn",
    "gunicorn": "gunicorn",
    "pytest": "pytest",
    "ruff": "ruff",
    "black": "black",
    "mypy": "mypy",
    "isort": "isort",
    "coverage": "coverage",
    "http": "httpie",
    "pre-commit": "pre-commit",
    "mkdocs": "mkdocs",
    "tox": "tox",
}

# Commands that are shell/built-in commands rather than Python
# packages. These must never be passed to pip.
SYSTEM_COMMANDS = {
    "cd",
    "dir",
    "echo",
    "copy",
    "move",
    "del",
    "type",
    "where",
    "set",
    "cls",
    "mkdir",
    "rmdir",
    "powershell",
    "pwsh",
    "cmd",
    "python",
    "python3",
    "pip",
    "pip3",
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

    if target_path.is_file():

        if is_pytest_test_file(target_path):
            return [target_path]

        return []

    test_files: list[Path] = []

    for path in target_path.rglob("*.py"):

        if any(
            part in IGNORED_DIRECTORIES
            for part in path.parts
        ):
            continue

        if is_pytest_test_file(path):
            test_files.append(path)

    return sorted(test_files)


# ============================================================
# CLI command parsing
# ============================================================

def normalize_cli_executable(
    executable: str,
) -> str:
    """
    Normalize a CLI executable name.

    Examples:

        uvicorn.exe -> uvicorn
        pytest.exe  -> pytest
        ruff        -> ruff
    """

    executable = Path(executable).name.lower()

    if executable.endswith(".exe"):
        executable = executable[:-4]

    if executable.endswith(".cmd"):
        executable = executable[:-4]

    if executable.endswith(".bat"):
        executable = executable[:-4]

    return executable


def extract_cli_executable(
    command: list[str],
) -> str | None:
    """
    Extract the executable from a CLI command.

    Example:

        ["uvicorn", "app.main:app", "--reload"]

    returns:

        "uvicorn"
    """

    if not command:
        return None

    executable = command[0].strip()

    if not executable:
        return None

    return normalize_cli_executable(
        executable
    )


def get_cli_pypi_package(
    executable: str,
) -> str | None:
    """
    Convert a CLI executable name into its PyPI package name.

    Known mappings are used first.

    If no special mapping exists, the executable name itself
    is treated as the PyPI package name.

    Examples:

        uvicorn -> uvicorn
        pytest  -> pytest
        ruff    -> ruff
    """

    executable = normalize_cli_executable(
        executable
    )

    if executable in SYSTEM_COMMANDS:
        return None

    return CLI_TO_PYPI.get(
        executable,
        executable,
    )


# ============================================================
# CLI executable detection
# ============================================================

def is_cli_available(
    executable: str,
    project_python: Path | None = None,
) -> bool:
    """
    Determine whether a CLI executable is available.

    First checks PATH.

    Then, when project_python is supplied, checks the Scripts/bin
    directory belonging to that Python environment.

    This is important on Windows because a package may be installed
    in the target virtual environment even when the shell PATH has
    not been refreshed.
    """

    executable = normalize_cli_executable(
        executable
    )

    if shutil.which(executable):
        return True

    if project_python:

        python_path = Path(
            project_python
        ).resolve()

        python_dir = python_path.parent

        candidates = [
            python_dir / f"{executable}.exe",
            python_dir / f"{executable}.cmd",
            python_dir / f"{executable}.bat",
        ]

        if os.name != "nt":
            candidates.append(
                python_dir / executable
            )

        for candidate in candidates:

            if candidate.exists():
                return True

    return False


# ============================================================
# Install CLI dependency
# ============================================================

def install_cli_dependency(
    executable: str,
    installer: PackageInstaller,
) -> bool:
    """
    Install the PyPI package associated with a missing CLI
    executable.
    """

    executable = normalize_cli_executable(
        executable
    )

    package_name = get_cli_pypi_package(
        executable
    )

    if not package_name:
        print(
            "[TraceReq] CLI executable "
            f"'{executable}' is a system command."
        )
        return True

    print(
        "[TraceReq] CLI executable detected: "
        f"{executable}"
    )

    print(
        "[TraceReq] PyPI package resolved: "
        f"{package_name}"
    )

    # --------------------------------------------------------
    # Use the target Python environment for installation.
    # --------------------------------------------------------

    python_exec = installer.get_target_python()

    print(
        "[TraceReq] Installing CLI dependency: "
        f"{package_name}"
    )

    command = [
        str(python_exec),
        "-m",
        "pip",
        "install",
        package_name,
    ]

    print(
        "[TraceReq] Installation command:\n"
        f"  {' '.join(command)}\n"
    )

    process = subprocess.run(
        command,
        cwd=str(installer.project_root),
        capture_output=True,
        text=True,
    )

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

    if process.returncode != 0:

        print(
            "[TraceReq] Failed to install CLI dependency: "
            f"{package_name}"
        )

        return False

    print(
        "[TraceReq] CLI dependency installed successfully: "
        f"{package_name}"
    )

    return True


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
# Add target Python Scripts directory to PATH
# ============================================================

def build_cli_execution_environment(
    project_root: Path,
    python_exec: Path,
) -> dict[str, str]:
    """
    Build an execution environment for CLI applications.

    The target Python environment's Scripts/bin directory is
    added to PATH.

    This allows Reqora to execute:

        uvicorn
        pytest
        ruff
        black
        etc.

    even when the parent shell PATH does not contain that
    virtual environment's Scripts directory.
    """

    environment = build_execution_environment(
        project_root
    )

    python_dir = Path(
        python_exec
    ).resolve().parent

    existing_path = environment.get(
        "PATH",
        "",
    )

    environment["PATH"] = (
        str(python_dir)
        + os.pathsep
        + existing_path
    )

    return environment


# ============================================================
# Execute subprocess
# ============================================================

def execute_command(
    command: list[str],
    project_root: Path,
    python_exec: Path | None = None,
) -> subprocess.CompletedProcess:
    """
    Execute a command from the project root.

    When python_exec is supplied, its Scripts/bin directory is
    added to PATH so installed CLI tools can be executed.
    """

    if python_exec:

        environment = (
            build_cli_execution_environment(
                project_root,
                python_exec,
            )
        )

    else:

        environment = (
            build_execution_environment(
                project_root
            )
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
# Execute CLI command
# ============================================================

def run_cli_command(
    command: list[str],
    python_exec: Path,
    project_root: Path,
) -> subprocess.CompletedProcess:
    """
    Execute an external CLI command.

    Example:

        reqora run uvicorn app.main:app --reload

    """

    return execute_command(
        command=command,
        project_root=project_root,
        python_exec=python_exec,
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

    if is_pytest_test_file(target_path):

        command = build_pytest_command(
            test_files=[target_path],
            python_exec=python_exec,
            project_root=project_root,
        )

        return execute_command(
            command=command,
            project_root=project_root,
            python_exec=python_exec,
        )

    command = build_python_command(
        target_path=target_path,
        python_exec=python_exec,
        project_root=project_root,
    )

    return execute_command(
        command=command,
        project_root=project_root,
        python_exec=python_exec,
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
        python_exec=python_exec,
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
# Execute CLI mode
# ============================================================

def execute_cli_mode(
    command: list[str],
    project_root: Path,
    installer: PackageInstaller,
) -> None:
    """
    Execute an external CLI command.

    Missing CLI executables are automatically mapped to PyPI
    packages, installed into Reqora's target environment, and
    then retried.

    Example:

        reqora run uvicorn app.main:app --reload
    """

    if not command:

        print(
            "[TraceReq] Error: No CLI command supplied."
        )

        sys.exit(1)

    python_exec = (
        installer.get_target_python()
    )

    executable = extract_cli_executable(
        command
    )

    if not executable:

        print(
            "[TraceReq] Error: Unable to determine "
            "CLI executable."
        )

        sys.exit(1)

    print(
        "[TraceReq] CLI command requested:\n"
        f"  {' '.join(command)}"
    )

    # --------------------------------------------------------
    # Check whether executable exists.
    # --------------------------------------------------------

    available = is_cli_available(
        executable=executable,
        project_python=python_exec,
    )

    if not available:

        print(
            "[TraceReq] CLI executable not found: "
            f"{executable}"
        )

        installed = install_cli_dependency(
            executable=executable,
            installer=installer,
        )

        if not installed:
            sys.exit(1)

    else:

        print(
            "[TraceReq] CLI executable already available: "
            f"{executable}"
        )

    # --------------------------------------------------------
    # Execute CLI command.
    # --------------------------------------------------------

    process = run_cli_command(
        command=command,
        python_exec=python_exec,
        project_root=project_root,
    )

    print_process_output(
        process
    )

    # --------------------------------------------------------
    # Success.
    # --------------------------------------------------------

    if process.returncode == 0:

        print(
            "\n[TraceReq] CLI command completed "
            "successfully."
        )

        sys.exit(0)

    # --------------------------------------------------------
    # Failed CLI execution.
    #
    # Existing Reqora error-remediation is still allowed.
    # --------------------------------------------------------

    handle_execution_failure(
        process=process,
        target_name=" ".join(command),
        installer=installer,
        retry_function=lambda: (
            run_cli_command(
                command=command,
                python_exec=python_exec,
                project_root=project_root,
            )
        ),
    )

# ============================================================
# Analyze and install project dependencies
# ============================================================

def analyze_and_install_dependencies(
    project_root: Path,
    target_path: Path | None = None,
) -> PackageInstaller:
    """
    Analyze project dependencies and install missing packages.

    This function ONLY handles dependency analysis and
    installation.

    It does NOT execute Python files or tests.
    """

    analyzer = CodeAnalyzer(
        project_root=project_root
    )

    if target_path is not None and target_path.is_file():

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

        scan_path = (
            target_path
            if target_path is not None
            else project_root
        )

        print(
            "[TraceReq] Scanning project dependencies: "
            f"{scan_path}"
        )

        required_imports = (
            analyzer.scan_directory(
                scan_path
            )
        )

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

    return installer
# ============================================================
# Main CLI
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Reqora: discover runtime dependencies, "
            "install missing packages, install missing "
            "CLI dependencies, and execute Python "
            "projects and pytest tests."
        )
    )

    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help=(
            "Python file, pytest test file, folder, "
            "project directory, or 'run' for a CLI "
            "command."
        ),
    )

    parser.add_argument(
        "command_args",
        nargs=argparse.REMAINDER,
        help=(
            "Arguments for an external CLI command "
            "when using: reqora run <command> ..."
        ),
    )

    args = parser.parse_args()
        # ========================================================
    # DEPENDENCY-ONLY MODE
    #
    # reqora
    #
    # Analyze the current project and install missing
    # dependencies, but do NOT execute any files/tests.
    # ========================================================

    if args.target is None:

        current_directory = Path.cwd().resolve()

        project_root = (
            CodeAnalyzer.discover_project_root(
                current_directory
            )
        )

        print(
            f"[TraceReq] Project root: "
            f"{project_root}"
        )

        analyzer = CodeAnalyzer(
            project_root=project_root
        )

        print(
            "[TraceReq] Scanning project dependencies..."
        )

        required_imports = (
            analyzer.scan_directory(
                project_root
            )
        )

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

        print(
            "\n[TraceReq] Dependency analysis completed."
        )

        print(
            "[TraceReq] No files or tests were executed."
        )

        sys.exit(0)

    # ========================================================
    # CLI MODE
    #
    # reqora run uvicorn app.main:app --reload
    # ========================================================

    if args.target.lower() == "run":

        command = args.command_args

        if command and command[0] == "--":
            command = command[1:]

        # ----------------------------------------------------
        # Discover project root from current directory.
        # ----------------------------------------------------

        current_directory = Path.cwd().resolve()

        project_root = (
            CodeAnalyzer.discover_project_root(
                current_directory
            )
        )

        print(
            f"[TraceReq] Project root: "
            f"{project_root}"
        )

        installer = PackageInstaller(
            project_root=project_root
        )

        execute_cli_mode(
            command=command,
            project_root=project_root,
            installer=installer,
        )

        return

    # ========================================================
    # Normal Reqora target mode
    # ========================================================

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
            execution_type = "pytest test"
        else:
            execution_type = "Python script"

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

        if process.returncode == 0:
            sys.exit(0)

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

    if process.returncode == 0:

        print(
            "\n[TraceReq] All discovered tests "
            "completed successfully."
        )

        sys.exit(0)

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