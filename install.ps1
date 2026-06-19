# psychopy-mcp installer (Windows PowerShell)
# Creates a venv, installs PsychoPy + this package, and registers with Claude Code.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$py = "python"
Write-Host "==> Creating virtual environment (.venv)..."
& $py -m venv .venv

$venvPy = Join-Path $root ".venv\Scripts\python.exe"
Write-Host "==> Upgrading pip..."
& $venvPy -m pip install --upgrade pip

Write-Host "==> Installing psychopy-mcp (this pulls in PsychoPy; may take a while)..."
& $venvPy -m pip install -e .

Write-Host "==> Registering MCP server with Claude Code..."
& $venvPy -m psychopy_mcp.cli configure-claude

Write-Host ""
Write-Host "Done. Open Claude Code in this folder, or run:"
Write-Host "    .venv\Scripts\python -m psychopy_mcp.cli gui"
