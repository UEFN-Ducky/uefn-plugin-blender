"""The real add-on server, wrapped by Ducky's startup guard, runs only token-bearing requests."""

from __future__ import annotations

import importlib
import importlib.util
import socket
import sys
import threading
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import connection  # noqa: E402

_ASSETS = ROOT / "assets"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # NamedTuple / dataclass lookups need the module registered
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def guarded_server(tmp_path):
    # A bare package over assets/mcp: its relative imports work, its bpy-using __init__ never runs.
    pkg = types.ModuleType("ducky_test_mcp")
    pkg.__path__ = [str(_ASSETS / "mcp")]
    sys.modules["ducky_test_mcp"] = pkg
    srv = importlib.import_module("ducky_test_mcp.mcp_to_blender_server")
    # Running code needs bpy; the guard sits in front of this, so a stub proves it was reached.
    srv._execute_code = lambda code, strict_json: srv._ExecResult({"status": "ok", "result": {"ran": code}})
    startup = _load("ducky_test_startup", _ASSETS / "startup" / "uefn_ducky_blender_mcp.py")
    token_file = tmp_path / "blender_mcp.token"
    token_file.write_text("right-token", encoding="utf-8")
    startup.install_token_guard(srv, token_file)
    startup.install_token_guard(srv, token_file)  # idempotent: one wrapper, not two

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    srv.start("127.0.0.1", port)
    stop = threading.Event()

    def _loop() -> None:
        while not stop.is_set() and srv.is_running():
            srv.poll_blocking(0.2)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    yield port, srv
    stop.set()
    t.join(2)
    srv.stop()
    for name in [m for m in sys.modules if m == "ducky_test_mcp" or m.startswith("ducky_test_mcp.")]:
        sys.modules.pop(name, None)
    sys.modules.pop("ducky_test_startup", None)


def test_right_token_runs(guarded_server):
    port, _srv = guarded_server
    out = connection.execute("result = {'ok': 1}", host="127.0.0.1", port=port, token="right-token", timeout=10)
    assert out["result"] == {"ran": "result = {'ok': 1}"}


@pytest.mark.parametrize("token", ["", "wrong-token"])
def test_missing_or_wrong_token_refused(guarded_server, token):
    port, _srv = guarded_server
    with pytest.raises(connection.BlenderError, match="refused"):
        connection.execute("result = {'ran': 1}", host="127.0.0.1", port=port, token=token, timeout=10)


def test_auth_token_created_once(tmp_path):
    path = tmp_path / "sub" / "blender_mcp.token"
    first = connection.auth_token(path)
    assert len(first) == 64 and connection.auth_token(path) == first
    assert path.read_text(encoding="utf-8") == first
