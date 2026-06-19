"""Command-line entry point for psychopy-mcp.

    psychopy-mcp serve              # run the MCP server (stdio)
    psychopy-mcp gui                # open the desktop launcher
    psychopy-mcp configure-claude   # add this server to Claude Code's config
    psychopy-mcp list               # list available paradigms

`configure-claude` detects this interpreter and writes an mcpServers entry into
the user's Claude Code config so the server is available in every session.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _claude_config_path() -> Path:
    return Path.home() / ".claude.json"


def configure_claude() -> int:
    from psychopy_mcp.paths import PROJECT_ROOT
    cfg_path = _claude_config_path()
    py = sys.executable                       # the interpreter running this CLI
    # include PYTHONPATH so the server is importable from any working directory
    # (the venv is created with uv and has no pip-installed package).
    entry = {
        "command": py,
        "args": ["-m", "psychopy_mcp.server"],
        "env": {"PYTHONPATH": str(PROJECT_ROOT)},
    }
    cfg = {}
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            print(f"! could not parse {cfg_path}; writing a fresh mcpServers block")
    cfg.setdefault("mcpServers", {})
    cfg["mcpServers"]["psychopy"] = entry
    cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    print(f"[OK] configured Claude Code MCP server 'psychopy' -> {py} -m psychopy_mcp.server")
    print(f"     ({cfg_path})")
    return 0


def serve() -> int:
    from psychopy_mcp.server import mcp
    mcp.run()
    return 0


def gui() -> int:
    from psychopy_mcp.paths import LAUNCHER
    return subprocess.call([sys.executable, str(LAUNCHER)])


def list_paradigms() -> int:
    from psychopy_mcp import paradigms
    for p in paradigms.list_paradigms():
        tag = "" if p.get("builtin") else " [custom]"
        print(f"  {p.get('key',''):16s}{tag} {p.get('name', p.get('error',''))}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="psychopy-mcp", description=__doc__)
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("serve", help="run the MCP server (stdio)")
    sub.add_parser("gui", help="open the desktop launcher")
    sub.add_parser("configure-claude", help="add this server to Claude Code config")
    sub.add_parser("list", help="list available paradigms")
    args = ap.parse_args(argv)

    if args.cmd in (None, "serve"):
        return serve()
    if args.cmd == "gui":
        return gui()
    if args.cmd == "configure-claude":
        return configure_claude()
    if args.cmd == "list":
        return list_paradigms()
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
