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
        /// <summary>U-157: the round brush's radius (m): a stroke works the 1 to 4 tiles whose centres lie within it.</summary>
        public const float BrushRadius = 0.9f;

        public TerrainStreamer terrain;
        public ItemDrops drops;
        public Transform owner;
        /// <summary>Where Builder material comes from and dug items go (GameState's; U-045, closes D-021).</summary>
        public Meridian.Items.Inventory inventory;
        /// <summary>Raised after the Beam removes a tile (U-032 dig animation).</summary>
        public event System.Action<Vector2> Dug;
        /// <summary>U-157: raised after the Builder piles a mound (its puff).</summary>
        public event System.Action<Vector2> Mounded;

        void Start()
        {
            if (inventory == null && Meridian.Core.GameState.Instance != null) inventory = Meridian.Core.GameState.Instance.inventory;
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

        /// <summary>Beam: removes the solid tile at the world point (on a smooth planet, the brush's tiles) and spawns its item.</summary>
        public bool Dig(Vector2 world)
        {
            var t = TileOf(world);
            if (terrain == null || !(Brush ? InReach(world) : InReach(t))) return false;
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
            }
            finally { terrain.EndBatch(); }
            if (dug == 0) return false;
            Dug?.Invoke(p);
            return true;
        }

        /// <summary>The dug tile's item (and the planet's only-here finds) at the tile's centre.</summary>
        void DropFor(byte id, int x, int y)
        {
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
            terrain.BeginBatch();
            try
            {
                foreach (var c in moundScratch)
                {
                    if (filled >= budget) break;
                    if (!terrain.SetTile(c.x, c.y, id)) continue;
                    filled++;
                }
            }
            finally { terrain.EndBatch(); }
            if (spend) SpendGroundItems(filled);
            if (filled > 0) Mounded?.Invoke(p);
            return filled;
        }

        /// <summary>U-157: the planet's one ground material a mound is made of (its near-surface ground).</summary>
        public byte GroundMaterial => terrain == null || terrain.Config == null ? TileId.Soil : terrain.Config.id switch
        {
            Meridian.Planets.PlanetId.Mars => TileId.Regolith,
            Meridian.Planets.PlanetId.Mercury => TileId.MercuryRegolith,
            Meridian.Planets.PlanetId.Venus => TileId.VenusBasalt,
            _ => TileId.Soil,
        };

        /// <summary>U-157: the ground items carried (any dug material: an item the old Builder could place).</summary>
        public int GroundItems()
        {
            if (inventory == null) return 0;
            int n = 0;
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
