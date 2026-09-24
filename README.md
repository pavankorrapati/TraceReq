# Reqora

**Reqora** is an AST-driven Python dependency discovery, resolution, environment detection, dependency provisioning, and runtime execution engine.

It analyzes the Python code you want to run, discovers imported dependencies, recursively follows reachable local project imports, identifies standard-library and third-party dependencies, maps Python import names to their corresponding PyPI distributions, detects the appropriate Python environment, installs missing dependencies, and then executes the requested target when execution has explicitly been requested.

Reqora is designed to reduce the need to manually maintain a static `requirements.txt` file for every runtime scenario.

---

## Key Features

Reqora provides:

* AST-based Python dependency discovery
* Recursive analysis of reachable local Python modules
* Standard-library detection
* Third-party dependency detection
* Import-name → PyPI-package mapping
* Automatic missing dependency installation
* Virtual-environment detection
* Support for activated environments
* Support for custom virtual-environment names
* Single-file execution
* Recursive test discovery
* Pytest test execution
* Explicit CLI command execution
* Automatic provisioning of missing CLI dependencies
* Project-root-aware execution
* `PYTHONPATH` configuration for local project imports
* Dependency analysis separated from execution

---

# How Reqora Works

The overall workflow is:

```text
Reqora source project
        │
        │ python -m build
        ▼
dist/
 ├── reqora-0.1.2-py3-none-any.whl
 │       ← reusable Python package
 │
 └── reqora-0.1.2.tar.gz
        │
        │ pip install reqora
        ▼
Any Python project
        │
        ├── .venv/
        ├── tests/
        ├── src/
        ├── main.py
        ├── script.py
        └── ...
        │
        ▼
      Reqora
        │
        ├── Analyze target
        │
        ├── Discover local imports
        │
        ├── Recursively analyze reachable
        │   local Python modules
        │
        ├── Detect standard-library modules
        │
        ├── Detect third-party imports
        │
        ├── Map imports
        │   → PyPI distributions
        │
        ├── Detect appropriate Python environment
        │
        ├── Install missing dependencies
        │
        └── Execute only when requested
```

---

# Installation

Install Reqora from PyPI:

```powershell
pip install reqora
```

After installation, the `reqora` command becomes available:

```powershell
reqora --help
```

The public PyPI distribution name is:

```text
reqora
```

The command-line executable is:

```text
reqora
```

The internal Python package remains:

```text
auto_req
```

Therefore:

```python
import auto_req
```

while installation is performed using:

```powershell
pip install reqora
```

and the CLI is:

```powershell
reqora
```

---

# CLI Behavior

Reqora supports several execution modes.

## 1. `reqora`

Running:

```powershell
reqora
```

performs dependency analysis and provisioning for the current project.

It **does not execute application files or tests automatically**.

The result is intended to be:

```text
Dependency analysis
        │
        ▼
Dependency resolution
        │
        ▼
Missing dependency installation
        │
        ▼
No files executed
```

This makes the no-argument command useful when the developer only wants to prepare the environment.

---

# 2. Execute a Python File

To analyze and execute a specific Python file:

```powershell
reqora script.py
```

Reqora:

1. Identifies the project root.
2. Analyzes `script.py`.
3. Discovers imports.
4. Recursively follows reachable local Python modules.
5. Separates local modules from third-party modules.
6. Identifies standard-library modules.
7. Maps third-party imports to PyPI packages.
8. Detects the appropriate Python environment.
9. Installs missing dependencies.
10. Executes only `script.py`.

Example:

```text
reqora script.py
        │
        ▼
Analyze script.py
        │
        ▼
Resolve dependencies
        │
        ▼
Install missing packages
        │
        ▼
Execute script.py
```

A normal application script is executed directly using Python rather than being passed through pytest.

---

# 3. Execute a Specific Test File

A specific test file can be executed directly:

```powershell
reqora tests\test_privacy.py
```

Reqora analyzes the selected test file and its reachable local imports before executing that test file.

Example:

```text
reqora tests\test_privacy.py
        │
        ▼
Analyze test_privacy.py
        │
        ▼
Discover dependencies
        │
        ▼
Install missing dependencies
        │
        ▼
Execute test_privacy.py
```

