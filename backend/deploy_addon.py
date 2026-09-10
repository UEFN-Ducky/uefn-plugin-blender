"""Deploy the vendored official Blender MCP add-on into Blender 5.1+ user folders.

Layout written per Blender version root (``%APPDATA%/Blender Foundation/Blender/5.1``):

    extensions/user_default/mcp/         ← assets/mcp (GPL, untouched)
    scripts/startup/uefn_ducky_blender_mcp.py  ← enables online access + add-on

Older Blender versions are skipped: the add-on needs 5.1 (see blender_manifest.toml).

Socket is locked to localhost:9876 — no user-facing host/port.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

PLUGIN_ID = "blender"
ADDON_ID = "mcp"
MIN_BLENDER = "5.1"
STARTUP_NAME = "uefn_ducky_blender_mcp.py"
STAMP_NAME = "uefn_ducky_blender_mcp.stamp"
_LEGACY_ADDON = "blendermcp"
_LEGACY_STARTUP = "uefn_ducky_blendermcp.py"
LOCKED_HOST = "localhost"
LOCKED_PORT = 9876
_SKIP_LAUNCH_FLAGS = ("--background", "-b", "--python", "--command", "--factory-startup")


def plugin_root() -> Path:
    """Installed plugin root (AppData) or repo package root during develop."""
    try:
        from backend.uefn_plugins.store import appdata_uefn_plugins_dir

        installed = appdata_uefn_plugins_dir() / PLUGIN_ID
        if (installed / "assets" / ADDON_ID).is_dir():
            return installed
    except Exception:
        pass
    return Path(__file__).resolve().parents[1]


def blender_user_roots() -> list[Path]:
    """All Blender Foundation/<version> user config roots on this machine."""
    roots: list[Path] = []
    candidates: list[Path] = []
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA") or ""
        if appdata:
            candidates.append(Path(appdata) / "Blender Foundation" / "Blender")
    elif sys.platform == "darwin":
        candidates.append(Path.home() / "Library" / "Application Support" / "Blender")
    else:
        candidates.append(Path.home() / ".config" / "blender")

    for base in candidates:
        if not base.is_dir():
            continue
        for child in sorted(base.iterdir()):
            if child.is_dir() and not child.name.startswith("."):
                roots.append(child)
    return roots


def _version_ok(root: Path) -> bool:
    try:
        major, minor = (int(x) for x in root.name.split(".")[:2])
    except ValueError:
        return False
    need_major, need_minor = (int(x) for x in MIN_BLENDER.split("."))
    return (major, minor) >= (need_major, need_minor)


def _copy_tree(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def needs_upgrade_warning(roots: list[Path] | None = None) -> str:
    """Loud warning when no Blender >= 5.1 user folder exists."""
    versions = list(roots) if roots is not None else blender_user_roots()
    if any(_version_ok(p) for p in versions):
        return ""
    old = [p.name for p in versions]
    if old:
        return (
            f"WARNING: Blender {', '.join(old)} found — this plugin needs Blender "
            f"{MIN_BLENDER}+. 4.x cannot run the official MCP add-on. Install 5.1 "
            "from blender.org, open it once, then restart Blender."
        )
    return (
        f"WARNING: this plugin needs Blender {MIN_BLENDER}+. Install it from blender.org, "
        "open it once, then restart Blender."
    )


def _remove_legacy(ver_root: Path) -> None:
    """Old community add-on listened on the same port — take it off disk."""
    shutil.rmtree(ver_root / "scripts" / "addons" / _LEGACY_ADDON, ignore_errors=True)
    try:
        (ver_root / "scripts" / "startup" / _LEGACY_STARTUP).unlink()
    except OSError:
        pass


def _legacy_present(ver_root: Path) -> bool:
    return (ver_root / "scripts" / "addons" / _LEGACY_ADDON).exists() or (
        ver_root / "scripts" / "startup" / _LEGACY_STARTUP
    ).exists()


def source_stamp(root: Path) -> str:
    addon = root / "assets" / ADDON_ID / "blender_manifest.toml"
    startup = root / "assets" / "startup" / STARTUP_NAME
    h = hashlib.sha256()
    h.update(addon.read_bytes() if addon.is_file() else b"")
    h.update(startup.read_bytes() if startup.is_file() else b"")
    return h.hexdigest()[:16]


def _stamp_path(ver_root: Path) -> Path:
    return ver_root / "scripts" / "startup" / STAMP_NAME


def deploy_current(ver_root: Path, stamp: str) -> bool:
    addon = ver_root / "extensions" / "user_default" / ADDON_ID / "blender_manifest.toml"
    startup = ver_root / "scripts" / "startup" / STARTUP_NAME
    try:
        return addon.is_file() and startup.is_file() and _stamp_path(ver_root).read_text(encoding="utf-8") == stamp
    except OSError:
        return False


def port_open(host: str = LOCKED_HOST, port: int = LOCKED_PORT, timeout: float = 0.3) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        try:
            sock.close()
        except OSError:
            pass


def wait_port(host: str = LOCKED_HOST, port: int = LOCKED_PORT, timeout: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if port_open(host, port):
            return True
        time.sleep(0.4)
    return False


def is_plain_gui_launch(cmdline: str) -> bool:
    """True when Blender was opened as a normal GUI with no file — safe to relaunch."""
    if not cmdline or not cmdline.strip():
        return False
    try:
        import shlex

        parts = shlex.split(cmdline, posix=os.name != "nt")
    except ValueError:
        parts = cmdline.split()
    args = parts[1:] if parts else []
    for raw in args:
        low = raw.lower()
        if low in _SKIP_LAUNCH_FLAGS or low.startswith("--python") or low.startswith("--command"):
            return False
        if low.endswith(".blend") or low.endswith(".blend1"):
            return False
    return True


def _win_blender_procs() -> list[dict[str, Any]]:
    # ponytail: one CIM query; upgrade to a named-pipe watch if we need sub-second detect.
    r = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-CimInstance Win32_Process -Filter \"Name='blender.exe'\" "
            "| Select-Object ProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Compress",
        ],
        capture_output=True,
        text=True,
        timeout=8,
    )
    text = (r.stdout or "").strip()
    if not text:
        return []
    import json

    data = json.loads(text)
    rows = data if isinstance(data, list) else [data]
    out: list[dict[str, Any]] = []
    for row in rows:
        pid = int(row.get("ProcessId") or 0)
        if not pid:
            continue
        out.append(
            {
                "pid": pid,
                "exe": str(row.get("ExecutablePath") or ""),
                "cmd": str(row.get("CommandLine") or ""),
            }
        )
    return out


def list_blender_processes() -> list[dict[str, Any]]:
    if sys.platform == "win32":
        try:
            return _win_blender_procs()
        except Exception:
            return []
    return []


def _terminate(pid: int) -> None:
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/PID", str(pid)], capture_output=True, timeout=10)
        return
    os.kill(pid, 15)


def relaunch_plain_gui_blender() -> dict[str, Any]:
    """Restart untitled Blender GUIs so the startup script can bind :9876.

    Saved .blend / --background / --python sessions are left alone (unsaved edits).
    """
    procs = [p for p in list_blender_processes() if is_plain_gui_launch(str(p.get("cmd") or ""))]
    if not procs:
        return {"relaunched": False, "reason": "no plain Blender GUI"}
    exe = str(procs[0].get("exe") or "").strip()
    if not exe:
        return {"relaunched": False, "reason": "no blender.exe path"}
    killed = [int(p["pid"]) for p in procs]
    for pid in killed:
        try:
            _terminate(pid)
        except OSError:
            pass
    time.sleep(0.8)
    subprocess.Popen([exe], close_fds=True)
    return {"relaunched": True, "exe": exe, "killed": killed}


def deploy_addon(*, root: Path | None = None, roots: list[Path] | None = None) -> dict[str, Any]:
    """Copy add-on + startup enabler into every Blender >= 5.1 user version dir found."""
    root = root or plugin_root()
    addon_src = root / "assets" / ADDON_ID
    startup_src = root / "assets" / "startup" / STARTUP_NAME
    if not (addon_src / "blender_manifest.toml").is_file():
        return {"ok": False, "error": f"add-on missing at {addon_src}", "deployed": []}
    if not startup_src.is_file():
        return {"ok": False, "error": f"startup script missing at {startup_src}", "deployed": []}

    versions = list(roots) if roots is not None else blender_user_roots()
    if not versions:
        warn = needs_upgrade_warning([])
        return {
            "ok": False,
            "error": warn,
            "requires_blender": f"{MIN_BLENDER}+",
            "warning": warn,
            "deployed": [],
        }

    stamp = source_stamp(root)
    deployed: list[str] = []
    skipped: list[str] = []
    unchanged: list[str] = []
    errors: list[str] = []
    for ver_root in versions:
        _remove_legacy(ver_root)
        if not _version_ok(ver_root):
            skipped.append(f"{ver_root.name} (needs Blender {MIN_BLENDER}+)")
            continue
        if deploy_current(ver_root, stamp) and not _legacy_present(ver_root):
            unchanged.append(str(ver_root))
            deployed.append(str(ver_root))
            continue
        try:
            ext_dir = ver_root / "extensions" / "user_default"
            startup_dir = ver_root / "scripts" / "startup"
            ext_dir.mkdir(parents=True, exist_ok=True)
            startup_dir.mkdir(parents=True, exist_ok=True)
            _copy_tree(addon_src, ext_dir / ADDON_ID)
            shutil.copy2(startup_src, startup_dir / STARTUP_NAME)
            _stamp_path(ver_root).write_text(stamp, encoding="utf-8")
            deployed.append(str(ver_root))
        except OSError as exc:
            errors.append(f"{ver_root}: {exc}")

    warning = needs_upgrade_warning(versions)
    return {
        "ok": bool(deployed) and not errors,
        "requires_blender": f"{MIN_BLENDER}+",
        "deployed": deployed,
        "unchanged": unchanged,
        "skipped": skipped,
        "errors": errors,
        "warning": warning,
        "host": LOCKED_HOST,
        "port": LOCKED_PORT,
    }


def _heal_lock_path() -> Path:
    return Path(os.environ.get("TEMP") or os.environ.get("TMP") or "/tmp") / "uefn-ducky-blender-heal.lock"


def _try_heal_lock(timeout: float = 20.0) -> bool:
    path = _heal_lock_path()
    try:
        if path.is_file() and (time.time() - path.stat().st_mtime) < timeout:
            return False
        path.write_text(str(os.getpid()), encoding="utf-8")
        return True
    except OSError:
        return True


def ensure_live(*, root: Path | None = None, roots: list[Path] | None = None) -> dict[str, Any]:
    """Deploy if stale, then relaunch an untitled Blender GUI when :9876 is down."""
    deployed = deploy_addon(root=root, roots=roots)
    online = port_open()
    relaunch: dict[str, Any] | None = None
    if not online:
        if _try_heal_lock():
            relaunch = relaunch_plain_gui_blender()
            online = wait_port(timeout=15.0 if relaunch.get("relaunched") else 8.0)
        else:
            relaunch = {"relaunched": False, "reason": "heal already in progress"}
            online = wait_port(timeout=12.0)
    deployed["online"] = online
    deployed["relaunch"] = relaunch
    return deployed


def _self_check() -> None:
    import tempfile

    assert isinstance(blender_user_roots(), list)
    assert is_plain_gui_launch(r'"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"')
    assert not is_plain_gui_launch(r'"C:\Blender\blender.exe" C:\isle.blend')
    assert not is_plain_gui_launch(r'"C:\Blender\blender.exe" --background')
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as tmp:
        new, old = Path(tmp) / "5.1", Path(tmp) / "4.2"
        new.mkdir()
        (old / "scripts" / "addons" / _LEGACY_ADDON).mkdir(parents=True)
        result = deploy_addon(root=root, roots=[new, old])
        assert result["ok"] is True, result
        assert (new / "extensions" / "user_default" / ADDON_ID / "blender_manifest.toml").is_file()
        assert (new / "scripts" / "startup" / STARTUP_NAME).is_file()
        assert _stamp_path(new).is_file()
        assert result["skipped"] == ["4.2 (needs Blender 5.1+)"], result
        assert not (old / "scripts" / "addons" / _LEGACY_ADDON).exists()
        again = deploy_addon(root=root, roots=[new, old])
        assert again["ok"] is True, again
        assert str(new) in (again.get("unchanged") or []), again
        warn_only = deploy_addon(root=root, roots=[old])
        assert "WARNING" in (warn_only.get("warning") or ""), warn_only
        assert "5.1" in warn_only["warning"]
        assert not needs_upgrade_warning([new])
    print("deploy_addon.py self-check ok")


if __name__ == "__main__":
    _self_check()
