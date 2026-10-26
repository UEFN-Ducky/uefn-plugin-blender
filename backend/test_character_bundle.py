"""The Blender character bundles in plugin.json are well formed and save through core like a real template.

Needs the Ducky app source (core's template and workflow store) and the Tripo plugin as siblings in the
GitHub folder, or DUCKY_APP_DIR / TRIPO_PLUGIN_JSON; skipped without them."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
PLUGIN = json.loads((HERE / "plugin.json").read_text(encoding="utf-8"))
ROWS = {r["id"]: r for r in PLUGIN["contributes"]["automations"]["templates"]}
ROW = ROWS["blender-character"]
MIX = ROWS["blender-character-mix"]

APP = Path(os.environ.get("DUCKY_APP_DIR") or HERE.parent.parent / "UEFN-Ducky-Release" / "ducky_app")
TRIPO = Path(os.environ.get("TRIPO_PLUGIN_JSON") or HERE.parent / "uefn-plugin-tripo" / "plugin.json")

NODE_TYPES = {
    "start.chat", "flow.input", "flow.output", "flow.repeat", "flow.branch", "flow.choose", "workflow.call",
    "pipeline.agent", "pipeline.finish", "tool.call", "uefn.open_project", "uefn.import", "notify.message",
    "llm.ask", "llm.extract", "llm.vision", "text.template", "input.text", "list.make",
    "logic.compare", "logic.expression", "logic.if",
    "image.generate", "image.edit", "image.remove_bg", "image.concat",
    "blender.open", "blender.export", "blender.render", "mesh.rig", "mesh.animate", "mesh.from_image",
}
EDGE_KINDS = {"main", "data", "true", "false", "each", "done"}
SHARED = ("spec", "sheet", "ship")


def keys(row):
    return [w["key"] for w in row["workflows"]]


def tripo_shared():
    if not TRIPO.is_file():
        pytest.skip("Tripo plugin not next to this repo")
    row = next(r for r in json.loads(TRIPO.read_text(encoding="utf-8"))["contributes"]["automations"]["templates"] if r["id"] == "tripo-character")
    return {w["key"]: w for w in row["bundle"]["workflows"]}


def test_bundle_shapes():
    assert keys(ROW) == ["character", "spec", "sheet", "make3d", "rig", "gear", "ship"]
    assert keys(MIX) == ["character", "spec", "sheet", "make3d", "cleanup", "rig", "ship"]
    for row in (ROW, MIX):
        assert row["folders"] == ["Functions"] and row["workflows"][0]["folder"] == ""
        assert len(set(keys(row))) == len(keys(row))


def test_every_node_type_exists_and_every_edge_lands():
    for row in (ROW, MIX):
        for wf in row["workflows"]:
            nodes = {n["id"]: n for n in wf["graph"]["nodes"]}
            assert len(nodes) == len(wf["graph"]["nodes"]), wf["key"]
            assert all(n["type"] in NODE_TYPES for n in nodes.values()), (row["id"], wf["key"])
            assert all(e["source"] in nodes and e["target"] in nodes and e["kind"] in EDGE_KINDS for e in wf["graph"]["edges"]), (row["id"], wf["key"])


def test_main_calls_run_in_order():
    def calls(row):
        return [n["config"]["workflow_id"] for n in row["workflows"][0]["graph"]["nodes"] if n["type"] == "workflow.call"]

    assert calls(ROW) == ["@spec", "@sheet", "@make3d", "@rig", "@gear", "@ship"]
    assert calls(MIX) == ["@spec", "@sheet", "@make3d", "@cleanup", "@rig", "@ship"]


def test_shared_three_are_tripos_unchanged():
    theirs = tripo_shared()
    for row in (ROW, MIX):
        for key in SHARED:
            mine = next(w for w in row["workflows"] if w["key"] == key)
            assert mine == theirs[key], (row["id"], key)


def test_standards_hold():
    def nodes(row, key):
        return next(w for w in row["workflows"] if w["key"] == key)["graph"]["nodes"]

    def types(row, key):
        return [n["type"] for n in nodes(row, key)]

    assert {"pipeline.agent", "blender.export", "blender.render", "llm.vision"} <= set(types(ROW, "make3d"))
    assert types(ROW, "rig")[1] == "blender.open"
    assert next(n for n in nodes(ROW, "rig") if n["type"] == "flow.repeat")["config"]["max"] == 2
    assert next(n for n in nodes(ROW, "rig") if n["type"] == "mesh.rig")["config"]["backend"] == "auto"
    assert "mesh.from_image" in types(MIX, "make3d") and types(MIX, "cleanup")[1] == "blender.open"
    assert {"mesh.rig", "mesh.animate"} <= set(types(MIX, "rig"))
    for row in (ROW, MIX):
        assert all(n["config"].get("ducky") == "blender-artist" for w in row["workflows"] for n in w["graph"]["nodes"] if n["type"] == "pipeline.agent")


# Core's `backend` package clashes with this plugin's, so core runs in its own process.
CORE_CHECK = r"""
import json, sys
from pathlib import Path

