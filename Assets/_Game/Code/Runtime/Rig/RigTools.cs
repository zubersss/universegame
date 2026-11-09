using Meridian.Terrain;
using UnityEngine;

namespace Meridian.Rig
{
    /// <summary>
    /// The Rig's M1 modules (Bible §8): Beam digs a solid tile and drops its item; Builder places
    /// a tile into air or water. Reach is measured from the owner. Input wiring comes with the
    /// player controller (U-009); these are the actions it calls.
    /// U-157 (D-162, Bible 5.0 (b)): on a smooth planet both are a round brush over the hidden grid: the Beam carves every solid tile whose
    /// centre lies within BrushRadius of the point (a rounded, ink-rimmed scoop once traced; each tile drops its item as before), and the
    /// Builder piles the planet's one ground material back into the open tiles there as a rounded mound, spending one ground item (any dug
    /// material the player carries) per tile, never covering a body (D-165). No block type is chosen: there is no hotbar of blocks.
    /// </summary>
    public sealed class RigTools : MonoBehaviour
    {
        /// <summary>Tool reach in meters (Bible is silent; P-09).</summary>
        public const float Reach = 5f;
        /// <summary>U-157: the round brush's radius (m): a stroke works the 1 to 4 tiles whose centres lie within it. U-175: 0.9 m plus the
        /// Dig branch's, under the expedition factor.</summary>
        public static float BrushRadius => Meridian.Progress.SkillStats.BrushRadius;

        public TerrainStreamer terrain;
        public ItemDrops drops;
        public Transform owner;
        /// <summary>Where Builder material comes from and dug items go (GameState's; U-045, closes D-021).</summary>
        public Meridian.Items.Inventory inventory;
        /// <summary>U-174 (D-174): the dirt store a dug matrix tile goes into and the Builder spends (GameState's).</summary>
        [System.NonSerialized] public Meridian.Mining.DirtStore dirt; // GameState's (a serialized field would get its own empty store)
        /// <summary>U-174: the dirt store (GameState's unless one was set).</summary>
        public Meridian.Mining.DirtStore Dirt => dirt ??= Meridian.Core.GameState.Instance != null ? Meridian.Core.GameState.Instance.dirt : null;
        /// <summary>U-174: the Beam's power (1 at the start; U-175: the Dig branch raises it): a stroke's time divides by it. Setting it pins
        /// a value (tests); 0 or less: the tree's again.</summary>
        public float BeamPower { get => beamPin > 0f ? beamPin : Meridian.Progress.SkillStats.BeamPower; set => beamPin = value; }
        /// <summary>U-193: the dig tool now (the shovel until The Beam) and its power (a pinned BeamPower overrides either, tests).</summary>
        public DigTool Tool => Meridian.Progress.SkillStats.DigTool;
        public float DigPower => beamPin > 0f ? beamPin : Meridian.Progress.SkillStats.DigPower;
        float beamPin;
        /// <summary>U-174: raised when a dug tile gives dirt (true: into the store; false: the store was full, a puff only).</summary>
        public event System.Action<bool> DirtDug;
        /// <summary>Raised after the Beam removes a tile (U-032 dig animation).</summary>
        public event System.Action<Vector2> Dug;
        /// <summary>U-157: raised after the Builder piles a mound (its puff).</summary>
        public event System.Action<Vector2> Mounded;

        void Start()
        {
            if (inventory == null && Meridian.Core.GameState.Instance != null) inventory = Meridian.Core.GameState.Instance.inventory;
            if (dirt == null && Meridian.Core.GameState.Instance != null) dirt = Meridian.Core.GameState.Instance.dirt;
            if (drops != null && drops.collector == null) drops.collector = owner;
            if (drops != null && drops.inventory == null) drops.inventory = inventory;
        }

        public static Vector2Int TileOf(Vector2 world) =>
            new Vector2Int(Mathf.FloorToInt(world.x), Mathf.FloorToInt(world.y));

        /// <summary>U-157: the round brush is the tool on this planet (its ground is the smooth outline).</summary>
        public bool Brush => terrain != null && terrain.SmoothGround;