Only the requested test file is executed.

---

# 4. Execute a Test Directory

A directory can be supplied explicitly:

```powershell
reqora tests\
```

When a directory is explicitly provided, Reqora recursively searches for pytest-compatible test files.

Supported test-file patterns are:

```text
test_*.py
*_test.py
```

For example:

```text
tests/
│
├── test_events.py
├── test_privacy.py
├── test_pypi_stats.py
│
└── api/
    ├── test_api.py
    └── test_auth.py
```

Running:

```powershell
reqora tests\
```

discovers the test files and executes them together in a single pytest session.

Conceptually:

```text
reqora tests\
      │
      ▼
Discover test files
      │
      ├── test_events.py
      ├── test_privacy.py
      ├── test_pypi_stats.py
      ├── api/test_api.py
      └── api/test_auth.py
      │
      ▼
Run pytest once
      │
      ▼
Test results
```

---

# 5. Explicit CLI Command Execution

Reqora also supports explicit execution of command-line applications.

Use:

```powershell
reqora run <command>
```

For example:

```powershell
reqora run uvicorn app.main:app
```

or:

```powershell
reqora run uvicorn app.main:app --reload
```

This mode is intentionally explicit.

The command:

```powershell
reqora run uvicorn app.main:app
```

means:

```text
User explicitly requested:
        │
        ▼
Run uvicorn
        │
        ▼
Is uvicorn available?
        │
   ┌────┴────┐
   │         │
  YES        NO
   │         │
   │         ▼
   │    Resolve PyPI package
   │         │
   │         ▼
   │    Install uvicorn
   │         │
   └────┬────┘
        ▼
Execute command
```

Reqora can map common command-line executables to their PyPI distributions.

Current mappings include:

| CLI executable | PyPI package |
| -------------- | ------------ |
| `uvicorn`      | `uvicorn`    |
| `gunicorn`     | `gunicorn`   |
| `pytest`       | `pytest`     |
| `ruff`         | `ruff`       |
| `black`        | `black`      |
| `mypy`         | `mypy`       |
| `isort`        | `isort`      |
| `coverage`     | `coverage`   |
| `http`         | `httpie`     |
| `pre-commit`   | `pre-commit` |
| `mkdocs`       | `mkdocs`     |
| `tox`          | `tox`        |

For example:

```powershell
reqora run pytest tests\
```

or:

```powershell
reqora run uvicorn app.main:app --reload
```

---

# CLI Execution Rules

Reqora distinguishes between implicit and explicit execution.

| Command                      | Dependency analysis |          Execute |
| ---------------------------- | ------------------: | ---------------: |
| `reqora`                     |                 Yes |               No |
| `reqora script.py`           |                 Yes |        script.py |
| `reqora tests\test_api.py`   |                 Yes |    Selected test |
| `reqora tests\`              |                 Yes | Discovered tests |
| `reqora run uvicorn app:app` |   Yes/provision CLI |     Explicit CLI |
| `reqora run pytest tests\`   |   Yes/provision CLI |     Explicit CLI |

This separation prevents Reqora from unexpectedly executing project code when the developer only wants dependency provisioning.

---

# Recursive Dependency Analysis

Reqora is not limited to imports directly present in the file being executed.

For example:

```text
script.py
    │
    ▼
main.py
    │
    ▼
service.py
    │
    ▼
repository.py
    │
    ▼
client.py
    │
    ├── requests
    └── pydantic
```

Running:

```powershell
reqora script.py
```

causes Reqora to follow reachable local Python modules.

The resulting dependency graph can be represented as:

```text
script.py
    │
    ▼
main.py
    │
    ├── services/api.py
    │       │
    │       ├── requests
    │       └── yaml
    │
    └── utils/helpers.py
            │
            ├── json
            └── os
