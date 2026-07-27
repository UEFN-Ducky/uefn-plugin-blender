# Blender connection — teach the user when not detected

## Mental model (say this clearly)

| Layer | What it means |
|-------|----------------|
| Store plugin **Blender** enabled | UEFN-Ducky has `blender_*` tools + copies addon files into Blender’s user folder |
| Addon files on disk | `…/Blender/<version>/scripts/addons/blendermcp/` exists |
| Addon **enabled** in Blender Preferences | Checkbox on — required. Copying files does **not** turn the checkbox on by itself |
| TCP server on `localhost:9876` | BlenderMCP sidebar → Connect, or auto-start after enable + restart |

**Store plugin ≠ live socket.** `blender_status` → `connected: false` means the Blender process is not listening, even if Blender is open.

## Diagnose (agent)

1. Call `blender_status`.
2. If `connected: false`:
   - Call `blender_redeploy_addon` (refreshes files for every Blender version folder found).
   - Tell the user the exact UI steps below — do **not** invent uv/GitHub installs.
3. After they enable / Connect, call `blender_status` again before modeling.

## Teach the user (copy these steps)

### A) Addon missing from Preferences search

1. In UEFN-Ducky: Settings → Store → Blender → Enable (or Update).
2. Ask the agent to run `blender_redeploy_addon`, **or** restart UEFN-Ducky after enable.
3. **Save** any unsaved `.blend`, quit Blender, reopen (startup script enables the addon).

### B) Addon listed but checkbox **off** (your case)

1. Blender → **Edit → Preferences → Add-ons**.
2. Search `blender mcp` / `blendermcp`.
3. **Tick the checkbox** for **Blender MCP**.
4. Close Preferences.
5. Press **N** in the 3D Viewport → **BlenderMCP** tab → **Connect to MCP server** (if the socket did not auto-start).
6. Optional: save user preferences if Blender prompts.

### C) Checkbox on, still `connected: false`

1. **N** → BlenderMCP → **Connect to MCP server**.
2. Confirm nothing else binds port **9876** (old nested `uvx blender-mcp` in AppData `mcp.json` — disable that entry).
3. Restart Blender once after first install.

## Do not tell the user

- Install `uv` / clone GitHub `blender-mcp`
- Sideload a zip into AppData by hand
- That “Blender is open” alone means the agent can control it
