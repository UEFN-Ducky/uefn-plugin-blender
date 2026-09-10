"""TCP client for the official Blender Lab MCP add-on (projects.blender.org/lab/blender_mcp).

Wire format (see assets/mcp/mcp_to_blender_server.py):

    request:  {"type": "execute", "code": "...", "strict_json": bool}\\0
    response: {"status": "ok"|"error", "result": {...}, "stdout": "", "stderr": ""}\\0

One connection per request — the add-on closes the socket after replying.
The executed code must assign a dict to ``result``.
"""

from __future__ import annotations

import json
import socket
from typing import Any

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9876
CONNECT_TIMEOUT_S = 3.0
# Long: renders / bakes return via the add-on's deferred path (up to 1h there).
RESPONSE_TIMEOUT_S = 600.0
_RECV = 65536


class BlenderError(RuntimeError):
    """The add-on ran the code and reported ``status: error``."""


def pack_request(code: str, strict_json: bool) -> bytes:
    return (json.dumps({"type": "execute", "code": code, "strict_json": strict_json}) + "\0").encode("utf-8")


def unpack_response(data: bytes) -> dict[str, Any]:
    text = data.split(b"\0", 1)[0].decode("utf-8")
    obj = json.loads(text)
    return obj if isinstance(obj, dict) else {"status": "error", "message": f"bad frame: {obj!r}"}


def execute(
    code: str,
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    strict_json: bool = True,
    timeout: float = RESPONSE_TIMEOUT_S,
) -> dict[str, Any]:
    """Run ``code`` in Blender. Returns the full envelope; raises on socket/exec error."""
    try:
        sock = socket.create_connection((host, port), timeout=CONNECT_TIMEOUT_S)
    except OSError as exc:
        raise ConnectionError(
            f"Blender MCP not reachable on {host}:{port}. Open Blender 5.1+ — "
            "the add-on is installed and started automatically."
        ) from exc
    try:
        sock.sendall(pack_request(code, strict_json))
        sock.settimeout(timeout)
        buf = bytearray()
        while b"\0" not in buf:
            chunk = sock.recv(_RECV)
            if not chunk:
                break
            buf.extend(chunk)
    except socket.timeout as exc:
        raise TimeoutError(f"Blender did not answer within {timeout:.0f}s") from exc
    finally:
        sock.close()
    if not buf:
        raise ConnectionError("Blender closed the connection without a response")
    resp = unpack_response(bytes(buf))
    if resp.get("status") != "ok":
        raise BlenderError(str(resp.get("message") or "Unknown error from Blender"))
    return resp


def _self_check() -> None:
    import threading

    assert pack_request("result = {}", True).endswith(b"\0")
    assert unpack_response(b'{"status":"ok","result":{"a":1}}\0junk')["result"] == {"a": 1}

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    seen: list[dict[str, Any]] = []

    def _serve() -> None:
        conn, _ = srv.accept()
        with conn:
            buf = b""
            while b"\0" not in buf:
                buf += conn.recv(4096)
            seen.append(json.loads(buf.split(b"\0", 1)[0]))
            conn.sendall(b'{"status":"ok","result":{"ping":true},"stdout":"hi\\n"}\0')

    threading.Thread(target=_serve, daemon=True).start()
    out = execute("result = {'ping': True}", host="127.0.0.1", port=port)
    assert out["result"] == {"ping": True} and out["stdout"] == "hi\n"
    assert seen[0] == {"type": "execute", "code": "result = {'ping': True}", "strict_json": True}
    srv.close()

    try:
        execute("x", host="127.0.0.1", port=1)
        raise AssertionError("expected ConnectionError")
    except ConnectionError:
        pass
    print("connection.py self-check ok")


if __name__ == "__main__":
    _self_check()