        bool InReach(Vector2Int tile)
        {
            if (owner == null) return true;
            var centre = new Vector2(tile.x + 0.5f, tile.y + 0.5f);
            return (centre - (Vector2)owner.position).sqrMagnitude <= Reach * Reach;
        }

        bool InReach(Vector2 point) => owner == null || (point - (Vector2)owner.position).sqrMagnitude <= Reach * Reach;

        /// <summary>U-193: within the dig tool's reach (the shovel's 2 m, the Beam's Reach) of the owner's body (its Rigidbody2D: the transform
        /// trails an interpolated body, and a body set while not simulated until the next physics step); building keeps Reach.</summary>
        bool InDigReach(Vector2 point)
        {
            if (owner == null) return true;
            float r = Meridian.Progress.SkillStats.DigReach;
            return (point - OwnerAt).sqrMagnitude <= r * r;
        }

        /// <summary>U-193: the owner's position as physics holds it (its Rigidbody2D's, else the transform's).</summary>
        Vector2 OwnerAt
        {
            get
            {
                if (bodyOf != owner) { bodyOf = owner; ownerBody = owner != null ? owner.GetComponent<Rigidbody2D>() : null; }
                return ownerBody != null ? ownerBody.position : (Vector2)owner.position;
            }
        }
        Transform bodyOf;
        Rigidbody2D ownerBody;

        /// <summary>The dig tool (the shovel, then the Beam): removes the solid tile at the world point (on a smooth planet, the brush's
        /// tiles) and spawns its item.</summary>
        public bool Dig(Vector2 world)
        {
            var t = TileOf(world);
            if (terrain == null || !InDigReach(Brush ? world : new Vector2(t.x + 0.5f, t.y + 0.5f))) return false;
            // U-056: base pieces come down first (their item comes back).
            if (dismantle != null && dismantle(world)) { Dug?.Invoke(world); return true; }
            // U-059: harvestable props first (Mercury's Solarite crystals): -1 not one, 0 glanced off, 1 cut.
            if (harvest != null)
            {
                int h = harvest(world);
                if (h >= 0)
                {
                    if (h > 0) Dug?.Invoke(world);
                    return h > 0;
                }
            }
            // U-158: the planet's resource nodes (and any other harvester) next.
            for (int i = 0; i < harvesters.Count; i++)
            {
                int h = harvesters[i](world);
                if (h < 0) continue;
                if (h > 0) Dug?.Invoke(world);
                return h > 0;
            }
            if (Brush) return DigBrush(world);
            byte id = terrain.GetTile(t.x, t.y);
            if (!TileId.IsSolid(id)) return false;
            if (!terrain.SetTile(t.x, t.y, TileId.Air)) return false;
            Dug?.Invoke(world);
            DropFor(id, t.x, t.y);
            return true;
        }

        /// <summary>U-157: the Beam's round scoop: every solid tile within BrushRadius of the point, one outline rebuild per chunk.</summary>
        bool DigBrush(Vector2 p)
        {
            int dug = 0;
            ShapeRead(p); // D-168: the field as drawn before any tile flips (a dug tile's node must not read 0 where the disc says 0.49)
            terrain.BeginBatch();
            try
            {
                foreach (var c in BrushCells(p))
                {
                    byte id = terrain.GetTile(c.x, c.y);
                    if (!TileId.IsSolid(id) || !terrain.SetTile(c.x, c.y, TileId.Air)) continue;
                    dug++;
                    DropFor(id, c.x, c.y);
                }
                // D-168: a mound's rounded skirt can stand in tiles the grid still holds open; the drawn ground there carves too (no item).
                if (dug == 0 && terrain.FieldAt(p) >= GroundField.Iso) dug = -1;
                if (dug != 0) ShapeApply(p, true, null);
            }
            finally { terrain.EndBatch(); }
            if (dug == 0) return false;
            Dug?.Invoke(p);
            return true;
        }

        /// <summary>U-174: the planet digs by the D1 tables (Earth, Mars, Mercury, Venus): strokes take time and tiles give dirt or a material.</summary>
        public bool D1 => terrain != null && terrain.Config != null && Meridian.Mining.D1Tables.Current.PlanetOf(terrain.Config.id) != null;

