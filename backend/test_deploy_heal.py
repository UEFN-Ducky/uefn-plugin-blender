"""Deploy stamp + locked socket + untitled-relaunch rules. No Blender required."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import _host_port  # noqa: E402
from backend.connection import DEFAULT_HOST, DEFAULT_PORT  # noqa: E402
from backend.deploy_addon import deploy_addon, is_plain_gui_launch, source_stamp  # noqa: E402


def test_host_port_are_locked() -> None:
    assert _host_port() == (DEFAULT_HOST, DEFAULT_PORT) == ("localhost", 9876)


def test_plugin_json_has_no_host_port_settings() -> None:
    spec = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    contrib = spec.get("contributes") or {}
    assert "settings.tabs" not in contrib
    assert "settings.sections" not in contrib
    blob = json.dumps(contrib)
    assert '"id": "host"' not in blob
    assert '"id": "port"' not in blob


def test_win_no_window_kwargs_hides_console() -> None:
    from backend.deploy_addon import _win_no_window_kwargs

    kw = _win_no_window_kwargs()
    if sys.platform == "win32":
        import subprocess

        assert kw.get("creationflags") == getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        assert kw.get("startupinfo") is not None
    else:
        assert kw == {}


def test_plain_gui_launch_rules() -> None:
    exe = r'"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"'
    assert is_plain_gui_launch(exe)
    assert not is_plain_gui_launch(exe + " C:\\isle.blend")
    assert not is_plain_gui_launch(exe + " --background")
    assert not is_plain_gui_launch(exe + " --python C:\\x.py")
    assert not is_plain_gui_launch("")


def test_second_deploy_is_unchanged() -> None:
    import tempfile

    stamp = source_stamp(ROOT)
    with tempfile.TemporaryDirectory() as tmp:
        ver = Path(tmp) / "5.2"
        ver.mkdir()
        first = deploy_addon(root=ROOT, roots=[ver])
        assert first["ok"] is True, first
        assert stamp
        second = deploy_addon(root=ROOT, roots=[ver])
        assert str(ver) in (second.get("unchanged") or []), second


if __name__ == "__main__":
    test_host_port_are_locked()
    test_plugin_json_has_no_host_port_settings()
    test_win_no_window_kwargs_hides_console()
    test_plain_gui_launch_rules()
    test_second_deploy_is_unchanged()
    print("test_deploy_heal.py ok")
