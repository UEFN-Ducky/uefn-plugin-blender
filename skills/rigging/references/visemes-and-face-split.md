---
description: "Lip-sync visemes as ARKit shape-key mixes (Oculus / Ready Player Me viseme_ names), left/right shape-key splits with a soft centre falloff, and a report of shape keys that move nothing"
metadata:
  label: "Visemes and Face Split"
---

# Visemes and Face Split

## 15 visemes from ARKit keys

`viseme_sil` is the rest pose. Build each as a new key from a mix of existing ARKit keys (`L+R` = both sides).

| Viseme | Mix |
|---|---|
| PP | mouthClose 1, mouthPress L+R .5 |
| FF | mouthRollLower .6, mouthUpperUp L+R .3 |
| TH | jawOpen .2, tongueOut .4 |
| DD | jawOpen .3, mouthStretch L+R .2 |
| kk | jawOpen .35, mouthStretch L+R .3 |
| CH | mouthFunnel .6, jawOpen .2 |
| SS | mouthStretch L+R .5, jawOpen .1 |
| nn | jawOpen .25, mouthClose .2 |
| RR | mouthFunnel .4, jawOpen .2 |
| aa | jawOpen .7 |
| E | jawOpen .35, mouthStretch L+R .5 |
| ih | jawOpen .25, mouthSmile L+R .3 |
| oh | jawOpen .5, mouthFunnel .5 |
| ou | mouthPucker .8, jawOpen .15 |

```python
import bpy
def mix_key(obj, name, mix):
    keys = obj.data.shape_keys.key_blocks
    for k in keys: k.value = 0
    for n, w in mix.items(): keys[n].value = w
    new = obj.shape_key_add(name=name, from_mix=True)
    for k in keys: k.value = 0
    return new
# mix_key(head, "viseme_aa", {"jawOpen": .7})
```

## Split a key into _L and _R

Left is +X. A smoothstep over 10 % of the head width keeps the centre seamless (L + R = the original).

```python
def split_lr(obj, name, soft=0.1):
    me, keys = obj.data, obj.data.shape_keys.key_blocks
    xs = [v.co.x for v in me.vertices]; cx = (min(xs) + max(xs)) / 2; half = soft * (max(xs) - min(xs))
    src, basis = keys[name], keys[0]
    for side, sgn in (("_L", 1), ("_R", -1)):
        k = obj.shape_key_add(name=name + side, from_mix=False)
        for i, v in enumerate(me.vertices):
            t = min(1, max(0, (sgn * (v.co.x - cx) + half) / (2 * half))); w = t * t * (3 - 2 * t)
            k.data[i].co = basis.data[i].co + (src.data[i].co - basis.data[i].co) * w
```

## Report

A key whose largest offset from Basis is under 0.0001 m moves nothing: sculpt it or delete it before export (engines import it as a dead morph target).

Adapted from Blender Agent Skills by EL4CTEO (rigging, face shapes; MIT). Same as Forge `face_shapes(visemes, split, report)`.
