# Blender

Control Blender 5.1+ for 3D modeling and export to UEFN via the official [Blender Lab MCP add-on](https://www.blender.org/lab/mcp-server/). The add-on is installed into Blender automatically — open Blender after enabling.

Desktop plugin for [UEFN-Ducky](https://github.com/UEFN-Ducky/UEFN-Ducky) (`blender`).
Install or update from **Settings → Store** in the app — do not install from a zip by hand.

## Build

```bash
py scripts/build_zip.py
```

Writes `deploy/blender-1.0.17.ducky-plugin.zip` (scripts/ and deploy/ are not packed).

## License

MIT. Copyright (c) 2026 Mindful Path Company, LLC. See [LICENSE](LICENSE).

`assets/mcp/` is the official Blender MCP add-on, vendored unmodified — GPL-3.0-or-later, Copyright Blender Authors. See [assets/mcp/LICENSE.txt](assets/mcp/LICENSE.txt). Nothing in `backend/` or `skills/` imports it; it is copied into Blender and spoken to over TCP.
