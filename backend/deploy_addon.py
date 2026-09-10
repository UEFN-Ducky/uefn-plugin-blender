"""Deploy the vendored official Blender MCP add-on into Blender 5.1+ user folders.

Layout written per Blender version root (``%APPDATA%/Blender Foundation/Blender/5.1``):

    extensions/user_default/mcp/         ← assets/mcp (GPL, untouched)
    scripts/startup/uefn_ducky_blender_mcp.py  ← enables online access + add-on

Older Blender versions are skipped: the add-on needs 5.1 (see blender_manifest.toml).
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Any

PLUGIN_ID = "blender"
ADDON_ID = "mcp"
MIN_BLENDER = "5.1"
STARTUP_NAME = "uefn_ducky_blender_mcp.py"
_LEGACY_ADDON = "blendermcp"
_LEGACY_STARTUP = "uefn_ducky_blendermcp.py"


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

    deployed: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []
    for ver_root in versions:
        _remove_legacy(ver_root)
        if not _version_ok(ver_root):
            skipped.append(f"{ver_root.name} (needs Blender {MIN_BLENDER}+)")
            continue
        try:
            ext_dir = ver_root / "extensions" / "user_default"
            startup_dir = ver_root / "scripts" / "startup"
            ext_dir.mkdir(parents=True, exist_ok=True)
            startup_dir.mkdir(parents=True, exist_ok=True)
            _copy_tree(addon_src, ext_dir / ADDON_ID)
            shutil.copy2(startup_src, startup_dir / STARTUP_NAME)
            deployed.append(str(ver_root))
        except OSError as exc:
            errors.append(f"{ver_root}: {exc}")

    warning = needs_upgrade_warning(versions)
    note = ""
    if deployed:
        note = "Restart Blender once if it was already open so the add-on loads and the server auto-starts on 9876."
    elif warning:
        note = warning
    return {
        "ok": bool(deployed) and not errors,
        "requires_blender": f"{MIN_BLENDER}+",
        "deployed": deployed,
        "skipped": skipped,
        "errors": errors,
        "warning": warning,
        "note": note,
    }


def _self_check() -> None:
    import tempfile

    assert isinstance(blender_user_roots(), list)
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as tmp:
        new, old = Path(tmp) / "5.1", Path(tmp) / "4.2"
        new.mkdir()
        (old / "scripts" / "addons" / _LEGACY_ADDON).mkdir(parents=True)
        result = deploy_addon(root=root, roots=[new, old])
        assert result["ok"] is True, result
        assert (new / "extensions" / "user_default" / ADDON_ID / "blender_manifest.toml").is_file()
        assert (new / "scripts" / "startup" / STARTUP_NAME).is_file()
        assert result["skipped"] == ["4.2 (needs Blender 5.1+)"], result
        assert not (old / "scripts" / "addons" / _LEGACY_ADDON).exists()
        warn_only = deploy_addon(root=root, roots=[old])
        assert "WARNING" in (warn_only.get("warning") or ""), warn_only
        assert "5.1" in warn_only["warning"]
        assert not needs_upgrade_warning([new])
    print("deploy_addon.py self-check ok")


if __name__ == "__main__":
    _self_check()
