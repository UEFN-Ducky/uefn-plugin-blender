# Blender connection — official Blender Lab MCP add-on

UEFN-Ducky ships the **official** Blender MCP add-on (blender.org/lab/mcp-server, Blender **5.1+**) and copies it into Blender's user extensions on plugin load. Ducky itself is the MCP server and the LLM client — there is **no** `uvx blender-mcp`, no second MCP server, no community `blendermcp` add-on.

The socket is **locked** to `localhost:9876`. There is no Settings host/port. Do not tell anyone to type a port, enable an add-on, or allow online access — the startup script does that.

## Mental model

| Layer | What it means |
|-------|----------------|
| Store plugin **Blender** enabled | Ducky has `blender_*` tools. `register()` / `blender_status` copy `extensions/user_default/mcp/` + a startup script into every `Blender/<5.1+>` user folder and start the server |
| TCP server on `localhost:9876` | Autostarts ~1.5 s after Blender opens. Untitled GUIs are relaunched once if the port is down after deploy |

**Store plugin ≠ live socket.** `blender_status` → `connected: false` after heal means Blender is not open (or a saved `.blend` session was already running before deploy — that session picks up the add-on on the next Blender start).

## Wire contract (what every `blender_*` tool does)

One request type: run Python inside Blender. The code must assign a **dict** to `result`; `print()` comes back as `stdout`; exceptions come back as the error message. The add-on's weak sandbox blocks `sys.exit`, `wm.quit_blender`, and factory/userpref resets. Ducky opens one socket per call; long jobs (renders, bakes) may take minutes — do not re-issue while one is running.

## Diagnose (agent)

1. `blender_status` (deploys + starts; may relaunch an untitled Blender).
2. `connected: false` → `blender_redeploy_addon` once. Never invent uv / GitHub / zip installs. Never ask the user to open Preferences, Allow Online Access, or type a port.
3. `connected: true` → model.

## Do not tell the user

- Install `uv`, clone GitHub `blender-mcp`, or add a Blender MCP server to Cursor/Claude config — Ducky already is that server.
- Sideload a zip into AppData by hand, or click Store → Update.
- Edit host/port, tick MCP in Preferences, or allow online access — those are automatic.
- That "Blender is open" alone means the agent can control it before `blender_status` has healed.
