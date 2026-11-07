using Meridian.Art;
using System.Collections.Generic;
using Meridian.Items;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.UI
{
    /// <summary>
    /// U-058: one icon cache for every panel (inventory, crafting, market). An item's B-013/B-042 icon, loaded once and
    /// kept for the session; a tile item without an icon shows its sheet's sprite only while that sheet is loaded (its own
    /// planet, U-091: a sprite destroyed with its planet's bundle falls through to the live TileSet, or to null, which the
    /// panels hide). `Loaded` fires when an icon arrives so open panels can redraw.
    /// </summary>
    public static class ItemIcons
    {
        static readonly Dictionary<int, Sprite> icons = new Dictionary<int, Sprite>();
        static readonly HashSet<int> requested = new HashSet<int>();
        public static event System.Action Loaded;

        /// <summary>The icon now (null while it loads or when the item has none; then Loaded fires later).</summary>
        public static Sprite Get(int itemId, Meridian.Terrain.TerrainStreamer terrain = null)
        {
            if (icons.TryGetValue(itemId, out var sp) && sp != null) return sp; // U-091: a destroyed tile sprite is looked up again
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
                var h = ArtLoad.Asset<IList<Sprite>>(def.icon);
                h.Completed += op =>
                {
                    if (op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                    icons[itemId] = op.Result[0];
                    Loaded?.Invoke();
                };
            }
            return null;
        }

        static readonly Dictionary<string, Sprite> named = new Dictionary<string, Sprite>();
        static readonly HashSet<string> namedRequested = new HashSet<string>();

        /// <summary>U-091 (tests): forgets every cached icon and request.</summary>
        public static void ClearCache()
        {
            icons.Clear(); requested.Clear(); named.Clear(); namedRequested.Clear();
        }

        /// <summary>An icon by its art name (icons/&lt;name&gt;/base): blueprint nodes, which are not items (B-051).</summary>
        public static Sprite GetNamed(string name)
        {
            if (string.IsNullOrEmpty(name)) return null;
            if (named.TryGetValue(name, out var sp)) return sp;
            if (namedRequested.Add(name))
            {
                var h = ArtLoad.Asset<IList<Sprite>>($"icons/{name}/base");
                h.Completed += op =>
                {
                    if (op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                    named[name] = op.Result[0];
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
