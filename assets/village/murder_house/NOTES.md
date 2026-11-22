# murder_house notes

## Agent visual check
Compared against blueprint/spike/blender/out_house and out_styled.

- Kawara (rebuilt 2026-11-21, kawara v2): passes. The roof now reads as tiles, not logs:
  wide shallow pans with narrow round covers over the joints, laid in ~1.1-stud courses that
  each step up and end in a lip, so clear horizontal course lines run across the slope.
  Missing tiles show bare roof boards; slipped tiles sit skewed and proud. Remaining nits:
  the covers are fairly low-contrast against the pans in the flat preview light, so up close
  it leans toward "stepped shingles with ribs" more than deeply sculpted kawara. Damage density
  (missing + slipped + jitter) makes the roof look busy in the roof preview.
- Plaster (rebuilt): the green-grey camouflage came mostly from moss, which tiled bakes apply
  everywhere (no position info), not from mottle. aged_plaster now skips moss, mottle is 0.28,
  and mottle darkens/yellows the plaster's own colour. It reads as pale aged plaster now; if
  anything a bit clean at distance. Moss stays on the wainscot, base and roof.
- Dust: on the console tops it reads as a muted film, not mold. Water stains and grime give
  a slight green cast on the drawer fronts that is a little mold-like.
- Decal smear: first build was NOT visible (plane at y=-0.7 sat inside the proud drawer
  fronts). Moved the decal to y=-0.78 and rebuilt once. Now a faint, muted dark-brown smear is visible on the top drawer front and left edge; subtle, non-graphic, not black or red.
- Cabinet handles: rusted iron reads as dark metal with rust blotches; metalness looks low but
  they still read as iron hardware.
- Opening: dark interior with light bleeding through the back lattice, door ajar; reads well.

## Creator verdict: PENDING
Show the creator these previews:
- wide: assets/village/murder_house/out/previews/preview_wide.png
- close_opening: assets/village/murder_house/out/previews/preview_close_opening.png
- roof: assets/village/murder_house/out/previews/preview_roof.png
