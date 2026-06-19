# Quick Start

## 1. Install

**One-click (Windows):**
```bat
install.bat
```
This creates a `.venv`, installs PsychoPy + this package, and registers the MCP
server with Claude Code.

**Manual:**
```bash
python -m venv .venv
.venv\Scripts\python -m pip install -e .
.venv\Scripts\python -m psychopy_mcp.cli configure-claude
```

## 2. Open in Claude Code

The repo ships a `.mcp.json`, so launching Claude Code in this folder loads the
`psychopy` server automatically. Confirm with:

> "调用 env_info 看看 PsychoPy 环境"

## 3. Run a literature-grounded experiment

> "列出所有范式" → `list_paradigms`
> "用 stroop 范式生成一个实验并运行" → `scaffold_paradigm("stroop","exp1")` + `run_experiment`
> "读一下刚才的数据" → `read_data`

Or open the GUI launcher:

> "打开实验启动器" → `launch_gui`
or `.venv\Scripts\python -m psychopy_mcp.cli gui`

## 4. Make your own paradigm

In the launcher click **＋ 新建自定义范式**, or ask Claude:

> "创建一个自定义范式：呈现 HAPPY/SAD 两个词，按 f/j 反应"
→ `create_custom_paradigm(...)`

It then behaves like any built-in paradigm (`list_paradigms` → `scaffold_paradigm`).

## Notes
- PsychoPy is GUI-based: running an experiment opens a real window (not headless).
- The server + each experiment use `.venv` (Python 3.10 + PsychoPy). First import
  takes ~1–2 minutes.
