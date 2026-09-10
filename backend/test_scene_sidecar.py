"""Named-object snapshot → ledger sidecar. No Blender required."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import _sidecar_for_execute  # noqa: E402


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