```

Reqora understands that:

```text
script.py
main.py
services/api.py
utils/helpers.py
```

are local project files.

They are therefore not treated as PyPI dependencies.

---

# Standard Library Detection

Reqora identifies Python standard-library modules separately.

For example:

```python
import json
import os
```

does not result in:

```text
pip install json
pip install os
```

Instead, Reqora recognizes:

```text
json → Python standard library
os   → Python standard library
```

No PyPI installation is required.

---

# Third-Party Dependency Detection

Consider:

```python
import requests
import yaml
```

Reqora identifies these as external dependencies.

The import names are:

```text
requests
yaml
```

The corresponding PyPI distributions are:

```text
requests → requests
yaml     → PyYAML
```

Therefore Reqora can install:

```powershell
pip install requests PyYAML
```

into the appropriate Python environment when they are missing.

---

# Import Name → PyPI Distribution Mapping

Python import names and PyPI distribution names are not always identical.

For example:

```text
Python import       PyPI distribution
-------------------------------------
requests            requests
yaml                PyYAML
bs4                 beautifulsoup4
PIL                 Pillow
cv2                 opencv-python
sklearn             scikit-learn
```

Reqora maintains known mappings for common import/package-name differences and can use PyPI resolution for packages that are not covered by static mappings.

---

# Local Module Detection

Reqora distinguishes between:

```text
Local project modules
```

and:

```text
External Python packages
```

For example:

```text
my_project/
│
├── script.py
├── main.py
├── services/
│   ├── __init__.py
│   └── api.py
└── utils/
    └── helpers.py
```

If:

```python
from main import run_application
```

appears in `script.py`, Reqora checks whether `main.py` exists locally.

If it does, Reqora analyzes that file rather than attempting to install a PyPI package called `main`.

This principle applies recursively.

---

# Relative Imports

Reqora supports project structures containing relative imports such as:

```python
from .services import api
```

and:

```python
from ..utils import helpers
```

The dependency analyzer resolves reachable local modules within the project structure.

This is particularly useful for Python packages and layered application architectures.

---

# Virtual Environment Detection

Reqora does not require every virtual environment to have the same name.

Common names include:

```text
.venv
venv
env
.env
virtualenv
```

These are recognized conventional environment names.

However, Reqora can also identify environments based on their Python virtual-environment structure rather than relying exclusively on their directory name.

For example:

```text
qa_environment/
automation_env/
python312/
company_python/
my_project_environment/
test_runtime/
anything_you_want/
```

can be considered when they contain the expected environment structure.

---

# Windows Environment

On Windows, a Python virtual environment generally contains:

```text
pyvenv.cfg

Scripts/
    python.exe
    pip.exe
```

Reqora can use this structure to identify the environment's Python executable.

Example:

```text
my_environment/
│
├── pyvenv.cfg
│
└── Scripts/
    ├── python.exe
    └── pip.exe
```

---

# Linux / macOS Environment

On Linux and macOS, a typical virtual environment contains:

```text
pyvenv.cfg

bin/
    python
    pip
```

Reqora can identify the corresponding Python executable.

---

# Already Activated Environments

If a virtual environment is already activated, Reqora respects the active Python environment.

For example:

```powershell
.\venv\Scripts\Activate.ps1
```

followed by:

```powershell
reqora script.py
```

allows Reqora to work with the active environment rather than unnecessarily creating another environment.

---

# Project Root Detection

Reqora operates relative to the project containing the target.

For example:

```text
my_project/
│
├── pyproject.toml
├── src/
├── tests/
└── app/
```

Running:

```powershell
reqora src\main.py
```

allows Reqora to determine the project context and analyze local imports relative to that project.

The project root is also used as the execution working directory.

---

# PYTHONPATH Handling

When executing project files, Reqora prepares the execution environment so that local project modules can be imported correctly.

Conceptually:

```text
Project root
     │
     ├── app/
     ├── services/
     ├── utils/
     └── tests/
```

becomes available through the Python module search path.

This allows structures such as:

```python
from services.api import get_data
```

to resolve correctly when the project is executed through Reqora.

---

# Test Discovery

When an explicitly supplied directory is intended for testing, Reqora recursively discovers Python test files.

Supported patterns:

```text
test_*.py
*_test.py
```

For example:

```text
tests/
│
├── test_api.py
├── test_database.py
│
└── integration/
    ├── test_login.py
    └── test_checkout.py
