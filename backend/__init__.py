"""Blender — Store desktop plugin. Talks to the official Blender Lab MCP add-on.

The add-on (assets/mcp, GPL, vendored untouched) exposes exactly one request
type: ``execute`` Python code that assigns a dict to ``result``. Every tool here
is sugar over that call. Ducky is the MCP server and the LLM client — no
second MCP server, no uvx.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from .connection import DEFAULT_HOST, DEFAULT_PORT, execute
from .deploy_addon import MIN_BLENDER, blender_user_roots, deploy_addon, needs_upgrade_warning

log = logging.getLogger("uefn.plugin.blender")
PLUGIN_ID = "blender"


def _prefs() -> dict[str, Any]:
    try:
        from frontend.ui_web.plugin_host_api import prefs_plugin_get

        return prefs_plugin_get(PLUGIN_ID) or {}
    except Exception:
        return {}


def _host_port() -> tuple[str, int]:
    prefs = _prefs()
    host = str(prefs.get("host") or os.environ.get("BLENDER_HOST") or DEFAULT_HOST).strip() or DEFAULT_HOST
    raw_port = prefs.get("port") or os.environ.get("BLENDER_PORT") or DEFAULT_PORT
    try:
        port = int(str(raw_port).strip())
    except (TypeError, ValueError):
        port = DEFAULT_PORT
    return host, port


def _socket_live() -> tuple[bool, str]:
    """Cheap TCP probe for the Connections menu — no code execution."""
    import socket

    host, port = _host_port()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.3)
    try:
        sock.connect((host, port))
        return True, f"Connected · {host}:{port}"
    except OSError:
        warn = needs_upgrade_warning()
        if warn:
            return False, f"Offline · needs Blender {MIN_BLENDER}+ ({host}:{port})"
        return False, f"Offline · open Blender {MIN_BLENDER}+ ({host}:{port})"
    finally:
        try:
            sock.close()
        except OSError:
            pass


def _execute(code: str, *, strict_json: bool = True) -> dict[str, Any]:
    host, port = _host_port()
    return execute(code, host=host, port=port, strict_json=strict_json)


def _dumps(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=str)


def _scene_object_names() -> list[str] | None:
    """Every object name in the file, or None if Blender could not be asked."""
    try:
        resp = _execute("import bpy\nresult = {'names': [o.name for o in bpy.data.objects]}")
        return [str(n) for n in resp["result"]["names"]]
    except Exception:
        return None


def _delete_objects_code(names: list[str]) -> str:
    lines = ["import bpy"]
    for name in names:
        dumped = json.dumps(name)
        lines.append(f"o = bpy.data.objects.get({dumped})")
        lines.append("if o is not None:")
        lines.append("    bpy.data.objects.remove(o, do_unlink=True)")
    lines.append("result = {'ok': True}")
    return "\n".join(lines)


def _sidecar_for_execute(before: list[str] | None, after: list[str] | None) -> dict[str, Any] | None:
    # No snapshot → no sidecar. A missing "before" would make every object look
    # added and Revert would wipe the scene.
    if before is None or after is None:
        return None
    before_set, after_set = set(before), set(after)
    added = [n for n in after if n not in before_set]
    removed = [n for n in before if n not in after_set]
    if not added and not removed:
        return None
    # Create (or rename Cube → SM_Chair / join temps) is undoable: delete what appeared.
    # Only a pure delete has no inverse.
    if added:
        ident = added[0]
        return {
            "program": PLUGIN_ID,
            "kind": "object",
            "facet": "exists",
            "slot": f"blender://object/{ident}/exists",
            "targets": [{"kind": "object", "id": n, "label": n, "path": n} for n in added],
            "before": {"names": before},
            "inverse": [{"command": "blender_execute_blender_code", "params": {"code": _delete_objects_code(added)}}],
            "created": [{"kind": "object", "id": n, "label": n, "path": n} for n in added],
            "revertable": "auto",
            "reason": "",
            "summary": f"added {', '.join(added[:4])}" + ("…" if len(added) > 4 else ""),
        }
    ident = removed[0]
    return {
        "program": PLUGIN_ID,
        "kind": "object",
        "facet": "exists",
        "slot": f"blender://object/{ident}/exists",
        "targets": [{"kind": "object", "id": ident, "label": ident, "path": ident}],
        "before": {"names": before},
        "inverse": [],
        "created": [],
        "revertable": "manual",
        "reason": "Blender objects were removed; Ducky cannot recreate them",
        "summary": "changed scene objects",
    }


_SCENE_INFO_CODE = """
import bpy
sc = bpy.context.scene
result = {
    "blender": bpy.app.version_string,
    "file": bpy.data.filepath,
    "scene": sc.name,
    "frame": sc.frame_current,
    "mode": bpy.context.mode,
    "active": bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None,
    "selected": [o.name for o in bpy.context.selected_objects],
    "collections": [c.name for c in bpy.data.collections],
    "materials": [m.name for m in bpy.data.materials],
    "object_count": len(bpy.data.objects),
    "objects": [
        {
            "name": o.name,
            "type": o.type,
            "collection": o.users_collection[0].name if o.users_collection else None,
            "location": [round(v, 3) for v in o.location],
            "dimensions": [round(v, 3) for v in o.dimensions],
            "verts": len(o.data.vertices) if o.type == "MESH" else None,
        }
        for o in bpy.data.objects
    ],
}
"""

_OBJECT_INFO_CODE = """
import bpy
ob = bpy.data.objects.get(NAME)
if ob is None:
    raise KeyError("no object " + repr(NAME) + "; have " + repr(sorted(o.name for o in bpy.data.objects)))
