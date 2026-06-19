"""Shared path resolution for psychopy-mcp.

Code lives in this package; runtime data (workspace, custom paradigms) lives at
the project root by default, or wherever PSYCHOPY_MCP_HOME points.
"""
from __future__ import annotations

import os
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent              # .../psychopy_mcp
PROJECT_ROOT = Path(os.environ.get("PSYCHOPY_MCP_HOME", str(PKG_DIR.parent)))

WORKSPACE = PROJECT_ROOT / "workspace"
CUSTOM_DIR = PROJECT_ROOT / "custom_paradigms"
TEMPLATES = PKG_DIR / "templates"
LIVE_SCRIPT = PKG_DIR / "runner" / "live_session.py"
LAUNCHER = PKG_DIR / "frontend" / "launcher.py"
VENV_PY = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
