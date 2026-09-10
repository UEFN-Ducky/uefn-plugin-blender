# Blender connection — official Blender Lab MCP add-on

UEFN-Ducky ships the **official** Blender MCP add-on (blender.org/lab/mcp-server, Blender **5.1+**) and copies it into Blender's user extensions on plugin enable. Ducky itself is the MCP server and the LLM client — there is **no** `uvx blender-mcp`, no second MCP server, no community `blendermcp` add-on.

## Mental model

| Layer | What it means |
|-------|----------------|
| Store plugin **Blender** enabled | Ducky has `blender_*` tools and copied `extensions/user_default/mcp/` + a startup script into every `Blender/<5.1+>` user folder |
| Add-on enabled in Blender | Preferences → Add-ons → **MCP** ticked. The startup script does this on launch (and turns on **Allow Online Access**, which the add-on requires) |
| TCP server on `localhost:9876` | Add-on preference "Server is running" — autostarts ~1 s after Blender opens |

**Store plugin ≠ live socket.** `blender_status` → `connected: false` means the Blender process is not listening, even if Blender is open.

## Wire contract (what every `blender_*` tool does)

One request type: run Python inside Blender. The code must assign a **dict** to `result`; `print()` comes back as `stdout`; exceptions come back as the error message. The add-on's weak sandbox blocks `sys.exit`, `wm.quit_blender`, and factory/userpref resets. Ducky opens one socket per call; long jobs (renders, bakes) may take minutes — do not re-issue while one is running.

## Diagnose (agent)

1. `blender_status`.
2. `connected: false` →
   - `blender_redeploy_addon` (refreshes files; reports `skipped` for Blender < 5.1).
   - Then the user steps below. Never invent uv / GitHub / zip installs.
3. `connected: true` → model. Re-run `blender_status` only after Blender was restarted.

## Teach the user

### A) Blender older than 5.1
The official add-on needs Blender 5.1+. Install 5.1 from blender.org (LTS or current), open it once, then the agent runs `blender_redeploy_addon` and you restart Blender.

### B) Blender 5.1+ open but `connected: false`
1. **Save** any unsaved `.blend`, quit Blender, reopen it — the startup script enables the add-on and starts the server.
2. Still offline: Edit → Preferences → **Add-ons** → search `MCP` → tick **MCP**; expand it → **Server is running** on, port **9876**.
3. If Blender says online access is disabled: Preferences → System → **Allow Online Access** on (the add-on refuses to start without it).
4. Confirm nothing else binds **9876** (an old nested `uvx blender-mcp` entry in an IDE `mcp.json` — remove it).

### C) Headless / CI
`blender --background --command blender_mcp` runs the same server without a UI. Screenshots are unavailable there (no viewport); everything else works.

## Do not tell the user

- Install `uv`, clone GitHub `blender-mcp`, or add a Blender MCP server to Cursor/Claude config — Ducky already is that server.
- Sideload a zip into AppData by hand, or click Store → Update.
- That "Blender is open" alone means the agent can control it.
