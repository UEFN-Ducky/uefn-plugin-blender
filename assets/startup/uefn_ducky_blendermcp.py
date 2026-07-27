"""UEFN-Ducky: ensure the Blender MCP addon is enabled on Blender startup.

Copied into Blender's scripts/startup/ by the blender desktop plugin.
Idempotent — safe if the addon is already enabled.

Important: enabling during early startup ``register()`` often fails silently
(context/prefs not ready). We defer via ``bpy.app.timers`` so the checkbox
actually flips and the TCP server can auto-start.
"""

from __future__ import annotations

_MOD = "blendermcp"
_TIMER_REGISTERED = False


def _enable_blendermcp() -> float | None:
    """Timer callback: enable addon + leave prefs saved. Return None to stop."""
    try:
        import addon_utils
        import bpy

        # Already active in this session?
        if _MOD in getattr(bpy.context.preferences, "addons", {}):
            return None

        try:
            addon_utils.enable(_MOD, default_set=True, persistent=True)
        except TypeError:
            # Older Blender signatures.
            addon_utils.enable(_MOD, default_set=True)
        except Exception as exc:
            print(f"[uefn-ducky] blendermcp enable failed: {exc}")
            return None

        # Persist so the Preferences checkbox stays on after quit.
        try:
            bpy.ops.wm.save_userpref()
        except Exception:
            pass
        print("[uefn-ducky] blendermcp enabled (deferred)")
    except Exception as exc:
        print(f"[uefn-ducky] blendermcp enable timer failed: {exc}")
    return None


def _schedule_enable() -> None:
    global _TIMER_REGISTERED
    try:
        import bpy

        if _TIMER_REGISTERED:
            return
        # Small delay so preferences + addon registry are ready.
        bpy.app.timers.register(_enable_blendermcp, first_interval=0.5)
        _TIMER_REGISTERED = True
    except Exception as exc:
        print(f"[uefn-ducky] could not schedule blendermcp enable: {exc}")


def register() -> None:
    _schedule_enable()


def unregister() -> None:
    pass


# Blender runs register() for scripts in scripts/startup/ automatically when
# the file defines register — also invoke at import for older loaders.
try:
    register()
except Exception:
    pass