        /// <summary>U-174: a Beam stroke's time at p (0 where the planet does not dig by the D1 tables: a stroke a frame, as before).</summary>
        public float StrokeSeconds(Vector2 p) => D1 ? Meridian.Mining.DigRun.StrokeSeconds(terrain, p, DigPower, Tool) : 0f;

        /// <summary>The dug tile's item (and the planet's only-here finds) at the tile's centre.</summary>
        void DropFor(byte id, int x, int y)
        {
            if (D1) { DropD1(x, y); return; }
            int item = Meridian.Items.ItemRegistry.DropOf(id);
            // U-059: "only here" finds (Mars perchlorate deposits, Earth living seed).
            int depth = terrain.Generator != null ? terrain.Generator.SurfaceHeight(terrain.WrapX(x)) - y : 0;
            var (replace, bonus) = Meridian.Items.OnlyHere.DropAt(terrain.Config.id, id, terrain.WrapX(x), y, depth);
            if (replace != 0) item = replace;
            if (drops != null && item != 0)
            {
                // U-157: on a smooth planet the drop shows its item's icon, never a block tile (D-161: no blocks drawn).
                var tile = replace != 0 || Brush ? null : terrain.TileSet.Get(id, 0) as UnityEngine.Tilemaps.Tile;
                drops.Spawn(item, new Vector2(x + 0.5f, y + 0.5f), tile != null ? tile.sprite : null);
            }
            if (drops != null && bonus != 0) drops.Spawn(bonus, new Vector2(x + 0.5f, y + 0.7f), null);
        }

        /// <summary>
        /// U-174 (D1_TABLES §1): a dug tile gives either dirt into the dirt store (full: a puff, nothing lost but the dirt) or, by its depth
        /// tier's material chance, a material from the planet's tier table, dropped at the tile for the pack (refused past the weight limit, it
        /// stays on the ground). The rolls hash the cell and the world seed: the same tile always gives the same. U-059's only-here finds stay.
        /// </summary>
        void DropD1(int x, int y)
        {
            var tables = Meridian.Mining.D1Tables.Current;
            var pid = terrain.Config.id;
            int wx = terrain.WrapX(x);
            var centre = new Vector2(x + 0.5f, y + 0.5f);
            int tier = Meridian.Mining.DigRun.TierAt(terrain, centre);
            int seed = Meridian.Core.GameState.Instance != null ? Meridian.Core.GameState.Instance.worldSeed : 1969;
            Meridian.Mining.DigRun.Rolls(wx, y, seed, out float materialRoll, out float pickRoll);
            bool coldTrap = pid == Meridian.Planets.PlanetId.Mercury && MercuryLandforms.PermanentShadow(wx, terrain.Config.worldWidth);
            int item = tables.Roll(pid, tier, materialRoll, pickRoll, coldTrap);
            if (item != 0) { if (drops != null) drops.Spawn(item, centre, null); }
            else
            {
                var store = Dirt;
                bool stored = store != null && store.Add(1) == 1;
                DirtDug?.Invoke(stored);
            }
            int depth = terrain.Generator != null ? terrain.Generator.SurfaceHeight(wx) - y : 0;
            var (_, bonus) = Meridian.Items.OnlyHere.DropAt(pid, terrain.GetTile(x, y), wx, y, depth);
            if (drops != null && bonus != 0) drops.Spawn(bonus, new Vector2(x + 0.5f, y + 0.7f), null);
        }

        /// <summary>U-157: the tiles a brush stroke at p works, nearest first.</summary>
        public static System.Collections.Generic.List<Vector2Int> BrushCells(Vector2 p)
        {
            var cells = new System.Collections.Generic.List<Vector2Int>(4);
            int x0 = Mathf.FloorToInt(p.x - BrushRadius), x1 = Mathf.FloorToInt(p.x + BrushRadius);
            int y0 = Mathf.FloorToInt(p.y - BrushRadius), y1 = Mathf.FloorToInt(p.y + BrushRadius);
            for (int y = y0; y <= y1; y++)
                for (int x = x0; x <= x1; x++)
                    if ((new Vector2(x + 0.5f, y + 0.5f) - p).sqrMagnitude <= BrushRadius * BrushRadius) cells.Add(new Vector2Int(x, y));
            if (cells.Count == 0) cells.Add(TileOf(p)); // a point near a tile corner still takes its own tile
            cells.Sort((a, b) => (new Vector2(a.x + 0.5f, a.y + 0.5f) - p).sqrMagnitude.CompareTo((new Vector2(b.x + 0.5f, b.y + 0.5f) - p).sqrMagnitude));
            return cells;
        }