plugin_json, row_id, tmp = sys.argv[1:4]
from backend.automations import bundles, catalog, store
from backend.automations.runner import _Dataflow
from backend.automations.templates import bundle_of
from backend.uefn_plugins.host import _automation_template_row

store.use_db = lambda *_: False
store._files_dir = lambda: Path(tmp) / "workflows"
(Path(tmp) / "workflows").mkdir()
store._announce_graphs_changed = lambda: None
rows = json.load(open(plugin_json, encoding="utf-8"))["contributes"]["automations"]["templates"]
row = next(r for r in rows if r["id"] == row_id)
out = bundles.import_bundle(bundle_of(_automation_template_row(row, "blender")), "local")
problems = []
if out["outside"] or len(out["workflows"]) != 7:
    problems.append(["import", out["outside"], len(out["workflows"])])
saved = {w["key"]: store.get_workflow(w["id"]) for w in out["workflows"]}
specs = catalog.node_specs()
for key, wf in saved.items():
    nodes = {n["id"]: n for n in wf["graph"]["nodes"]}
    flow = _Dataflow(nodes, wf["graph"]["edges"], specs)
    for e in wf["graph"]["edges"]:
        if e["kind"] != "data":
            continue
        outs = {p["id"] for p in flow.pins(e["source"])["outputs"]}
        ins = {p["id"] for p in flow.pins(e["target"])["inputs"]}
        if e["source_pin"] not in outs:
            problems.append([key, "no output pin", e["source"], e["source_pin"]])
        if e["target_pin"] not in ins:
            problems.append([key, "no input pin", e["target"], e["target_pin"]])
    for n in nodes.values():
        if n["type"] != "workflow.call":
            continue
        callee = next(w for w in saved.values() if w["id"] == n["config"]["workflow_id"])
        wanted = {i["name"] for i in next(c for c in callee["graph"]["nodes"] if c["type"] == "flow.input")["config"]["inputs"]}
        extra = set(n["config"].get("args") or {}) - wanted
        if extra:
            problems.append([key, "call passes unknown inputs", n["id"], sorted(extra)])
print(json.dumps(problems))
"""


@pytest.mark.parametrize("row_id", ["blender-character", "blender-character-mix"])
def test_bundle_saves_and_every_wire_and_call_matches(tmp_path, row_id):
    if not (APP / "backend" / "automations" / "templates.py").is_file():
        pytest.skip("Ducky app source not found")
    done = subprocess.run([sys.executable, "-c", CORE_CHECK, str(HERE / "plugin.json"), row_id, str(tmp_path)],
                          cwd=APP, capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(APP)})
    assert done.returncode == 0, done.stderr[-2000:]
    assert json.loads(done.stdout.strip().splitlines()[-1]) == []
