---
description: "Reference-match gate: compare the model's front and side silhouettes with the reference drawings by IoU (pass at 0.85 or more), 10 height bands within 5 percent and width/height drift under 3 percent"
metadata:
  label: "Silhouette IoU Gate"
---

# Silhouette IoU Gate

1. Mask the reference: alpha, else pixels more than 40 (0-255) from the border colour; keep the biggest blob, fill holes, crop to its box.
2. Render the model orthographic from the same view (front = -Y camera, side = +X camera) as a black silhouette on transparent, crop to its box.
3. Scale both to the same height (96 rows), centre them side by side.

| Metric | Pass |
|---|---|
| IoU = overlap / union | >= 0.85 |
| width per 10 height bands | 8 of 10 within 5 % |
| width / height drift | <= 3 % (warn), <= 1.5 % for hero assets |

```python
import numpy as np

def iou(a, b):  # boolean arrays, same height, centred to the same width
    w = max(a.shape[1], b.shape[1])
    pad = lambda m: np.pad(m, ((0, 0), ((w - m.shape[1]) // 2, w - m.shape[1] - (w - m.shape[1]) // 2)))
    a, b = pad(a), pad(b)
    bands = sum(abs(a[r].any(0).sum() - b[r].any(0).sum()) <= max(1, .05 * max(a[r].any(0).sum(), b[r].any(0).sum()))
                for r in np.array_split(np.arange(a.shape[0]), 10))
    return (a & b).sum() / max(1, (a | b).sum()), bands
```

Loop: build → render silhouette → IoU → fix the worst band → repeat (cap at 5 passes). Same gate as Forge `ref_compare`.

Adapted from majidmanzarpour/blender-game-skills (silhouette IoU gate; MIT) and RobLe3/cc-blender-skill (multiview fit gates; MIT).
