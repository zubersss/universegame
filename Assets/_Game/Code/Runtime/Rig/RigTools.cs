using Meridian.Terrain;
using UnityEngine;

namespace Meridian.Rig
{
    /// <summary>
    /// The Rig's M1 modules (Bible §8): Beam digs a solid tile and drops its item; Builder places
    /// a tile into air or water. Reach is measured from the owner. Input wiring comes with the
    /// player controller (U-009); these are the actions it calls.
    /// </summary>
    public sealed class RigTools : MonoBehaviour
    {
        /// <summary>Tool reach in meters (Bible is silent; P-09).</summary>
        public const float Reach = 5f;

        public TerrainStreamer terrain;
        public ItemDrops drops;
        public Transform owner;
        /// <summary>Where Builder material comes from and dug items go (GameState's; U-045, closes D-021).</summary>
        public Meridian.Items.Inventory inventory;
        /// <summary>Raised after the Beam removes a tile (U-032 dig animation).</summary>
        public event System.Action<Vector2> Dug;

        void Start()
        {
            if (inventory == null && Meridian.Core.GameState.Instance != null) inventory = Meridian.Core.GameState.Instance.inventory;
            if (drops != null && drops.collector == null) drops.collector = owner;
            if (drops != null && drops.inventory == null) drops.inventory = inventory;
        }

        public static Vector2Int TileOf(Vector2 world) =>
            new Vector2Int(Mathf.FloorToInt(world.x), Mathf.FloorToInt(world.y));

        bool InReach(Vector2Int tile)
        {
            if (owner == null) return true;
            var centre = new Vector2(tile.x + 0.5f, tile.y + 0.5f);
            return (centre - (Vector2)owner.position).sqrMagnitude <= Reach * Reach;
        }

        /// <summary>Beam: removes the solid tile at the world point and spawns its item.</summary>
        public bool Dig(Vector2 world)
        {
            var t = TileOf(world);
            if (terrain == null || !InReach(t)) return false;
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
            byte id = terrain.GetTile(t.x, t.y);
            if (!TileId.IsSolid(id)) return false;
            if (!terrain.SetTile(t.x, t.y, TileId.Air)) return false;
            Dug?.Invoke(world);
            int item = Meridian.Items.ItemRegistry.DropOf(id);
            // U-059: "only here" finds (Mars perchlorate deposits, Earth living seed).
            int depth = terrain.Generator != null ? terrain.Generator.SurfaceHeight(terrain.WrapX(t.x)) - t.y : 0;
            var (replace, bonus) = Meridian.Items.OnlyHere.DropAt(terrain.Config.id, id, terrain.WrapX(t.x), t.y, depth);
            if (replace != 0) item = replace;
            if (drops != null && item != 0)
            {
                var tile = replace != 0 ? null : terrain.TileSet.Get(id, 0) as UnityEngine.Tilemaps.Tile;
                drops.Spawn(item, new Vector2(t.x + 0.5f, t.y + 0.5f), tile != null ? tile.sprite : null);
            }
            if (drops != null && bonus != 0) drops.Spawn(bonus, new Vector2(t.x + 0.5f, t.y + 0.7f), null);
            return true;
        }

        /// <summary>U-059: a harvestable at the Beam's point (set by SolariteCrystals on Mercury).</summary>
        public System.Func<Vector2, int> harvest;
        /// <summary>U-056: the Beam on a base piece (BaseBuilder.Dismantle); the Builder with a base-piece item (BaseBuilder.PlaceItem).</summary>
        public System.Func<Vector2, bool> dismantle;
        public System.Func<Vector2, int, bool> placePiece;

        /// <summary>
        /// Builder (player input): places the inventory's selected material and uses one up. Nothing
        /// selected, or a material that isn't placeable: no placement.
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
            byte tile = inventory.SelectedTile;
            if (tile == TileId.Air || !Place(world, tile)) return false;
            inventory.TakeFrom(inventory.Selected, 1);
            return true;
        }

        /// <summary>Builder as a raw tool (tests, scripted placement): places `id` without touching the inventory.</summary>

        public bool Place(Vector2 world, byte id) => CanPlace(world, id) && terrain.SetTile(TileOf(world).x, TileOf(world).y, id);

        /// <summary>Whether the Builder could place `id` at the world point now (U-046: the ghost turns red when not).</summary>
        public bool CanPlace(Vector2 world, byte id)
        {
            var t = TileOf(world);
            if (terrain == null || !InReach(t) || id == TileId.Air) return false;
            byte current = terrain.GetTile(t.x, t.y);
            if (TileId.IsSolid(current)) return false;
            var centre = new Vector2(t.x + 0.5f, t.y + 0.5f);
            // Anything that isn't terrain in the cell (player, drop, ship) blocks placement.
            var hit = Physics2D.OverlapBox(centre, Vector2.one * 0.9f, 0f);
            return hit == null || hit.GetComponentInParent<TerrainChunk>() != null;
        }

        /// <summary>The material the player's Builder would place now (the inventory's selected stack; 0 = none).</summary>
        public byte SelectedTile => inventory != null ? inventory.SelectedTile : (byte)0;
    }
}
