"""Linux-only paths: Blender processes read from /proc, an owner-only socket token."""

from __future__ import annotations

import os
import stat
import sys

import pytest

from backend import connection, deploy_addon


def test_linux_blender_procs_reads_proc(tmp_path):
    (tmp_path / "uptime").write_text("1000.0 50.0\n")
    tick = os.sysconf("SC_CLK_TCK") if hasattr(os, "sysconf") else 100
    rows = {"41": ("blender", [b"/opt/blender/blender"]), "42": ("python3", [b"python3"])}
    for pid, (comm, argv) in rows.items():
        d = tmp_path / pid
        d.mkdir()
        (d / "comm").write_text(comm + "\n")
        (d / "cmdline").write_bytes(b"\0".join(argv) + b"\0")
        fields = ["S"] + ["0"] * 18 + [str(900 * tick)]  # field 22 = start, 900 s after boot
        (d / "stat").write_text(f"{pid} ({comm}) " + " ".join(fields) + "\n")
    (tmp_path / "self").mkdir()
    got = deploy_addon._linux_blender_procs(tmp_path)
    assert [r["pid"] for r in got] == [41]
    assert got[0]["exe"] == "/opt/blender/blender" and got[0]["cmd"] == "/opt/blender/blender"
    assert abs(got[0]["age"] - 100.0) < 0.01
    assert deploy_addon.is_plain_gui_launch(got[0]["cmd"]) or sys.platform == "win32"


@pytest.mark.skipif(os.name == "nt", reason="POSIX file modes")
def test_token_is_owner_only(tmp_path):
    path = tmp_path / "UEFN-Ducky" / "blender_mcp.token"
    token = connection.auth_token(path)
    assert len(token) == 64 and connection.auth_token(path) == token
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700


@pytest.mark.skipif(os.name == "nt", reason="non-Windows token location")
def test_token_not_in_shared_tmp():
    assert connection.TOKEN_FILE.parent.parent == connection.Path.home() / ".cache"