        /// <summary>U-059: a harvestable at the Beam's point (set by SolariteCrystals on Mercury).</summary>
        public System.Func<Vector2, int> harvest;
        /// <summary>U-158: more harvestables at the Beam's point, tried in order after `harvest` (-1 none there, 0 glanced off, 1 harvested).</summary>
        public readonly System.Collections.Generic.List<System.Func<Vector2, int>> harvesters = new System.Collections.Generic.List<System.Func<Vector2, int>>(2);
        /// <summary>U-056: the Beam on a base piece (BaseBuilder.Dismantle); the Builder with a base-piece item (BaseBuilder.PlaceItem).</summary>
        public System.Func<Vector2, bool> dismantle;
        public System.Func<Vector2, int, bool> placePiece;

        /// <summary>
        /// Builder (player input): a base-piece item builds that piece; else, on a smooth planet, a mound of the planet's ground material
        /// spending ground items; on a block planet, the inventory's selected material, one used up. Nothing to place: no placement.
        /// </summary>
        public bool Place(Vector2 world)
        {
            if (inventory == null) return false;
            // U-056: a base-piece item (wall, door, lamp, crate, deck, float cell) builds that piece.
            var held = inventory[inventory.Selected];
            if (!held.IsEmpty && placePiece != null && InReach(TileOf(world)) && placePiece(world, held.itemId))
            {
                inventory.TakeFrom(inventory.Selected, 1);
                return true;
            }
            if (Brush) return Mound(world, GroundMaterial, true) > 0;
            byte tile = inventory.SelectedTile;
            if (tile == TileId.Air || !Place(world, tile)) return false;
            inventory.TakeFrom(inventory.Selected, 1);
            return true;
        }

        /// <summary>Builder as a raw tool (tests, scripted placement): places `id` without touching the inventory (a mound on a smooth planet).</summary>
        public bool Place(Vector2 world, byte id) =>
            Brush ? Mound(world, id, false) > 0 : CanPlace(world, id) && terrain.SetTile(TileOf(world).x, TileOf(world).y, id);

        /// <summary>Whether the Builder could place `id` at the world point now (U-046: the ghost turns red when not; on a smooth planet, the
        /// mound's: an open tile within the brush that no body stands in).</summary>
        public bool CanPlace(Vector2 world, byte id)
        {
            if (Brush) return id != TileId.Air && terrain != null && InReach(world) && MoundCells(world, null) > 0;
            var t = TileOf(world);
            if (terrain == null || !InReach(t) || id == TileId.Air) return false;
            byte current = terrain.GetTile(t.x, t.y);
            if (TileId.IsSolid(current)) return false;
            // Anything that isn't terrain in the cell (player, drop, ship) blocks placement.
            var hit = Physics2D.OverlapBox(new Vector2(t.x + 0.5f, t.y + 0.5f), Vector2.one * 0.9f, 0f);
            return hit == null || hit.GetComponentInParent<TerrainChunk>() != null;
        }

        /// <summary>U-157: no body (player, creature, drop, ship; triggers aside) in the cell: a mound may fill it.</summary>
        static bool Clear(Vector2 centre)
        {
            foreach (var hit in Physics2D.OverlapBoxAll(centre, Vector2.one * 0.9f, 0f))
                if (hit != null && !hit.isTrigger && hit.GetComponentInParent<TerrainChunk>() == null) return false;
            return true;
        }

        readonly System.Collections.Generic.List<Vector2Int> moundScratch = new System.Collections.Generic.List<Vector2Int>(4);

        /// <summary>The brush's open tiles at p that no body stands in (into `into` when given), nearest first; returns how many.</summary>
        int MoundCells(Vector2 p, System.Collections.Generic.List<Vector2Int> into)
        {
            into?.Clear();
            int n = 0;
            foreach (var c in BrushCells(p))
            {
                if (TileId.IsSolid(terrain.GetTile(c.x, c.y)) || !Clear(new Vector2(c.x + 0.5f, c.y + 0.5f))) continue; // D-165: never over a body
                n++;
                into?.Add(c);
            }
            return n;
        }

