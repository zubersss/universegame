# Terrain tile-sheet layout (47-tile blob) — UNITY → BLENDER
Updated: 2026-10-30 · Source of truth: `Assets/_Game/Code/Runtime/Terrain/BlobAutotile.cs`

Each `terrain/<planet>/<material>` sheet is 1024×1024: 128 px tiles, 8 columns, no gutters,
cells numbered row-major from the **top-left**. Cell *i* shows the tile whose **connected
neighbours** are listed below; every other side is an exposed edge (air). Cells 47–63 are unused.
A corner (NE/SE/SW/NW) counts only when both of its adjacent sides connect. Solids connect to
any solid; water connects to water and solids. Cell 46 is the fully interior tile; cell 0 is an
isolated single block. The importer slices the grid automatically (no `.json` needed).

| Cell | Row | Col | Mask | Connected neighbours |
|------|-----|-----|------|----------------------|
| 0 | 0 | 0 | 0 | (none: isolated) |
| 1 | 0 | 1 | 1 | N |
| 2 | 0 | 2 | 4 | E |
| 3 | 0 | 3 | 5 | N+E |
| 4 | 0 | 4 | 7 | N+NE+E |
| 5 | 0 | 5 | 16 | S |
| 6 | 0 | 6 | 17 | N+S |
| 7 | 0 | 7 | 20 | E+S |
| 8 | 1 | 0 | 21 | N+E+S |
| 9 | 1 | 1 | 23 | N+NE+E+S |
| 10 | 1 | 2 | 28 | E+SE+S |
| 11 | 1 | 3 | 29 | N+E+SE+S |
| 12 | 1 | 4 | 31 | N+NE+E+SE+S |
| 13 | 1 | 5 | 64 | W |
| 14 | 1 | 6 | 65 | N+W |
| 15 | 1 | 7 | 68 | E+W |
| 16 | 2 | 0 | 69 | N+E+W |
| 17 | 2 | 1 | 71 | N+NE+E+W |
| 18 | 2 | 2 | 80 | S+W |
| 19 | 2 | 3 | 81 | N+S+W |
| 20 | 2 | 4 | 84 | E+S+W |
| 21 | 2 | 5 | 85 | N+E+S+W |
| 22 | 2 | 6 | 87 | N+NE+E+S+W |
| 23 | 2 | 7 | 92 | E+SE+S+W |
| 24 | 3 | 0 | 93 | N+E+SE+S+W |
| 25 | 3 | 1 | 95 | N+NE+E+SE+S+W |
| 26 | 3 | 2 | 112 | S+SW+W |
| 27 | 3 | 3 | 113 | N+S+SW+W |
| 28 | 3 | 4 | 116 | E+S+SW+W |
| 29 | 3 | 5 | 117 | N+E+S+SW+W |
| 30 | 3 | 6 | 119 | N+NE+E+S+SW+W |
| 31 | 3 | 7 | 124 | E+SE+S+SW+W |
| 32 | 4 | 0 | 125 | N+E+SE+S+SW+W |
| 33 | 4 | 1 | 127 | N+NE+E+SE+S+SW+W |
| 34 | 4 | 2 | 193 | N+W+NW |
| 35 | 4 | 3 | 197 | N+E+W+NW |
| 36 | 4 | 4 | 199 | N+NE+E+W+NW |
| 37 | 4 | 5 | 209 | N+S+W+NW |
| 38 | 4 | 6 | 213 | N+E+S+W+NW |
| 39 | 4 | 7 | 215 | N+NE+E+S+W+NW |
| 40 | 5 | 0 | 221 | N+E+SE+S+W+NW |
| 41 | 5 | 1 | 223 | N+NE+E+SE+S+W+NW |
| 42 | 5 | 2 | 241 | N+S+SW+W+NW |
| 43 | 5 | 3 | 245 | N+E+S+SW+W+NW |
| 44 | 5 | 4 | 247 | N+NE+E+S+SW+W+NW |
| 45 | 5 | 5 | 253 | N+E+SE+S+SW+W+NW |
| 46 | 5 | 6 | 255 | N+NE+E+SE+S+SW+W+NW |