info = {
    "name": ob.name, "type": ob.type, "data": ob.data.name if ob.data else None,
    "collections": [c.name for c in ob.users_collection],
    "parent": ob.parent.name if ob.parent else None,
    "location": list(ob.location), "rotation_euler": list(ob.rotation_euler), "scale": list(ob.scale),
    "dimensions": list(ob.dimensions),
    "visible": ob.visible_get(),
    "modifiers": [{"name": m.name, "type": m.type, "show_render": m.show_render} for m in ob.modifiers],
    "materials": [s.material.name if s.material else None for s in ob.material_slots],
}
if ob.type == "MESH":
    me = ob.data
    info["mesh"] = {"verts": len(me.vertices), "edges": len(me.edges), "faces": len(me.polygons),
                    "tris": sum(len(p.vertices) - 2 for p in me.polygons),
                    "uv_layers": [u.name for u in me.uv_layers], "users": me.users}
result = info
"""

_SCREENSHOT_CODE = """
import bpy
path = PATH
wm = bpy.context.window_manager
hit = None
for w in wm.windows:
    for a in w.screen.areas:
        if a.type == 'VIEW_3D':
            hit = (w, a)
            break
    if hit:
        break
if hit is None:
    raise RuntimeError("No 3D Viewport is open in Blender (background mode has no viewport)")
w, a = hit
region = next(r for r in a.regions if r.type == 'WINDOW')
with bpy.context.temp_override(window=w, area=a, region=region):
    bpy.ops.screen.screenshot_area(filepath=path)
img = bpy.data.images.load(path)
width, height = img.size
if max(width, height) > MAX_SIZE:
    s = MAX_SIZE / max(width, height)
    img.scale(int(width * s), int(height * s))
    img.file_format = 'PNG'
    img.save()
    width, height = img.size
bpy.data.images.remove(img)
result = {"width": width, "height": height}
"""

_API_DOCS_CODE = """
import bpy, importlib, inspect
ident = IDENT

def _resolve(path):
    parts = path.split(".")
    obj = importlib.import_module(parts[0])
    for p in parts[1:]:
        obj = getattr(obj, p)
    return obj

out = {"identifier": ident}
if ident.endswith("*"):
    parent, _, stem = ident[:-1].rpartition(".")
    names = dir(_resolve(parent)) if parent else ["bpy", "bmesh", "mathutils", "bpy.data", "bpy.ops", "bpy.types", "bpy.context"]
    out["matches"] = sorted(n for n in names if n.startswith(stem) and not n.startswith("_"))[:200]
