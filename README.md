# Blender

Control Blender for 3D modeling and export to UEFN. Installs the Blender addon automatically — open Blender after enabling.

Desktop plugin for [UEFN-Ducky](https://github.com/UEFN-Ducky/UEFN-Ducky) (`blender`).
Install or update from **Settings → Store** in the app — do not install from a zip by hand.

## Build

```bash
py scripts/build_zip.py
```

Writes `deploy/blender-1.0.17.ducky-plugin.zip` (scripts/ and deploy/ are not packed).
