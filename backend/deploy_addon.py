"""Deploy the vendored Blender MCP addon into Blender user script folders."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Any

PLUGIN_ID = "blender"
ADDON_MODULE = "blendermcp"
STARTUP_NAME = "uefn_ducky_blendermcp.py"


def plugin_root() -> Path:
    """Installed plugin root (AppData) or repo package root during develop."""
    try:
        from backend.uefn_plugins.store import appdata_uefn_plugins_dir

        installed = appdata_uefn_plugins_dir() / PLUGIN_ID
        if (installed / "assets" / ADDON_MODULE).is_dir():
            return installed
    except Exception:
        pass
    # backend/ is one level under package root
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
        home = Path.home()
        candidates.append(home / "Library" / "Application Support" / "Blender")
    else:
        home = Path.home()
        candidates.append(home / ".config" / "blender")

    for base in candidates:
        if not base.is_dir():
            continue
        for child in sorted(base.iterdir()):
            if child.is_dir() and not child.name.startswith("."):
                roots.append(child)
    return roots


def _copy_tree(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def deploy_addon(
    *,
    root: Path | None = None,
    roots: list[Path] | None = None,
) -> dict[str, Any]:
    """Copy addon + startup enabler into every Blender user version dir found."""
    root = root or plugin_root()
    addon_src = root / "assets" / ADDON_MODULE
    startup_src = root / "assets" / "startup" / STARTUP_NAME
    if not addon_src.is_dir():
        return {"ok": False, "error": f"addon missing at {addon_src}", "deployed": []}
    if not startup_src.is_file():
        return {"ok": False, "error": f"startup script missing at {startup_src}", "deployed": []}

    versions = list(roots) if roots is not None else blender_user_roots()
    if not versions:
        return {
            "ok": False,
            "error": (
                "Blender user folder not found. Install Blender, launch it once, "
                "then call blender_redeploy_addon."
            ),
            "deployed": [],
        }

    deployed: list[str] = []
    errors: list[str] = []
    for ver_root in versions:
        try:
            addons_dir = ver_root / "scripts" / "addons"
            startup_dir = ver_root / "scripts" / "startup"
            addons_dir.mkdir(parents=True, exist_ok=True)
            startup_dir.mkdir(parents=True, exist_ok=True)
            _copy_tree(addon_src, addons_dir / ADDON_MODULE)
            shutil.copy2(startup_src, startup_dir / STARTUP_NAME)
            deployed.append(str(ver_root))
        except OSError as exc:
            errors.append(f"{ver_root}: {exc}")

    return {
        "ok": bool(deployed) and not errors,
        "deployed": deployed,
        "errors": errors,
        "note": (
            "Restart Blender once if it was already open so the addon loads "
            "and the socket auto-starts."
            if deployed
            else ""
        ),
    }


def _self_check() -> None:
    # Dry-run path discovery — must not throw.
    found = blender_user_roots()
    assert isinstance(found, list)
    root = Path(__file__).resolve().parents[1]
    assert (root / "assets" / ADDON_MODULE).is_dir()
    assert (root / "assets" / "startup" / STARTUP_NAME).is_file()
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        fake = Path(tmp) / "4.2"
        fake.mkdir()
        result = deploy_addon(root=root, roots=[fake])
        assert result.get("ok") is True, result
        assert (fake / "scripts" / "addons" / ADDON_MODULE / "__init__.py").is_file()
        assert (fake / "scripts" / "startup" / STARTUP_NAME).is_file()
    print("deploy_addon.py self-check ok")


if __name__ == "__main__":
    _self_check()