        /// <summary>U-157: piles `id` into the brush's open tiles at p (spending one ground item per tile when `spend`); returns tiles filled.</summary>
        public int Mound(Vector2 p, byte id, bool spend)
        {
            if (terrain == null || id == TileId.Air || !InReach(p)) return 0;
            if (MoundCells(p, moundScratch) == 0) return 0;
            int budget = spend ? GroundItems() : moundScratch.Count;
            int filled = 0;
            ShapeRead(p); // D-168: before the piled tiles flip
            terrain.BeginBatch();
            try
            {
                shapeSkip.Clear();
                foreach (var c in BrushCells(p)) if (!TileId.IsSolid(terrain.GetTile(c.x, c.y))) shapeSkip.Add(c); // an open cell within the brush keeps its density unless it is piled (a body stands there); a solid one rounds up with the disc
                foreach (var c in moundScratch)
                {
                    if (filled >= budget) break;
                    if (!terrain.SetTile(c.x, c.y, id)) continue;
                    filled++;
                    shapeSkip.Remove(c);
                }
                if (filled > 0) ShapeApply(p, false, shapeSkip);
            }
            finally { terrain.EndBatch(); }
            if (spend) SpendGroundItems(filled);
            if (filled > 0) Mounded?.Invoke(p);
            return filled;
        }

        readonly System.Collections.Generic.HashSet<Vector2Int> shapeSkip = new System.Collections.Generic.HashSet<Vector2Int>();

        /// <summary>U-157 (P-54, D-168): the density ramp round a stroke's circle at the quarter-metre sub-nodes (m). Two sub-cells wide: every
        /// sub-cell the traced edge crosses has its corners within ±0.25 m of the circle, so the field there is the disc's exact distance ramp and
        /// the edge holds BrushRadius to about a centimetre in every direction (at 1 m tile centres the best was 0.9 m on the axes, 0.755 m on the
        /// diagonals).</summary>
        public const float BrushRamp = 0.5f;

        const int Q = TerrainEdits.BlockSide, QQ = TerrainEdits.Block;
        float[] shapeNodes = new float[64];
        byte[] shapeNew = new byte[49 * QQ];
        bool[] shapeChanged = new bool[49], shapeOwn = new bool[49], shapeNode0 = new bool[49];
        byte[][] shapeBlocks = new byte[49][];
        readonly System.Collections.Generic.Dictionary<Vector2Int, bool> shapeClear = new System.Collections.Generic.Dictionary<Vector2Int, bool>();

        /// <summary>
        /// U-157 (P-54, D-168): the stroke's round shape in the drawn field. Every quarter-metre sub-node within BrushRadius + BrushRamp / 2 of p
        /// takes the disc's density (carve: the lower of its own and the disc's outside; pile: the higher of its own and the disc's inside), held
        /// in its tile's block (TerrainEdits.Block bytes). A tile without a block takes one first, holding what the tracer drew there (the bilinear
        /// between its four nodes), and so does any tile whose cell has a corner node that moved, so nothing outside the disc shifts. The tiles the
        /// brush flipped (centres within BrushRadius) agree with the disc, so the grid stays the game's solid / open truth. A mound never raises a
        /// sub-node in a cell a body stands in, nor in an unpiled cell within the brush (`skip`). Every value is read before any is written.
        /// </summary>
        int shapeX0, shapeY0, shapeW, shapeH;
        byte[] shapeGrid = new byte[64];
        float[] shapeCur = new float[49 * QQ];

