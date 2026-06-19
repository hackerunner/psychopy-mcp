@echo off
REM psychopy-mcp installer (Windows)
setlocal
cd /d "%~dp0"

echo ==> Creating virtual environment (.venv)...
python -m venv .venv || goto :err

echo ==> Upgrading pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip || goto :err

echo ==> Installing psychopy-mcp (this pulls in PsychoPy; may take a while)...
".venv\Scripts\python.exe" -m pip install -e . || goto :err

echo ==> Registering MCP server with Claude Code...
".venv\Scripts\python.exe" -m psychopy_mcp.cli configure-claude || goto :err

echo.
echo Done. Open Claude Code in this folder, or run:
echo     .venv\Scripts\python -m psychopy_mcp.cli gui
goto :eof

:err
echo Installation failed. See the message above.
exit /b 1
