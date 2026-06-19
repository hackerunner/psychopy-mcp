# PsychoPy MCP

![license](https://img.shields.io/badge/license-MIT-green)
![python](https://img.shields.io/badge/python-3.10%2B-blue)
![platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![MCP](https://img.shields.io/badge/protocol-MCP-purple)
![paradigms](https://img.shields.io/badge/paradigms-14%20literature--grounded-orange)

让 **Claude Code / Codex 直接操作并接管 PsychoPy** 的 MCP 服务器 —— 用自然语言设计、运行、读取心理学实验，且**自动遵循前人文献的范式参数**。

Claude/Codex 用自己的文件工具读写实验脚本（`.py`）；本服务器提供这些工具**做不到**的 PsychoPy 专属能力：内省、静态校验、运行实验、编译 Builder 文件、驱动常驻交互窗口，以及一套**文献校准的经典范式库**。

> 快速上手见 [QUICK_START.md](QUICK_START.md)，工具清单见 [TOOLS_REFERENCE.md](TOOLS_REFERENCE.md)。

## 演示 Demo

一句话「用 Stroop 范式跑个实验再分析」即可走完：**生成（文献校准）→ 运行（真实开窗）→ 自动分析出图**。

| 刺激呈现（不一致试次：蓝色墨水的"RED"） | 自动分析（Stroop 效应 = 131 ms） |
|:--:|:--:|
| ![stimulus](docs/stroop_stimulus.png) | ![analysis](docs/stroop_analysis.png) |

## 架构

```
Claude Code / Codex
      │  (MCP / stdio JSON-RPC)
      ▼
  psychopy_mcp/server.py  ──FastMCP──┐
      │                              │ subprocess (psychopy venv)
      │   paradigms/  (引擎+15范式)   ├── run_experiment   → 运行 *.py 实验
      │   runner/     (常驻窗口)      ├── scaffold_paradigm → 生成文献校准实验
      │   analysis/web (分析/网页)    └── validate / compile / live
      ▼
 .venv (Python 3.10 + PsychoPy 2026.1.3)
```

- **psychopy_mcp/server.py** —— MCP 服务器（FastMCP），暴露全部 21 个工具。
- **psychopy_mcp/paradigms/** —— 文献校准范式库：共享 `engine.py`（phase 引擎）+ 每范式一个模块（`SPEC` + `build_trials`）+ `custom.py`（对话式自定义范式）。
- **psychopy_mcp/runner/live_session.py** —— 常驻子进程，持有 PsychoPy `Window`，按行收发 JSON，实现"实时接管"。
- **workspace/** —— 脚手架/运行/数据的默认工作目录（相对路径解析到这里）。

## 工具一览

| 分组 | 工具 | 作用 |
|------|------|------|
| 内省 | `env_info` | 报告解释器/版本/安装路径，先调它确认环境连通 |
| 内省 | `list_components` | 列出可用的 visual 刺激类与 Builder 组件 |
| 内省 | `api_help` | 返回任意 PsychoPy 符号的签名+文档（如 `visual.TextStim`）|
| **范式** | `list_paradigms` | 列出内置的「文献校准」经典范式 |
| **范式** | `get_paradigm` | 返回某范式的完整规范（设计/固定的字号位置/时序/引用）|
| **范式** | `scaffold_paradigm` | 按文献规范生成可运行实验脚本（各条件字号/位置一致，杜绝 NL 自由发挥导致的偏差）|
| **范式** | `create_custom_paradigm` | 对话式定义并保存自定义范式（之后像内置范式一样用）|
| 创作 | `scaffold_experiment` | 从模板生成 coder/builder 起始文件 |
| 创作 | `validate_script` | 静态检查：语法 + import 解析（不运行、不开窗）|
| 执行 | `run_experiment` | 以子进程运行实验，捕获 stdout/stderr + 新增数据文件 |
| 执行 | `list_data` / `read_data` | 列出/读取 csv/tsv/log/psydat/xlsx 数据 |
| **分析** | `analyze_data` | 算范式的标准效应（Stroop效应/搜索斜率/SSRT/d′/ANT网络分等）+ 出图 |
| **联动** | `export_for_spss` | 导出 SPSS 可直接导入的整洁/聚合 CSV（配合 SPSS-MCP 一站式统计）|
| **网页** | `export_web` | 把范式导出成 Builder `.psyexp` + PsychoJS `.js`，上 Pavlovia 做线上实验 |
| Builder | `read_psyexp` | 把 `.psyexp` 解析成结构化摘要（flow/routines/params）|
| Builder | `compile_psyexp` | 把 `.psyexp` 编译成可运行的 `.py` |
| 实时接管 | `live_start` | 打开常驻窗口 |
| 实时接管 | `live_cmd` | 发命令：present_text/image/shape、flip、wait_keys、screenshot、exec、info |
| 实时接管 | `live_status` / `live_stop` | 查询/关闭常驻窗口 |

## 安装

**一键（Windows）：**
```bat
install.bat
```
创建 `.venv`、安装 PsychoPy + 本包、并自动注册到 Claude Code。

**手动：**
```bash
python -m venv .venv
.venv\Scripts\python -m pip install -e .
.venv\Scripts\python -m psychopy_mcp.cli configure-claude
```

项目自带 `.mcp.json`（用 `python -m psychopy_mcp.server` 启动），在本目录打开 Claude Code 即自动加载。Codex 用同样的 command/args 即可。CLI 还提供 `psychopy-mcp serve|list|configure-claude`。

## 典型工作流

**批处理实验（最常用）**
```
env_info()                              # 1. 确认环境
scaffold_experiment("stroop")           # 2. 生成 workspace/stroop.py
   …用文件工具编辑 stroop.py…
validate_script("stroop.py")            # 3. 静态校验
run_experiment("stroop.py")             # 4. 运行（开窗）并收数据
list_data() / read_data("data/xxx.csv") # 5. 看结果
```

**实时接管窗口（边做边看）**
```
live_start(size=[1024,768])
live_cmd("present_text", {"text":"Hello", "wait_keys":["space"]})
live_cmd("present_shape", {"shape":"circle", "size":0.3, "fillColor":"red"})
live_cmd("screenshot", {"filename":"shot.png"})
live_stop()
```

**Builder 文件**
```
read_psyexp("templates/experiment.psyexp")   # 看结构
compile_psyexp("templates/experiment.psyexp") # 编译成 .py 再 run_experiment
```

## 文献校准（关键设计）

自然语言搭建实验最大的隐患：模型每次会**自己瞎编**字号、刺激位置、时序、配色，导致和已发表范式不可比。`paradigms/` 把经典范式的**规范参数**固化下来（含引用），所有条件**共享同一套字号与居中位置**——拥挤/不一致这类错误从根上不可能出现。

```
list_paradigms()                    # 看 14 个校准范式
get_paradigm("stroop")              # 看完整规范 + 引用(Stroop 1935; MacLeod 1991)
scaffold_paradigm("stroop", "exp1") # 生成 144 试次平衡版(con=incon=neutral=48)
scaffold_paradigm("nback", "wm1", {"n": 3})   # 可传参数覆盖默认
```

所有范式都跑在共享的 **phase 引擎**（`paradigms/engine.py`）上：每个范式 = 一串 trial，每个 trial = 一串 phase（注视/线索/刺激/反应）。字号、位置、配色统一来自该范式的 `SPEC`，**结构上保证各条件一致**。

| key | 范式 | 关键引用 | 默认试次 |
|-----|------|---------|---------|
| `stroop` | Colour–Word Stroop | Stroop 1935; MacLeod 1991 | 144 |
| `flanker` | Eriksen Flanker | Eriksen & Eriksen 1974 | 240 |
| `simon` | Simon | Simon & Rudell 1967 | 160 |
| `gonogo` | Go/No-Go | Wessel 2018 | 100 |
| `posner` | Posner 空间线索 | Posner 1980 | 40 |
| `stopsignal` | 停止信号(SSRT, 自适应阶梯) | Logan & Cowan 1984; Verbruggen 2019 | 128 |
| `ant` | 注意网络测验 ANT | Fan et al. 2002 | 48–96 |
| `nback` | N-back 工作记忆 | Kirchner 1958; Owen 2005 | 30 |
| `sternberg` | Sternberg 记忆扫描 | Sternberg 1966 | 40 |
| `visualsearch` | 视觉搜索(特征/合取) | Treisman & Gelade 1980 | 60 |
| `taskswitch` | 线索化任务切换 | Meiran 1996; Monsell 2003 | 64 |
| `lexdecision` | 词汇判断 | Meyer & Schvaneveldt 1971 | 144 |
| `mentalrotation` | 心理旋转(2D 字符变体) | Shepard & Metzler 1971 | 80 |
| `dotprobe` | 点探测(注意偏向) | MacLeod, Mathews & Tata 1986 | 48 |

> 词汇判断/点探测内置的是小词表，正式研究请替换为 SUBTLEX/ELP 等规范词库；心理旋转默认用 2D 字符变体，需要原版 3D 立方体图请放入图片素材并把刺激改为 `kind="image"`。

## 线上实验（Pavlovia / PsychoJS）

只有 Builder `.psyexp` 能自动转成 JavaScript 在浏览器跑（纯 Coder 脚本不行）。`export_web` 帮你把范式导出成 `.psyexp` + `.js` + 条件文件：

```
export_web("stroop")   # → workspace/web_stroop/{*.psyexp, *.js, *_conditions.csv}
```
把该文件夹上传到 [Pavlovia](https://pavlovia.org)（或在 PsychoPy Builder 里 Sync）即可招募线上被试。
> 目前支持「单文字刺激 + 按键」类范式（Stroop / Flanker / 词汇判断 / 文字类自定义）；含图形/多阶段的范式（Posner/ANT/Simon 等）暂为桌面端。

## 与 SPSS-MCP 联动（设计→运行→统计 一条龙）

本服务器负责**采数据**，[SPSS-MCP](https://github.com/Exekiel179/SPSS-MCP) 负责**做统计**，靠 CSV 衔接。在同一个 Claude 会话里同时配置两个 MCP：

```
run_experiment("stroop_exp.py")          # 1. 采数据
export_for_spss("data/xxx.csv", aggregate=True)  # 2. 导出 SPSS 可读 CSV
   → 让 SPSS-MCP 导入该 CSV，对 rt_ms 按 condition 跑重复测量 ANOVA   # 3. 出统计
```

## 实验文件与数据在哪里

| 内容 | 位置 |
|------|------|
| 生成的实验脚本 | `workspace/<名字>.py`（如 `workspace/lie_experiment.py`）|
| **运行产生的数据** | `workspace/data/`：`*.csv`(每试次一行)、`*.psydat`、`*_1.csv`(宽格式)、`*_analysis.png`(分析图) |
| 自定义范式 | `custom_paradigms/<名字>.json` |
| 网页导出 | `workspace/<名字>/`（`.psyexp` + `.js` + `conditions.csv`）|

> `workspace/` 和数据**默认不纳入 git**（见 `.gitignore`）——它们是你本机的实验产物。
> 想换存放根目录，设环境变量 `PSYCHOPY_MCP_HOME` 即可。

## 说明 / 限制

- **不是 headless**：PsychoPy 基于 GUI，Windows 上运行实验会真实开窗。在带屏幕（或虚拟显示）的机器上跑。
- **venv 隔离**：服务器与实验都用 `.venv\Scripts\python.exe`（Python 3.10 + PsychoPy 2026.1.3），不污染系统环境。
- **`live_cmd exec` 是逃生舱**：可在窗口进程内执行任意 PsychoPy 代码（作用域含 `win, visual, core, event`），灵活但需自负其责。
- 一次只允许一个 live 会话；再开需先 `live_stop`。