```

Reqora discovers all matching files while ignoring common non-project directories.

Ignored directories include:

```text
.git
.venv
venv
env
.env
__pycache__
.pytest_cache
build
dist
```

This prevents generated files, virtual environments, caches, and build artifacts from being treated as application/test sources.

---

# Test Execution

Discovered tests are executed together in a single pytest session.

For example:

```powershell
reqora tests\
```

is conceptually equivalent to:

```text
Discover:
    tests/test_api.py
    tests/test_database.py
    tests/integration/test_login.py
    tests/integration/test_checkout.py

        │
        ▼

One pytest execution
        │
        ▼
Test result
```

This is different from executing every test file as an independent Python process.

---

# Normal Python Script Execution

A normal Python file is not automatically treated as a pytest test.

For example:

```powershell
reqora application.py
```

executes:

```text
application.py
```

directly.

It does not automatically transform the command into:

```powershell
pytest application.py
```

This distinction allows Reqora to support both:

```text
Application execution
```

and:

```text
Test execution
```

without confusing the two workflows.

---

# CLI Dependency Provisioning

Some applications are normally started through command-line executables instead of Python imports.

For example:

```powershell
uvicorn app.main:app
```

The application source might not contain:

```python
import uvicorn
```

because Uvicorn is being invoked externally.

Reqora therefore provides explicit CLI execution:

```powershell
reqora run uvicorn app.main:app
```

If the executable is missing, Reqora can resolve the executable to its corresponding PyPI package:

```text
uvicorn
   │
   ▼
PyPI package: uvicorn
   │
   ▼
Install
   │
   ▼
Execute uvicorn
```

This addresses dependencies that are not necessarily discoverable through the Python AST alone.

---

# System Commands

Reqora does not treat operating-system commands such as the following as PyPI packages:

```text
cd
dir
echo
copy
move
del
type
where
set
cls
mkdir
rmdir
powershell
pwsh
cmd
python
python3
pip
pip3
```

These are considered system/runtime commands rather than Python package dependencies.

---

# CLI Architecture

The command-line entry point is:

```text
auto_req.cli:main
```

The public CLI is:

```text
reqora
```

The architecture can be represented as:

```text
reqora
  │
  ▼
auto_req.cli:main
  │
  ├── Target validation
  │
  ├── Project-root detection
  │
  ├── CodeAnalyzer
  │      │
  │      ├── Import discovery
  │      ├── Local-module resolution
  │      └── Dependency graph
  │
  ├── PackageInstaller
  │      │
  │      ├── Environment detection
  │      ├── PyPI resolution
  │      └── Dependency installation
  │
  └── Execution
         │
         ├── Python file
         │
         ├── Test files
         │
         └── Explicit CLI command
```

---

# CLI Processing Flow

The latest CLI implementation follows this general decision flow:

```text
                         reqora
                           │
              ┌────────────┴────────────┐
              │                         │
        No target supplied        Target supplied
              │                         │
              ▼                         ▼
     Analyze current project      Is target "run"?
              │                         │
              ▼                    ┌────┴────┐
     Install dependencies         YES       NO
              │                    │         │
              ▼                    ▼         ▼
      No execution          CLI execution  Validate target
                                      │         │
                                      │         ▼
                                      │   Analyze dependencies
                                      │         │
                                      │         ▼
                                      │   Install dependencies
                                      │         │
                                      │         ▼
                                      │   File or directory?
                                      │         │
                                      │    ┌────┴────┐
                                      │   FILE     DIR
                                      │    │         │
                                      │    ▼         ▼
                                      │ Execute   Discover tests
                                      │ file         │
                                      │              ▼
                                      │         Execute tests
```

---

# Package Architecture

The source project follows this general structure:

```text
TraceReq/
│
├── auto_req/
│   ├── __init__.py
│   ├── analyzer.py
│   ├── installer.py
│   ├── cli.py
│   └── ...
│
├── tests/
│
├── README.md
│
├── pyproject.toml
│
└── ...
```

The internal Python package is:

```text
auto_req
```

Import example:

```python
import auto_req
```

The PyPI distribution is:

```text
reqora
```

Installation:

```powershell
pip install reqora
```

CLI:

```powershell
reqora
```

---

# Example Project

Suppose a project contains:

```text
my_project/
│
├── my_environment/
│   ├── pyvenv.cfg
│   └── Scripts/
│       └── python.exe
│
├── script.py
├── main.py
│
├── services/
│   ├── __init__.py
│   └── api.py
│
└── utils/
    └── helpers.py
