# Art v7: the surveyor as frame sheets or as a live skinned mesh

UNITY, 2026-11-10 15:1x, for LEAD (asked 15:0x). One page. **M** = read from a file or measured on this machine;
**E** = my estimate, with what would replace it. Nothing below was run for this page: the RAM gate is shut.

## What ships today (M), because both answers hang on it

- The Editor's sprite packer is OFF (`ProjectSettings/EditorSettings.asset`: `m_SpritePackerMode: 0`), and the built
  player's probe says so too: every leg of 0.6.3's probe reads `"atlases":0,"packedSprites":0`
  (logs/memory_probe_20261110_104051.jsonl). The sixteen `.spriteatlasv2` files under Settings/Atlases are never packed.
- So a frame sheet ships AS BLENDER WROTE IT: one texture a PNG, frames on its grid, each frame's empty margin included,
  in the PNG's own import format. BLENDER's price list (pages x 16 MB or x 4 MB) is therefore the true memory, and the
  Bible's "8 atlases a planet" is not what limits us: the 512 MB of loaded textures is.
- The surveyor draws as ONE SpriteRenderer; the Animator swaps the sprite; one pivot for every frame of a sheet
  (ArtImporter.PivotFor); the hand, tip, grip and stow tables are metres from that pivot, per drawing.

## Trimmed frames on the side-sheet pipeline: YES, with BLENDER's exporter doing the packing

- A Unity sprite is a rectangle AND its own pivot, and the pivot may lie outside the rectangle. So a frame cut to its
  ink draws exactly where the whole box drew if its pivot is moved by the cut: `pivot = (boxPivot_px - cutOffset_px) /
  cutSize_px`. The Animator, the sockets (measured from the pivot), SpriteCharacterView and the normal sheet (same
  layout) need no change.
- What I need in the sheet's json, per drawing, beside today's `frame_width / frame_height / pivot` (kept as the BOX):
  `"cuts": [[x, y, w, h, ox, oy], ...]`: the cut's place on the page (x, y from the top-left, as today) and where its
  bottom-left sat inside the box (ox, oy). Absent: the grid, as today. Cuts keep the 4 px gutter and stay unrotated.
- My side: `ArtImporter.SliceIfNeeded` reads the cuts (about half a day with ArtImporterTests: a cut frame's sprite
  bounds and pivot against the whole frame's, to a pixel). The exporter's side: a shelf packer over the trimmed boxes.
- NOT the other way (switching Unity's packer on): it would repack every sprite of the game at once, set formats per
  atlas (D-197's wall and backdrop formats), and pack in the Editor on an 8 GB machine. Not for a pilot.
- What it buys (E, from BLENDER's 28 % standing / 70 % digging ink): 13 pages at ppu 192 become about 7:
  104 MB -> about 56 MB as BC7 + BC5. To replace the estimate: slice 1's 100 drawings packed once by the exporter.

## The live skinned mesh in the 2D renderer

**How it would have to be drawn.** Not as a mesh standing in the scene: a mesh that hides its own far arm must write
depth, and depth written at the figure then cuts every sprite drawn later at z 0 (a foreground leaf, the reticle):
the fault U-212 just fixed on block ground (marks drawn behind the block mesh). The workable form is a LIVE IMPOSTOR:
each frame the skinned figure is drawn into a small render texture (432 x 480 at ppu 192, colour and normal, 4x MSAA
for the edge), and that texture is shown on today's surveyor quad. Then:
- **Sorting**: exactly today's (one quad at SurveyorOrder; play_front, foreground, reticle and finds unchanged).
- **Light**: the painted light CANNOT be baked per pose. What is left: (a) painted albedo with a pose-free occlusion
  painted in, lit in the impostor's own pass by ONE direction (the stage file's sun) through a painted ramp, with no
  cast shadow of an arm on the body; (b) the game's 2D lights through the impostor's normal texture, as for a sprite.
  That is "a lit model with painted textures", not "a render painted per drawing": the Cycles light, the bounce and
  the paint pass over the whole figure (the brushed edge, strokes that cross form) are what B-258 part 1 judged as
  the look, and none of it survives. This is the real cost, and it is a look question, LEAD's and the owner's.
- **Cost on the Intel chip (E)**: skinning 6-10 k vertices on 40-60 bones and two small passes: 0.3-0.6 ms a frame
  and 3-4 draw calls; memory about 10-20 MB (one 2048 colour + normal, the mesh, 16 s of clips) against 104 MB (56
  trimmed). To replace the estimate: a stand-in rigged figure (any CC0 base mesh) on the built player's probe, one
  lock; I can card it as a half-day experiment if wanted.
- **The dig's contact and sockets**: better than sheets. The hand, the tool's grip and the stow point are bones (exact
  on every frame, no tables); the blade can be put ON the contact by a two-bone arm solve at any reach and angle, so
  the slide / lunge rule, the far-reach and low `dig_up` drawings (B-252) and the 0.13-0.21 m buried tip all go.
  Pace by ground speed is free (no doubled drawings); 12 drawings a second can be kept by stepping the clip.
- **What breaks or is new work**: a rigged-model import path for a character with clips (the October 3D code has
  static and rig-set models, not a skinned character); cloth, straps and the antenna baked to extra bones or run as
  springs; a render feature for the impostor pass; the film pass and the iris must take it (they see a sprite, so
  likely nothing); every creature would follow the same road or stay a sheet.

## My read

- For the pilot: SHEETS, as ruled (12 a second, ppu 192), TRIMMED. It keeps the one thing the method is for (light and
  paint per drawing), needs half a day of importer work, and its memory is known: about 56 MB compressed.
- The live impostor is the answer to a different problem: MEMORY AT SCALE (thirty species as painted sheets will not fit
  512 MB; thirty rigs will) and exact contact. It should be priced once on the built player with a stand-in, and judged
  by eye beside a sheet figure, before any creature is carded as v7. It is not a reason to delay the surveyor.
- Either way the compression A/B (U-217) decides more than this choice does: uncompressed, even trimmed sheets are 224 MB.