else:
    obj = _resolve(ident)
    out["doc"] = (getattr(obj, "__doc__", None) or "").strip()[:4000]
    rna = None
    try:
        rna = obj.get_rna_type()
    except Exception:
        rna = getattr(obj, "bl_rna", None)
    if rna is not None:
        out["description"] = rna.description
        props = []
        for p in rna.properties:
            if p.identifier == "rna_type":
                continue
            d = {"name": p.identifier, "type": p.type, "description": p.description}
            if p.type == "ENUM":
                d["items"] = [i.identifier for i in p.enum_items][:40]
            try:
                d["default"] = list(p.default_array) if getattr(p, "is_array", False) else p.default
            except Exception:
                pass
            props.append(d)
        out["properties"] = props[:150]
        funcs = getattr(rna, "functions", None)
        if funcs:
            out["functions"] = [
                {"name": f.identifier, "description": f.description,
                 "params": [{"name": pp.identifier, "type": pp.type, "output": pp.is_output} for pp in f.parameters]}
                for f in funcs
            ][:80]
    elif callable(obj):
        try:
            out["signature"] = str(inspect.signature(obj))
        except Exception:
            pass
        members = [n for n in dir(obj) if not n.startswith("_")]
        if members:
            out["members"] = members[:200]
    else:
        out["members"] = [n for n in dir(obj) if not n.startswith("_")][:200]