        /// <summary>D-168: reads the drawn field round p (each tile's block, or the bilinear between its nodes) before the stroke flips any tile.</summary>
        void ShapeRead(Vector2 p)
        {
            float reach = BrushRadius + BrushRamp * 0.5f;
            int x0 = Mathf.FloorToInt(p.x - reach - 1.5f), x1 = Mathf.FloorToInt(p.x + reach - 0.5f);
            int y0 = Mathf.FloorToInt(p.y - reach - 1.5f), y1 = Mathf.FloorToInt(p.y + reach - 0.5f);
            int w = x1 - x0 + 1, h = y1 - y0 + 1, tiles = w * h, nw = w + 1;
            if (tiles > shapeChanged.Length)
            {
                shapeNew = new byte[tiles * QQ]; shapeChanged = new bool[tiles]; shapeOwn = new bool[tiles]; shapeNode0 = new bool[tiles]; shapeBlocks = new byte[tiles][];
                shapeCur = new float[tiles * QQ];
            }
            shapeX0 = x0; shapeY0 = y0; shapeW = w; shapeH = h;
            if (nw * (h + 1) > shapeNodes.Length) shapeNodes = new float[nw * (h + 1)];
            for (int j = 0; j <= h; j++)
                for (int i = 0; i <= w; i++) shapeNodes[j * nw + i] = terrain.NodeDensity(x0 + i, y0 + j);
            for (int j = 0; j < h; j++)
                for (int i = 0; i < w; i++)
                {
                    int k = j * w + i, tx = x0 + i, ty = y0 + j;
                    bool own = terrain.TryBlock(tx, ty, out var blk);
                    shapeOwn[k] = own; shapeBlocks[k] = blk;
                    float n00 = shapeNodes[j * nw + i], n10 = shapeNodes[j * nw + i + 1], n01 = shapeNodes[(j + 1) * nw + i], n11 = shapeNodes[(j + 1) * nw + i + 1];
                    for (int b = 0; b < Q; b++)
                        for (int a = 0; a < Q; a++)
                        {
                            float fx = a / (float)Q, fy = b / (float)Q;
                            shapeCur[k * QQ + b * Q + a] = own ? blk[b * Q + a] / 255f : Mathf.Lerp(Mathf.Lerp(n00, n10, fx), Mathf.Lerp(n01, n11, fx), fy);
                        }
                }
        }

        /// <summary>D-168: the stroke's disc over the field ShapeRead took (same p), written as blocks once the tiles have flipped.</summary>
        void ShapeApply(Vector2 p, bool carve, System.Collections.Generic.HashSet<Vector2Int> skip)
        {
            int x0 = shapeX0, y0 = shapeY0, w = shapeW, h = shapeH, gw = w + 1;
            shapeClear.Clear();
            if (!carve)
            {
                // D-168: the grid after the pile, round the range: solid, and built (piled where the generator left air). A sub-node whose cell's
                // four tiles are all solid, one of them built, is inside the mound: filled, so no gap between two strokes' discs shows as a hole.
                if (gw * (h + 1) > shapeGrid.Length) shapeGrid = new byte[gw * (h + 1)];
                for (int j = 0; j <= h; j++)
                    for (int i = 0; i <= w; i++)
                    {
                        int gx = x0 + i, gy = y0 + j;
                        bool solid = TileId.IsSolid(terrain.GetTile(gx, gy));
                        bool built = solid && !TileId.IsSolid(terrain.BaseGenerator.TileAt(terrain.WrapX(gx), gy));
                        shapeGrid[j * gw + i] = (byte)(solid ? built ? 2 : 1 : 0);
                    }
            }
            bool any = false;
            for (int j = 0; j < h; j++)
                for (int i = 0; i < w; i++)
                {
                    int k = j * w + i, tx = x0 + i, ty = y0 + j;
                    bool own = shapeOwn[k]; var blk = shapeBlocks[k];
                    shapeChanged[k] = false; shapeNode0[k] = false;
                    for (int b = 0; b < Q; b++)
                        for (int a = 0; a < Q; a++)
                        {
                            float fx = a / (float)Q, fy = b / (float)Q;
                            float cur = shapeCur[k * QQ + b * Q + a];
                            var pos = new Vector2(tx + 0.5f + fx, ty + 0.5f + fy);
                            float t = Mathf.Clamp01(((pos - p).magnitude - BrushRadius) / BrushRamp + 0.5f);
                            float next = cur;
                            if (carve) next = Mathf.Min(cur, t);
                            else
                            {
                                if (t < 1f && Pileable(pos, skip)) next = Mathf.Max(cur, 1f - t);
                                byte g00 = shapeGrid[j * gw + i], g10 = shapeGrid[j * gw + i + 1], g01 = shapeGrid[(j + 1) * gw + i], g11 = shapeGrid[(j + 1) * gw + i + 1];
                                if (g00 > 0 && g10 > 0 && g01 > 0 && g11 > 0 && (g00 == 2 || g10 == 2 || g01 == 2 || g11 == 2)) next = 1f;
                            }
                            bool moved = Mathf.Abs(next - cur) >= 0.5f / 255f;
                            shapeNew[k * QQ + b * Q + a] = own && !moved ? blk[b * Q + a] : (byte)Mathf.RoundToInt(Mathf.Clamp01(next) * 255f);
                            if (!moved) continue;
                            shapeChanged[k] = true; any = true;
                            if (a == 0 && b == 0) shapeNode0[k] = true;
                        }
                }
            if (!any) return;
            for (int j = 0; j < h; j++)
                for (int i = 0; i < w; i++)
                {
                    int k = j * w + i;
                    bool store = shapeChanged[k] || !shapeOwn[k] && (Node0(i + 1, j) || Node0(i, j + 1) || Node0(i + 1, j + 1));
                    if (!store) continue;
                    var blk = shapeOwn[k] ? shapeBlocks[k] : new byte[QQ];
                    System.Array.Copy(shapeNew, k * QQ, blk, 0, QQ);
                    terrain.SetBlock(x0 + i, y0 + j, blk);
                }

            bool Node0(int i, int j) => i < w && j < h && shapeNode0[j * w + i];
        }

