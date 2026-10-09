# Blender

**Requires Blender 5.1+.** 4.x will not connect. Control Blender for 3D modeling and export to UEFN via the official [Blender Lab MCP add-on](https://www.blender.org/lab/mcp-server/). The add-on is installed and started automatically on `localhost:9876` — open Blender 5.1+. There is no host/port setting.

Desktop plugin for [UEFN-Ducky](https://github.com/UEFN-Ducky/UEFN-Ducky) (`blender`).
Install or update from **Settings → Store** in the app — do not install from a zip by hand.

## Build

```bash
py scripts/build_zip.py
```

Writes `deploy/blender-1.0.17.ducky-plugin.zip` (scripts/ and deploy/ are not packed).

## Next release: ship compiled

This plugin still ships its Python source on the Store. Its next release has to ship compiled and signed, the way Ducky Account and Roguelike do:

1. Give `scripts/release.py` and `scripts/build_zip.py` the compiled build from `uefn-plugin-account` (`build_compiled_zip`, upload by ticket, `--plain` only as an escape hatch).
2. Bump `version` and set `min_app_version` to `1.2.356` or newer.
3. Publish, then check the download with the start-up license check (signature, id and version, compiled, team access), not only the signature.
4. The Store must hold the version back from apps older than `min_app_version`. Until it does, older apps install a build they can't run.

For this plugin:

- The Blender add-on is copied into Blender as-is; only the Ducky-side backend compiles.

Remove this section once a compiled version is live.

## License

MIT. Copyright (c) 2026 Mindful Path Company, LLC. See [LICENSE](LICENSE).

`assets/mcp/` is the official Blender MCP add-on, vendored unmodified — GPL-3.0-or-later, Copyright Blender Authors. See [assets/mcp/LICENSE.txt](assets/mcp/LICENSE.txt). Nothing in `backend/` or `skills/` imports it; it is copied into Blender and spoken to over TCP.