```

## `script.py`

```python
from main import run_application
```

## `main.py`

```python
from services.api import get_data
from utils.helpers import process_data
```

## `services/api.py`

```python
import requests
import yaml
```

## `utils/helpers.py`

```python
import json
import os
```

Execute:

```powershell
reqora script.py
```

Reqora analyzes:

```text
script.py
    │
    ▼
main.py
    │
    ├── services/api.py
    │       ├── requests
    │       └── yaml
    │
    └── utils/helpers.py
            ├── json
            └── os
```

It identifies:

```text
Local:
    script.py
    main.py
    services/api.py
    utils/helpers.py

Standard library:
    json
    os

Third-party:
    requests
    yaml
```

Then maps:

```text
requests → requests
yaml     → PyYAML
```

Missing dependencies can then be installed into the detected Python environment.

Finally:

```text
script.py
```

is executed.

---

# Larger Application Example

Reqora can work with a layered architecture:

```text
application/
│
├── app.py
│
├── services/
│   ├── user_service.py
│   └── order_service.py
│
├── repositories/
│   ├── user_repository.py
│   └── order_repository.py
│
├── clients/
│   └── api_client.py
│
├── utils/
│   └── helpers.py
│
└── config/
    └── settings.py
```

Dependency flow:

```text
app.py
 │
 ├── services/user_service.py
 │       │
 │       └── repositories/user_repository.py
 │                    │
 │                    └── sqlalchemy
 │
 ├── services/order_service.py
 │       │
 │       └── repositories/order_repository.py
 │                    │
 │                    └── sqlalchemy
 │
 └── clients/api_client.py
          │
          └── requests
```

Reqora follows the reachable local modules and identifies the external packages:

```text
sqlalchemy
requests
```

instead of treating the internal modules as external dependencies.

---

# Building the Package

From the Reqora source project:

```powershell
cd "C:\Users\anuab\Desktop\CoreDon_Automation_Terra\TraceReq"
```

Clean previous build artifacts:

```powershell
Remove-Item -Recurse -Force .\build -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .\dist -ErrorAction SilentlyContinue

Get-ChildItem -Directory -Filter "*.egg-info" |
    Remove-Item -Recurse -Force
```

Build:

```powershell
python -m build
```

The generated distribution will look like:

```text
dist/
├── reqora-0.1.2-py3-none-any.whl
└── reqora-0.1.2.tar.gz
```

The wheel is the primary reusable installation artifact.

---

# Installing a Local Build

The wheel can be installed locally:

```powershell
pip install .\dist\reqora-0.1.2-py3-none-any.whl
```

Then verify:

```powershell
reqora --help
```

Verify the internal package:

```powershell
python -c "import auto_req; print(auto_req.__file__)"
```

---

# Package Validation

Before publishing, validate the generated distributions:

```powershell
python -m twine check .\dist\*
```

A successful validation should report:

```text
Checking reqora-0.1.2-py3-none-any.whl: PASSED
Checking reqora-0.1.2.tar.gz: PASSED
```

---

# Publishing to PyPI

After the package has been validated:

```powershell
python -m twine upload .\dist\*
```

The published distribution is:

```text
reqora
```

Users install it using:

```powershell
pip install reqora
```

After installation:

```powershell
reqora --help
```

and:

```powershell
reqora script.py
```

---

# Version Management

Every new PyPI release must use a new version.

For example:

```text
0.1.0
   ↓
0.1.1
   ↓
0.1.2
   ↓
