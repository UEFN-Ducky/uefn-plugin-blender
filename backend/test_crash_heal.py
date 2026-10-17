"""A Blender crash mid-call answers fast; the heal never loops on a starting Blender and
force-closes one that ignores the polite close. No Blender required."""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import connection, deploy_addon  # noqa: E402

CRASH = """# Blender 5.2.1
# backtrace
ExceptionCode         : EXCEPTION_ACCESS_VIOLATION (0xc0000005)
Stack trace:
blender.exe         :0x00007FF7B68C74D0  blender::BKE_view_layer_copy_data
blender.exe         :0x00007FF7B647F430  blender::scene_copy_data
blender.exe         :0x00007FF7B98949F0  blender::bpy_lib_write
"""


def test_crash_report_is_read_only_when_written_after_the_call(tmp_path) -> None:
    crash = tmp_path / "blender.crash.txt"
    crash.write_text(CRASH, encoding="utf-8")
    now = time.time()
    os.utime(crash, (now - 100, now - 100))
    assert connection.crash_report_since(now, str(crash)) == ""
    os.utime(crash, (now + 1, now + 1))
    got = connection.crash_report_since(now, str(crash))
    assert "EXCEPTION_ACCESS_VIOLATION" in got and "bpy_lib_write" in got


def test_a_crash_during_a_call_answers_in_seconds(tmp_path, monkeypatch) -> None:
    # Oct 17 2026: Blender crashed in bpy.data.libraries.write and the agent waited 600 s.
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    held: list[socket.socket] = []
    threading.Thread(target=lambda: held.append(srv.accept()[0]), daemon=True).start()

    def crash_soon() -> None:
        time.sleep(0.3)
        (tmp_path / "blender.crash.txt").write_text(CRASH, encoding="utf-8")

    monkeypatch.setattr(connection.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(connection, "_CRASH_POLL_S", 0.2)
    threading.Thread(target=crash_soon, daemon=True).start()
    started = time.monotonic()
    try:
        connection.execute("result = {}", host="127.0.0.1", port=port, timeout=60)
        raise AssertionError("expected a crash error")
    except ConnectionError as exc:
        assert "Blender crashed" in str(exc) and "save_as_mainfile" in str(exc)
    assert time.monotonic() - started < 10
    srv.close()


def test_a_starting_blender_is_left_to_start(monkeypatch) -> None:
    killed: list[int] = []
    gui = '"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"'
    monkeypatch.setattr(deploy_addon, "list_blender_processes", lambda: [{"pid": 7, "exe": "b.exe", "cmd": gui, "age": 20.0}])
    monkeypatch.setattr(deploy_addon, "_terminate", lambda pid: killed.append(pid))
    out = deploy_addon.relaunch_plain_gui_blender()
    assert out["starting"] is True and killed == []


def test_a_blender_that_ignores_the_polite_close_is_forced(monkeypatch) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(deploy_addon.subprocess, "run", lambda cmd, **kw: calls.append(cmd))
    monkeypatch.setattr(deploy_addon, "_pid_alive", lambda pid: True)
    deploy_addon._terminate(42, grace=0.2)
    if sys.platform == "win32":
        assert calls[0] == ["taskkill", "/PID", "42"]
        assert calls[-1] == ["taskkill", "/PID", "42", "/F", "/T"]
