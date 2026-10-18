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


def test_the_newest_installed_blender_is_found() -> None:
    import tempfile

    from backend.deploy_addon import installed_blender_exe

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "Blender Foundation"
        for name in ("Blender 4.5", "Blender 5.1", "Blender 5.2", "Blender 5.3"):
            (base / name).mkdir(parents=True)
            if name != "Blender 5.3":
                (base / name / "blender.exe").write_text("", encoding="utf-8")
        assert installed_blender_exe([base]) == str(base / "Blender 5.2" / "blender.exe")
        assert installed_blender_exe([Path(tmp) / "nothing"]) == ""


def test_no_blender_running_starts_one(monkeypatch) -> None:
    from backend import deploy_addon as da

    started: list[list[str]] = []
    monkeypatch.setattr(da, "list_blender_processes", lambda: [])
    monkeypatch.setattr(da, "installed_blender_exe", lambda: "C:/B/Blender 5.2/blender.exe")
    monkeypatch.setattr(da.subprocess, "Popen", lambda cmd, **kw: started.append(cmd))
    out = da.relaunch_plain_gui_blender()
    assert out["started"] is True and started == [["C:/B/Blender 5.2/blender.exe"]]

    monkeypatch.setattr(da, "list_blender_processes", lambda: [{"pid": 1, "cmd": '"C:/B/blender.exe" C:/isle.blend'}])
    started.clear()
    out = da.relaunch_plain_gui_blender()
    assert out["relaunched"] is False and started == []


def test_ducky_starting_never_opens_or_restarts_blender(monkeypatch) -> None:
    """Oct 18 2026: every Ducky launch opened Blender (the startup heal started one)."""
    import inspect

    import backend
    from backend import deploy_addon as da

    started: list[list[str]] = []
    monkeypatch.setattr(da, "deploy_addon", lambda **kw: {"ok": True})
    monkeypatch.setattr(da, "port_open", lambda *a, **kw: False)
    monkeypatch.setattr(da, "list_blender_processes", lambda: [])
    monkeypatch.setattr(da, "installed_blender_exe", lambda: "C:/B/Blender 5.2/blender.exe")
    monkeypatch.setattr(da.subprocess, "Popen", lambda cmd, **kw: started.append(cmd))
    monkeypatch.setattr(da, "_terminate", lambda pid, grace=5.0: started.append(["kill", str(pid)]))
    out = da.ensure_live(start=False)
    assert out["online"] is False and out["relaunch"] is None and started == []
    # An untitled Blender without the add-on is left alone at start-up too.
    monkeypatch.setattr(da, "list_blender_processes", lambda: [{"pid": 7, "cmd": '"C:/B/blender.exe"', "age": 999}])
    assert da.ensure_live(start=False)["relaunch"] is None and started == []
    # The startup hook asks for a deploy only.
    assert "ensure_live(start=False)" in inspect.getsource(backend.register)


if __name__ == "__main__":
    test_host_port_are_locked()
    test_plugin_json_has_no_host_port_settings()
    test_win_no_window_kwargs_hides_console()
    test_plain_gui_launch_rules()
    test_second_deploy_is_unchanged()
    print("test_deploy_heal.py ok")