0.2.0
```

The version is defined in:

```text
pyproject.toml
```

For example:

```toml
[project]
name = "reqora"
version = "0.1.2"
```

Do not attempt to upload another distribution using an already-published version.

---

# Release Workflow

The recommended release workflow is:

```text
TraceReq
   │
   ├── pyproject.toml
   │       │
   │       ├── name = "reqora"
   │       └── version = "0.1.2"
   │
   ├── README.md
   │       │
   │       └── Reqora documentation
   │
   └── auto_req/
           │
           ├── analyzer.py
           ├── installer.py
           └── cli.py
                   │
                   ▼
              python -m build
                   │
                   ▼
                 dist/
                   │
             ┌─────┴─────┐
             ▼           ▼
       .whl file      .tar.gz
             │           │
             └─────┬─────┘
                   ▼
       python -m twine check .\dist\*
                   │
                   ▼
       python -m twine upload .\dist\*
                   │
                   ▼
                  PyPI
                   │
                   ▼
          pip install reqora
                   │
                   ▼
             reqora script.py
```

---

# Recommended Verification After Publishing

After publishing the new release, create a clean environment and install Reqora directly from PyPI:

```powershell
python -m venv reqora_test_env
```

Activate:

```powershell
.\reqora_test_env\Scripts\Activate.ps1
```

Install:

```powershell
python -m pip install --upgrade pip
python -m pip install reqora
```

Verify:

```powershell
reqora --help
```

Verify the installed package:

```powershell
python -c "import auto_req; print(auto_req.__file__)"
```

Then test the major execution modes:

```powershell
reqora
```

Dependency analysis only.

```powershell
reqora script.py
```

Analyze and execute one Python file.

```powershell
reqora tests\
```

Analyze and execute discovered tests.

```powershell
reqora tests\test_privacy.py
```

Analyze and execute one specific test file.

```powershell
reqora run uvicorn app.main:app
```

Provision and execute an explicit CLI command.

---

# Reqora vs `requirements.txt`

Traditional workflow:

```text
requirements.txt
       │
       ▼
pip install -r requirements.txt
       │
       ▼
Run application
```

Reqora workflow:

```text
Python target
       │
       ▼
     Reqora
       │
       ▼
Analyze dependency graph
       │
       ▼
Detect local modules
       │
       ▼
Detect standard-library modules
       │
       ▼
Detect external dependencies
       │
       ▼
Map imports → PyPI packages
       │
       ▼
Detect Python environment
       │
       ▼
Install missing dependencies
       │
       ▼
Execute requested target
```

Reqora therefore moves dependency provisioning closer to the runtime execution workflow.

---

# Intended User Experience

The intended workflow is:

```text
                 pip install reqora
                         │
                         ▼
                ┌─────────────────┐
                │      reqora     │
                └────────┬────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
         reqora script.py      reqora tests\
              │                     │
              ▼                     ▼
      Analyze Python file     Discover tests
              │                     │
              ▼                     ▼
      Recursive imports       Analyze dependencies
              │                     │
              ▼                     ▼
      Resolve dependencies    Install dependencies
              │                     │
              ▼                     ▼
      Detect environment      Run pytest
              │
              ▼
      Install dependencies
              │
              ▼
       Execute script.py
```

For explicit command-line applications:

```text
pip install reqora
        │
        ▼
reqora run uvicorn app.main:app
        │
        ▼
Check executable
        │
        ├── Available
        │      │
        │      ▼
        │   Execute
        │
        └── Missing
               │
               ▼
        Resolve PyPI package
               │
               ▼
        Install dependency
               │
               ▼
             Execute
```

---

# Design Principle

Reqora follows a simple principle:

> **Analyze first, provision dependencies second, and execute only when execution is explicitly requested.**

This provides a predictable CLI while still allowing automatic dependency provisioning.

The three major responsibilities are therefore:

```text
        ┌────────────────────────────┐
        │  1. Dependency Discovery   │
        └─────────────┬──────────────┘
                      │
                      ▼
        ┌────────────────────────────┐
        │  2. Dependency Provision   │
        └─────────────┬──────────────┘
                      │
                      ▼
        ┌────────────────────────────┐
        │  3. Requested Execution    │
        └────────────────────────────┘
```

Reqora is intended to make Python execution dependency-aware without requiring developers to manually maintain a separate static dependency declaration for every runtime scenario.