        /// <summary>U-157: a mound may raise the sub-node at `pos`: its cell is not an unpiled brush cell and no body stands in it.</summary>
        bool Pileable(Vector2 pos, System.Collections.Generic.HashSet<Vector2Int> skip)
        {
            var cell = new Vector2Int(Mathf.FloorToInt(pos.x), Mathf.FloorToInt(pos.y));
            if (skip != null && skip.Contains(cell)) return false;
            if (!shapeClear.TryGetValue(cell, out bool clear)) shapeClear[cell] = clear = Clear(new Vector2(cell.x + 0.5f, cell.y + 0.5f));
            return clear;
        }

        /// <summary>U-157: the planet's one ground material a mound is made of (its near-surface ground).</summary>
        public byte GroundMaterial => terrain == null || terrain.Config == null ? TileId.Soil : terrain.Config.id switch
        {
            Meridian.Planets.PlanetId.Mars => TileId.Regolith,
            Meridian.Planets.PlanetId.Mercury => TileId.MercuryRegolith,
            Meridian.Planets.PlanetId.Venus => TileId.VenusBasalt,
            _ => TileId.Soil,
        };

        /// <summary>U-157: the ground items carried (any dug material: an item the old Builder could place). U-174: the dirt store first.</summary>
        public int GroundItems()
        {
            int n = D1 && Dirt != null ? Dirt.count : 0;
            if (inventory == null) return n;
            for (int s = 0; s < Meridian.Items.Inventory.SlotCount; s++)
            {
                var st = inventory[s];
                if (!st.IsEmpty && IsGround(st.itemId)) n += st.count;
            }
            return n;
        }

        static bool IsGround(int itemId) => (Meridian.Items.ItemRegistry.Get(itemId)?.placeTile ?? 0) != 0;

        void SpendGroundItems(int n)
        {
            if (D1 && Dirt != null) n -= Dirt.Spend(n); // U-174: the Builder spends the dirt store first
            for (int s = 0; s < Meridian.Items.Inventory.SlotCount && n > 0; s++)
            {
                var st = inventory[s];
                if (st.IsEmpty || !IsGround(st.itemId)) continue;
                int take = Mathf.Min(n, st.count);
                inventory.TakeFrom(s, take);
                n -= take;
            }
        }

        /// <summary>The material the player's Builder would place now (the inventory's selected stack; on a smooth planet the ground material
        /// while any ground item is carried; 0 = none).</summary>
        public byte SelectedTile => Brush ? (GroundItems() > 0 ? GroundMaterial : (byte)0) : inventory != null ? inventory.SelectedTile : (byte)0;
    }
}
