"""Persistent PsychoPy live session.

Run by the MCP server as a subprocess. Holds an open Window on the main thread
and processes one JSON command per line from stdin, replying with exactly one
JSON line on stdout. All diagnostic text goes to stderr so stdout stays a clean
JSON channel.

Protocol (request -> response), one JSON object per line:
  {"cmd": "init", "params": {fullscreen,size,color,units}} -> {"ok":true, ...}
  {"cmd": "present_text", "params": {text,color,pos,height,wait_keys,max_wait}}
  {"cmd": "present_image", "params": {image,size,pos,wait_keys,max_wait}}
  {"cmd": "present_shape", "params": {shape,size,pos,color,fillColor,wait_keys,max_wait}}
  {"cmd": "flip"}            -> {"ok":true}
  {"cmd": "clear"}           -> {"ok":true}
  {"cmd": "wait_keys", "params": {keys,max_wait}} -> {"key":..,"rt":..}
  {"cmd": "screenshot", "params": {filename}}     -> {"path":..}
  {"cmd": "exec", "params": {code}}               -> {"ok":true,"result":..}
  {"cmd": "info"}            -> window info
  {"cmd": "quit"}            -> {"ok":true}; process exits
"""
import json
import sys
import traceback


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def reply(obj):
    sys.stdout.write(json.dumps(obj, default=str) + "\n")
    sys.stdout.flush()


def main():
    from psychopy import visual, core, event

    win = None
    # namespace exposed to the `exec` escape hatch
    ns = {"visual": visual, "core": core, "event": event}

    def draw_and_present(stim, params):
        stim.draw()
        win.flip()
        wk = params.get("wait_keys", None)
        if wk is not None or params.get("max_wait") is not None:
            keys = wk if isinstance(wk, list) else None
            clock = core.Clock()
            pressed = event.waitKeys(
                maxWait=params.get("max_wait", float("inf")),
                keyList=keys, timeStamped=clock,
            )
            if pressed:
                k, rt = pressed[0]
                return {"ok": True, "key": k, "rt": rt}
            return {"ok": True, "key": None, "rt": None, "timed_out": True}
        return {"ok": True}

    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            msg = json.loads(raw)
        except Exception as e:
            reply({"error": f"bad json: {e!r}"})
            continue
        cmd = msg.get("cmd")
        p = msg.get("params", {}) or {}

        try:
            if cmd == "init":
                win = visual.Window(
                    size=p.get("size", [1024, 768]),
                    fullscr=p.get("fullscreen", False),
                    color=p.get("color", "gray"),
                    units=p.get("units", "height"),
                    allowGUI=True,
                )
                ns["win"] = win
                reply({"ok": True, "fps": round(win.getActualFrameRate() or 0, 1),
                       "size": list(win.size)})

            elif win is None:
                reply({"error": "window not initialized; send init first"})

            elif cmd == "present_text":
                stim = visual.TextStim(
                    win, text=p.get("text", ""), color=p.get("color", "white"),
                    pos=p.get("pos", [0, 0]), height=p.get("height", 0.08),
                )
                reply(draw_and_present(stim, p))

            elif cmd == "present_image":
                stim = visual.ImageStim(
                    win, image=p.get("image"), pos=p.get("pos", [0, 0]),
                    size=p.get("size"),
                )
                reply(draw_and_present(stim, p))

            elif cmd == "present_shape":
                shape = p.get("shape", "rect")
                common = dict(
                    pos=p.get("pos", [0, 0]),
                    lineColor=p.get("color", "white"),
                    fillColor=p.get("fillColor", None),
                )
                size = p.get("size", 0.2)
                if shape == "circle":
                    stim = visual.Circle(win, radius=size if isinstance(size, (int, float))
                                         else size[0], **common)
                elif shape == "line":
                    stim = visual.Line(win, start=p.get("start", [-0.2, 0]),
                                       end=p.get("end", [0.2, 0]),
                                       lineColor=p.get("color", "white"))
                elif shape == "polygon":
                    stim = visual.Polygon(win, edges=p.get("edges", 5),
                                          radius=size if isinstance(size, (int, float))
                                          else size[0], **common)
                else:  # rect
                    stim = visual.Rect(win, width=size[0] if isinstance(size, list) else size,
                                       height=size[1] if isinstance(size, list) else size,
                                       **common)
                reply(draw_and_present(stim, p))

            elif cmd == "flip":
                win.flip()
                reply({"ok": True})

            elif cmd == "clear":
                win.flip()
                reply({"ok": True})

            elif cmd == "wait_keys":
                keys = p.get("keys")
                clock = core.Clock()
                pressed = event.waitKeys(
                    maxWait=p.get("max_wait", float("inf")),
                    keyList=keys if isinstance(keys, list) else None,
                    timeStamped=clock,
                )
                if pressed:
                    k, rt = pressed[0]
                    reply({"ok": True, "key": k, "rt": rt})
                else:
                    reply({"ok": True, "key": None, "rt": None, "timed_out": True})

            elif cmd == "screenshot":
                fn = p.get("filename", "live_screenshot.png")
                win.getMovieFrame()
                win.saveMovieFrames(fn)
                reply({"ok": True, "path": fn})

            elif cmd == "exec":
                code = p.get("code", "")
                local: dict = {}
                exec(code, ns, local)  # noqa: S102 - intentional escape hatch
                reply({"ok": True, "result": local.get("result")})

            elif cmd == "info":
                reply({"ok": True, "size": list(win.size),
                       "units": win.units, "color": list(win.color)})

            elif cmd == "quit":
                reply({"ok": True})
                try:
                    win.close()
                except Exception:
                    pass
                core.quit()
                return

            else:
                reply({"error": f"unknown cmd: {cmd}"})

        except Exception as e:
            reply({"error": repr(e), "traceback": traceback.format_exc()[-2000:]})


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("live_session fatal:", e)
        reply({"error": f"fatal: {e!r}", "traceback": traceback.format_exc()[-2000:]})
