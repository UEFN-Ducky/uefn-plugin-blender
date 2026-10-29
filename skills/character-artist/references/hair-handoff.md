---
description: "Hair hand-off for realistic heads: scalp cap, hairline, strand groom to hair cards, card counts and atlas, brows and lashes"
metadata:
  label: "Hair cards hand-off"
---

# Hair hand-off

The head ships bald. Hair is a separate object on a scalp cap so it can swap, LOD and sort alpha on its own.

1. **Scalp cap**: duplicate the head faces above the hairline (0.86 H at the front, dropping to the ear tops and the nape). Offset it 0.5 mm. Paint a soft-edged hairline density mask; a hard line is the usual giveaway.
2. **Groom (cinematic or source)**: curves hair, guide spacing 5–8 mm, 30–80k strands, root width 0.06 mm, tip 0.01 mm. Forge: `hair(id, style=short|long|ponytail|afro|beard)`.
3. **Cards (game)**: convert clumps to strips. Budgets: short hair 80–150 cards, long hair 200–400, at 6–12k tris. Use one 2K atlas with 8–16 clump variants. Forge: `hair_cards(id, cards=120, atlas=1K)`.
4. **Layering**: lay a base layer of wide dense cards on the scalp, then mid clumps, then flyaways (5% of cards, thin). Sort the cards inner to outer.
5. **Brows and lashes**: brows are 15–25 short cards or a decal on the brows group. Lashes are 2 strips per lid with 40–70 alpha strands, the upper lashes 8–10 mm long and curving up.
6. **Material**: alpha-tested (clip 0.3) for game, plus a root-to-tip gradient, anisotropic highlight and a darker root. Never use alpha blend on the main cards.

## Done when

A three-quarter screenshot shows no visible scalp through the parting except at the hairline fade, no sorting flicker, and tris within budget.

---
MIT, uefn-ducky; own words.
