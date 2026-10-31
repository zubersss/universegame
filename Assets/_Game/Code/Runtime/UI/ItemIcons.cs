using System.Collections.Generic;
using Meridian.Items;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.UI
{
    /// <summary>
    /// U-058: one icon cache for every panel (inventory, crafting, market). An item's B-013/B-042 icon, or for
    /// tile items without one the tile's own sprite; loaded once, kept for the session. `Loaded` fires when an
    /// icon arrives so open panels can redraw.
    /// </summary>
    public static class ItemIcons
    {
        static readonly Dictionary<int, Sprite> icons = new Dictionary<int, Sprite>();
        static readonly HashSet<int> requested = new HashSet<int>();
        public static event System.Action Loaded;

        /// <summary>The icon now (null while it loads or when the item has none; then Loaded fires later).</summary>
        public static Sprite Get(int itemId, Meridian.Terrain.TerrainStreamer terrain = null)
        {
            if (icons.TryGetValue(itemId, out var sp)) return sp;
            var def = ItemRegistry.Get(itemId);
            if (def == null) return null;
            if (def.icon == null)
            {
                if (def.placeTile == 0 || terrain == null) return null;
                var tile = terrain.TileSet.Get(def.placeTile, Meridian.Terrain.BlobAutotile.VariantCount - 1) as UnityEngine.Tilemaps.Tile;
                if (tile != null && tile.sprite != null) icons[itemId] = tile.sprite;
                return tile != null ? tile.sprite : null;
            }
            if (requested.Add(itemId))
            {
                var h = Addressables.LoadAssetAsync<IList<Sprite>>(def.icon);
                h.Completed += op =>
                {
                    if (op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                    icons[itemId] = op.Result[0];
                    Loaded?.Invoke();
                };
            }
            return null;
        }

        public static Sprite Get(string key, Meridian.Terrain.TerrainStreamer terrain = null)
        {
            var def = ItemRegistry.Get(key);
            return def != null ? Get(def.id, terrain) : null;
        }
    }
}
