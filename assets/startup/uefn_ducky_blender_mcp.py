"""UEFN-Ducky: make the official Blender Lab MCP add-on live on Blender startup.

Copied into ``<version>/scripts/startup/`` by the blender desktop plugin.
Idempotent. Defers via ``bpy.app.timers`` because prefs are not ready inside
startup ``register()``.

Does three things, in order:
1. Allow Online Access (the official add-on refuses to start without it).
2. Disable the old community ``blendermcp`` add-on (same port 9876).
3. Enable ``bl_ext.user_default.mcp`` and start its server.
"""

from __future__ import annotations

_OFFICIAL = "bl_ext.user_default.mcp"
_LEGACY = "blendermcp"
_SCHEDULED = False


def _enable() -> float | None:
    try:
        import addon_utils
        import bpy

        prefs = bpy.context.preferences
        if hasattr(prefs.system, "use_online_access") and not prefs.system.use_online_access:
            prefs.system.use_online_access = True

        if _LEGACY in prefs.addons:
            try:
                addon_utils.disable(_LEGACY, default_set=True)
            except Exception as exc:  # noqa: BLE001
                print(f"[uefn-ducky] could not disable {_LEGACY}: {exc}")

        if _OFFICIAL not in prefs.addons:
            try:
                addon_utils.enable(_OFFICIAL, default_set=True, persistent=True)
            except TypeError:
                addon_utils.enable(_OFFICIAL, default_set=True)
            except Exception as exc:  # noqa: BLE001
                print(f"[uefn-ducky] enable {_OFFICIAL} failed: {exc}")
                return None
            try:
                bpy.ops.wm.save_userpref()
            except Exception:  # noqa: BLE001
                pass

        # Autostart timer is registered on enable; nudge once in case it is off.
        try:
            from bl_ext.user_default.mcp import mcp_to_blender_server as srv  # type: ignore

            if not srv.is_running():
                bpy.ops.blmcp.server_start()
        except Exception:  # noqa: BLE001
            pass
        print(f"[uefn-ducky] {_OFFICIAL} ready")
    except Exception as exc:  # noqa: BLE001
        print(f"[uefn-ducky] blender mcp enable timer failed: {exc}")
    return None


def register() -> None:
    global _SCHEDULED
    if _SCHEDULED:
        return
    try:
        import bpy

        bpy.app.timers.register(_enable, first_interval=1.5)
        _SCHEDULED = True
    except Exception as exc:  # noqa: BLE001
        print(f"[uefn-ducky] could not schedule blender mcp enable: {exc}")


def unregister() -> None:
    pass


try:
    register()
except Exception:  # noqa: BLE001
    pass
