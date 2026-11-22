# murder_house notes

## Agent visual check
Compared against blueprint/spike/blender/out_house and out_styled.

- Kawara: partly passes. Gaps show bare roof boards and the ridge is correct, but the cover
  tiles dominate and the flat pans between them are barely visible, so from the roof preview
  it reads closer to rows of half-round logs than pan + cover tiles. It is denser and more
  uniform than the spike render. Needs a builder change (wider pan gap or lower cover-tile
  radius); not fixable in spec or STYLE.md. No cover tiles seen floating over bare roof.
- Plaster: mottling is visible and there are faint cracks, but at mottle 0.5 the blotches are
  high contrast grey-green and read a bit like camouflage/mold at distance. Consider lowering
  mottle (about 0.3) and the tint if the creator agrees.
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
