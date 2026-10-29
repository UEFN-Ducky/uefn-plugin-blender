# Compare a model to its reference silhouette

Measure instead of eyeballing. Project the mesh orthographically (front = XZ, side = YZ), compare with the reference drawing's silhouette, and report numbers you can act on.

| Check | Pass |
|---|---|
| Silhouette IoU | ≥ 0.85 |
| Width in each of 10 height bands | within 5 % of the reference |
| Bounding-box aspect drift | ≤ 1.5 % (front), ≤ 3 % (side) |

The worst band names where to sculpt: band 0 is the feet, band 9 the top of the head.

```python
import bpy, numpy as np

def _mesh_mask(ob, axes=(0, 2), n=128):
    me = ob.data; me.calc_loop_triangles(); mw = np.array(ob.matrix_world)
    co = np.array([v.co[:] + (1.0,) for v in me.vertices]) @ mw.T
    p = co[:, list(axes)]; lo, hi = p.min(0), p.max(0); p = (p - lo) / (hi - lo).max() * (n - 1)
    w, h = int(np.ceil((hi - lo)[0] / (hi - lo).max() * (n - 1))) + 1, int(np.ceil((hi - lo)[1] / (hi - lo).max() * (n - 1))) + 1
    mask = np.zeros((h, w), bool); yy, xx = np.mgrid[0:h, 0:w]
    for t in me.loop_triangles:
        a, b, c = p[list(t.vertices)]
        x0, y0 = np.floor(np.minimum(np.minimum(a, b), c)).astype(int); x1, y1 = np.ceil(np.maximum(np.maximum(a, b), c)).astype(int) + 1
        X, Y = xx[y0:y1, x0:x1] + .5, yy[y0:y1, x0:x1] + .5
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12: continue
        l1 = ((b[1] - c[1]) * (X - c[0]) + (c[0] - b[0]) * (Y - c[1])) / d
        l2 = ((c[1] - a[1]) * (X - c[0]) + (a[0] - c[0]) * (Y - c[1])) / d
        mask[y0:y1, x0:x1] |= (l1 >= -1e-6) & (l2 >= -1e-6) & (1 - l1 - l2 >= -1e-6)
    return mask[::-1]  # row 0 = top

def _image_mask(path, shape):
    img = bpy.data.images.load(path, check_existing=True); w, h = img.size
    px = np.array(img.pixels[:]).reshape(h, w, 4)[::-1]
    solid = (px[..., 3] > .5) & (px[..., :3].mean(-1) < .9)  # not transparent, not white
    ys, xs = np.nonzero(solid); solid = solid[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    ry = np.linspace(0, solid.shape[0] - 1, shape[0]).astype(int); rx = np.linspace(0, solid.shape[1] - 1, shape[1]).astype(int)
    return solid[np.ix_(ry, rx)], solid.shape[1] / solid.shape[0]

def ref_compare(ob, front, side=None):
    out = []
    for view, path, axes, tol in (("front", front, (0, 2), .015), ("side", side, (1, 2), .03)):
        if not path: continue
        m = _mesh_mask(ob, axes); r, aspect = _image_mask(path, m.shape)
        iou = (m & r).sum() / max(1, (m | r).sum())
        bands = np.array_split(np.arange(m.shape[0]), 10)[::-1]  # band 0 = bottom
        diff = [abs(m[b].any(0).sum() - r[b].any(0).sum()) / max(1, r[b].any(0).sum()) for b in bands]
        drift = abs(m.shape[1] / m.shape[0] - aspect) / aspect
        worst = int(np.argmax(diff))
        ok = iou >= .85 and max(diff) <= .05 and drift <= tol
        out.append(f"{view}: IoU {iou:.2f}, worst band {worst} {diff[worst]:.0%}, aspect drift {drift:.1%} -> {'PASS' if ok else 'FIX'}")
    return "; ".join(out)

# Self-contained example: an ellipse drawing vs a scaled sphere.
import os, tempfile
W, H = 200, 300; yy, xx = np.mgrid[0:H, 0:W]
ell = ((xx - 100) / 80) ** 2 + ((yy - 150) / 120) ** 2 <= 1
px = np.ones((H, W, 4)); px[ell, :3] = 0.2
img = bpy.data.images.new("ref_front", W, H); img.pixels[:] = px.ravel()
path = os.path.join(tempfile.gettempdir(), "ref_front.png"); img.filepath_raw = path; img.file_format = "PNG"; img.save()
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=48, ring_count=24); body = bpy.context.active_object
body.scale = (0.8, 0.8, 1.2); bpy.context.view_layer.update()
print(ref_compare(body, path))
```

**Done when:** every view prints `PASS`. On `FIX`, sculpt the worst band (inflate or deflate there), re-run, and stop after 3 rounds to ask whether the reference or the model is right.

---
Adapted from the R2 survey's reference-matching checks (silhouette IoU, height bands, bounding-box drift) and Blender Agent Skills by EL4CTEO, MIT licence.
