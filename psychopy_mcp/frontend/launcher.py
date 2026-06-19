"""psychopy-mcp launcher — a simple desktop frontend.

Pick a literature-grounded paradigm, set participant/options, and Generate or
Generate & Run it. Or build your own paradigm with the "New custom paradigm"
form. Runs experiments as subprocesses so the launcher stays open.

Start it with the project's venv python:
    .venv\\Scripts\\python.exe frontend\\launcher.py
(or via the MCP tool `launch_gui`).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]   # project root (above the package)
sys.path.insert(0, str(ROOT))

import tkinter as tk
from tkinter import messagebox, ttk

from psychopy_mcp import paradigms
from psychopy_mcp.paradigms import custom as customlib
from psychopy_mcp.paths import WORKSPACE

WORKSPACE.mkdir(parents=True, exist_ok=True)


def _scaffold(key: str, name: str, opts: dict) -> Path:
    src = paradigms.generate_script(key, name, opts)
    dest = WORKSPACE / f"{name}.py"
    dest.write_text(src, encoding="utf-8")
    return dest


class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("psychopy-mcp · 实验范式启动器")
        self.geometry("820x560")
        self._build()
        self._refresh()

    # ── layout ──────────────────────────────────────────────
    def _build(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill="both", expand=True)

        left = ttk.Frame(top)
        left.pack(side="left", fill="y")
        ttk.Label(left, text="范式 Paradigms", font=("", 11, "bold")).pack(anchor="w")
        self.listbox = tk.Listbox(left, width=28, height=24)
        self.listbox.pack(fill="y", expand=True)
        self.listbox.bind("<<ListboxSelect>>", lambda e: self._on_select())
        ttk.Button(left, text="↻ 刷新", command=self._refresh).pack(fill="x", pady=2)
        ttk.Button(left, text="＋ 新建自定义范式",
                   command=self._open_custom_editor).pack(fill="x", pady=2)

        right = ttk.Frame(top, padding=(12, 0))
        right.pack(side="left", fill="both", expand=True)
        self.title_lbl = ttk.Label(right, text="", font=("", 13, "bold"))
        self.title_lbl.pack(anchor="w")
        self.detail = tk.Text(right, height=16, wrap="word", relief="flat",
                              bg=self.cget("bg"))
        self.detail.pack(fill="both", expand=True, pady=6)

        form = ttk.Frame(right)
        form.pack(fill="x")
        ttk.Label(form, text="被试编号").grid(row=0, column=0, sticky="w")
        self.participant = ttk.Entry(form, width=10)
        self.participant.insert(0, "001")
        self.participant.grid(row=0, column=1, padx=6)
        ttk.Label(form, text="reps (留空=默认)").grid(row=0, column=2, sticky="w")
        self.reps = ttk.Entry(form, width=8)
        self.reps.grid(row=0, column=3, padx=6)

        btns = ttk.Frame(right)
        btns.pack(fill="x", pady=10)
        ttk.Button(btns, text="生成脚本", command=lambda: self._go(run=False)).pack(side="left")
        ttk.Button(btns, text="生成并运行 ▶", command=lambda: self._go(run=True)).pack(side="left", padx=8)
        self.status = ttk.Label(right, text="", foreground="green")
        self.status.pack(anchor="w")

    # ── data ────────────────────────────────────────────────
    def _refresh(self):
        self.items = paradigms.list_paradigms()
        self.listbox.delete(0, "end")
        for p in self.items:
            tag = "" if p.get("builtin") else "  [自定义]"
            self.listbox.insert("end", f"{p.get('key','?')}{tag}")
        if self.items:
            self.listbox.selection_set(0)
            self._on_select()

    def _current(self):
        sel = self.listbox.curselection()
        return self.items[sel[0]] if sel else None

    def _on_select(self):
        p = self._current()
        if not p:
            return
        spec = paradigms.get_paradigm(p["key"]) or {}
        self.title_lbl.config(text=f"{p['key']} — {spec.get('name','')}")
        self.detail.delete("1.0", "end")
        lines = [spec.get("summary", ""), ""]
        if spec.get("task"):
            lines += [f"任务: {spec['task']}", ""]
        if spec.get("conditions"):
            lines += [f"条件: {', '.join(map(str, spec['conditions']))}"]
        if spec.get("condition_balance"):
            lines += [f"平衡: {spec['condition_balance']}", ""]
        for r in spec.get("references", []):
            lines.append("· " + r)
        self.detail.insert("1.0", "\n".join(lines))

    def _opts(self):
        opts = {}
        if self.reps.get().strip():
            try:
                opts["reps"] = int(self.reps.get().strip())
            except ValueError:
                pass
        return opts

    def _go(self, run: bool):
        p = self._current()
        if not p:
            return
        name = f"{p['key']}_{self.participant.get().strip() or '001'}"
        try:
            dest = _scaffold(p["key"], name, self._opts())
        except Exception as e:
            messagebox.showerror("生成失败", repr(e))
            return
        if run:
            subprocess.Popen([sys.executable, str(dest)], cwd=str(WORKSPACE))
            self.status.config(text=f"已运行: {dest.name}（窗口加载中…）")
        else:
            self.status.config(text=f"已生成: {dest}")

    # ── custom paradigm editor ──────────────────────────────
    def _open_custom_editor(self):
        CustomEditor(self, on_save=self._refresh)


class CustomEditor(tk.Toplevel):
    """Minimal form to define a simple choice-RT custom paradigm."""

    def __init__(self, master, on_save):
        super().__init__(master)
        self.title("新建自定义范式")
        self.geometry("640x520")
        self.on_save = on_save
        f = ttk.Frame(self, padding=10)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="范式名").grid(row=0, column=0, sticky="w")
        self.name = ttk.Entry(f, width=30)
        self.name.grid(row=0, column=1, columnspan=3, sticky="w", pady=2)

        ttk.Label(f, text="反应键映射 (label=key, 逗号分隔)").grid(row=1, column=0, columnspan=2, sticky="w")
        self.mapping = ttk.Entry(f, width=40)
        self.mapping.insert(0, "left=f, right=j")
        self.mapping.grid(row=1, column=2, columnspan=2, sticky="w", pady=2)

        ttk.Label(f, text="每条件重复次数 reps").grid(row=2, column=0, sticky="w")
        self.reps = ttk.Entry(f, width=8)
        self.reps.insert(0, "10")
        self.reps.grid(row=2, column=1, sticky="w", pady=2)

        ttk.Label(f, text="试次项 (每行: 文字 | 颜色 | 条件 | 正确键)",
                  font=("", 10, "bold")).grid(row=3, column=0, columnspan=4, sticky="w", pady=(8, 0))
        self.items = tk.Text(f, height=12, width=70)
        self.items.insert("1.0",
                          "LEFT | white | A | f\nRIGHT | white | B | j")
        self.items.grid(row=4, column=0, columnspan=4, sticky="we", pady=4)

        ttk.Button(f, text="保存", command=self._save).grid(row=5, column=0, pady=8)
        ttk.Button(f, text="取消", command=self.destroy).grid(row=5, column=1, sticky="w")

    def _save(self):
        name = self.name.get().strip()
        if not name:
            messagebox.showerror("缺少范式名", "请填写范式名")
            return
        spec = customlib.create_template(name)
        # response mapping
        mp = {}
        for pair in self.mapping.get().split(","):
            if "=" in pair:
                lab, key = pair.split("=", 1)
                mp[lab.strip()] = key.strip()
        spec["responses"]["mapping"] = mp or {"resp": "space"}
        try:
            spec["reps"] = int(self.reps.get().strip() or "10")
        except ValueError:
            spec["reps"] = 10
        # items
        items = []
        for line in self.items.get("1.0", "end").strip().splitlines():
            parts = [c.strip() for c in line.split("|")]
            if not parts or not parts[0]:
                continue
            text = parts[0]
            color = parts[1] if len(parts) > 1 and parts[1] else "white"
            cond = parts[2] if len(parts) > 2 and parts[2] else "default"
            ck = parts[3] if len(parts) > 3 and parts[3] else None
            it = {"text": text, "color": color, "condition": cond}
            if ck:
                it["correct_key"] = ck
            items.append(it)
        spec["items"] = items
        errs = customlib.validate(spec)
        if errs:
            messagebox.showerror("校验失败", "\n".join(errs))
            return
        path = customlib.save(spec, paradigms.CUSTOM_DIR)
        messagebox.showinfo("已保存", f"自定义范式已保存:\n{path}")
        self.on_save()
        self.destroy()


if __name__ == "__main__":
    Launcher().mainloop()