result = out
"""


def register(api) -> None:
    # MCP bridge process: skip disk deploy (slow); use blender_redeploy_addon when needed.
    if os.environ.get("UEFN_DUCKY_MCP_BRIDGE") != "1":
        try:
            api.log(f"addon deploy: {deploy_addon()}")
        except Exception as exc:
            api.log(f"addon deploy failed: {exc}")
    else:
        api.log("addon deploy skipped (MCP bridge process)")

    connect = getattr(api, "connection", None)
    if callable(connect):
        def _connection():
            online, detail = _socket_live()
            return {"online": online, "detail": detail}

        connect(_connection, label="Blender MCP")

    @api.tool(name="blender_status", intent=r"\bblender\b")
    def blender_status() -> str:
        """Ping the official Blender MCP add-on (Blender 5.1+) and report deploy paths."""
        host, port = _host_port()
        warning = needs_upgrade_warning()
        payload: dict[str, Any] = {
            "host": host,
            "port": port,
            "requires_blender": f"{MIN_BLENDER}+",
        }
        try:
            resp = _execute("import bpy\nresult = {'ok': True, 'blender': bpy.app.version_string, 'file': bpy.data.filepath}")
            payload.update({"connected": True, **resp["result"], "hint": "Ready."})
        except Exception as exc:
            payload.update(
                {
                    "connected": False,
                    "detail": str(exc),
                    "hint": (
                        f"WARNING: this plugin needs Blender {MIN_BLENDER}+. 4.x will not connect. "
                        "Install 5.1 from blender.org, open it once, then restart Blender. "
                        "Preferences → Add-ons → MCP must be enabled with Allow Online Access on."
                    ),
                }
            )
        if warning:
            payload["warning"] = warning
        try:
            payload["blender_user_roots"] = [str(p) for p in blender_user_roots()]
        except Exception:
            pass
        return _dumps(payload)

    @api.tool(name="blender_redeploy_addon", intent=r"\bblender\b")
    def blender_redeploy_addon() -> str:
        """Re-copy the official MCP add-on into Blender 5.1+ user folders (then restart Blender)."""
        return _dumps(deploy_addon())

    @api.tool(name="blender_get_scene_info", intent=r"\bblender\b")
    def blender_get_scene_info() -> str:
        """Scene summary: every object (name, type, collection, location, dimensions, verts), collections, materials, mode, selection."""
        try:
            return _dumps(_execute(_SCENE_INFO_CODE)["result"])
        except Exception as exc:
            return f"Error getting scene info: {exc}"

    @api.tool(name="blender_get_object_info", intent=r"\bblender\b")
    def blender_get_object_info(object_name: str) -> str:
        """One object in detail: transform, dimensions, collections, modifiers, materials, mesh counts, UV layers."""
        try:
            code = _OBJECT_INFO_CODE.replace("NAME", json.dumps(object_name))
            return _dumps(_execute(code)["result"])
        except Exception as exc:
            return f"Error getting object info: {exc}"

    @api.tool(name="blender_get_viewport_screenshot", intent=r"\bblender\b")
    def blender_get_viewport_screenshot(max_size: int = 1000) -> str:
        """Capture the Blender 3D viewport. Returns a short JSON path payload plus the image — never base64."""
        temp_path = os.path.join(tempfile.gettempdir(), f"blender_screenshot_{os.getpid()}.png")
        try:
            code = _SCREENSHOT_CODE.replace("PATH", json.dumps(temp_path)).replace("MAX_SIZE", str(int(max_size)))
            result = _execute(code)["result"]
            if not os.path.exists(temp_path):
                return "Error: screenshot file was not created"
            raw = Path(temp_path).read_bytes()
            try:
                os.remove(temp_path)
            except OSError:
                pass
            from frontend.ui_web.tool_captures import save_capture_for_agents
            from mcp.server.fastmcp import Image

            saved = save_capture_for_agents(raw, prefix="blender_viewport")
            payload = {
                "ok": True,
                "format": saved.get("format", "png"),
                "bytes": saved.get("bytes", len(raw)),
                "path": saved.get("path"),
                "capture_path": saved.get("capture_path") or saved.get("path"),
                "filename": saved.get("filename"),
                "media_url": saved.get("media_url"),
                "width": result.get("width"),
                "height": result.get("height"),
                "hint": "media_url/capture_path are AppData preview-only. Image also returned as MCP content.",
            }
            text = _dumps(payload)
            project_path = str(saved.get("path") or "")
            if project_path and Path(project_path).is_file():
                return [text, Image(path=project_path)]
            return text
        except Exception as exc:
            return f"Screenshot failed: {exc}"

    @api.tool(name="blender_execute_blender_code", intent=r"\bblender\b")
    def blender_execute_blender_code(code: str) -> str:
        """Run Python inside Blender (official MCP add-on).

        Contract: `import bpy`; assign a JSON-friendly dict to `result`; print() comes back as stdout;
        no sys.exit / quit. One named object per call (primitive, rename, material, or join) — never a whole
        asset in one script; the ledger records one revertable row per call.
        """
        before = _scene_object_names()
        try:
            resp = _execute(code, strict_json=False)
        except Exception as exc:
            return f"Error executing code: {exc}"
        after = _scene_object_names()
        payload: dict[str, Any] = {"ok": True, "result": resp.get("result", {})}
        if resp.get("stdout"):
            payload["stdout"] = resp["stdout"]
        if resp.get("stderr"):
            payload["stderr"] = resp["stderr"]
        sidecar = _sidecar_for_execute(before, after)
        if sidecar:
            payload["_ducky"] = sidecar
        return _dumps(payload)

    @api.tool(name="blender_get_python_api_docs", intent=r"\bblender\b")
    def blender_get_python_api_docs(identifier: str) -> str:
        """Live bpy API docs from the running Blender: `bpy.ops.mesh.primitive_cube_add`, `bpy.types.Object`,
        `bmesh.ops.bevel`. End with `*` to discover names (`bpy.ops.mesh.primitive_*`). Use before inventing an operator."""
        ident = identifier.strip()
        if not ident or any(c in ident for c in " ()[]\"'\n;"):
            return "Error: pass a dotted identifier such as bpy.ops.mesh.primitive_cube_add or bpy.types.Mesh.*"
        try:
            return _dumps(_execute(_API_DOCS_CODE.replace("IDENT", json.dumps(ident)), strict_json=False)["result"])
        except Exception as exc:
            return f"Error reading API docs for {ident}: {exc}"

    api.log("blender tools registered")
