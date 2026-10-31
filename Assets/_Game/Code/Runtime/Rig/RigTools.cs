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
        [Tooltip("Material the Builder places (inventory selection arrives with the inventory task).")]
        public byte builderTile = TileId.Soil;
        /// <summary>Raised after the Beam removes a tile (U-032 dig animation).</summary>
        public event System.Action<Vector2> Dug;

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
            byte id = terrain.GetTile(t.x, t.y);
            if (!TileId.IsSolid(id)) return false;
            if (!terrain.SetTile(t.x, t.y, TileId.Air)) return false;
            Dug?.Invoke(world);
            if (drops != null)
            {
                var tile = terrain.TileSet.Get(id, 0) as UnityEngine.Tilemaps.Tile;
                drops.Spawn(id, new Vector2(t.x + 0.5f, t.y + 0.5f), tile != null ? tile.sprite : null);
            }
            return true;
        }

        /// <summary>Builder: places builderTile into an air or water cell that nothing solid overlaps.</summary>
        public bool Place(Vector2 world) => Place(world, builderTile);

        public bool Place(Vector2 world, byte id)
        {
            var t = TileOf(world);
            if (terrain == null || !InReach(t) || id == TileId.Air) return false;
            byte current = terrain.GetTile(t.x, t.y);
            if (TileId.IsSolid(current)) return false;
            var centre = new Vector2(t.x + 0.5f, t.y + 0.5f);
            // Anything that isn't terrain in the cell (player, drop, ship) blocks placement.
            var hit = Physics2D.OverlapBox(centre, Vector2.one * 0.9f, 0f);
            if (hit != null && hit.GetComponentInParent<TerrainChunk>() == null) return false;
            return terrain.SetTile(t.x, t.y, id);
        }
    }
}
