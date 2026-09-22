TraceReq source project
        │
        │ python -m build
        ▼
dist/
 ├── auto_req-0.1.2-py3-none-any.whl   ← reusable package
 └── auto_req-0.1.2.tar.gz
        │
        │ pip install
        ▼
Any Python project
 ├── .venv/
 ├── tests/
 ├── src/
 └── ...
        │
        └── auto-req command