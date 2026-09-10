"""Named-object snapshot → ledger sidecar. No Blender required."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import ast  # noqa: E402
import json  # noqa: E402

import backend  # noqa: E402
from backend import _sidecar_for_execute  # noqa: E402


def test_embedded_bpy_templates_parse_after_substitution() -> None:
    for code in (
        backend._SCENE_INFO_CODE,
        backend._OBJECT_INFO_CODE.replace("NAME", json.dumps("SM_Chair")),
        backend._SCREENSHOT_CODE.replace("PATH", json.dumps(r"C:\t m\p.png")).replace("MAX_SIZE", "1000"),
        backend._API_DOCS_CODE.replace("IDENT", json.dumps("bpy.ops.mesh.primitive_*")),
    ):
        tree = ast.parse(code)
        assigned = {t.id for n in tree.body if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)}
        assert "result" in assigned, code[:60]


def test_added_object_records_an_inverse() -> None:
    side = _sidecar_for_execute(["Camera"], ["Camera", "Cube"])
    assert side is not None
    assert side["revertable"] == "auto"
    assert side["slot"] == "blender://object/Cube/exists"
    assert "bpy.data.objects.remove" in side["inverse"][0]["params"]["code"]


def test_unchanged_scene_is_not_recorded() -> None:
    assert _sidecar_for_execute(["Cube"], ["Cube"]) is None


def test_removed_object_is_manual() -> None:
    side = _sidecar_for_execute(["Cube", "Lamp"], ["Lamp"])
    assert side is not None
    assert side["revertable"] == "manual"


def test_missing_snapshot_never_records() -> None:
    """A failed 'before' snapshot must not turn the whole scene into 'added'."""
    assert _sidecar_for_execute(None, ["Camera", "Cube"]) is None
    assert _sidecar_for_execute(["Camera"], None) is None


def test_inverse_code_assigns_result() -> None:
    side = _sidecar_for_execute([], ["Cube"])
    assert side is not None
    assert side["inverse"][0]["params"]["code"].rstrip().endswith("result = {'ok': True}")


def test_create_that_also_deletes_temps_is_still_auto() -> None:
    """Chair scripts drop Cube / helpers — Revert must still delete SM_Chair."""
    side = _sidecar_for_execute(["Camera", "Cube"], ["Camera", "SM_Chair"])
    assert side is not None
    assert side["revertable"] == "auto"
    assert side["slot"] == "blender://object/SM_Chair/exists"
    code = side["inverse"][0]["params"]["code"]
    assert "SM_Chair" in code
    assert "bpy.data.objects.remove" in code
