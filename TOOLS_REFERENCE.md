# Tools Reference

19 MCP tools, grouped. Relative paths resolve under `workspace/`.

## Introspection
| Tool | Args | Returns |
|------|------|---------|
| `env_info` | – | interpreter, PsychoPy version/path, workspace |
| `list_components` | `query?` | visual stimulus classes + Builder components |
| `api_help` | `symbol` | signature + docstring of a PsychoPy symbol |

## Paradigms (literature-grounded)
| Tool | Args | Returns |
|------|------|---------|
| `list_paradigms` | – | all built-in + custom paradigms (key/name/summary) |
| `get_paradigm` | `key` | full spec: design, fixed surface params, timing, refs |
| `scaffold_paradigm` | `key, name, opts?` | generates a runnable experiment script |
| `create_custom_paradigm` | `name, items, mapping, reps?, …` | saves a custom paradigm |
| `launch_gui` | – | opens the desktop launcher |

Built-in keys: `stroop, flanker, simon, gonogo, posner, stopsignal, ant, nback,
sternberg, visualsearch, taskswitch, lexdecision, mentalrotation, dotprobe`.

## Authoring
| Tool | Args | Returns |
|------|------|---------|
| `scaffold_experiment` | `name, kind` | blank coder/builder starter file |
| `validate_script` | `path` | syntax + import check (no window opens) |

## Execution
| Tool | Args | Returns |
|------|------|---------|
| `run_experiment` | `path, args?, timeout?, cwd?` | runs the script, captures output + new data files |
| `list_data` | `folder?` | csv/tsv/log/psydat/xlsx files |
| `read_data` | `path, max_rows?` | parsed table / psydat / log preview |

## Builder (.psyexp)
| Tool | Args | Returns |
|------|------|---------|
| `read_psyexp` | `path` | structured flow + routines + params |
| `compile_psyexp` | `path, out?` | compiles Builder file to a runnable .py |

## Live control (interactive window)
| Tool | Args | Returns |
|------|------|---------|
| `live_start` | `fullscreen?, size?, color?, units?` | opens a persistent window |
| `live_cmd` | `command, params?` | present_text/image/shape, flip, wait_keys, screenshot, exec, info |
| `live_status` | – | whether a live session is running |
| `live_stop` | – | closes the live window |

## Typical chains
- **Batch study:** `env_info` → `scaffold_paradigm` → `run_experiment` → `read_data`
- **Custom:** `create_custom_paradigm` → `scaffold_paradigm` → `run_experiment`
- **Pilot a stimulus:** `live_start` → `live_cmd` … → `live_stop`
