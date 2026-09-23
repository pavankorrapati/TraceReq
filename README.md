# Reqora

**Reqora** is an AST-driven Python dependency discovery, resolution, and runtime provisioning engine.

It analyzes the Python file you want to execute, discovers its imported dependencies, recursively follows reachable local project imports, identifies third-party dependencies, maps Python import names to their corresponding PyPI packages, detects the appropriate Python environment, and installs missing dependencies automatically.

Reqora is designed to reduce the need to manually maintain a static `requirements.txt` file for every runtime scenario.

---

## How it works

```text
Reqora source project

        │
        │ python -m build
        ▼
dist/

 ├── reqora-0.1.0-py3-none-any.whl
 │       ← reusable Python package
 │
 └── reqora-0.1.0.tar.gz

        │
        │ pip install reqora
        ▼

Any Python project

 ├── .venv/
 ├── tests/
 ├── src/
 ├── main.py
 ├── script.py
 └── ...

        │
        │ reqora script.py
        ▼

Dependency Analysis

        │
        ├── Analyze script.py
        │
        ├── Find local imports
        │
        ├── Recursively analyze reachable
        │   local dependency files
        │
        ├── Detect standard-library
        │   dependencies
        │
        ├── Detect third-party
        │   dependencies
        │
        ├── Map import names
        │   → PyPI package names
        │
        ├── Detect the project's
        │   appropriate virtual environment
        │
        └── Install missing dependencies
```

---

## Installation

Install Reqora from PyPI:

```powershell
pip install reqora
```

After installation, the `reqora` command is available.

```powershell
reqora script.py
```

Reqora analyzes the target Python application, resolves the required external packages, installs missing dependencies into the appropriate environment, and then proceeds with execution.

---

## Example

Suppose your project contains:

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
├── services/
│   ├── __init__.py
│   └── api.py
└── utils/
    └── helpers.py
```

### `script.py`

```python
from main import run_application
```

### `main.py`

```python
from services.api import get_data
from utils.helpers import process_data
```

### `services/api.py`

```python
import requests
import yaml
```

### `utils/helpers.py`

```python
import json
import os
```

Run:

```powershell
reqora script.py
```

Reqora recursively analyzes the reachable local modules:

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

It understands that:

```text
script.py
main.py
services/api.py
utils/helpers.py
```

are local project files and should **not** be installed from PyPI.

It also recognizes:

```text
json
os
```

as Python standard-library modules.

The external dependencies requiring package resolution are therefore:

```text
requests
yaml
```

which are mapped to their corresponding PyPI distributions:

```text
requests → requests
yaml     → PyYAML
```

Missing packages can then be installed into the detected Python environment.

---

## Recursive dependency analysis

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

Starting with:

```powershell
reqora script.py
```

the dependency analyzer follows reachable local Python modules and builds the dependency graph.

This makes Reqora suitable for projects containing:

* Framework-based architectures
* `src/` layouts
* Service layers
* Repository layers
* Utility modules
* Internal Python packages
* Test frameworks
* Nested project modules
* Relative imports
* Package-based application structures

---

## Virtual environment detection

Reqora does not require a virtual environment to have one specific name.

It recognizes conventional names such as:

```text
.venv
venv
env
.env
virtualenv
```

but these names are not required.

For example, environments with names such as:

```text
qa_environment/
automation_env/
python312/
company_python/
my_project_environment/
test_runtime/
anything_you_want/
```

can also be identified when they have the expected Python virtual-environment structure.

On Windows, this may include:

```text
pyvenv.cfg
Scripts/
    python.exe
```

On Linux/macOS:

```text
pyvenv.cfg
bin/
    python
```

An already activated Python environment is also respected.

The objective is to identify the actual Python environment rather than relying exclusively on a hard-coded virtual-environment directory name.

---

## Command

Reqora provides the following command:

```text
reqora
```

Example:

```powershell
reqora script.py
```

The CLI uses:

```text
auto_req.cli:main
```

internally.

The public PyPI distribution name and CLI are:

```text
reqora
```

while the internal Python source package remains:

```text
auto_req
```

This separation allows the public project name to evolve independently from the internal Python package structure.

---

## Project structure

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
├── pyproject.toml
└── ...
```

The Python import package is:

```python
import auto_req
```

The PyPI distribution is:

```text
reqora
```

Install it with:

```powershell
pip install reqora
```

The CLI is:

```powershell
reqora
```

---

## Building the package

From the TraceReq source project:

```powershell
python -m build
```

This generates:

```text
dist/

├── reqora-0.1.0-py3-none-any.whl
└── reqora-0.1.0.tar.gz
```

The wheel is the primary reusable installation artifact.

Install the locally built wheel with:

```powershell
pip install dist\reqora-0.1.0-py3-none-any.whl
```

After installation:

```powershell
reqora script.py
```

---

## Publishing to PyPI

After validating the package:

```powershell
python -m build
```

verify the generated distributions:

```powershell
python -m twine check .\dist\*
```

The generated artifacts can then be uploaded to PyPI using your preferred publishing workflow.

The published distribution name is:

```text
reqora
```

Users can install it with:

```powershell
pip install reqora
```

---

## Goal

The primary goal of Reqora is to make Python project execution dependency-aware without requiring developers to manually maintain a static dependency file for every runtime scenario.

Instead of:

```text
requirements.txt
       │
       ▼
pip install -r requirements.txt
       │
       ▼
run application
```

the workflow becomes:

```text
Python file
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
Detect appropriate Python environment
       │
       ▼
Install missing dependencies
       │
       ▼
Execute the project
```

This allows runtime dependency provisioning to work with both simple Python scripts and larger, framework-based projects.

---

## Intended user experience

The intended user experience is:

```text
pip install reqora

        │
        ▼

┌──────────────────────┐
│        reqora        │
└──────────┬───────────┘
           │
           ▼
       script.py
           │
           ▼
   Analyze local imports
           │
           ▼
   Recursively analyze
   reachable local modules
           │
           ▼
 Identify external imports
           │
           ▼
 Map import → PyPI package
           │
           ▼
 Detect appropriate Python
 environment
           │
           ▼
 Install missing packages
           │
           ▼
      Execute project
```

Reqora is intended to make dependency provisioning part of the execution workflow rather than a separate manual preparation step.

Final Release flow:
TraceReq
   │
   ├── pyproject.toml
   │      name = reqora
   │      version = 0.1.0
   │
   ├── README.md
   │      Reqora documentation
   │
   ▼
python -m build
   │
   ▼
dist/
   ├── reqora-0.1.0-py3-none-any.whl
   └── reqora-0.1.0.tar.gz
   │
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