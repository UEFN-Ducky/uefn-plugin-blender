"""TCP client for the Blender MCP addon socket (ahujasid/blender-mcp protocol).

Adapted from blender-mcp (MIT) — no telemetry, no uvx process.
"""

from __future__ import annotations

import json
import logging
import socket
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger("uefn.plugin.blender.connection")

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9876
SOCKET_TIMEOUT_S = 180.0


@dataclass
class BlenderConnection:
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    sock: socket.socket | None = field(default=None, repr=False)

    def connect(self) -> bool:
        if self.sock is not None:
            return True
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            return True
        except OSError as exc:
            log.warning("connect %s:%s failed: %s", self.host, self.port, exc)
            self.sock = None
            return False

    def disconnect(self) -> None:
        if self.sock is None:
            return
        try:
            self.sock.close()
        except OSError:
            pass
        self.sock = None

    def receive_full_response(self, sock: socket.socket, buffer_size: int = 8192) -> bytes:
        chunks: list[bytes] = []
        sock.settimeout(SOCKET_TIMEOUT_S)
        while True:
            try:
                chunk = sock.recv(buffer_size)
            except socket.timeout as exc:
                if chunks:
                    break
                raise TimeoutError("Timeout waiting for Blender response") from exc
            if not chunk:
                if not chunks:
                    raise ConnectionError("Connection closed before receiving any data")
                break
            chunks.append(chunk)
            data = b"".join(chunks)
            try:
                json.loads(data.decode("utf-8"))
                return data
            except json.JSONDecodeError:
                continue
        if not chunks:
            raise ConnectionError("No data received")
        data = b"".join(chunks)
        json.loads(data.decode("utf-8"))  # raises if incomplete
        return data

    def send_command(self, command_type: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.sock is None and not self.connect():
            raise ConnectionError(
                "Open Blender — addon should auto-start on "
                f"{self.host}:{self.port}. Restart Blender once after first plugin install."
            )
        assert self.sock is not None
        command = {"type": command_type, "params": params or {}}
        try:
            self.sock.sendall(json.dumps(command).encode("utf-8"))
            self.sock.settimeout(SOCKET_TIMEOUT_S)
            response_data = self.receive_full_response(self.sock)
            response = json.loads(response_data.decode("utf-8"))
            if response.get("status") == "error":
                raise RuntimeError(response.get("message") or "Unknown error from Blender")
            result = response.get("result", {})
            return result if isinstance(result, dict) else {"result": result}
        except (ConnectionError, BrokenPipeError, ConnectionResetError, OSError) as exc:
            self.sock = None
            raise ConnectionError(f"Connection to Blender lost: {exc}") from exc
        except TimeoutError:
            self.sock = None
            raise


def pack_command(command_type: str, params: dict[str, Any] | None = None) -> bytes:
    """Serialize a command frame (self-check helper)."""
    return json.dumps({"type": command_type, "params": params or {}}).encode("utf-8")


def unpack_response(data: bytes) -> dict[str, Any]:
    """Parse a response frame (self-check helper)."""
    return json.loads(data.decode("utf-8"))


def _self_check() -> None:
    packed = pack_command("get_scene_info", {})
    assert b'"type": "get_scene_info"' in packed or b'"type":"get_scene_info"' in packed
    resp = unpack_response(b'{"status":"ok","result":{"objects":[]}}')
    assert resp["status"] == "ok"
    assert resp["result"]["objects"] == []
    # Framing round-trip through a local pair of sockets.
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    client = BlenderConnection(host="127.0.0.1", port=port)
    assert client.connect()

    import threading

    def _serve() -> None:
        conn, _ = srv.accept()
        with conn:
            buf = b""
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                buf += chunk
                try:
                    json.loads(buf.decode("utf-8"))
                    break
                except json.JSONDecodeError:
                    continue
            conn.sendall(b'{"status":"ok","result":{"ping":true}}')

    t = threading.Thread(target=_serve, daemon=True)
    t.start()
    out = client.send_command("ping")
    assert out.get("ping") is True
    client.disconnect()
    srv.close()
    print("connection.py self-check ok")


if __name__ == "__main__":
    _self_check()
